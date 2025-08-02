"""Web错误处理和用户反馈系统

提供统一的错误处理、用户通知和操作反馈机制。
"""

import streamlit as st
import traceback
import logging
from typing import Any, Callable, Optional, Dict, List, Union
from functools import wraps
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import inspect

from ..utils import get_logger
from ..utils.errors import ResumeAssistantError

logger = get_logger(__name__)

class NotificationType(Enum):
    """通知类型"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Notification:
    """通知消息"""
    message: str
    type: NotificationType
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[str] = None
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissible: bool = True
    auto_dismiss_seconds: Optional[int] = None

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    def handle_error(
        self,
        error: Exception,
        context: str = "",
        show_to_user: bool = True,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ) -> bool:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            show_to_user: 是否向用户显示
            user_message: 自定义用户消息
            suggestions: 解决建议
            
        Returns:
            是否成功处理
        """
        try:
            # 记录错误
            error_info = {
                'timestamp': datetime.now(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'traceback': traceback.format_exc(),
                'user_message': user_message,
                'suggestions': suggestions or []
            }
            
            self.error_history.append(error_info)
            
            # 限制历史记录大小
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
            
            # 记录日志
            logger.error(f"Error in {context}: {error}", exc_info=True)
            
            # 向用户显示错误
            if show_to_user:
                self._show_error_to_user(error, user_message, suggestions)
            
            return True
            
        except Exception as handler_error:
            logger.critical(f"Error handler failed: {handler_error}")
            # 备用错误显示
            if show_to_user:
                st.error("发生了未知错误，请稍后重试。")
            return False
    
    def _show_error_to_user(
        self,
        error: Exception,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """向用户显示错误"""
        
        # 确定显示的消息
        if user_message:
            display_message = user_message
        elif isinstance(error, ResumeAssistantError):
            display_message = error.user_message
        else:
            display_message = self._get_friendly_error_message(error)
        
        # 显示主要错误消息
        st.error(f"❌ {display_message}")
        
        # 显示建议（如果有）
        if suggestions:
            with st.expander("💡 解决建议"):
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # 显示详细错误信息（仅调试模式）
        if st.session_state.get('debug_mode', False):
            with st.expander("🔍 详细错误信息（调试）"):
                st.code(str(error))
                if hasattr(error, '__traceback__'):
                    st.code(traceback.format_exc())
    
    def _get_friendly_error_message(self, error: Exception) -> str:
        """获取用户友好的错误消息"""
        error_type = type(error).__name__
        
        friendly_messages = {
            'ConnectionError': '网络连接失败，请检查网络设置',
            'TimeoutError': '操作超时，请稍后重试',
            'FileNotFoundError': '文件未找到，请确认文件路径正确',
            'PermissionError': '没有足够的权限访问文件',
            'ValueError': '输入数据格式不正确',
            'KeyError': '缺少必要的数据项',
            'ImportError': '模块加载失败，请检查依赖',
            'AttributeError': '功能暂时不可用',
            'TypeError': '数据类型不匹配',
            'IndexError': '数据范围超出限制',
            'OSError': '系统操作失败',
            'IOError': '文件读写失败'
        }
        
        return friendly_messages.get(error_type, '发生了未知错误，请联系技术支持')
    
    def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取错误历史"""
        return self.error_history[-limit:]
    
    def clear_error_history(self):
        """清空错误历史"""
        self.error_history.clear()

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.max_notifications = 10
    
    def show_notification(
        self,
        message: str,
        type: NotificationType = NotificationType.INFO,
        details: Optional[str] = None,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        auto_dismiss_seconds: Optional[int] = None
    ):
        """显示通知"""
        notification = Notification(
            message=message,
            type=type,
            details=details,
            action_label=action_label,
            action_callback=action_callback,
            auto_dismiss_seconds=auto_dismiss_seconds
        )
        
        self.notifications.append(notification)
        
        # 限制通知数量
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        # 立即显示
        self._display_notification(notification)
    
    def _display_notification(self, notification: Notification):
        """显示单个通知"""
        # 根据类型选择显示方法
        if notification.type == NotificationType.SUCCESS:
            st.success(f"✅ {notification.message}")
        elif notification.type == NotificationType.ERROR:
            st.error(f"❌ {notification.message}")
        elif notification.type == NotificationType.WARNING:
            st.warning(f"⚠️ {notification.message}")
        else:
            st.info(f"ℹ️ {notification.message}")
        
        # 显示详细信息
        if notification.details:
            with st.expander("查看详情"):
                st.write(notification.details)
        
        # 显示操作按钮
        if notification.action_label and notification.action_callback:
            if st.button(notification.action_label, key=f"action_{id(notification)}"):
                try:
                    notification.action_callback()
                except Exception as e:
                    st.error(f"操作失败: {e}")
    
    def success(self, message: str, details: Optional[str] = None):
        """显示成功通知"""
        self.show_notification(message, NotificationType.SUCCESS, details)
    
    def error(self, message: str, details: Optional[str] = None):
        """显示错误通知"""
        self.show_notification(message, NotificationType.ERROR, details)
    
    def warning(self, message: str, details: Optional[str] = None):
        """显示警告通知"""
        self.show_notification(message, NotificationType.WARNING, details)
    
    def info(self, message: str, details: Optional[str] = None):
        """显示信息通知"""
        self.show_notification(message, NotificationType.INFO, details)

class OperationTracker:
    """操作跟踪器"""
    
    def __init__(self):
        self.operations: Dict[str, Dict[str, Any]] = {}
    
    def start_operation(self, operation_id: str, description: str):
        """开始操作"""
        self.operations[operation_id] = {
            'description': description,
            'start_time': datetime.now(),
            'status': 'running'
        }
        
        # 显示开始状态
        st.info(f"🔄 开始: {description}")
    
    def complete_operation(self, operation_id: str, success: bool = True, message: Optional[str] = None):
        """完成操作"""
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        operation['end_time'] = datetime.now()
        operation['status'] = 'success' if success else 'failed'
        operation['message'] = message
        
        # 计算耗时
        duration = (operation['end_time'] - operation['start_time']).total_seconds()
        
        # 显示完成状态
        if success:
            status_message = f"✅ 完成: {operation['description']}"
            if duration > 1:
                status_message += f" (耗时: {duration:.1f}秒)"
            if message:
                status_message += f" - {message}"
            st.success(status_message)
        else:
            error_message = f"❌ 失败: {operation['description']}"
            if message:
                error_message += f" - {message}"
            st.error(error_message)

# 全局实例
_error_handler = None
_notification_manager = None
_operation_tracker = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def get_notification_manager() -> NotificationManager:
    """获取全局通知管理器"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def get_operation_tracker() -> OperationTracker:
    """获取全局操作跟踪器"""
    global _operation_tracker
    if _operation_tracker is None:
        _operation_tracker = OperationTracker()
    return _operation_tracker

# 装饰器
def handle_errors(
    user_message: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    show_to_user: bool = True,
    return_on_error: Any = None
):
    """错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取函数上下文
                context = f"{func.__module__}.{func.__name__}"
                
                # 处理错误
                error_handler = get_error_handler()
                error_handler.handle_error(
                    error=e,
                    context=context,
                    show_to_user=show_to_user,
                    user_message=user_message,
                    suggestions=suggestions
                )
                
                return return_on_error
        
        return wrapper
    return decorator

def track_operation(description: str):
    """操作跟踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import uuid
            operation_id = f"op_{uuid.uuid4().hex[:8]}"
            
            tracker = get_operation_tracker()
            tracker.start_operation(operation_id, description)
            
            try:
                result = func(*args, **kwargs)
                tracker.complete_operation(operation_id, True)
                return result
            except Exception as e:
                tracker.complete_operation(operation_id, False, str(e))
                raise
        
        return wrapper
    return decorator

def with_confirmation(
    message: str,
    confirm_button: str = "确认",
    cancel_button: str = "取消"
):
    """确认对话框装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成唯一键
            func_key = f"confirm_{func.__name__}_{id(args)}"
            
            if not st.session_state.get(f"{func_key}_confirmed", False):
                st.warning(f"⚠️ {message}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ {confirm_button}", key=f"{func_key}_confirm"):
                        st.session_state[f"{func_key}_confirmed"] = True
                        st.rerun()
                
                with col2:
                    if st.button(f"❌ {cancel_button}", key=f"{func_key}_cancel"):
                        return None
                
                return None
            else:
                # 重置确认状态
                st.session_state[f"{func_key}_confirmed"] = False
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# 工具函数
def safe_execute(
    func: Callable,
    *args,
    error_message: str = "操作失败",
    success_message: Optional[str] = None,
    **kwargs
) -> Any:
    """安全执行函数"""
    try:
        result = func(*args, **kwargs)
        if success_message:
            get_notification_manager().success(success_message)
        return result
    except Exception as e:
        get_error_handler().handle_error(
            error=e,
            context=f"safe_execute({func.__name__})",
            user_message=error_message
        )
        return None

def validate_input(
    value: Any,
    validators: List[Callable[[Any], bool]],
    error_messages: List[str]
) -> bool:
    """验证输入"""
    for validator, error_msg in zip(validators, error_messages):
        if not validator(value):
            st.error(f"❌ {error_msg}")
            return False
    return True

def show_loading_state(message: str = "处理中..."):
    """显示加载状态"""
    return st.spinner(message)

def display_error_management():
    """显示错误管理界面"""
    st.subheader("🚨 错误管理")
    
    error_handler = get_error_handler()
    
    # 错误历史统计
    errors = error_handler.get_error_history()
    
    if errors:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("错误总数", len(errors))
        
        with col2:
            recent_errors = [e for e in errors if (datetime.now() - e['timestamp']).seconds < 3600]
            st.metric("最近1小时", len(recent_errors))
        
        with col3:
            error_types = {}
            for error in errors:
                error_type = error['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            most_common = max(error_types.items(), key=lambda x: x[1]) if error_types else ("无", 0)
            st.metric("最常见错误", f"{most_common[0]} ({most_common[1]})")
        
        st.divider()
        
        # 操作按钮
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清空错误历史"):
                error_handler.clear_error_history()
                st.success("错误历史已清空")
                st.rerun()
        
        with col2:
            if st.button("📊 显示详细信息"):
                st.session_state.show_error_details = not st.session_state.get('show_error_details', False)
        
        # 详细错误信息
        if st.session_state.get('show_error_details', False):
            st.divider()
            st.subheader("📋 错误详情")
            
            import pandas as pd
            df = pd.DataFrame(errors)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 显示表格
            st.dataframe(
                df[['timestamp', 'error_type', 'error_message', 'context']],
                use_container_width=True
            )
            
            # 显示详细错误
            if st.selectbox("选择错误查看详情", range(len(errors)), format_func=lambda i: f"{errors[i]['timestamp'].strftime('%H:%M:%S')} - {errors[i]['error_type']}"):
                selected_error = errors[st.session_state.get('selected_error_index', 0)]
                
                st.code(selected_error['traceback'])
                
                if selected_error['suggestions']:
                    st.write("**建议解决方案:**")
                    for suggestion in selected_error['suggestions']:
                        st.write(f"• {suggestion}")
    else:
        st.info("暂无错误记录")

# 上下文管理器
class ErrorContext:
    """错误上下文管理器"""
    
    def __init__(self, operation_name: str, user_message: Optional[str] = None):
        self.operation_name = operation_name
        self.user_message = user_message
        self.error_handler = get_error_handler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(
                error=exc_val,
                context=self.operation_name,
                user_message=self.user_message
            )
            return True  # 抑制异常
        return False

# 快捷函数
def notify_success(message: str, details: Optional[str] = None):
    """快捷成功通知"""
    get_notification_manager().success(message, details)

def notify_error(message: str, details: Optional[str] = None):
    """快捷错误通知"""
    get_notification_manager().error(message, details)

def notify_warning(message: str, details: Optional[str] = None):
    """快捷警告通知"""
    get_notification_manager().warning(message, details)

def notify_info(message: str, details: Optional[str] = None):
    """快捷信息通知"""
    get_notification_manager().info(message, details)