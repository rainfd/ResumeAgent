"""增强爬虫模块测试

测试爬虫协调器、多站点支持和Web适配器功能。
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_assistant.core.scraping_orchestrator import (
    ScrapingOrchestrator,
    ScrapingConfig,
    SiteSupport,
    AntiDetectionManager,
    DataValidator,
    ScrapingMonitor,
    MultiSiteScraper
)
from resume_assistant.core.lagou_scraper import LagouScraper
from resume_assistant.web.enhanced_job_adapter import EnhancedJobAdapter
from resume_assistant.data.database import DatabaseManager
from resume_assistant.core.job_manager import Job


class TestScrapingConfig:
    """测试爬虫配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ScrapingConfig()
        
        assert config.max_retries == 3
        assert config.retry_delay == 2.0
        assert config.timeout == 30
        assert config.concurrent_limit == 3
        assert config.use_proxy == False
        assert config.enable_monitoring == True
        assert config.data_validation == True
        assert config.headless == False
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ScrapingConfig(
            max_retries=5,
            timeout=60,
            headless=True,
            enable_monitoring=False
        )
        
        assert config.max_retries == 5
        assert config.timeout == 60
        assert config.headless == True
        assert config.enable_monitoring == False


class TestAntiDetectionManager:
    """测试反检测管理器"""
    
    def test_user_agent_generation(self):
        """测试用户代理生成"""
        manager = AntiDetectionManager()
        
        ua1 = manager.get_random_user_agent()
        ua2 = manager.get_random_user_agent()
        
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        assert len(ua1) > 10
        assert 'Mozilla' in ua1
    
    def test_delay_calculation(self):
        """测试延迟计算"""
        manager = AntiDetectionManager()
        
        delay1 = manager.calculate_delay()
        delay2 = manager.calculate_delay()
        
        assert delay1 > 0
        assert delay2 > delay1  # 第二次应该更长，因为间隔短
    
    def test_human_behavior_simulation(self):
        """测试人类行为模拟"""
        manager = AntiDetectionManager()
        
        behavior = manager.simulate_human_behavior()
        
        assert 'scroll_behavior' in behavior
        assert 'mouse_movement' in behavior
        assert 'reading_time' in behavior
        assert behavior['scroll_behavior']['scroll_count'] >= 2
        assert behavior['reading_time'] >= 5.0


class TestDataValidator:
    """测试数据验证器"""
    
    def create_valid_job(self):
        """创建有效的职位对象"""
        job = Job()
        job.title = "Python开发工程师"
        job.company = "科技公司"
        job.description = "负责后端开发工作，使用Python、Django等技术栈"
        job.salary_min = 10000
        job.salary_max = 15000
        job.skills = ["Python", "Django", "MySQL"]
        return job
    
    def test_valid_job_validation(self):
        """测试有效职位验证"""
        validator = DataValidator()
        job = self.create_valid_job()
        
        is_valid, errors = validator.validate_job_data(job)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_invalid_job_validation(self):
        """测试无效职位验证"""
        validator = DataValidator()
        job = Job()
        job.title = ""  # 空标题
        job.company = "A"  # 太短
        job.description = "短"  # 太短
        job.salary_min = 20000
        job.salary_max = 10000  # 不合理的薪资范围
        
        is_valid, errors = validator.validate_job_data(job)
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("标题" in error for error in errors)
        assert any("公司" in error for error in errors)
        assert any("薪资" in error for error in errors)
    
    def test_job_data_cleaning(self):
        """测试职位数据清洗"""
        validator = DataValidator()
        job = Job()
        job.title = "  Python  开发工程师  "
        job.company = "  科技  公司  "
        job.description = "  职位描述  \n\n  \n  详细内容  \n  "
        job.skills = ["  Python  ", "Django", "", "  MySQL  ", "Python"]  # 包含重复和空值
        
        cleaned_job = validator.clean_job_data(job)
        
        assert cleaned_job.title == "Python 开发工程师"
        assert cleaned_job.company == "科技 公司"
        assert "职位描述\n详细内容" in cleaned_job.description
        assert len(cleaned_job.skills) == 3  # 去重后
        assert "" not in cleaned_job.skills  # 移除空值
        assert "Python" in cleaned_job.skills
        assert "Django" in cleaned_job.skills
        assert "MySQL" in cleaned_job.skills


