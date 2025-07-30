#!/usr/bin/env python3
"""TUI基础功能测试脚本"""

import sys
sys.path.insert(0, 'src')

from resume_assistant.ui.app import ResumeAssistantApp
from resume_assistant.utils import configure_logging

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试Resume Assistant基础功能")
    
    # 初始化日志
    configure_logging()
    
    try:
        # 创建应用实例
        app = ResumeAssistantApp()
        print("✅ 应用实例创建成功")
        
        # 测试简历处理器
        processor = app.resume_processor
        print(f"✅ 简历处理器初始化成功，支持格式: {processor.supported_formats}")
        
        # 测试获取简历列表（应该为空）
        resumes = processor.list_resumes()
        print(f"✅ 简历列表获取成功，当前简历数量: {len(resumes)}")
        
        # 测试布局创建
        app._update_layout()
        print("✅ TUI布局创建成功")
        
        # 测试面板切换
        original_panel = app.current_panel
        app.current_panel = "简历管理"
        content_panel = app._create_resumes_panel()
        app.current_panel = original_panel
        print("✅ 面板切换和内容创建成功")
        
        print("\n🎉 所有基础功能测试通过！")
        print("\n📝 使用方法:")
        print("1. 运行 './venv/bin/python demo_tui.py' 启动完整TUI")
        print("2. 在简历管理面板(按3)中:")
        print("   - 按 'u' 上传简历文件")  
        print("   - 按 'v' 查看简历详情")
        print("   - 按 'd' 删除简历")
        print("3. 在简化模式下，输入命令后按回车确认")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)