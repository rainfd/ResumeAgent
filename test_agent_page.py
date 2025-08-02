#!/usr/bin/env python3
"""测试Agent管理页面

简单测试Agent管理功能的基本操作。
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.resume_assistant.core.agents import AgentManager, AIAnalyzer, DeepSeekClient
from unittest.mock import Mock, AsyncMock
from src.resume_assistant.data.database import DatabaseManager
from src.resume_assistant.data.models import AgentType


async def test_agent_management():
    """测试Agent管理功能"""
    print("🧪 测试Agent管理功能...")
    
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        # 初始化数据库
        db_manager = DatabaseManager(db_path)
        await db_manager.init_database()
        
        # 创建Mock AI分析器（避免API调用）
        mock_deepseek = Mock(spec=DeepSeekClient)
        mock_deepseek.chat_completion = Mock(return_value='{"overall_score": 85.0}')
        
        ai_analyzer = AIAnalyzer(mock_deepseek)
        agent_manager = AgentManager(db_manager, ai_analyzer)
        await agent_manager.initialize()
        
        print("✅ Agent管理器初始化成功")
        
        # 测试获取内置Agent
        builtin_agents = await agent_manager.get_all_agents(include_custom=False)
        print(f"✅ 发现 {len(builtin_agents)} 个内置Agent:")
        for agent in builtin_agents:
            print(f"   - {agent.name} ({agent.agent_type.value})")
        
        # 测试创建自定义Agent
        custom_agent_data = {
            "name": "测试自定义Agent",
            "description": "用于测试的自定义Agent",
            "agent_type": "custom",
            "prompt_template": "请分析职位：{job_description}和简历：{resume_content}"
        }
        
        custom_agent_id = await agent_manager.create_agent(custom_agent_data)
        print(f"✅ 创建自定义Agent成功，ID: {custom_agent_id}")
        
        # 测试获取Agent详情
        custom_agent = await agent_manager.get_agent(custom_agent_id)
        print(f"✅ 获取Agent详情: {custom_agent.name}")
        
        # 测试Agent统计
        stats = await agent_manager.get_agent_statistics(custom_agent_id)
        print(f"✅ 获取Agent统计: {stats}")
        
        # 测试更新Agent
        updates = {"description": "更新后的描述"}
        success = await agent_manager.update_agent(custom_agent_id, updates)
        print(f"✅ 更新Agent: {success}")
        
        # 测试删除Agent
        success = await agent_manager.delete_agent(custom_agent_id)
        print(f"✅ 删除Agent: {success}")
        
        print("🎉 Agent管理功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if db_path.exists():
            db_path.unlink()
    
    return True


async def main():
    """主函数"""
    print("=" * 50)
    print("Agent管理功能测试")
    print("=" * 50)
    
    success = await test_agent_management()
    
    if success:
        print("\n✅ 所有测试通过！Agent管理页面应该可以正常工作。")
    else:
        print("\n❌ 测试失败！请检查错误信息。")
    
    return success


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)