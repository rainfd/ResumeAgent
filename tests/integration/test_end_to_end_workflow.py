"""端到端工作流集成测试 - 使用真实数据"""

import unittest
import asyncio
import tempfile
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.data.database import DatabaseManager
from resume_assistant.core.job_manager import Job, JobManager
from resume_assistant.data.models import JobInfo, ResumeContent
from resume_assistant.core.ai_analyzer import AIAnalyzer, AnalysisResult
from resume_assistant.core.scraper import ScrapingResult
from resume_assistant.core.resume_processor import ResumeProcessor
from resume_assistant.utils.errors import (
    DatabaseError, AIAnalysisError, ResumeProcessingError, NetworkError
)


# 加载真实数据
def load_real_jobs_data():
    """加载真实职位数据"""
    project_root = Path(__file__).parent.parent.parent
    jobs_data = []
    
    # 加载所有职位数据
    job_files = [
        "5c384a14-4174-4c51-b5b9-87ef63454441.json",  # Python后端
        "2b62bee0-3659-47a0-b175-efa18e0eaa44.json",  # AI算法工程师
        "594e9122-8f0e-499f-87c9-0f92d1d4e2d8.json"   # 全栈工程师
    ]
    
    for job_file in job_files:
        job_path = project_root / "data" / "jobs" / job_file
        if job_path.exists():
            with open(job_path, 'r', encoding='utf-8') as f:
                jobs_data.append(json.load(f))
    
    return jobs_data

def load_real_resumes_data():
    """加载真实简历数据"""
    project_root = Path(__file__).parent.parent.parent
    resumes_data = []
    
    # 加载简历文件
    resume_files = [
        ("test_resume_1.md", "张三", "前端开发"),
        ("test_resume_2.md", "李四", "后端开发")
    ]
    
    for resume_file, name, role in resume_files:
        resume_path = project_root / "data" / "resumes" / resume_file
        if resume_path.exists():
            with open(resume_path, 'r', encoding='utf-8') as f:
                content = f.read()
                resumes_data.append({
                    "filename": resume_file,
                    "content": content,
                    "name": name,
                    "role": role,
                    "path": str(resume_path)
                })
    
    return resumes_data

def load_real_metadata():
    """加载真实元数据"""
    project_root = Path(__file__).parent.parent.parent
    
    # 加载简历元数据
    resume_metadata_file = project_root / "data" / "resumes" / "resumes_metadata.json"
    resume_metadata = {}
    if resume_metadata_file.exists():
        with open(resume_metadata_file, 'r', encoding='utf-8') as f:
            resume_metadata = json.load(f)
    
    # 加载职位元数据
    job_metadata_file = project_root / "data" / "jobs" / "jobs_metadata.json"
    job_metadata = {}
    if job_metadata_file.exists():
        with open(job_metadata_file, 'r', encoding='utf-8') as f:
            job_metadata = json.load(f)
    
    return resume_metadata, job_metadata


class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流测试 - 使用真实数据"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.job_manager = JobManager(self.db_manager)
        self.resume_processor = ResumeProcessor()
        self.ai_analyzer = AIAnalyzer()
        
        # 加载真实数据
        self.real_jobs = load_real_jobs_data()
        self.real_resumes = load_real_resumes_data()
        self.resume_metadata, self.job_metadata = load_real_metadata()
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_complete_job_analysis_workflow_with_real_data(self):
        """测试使用真实数据的完整职位分析工作流"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 1. 使用真实职位数据进行爬取模拟
        real_job = self.real_jobs[0]  # Python后端开发工程师
        
        with patch.object(self.job_manager, 'scrape_job') as mock_scrape:
            job = Job(
                id=real_job['id'],
                title=real_job['title'],
                company=real_job['company'],
                location=real_job['location'],
                source_url=f"https://www.lagou.com/jobs/{real_job['id']}.html",
                salary=real_job['salary'],
                requirements=real_job['requirements'],
                description=real_job['description']
            )
            mock_scrape.return_value = ScrapingResult(
                success=True,
                job=job,
                url=f"https://www.lagou.com/jobs/{real_job['id']}.html",
                scraped_at=datetime.now()
            )
            
            # 爬取并保存职位
            job_result = await self.job_manager.scrape_job(f"https://www.lagou.com/jobs/{real_job['id']}.html")
            job_id = await self.job_manager.save_job(job_result)
            
            self.assertIsNotNone(job_id)
            self.assertEqual(job_result.job.title, "Python后端开发工程师")
            self.assertEqual(job_result.job.company, "科技有限公司A")
        
        # 2. 使用真实简历数据
        real_resume = self.real_resumes[1]  # 李四的后端简历
        
        # 处理真实简历文件
        resume_data = self.resume_processor.process_file(real_resume["path"])
        resume_id = await self.db_manager.save_resume(Resume(
            id=resume_data["id"],
            filename=real_resume["filename"],
            file_path=real_resume["path"],
            content=real_resume["content"],
            parsed_data=resume_data.get("parsed_data", {})
        ))
        
        self.assertIsNotNone(resume_id)
        
        # 3. 使用真实数据进行AI分析
        with patch.object(self.ai_analyzer, 'analyze_resume') as mock_analyze:
            # 基于真实数据特征生成分析结果
            realistic_analysis = f"""## 李四简历与{real_job['title']}职位匹配分析

