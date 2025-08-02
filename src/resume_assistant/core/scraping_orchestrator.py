"""爬虫协调器 - 统一管理多网站爬虫和反检测机制

这个模块提供了一个统一的爬虫接口，支持多个招聘网站的职位信息爬取，
并集成了先进的反检测机制和性能监控功能。
"""

import time
import random
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
from enum import Enum
import json
import os
from pathlib import Path

try:
    import aiohttp
    from fake_useragent import UserAgent
    HAS_ASYNC_SUPPORT = True
except ImportError:
    HAS_ASYNC_SUPPORT = False

from ..utils import get_logger
from ..utils.errors import NetworkError, ResumeAssistantError
from .scraper import JobScraper, ScrapingResult, PlaywrightScraper
from .job_manager import Job

logger = get_logger(__name__)


class SiteSupport(Enum):
    """支持的招聘网站"""
    BOSS_ZHIPIN = "boss"
    LAGOU = "lagou"  
    ZHILIAN = "zhilian"
    LIEPIN = "liepin"
    QIANCHENG = "51job"


@dataclass
class ScrapingConfig:
    """爬虫配置"""
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: int = 30
    concurrent_limit: int = 3
    use_proxy: bool = False
    proxy_pool: List[str] = field(default_factory=list)
    enable_monitoring: bool = True
    data_validation: bool = True
    headless: bool = False
    user_data_dir: Optional[str] = None


