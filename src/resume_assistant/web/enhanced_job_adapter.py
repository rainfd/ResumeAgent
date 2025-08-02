"""增强的职位管理Web适配器

集成了新的爬虫协调器，提供更强大的多站点支持和性能监控功能。
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import streamlit as st

from ..core.scraping_orchestrator import (
    ScrapingOrchestrator, 
    ScrapingConfig, 
    ScrapingResult,
    SiteSupport,
    get_scraping_config
)
from ..data.models import JobInfo
from ..data.database import DatabaseManager
from ..utils import get_logger

logger = get_logger(__name__)


class EnhancedJobAdapter:
    """增强的职位管理适配器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(self.__class__.__name__)
        self.orchestrator: Optional[ScrapingOrchestrator] = None
        self._current_config = None
        
    def _get_orchestrator(self, config: Optional[ScrapingConfig] = None) -> ScrapingOrchestrator:
        """获取或创建爬虫协调器实例"""
        # 如果配置有变化，重新创建协调器
        if config != self._current_config or not self.orchestrator:
            if self.orchestrator:
                self.orchestrator.cleanup()
            
            self.orchestrator = ScrapingOrchestrator(config or ScrapingConfig())
            self._current_config = config
            
        return self.orchestrator
    
    async def scrape_single_job_async(
        self, 
        url: str, 
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ScrapingResult:
        """异步爬取单个职位"""
        orchestrator = self._get_orchestrator(config)
        
        if progress_callback:
            progress_callback("开始爬取职位信息...")
        
        try:
            # 检查URL是否被支持
            if not orchestrator.is_url_supported(url):
                return ScrapingResult(
                    success=False,
                    error="不支持的招聘网站URL",
                    url=url,
                    scraped_at=datetime.now()
                )
            
            if progress_callback:
                progress_callback("正在连接目标网站...")
            
            # 执行爬取
            result = await orchestrator.scrape_single_job(url)
            
            if result.success and result.job:
                if progress_callback:
                    progress_callback("正在保存到数据库...")
                
                # 转换为JobInfo并保存
                job_info = self._convert_to_job_info(result.job, url)
                job_id = await self.db_manager.save_job(job_info)
                
                if progress_callback:
                    progress_callback(f"成功保存职位: {result.job.title}")
                
                self.logger.info(f"成功爬取并保存职位: {result.job.title} (ID: {job_id})")
                
            return result
            
        except Exception as e:
            self.logger.error(f"爬取过程出错: {e}")
            return ScrapingResult(
                success=False,
                error=f"爬取过程出错: {str(e)}",
                url=url,
                scraped_at=datetime.now()
            )
    
    def scrape_single_job_sync(
        self, 
        url: str, 
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ScrapingResult:
        """同步爬取单个职位（Streamlit兼容）"""
        # 转换配置
        scraping_config = None
        if config:
            scraping_config = get_scraping_config(**config)
        
        # 运行异步函数
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果事件循环正在运行，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.scrape_single_job_async(url, scraping_config, progress_callback)
                )
                return future.result()
        else:
            return loop.run_until_complete(
                self.scrape_single_job_async(url, scraping_config, progress_callback)
            )
    
    async def scrape_multiple_jobs_async(
        self, 
        urls: List[str], 
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[ScrapingResult]:
        """异步批量爬取职位"""
        orchestrator = self._get_orchestrator(config)
        
        if progress_callback:
            progress_callback(f"开始批量爬取 {len(urls)} 个职位...", 0.0)
        
        try:
            # 过滤支持的URL
            supported_urls = []
            unsupported_results = []
            
            for url in urls:
                if orchestrator.is_url_supported(url):
                    supported_urls.append(url)
                else:
                    unsupported_results.append(ScrapingResult(
                        success=False,
                        error="不支持的招聘网站URL",
                        url=url,
                        scraped_at=datetime.now()
                    ))
            
            if progress_callback and unsupported_results:
                progress_callback(f"过滤掉 {len(unsupported_results)} 个不支持的URL", 0.1)
            
            # 执行批量爬取
            if supported_urls:
                if progress_callback:
                    progress_callback("正在并发爬取支持的URL...", 0.2)
                
                scraping_results = await orchestrator.scrape_multiple_jobs(supported_urls)
                
                # 保存成功的结果到数据库
                saved_count = 0
                for i, result in enumerate(scraping_results):
                    if result.success and result.job:
                        try:
                            job_info = self._convert_to_job_info(result.job, result.url)
                            await self.db_manager.save_job(job_info)
                            saved_count += 1
                        except Exception as e:
                            self.logger.error(f"保存职位失败: {e}")
                            result.success = False
                            result.error = f"保存失败: {str(e)}"
                    
                    if progress_callback:
                        progress = 0.2 + 0.7 * (i + 1) / len(scraping_results)
                        progress_callback(f"已处理 {i + 1}/{len(scraping_results)} 个URL", progress)
                
                if progress_callback:
                    progress_callback(f"完成！成功保存 {saved_count} 个职位", 1.0)
                
                # 合并结果
                all_results = scraping_results + unsupported_results
                
            else:
                all_results = unsupported_results
                if progress_callback:
                    progress_callback("没有支持的URL需要处理", 1.0)
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"批量爬取过程出错: {e}")
            # 返回错误结果
            return [ScrapingResult(
                success=False,
                error=f"批量爬取出错: {str(e)}",
                url=url,
                scraped_at=datetime.now()
            ) for url in urls]
    
    def scrape_multiple_jobs_sync(
        self, 
        urls: List[str], 
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[ScrapingResult]:
        """同步批量爬取职位（Streamlit兼容）"""
        # 转换配置
        scraping_config = None
        if config:
            scraping_config = get_scraping_config(**config)
        
        # 运行异步函数
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果事件循环正在运行，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.scrape_multiple_jobs_async(urls, scraping_config, progress_callback)
                )
                return future.result()
        else:
            return loop.run_until_complete(
                self.scrape_multiple_jobs_async(urls, scraping_config, progress_callback)
            )
    
    def _convert_to_job_info(self, job: Any, url: str) -> JobInfo:
        """将爬取的Job对象转换为JobInfo数据模型"""
        return JobInfo(
            url=url,
            title=getattr(job, 'title', ''),
            company=getattr(job, 'company', ''),
            description=getattr(job, 'description', ''),
            requirements=getattr(job, 'requirements', ''),
            skills=getattr(job, 'skills', []),
            location=getattr(job, 'location', ''),
            salary_range=getattr(job, 'salary_range', ''),
            salary_min=getattr(job, 'salary_min', None),
            salary_max=getattr(job, 'salary_max', None),
            experience_min=getattr(job, 'experience_min', None),
            experience_max=getattr(job, 'experience_max', None),
            education=getattr(job, 'education', ''),
            company_info=getattr(job, 'company_info', ''),
            published_time=getattr(job, 'published_time', ''),
            source=getattr(job, 'source', 'unknown'),
            crawled_at=datetime.now()
        )
    
    def get_supported_sites(self) -> List[Dict[str, str]]:
        """获取支持的招聘网站列表"""
        orchestrator = self._get_orchestrator()
        sites_info = []
        
        for site in SiteSupport:
            site_info = {
                'value': site.value,
                'name': self._get_site_display_name(site.value),
                'example_url': self._get_site_example_url(site.value),
                'status': 'available' if site.value in orchestrator.multi_scraper.scrapers else 'unavailable'
            }
            sites_info.append(site_info)
        
        return sites_info
    
    def _get_site_display_name(self, site_value: str) -> str:
        """获取网站显示名称"""
        name_mapping = {
            'boss': 'BOSS直聘',
            'lagou': '拉勾网',
            'zhilian': '智联招聘',
            'liepin': '猎聘网',
            '51job': '前程无忧'
        }
        return name_mapping.get(site_value, site_value.upper())
    
    def _get_site_example_url(self, site_value: str) -> str:
        """获取网站示例URL"""
        example_mapping = {
            'boss': 'https://www.zhipin.com/job_detail/123456.html',
            'lagou': 'https://www.lagou.com/jobs/123456.html',
            'zhilian': 'https://jobs.zhaopin.com/123456.htm',
            'liepin': 'https://www.liepin.com/job/123456.shtml',
            '51job': 'https://jobs.51job.com/123456.html'
        }
        return example_mapping.get(site_value, '')
    
    def is_url_supported(self, url: str) -> bool:
        """检查URL是否被支持"""
        orchestrator = self._get_orchestrator()
        return orchestrator.is_url_supported(url)
    
    def get_performance_stats(self) -> Optional[Dict[str, Any]]:
        """获取爬虫性能统计"""
        if self.orchestrator:
            return self.orchestrator.get_performance_stats()
        return None
    
    async def health_check_async(self) -> Dict[str, Any]:
        """异步健康检查"""
        orchestrator = self._get_orchestrator()
        return await orchestrator.health_check()
    
    def health_check_sync(self) -> Dict[str, Any]:
        """同步健康检查（Streamlit兼容）"""
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.health_check_async())
                return future.result()
        else:
            return loop.run_until_complete(self.health_check_async())
    
    def cleanup(self):
        """清理资源"""
        if self.orchestrator:
            self.orchestrator.cleanup()
            self.orchestrator = None
            self._current_config = None