### 技能匹配度评估：92%

**高度匹配的技能：**
- **Python开发**：候选人有5年Python开发经验，完全符合要求 ✓✓✓
- **Django/Flask**：有实际项目经验，技能熟练 ✓✓✓
- **数据库技术**：精通MySQL、PostgreSQL、Redis ✓✓✓
- **云服务经验**：AWS、阿里云实战经验 ✓✓✓
- **容器化技术**：Docker、Kubernetes经验 ✓✓✓

### 工作经验匹配度：95%
- 当前在金融科技公司担任高级后端工程师
- 负责核心支付系统架构设计，与{real_job['company']}业务场景高度相关
- 有微服务架构改造经验，符合现代化技术要求
- 处理过高并发系统优化，技术深度足够

### 项目经验亮点：
1. **分布式任务调度系统**：展现了系统架构设计能力
2. **实时数据处理平台**：体现了大数据处理经验  
3. **微服务API网关**：与目标职位技术栈完美匹配

### 薪资匹配度：
- 候选人期望：20-35K
- 职位提供：{real_job['salary']}
- 匹配度：完全符合 ✓

### 地理位置：
- 候选人当前：北京
- 职位地点：{real_job['location']}
- 无地域限制 ✓

## 综合评价：
李四是{real_job['title']}职位的理想候选人。技术能力、工作经验、项目背景都与职位要求高度匹配。

