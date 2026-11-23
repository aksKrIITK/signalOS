from typing import Any, Dict, Optional


class AppError(Exception):
    """Base application exception with machine-readable error codes and HTTP status code mappings."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when an entity, record, or resource does not exist in the tenant workspace."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class ValidationError(AppError):
    """Raised when incoming user request payload or state fails domain validation rules."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422, details=details)


class UnauthorizedError(AppError):
    """Raised when authentication credentials are missing, expired, or invalid."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401, details=details)


class ForbiddenError(AppError):
    """Raised when authenticated user lacks permissions or roles to access a resource."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, details=details)


class ConflictError(AppError):
    """Raised when a resource state conflict or unique constraint violation occurs."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)


class ProviderError(AppError):
    """Raised when an external LLM provider API fails or returns unexpected responses."""

    def __init__(self, message: str = "LLM provider error", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="PROVIDER_ERROR", message=message, status_code=502, details=details)


class ToolExecutionError(AppError):
    """Raised when an agent tool invocation fails during pipeline runtime."""

    def __init__(self, message: str = "Tool execution failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="TOOL_EXECUTION_ERROR", message=message, status_code=500, details=details)


class RateLimitError(AppError):
    """Raised when request volume exceeds defined quota limits or rate throttling gates."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, status_code=429, details=details)


class SecurityError(AppError):
    """Raised when an operation violates security policies, such as SSRF or prompt injection detection."""

    def __init__(self, message: str = "Security policy violation", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="SECURITY_VIOLATION", message=message, status_code=400, details=details)


# Queue & Retry System Exceptions
class QueueError(AppError):
    """Base exception for message queue & retry pipeline operations."""
    def __init__(self, code: str = "QUEUE_ERROR", message: str = "Queue operation failed", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status_code, details=details)


class MessageBrokerConnectionError(QueueError):
    def __init__(self, message: str = "Failed to connect to message broker", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="BROKER_CONNECTION_ERROR", message=message, status_code=503, details=details)


class TransientQueueError(QueueError):
    """Transient errors that are safe to retry with backoff (e.g. network timeout, rate limit, temp deadlock)."""
    def __init__(self, message: str = "Transient queue error - retryable", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="TRANSIENT_QUEUE_ERROR", message=message, status_code=503, details=details)


class NonTransientQueueError(QueueError):
    """Fatal, non-retryable errors (e.g. corrupt payload, schema mismatch, unauthorized). Sent directly to DLQ."""
    def __init__(self, message: str = "Fatal non-transient error - routed to DLQ", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="NON_TRANSIENT_QUEUE_ERROR", message=message, status_code=400, details=details)


class MaxRetriesExceededError(QueueError):
    """Raised when job retry count reaches MAX_RETRIES threshold."""
    def __init__(self, message: str = "Max retries exceeded for job", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="MAX_RETRIES_EXCEEDED", message=message, status_code=500, details=details)


class DLQRoutingError(QueueError):
    """Raised when writing to Dead Letter Queue fails."""
    def __init__(self, message: str = "Failed to route message to Dead Letter Queue", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="DLQ_ROUTING_ERROR", message=message, status_code=500, details=details)

