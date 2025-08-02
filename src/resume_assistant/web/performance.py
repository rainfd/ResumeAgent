"""性能监控和优化

集成异步处理、缓存管理和错误处理的统一性能优化系统。
"""

import streamlit as st
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import asyncio
import resource
import gc

from .async_utils import get_async_manager, run_async_operation_with_ui
from .cache_manager import get_cache_manager, schedule_cache_cleanup, st_cache
from .error_handler import get_error_handler, handle_errors, track_operation
from ..utils import get_logger

logger = get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    cache_hit_rate: float = 0.0
    cache_size_mb: float = 0.0
    active_operations: int = 0
    error_count: int = 0
    response_time_ms: float = 0.0
    session_count: int = 0

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history_points: int = 1000):
        self.max_history_points = max_history_points
        self.metrics_history: List[PerformanceMetrics] = []
        self.start_time = datetime.now()
        self.last_cleanup = datetime.now()
        
        # 性能阈值
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'cache_hit_rate': 0.5,  # 50%
            'response_time_ms': 5000.0,  # 5秒
            'error_rate': 0.1  # 10%
        }
        
        # 启动定期监控
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动后台监控"""
        def monitor_loop():
            while True:
                try:
                    metrics = self.collect_metrics()
                    self.add_metrics(metrics)
                    
                    # 检查性能阈值
                    self.check_performance_thresholds(metrics)
                    
                    # 自动优化
                    self.auto_optimize(metrics)
                    
                    time.sleep(30)  # 每30秒收集一次
                except Exception as e:
                    logger.error(f"Performance monitoring error: {e}")
                    time.sleep(60)  # 出错时等待更久
        
        # 在后台线程中运行监控
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            # 系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # 缓存指标
            cache_manager = get_cache_manager()
            cache_stats = cache_manager.get_stats()
            
            # 异步操作指标
            async_manager = get_async_manager()
            active_ops = len([op for op in async_manager.operations.values() 
                            if op.status == "running"])
            
            # 错误指标
            error_handler = get_error_handler()
            recent_errors = len([e for e in error_handler.get_error_history(50)
                               if (datetime.now() - e['timestamp']).seconds < 3600])
            
            # Session指标
            session_count = len(st.session_state) if hasattr(st, 'session_state') else 0
            
            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                cache_hit_rate=cache_stats.get('hit_rate', 0.0),
                cache_size_mb=cache_stats.get('size_mb', 0.0),
                active_operations=active_ops,
                error_count=recent_errors,
                session_count=session_count
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return PerformanceMetrics()
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """添加指标到历史记录"""
        self.metrics_history.append(metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > self.max_history_points:
            self.metrics_history = self.metrics_history[-self.max_history_points:]
    
    def check_performance_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        alerts = []
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")
        
        if metrics.cache_hit_rate < self.thresholds['cache_hit_rate']:
            alerts.append(f"缓存命中率过低: {metrics.cache_hit_rate:.1%}")
        
        if metrics.response_time_ms > self.thresholds['response_time_ms']:
            alerts.append(f"响应时间过长: {metrics.response_time_ms:.0f}ms")
        
        # 记录警告
        for alert in alerts:
            logger.warning(f"Performance alert: {alert}")
    
    def auto_optimize(self, metrics: PerformanceMetrics):
        """自动优化"""
        try:
            # 内存清理
            if metrics.memory_percent > 80:
                self._cleanup_memory()
            
            # 缓存清理
            if metrics.cache_size_mb > 50:  # 50MB
                cache_manager = get_cache_manager()
                cache_manager.cleanup_expired()
            
            # 错误历史清理
            if metrics.error_count > 100:
                error_handler = get_error_handler()
                error_handler.clear_error_history()
                
        except Exception as e:
            logger.error(f"Auto optimization failed: {e}")
    
    def _cleanup_memory(self):
        """清理内存"""
        # 强制垃圾回收
        gc.collect()
        
        # 清理缓存
        cache_manager = get_cache_manager()
        cleaned = cache_manager.cleanup_expired()
        
        if cleaned > 0:
            logger.info(f"Memory cleanup: removed {cleaned} cache entries")
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        return self.collect_metrics()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {}
        
        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'max_cpu_percent': max(m.cpu_percent for m in recent_metrics),
            'avg_memory_mb': sum(m.memory_mb for m in recent_metrics) / len(recent_metrics),
            'max_memory_mb': max(m.memory_mb for m in recent_metrics),
            'avg_cache_hit_rate': sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
            'total_operations': sum(m.active_operations for m in recent_metrics),
            'total_errors': sum(m.error_count for m in recent_metrics),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }

class OptimizedOperation:
    """优化的操作执行器"""
    
    @staticmethod
    def execute_with_caching(
        func: Callable,
        cache_key: str,
        ttl_seconds: int = 3600,
        *args,
        **kwargs
    ) -> Any:
        """带缓存的执行"""
        cache_manager = get_cache_manager()
        
        # 尝试从缓存获取
        result = cache_manager.get(cache_key)
        if result is not None:
            return result
        
        # 执行函数
        with st.spinner("处理中..."):
            result = func(*args, **kwargs)
        
        # 缓存结果
        cache_manager.set(cache_key, result, ttl_seconds)
        
        return result
    
    @staticmethod
    def execute_async_with_ui(
        func: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """带UI的异步执行"""
        return run_async_operation_with_ui(
            func=func,
            operation_name=operation_name,
            operation_description=f"执行 {operation_name}",
            *args,
            **kwargs
        )
    
    @staticmethod
    @handle_errors(user_message="操作执行失败，请稍后重试")
    @track_operation("优化操作执行")
    def execute_safe(func: Callable, *args, **kwargs) -> Any:
        """安全执行（带错误处理）"""
        return func(*args, **kwargs)

# 全局监控器
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

# 性能装饰器
def optimize_performance(
    cache_ttl: Optional[int] = None,
    async_execution: bool = False,
    track_metrics: bool = True
):
    """性能优化装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # 缓存执行
                if cache_ttl:
                    cache_manager = get_cache_manager()
                    cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
                    
                    result = cache_manager.get(cache_key)
                    if result is not None:
                        return result
                
                # 异步执行
                if async_execution:
                    result = run_async_operation_with_ui(
                        func=func,
                        operation_name=func.__name__,
                        operation_description=f"执行 {func.__name__}",
                        *args,
                        **kwargs
                    )
                else:
                    result = func(*args, **kwargs)
                
                # 缓存结果
                if cache_ttl:
                    cache_manager.set(cache_key, result, cache_ttl)
                
                # 记录性能指标
                if track_metrics:
                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # 毫秒
                    
                    monitor = get_performance_monitor()
                    metrics = monitor.get_current_metrics()
                    metrics.response_time_ms = execution_time
                    monitor.add_metrics(metrics)
                
                return result
                
            except Exception as e:
                # 错误处理
                error_handler = get_error_handler()
                error_handler.handle_error(
                    error=e,
                    context=f"optimize_performance({func.__name__})"
                )
                raise
        
        return wrapper
    return decorator

