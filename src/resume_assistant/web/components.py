"""Reusable UI Components for Streamlit Web Interface."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json

from ..utils import get_logger

logger = get_logger(__name__)

class UIComponents:
    """可复用的Streamlit UI组件库"""
    
    @staticmethod
    def render_header(title: str, subtitle: str = None, icon: str = None):
        """渲染页面标题"""
        if icon:
            st.title(f"{icon} {title}")
        else:
            st.title(title)
        
        if subtitle:
            st.markdown(f"*{subtitle}*")
        
        st.markdown("---")
    
    @staticmethod
    def render_metric_cards(metrics: List[Dict[str, Any]], columns: int = 3):
        """渲染指标卡片"""
        cols = st.columns(columns)
        
        for i, metric in enumerate(metrics):
            with cols[i % columns]:
                st.metric(
                    label=metric.get('label', ''),
                    value=metric.get('value', 0),
                    delta=metric.get('delta', None),
                    delta_color=metric.get('delta_color', 'normal')
                )
    
    @staticmethod
    def render_progress_bar(label: str, progress: float, show_percentage: bool = True):
        """渲染进度条"""
        st.write(label)
        progress_bar = st.progress(progress)
        
        if show_percentage:
            st.write(f"{progress * 100:.1f}%")
        
        return progress_bar
    
    @staticmethod
    def render_status_indicator(status: str, message: str = None):
        """渲染状态指示器"""
        status_config = {
            'success': {'color': 'green', 'icon': '✅'},
            'error': {'color': 'red', 'icon': '❌'},
            'warning': {'color': 'orange', 'icon': '⚠️'},
            'info': {'color': 'blue', 'icon': 'ℹ️'},
            'loading': {'color': 'gray', 'icon': '⏳'}
        }
        
        config = status_config.get(status, status_config['info'])
        
        if message:
            st.markdown(f"{config['icon']} **{message}**")
        else:
            st.markdown(f"{config['icon']} {status.upper()}")
    
    @staticmethod
    def render_data_table(data: List[Dict[str, Any]], 
                         columns: List[str] = None,
                         sortable: bool = True,
                         filterable: bool = True,
                         selectable: bool = False) -> Optional[List[int]]:
        """渲染数据表格"""
        if not data:
            st.info("暂无数据")
            return None
        
        import pandas as pd
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 选择要显示的列
        if columns:
            df = df[columns]
        
        # 过滤功能
        if filterable:
            filter_cols = st.columns(len(df.columns))
            filters = {}
            
            for i, col in enumerate(df.columns):
                with filter_cols[i]:
                    if df[col].dtype == 'object':
                        unique_values = df[col].unique()
                        selected = st.multiselect(
                            f"筛选 {col}",
                            options=unique_values,
                            key=f"filter_{col}"
                        )
                        if selected:
                            filters[col] = selected
            
            # 应用筛选
            for col, values in filters.items():
                df = df[df[col].isin(values)]
        
        # 显示表格
        if selectable:
            selected_rows = st.dataframe(
                df,
                use_container_width=True,
                on_select="rerun",
                selection_mode="multiple-rows"
            )
            return selected_rows.selection.rows if selected_rows.selection else []
        else:
            st.dataframe(df, use_container_width=True)
            return None
    
    @staticmethod
    def render_file_uploader(label: str, 
                           file_types: List[str] = None,
                           multiple: bool = False,
                           help_text: str = None) -> Any:
        """渲染文件上传组件"""
        return st.file_uploader(
            label=label,
            type=file_types,
            accept_multiple_files=multiple,
            help=help_text
        )
    
    @staticmethod
    def render_form_input(form_config: Dict[str, Any], form_key: str = None) -> Dict[str, Any]:
        """渲染表单输入"""
        form_data = {}
        
        with st.form(form_key or "input_form"):
            for field_name, field_config in form_config.items():
                field_type = field_config.get('type', 'text')
                label = field_config.get('label', field_name)
                default = field_config.get('default', '')
                required = field_config.get('required', False)
                help_text = field_config.get('help', None)
                
                if field_type == 'text':
                    form_data[field_name] = st.text_input(
                        label, value=default, help=help_text
                    )
                elif field_type == 'textarea':
                    form_data[field_name] = st.text_area(
                        label, value=default, help=help_text
                    )
                elif field_type == 'number':
                    form_data[field_name] = st.number_input(
                        label, value=default, help=help_text
                    )
                elif field_type == 'select':
                    options = field_config.get('options', [])
                    form_data[field_name] = st.selectbox(
                        label, options=options, help=help_text
                    )
                elif field_type == 'multiselect':
                    options = field_config.get('options', [])
                    form_data[field_name] = st.multiselect(
                        label, options=options, help=help_text
                    )
                elif field_type == 'checkbox':
                    form_data[field_name] = st.checkbox(
                        label, value=default, help=help_text
                    )
                elif field_type == 'date':
                    form_data[field_name] = st.date_input(
                        label, help=help_text
                    )
                elif field_type == 'time':
                    form_data[field_name] = st.time_input(
                        label, help=help_text
                    )
            
            submitted = st.form_submit_button("提交")
            
            if submitted:
                # 验证必填字段
                missing_fields = []
                for field_name, field_config in form_config.items():
                    if field_config.get('required', False) and not form_data.get(field_name):
                        missing_fields.append(field_config.get('label', field_name))
                
                if missing_fields:
                    st.error(f"请填写必填字段: {', '.join(missing_fields)}")
                    return None
                
                return form_data
        
        return None
    
    @staticmethod
    def render_match_score_chart(scores: Dict[str, float], title: str = "匹配度分析"):
        """渲染匹配度评分图表"""
        # 创建雷达图
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='匹配度',
            line_color='rgb(0, 123, 255)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title=title
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_text_diff(original: str, modified: str, title: str = "文本对比"):
        """渲染文本差异对比"""
        st.subheader(title)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**原文本:**")
            st.text_area("", value=original, height=200, key="original_text", disabled=True)
        
        with col2:
            st.markdown("**修改后:**")
            st.text_area("", value=modified, height=200, key="modified_text", disabled=True)
    
    @staticmethod
    def render_notification_area():
        """渲染通知区域"""
        if 'notifications' in st.session_state and st.session_state.notifications:
            for notification in st.session_state.notifications[-3:]:  # 显示最新3条
                notification_type = notification.get('type', 'info')
                message = notification.get('message', '')
                
                if notification_type == 'success':
                    st.success(message)
                elif notification_type == 'error':
                    st.error(message)
                elif notification_type == 'warning':
                    st.warning(message)
                else:
                    st.info(message)
    
    @staticmethod
    def render_sidebar_stats():
        """渲染侧边栏统计信息"""
        with st.sidebar:
            st.markdown("### 📊 统计信息")
            
            if 'jobs' in st.session_state:
                st.metric("职位数量", len(st.session_state.jobs))
            
            if 'resumes' in st.session_state:
                st.metric("简历数量", len(st.session_state.resumes))
            
            if 'analyses' in st.session_state:
                st.metric("分析记录", len(st.session_state.analyses))
    
    @staticmethod
    def render_loading_spinner(message: str = "加载中..."):
        """渲染加载动画"""
        return st.spinner(message)
    
    @staticmethod
    def render_expandable_section(title: str, content: str, expanded: bool = False):
        """渲染可展开的内容区域"""
        with st.expander(title, expanded=expanded):
            st.markdown(content)
    
    @staticmethod
    def render_json_viewer(data: Dict[str, Any], title: str = "数据详情"):
        """渲染JSON数据查看器"""
        with st.expander(title):
            st.json(data)
    
    @staticmethod
    def render_copy_button(text: str, button_text: str = "复制", success_message: str = "已复制到剪贴板"):
        """渲染复制按钮 (需要JavaScript支持)"""
        if st.button(button_text):
            # 注意: 真正的复制到剪贴板需要JavaScript支持
            # 这里只是显示一个成功消息
            st.success(success_message)
            st.code(text)  # 显示要复制的内容
    
    @staticmethod
    def render_confirmation_dialog(message: str, key: str) -> bool:
        """渲染确认对话框"""
        if st.button("确认", key=f"{key}_confirm"):
            return st.checkbox(f"确认: {message}", key=f"{key}_checkbox")
        return False