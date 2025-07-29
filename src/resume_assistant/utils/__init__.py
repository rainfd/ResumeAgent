"""Utility modules for Resume Assistant."""

from .errors import (
    ResumeAssistantError,
    NetworkError,
    ParseError,
    AIServiceError,
    DatabaseError,
    ConfigurationError,
    ValidationError,
    ErrorSeverity,
    get_error_severity,
    format_error_message,
)
from .error_handler import (
    ErrorHandler,
    error_handler,
    handle_exceptions,
    handle_async_exceptions,
)
from .logging import (
    configure_logging,
    get_logger,
    log_safe,
    log_error_with_context,
)

__all__ = [
    # Errors
    "ResumeAssistantError",
    "NetworkError", 
    "ParseError",
    "AIServiceError",
    "DatabaseError",
    "ConfigurationError",
    "ValidationError",
    "ErrorSeverity",
    "get_error_severity",
    "format_error_message",
    # Error handling
    "ErrorHandler",
    "error_handler",
    "handle_exceptions",
    "handle_async_exceptions",
    # Logging
    "configure_logging",
    "get_logger",
    "log_safe",
    "log_error_with_context",
]