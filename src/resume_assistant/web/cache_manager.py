"""Cache Management for Streamlit Web Interface."""

import streamlit as st
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import json

from ..utils import get_logger

logger = get_logger(__name__)

class CacheManager:
    """Streamlit缓存管理器"""
    
    @staticmethod
    def get_cache_key(prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转换为字符串并生成哈希
        data = {
            'args': args,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()[:19]  # 精确到秒
        }
        content = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.md5(content.encode())
        return f"{prefix}_{hash_obj.hexdigest()[:8]}"
    
    @staticmethod
    @st.cache_data(ttl=300)  # 5分钟缓存
    def cache_job_scraping_result(url: str, scraper_func: Callable) -> Dict[str, Any]:
        """缓存职位爬取结果"""
        try:
            logger.info(f"Cache miss for job scraping: {url}")
            return scraper_func(url)
        except Exception as e:
            logger.error(f"Cache job scraping error: {e}")
            return {}
    
    @staticmethod
    @st.cache_data(ttl=600)  # 10分钟缓存
    def cache_resume_parsing_result(file_content: bytes, file_type: str, parser_func: Callable) -> Dict[str, Any]:
        """缓存简历解析结果"""
        try:
            # 为文件内容生成哈希作为缓存键的一部分
            content_hash = hashlib.md5(file_content).hexdigest()
            logger.info(f"Cache miss for resume parsing: {file_type}_{content_hash[:8]}")
            return parser_func(file_content, file_type)
        except Exception as e:
            logger.error(f"Cache resume parsing error: {e}")
            return {}
    
    @staticmethod
    @st.cache_data(ttl=1800)  # 30分钟缓存
    def cache_ai_analysis_result(resume_id: str, job_id: str, analysis_func: Callable) -> Dict[str, Any]:
        """缓存AI分析结果"""
        try:
            cache_key = f"analysis_{resume_id}_{job_id}"
            logger.info(f"Cache miss for AI analysis: {cache_key}")
            return analysis_func()
        except Exception as e:
            logger.error(f"Cache AI analysis error: {e}")
            return {}
    
    @staticmethod
    @st.cache_data(ttl=900)  # 15分钟缓存
    def cache_greeting_generation(job_data: str, resume_data: str, generation_func: Callable) -> List[str]:
        """缓存打招呼语生成结果"""
        try:
            # 为数据生成哈希
            combined_data = f"{job_data}_{resume_data}"
            data_hash = hashlib.md5(combined_data.encode()).hexdigest()
            logger.info(f"Cache miss for greeting generation: {data_hash[:8]}")
            return generation_func()
        except Exception as e:
            logger.error(f"Cache greeting generation error: {e}")
            return []
    
    @staticmethod
    def clear_cache(cache_type: str = "all"):
        """清除缓存"""
        try:
            if cache_type == "all":
                st.cache_data.clear()
                logger.info("All cache cleared")
            else:
                # 这里可以添加特定类型的缓存清除逻辑
                logger.info(f"Cache type {cache_type} clearing not implemented")
            
            # 添加通知
            if 'notifications' not in st.session_state:
                st.session_state.notifications = []
            
            st.session_state.notifications.append({
                'type': 'success',
                'message': f'缓存已清除: {cache_type}',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Clear cache error: {e}")
            if 'notifications' not in st.session_state:
                st.session_state.notifications = []
            
            st.session_state.notifications.append({
                'type': 'error',
                'message': f'清除缓存失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            # Streamlit缓存统计（这是一个模拟，实际API可能不同）
            stats = {
                'total_cached_functions': 4,
                'cache_hit_rate': 0.75,  # 模拟75%的命中率
                'total_cache_size': '2.3 MB',  # 模拟缓存大小
                'last_cleared': st.session_state.get('last_cache_clear', '未清除'),
                'cache_enabled': True
            }
            return stats
        except Exception as e:
            logger.error(f"Get cache stats error: {e}")
            return {
                'error': str(e),
                'cache_enabled': False
            }
    
    @staticmethod
    def render_cache_management_panel():
        """渲染缓存管理面板"""
        st.subheader("🗄️ 缓存管理")
        
        # 获取缓存统计
        stats = CacheManager.get_cache_stats()
        
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("缓存函数数量", stats.get('total_cached_functions', 0))
        
        with col2:
            hit_rate = stats.get('cache_hit_rate', 0)
            st.metric("命中率", f"{hit_rate * 100:.1f}%")
        
        with col3:
            st.metric("缓存大小", stats.get('total_cache_size', '0 MB'))
        
        # 缓存控制
        st.markdown("### 缓存控制")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ 清除全部缓存", type="secondary"):
                CacheManager.clear_cache("all")
                st.session_state.last_cache_clear = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.rerun()
        
        with col2:
            if st.button("📊 刷新统计", type="secondary"):
                st.rerun()
        
        with col3:
            cache_enabled = st.checkbox("启用缓存", value=stats.get('cache_enabled', True))
        
        # 缓存详情
        with st.expander("📋 缓存详情"):
            st.json(stats)
    
    @staticmethod
    def setup_cache_config():
        """设置缓存配置"""
        # 在应用启动时调用此函数来配置缓存
        # 这里可以设置全局缓存参数
        if 'cache_config' not in st.session_state:
            st.session_state.cache_config = {
                'job_scraping_ttl': 300,
                'resume_parsing_ttl': 600,
                'ai_analysis_ttl': 1800,
                'greeting_generation_ttl': 900,
                'max_cache_size': '50MB',
                'auto_clear_enabled': True,
                'auto_clear_interval': 3600  # 1小时
            }
        
        logger.info("Cache configuration initialized")

class PerformanceMonitor:
    """性能监控器"""
    
    @staticmethod
    def track_operation_time(operation_name: str):
        """装饰器：跟踪操作时间"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 记录成功操作
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    PerformanceMonitor._record_performance(operation_name, duration, True)
                    
                    return result
                    
                except Exception as e:
                    # 记录失败操作
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    PerformanceMonitor._record_performance(operation_name, duration, False, str(e))
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def _record_performance(operation: str, duration: float, success: bool, error: str = None):
        """记录性能数据"""
        if 'performance_data' not in st.session_state:
            st.session_state.performance_data = []
        
        record = {
            'operation': operation,
            'duration': duration,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        st.session_state.performance_data.append(record)
        
        # 只保留最近100条记录
        if len(st.session_state.performance_data) > 100:
            st.session_state.performance_data = st.session_state.performance_data[-100:]
        
        logger.info(f"Performance recorded: {operation} - {duration:.2f}s - {'Success' if success else 'Failed'}")
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """获取性能摘要"""
        if 'performance_data' not in st.session_state:
            return {'total_operations': 0}
        
        data = st.session_state.performance_data
        
        if not data:
            return {'total_operations': 0}
        
        # 计算统计信息
        total_ops = len(data)
        success_ops = sum(1 for record in data if record['success'])
        success_rate = success_ops / total_ops if total_ops > 0 else 0
        
        durations = [record['duration'] for record in data if record['success']]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 按操作类型分组
        operations = {}
        for record in data:
            op_name = record['operation']
            if op_name not in operations:
                operations[op_name] = {'count': 0, 'avg_duration': 0, 'success_rate': 0}
            
            operations[op_name]['count'] += 1
        
        return {
            'total_operations': total_ops,
            'success_rate': success_rate,
            'average_duration': avg_duration,
            'operations_breakdown': operations,
            'recent_errors': [record for record in data[-10:] if not record['success']]
        }
    
    @staticmethod
    def render_performance_panel():
        """渲染性能监控面板"""
        st.subheader("📈 性能监控")
        
        summary = PerformanceMonitor.get_performance_summary()
        
        if summary['total_operations'] == 0:
            st.info("还没有性能数据记录")
            return
        
        # 显示关键指标
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总操作数", summary['total_operations'])
        
        with col2:
            success_rate = summary['success_rate'] * 100
            st.metric("成功率", f"{success_rate:.1f}%")
        
        with col3:
            avg_duration = summary['average_duration']
            st.metric("平均耗时", f"{avg_duration:.2f}s")
        
        # 操作分解
        if summary['operations_breakdown']:
            st.markdown("### 操作分解")
            
            import pandas as pd
            ops_data = []
            for op_name, op_data in summary['operations_breakdown'].items():
                ops_data.append({
                    '操作': op_name,
                    '次数': op_data['count'],
                    '平均耗时': f"{op_data.get('avg_duration', 0):.2f}s"
                })
            
            df = pd.DataFrame(ops_data)
            st.dataframe(df, use_container_width=True)
        
        # 最近错误
        recent_errors = summary.get('recent_errors', [])
        if recent_errors:
            with st.expander(f"⚠️ 最近错误 ({len(recent_errors)}条)"):
                for error in recent_errors:
                    st.error(f"**{error['operation']}**: {error['error']} ({error['timestamp'][:19]})")