"""Streamlit异步处理工具

提供异步操作支持、进度跟踪和操作取消功能。
"""

import asyncio
import threading
import time
from typing import Any, Callable, Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, Future
import streamlit as st
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from ..utils import get_logger

logger = get_logger(__name__)

@dataclass
class AsyncOperation:
    """异步操作描述"""
    id: str
    name: str
    description: str
    progress: float = 0.0
    status: str = "pending"  # pending, running, completed, cancelled, error
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration: Optional[float] = None  # 预估时长（秒）
    cancellable: bool = True
    steps: List[str] = field(default_factory=list)
    current_step: int = 0

    @property
    def duration(self) -> Optional[float]:
        """获取操作持续时间"""
        if self.start_time:
            end = self.end_time or datetime.now()
            return (end - self.start_time).total_seconds()
        return None

    @property
    def eta(self) -> Optional[float]:
        """估算剩余时间"""
        if self.progress > 0 and self.duration and self.status == "running":
            total_time = self.duration / self.progress
            return total_time - self.duration
        return self.estimated_duration

class AsyncOperationManager:
    """异步操作管理器"""
    
    def __init__(self):
        self.operations: Dict[str, AsyncOperation] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.futures: Dict[str, Future] = {}
        
    def create_operation(
        self,
        operation_id: str,
        name: str,
        description: str,
        steps: Optional[List[str]] = None,
        estimated_duration: Optional[float] = None,
        cancellable: bool = True
    ) -> AsyncOperation:
        """创建异步操作"""
        operation = AsyncOperation(
            id=operation_id,
            name=name,
            description=description,
            steps=steps or [],
            estimated_duration=estimated_duration,
            cancellable=cancellable
        )
        self.operations[operation_id] = operation
        logger.info(f"Created async operation: {name} (ID: {operation_id})")
        return operation
    
    def start_operation(
        self,
        operation_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> bool:
        """开始执行异步操作"""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return False
            
        operation = self.operations[operation_id]
        if operation.status == "running":
            logger.warning(f"Operation already running: {operation_id}")
            return False
            
        try:
            # 包装函数以更新进度
            def wrapped_func(*args, **kwargs):
                operation.status = "running"
                operation.start_time = datetime.now()
                try:
                    result = func(operation, *args, **kwargs)
                    operation.result = result
                    operation.status = "completed"
                    operation.progress = 1.0
                    return result
                except Exception as e:
                    operation.error = str(e)
                    operation.status = "error"
                    logger.error(f"Operation failed: {operation_id}, error: {e}")
                    raise
                finally:
                    operation.end_time = datetime.now()
            
            # 提交到线程池
            future = self.executor.submit(wrapped_func, *args, **kwargs)
            self.futures[operation_id] = future
            
            logger.info(f"Started async operation: {operation.name}")
            return True
            
        except Exception as e:
            operation.status = "error"
            operation.error = str(e)
            logger.error(f"Failed to start operation: {operation_id}, error: {e}")
            return False
    
    def cancel_operation(self, operation_id: str) -> bool:
        """取消异步操作"""
        if operation_id not in self.operations:
            return False
            
        operation = self.operations[operation_id]
        if not operation.cancellable or operation.status != "running":
            return False
            
        future = self.futures.get(operation_id)
        if future and future.cancel():
            operation.status = "cancelled"
            operation.end_time = datetime.now()
            logger.info(f"Cancelled operation: {operation.name}")
            return True
            
        return False
    
    def get_operation(self, operation_id: str) -> Optional[AsyncOperation]:
        """获取操作状态"""
        return self.operations.get(operation_id)
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """清理已完成的操作"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for op_id, operation in self.operations.items():
            if (operation.status in ["completed", "cancelled", "error"] and 
                operation.end_time and operation.end_time < cutoff):
                to_remove.append(op_id)
        
        for op_id in to_remove:
            del self.operations[op_id]
            if op_id in self.futures:
                del self.futures[op_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old operations")

# 全局异步操作管理器
_async_manager = None

def get_async_manager() -> AsyncOperationManager:
    """获取全局异步操作管理器"""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncOperationManager()
    return _async_manager

class AsyncProgressTracker:
    """异步进度跟踪器"""
    
    def __init__(self, operation: AsyncOperation):
        self.operation = operation
        
    def update_progress(self, progress: float, step_description: Optional[str] = None):
        """更新进度"""
        self.operation.progress = min(1.0, max(0.0, progress))
        if step_description:
            # 如果有步骤描述，添加到步骤列表中
            if step_description not in self.operation.steps:
                self.operation.steps.append(step_description)
                self.operation.current_step = len(self.operation.steps) - 1
        
    def next_step(self, step_description: str, progress: Optional[float] = None):
        """进入下一步"""
        if step_description not in self.operation.steps:
            self.operation.steps.append(step_description)
        self.operation.current_step = len(self.operation.steps) - 1
        
        if progress is not None:
            self.update_progress(progress)
        elif self.operation.steps:
            # 自动计算进度
            auto_progress = (self.operation.current_step + 1) / len(self.operation.steps)
            self.update_progress(auto_progress)

def create_progress_display(operation_id: str) -> tuple:
    """创建进度显示组件
    
    Returns:
        tuple: (progress_bar, status_text, cancel_button_container)
    """
    manager = get_async_manager()
    operation = manager.get_operation(operation_id)
    
    if not operation:
        st.error(f"操作不存在: {operation_id}")
        return None, None, None
    
    # 创建进度显示区域
    progress_container = st.container()
    
    with progress_container:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 进度条
            progress_bar = st.progress(operation.progress)
            
            # 状态文本
            status_text = st.empty()
            
            # 显示当前状态
            if operation.status == "pending":
                status_text.info(f"⏳ 准备中: {operation.description}")
            elif operation.status == "running":
                current_step = ""
                if operation.steps and operation.current_step < len(operation.steps):
                    current_step = f" - {operation.steps[operation.current_step]}"
                
                eta_text = ""
                if operation.eta:
                    eta_text = f" (预计剩余: {operation.eta:.1f}秒)"
                
                status_text.info(f"🔄 执行中: {operation.description}{current_step}{eta_text}")
            elif operation.status == "completed":
                status_text.success(f"✅ 完成: {operation.description}")
            elif operation.status == "cancelled":
                status_text.warning(f"⚠️ 已取消: {operation.description}")
            elif operation.status == "error":
                status_text.error(f"❌ 错误: {operation.error}")
        
        with col2:
            # 取消按钮
            cancel_container = st.empty()
            if operation.cancellable and operation.status == "running":
                if cancel_container.button("🛑 取消", key=f"cancel_{operation_id}"):
                    manager.cancel_operation(operation_id)
                    st.rerun()
            
    return progress_bar, status_text, cancel_container

def with_async_operation(
    operation_name: str,
    operation_description: str,
    steps: Optional[List[str]] = None,
    estimated_duration: Optional[float] = None,
    auto_display: bool = True
):
    """装饰器：将函数包装为异步操作"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成操作ID
            import uuid
            operation_id = f"op_{uuid.uuid4().hex[:8]}"
            
            # 创建操作
            manager = get_async_manager()
            operation = manager.create_operation(
                operation_id=operation_id,
                name=operation_name,
                description=operation_description,
                steps=steps,
                estimated_duration=estimated_duration
            )
            
            # 如果启用自动显示，创建进度显示
            if auto_display:
                progress_bar, status_text, cancel_container = create_progress_display(operation_id)
            
            # 包装原函数以支持进度跟踪
            def wrapped_func(operation, *args, **kwargs):
                tracker = AsyncProgressTracker(operation)
                return func(tracker, *args, **kwargs)
            
            # 开始执行
            if manager.start_operation(operation_id, wrapped_func, *args, **kwargs):
                # 等待完成或定期更新UI
                while operation.status == "running":
                    time.sleep(0.1)
                    if auto_display:
                        # 更新进度显示
                        if progress_bar:
                            progress_bar.progress(operation.progress)
                        # 刷新页面以更新状态
                        st.rerun()
                
                # 返回结果
                if operation.status == "completed":
                    return operation.result
                elif operation.status == "error":
                    st.error(f"操作失败: {operation.error}")
                    return None
                elif operation.status == "cancelled":
                    st.warning("操作已被取消")
                    return None
            else:
                st.error("无法启动异步操作")
                return None
                
        return wrapper
    return decorator

def run_async_operation_with_ui(
    func: Callable,
    operation_name: str,
    operation_description: str,
    steps: Optional[List[str]] = None,
    estimated_duration: Optional[float] = None,
    *args,
    **kwargs
) -> Any:
    """运行异步操作并显示UI
    
    Args:
        func: 要执行的函数，第一个参数应该是AsyncProgressTracker
        operation_name: 操作名称
        operation_description: 操作描述
        steps: 操作步骤列表
        estimated_duration: 预估持续时间
        *args, **kwargs: 传递给func的参数
    
    Returns:
        操作结果
    """
    import uuid
    operation_id = f"op_{uuid.uuid4().hex[:8]}"
    
    # 创建操作
    manager = get_async_manager()
    operation = manager.create_operation(
        operation_id=operation_id,
        name=operation_name,
        description=operation_description,
        steps=steps,
        estimated_duration=estimated_duration
    )
    
    # 创建进度显示
    progress_container = st.container()
    
    with progress_container:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            progress_bar = st.progress(0.0)
            status_text = st.empty()
        
        with col2:
            cancel_button = st.empty()
    
    # 包装函数
    def wrapped_func(operation, *args, **kwargs):
        tracker = AsyncProgressTracker(operation)
        return func(tracker, *args, **kwargs)
    
    # 开始执行
    if manager.start_operation(operation_id, wrapped_func, *args, **kwargs):
        # 实时更新进度
        while operation.status == "running":
            # 更新进度条
            progress_bar.progress(operation.progress)
            
            # 更新状态文本
            current_step = ""
            if operation.steps and operation.current_step < len(operation.steps):
                current_step = f" - {operation.steps[operation.current_step]}"
            
            eta_text = ""
            if operation.eta:
                eta_text = f" (预计剩余: {operation.eta:.1f}秒)"
            
            status_text.info(f"🔄 {operation.description}{current_step}{eta_text}")
            
            # 显示取消按钮
            if operation.cancellable:
                if cancel_button.button("🛑 取消", key=f"cancel_{operation_id}"):
                    manager.cancel_operation(operation_id)
                    break
            
            time.sleep(0.1)
        
        # 显示最终状态
        if operation.status == "completed":
            progress_bar.progress(1.0)
            status_text.success(f"✅ 完成: {operation.description}")
            cancel_button.empty()
            return operation.result
        elif operation.status == "error":
            status_text.error(f"❌ 错误: {operation.error}")
            cancel_button.empty()
            return None
        elif operation.status == "cancelled":
            status_text.warning(f"⚠️ 已取消: {operation.description}")
            cancel_button.empty()
            return None
    else:
        st.error("无法启动异步操作")
        return None

# 工具函数
def is_operation_running(operation_id: str) -> bool:
    """检查操作是否正在运行"""
    manager = get_async_manager()
    operation = manager.get_operation(operation_id)
    return operation and operation.status == "running"

def get_operation_progress(operation_id: str) -> float:
    """获取操作进度"""
    manager = get_async_manager()
    operation = manager.get_operation(operation_id)
    return operation.progress if operation else 0.0

def cancel_all_operations():
    """取消所有运行中的操作"""
    manager = get_async_manager()
    cancelled = 0
    for op_id, operation in manager.operations.items():
        if operation.status == "running" and operation.cancellable:
            if manager.cancel_operation(op_id):
                cancelled += 1
    
    logger.info(f"Cancelled {cancelled} operations")
    return cancelled