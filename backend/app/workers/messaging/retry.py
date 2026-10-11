import math
import random
import sys
import traceback
from typing import Set, Type
from app.core.config import settings
from app.core.exceptions import (
    NonTransientQueueError,
    TransientQueueError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
)
from app.workers.messaging.interfaces import IRetryPolicy


class ExponentialBackoffJitterPolicy(IRetryPolicy):
    """
    Production-grade retry policy implementing Exponential Backoff with Full Jitter.
    Formula: T_wait = random_uniform(0, min(max_delay, initial_delay * (factor ** attempt)))
    """

    def __init__(
        self,
        initial_delay: float = settings.RETRY_INITIAL_DELAY_SECONDS,
        max_delay: float = settings.RETRY_MAX_DELAY_SECONDS,
        backoff_factor: float = settings.RETRY_BACKOFF_FACTOR,
        use_jitter: bool = settings.RETRY_JITTER,
        non_retryable_exceptions: Optional[Set[Type[Exception]]] = None,
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.use_jitter = use_jitter
        self.non_retryable_exceptions: Set[Type[Exception]] = non_retryable_exceptions or {
            ValidationError,
            UnauthorizedError,
            ForbiddenError,
            NonTransientQueueError,
            ValueError,
            KeyError,
            TypeError,
        }

    def calculate_backoff(self, attempt: int) -> float:
        """Computes next retry interval in seconds."""
        if attempt <= 0:
            return 0.0

        # Calculated exponential duration
        calculated_delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        capped_delay = min(self.max_delay, calculated_delay)

        if self.use_jitter:
            # Full Jitter: random duration between 0 and capped_delay
            return random.uniform(0.5 * capped_delay, capped_delay)
        return capped_delay

    def is_retryable(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        """
        Determines whether an exception is transient and should be retried.
        Fatal / non-transient exceptions bypass retry and go straight to DLQ.
        """
        if attempt >= max_attempts:
            return False

        # If explicitly non-retryable exception class or subclass
        if any(isinstance(exception, exc_cls) for exc_cls in self.non_retryable_exceptions):
            return False

        # If explicitly transient queue error
        if isinstance(exception, TransientQueueError):
            return True

        # Default transient errors: IO errors, timeouts, connection issues, 5xx server errors
        exc_str = str(exception).lower()
        transient_keywords = [
            "timeout", "connect", "connection", "lock", "deadlock",
            "503", "502", "504", "429", "rate limit", "busy", "temporarily unavailable"
        ]
        if any(k in exc_str for k in transient_keywords):
            return True

        # Custom domain AppErrors with status 5xx or 429 are retryable
        if hasattr(exception, "status_code"):
            status_code = getattr(exception, "status_code")
            if status_code in (429, 502, 503, 504):
                return True
            if 400 <= status_code < 500:
                return False

        # Default: default to retryable for unknown unexpected system exceptions up to max_attempts
        return True


def format_exception_stack(exc: Exception) -> str:
    """Utility to format full exception traceback for diagnostic tracking."""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
