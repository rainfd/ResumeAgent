#!/usr/bin/env python3
"""Agent工作流集成测试

测试完整的Agent工作流程，从创建到分析。
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.core.agents import (
    AgentManager, AgentFactory, AgentAnalysisIntegrator, AIAnalyzer
)
from resume_assistant.data.database import DatabaseManager
from resume_assistant.web.adapters import WebAgentManager


class TestAgentWorkflow:
    """Agent工作流集成测试"""
    
    @pytest.fixture
    async def workflow_setup(self):
        """设置完整的工作流环境"""
        # 创建临时数据库
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # 初始化数据库
            db_manager = DatabaseManager(db_path)
            await db_manager.init_database()
            
            # 创建Mock AI分析器
            mock_ai_analyzer = Mock(spec=AIAnalyzer)
            mock_ai_analyzer.chat_completion = Mock(return_value="""{
                "overall_score": 85.0,
                "skill_match_score": 80.0,
                "experience_score": 90.0,
                "keyword_coverage": 75.0,
                "missing_skills": ["Docker", "Kubernetes"],
                "strengths": ["Python经验丰富", "有大型项目经验"],
                "suggestions": ["建议学习容器化技术", "可以补充云平台知识"]
            }""")
            
            # 创建各种管理器
            agent_manager = AgentManager(db_manager, mock_ai_analyzer)
            await agent_manager.initialize()
            
            agent_factory = AgentFactory(agent_manager)
            agent_integrator = AgentAnalysisIntegrator(agent_manager, db_manager)
            web_agent_manager = WebAgentManager()
            
            yield {
                "db_manager": db_manager,
                "agent_manager": agent_manager,
                "agent_factory": agent_factory,
                "agent_integrator": agent_integrator,
                "web_agent_manager": web_agent_manager,
                "mock_ai_analyzer": mock_ai_analyzer
            }
            
        finally:
            # 清理临时文件
            if db_path.exists():
                db_path.unlink()
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, workflow_setup):
        """测试完整的Agent工作流程"""
        setup = workflow_setup
        agent_manager = setup["agent_manager"]
        agent_factory = setup["agent_factory"]
        agent_integrator = setup["agent_integrator"]
        
        # 1. 验证内置Agent初始化
        builtin_agents = await agent_manager.get_all_agents(include_custom=False)
        assert len(builtin_agents) == 5
        print(f"✅ 初始化了 {len(builtin_agents)} 个内置Agent")
        
        # 2. 创建自定义Agent
        custom_agent_data = {
            "name": "Python专家Agent",
            "description": "专门针对Python开发岗位的分析Agent",
            "agent_type": "technical",
            "prompt_template": """
            请专业分析以下Python开发岗位与候选人的匹配情况：
            
            【职位要求】
            {job_description}
            
            【候选人简历】
            {resume_content}
            
            请从以下维度评分（0-100分）：
            1. Python技术水平匹配度
            2. 框架和工具经验匹配度
            3. 项目经验相关度
            4. 综合匹配度
            
            并提供改进建议。
            """
        }
        
        custom_agent_id = await agent_manager.create_agent(custom_agent_data)
        assert custom_agent_id is not None
        print(f"✅ 创建自定义Agent成功，ID: {custom_agent_id}")
        
        # 3. 验证Agent创建成功
        custom_agent = await agent_manager.get_agent(custom_agent_id)
        assert custom_agent.name == "Python专家Agent"
        assert custom_agent.agent_type.value == "technical"
        print("✅ 自定义Agent创建验证成功")
        
        # 4. 测试Agent推荐功能
        job_description = """
        Python后端开发工程师
        
        职位要求：
        - 3年以上Python开发经验
        - 熟悉Django或Flask框架
        - 熟悉MySQL数据库
        - 有RESTful API开发经验
        - 了解Redis缓存
        """
        
        recommended_agent = await agent_factory.get_recommended_agent(job_description)
        assert recommended_agent is not None
        assert recommended_agent.agent_type.value == "technical"
        print(f"✅ 推荐Agent: {recommended_agent.name}")
        
        # 5. 使用推荐Agent进行分析
        resume_content = """
        张三 - Python开发工程师
        
        工作经验：
        - 5年Python开发经验
        - 熟练使用Django框架开发Web应用
        - 熟悉MySQL数据库设计和优化
        - 有丰富的RESTful API开发经验
        - 使用过Redis进行缓存优化
        - 参与过大型电商项目开发
        
        技能：Python, Django, MySQL, Redis, Git, Linux
        """
        
        analysis_result = await agent_integrator.analyze_with_recommended_agent(
            job_description=job_description,
            resume_content=resume_content,
            job_id=1,
            resume_id=1
        )
        
        assert analysis_result["success"]
        assert "analysis" in analysis_result
        assert analysis_result["analysis"]["overall_score"] == 85.0
        print(f"✅ 分析成功，总体匹配度: {analysis_result['analysis']['overall_score']}")
        
        # 6. 测试多Agent对比
        agents = await agent_manager.get_all_agents(include_custom=False)
        agent_ids = [agent.id for agent in agents[:3]]  # 取前3个Agent
        
        comparison_result = await agent_integrator.compare_agents(
            job_description=job_description,
            resume_content=resume_content,
            job_id=1,
            resume_id=1,
            agent_ids=agent_ids
        )
        
        assert comparison_result["success"]
        assert len(comparison_result["results"]) == 3
        assert "comparison" in comparison_result
        print(f"✅ Agent对比成功，对比了 {len(comparison_result['results'])} 个Agent")
        
        # 7. 测试Agent统计更新
        stats_before = await agent_manager.get_agent_statistics(recommended_agent.id)
        
        # 更新使用统计
        await agent_manager.update_agent_usage(recommended_agent.id, True, 1.5, 4.5)
        
        stats_after = await agent_manager.get_agent_statistics(recommended_agent.id)
        assert stats_after["usage_count"] > stats_before["usage_count"]
        print("✅ Agent使用统计更新成功")
        
        # 8. 测试Agent编辑
        updates = {
            "description": "更新后的描述：专门针对高级Python开发岗位"
        }
        
        update_success = await agent_manager.update_agent(custom_agent_id, updates)
        assert update_success
        
        updated_agent = await agent_manager.get_agent(custom_agent_id)
        assert "更新后的描述" in updated_agent.description
        print("✅ Agent更新成功")
        
        # 9. 测试Agent删除
        delete_success = await agent_manager.delete_agent(custom_agent_id)
        assert delete_success
        
        deleted_agent = await agent_manager.get_agent(custom_agent_id)
        assert deleted_agent is None
        print("✅ Agent删除成功")
        
        print("\n🎉 完整Agent工作流测试通过！")
    
    @pytest.mark.asyncio 
    async def test_web_agent_manager_workflow(self, workflow_setup):
        """测试WebAgentManager工作流"""
        setup = workflow_setup
        web_agent_manager = setup["web_agent_manager"]
        
        # 测试获取Agent类型
        agent_types = web_agent_manager.get_agent_types()
        assert len(agent_types) == 6
        print(f"✅ WebAgentManager支持 {len(agent_types)} 种Agent类型")
        
        # 测试获取Agent统计
        stats = web_agent_manager.get_agent_statistics(1)
        assert isinstance(stats, dict)
        print("✅ WebAgentManager统计功能正常")
        
        print("✅ WebAgentManager工作流测试通过")
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, workflow_setup):
        """测试错误处理工作流"""
        setup = workflow_setup
        agent_manager = setup["agent_manager"]
        mock_ai_analyzer = setup["mock_ai_analyzer"]
        
        # 测试AI分析失败的情况
        mock_ai_analyzer.chat_completion.side_effect = Exception("API调用失败")
        
        agents = await agent_manager.get_all_agents(include_custom=False)
        test_agent = agents[0]
        
        from src.resume_assistant.core.agents import AnalysisContext
        context = AnalysisContext(
            job_id=1,
            resume_id=1,
            job_description="测试职位",
            resume_content="测试简历"
        )
        
        result = await agent_manager.analyze_with_agent(test_agent.id, context)
        
        # 应该处理错误并返回失败结果
        assert not result["success"]
        assert "error" in result
        print("✅ 错误处理工作流测试通过")


# 运行测试的入口
if __name__ == "__main__":
    # 运行工作流测试
    pytest.main([__file__, "-v", "--tb=short"])