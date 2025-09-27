"""
Custom exception handlers and error definitions.
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models.schemas import ErrorResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAPIException(HTTPException):
    """Base exception for API errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.details = details


class SabyAPIError(BaseAPIException):
    """Exception for Saby CRM API errors."""

    def __init__(
        self,
        message: str,
        saby_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Saby CRM API Error: {message}",
            code="SABY_API_ERROR",
            details={"saby_code": saby_code, **(details or {})}
        )


class SabyAuthError(BaseAPIException):
    """Exception for Saby CRM authentication errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {message}",
            code="SABY_AUTH_ERROR",
            details=details
        )


class ValidationError(BaseAPIException):
    """Exception for data validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
            code="VALIDATION_ERROR",
            details=details
        )


class ConfigurationError(BaseAPIException):
    """Exception for configuration errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {message}",
            code="CONFIG_ERROR",
            details=details
        )


class RateLimitError(BaseAPIException):
    """Exception for rate limiting errors."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after, **(details or {})}
        )


async def saby_api_exception_handler(request: Request, exc: SabyAPIError) -> JSONResponse:
    """Handle Saby API errors."""
    logger.error(
        "Saby API error",
        extra={
            "error": exc.detail,
            "saby_code": exc.details.get("saby_code") if exc.details else None,
            "path": str(request.url.path),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.detail,
            code=exc.code,
            details=exc.details
        ))
    )


async def saby_auth_exception_handler(request: Request, exc: SabyAuthError) -> JSONResponse:
    """Handle Saby authentication errors."""
    logger.error(
        "Saby authentication error",
        extra={
            "error": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.detail,
            code=exc.code,
            details=exc.details
        ))
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(
        "Validation error",
        extra={
            "error": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.detail,
            code=exc.code,
            details=exc.details
        ))
    )


async def pydantic_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Pydantic validation error",
        extra={
            "errors": exc.errors(),
            "path": str(request.url.path),
            "method": request.method
        }
    )

    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(ErrorResponse(
            error="Validation failed",
            code="PYDANTIC_VALIDATION_ERROR",
            details={"validation_errors": error_details}
        ))
    )


async def configuration_exception_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    """Handle configuration errors."""
    logger.error(
        "Configuration error",
        extra={
            "error": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.detail,
            code=exc.code,
            details=exc.details
        ))
    )


async def rate_limit_exception_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handle rate limit errors."""
    logger.warning(
        "Rate limit exceeded",
        extra={
            "error": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.detail,
            code=exc.code,
            details=exc.details
        ))
    )

    if exc.details and exc.details.get("retry_after"):
        response.headers["Retry-After"] = str(exc.details["retry_after"])

    return response


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(
        "Unexpected error",
        extra={
            "error": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            details={"error_type": type(exc).__name__}
        ))
    )


def create_exception_handlers() -> Dict[type, Any]:
    """Create dictionary of exception handlers for FastAPI."""
    return {
        SabyAPIError: saby_api_exception_handler,
        SabyAuthError: saby_auth_exception_handler,
        ValidationError: validation_exception_handler,
        RequestValidationError: pydantic_validation_exception_handler,
        ConfigurationError: configuration_exception_handler,
        RateLimitError: rate_limit_exception_handler,
        Exception: generic_exception_handler,
    }