"""Base Page Class for Web Interface."""

import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..session_manager import SessionManager
from ..components import UIComponents
from ...utils import get_logger

logger = get_logger(__name__)

class BasePage(ABC):
    """页面基类"""
    
    def __init__(self, title: str, icon: str = None, subtitle: str = None):
        self.title = title
        self.icon = icon
        self.subtitle = subtitle
        self.components = UIComponents()
    
    def render(self):
        """渲染页面的主方法"""
        try:
            # 渲染页面头部
            self.render_header()
            
            # 渲染通知区域
            self.components.render_notification_area()
            
            # 渲染页面内容
            self.render_content()
            
            # 渲染页面底部
            self.render_footer()
            
        except Exception as e:
            logger.error(f"Error rendering page {self.title}: {e}")
            st.error(f"页面渲染出错: {str(e)}")
    
    def render_header(self):
        """渲染页面头部"""
        self.components.render_header(self.title, self.subtitle, self.icon)
    
    @abstractmethod
    def render_content(self):
        """渲染页面主要内容 - 由子类实现"""
        pass
    
    def render_footer(self):
        """渲染页面底部"""
        # 默认不显示底部，子类可以重写
        pass
    
    def get_page_key(self) -> str:
        """获取页面唯一标识符"""
        return self.title.lower().replace(' ', '_')

class DashboardPage(BasePage):
    """仪表板页面基类"""
    
    def render_stats(self, stats: Dict[str, Any]):
        """渲染统计信息"""
        metrics = []
        for key, value in stats.items():
            metrics.append({
                'label': key,
                'value': value
            })
        
        self.components.render_metric_cards(metrics)

class FormPage(BasePage):
    """表单页面基类"""
    
    def __init__(self, title: str, form_config: Dict[str, Any], 
                 icon: str = None, subtitle: str = None):
        super().__init__(title, icon, subtitle)
        self.form_config = form_config
    
    def render_form(self, form_key: str = None) -> Optional[Dict[str, Any]]:
        """渲染表单"""
        return self.components.render_form_input(
            self.form_config, 
            form_key or f"{self.get_page_key()}_form"
        )
    
    @abstractmethod
    def handle_form_submission(self, form_data: Dict[str, Any]):
        """处理表单提交 - 由子类实现"""
        pass

class ListPage(BasePage):
    """列表页面基类"""
    
    def render_data_list(self, data: list, columns: list = None, 
                        show_actions: bool = True):
        """渲染数据列表"""
        if show_actions:
            col1, col2 = st.columns([4, 1])
            with col2:
                self.render_list_actions()
            with col1:
                selected = self.components.render_data_table(
                    data, columns, selectable=True
                )
                return selected
        else:
            return self.components.render_data_table(data, columns)
    
    def render_list_actions(self):
        """渲染列表操作按钮"""
        # 默认操作，子类可以重写
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
    
    @abstractmethod
    def get_list_data(self) -> list:
        """获取列表数据 - 由子类实现"""
        pass