class TestScrapingMonitor:
    """测试爬取监控器"""
    
    def test_stats_initialization(self):
        """测试统计初始化"""
        monitor = ScrapingMonitor()
        
        assert monitor.stats.total_attempts == 0
        assert monitor.stats.successful_scrapes == 0
        assert monitor.stats.failed_scrapes == 0
        assert monitor.stats.success_rate == 0.0
    
    def test_record_success(self):
        """测试记录成功"""
        monitor = ScrapingMonitor()
        
        monitor.record_attempt("boss", "https://test.com", time.time())
        monitor.record_success("boss", "https://test.com", 2.5)
        
        assert monitor.stats.total_attempts == 1
        assert monitor.stats.successful_scrapes == 1
        assert monitor.stats.success_rate == 1.0
        assert monitor.stats.average_response_time == 2.5
    
    def test_record_failure(self):
        """测试记录失败"""
        monitor = ScrapingMonitor()
        
        monitor.record_attempt("boss", "https://test.com", time.time())
        monitor.record_failure("boss", "https://test.com", "网络错误")
        
        assert monitor.stats.total_attempts == 1
        assert monitor.stats.failed_scrapes == 1
        assert monitor.stats.success_rate == 0.0
    
    def test_performance_report(self):
        """测试性能报告"""
        monitor = ScrapingMonitor()
        
        # 记录一些数据
        monitor.record_attempt("boss", "https://test1.com", time.time())
        monitor.record_success("boss", "https://test1.com", 2.0)
        
        monitor.record_attempt("lagou", "https://test2.com", time.time())
        monitor.record_failure("lagou", "https://test2.com", "错误")
        
        report = monitor.get_performance_report()
        
        assert 'overall' in report
        assert 'by_site' in report
        assert report['overall']['total_attempts'] == 2
        assert report['overall']['success_rate'] == '50.00%'
        assert 'boss' in report['by_site']
        assert 'lagou' in report['by_site']


class TestMultiSiteScraper:
    """测试多站点爬虫"""
    
    def test_site_detection(self):
        """测试网站检测"""
        config = ScrapingConfig()
        scraper = MultiSiteScraper(config)
        
        # 测试BOSS直聘URL
        boss_site = scraper.detect_site("https://www.zhipin.com/job_detail/123456.html")
        assert boss_site == SiteSupport.BOSS_ZHIPIN
        
        # 测试拉勾网URL
        lagou_site = scraper.detect_site("https://www.lagou.com/jobs/123456.html")
        assert lagou_site == SiteSupport.LAGOU
        
        # 测试不支持的URL
        unknown_site = scraper.detect_site("https://www.unknown.com/jobs/123456")
        assert unknown_site is None
    
    @patch('src.resume_assistant.core.scraping_orchestrator.PlaywrightScraper')
    def test_scraper_initialization(self, mock_playwright):
        """测试爬虫初始化"""
        config = ScrapingConfig(headless=True)
        scraper = MultiSiteScraper(config)
        
        # 验证BOSS直聘爬虫被初始化
        assert 'boss' in scraper.scrapers
        mock_playwright.assert_called_once_with(headless=True, user_data_dir=None)


class TestScrapingOrchestrator:
    """测试爬虫协调器"""
    
    def test_initialization(self):
        """测试初始化"""
        orchestrator = ScrapingOrchestrator()
        
        assert orchestrator.config is not None
        assert orchestrator.multi_scraper is not None
        assert orchestrator.semaphore._value == 3  # 默认并发限制
    
    def test_supported_sites(self):
        """测试支持的网站列表"""
        orchestrator = ScrapingOrchestrator()
        
        sites = orchestrator.get_supported_sites()
        
        assert isinstance(sites, list)
        assert len(sites) > 0
        assert 'boss' in sites
        assert 'lagou' in sites
    
    def test_url_support_check(self):
        """测试URL支持检查"""
        orchestrator = ScrapingOrchestrator()
        
        # 支持的URL
        assert orchestrator.is_url_supported("https://www.zhipin.com/job_detail/123456.html") == True
        assert orchestrator.is_url_supported("https://www.lagou.com/jobs/123456.html") == True
        
        # 不支持的URL
        assert orchestrator.is_url_supported("https://www.unknown.com/jobs/123456") == False
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        orchestrator = ScrapingOrchestrator()
        
        health = await orchestrator.health_check()
        
        assert 'status' in health
        assert 'scrapers_available' in health
        assert 'supported_sites' in health
        assert 'config' in health
        assert 'timestamp' in health
        assert health['status'] in ['healthy', 'degraded']


