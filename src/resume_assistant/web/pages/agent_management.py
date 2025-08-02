"""AI Agent 管理页面

提供AI Agent的创建、编辑、删除和管理功能。
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from ...core.agents import AgentManager, AgentFactory, AIAnalyzer
from ...data.models import AIAgent, AgentType, AgentUsageHistory
from ...data.database import DatabaseManager
from ...utils.errors import ValidationError, AIAnalysisError
from ...utils import get_logger
from ..components import UIComponents
from ..session_manager import SessionManager
from ..adapters import WebAgentManager
from ..user_experience import ConfirmationManager, NotificationManager, ValidationManager, FormManager, HelpManager

logger = get_logger(__name__)


class AgentManagementPage:
    """AI Agent 管理页面类"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.ui = UIComponents()
        self.web_agent_manager = WebAgentManager()
        self._agent_manager = None
        self._agent_factory = None
    
    async def _get_agent_manager(self) -> AgentManager:
        """获取Agent管理器"""
        if self._agent_manager is None:
            db_manager = await self.session_manager.get_database_manager()
            ai_analyzer = AIAnalyzer()
            self._agent_manager = AgentManager(db_manager, ai_analyzer)
            await self._agent_manager.initialize()
        return self._agent_manager
    
    async def _get_agent_factory(self) -> AgentFactory:
        """获取Agent工厂"""
        if self._agent_factory is None:
            agent_manager = await self._get_agent_manager()
            self._agent_factory = AgentFactory(agent_manager)
        return self._agent_factory
    
    def render(self):
        """渲染Agent管理页面"""
        st.header("🤖 AI Agent 管理")
        st.markdown("创建和管理自定义AI分析Agent，优化简历分析效果")
        
        # 页面选项卡
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Agent列表", 
            "➕ 创建Agent", 
            "📊 使用统计", 
            "🔬 Agent测试",
            "⚖️ Agent对比"
        ])
        
        with tab1:
            self._render_agent_list()
        
        with tab2:
            self._render_create_agent()
        
        with tab3:
            self._render_usage_statistics()
        
        with tab4:
            self._render_agent_testing()
        
        with tab5:
            self._render_agent_comparison()
    
    def _render_agent_list(self):
        """渲染Agent列表"""
        st.subheader("📋 Agent 列表")
        
        # 筛选选项
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            agent_type_filter = st.selectbox(
                "Agent类型筛选",
                options=["全部"] + [t.value for t in AgentType],
                key="agent_type_filter"
            )
        
        with col2:
            show_builtin = st.checkbox("显示内置Agent", value=True, key="show_builtin")
            show_custom = st.checkbox("显示自定义Agent", value=True, key="show_custom")
        
        with col3:
            if st.button("🔄 刷新列表", key="refresh_agents"):
                st.rerun()
        
        # 获取Agent列表
        try:
            agents = asyncio.run(self._load_agents(agent_type_filter, show_builtin, show_custom))
            
            if not agents:
                st.info("暂无Agent，请创建新的Agent")
                return
            
            # 显示Agent卡片
            self._display_agent_cards(agents)
            
        except Exception as e:
            st.error(f"加载Agent列表失败: {e}")
            logger.error(f"Failed to load agents: {e}")
    
    async def _load_agents(self, type_filter: str, show_builtin: bool, show_custom: bool) -> List[AIAgent]:
        """加载Agent列表"""
        agent_manager = await self._get_agent_manager()
        
        # 获取筛选类型
        filter_type = None if type_filter == "全部" else AgentType(type_filter)
        
        # 获取所有Agent
        all_agents = await agent_manager.get_all_agents(
            agent_type=filter_type,
            include_builtin=show_builtin,
            include_custom=show_custom
        )
        
        return all_agents
    
    def _display_agent_cards(self, agents: List[AIAgent]):
        """显示Agent卡片"""
        for agent in agents:
            with st.container():
                # Agent卡片
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                
                with col1:
                    # Agent基本信息
                    icon = "🏗️" if agent.is_builtin else "⚙️"
                    st.markdown(f"### {icon} {agent.name}")
                    st.caption(f"类型: {agent.agent_type.value} | ID: {agent.id}")
                    if agent.description:
                        st.markdown(f"📝 {agent.description}")
                
                with col2:
                    # 使用统计
                    st.metric("使用次数", agent.usage_count)
                
                with col3:
                    # 平均评分
                    rating_display = f"{agent.average_rating:.1f}/5.0" if agent.average_rating > 0 else "未评分"
                    st.metric("平均评分", rating_display)
                
                with col4:
                    # 操作按钮
                    button_col1, button_col2 = st.columns(2)
                    
                    with button_col1:
                        if st.button("📖 详情", key=f"view_{agent.id}"):
                            self._show_agent_details(agent)
                    
                    with button_col2:
                        if not agent.is_builtin:
                            if st.button("✏️ 编辑", key=f"edit_{agent.id}"):
                                self._edit_agent(agent)
                        else:
                            st.caption("内置Agent")
                
                # Prompt预览
                with st.expander(f"查看 {agent.name} 的Prompt模板"):
                    st.code(agent.prompt_template, language="text")
                
                st.divider()
    
    def _show_agent_details(self, agent: AIAgent):
        """显示Agent详细信息"""
        with st.expander(f"📖 {agent.name} 详细信息", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**基本信息**")
                st.write(f"• **名称**: {agent.name}")
                st.write(f"• **类型**: {agent.agent_type.value}")
                st.write(f"• **是否内置**: {'是' if agent.is_builtin else '否'}")
                st.write(f"• **创建时间**: {agent.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"• **更新时间**: {agent.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                st.markdown("**使用统计**")
                st.write(f"• **使用次数**: {agent.usage_count}")
                st.write(f"• **平均评分**: {agent.average_rating:.2f}/5.0")
                
                # 获取详细统计
                try:
                    stats = asyncio.run(self._get_agent_detailed_stats(agent.id))
                    if stats:
                        st.write(f"• **成功率**: {stats.get('success_rate', 0)*100:.1f}%")
                        st.write(f"• **平均执行时间**: {stats.get('avg_execution_time', 0):.2f}秒")
                except Exception as e:
                    st.warning(f"无法加载详细统计: {e}")
            
            if agent.description:
                st.markdown("**描述**")
                st.write(agent.description)
            
            st.markdown("**Prompt 模板**")
            st.code(agent.prompt_template, language="text")
            
            # 删除按钮（仅限自定义Agent）
            if not agent.is_builtin:
                st.markdown("---")
                if st.button(f"🗑️ 删除 {agent.name}", key=f"delete_{agent.id}", type="secondary"):
                    if st.button(f"确认删除？", key=f"confirm_delete_{agent.id}", type="primary"):
                        self._delete_agent(agent.id, agent.name)
    
    async def _get_agent_detailed_stats(self, agent_id: int) -> Dict[str, Any]:
        """获取Agent详细统计信息"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.get_agent_statistics(agent_id)
    
    def _edit_agent(self, agent: AIAgent):
        """编辑Agent"""
        with st.expander(f"✏️ 编辑 {agent.name}", expanded=True):
            with st.form(f"edit_agent_{agent.id}"):
                st.subheader(f"编辑 {agent.name}")
                
                # 编辑表单
                new_name = st.text_input("Agent名称", value=agent.name, key=f"edit_name_{agent.id}")
                new_description = st.text_area("描述", value=agent.description or "", key=f"edit_desc_{agent.id}")
                
                new_type = st.selectbox(
                    "Agent类型", 
                    options=[t.value for t in AgentType],
                    index=list(AgentType).index(agent.agent_type),
                    key=f"edit_type_{agent.id}"
                )
                
                new_prompt = st.text_area(
                    "Prompt模板",
                    value=agent.prompt_template,
                    height=200,
                    help="必须包含 {job_description} 和 {resume_content} 变量",
                    key=f"edit_prompt_{agent.id}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 保存修改", type="primary"):
                        self._save_agent_changes(agent.id, {
                            "name": new_name,
                            "description": new_description,
                            "agent_type": new_type,
                            "prompt_template": new_prompt
                        })
                
                with col2:
                    if st.form_submit_button("❌ 取消", type="secondary"):
                        st.rerun()
    
    def _save_agent_changes(self, agent_id: int, updates: Dict[str, Any]):
        """保存Agent修改"""
        try:
            success = asyncio.run(self._update_agent(agent_id, updates))
            if success:
                st.success("Agent更新成功！")
                st.rerun()
            else:
                st.error("Agent更新失败")
        except Exception as e:
            st.error(f"保存失败: {e}")
    
    async def _update_agent(self, agent_id: int, updates: Dict[str, Any]) -> bool:
        """更新Agent"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.update_agent(agent_id, updates)
    
    def _delete_agent(self, agent_id: int, agent_name: str):
        """删除Agent"""
        try:
            success = asyncio.run(self._remove_agent(agent_id))
            if success:
                st.success(f"Agent '{agent_name}' 删除成功！")
                st.rerun()
            else:
                st.error("删除失败")
        except Exception as e:
            st.error(f"删除失败: {e}")
    
    async def _remove_agent(self, agent_id: int) -> bool:
        """删除Agent"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.delete_agent(agent_id)
    
    def _render_create_agent(self):
        """渲染创建Agent表单"""
        st.subheader("➕ 创建新的 AI Agent")
        
        with st.form("create_agent_form"):
            # 基本信息
            st.markdown("**基本信息**")
            name = st.text_input(
                "Agent名称 *",
                placeholder="例如：金融行业专用Agent",
                help="为Agent起一个描述性的名称"
            )
            
            description = st.text_area(
                "Agent描述",
                placeholder="描述这个Agent的用途和特点...",
                help="可选，帮助用户理解此Agent的作用"
            )
            
            agent_type = st.selectbox(
                "Agent类型 *",
                options=[t.value for t in AgentType],
                index=5,  # 默认选择CUSTOM
                help="选择Agent的类型，影响推荐算法"
            )
            
            # Prompt模板
            st.markdown("**Prompt 模板**")
            st.info("💡 Prompt模板必须包含 `{job_description}` 和 `{resume_content}` 变量")
            
            # 提供预设模板选择
            template_choice = st.selectbox(
                "选择模板起点",
                options=[
                    "自定义模板",
                    "基于通用模板",
                    "基于技术岗位模板",
                    "基于管理岗位模板"
                ]
            )
            
            # 根据选择提供默认模板
            default_template = self._get_template_by_choice(template_choice)
            
            prompt_template = st.text_area(
                "Prompt模板 *",
                value=default_template,
                height=300,
                help="定义Agent如何分析简历。可以使用 {job_description}, {resume_content}, {job_skills}, {resume_skills} 等变量"
            )
            
            # 预览变量
            with st.expander("📋 可用变量说明"):
                st.markdown("""
                - `{job_description}`: 职位描述
                - `{resume_content}`: 简历内容
                - `{job_skills}`: 职位技能要求（逗号分隔）
                - `{resume_skills}`: 简历技能（逗号分隔）
                """)
            
            # 提交按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✨ 创建 Agent", type="primary"):
                    self._create_new_agent(name, description, agent_type, prompt_template)
            
            with col2:
                if st.form_submit_button("🧪 测试 Prompt", type="secondary"):
                    self._test_prompt_template(prompt_template)
    
    def _get_template_by_choice(self, choice: str) -> str:
        """根据选择获取模板"""
        if choice == "基于通用模板":
            return """请分析以下简历与职位的匹配度：

职位描述：{job_description}
简历内容：{resume_content}

请从以下维度进行分析：
1. 技能匹配度 (0-100分)
2. 经验匹配度 (0-100分)  
3. 关键词覆盖率 (0-100分)
4. 总体匹配度 (0-100分)
5. 缺失的关键技能
6. 简历优势
7. 改进建议

请以JSON格式返回结果，或者清晰地列出各项评分和建议。"""
        
        elif choice == "基于技术岗位模板":
            return """作为技术招聘专家，请深度分析以下技术岗位简历匹配度：

职位技能要求：{job_skills}
职位描述：{job_description}
简历技能：{resume_skills}
简历内容：{resume_content}

重点分析：
1. 编程语言匹配度
2. 技术栈相关性
3. 项目经验技术含量
4. 技术深度评估
5. 学习能力体现
6. 具体的技术改进建议

请提供详细的技术评估和具体的技能提升建议。"""
        
        elif choice == "基于管理岗位模板":
            return """作为管理岗位招聘专家，请分析以下管理岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 领导力体现
2. 团队管理经验
3. 项目管理能力
4. 战略思维展现
5. 沟通协调能力
6. 业绩管理经验
7. 管理经验的提升建议

请从管理者角度提供专业评估和发展建议。"""
        
        else:  # 自定义模板
            return """请分析以下简历与职位的匹配情况：

职位描述：{job_description}
简历内容：{resume_content}

请提供详细的分析和建议。"""
    
    def _test_prompt_template(self, template: str):
        """测试Prompt模板"""
        if not template.strip():
            st.error("Prompt模板不能为空")
            return
        
        # 验证必需变量
        required_vars = ["{job_description}", "{resume_content}"]
        missing_vars = [var for var in required_vars if var not in template]
        
        if missing_vars:
            st.error(f"Prompt模板缺少必需变量: {', '.join(missing_vars)}")
            return
        
        # 显示测试结果
        st.success("✅ Prompt模板验证通过！")
        
        # 提供示例预览
        with st.expander("🔍 模板预览（使用示例数据）"):
            sample_job = "Python开发工程师，负责后端API开发"
            sample_resume = "3年Python开发经验，熟悉Django框架"
            sample_job_skills = "Python, Django, MySQL"
            sample_resume_skills = "Python, Django, Git"
            
            try:
                formatted = template.format(
                    job_description=sample_job,
                    resume_content=sample_resume,
                    job_skills=sample_job_skills,
                    resume_skills=sample_resume_skills
                )
                st.code(formatted, language="text")
            except KeyError as e:
                st.warning(f"模板中包含未知变量: {e}")
    
    def _create_new_agent(self, name: str, description: str, agent_type: str, prompt_template: str):
        """创建新Agent"""
        # 验证输入
        if not name.strip():
            st.error("Agent名称不能为空")
            return
        
        if not prompt_template.strip():
            st.error("Prompt模板不能为空")
            return
        
        # 验证必需变量
        required_vars = ["{job_description}", "{resume_content}"]
        missing_vars = [var for var in required_vars if var not in prompt_template]
        
        if missing_vars:
            st.error(f"Prompt模板缺少必需变量: {', '.join(missing_vars)}")
            return
        
        try:
            # 创建Agent
            agent_data = {
                "name": name.strip(),
                "description": description.strip() if description else "",
                "agent_type": agent_type,
                "prompt_template": prompt_template.strip(),
                "is_builtin": False
            }
            
            agent_id = asyncio.run(self._create_agent(agent_data))
            
            st.success(f"🎉 Agent '{name}' 创建成功！ID: {agent_id}")
            st.info("请切换到 'Agent列表' 选项卡查看新创建的Agent")
            
            # 清空表单（通过重新运行）
            st.rerun()
            
        except Exception as e:
            st.error(f"创建Agent失败: {e}")
            logger.error(f"Failed to create agent: {e}")
    
    async def _create_agent(self, agent_data: Dict[str, Any]) -> int:
        """创建Agent"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.create_agent(agent_data)
    
    def _render_usage_statistics(self):
        """渲染使用统计"""
        st.subheader("📊 Agent 使用统计")
        
        try:
            # 获取所有Agent的统计信息
            stats_data = asyncio.run(self._load_usage_statistics())
            
            if not stats_data:
                st.info("暂无使用统计数据")
                return
            
            # 显示总体统计
            self._display_overall_statistics(stats_data)
            
            # 显示各Agent详细统计
            self._display_detailed_statistics(stats_data)
            
        except Exception as e:
            st.error(f"加载统计数据失败: {e}")
    
    async def _load_usage_statistics(self) -> List[Dict[str, Any]]:
        """加载使用统计数据"""
        agent_manager = await self._get_agent_manager()
        
        # 获取所有Agent
        agents = await agent_manager.get_all_agents()
        
        stats_data = []
        for agent in agents:
            stats = await agent_manager.get_agent_statistics(agent.id)
            stats_data.append({
                "agent": agent,
                "stats": stats
            })
        
        return stats_data
    
    def _display_overall_statistics(self, stats_data: List[Dict[str, Any]]):
        """显示总体统计"""
        # 计算总体指标
        total_usage = sum(data["agent"].usage_count for data in stats_data)
        total_agents = len(stats_data)
        builtin_agents = sum(1 for data in stats_data if data["agent"].is_builtin)
        custom_agents = total_agents - builtin_agents
        
        # 显示总体指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总Agent数", total_agents)
        
        with col2:
            st.metric("内置Agent", builtin_agents)
        
        with col3:
            st.metric("自定义Agent", custom_agents)
        
        with col4:
            st.metric("总使用次数", total_usage)
        
        st.divider()
    
    def _display_detailed_statistics(self, stats_data: List[Dict[str, Any]]):
        """显示详细统计"""
        st.markdown("### 各Agent详细统计")
        
        # 按使用次数排序
        sorted_data = sorted(stats_data, key=lambda x: x["agent"].usage_count, reverse=True)
        
        for data in sorted_data:
            agent = data["agent"]
            stats = data["stats"]
            
            with st.expander(f"{agent.name} - 使用次数: {agent.usage_count}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**基本统计**")
                    st.write(f"• 使用次数: {agent.usage_count}")
                    st.write(f"• 平均评分: {agent.average_rating:.2f}/5.0")
                    st.write(f"• Agent类型: {agent.agent_type.value}")
                    st.write(f"• 是否内置: {'是' if agent.is_builtin else '否'}")
                
                with col2:
                    st.markdown("**性能统计**")
                    if stats:
                        st.write(f"• 成功率: {stats.get('success_rate', 0)*100:.1f}%")
                        st.write(f"• 平均执行时间: {stats.get('avg_execution_time', 0):.2f}秒")
                        st.write(f"• 评分次数: {stats.get('rating_count', 0)}")
                        st.write(f"• 用户评分: {stats.get('avg_user_rating', 0):.2f}/5.0")
                    else:
                        st.write("暂无性能数据")
    
    def _render_agent_testing(self):
        """渲染Agent测试"""
        st.subheader("🔬 Agent 测试")
        
        # 选择要测试的Agent
        try:
            agents = asyncio.run(self._load_all_agents())
            
            if not agents:
                st.warning("没有可用的Agent进行测试")
                return
            
            agent_options = {f"{agent.name} ({agent.agent_type.value})": agent.id for agent in agents}
            
            selected_agent_name = st.selectbox(
                "选择要测试的Agent",
                options=list(agent_options.keys()),
                key="test_agent_select"
            )
            
            if selected_agent_name:
                agent_id = agent_options[selected_agent_name]
                selected_agent = next(agent for agent in agents if agent.id == agent_id)
                
                # 测试表单
                self._render_agent_test_form(selected_agent)
                
        except Exception as e:
            st.error(f"加载Agent列表失败: {e}")
    
    async def _load_all_agents(self) -> List[AIAgent]:
        """加载所有Agent"""
        agent_manager = await self._get_agent_manager()
        return await agent_manager.get_all_agents()
    
    def _render_agent_test_form(self, agent: AIAgent):
        """渲染Agent测试表单"""
        st.markdown(f"### 测试 {agent.name}")
        st.markdown(f"**类型**: {agent.agent_type.value}")
        
        with st.form(f"test_agent_{agent.id}"):
            # 测试数据输入
            col1, col2 = st.columns(2)
            
            with col1:
                test_job_desc = st.text_area(
                    "职位描述",
                    value="Python后端开发工程师，负责API开发和数据库设计，要求3年以上开发经验。",
                    height=150,
                    key=f"test_job_{agent.id}"
                )
            
            with col2:
                test_resume = st.text_area(
                    "简历内容",
                    value="有3年Python开发经验，熟悉Django、Flask框架，有MySQL数据库经验。",
                    height=150,
                    key=f"test_resume_{agent.id}"
                )
            
            # 可选技能输入
            col3, col4 = st.columns(2)
            
            with col3:
                test_job_skills = st.text_input(
                    "职位技能（可选，逗号分隔）",
                    value="Python,Django,MySQL,Redis",
                    key=f"test_job_skills_{agent.id}"
                )
            
            with col4:
                test_resume_skills = st.text_input(
                    "简历技能（可选，逗号分隔）",
                    value="Python,Django,MySQL,Git",
                    key=f"test_resume_skills_{agent.id}"
                )
            
            # 提交测试
            if st.form_submit_button("🧪 开始测试", type="primary"):
                self._run_agent_test(
                    agent, test_job_desc, test_resume, 
                    test_job_skills, test_resume_skills
                )
    
    def _run_agent_test(self, agent: AIAgent, job_desc: str, resume_content: str, 
                       job_skills: str, resume_skills: str):
        """运行Agent测试"""
        if not job_desc.strip() or not resume_content.strip():
            st.error("职位描述和简历内容不能为空")
            return
        
        try:
            with st.spinner(f"正在使用 {agent.name} 进行分析..."):
                # 运行测试
                result = asyncio.run(self._execute_agent_test(
                    agent.id, job_desc, resume_content, job_skills, resume_skills
                ))
                
                # 显示结果
                self._display_test_result(agent, result)
                
        except Exception as e:
            st.error(f"测试失败: {e}")
            logger.error(f"Agent test failed: {e}")
    
    async def _execute_agent_test(self, agent_id: int, job_desc: str, resume_content: str,
                                job_skills: str, resume_skills: str) -> Dict[str, Any]:
        """执行Agent测试"""
        from ...core.agents import AnalysisContext
        
        agent_manager = await self._get_agent_manager()
        
        # 构建测试上下文
        context = AnalysisContext(
            job_id=0,  # 测试用的虚拟ID
            resume_id=0,  # 测试用的虚拟ID
            job_description=job_desc,
            resume_content=resume_content,
            job_skills=job_skills.split(",") if job_skills else [],
            resume_skills=resume_skills.split(",") if resume_skills else []
        )
        
        # 执行分析
        result = await agent_manager.analyze_with_agent(agent_id, context)
        return result
    
    def _display_test_result(self, agent: AIAgent, result: Dict[str, Any]):
        """显示测试结果"""
        st.markdown("### 🔍 测试结果")
        
        if result["success"]:
            # 显示分析结果
            analysis = result["analysis"]
            
            # 评分指标
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总体匹配度", f"{analysis.get('overall_score', 0):.1f}/100")
            
            with col2:
                st.metric("技能匹配度", f"{analysis.get('skill_match_score', 0):.1f}/100")
            
            with col3:
                st.metric("经验匹配度", f"{analysis.get('experience_score', 0):.1f}/100")
            
            with col4:
                st.metric("关键词覆盖", f"{analysis.get('keyword_coverage', 0):.1f}/100")
            
            # 详细分析
            col5, col6 = st.columns(2)
            
            with col5:
                st.markdown("**🎯 简历优势**")
                strengths = analysis.get("strengths", [])
                if strengths:
                    for strength in strengths:
                        st.write(f"• {strength}")
                else:
                    st.write("未识别到明显优势")
            
            with col6:
                st.markdown("**⚠️ 缺失技能**")
                missing_skills = analysis.get("missing_skills", [])
                if missing_skills:
                    for skill in missing_skills:
                        st.write(f"• {skill}")
                else:
                    st.write("无明显缺失技能")
            
            # 性能信息
            st.markdown("**⚡ 性能信息**")
            st.write(f"• 执行时间: {result['execution_time']:.2f} 秒")
            st.write(f"• Agent: {agent.name} ({agent.agent_type.value})")
            
            # 原始响应
            with st.expander("🔤 AI原始响应"):
                st.code(result["raw_response"], language="text")
            
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")
            
            # 错误详情
            with st.expander("错误详情"):
                st.code(str(result), language="json")
    
    def _render_agent_comparison(self):
        """渲染Agent对比功能"""
        st.subheader("⚖️ Agent 效果对比")
        st.markdown("选择多个Agent进行对比分析，了解不同Agent的分析效果差异")
        
        try:
            # 加载可用的Agent
            agents = asyncio.run(self._load_all_agents())
            
            if len(agents) < 2:
                st.warning("⚠️ 至少需要2个Agent才能进行对比")
                return
            
            # Agent选择
            st.markdown("### 🎯 选择要对比的Agent")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                agent_options = {f"{agent.name} ({agent.agent_type.value})": agent.id for agent in agents}
                
                selected_agents = st.multiselect(
                    "选择要对比的Agent（2-4个）",
                    options=list(agent_options.keys()),
                    max_selections=4,
                    help="选择2-4个Agent进行对比分析",
                    key="comparison_agents"
                )
                
                if len(selected_agents) < 2:
                    st.info("请至少选择2个Agent进行对比")
                    return
                
                selected_agent_ids = [agent_options[name] for name in selected_agents]
            
            with col2:
                st.markdown("**选中的Agent**")
                for name in selected_agents:
                    agent_id = agent_options[name]
                    agent = next(a for a in agents if a.id == agent_id)
                    icon = "🏗️" if agent.is_builtin else "⚙️"
                    st.write(f"{icon} {agent.name}")
            
            # 测试数据输入
            st.markdown("---")
            st.markdown("### 📝 测试数据")
            
            col1, col2 = st.columns(2)
            
            with col1:
                test_job_desc = st.text_area(
                    "职位描述",
                    value="Python后端开发工程师，负责微服务架构开发，要求3年以上Python经验，熟悉Django/Flask，了解MySQL和Redis。",
                    height=150,
                    key="comparison_job_desc"
                )
            
            with col2:
                test_resume = st.text_area(
                    "简历内容",
                    value="有4年Python开发经验，熟悉Django、Flask框架，有MySQL、Redis、Docker经验，参与过微服务项目开发。",
                    height=150,
                    key="comparison_resume"
                )
            
            # 可选技能输入
            col3, col4 = st.columns(2)
            
            with col3:
                test_job_skills = st.text_input(
                    "职位技能（可选，逗号分隔）",
                    value="Python,Django,MySQL,Redis,Docker",
                    key="comparison_job_skills"
                )
            
            with col4:
                test_resume_skills = st.text_input(
                    "简历技能（可选，逗号分隔）",
                    value="Python,Django,Flask,MySQL,Redis,Docker",
                    key="comparison_resume_skills"
                )
            
            # 开始对比按钮
            st.markdown("---")
            
            if st.button("🚀 开始Agent对比分析", type="primary", use_container_width=True):
                self._run_agent_comparison(
                    selected_agent_ids, test_job_desc, test_resume, 
                    test_job_skills, test_resume_skills
                )
        
        except Exception as e:
            st.error(f"加载Agent对比功能失败: {e}")
            logger.error(f"Failed to load agent comparison: {e}")
    
    def _run_agent_comparison(self, agent_ids: List[int], job_desc: str, resume_content: str,
                            job_skills: str, resume_skills: str):
        """运行Agent对比分析"""
        if not job_desc.strip() or not resume_content.strip():
            st.error("职位描述和简历内容不能为空")
            return
        
        if len(agent_ids) < 2:
            st.error("请至少选择2个Agent进行对比")
            return
        
        try:
            with st.spinner("正在进行Agent对比分析..."):
                # 运行对比分析
                comparison_result = asyncio.run(self._execute_agent_comparison(
                    agent_ids, job_desc, resume_content, job_skills, resume_skills
                ))
                
                # 显示对比结果
                self._display_comparison_results(comparison_result)
                
        except Exception as e:
            st.error(f"对比分析失败: {e}")
            logger.error(f"Agent comparison failed: {e}")
    
    async def _execute_agent_comparison(self, agent_ids: List[int], job_desc: str, 
                                      resume_content: str, job_skills: str, 
                                      resume_skills: str) -> Dict[str, Any]:
        """执行Agent对比分析"""
        from ...core.agents import AgentAnalysisIntegrator
        
        # 获取Agent管理器和集成器
        agent_manager = await self._get_agent_manager()
        db_manager = await self.session_manager.get_database_manager()
        integrator = AgentAnalysisIntegrator(agent_manager, db_manager)
        
        # 执行对比分析
        result = await integrator.compare_agents(
            job_description=job_desc,
            resume_content=resume_content,
            job_id=0,  # 测试用虚拟ID
            resume_id=0,  # 测试用虚拟ID
            agent_ids=agent_ids,
            job_skills=job_skills.split(",") if job_skills else [],
            resume_skills=resume_skills.split(",") if resume_skills else []
        )
        
        return result
    
    def _display_comparison_results(self, comparison_result: Dict[str, Any]):
        """显示对比分析结果"""
        st.markdown("---")
        st.subheader("📊 Agent对比分析结果")
        
        if not comparison_result.get("success"):
            st.error(f"对比分析失败: {comparison_result.get('error', '未知错误')}")
            return
        
        results = comparison_result.get("results", [])
        comparison = comparison_result.get("comparison", {})
        
        if not results:
            st.warning("没有成功的分析结果")
            return
        
        # 显示最佳Agent
        if "best_agent" in comparison:
            best = comparison["best_agent"]
            st.success(f"🏆 **最佳Agent**: {best['agent_name']} ({best['agent_type']}) - 总体匹配度: {best['overall_score']:.1f}/100")
        
        # 显示各Agent详细结果
        st.markdown("### 📋 各Agent分析结果")
        
        # 创建对比表格
        cols = st.columns(len(results))
        
        for i, result in enumerate(results):
            with cols[i]:
                agent_name = result["agent_name"]
                agent_type = result["agent_type"]
                analysis = result["analysis"]
                execution_time = result["execution_time"]
                
                st.markdown(f"#### {agent_name}")
                st.caption(f"类型: {agent_type}")
                
                # 显示评分
                st.metric("总体匹配度", f"{analysis.get('overall_score', 0):.1f}/100")
                st.metric("技能匹配度", f"{analysis.get('skill_match_score', 0):.1f}/100")
                st.metric("经验匹配度", f"{analysis.get('experience_score', 0):.1f}/100")
                st.metric("关键词覆盖", f"{analysis.get('keyword_coverage', 0):.1f}/100")
                
                # 执行时间
                st.caption(f"⏱️ 执行时间: {execution_time:.2f}秒")
                
                # 优势和缺失技能
                with st.expander(f"📋 {agent_name} 详细分析"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🎯 优势**")
                        strengths = analysis.get("strengths", [])
                        if strengths:
                            for strength in strengths[:3]:  # 显示前3个
                                st.write(f"• {strength}")
                        else:
                            st.write("无明显优势")
                    
                    with col2:
                        st.markdown("**⚠️缺失技能**")
                        missing = analysis.get("missing_skills", [])
                        if missing:
                            for skill in missing[:3]:  # 显示前3个
                                st.write(f"• {skill}")
                        else:
                            st.write("无明显缺失")
        
        # 显示统计对比
        st.markdown("---")
        st.markdown("### 📈 统计对比")
        
        if comparison:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if "overall_score" in comparison:
                    stats = comparison["overall_score"]
                    st.metric(
                        "总体匹配度", 
                        f"{stats['average']:.1f}/100",
                        delta=f"±{stats.get('variance', 0):.1f}"
                    )
            
            with col2:
                if "skill_match_score" in comparison:
                    stats = comparison["skill_match_score"]
                    st.metric(
                        "技能匹配度", 
                        f"{stats['average']:.1f}/100",
                        delta=f"±{stats.get('variance', 0):.1f}"
                    )
            
            with col3:
                if "experience_score" in comparison:
                    stats = comparison["experience_score"]
                    st.metric(
                        "经验匹配度", 
                        f"{stats['average']:.1f}/100",
                        delta=f"±{stats.get('variance', 0):.1f}"
                    )
            
            with col4:
                if "keyword_coverage" in comparison:
                    stats = comparison["keyword_coverage"]
                    st.metric(
                        "关键词覆盖", 
                        f"{stats['average']:.1f}/100",
                        delta=f"±{stats.get('variance', 0):.1f}"
                    )
        
        # 分析建议
        st.markdown("---")
        st.markdown("### 💡 分析建议")
        
        if len(results) > 1:
            # 找出得分差异最大的指标
            scores_by_metric = {}
            for metric in ["overall_score", "skill_match_score", "experience_score", "keyword_coverage"]:
                scores = [r["analysis"].get(metric, 0) for r in results]
                if scores:
                    scores_by_metric[metric] = {
                        "max": max(scores),
                        "min": min(scores),
                        "diff": max(scores) - min(scores)
                    }
            
            if scores_by_metric:
                max_diff_metric = max(scores_by_metric.keys(), key=lambda k: scores_by_metric[k]["diff"])
                max_diff = scores_by_metric[max_diff_metric]["diff"]
                
                st.info(f"""
                📊 **对比分析摘要**:
                
                • 参与对比的Agent数量: {len(results)}个
                • 差异最大的指标: {max_diff_metric} (差值: {max_diff:.1f}分)
                • 建议: 根据具体需求选择在该指标上表现最好的Agent
                """)
        
        # 导出对比结果
        if st.button("📄 导出对比结果", type="secondary"):
            self._export_comparison_results(comparison_result)
    
    def _export_comparison_results(self, comparison_result: Dict[str, Any]):
        """导出对比结果"""
        try:
            import json
            from datetime import datetime
            
            # 准备导出数据
            export_data = {
                "comparison_timestamp": datetime.now().isoformat(),
                "results": comparison_result.get("results", []),
                "comparison_stats": comparison_result.get("comparison", {}),
                "summary": {
                    "total_agents": len(comparison_result.get("results", [])),
                    "best_agent": comparison_result.get("comparison", {}).get("best_agent", {})
                }
            }
            
            # 生成JSON字符串
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            # 提供下载
            st.download_button(
                label="💾 下载对比结果 (JSON)",
                data=json_str,
                file_name=f"agent_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("对比结果已准备好下载！")
            
        except Exception as e:
            st.error(f"导出失败: {e}")