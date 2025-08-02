"""AI Agent 功能数据库迁移脚本

添加 ai_agents 和 agent_usage_history 表，以及修改 analyses 表。
"""

import asyncio
import sqlite3
from pathlib import Path
from typing import Optional

import aiosqlite

from ..database import DatabaseManager
from ...utils import get_logger

logger = get_logger(__name__)


class AIAgentMigration:
    """AI Agent 功能迁移类"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".resume_assistant" / "data.db"
        
    async def check_migration_needed(self) -> bool:
        """检查是否需要迁移"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 检查 ai_agents 表是否存在
                cursor = await db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='ai_agents'
                """)
                result = await cursor.fetchone()
                
                if result:
                    logger.info("AI Agent tables already exist, no migration needed")
                    return False
                    
                logger.info("AI Agent tables not found, migration needed")
                return True
                
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False
    
    async def backup_database(self) -> Path:
        """备份数据库"""
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.with_suffix(f".backup_{timestamp}.db")
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise
    
    async def migrate_database(self, create_backup: bool = True) -> bool:
        """执行数据库迁移"""
        try:
            # 检查是否需要迁移
            if not await self.check_migration_needed():
                return True
            
            # 创建备份
            if create_backup:
                await self.backup_database()
            
            logger.info("Starting AI Agent migration...")
            
            async with aiosqlite.connect(self.db_path) as db:
                # 启用外键约束
                await db.execute("PRAGMA foreign_keys = ON")
                
                # 1. 创建 ai_agents 表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS ai_agents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        agent_type TEXT NOT NULL DEFAULT 'general',
                        prompt_template TEXT NOT NULL,
                        is_builtin BOOLEAN DEFAULT FALSE,
                        usage_count INTEGER DEFAULT 0,
                        average_rating REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 2. 创建 agent_usage_history 表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_usage_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id INTEGER NOT NULL,
                        analysis_id INTEGER NOT NULL,
                        rating REAL,
                        feedback TEXT,
                        execution_time REAL DEFAULT 0.0,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES ai_agents (id) ON DELETE CASCADE,
                        FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
                    )
                """)
                
                # 3. 检查 analyses 表是否需要添加新字段
                cursor = await db.execute("PRAGMA table_info(analyses)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # 添加 agent_id 字段（如果不存在）
                if 'agent_id' not in column_names:
                    await db.execute("""
                        ALTER TABLE analyses ADD COLUMN agent_id INTEGER
                        REFERENCES ai_agents (id) ON DELETE SET NULL
                    """)
                    logger.info("Added agent_id column to analyses table")
                
                # 添加 raw_response 字段（如果不存在）
                if 'raw_response' not in column_names:
                    await db.execute("""
                        ALTER TABLE analyses ADD COLUMN raw_response TEXT
                    """)
                    logger.info("Added raw_response column to analyses table")
                
                # 添加 execution_time 字段（如果不存在）
                if 'execution_time' not in column_names:
                    await db.execute("""
                        ALTER TABLE analyses ADD COLUMN execution_time REAL DEFAULT 0.0
                    """)
                    logger.info("Added execution_time column to analyses table")
                
                # 4. 创建索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_analyses_agent_id ON analyses(agent_id)",
                    "CREATE INDEX IF NOT EXISTS idx_agents_type ON ai_agents(agent_type)",
                    "CREATE INDEX IF NOT EXISTS idx_agents_builtin ON ai_agents(is_builtin)",
                    "CREATE INDEX IF NOT EXISTS idx_agent_usage_agent_id ON agent_usage_history(agent_id)",
                    "CREATE INDEX IF NOT EXISTS idx_agent_usage_analysis_id ON agent_usage_history(analysis_id)"
                ]
                
                for index_sql in indexes:
                    await db.execute(index_sql)
                
                # 5. 插入内置 Agent 数据
                await self.insert_builtin_agents(db)
                
                await db.commit()
                logger.info("AI Agent migration completed successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def insert_builtin_agents(self, db: aiosqlite.Connection):
        """插入内置 Agent 数据"""
        builtin_agents = [
            {
                'name': '通用分析Agent',
                'description': '适用于所有类型职位的通用分析',
                'agent_type': 'general',
                'prompt_template': '''请分析以下简历与职位的匹配度：

职位描述：{job_description}
简历内容：{resume_content}

请从以下维度进行分析：
1. 技能匹配度 (0-100分)
2. 经验匹配度 (0-100分)  
3. 关键词覆盖率 (0-100分)
4. 总体匹配度 (0-100分)
5. 缺失的关键技能
6. 简历优势
7. 改进建议

请以JSON格式返回结果。''',
                'is_builtin': True
            },
            {
                'name': '技术岗位专用Agent',
                'description': '专门针对技术开发岗位的深度分析',
                'agent_type': 'technical',
                'prompt_template': '''作为技术招聘专家，请深度分析以下技术岗位简历匹配度：

职位技能要求：{job_skills}
职位描述：{job_description}
简历技能：{resume_skills}
简历内容：{resume_content}

重点分析：
1. 编程语言匹配度
2. 技术栈相关性
3. 项目经验技术含量
4. 技术深度评估
5. 学习能力体现
6. 具体的技术改进建议

请提供详细的技术评估和具体的技能提升建议。''',
                'is_builtin': True
            },
            {
                'name': '管理岗位专用Agent',
                'description': '专门针对管理类岗位的领导力分析',
                'agent_type': 'management',
                'prompt_template': '''作为管理岗位招聘专家，请分析以下管理岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 领导力体现
2. 团队管理经验
3. 项目管理能力
4. 战略思维展现
5. 沟通协调能力
6. 业绩管理经验
7. 管理经验的提升建议

请从管理者角度提供专业评估和发展建议。''',
                'is_builtin': True
            },
            {
                'name': '创意行业专用Agent',
                'description': '专门针对创意设计类岗位的创新能力分析',
                'agent_type': 'creative',
                'prompt_template': '''作为创意行业招聘专家，请分析以下创意岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 创意思维体现
2. 设计能力展现
3. 作品集质量
4. 创新项目经验
5. 美学素养体现
6. 跨媒体技能
7. 创意能力提升建议

请从创意专业角度提供评估和作品优化建议。''',
                'is_builtin': True
            },
            {
                'name': '销售岗位专用Agent',
                'description': '专门针对销售类岗位的业绩和沟通能力分析',
                'agent_type': 'sales',
                'prompt_template': '''作为销售招聘专家，请分析以下销售岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 销售业绩数据
2. 客户关系管理能力
3. 沟通谈判技巧
4. 市场开拓经验
5. 目标达成能力
6. 抗压能力体现
7. 销售技能提升建议

请从销售专业角度提供评估和业绩优化建议。''',
                'is_builtin': True
            }
        ]
        
        for agent_data in builtin_agents:
            # 检查是否已存在
            cursor = await db.execute("""
                SELECT id FROM ai_agents WHERE name = ? AND is_builtin = 1
            """, (agent_data['name'],))
            existing = await cursor.fetchone()
            
            if not existing:
                await db.execute("""
                    INSERT INTO ai_agents (name, description, agent_type, prompt_template, is_builtin)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    agent_data['name'],
                    agent_data['description'],
                    agent_data['agent_type'],
                    agent_data['prompt_template'],
                    agent_data['is_builtin']
                ))
                logger.info(f"Inserted builtin agent: {agent_data['name']}")
    
    async def rollback_migration(self, backup_path: Path) -> bool:
        """回滚迁移（从备份恢复）"""
        try:
            import shutil
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # 替换当前数据库
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            return False


# 便捷函数
async def migrate_ai_agents(db_path: Optional[Path] = None, create_backup: bool = True) -> bool:
    """执行 AI Agent 迁移"""
    migration = AIAgentMigration(db_path)
    return await migration.migrate_database(create_backup)


async def check_ai_agent_migration_needed(db_path: Optional[Path] = None) -> bool:
    """检查是否需要 AI Agent 迁移"""
    migration = AIAgentMigration(db_path)
    return await migration.check_migration_needed()


if __name__ == "__main__":
    # 运行迁移
    async def main():
        migration = AIAgentMigration()
        
        if await migration.check_migration_needed():
            print("Starting AI Agent migration...")
            success = await migration.migrate_database()
            if success:
                print("Migration completed successfully!")
            else:
                print("Migration failed!")
        else:
            print("No migration needed.")
    
    asyncio.run(main())