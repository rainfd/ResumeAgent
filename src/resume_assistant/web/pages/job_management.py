"""Job Management Page for Streamlit Web Interface."""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
import re

from ..components import UIComponents
from ..session_manager import SessionManager
from ..adapters import WebJobManager
from ...utils import get_logger

logger = get_logger(__name__)

class JobManagementPage:
    """职位管理页面"""
    
    def __init__(self):
        self.components = UIComponents()
        self.job_manager = WebJobManager()
    
    def render(self):
        """渲染页面"""
        self.components.render_header(
            "职位管理", 
            "爬取、分析和管理目标职位信息",
            "💼"
        )
        
        # 显示通知
        self.components.render_notification_area()
        
        # 主要内容区域
        tab1, tab2, tab3 = st.tabs(["🕷️ 爬取职位", "📋 职位列表", "🔍 职位详情"])
        
        with tab1:
            self._render_scraping_section()
        
        with tab2:
            self._render_job_list()
        
        with tab3:
            self._render_job_details()
    
    def _render_scraping_section(self):
        """渲染爬取区域"""
        st.subheader("🕷️爬取新职位")
        
        # URL输入
        job_url = st.text_input(
            "职位URL",
            placeholder="请输入BOSS直聘等招聘网站的职位链接",
            help="支持BOSS直聘、智联招聘等主流招聘网站的职位链接"
        )
        
        # URL验证
        if job_url:
            is_valid = self._validate_job_url(job_url)
            if is_valid:
                st.success("✅ URL格式验证通过")
            else:
                st.error("❌ URL格式不支持，请检查链接是否来自支持的招聘网站")
        
        # 爬取选项
        with st.expander("⚙️ 爬取选项"):
            col1, col2 = st.columns(2)
            with col1:
                headless_mode = st.checkbox("无头模式", value=True, help="无头模式运行更快，但无法手动处理验证码")
                retry_count = st.number_input("重试次数", min_value=1, max_value=5, value=3)
            with col2:
                wait_time = st.number_input("等待时间(秒)", min_value=1, max_value=30, value=5)
                save_screenshot = st.checkbox("保存截图", value=False, help="遇到问题时保存页面截图")
        
        # 爬取按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🚀 开始爬取", type="primary", disabled=not job_url or not self._validate_job_url(job_url)):
                self._scrape_job(job_url, {
                    'headless': headless_mode,
                    'retry_count': retry_count,
                    'wait_time': wait_time,
                    'save_screenshot': save_screenshot
                })
        
        with col2:
            if st.button("📋 示例URL"):
                self._show_example_urls()
    
    def _render_job_list(self):
        """渲染职位列表"""
        st.subheader("📋 已爬取的职位")
        
        jobs = self.job_manager.get_jobs_list()
        
        if not jobs:
            st.info("还没有爬取任何职位。请在爬取职位标签页中添加职位链接。")
            return
        
        # 显示职位统计
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总数量", len(jobs))
        with col2:
            companies = set(job.get('company', 'Unknown') for job in jobs)
            st.metric("公司数量", len(companies))
        with col3:
            locations = set(job.get('location', 'Unknown') for job in jobs)
            st.metric("城市数量", len(locations))
        with col4:
            today_jobs = [job for job in jobs if job.get('created_at', '').startswith(str(st.date.today()))]
            st.metric("今日新增", len(today_jobs))
        
        # 搜索和筛选
        st.markdown("---")
        search_col, filter_col = st.columns(2)
        
        with search_col:
            search_term = st.text_input("🔍 搜索职位", placeholder="输入职位名称、公司名称或关键词")
        
        with filter_col:
            companies_list = list(companies) if companies else []
            selected_companies = st.multiselect("🏢 筛选公司", companies_list)
        
        # 过滤职位
        filtered_jobs = jobs
        if search_term:
            filtered_jobs = [
                job for job in filtered_jobs 
                if search_term.lower() in job.get('title', '').lower() 
                or search_term.lower() in job.get('company', '').lower()
                or search_term.lower() in job.get('description', '').lower()
            ]
        
        if selected_companies:
            filtered_jobs = [job for job in filtered_jobs if job.get('company') in selected_companies]
        
        # 职位表格
        st.markdown("---")
        st.write(f"显示 {len(filtered_jobs)} 个职位")
        
        for i, job in enumerate(filtered_jobs):
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{job.get('title', 'Unknown Position')}**")
                    st.caption(f"🏢 {job.get('company', 'Unknown Company')}")
                    if job.get('salary'):
                        st.caption(f"💰 {job.get('salary')}")
                
                with col2:
                    st.text(f"📍 {job.get('location', 'Unknown')}")
                    if job.get('experience'):
                        st.text(f"💼 {job.get('experience')}")
                
                with col3:
                    if job.get('created_at'):
                        st.text(f"📅 {job.get('created_at')[:10]}")
                    skills = job.get('skills', [])
                    if skills:
                        st.text(f"🛠️ {len(skills)} 项技能")
                
                with col4:
                    if st.button("👁️", key=f"view_job_{i}", help="查看详情"):
                        st.session_state.selected_job = job
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_job_{i}", help="删除"):
                        if self.job_manager.remove_job_from_session(job.get('id')):
                            st.success("职位已删除")
                            st.rerun()
                
                st.markdown("---")
    
    def _render_job_details(self):
        """渲染职位详情"""
        st.subheader("🔍 职位详情")
        
        selected_job = st.session_state.get('selected_job')
        
        if not selected_job:
            st.info("请从职位列表中选择一个职位查看详情。")
            return
        
        # 职位基本信息
        st.markdown("### 📋 基本信息")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**职位名称**: {selected_job.get('title', 'Unknown')}")
            st.info(f"**公司名称**: {selected_job.get('company', 'Unknown')}")
            st.info(f"**工作地点**: {selected_job.get('location', 'Unknown')}")
        
        with col2:
            st.info(f"**薪资范围**: {selected_job.get('salary', 'Unknown')}")
            st.info(f"**工作经验**: {selected_job.get('experience', 'Unknown')}")
            st.info(f"**学历要求**: {selected_job.get('education', 'Unknown')}")
        
        # 职位描述
        st.markdown("### 📝 职位描述")
        description = selected_job.get('description', '暂无描述')
        st.text_area("", value=description, height=200, disabled=True)
        
        # 任职要求
        if selected_job.get('requirements'):
            st.markdown("### 📋 任职要求")
            requirements = selected_job.get('requirements', '暂无要求')
            st.text_area("", value=requirements, height=150, disabled=True, key="requirements")
        
        # 技能要求
        skills = selected_job.get('skills', [])
        if skills:
            st.markdown("### 🛠️ 技能要求")
            # 以标签形式显示技能
            skills_html = ""
            for skill in skills:
                skills_html += f'<span style="background-color: #e1f5fe; padding: 2px 8px; margin: 2px; border-radius: 10px; display: inline-block;">{skill}</span> '
            st.markdown(skills_html, unsafe_allow_html=True)
        
        # 操作按钮
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 开始分析", type="primary"):
                st.session_state.current_page = 'analysis'
                st.rerun()
        
        with col2:
            if st.button("💬 生成打招呼语"):
                st.session_state.current_page = 'greeting'
                st.rerun()
        
        with col3:
            if st.button("🔗 访问原页面"):
                if selected_job.get('url'):
                    st.markdown(f"[点击访问原页面]({selected_job.get('url')})")
                else:
                    st.error("未找到原页面链接")
        
        with col4:
            if st.button("📋 复制信息"):
                job_info = f"""
职位：{selected_job.get('title', 'Unknown')}
公司：{selected_job.get('company', 'Unknown')}
地点：{selected_job.get('location', 'Unknown')}
薪资：{selected_job.get('salary', 'Unknown')}
技能：{', '.join(selected_job.get('skills', []))}
                """.strip()
                self.components.render_copy_button(job_info, "复制职位信息")
    
    def _validate_job_url(self, url: str) -> bool:
        """验证职位URL格式"""
        if not url:
            return False
        
        # 支持的招聘网站URL模式
        patterns = [
            r'https?://www\.zhipin\.com/job_detail/.*',  # BOSS直聘
            r'https?://jobs\.zhaopin\.com/.*',  # 智联招聘
            r'https?://www\.51job\.com/.*',  # 前程无忧
            r'https?://www\.lagou\.com/jobs/.*',  # 拉勾网
        ]
        
        return any(re.match(pattern, url) for pattern in patterns)
    
    def _show_example_urls(self):
        """显示示例URL"""
        st.info("""
        **支持的招聘网站示例URL：**
        
        • BOSS直聘: https://www.zhipin.com/job_detail/xxx.html
        • 智联招聘: https://jobs.zhaopin.com/xxx.htm
        • 前程无忧: https://www.51job.com/job/xxx.html
        • 拉勾网: https://www.lagou.com/jobs/xxx.html
        
        请复制完整的职位详情页面链接。
        """)
    
    def _scrape_job(self, url: str, options: Dict[str, Any]):
        """爬取职位信息"""
        try:
            # 使用适配器进行爬取
            job_data = self.job_manager.scrape_job(url)
            
            if job_data:
                # 添加到会话
                if self.job_manager.add_job_to_session(job_data):
                    st.success(f"✅ 职位 '{job_data.get('title', 'Unknown')}' 爬取成功！")
                    
                    # 显示爬取结果摘要
                    st.markdown("### 📊 爬取结果摘要")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("公司名称", job_data.get('company', 'Unknown')[:10] + "...")
                    with col2:
                        st.metric("职位名称", job_data.get('title', 'Unknown')[:10] + "...")
                    with col3:
                        st.metric("工作地点", job_data.get('location', 'Unknown'))
                    with col4:
                        st.metric("技能要求", len(job_data.get('skills', [])))
                    
                    # 快速预览
                    if job_data.get('description'):
                        st.markdown("**📝 职位描述预览:**")
                        description_preview = job_data.get('description', '')[:200]
                        st.write(description_preview + "..." if len(job_data.get('description', '')) > 200 else description_preview)
                    
                    # 自动切换到职位列表标签
                    if st.button("📋 查看职位列表", type="secondary"):
                        st.rerun()
                else:
                    st.error("保存职位到会话失败")
            else:
                st.error("职位爬取失败，请检查URL是否正确或稍后重试")
                
        except Exception as e:
            logger.error(f"爬取职位时出错: {str(e)}")
            st.error(f"爬取失败: {str(e)}")
            st.info("如遇到IP验证或其他反爬限制，请稍后重试或尝试手动访问页面后再爬取。")