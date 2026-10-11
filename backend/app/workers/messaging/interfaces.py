from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, List, Optional
from app.workers.messaging.schemas import DLQItem, JobExecutionTracker, MessagePayload, QueueMetrics


class IMessageProducer(ABC):
    """Abstract Producer Interface (DIP / OCP) for pushing messages to brokers."""

    @abstractmethod
    async def start(self) -> None:
        """Initialize producer client connection."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Close producer connection cleanly."""
        pass

    @abstractmethod
    async def produce(self, topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> MessagePayload:
        """Publish a message payload to specified topic."""
        pass


class IMessageConsumer(ABC):
    """Abstract Consumer Interface (DIP / OCP) for subscribing to topics."""

    @abstractmethod
    async def start(self) -> None:
        """Start consumer loop and subscribe to topics."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shutdown consumer loop."""
        pass

    @abstractmethod
    async def consume(
        self,
        topic: str,
        handler: Callable[[MessagePayload], Coroutine[Any, Any, None]],
        batch_size: int = 1,
    ) -> None:
        """Consume messages from topic and pass to handler function."""
        pass


class IRetryPolicy(ABC):
    """Strategy interface for computing retry backoffs and evaluating retryability."""

    @abstractmethod
    def calculate_backoff(self, attempt: int) -> float:
        """Compute wait duration in seconds for given attempt count."""
        pass

    @abstractmethod
    def is_retryable(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        """Determine if exception is transient and attempt < max_attempts."""
        pass


class IRetryTracker(ABC):
    """Interface for tracking job execution states, attempts, and error history."""

    @abstractmethod
    async def record_attempt(
        self,
        job_id: str,
        topic: str,
        attempt: int,
        max_attempts: int,
        error: Optional[Exception] = None,
        backoff_seconds: float = 0.0,
        payload: Optional[Dict[str, Any]] = None,
    ) -> JobExecutionTracker:
        """Record an execution attempt and log error history."""
        pass

    @abstractmethod
    async def record_success(self, job_id: str) -> None:
        """Mark job as successfully completed."""
        pass

    @abstractmethod
    async def record_dlq_failure(self, job_id: str, final_error: str) -> None:
        """Mark job state as failed and transferred to DLQ."""
        pass

    @abstractmethod
    async def get_job_state(self, job_id: str) -> Optional[JobExecutionTracker]:
        """Fetch tracking state for a specific job."""
        pass


class IDeadLetterQueue(ABC):
    """Interface for managing unrecoverable failed messages (DLQ)."""

    @abstractmethod
    async def send_to_dlq(self, message: MessagePayload, final_error: Exception, history: List[Any]) -> DLQItem:
        """Persist message to Dead Letter Queue."""
        pass

    @abstractmethod
    async def list_dlq_items(self, topic: Optional[str] = None, limit: int = 50) -> List[DLQItem]:
        """Retrieve items stored in Dead Letter Queue."""
        pass

    @abstractmethod
    async def replay_dlq_item(self, dlq_id: str, producer: IMessageProducer) -> Optional[MessagePayload]:
        """Replay a DLQ item back onto its original topic."""
        pass

    @abstractmethod
    async def purge(self, topic: Optional[str] = None) -> int:
        """Clear items from DLQ."""
        pass
