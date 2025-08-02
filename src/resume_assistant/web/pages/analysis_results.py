"""Analysis Results Page for Streamlit Web Interface."""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional

from ..components import UIComponents
from ..session_manager import SessionManager
from ..adapters import WebAnalysisManager
from ...utils import get_logger
from ...core.agents import AgentManager, AgentFactory, AIAnalyzer
from ...data.models import AIAgent, AgentType

logger = get_logger(__name__)

class AnalysisResultsPage:
    """分析结果页面"""
    
    def __init__(self):
        self.components = UIComponents()
        self.analysis_manager = WebAnalysisManager()
        self._agent_manager = None
    
    def render(self):
        """渲染页面"""
        self.components.render_header(
            "分析结果", 
            "AI驱动的简历与职位匹配度分析",
            "🔍"
        )
        
        # 显示通知
        self.components.render_notification_area()
        
        # 主要内容区域
        tab1, tab2, tab3 = st.tabs(["🚀 开始分析", "📊 分析结果", "📈 历史记录"])
        
        with tab1:
            self._render_analysis_setup()
        
        with tab2:
            self._render_current_analysis()
        
        with tab3:
            self._render_analysis_history()
    
    def _render_analysis_setup(self):
        """渲染分析设置区域"""
        st.subheader("🚀 开始新的匹配度分析")
        
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
                    key="selected_job_for_analysis"
                )
                
                if selected_job_index is not None:
                    selected_job = jobs[selected_job_index]
                    st.session_state.analysis_selected_job = selected_job
                    
                    # 显示职位信息
                    with st.expander("📋 职位信息预览"):
                        st.write(f"**职位**: {selected_job.get('title', 'Unknown')}")
                        st.write(f"**公司**: {selected_job.get('company', 'Unknown')}")
                        st.write(f"**地点**: {selected_job.get('location', 'Unknown')}")
                        if selected_job.get('skills'):
                            st.write(f"**技能要求**: {', '.join(selected_job.get('skills', [])[:5])}")
        
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
                    key="selected_resume_for_analysis"
                )
                
                if selected_resume_index is not None:
                    selected_resume = resumes[selected_resume_index]
                    st.session_state.analysis_selected_resume = selected_resume
                    
                    # 显示简历信息
                    with st.expander("📄 简历信息预览"):
                        if selected_resume.get('personal_info', {}).get('name'):
                            st.write(f"**姓名**: {selected_resume['personal_info']['name']}")
                        st.write(f"**文件**: {selected_resume.get('name', 'Unknown')}")
                        st.write(f"**类型**: {selected_resume.get('file_type', 'Unknown').upper()}")
                        if selected_resume.get('skills'):
                            st.write(f"**技能**: {', '.join(selected_resume.get('skills', [])[:5])}")
        
        # Agent选择
        st.markdown("---")
        st.markdown("### 🤖 选择AI分析Agent")
        self._render_agent_selection()
        
        # 分析选项
        st.markdown("---")
        st.markdown("### ⚙️ 分析选项")
        
        col1, col2 = st.columns(2)
        with col1:
            analysis_depth = st.select_slider(
                "分析深度",
                options=["快速", "标准", "深度"],
                value="标准",
                help="快速模式关注关键匹配点，深度模式提供详细分析"
            )
            
            include_suggestions = st.checkbox("生成优化建议", value=True, help="生成具体的简历改进建议")
        
        with col2:
            focus_areas = st.multiselect(
                "重点分析领域",
                ["技能匹配", "工作经验", "教育背景", "项目经历", "关键词覆盖"],
                default=["技能匹配", "工作经验", "关键词覆盖"],
                help="选择需要重点分析的领域"
            )
        
        # 开始分析按钮
        st.markdown("---")
        
        can_analyze = (
            st.session_state.get('analysis_selected_job') and 
            st.session_state.get('analysis_selected_resume') and
            st.session_state.get('analysis_selected_agent_id')
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button(
                "🔍 开始AI分析", 
                type="primary", 
                disabled=not can_analyze,
                use_container_width=True
            ):
                self._start_analysis({
                    'depth': analysis_depth,
                    'include_suggestions': include_suggestions,
                    'focus_areas': focus_areas,
                    'agent_id': st.session_state.get('analysis_selected_agent_id')
                })
        
        with col2:
            if st.button("📋 预览数据", disabled=not can_analyze):
                self._preview_analysis_data()
        
        with col3:
            if st.button("🔄 重置选择"):
                if 'analysis_selected_job' in st.session_state:
                    del st.session_state.analysis_selected_job
                if 'analysis_selected_resume' in st.session_state:
                    del st.session_state.analysis_selected_resume
                if 'analysis_selected_agent_id' in st.session_state:
                    del st.session_state.analysis_selected_agent_id
                st.rerun()
    
    def _render_current_analysis(self):
        """渲染当前分析结果"""
        st.subheader("📊 分析结果")
        
        current_analysis = st.session_state.get('current_analysis')
        
        if not current_analysis:
            st.info("还没有分析结果。请在开始分析标签页中选择职位和简历进行分析。")
            return
        
        # 显示分析结果
        self.analysis_manager.display_analysis_results(current_analysis)
        
        # 操作按钮
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 保存结果", type="primary"):
                if self.analysis_manager.add_analysis_to_session(current_analysis):
                    st.success("分析结果已保存到历史记录")
                    st.rerun()
        
        with col2:
            if st.button("📋 复制结果"):
                self._copy_analysis_results(current_analysis)
        
        with col3:
            if st.button("📊 重新分析"):
                # 清除当前结果，返回分析设置
                st.session_state.current_analysis = None
                st.rerun()
        
        with col4:
            if st.button("💬 生成打招呼语"):
                st.session_state.current_page = 'greeting'
                st.rerun()
    
    def _render_analysis_history(self):
        """渲染分析历史"""
        st.subheader("📈 历史分析记录")
        
        analyses = self.analysis_manager.get_analyses_list()
        
        if not analyses:
            st.info("还没有保存任何分析记录。")
            return
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总分析次数", len(analyses))
        with col2:
            avg_score = sum(a.get('overall_score', 0) for a in analyses) / len(analyses) if analyses else 0
            st.metric("平均匹配度", f"{avg_score:.2f}")
        with col3:
            high_match = len([a for a in analyses if a.get('overall_score', 0) > 0.8])
            st.metric("高匹配数量", high_match)
        with col4:
            recent_analyses = [a for a in analyses if a.get('created_at', '').startswith(str(st.date.today()))]
            st.metric("今日分析", len(recent_analyses))
        
        # 分析记录列表
        st.markdown("---")
        
        for i, analysis in enumerate(analyses):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    job_id = analysis.get('job_id')
                    resume_id = analysis.get('resume_id')
                    job = SessionManager.get_job_by_id(job_id) if job_id else None
                    resume = SessionManager.get_resume_by_id(resume_id) if resume_id else None
                    
                    job_title = job.get('title') if job else 'Unknown Job'
                    resume_name = resume.get('name') if resume else 'Unknown Resume'
                    
                    st.markdown(f"**{job_title}** vs **{resume_name}**")
                    if analysis.get('created_at'):
                        st.caption(f"📅 {analysis.get('created_at')[:16]}")
                
                with col2:
                    overall_score = analysis.get('overall_score', 0)
                    score_color = "🟢" if overall_score > 0.8 else "🟡" if overall_score > 0.6 else "🔴"
                    st.text(f"{score_color} 总体: {overall_score:.2f}")
                    
                    skill_score = analysis.get('skill_match_score', 0)
                    st.text(f"🛠️ 技能: {skill_score:.2f}")
                
                with col3:
                    exp_score = analysis.get('experience_score', 0)
                    st.text(f"💼 经验: {exp_score:.2f}")
                    
                    keyword_score = analysis.get('keyword_coverage', 0)
                    st.text(f"🔍 关键词: {keyword_score:.2f}")
                
                with col4:
                    if st.button("👁️", key=f"view_analysis_{i}", help="查看详情"):
                        st.session_state.current_analysis = analysis
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_analysis_{i}", help="删除"):
                        # 删除分析记录的逻辑
                        st.session_state.analyses = [a for a in st.session_state.analyses if a != analysis]
                        st.success("分析记录已删除")
                        st.rerun()
                
                st.markdown("---")
    
    def _start_analysis(self, options: Dict[str, Any]):
        """开始分析"""
        job = st.session_state.get('analysis_selected_job')
        resume = st.session_state.get('analysis_selected_resume')
        agent_id = options.get('agent_id')
        
        if not job or not resume:
            st.error("请先选择职位和简历")
            return
        
        if not agent_id:
            st.error("请选择AI分析Agent")
            return
        
        try:
            # 执行分析（传递agent_id）
            analysis_result = self.analysis_manager.analyze_match(job, resume, agent_id)
            
            if analysis_result:
                st.session_state.current_analysis = analysis_result
                st.success("✅ 分析完成！请查看分析结果标签页。")
                
                # 显示使用的Agent信息
                if 'agent_info' in analysis_result:
                    agent_info = analysis_result['agent_info']
                    st.info(f"🤖 使用Agent: {agent_info['name']} ({agent_info['type']})")
                
                # 自动切换到结果标签
                if st.button("📊 查看分析结果", type="secondary"):
                    st.rerun()
            else:
                st.error("分析失败，请稍后重试")
                
        except Exception as e:
            logger.error(f"分析过程中出错: {str(e)}")
            st.error(f"分析失败: {str(e)}")
    
    def _preview_analysis_data(self):
        """预览将要分析的数据"""
        job = st.session_state.get('analysis_selected_job')
        resume = st.session_state.get('analysis_selected_resume')
        
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
    
    def _copy_analysis_results(self, analysis: Dict[str, Any]):
        """复制分析结果"""
        result_text = f"""
分析结果摘要:
- 总体匹配度: {analysis.get('overall_score', 0):.2f}
- 技能匹配: {analysis.get('skill_match_score', 0):.2f}
- 经验匹配: {analysis.get('experience_score', 0):.2f}
- 关键词覆盖: {analysis.get('keyword_coverage', 0):.2f}

缺失技能: {', '.join(analysis.get('missing_skills', []))}
优势项: {', '.join(analysis.get('strengths', []))}
        """.strip()
        
        self.components.render_copy_button(result_text, "复制分析结果")
    
    async def _get_agent_manager(self) -> AgentManager:
        """获取Agent管理器"""
        if self._agent_manager is None:
            # 从session manager获取数据库管理器
            session_manager = SessionManager()
            db_manager = await session_manager.get_database_manager()
            ai_analyzer = AIAnalyzer()
            self._agent_manager = AgentManager(db_manager, ai_analyzer)
            await self._agent_manager.initialize()
        return self._agent_manager
    
    def _render_agent_selection(self):
        """渲染Agent选择界面"""
        try:
            # 加载可用的Agent
            agents = asyncio.run(self._load_available_agents())
            
            if not agents:
                st.warning("⚠️ 没有可用的AI Agent，请先到Agent管理页面创建Agent")
                if st.button("🔗 前往Agent管理"):
                    st.session_state.current_page = 'agents'
                    st.rerun()
                return
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Agent选择
                agent_options = {}
                for agent in agents:
                    display_name = f"{agent.name} ({agent.agent_type.value})"
                    if agent.is_builtin:
                        display_name += " 🏗️"
                    agent_options[display_name] = agent.id
                
                # 智能推荐Agent
                recommended_agent = self._get_recommended_agent(agents)
                default_index = 0
                if recommended_agent:
                    recommended_display = f"{recommended_agent.name} ({recommended_agent.agent_type.value})"
                    if recommended_agent.is_builtin:
                        recommended_display += " 🏗️"
                    
                    if recommended_display in agent_options:
                        default_index = list(agent_options.keys()).index(recommended_display)
                
                selected_agent_name = st.selectbox(
                    "选择AI分析Agent",
                    options=list(agent_options.keys()),
                    index=default_index,
                    help="选择用于分析的AI Agent。系统会根据职位类型推荐最适合的Agent。",
                    key="selected_analysis_agent"
                )
                
                if selected_agent_name:
                    selected_agent_id = agent_options[selected_agent_name]
                    st.session_state.analysis_selected_agent_id = selected_agent_id
                    
                    # 显示选中Agent的信息
                    selected_agent = next(a for a in agents if a.id == selected_agent_id)
                    self._display_agent_info(selected_agent)
            
            with col2:
                # 推荐信息
                if recommended_agent:
                    st.info(f"💡 **推荐Agent**\n\n{recommended_agent.name}\n\n基于当前职位类型推荐")
                
                # Agent使用统计
                if 'analysis_selected_agent_id' in st.session_state:
                    self._display_agent_stats(st.session_state.analysis_selected_agent_id)
        
        except Exception as e:
            st.error(f"加载Agent失败: {e}")
            logger.error(f"Failed to load agents: {e}")
    
    async def _load_available_agents(self) -> List[AIAgent]:
        """加载可用的Agent列表"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.get_all_agents()
    
    def _get_recommended_agent(self, agents: List[AIAgent]) -> Optional[AIAgent]:
        """获取推荐的Agent"""
        try:
            # 获取当前选择的职位
            selected_job = st.session_state.get('analysis_selected_job')
            if not selected_job:
                return None
            
            job_description = selected_job.get('description', '')
            if not job_description:
                return None
            
            # 使用AgentFactory获取推荐
            agent_manager = asyncio.run(self._get_agent_manager())
            factory = AgentFactory(agent_manager)
            recommended = asyncio.run(factory.get_recommended_agent(job_description))
            
            return recommended
            
        except Exception as e:
            logger.error(f"Failed to get recommended agent: {e}")
            return None
    
    def _display_agent_info(self, agent: AIAgent):
        """显示Agent信息"""
        with st.expander(f"📖 {agent.name} 详情"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**类型**: {agent.agent_type.value}")
                st.write(f"**是否内置**: {'是' if agent.is_builtin else '否'}")
            
            with col2:
                st.write(f"**使用次数**: {agent.usage_count}")
                if agent.average_rating > 0:
                    st.write(f"**平均评分**: {agent.average_rating:.2f}/5.0")
                else:
                    st.write("**平均评分**: 暂无评分")
            
            if agent.description:
                st.write(f"**描述**: {agent.description}")
            
            # Prompt预览
            with st.expander("查看Prompt模板"):
                st.code(agent.prompt_template, language="text")
    
    def _display_agent_stats(self, agent_id: int):
        """显示Agent统计信息"""
        try:
            stats = asyncio.run(self._get_agent_stats(agent_id))
            
            if stats:
                st.markdown("**📊 使用统计**")
                st.write(f"• 成功率: {stats.get('success_rate', 0)*100:.1f}%")
                st.write(f"• 平均执行时间: {stats.get('avg_execution_time', 0):.2f}秒")
                
        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
    
    async def _get_agent_stats(self, agent_id: int) -> Dict[str, Any]:
        """获取Agent统计信息"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.get_agent_statistics(agent_id)