"""数据库和模型单元测试"""

import unittest
import asyncio
import tempfile
import sys
from pathlib import Path
from datetime import datetime
import sqlite3
import os

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.data.database import DatabaseManager
from resume_assistant.core.job_manager import Job
from resume_assistant.data.models import (
    JobInfo, ResumeContent, AIAgent, AgentType
)
from resume_assistant.utils.errors import DatabaseError


class TestDatabaseManager(unittest.TestCase):
    """数据库管理器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        # 关闭数据库连接
        asyncio.run(self.db_manager.close())
        
        # 删除临时数据库文件
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_database_initialization(self):
        """测试数据库初始化"""
        await self.db_manager.initialize()
        
        # 检查表是否存在
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['jobs', 'resumes', 'analyses', 'ai_agents']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    async def test_database_migration(self):
        """测试数据库迁移"""
        await self.db_manager.initialize()
        
        # 检查迁移记录
        migration_status = await self.db_manager.get_migration_status()
        self.assertIsInstance(migration_status, dict)
    
    async def test_connection_management(self):
        """测试连接管理"""
        # 测试获取连接
        async with self.db_manager.get_connection() as conn:
            self.assertIsNotNone(conn)
            
            # 执行简单查询
            async with conn.execute("SELECT 1") as cursor:
                result = await cursor.fetchone()
                self.assertEqual(result[0], 1)
    
    async def test_transaction_management(self):
        """测试事务管理"""
        await self.db_manager.initialize()
        
        # 测试成功事务
        async with self.db_manager.transaction() as conn:
            await conn.execute(
                "INSERT INTO jobs (id, title, company, url, status) VALUES (?, ?, ?, ?, ?)",
                ("test-job-1", "测试职位", "测试公司", "https://example.com", "active")
            )
        
        # 验证数据已提交
        job = await self.db_manager.get_job("test-job-1")
        self.assertIsNotNone(job)
        self.assertEqual(job.title, "测试职位")
        
        # 测试回滚事务
        try:
            async with self.db_manager.transaction() as conn:
                await conn.execute(
                    "INSERT INTO jobs (id, title, company, url, status) VALUES (?, ?, ?, ?, ?)",
                    ("test-job-2", "测试职位2", "测试公司2", "https://example2.com", "active")
                )
                # 强制抛出异常
                raise Exception("测试回滚")
        except Exception:
            pass
        
        # 验证数据未提交
        job = await self.db_manager.get_job("test-job-2")
        self.assertIsNone(job)
    
    async def test_error_handling(self):
        """测试错误处理"""
        await self.db_manager.initialize()
        
        # 测试SQL错误
        with self.assertRaises(DatabaseError):
            async with self.db_manager.get_connection() as conn:
                await conn.execute("INVALID SQL STATEMENT")


class TestJobModel(unittest.TestCase):
    """职位模型测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_job_creation(self):
        """测试创建职位"""
        await self.db_manager.initialize()
        
        job = Job(
            id="test-job-123",
            title="Python开发工程师",
            company="测试公司",
            url="https://example.com/job/123",
            location="北京",
            salary="15k-25k",
            requirements="Python, Django, Redis",
            description="负责后端开发工作",
            status=JobStatus.ACTIVE
        )
        
        # 保存职位
        await self.db_manager.save_job(job)
        
        # 获取职位
        saved_job = await self.db_manager.get_job("test-job-123")
        
        self.assertIsNotNone(saved_job)
        self.assertEqual(saved_job.title, "Python开发工程师")
        self.assertEqual(saved_job.company, "测试公司")
        self.assertEqual(saved_job.status, JobStatus.ACTIVE)
    
    async def test_job_update(self):
        """测试更新职位"""
        await self.db_manager.initialize()
        
        # 创建职位
        job = Job(
            id="test-job-update",
            title="原始标题",
            company="原始公司",
            url="https://example.com/job/update"
        )
        await self.db_manager.save_job(job)
        
        # 更新职位
        job.title = "更新后标题"
        job.company = "更新后公司"
        job.status = JobStatus.ARCHIVED
        
        await self.db_manager.update_job(job)
        
        # 验证更新
        updated_job = await self.db_manager.get_job("test-job-update")
        self.assertEqual(updated_job.title, "更新后标题")
        self.assertEqual(updated_job.company, "更新后公司")
        self.assertEqual(updated_job.status, JobStatus.ARCHIVED)
    
    async def test_job_deletion(self):
        """测试删除职位"""
        await self.db_manager.initialize()
        
        # 创建职位
        job = Job(
            id="test-job-delete",
            title="待删除职位",
            company="测试公司",
            url="https://example.com/job/delete"
        )
        await self.db_manager.save_job(job)
        
        # 验证职位存在
        self.assertIsNotNone(await self.db_manager.get_job("test-job-delete"))
        
        # 删除职位
        await self.db_manager.delete_job("test-job-delete")
        
        # 验证职位已删除
        self.assertIsNone(await self.db_manager.get_job("test-job-delete"))
    
    async def test_job_list(self):
        """测试获取职位列表"""
        await self.db_manager.initialize()
        
        # 创建多个职位
        jobs = [
            Job(id="job-1", title="职位1", company="公司1", url="https://example.com/1"),
            Job(id="job-2", title="职位2", company="公司2", url="https://example.com/2"),
            Job(id="job-3", title="职位3", company="公司3", url="https://example.com/3", status=JobStatus.ARCHIVED)
        ]
        
        for job in jobs:
            await self.db_manager.save_job(job)
        
        # 获取所有职位
        all_jobs = await self.db_manager.get_all_jobs()
        self.assertEqual(len(all_jobs), 3)
        
        # 获取活跃职位
        active_jobs = await self.db_manager.get_jobs_by_status(JobStatus.ACTIVE)
        self.assertEqual(len(active_jobs), 2)
        
        # 获取归档职位
        archived_jobs = await self.db_manager.get_jobs_by_status(JobStatus.ARCHIVED)
        self.assertEqual(len(archived_jobs), 1)
    
    async def test_job_search(self):
        """测试职位搜索"""
        await self.db_manager.initialize()
        
        # 创建测试职位
        jobs = [
            Job(id="job-py-1", title="Python开发工程师", company="公司A", url="https://example.com/py1"),
            Job(id="job-py-2", title="高级Python工程师", company="公司B", url="https://example.com/py2"),
            Job(id="job-java-1", title="Java开发工程师", company="公司C", url="https://example.com/java1")
        ]
        
        for job in jobs:
            await self.db_manager.save_job(job)
        
        # 按标题搜索
        python_jobs = await self.db_manager.search_jobs(keyword="Python")
        self.assertEqual(len(python_jobs), 2)
        
        # 按公司搜索
        company_jobs = await self.db_manager.search_jobs(company="公司A")
        self.assertEqual(len(company_jobs), 1)