class TestLagouScraper:
    """测试拉勾网爬虫"""
    
    def test_url_validation(self):
        """测试URL验证"""
        scraper = LagouScraper(headless=True)
        
        # 有效URL
        valid_urls = [
            "https://www.lagou.com/jobs/123456.html",
            "https://www.lagou.com/jobs/789012.html"
        ]
        
        for url in valid_urls:
            assert scraper._validate_lagou_url(url) == True
        
        # 无效URL
        invalid_urls = [
            "https://www.zhipin.com/job_detail/123456.html",
            "https://www.lagou.com/company/123456",
            "invalid-url"
        ]
        
        for url in invalid_urls:
            assert scraper._validate_lagou_url(url) == False
    
    def test_job_id_extraction(self):
        """测试职位ID提取"""
        scraper = LagouScraper(headless=True)
        
        # HTML格式URL
        job_id1 = scraper._extract_job_id("https://www.lagou.com/jobs/123456.html")
        assert job_id1 == "123456"
        
        # 普通格式URL
        job_id2 = scraper._extract_job_id("https://www.lagou.com/jobs/789012")
        assert job_id2 == "789012"
        
        # 无效URL
        job_id3 = scraper._extract_job_id("https://www.lagou.com/company/123456")
        assert job_id3 is None
    
    def test_skills_extraction(self):
        """测试技能提取"""
        scraper = LagouScraper(headless=True)
        
        description = """
        我们需要一名优秀的Python开发工程师，要求：
        1. 熟练掌握Python、Django、Flask框架
        2. 熟悉MySQL、Redis数据库
        3. 了解Docker、Kubernetes部署
        4. 有React、Vue.js前端经验优先
        """
        
        skills = scraper._extract_skills_from_description(description)
        
        assert "Python" in skills
        assert "Django" in skills
        assert "Flask" in skills
        assert "MySQL" in skills
        assert "Redis" in skills
        assert "Docker" in skills
        
        # 技能数量应该被限制
        assert len(skills) <= 10
    
    def test_anti_robot_detection(self):
        """测试反爬检测"""
        scraper = LagouScraper(headless=True)
        
        # 包含验证码的内容
        robot_content = "请输入验证码以继续访问"
        assert scraper._check_anti_robot(robot_content) == True
        
        # 正常内容
        normal_content = "Python开发工程师招聘信息"
        assert scraper._check_anti_robot(normal_content) == False


class TestEnhancedJobAdapter:
    """测试增强的职位适配器"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """模拟数据库管理器"""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.save_job = AsyncMock(return_value=1)
        return db_manager
    
    def test_initialization(self, mock_db_manager):
        """测试初始化"""
        adapter = EnhancedJobAdapter(mock_db_manager)
        
        assert adapter.db_manager == mock_db_manager
        assert adapter.orchestrator is None
        assert adapter._current_config is None
    
    def test_orchestrator_creation(self, mock_db_manager):
        """测试协调器创建"""
        adapter = EnhancedJobAdapter(mock_db_manager)
        
        # 第一次获取
        orchestrator1 = adapter._get_orchestrator()
        assert orchestrator1 is not None
        assert adapter.orchestrator == orchestrator1
        
        # 第二次获取应该返回同一个实例
        orchestrator2 = adapter._get_orchestrator()
        assert orchestrator2 == orchestrator1
    
    def test_supported_sites_info(self, mock_db_manager):
        """测试支持的网站信息"""
        adapter = EnhancedJobAdapter(mock_db_manager)
        
        sites = adapter.get_supported_sites()
        
        assert isinstance(sites, list)
        assert len(sites) > 0
        
        for site in sites:
            assert 'value' in site
            assert 'name' in site
            assert 'example_url' in site
            assert 'status' in site
    
    def test_url_support_check(self, mock_db_manager):
        """测试URL支持检查"""
        adapter = EnhancedJobAdapter(mock_db_manager)
        
        # 支持的URL
        assert adapter.is_url_supported("https://www.zhipin.com/job_detail/123456.html") == True
        
        # 不支持的URL
        assert adapter.is_url_supported("https://www.unknown.com/jobs/123456") == False
    
    def test_job_conversion(self, mock_db_manager):
        """测试职位对象转换"""
        adapter = EnhancedJobAdapter(mock_db_manager)
        
        # 创建模拟的Job对象
        job = Job()
        job.title = "Python开发工程师"
        job.company = "科技公司"
        job.description = "职位描述"
        job.skills = ["Python", "Django"]
        job.salary_range = "10k-15k"
        job.location = "北京"
        
        job_info = adapter._convert_to_job_info(job, "https://test.com")
        
        assert job_info.title == "Python开发工程师"
        assert job_info.company == "科技公司"
        assert job_info.url == "https://test.com"
        assert job_info.skills == ["Python", "Django"]


# 集成测试
class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    @patch('src.resume_assistant.core.scraper.PlaywrightScraper')
    async def test_full_scraping_workflow(self, mock_scraper_class):
        """测试完整爬取工作流"""
        # 设置模拟
        mock_scraper = Mock()
        mock_job = Job()
        mock_job.title = "测试职位"
        mock_job.company = "测试公司"
        mock_job.description = "测试描述"
        
        from src.resume_assistant.core.scraper import ScrapingResult
        mock_result = ScrapingResult(
            success=True,
            job=mock_job,
            url="https://www.zhipin.com/job_detail/123456.html",
            scraped_at=datetime.now()
        )
        
        mock_scraper.scrape_job.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # 创建协调器并测试
        config = ScrapingConfig(enable_monitoring=False)  # 禁用监控以简化测试
        orchestrator = ScrapingOrchestrator(config)
        
        result = await orchestrator.scrape_single_job("https://www.zhipin.com/job_detail/123456.html")
        
        assert result.success == True
        assert result.job.title == "测试职位"
        
        # 清理
        orchestrator.cleanup()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])