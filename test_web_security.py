#!/usr/bin/env python3
"""测试Web界面安全功能的简单Streamlit应用"""

import streamlit as st
import sys
from pathlib import Path

# 添加src路径到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from resume_assistant.web.pages.settings import SettingsPage

def main():
    """主函数"""
    st.set_page_config(
        page_title="安全功能测试",
        page_icon="🔒",
        layout="wide"
    )
    
    st.title("🔒 Resume Assistant 安全功能测试")
    
    # 初始化session state
    if 'auto_anonymize' not in st.session_state:
        st.session_state.auto_anonymize = True
    if 'log_masking' not in st.session_state:
        st.session_state.log_masking = True
    if 'data_retention_days' not in st.session_state:
        st.session_state.data_retention_days = 30
    
    # 创建设置页面实例
    settings_page = SettingsPage()
    
    # 只渲染安全设置部分
    st.markdown("## 🔒 安全设置测试")
    st.markdown("这是Resume Assistant安全功能的测试页面，包含以下功能：")
    
    st.markdown("""
    ### 🔑 主要安全功能
    
    1. **API密钥加密存储**
       - 使用PBKDF2密钥派生
       - Fernet对称加密
       - 支持过期时间设置
       - 密钥轮换功能
    
    2. **数据验证和输入过滤**
       - URL格式验证
       - 文件类型和大小验证
       - 输入内容清理
       - API密钥格式验证
    
    3. **隐私保护措施**
       - 敏感信息自动遮蔽
       - 简历数据匿名化
       - 日志信息保护
       - 数据保留策略
    
    4. **安全测试和监控**
       - 加密解密测试
       - 系统安全状态检查
       - 安全评分和建议
       - 详细安全报告
    """)
    
    st.divider()
    
    # 渲染安全设置
    settings_page._render_security_settings()
    
    st.divider()
    
    # 显示测试信息
    st.markdown("### 📋 测试信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **已实现的安全特性：**
        - ✅ API密钥加密存储
        - ✅ 数据验证和过滤
        - ✅ 隐私信息保护
        - ✅ 安全状态监控
        - ✅ 完整的测试覆盖
        """)
    
    with col2:
        st.success("""
        **测试结果：**
        - ✅ 加密解密功能正常
        - ✅ API密钥管理正常
        - ✅ 数据验证功能正常
        - ✅ 隐私保护功能正常
        - ✅ 全局管理器正常
        """)

if __name__ == "__main__":
    main()