"""AI Agent 模块测试

测试 AgentManager、CustomizableAgent 和 AgentFactory 的功能。
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.core.agents import (
    AgentManager, CustomizableAgent, AgentFactory, AnalysisContext, LLMAgent
)
from resume_assistant.data.models import AIAgent, AgentType, AgentUsageHistory
from resume_assistant.data.database import DatabaseManager
from resume_assistant.core.ai_analyzer import AIAnalyzer
from resume_assistant.utils.errors import ValidationError, AIAnalysisError


class TestAnalysisContext:
    """测试 AnalysisContext 数据类"""
    
    def test_analysis_context_creation(self):
        """测试创建 AnalysisContext"""
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发工程师",
            resume_content="有3年Python经验"
        )
        
        assert context.job_id == 1
        assert context.resume_id == 2
        assert context.job_description == "Python 开发工程师"
        assert context.resume_content == "有3年Python经验"
        assert context.job_skills is None
        assert context.resume_skills is None
        assert context.additional_context is None
    
    def test_analysis_context_with_skills(self):
        """测试带技能信息的 AnalysisContext"""
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Java 开发工程师",
            resume_content="有Java开发经验",
            job_skills=["Java", "Spring", "MySQL"],
            resume_skills=["Java", "Python", "Git"],
            additional_context={"company": "阿里巴巴"}
        )
        
        assert context.job_skills == ["Java", "Spring", "MySQL"]
        assert context.resume_skills == ["Java", "Python", "Git"]
        assert context.additional_context == {"company": "阿里巴巴"}


class TestCustomizableAgent:
    """测试 CustomizableAgent 类"""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Mock AI 分析器"""
        analyzer = Mock(spec=AIAnalyzer)
        analyzer.analyze_text = AsyncMock()
        return analyzer
    
    @pytest.fixture
    def valid_agent(self):
        """有效的 Agent 配置"""
        return AIAgent(
            id=1,
            name="测试Agent",
            description="用于测试",
            agent_type=AgentType.TECHNICAL,
            prompt_template="分析职位：{job_description}\\n简历：{resume_content}",
            is_builtin=False
        )
    
    def test_valid_prompt_template(self, valid_agent, mock_analyzer):
        """测试有效的 Prompt 模板"""
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        assert agent.agent == valid_agent
        assert agent.analyzer == mock_analyzer
    
    def test_invalid_prompt_template_missing_job_description(self, mock_analyzer):
        """测试缺少 job_description 的 Prompt 模板"""
        invalid_agent = AIAgent(
            name="无效Agent",
            agent_type=AgentType.GENERAL,
            prompt_template="只有简历：{resume_content}",  # 缺少 job_description
        )
        
        with pytest.raises(ValidationError, match="missing required variable: job_description"):
            CustomizableAgent(invalid_agent, mock_analyzer)
    
    def test_invalid_prompt_template_missing_resume_content(self, mock_analyzer):
        """测试缺少 resume_content 的 Prompt 模板"""
        invalid_agent = AIAgent(
            name="无效Agent",
            agent_type=AgentType.GENERAL,
            prompt_template="只有职位：{job_description}",  # 缺少 resume_content
        )
        
        with pytest.raises(ValidationError, match="missing required variable: resume_content"):
            CustomizableAgent(invalid_agent, mock_analyzer)
    
    def test_format_prompt_basic(self, valid_agent, mock_analyzer):
        """测试基础 Prompt 格式化"""
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发工程师",
            resume_content="有3年Python经验"
        )
        
        formatted = agent._format_prompt(context)
        expected = "分析职位：Python 开发工程师\\n简历：有3年Python经验"
        assert formatted == expected
    
    def test_format_prompt_with_skills(self, mock_analyzer):
        """测试包含技能的 Prompt 格式化"""
        agent_with_skills = AIAgent(
            name="技能Agent",
            agent_type=AgentType.TECHNICAL,
            prompt_template="职位：{job_description}\\n职位技能：{job_skills}\\n简历：{resume_content}\\n简历技能：{resume_skills}"
        )
        
        agent = CustomizableAgent(agent_with_skills, mock_analyzer)
        
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发",
            resume_content="Python经验",
            job_skills=["Python", "Django"],
            resume_skills=["Python", "Flask"]
        )
        
        formatted = agent._format_prompt(context)
        expected = "职位：Python 开发\\n职位技能：Python, Django\\n简历：Python经验\\n简历技能：Python, Flask"
        assert formatted == expected
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, valid_agent, mock_analyzer):
        """测试成功的分析"""
        # Mock AI 响应
        ai_response = '''{"overall_score": 85.0, "skill_match_score": 90.0, "strengths": ["Python经验丰富"]}'''
        mock_analyzer.analyze_text.return_value = ai_response
        
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发工程师",
            resume_content="有3年Python经验"
        )
        
        result = await agent.analyze(context)
        
        assert result["success"] == True
        assert result["agent_id"] == 1
        assert "execution_time" in result
        assert "analysis" in result
        assert result["analysis"]["overall_score"] == 85.0
        assert result["analysis"]["skill_match_score"] == 90.0
        assert "Python经验丰富" in result["analysis"]["strengths"]
        assert result["raw_response"] == ai_response
    
    @pytest.mark.asyncio
    async def test_analyze_failure(self, valid_agent, mock_analyzer):
        """测试分析失败"""
        # Mock AI 分析器抛出异常
        mock_analyzer.analyze_text.side_effect = Exception("API调用失败")
        
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发工程师",
            resume_content="有3年Python经验"
        )
        
        result = await agent.analyze(context)
        
        assert result["success"] == False
        assert result["agent_id"] == 1
        assert "execution_time" in result
        assert result["error"] == "API调用失败"
        assert result["raw_response"] == ""
        assert result["analysis"] == {}
    
    def test_parse_json_response(self, valid_agent, mock_analyzer):
        """测试解析 JSON 响应"""
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        
        json_response = '''{"overall_score": 85.0, "strengths": ["Python"]}'''
        result = agent._parse_response(json_response)
        
        assert result["overall_score"] == 85.0
        assert result["strengths"] == ["Python"]
    
    def test_parse_text_response(self, valid_agent, mock_analyzer):
        """测试解析文本响应"""
        agent = CustomizableAgent(valid_agent, mock_analyzer)
        
        text_response = """
        总体匹配度：85分
        技能匹配度：90分
        
        优势：
        - Python经验丰富
        - 项目经验充足
        
        缺失技能：
        - Docker经验不足
        - AWS部署经验缺乏
        """
        
        result = agent._extract_analysis_info(text_response)
        
        assert result["overall_score"] == 85.0
        assert result["skill_match_score"] == 90.0
        assert "Python经验丰富" in result["strengths"]
        # 检查至少提取了一些缺失技能信息
        assert len(result["missing_skills"]) > 0
        assert len(result["strengths"]) > 0


