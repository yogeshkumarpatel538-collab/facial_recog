from typing import Any, Optional


class AppException(Exception):
    """Base application exception with HTTP mapping metadata."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        self.message = message or self.message
        if error_code:
            self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Could not validate credentials"


class AuthorizationError(AppException):
    status_code = 403
    error_code = "AUTHORIZATION_FAILED"
    message = "Insufficient permissions"


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"


class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"
