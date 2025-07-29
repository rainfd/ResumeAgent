"""Logging configuration and utilities."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ..config import get_settings


def configure_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    enable_console: bool = True
) -> None:
    """Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_console: Whether to enable console logging
    """
    settings = get_settings()
    
    # Remove default logger
    logger.remove()
    
    # Use provided values or fall back to settings
    level = log_level or settings.log_level
    file_path = log_file or settings.log_file
    
    # Console logging
    if enable_console:
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # File logging
    if file_path:
        # Ensure log directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(file_path),
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="1 month",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )


def get_logger(name: str):
    """Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


# Security-aware logging functions
def log_safe(message: str, level: str = "INFO", **kwargs) -> None:
    """Log a message safely, filtering out sensitive information.
    
    Args:
        message: Log message
        level: Log level
        **kwargs: Additional context
    """
    # Filter sensitive keys
    sensitive_keys = {
        "password", "token", "key", "secret", "api_key", 
        "auth", "credential", "authorization"
    }
    
    filtered_kwargs = {}
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered_kwargs[key] = "[REDACTED]"
        else:
            filtered_kwargs[key] = value
    
    log_func = getattr(logger, level.lower(), logger.info)
    if filtered_kwargs:
        log_func(f"{message} | Context: {filtered_kwargs}")
    else:
        log_func(message)


def log_error_with_context(
    error: Exception, 
    context: str = "", 
    extra: Optional[dict] = None
) -> None:
    """Log an error with additional context.
    
    Args:
        error: Exception instance
        context: Additional context string
        extra: Extra context data
    """
    message = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
    
    if extra:
        log_safe(message, "ERROR", **extra)
    else:
        logger.error(message)
    
    # Log stack trace for debugging
    logger.debug(f"Stack trace for error in {context}", exc_info=error)