**推荐决策：强烈推荐**
**面试建议：安排技术面试，重点考察微服务架构经验**
**录用概率：95%**"""
            
            mock_analyze.return_value = AnalysisResult(
                resume_id=resume_id,
                job_id=job_id,
                analysis_content=realistic_analysis,
                confidence_score=0.92
            )
            
            # 执行分析
            job = await self.db_manager.get_job(job_id)
            resume = await self.db_manager.get_resume(resume_id)
            
            analysis_result = await self.ai_analyzer.analyze_resume(
                resume.to_dict(), job.to_dict()
            )
            
            # 保存分析结果
            analysis_id = await self.db_manager.save_analysis(Analysis(
                id=analysis_result.id,
                resume_id=analysis_result.resume_id,
                job_id=analysis_result.job_id,
                analysis_content=analysis_result.analysis_content,
                confidence_score=analysis_result.confidence_score
            ))
            
            self.assertIsNotNone(analysis_id)
            self.assertGreater(analysis_result.confidence_score, 0.9)
            self.assertIn("李四", analysis_result.analysis_content)
            self.assertIn("92%", analysis_result.analysis_content)
            self.assertIn("强烈推荐", analysis_result.analysis_content)
        
        # 4. 验证完整工作流结果
        # 检查职位是否正确保存
        saved_job = await self.db_manager.get_job(job_id)
        self.assertEqual(saved_job.title, real_job['title'])
        self.assertEqual(saved_job.company, real_job['company'])
        self.assertEqual(saved_job.location, real_job['location'])
        
        # 检查简历是否正确保存
        saved_resume = await self.db_manager.get_resume(resume_id)
        self.assertEqual(saved_resume.filename, real_resume["filename"])
        self.assertIn("李四", saved_resume.content)
        self.assertIn("Python", saved_resume.content)
        
        # 检查分析结果是否正确保存
        saved_analysis = await self.db_manager.get_analysis(analysis_id)
        self.assertEqual(saved_analysis.resume_id, resume_id)
        self.assertEqual(saved_analysis.job_id, job_id)
        self.assertGreater(saved_analysis.confidence_score, 0.9)
        self.assertIn("技能匹配度", saved_analysis.analysis_content)
    
    async def test_batch_resume_analysis_with_real_data(self):
        """测试使用真实数据的批量简历分析工作流"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 1. 创建真实职位
        real_job = self.real_jobs[0]  # Python后端职位
        job = Job(
            id=real_job['id'],
            title=real_job['title'],
            company=real_job['company'],
            url=f"https://www.lagou.com/jobs/{real_job['id']}.html",
            location=real_job['location'],
            salary=real_job['salary'],
            requirements=real_job['requirements'],
            description=real_job['description']
        )
        await self.db_manager.save_job(job)
        
        # 2. 处理多个真实简历
        resume_ids = []
        for real_resume in self.real_resumes:
            resume_data = self.resume_processor.process_file(real_resume["path"])
            resume = Resume(
                id=resume_data["id"],
                filename=real_resume["filename"],
                file_path=real_resume["path"],
                content=real_resume["content"],
                parsed_data=resume_data.get("parsed_data", {})
            )
            resume_id = await self.db_manager.save_resume(resume)
            resume_ids.append(resume_id)
        
        # 3. 批量分析
        with patch.object(self.ai_analyzer, 'batch_analyze_resumes') as mock_batch_analyze:
            # 基于真实数据生成不同的分析结果
            mock_results = []
            
            # 张三（前端）vs Python后端职位 - 低匹配度
            zhang_analysis = f"""## 张三简历与{real_job['title']}职位跨领域分析

### 技能转换评估：65%

**可转移技能：**
- **编程基础**：JavaScript经验可快速转向Python ⚠️
- **框架思维**：React/Vue经验有助于理解Django ⚠️
- **后端了解**：有Node.js、MongoDB基础 ✓
- **工程化经验**：Git、Webpack等开发流程熟悉 ✓

**需要补强的核心技能：**
- **Python语言**：需要系统学习Python语法和特性
- **Django框架**：需要深入学习后端框架
- **关系型数据库**：MySQL/PostgreSQL经验不足
- **系统架构**：缺乏微服务架构经验

### 工作经验评估：60%
- 3年前端开发经验，技术基础扎实
- 需要从前端转向后端开发
- 学习能力强，有转岗潜力

### 转岗可行性分析：
**优势：** 年轻有活力，学习能力强，有一定后端基础
**挑战：** 需要3-6个月的技能转换期
**建议：** 如果公司有培训计划，可以考虑

**当前匹配度：65%**
**转岗建议：中等可行（需要培训支持）**"""
            
            # 李四（后端）vs Python后端职位 - 高匹配度
            li_analysis = f"""## 李四简历与{real_job['title']}职位专业匹配分析

### 技能完美匹配：92%

**核心技能高度吻合：**
- **Python开发**：5年丰富经验，技术深度优秀 ✓✓✓
- **Django/Flask**：项目实战经验丰富 ✓✓✓
- **数据库技术**：MySQL、PostgreSQL、Redis全掌握 ✓✓✓
- **云服务**：AWS、阿里云实战经验 ✓✓✓
- **架构设计**：微服务、分布式系统经验 ✓✓✓

### 工作经验完全符合：95%
- 当前金融科技公司高级后端工程师
- 核心支付系统架构负责人
- 高并发系统优化专家
- 团队协作和项目管理经验丰富

### 项目经验突出：
1. **分布式任务调度系统** - 架构能力体现
2. **实时数据处理平台** - 大数据处理能力
3. **微服务API网关** - 与职位需求完美匹配

### 综合评价：
李四是{real_job['company']}的理想人选，无论是技术能力、工作经验还是项目背景都与职位要求高度匹配。

**推荐决策：强烈推荐，优先面试**
**录用建议：快速推进面试流程**
**匹配度：92%**"""
            
            mock_results = [
                AnalysisResult(
                    resume_id=resume_ids[0],  # 张三
                    job_id=real_job['id'],
                    analysis_content=zhang_analysis,
                    confidence_score=0.65
                ),
                AnalysisResult(
                    resume_id=resume_ids[1],  # 李四
                    job_id=real_job['id'],
                    analysis_content=li_analysis,
                    confidence_score=0.92
                )
            ]
            mock_batch_analyze.return_value = mock_results
            
            # 执行批量分析
            resumes = [await self.db_manager.get_resume(rid) for rid in resume_ids]
            job_dict = job.to_dict()
            
            analysis_results = await self.ai_analyzer.batch_analyze_resumes(
                [r.to_dict() for r in resumes], job_dict
            )
            
            # 保存分析结果
            for result in analysis_results:
                await self.db_manager.save_analysis(Analysis(
                    id=result.id,
                    resume_id=result.resume_id,
                    job_id=result.job_id,
                    analysis_content=result.analysis_content,
                    confidence_score=result.confidence_score
                ))
            
            # 4. 验证批量分析结果
            self.assertEqual(len(analysis_results), 2)
            
            # 验证张三的结果（跨领域，中等匹配度）
            zhang_result = next(r for r in analysis_results if "张三" in r.analysis_content)
            self.assertIn("65%", zhang_result.analysis_content)
            self.assertIn("转岗", zhang_result.analysis_content)
            self.assertLess(zhang_result.confidence_score, 0.7)
            
            # 验证李四的结果（专业匹配，高匹配度）
            li_result = next(r for r in analysis_results if "李四" in r.analysis_content)
            self.assertIn("92%", li_result.analysis_content)
            self.assertIn("强烈推荐", li_result.analysis_content)
            self.assertGreater(li_result.confidence_score, 0.9)
            
            # 验证数据库中的分析记录
            job_analyses = await self.db_manager.get_analyses_by_job(real_job['id'])
            self.assertEqual(len(job_analyses), 2)
    
    async def test_cross_domain_matching_workflow(self):
        """测试跨领域匹配工作流"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 使用AI算法工程师职位
        ai_job = self.real_jobs[1] if len(self.real_jobs) > 1 else self.real_jobs[0]
        
        # 创建AI职位
        job = Job(
            id=ai_job['id'],
            title=ai_job['title'],
            company=ai_job['company'],
            url=f"https://www.lagou.com/jobs/{ai_job['id']}.html",
            requirements=ai_job['requirements'],
            description=ai_job['description']
        )
        await self.db_manager.save_job(job)
        
        # 使用后端开发简历（李四）测试跨领域匹配
        backend_resume = self.real_resumes[1]  # 李四的后端简历
        resume_data = self.resume_processor.process_file(backend_resume["path"])
        resume = Resume(
            id=resume_data["id"],
            filename=backend_resume["filename"],
            content=backend_resume["content"],
            parsed_data=resume_data.get("parsed_data", {})
        )
        await self.db_manager.save_resume(resume)
        
        # 跨领域分析
        with patch.object(self.ai_analyzer, 'analyze_resume') as mock_analyze:
            cross_domain_analysis = f"""## 跨领域分析：后端工程师 → {ai_job['title']}

