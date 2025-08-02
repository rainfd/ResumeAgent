"""Greeting Generator Page for Streamlit Web Interface."""

import streamlit as st
from typing import Dict, Any, List, Optional

from ..components import UIComponents
from ..session_manager import SessionManager
from ..adapters import WebGreetingManager
from ...utils import get_logger

logger = get_logger(__name__)

class GreetingGeneratorPage:
    """打招呼语生成页面"""
    
    def __init__(self):
        self.components = UIComponents()
        self.greeting_manager = WebGreetingManager()
    
    def render(self):
        """渲染页面"""
        self.components.render_header(
            "打招呼语生成", 
            "AI生成个性化求职开场白",
            "💬"
        )
        
        # 显示通知
        self.components.render_notification_area()
        
        # 主要内容区域
        tab1, tab2 = st.tabs(["🎯 生成打招呼语", "📋 历史记录"])
        
        with tab1:
            self._render_greeting_generator()
        
        with tab2:
            self._render_greeting_history()
    
    def _render_greeting_generator(self):
        """渲染打招呼语生成区域"""
        st.subheader("💬 生成个性化打招呼语")
        
        # 选择职位和简历
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 选择目标职位")
            jobs = st.session_state.get('jobs', [])
            
            if not jobs:
                st.warning("⚠️ 还没有职位数据，请先到职位管理页面添加职位。")
                if st.button("🔗 前往职位管理"):
                    st.session_state.current_page = 'jobs'
                    st.rerun()
            else:
                job_options = [f"{job.get('title', 'Unknown')} - {job.get('company', 'Unknown')}" for job in jobs]
                selected_job_index = st.selectbox(
                    "选择职位",
                    range(len(job_options)),
                    format_func=lambda x: job_options[x],
                    key="greeting_selected_job"
                )
                
                if selected_job_index is not None:
                    selected_job = jobs[selected_job_index]
                    st.session_state.greeting_job = selected_job
                    
                    # 显示职位信息
                    with st.expander("📋 职位信息预览"):
                        st.write(f"**职位**: {selected_job.get('title', 'Unknown')}")
                        st.write(f"**公司**: {selected_job.get('company', 'Unknown')}")
                        st.write(f"**地点**: {selected_job.get('location', 'Unknown')}")
                        if selected_job.get('salary'):
                            st.write(f"**薪资**: {selected_job.get('salary')}")
        
        with col2:
            st.markdown("### 📄 选择简历")
            resumes = st.session_state.get('resumes', [])
            
            if not resumes:
                st.warning("⚠️ 还没有简历数据，请先到简历管理页面上传简历。")
                if st.button("🔗 前往简历管理"):
                    st.session_state.current_page = 'resumes'
                    st.rerun()
            else:
                resume_options = [f"{resume.get('name', 'Unknown')}" for resume in resumes]
                selected_resume_index = st.selectbox(
                    "选择简历",
                    range(len(resume_options)),
                    format_func=lambda x: resume_options[x],
                    key="greeting_selected_resume"
                )
                
                if selected_resume_index is not None:
                    selected_resume = resumes[selected_resume_index]
                    st.session_state.greeting_resume = selected_resume
                    
                    # 显示简历信息
                    with st.expander("📄 简历信息预览"):
                        if selected_resume.get('personal_info', {}).get('name'):
                            st.write(f"**姓名**: {selected_resume['personal_info']['name']}")
                        st.write(f"**文件**: {selected_resume.get('name', 'Unknown')}")
                        st.write(f"**类型**: {selected_resume.get('file_type', 'Unknown').upper()}")
                        if selected_resume.get('skills'):
                            st.write(f"**技能**: {', '.join(selected_resume.get('skills', [])[:5])}")
        
        # 生成选项
        st.markdown("---")
        st.markdown("### ⚙️ 生成选项")
        
        col1, col2 = st.columns(2)
        with col1:
            greeting_style = st.selectbox(
                "打招呼语风格",
                ["智能混合", "正式商务", "友好专业", "简洁直接"],
                index=0,
                help="选择打招呼语的整体风格"
            )
            
            length_preference = st.select_slider(
                "内容长度",
                options=["简短", "适中", "详细"],
                value="适中",
                help="控制打招呼语的详细程度"
            )
        
        with col2:
            highlight_skills = st.checkbox("突出技能匹配", value=True, help="重点展示与职位匹配的技能")
            include_experience = st.checkbox("提及工作经验", value=True, help="在打招呼语中提及相关工作经验")
            
            custom_tone = st.text_input(
                "自定义语调",
                placeholder="例如：热情、专业、诚恳...",
                help="可选：指定特定的语调风格"
            )
        
        # 生成按钮
        st.markdown("---")
        
        can_generate = (
            st.session_state.get('greeting_job') and 
            st.session_state.get('greeting_resume')
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button(
                "🎯 生成打招呼语", 
                type="primary", 
                disabled=not can_generate,
                use_container_width=True
            ):
                self._generate_greetings({
                    'style': greeting_style,
                    'length': length_preference,
                    'highlight_skills': highlight_skills,
                    'include_experience': include_experience,
                    'custom_tone': custom_tone
                })
        
        with col2:
            if st.button("📋 预览数据", disabled=not can_generate):
                self._preview_data()
        
        with col3:
            if st.button("🔄 重置选择"):
                if 'greeting_job' in st.session_state:
                    del st.session_state.greeting_job
                if 'greeting_resume' in st.session_state:
                    del st.session_state.greeting_resume
                if 'current_greetings' in st.session_state:
                    del st.session_state.current_greetings
                st.rerun()
        
        # 显示生成结果
        if st.session_state.get('current_greetings'):
            self._display_greeting_results()
    
    def _render_greeting_history(self):
        """渲染打招呼语历史记录"""
        st.subheader("📋 打招呼语历史记录")
        
        greetings_history = st.session_state.get('greetings', [])
        
        if not greetings_history:
            st.info("还没有生成过打招呼语。请在生成标签页中创建您的第一个打招呼语。")
            return
        
        # 搜索和筛选
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 搜索打招呼语", placeholder="搜索公司名或内容...")
        with col2:
            sort_by = st.selectbox("排序方式", ["最新优先", "最旧优先", "按公司"])
        
        # 过滤和排序
        filtered_greetings = self._filter_greetings(greetings_history, search_term, sort_by)
        
        # 显示历史记录
        for i, greeting_record in enumerate(filtered_greetings):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    company = greeting_record.get('company', 'Unknown Company')
                    position = greeting_record.get('position', 'Unknown Position')
                    st.markdown(f"**{position}** - {company}")
                    
                    # 显示第一个打招呼语的预览
                    greetings = greeting_record.get('greetings', [])
                    if greetings:
                        preview = greetings[0][:80] + "..." if len(greetings[0]) > 80 else greetings[0]
                        st.caption(preview)
                
                with col2:
                    created_at = greeting_record.get('created_at', '')
                    st.text(f"📅 {created_at[:10]}")  # 只显示日期部分
                    st.text(f"📝 {len(greetings)}个版本")
                
                with col3:
                    if st.button("👁️", key=f"view_greeting_{i}", help="查看详情"):
                        st.session_state.current_greetings = greetings
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_greeting_{i}", help="删除"):
                        st.session_state.greetings = [g for g in st.session_state.greetings if g != greeting_record]
                        st.success("打招呼语记录已删除")
                        st.rerun()
                
                st.markdown("---")
    
    def _generate_greetings(self, options: Dict[str, Any]):
        """生成打招呼语"""
        job = st.session_state.get('greeting_job')
        resume = st.session_state.get('greeting_resume')
        
        if not job or not resume:
            st.error("请先选择职位和简历")
            return
        
        try:
            # 生成打招呼语
            greetings = self.greeting_manager.generate_greeting(job, resume)
            
            if greetings:
                st.session_state.current_greetings = greetings
                st.success("✅ 打招呼语生成完成！")
                st.rerun()
            else:
                st.error("生成失败，请稍后重试")
                
        except Exception as e:
            logger.error(f"生成打招呼语时出错: {str(e)}")
            st.error(f"生成失败: {str(e)}")
    
    def _display_greeting_results(self):
        """显示生成的打招呼语结果"""
        st.markdown("---")
        st.subheader("✅ 生成的打招呼语")
        
        greetings = st.session_state.get('current_greetings', [])
        
        for i, greeting in enumerate(greetings, 1):
            st.markdown(f"### 版本 {i}")
            
            # 显示打招呼语内容
            st.text_area(
                f"打招呼语 {i}",
                value=greeting,
                height=100,
                key=f"greeting_display_{i}",
                disabled=True
            )
            
            # 操作按钮
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(f"📋 复制版本 {i}", key=f"copy_greeting_{i}"):
                    self.components.render_copy_button(greeting, f"打招呼语版本{i}")
                    st.success(f"版本 {i} 已复制到剪贴板（模拟）")
            
            with col2:
                if st.button(f"✏️ 编辑版本 {i}", key=f"edit_greeting_{i}"):
                    st.session_state[f'edit_greeting_{i}'] = True
                    st.rerun()
            
            # 编辑模式
            if st.session_state.get(f'edit_greeting_{i}', False):
                edited_greeting = st.text_area(
                    f"编辑版本 {i}",
                    value=greeting,
                    height=100,
                    key=f"greeting_edit_{i}"
                )
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button(f"💾 保存", key=f"save_greeting_{i}"):
                        greetings[i-1] = edited_greeting
                        st.session_state.current_greetings = greetings
                        st.session_state[f'edit_greeting_{i}'] = False
                        st.success("修改已保存")
                        st.rerun()
                
                with col_cancel:
                    if st.button(f"❌ 取消", key=f"cancel_greeting_{i}"):
                        st.session_state[f'edit_greeting_{i}'] = False
                        st.rerun()
            
            st.markdown("---")
        
        # 保存到历史记录
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("💾 保存到历史记录", type="primary"):
                self._save_to_history()
        
        with col2:
            if st.button("🔄 重新生成"):
                st.session_state.current_greetings = None
                st.rerun()
        
        with col3:
            if st.button("📋 复制全部"):
                all_text = "\n\n".join([f"版本 {i+1}:\n{greeting}" for i, greeting in enumerate(greetings)])
                self.components.render_copy_button(all_text, "所有打招呼语版本")
    
    def _preview_data(self):
        """预览将要使用的数据"""
        job = st.session_state.get('greeting_job')
        resume = st.session_state.get('greeting_resume')
        
        if not job or not resume:
            st.warning("请先选择职位和简历")
            return
        
        with st.expander("📋 数据预览", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**职位信息:**")
                st.write(f"职位: {job.get('title')}")
                st.write(f"公司: {job.get('company')}")
                if job.get('skills'):
                    st.write(f"技能要求: {', '.join(job.get('skills', [])[:3])}...")
            
            with col2:
                st.markdown("**简历信息:**")
                st.write(f"文件: {resume.get('name')}")
                if resume.get('personal_info', {}).get('name'):
                    st.write(f"姓名: {resume['personal_info']['name']}")
                if resume.get('skills'):
                    st.write(f"技能: {', '.join(resume.get('skills', [])[:3])}...")
    
    def _save_to_history(self):
        """保存打招呼语到历史记录"""
        job = st.session_state.get('greeting_job')
        resume = st.session_state.get('greeting_resume')
        greetings = st.session_state.get('current_greetings')
        
        if not all([job, resume, greetings]):
            st.error("数据不完整，无法保存")
            return
        
        # 创建历史记录项
        from datetime import datetime
        import uuid
        
        history_item = {
            'id': str(uuid.uuid4()),
            'company': job.get('company', ''),
            'position': job.get('title', ''),
            'greetings': greetings,
            'job_data': job,
            'resume_data': resume,
            'created_at': datetime.now().isoformat()
        }
        
        # 添加到会话状态
        if 'greetings' not in st.session_state:
            st.session_state.greetings = []
        
        st.session_state.greetings.append(history_item)
        st.success("✅ 已保存到历史记录")
        
        # 清除当前结果
        st.session_state.current_greetings = None
    
    def _filter_greetings(self, greetings: List[Dict[str, Any]], search_term: str, sort_by: str) -> List[Dict[str, Any]]:
        """过滤和排序打招呼语历史记录"""
        # 搜索过滤
        if search_term:
            filtered = []
            for greeting in greetings:
                company = greeting.get('company', '').lower()
                position = greeting.get('position', '').lower()
                content = ' '.join(greeting.get('greetings', [])).lower()
                
                if (search_term.lower() in company or 
                    search_term.lower() in position or 
                    search_term.lower() in content):
                    filtered.append(greeting)
        else:
            filtered = greetings.copy()
        
        # 排序
        if sort_by == "最新优先":
            filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == "最旧优先":
            filtered.sort(key=lambda x: x.get('created_at', ''))
        elif sort_by == "按公司":
            filtered.sort(key=lambda x: x.get('company', ''))
        
        return filtered