class TestResumeModel(unittest.TestCase):
    """简历模型测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_resume_creation(self):
        """测试创建简历"""
        await self.db_manager.initialize()
        
        resume = Resume(
            id="test-resume-123",
            filename="张三_简历.pdf",
            file_path="/data/resumes/zhang_san.pdf",
            content="张三的简历内容",
            parsed_data={
                "name": "张三",
                "skills": ["Python", "Django"],
                "experience": "3年"
            }
        )
        
        # 保存简历
        await self.db_manager.save_resume(resume)
        
        # 获取简历
        saved_resume = await self.db_manager.get_resume("test-resume-123")
        
        self.assertIsNotNone(saved_resume)
        self.assertEqual(saved_resume.filename, "张三_简历.pdf")
        self.assertEqual(saved_resume.content, "张三的简历内容")
        self.assertIn("name", saved_resume.parsed_data)
    
    async def test_resume_content_update(self):
        """测试更新简历内容"""
        await self.db_manager.initialize()
        
        # 创建简历
        resume = Resume(
            id="test-resume-update",
            filename="test.pdf",
            content="原始内容"
        )
        await self.db_manager.save_resume(resume)
        
        # 更新内容
        resume.content = "更新后内容"
        resume.parsed_data = {"updated": True}
        
        await self.db_manager.update_resume(resume)
        
        # 验证更新
        updated_resume = await self.db_manager.get_resume("test-resume-update")
        self.assertEqual(updated_resume.content, "更新后内容")
        self.assertTrue(updated_resume.parsed_data["updated"])
    
    async def test_resume_file_handling(self):
        """测试简历文件处理"""
        await self.db_manager.initialize()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("临时简历内容")
            temp_file_path = f.name
        
        try:
            # 创建简历记录
            resume = Resume(
                id="test-resume-file",
                filename="temp_resume.txt",
                file_path=temp_file_path,
                content="临时简历内容"
            )
            
            await self.db_manager.save_resume(resume)
            
            # 验证文件路径
            saved_resume = await self.db_manager.get_resume("test-resume-file")
            self.assertEqual(saved_resume.file_path, temp_file_path)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


class TestAnalysisModel(unittest.TestCase):
    """分析模型测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_analysis_creation(self):
        """测试创建分析"""
        await self.db_manager.initialize()
        
        # 先创建依赖的职位和简历
        job = Job(id="job-for-analysis", title="测试职位", company="测试公司", url="https://example.com")
        resume = Resume(id="resume-for-analysis", filename="test.pdf", content="测试简历")
        
        await self.db_manager.save_job(job)
        await self.db_manager.save_resume(resume)
        
        # 创建分析
        analysis = Analysis(
            id="test-analysis-123",
            resume_id="resume-for-analysis",
            job_id="job-for-analysis",
            analysis_content="这是一份很好的简历，匹配度很高。",
            confidence_score=0.85,
            status=AnalysisStatus.COMPLETED
        )
        
        # 保存分析
        await self.db_manager.save_analysis(analysis)
        
        # 获取分析
        saved_analysis = await self.db_manager.get_analysis("test-analysis-123")
        
        self.assertIsNotNone(saved_analysis)
        self.assertEqual(saved_analysis.resume_id, "resume-for-analysis")
        self.assertEqual(saved_analysis.job_id, "job-for-analysis")
        self.assertEqual(saved_analysis.confidence_score, 0.85)
        self.assertEqual(saved_analysis.status, AnalysisStatus.COMPLETED)
    
    async def test_analysis_by_resume_and_job(self):
        """测试按简历和职位获取分析"""
        await self.db_manager.initialize()
        
        # 创建测试数据
        job = Job(id="job-1", title="职位1", company="公司1", url="https://example.com/1")
        resume = Resume(id="resume-1", filename="resume1.pdf", content="简历1")
        
        await self.db_manager.save_job(job)
        await self.db_manager.save_resume(resume)
        
        # 创建多个分析
        analyses = [
            Analysis(id="analysis-1", resume_id="resume-1", job_id="job-1", analysis_content="分析1"),
            Analysis(id="analysis-2", resume_id="resume-1", job_id="job-1", analysis_content="分析2"),
        ]
        
        for analysis in analyses:
            await self.db_manager.save_analysis(analysis)
        
        # 获取特定简历和职位的分析
        resume_job_analyses = await self.db_manager.get_analyses_by_resume_and_job("resume-1", "job-1")
        self.assertEqual(len(resume_job_analyses), 2)
        
        # 获取简历的所有分析
        resume_analyses = await self.db_manager.get_analyses_by_resume("resume-1")
        self.assertEqual(len(resume_analyses), 2)