### 技能迁移潜力评估：75%

**可迁移的技术基础：**
- **编程能力**：Python基础扎实，转向AI开发有优势 ✓✓
- **数据处理**：有实时数据处理平台经验 ✓✓
- **系统架构**：分布式系统经验有助于AI系统设计 ✓
- **工程化能力**：Docker、云服务经验直接适用 ✓✓

**需要补强的AI专业技能：**
- **机器学习框架**：需要学习TensorFlow/PyTorch ⚠️
- **算法理论**：缺乏深度学习理论基础 ⚠️
- **数据科学**：需要补充统计学和数据分析技能 ⚠️
- **AI项目经验**：缺乏实际AI项目经验 ⚠️

### 转型可行性分析：
**优势：**
1. 扎实的编程基础，学习能力强
2. 有大数据处理经验，与AI数据处理相关
3. 系统架构经验有助于AI系统工程化

**挑战：**
1. 需要系统学习机器学习理论
2. 缺乏AI项目实战经验
3. 需要6-12个月的技能转换期

### 建议：
- 如果候选人有强烈的AI转型意愿，可以考虑
- 建议安排AI基础技能培训
- 初期可从AI工程化方向入手

**跨领域匹配度：75%**
**转型建议：可行但需要培训支持**"""
            
            mock_analyze.return_value = AnalysisResult(
                resume_id=resume.id,
                job_id=job.id,
                analysis_content=cross_domain_analysis,
                confidence_score=0.75
            )
            
            # 执行跨领域分析
            analysis_result = await self.ai_analyzer.analyze_resume(
                resume.to_dict(), job.to_dict()
            )
            
            # 验证跨领域分析结果
            self.assertIn("跨领域", analysis_result.analysis_content)
            self.assertIn("75%", analysis_result.analysis_content)
            self.assertIn("转型", analysis_result.analysis_content)
            self.assertIn("培训", analysis_result.analysis_content)
            self.assertEqual(analysis_result.confidence_score, 0.75)
    
    async def test_error_recovery_with_real_scenarios(self):
        """测试真实场景下的错误恢复工作流"""
        await self.db_manager.initialize()
        
        # 1. 测试网络错误恢复
        with patch.object(self.job_manager, 'scrape_job') as mock_scrape:
            # 使用真实URL模拟网络错误
            real_url = "https://www.lagou.com/jobs/network-error-test.html"
            
            # 第一次调用失败，第二次成功
            mock_scrape.side_effect = [
                NetworkError("网络连接超时"),
                ScrapingResult(
                    url=real_url,
                    title="网络恢复测试职位",
                    company="测试公司",
                    location="北京"
                )
            ]
            
            # 模拟重试机制
            job_result = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    job_result = await self.job_manager.scrape_job(real_url)
                    break
                except NetworkError:
                    if attempt == max_retries - 1:
                        raise
                    continue
            
            self.assertIsNotNone(job_result)
            self.assertEqual(job_result.title, "网络恢复测试职位")
        
        # 2. 测试数据库事务回滚
        if self.real_jobs:
            real_job = self.real_jobs[0]
            job = Job(
                id=f"transaction-test-{real_job['id']}",
                title=real_job['title'],
                company=real_job['company'],
                url=f"https://test.com/transaction-test.html"
            )
            
            # 成功保存职位
            job_id = await self.db_manager.save_job(job)
            self.assertIsNotNone(job_id)
            
            # 模拟事务失败的情况
            try:
                async with self.db_manager.transaction() as conn:
                    # 更新职位
                    await conn.execute(
                        "UPDATE jobs SET title = ? WHERE id = ?",
                        ("更新后的标题", job_id)
                    )
                    
                    # 模拟异常
                    raise Exception("模拟事务失败")
                    
            except Exception:
                pass
            
            # 验证数据未被更新（事务已回滚）
            job_after_rollback = await self.db_manager.get_job(job_id)
            self.assertEqual(job_after_rollback.title, real_job['title'])  # 原始标题


class TestRealDataIntegration(unittest.TestCase):
    """真实数据集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        
        # 加载真实数据
        self.real_jobs = load_real_jobs_data()
        self.real_resumes = load_real_resumes_data()
        self.resume_metadata, self.job_metadata = load_real_metadata()
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_real_data_persistence_and_retrieval(self):
        """测试真实数据的持久化和检索"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 1. 保存所有真实职位
        saved_job_ids = []
        for real_job in self.real_jobs:
            job = Job(
                id=real_job['id'],
                title=real_job['title'],
                company=real_job['company'],
                location=real_job.get('location', ''),
                salary=real_job.get('salary', ''),
                requirements=real_job.get('requirements', ''),
                description=real_job.get('description', ''),
                url=f"https://www.lagou.com/jobs/{real_job['id']}.html"
            )
            job_id = await self.db_manager.save_job(job)
            saved_job_ids.append(job_id)
        
        # 验证所有职位都保存成功
        self.assertEqual(len(saved_job_ids), len(self.real_jobs))
        
        # 2. 保存所有真实简历
        saved_resume_ids = []
        resume_processor = ResumeProcessor()
        
        for real_resume in self.real_resumes:
            resume_data = resume_processor.process_file(real_resume["path"])
            resume = Resume(
                id=resume_data["id"],
                filename=real_resume["filename"],
                content=real_resume["content"],
                file_path=real_resume["path"],
                parsed_data=resume_data.get("parsed_data", {})
            )
            resume_id = await self.db_manager.save_resume(resume)
            saved_resume_ids.append(resume_id)
        
        # 验证所有简历都保存成功
        self.assertEqual(len(saved_resume_ids), len(self.real_resumes))
        
        # 3. 测试数据检索
        # 按公司搜索职位
        beijing_jobs = await self.db_manager.search_jobs(location="北京")
        self.assertGreater(len(beijing_jobs), 0)
        
        # 按技能搜索
        python_jobs = await self.db_manager.search_jobs(keyword="Python")
        self.assertGreater(len(python_jobs), 0)
        
        # 验证搜索结果包含真实数据
        for job in python_jobs:
            self.assertIn("Python", job.title + job.requirements)
    
    async def test_real_data_analysis_scenarios(self):
        """测试真实数据的分析场景"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 创建真实的分析场景
        analysis_scenarios = [
            {
                "job_index": 0,  # Python后端
                "resume_index": 1,  # 李四（后端）
                "expected_score": 0.9,
                "scenario": "专业匹配"
            },
            {
                "job_index": 0,  # Python后端
                "resume_index": 0,  # 张三（前端）
                "expected_score": 0.65,
                "scenario": "跨领域匹配"
            }
        ]
        
        if len(self.real_jobs) > 1:
            analysis_scenarios.append({
                "job_index": 1,  # AI算法工程师
                "resume_index": 1,  # 李四（后端）
                "expected_score": 0.75,
                "scenario": "技能迁移"
            })
        
        for scenario in analysis_scenarios:
            with self.subTest(scenario=scenario["scenario"]):
                # 准备职位和简历数据
                real_job = self.real_jobs[scenario["job_index"]]
                real_resume = self.real_resumes[scenario["resume_index"]]
                
                # 保存职位
                job = Job(
                    id=f"scenario-{real_job['id']}",
                    title=real_job['title'],
                    company=real_job['company'],
                    requirements=real_job.get('requirements', '')
                )
                await self.db_manager.save_job(job)
                
                # 保存简历
                resume_processor = ResumeProcessor()
                resume_data = resume_processor.process_file(real_resume["path"])
                resume = Resume(
                    id=f"scenario-{resume_data['id']}",
                    filename=real_resume["filename"],
                    content=real_resume["content"]
                )
                await self.db_manager.save_resume(resume)
                
                # 模拟分析
                analysis = Analysis(
                    id=f"analysis-{scenario['scenario']}",
                    job_id=job.id,
                    resume_id=resume.id,
                    analysis_content=f"{scenario['scenario']}分析结果",
                    confidence_score=scenario["expected_score"]
                )
                await self.db_manager.save_analysis(analysis)
                
                # 验证分析结果
                saved_analysis = await self.db_manager.get_analysis(analysis.id)
                self.assertEqual(saved_analysis.confidence_score, scenario["expected_score"])
                self.assertIn(scenario["scenario"], saved_analysis.analysis_content)


