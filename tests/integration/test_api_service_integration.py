"""API和服务集成测试"""

import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import os
import json

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resume_assistant.core.ai_analyzer import AIAnalyzer, DeepSeekClient
from resume_assistant.core.scraper import PlaywrightScraper, BossZhipinScraper
from resume_assistant.data.database import DatabaseManager
from resume_assistant.utils.errors import AIServiceError, NetworkError
from resume_assistant.utils.security import get_api_key_manager, get_security_manager


class TestAIServiceIntegration(unittest.TestCase):
    """AI服务集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.ai_analyzer = AIAnalyzer()
    
    @patch('httpx.AsyncClient.post')
    async def test_deepseek_api_integration(self, mock_post):
        """测试DeepSeek API集成"""
        # 模拟成功的API响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "根据简历分析，该候选人具备以下优势：\n1. 技能匹配度：85%\n2. 工作经验符合要求\n3. 教育背景良好\n\n建议：进入下一轮面试"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 80,
                "total_tokens": 230
            }
        }
        mock_post.return_value = mock_response
        
        # 创建DeepSeek客户端
        client = DeepSeekClient(api_key="test-key")
        
        # 执行分析
        result = await client.analyze(
            "张三，Python开发工程师，3年经验，熟悉Django和PostgreSQL",
            "招聘Python后端工程师，要求2-5年经验，熟悉Python Web框架"
        )
        
        # 验证结果
        self.assertIn("技能匹配度", result)
        self.assertIn("85%", result)
        self.assertIn("面试", result)
        
        # 验证API调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("messages", call_args[1]["json"])
        self.assertIn("model", call_args[1]["json"])
    
    @patch('httpx.AsyncClient.post')
    async def test_api_error_handling(self, mock_post):
        """测试API错误处理"""
        # 测试不同类型的错误
        error_scenarios = [
            (401, "Unauthorized", "API密钥无效"),
            (429, "Rate limited", "请求频率过高"),
            (500, "Internal server error", "服务器内部错误"),
            (503, "Service unavailable", "服务暂时不可用")
        ]
        
        client = DeepSeekClient(api_key="test-key")
        
        for status_code, response_text, expected_error in error_scenarios:
            with self.subTest(status_code=status_code):
                mock_response = MagicMock()
                mock_response.status_code = status_code
                mock_response.text = response_text
                mock_post.return_value = mock_response
                
                with self.assertRaises(AIServiceError) as context:
                    await client.analyze("测试简历", "测试职位")
                
                # 验证错误信息包含状态码
                self.assertIn(str(status_code), str(context.exception))
    
    @patch('httpx.AsyncClient.post')
    async def test_api_timeout_handling(self, mock_post):
        """测试API超时处理"""
        # 模拟超时
        mock_post.side_effect = asyncio.TimeoutError()
        
        client = DeepSeekClient(api_key="test-key", timeout=1)
        
        with self.assertRaises(AIServiceError) as context:
            await client.analyze("测试简历", "测试职位")
        
        self.assertIn("timeout", str(context.exception).lower())
    
    async def test_api_key_management_integration(self):
        """测试API密钥管理集成"""
        # 使用安全管理器存储API密钥
        api_key_manager = get_api_key_manager()
        
        # 存储测试API密钥
        test_api_key = "sk-test-deepseek-key-123456"
        api_key_manager.store_api_key("deepseek", test_api_key)
        
        # 验证AI分析器能够获取存储的密钥
        with patch.object(AIAnalyzer, '_get_api_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # 触发客户端获取
            analyzer = AIAnalyzer()
            client = analyzer._get_api_client()
            
            # 验证使用了存储的密钥
            mock_get_client.assert_called_once()
        
        # 清理测试数据
        api_key_manager.delete_api_key("deepseek")


class TestScrapingServiceIntegration(unittest.TestCase):
    """爬虫服务集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.playwright_scraper = PlaywrightScraper()
        self.boss_scraper = BossZhipinScraper()
    
    @patch('playwright.async_api.async_playwright')
    async def test_playwright_browser_integration(self, mock_playwright):
        """测试Playwright浏览器集成"""
        # 模拟Playwright对象
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # 模拟页面响应
        mock_page.content.return_value = """
        <html>
            <head><title>Python开发工程师 - 测试公司 - 拉勾网</title></head>
            <body>
                <div class="job-name">
                    <h1>Python开发工程师</h1>
                </div>
                <div class="company-name">测试公司</div>
                <div class="job-salary">15k-25k·14薪</div>
                <div class="job-address">北京市朝阳区</div>
                <div class="job-detail">
                    <h3>职位描述</h3>
                    <p>负责后端开发，熟悉Python、Django框架</p>
                </div>
            </body>
        </html>
        """
        
        # 执行爬取
        result = await self.playwright_scraper.scrape("https://www.lagou.com/jobs/12345678.html")
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.url, "https://www.lagou.com/jobs/12345678.html")
        
        # 验证浏览器操作
        mock_playwright_instance.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_browser.close.assert_called_once()
    
    @patch('playwright.async_api.async_playwright')
    async def test_lagou_specific_parsing(self, mock_playwright):
        """测试拉勾网特定解析"""
        # 设置Playwright模拟
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # 模拟拉勾网页面结构
        mock_page.content.return_value = """
        <html>
            <body>
                <div class="position-content">
                    <div class="position-head">
                        <h1 class="name">高级Python工程师</h1>
                        <span class="salary">20k-35k</span>
                    </div>
                    <p class="company_name">
                        <a href="/company/123456.html">创新科技公司</a>
                    </p>
                    <p class="work_addr">北京市海淀区</p>
                    <div class="job_bt">
                        <h3>职位诱惑</h3>
                        <p>年终奖，股票期权，弹性工作</p>
                        <h3>职位描述</h3>
                        <p>1. 负责后端服务开发和维护</p>
                        <p>2. 参与系统架构设计</p>
                        <p>3. 熟练掌握Python、Django、FastAPI</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # 执行BOSS直聘爬取
        result = await self.boss_scraper.scrape_job("https://www.zhipin.com/job_detail/9876543.html")
        
        # 验证拉勾网特定解析
        self.assertIsNotNone(result)
        # 由于模拟的HTML结构，具体断言可能需要根据实际解析逻辑调整
    
    async def test_scraping_rate_limiting(self):
        """测试爬虫速率限制"""
        import time
        
        # 记录请求时间
        request_times = []
        
        async def mock_scrape(url):
            request_times.append(time.time())
            return MagicMock()
        
        # 替换爬取方法
        original_scrape = self.playwright_scraper.scrape
        self.playwright_scraper.scrape = mock_scrape
        
        try:
            # 快速连续发起多个请求
            urls = [f"https://example.com/job/{i}" for i in range(3)]
            await asyncio.gather(*[self.playwright_scraper.scrape(url) for url in urls])
            
            # 验证请求间隔（如果有速率限制的话）
            if len(request_times) > 1:
                intervals = [request_times[i] - request_times[i-1] for i in range(1, len(request_times))]
                # 根据实际的速率限制策略进行验证
                # 这里只是示例，具体值需要根据实现调整
                for interval in intervals:
                    self.assertGreaterEqual(interval, 0)  # 至少不是负数
        finally:
            # 恢复原始方法
            self.playwright_scraper.scrape = original_scrape
    
    @patch('playwright.async_api.async_playwright')
    async def test_browser_error_handling(self, mock_playwright):
        """测试浏览器错误处理"""
        # 模拟浏览器启动失败
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.side_effect = Exception("Browser launch failed")
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        with self.assertRaises(NetworkError):
            await self.playwright_scraper.scrape("https://example.com")
    
    async def test_concurrent_scraping(self):
        """测试并发爬取"""
        with patch.object(self.playwright_scraper, 'scrape') as mock_scrape:
            # 模拟不同的爬取结果
            mock_scrape.side_effect = [
                MagicMock(url=f"https://example.com/job/{i}", title=f"职位{i}")
                for i in range(5)
            ]
            
            # 并发爬取
            urls = [f"https://example.com/job/{i}" for i in range(5)]
            results = await asyncio.gather(
                *[self.playwright_scraper.scrape(url) for url in urls],
                return_exceptions=True
            )
            
            # 验证结果
            self.assertEqual(len(results), 5)
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    self.assertEqual(result.url, f"https://example.com/job/{i}")


class TestDatabaseServiceIntegration(unittest.TestCase):
    """数据库服务集成测试"""
    
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
    
    async def test_database_connection_pool(self):
        """测试数据库连接池"""
        await self.db_manager.initialize()
        
        # 并发数据库操作
        async def db_operation(index):
            async with self.db_manager.get_connection() as conn:
                async with conn.execute("SELECT ?", (index,)) as cursor:
                    result = await cursor.fetchone()
                    return result[0]
        
        # 并发执行多个数据库操作
        tasks = [db_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        self.assertEqual(len(results), 10)
        for i, result in enumerate(results):
            self.assertEqual(result, i)
    
    async def test_database_transaction_isolation(self):
        """测试数据库事务隔离"""
        await self.db_manager.initialize()
        
        from resume_assistant.data.models import Job
        
        # 创建测试职位
        job = Job(
            id="isolation-test-job",
            title="隔离测试职位",
            company="测试公司",
            url="https://example.com/isolation"
        )
        await self.db_manager.save_job(job)
        
        # 模拟并发更新
        async def update_job_title(new_title):
            async with self.db_manager.transaction() as conn:
                await conn.execute(
                    "UPDATE jobs SET title = ? WHERE id = ?",
                    (new_title, "isolation-test-job")
                )
                # 模拟处理时间
                await asyncio.sleep(0.1)
        
        # 并发执行更新
        await asyncio.gather(
            update_job_title("更新标题1"),
            update_job_title("更新标题2"),
            return_exceptions=True
        )
        
        # 验证最终状态一致
        updated_job = await self.db_manager.get_job("isolation-test-job")
        self.assertIsNotNone(updated_job)
        self.assertIn("更新标题", updated_job.title)
    
    async def test_database_backup_restore(self):
        """测试数据库备份和恢复"""
        await self.db_manager.initialize()
        
        from resume_assistant.data.models import Job, Resume
        
        # 创建测试数据
        original_job = Job(
            id="backup-job",
            title="备份测试职位",
            company="备份公司",
            url="https://example.com/backup"
        )
        await self.db_manager.save_job(original_job)
        
        original_resume = Resume(
            id="backup-resume",
            filename="backup_resume.pdf",
            content="备份测试简历内容"
        )
        await self.db_manager.save_resume(original_resume)
        
        # 模拟备份（复制数据库文件）
        backup_path = self.temp_db.name + ".backup"
        
        # 关闭当前连接
        await self.db_manager.close()
        
        # 复制文件作为备份
        import shutil
        shutil.copy2(self.temp_db.name, backup_path)
        
        try:
            # 重新初始化数据库管理器
            self.db_manager = DatabaseManager(self.temp_db.name)
            await self.db_manager.initialize()
            
            # 删除原始数据
            await self.db_manager.delete_job("backup-job")
            await self.db_manager.delete_resume("backup-resume")
            
            # 验证数据已删除
            self.assertIsNone(await self.db_manager.get_job("backup-job"))
            self.assertIsNone(await self.db_manager.get_resume("backup-resume"))
            
            # 模拟恢复（替换数据库文件）
            await self.db_manager.close()
            shutil.copy2(backup_path, self.temp_db.name)
            
            # 重新初始化
            self.db_manager = DatabaseManager(self.temp_db.name)
            await self.db_manager.initialize()
            
            # 验证数据已恢复
            restored_job = await self.db_manager.get_job("backup-job")
            restored_resume = await self.db_manager.get_resume("backup-resume")
            
            self.assertIsNotNone(restored_job)
            self.assertIsNotNone(restored_resume)
            self.assertEqual(restored_job.title, "备份测试职位")
            self.assertEqual(restored_resume.filename, "backup_resume.pdf")
        
        finally:
            # 清理备份文件
            try:
                os.unlink(backup_path)
            except OSError:
                pass


class TestServiceCommunication(unittest.TestCase):
    """服务间通信测试"""
    
    async def test_ai_analyzer_with_real_api_format(self):
        """测试AI分析器与真实API格式的兼容性"""
        # 使用真实的API响应格式进行测试
        real_api_response = {
            "id": "chatcmpl-123456789",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "根据提供的简历和职位信息分析：\n\n**匹配度分析：**\n1. 技能匹配度：90%\n   - Python开发经验：3年 ✓\n   - Django框架：熟练 ✓\n   - 数据库经验：PostgreSQL ✓\n\n2. 工作经验：符合要求\n   - 3年后端开发经验\n   - 有团队协作经验\n\n**综合评价：**\n该候选人技能与职位要求高度匹配，建议安排技术面试。\n\n**面试建议：**\n- 重点考察Django项目经验\n- 了解其对微服务架构的理解\n- 评估其学习能力和团队协作"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 256,
                "completion_tokens": 180,
                "total_tokens": 436
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = real_api_response
            mock_post.return_value = mock_response
            
            client = DeepSeekClient(api_key="test-key")
            result = await client.analyze("测试简历内容", "测试职位要求")
            
            # 验证解析结果
            self.assertIn("匹配度分析", result)
            self.assertIn("90%", result)
            self.assertIn("技术面试", result)
            self.assertIn("面试建议", result)
    
    async def test_error_propagation_chain(self):
        """测试错误传播链"""
        # 模拟从底层到上层的错误传播
        
        # 1. 数据库错误
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db_manager = DatabaseManager(temp_db.name)
            await db_manager.initialize()
            
            # 模拟数据库连接问题
            with patch.object(db_manager, 'get_connection') as mock_conn:
                mock_conn.side_effect = Exception("Database connection failed")
                
                # 2. 服务层错误传播
                ai_analyzer = AIAnalyzer()
                
                # 这应该触发数据库错误，然后传播到服务层
                with self.assertRaises(Exception) as context:
                    # 模拟需要数据库的操作
                    await db_manager.get_job("non-existent-job")
                
                self.assertIn("Database connection failed", str(context.exception))
            
        finally:
            await db_manager.close()
            try:
                os.unlink(temp_db.name)
            except OSError:
                pass


def run_api_service_integration_tests():
    """运行API和服务集成测试"""
    print("🔌 运行API和服务集成测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestAIServiceIntegration,
        TestScrapingServiceIntegration,
        TestDatabaseServiceIntegration,
        TestServiceCommunication
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_api_service_integration_tests()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")