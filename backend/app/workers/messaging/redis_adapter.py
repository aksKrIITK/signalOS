import asyncio
import json
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger
from app.workers.messaging.interfaces import IMessageConsumer, IMessageProducer
from app.workers.messaging.schemas import MessagePayload


class RedisProducerAdapter(IMessageProducer):
    """
    Production-grade Redis Producer supporting High-Throughput Queues and Pub/Sub events.
    Fulfills IMessageProducer interface (DIP/SRP).
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None

    async def start(self) -> None:
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    health_check_interval=30,
                )
                await self._redis.ping()
                logger.info("redis_producer_connected", url=self.redis_url)
            except Exception as e:
                logger.warning("redis_producer_connection_failed", error=str(e))
                self._redis = None

    async def stop(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get_redis(self) -> Optional[redis.Redis]:
        if not self._redis:
            await self.start()
        return self._redis

    async def produce(self, topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> MessagePayload:
        job_id = payload.get("job_id") or str(uuid.uuid4())
        msg = MessagePayload(
            job_id=job_id,
            topic=topic,
            payload=payload,
            attempts=payload.get("attempts", 0),
            max_attempts=payload.get("max_attempts", settings.MAX_JOB_RETRIES),
        )
        data_json = msg.model_dump_json()

        r = await self.get_redis()
        if r:
            try:
                # Push to main list queue
                await r.rpush(f"queue:{topic}", data_json)
                # Set job status in Redis cache
                await r.hset(f"job:{job_id}", mapping={"status": "QUEUED", "topic": topic, "attempts": str(msg.attempts)})
                await r.expire(f"job:{job_id}", 86400)  # 24 hour TTL
                logger.debug("redis_message_enqueued", topic=topic, job_id=job_id)
            except Exception as e:
                logger.error("redis_produce_error", topic=topic, job_id=job_id, error=str(e))
                raise e
        return msg


class RedisConsumerAdapter(IMessageConsumer):
    """
    Production-grade Redis Consumer using non-blocking BLPOP with connection resiliency.
    Fulfills IMessageConsumer interface (DIP/SRP).
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        self._running = True
        if not self._redis:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                await self._redis.ping()
                logger.info("redis_consumer_connected")
            except Exception as e:
                logger.warning("redis_consumer_connection_failed", error=str(e))

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def consume(
        self,
        topic: str,
        handler: Callable[[MessagePayload], Coroutine[Any, Any, None]],
        batch_size: int = 1,
    ) -> None:
        if not self._redis:
            await self.start()

        async def _consumer_loop():
            queue_key = f"queue:{topic}"
            logger.info("redis_consumer_loop_started", topic=topic)
            while self._running:
                if not self._redis:
                    await asyncio.sleep(1.0)
                    await self.start()
                    continue

                try:
                    # BLPOP with 2s timeout
                    item = await self._redis.blpop(queue_key, timeout=2)
                    if item:
                        _, raw_data = item
                        try:
                            data_dict = json.loads(raw_data)
                            message = MessagePayload(**data_dict)
                            await handler(message)
                        except Exception as handler_err:
                            logger.error("redis_consumer_handler_uncaught_error", topic=topic, error=str(handler_err))
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning("redis_consumer_poll_error", topic=topic, error=str(e))
                    await asyncio.sleep(1.0)

        task = asyncio.create_task(_consumer_loop())
        self._tasks.append(task)
