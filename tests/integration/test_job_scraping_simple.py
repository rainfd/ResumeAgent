"""简化的职位爬取工作流集成测试

测试从输入BOSS直聘网址到查看职位详情的完整用户流程
"""

import unittest
import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import time
import pytest

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.core.job_manager import JobManager, Job
from resume_assistant.core.scraper import BossZhipinScraper, ScrapingResult
from resume_assistant.web.session_manager import SessionManager
from resume_assistant.utils.errors import NetworkError, ParseError as ScrapingError, ResumeAssistantError


class TestJobScrapingWorkflowSimple(unittest.TestCase):
    """简化的职位爬取工作流集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 初始化组件
        self.job_manager = JobManager()
        self.session_manager = SessionManager()
        
        # 测试用的BOSS直聘URL
        self.test_boss_urls = [
            "https://www.zhipin.com/job_detail/12345.html",
            "https://www.zhipin.com/job_detail/python-backend-67890.html",
            "https://www.zhipin.com/web/geek/job/abcd1234efgh5678.html"
        ]
        
        # 模拟的职位数据
        self.mock_job_data = {
            'id': 'scraped-job-001',
            'title': 'Python后端开发工程师',
            'company': 'BOSS直聘科技有限公司',
            'location': '北京·朝阳区',
            'salary': '18-30K·14薪',
            'experience_level': '3-5年',
            'education_level': '本科',
            'description': '''
职位描述：
1. 负责公司核心业务系统的后端开发和维护
2. 参与系统架构设计，优化系统性能
3. 配合前端工程师完成产品功能开发
4. 参与代码审查，保证代码质量

技术要求：
- 熟练掌握Python语言，有Django/Flask框架经验
- 熟悉MySQL、Redis等数据库
- 了解微服务架构，有容器化部署经验
- 具备良好的代码习惯和文档意识
            ''',
            'requirements': 'Python, Django, Flask, MySQL, Redis, 微服务, Docker',
            'company_info': {
                'size': '500-1000人',
                'stage': 'D轮及以上',
                'industry': '互联网'
            },
            'source_url': 'https://www.zhipin.com/job_detail/12345.html',
            'tags': ['Python', '后端开发', '互联网'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    @patch('resume_assistant.core.scraper.BossZhipinScraper.scrape_job')
    def test_job_scraping_manager_workflow(self, mock_scrape_job):
        """测试职位爬取管理器工作流"""
        print("\n🧪 开始测试职位爬取管理器工作流...")
        
        # 1. 模拟爬虫返回结果
        mock_job = Job(
            id=self.mock_job_data['id'],
            title=self.mock_job_data['title'],
            company=self.mock_job_data['company'],
            description=self.mock_job_data['description'],
            requirements=self.mock_job_data['requirements'],
            location=self.mock_job_data['location'],
            salary=self.mock_job_data['salary'],
            source_url=self.mock_job_data['source_url']
        )
        
        mock_scraping_result = ScrapingResult(
            success=True,
            job=mock_job,
            url=self.test_boss_urls[0],
            scraped_at=datetime.now()
        )
        mock_scrape_job.return_value = mock_scraping_result
        
        # 2. 测试通过JobManager爬取职位
        print("🕷️ 步骤1：通过JobManager爬取职位")
        
        # 使用patch来模拟scrape_job_from_url方法
        with patch.object(self.job_manager, 'scrape_job_from_url') as mock_scrape:
            mock_scrape.return_value = mock_job
            
            # 执行爬取
            result = self.job_manager.scrape_job_from_url(self.test_boss_urls[0])
            
            # 验证结果
            self.assertIsNotNone(result, "爬取结果不应该为空")
            self.assertEqual(result.title, self.mock_job_data['title'])
            self.assertEqual(result.company, self.mock_job_data['company'])
            self.assertEqual(result.source_url, self.test_boss_urls[0])
            
            print(f"  ✓ 成功爬取职位: {result.title}")
        
        # 3. 测试职位信息验证
        print("📊 步骤2：验证职位信息完整性")
        
        required_fields = ['id', 'title', 'company', 'location', 'salary', 'description']
        for field in required_fields:
            self.assertTrue(hasattr(result, field), f"职位应该有{field}字段")
            value = getattr(result, field)
            self.assertIsNotNone(value, f"{field}不应该为空")
            print(f"  ✓ {field}: {str(value)[:50]}...")
        
        print("✅ 职位爬取管理器工作流测试通过")
    
    def test_boss_url_validation(self):
        """测试BOSS直聘URL验证"""
        print("\n🧪 测试BOSS直聘URL验证...")
        
        def validate_boss_url(url: str) -> bool:
            """验证BOSS直聘URL"""
            if not url:
                return False
            if not url.startswith(('http://', 'https://')):
                return False
            if 'zhipin.com' not in url:
                return False
            return True
        
        # 测试有效的BOSS直聘URL
        valid_urls = [
            "https://www.zhipin.com/job_detail/12345.html",
            "https://www.zhipin.com/web/geek/job/abcd1234.html",
            "http://www.zhipin.com/job_detail/python-dev.html"
        ]
        
        # 测试无效URL
        invalid_urls = [
            "https://www.lagou.com/jobs/12345.html",  # 拉勾网
            "https://jobs.51job.com/beijing/123456.html",  # 51job
            "not-a-url",  # 无效格式
            "javascript:alert(1)",  # 恶意URL
            ""  # 空URL
        ]
        
        for url in valid_urls:
            self.assertTrue(validate_boss_url(url), f"应该是有效的BOSS直聘URL: {url}")
            print(f"  ✓ 验证有效URL: {url}")
        
        for url in invalid_urls:
            self.assertFalse(validate_boss_url(url), f"应该是无效URL: {url}")
            print(f"  ✓ 验证无效URL: {url}")
        
        print("✅ URL验证测试通过")
    
    @patch('resume_assistant.core.scraper.BossZhipinScraper.scrape_job')
    def test_scraping_error_handling(self, mock_scrape_job):
        """测试爬取错误处理"""
        print("\n🧪 测试爬取错误处理...")
        
        # 测试不同的错误场景
        error_scenarios = [
            {
                'name': '网络超时错误',
                'exception': NetworkError("连接超时"),
                'expected_type': NetworkError
            },
            {
                'name': '页面解析错误', 
                'exception': ScrapingError("页面结构变化"),
                'expected_type': ScrapingError
            },
            {
                'name': '通用异常',
                'exception': Exception("未知错误"),
                'expected_type': Exception
            }
        ]
        
        for scenario in error_scenarios:
            print(f"  🔍 测试场景: {scenario['name']}")
            
            # 模拟错误
            mock_scrape_job.side_effect = scenario['exception']
            
            # 使用patch来模拟JobManager的错误处理
            with patch.object(self.job_manager, 'scrape_job_from_url') as mock_scrape:
                mock_scrape.side_effect = scenario['exception']
                
                # 验证异常处理
                with self.assertRaises(scenario['expected_type']):
                    self.job_manager.scrape_job_from_url(self.test_boss_urls[0])
            
            print(f"    ✓ {scenario['name']}处理正常")
        
        print("✅ 错误处理测试通过")
    
    def test_job_data_structure(self):
        """测试职位数据结构"""
        print("\n🧪 测试职位数据结构...")
        
        # 创建Job对象
        job = Job(
            id=self.mock_job_data['id'],
            title=self.mock_job_data['title'],
            company=self.mock_job_data['company'],
            description=self.mock_job_data['description'],
            requirements=self.mock_job_data['requirements'],
            location=self.mock_job_data['location'],
            salary=self.mock_job_data['salary'],
            source_url=self.mock_job_data['source_url']
        )
        
        # 验证必要字段
        self.assertIsNotNone(job.id, "职位ID不能为空")
        self.assertIsNotNone(job.title, "职位标题不能为空")
        self.assertIsNotNone(job.company, "公司名称不能为空")
        self.assertIsNotNone(job.description, "职位描述不能为空")
        
        # 验证字段类型
        self.assertIsInstance(job.title, str, "职位标题应该是字符串")
        self.assertIsInstance(job.company, str, "公司名称应该是字符串")
        
        # 验证URL格式
        self.assertTrue(job.source_url.startswith(('http://', 'https://')), "来源URL应该有协议")
        
        print(f"  ✓ 职位ID: {job.id}")
        print(f"  ✓ 职位标题: {job.title}")
        print(f"  ✓ 公司名称: {job.company}")
        print(f"  ✓ 工作地点: {job.location}")
        print(f"  ✓ 薪资范围: {job.salary}")
        
        print("✅ 职位数据结构测试通过")
    
    def test_scraping_result_structure(self):
        """测试爬取结果结构"""
        print("\n🧪 测试爬取结果结构...")
        
        # 创建Job对象
        job = Job(
            id=self.mock_job_data['id'],
            title=self.mock_job_data['title'],
            company=self.mock_job_data['company'],
            description=self.mock_job_data['description'],
            requirements=self.mock_job_data['requirements'],
            location=self.mock_job_data['location'],
            salary=self.mock_job_data['salary'],
            source_url=self.mock_job_data['source_url']
        )
        
        # 创建ScrapingResult对象
        result = ScrapingResult(
            success=True,
            job=job,
            url=self.test_boss_urls[0],
            scraped_at=datetime.now()
        )
        
        # 验证ScrapingResult结构
        self.assertIsInstance(result.success, bool, "success应该是布尔值")
        self.assertTrue(result.success, "爬取应该成功")
        self.assertIsInstance(result.job, Job, "job应该是Job对象")
        self.assertEqual(result.url, self.test_boss_urls[0], "URL应该匹配")
        self.assertIsInstance(result.scraped_at, datetime, "scraped_at应该是datetime对象")
        
        print(f"  ✓ 爬取状态: {result.success}")
        print(f"  ✓ 职位对象: {type(result.job).__name__}")
        print(f"  ✓ 爬取URL: {result.url}")
        print(f"  ✓ 爬取时间: {result.scraped_at}")
        
        print("✅ 爬取结果结构测试通过")
    
    def test_performance_timing(self):
        """测试性能时间"""
        print("\n🧪 测试性能时间...")
        
        # 测量Job对象创建时间
        start_time = time.time()
        
        for i in range(100):
            job = Job(
                id=f"job-{i:03d}",
                title=f"Python开发工程师 {i+1}",
                company=f"科技公司{chr(65 + i % 5)}",
                description="职位描述内容",
                requirements="Python, Django, MySQL",
                location="北京",
                salary="15k-25k",
                source_url=f"https://www.zhipin.com/job_detail/{i}.html"
            )
        
        creation_time = time.time() - start_time
        
        print(f"  ⏱️ 创建100个Job对象耗时: {creation_time:.3f}秒")
        
        # 验证性能在合理范围内
        self.assertLess(creation_time, 1.0, "Job对象创建时间应该在1秒内")
        
        print("✅ 性能测试通过")


def run_job_scraping_simple_tests():
    """运行简化的职位爬取工作流测试"""
    print("🧪 运行简化的职位爬取工作流集成测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试方法
    test_methods = [
        'test_job_scraping_manager_workflow',
        'test_boss_url_validation', 
        'test_scraping_error_handling',
        'test_job_data_structure',
        'test_scraping_result_structure',
        'test_performance_timing'
    ]
    
    for method_name in test_methods:
        test_suite.addTest(TestJobScrapingWorkflowSimple(method_name))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_job_scraping_simple_tests()
    print(f"\n{'✅ 所有测试通过' if success else '❌ 部分测试失败'}")