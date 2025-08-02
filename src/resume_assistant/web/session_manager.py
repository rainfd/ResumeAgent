"""Session State Management for Streamlit Web Interface."""

from typing import Any, Dict, List, Optional
import streamlit as st
from datetime import datetime
from pathlib import Path

from ..config import get_settings
from ..utils import get_logger

logger = get_logger(__name__)

class SessionManager:
    """管理Streamlit Session State的类"""
    
    @staticmethod
    def init_session_state():
        """初始化所有Session State变量"""
        # 应用基本状态
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
        
        if 'app_logger' not in st.session_state:
            st.session_state.app_logger = logger
        
        # 配置设置
        if 'settings' not in st.session_state:
            st.session_state.settings = get_settings()
        
        # 页面导航
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
        
        # 职位相关数据
        SessionManager._init_job_state()
        
        # 简历相关数据
        SessionManager._init_resume_state()
        
        # 分析结果数据
        SessionManager._init_analysis_state()
        
        # 打招呼语数据
        SessionManager._init_greeting_state()
        
        # Agent相关数据
        SessionManager._init_agent_state()
        
        # UI状态
        SessionManager._init_ui_state()
    
    @staticmethod
    def _init_job_state():
        """初始化职位相关状态"""
        if 'jobs' not in st.session_state:
            st.session_state.jobs = []
        
        if 'selected_job' not in st.session_state:
            st.session_state.selected_job = None
        
        if 'job_scraping_progress' not in st.session_state:
            st.session_state.job_scraping_progress = {}
        
        if 'current_job_url' not in st.session_state:
            st.session_state.current_job_url = ""
    
    @staticmethod
    def _init_resume_state():
        """初始化简历相关状态"""
        if 'resumes' not in st.session_state:
            st.session_state.resumes = []
        
        if 'selected_resume' not in st.session_state:
            st.session_state.selected_resume = None
        
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        
        if 'resume_parsing_progress' not in st.session_state:
            st.session_state.resume_parsing_progress = {}
    
    @staticmethod
    def _init_analysis_state():
        """初始化分析结果状态"""
        if 'analyses' not in st.session_state:
            st.session_state.analyses = []
        
        if 'current_analysis' not in st.session_state:
            st.session_state.current_analysis = None
        
        if 'analysis_progress' not in st.session_state:
            st.session_state.analysis_progress = {}
        
        if 'optimization_suggestions' not in st.session_state:
            st.session_state.optimization_suggestions = []
    
    @staticmethod
    def _init_greeting_state():
        """初始化打招呼语状态"""
        if 'greetings' not in st.session_state:
            st.session_state.greetings = []
        
        if 'current_greeting' not in st.session_state:
            st.session_state.current_greeting = None
        
        if 'greeting_generation_progress' not in st.session_state:
            st.session_state.greeting_generation_progress = {}
    
    @staticmethod
    def _init_agent_state():
        """初始化Agent相关状态"""
        if 'agents' not in st.session_state:
            st.session_state.agents = []
        
        if 'selected_agent' not in st.session_state:
            st.session_state.selected_agent = None
        
        if 'agent_creation_progress' not in st.session_state:
            st.session_state.agent_creation_progress = {}
        
        if 'agent_test_results' not in st.session_state:
            st.session_state.agent_test_results = {}
        
        if 'agent_comparison_results' not in st.session_state:
            st.session_state.agent_comparison_results = None
    
    @staticmethod
    def _init_ui_state():
        """初始化UI相关状态"""
        if 'sidebar_expanded' not in st.session_state:
            st.session_state.sidebar_expanded = True
        
        if 'theme' not in st.session_state:
            st.session_state.theme = 'light'
        
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
    
    @staticmethod
    def add_job(job_data: Dict[str, Any]) -> bool:
        """添加职位到Session State"""
        try:
            job_data['id'] = len(st.session_state.jobs) + 1
            job_data['created_at'] = datetime.now().isoformat()
            st.session_state.jobs.append(job_data)
            
            SessionManager.add_notification("success", f"成功添加职位: {job_data.get('title', '未知职位')}")
            logger.info(f"Added job to session: {job_data.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            SessionManager.add_notification("error", f"添加职位失败: {str(e)}")
            logger.error(f"Failed to add job to session: {e}")
            return False
    
    @staticmethod
    def add_resume(resume_data: Dict[str, Any]) -> bool:
        """添加简历到Session State"""
        try:
            resume_data['id'] = len(st.session_state.resumes) + 1
            resume_data['created_at'] = datetime.now().isoformat()
            st.session_state.resumes.append(resume_data)
            
            SessionManager.add_notification("success", f"成功添加简历: {resume_data.get('name', '未知简历')}")
            logger.info(f"Added resume to session: {resume_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            SessionManager.add_notification("error", f"添加简历失败: {str(e)}")
            logger.error(f"Failed to add resume to session: {e}")
            return False
    
    @staticmethod
    def add_analysis(analysis_data: Dict[str, Any]) -> bool:
        """添加分析结果到Session State"""
        try:
            analysis_data['id'] = len(st.session_state.analyses) + 1
            analysis_data['created_at'] = datetime.now().isoformat()
            st.session_state.analyses.append(analysis_data)
            
            SessionManager.add_notification("success", "分析结果已保存")
            logger.info("Added analysis result to session")
            return True
            
        except Exception as e:
            SessionManager.add_notification("error", f"保存分析结果失败: {str(e)}")
            logger.error(f"Failed to add analysis to session: {e}")
            return False
    
    @staticmethod
    def add_agent(agent_data: Dict[str, Any]) -> bool:
        """添加Agent到Session State"""
        try:
            agent_data['id'] = len(st.session_state.agents) + 1
            agent_data['created_at'] = datetime.now().isoformat()
            st.session_state.agents.append(agent_data)
            
            SessionManager.add_notification("success", f"成功添加Agent: {agent_data.get('name', '未知Agent')}")
            logger.info(f"Added agent to session: {agent_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            SessionManager.add_notification("error", f"添加Agent失败: {str(e)}")
            logger.error(f"Failed to add agent to session: {e}")
            return False
    
    @staticmethod
    def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取职位"""
        for job in st.session_state.jobs:
            if job.get('id') == job_id:
                return job
        return None
    
    @staticmethod
    def get_resume_by_id(resume_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取简历"""
        for resume in st.session_state.resumes:
            if resume.get('id') == resume_id:
                return resume
        return None
    
    @staticmethod
    def get_agent_by_id(agent_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取Agent"""
        for agent in st.session_state.agents:
            if agent.get('id') == agent_id:
                return agent
        return None
    
    @staticmethod
    def remove_job(job_id: int) -> bool:
        """删除职位"""
        try:
            st.session_state.jobs = [job for job in st.session_state.jobs if job.get('id') != job_id]
            SessionManager.add_notification("success", "职位已删除")
            logger.info(f"Removed job with id: {job_id}")
            return True
        except Exception as e:
            SessionManager.add_notification("error", f"删除职位失败: {str(e)}")
            logger.error(f"Failed to remove job: {e}")
            return False
    
    @staticmethod
    def remove_resume(resume_id: int) -> bool:
        """删除简历"""
        try:
            st.session_state.resumes = [resume for resume in st.session_state.resumes if resume.get('id') != resume_id]
            SessionManager.add_notification("success", "简历已删除")
            logger.info(f"Removed resume with id: {resume_id}")
            return True
        except Exception as e:
            SessionManager.add_notification("error", f"删除简历失败: {str(e)}")
            logger.error(f"Failed to remove resume: {e}")
            return False
    
    @staticmethod
    def remove_agent(agent_id: int) -> bool:
        """删除Agent"""
        try:
            st.session_state.agents = [agent for agent in st.session_state.agents if agent.get('id') != agent_id]
            SessionManager.add_notification("success", "Agent已删除")
            logger.info(f"Removed agent with id: {agent_id}")
            return True
        except Exception as e:
            SessionManager.add_notification("error", f"删除Agent失败: {str(e)}")
            logger.error(f"Failed to remove agent: {e}")
            return False
    
    @staticmethod
    def set_loading_state(component: str, is_loading: bool):
        """设置组件加载状态"""
        st.session_state.loading_states[component] = is_loading
    
    @staticmethod
    def get_loading_state(component: str) -> bool:
        """获取组件加载状态"""
        return st.session_state.loading_states.get(component, False)
    
    @staticmethod
    def add_notification(type: str, message: str):
        """添加通知消息"""
        notification = {
            'type': type,  # success, error, warning, info
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.notifications.append(notification)
        
        # 限制通知数量，保留最新的10条
        if len(st.session_state.notifications) > 10:
            st.session_state.notifications = st.session_state.notifications[-10:]
    
    @staticmethod
    def clear_notifications():
        """清空通知"""
        st.session_state.notifications = []
    
    @staticmethod
    def reset_session():
        """重置Session State"""
        logger.info("Resetting session state")
        
        # 保留基本配置
        settings = st.session_state.get('settings')
        
        # 清空所有状态
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # 重新初始化
        SessionManager.init_session_state()
        
        # 恢复配置
        if settings:
            st.session_state.settings = settings
        
        SessionManager.add_notification("success", "会话已重置")
    
    @staticmethod
    def get_session_stats() -> Dict[str, Any]:
        """获取Session State统计信息"""
        return {
            'jobs_count': len(st.session_state.jobs),
            'resumes_count': len(st.session_state.resumes),
            'analyses_count': len(st.session_state.analyses),
            'agents_count': len(st.session_state.agents),
            'greetings_count': len(st.session_state.greetings),
            'notifications_count': len(st.session_state.notifications),
            'current_page': st.session_state.current_page,
            'initialized': st.session_state.initialized
        }
    
    @staticmethod 
    async def get_database_manager():
        """获取数据库管理器"""
        from ..data.database import get_database_manager
        return get_database_manager()