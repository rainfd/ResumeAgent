#!/usr/bin/env python3
"""测试WebAgentManager适配器

验证WebAgentManager的基本功能。
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_web_agent_manager():
    """测试WebAgentManager适配器"""
    print("🧪 测试WebAgentManager适配器...")
    
    try:
        # 导入WebAgentManager
        from src.resume_assistant.web.adapters import WebAgentManager
        
        # 创建适配器实例
        web_agent_manager = WebAgentManager()
        print("✅ WebAgentManager实例创建成功")
        
        # 测试获取Agent类型
        agent_types = web_agent_manager.get_agent_types()
        print(f"✅ 获取Agent类型成功: {len(agent_types)}个类型")
        for agent_type in agent_types:
            print(f"   - {agent_type['value']}: {agent_type['label']}")
        
        # 测试_agent_to_dict方法
        from src.resume_assistant.data.models import AIAgent, AgentType
        from datetime import datetime
        
        test_agent = AIAgent(
            id=1,
            name="测试Agent",
            description="用于测试的Agent",
            agent_type=AgentType.CUSTOM,
            is_builtin=False,
            prompt_template="测试模板",
            usage_count=5,
            average_rating=4.5,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        agent_dict = web_agent_manager._agent_to_dict(test_agent)
        print("✅ Agent对象转换为字典成功")
        print(f"   - ID: {agent_dict['id']}")
        print(f"   - 名称: {agent_dict['name']}")
        print(f"   - 类型: {agent_dict['agent_type_label']}")
        
        print("🎉 WebAgentManager适配器测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("WebAgentManager适配器测试")
    print("=" * 50)
    
    success = test_web_agent_manager()
    
    if success:
        print("\n✅ 所有测试通过！WebAgentManager适配器功能正常。")
    else:
        print("\n❌ 测试失败！请检查错误信息。")
    
    return success


if __name__ == "__main__":
    # 运行测试
    result = main()
    sys.exit(0 if result else 1)