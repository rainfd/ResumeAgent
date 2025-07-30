#!/usr/bin/env python3
"""TUI演示脚本"""

import sys
import os
sys.path.insert(0, 'src')

from resume_assistant.ui.app import ResumeAssistantApp
from resume_assistant.utils import configure_logging

def main():
    """演示TUI应用"""
    print("🚀 Resume Assistant TUI Demo")
    print("=" * 50)
    
    # 初始化日志
    configure_logging()
    
    # 创建并运行应用
    app = ResumeAssistantApp()
    
    print("启动TUI应用，您可以：")
    print("- 直接按 1-6 键切换不同面板（无需回车）")
    print("- 使用 j/k 或 ↑/↓ 键滚动内容（vim风格）")
    print("- 按 h 查看帮助，按 q 退出程序")
    print("- 按 : 进入命令模式（默认隐藏）")
    print()
    
    app.run()

if __name__ == "__main__":
    main()