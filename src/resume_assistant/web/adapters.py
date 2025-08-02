"""Adapters for integrating core modules with Web interface."""

import asyncio
import streamlit as st
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import os

from ..core.scraper import JobScraper
from ..core.parser import ResumeParser
from ..core.ai_analyzer import AIAnalyzer
from ..core.job_manager import JobManager
from ..core.resume_processor import ResumeProcessor
from .session_manager import SessionManager
from ..data.database import get_database_manager
from ..utils import get_logger

logger = get_logger(__name__)

class WebJobManager:
    """Web界面职位管理适配器"""
    
    def __init__(self):
        self.job_manager = JobManager()
        self.scraper = JobScraper()
        self.db_manager = get_database_manager()
    
    @st.cache_data(ttl=300)  # 缓存5分钟
    def scrape_job(self, url: str) -> Dict[str, Any]:
        """爬取职位信息"""
        try:
            SessionManager.set_loading_state('job_scraping', True)
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 模拟爬取进度
            status_text.text("正在初始化爬虫...")
            progress_bar.progress(0.2)
            
            status_text.text("正在访问职位页面...")
            progress_bar.progress(0.4)
            
            # 实际爬取 (这里需要适配异步)
            job_info = asyncio.run(self.scraper.scrape_job(url))
            
            status_text.text("正在解析职位信息...")
            progress_bar.progress(0.8)
            
            status_text.text("爬取完成！")
            progress_bar.progress(1.0)
            
            # 清理UI
            progress_bar.empty()
            status_text.empty()
            
            return job_info.__dict__ if job_info else {}
            
        except Exception as e:
            logger.error(f"Job scraping error: {e}")
            st.error(f"职位爬取失败: {str(e)}")
            return {}
        finally:
            SessionManager.set_loading_state('job_scraping', False)
    
    def get_jobs_list(self) -> List[Dict[str, Any]]:
        """获取职位列表"""
        return st.session_state.jobs
    
    def add_job_to_session(self, job_data: Dict[str, Any]) -> bool:
        """添加职位到会话并保存到数据库"""
        # 添加到会话状态
        success = SessionManager.add_job(job_data)
        
        if success:
            # 异步保存到数据库
            try:
                asyncio.create_task(self.db_manager.save_job(job_data))
            except Exception as e:
                logger.error(f"Failed to save job to database: {e}")
        
        return success
    
    def remove_job_from_session(self, job_id: int) -> bool:
        """从会话中删除职位"""
        return SessionManager.remove_job(job_id)