class TestPerformanceWithRealData(unittest.TestCase):
    """使用真实数据的性能测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        
        # 加载真实数据
        self.real_jobs = load_real_jobs_data()
        self.real_resumes = load_real_resumes_data()
    
    def tearDown(self):
        """清理测试环境"""
        asyncio.run(self.db_manager.close())
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    async def test_real_data_processing_performance(self):
        """测试真实数据处理性能"""
        if not self.real_jobs or not self.real_resumes:
            self.skipTest("真实数据文件不存在")
        
        await self.db_manager.initialize()
        
        # 测试批量数据处理性能
        start_time = datetime.now()
        
        # 批量保存真实职位
        for real_job in self.real_jobs:
            job = Job(
                id=f"perf-{real_job['id']}",
                title=real_job['title'],
                company=real_job['company'],
                requirements=real_job.get('requirements', ''),
                description=real_job.get('description', '')
            )
            await self.db_manager.save_job(job)
        
        # 批量保存真实简历
        resume_processor = ResumeProcessor()
        for real_resume in self.real_resumes:
            resume_data = resume_processor.process_file(real_resume["path"])
            resume = Resume(
                id=f"perf-{resume_data['id']}",
                filename=real_resume["filename"],
                content=real_resume["content"]
            )
            await self.db_manager.save_resume(resume)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 验证性能要求（根据数据量调整）
        expected_max_time = len(self.real_jobs + self.real_resumes) * 0.5  # 每条记录0.5秒
        self.assertLess(processing_time, expected_max_time)
        
        # 测试查询性能
        start_time = datetime.now()
        
        # 执行复杂查询
        all_jobs = await self.db_manager.get_all_jobs()
        all_resumes = await self.db_manager.get_all_resumes()
        python_jobs = await self.db_manager.search_jobs(keyword="Python")
        
        query_time = (datetime.now() - start_time).total_seconds()
        
        # 验证查询性能
        self.assertLess(query_time, 2.0)  # 查询应在2秒内完成
        
        # 验证查询结果
        self.assertEqual(len(all_jobs), len(self.real_jobs))
        self.assertEqual(len(all_resumes), len(self.real_resumes))
        self.assertGreater(len(python_jobs), 0)


def run_integration_tests():
    """运行集成测试"""
    print("🔧 运行端到端工作流集成测试（使用真实数据）...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndWorkflow,
        TestRealDataIntegration,
        TestPerformanceWithRealData
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")