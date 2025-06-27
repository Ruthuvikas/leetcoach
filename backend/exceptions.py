from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class LeetCoachException(Exception):
    """Base exception for LeetCoach application"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LeetCoachException):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(LeetCoachException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(LeetCoachException):
    """Raised when user is not authorized to perform an action"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class NotFoundError(LeetCoachException):
    """Raised when a resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class RateLimitError(LeetCoachException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class OpenAIError(LeetCoachException):
    """Raised when OpenAI API fails"""
    def __init__(self, message: str = "OpenAI service error"):
        super().__init__(message, status_code=503)


class DatabaseError(LeetCoachException):
    """Raised when database operations fail"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)


def handle_leetcoach_exception(exc: LeetCoachException) -> HTTPException:
    """Convert LeetCoachException to FastAPI HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.message,
            "details": exc.details
        }
    )


def handle_validation_error(exc: ValidationError) -> HTTPException:
    """Handle validation errors with detailed feedback"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.details
        }
    )


def handle_openai_error(exc: OpenAIError) -> HTTPException:
    """Handle OpenAI API errors"""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "AI Service Unavailable",
            "message": exc.message,
            "retry_after": 30  # Suggest retry after 30 seconds
        }
    )


def handle_rate_limit_error(exc: RateLimitError) -> HTTPException:
    """Handle rate limit errors"""
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate Limit Exceeded",
            "message": exc.message,
            "retry_after": 60  # Suggest retry after 1 minute
        }
    ) 