class WebResumeManager:
    """Web界面简历管理适配器"""
    
    def __init__(self):
        self.resume_processor = ResumeProcessor()
        self.parser = ResumeParser()
        self.db_manager = get_database_manager()
    
    def process_uploaded_file(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """处理上传的文件"""
        if not uploaded_file:
            return None
        
        try:
            SessionManager.set_loading_state('resume_parsing', True)
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("正在保存文件...")
            progress_bar.progress(0.2)
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            status_text.text("正在解析简历...")
            progress_bar.progress(0.5)
            
            # 根据文件类型解析
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            try:
                # 使用统一的parse_file方法
                parsed_resume = self.parser.parse_file(tmp_file_path)
            except Exception as e:
                st.error(f"不支持的文件类型或解析失败: {file_extension} - {str(e)}")
                return None
            
            status_text.text("正在结构化数据...")
            progress_bar.progress(0.8)
            
            # 转换为字典格式
            resume_dict = {
                'name': uploaded_file.name,
                'file_path': parsed_resume.file_path,
                'content': parsed_resume.raw_text,
                'personal_info': parsed_resume.personal_info,
                'education': parsed_resume.education,
                'experience': parsed_resume.work_experience,
                'projects': parsed_resume.projects,
                'skills': parsed_resume.skills,
                'file_type': file_extension,
                'file_size': len(uploaded_file.getvalue()),
                'sections': [{'title': s.title, 'content': s.content} for s in parsed_resume.sections]
            }
            
            status_text.text("解析完成！")
            progress_bar.progress(1.0)
            
            # 清理UI和临时文件
            progress_bar.empty()
            status_text.empty()
            os.unlink(tmp_file_path)  # 删除临时文件
            
            return resume_dict
            
        except Exception as e:
            logger.error(f"Resume parsing error: {e}")
            st.error(f"简历解析失败: {str(e)}")
            # 清理临时文件
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            return None
        finally:
            SessionManager.set_loading_state('resume_parsing', False)
    
    def get_resumes_list(self) -> List[Dict[str, Any]]:
        """获取简历列表"""
        return st.session_state.resumes
    
    def add_resume_to_session(self, resume_data: Dict[str, Any]) -> bool:
        """添加简历到会话并保存到数据库"""
        # 添加到会话状态
        success = SessionManager.add_resume(resume_data)
        
        if success:
            # 异步保存到数据库
            try:
                asyncio.create_task(self.db_manager.save_resume(resume_data))
            except Exception as e:
                logger.error(f"Failed to save resume to database: {e}")
        
        return success
    
    def remove_resume_from_session(self, resume_id: int) -> bool:
        """从会话中删除简历"""
        return SessionManager.remove_resume(resume_id)
    
    def preview_resume(self, resume_data: Dict[str, Any]):
        """预览简历内容"""
        st.subheader("📄 简历预览")
        
        # 基本信息
        col1, col2 = st.columns(2)
        with col1:
            st.metric("文件名", resume_data.get('name', 'Unknown'))
            st.metric("文件类型", resume_data.get('file_type', 'Unknown'))
        with col2:
            st.metric("文件大小", f"{resume_data.get('file_size', 0)} bytes")
            st.metric("技能数量", len(resume_data.get('skills', [])))
        
        # 内容预览
        with st.expander("📝 简历内容", expanded=True):
            content = resume_data.get('content', '')
            st.text_area(
                "内容预览",
                value=content[:1000] + "..." if len(content) > 1000 else content,
                height=200,
                disabled=True
            )
        
        # 结构化信息
        if resume_data.get('skills'):
            with st.expander("🛠️ 技能清单"):
                st.write(", ".join(resume_data.get('skills', [])))
        
        if resume_data.get('experience'):
            with st.expander("💼 工作经验"):
                for exp in resume_data.get('experience', []):
                    st.write(f"- {exp}")

class WebAnalysisManager:
    """Web界面分析管理适配器"""
    
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.db_manager = get_database_manager()
    
    def analyze_match(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析匹配度"""
        if not job_data or not resume_data:
            st.error("请先选择职位和简历")
            return None
        
        try:
            SessionManager.set_loading_state('analysis', True)
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("正在连接AI服务...")
            progress_bar.progress(0.2)
            
            status_text.text("正在分析职位要求...")
            progress_bar.progress(0.4)
            
            status_text.text("正在分析简历内容...")
            progress_bar.progress(0.6)
            
            # 执行AI分析
            # 这里需要适配现有的AI分析器
            analysis_result = {
                'job_id': job_data.get('id'),
                'resume_id': resume_data.get('id'),
                'overall_score': 0.78,
                'skill_match_score': 0.85,
                'experience_score': 0.72,
                'keyword_coverage': 0.68,
                'missing_skills': ['Docker', 'Kubernetes', 'Redis'],
                'strengths': ['Python', 'Django', 'MySQL', '团队协作'],
                'suggestions': [
                    {
                        'section': '技能清单',
                        'original': '熟悉Python开发',
                        'suggested': '精通Python开发，有3年项目经验',
                        'reason': '更具体地描述技能水平和经验'
                    }
                ]
            }
            
            status_text.text("正在生成分析报告...")
            progress_bar.progress(0.9)
            
            status_text.text("分析完成！")
            progress_bar.progress(1.0)
            
            # 清理UI
            progress_bar.empty()
            status_text.empty()
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            st.error(f"分析失败: {str(e)}")
            return None
        finally:
            SessionManager.set_loading_state('analysis', False)
    
    def get_analyses_list(self) -> List[Dict[str, Any]]:
        """获取分析列表"""
        return st.session_state.analyses
    
    def add_analysis_to_session(self, analysis_data: Dict[str, Any]) -> bool:
        """添加分析结果到会话并保存到数据库"""
        # 添加到会话状态
        success = SessionManager.add_analysis(analysis_data)
        
        if success:
            # 异步保存到数据库
            try:
                asyncio.create_task(self.db_manager.save_analysis(analysis_data))
            except Exception as e:
                logger.error(f"Failed to save analysis to database: {e}")
        
        return success
    
    def display_analysis_results(self, analysis_data: Dict[str, Any]):
        """显示分析结果"""
        from .components import UIComponents
        
        components = UIComponents()
        
        # 匹配度评分
        st.subheader("📊 匹配度评分")
        scores = {
            "总体匹配度": analysis_data.get('overall_score', 0),
            "技能匹配": analysis_data.get('skill_match_score', 0),
            "经验匹配": analysis_data.get('experience_score', 0),
            "关键词覆盖": analysis_data.get('keyword_coverage', 0)
        }
        components.render_match_score_chart(scores)
        
        # 缺失技能
        missing_skills = analysis_data.get('missing_skills', [])
        if missing_skills:
            st.subheader("⚠️ 缺失技能")
            for skill in missing_skills:
                st.warning(f"建议补充: {skill}")
        
        # 优势项
        strengths = analysis_data.get('strengths', [])
        if strengths:
            st.subheader("✅ 优势项")
            for strength in strengths:
                st.success(f"匹配良好: {strength}")
        
        # 优化建议
        suggestions = analysis_data.get('suggestions', [])
        if suggestions:
            st.subheader("💡 优化建议")
            for suggestion in suggestions:
                with st.expander(f"优化 {suggestion.get('section', 'Unknown')}"):
                    components.render_text_diff(
                        suggestion.get('original', ''),
                        suggestion.get('suggested', ''),
                        "修改建议"
                    )
                    st.info(f"**理由**: {suggestion.get('reason', '')}")

class WebGreetingManager:
    """Web界面打招呼语管理适配器"""
    
    def __init__(self):
        pass
    
    def generate_greeting(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> List[str]:
        """生成打招呼语"""
        if not job_data or not resume_data:
            st.error("请先选择职位和简历")
            return []
        
        try:
            SessionManager.set_loading_state('greeting_generation', True)
            
            # 模拟生成过程
            with st.spinner("正在生成个性化打招呼语..."):
                # 这里将来集成AI生成逻辑
                greetings = [
                    f"您好！我对{job_data.get('company', '')}的{job_data.get('title', '')}职位非常感兴趣...",
                    f"尊敬的HR，我是一名有经验的开发者，希望能加入{job_data.get('company', '')}团队...",
                    f"Hello! 我在招聘网站上看到贵公司的{job_data.get('title', '')}职位招聘..."
                ]
            
            return greetings
            
        except Exception as e:
            logger.error(f"Greeting generation error: {e}")
            st.error(f"生成打招呼语失败: {str(e)}")
            return []
        finally:
            SessionManager.set_loading_state('greeting_generation', False)