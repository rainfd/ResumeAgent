"""SQLite Database Manager for Resume Assistant."""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from contextlib import asynccontextmanager

import aiosqlite

from .models import JobInfo, ResumeContent, MatchAnalysis, GreetingMessage, AIAgent, AgentUsageHistory, AgentType
from ..utils import get_logger
from ..utils.errors import DatabaseError

logger = get_logger(__name__)

class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: Union[str, Path] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            db_path = Path.home() / ".resume_assistant" / "data.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database initialized at: {self.db_path}")
        self._closed = False
    
    async def close(self):
        """关闭数据库连接"""
        if not self._closed:
            self._closed = True
            logger.info("Database connection closed")
    
    async def init_database(self):
        """初始化数据库表结构"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 启用外键约束
                await db.execute("PRAGMA foreign_keys = ON")
                
                # 创建职位表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        location TEXT,
                        salary TEXT,
                        experience TEXT,
                        education TEXT,
                        description TEXT,
                        requirements TEXT,
                        skills TEXT, -- JSON格式存储
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建简历表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS resumes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        file_path TEXT,
                        content TEXT NOT NULL,
                        personal_info TEXT, -- JSON格式
                        education TEXT, -- JSON格式
                        experience TEXT, -- JSON格式
                        projects TEXT, -- JSON格式
                        skills TEXT, -- JSON格式
                        file_type TEXT,
                        file_size INTEGER,
                        is_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建分析结果表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER NOT NULL,
                        resume_id INTEGER NOT NULL,
                        agent_id INTEGER, -- 使用的 Agent ID
                        overall_score REAL,
                        skill_match_score REAL,
                        experience_score REAL,
                        keyword_coverage REAL,
                        missing_skills TEXT, -- JSON格式
                        strengths TEXT, -- JSON格式
                        suggestions TEXT, -- JSON格式存储优化建议
                        raw_response TEXT, -- AI 原始响应
                        execution_time REAL DEFAULT 0.0, -- 执行时间
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
                        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
                        FOREIGN KEY (agent_id) REFERENCES ai_agents (id) ON DELETE SET NULL
                    )
                """)
                
                # 创建打招呼语表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS greetings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER NOT NULL,
                        resume_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        version INTEGER DEFAULT 1,
                        is_custom BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
                        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建 AI Agent 配置表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS ai_agents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        agent_type TEXT NOT NULL DEFAULT 'general', -- general, technical, management, creative, sales, custom
                        prompt_template TEXT NOT NULL,
                        is_builtin BOOLEAN DEFAULT FALSE,
                        usage_count INTEGER DEFAULT 0,
                        average_rating REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建 Agent 使用历史表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_usage_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id INTEGER NOT NULL,
                        analysis_id INTEGER NOT NULL,
                        rating REAL, -- 用户评分 1-5
                        feedback TEXT, -- 用户反馈
                        execution_time REAL DEFAULT 0.0, -- 执行时间（秒）
                        success BOOLEAN DEFAULT TRUE, -- 是否执行成功
                        error_message TEXT, -- 错误信息（如果有）
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES ai_agents (id) ON DELETE CASCADE,
                        FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建应用配置表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引以优化查询性能
                await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_analyses_job_resume ON analyses(job_id, resume_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_analyses_agent_id ON analyses(agent_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_greetings_job_id ON greetings(job_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_type ON ai_agents(agent_type)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_builtin ON ai_agents(is_builtin)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_usage_agent_id ON agent_usage_history(agent_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_usage_analysis_id ON agent_usage_history(analysis_id)")
                
                await db.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row  # 使用Row工厂以便按列名访问
                yield db
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    # 职位相关操作
    async def save_job(self, job_data: Dict[str, Any]) -> int:
        """保存职位信息"""
        try:
            async with self.get_connection() as db:
                # 检查URL是否已存在
                cursor = await db.execute("SELECT id FROM jobs WHERE url = ?", (job_data.get('url'),))
                existing_job = await cursor.fetchone()
                
                if existing_job:
                    logger.info(f"Job with URL already exists, updating: {job_data.get('url')}")
                    return await self.update_job(existing_job['id'], job_data)
                
                # 插入新职位
                skills_json = json.dumps(job_data.get('skills', []), ensure_ascii=False)
                
                cursor = await db.execute("""
                    INSERT INTO jobs (url, title, company, location, salary, experience, 
                                    education, description, requirements, skills)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data.get('url', ''),
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('location', ''),
                    job_data.get('salary', ''),
                    job_data.get('experience', ''),
                    job_data.get('education', ''),
                    job_data.get('description', ''),
                    job_data.get('requirements', ''),
                    skills_json
                ))
                
                await db.commit()
                job_id = cursor.lastrowid
                logger.info(f"Job saved with ID: {job_id}")
                return job_id
                
        except Exception as e:
            logger.error(f"Failed to save job: {e}")
            raise DatabaseError(f"Failed to save job: {e}")
    
    async def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取职位信息"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = await cursor.fetchone()
                
                if row:
                    job_data = dict(row)
                    job_data['skills'] = json.loads(job_data.get('skills', '[]'))
                    return job_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise DatabaseError(f"Failed to get job: {e}")
    
    async def get_all_jobs(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有职位信息"""
        try:
            async with self.get_connection() as db:
                query = "SELECT * FROM jobs ORDER BY created_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                jobs = []
                for row in rows:
                    job_data = dict(row)
                    job_data['skills'] = json.loads(job_data.get('skills', '[]'))
                    jobs.append(job_data)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Failed to get all jobs: {e}")
            raise DatabaseError(f"Failed to get jobs: {e}")
    
    async def update_job(self, job_id: int, job_data: Dict[str, Any]) -> int:
        """更新职位信息"""
        try:
            async with self.get_connection() as db:
                skills_json = json.dumps(job_data.get('skills', []), ensure_ascii=False)
                
                await db.execute("""
                    UPDATE jobs SET title = ?, company = ?, location = ?, salary = ?, 
                                  experience = ?, education = ?, description = ?, 
                                  requirements = ?, skills = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('location', ''),
                    job_data.get('salary', ''),
                    job_data.get('experience', ''),
                    job_data.get('education', ''),
                    job_data.get('description', ''),
                    job_data.get('requirements', ''),
                    skills_json,
                    job_id
                ))
                
                await db.commit()
                logger.info(f"Job updated: {job_id}")
                return job_id
                
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise DatabaseError(f"Failed to update job: {e}")
    
    async def delete_job(self, job_id: int) -> bool:
        """删除职位信息"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                await db.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Job deleted: {job_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise DatabaseError(f"Failed to delete job: {e}")
    
    # 简历相关操作
    async def save_resume(self, resume_data: Dict[str, Any]) -> int:
        """保存简历信息"""
        try:
            async with self.get_connection() as db:
                # 转换为JSON格式
                personal_info_json = json.dumps(resume_data.get('personal_info', {}), ensure_ascii=False)
                education_json = json.dumps(resume_data.get('education', []), ensure_ascii=False)
                experience_json = json.dumps(resume_data.get('experience', []), ensure_ascii=False)
                projects_json = json.dumps(resume_data.get('projects', []), ensure_ascii=False)
                skills_json = json.dumps(resume_data.get('skills', []), ensure_ascii=False)
                
                cursor = await db.execute("""
                    INSERT INTO resumes (name, file_path, content, personal_info, education, 
                                       experience, projects, skills, file_type, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    resume_data.get('name', ''),
                    resume_data.get('file_path', ''),
                    resume_data.get('content', ''),
                    personal_info_json,
                    education_json,
                    experience_json,
                    projects_json,
                    skills_json,
                    resume_data.get('file_type', ''),
                    resume_data.get('file_size', 0)
                ))
                
                await db.commit()
                resume_id = cursor.lastrowid
                logger.info(f"Resume saved with ID: {resume_id}")
                return resume_id
                
        except Exception as e:
            logger.error(f"Failed to save resume: {e}")
            raise DatabaseError(f"Failed to save resume: {e}")
    
    async def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取简历信息"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
                row = await cursor.fetchone()
                
                if row:
                    resume_data = dict(row)
                    # 解析JSON字段
                    resume_data['personal_info'] = json.loads(resume_data.get('personal_info', '{}'))
                    resume_data['education'] = json.loads(resume_data.get('education', '[]'))
                    resume_data['experience'] = json.loads(resume_data.get('experience', '[]'))
                    resume_data['projects'] = json.loads(resume_data.get('projects', '[]'))
                    resume_data['skills'] = json.loads(resume_data.get('skills', '[]'))
                    return resume_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get resume {resume_id}: {e}")
            raise DatabaseError(f"Failed to get resume: {e}")
    
    async def get_all_resumes(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有简历信息"""
        try:
            async with self.get_connection() as db:
                query = "SELECT * FROM resumes ORDER BY created_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                resumes = []
                for row in rows:
                    resume_data = dict(row)
                    # 解析JSON字段
                    resume_data['personal_info'] = json.loads(resume_data.get('personal_info', '{}'))
                    resume_data['education'] = json.loads(resume_data.get('education', '[]'))
                    resume_data['experience'] = json.loads(resume_data.get('experience', '[]'))
                    resume_data['projects'] = json.loads(resume_data.get('projects', '[]'))
                    resume_data['skills'] = json.loads(resume_data.get('skills', '[]'))
                    resumes.append(resume_data)
                
                return resumes
                
        except Exception as e:
            logger.error(f"Failed to get all resumes: {e}")
            raise DatabaseError(f"Failed to get resumes: {e}")
    
    async def delete_resume(self, resume_id: int) -> bool:
        """删除简历信息"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
                await db.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Resume deleted: {resume_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            raise DatabaseError(f"Failed to delete resume: {e}")
    
    # 分析结果相关操作
    async def save_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """保存分析结果"""
        try:
            async with self.get_connection() as db:
                missing_skills_json = json.dumps(analysis_data.get('missing_skills', []), ensure_ascii=False)
                strengths_json = json.dumps(analysis_data.get('strengths', []), ensure_ascii=False)
                suggestions_json = json.dumps(analysis_data.get('suggestions', []), ensure_ascii=False)
                
                cursor = await db.execute("""
                    INSERT INTO analyses (job_id, resume_id, overall_score, skill_match_score,
                                        experience_score, keyword_coverage, missing_skills, 
                                        strengths, suggestions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data.get('job_id'),
                    analysis_data.get('resume_id'),
                    analysis_data.get('overall_score', 0.0),
                    analysis_data.get('skill_match_score', 0.0),
                    analysis_data.get('experience_score', 0.0),
                    analysis_data.get('keyword_coverage', 0.0),
                    missing_skills_json,
                    strengths_json,
                    suggestions_json
                ))
                
                await db.commit()
                analysis_id = cursor.lastrowid
                logger.info(f"Analysis saved with ID: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            raise DatabaseError(f"Failed to save analysis: {e}")
    
    async def get_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取分析结果"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
                row = await cursor.fetchone()
                
                if row:
                    analysis_data = dict(row)
                    # 解析JSON字段
                    analysis_data['missing_skills'] = json.loads(analysis_data.get('missing_skills', '[]'))
                    analysis_data['strengths'] = json.loads(analysis_data.get('strengths', '[]'))
                    analysis_data['suggestions'] = json.loads(analysis_data.get('suggestions', '[]'))
                    return analysis_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get analysis {analysis_id}: {e}")
            raise DatabaseError(f"Failed to get analysis: {e}")
    
    async def get_all_analyses(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有分析结果"""
        try:
            async with self.get_connection() as db:
                query = "SELECT * FROM analyses ORDER BY created_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                analyses = []
                for row in rows:
                    analysis_data = dict(row)
                    # 解析JSON字段
                    analysis_data['missing_skills'] = json.loads(analysis_data.get('missing_skills', '[]'))
                    analysis_data['strengths'] = json.loads(analysis_data.get('strengths', '[]'))
                    analysis_data['suggestions'] = json.loads(analysis_data.get('suggestions', '[]'))
                    analyses.append(analysis_data)
                
                return analyses
                
        except Exception as e:
            logger.error(f"Failed to get all analyses: {e}")
            raise DatabaseError(f"Failed to get analyses: {e}")
    
    # 打招呼语相关操作
    async def save_greeting(self, greeting_data: Dict[str, Any]) -> int:
        """保存打招呼语"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    INSERT INTO greetings (job_id, resume_id, content, version, is_custom)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    greeting_data.get('job_id'),
                    greeting_data.get('resume_id'),
                    greeting_data.get('content', ''),
                    greeting_data.get('version', 1),
                    greeting_data.get('is_custom', False)
                ))
                
                await db.commit()
                greeting_id = cursor.lastrowid
                logger.info(f"Greeting saved with ID: {greeting_id}")
                return greeting_id
                
        except Exception as e:
            logger.error(f"Failed to save greeting: {e}")
            raise DatabaseError(f"Failed to save greeting: {e}")
    
    async def get_greeting(self, greeting_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取打招呼语"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("SELECT * FROM greetings WHERE id = ?", (greeting_id,))
                row = await cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get greeting {greeting_id}: {e}")
            raise DatabaseError(f"Failed to get greeting: {e}")
    
    async def get_greetings_by_job_resume(self, job_id: int, resume_id: int) -> List[Dict[str, Any]]:
        """根据职位和简历ID获取打招呼语列表"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute(
                    "SELECT * FROM greetings WHERE job_id = ? AND resume_id = ? ORDER BY created_at DESC", 
                    (job_id, resume_id)
                )
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get greetings for job {job_id} and resume {resume_id}: {e}")
            raise DatabaseError(f"Failed to get greetings: {e}")
    
    async def get_all_greetings(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有打招呼语"""
        try:
            async with self.get_connection() as db:
                query = "SELECT * FROM greetings ORDER BY created_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all greetings: {e}")
            raise DatabaseError(f"Failed to get greetings: {e}")
    
    async def delete_greeting(self, greeting_id: int) -> bool:
        """删除打招呼语"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("DELETE FROM greetings WHERE id = ?", (greeting_id,))
                await db.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Greeting deleted: {greeting_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete greeting {greeting_id}: {e}")
            raise DatabaseError(f"Failed to delete greeting: {e}")
    
    # AI Agent 相关操作
    async def save_agent(self, agent: AIAgent) -> int:
        """保存 AI Agent 配置"""
        try:
            async with self.get_connection() as db:
                if agent.id:
                    # 更新现有 Agent
                    cursor = await db.execute("""
                        UPDATE ai_agents SET 
                        name = ?, description = ?, agent_type = ?, prompt_template = ?,
                        is_builtin = ?, usage_count = ?, average_rating = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        agent.name, agent.description, agent.agent_type.value,
                        agent.prompt_template, agent.is_builtin, agent.usage_count,
                        agent.average_rating, datetime.now().isoformat(), agent.id
                    ))
                    await db.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Agent updated: {agent.name} (ID: {agent.id})")
                        return agent.id
                    else:
                        raise DatabaseError(f"Agent with ID {agent.id} not found")
                else:
                    # 创建新 Agent
                    cursor = await db.execute("""
                        INSERT INTO ai_agents (name, description, agent_type, prompt_template, 
                                             is_builtin, usage_count, average_rating, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        agent.name, agent.description, agent.agent_type.value,
                        agent.prompt_template, agent.is_builtin, agent.usage_count,
                        agent.average_rating, agent.created_at.isoformat(), 
                        agent.updated_at.isoformat()
                    ))
                    await db.commit()
                    
                    agent_id = cursor.lastrowid
                    logger.info(f"Agent created: {agent.name} (ID: {agent_id})")
                    return agent_id
                    
        except Exception as e:
            logger.error(f"Failed to save agent: {e}")
            raise DatabaseError(f"Failed to save agent: {e}")
    
    async def get_agent(self, agent_id: int) -> Optional[AIAgent]:
        """获取指定的 AI Agent"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    SELECT * FROM ai_agents WHERE id = ?
                """, (agent_id,))
                row = await cursor.fetchone()
                
                if row:
                    return self._row_to_agent(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise DatabaseError(f"Failed to get agent: {e}")
    
    async def get_all_agents(self, include_builtin: bool = True, agent_type: Optional[AgentType] = None) -> List[AIAgent]:
        """获取所有 AI Agent"""
        try:
            async with self.get_connection() as db:
                query = "SELECT * FROM ai_agents"
                params = []
                conditions = []
                
                if not include_builtin:
                    conditions.append("is_builtin = ?")
                    params.append(False)
                
                if agent_type:
                    conditions.append("agent_type = ?")
                    params.append(agent_type.value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY is_builtin DESC, created_at ASC"
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                agents = []
                for row in rows:
                    agent = self._row_to_agent(dict(row))
                    if agent:
                        agents.append(agent)
                
                return agents
                
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            raise DatabaseError(f"Failed to get agents: {e}")
    
    async def update_agent(self, agent: AIAgent) -> bool:
        """更新 AI Agent"""
        try:
            if not agent.id:
                raise ValueError("Agent ID is required for update")
            
            agent.updated_at = datetime.now()
            updated_id = await self.save_agent(agent)
            return updated_id == agent.id
            
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            raise DatabaseError(f"Failed to update agent: {e}")
    
    async def delete_agent(self, agent_id: int) -> bool:
        """删除 AI Agent（仅限非内置）"""
        try:
            async with self.get_connection() as db:
                # 启用外键约束
                await db.execute("PRAGMA foreign_keys = ON")
                
                # 首先检查是否为内置 Agent
                cursor = await db.execute("SELECT is_builtin FROM ai_agents WHERE id = ?", (agent_id,))
                row = await cursor.fetchone()
                
                if not row:
                    return False
                
                if row['is_builtin']:
                    raise ValueError("Cannot delete builtin agent")
                
                # 删除 Agent（由于外键约束，相关的使用历史会被级联删除）
                cursor = await db.execute("DELETE FROM ai_agents WHERE id = ?", (agent_id,))
                await db.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Agent deleted: {agent_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise DatabaseError(f"Failed to delete agent: {e}")
    
    async def update_agent_usage(self, agent_id: int, rating: Optional[float] = None) -> bool:
        """更新 Agent 使用统计"""
        try:
            async with self.get_connection() as db:
                # 获取当前统计信息
                cursor = await db.execute("""
                    SELECT usage_count, average_rating FROM ai_agents WHERE id = ?
                """, (agent_id,))
                row = await cursor.fetchone()
                
                if not row:
                    return False
                
                current_usage = row['usage_count']
                current_rating = row['average_rating']
                
                # 更新使用次数
                new_usage = current_usage + 1
                
                # 更新平均评分（如果提供了新评分）
                if rating is not None and 1.0 <= rating <= 5.0:
                    if current_usage == 0:
                        new_rating = rating
                    else:
                        total_rating = current_rating * current_usage + rating
                        new_rating = total_rating / new_usage
                else:
                    new_rating = current_rating
                
                # 保存更新
                cursor = await db.execute("""
                    UPDATE ai_agents SET usage_count = ?, average_rating = ?, updated_at = ?
                    WHERE id = ?
                """, (new_usage, new_rating, datetime.now().isoformat(), agent_id))
                await db.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update agent usage {agent_id}: {e}")
            raise DatabaseError(f"Failed to update agent usage: {e}")
    
    async def save_agent_usage_history(self, usage: AgentUsageHistory) -> int:
        """保存 Agent 使用历史"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    INSERT INTO agent_usage_history 
                    (agent_id, analysis_id, rating, feedback, execution_time, success, error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.agent_id, usage.analysis_id, usage.rating, usage.feedback,
                    usage.execution_time, usage.success, usage.error_message,
                    usage.created_at.isoformat()
                ))
                await db.commit()
                
                usage_id = cursor.lastrowid
                logger.info(f"Agent usage history saved: {usage_id}")
                return usage_id
                
        except Exception as e:
            logger.error(f"Failed to save agent usage history: {e}")
            raise DatabaseError(f"Failed to save agent usage history: {e}")
    
    async def get_agent_usage_history(self, agent_id: int, limit: int = 50, offset: int = 0) -> List[AgentUsageHistory]:
        """获取 Agent 使用历史"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    SELECT * FROM agent_usage_history 
                    WHERE agent_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (agent_id, limit, offset))
                rows = await cursor.fetchall()
                
                history = []
                for row in rows:
                    usage = self._row_to_usage_history(dict(row))
                    if usage:
                        history.append(usage)
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get agent usage history for {agent_id}: {e}")
            raise DatabaseError(f"Failed to get agent usage history: {e}")
    
    async def get_agent_statistics(self, agent_id: int) -> Dict[str, Any]:
        """获取 Agent 统计信息"""
        try:
            async with self.get_connection() as db:
                # 基本统计
                cursor = await db.execute("""
                    SELECT usage_count, average_rating FROM ai_agents WHERE id = ?
                """, (agent_id,))
                agent_row = await cursor.fetchone()
                
                if not agent_row:
                    return {}
                
                # 使用历史统计
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_uses,
                        AVG(execution_time) as avg_execution_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_uses,
                        AVG(CASE WHEN rating IS NOT NULL THEN rating END) as avg_user_rating,
                        COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as rating_count
                    FROM agent_usage_history 
                    WHERE agent_id = ?
                """, (agent_id,))
                stats_row = await cursor.fetchone()
                
                stats = {
                    'usage_count': agent_row['usage_count'],
                    'average_rating': agent_row['average_rating'],
                    'total_uses': stats_row['total_uses'] if stats_row else 0,
                    'avg_execution_time': stats_row['avg_execution_time'] if stats_row else 0.0,
                    'successful_uses': stats_row['successful_uses'] if stats_row else 0,
                    'success_rate': 0.0,
                    'avg_user_rating': stats_row['avg_user_rating'] if stats_row else 0.0,
                    'rating_count': stats_row['rating_count'] if stats_row else 0
                }
                
                # 计算成功率
                if stats['total_uses'] > 0:
                    stats['success_rate'] = stats['successful_uses'] / stats['total_uses']
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get agent statistics for {agent_id}: {e}")
            return {}
    
    async def get_agent_usage_history_by_id(self, usage_id: int) -> Optional[AgentUsageHistory]:
        """根据ID获取单个使用历史记录"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    SELECT * FROM agent_usage_history WHERE id = ?
                """, (usage_id,))
                row = await cursor.fetchone()
                
                if row:
                    return self._row_to_agent_usage_history(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent usage history {usage_id}: {e}")
            return None
    
    async def update_agent_usage_history(self, usage: AgentUsageHistory) -> bool:
        """更新Agent使用历史记录"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    UPDATE agent_usage_history SET 
                        rating = ?, feedback = ?
                    WHERE id = ?
                """, (usage.rating, usage.feedback, usage.id))
                await db.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated agent usage history: {usage.id}")
                return success
                
        except Exception as e:
            logger.error(f"Failed to update agent usage history {usage.id}: {e}")
            return False
    
    def _row_to_agent(self, row: Dict[str, Any]) -> Optional[AIAgent]:
        """将数据库行转换为 AIAgent 对象"""
        try:
            # 处理 agent_type
            agent_type_str = row.get('agent_type', 'general')
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                agent_type = AgentType.GENERAL
            
            # 处理日期时间
            created_at = row.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            elif not isinstance(created_at, datetime):
                created_at = datetime.now()
            
            updated_at = row.get('updated_at')
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            elif not isinstance(updated_at, datetime):
                updated_at = datetime.now()
            
            return AIAgent(
                id=row.get('id'),
                name=row.get('name', ''),
                description=row.get('description', ''),
                agent_type=agent_type,
                prompt_template=row.get('prompt_template', ''),
                is_builtin=bool(row.get('is_builtin', False)),
                usage_count=row.get('usage_count', 0),
                average_rating=row.get('average_rating', 0.0),
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to convert row to AIAgent: {e}")
            return None
    
    def _row_to_usage_history(self, row: Dict[str, Any]) -> Optional[AgentUsageHistory]:
        """将数据库行转换为 AgentUsageHistory 对象"""
        try:
            created_at = row.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            elif not isinstance(created_at, datetime):
                created_at = datetime.now()
            
            return AgentUsageHistory(
                id=row.get('id'),
                agent_id=row.get('agent_id', 0),
                analysis_id=row.get('analysis_id', 0),
                rating=row.get('rating'),
                feedback=row.get('feedback', ''),
                execution_time=row.get('execution_time', 0.0),
                success=bool(row.get('success', True)),
                error_message=row.get('error_message', ''),
                created_at=created_at
            )
        except Exception as e:
            logger.error(f"Failed to convert row to AgentUsageHistory: {e}")
            return None
    
    # 数据库维护和工具方法
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            async with self.get_connection() as db:
                stats = {}
                
                # 获取各表的记录数
                tables = ['jobs', 'resumes', 'analyses', 'greetings', 'ai_agents', 'agent_usage_history']
                for table in tables:
                    cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table}")
                    row = await cursor.fetchone()
                    stats[f"{table}_count"] = row['count'] if row else 0
                
                # 获取数据库文件大小
                stats['db_size'] = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def vacuum_database(self):
        """压缩数据库"""
        try:
            async with self.get_connection() as db:
                await db.execute("VACUUM")
                logger.info("Database vacuumed successfully")
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            raise DatabaseError(f"Failed to vacuum database: {e}")


# 创建全局数据库实例
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """获取数据库管理器单例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_database():
    """初始化数据库"""
    db_manager = get_database_manager()
    await db_manager.init_database()