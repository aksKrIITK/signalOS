import asyncio
import json
from typing import Any, Callable, Coroutine, Dict, Optional

from app.core.config import settings
from app.core.logging import logger
from app.workers.messaging.dlq import RedisDeadLetterQueue
from app.workers.messaging.interfaces import (
    IDeadLetterQueue,
    IMessageConsumer,
    IMessageProducer,
    IRetryPolicy,
    IRetryTracker,
)
from app.workers.messaging.kafka_adapter import KafkaConsumerAdapter, KafkaProducerAdapter
from app.workers.messaging.memory_adapter import MemoryConsumerAdapter, MemoryProducerAdapter
from app.workers.messaging.redis_adapter import RedisConsumerAdapter, RedisProducerAdapter
from app.workers.messaging.retry import ExponentialBackoffJitterPolicy
from app.workers.messaging.retry_tracker import RedisRetryTracker
from app.workers.messaging.schemas import MessagePayload, QueueMetrics


class MessageBus:
    """
    Unified Production MessageBus Facade & Container (DIP / SOLID).
    Orchestrates Producer, Consumer, Exponential Retry Policy, Retry Tracker, and Dead Letter Queue.
    """

    def __init__(
        self,
        producer: IMessageProducer,
        consumer: IMessageConsumer,
        retry_policy: IRetryPolicy,
        retry_tracker: IRetryTracker,
        dlq: IDeadLetterQueue,
    ):
        self.producer = producer
        self.consumer = consumer
        self.retry_policy = retry_policy
        self.retry_tracker = retry_tracker
        self.dlq = dlq
        self._started = False

    async def start(self) -> None:
        if not self._started:
            await self.producer.start()
            await self.consumer.start()
            self._started = True
            logger.info("message_bus_started", backend=settings.QUEUE_BACKEND)

    async def stop(self) -> None:
        if self._started:
            await self.producer.stop()
            await self.consumer.stop()
            self._started = False
            logger.info("message_bus_stopped")

    async def publish(self, topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> MessagePayload:
        """Publishes job message onto queue/topic with attempt tracking."""
        if not self._started:
            await self.start()
        return await self.producer.produce(topic=topic, payload=payload, key=key)

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
        batch_size: int = 1,
    ) -> None:
        """
        Subscribes handler to topic with automated error handling, exponential backoff retries,
        attempt tracking, and Dead Letter Queue routing.
        """
        if not self._started:
            await self.start()

        async def _resilient_wrapper(message: MessagePayload) -> None:
            attempt = message.attempts + 1
            max_attempts = message.max_attempts or settings.MAX_JOB_RETRIES

            logger.info(
                "job_execution_started",
                topic=topic,
                job_id=message.job_id,
                attempt=attempt,
                max_attempts=max_attempts,
            )

            try:
                # 1. Execute domain handler
                await handler(message.payload)

                # 2. Record success in tracker
                await self.retry_tracker.record_success(message.job_id)
                logger.info("job_execution_succeeded", topic=topic, job_id=message.job_id, attempt=attempt)

            except Exception as exc:
                # 3. Evaluate retryability & compute backoff with jitter
                is_retryable = self.retry_policy.is_retryable(exc, attempt, max_attempts)
                backoff_seconds = self.retry_policy.calculate_backoff(attempt) if is_retryable else 0.0

                # 4. Record attempt in tracker
                tracker_state = await self.retry_tracker.record_attempt(
                    job_id=message.job_id,
                    topic=topic,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=exc,
                    backoff_seconds=backoff_seconds,
                    payload=message.payload,
                )

                if is_retryable and attempt < max_attempts:
                    logger.warning(
                        "job_execution_failed_scheduling_retry",
                        topic=topic,
                        job_id=message.job_id,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        backoff_seconds=round(backoff_seconds, 2),
                        error=str(exc),
                    )
                    # Prepare message payload for retry attempt
                    retry_payload = dict(message.payload)
                    retry_payload["attempts"] = attempt
                    retry_payload["job_id"] = message.job_id

                    # Sleep backoff duration asynchronously before re-enqueueing
                    if backoff_seconds > 0:
                        await asyncio.sleep(backoff_seconds)
                    await self.producer.produce(topic, retry_payload, key=message.job_id)

                else:
                    # 5. Route to Dead Letter Queue (DLQ)
                    logger.error(
                        "job_execution_failed_max_retries_or_fatal_routing_to_dlq",
                        topic=topic,
                        job_id=message.job_id,
                        attempt=attempt,
                        error=str(exc),
                    )
                    message.attempts = attempt
                    dlq_item = await self.dlq.send_to_dlq(
                        message=message,
                        final_error=exc,
                        history=tracker_state.history if tracker_state else [],
                    )
                    await self.retry_tracker.record_dlq_failure(message.job_id, str(exc))

        await self.consumer.consume(topic=topic, handler=_resilient_wrapper, batch_size=batch_size)


class MessageBusFactory:
    """Factory creating MessageBus instances based on environment settings (OCP / Factory Pattern)."""

    @staticmethod
    def create_bus(backend: Optional[str] = None) -> MessageBus:
        selected_backend = backend or settings.QUEUE_BACKEND.lower()
        retry_policy = ExponentialBackoffJitterPolicy()
        retry_tracker = RedisRetryTracker()
        dlq = RedisDeadLetterQueue()

        if selected_backend == "kafka":
            producer = KafkaProducerAdapter()
            consumer = KafkaConsumerAdapter()
        elif selected_backend == "redis":
            producer = RedisProducerAdapter()
            consumer = RedisConsumerAdapter()
        else:
            # Memory adapter for testing / zero-dependency fallback
            shared_queues: Dict[str, asyncio.Queue] = {}
            producer = MemoryProducerAdapter(shared_queues)
            consumer = MemoryConsumerAdapter(shared_queues)

        return MessageBus(
            producer=producer,
            consumer=consumer,
            retry_policy=retry_policy,
            retry_tracker=retry_tracker,
            dlq=dlq,
        )


# Global Singleton Bus Instance
message_bus = MessageBusFactory.create_bus()
