import asyncio
import json
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.workers.messaging.interfaces import IMessageConsumer, IMessageProducer
from app.workers.messaging.schemas import MessagePayload

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    AIOKafkaConsumer = None
    AIOKafkaProducer = None


class KafkaProducerAdapter(IMessageProducer):
    """
    Production-grade Kafka Producer implementing IMessageProducer.
    Supports high-throughput multi-partition message dispatching with key partitioning.
    """

    def __init__(
        self,
        bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS,
        client_id: str = settings.KAFKA_CLIENT_ID,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self._producer = None
        self._is_started = False

    async def start(self) -> None:
        if not KAFKA_AVAILABLE:
            logger.warning("aiokafka_not_installed_kafka_producer_disabled")
            return

        if not self._is_started:
            try:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    client_id=self.client_id,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    acks="all",  # Guaranteed delivery
                    retry_backoff_ms=500,
                )
                await self._producer.start()
                self._is_started = True
                logger.info("kafka_producer_started", bootstrap_servers=self.bootstrap_servers)
            except Exception as e:
                logger.warning("kafka_producer_start_failed_using_fallback", error=str(e))
                self._producer = None

    async def stop(self) -> None:
        if self._producer and self._is_started:
            try:
                await self._producer.stop()
                logger.info("kafka_producer_stopped")
            except Exception as e:
                logger.warning("kafka_producer_stop_error", error=str(e))
            finally:
                self._is_started = False
                self._producer = None

    async def produce(self, topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> MessagePayload:
        job_id = payload.get("job_id") or str(uuid.uuid4())
        msg = MessagePayload(
            job_id=job_id,
            topic=topic,
            payload=payload,
            attempts=payload.get("attempts", 0),
            max_attempts=payload.get("max_attempts", settings.MAX_JOB_RETRIES),
        )

        if not self._is_started or not self._producer:
            await self.start()

        if self._producer and self._is_started:
            try:
                partition_key = key or job_id
                await self._producer.send_and_wait(
                    topic=topic,
                    value=msg.model_dump(),
                    key=partition_key,
                )
                logger.debug("kafka_message_published", topic=topic, job_id=job_id, key=partition_key)
            except Exception as e:
                logger.error("kafka_produce_send_error", topic=topic, job_id=job_id, error=str(e))
                raise e
        else:
            logger.warning("kafka_producer_unavailable_msg_dropped", topic=topic, job_id=job_id)

        return msg


class KafkaConsumerAdapter(IMessageConsumer):
    """
    Production-grade Kafka Consumer Group worker implementing IMessageConsumer.
    Consumes partitions concurrently with auto-rebalancing and offset commits.
    """

    def __init__(
        self,
        bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id: str = settings.KAFKA_CONSUMER_GROUP,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self._consumer = None
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._consumer:
            try:
                await self._consumer.stop()
                logger.info("kafka_consumer_stopped")
            except Exception as e:
                logger.warning("kafka_consumer_stop_error", error=str(e))

    async def consume(
        self,
        topic: str,
        handler: Callable[[MessagePayload], Coroutine[Any, Any, None]],
        batch_size: int = 1,
    ) -> None:
        if not KAFKA_AVAILABLE:
            logger.warning("aiokafka_not_installed_kafka_consumer_disabled", topic=topic)
            return

        async def _consumer_loop():
            logger.info("kafka_consumer_loop_starting", topic=topic, group_id=self.group_id)
            try:
                consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=f"{self.group_id}-{topic}",
                    auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                    enable_auto_commit=True,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                )
                await consumer.start()
                self._consumer = consumer

                while self._running:
                    try:
                        data = await consumer.getmany(timeout_ms=1000, max_records=batch_size)
                        for tp, messages in data.items():
                            for k_msg in messages:
                                try:
                                    payload_dict = k_msg.value
                                    msg = MessagePayload(**payload_dict)
                                    await handler(msg)
                                except Exception as err:
                                    logger.error("kafka_consumer_handler_error", topic=topic, error=str(err))
                    except asyncio.CancelledError:
                        break
                    except Exception as poll_err:
                        logger.warning("kafka_consumer_poll_error", topic=topic, error=str(poll_err))
                        await asyncio.sleep(1.0)
            except Exception as init_err:
                logger.warning("kafka_consumer_init_failed", topic=topic, error=str(init_err))
            finally:
                if self._consumer:
                    await self._consumer.stop()

        task = asyncio.create_task(_consumer_loop())
        self._tasks.append(task)
