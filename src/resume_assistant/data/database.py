"""SQLite Database Manager for Resume Assistant."""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from contextlib import asynccontextmanager

import aiosqlite

from .models import JobInfo, ResumeContent, MatchAnalysis, GreetingMessage
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
                        overall_score REAL,
                        skill_match_score REAL,
                        experience_score REAL,
                        keyword_coverage REAL,
                        missing_skills TEXT, -- JSON格式
                        strengths TEXT, -- JSON格式
                        suggestions TEXT, -- JSON格式存储优化建议
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
                        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
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
                await db.execute("CREATE INDEX IF NOT EXISTS idx_greetings_job_id ON greetings(job_id)")
                
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
    
    # 数据库维护和工具方法
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            async with self.get_connection() as db:
                stats = {}
                
                # 获取各表的记录数
                tables = ['jobs', 'resumes', 'analyses', 'greetings']
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