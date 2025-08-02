"""AI Agent 数据层测试

测试 AI Agent 相关的数据模型、数据库表结构和 CRUD 操作。
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_assistant.data.models import AIAgent, AgentUsageHistory, AgentType, MatchAnalysis
from resume_assistant.data.database import DatabaseManager
from resume_assistant.utils.errors import DatabaseError


class TestAIAgentDataModels:
    """测试 AI Agent 数据模型"""
    
    def test_agent_type_enum(self):
        """测试 AgentType 枚举"""
        assert AgentType.GENERAL.value == "general"
        assert AgentType.TECHNICAL.value == "technical"
        assert AgentType.MANAGEMENT.value == "management"
        assert AgentType.CREATIVE.value == "creative"
        assert AgentType.SALES.value == "sales"
        assert AgentType.CUSTOM.value == "custom"
    
    def test_ai_agent_creation(self):
        """测试 AIAgent 创建"""
        agent = AIAgent(
            name="测试Agent",
            description="用于测试的Agent",
            agent_type=AgentType.TECHNICAL,
            prompt_template="测试Prompt: {job_description}, {resume_content}",
            is_builtin=False
        )
        
        assert agent.name == "测试Agent"
        assert agent.description == "用于测试的Agent"
        assert agent.agent_type == AgentType.TECHNICAL
        assert agent.prompt_template == "测试Prompt: {job_description}, {resume_content}"
        assert agent.is_builtin == False
        assert agent.usage_count == 0
        assert agent.average_rating == 0.0
        assert isinstance(agent.created_at, datetime)
        assert isinstance(agent.updated_at, datetime)
    
    def test_ai_agent_to_dict(self):
        """测试 AIAgent 转字典"""
        agent = AIAgent(
            name="测试Agent",
            agent_type=AgentType.TECHNICAL,
            prompt_template="测试Prompt"
        )
        
        data = agent.to_dict()
        
        assert data['name'] == "测试Agent"
        assert data['agent_type'] == "technical"
        assert data['prompt_template'] == "测试Prompt"
        assert data['is_builtin'] == False
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_ai_agent_from_dict(self):
        """测试从字典创建 AIAgent"""
        data = {
            'id': 1,
            'name': '测试Agent',
            'description': '测试描述',
            'agent_type': 'technical',
            'prompt_template': '测试Prompt',
            'is_builtin': True,
            'usage_count': 5,
            'average_rating': 4.5,
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        }
        
        agent = AIAgent.from_dict(data)
        
        assert agent.id == 1
        assert agent.name == '测试Agent'
        assert agent.agent_type == AgentType.TECHNICAL
        assert agent.is_builtin == True
        assert agent.usage_count == 5
        assert agent.average_rating == 4.5
        assert isinstance(agent.created_at, datetime)
    
    def test_agent_usage_history_creation(self):
        """测试 AgentUsageHistory 创建"""
        usage = AgentUsageHistory(
            agent_id=1,
            analysis_id=10,
            rating=4.5,
            feedback="很好用",
            execution_time=2.3,
            success=True
        )
        
        assert usage.agent_id == 1
        assert usage.analysis_id == 10
        assert usage.rating == 4.5
        assert usage.feedback == "很好用"
        assert usage.execution_time == 2.3
        assert usage.success == True
        assert usage.error_message == ""
        assert isinstance(usage.created_at, datetime)
    
    def test_agent_usage_history_to_dict(self):
        """测试 AgentUsageHistory 转字典"""
        usage = AgentUsageHistory(
            agent_id=1,
            analysis_id=10,
            rating=4.5,
            execution_time=2.3
        )
        
        data = usage.to_dict()
        
        assert data['agent_id'] == 1
        assert data['analysis_id'] == 10
        assert data['rating'] == 4.5
        assert data['execution_time'] == 2.3
        assert 'created_at' in data
    
    def test_agent_usage_history_from_dict(self):
        """测试从字典创建 AgentUsageHistory"""
        data = {
            'id': 1,
            'agent_id': 5,
            'analysis_id': 20,
            'rating': 3.5,
            'feedback': '还不错',
            'execution_time': 1.8,
            'success': True,
            'error_message': '',
            'created_at': '2024-01-01T10:00:00'
        }
        
        usage = AgentUsageHistory.from_dict(data)
        
        assert usage.id == 1
        assert usage.agent_id == 5
        assert usage.analysis_id == 20
        assert usage.rating == 3.5
        assert usage.feedback == '还不错'
        assert usage.execution_time == 1.8
        assert usage.success == True
        assert isinstance(usage.created_at, datetime)
    
    def test_match_analysis_with_agent(self):
        """测试带 Agent 信息的 MatchAnalysis"""
        analysis = MatchAnalysis(
            job_id=1,
            resume_id=2,
            agent_id=3,
            overall_score=85.5,
            raw_response="AI分析结果...",
            execution_time=3.2
        )
        
        assert analysis.job_id == 1
        assert analysis.resume_id == 2
        assert analysis.agent_id == 3
        assert analysis.overall_score == 85.5
        assert analysis.raw_response == "AI分析结果..."
        assert analysis.execution_time == 3.2


class TestAIAgentDatabase:
    """测试 AI Agent 数据库操作"""
    
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
    
    @pytest.mark.asyncio
    async def test_save_and_get_agent(self, db_manager):
        """测试保存和获取 Agent"""
        # 创建测试 Agent
        agent = AIAgent(
            name="技术专家Agent",
            description="专门分析技术岗位",
            agent_type=AgentType.TECHNICAL,
            prompt_template="分析技术职位: {job_description}\n简历: {resume_content}",
            is_builtin=True
        )
        
        # 保存 Agent
        agent_id = await db_manager.save_agent(agent)
        assert agent_id > 0
        
        # 获取 Agent
        retrieved_agent = await db_manager.get_agent(agent_id)
        assert retrieved_agent is not None
        assert retrieved_agent.name == "技术专家Agent"
        assert retrieved_agent.agent_type == AgentType.TECHNICAL
        assert retrieved_agent.is_builtin == True
        assert retrieved_agent.id == agent_id
    
    @pytest.mark.asyncio
    async def test_get_all_agents(self, db_manager):
        """测试获取所有 Agent"""
        # 创建多个测试 Agent
        agents_data = [
            AIAgent(
                name="通用Agent",
                agent_type=AgentType.GENERAL,
                prompt_template="通用分析",
                is_builtin=True
            ),
            AIAgent(
                name="自定义Agent",
                agent_type=AgentType.CUSTOM,
                prompt_template="自定义分析",
                is_builtin=False
            ),
            AIAgent(
                name="管理Agent",
                agent_type=AgentType.MANAGEMENT,
                prompt_template="管理岗位分析",
                is_builtin=True
            )
        ]
        
        # 保存所有 Agent
        saved_ids = []
        for agent in agents_data:
            agent_id = await db_manager.save_agent(agent)
            saved_ids.append(agent_id)
        
        # 获取所有 Agent
        all_agents = await db_manager.get_all_agents()
        assert len(all_agents) == 3
        
        # 获取仅内置 Agent
        all_agents_builtin = await db_manager.get_all_agents(include_builtin=True)
        builtin_agents = [a for a in all_agents_builtin if a.is_builtin]
        assert len(builtin_agents) == 2
        
        # 获取仅自定义 Agent
        custom_agents = await db_manager.get_all_agents(include_builtin=False)
        assert len(custom_agents) == 1
        assert custom_agents[0].agent_type == AgentType.CUSTOM
        
        # 按类型筛选
        tech_agents = await db_manager.get_all_agents(agent_type=AgentType.MANAGEMENT)
        assert len(tech_agents) == 1
        assert tech_agents[0].name == "管理Agent"
    
    @pytest.mark.asyncio
    async def test_update_agent(self, db_manager):
        """测试更新 Agent"""
        # 创建和保存 Agent
        agent = AIAgent(
            name="原始Agent",
            description="原始描述",
            agent_type=AgentType.GENERAL,
            prompt_template="原始Prompt"
        )
        
        agent_id = await db_manager.save_agent(agent)
        agent.id = agent_id
        
        # 更新 Agent
        agent.name = "更新后Agent"
        agent.description = "更新后描述"
        agent.agent_type = AgentType.TECHNICAL
        agent.prompt_template = "更新后Prompt"
        
        success = await db_manager.update_agent(agent)
        assert success == True
        
        # 验证更新
        updated_agent = await db_manager.get_agent(agent_id)
        assert updated_agent.name == "更新后Agent"
        assert updated_agent.description == "更新后描述"
        assert updated_agent.agent_type == AgentType.TECHNICAL
        assert updated_agent.prompt_template == "更新后Prompt"
        assert updated_agent.updated_at > updated_agent.created_at
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, db_manager):
        """测试删除 Agent"""
        # 创建内置 Agent
        builtin_agent = AIAgent(
            name="内置Agent",
            agent_type=AgentType.GENERAL,
            prompt_template="内置Prompt",
            is_builtin=True
        )
        builtin_id = await db_manager.save_agent(builtin_agent)
        
        # 创建自定义 Agent
        custom_agent = AIAgent(
            name="自定义Agent",
            agent_type=AgentType.CUSTOM,
            prompt_template="自定义Prompt",
            is_builtin=False
        )
        custom_id = await db_manager.save_agent(custom_agent)
        
        # 尝试删除内置 Agent（应该失败）
        with pytest.raises(DatabaseError):
            await db_manager.delete_agent(builtin_id)
        
        # 删除自定义 Agent（应该成功）
        deleted = await db_manager.delete_agent(custom_id)
        assert deleted == True
        
        # 验证删除
        deleted_agent = await db_manager.get_agent(custom_id)
        assert deleted_agent is None
        
        # 内置 Agent 应该仍然存在
        builtin_still_exists = await db_manager.get_agent(builtin_id)
        assert builtin_still_exists is not None
    
    @pytest.mark.asyncio
    async def test_update_agent_usage(self, db_manager):
        """测试更新 Agent 使用统计"""
        # 创建 Agent
        agent = AIAgent(
            name="测试Agent",
            agent_type=AgentType.GENERAL,
            prompt_template="测试"
        )
        agent_id = await db_manager.save_agent(agent)
        
        # 第一次使用，评分 4.0
        success = await db_manager.update_agent_usage(agent_id, 4.0)
        assert success == True
        
        # 检查统计信息
        updated_agent = await db_manager.get_agent(agent_id)
        assert updated_agent.usage_count == 1
        assert updated_agent.average_rating == 4.0
        
        # 第二次使用，评分 5.0
        await db_manager.update_agent_usage(agent_id, 5.0)
        
        # 检查统计信息
        updated_agent = await db_manager.get_agent(agent_id)
        assert updated_agent.usage_count == 2
        assert updated_agent.average_rating == 4.5  # (4.0 + 5.0) / 2
        
        # 第三次使用，无评分
        await db_manager.update_agent_usage(agent_id)
        
        # 检查统计信息
        updated_agent = await db_manager.get_agent(agent_id)
        assert updated_agent.usage_count == 3
        assert updated_agent.average_rating == 4.5  # 平均评分不变
    
    @pytest.mark.asyncio
    async def test_agent_usage_history(self, db_manager):
        """测试 Agent 使用历史"""
        # 创建 Agent
        agent = AIAgent(name="测试Agent", agent_type=AgentType.GENERAL, prompt_template="测试")
        agent_id = await db_manager.save_agent(agent)
        
        # 创建使用历史记录
        usage_records = [
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=1,
                rating=4.0,
                feedback="很好用",
                execution_time=2.5,
                success=True
            ),
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=2,
                rating=5.0,
                feedback="非常棒",
                execution_time=1.8,
                success=True
            ),
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=3,
                rating=None,
                feedback="",
                execution_time=0.0,
                success=False,
                error_message="执行失败"
            )
        ]
        
        # 保存使用历史
        saved_ids = []
        for usage in usage_records:
            usage_id = await db_manager.save_agent_usage_history(usage)
            saved_ids.append(usage_id)
        
        assert len(saved_ids) == 3
        assert all(uid > 0 for uid in saved_ids)
        
        # 获取使用历史
        history = await db_manager.get_agent_usage_history(agent_id)
        assert len(history) == 3
        
        # 验证历史记录（按时间倒序）
        assert history[0].rating == None  # 最新的记录
        assert history[0].success == False
        assert history[1].rating == 5.0
        assert history[2].rating == 4.0
        
        # 测试分页
        limited_history = await db_manager.get_agent_usage_history(agent_id, limit=2)
        assert len(limited_history) == 2
        
        offset_history = await db_manager.get_agent_usage_history(agent_id, limit=2, offset=1)
        assert len(offset_history) == 2
        assert offset_history[0].rating == 5.0
    
    @pytest.mark.asyncio
    async def test_agent_statistics(self, db_manager):
        """测试 Agent 统计信息"""
        # 创建 Agent
        agent = AIAgent(name="测试Agent", agent_type=AgentType.GENERAL, prompt_template="测试")
        agent_id = await db_manager.save_agent(agent)
        
        # 更新基本统计
        await db_manager.update_agent_usage(agent_id, 4.0)
        await db_manager.update_agent_usage(agent_id, 5.0)
        
        # 添加详细使用历史
        usage_records = [
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=1,
                rating=4.5,
                execution_time=2.0,
                success=True
            ),
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=2,
                rating=3.5,
                execution_time=3.0,
                success=True
            ),
            AgentUsageHistory(
                agent_id=agent_id,
                analysis_id=3,
                execution_time=0.0,
                success=False
            )
        ]
        
        for usage in usage_records:
            await db_manager.save_agent_usage_history(usage)
        
        # 获取统计信息
        stats = await db_manager.get_agent_statistics(agent_id)
        
        assert stats['usage_count'] == 2  # 从 update_agent_usage 来的
        assert stats['average_rating'] == 4.5  # (4.0 + 5.0) / 2
        assert stats['total_uses'] == 3  # 从 usage_history 来的
        assert stats['successful_uses'] == 2
        assert stats['success_rate'] == 2/3  # 2 成功 / 3 总计
        assert stats['avg_execution_time'] == (2.0 + 3.0 + 0.0) / 3
        assert stats['avg_user_rating'] == (4.5 + 3.5) / 2  # 只计算有评分的
        assert stats['rating_count'] == 2  # 有评分的记录数
    
    @pytest.mark.asyncio
    async def test_database_stats_with_agents(self, db_manager):
        """测试包含 Agent 表的数据库统计"""
        # 创建一些测试数据
        agent = AIAgent(name="测试Agent", agent_type=AgentType.GENERAL, prompt_template="测试")
        agent_id = await db_manager.save_agent(agent)
        
        usage = AgentUsageHistory(agent_id=agent_id, analysis_id=1)
        await db_manager.save_agent_usage_history(usage)
        
        # 获取数据库统计
        stats = await db_manager.get_database_stats()
        
        assert 'ai_agents_count' in stats
        assert 'agent_usage_history_count' in stats
        assert stats['ai_agents_count'] == 1
        assert stats['agent_usage_history_count'] == 1
    
    @pytest.mark.asyncio
    async def test_agent_type_conversion(self, db_manager):
        """测试 AgentType 枚举的数据库存储和转换"""
        # 测试所有 AgentType
        agent_types = [
            AgentType.GENERAL,
            AgentType.TECHNICAL,
            AgentType.MANAGEMENT,
            AgentType.CREATIVE,
            AgentType.SALES,
            AgentType.CUSTOM
        ]
        
        saved_agents = []
        for agent_type in agent_types:
            agent = AIAgent(
                name=f"{agent_type.value}Agent",
                agent_type=agent_type,
                prompt_template="测试"
            )
            agent_id = await db_manager.save_agent(agent)
            saved_agents.append((agent_id, agent_type))
        
        # 验证每个类型都能正确保存和读取
        for agent_id, expected_type in saved_agents:
            retrieved_agent = await db_manager.get_agent(agent_id)
            assert retrieved_agent.agent_type == expected_type
        
        # 测试按类型筛选
        for agent_type in agent_types:
            filtered_agents = await db_manager.get_all_agents(agent_type=agent_type)
            assert len(filtered_agents) == 1
            assert filtered_agents[0].agent_type == agent_type


class TestAIAgentDataIntegration:
    """测试 AI Agent 数据层集成"""
    
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
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, db_manager):
        """测试完整的 Agent 工作流程"""
        # 1. 创建 Agent
        agent = AIAgent(
            name="完整测试Agent",
            description="用于完整工作流程测试",
            agent_type=AgentType.TECHNICAL,
            prompt_template="技术分析: {job_description}\n简历: {resume_content}",
            is_builtin=False
        )
        
        agent_id = await db_manager.save_agent(agent)
        assert agent_id > 0
        
        # 2. 模拟分析过程 - 创建分析记录
        # 注意：这里我们不直接创建 MatchAnalysis，因为这需要先有 job 和 resume
        # 我们只测试 Agent 相关的部分
        
        # 3. 记录使用历史
        usage = AgentUsageHistory(
            agent_id=agent_id,
            analysis_id=1,  # 假设的分析ID
            rating=4.5,
            feedback="技术分析很准确",
            execution_time=2.3,
            success=True
        )
        
        usage_id = await db_manager.save_agent_usage_history(usage)
        assert usage_id > 0
        
        # 4. 更新使用统计
        await db_manager.update_agent_usage(agent_id, 4.5)
        
        # 5. 验证整个流程
        final_agent = await db_manager.get_agent(agent_id)
        assert final_agent.usage_count == 1
        assert final_agent.average_rating == 4.5
        
        history = await db_manager.get_agent_usage_history(agent_id)
        assert len(history) == 1
        assert history[0].rating == 4.5
        
        stats = await db_manager.get_agent_statistics(agent_id)
        assert stats['usage_count'] == 1
        assert stats['total_uses'] == 1
        assert stats['success_rate'] == 1.0
        
        # 6. 测试删除（因为不是内置）
        deleted = await db_manager.delete_agent(agent_id)
        assert deleted == True
        
        # 验证删除后的状态
        deleted_agent = await db_manager.get_agent(agent_id)
        assert deleted_agent is None
        
        # 使用历史应该也被级联删除
        deleted_history = await db_manager.get_agent_usage_history(agent_id)
        assert len(deleted_history) == 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])