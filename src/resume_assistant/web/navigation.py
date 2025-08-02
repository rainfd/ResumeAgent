"""Navigation System for Streamlit Web Interface."""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .session_manager import SessionManager
from ..utils import get_logger

logger = get_logger(__name__)

@dataclass
class MenuItem:
    """菜单项数据类"""
    key: str
    title: str
    icon: str
    page_class: Optional[Callable] = None
    visible: bool = True
    badge: Optional[str] = None

class NavigationManager:
    """导航管理器"""
    
    def __init__(self):
        self.menu_items = self._create_menu_items()
    
    def _create_menu_items(self) -> List[MenuItem]:
        """创建菜单项"""
        return [
            MenuItem(
                key="home",
                title="首页",
                icon="🏠",
                visible=True
            ),
            MenuItem(
                key="jobs",
                title="职位管理",
                icon="💼",
                visible=True
            ),
            MenuItem(
                key="resumes",
                title="简历管理", 
                icon="📄",
                visible=True
            ),
            MenuItem(
                key="analysis",
                title="分析结果",
                icon="🔍",
                visible=True
            ),
            MenuItem(
                key="greeting",
                title="打招呼语",
                icon="💬",
                visible=True
            ),
            MenuItem(
                key="settings",
                title="设置",
                icon="⚙️",
                visible=True
            )
        ]
    
    def render_sidebar_navigation(self):
        """渲染侧边栏导航"""
        with st.sidebar:
            # 应用标题
            st.title("📝 Resume Assistant")
            st.markdown("---")
            
            # 渲染主导航菜单
            self._render_main_menu()
            
            st.markdown("---")
            
            # 渲染统计信息
            self._render_sidebar_stats()
            
            st.markdown("---")
            
            # 渲染快捷操作
            self._render_quick_actions()
    
    def _render_main_menu(self):
        """渲染主菜单"""
        st.markdown("### 📋 主菜单")
        
        # 获取当前页面
        current_page = st.session_state.get('current_page', 'home')
        
        # 创建菜单选项
        menu_options = []
        menu_keys = []
        
        for item in self.menu_items:
            if item.visible:
                title = f"{item.icon} {item.title}"
                if item.badge:
                    title += f" ({item.badge})"
                
                menu_options.append(title)
                menu_keys.append(item.key)
        
        # 找到当前选中的索引
        try:
            current_index = menu_keys.index(current_page)
        except ValueError:
            current_index = 0
        
        # 渲染单选按钮菜单
        selected_index = st.radio(
            "选择页面",
            range(len(menu_options)),
            format_func=lambda x: menu_options[x],
            index=current_index,
            key="main_navigation"
        )
        
        # 更新当前页面
        selected_key = menu_keys[selected_index]
        if selected_key != current_page:
            st.session_state.current_page = selected_key
            st.rerun()
    
    def _render_sidebar_stats(self):
        """渲染侧边栏统计信息"""
        st.markdown("### 📊 统计信息")
        
        stats = SessionManager.get_session_stats()
        
        # 显示关键统计数据
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("职位", stats.get('jobs_count', 0))
            st.metric("简历", stats.get('resumes_count', 0))
        
        with col2:
            st.metric("分析", stats.get('analyses_count', 0))
            st.metric("通知", stats.get('notifications_count', 0))
        
        # 显示当前页面
        st.caption(f"当前页面: {stats.get('current_page', 'unknown')}")
    
    def _render_quick_actions(self):
        """渲染快捷操作"""
        st.markdown("### ⚡ 快捷操作")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 刷新", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🗑️ 清空", use_container_width=True):
                if st.session_state.get('confirm_reset', False):
                    SessionManager.reset_session()
                    st.session_state.confirm_reset = False
                    st.rerun()
                else:
                    st.session_state.confirm_reset = True
                    st.warning("再次点击确认重置")
        
        # 重置确认状态的自动清除
        if 'confirm_reset' in st.session_state and st.session_state.confirm_reset:
            if st.button("❌ 取消重置", use_container_width=True):
                st.session_state.confirm_reset = False
                st.rerun()
    
    def get_current_page(self) -> str:
        """获取当前页面"""
        return st.session_state.get('current_page', 'home')
    
    def set_current_page(self, page_key: str):
        """设置当前页面"""
        if page_key in [item.key for item in self.menu_items]:
            st.session_state.current_page = page_key
        else:
            logger.warning(f"Invalid page key: {page_key}")
    
    def get_menu_item(self, key: str) -> Optional[MenuItem]:
        """获取菜单项"""
        for item in self.menu_items:
            if item.key == key:
                return item
        return None
    
    def update_menu_badge(self, key: str, badge: str = None):
        """更新菜单项徽章"""
        item = self.get_menu_item(key)
        if item:
            item.badge = badge
    
    def set_menu_visibility(self, key: str, visible: bool):
        """设置菜单项可见性"""
        item = self.get_menu_item(key)
        if item:
            item.visible = visible

class BreadcrumbManager:
    """面包屑导航管理器"""
    
    @staticmethod
    def render_breadcrumb(path: List[Dict[str, str]]):
        """渲染面包屑导航"""
        if not path:
            return
        
        breadcrumb_items = []
        for i, item in enumerate(path):
            title = item.get('title', '')
            if i < len(path) - 1:
                # 非最后一项，可以点击
                breadcrumb_items.append(f"[{title}]")
            else:
                # 最后一项，当前页面
                breadcrumb_items.append(f"**{title}**")
        
        st.markdown(" > ".join(breadcrumb_items))

class TabManager:
    """选项卡管理器"""
    
    @staticmethod
    def render_tabs(tabs: List[Dict[str, Any]], selected_tab: str = None) -> str:
        """渲染选项卡"""
        if not tabs:
            return ""
        
        tab_titles = [tab.get('title', '') for tab in tabs]
        tab_keys = [tab.get('key', '') for tab in tabs]
        
        # 找到默认选中的选项卡
        if selected_tab and selected_tab in tab_keys:
            default_index = tab_keys.index(selected_tab)
        else:
            default_index = 0
        
        # 渲染选项卡
        selected_tab_obj = st.tabs(tab_titles)[default_index]
        
        return tab_keys[default_index] if default_index < len(tab_keys) else ""

class PageRouter:
    """页面路由器"""
    
    def __init__(self):
        self.navigation = NavigationManager()
        self.pages = {}
    
    def register_page(self, key: str, page_class: Callable):
        """注册页面"""
        self.pages[key] = page_class
    
    def render_current_page(self):
        """渲染当前页面"""
        current_page_key = self.navigation.get_current_page()
        
        if current_page_key in self.pages:
            page_class = self.pages[current_page_key]
            page_instance = page_class()
            page_instance.render()
        else:
            # 渲染默认页面或404页面
            self.render_404_page(current_page_key)
    
    def render_404_page(self, page_key: str):
        """渲染404页面"""
        st.title("🔍 页面未找到")
        st.error(f"页面 '{page_key}' 不存在或正在开发中")
        st.info("请从侧边栏选择其他页面")
        
        if st.button("返回首页"):
            self.navigation.set_current_page('home')
            st.rerun()