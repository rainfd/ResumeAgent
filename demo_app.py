#!/usr/bin/env python3
"""Resume Assistant Demo - Simplified Version."""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import streamlit as st
    from datetime import datetime
    import json
    
    # 如果Streamlit可用，创建完整版本
    st.set_page_config(
        page_title="Resume Assistant",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    def main():
        # 初始化session state
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.jobs = []
            st.session_state.resumes = []
            st.session_state.analyses = []
            st.session_state.current_page = 'home'
        
        # 侧边栏导航
        with st.sidebar:
            st.title("📝 Resume Assistant")
            st.markdown("---")
            
            page = st.radio(
                "导航",
                ["🏠 首页", "💼 职位管理", "📄 简历管理", "🔍 分析结果", "💬 打招呼语", "⚙️ 设置"],
                key="navigation"
            )
            
            st.markdown("---")
            
            # 统计信息
            st.markdown("### 📊 统计信息")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("职位", len(st.session_state.jobs))
                st.metric("简历", len(st.session_state.resumes))
            with col2:
                st.metric("分析", len(st.session_state.analyses))
                st.metric("通知", 0)
        
        # 主要内容区域
        if page == "🏠 首页":
            render_home_page()
        elif page == "💼 职位管理":
            render_job_management()
        elif page == "📄 简历管理":
            render_resume_management()
        elif page == "🔍 分析结果":
            render_analysis_results()
        elif page == "💬 打招呼语":
            render_greeting_generator()
        elif page == "⚙️ 设置":
            render_settings()
    
    def render_home_page():
        st.title("🏠 欢迎使用 Resume Assistant")
        st.markdown("*基于AI的智能简历优化工具*")
        st.markdown("---")
        
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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("职位数量", len(st.session_state.jobs))
        with col2:
            st.metric("简历数量", len(st.session_state.resumes))
        with col3:
            st.metric("分析记录", len(st.session_state.analyses))
    
    def render_job_management():
        st.title("💼 职位管理")
        st.markdown("*爬取、分析和管理目标职位信息*")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🕷️ 爬取职位", "📋 职位列表"])
        
        with tab1:
            st.subheader("🕷️爬取新职位")
            
            job_url = st.text_input(
                "职位URL",
                placeholder="请输入BOSS直聘等招聘网站的职位链接",
                help="支持BOSS直聘、智联招聘等主流招聘网站的职位链接"
            )
            
            if job_url:
                st.success("✅ URL格式验证通过")
            
            if st.button("🚀 开始爬取", type="primary", disabled=not job_url):
                # 模拟爬取过程
                with st.spinner("正在爬取职位信息..."):
                    import time
                    time.sleep(2)
                    
                    # 添加示例职位
                    job_data = {
                        'id': len(st.session_state.jobs) + 1,
                        'url': job_url,
                        'title': 'Python开发工程师',
                        'company': '科技有限公司',
                        'location': '北京',
                        'salary': '15K-25K',
                        'experience': '3-5年',
                        'description': '负责后端系统开发，使用Python、Django等技术栈...',
                        'skills': ['Python', 'Django', 'MySQL', 'Redis'],
                        'created_at': datetime.now().isoformat()
                    }
                    
                    st.session_state.jobs.append(job_data)
                    st.success("✅ 职位爬取成功！")
                    st.rerun()
        
        with tab2:
            st.subheader("📋 已爬取的职位")
            
            if not st.session_state.jobs:
                st.info("还没有爬取任何职位。请在爬取职位标签页中添加职位链接。")
            else:
                for i, job in enumerate(st.session_state.jobs):
                    with st.container():
                        col1, col2, col3 = st.columns([4, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{job.get('title', 'Unknown Position')}**")
                            st.caption(f"🏢 {job.get('company', 'Unknown Company')}")
                            st.caption(f"💰 {job.get('salary', 'Unknown')}")
                        
                        with col2:
                            st.text(f"📍 {job.get('location', 'Unknown')}")
                            st.text(f"💼 {job.get('experience', 'Unknown')}")
                        
                        with col3:
                            if st.button("🗑️", key=f"delete_job_{i}", help="删除"):
                                st.session_state.jobs.pop(i)
                                st.rerun()
                        
                        st.markdown("---")
    
    def render_resume_management():
        st.title("📄 简历管理")
        st.markdown("*上传、解析和管理您的简历文件*")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📤 上传简历", "📋 简历列表"])
        
        with tab1:
            st.subheader("📤 上传新简历")
            
            uploaded_file = st.file_uploader(
                "选择简历文件",
                type=['pdf', 'txt', 'md'],
                help="支持 PDF、TXT、Markdown 格式，最大 10MB"
            )
            
            if uploaded_file is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("文件名", uploaded_file.name)
                with col2:
                    st.metric("大小", f"{len(uploaded_file.getvalue()) / 1024:.1f} KB")
                with col3:
                    st.metric("类型", uploaded_file.type)
                
                if st.button("🔄 解析简历", type="primary"):
                    with st.spinner("正在解析简历..."):
                        import time
                        time.sleep(2)
                        
                        # 添加示例简历
                        resume_data = {
                            'id': len(st.session_state.resumes) + 1,
                            'name': uploaded_file.name,
                            'content': '这是一份示例简历内容...',
                            'personal_info': {'name': '张三', 'email': 'zhangsan@example.com'},
                            'skills': ['Python', 'Java', 'React', 'MySQL'],
                            'experience': ['软件开发工程师 - 3年经验'],
                            'education': ['计算机科学与技术 - 本科'],
                            'file_type': uploaded_file.name.split('.')[-1],
                            'file_size': len(uploaded_file.getvalue()),
                            'created_at': datetime.now().isoformat()
                        }
                        
                        st.session_state.resumes.append(resume_data)
                        st.success("✅ 简历解析成功！")
                        
                        # 显示解析结果
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("技能数量", len(resume_data.get('skills', [])))
                        with col2:
                            st.metric("工作经验", len(resume_data.get('experience', [])))
                        with col3:
                            st.metric("项目经历", 0)
                        with col4:
                            st.metric("教育背景", len(resume_data.get('education', [])))
                        
                        st.rerun()
        
        with tab2:
            st.subheader("📋 已上传的简历")
            
            if not st.session_state.resumes:
                st.info("还没有上传任何简历。请在上传简历标签页中上传您的简历文件。")
            else:
                for i, resume in enumerate(st.session_state.resumes):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{resume.get('name', 'Unknown')}**")
                            if resume.get('personal_info', {}).get('name'):
                                st.caption(f"姓名: {resume['personal_info']['name']}")
                        
                        with col2:
                            st.text(f"类型: {resume.get('file_type', 'Unknown').upper()}")
                            skills_count = len(resume.get('skills', []))
                            st.text(f"技能: {skills_count} 项")
                        
                        with col3:
                            if st.button("🗑️", key=f"delete_resume_{i}", help="删除"):
                                st.session_state.resumes.pop(i)
                                st.rerun()
                        
                        st.markdown("---")
    
    def render_analysis_results():
        st.title("🔍 分析结果")
        st.markdown("*AI驱动的简历与职位匹配度分析*")
        st.markdown("---")
        
        if not st.session_state.jobs:
            st.warning("⚠️ 还没有职位数据，请先到职位管理页面添加职位。")
            return
        
        if not st.session_state.resumes:
            st.warning("⚠️ 还没有简历数据，请先到简历管理页面上传简历。")
            return
        
        st.subheader("🚀 开始新的匹配度分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 选择目标职位")
            job_options = [f"{job.get('title', 'Unknown')} - {job.get('company', 'Unknown')}" for job in st.session_state.jobs]
            selected_job_index = st.selectbox("选择职位", range(len(job_options)), format_func=lambda x: job_options[x])
            selected_job = st.session_state.jobs[selected_job_index]
        
        with col2:
            st.markdown("### 📄 选择简历")
            resume_options = [resume.get('name', 'Unknown') for resume in st.session_state.resumes]
            selected_resume_index = st.selectbox("选择简历", range(len(resume_options)), format_func=lambda x: resume_options[x])
            selected_resume = st.session_state.resumes[selected_resume_index]
        
        if st.button("🔍 开始AI分析", type="primary"):
            with st.spinner("正在进行AI分析..."):
                import time
                time.sleep(3)
                
                # 模拟分析结果
                analysis_result = {
                    'id': len(st.session_state.analyses) + 1,
                    'job_id': selected_job.get('id'),
                    'resume_id': selected_resume.get('id'),
                    'overall_score': 0.78,
                    'skill_match_score': 0.85,
                    'experience_score': 0.72,
                    'keyword_coverage': 0.68,
                    'missing_skills': ['Docker', 'Kubernetes', 'Redis'],
                    'strengths': ['Python', 'Django', 'MySQL', '团队协作'],
                    'created_at': datetime.now().isoformat()
                }
                
                st.session_state.analyses.append(analysis_result)
                st.success("✅ 分析完成！")
                
                # 显示分析结果
                st.markdown("### 📊 分析结果")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总体匹配度", f"{analysis_result['overall_score']:.2f}")
                with col2:
                    st.metric("技能匹配", f"{analysis_result['skill_match_score']:.2f}")
                with col3:
                    st.metric("经验匹配", f"{analysis_result['experience_score']:.2f}")
                with col4:
                    st.metric("关键词覆盖", f"{analysis_result['keyword_coverage']:.2f}")
                
                # 缺失技能
                if analysis_result.get('missing_skills'):
                    st.subheader("⚠️ 缺失技能")
                    for skill in analysis_result['missing_skills']:
                        st.warning(f"建议补充: {skill}")
                
                # 优势项
                if analysis_result.get('strengths'):
                    st.subheader("✅ 优势项")
                    for strength in analysis_result['strengths']:
                        st.success(f"匹配良好: {strength}")
    
    def render_greeting_generator():
        st.title("💬 打招呼语生成")
        st.markdown("*AI生成个性化求职开场白*")
        st.markdown("---")
        
        if not st.session_state.jobs or not st.session_state.resumes:
            st.info("请先添加职位和简历数据，然后返回此页面生成打招呼语。")
            return
        
        st.subheader("💬 生成个性化打招呼语")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_options = [f"{job.get('title', 'Unknown')} - {job.get('company', 'Unknown')}" for job in st.session_state.jobs]
            selected_job_index = st.selectbox("选择职位", range(len(job_options)), format_func=lambda x: job_options[x], key="greeting_job")
        
        with col2:
            resume_options = [resume.get('name', 'Unknown') for resume in st.session_state.resumes]
            selected_resume_index = st.selectbox("选择简历", range(len(resume_options)), format_func=lambda x: resume_options[x], key="greeting_resume")
        
        if st.button("🎯 生成打招呼语", type="primary"):
            with st.spinner("正在生成个性化打招呼语..."):
                import time
                time.sleep(2)
                
                job = st.session_state.jobs[selected_job_index]
                resume = st.session_state.resumes[selected_resume_index]
                
                greetings = [
                    f"您好！我对{job.get('company', '')}的{job.get('title', '')}职位非常感兴趣，我有相关的技术背景和项目经验，希望能有机会与您详细交流。",
                    f"尊敬的HR，我是一名有经验的开发者，在看到{job.get('company', '')}的职位招聘后，觉得自己的技能和经验与贵公司的需求非常匹配。",
                    f"Hello! 我在招聘网站上看到贵公司的{job.get('title', '')}职位招聘，我的技术栈正好符合您的要求，期待能有进一步沟通的机会。"
                ]
                
                st.success("✅ 打招呼语生成完成！")
                
                for i, greeting in enumerate(greetings, 1):
                    st.markdown(f"### 版本 {i}")
                    st.text_area("", value=greeting, height=100, key=f"greeting_{i}", disabled=True)
                    if st.button(f"📋 复制版本 {i}", key=f"copy_{i}"):
                        st.success("已复制到剪贴板（模拟）")
    
    def render_settings():
        st.title("⚙️ 设置")
        st.markdown("*配置应用程序设置*")
        st.markdown("---")
        
        st.subheader("🤖 AI服务配置")
        api_key = st.text_input("DeepSeek API密钥", type="password", help="输入您的DeepSeek API密钥")
        
        st.subheader("🎨 界面设置")
        theme = st.selectbox("主题", ["浅色", "深色"], index=0)
        
        st.subheader("📊 数据管理")
        if st.button("🗑️ 清空所有数据", type="secondary"):
            if st.checkbox("确认清空所有数据"):
                st.session_state.jobs = []
                st.session_state.resumes = []
                st.session_state.analyses = []
                st.success("所有数据已清空")
                st.rerun()
        
        if st.button("💾 保存设置", type="primary"):
            st.success("设置已保存")
    
    if __name__ == "__main__":
        main()

except ImportError:
    # 如果Streamlit不可用，显示安装说明
    print("""
    🔧 Streamlit Demo App
    
    Streamlit未安装，请运行以下命令安装：
    
    pip install streamlit plotly
    
    然后运行：
    streamlit run demo_app.py
    
    或访问已部署的版本。
    """)
    
    # 创建一个简单的HTML版本
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Assistant</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 10px; }
            .feature { margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📝 Resume Assistant</h1>
            <p>基于AI的智能简历优化工具</p>
        </div>
        
        <div class="feature">
            <h3>🕷️ 职位管理</h3>
            <p>从BOSS直聘等网站抓取职位信息</p>
        </div>
        
        <div class="feature">
            <h3>📄 简历管理</h3>
            <p>上传和管理PDF/Markdown格式简历</p>
        </div>
        
        <div class="feature">
            <h3>🤖 AI分析</h3>
            <p>智能分析简历与职位的匹配度</p>
        </div>
        
        <div class="feature">
            <h3>💡 优化建议</h3>
            <p>获得针对性的简历改进建议</p>
        </div>
        
        <div class="feature">
            <h3>💬 打招呼语</h3>
            <p>生成个性化的求职开场白</p>
        </div>
        
        <p><strong>要运行完整版本，请安装Streamlit:</strong></p>
        <code>pip install streamlit plotly</code><br>
        <code>streamlit run demo_app.py</code>
    </body>
    </html>
    """
    
    with open("demo.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("已创建demo.html演示页面")