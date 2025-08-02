"""网页爬虫模块

提供BOSS直聘等招聘网站的职位信息爬取功能。
"""

import re
import time
import random
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
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
from .job_manager import Job

logger = get_logger(__name__)


@dataclass
class ScrapingResult:
    """爬取结果数据结构"""
    success: bool
    job: Optional[Job] = None
    error: Optional[str] = None
    url: Optional[str] = None
    scraped_at: Optional[datetime] = None


class JobScraper:
    """职位信息爬虫基类"""
    
    def __init__(self):
        """初始化爬虫"""
        if not HAS_SCRAPING_SUPPORT:
            raise ResumeAssistantError("爬虫依赖库未安装。请安装: pip install requests beautifulsoup4")
        
        self.session = requests.Session()
        self._setup_session()
        self.logger = get_logger(self.__class__.__name__)
    
    def _setup_session(self):
        """设置HTTP会话"""
        # 设置用户代理
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 设置超时
        self.session.timeout = 30
    
    def scrape_job(self, url: str) -> ScrapingResult:
        """爬取职位信息
        
        Args:
            url: 职位页面URL
            
        Returns:
            ScrapingResult: 爬取结果
        """
        try:
            # 验证URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ScrapingResult(
                    success=False,
                    error="无效的URL格式",
                    url=url
                )
            
            # 根据域名选择对应的爬虫
            if 'zhipin.com' in parsed_url.netloc:
                return self._scrape_boss_job(url)
            else:
                return ScrapingResult(
                    success=False,
                    error=f"暂不支持的网站: {parsed_url.netloc}",
                    url=url
                )
        
        except Exception as e:
            self.logger.error(f"爬取职位信息失败 {url}: {e}")
            return ScrapingResult(
                success=False,
                error=str(e),
                url=url
            )
    
    def _scrape_boss_job(self, url: str) -> ScrapingResult:
        """爬取BOSS直聘职位信息
        
        Args:
            url: BOSS直聘职位页面URL
            
        Returns:
            ScrapingResult: 爬取结果
        """
        try:
            # 添加随机延时
            time.sleep(random.uniform(1, 3))
            
            # 发送HTTP请求
            response = self._make_request(url)
            if not response:
                return ScrapingResult(
                    success=False,
                    error="请求失败",
                    url=url
                )
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取职位信息
            job_data = self._extract_boss_job_data(soup, url)
            if not job_data:
                return ScrapingResult(
                    success=False,
                    error="未能提取到职位信息",
                    url=url
                )
            
            # 创建Job对象
            job = Job(
                id=job_data.get('id', ''),
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', ''),
                location=job_data.get('location', ''),
                salary=job_data.get('salary', ''),
                experience_level=job_data.get('experience_level', ''),
                education_level=job_data.get('education_level', ''),
                job_type=job_data.get('job_type', ''),
                tags=job_data.get('tags', []),
                company_info=job_data.get('company_info', {}),
                contact_info=job_data.get('contact_info', {}),
                source_url=url,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            return ScrapingResult(
                success=True,
                job=job,
                url=url,
                scraped_at=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"BOSS直聘爬取失败 {url}: {e}")
            return ScrapingResult(
                success=False,
                error=f"爬取失败: {e}",
                url=url
            )
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """发送HTTP请求（带重试机制）
        
        Args:
            url: 请求URL
            max_retries: 最大重试次数
            
        Returns:
            requests.Response: 响应对象，失败返回None
        """
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"请求URL (尝试 {attempt + 1}/{max_retries}): {url}")
                
                response = self.session.get(url)
                response.raise_for_status()
                
                # 检查是否被反爬
                if self._is_blocked_response(response):
                    self.logger.warning(f"疑似被反爬机制拦截: {url}")
                    if attempt < max_retries - 1:
                        # 增加延时后重试
                        time.sleep(random.uniform(3, 8))
                        continue
                    else:
                        return None
                
                return response
            
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                    continue
                else:
                    raise NetworkError(f"请求失败: {e}", url=url)
        
        return None
    
    def _is_blocked_response(self, response: requests.Response) -> bool:
        """检查响应是否被反爬机制拦截
        
        Args:
            response: HTTP响应对象
            
        Returns:
            bool: 是否被拦截
        """
        # 检查常见的反爬标识
        blocked_indicators = [
            "验证码",
            "captcha",
            "robot",
            "blocked",
            "访问受限",
            "请稍后再试"
        ]
        
        response_text = response.text.lower()
        for indicator in blocked_indicators:
            if indicator in response_text:
                return True
        
        # 检查状态码
        if response.status_code in [403, 429, 503]:
            return True
        
        # 检查响应内容长度（过短可能是被拦截）
        if len(response.text.strip()) < 1000:
            return True
        
        return False
    
    def _extract_boss_job_data(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """从BOSS直聘页面提取职位数据
        
        Args:
            soup: BeautifulSoup解析对象
            url: 页面URL
            
        Returns:
            Dict: 职位数据字典，失败返回None
        """
        try:
            job_data = {}
            
            # 生成唯一ID
            import hashlib
            job_data['id'] = hashlib.md5(url.encode()).hexdigest()[:8]
            
            # 提取职位标题
            title_elem = soup.find('h1', class_='name') or soup.find('div', class_='job-title')
            if title_elem:
                job_data['title'] = title_elem.get_text(strip=True)
            
            # 提取公司名称
            company_elem = soup.find('div', class_='company-name') or soup.find('a', class_='company-name')
            if company_elem:
                job_data['company'] = company_elem.get_text(strip=True)
            
            # 提取薪资范围
            salary_elem = soup.find('span', class_='salary') or soup.find('div', class_='job-salary')
            if salary_elem:
                job_data['salary'] = salary_elem.get_text(strip=True)
            
            # 提取工作地点
            location_elem = soup.find('p', class_='job-location') or soup.find('span', class_='job-area')
            if location_elem:
                job_data['location'] = location_elem.get_text(strip=True)
            
            # 提取经验要求
            exp_elem = soup.find('p', class_='job-experience') or soup.find('span', class_='job-experience')
            if exp_elem:
                job_data['experience_level'] = exp_elem.get_text(strip=True)
            
            # 提取学历要求
            edu_elem = soup.find('p', class_='job-degree') or soup.find('span', class_='job-degree')
            if edu_elem:
                job_data['education_level'] = edu_elem.get_text(strip=True)
            
            # 提取职位描述
            desc_elem = soup.find('div', class_='job-sec') or soup.find('div', class_='job-detail')
            if desc_elem:
                job_data['description'] = desc_elem.get_text(strip=True)
                job_data['requirements'] = job_data['description']  # 暂时设为相同
            
            # 提取职位标签
            tags = []
            tag_elems = soup.find_all('span', class_='job-tag') or soup.find_all('div', class_='job-tags')
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            job_data['tags'] = tags
            
            # 提取公司信息
            company_info = {}
            company_size_elem = soup.find('p', class_='company-size')
            if company_size_elem:
                company_info['size'] = company_size_elem.get_text(strip=True)
            
            company_type_elem = soup.find('p', class_='company-type')
            if company_type_elem:
                company_info['type'] = company_type_elem.get_text(strip=True)
            
            job_data['company_info'] = company_info
            
            # 提取联系信息（如果有）
            job_data['contact_info'] = {}
            
            # 设置职位类型
            job_data['job_type'] = '全职'  # 默认值
            
            # 验证必要字段
            if not job_data.get('title') or not job_data.get('company'):
                self.logger.warning("职位标题或公司名称为空")
                return None
            
            return job_data
        
        except Exception as e:
            self.logger.error(f"提取职位数据失败: {e}")
            return None
    
    def test_connection(self, url: str) -> bool:
        """测试网络连接
        
        Args:
            url: 测试URL
            
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False


class BossZhipinScraper(JobScraper):
    """BOSS直聘专用爬虫"""
    
    def __init__(self):
        super().__init__()
        
        # BOSS直聘特定设置
        self.session.headers.update({
            'Referer': 'https://www.zhipin.com/',
            'Host': 'www.zhipin.com'
        })
    
    def scrape_search_results(self, search_url: str, max_pages: int = 3) -> List[ScrapingResult]:
        """爬取搜索结果页面的职位列表
        
        Args:
            search_url: 搜索页面URL
            max_pages: 最大爬取页数
            
        Returns:
            List[ScrapingResult]: 爬取结果列表
        """
        results = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.info(f"爬取第 {page} 页: {search_url}")
                
                # 构造分页URL
                page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
                
                # 获取页面内容
                response = self._make_request(page_url)
                if not response:
                    continue
                
                # 解析页面，提取职位链接
                soup = BeautifulSoup(response.text, 'html.parser')
                job_links = self._extract_job_links(soup)
                
                if not job_links:
                    self.logger.warning(f"第 {page} 页未找到职位链接")
                    break
                
                # 爬取每个职位详情
                for job_link in job_links:
                    full_url = urljoin(search_url, job_link)
                    result = self.scrape_job(full_url)
                    results.append(result)
                    
                    # 添加延时避免被封
                    time.sleep(random.uniform(2, 4))
                
                # 页面间延时
                time.sleep(random.uniform(3, 6))
        
        except Exception as e:
            self.logger.error(f"搜索结果爬取失败: {e}")
        
        return results
    
    def _extract_job_links(self, soup: BeautifulSoup) -> List[str]:
        """从搜索结果页面提取职位链接
        
        Args:
            soup: BeautifulSoup解析对象
            
        Returns:
            List[str]: 职位链接列表
        """
        links = []
        
        try:
            # BOSS直聘职位链接选择器
            job_elements = soup.find_all('a', href=re.compile(r'/job_detail/'))
            
            for elem in job_elements:
                href = elem.get('href')
                if href and href.startswith('/job_detail/'):
                    links.append(href)
            
            # 去重
            links = list(set(links))
            
        except Exception as e:
            self.logger.error(f"提取职位链接失败: {e}")
        
        return links


class PlaywrightScraper(JobScraper):
    """基于Playwright的职位爬虫"""
    
    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        """初始化Playwright爬虫
        
        Args:
            headless: 是否使用无头模式，False为有头模式（更难被检测）
            user_data_dir: 用户数据目录路径，用于保持登录状态
        """
        if not HAS_PLAYWRIGHT_SUPPORT:
            raise ResumeAssistantError("Playwright依赖库未安装。请安装: pip install playwright")
        
        self.logger = get_logger(self.__class__.__name__)
        self.playwright = None
        self.browser = None
        self.context = None
        self.headless = headless
        self.user_data_dir = user_data_dir
    
    def _setup_browser(self):
        """设置浏览器"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
        
        # 浏览器启动参数（增强反检测）
        launch_args = [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-dev-shm-usage',
            '--disable-extensions-except=',
            '--disable-plugins-discovery',
            '--disable-javascript-harmony-shipping',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-device-discovery-notifications',
            '--disable-backgrounding-occluded-windows',
            '--disable-ipc-flooding-protection'
        ]
        
        # 如果不是无头模式，移除一些可能影响显示的参数
        if not self.headless:
            # 移除可能影响显示的参数
            launch_args = [arg for arg in launch_args if 'disable-images' not in arg]
            self.logger.info("启动有头浏览器模式（更难被检测）")
        else:
            # 无头模式添加更多优化参数
            launch_args.extend([
                '--disable-images',  # 禁用图片加载以提高速度
                '--disable-audio-output'
            ])
            
        # 创建浏览器上下文选项
        context_options = {
            'user_agent': self._get_random_user_agent(),
            'viewport': {'width': 1920, 'height': 1080},
            'extra_http_headers': {
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
        }
        
        # 如果指定了用户数据目录，使用持久化上下文
        if self.user_data_dir:
            self.logger.info(f"使用用户数据目录: {self.user_data_dir}")
            # 使用持久化上下文
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                args=launch_args,
                **context_options
            )
            # 持久化上下文本身就是browser和context的组合
            self.browser = None  # 持久化模式下不需要单独的browser对象
        else:
            # 常规模式：先创建browser，再创建context
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            self.context = self.browser.new_context(**context_options)
    
    def _cleanup_browser(self):
        """清理浏览器资源"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.warning(f"清理浏览器资源失败: {e}")
        finally:
            self.context = None
            self.browser = None
            self.playwright = None
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    def _wait_for_manual_verification(self, page, timeout: int = 120) -> bool:
        """等待用户手动处理验证码或登录
        
        Args:
            page: Playwright页面对象
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否成功通过验证
        """
        try:
            if self.headless:
                self.logger.warning("检测到验证码但当前为无头模式，无法手动处理")
                return False
            
            # 显眼的提示信息
            print("\n" + "="*80)
            print("🤖 检测到需要人工验证！")
            print("="*80)
            print("📋 请按以下步骤操作：")
            print("   1. 在打开的浏览器窗口中完成IP验证或人机验证")
            print("   2. 如果出现滑块验证，请拖动滑块到正确位置")
            print("   3. 如果出现验证码，请按提示输入验证码")
            print("   4. 等待页面跳转到正常的职位详情页面")
            print("   5. 不要关闭浏览器窗口，程序会自动检测完成状态")
            print()
            print(f"⏰ 最大等待时间: {timeout} 秒")
            print(f"🌐 当前页面: {page.url}")
            print("💡 提示: 如需取消操作，请关闭浏览器窗口")
            print("="*80)
            
            self.logger.info("等待用户手动完成验证...")
            
            # 等待页面URL变化或特定元素消失，表示用户已处理完验证
            start_time = time.time()
            current_url = page.url
            check_interval = 2  # 缩短检查间隔到2秒，更快响应
            
            # 先等待2秒让用户看到提示
            time.sleep(2)
            
            while time.time() - start_time < timeout:
                try:
                    elapsed = int(time.time() - start_time)
                    remaining = timeout - elapsed
                    
                    # 更频繁显示进度（每10秒）
                    if elapsed % 10 == 0 and elapsed > 0:
                        print(f"⏳ 等待中... ({elapsed}/{timeout}秒) 剩余: {remaining}秒")
                    
                    # 首先快速检查是否不再是验证页面
                    is_still_blocked = self._check_blocked_page(page)
                    
                    if not is_still_blocked:
                        # 验证页面特征消失，确认验证通过
                        print("✅ 验证完成！页面恢复正常")
                        self.logger.info("验证页面特征消失，验证完成")
                        return True
                    
                    # 检查URL是否变化（可能表示跳转）
                    new_url = page.url
                    if new_url != current_url:
                        print(f"🔄 检测到页面跳转: {new_url}")
                        current_url = new_url
                        
                        # 等待新页面稳定
                        time.sleep(2)
                        
                        # 再次检查新页面是否需要验证
                        if not self._check_blocked_page(page):
                            print("✅ 跳转后的页面验证通过！")
                            return True
                        else:
                            print("⚠️ 新页面仍需验证，继续等待...")
                    
                    # 检查浏览器是否已关闭（用户取消操作）
                    try:
                        page.title()  # 尝试访问页面，如果浏览器关闭会抛出异常
                    except Exception:
                        print("🚫 检测到浏览器已关闭，取消验证")
                        return False
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.debug(f"验证状态检查异常: {e}")
                    # 可能是页面正在加载，继续等待
                    time.sleep(check_interval)
            
            print("\n❌ 手动验证超时")
            print("💡 提示: 如果您已完成验证但程序仍然超时，可以:")
            print("   - 尝试刷新页面")
            print("   - 重新运行程序")
            return False
            
        except Exception as e:
            self.logger.error(f"手动验证处理失败: {e}")
            return False
    
    def scrape_job(self, url: str) -> ScrapingResult:
        """使用Playwright爬取职位信息
        
        Args:
            url: 职位页面URL
            
        Returns:
            ScrapingResult: 爬取结果
        """
        try:
            # 验证URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ScrapingResult(
                    success=False,
                    error="无效的URL格式",
                    url=url
                )
            
            # 设置浏览器
            self._setup_browser()
            
            # 创建页面
            page = self.context.new_page()
            
            try:
                self.logger.info(f"使用Playwright访问: {url}")
                
                # 注入增强反检测脚本
                page.add_init_script("""
                    // 隐藏webdriver属性
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // 伪造chrome对象
                    window.chrome = {
                        runtime: {},
                        app: {
                            isInstalled: false,
                        },
                        webstore: {
                            onInstallStageChanged: {},
                            onDownloadProgress: {},
                        },
                    };
                    
                    // 伪造插件数组
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            return [
                                {
                                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                                    description: "Portable Document Format",
                                    filename: "internal-pdf-viewer",
                                    length: 1,
                                    name: "Chrome PDF Plugin"
                                },
                                {
                                    0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                                    description: "",
                                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                    length: 1,
                                    name: "Chrome PDF Viewer"
                                }
                            ];
                        },
                    });
                    
                    // 伪造权限查询
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // 伪造语言和平台
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                    });
                    
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32',
                    });
                    
                    // 移除自动化检测特征
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """)
                
                # 访问页面，等待页面加载
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # 等待一段时间让JavaScript执行
                page.wait_for_timeout(random.uniform(3000, 6000))
                
                # 模拟人类浏览行为
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                page.wait_for_timeout(random.uniform(1000, 2000))
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                page.wait_for_timeout(random.uniform(1000, 2000))
                
                # 首次检查是否需要处理验证码或登录
                verification_detected = self._check_blocked_page(page)
                
                if verification_detected:
                    page_title = page.title()
                    page_url = page.url
                    self.logger.warning(f"检测到验证页面: {page_title} - {page_url}")
                    
                    # 如果是有头模式，尝试等待用户手动处理
                    if not self.headless:
                        print(f"\n🔍 当前页面标题: {page_title}")
                        print(f"🔗 页面URL: {page_url}")
                        
                        # 进入手动验证流程
                        if self._wait_for_manual_verification(page):
                            print("✅ 手动验证完成，继续爬取")
                            self.logger.info("手动验证完成，继续爬取")
                            
                            # 验证完成后再次等待页面稳定
                            page.wait_for_timeout(3000)
                        else:
                            print("❌ 验证处理失败或超时")
                            return ScrapingResult(
                                success=False,
                                error="验证码处理失败或超时",
                                url=url
                            )
                    else:
                        return ScrapingResult(
                            success=False,
                            error="页面被拦截需要验证，建议使用有头模式",
                            url=url
                        )
                else:
                    # 没有检测到验证，记录正常访问
                    self.logger.info(f"页面正常访问，无需验证: {page.title()}")
                
                # 获取页面HTML内容
                html_content = page.content()
                
                # 使用BeautifulSoup解析
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 根据网站类型提取信息
                if 'zhipin.com' in parsed_url.netloc:
                    job_data = self._extract_boss_job_data_playwright(soup, page, url)
                else:
                    job_data = self._extract_generic_job_data(soup, url)
                
                if not job_data:
                    return ScrapingResult(
                        success=False,
                        error="未能提取到职位信息",
                        url=url
                    )
                
                # 创建Job对象
                job = Job(
                    id=job_data.get('id', ''),
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    description=job_data.get('description', ''),
                    requirements=job_data.get('requirements', ''),
                    location=job_data.get('location', ''),
                    salary=job_data.get('salary', ''),
                    experience_level=job_data.get('experience_level', ''),
                    education_level=job_data.get('education_level', ''),
                    job_type=job_data.get('job_type', ''),
                    tags=job_data.get('tags', []),
                    company_info=job_data.get('company_info', {}),
                    contact_info=job_data.get('contact_info', {}),
                    source_url=url,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                return ScrapingResult(
                    success=True,
                    job=job,
                    url=url,
                    scraped_at=datetime.now()
                )
                
            finally:
                page.close()
                
        except Exception as e:
            self.logger.error(f"Playwright爬取失败 {url}: {e}")
            return ScrapingResult(
                success=False,
                error=f"爬取失败: {e}",
                url=url
            )
        finally:
            self._cleanup_browser()
    
    def _check_blocked_page(self, page) -> bool:
        """检查页面是否被拦截"""
        try:
            # 获取页面基本信息
            title = page.title().lower()
            url = page.url.lower()
            
            # 检查是否是明确的验证页面标题
            verification_titles = [
                '安全验证',
                '人机验证', 
                '滑块验证',
                '验证码验证',
                'security verification',
                'captcha verification',
                '请完成验证'
            ]
            
            # 排除职位相关的标题
            job_indicators = ['工程师', '专家', '岗位', '职位', '招聘', '-', '公司']
            is_job_page = any(indicator in title for indicator in job_indicators)
            
            if not is_job_page:  # 只有在不是职位页面时才检查验证标题
                for verification_title in verification_titles:
                    if verification_title in title:
                        self.logger.info(f"检测到验证页面标题: {title}")
                        return True
            
            # 检查URL是否包含验证相关路径
            verification_urls = [
                '/captcha/',
                '/verification/',
                '/security/',
                '/verify',
                '/challenge'
            ]
            
            for verification_url in verification_urls:
                if verification_url in url:
                    self.logger.info(f"检测到验证页面URL: {url}")
                    return True
            
            # 检查页面内容中的验证元素
            try:
                # 先检查是否是职位页面 - 如果是职位页面，则不太可能是验证页面
                job_page_indicators = [
                    '.job-detail',
                    '.job-name',  
                    '.job-title',
                    '.position-detail',
                    '.company-info',
                    '.salary-info',
                    '[class*="job-"]',
                    '.boss-info'
                ]
                
                is_job_page = False
                for indicator in job_page_indicators:
                    if page.query_selector(indicator):
                        is_job_page = True
                        break
                
                # 如果确定是职位页面，则不检查验证元素（避免误判）
                if is_job_page:
                    self.logger.debug("检测到职位页面，跳过验证元素检查")
                    return False
                
                # 检查是否存在验证码相关的特定元素（更严格的选择器）
                verification_selectors = [
                    '.captcha-container',
                    '.verification-container', 
                    '.slide-verify',
                    '.geetest_captcha',  # 更具体的极验验证
                    '.yidun_panel',  # 网易云盾验证
                    '.nc_wrapper',  # 阿里云滑块验证
                    'div[class*="verify"]',  # 验证相关div
                    'form[class*="verify"]'  # 验证相关表单
                ]
                
                for selector in verification_selectors: 
                    element = page.query_selector(selector)
                    if element and element.is_visible():  # 确保元素可见
                        self.logger.info(f"检测到验证元素: {selector}")
                        return True
                
                # 检查特定的验证文本（更精确）
                body_text = page.inner_text('body') if page.query_selector('body') else ''
                
                # 只检查明确的验证提示文本
                specific_verification_texts = [
                    '请拖动滑块完成验证',
                    '点击按钮进行验证',
                    '请点击完成验证',
                    '安全验证中',
                    '人机身份验证',
                    '请输入验证码',
                    '验证失败，请重试',
                    '为了保护账号安全'
                ]
                
                for verification_text in specific_verification_texts:
                    if verification_text in body_text:
                        self.logger.info(f"检测到验证文本: {verification_text}")
                        return True
                
                # 检查页面内容长度，验证页面通常内容较少且包含特定验证词汇
                if len(body_text.strip()) < 200:
                    verification_indicators = ['请完成验证', '人机验证', '安全验证', '滑块验证', '验证码']
                    if any(indicator in body_text for indicator in verification_indicators):
                        self.logger.info(f"检测到简短的验证页面内容: {len(body_text)} 字符")
                        return True
                    
            except Exception as e:
                self.logger.debug(f"验证元素检查失败: {e}")
            
            return False
            
        except Exception as e:
            self.logger.warning(f"检查页面拦截状态失败: {e}")
            return False
    
    def _extract_boss_job_data_playwright(self, soup: BeautifulSoup, page, url: str) -> Optional[Dict[str, Any]]:
        """从BOSS直聘页面提取职位数据（Playwright版本）"""
        try:
            job_data = {}
            
            # 生成唯一ID
            import hashlib
            job_data['id'] = hashlib.md5(url.encode()).hexdigest()[:8]
            
            # 尝试使用更精确的选择器
            selectors = {
                'title': [
                    '.job-title',
                    '.job-name', 
                    'h1.name',
                    '[class*="job"][class*="title"]',
                    'h1',
                    '.position-head h1'
                ],
                'company': [
                    '.company-name a',
                    '.company-name',
                    '[class*="company"][class*="name"]',
                    '.info-company h3',
                    '.company-info .name'
                ],
                'salary': [
                    '.salary',
                    '.job-salary',
                    '[class*="salary"]',
                    '.position-salary'
                ],
                'location': [
                    '.job-area',
                    '.job-location', 
                    '[class*="location"]',
                    '.position-location'
                ],
                'experience': [
                    '.job-experience',
                    '[class*="experience"]',
                    '.position-require'
                ],
                'education': [
                    '.job-degree',
                    '[class*="degree"]',
                    '[class*="education"]'
                ]
            }
            
            # 提取基本信息
            for field, selector_list in selectors.items():
                for selector in selector_list:
                    try:
                        element = soup.select_one(selector)
                        if element:
                            text = element.get_text(strip=True)
                            if text:
                                if field == 'title':
                                    job_data['title'] = text
                                elif field == 'company': 
                                    job_data['company'] = text
                                elif field == 'salary':
                                    job_data['salary'] = text
                                elif field == 'location':
                                    job_data['location'] = text
                                elif field == 'experience':
                                    job_data['experience_level'] = text
                                elif field == 'education':
                                    job_data['education_level'] = text
                                break
                    except Exception:
                        continue
            
            # 提取职位描述
            desc_selectors = [
                '.job-sec',
                '.job-detail', 
                '.job-description',
                '[class*="job"][class*="desc"]',
                '.position-detail'
            ]
            
            for selector in desc_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        description = element.get_text(strip=True)
                        if description and len(description) > 50:  # 确保不是空内容
                            job_data['description'] = description
                            job_data['requirements'] = description  # 暂时设为相同
                            break
                except Exception:
                    continue
            
            # 提取职位标签
            tags = []
            tag_selectors = ['.job-tag', '.position-tag', '[class*="tag"]']
            
            for selector in tag_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        tag_text = elem.get_text(strip=True)
                        if tag_text and tag_text not in tags:
                            tags.append(tag_text)
                except Exception:
                    continue
            
            job_data['tags'] = tags
            job_data['company_info'] = {}
            job_data['contact_info'] = {}
            job_data['job_type'] = '全职'
            
            # 验证必要字段
            if not job_data.get('title'):
                # 尝试从页面标题提取
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text()
                    # 从标题中提取职位名称（通常格式为"职位名-公司名-BOSS直聘"）
                    if '-' in title_text:
                        job_data['title'] = title_text.split('-')[0].strip()
            
            if not job_data.get('company'):
                # 尝试从URL或其他地方提取公司信息
                job_data['company'] = '未知公司'
            
            # 确保有基本信息
            if not job_data.get('title') or not job_data.get('company'):
                self.logger.warning("关键职位信息缺失")
                return None
            
            # 设置默认值
            job_data.setdefault('description', '职位描述暂无')
            job_data.setdefault('requirements', '职位要求暂无')
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Playwright提取职位数据失败: {e}")
            return None
    
    def _extract_generic_job_data(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """通用职位数据提取"""
        try:
            import hashlib
            job_data = {
                'id': hashlib.md5(url.encode()).hexdigest()[:8],
                'title': '未知职位',
                'company': '未知公司',
                'description': '职位描述暂无',
                'requirements': '职位要求暂无',
                'tags': [],
                'company_info': {},
                'contact_info': {},
                'job_type': '全职'
            }
            
            # 尝试从页面标题提取信息
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text()
                job_data['title'] = title_text.split('-')[0].strip() if '-' in title_text else title_text
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"通用数据提取失败: {e}")
            return None


def create_scraper(site: str = 'boss', use_playwright: bool = True, 
                  headless: bool = False, user_data_dir: Optional[str] = None) -> JobScraper:
    """创建爬虫实例
    
    Args:
        site: 网站类型 ('boss', 'generic')
        use_playwright: 是否使用Playwright（默认True）
        headless: 是否使用无头模式（默认False，有头模式更难被检测）
        user_data_dir: 用户数据目录路径，用于保持登录状态
        
    Returns:
        JobScraper: 爬虫实例
    """
    if use_playwright and HAS_PLAYWRIGHT_SUPPORT:
        return PlaywrightScraper(headless=headless, user_data_dir=user_data_dir)
    elif site.lower() == 'boss':
        return BossZhipinScraper()
    else:
        return JobScraper()


# 示例用法
if __name__ == "__main__":
    scraper = create_scraper('boss')
    
    # 测试单个职位爬取
    test_url = "https://www.zhipin.com/job_detail/xxx.html"
    result = scraper.scrape_job(test_url)
    
    if result.success:
        print(f"爬取成功: {result.job.title} @ {result.job.company}")
    else:
        print(f"爬取失败: {result.error}")