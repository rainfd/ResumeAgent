#!/usr/bin/env python3
"""Resume Assistant Streamlit Web Application."""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.resume_assistant.config import get_settings
from src.resume_assistant.utils import configure_logging, get_logger
from src.resume_assistant.web.session_manager import SessionManager
from src.resume_assistant.web.navigation import NavigationManager
from src.resume_assistant.web.components import UIComponents
from src.resume_assistant.web.pages.resume_management import ResumeManagementPage
from src.resume_assistant.web.pages.job_management import JobManagementPage
from src.resume_assistant.web.pages.analysis_results import AnalysisResultsPage
from src.resume_assistant.data.database import init_database

# 页面配置
st.set_page_config(
    page_title="Resume Assistant",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """初始化Session State"""
    SessionManager.init_session_state()

def init_application():
    """初始化应用程序"""
    if not st.session_state.initialized:
        try:
            # 配置日志
            configure_logging(enable_console=False)  # Web环境下关闭控制台日志
            logger = get_logger(__name__)
            
            logger.info("Resume Assistant Web App initializing...")
            
            # 初始化数据库
            asyncio.run(init_database())
            logger.info("Database initialized")
            
            # 标记为已初始化
            st.session_state.initialized = True
            st.session_state.app_logger = logger
            
            logger.info("Resume Assistant Web App initialized successfully")
            
        except Exception as e:
            st.error(f"应用初始化失败: {str(e)}")
            st.stop()

def render_sidebar():
    """渲染侧边栏导航"""
    navigation = NavigationManager()
    navigation.render_sidebar_navigation()

def render_home_page():
    """渲染首页"""
    components = UIComponents()
    
    components.render_header("欢迎使用 Resume Assistant", "基于AI的智能简历优化工具", "🏠")
    
    st.markdown("""
    ### 📋 功能概览
    
    Resume Assistant 是一个基于AI的智能简历优化工具，帮助您：
    
    - 🕷️ **职位管理**: 从BOSS直聘等网站抓取职位信息
    - 📄 **简历管理**: 上传和管理PDF/Markdown格式简历
    - 🤖 **AI分析**: 智能分析简历与职位的匹配度
    - 💡 **优化建议**: 获得针对性的简历改进建议
    - 💬 **打招呼语**: 生成个性化的求职开场白
    
    ### 🚀 快速开始
    
    1. 在 **职位管理** 页面添加目标职位  
    2. 在 **简历管理** 页面上传您的简历
    3. 在 **分析结果** 页面查看AI分析和建议
    4. 在 **打招呼语** 页面生成个性化开场白
    """)
    
    # 显示统计信息
    stats = SessionManager.get_session_stats()
    metrics = [
        {'label': '职位数量', 'value': stats.get('jobs_count', 0)},
        {'label': '简历数量', 'value': stats.get('resumes_count', 0)},
        {'label': '分析记录', 'value': stats.get('analyses_count', 0)}
    ]
    
    components.render_metric_cards(metrics, columns=3)

def render_placeholder_page(page_name: str, icon: str):
    """渲染占位符页面"""
    components = UIComponents()
    
    components.render_header(page_name, f"{page_name}功能正在开发中，敬请期待！", icon)
    
    # 显示一些基本的占位符内容
    if page_name == "职位管理":
        st.markdown("### 🔜 即将上线的功能:")
        st.markdown("- 职位URL输入和爬取")
        st.markdown("- 职位列表展示和管理") 
        st.markdown("- 职位详情预览")
        
        # 演示已有的职位数据
        if st.session_state.jobs:
            st.markdown("### 📋 现有职位数据:")
            components.render_data_table(st.session_state.jobs[:3])  # 显示前3条
        
    elif page_name == "简历管理":
        st.markdown("### 🔜 即将上线的功能:")
        st.markdown("- 简历文件上传（PDF/Markdown）")
        st.markdown("- 简历解析和预览")
        st.markdown("- 简历版本管理")
        
        # 演示文件上传器
        st.markdown("### 📄 文件上传演示:")
        uploaded_file = components.render_file_uploader(
            "选择简历文件", 
            file_types=['pdf', 'txt', 'md'],
            help_text="支持PDF、TXT、MD格式"
        )
        if uploaded_file:
            st.success(f"文件 '{uploaded_file.name}' 上传成功！")
        
    elif page_name == "分析结果":
        st.markdown("### 🔜 即将上线的功能:")
        st.markdown("- 匹配度分析展示")
        st.markdown("- 文本差异对比")
        st.markdown("- 优化建议列表")
        
        # 演示匹配度图表
        if st.session_state.analyses:
            st.markdown("### 📊 匹配度分析演示:")
            demo_scores = {
                "技能匹配": 0.85,
                "经验匹配": 0.72,
                "教育背景": 0.90,
                "关键词覆盖": 0.68
            }
            components.render_match_score_chart(demo_scores)
        
    elif page_name == "打招呼语":
        st.markdown("### 🔜 即将上线的功能:")
        st.markdown("- AI生成个性化开场白")
        st.markdown("- 多版本生成和选择")
        st.markdown("- 一键复制到剪贴板")
        
        # 演示打招呼语
        st.markdown("### 💬 打招呼语示例:")
        sample_greeting = "您好！我对贵公司的Python开发工程师职位非常感兴趣。我有3年Python开发经验..."
        components.render_copy_button(sample_greeting, "复制示例")
        
    elif page_name == "设置":
        st.markdown("### 🔜 即将上线的功能:")
        st.markdown("- AI服务配置")
        st.markdown("- 主题选择")
        st.markdown("- 数据导出功能")
        
        # 演示设置表单
        st.markdown("### ⚙️ 设置演示:")
        settings_config = {
            'api_key': {
                'type': 'text',
                'label': 'API密钥',
                'help': '输入您的DeepSeek API密钥'
            },
            'theme': {
                'type': 'select',
                'label': '主题',
                'options': ['浅色', '深色'],
                'default': '浅色'
            }
        }
        form_data = components.render_form_input(settings_config, "demo_settings")
        if form_data:
            st.success("设置已保存（演示）")

def main():
    """主函数"""
    # 初始化
    init_session_state()
    init_application()
    
    # 渲染侧边栏
    render_sidebar()
    
    # 根据选择的页面渲染内容
    current_page = st.session_state.get('current_page', 'home')
    
    if current_page == 'home':
        render_home_page()
    elif current_page == 'jobs':
        job_page = JobManagementPage()
        job_page.render()
    elif current_page == 'resumes':
        resume_page = ResumeManagementPage()
        resume_page.render()
    elif current_page == 'analysis':
        analysis_page = AnalysisResultsPage()
        analysis_page.render()
    elif current_page == 'greeting':
        render_placeholder_page("打招呼语", "💬")
    elif current_page == 'settings':
        render_placeholder_page("设置", "⚙️")
    else:
        render_home_page()

if __name__ == "__main__":
    main()