class TestAgentManager:
    """测试 AgentManager 类"""
    
    @pytest.fixture
    async def db_manager(self):
        """创建临时数据库管理器"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            manager = DatabaseManager(db_path)
            await manager.init_database()
            yield manager
        finally:
            if db_path.exists():
                db_path.unlink()
    
    @pytest.fixture
    def mock_analyzer(self):
        """Mock AI 分析器"""
        analyzer = Mock(spec=AIAnalyzer)
        analyzer.analyze_text = AsyncMock()
        return analyzer
    
    @pytest.fixture
    async def agent_manager(self, db_manager, mock_analyzer):
        """创建 Agent 管理器"""
        manager = AgentManager(db_manager, mock_analyzer)
        await manager.initialize()
        return manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent_manager):
        """测试管理器初始化"""
        # 应该创建了5个内置 Agent
        builtin_agents = await agent_manager.get_all_agents(include_custom=False)
        assert len(builtin_agents) == 5
        
        # 检查每种类型都有对应的 Agent
        agent_types = {agent.agent_type for agent in builtin_agents}
        expected_types = {
            AgentType.GENERAL, AgentType.TECHNICAL, AgentType.MANAGEMENT,
            AgentType.CREATIVE, AgentType.SALES
        }
        assert agent_types == expected_types
    
    @pytest.mark.asyncio
    async def test_create_custom_agent(self, agent_manager):
        """测试创建自定义 Agent"""
        agent_data = {
            "name": "自定义测试Agent",
            "description": "用于测试的自定义Agent",
            "agent_type": "custom",
            "prompt_template": "请分析：{job_description}和{resume_content}"
        }
        
        agent_id = await agent_manager.create_agent(agent_data)
        assert agent_id > 0
        
        # 验证创建的 Agent
        created_agent = await agent_manager.get_agent(agent_id)
        assert created_agent is not None
        assert created_agent.name == "自定义测试Agent"
        assert created_agent.agent_type == AgentType.CUSTOM
        assert created_agent.is_builtin == False
    
    @pytest.mark.asyncio
    async def test_create_agent_validation_error(self, agent_manager):
        """测试创建 Agent 时的验证错误"""
        # 缺少必需字段
        invalid_data = {
            "name": "无效Agent"
            # 缺少 agent_type 和 prompt_template
        }
        
        with pytest.raises(ValidationError, match="Missing required field"):
            await agent_manager.create_agent(invalid_data)
        
        # 无效的 agent_type
        invalid_type_data = {
            "name": "无效类型Agent",
            "agent_type": "invalid_type",
            "prompt_template": "{job_description}{resume_content}"
        }
        
        with pytest.raises(ValidationError, match="Invalid agent_type"):
            await agent_manager.create_agent(invalid_type_data)
        
        # 无效的 prompt_template
        invalid_prompt_data = {
            "name": "无效Prompt Agent",
            "agent_type": "general",
            "prompt_template": "只有职位描述"  # 缺少必需变量
        }
        
        with pytest.raises(ValidationError, match="must contain"):
            await agent_manager.create_agent(invalid_prompt_data)
    
    @pytest.mark.asyncio
    async def test_update_agent(self, agent_manager):
        """测试更新 Agent"""
        # 先创建一个自定义 Agent
        agent_data = {
            "name": "待更新Agent",
            "agent_type": "general",
            "prompt_template": "原始模板：{job_description}，{resume_content}"
        }
        agent_id = await agent_manager.create_agent(agent_data)
        
        # 更新 Agent
        updates = {
            "name": "已更新Agent",
            "description": "更新后的描述",
            "prompt_template": "新模板：{job_description}和{resume_content}"
        }
        
        success = await agent_manager.update_agent(agent_id, updates)
        assert success == True
        
        # 验证更新
        updated_agent = await agent_manager.get_agent(agent_id)
        assert updated_agent.name == "已更新Agent"
        assert updated_agent.description == "更新后的描述"
        assert "新模板" in updated_agent.prompt_template
    
    @pytest.mark.asyncio
    async def test_update_builtin_agent_error(self, agent_manager):
        """测试更新内置 Agent 的错误"""
        # 获取一个内置 Agent
        builtin_agents = await agent_manager.get_all_agents(include_custom=False)
        builtin_agent = builtin_agents[0]
        
        # 尝试更新内置 Agent 应该失败
        with pytest.raises(ValidationError, match="Cannot update builtin agent"):
            await agent_manager.update_agent(builtin_agent.id, {"name": "新名称"})
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_manager):
        """测试删除 Agent"""
        # 创建自定义 Agent
        agent_data = {
            "name": "待删除Agent",
            "agent_type": "general",
            "prompt_template": "{job_description}{resume_content}"
        }
        agent_id = await agent_manager.create_agent(agent_data)
        
        # 删除 Agent
        success = await agent_manager.delete_agent(agent_id)
        assert success == True
        
        # 验证删除
        deleted_agent = await agent_manager.get_agent(agent_id)
        assert deleted_agent is None
    
    @pytest.mark.asyncio
    async def test_delete_builtin_agent_error(self, agent_manager):
        """测试删除内置 Agent 的错误"""
        # 获取内置 Agent
        builtin_agents = await agent_manager.get_all_agents(include_custom=False)
        builtin_agent = builtin_agents[0]
        
        # 尝试删除内置 Agent 应该失败
        with pytest.raises(ValidationError, match="Cannot delete builtin agent"):
            await agent_manager.delete_agent(builtin_agent.id)
    
    @pytest.mark.asyncio
    async def test_analyze_with_agent(self, agent_manager, mock_analyzer):
        """测试使用 Agent 进行分析"""
        # Mock AI 响应
        mock_analyzer.analyze_text.return_value = '{"overall_score": 85.0}'
        
        # 获取一个内置 Agent
        agents = await agent_manager.get_all_agents(include_custom=False)
        agent = agents[0]
        
        context = AnalysisContext(
            job_id=1,
            resume_id=2,
            job_description="Python 开发工程师",
            resume_content="有3年Python经验"
        )
        
        result = await agent_manager.analyze_with_agent(agent.id, context)
        
        assert result["success"] == True
        assert result["agent_id"] == agent.id
        assert "execution_time" in result
        assert result["analysis"]["overall_score"] == 85.0
    
    @pytest.mark.asyncio
    async def test_get_agent_statistics(self, agent_manager):
        """测试获取 Agent 统计信息"""
        # 获取一个 Agent
        agents = await agent_manager.get_all_agents()
        agent = agents[0]
        
        stats = await agent_manager.get_agent_statistics(agent.id)
        
        # 新 Agent 应该有基础统计信息
        assert "usage_count" in stats
        assert "average_rating" in stats
        assert stats["usage_count"] >= 0


class TestAgentFactory:
    """测试 AgentFactory 类"""
    
    @pytest.fixture
    async def agent_manager(self):
        """Mock Agent Manager"""
        manager = Mock(spec=AgentManager)
        manager.get_agent = AsyncMock()
        manager.get_all_agents = AsyncMock()
        manager.ai_analyzer = Mock(spec=AIAnalyzer)
        return manager
    
    @pytest.fixture
    def agent_factory(self, agent_manager):
        """创建 Agent 工厂"""
        return AgentFactory(agent_manager)
    
    @pytest.mark.asyncio
    async def test_create_agent_instance(self, agent_factory, agent_manager):
        """测试创建 Agent 实例"""
        # Mock Agent
        mock_agent = AIAgent(
            id=1,
            name="测试Agent",
            agent_type=AgentType.TECHNICAL,
            prompt_template="测试：{job_description}{resume_content}"
        )
        agent_manager.get_agent.return_value = mock_agent
        
        instance = await agent_factory.create_agent_instance(1)
        
        assert instance is not None
        assert isinstance(instance, CustomizableAgent)
        assert instance.agent == mock_agent
    
    @pytest.mark.asyncio
    async def test_create_agent_instance_not_found(self, agent_factory, agent_manager):
        """测试创建不存在的 Agent 实例"""
        agent_manager.get_agent.return_value = None
        
        instance = await agent_factory.create_agent_instance(999)
        assert instance is None
    
    @pytest.mark.asyncio
    async def test_get_recommended_agent_technical(self, agent_factory, agent_manager):
        """测试技术岗位的 Agent 推荐"""
        # Mock 内置 Agents
        tech_agent = AIAgent(id=1, name="技术Agent", agent_type=AgentType.TECHNICAL, prompt_template="test")
        general_agent = AIAgent(id=2, name="通用Agent", agent_type=AgentType.GENERAL, prompt_template="test")
        
        agent_manager.get_all_agents.return_value = [tech_agent, general_agent]
        
        # 技术岗位描述
        job_desc = "我们招聘Python开发工程师，负责后端系统开发"
        
        recommended = await agent_factory.get_recommended_agent(job_desc)
        
        assert recommended == tech_agent
    
    @pytest.mark.asyncio
    async def test_get_recommended_agent_management(self, agent_factory, agent_manager):
        """测试管理岗位的 Agent 推荐"""
        # Mock Agents
        mgmt_agent = AIAgent(id=1, name="管理Agent", agent_type=AgentType.MANAGEMENT, prompt_template="test")
        general_agent = AIAgent(id=2, name="通用Agent", agent_type=AgentType.GENERAL, prompt_template="test")
        
        agent_manager.get_all_agents.return_value = [mgmt_agent, general_agent]
        
        # 管理岗位描述
        job_desc = "招聘项目经理，负责团队管理和项目推进"
        
        recommended = await agent_factory.get_recommended_agent(job_desc)
        
        assert recommended == mgmt_agent
    
    @pytest.mark.asyncio
    async def test_get_recommended_agent_default_general(self, agent_factory, agent_manager):
        """测试默认推荐通用 Agent"""
        # Mock Agents
        general_agent = AIAgent(id=1, name="通用Agent", agent_type=AgentType.GENERAL, prompt_template="test")
        
        agent_manager.get_all_agents.return_value = [general_agent]
        
        # 无特定关键词的职位描述
        job_desc = "我们在招聘一个职位"
        
        recommended = await agent_factory.get_recommended_agent(job_desc)
        
        assert recommended == general_agent


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])