# Streamlit 集成助手函数
def create_scraping_config_from_ui() -> ScrapingConfig:
    """从Streamlit UI创建爬虫配置"""
    with st.expander("🔧 爬虫配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            headless = st.checkbox("无头模式", value=False, help="开启后浏览器在后台运行，关闭后可以看到浏览器窗口")
            max_retries = st.number_input("最大重试次数", min_value=1, max_value=10, value=3)
            concurrent_limit = st.number_input("并发限制", min_value=1, max_value=10, value=3)
        
        with col2:
            timeout = st.number_input("超时时间(秒)", min_value=10, max_value=120, value=30)
            enable_monitoring = st.checkbox("性能监控", value=True, help="记录爬取性能统计信息")
            data_validation = st.checkbox("数据验证", value=True, help="对爬取的数据进行质量检查")
    
    return ScrapingConfig(
        headless=headless,
        max_retries=max_retries,
        concurrent_limit=concurrent_limit,
        timeout=timeout,
        enable_monitoring=enable_monitoring,
        data_validation=data_validation
    )


def display_scraping_result(result: ScrapingResult):
    """显示爬取结果"""
    if result.success and result.job:
        st.success(f"✅ 成功爬取: {result.job.title}")
        
        with st.expander("查看职位详情", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**公司**: {result.job.company}")
                st.write(f"**地点**: {getattr(result.job, 'location', '未知')}")
                st.write(f"**薪资**: {getattr(result.job, 'salary_range', '面议')}")
            
            with col2:
                st.write(f"**经验**: {getattr(result.job, 'experience_min', 0)}-{getattr(result.job, 'experience_max', 0)}年")
                st.write(f"**学历**: {getattr(result.job, 'education', '不限')}")
                st.write(f"**来源**: {getattr(result.job, 'source', 'unknown')}")
            
            if hasattr(result.job, 'skills') and result.job.skills:
                st.write("**技能要求**:")
                skills_text = " | ".join(result.job.skills[:10])  # 限制显示数量
                st.text(skills_text)
            
            if hasattr(result.job, 'description') and result.job.description:
                st.write("**职位描述**:")
                st.text_area("", value=result.job.description[:500] + "..." if len(result.job.description) > 500 else result.job.description, height=150, disabled=True)
    
    else:
        st.error(f"❌ 爬取失败: {result.error}")


def display_batch_results(results: List[ScrapingResult]):
    """显示批量爬取结果"""
    if not results:
        st.warning("没有爬取结果")
        return
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总数", len(results))
    
    with col2:
        st.metric("成功", len(successful), delta=f"{len(successful)/len(results)*100:.1f}%")
    
    with col3:
        st.metric("失败", len(failed), delta=f"{len(failed)/len(results)*100:.1f}%" if failed else None)
    
    # 成功结果
    if successful:
        st.subheader("✅ 成功爬取的职位")
        for result in successful:
            with st.expander(f"{result.job.title} - {result.job.company}"):
                display_scraping_result(result)
    
    # 失败结果
    if failed:
        st.subheader("❌ 爬取失败的URL")
        for result in failed:
            st.error(f"{result.url}: {result.error}")


def display_performance_stats(stats: Optional[Dict[str, Any]]):
    """显示性能统计"""
    if not stats:
        st.info("暂无性能统计数据")
        return
    
    st.subheader("📊 爬虫性能统计")
    
    # 总体统计
    overall = stats.get('overall', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总尝试次数", overall.get('total_attempts', 0))
    
    with col2:
        st.metric("成功率", overall.get('success_rate', '0%'))
    
    with col3:
        st.metric("平均响应时间", overall.get('average_response_time', '0s'))
    
    with col4:
        st.metric("成功次数", overall.get('successful_scrapes', 0))
    
    # 按网站统计
    by_site = stats.get('by_site', {})
    if by_site:
        st.subheader("按网站统计")
        
        for site, site_stats in by_site.items():
            with st.expander(f"📈 {site.upper()} 统计"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("尝试次数", site_stats.get('attempts', 0))
                
                with col2:
                    st.metric("成功率", site_stats.get('success_rate', '0%'))
                
                with col3:
                    st.metric("平均响应时间", site_stats.get('avg_response_time', '0s'))
                
                if site_stats.get('last_success'):
                    st.text(f"最后成功: {site_stats['last_success']}")
                
                if site_stats.get('last_failure'):
                    st.text(f"最后失败: {site_stats['last_failure']}")