class TestAIAgentModel(unittest.TestCase):
    """AI代理模型测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_ai_agent_creation(self):
        """测试创建AI代理"""
        await self.db_manager.initialize()
        
        agent = AIAgent(
            id="agent-123",
            name="简历分析专家",
            description="专门用于分析简历与职位匹配度的AI代理",
            system_prompt="你是一个专业的简历分析师...",
            model_name="deepseek-chat",
            temperature=0.7,
            max_tokens=2048,
            is_active=True
        )
        
        # 保存代理
        await self.db_manager.save_ai_agent(agent)
        
        # 获取代理
        saved_agent = await self.db_manager.get_ai_agent("agent-123")
        
        self.assertIsNotNone(saved_agent)
        self.assertEqual(saved_agent.name, "简历分析专家")
        self.assertEqual(saved_agent.model_name, "deepseek-chat")
        self.assertEqual(saved_agent.temperature, 0.7)
        self.assertTrue(saved_agent.is_active)
    
    async def test_ai_agent_list(self):
        """测试获取AI代理列表"""
        await self.db_manager.initialize()
        
        # 创建多个代理
        agents = [
            AIAgent(id="agent-1", name="代理1", is_active=True),
            AIAgent(id="agent-2", name="代理2", is_active=True),
            AIAgent(id="agent-3", name="代理3", is_active=False)
        ]
        
        for agent in agents:
            await self.db_manager.save_ai_agent(agent)
        
        # 获取所有代理
        all_agents = await self.db_manager.get_all_ai_agents()
        self.assertEqual(len(all_agents), 3)
        
        # 获取活跃代理
        active_agents = await self.db_manager.get_active_ai_agents()
        self.assertEqual(len(active_agents), 2)


class TestDatabaseIntegration(unittest.TestCase):
    """数据库集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_complete_workflow(self):
        """测试完整工作流程"""
        await self.db_manager.initialize()
        
        # 1. 创建职位
        job = Job(
            id="workflow-job",
            title="Python工程师",
            company="测试公司",
            url="https://example.com/job"
        )
        await self.db_manager.save_job(job)
        
        # 2. 创建简历
        resume = Resume(
            id="workflow-resume",
            filename="candidate.pdf",
            content="候选人简历内容"
        )
        await self.db_manager.save_resume(resume)
        
        # 3. 创建AI代理
        agent = AIAgent(
            id="workflow-agent",
            name="分析专家",
            system_prompt="分析简历匹配度"
        )
        await self.db_manager.save_ai_agent(agent)
        
        # 4. 创建分析
        analysis = Analysis(
            id="workflow-analysis",
            resume_id="workflow-resume",
            job_id="workflow-job",
            analysis_content="匹配度分析结果",
            confidence_score=0.9
        )
        await self.db_manager.save_analysis(analysis)
        
        # 5. 验证关联查询
        # 获取职位的所有分析
        job_analyses = await self.db_manager.get_analyses_by_job("workflow-job")
        self.assertEqual(len(job_analyses), 1)
        self.assertEqual(job_analyses[0].confidence_score, 0.9)
        
        # 获取简历的所有分析
        resume_analyses = await self.db_manager.get_analyses_by_resume("workflow-resume")
        self.assertEqual(len(resume_analyses), 1)
        
    async def test_data_consistency(self):
        """测试数据一致性"""
        await self.db_manager.initialize()
        
        # 创建职位和简历
        job = Job(id="consistency-job", title="测试职位", company="测试公司", url="https://example.com")
        resume = Resume(id="consistency-resume", filename="test.pdf", content="测试内容")
        
        await self.db_manager.save_job(job)
        await self.db_manager.save_resume(resume)
        
        # 创建分析
        analysis = Analysis(
            id="consistency-analysis",
            resume_id="consistency-resume",
            job_id="consistency-job",
            analysis_content="测试分析"
        )
        await self.db_manager.save_analysis(analysis)
        
        # 删除职位后，检查分析是否仍然存在（取决于外键约束设计）
        await self.db_manager.delete_job("consistency-job")
        
        # 分析应该仍然存在，但引用的职位不存在
        remaining_analysis = await self.db_manager.get_analysis("consistency-analysis")
        self.assertIsNotNone(remaining_analysis)
        
        # 职位应该已被删除
        deleted_job = await self.db_manager.get_job("consistency-job")
        self.assertIsNone(deleted_job)


def run_database_tests():
    """运行数据库测试"""
    print("🗄️ 运行数据库和模型单元测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestDatabaseManager,
        TestJobModel,
        TestResumeModel,
        TestAnalysisModel,
        TestAIAgentModel,
        TestDatabaseIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_database_tests()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")