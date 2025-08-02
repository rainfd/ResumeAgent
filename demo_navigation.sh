#!/bin/bash
# Resume Assistant 统一导航演示脚本

echo "🎯 Resume Assistant 统一导航系统演示"
echo "================================================"
echo ""
echo "📋 新的操作逻辑："
echo "• Tab / Shift+Tab - 在当前层级切换选项"
echo "• Enter - 进入下一层级"  
echo "• Esc - 退出到上一层级"
echo "• q - 退出程序"
echo ""
echo "🎮 操作演示："
echo "1. 启动后在主菜单，使用Tab切换选项"
echo "2. 按Enter进入'职位简历管理'"
echo "3. 在子菜单中使用Tab选择功能"
echo "4. 按Enter进入具体功能"
echo "5. 按Esc逐层返回到主菜单"
echo "6. 按q退出程序"
echo ""
echo "🚀 启动应用程序..."
echo ""

# 设置Python路径并启动应用
export PYTHONPATH=src
./venv/bin/python -m resume_assistant.main
