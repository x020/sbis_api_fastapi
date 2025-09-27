"""
Logging configuration and utilities.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

from config.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Setup structured logging for the application."""
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.logging.file_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog processors
    processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add appropriate final processor based on format
    if settings.logging.format.upper() == "JSON":
        processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format="%(message)s",
        stream=sys.stdout,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.logging.file_path)
        ]
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for application logs."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = log_record.get("timestamp", "")

        # Add service information
        log_record["service"] = "sbis-api-fastapi"
        log_record["version"] = "1.0.0"
        log_record["environment"] = settings.environment

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id


def configure_request_logging() -> None:
    """Configure logging for request/response cycle."""
    # Create a custom filter to add request context
    class RequestContextFilter(logging.Filter):
        """Filter to add request context to log records."""

        def filter(self, record: logging.LogRecord) -> bool:
            # Add request ID from thread local or request context
            # This would be set by middleware
            record.request_id = getattr(record, "request_id", "unknown")
            return True

    # Apply filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(RequestContextFilter())


def log_request_middleware(request: Any, call_next: Any) -> Any:
    """
    Middleware function to log HTTP requests.

    Args:
        request: FastAPI request object
        call_next: Next middleware function

    Returns:
        Response object
    """
    import time
    import uuid

    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Add request ID to request state
    request.state.request_id = request_id

    # Create logger with request context
    logger = get_logger("api.request")
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else "unknown",
        request_id=request_id
    )

    try:
        response = call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log successful request
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
            request_id=request_id
        )

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        # Calculate processing time
        process_time = time.time() - start_time

        # Log failed request
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=f"{process_time:.3f}s",
            request_id=request_id,
            exc_info=True
        )

        raise


def log_saby_api_call(logger: structlog.stdlib.BoundLogger, method: str, params: Dict[str, Any], **kwargs: Any) -> None:
    """
    Log Saby API calls with structured data.

    Args:
        logger: Logger instance
        method: API method name
        params: API parameters
        **kwargs: Additional context
    """
    # Remove sensitive data from params for logging
    safe_params = _sanitize_params(params)

    logger.info(
        "Saby API call",
        method=method,
        params=safe_params,
        **kwargs
    )


def log_saby_api_response(logger: structlog.stdlib.BoundLogger, method: str, success: bool, **kwargs: Any) -> None:
    """
    Log Saby API responses.

    Args:
        logger: Logger instance
        method: API method name
        success: Whether the call was successful
        **kwargs: Additional context
    """
    if success:
        logger.info("Saby API call successful", method=method, **kwargs)
    else:
        logger.error("Saby API call failed", method=method, **kwargs)


def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive data from parameters for logging.

    Args:
        params: Original parameters

    Returns:
        Sanitized parameters
    """
    sensitive_keys = {
        "app_secret", "secret_key", "password", "token", "access_token",
        "Пароль", "СекретныйКлюч", "Токен"
    }

    def sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [sanitize_value(item) for item in value]
        elif isinstance(value, str) and any(key.lower() in value.lower() for key in sensitive_keys):
            return "***REDACTED***"
        return value

    return sanitize_value(params)


def log_performance(logger: structlog.stdlib.BoundLogger, operation: str, duration: float, **kwargs: Any) -> None:
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional context
    """
    logger.info(
        "Performance metric",
        operation=operation,
        duration=f"{duration:.3f}s",
        **kwargs
    )


def log_security_event(logger: structlog.stdlib.BoundLogger, event: str, **kwargs: Any) -> None:
    """
    Log security-related events.

    Args:
        logger: Logger instance
        event: Security event type
        **kwargs: Additional context
    """
    logger.warning(
        "Security event",
        event=event,
        **kwargs
    )


def log_business_event(logger: structlog.stdlib.BoundLogger, event: str, **kwargs: Any) -> None:
    """
    Log business logic events.

    Args:
        logger: Logger instance
        event: Business event type
        **kwargs: Additional context
    """
    logger.info(
        "Business event",
        event=event,
        **kwargs
    )