@dataclass
class ScrapingStats:
    """爬取统计信息"""
    total_attempts: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    site_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class AntiDetectionManager:
    """反检测管理器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.user_agents = self._load_user_agents()
        self.request_intervals = []
        self.last_request_time = None
        
    def _load_user_agents(self) -> List[str]:
        """加载用户代理列表"""
        try:
            if HAS_ASYNC_SUPPORT:
                ua = UserAgent()
                return [ua.random for _ in range(10)]
        except Exception:
            pass
            
        # 备用用户代理列表
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    def get_random_user_agent(self) -> str:
        """获取随机用户代理"""
        return random.choice(self.user_agents)
    
    def calculate_delay(self) -> float:
        """计算智能延迟时间"""
        base_delay = random.uniform(1.0, 3.0)
        
        # 如果最近请求频繁，增加延迟
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < 2.0:
                base_delay += random.uniform(2.0, 5.0)
        
        # 记录请求间隔
        if len(self.request_intervals) >= 10:
            self.request_intervals.pop(0)
        
        if self.last_request_time:
            interval = time.time() - self.last_request_time
            self.request_intervals.append(interval)
            
            # 如果平均间隔太短，增加延迟
            avg_interval = sum(self.request_intervals) / len(self.request_intervals)
            if avg_interval < 3.0:
                base_delay += random.uniform(1.0, 3.0)
        
        self.last_request_time = time.time()
        return base_delay
    
    def simulate_human_behavior(self) -> Dict[str, Any]:
        """模拟人类浏览行为"""
        return {
            'scroll_behavior': {
                'scroll_count': random.randint(2, 5),
                'scroll_delay': random.uniform(0.5, 2.0),
                'random_pauses': random.randint(1, 3)
            },
            'mouse_movement': {
                'move_count': random.randint(3, 8),
                'move_delay': random.uniform(0.1, 0.5)
            },
            'reading_time': random.uniform(5.0, 15.0)
        }


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
    def validate_job_data(self, job: Job) -> Tuple[bool, List[str]]:
        """验证职位数据质量"""
        errors = []
        
        # 必填字段检查
        if not job.title or len(job.title.strip()) < 2:
            errors.append("职位标题缺失或过短")
            
        if not job.company or len(job.company.strip()) < 2:
            errors.append("公司名称缺失或过短")
            
        if not job.description or len(job.description.strip()) < 10:
            errors.append("职位描述缺失或过短")
            
        # 数据质量检查
        if job.salary_min and job.salary_max:
            if job.salary_min > job.salary_max:
                errors.append("薪资范围不合理")
                
        # 技能标签检查
        if job.skills:
            if len(job.skills) > 20:
                errors.append("技能标签过多，可能存在噪音数据")
                
        # 内容质量检查
        if len(job.description) > 10000:
            errors.append("职位描述过长，可能包含非相关内容")
            
        return len(errors) == 0, errors
    
    def clean_job_data(self, job: Job) -> Job:
        """清洗职位数据"""
        # 清理标题
        if job.title:
            job.title = job.title.strip()
            # 移除多余的空格和特殊字符
            job.title = ' '.join(job.title.split())
            
        # 清理公司名称
        if job.company:
            job.company = job.company.strip()
            job.company = ' '.join(job.company.split())
            
        # 清理描述
        if job.description:
            job.description = job.description.strip()
            # 移除过多的换行符
            job.description = '\n'.join(line.strip() for line in job.description.split('\n') if line.strip())
            
        # 清理技能列表
        if job.skills:
            job.skills = [skill.strip() for skill in job.skills if skill.strip()]
            job.skills = list(set(job.skills))  # 去重
            
        return job


class ScrapingMonitor:
    """爬取监控器"""
    
    def __init__(self, stats_file: Optional[str] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.stats = ScrapingStats()
        self.stats_file = stats_file or "scraping_stats.json"
        self.load_stats()
        
    def load_stats(self):
        """加载统计数据"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats.total_attempts = data.get('total_attempts', 0)
                    self.stats.successful_scrapes = data.get('successful_scrapes', 0)
                    self.stats.failed_scrapes = data.get('failed_scrapes', 0)
                    self.stats.average_response_time = data.get('average_response_time', 0.0)
                    self.stats.success_rate = data.get('success_rate', 0.0)
                    self.stats.site_stats = data.get('site_stats', {})
        except Exception as e:
            self.logger.warning(f"加载统计数据失败: {e}")
            
    def save_stats(self):
        """保存统计数据"""
        try:
            data = {
                'total_attempts': self.stats.total_attempts,
                'successful_scrapes': self.stats.successful_scrapes,
                'failed_scrapes': self.stats.failed_scrapes,
                'average_response_time': self.stats.average_response_time,
                'success_rate': self.stats.success_rate,
                'site_stats': self.stats.site_stats,
                'last_updated': self.stats.last_updated.isoformat()
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存统计数据失败: {e}")
            
    def record_attempt(self, site: str, url: str, start_time: float):
        """记录爬取尝试"""
        self.stats.total_attempts += 1
        
        # 记录站点统计
        if site not in self.stats.site_stats:
            self.stats.site_stats[site] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'avg_response_time': 0.0,
                'last_success': None,
                'last_failure': None
            }
        
        self.stats.site_stats[site]['attempts'] += 1
        self.stats.last_updated = datetime.now()
        
    def record_success(self, site: str, url: str, response_time: float):
        """记录成功爬取"""
        self.stats.successful_scrapes += 1
        
        # 更新平均响应时间
        total_time = self.stats.average_response_time * (self.stats.successful_scrapes - 1)
        self.stats.average_response_time = (total_time + response_time) / self.stats.successful_scrapes
        
        # 更新成功率
        self.stats.success_rate = self.stats.successful_scrapes / self.stats.total_attempts if self.stats.total_attempts > 0 else 0
        
        # 更新站点统计
        if site in self.stats.site_stats:
            site_stats = self.stats.site_stats[site]
            site_stats['successes'] += 1
            
            # 更新站点平均响应时间
            if site_stats['successes'] > 1:
                total_site_time = site_stats['avg_response_time'] * (site_stats['successes'] - 1)
                site_stats['avg_response_time'] = (total_site_time + response_time) / site_stats['successes']
            else:
                site_stats['avg_response_time'] = response_time
                
            site_stats['last_success'] = datetime.now().isoformat()
        
        self.save_stats()
        
    def record_failure(self, site: str, url: str, error: str):
        """记录失败爬取"""
        self.stats.failed_scrapes += 1
        self.stats.success_rate = self.stats.successful_scrapes / self.stats.total_attempts if self.stats.total_attempts > 0 else 0
        
        # 更新站点统计
        if site in self.stats.site_stats:
            site_stats = self.stats.site_stats[site]
            site_stats['failures'] += 1
            site_stats['last_failure'] = datetime.now().isoformat()
        
        self.save_stats()
        
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {
            'overall': {
                'total_attempts': self.stats.total_attempts,
                'success_rate': f"{self.stats.success_rate:.2%}",
                'average_response_time': f"{self.stats.average_response_time:.2f}s",
                'successful_scrapes': self.stats.successful_scrapes,
                'failed_scrapes': self.stats.failed_scrapes
            },
            'by_site': {}
        }
        
        for site, stats in self.stats.site_stats.items():
            site_success_rate = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0
            report['by_site'][site] = {
                'attempts': stats['attempts'],
                'success_rate': f"{site_success_rate:.2%}",
                'avg_response_time': f"{stats['avg_response_time']:.2f}s",
                'last_success': stats['last_success'],
                'last_failure': stats['last_failure']
            }
            
        return report


