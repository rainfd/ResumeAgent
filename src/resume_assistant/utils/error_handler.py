"""Error handling utilities and decorators."""

import functools
import traceback
from typing import Any, Callable, Optional, Type, Union

from rich.console import Console
from rich.panel import Panel

from .errors import (
    ResumeAssistantError, 
    ErrorSeverity, 
    get_error_severity, 
    format_error_message
)
from .logging import get_logger, log_error_with_context

logger = get_logger(__name__)


class ErrorHandler:
    """Centralized error handler for the application."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def handle_error(
        self, 
        error: Exception, 
        context: str = "",
        show_to_user: bool = True
    ) -> None:
        """Handle an error with appropriate logging and user feedback.
        
        Args:
            error: Exception instance
            context: Additional context string
            show_to_user: Whether to show error to user in UI
        """
        # Log the error
        log_error_with_context(error, context)
        
        # Show to user if requested
        if show_to_user:
            self._show_error_to_user(error, context)
    
    def _show_error_to_user(self, error: Exception, context: str = "") -> None:
        """Display error message to user in a formatted way.
        
        Args:
            error: Exception instance  
            context: Additional context string
        """
        severity = get_error_severity(error)
        message = format_error_message(error, include_context=False)
        
        # Choose color based on severity
        color_map = {
            ErrorSeverity.LOW: "yellow",
            ErrorSeverity.MEDIUM: "bright_yellow",
            ErrorSeverity.HIGH: "red",
            ErrorSeverity.CRITICAL: "bold red"
        }
        color = color_map.get(severity, "red")
        
        # Create error panel
        title = f"错误 - {severity.upper()}"
        if context:
            full_message = f"{message}\n\n上下文: {context}"
        else:
            full_message = message
        
        panel = Panel(
            full_message,
            title=title,
            border_style=color,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def handle_network_error(self, error: Exception, url: str = "") -> None:
        """Handle network-specific errors.
        
        Args:
            error: Exception instance
            url: URL that caused the error
        """
        context = f"网络请求失败"
        if url:
            context += f" (URL: {url})"
        
        self.handle_error(error, context)
        
        # Show recovery suggestions
        self.console.print("\n💡 [yellow]建议解决方案:[/yellow]")
        self.console.print("  • 检查网络连接")
        self.console.print("  • 验证URL是否正确")  
        self.console.print("  • 稍后重试")
    
    def handle_ai_service_error(self, error: Exception, service: str = "") -> None:
        """Handle AI service specific errors.
        
        Args:
            error: Exception instance
            service: AI service name
        """
        context = f"AI服务调用失败"
        if service:
            context += f" ({service})"
        
        self.handle_error(error, context)
        
        # Show recovery suggestions
        self.console.print("\n💡 [yellow]建议解决方案:[/yellow]")
        self.console.print("  • 检查API密钥配置")
        self.console.print("  • 验证API配额和权限")
        self.console.print("  • 检查网络连接")
    
    def handle_file_error(self, error: Exception, file_path: str = "") -> None:
        """Handle file operation errors.
        
        Args:
            error: Exception instance
            file_path: File path that caused the error
        """
        context = f"文件操作失败"
        if file_path:
            context += f" (文件: {file_path})"
        
        self.handle_error(error, context)
        
        # Show recovery suggestions
        self.console.print("\n💡 [yellow]建议解决方案:[/yellow]")
        self.console.print("  • 检查文件是否存在")
        self.console.print("  • 验证文件权限")
        self.console.print("  • 确认文件格式正确")


def handle_exceptions(
    error_types: Union[Type[Exception], tuple] = Exception,
    context: str = "",
    reraise: bool = False,
    default_return: Any = None
):
    """Decorator for handling exceptions in functions.
    
    Args:
        error_types: Exception types to catch
        context: Context string for error reporting
        reraise: Whether to reraise the exception after handling
        default_return: Default return value on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                # Create error handler instance
                handler = ErrorHandler()
                
                # Handle the error
                func_context = context or f"函数 {func.__name__}"
                handler.handle_error(e, func_context)
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def handle_async_exceptions(
    error_types: Union[Type[Exception], tuple] = Exception,
    context: str = "",
    reraise: bool = False,
    default_return: Any = None
):
    """Decorator for handling exceptions in async functions.
    
    Args:
        error_types: Exception types to catch
        context: Context string for error reporting
        reraise: Whether to reraise the exception after handling
        default_return: Default return value on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                # Create error handler instance
                handler = ErrorHandler()
                
                # Handle the error
                func_context = context or f"异步函数 {func.__name__}"
                handler.handle_error(e, func_context)
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


# Global error handler instance
error_handler = ErrorHandler()