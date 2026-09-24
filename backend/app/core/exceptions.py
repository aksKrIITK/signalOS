from typing import Any, Dict, Optional


class AppError(Exception):
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
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422, details=details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401, details=details)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, details=details)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)


class ProviderError(AppError):
    def __init__(self, message: str = "LLM provider error", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="PROVIDER_ERROR", message=message, status_code=502, details=details)


class ToolExecutionError(AppError):
    def __init__(self, message: str = "Tool execution failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="TOOL_EXECUTION_ERROR", message=message, status_code=500, details=details)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, status_code=429, details=details)


class SecurityError(AppError):
    def __init__(self, message: str = "Security policy violation", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="SECURITY_VIOLATION", message=message, status_code=400, details=details)