class MultiSiteScraper:
    """多站点爬虫管理器"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.scrapers: Dict[str, JobScraper] = {}
        self.anti_detection = AntiDetectionManager()
        self.data_validator = DataValidator()
        self.monitor = ScrapingMonitor() if config.enable_monitoring else None
        
        self._initialize_scrapers()
        
    def _initialize_scrapers(self):
        """初始化各站点爬虫"""
        # BOSS直聘爬虫 (使用现有的PlaywrightScraper)
        self.scrapers[SiteSupport.BOSS_ZHIPIN.value] = PlaywrightScraper(
            headless=self.config.headless,
            user_data_dir=self.config.user_data_dir
        )
        
        # 拉勾网爬虫
        try:
            from .lagou_scraper import LagouScraper
            self.scrapers[SiteSupport.LAGOU.value] = LagouScraper(
                headless=self.config.headless
            )
        except ImportError:
            self.logger.warning("拉勾网爬虫模块未找到，跳过初始化")
        
        # TODO: 其他网站爬虫实现
        # self.scrapers[SiteSupport.ZHILIAN.value] = ZhilianScraper()
        # self.scrapers[SiteSupport.LIEPIN.value] = LiepinScraper()
        
    def detect_site(self, url: str) -> Optional[SiteSupport]:
        """检测URL所属的招聘网站"""
        domain = urlparse(url).netloc.lower()
        
        if 'zhipin.com' in domain:
            return SiteSupport.BOSS_ZHIPIN
        elif 'lagou.com' in domain:
            return SiteSupport.LAGOU
        elif 'zhaopin.com' in domain:
            return SiteSupport.ZHILIAN
        elif 'liepin.com' in domain:
            return SiteSupport.LIEPIN
        elif '51job.com' in domain:
            return SiteSupport.QIANCHENG
            
        return None
        
    async def scrape_with_retries(self, url: str, max_retries: Optional[int] = None) -> ScrapingResult:
        """带重试机制的爬取"""
        max_retries = max_retries or self.config.max_retries
        site_type = self.detect_site(url)
        
        if not site_type:
            return ScrapingResult(
                success=False,
                error="不支持的招聘网站",
                url=url,
                scraped_at=datetime.now()
            )
            
        site_name = site_type.value
        if site_name not in self.scrapers:
            return ScrapingResult(
                success=False,
                error=f"网站 {site_name} 的爬虫未实现",
                url=url,
                scraped_at=datetime.now()
            )
            
        scraper = self.scrapers[site_name]
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                if self.monitor:
                    self.monitor.record_attempt(site_name, url, start_time)
                
                # 应用反检测延迟
                if attempt > 0:
                    delay = self.anti_detection.calculate_delay()
                    self.logger.info(f"第 {attempt + 1} 次尝试，延迟 {delay:.2f} 秒...")
                    await asyncio.sleep(delay)
                
                # 执行爬取
                result = scraper.scrape_job(url)
                response_time = time.time() - start_time
                
                if result.success and result.job:
                    # 数据验证和清洗
                    if self.config.data_validation:
                        is_valid, errors = self.data_validator.validate_job_data(result.job)
                        if not is_valid:
                            self.logger.warning(f"数据质量问题: {', '.join(errors)}")
                        
                        result.job = self.data_validator.clean_job_data(result.job)
                    
                    if self.monitor:
                        self.monitor.record_success(site_name, url, response_time)
                    
                    self.logger.info(f"成功爬取职位: {result.job.title} - {result.job.company}")
                    return result
                else:
                    last_error = result.error or "未知错误"
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"第 {attempt + 1} 次爬取失败: {last_error}")
                
                if attempt < max_retries:
                    # 指数退避
                    delay = self.config.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
        
        # 所有尝试都失败了
        if self.monitor:
            self.monitor.record_failure(site_name, url, last_error or "未知错误")
        
        return ScrapingResult(
            success=False,
            error=f"重试 {max_retries} 次后仍然失败: {last_error}",
            url=url,
            scraped_at=datetime.now()
        )


class ScrapingOrchestrator:
    """爬虫协调器 - 主要接口类"""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.logger = get_logger(self.__class__.__name__)
        self.multi_scraper = MultiSiteScraper(self.config)
        self.semaphore = asyncio.Semaphore(self.config.concurrent_limit)
        
    async def scrape_single_job(self, url: str) -> ScrapingResult:
        """爬取单个职位"""
        async with self.semaphore:
            return await self.multi_scraper.scrape_with_retries(url)
    
    async def scrape_multiple_jobs(self, urls: List[str]) -> List[ScrapingResult]:
        """并发爬取多个职位"""
        self.logger.info(f"开始并发爬取 {len(urls)} 个职位...")
        
        tasks = [self.scrape_single_job(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ScrapingResult(
                    success=False,
                    error=str(result),
                    url=urls[i],
                    scraped_at=datetime.now()
                ))
            else:
                processed_results.append(result)
        
        # 统计结果
        successful = sum(1 for r in processed_results if r.success)
        self.logger.info(f"爬取完成: {successful}/{len(urls)} 成功")
        
        return processed_results
    
    def get_supported_sites(self) -> List[str]:
        """获取支持的网站列表"""
        return [site.value for site in SiteSupport]
    
    def is_url_supported(self, url: str) -> bool:
        """检查URL是否被支持"""
        return self.multi_scraper.detect_site(url) is not None
    
    def get_performance_stats(self) -> Optional[Dict[str, Any]]:
        """获取性能统计"""
        if self.multi_scraper.monitor:
            return self.multi_scraper.monitor.get_performance_report()
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            'status': 'healthy',
            'scrapers_available': len(self.multi_scraper.scrapers),
            'supported_sites': self.get_supported_sites(),
            'config': {
                'max_retries': self.config.max_retries,
                'timeout': self.config.timeout,
                'concurrent_limit': self.config.concurrent_limit,
                'headless': self.config.headless
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 检查各个爬虫的状态
        scraper_status = {}
        for site, scraper in self.multi_scraper.scrapers.items():
            try:
                # 这里可以添加爬虫健康检查逻辑
                scraper_status[site] = 'available'
            except Exception as e:
                scraper_status[site] = f'error: {str(e)}'
                health_status['status'] = 'degraded'
        
        health_status['scrapers_status'] = scraper_status
        
        # 添加性能统计
        if self.config.enable_monitoring:
            health_status['performance'] = self.get_performance_stats()
        
        return health_status
    
    def cleanup(self):
        """清理资源"""
        try:
            for scraper in self.multi_scraper.scrapers.values():
                if hasattr(scraper, 'cleanup'):
                    scraper.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")


# 便捷函数
async def scrape_job_url(url: str, config: Optional[ScrapingConfig] = None) -> ScrapingResult:
    """便捷函数：爬取单个职位URL"""
    orchestrator = ScrapingOrchestrator(config)
    try:
        return await orchestrator.scrape_single_job(url)
    finally:
        orchestrator.cleanup()


async def scrape_job_urls(urls: List[str], config: Optional[ScrapingConfig] = None) -> List[ScrapingResult]:
    """便捷函数：批量爬取职位URL"""
    orchestrator = ScrapingOrchestrator(config)
    try:
        return await orchestrator.scrape_multiple_jobs(urls)
    finally:
        orchestrator.cleanup()


def get_scraping_config(
    headless: bool = False,
    max_retries: int = 3,
    concurrent_limit: int = 3,
    enable_monitoring: bool = True,
    user_data_dir: Optional[str] = None
) -> ScrapingConfig:
    """便捷函数：创建爬虫配置"""
    return ScrapingConfig(
        headless=headless,
        max_retries=max_retries,
        concurrent_limit=concurrent_limit,
        enable_monitoring=enable_monitoring,
        user_data_dir=user_data_dir
    )