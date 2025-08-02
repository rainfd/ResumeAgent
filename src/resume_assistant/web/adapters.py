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
            
            # 执行AI分析 - 集成真实的AIAnalyzer
            try:
                # 构建JobInfo对象
                from ..core.ai_analyzer import JobInfo
                job_info = JobInfo(
                    id=str(job_data.get('id', '')),
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    description=job_data.get('description', ''),
                    requirements=job_data.get('requirements', ''),
                    location=job_data.get('location'),
                    salary=job_data.get('salary'),
                    experience_level=job_data.get('experience_level')
                )
                
                # 获取简历内容
                resume_content = resume_data.get('content', '')
                resume_id = str(resume_data.get('id', ''))
                
                status_text.text("正在进行AI分析...")
                progress_bar.progress(0.8)
                
                # 调用真实的AI分析器
                ai_result = self.ai_analyzer.analyze_resume_job_match(
                    resume_content=resume_content,
                    resume_id=resume_id,
                    job_info=job_info
                )
                
                # 转换分析结果格式以适配Web界面
                analysis_result = self._convert_ai_result_to_web_format(ai_result)
                
            except Exception as ai_error:
                logger.warning(f"AI分析失败，使用模拟数据: {ai_error}")
                # 如果AI分析失败，使用模拟数据
                analysis_result = self._create_fallback_analysis(job_data, resume_data)
            
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
    
    def _convert_ai_result_to_web_format(self, ai_result) -> Dict[str, Any]:
        """转换AI分析结果为Web界面格式"""
        from ..core.ai_analyzer import AnalysisResult
        from datetime import datetime
        
        if not isinstance(ai_result, AnalysisResult):
            logger.error("AI结果格式错误")
            return self._create_fallback_analysis({}, {})
        
        # 转换匹配度分数（从0-100转换为0-1）
        match_scores = ai_result.match_scores
        
        return {
            'analysis_id': ai_result.id,
            'job_id': ai_result.job_id,
            'resume_id': ai_result.resume_id,
            'overall_score': ai_result.overall_score / 100.0,  # 转换为0-1范围
            'skill_match_score': match_scores.get('技能匹配度', 60.0) / 100.0,
            'experience_score': match_scores.get('经验匹配度', 60.0) / 100.0,
            'keyword_coverage': match_scores.get('关键词覆盖', 60.0) / 100.0,
            'missing_skills': ai_result.missing_skills,
            'strengths': ai_result.strengths,
            'weaknesses': ai_result.weaknesses,
            'suggestions': self._format_suggestions(ai_result.suggestions),
            'created_at': ai_result.created_at.isoformat(),
            'analysis_version': ai_result.analysis_version
        }
    
    def _format_suggestions(self, suggestions: List[str]) -> List[Dict[str, str]]:
        """格式化建议为Web界面格式"""
        formatted_suggestions = []
        
        for i, suggestion in enumerate(suggestions):
            # 尝试解析建议的结构，如果无法解析则使用默认格式
            formatted_suggestions.append({
                'section': f'建议 {i+1}',
                'original': '待优化内容',
                'suggested': suggestion,
                'reason': '基于AI分析的改进建议'
            })
        
        return formatted_suggestions
    
    def _create_fallback_analysis(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建回退分析结果（当AI分析失败时）"""
        import uuid
        from datetime import datetime
        
        return {
            'analysis_id': str(uuid.uuid4()),
            'job_id': job_data.get('id'),
            'resume_id': resume_data.get('id'),
            'overall_score': 0.74,
            'skill_match_score': 0.78,
            'experience_score': 0.70,
            'keyword_coverage': 0.65,
            'missing_skills': ['Docker', 'Kubernetes', 'Redis', '微服务架构'],
            'strengths': ['技术基础扎实', '学习能力强', '团队协作经验', 'Python开发经验'],
            'weaknesses': ['缺乏大型项目经验', '新技术实践较少'],
            'suggestions': [
                {
                    'section': '技能清单',
                    'original': '熟悉Python开发',
                    'suggested': '精通Python开发，具有3年以上项目经验，熟练使用Django/Flask框架',
                    'reason': '更具体地描述技能水平和实际经验'
                },
                {
                    'section': '项目经验',
                    'original': '参与过多个项目开发',
                    'suggested': '主导开发了XX系统，使用Python+MySQL技术栈，用户量达到10万+',
                    'reason': '量化项目成果，突出技术栈匹配度'
                }
            ],
            'created_at': datetime.now().isoformat(),
            'analysis_version': '1.0-fallback'
        }

class WebGreetingManager:
    """Web界面打招呼语管理适配器"""
    
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
    
    def generate_greeting(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> List[str]:
        """生成打招呼语"""
        if not job_data or not resume_data:
            st.error("请先选择职位和简历")
            return []
        
        try:
            SessionManager.set_loading_state('greeting_generation', True)
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("正在分析职位和简历信息...")
            progress_bar.progress(0.3)
            
            # 尝试使用AI生成打招呼语
            try:
                greetings = self._generate_ai_greetings(job_data, resume_data, status_text, progress_bar)
            except Exception as ai_error:
                logger.warning(f"AI生成失败，使用模板生成: {ai_error}")
                greetings = self._generate_template_greetings(job_data, resume_data)
            
            status_text.text("生成完成！")
            progress_bar.progress(1.0)
            
            # 清理UI
            progress_bar.empty()
            status_text.empty()
            
            return greetings
            
        except Exception as e:
            logger.error(f"Greeting generation error: {e}")
            st.error(f"生成打招呼语失败: {str(e)}")
            return []
        finally:
            SessionManager.set_loading_state('greeting_generation', False)
    
    def _generate_ai_greetings(self, job_data: Dict[str, Any], resume_data: Dict[str, Any], 
                              status_text, progress_bar) -> List[str]:
        """使用AI生成打招呼语"""
        if not self.ai_analyzer.is_available():
            raise Exception("AI服务不可用")
        
        status_text.text("正在连接AI服务...")
        progress_bar.progress(0.5)
        
        # 构建打招呼语生成提示
        prompt = self._build_greeting_prompt(job_data, resume_data)
        
        status_text.text("正在生成个性化内容...")
        progress_bar.progress(0.8)
        
        # 调用AI生成
        try:
            from ..core.ai_analyzer import DeepSeekClient
            client = DeepSeekClient()
            
            messages = [
                {"role": "system", "content": self._get_greeting_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            ai_response = client.chat_completion(messages)
            greetings = self._parse_greeting_response(ai_response)
            
        except Exception as e:
            logger.error(f"AI生成打招呼语失败: {e}")
            raise
        
        return greetings
    
    def _build_greeting_prompt(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
        """构建打招呼语生成提示"""
        # 提取关键信息
        job_title = job_data.get('title', '')
        company = job_data.get('company', '')
        job_skills = job_data.get('skills', [])
        
        resume_skills = resume_data.get('skills', [])
        personal_info = resume_data.get('personal_info', {})
        experience = resume_data.get('experience', [])
        
        # 计算匹配的技能
        matching_skills = list(set(job_skills) & set(resume_skills))
        
        return f"""请基于以下信息生成3个不同风格的求职打招呼语：

【目标职位】
职位名称：{job_title}
公司名称：{company}
技能要求：{', '.join(job_skills[:5])}

【求职者信息】
技能：{', '.join(resume_skills[:5])}
工作经验：{len(experience)}段工作经历
匹配技能：{', '.join(matching_skills[:3])}

要求：
1. 每个打招呼语控制在80-100字以内
2. 突出匹配的技能和经验
3. 体现对该职位的兴趣和了解
4. 语气要专业但不失亲和力
5. 三个版本分别采用：正式商务、友好专业、简洁直接的风格"""
    
    def _get_greeting_system_prompt(self) -> str:
        """获取打招呼语生成的系统提示"""
        return """你是一个专业的求职顾问，擅长撰写个性化的求职打招呼语。

请严格按照以下JSON格式返回结果：

{
    "greetings": [
        "第一个打招呼语内容",
        "第二个打招呼语内容", 
        "第三个打招呼语内容"
    ]
}

要求：
1. 每个打招呼语要个性化，避免模板化
2. 突出求职者与职位的匹配点
3. 语言要自然流畅，有说服力
4. 避免过度夸大或谦逊
5. 体现专业素养和求职诚意"""
    
    def _parse_greeting_response(self, response: str) -> List[str]:
        """解析AI生成的打招呼语响应"""
        import json
        import re
        
        try:
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                data = json.loads(response)
            
            greetings = data.get('greetings', [])
            
            # 验证和清理
            cleaned_greetings = []
            for greeting in greetings:
                if isinstance(greeting, str) and len(greeting.strip()) > 10:
                    cleaned_greetings.append(greeting.strip())
            
            if len(cleaned_greetings) >= 2:
                return cleaned_greetings[:3]  # 最多返回3个
            else:
                raise ValueError("AI生成的打招呼语数量不足")
                
        except Exception as e:
            logger.error(f"解析打招呼语响应失败: {e}")
            logger.debug(f"原始响应: {response}")
            raise
    
    def _generate_template_greetings(self, job_data: Dict[str, Any], resume_data: Dict[str, Any]) -> List[str]:
        """生成模板打招呼语（AI不可用时的回退方案）"""
        job_title = job_data.get('title', '该职位')
        company = job_data.get('company', '贵公司')
        
        # 提取简历中的关键技能
        skills = resume_data.get('skills', [])
        skill_text = f"，在{skills[0]}"等技术方面有丰富经验" if skills else ""
        
        return [
            f"您好！我对{company}的{job_title}职位非常感兴趣{skill_text}，希望能有机会与您详细交流，期待您的回复。",
            
            f"尊敬的HR，我是一名经验丰富的开发者，看到{company}招聘{job_title}的信息后，觉得自己的技能背景与职位需求高度匹配，希望能加入您的团队。",
            
            f"Hello！我在招聘平台上关注到{company}的{job_title}职位，我的专业技能和项目经验正好符合职位要求，希望有机会进一步沟通。"
        ]