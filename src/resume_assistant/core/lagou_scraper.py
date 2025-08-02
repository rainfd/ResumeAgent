"""拉勾网职位爬虫

专门用于爬取拉勾网(lagou.com)的职位信息，包含针对该网站特性的优化。
"""

import re
import time
import json
import random
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING_SUPPORT = True
except ImportError:
    HAS_SCRAPING_SUPPORT = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT_SUPPORT = True
except ImportError:
    HAS_PLAYWRIGHT_SUPPORT = False

from ..utils import get_logger
from ..utils.errors import NetworkError, ResumeAssistantError
from .scraper import JobScraper, ScrapingResult
from .job_manager import Job

logger = get_logger(__name__)


class LagouScraper(JobScraper):
    """拉勾网职位爬虫"""
    
    def __init__(self, headless: bool = False):
        """初始化拉勾网爬虫
        
        Args:
            headless: 是否使用无头模式
        """
        if not HAS_PLAYWRIGHT_SUPPORT:
            raise ResumeAssistantError("Playwright依赖库未安装。请安装: pip install playwright")
        
        self.logger = get_logger(self.__class__.__name__)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        
        # 拉勾网特有的请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _setup_browser(self):
        """设置浏览器"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
        
        # 浏览器启动参数
        launch_args = [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate'
        ]
        
        if not self.headless:
            self.logger.info("启动有头浏览器模式（拉勾网专用）")
        
        # 创建浏览器
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        
        # 创建上下文
        self.context = self.browser.new_context(
            user_agent=self.headers['User-Agent'],
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers=self.headers
        )
        
        # 创建页面
        self.page = self.context.new_page()
        
        # 拉勾网特有的反检测设置
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' }),
                }),
            });
        """)
    
    def _validate_lagou_url(self, url: str) -> bool:
        """验证是否为有效的拉勾网职位URL"""
        try:
            parsed = urlparse(url)
            return 'lagou.com' in parsed.netloc.lower() and '/jobs/' in parsed.path
        except Exception:
            return False
    
    def _extract_job_id(self, url: str) -> Optional[str]:
        """从URL中提取职位ID"""
        try:
            # 拉勾网职位URL格式: https://www.lagou.com/jobs/123456.html
            match = re.search(r'/jobs/(\d+)\.html', url)
            if match:
                return match.group(1)
                
            # API格式: https://www.lagou.com/jobs/123456
            match = re.search(r'/jobs/(\d+)$', url)
            if match:
                return match.group(1)
                
        except Exception as e:
            self.logger.error(f"提取职位ID失败: {e}")
        
        return None
    
    def _simulate_human_behavior(self):
        """模拟人类浏览行为"""
        try:
            # 随机滚动
            scroll_count = random.randint(2, 4)
            for _ in range(scroll_count):
                scroll_distance = random.randint(300, 800)
                self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                time.sleep(random.uniform(0.5, 1.5))
            
            # 随机鼠标移动
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1000)
                y = random.randint(100, 600)
                self.page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # 模拟阅读时间
            time.sleep(random.uniform(2.0, 5.0))
            
        except Exception as e:
            self.logger.warning(f"模拟人类行为时出错: {e}")
    
    def _check_anti_robot(self, content: str) -> bool:
        """检查是否触发了反爬验证"""
        anti_robot_indicators = [
            '请输入验证码',
            '人机验证',
            '安全验证',
            'robot',
            'captcha',
            '访问过于频繁',
            '请稍后再试'
        ]
        
        content_lower = content.lower()
        for indicator in anti_robot_indicators:
            if indicator.lower() in content_lower:
                return True
        
        return False
    
    def _wait_for_manual_verification(self):
        """等待用户手动处理验证"""
        print("\n" + "="*50)
        print("🚨 拉勾网检测到需要人工验证！")
        print("请在浏览器中完成以下操作：")
        print("1. 完成人机验证/验证码")
        print("2. 如需登录，请完成登录")
        print("3. 确保页面正常显示职位信息")
        print("4. 完成后请在此处按 Enter 继续...")
        print("="*50)
        
        input("等待手动验证完成，按 Enter 继续...")
        
        # 给用户一些时间完成操作
        time.sleep(2)
    
    def _extract_job_info(self, job_id: str) -> Optional[Job]:
        """从页面提取职位信息"""
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # 获取页面内容
            content = self.page.content()
            
            # 检查是否需要验证
            if self._check_anti_robot(content):
                self.logger.warning("检测到反爬验证，需要人工处理")
                self._wait_for_manual_verification()
                content = self.page.content()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取职位信息
            job = Job()
            
            # 职位标题
            title_elem = soup.find('span', class_='name') or soup.find('h1', class_='position-head-wrap-name')
            if title_elem:
                job.title = title_elem.get_text(strip=True)
            
            # 公司名称
            company_elem = soup.find('a', class_='b2') or soup.find('h2', class_='fl')
            if company_elem:
                job.company = company_elem.get_text(strip=True)
            
            # 薪资信息
            salary_elem = soup.find('span', class_='salary') or soup.find('span', class_='position-head-wrap-salary')
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                job.salary_range = salary_text
                
                # 解析薪资范围
                salary_match = re.search(r'(\d+)[kK]?[-~](\d+)[kK]?', salary_text)
                if salary_match:
                    job.salary_min = int(salary_match.group(1)) * 1000
                    job.salary_max = int(salary_match.group(2)) * 1000
            
            # 工作地点
            location_elem = soup.find('input', {'name': 'positionAddress'})
            if location_elem:
                job.location = location_elem.get('value', '').strip()
            else:
                # 备用方法
                location_elem = soup.find('span', class_='add') or soup.find('em', class_='add')
                if location_elem:
                    job.location = location_elem.get_text(strip=True)
            
            # 工作经验要求
            exp_elem = soup.find('dd', class_='job_request')
            if exp_elem:
                exp_text = exp_elem.get_text()
                exp_match = re.search(r'(\d+)[-~](\d+)年', exp_text)
                if exp_match:
                    job.experience_min = int(exp_match.group(1))
                    job.experience_max = int(exp_match.group(2))
                elif '经验不限' in exp_text:
                    job.experience_min = 0
                    job.experience_max = 0
            
            # 学历要求
            edu_elem = soup.find('dd', class_='job_request')
            if edu_elem:
                edu_text = edu_elem.get_text()
                if '本科' in edu_text:
                    job.education = '本科'
                elif '硕士' in edu_text:
                    job.education = '硕士'
                elif '大专' in edu_text:
                    job.education = '大专'
                elif '博士' in edu_text:
                    job.education = '博士'
                elif '学历不限' in edu_text:
                    job.education = '不限'
            
            # 职位描述
            desc_elem = soup.find('dd', class_='job_bt') or soup.find('div', class_='job_bt')
            if desc_elem:
                # 移除HTML标签，保留换行
                desc_text = desc_elem.get_text(separator='\n', strip=True)
                job.description = desc_text
            
            # 技能要求（从职位描述中提取）
            if job.description:
                job.skills = self._extract_skills_from_description(job.description)
            
            # 公司信息
            company_info_elem = soup.find('ul', class_='c_feature')
            if company_info_elem:
                company_features = []
                for li in company_info_elem.find_all('li'):
                    feature = li.get_text(strip=True)
                    if feature:
                        company_features.append(feature)
                job.company_info = ' | '.join(company_features)
            
            # 发布时间
            time_elem = soup.find('span', class_='time') or soup.find('time')
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                job.published_time = time_text
            
            # 设置来源
            job.source = 'lagou'
            job.crawled_at = datetime.now()
            
            # 验证必要字段
            if not job.title or not job.company:
                self.logger.warning("职位信息不完整，可能页面结构已变化")
                return None
            
            self.logger.info(f"成功提取拉勾网职位: {job.title} - {job.company}")
            return job
            
        except Exception as e:
            self.logger.error(f"提取职位信息失败: {e}")
            return None
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """从职位描述中提取技能关键词"""
        # 常见技能关键词
        skill_patterns = [
            r'\b(Java|Python|JavaScript|TypeScript|C\+\+|C#|Go|PHP|Ruby|Scala|Kotlin)\b',
            r'\b(React|Vue|Angular|Spring|Django|Flask|Node\.js|Express)\b',
            r'\b(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Kafka)\b',
            r'\b(Docker|Kubernetes|Jenkins|Git|Linux|AWS|Azure)\b',
            r'\b(HTML|CSS|SASS|LESS|Webpack|Babel)\b',
            r'\b(机器学习|深度学习|人工智能|数据分析|大数据)\b'
        ]
        
        skills = []
        description_upper = description.upper()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            skills.extend(matches)
        
        # 去重并清理
        skills = list(set(skill.strip() for skill in skills if skill.strip()))
        return skills[:10]  # 限制技能数量
    
    def scrape_job(self, url: str) -> ScrapingResult:
        """爬取拉勾网职位信息"""
        start_time = time.time()
        
        try:
            # 验证URL
            if not self._validate_lagou_url(url):
                return ScrapingResult(
                    success=False,
                    error="不是有效的拉勾网职位URL",
                    url=url,
                    scraped_at=datetime.now()
                )
            
            # 提取职位ID
            job_id = self._extract_job_id(url)
            if not job_id:
                return ScrapingResult(
                    success=False,
                    error="无法从URL中提取职位ID",
                    url=url,
                    scraped_at=datetime.now()
                )
            
            # 设置浏览器
            self._setup_browser()
            
            self.logger.info(f"开始爬取拉勾网职位: {url}")
            
            # 访问职位页面
            self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # 模拟人类行为
            self._simulate_human_behavior()
            
            # 提取职位信息
            job = self._extract_job_info(job_id)
            
            if job:
                job.url = url
                response_time = time.time() - start_time
                
                return ScrapingResult(
                    success=True,
                    job=job,
                    url=url,
                    scraped_at=datetime.now()
                )
            else:
                return ScrapingResult(
                    success=False,
                    error="提取职位信息失败",
                    url=url,
                    scraped_at=datetime.now()
                )
            
        except Exception as e:
            self.logger.error(f"爬取失败: {e}")
            return ScrapingResult(
                success=False,
                error=str(e),
                url=url,
                scraped_at=datetime.now()
            )
        
        finally:
            self.cleanup()
    
    def test_connection(self) -> bool:
        """测试拉勾网连接"""
        try:
            self._setup_browser()
            self.page.goto('https://www.lagou.com', timeout=30000)
            return True
        except Exception as e:
            self.logger.error(f"拉勾网连接测试失败: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.context:
                self.context.close()
                self.context = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")


# 便捷函数
def scrape_lagou_job(url: str, headless: bool = False) -> ScrapingResult:
    """便捷函数：爬取拉勾网职位"""
    scraper = LagouScraper(headless=headless)
    return scraper.scrape_job(url)


def test_lagou_connection(headless: bool = False) -> bool:
    """便捷函数：测试拉勾网连接"""
    scraper = LagouScraper(headless=headless)
    return scraper.test_connection()