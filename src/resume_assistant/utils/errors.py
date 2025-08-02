"""Custom exception classes and error handling utilities."""

from typing import Any, Dict, Optional


class ResumeAssistantError(Exception):
    """Base exception class for Resume Assistant."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class NetworkError(ResumeAssistantError):
    """Network-related errors."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        context = {}
        if url:
            context["url"] = url
        if status_code:
            context["status_code"] = status_code
        
        super().__init__(message, "NETWORK_ERROR", context)


class ParseError(ResumeAssistantError):
    """Document parsing related errors."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        file_type: Optional[str] = None
    ):
        context = {}
        if file_path:
            context["file_path"] = file_path
        if file_type:
            context["file_type"] = file_type
        
        super().__init__(message, "PARSE_ERROR", context)


class AIServiceError(ResumeAssistantError):
    """AI service related errors."""
    
    def __init__(
        self, 
        message: str, 
        service: Optional[str] = None,
        api_error_code: Optional[str] = None
    ):
        context = {}
        if service:
            context["service"] = service
        if api_error_code:
            context["api_error_code"] = api_error_code
        
        super().__init__(message, "AI_SERVICE_ERROR", context)


class DatabaseError(ResumeAssistantError):
    """Database operation related errors."""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        table: Optional[str] = None
    ):
        context = {}
        if operation:
            context["operation"] = operation
        if table:
            context["table"] = table
        
        super().__init__(message, "DATABASE_ERROR", context)


class ConfigurationError(ResumeAssistantError):
    """Configuration related errors."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None
    ):
        context = {}
        if config_key:
            context["config_key"] = config_key
        
        super().__init__(message, "CONFIG_ERROR", context)


class ValidationError(ResumeAssistantError):
    """Data validation related errors."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        context = {}
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)
        
        super().__init__(message, "VALIDATION_ERROR", context)


class ResumeProcessingError(ResumeAssistantError):
    """Resume file processing related errors."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        operation: Optional[str] = None
    ):
        context = {}
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation
        
        super().__init__(message, "RESUME_PROCESSING_ERROR", context)


class UnsupportedFormatError(ResumeAssistantError):
    """Unsupported file format related errors."""
    
    def __init__(
        self, 
        message: str, 
        file_format: Optional[str] = None,
        supported_formats: Optional[list] = None
    ):
        context = {}
        if file_format:
            context["file_format"] = file_format
        if supported_formats:
            context["supported_formats"] = supported_formats
        
        super().__init__(message, "UNSUPPORTED_FORMAT_ERROR", context)


class ResumeParsingError(ResumeAssistantError):
    """Resume parsing related errors."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        parser_type: Optional[str] = None
    ):
        context = {}
        if file_path:
            context["file_path"] = file_path
        if parser_type:
            context["parser_type"] = parser_type
        
        super().__init__(message, "RESUME_PARSING_ERROR", context)


class AIAnalysisError(ResumeAssistantError):
    """AI Agent analysis related errors."""
    
    def __init__(
        self, 
        message: str, 
        agent_id: Optional[int] = None,
        agent_name: Optional[str] = None
    ):
        context = {}
        if agent_id:
            context["agent_id"] = agent_id
        if agent_name:
            context["agent_name"] = agent_name
        
        super().__init__(message, "AI_ANALYSIS_ERROR", context)


# Error severity levels
class ErrorSeverity:
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def get_error_severity(error: Exception) -> str:
    """Get error severity level based on exception type.
    
    Args:
        error: Exception instance
        
    Returns:
        Severity level string
    """
    if isinstance(error, (NetworkError, AIServiceError)):
        return ErrorSeverity.MEDIUM
    elif isinstance(error, (DatabaseError, ConfigurationError)):
        return ErrorSeverity.HIGH
    elif isinstance(error, (ParseError, ValidationError)):
        return ErrorSeverity.LOW
    else:
        return ErrorSeverity.MEDIUM


def format_error_message(error: Exception, include_context: bool = True) -> str:
    """Format error message for display.
    
    Args:
        error: Exception instance
        include_context: Whether to include context information
        
    Returns:
        Formatted error message
    """
    if isinstance(error, ResumeAssistantError):
        message = str(error)
        if include_context and error.context:
            context_str = ", ".join(f"{k}={v}" for k, v in error.context.items())
            message += f" ({context_str})"
        return message
    else:
        return f"Unexpected error: {str(error)}"