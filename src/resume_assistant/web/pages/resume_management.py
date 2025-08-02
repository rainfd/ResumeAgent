"""Resume Management Page for Streamlit Web Interface."""

import streamlit as st
from typing import Dict, Any, List, Optional

from ..components import UIComponents
from ..session_manager import SessionManager
from ..adapters import WebResumeManager
from ...utils import get_logger

logger = get_logger(__name__)

class ResumeManagementPage:
    """简历管理页面"""
    
    def __init__(self):
        self.components = UIComponents()
        self.resume_manager = WebResumeManager()
    
    def render(self):
        """渲染页面"""
        self.components.render_header(
            "简历管理", 
            "上传、解析和管理您的简历文件",
            "📄"
        )
        
        # 显示通知
        self.components.render_notification_area()
        
        # 主要内容区域
        tab1, tab2, tab3 = st.tabs(["📤 上传简历", "📋 简历列表", "🔍 简历预览"])
        
        with tab1:
            self._render_upload_section()
        
        with tab2:
            self._render_resume_list()
        
        with tab3:
            self._render_resume_preview()
    
    def _render_upload_section(self):
        """渲染上传区域"""
        st.subheader("📤 上传新简历")
        
        # 文件上传器
        uploaded_file = self.components.render_file_uploader(
            "选择简历文件",
            file_types=['pdf', 'txt', 'md'],
            help_text="支持 PDF、TXT、Markdown 格式，最大 10MB"
        )
        
        if uploaded_file is not None:
            # 显示文件信息
            file_details = {
                "文件名": uploaded_file.name,
                "文件大小": f"{len(uploaded_file.getvalue()) / 1024:.1f} KB",
                "文件类型": uploaded_file.type
            }
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("文件名", file_details["文件名"])
            with col2:
                st.metric("大小", file_details["文件大小"])
            with col3:
                st.metric("类型", file_details["文件类型"])
            
            # 处理文件按钮
            if st.button("🔄 解析简历", type="primary", use_container_width=True):
                self._process_uploaded_file(uploaded_file)
    
    def _render_resume_list(self):
        """渲染简历列表"""
        st.subheader("📋 已上传的简历")
        
        resumes = self.resume_manager.get_resumes_list()
        
        if not resumes:
            st.info("还没有上传任何简历。请在上传简历标签页中上传您的简历文件。")
            return
        
        # 显示简历统计
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总数量", len(resumes))
        with col2:
            total_size = sum(r.get('file_size', 0) for r in resumes) / 1024
            st.metric("总大小", f"{total_size:.1f} KB")
        with col3:
            file_types = set(r.get('file_type', 'unknown') for r in resumes)
            st.metric("文件类型", len(file_types))
        
        # 简历表格
        st.markdown("---")
        
        for i, resume in enumerate(resumes):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{resume.get('name', 'Unknown')}**")
                    if resume.get('personal_info', {}).get('name'):
                        st.caption(f"姓名: {resume['personal_info']['name']}")
                
                with col2:
                    st.text(f"类型: {resume.get('file_type', 'Unknown').upper()}")
                    st.text(f"大小: {resume.get('file_size', 0) / 1024:.1f} KB")
                
                with col3:
                    skills_count = len(resume.get('skills', []))
                    exp_count = len(resume.get('experience', []))
                    st.text(f"技能: {skills_count} 项")
                    st.text(f"经验: {exp_count} 项")
                
                with col4:
                    if st.button("👁️", key=f"view_{i}", help="预览"):
                        st.session_state.selected_resume = resume
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_{i}", help="删除"):
                        if self.resume_manager.remove_resume_from_session(resume.get('id')):
                            st.rerun()
                
                st.markdown("---")
    
    def _render_resume_preview(self):
        """渲染简历预览"""
        st.subheader("🔍 简历预览")
        
        selected_resume = st.session_state.get('selected_resume')
        
        if not selected_resume:
            st.info("请从简历列表中选择一份简历进行预览。")
            return
        
        # 预览简历
        self.resume_manager.preview_resume(selected_resume)
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 开始分析", type="primary"):
                st.session_state.current_page = 'analysis'
                st.rerun()
        
        with col2:
            if st.button("💬 生成打招呼语"):
                st.session_state.current_page = 'greeting'
                st.rerun()
        
        with col3:
            if st.button("✏️ 编辑简历"):
                st.info("编辑功能开发中...")
    
    def _process_uploaded_file(self, uploaded_file):
        """处理上传的文件"""
        try:
            # 处理文件
            resume_data = self.resume_manager.process_uploaded_file(uploaded_file)
            
            if resume_data:
                # 添加到会话
                if self.resume_manager.add_resume_to_session(resume_data):
                    st.success(f"✅ 简历 '{uploaded_file.name}' 解析成功！")
                    
                    # 显示解析结果摘要
                    st.markdown("### 📊 解析结果摘要")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("技能数量", len(resume_data.get('skills', [])))
                    with col2:
                        st.metric("工作经验", len(resume_data.get('experience', [])))
                    with col3:
                        st.metric("项目经历", len(resume_data.get('projects', [])))
                    with col4:
                        st.metric("教育背景", len(resume_data.get('education', [])))
                    
                    # 快速预览
                    if resume_data.get('skills'):
                        st.markdown("**🛠️ 识别的技能:**")
                        skills_preview = resume_data.get('skills', [])[:5]  # 显示前5个
                        st.write(", ".join(skills_preview))
                        if len(resume_data.get('skills', [])) > 5:
                            st.caption(f"还有 {len(resume_data.get('skills', [])) - 5} 项技能...")
                    
                    # 自动切换到简历列表标签
                    if st.button("📋 查看简历列表", type="secondary"):
                        st.rerun()
                else:
                    st.error("保存简历到会话失败")
            else:
                st.error("简历解析失败，请检查文件格式和内容")
                
        except Exception as e:
            logger.error(f"处理上传文件时出错: {str(e)}")
            st.error(f"处理文件时出错: {str(e)}")