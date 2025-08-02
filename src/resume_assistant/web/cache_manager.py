"""Web界面缓存管理

优化Streamlit应用的性能通过智能缓存系统。
"""

import streamlit as st
import hashlib
import pickle
import json
import time
from typing import Any, Optional, Dict, List, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from dataclasses import dataclass, field
import os

from ..utils import get_logger

logger = get_logger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """获取缓存年龄（秒）"""
        return (datetime.now() - self.created_at).total_seconds()

class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self, max_size_mb: int = 100, default_ttl_seconds: int = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0
        }
        
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 创建参数的哈希
        param_str = json.dumps({
            'args': str(args),
            'kwargs': sorted(kwargs.items())
        }, sort_keys=True, default=str)
        
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"{func_name}:{param_hash}"
    
    def _calculate_size(self, value: Any) -> int:
        """计算对象大小"""
        try:
            return len(pickle.dumps(value))
        except:
            # 如果无法序列化，使用估算
            return len(str(value).encode())
    
    def _evict_if_needed(self, required_size: int):
        """如果需要，执行缓存驱逐"""
        while (self.stats['size_bytes'] + required_size > self.max_size_bytes and 
               self.cache):
            # LRU驱逐：删除最久未访问的项
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].last_accessed)
            
            entry = self.cache.pop(oldest_key)
            self.stats['size_bytes'] -= entry.size_bytes
            self.stats['evictions'] += 1
            
            logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # 检查过期
        if entry.is_expired:
            self.remove(key)
            self.stats['misses'] += 1
            return None
        
        # 更新访问信息
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        self.stats['hits'] += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            tags: Optional[List[str]] = None):
        """设置缓存值"""
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        size_bytes = self._calculate_size(value)
        
        # 如果需要，执行驱逐
        self._evict_if_needed(size_bytes)
        
        # 如果key已存在，先删除旧的
        if key in self.cache:
            self.stats['size_bytes'] -= self.cache[key].size_bytes
        
        # 创建新条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            size_bytes=size_bytes,
            tags=tags or []
        )
        
        self.cache[key] = entry
        self.stats['size_bytes'] += size_bytes
        
        logger.debug(f"Cached entry: {key}, size: {size_bytes} bytes")
    
    def remove(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.stats['size_bytes'] -= entry.size_bytes
            return True
        return False
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.stats['size_bytes'] = 0
        logger.info("Cache cleared")
    
    def clear_by_tag(self, tag: str):
        """根据标签清空缓存"""
        keys_to_remove = [
            key for key, entry in self.cache.items()
            if tag in entry.tags
        ]
        
        for key in keys_to_remove:
            self.remove(key)
        
        logger.info(f"Cleared {len(keys_to_remove)} entries with tag: {tag}")
    
    def cleanup_expired(self):
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            self.remove(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = (self.stats['hits'] / 
                   (self.stats['hits'] + self.stats['misses']) 
                   if (self.stats['hits'] + self.stats['misses']) > 0 else 0)
        
        return {
            **self.stats,
            'entries_count': len(self.cache),
            'hit_rate': hit_rate,
            'size_mb': self.stats['size_bytes'] / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024)
        }
    
    def get_entries_info(self) -> List[Dict[str, Any]]:
        """获取缓存条目信息"""
        return [
            {
                'key': entry.key,
                'created_at': entry.created_at,
                'expires_at': entry.expires_at,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed,
                'size_bytes': entry.size_bytes,
                'tags': entry.tags,
                'age_seconds': entry.age_seconds,
                'is_expired': entry.is_expired
            }
            for entry in self.cache.values()
        ]

# 全局缓存管理器
_cache_manager = None

def get_cache_manager() -> SmartCacheManager:
    """获取全局缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SmartCacheManager()
    return _cache_manager

# Streamlit缓存装饰器
def st_cache(
    ttl_seconds: Optional[int] = None,
    tags: Optional[List[str]] = None,
    show_spinner: bool = True,
    spinner_text: str = "加载中..."
):
    """Streamlit缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 缓存未命中，执行函数
            if show_spinner:
                with st.spinner(spinner_text):
                    result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, ttl_seconds, tags)
            
            return result
        
        return wrapper
    return decorator

# 缓存管理UI工具
def display_cache_stats():
    """显示缓存统计信息"""
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("缓存命中率", f"{stats['hit_rate']:.1%}")
    
    with col2:
        st.metric("缓存条目", stats['entries_count'])
    
    with col3:
        st.metric("缓存大小", f"{stats['size_mb']:.1f} MB")
    
    with col4:
        st.metric("驱逐次数", stats['evictions'])

def display_cache_management():
    """显示缓存管理界面"""
    st.subheader("🗄️ 缓存管理")
    
    cache_manager = get_cache_manager()
    
    # 显示统计信息
    display_cache_stats()
    
    st.divider()
    
    # 操作按钮
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🧹 清理过期", help="清理所有过期的缓存条目"):
            cleaned = cache_manager.cleanup_expired()
            st.success(f"清理了 {cleaned} 个过期条目")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 清空全部", help="清空所有缓存"):
            cache_manager.clear()
            st.success("已清空所有缓存")
            st.rerun()
    
    with col3:
        tag_to_clear = st.selectbox("按标签清理", 
                                   ["jobs", "resumes", "analyses", "agents", "files", "scraping", "analysis", "greeting"])
        if st.button("🏷️ 清理标签"):
            cache_manager.clear_by_tag(tag_to_clear)
            st.success(f"已清理标签 '{tag_to_clear}' 的缓存")
            st.rerun()
    
    with col4:
        if st.button("📊 详细信息", help="显示缓存条目详细信息"):
            st.session_state.show_cache_details = not st.session_state.get('show_cache_details', False)
    
    # 显示详细信息
    if st.session_state.get('show_cache_details', False):
        st.divider()
        st.subheader("📋 缓存条目详情")
        
        entries = cache_manager.get_entries_info()
        if entries:
            import pandas as pd
            df = pd.DataFrame(entries)
            df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df['last_accessed'] = df['last_accessed'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df['size_kb'] = (df['size_bytes'] / 1024).round(2)
            
            # 显示表格
            st.dataframe(
                df[['key', 'created_at', 'last_accessed', 'access_count', 'size_kb', 'tags', 'is_expired']],
                use_container_width=True
            )
        else:
            st.info("暂无缓存条目")

# 自动缓存清理任务
def schedule_cache_cleanup():
    """安排自动缓存清理任务"""
    cache_manager = get_cache_manager()
    
    # 每10分钟清理一次过期条目
    last_cleanup = st.session_state.get('last_cache_cleanup', 0)
    now = time.time()
    
    if now - last_cleanup > 600:  # 10分钟
        cleaned = cache_manager.cleanup_expired()
        st.session_state.last_cache_cleanup = now
        
        if cleaned > 0:
            logger.info(f"Auto-cleaned {cleaned} expired cache entries")

# 实用工具函数
def invalidate_cache(tags: Optional[List[str]] = None, keys: Optional[List[str]] = None):
    """使缓存失效"""
    cache_manager = get_cache_manager()
    
    if tags:
        for tag in tags:
            cache_manager.clear_by_tag(tag)
    
    if keys:
        for key in keys:
            cache_manager.remove(key)

def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """获取缓存键"""
    cache_manager = get_cache_manager()
    return cache_manager._generate_key(func_name, args, kwargs)