def display_performance_dashboard():
    """显示性能监控面板"""
    st.subheader("📊 性能监控")
    
    monitor = get_performance_monitor()
    current_metrics = monitor.get_current_metrics()
    summary = monitor.get_metrics_summary(24)
    
    # 实时指标
    st.write("**实时指标**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "CPU使用率",
            f"{current_metrics.cpu_percent:.1f}%",
            delta=f"{current_metrics.cpu_percent - summary.get('avg_cpu_percent', 0):.1f}%" if summary else None
        )
    
    with col2:
        st.metric(
            "内存使用",
            f"{current_metrics.memory_mb:.0f}MB",
            delta=f"{current_metrics.memory_mb - summary.get('avg_memory_mb', 0):.0f}MB" if summary else None
        )
    
    with col3:
        st.metric(
            "缓存命中率",
            f"{current_metrics.cache_hit_rate:.1%}",
            delta=f"{current_metrics.cache_hit_rate - summary.get('avg_cache_hit_rate', 0):.1%}" if summary else None
        )
    
    with col4:
        st.metric(
            "活跃操作",
            current_metrics.active_operations
        )
    
    st.divider()
    
    # 24小时摘要
    if summary:
        st.write("**24小时摘要**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均CPU", f"{summary['avg_cpu_percent']:.1f}%")
            st.metric("峰值CPU", f"{summary['max_cpu_percent']:.1f}%")
        
        with col2:
            st.metric("平均内存", f"{summary['avg_memory_mb']:.0f}MB")
            st.metric("峰值内存", f"{summary['max_memory_mb']:.0f}MB")
        
        with col3:
            st.metric("总操作数", summary['total_operations'])
            st.metric("总错误数", summary['total_errors'])
        
        with col4:
            st.metric("运行时间", f"{summary['uptime_hours']:.1f}小时")
            st.metric("缓存命中率", f"{summary['avg_cache_hit_rate']:.1%}")
    
    st.divider()
    
    # 性能图表
    if len(monitor.metrics_history) > 1:
        st.write("**性能趋势**")
        
        import pandas as pd
        
        # 准备数据
        df = pd.DataFrame([
            {
                'time': m.timestamp,
                'CPU%': m.cpu_percent,
                '内存MB': m.memory_mb,
                '缓存命中率': m.cache_hit_rate * 100,
                '活跃操作': m.active_operations
            }
            for m in monitor.metrics_history[-100:]  # 最近100个点
        ])
        
        # 显示图表
        st.line_chart(df.set_index('time'))
    
    st.divider()
    
    # 优化操作
    st.write("**性能优化**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 清理缓存"):
            cache_manager = get_cache_manager()
            cleaned = cache_manager.cleanup_expired()
            st.success(f"清理了 {cleaned} 个过期缓存条目")
    
    with col2:
        if st.button("🗑️ 内存清理"):
            monitor._cleanup_memory()
            st.success("内存清理完成")
    
    with col3:
        if st.button("📊 重置统计"):
            monitor.metrics_history.clear()
            st.success("统计数据已重置")

# 工具函数
def measure_execution_time(func: Callable) -> Callable:
    """测量执行时间装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000
        logger.info(f"Function {func.__name__} executed in {execution_time:.2f}ms")
        
        return result
    
    return wrapper

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': psutil.version_info,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {}

# 初始化
def initialize_performance_system():
    """初始化性能系统"""
    try:
        # 启动性能监控
        get_performance_monitor()
        
        # 启动缓存清理
        schedule_cache_cleanup()
        
        logger.info("Performance system initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize performance system: {e}")

# 自动初始化
initialize_performance_system()