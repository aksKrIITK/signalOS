import asyncio
import pytest
from app.core.exceptions import NonTransientQueueError, TransientQueueError, ValidationError
from app.workers.messaging import (
    DLQItem,
    ExponentialBackoffJitterPolicy,
    MemoryConsumerAdapter,
    MemoryProducerAdapter,
    MessageBus,
    RedisDeadLetterQueue,
    RedisRetryTracker,
)


@pytest.mark.asyncio
async def test_exponential_backoff_jitter_policy():
    policy = ExponentialBackoffJitterPolicy(
        initial_delay=1.0, max_delay=10.0, backoff_factor=2.0, use_jitter=False
    )
    # Without jitter: delay should double
    assert policy.calculate_backoff(1) == 1.0
    assert policy.calculate_backoff(2) == 2.0
    assert policy.calculate_backoff(3) == 4.0
    assert policy.calculate_backoff(5) == 10.0  # Capped at max_delay 10.0

    # Test jitter bounds
    jitter_policy = ExponentialBackoffJitterPolicy(
        initial_delay=1.0, max_delay=10.0, backoff_factor=2.0, use_jitter=True
    )
    backoff = jitter_policy.calculate_backoff(3)  # capped is 4.0 -> range [2.0, 4.0]
    assert 2.0 <= backoff <= 4.0


@pytest.mark.asyncio
async def test_retry_policy_exception_classification():
    policy = ExponentialBackoffJitterPolicy()

    # Retryable transient exceptions
    assert policy.is_retryable(TransientQueueError("Network blip"), attempt=1, max_attempts=3) is True
    assert policy.is_retryable(TimeoutError("Connection timed out"), attempt=1, max_attempts=3) is True

    # Non-retryable fatal exceptions
    assert policy.is_retryable(ValidationError("Invalid email"), attempt=1, max_attempts=3) is False
    assert policy.is_retryable(NonTransientQueueError("Corrupt payload"), attempt=1, max_attempts=3) is False

    # Max attempts exceeded
    assert policy.is_retryable(TransientQueueError("Network blip"), attempt=3, max_attempts=3) is False


@pytest.mark.asyncio
async def test_memory_producer_consumer():
    queues = {}
    producer = MemoryProducerAdapter(queues)
    consumer = MemoryConsumerAdapter(queues)

    received = []

    async def sample_handler(msg):
        received.append(msg.payload)

    await producer.start()
    await consumer.start()

    await consumer.consume("test.topic", sample_handler)
    await producer.produce("test.topic", {"test_key": "test_val"})

    await asyncio.sleep(0.6)
    await producer.stop()
    await consumer.stop()

    assert len(received) == 1
    assert received[0]["test_key"] == "test_val"


@pytest.mark.asyncio
async def test_retry_tracker_record_attempt():
    tracker = RedisRetryTracker()
    job_id = "test-job-123"

    # Record first failed attempt
    err = TransientQueueError("Service Unavailable 503")
    state = await tracker.record_attempt(
        job_id=job_id,
        topic="agent.runs",
        attempt=1,
        max_attempts=3,
        error=err,
        backoff_seconds=1.5,
        payload={"task": "scoring"},
    )

    assert state.job_id == job_id
    assert state.attempts == 1
    assert state.last_error == "Service Unavailable 503"
    assert len(state.history) == 1
    assert state.history[0].error_type == "TransientQueueError"
    assert state.history[0].backoff_seconds == 1.5

    # Record success
    await tracker.record_success(job_id)
    updated = await tracker.get_job_state(job_id)
    assert updated.state == "COMPLETED"


@pytest.mark.asyncio
async def test_message_bus_retry_and_dlq_flow():
    shared_queues = {}
    producer = MemoryProducerAdapter(shared_queues)
    consumer = MemoryConsumerAdapter(shared_queues)
    policy = ExponentialBackoffJitterPolicy(initial_delay=0.05, max_delay=0.2, use_jitter=False)
    retry_tracker = RedisRetryTracker()
    retry_tracker._connection_failed = True
    dlq = RedisDeadLetterQueue()
    dlq._connection_failed = True

    bus = MessageBus(
        producer=producer,
        consumer=consumer,
        retry_policy=policy,
        retry_tracker=retry_tracker,
        dlq=dlq,
    )
    await bus.start()

    attempts_count = 0

    async def failing_handler(payload):
        nonlocal attempts_count
        attempts_count += 1
        if attempts_count < 3:
            raise TransientQueueError(f"Transient error attempt {attempts_count}")

    await bus.subscribe("test.retry.topic", failing_handler)
    await bus.publish("test.retry.topic", {"item": 1}, key="test_job_id")

    await asyncio.sleep(0.5)
    await bus.stop()

    assert attempts_count == 3


@pytest.mark.asyncio
async def test_message_bus_non_transient_direct_dlq():
    shared_queues = {}
    producer = MemoryProducerAdapter(shared_queues)
    consumer = MemoryConsumerAdapter(shared_queues)
    policy = ExponentialBackoffJitterPolicy(initial_delay=0.05, max_delay=0.2, use_jitter=False)
    retry_tracker = RedisRetryTracker()
    retry_tracker._connection_failed = True
    dlq = RedisDeadLetterQueue()
    dlq._connection_failed = True

    bus = MessageBus(
        producer=producer,
        consumer=consumer,
        retry_policy=policy,
        retry_tracker=retry_tracker,
        dlq=dlq,
    )
    await bus.start()

    attempts_count = 0

    async def fatal_handler(payload):
        nonlocal attempts_count
        attempts_count += 1
        raise NonTransientQueueError("Fatal Schema Validation Failure")

    await bus.subscribe("test.fatal.topic", fatal_handler)
    await bus.publish("test.fatal.topic", {"item": "corrupt"}, key="fatal_job_id")

    await asyncio.sleep(0.3)
    await bus.stop()

    # Fatal errors should NOT be retried (attempt count must be 1)
    assert attempts_count == 1

    # Verify DLQ contains item
    dlq_items = await dlq.list_dlq_items(topic="test.fatal.topic")
    assert len(dlq_items) == 1
    assert dlq_items[0].error_type == "NonTransientQueueError"
