# Resume Assistant 增强爬虫模块使用指南

## 概述

本文档介绍了 Resume Assistant 中增强的网页爬虫模块，该模块支持多个招聘网站的职位信息爬取，具备先进的反检测机制、性能监控和错误处理功能。

## 功能特性

### 🌐 多站点支持
- **BOSS直聘** (zhipin.com) - 完全支持
- **拉勾网** (lagou.com) - 新增支持
- **智联招聘** (zhaopin.com) - 计划中
- **猎聘网** (liepin.com) - 计划中
- **前程无忧** (51job.com) - 计划中

### 🛡️ 反检测机制
- 智能用户代理轮换
- 动态延迟计算
- 人类行为模拟
- IP验证处理
- 请求频率控制

### 📊 性能监控
- 实时爬取统计
- 成功率监控
- 响应时间追踪
- 按网站分类统计
- 性能报告生成

### 🔧 配置管理
- 灵活的爬虫配置
- 并发控制
- 重试机制
- 数据验证
- 超时设置

## 快速开始

### 基本使用

```python
from src.resume_assistant.core.scraping_orchestrator import scrape_job_url

# 爬取单个职位
result = await scrape_job_url("https://www.zhipin.com/job_detail/123456.html")

if result.success:
    print(f"成功爬取: {result.job.title} - {result.job.company}")
else:
    print(f"爬取失败: {result.error}")
```

### 批量爬取

```python
from src.resume_assistant.core.scraping_orchestrator import scrape_job_urls

urls = [
    "https://www.zhipin.com/job_detail/123456.html",
    "https://www.lagou.com/jobs/789012.html"
]

results = await scrape_job_urls(urls)

for result in results:
    if result.success:
        print(f"✅ {result.job.title}")
    else:
        print(f"❌ {result.url}: {result.error}")
```

### 自定义配置

```python
from src.resume_assistant.core.scraping_orchestrator import (
    ScrapingOrchestrator, get_scraping_config
)

# 创建自定义配置
config = get_scraping_config(
    headless=False,          # 显示浏览器窗口
    max_retries=5,           # 最大重试5次
    concurrent_limit=2,      # 并发限制2个
    enable_monitoring=True   # 启用性能监控
)

# 使用配置创建协调器
orchestrator = ScrapingOrchestrator(config)

# 爬取职位
result = await orchestrator.scrape_single_job(url)
```

## 详细API文档

### ScrapingOrchestrator

主要的爬虫协调器类，提供统一的爬虫接口。

#### 方法

##### `scrape_single_job(url: str) -> ScrapingResult`
爬取单个职位URL

**参数:**
- `url`: 职位页面URL

**返回:** `ScrapingResult` 对象

**示例:**
```python
orchestrator = ScrapingOrchestrator()
result = await orchestrator.scrape_single_job(url)
```

##### `scrape_multiple_jobs(urls: List[str]) -> List[ScrapingResult]`
并发爬取多个职位URL

**参数:**
- `urls`: 职位URL列表

**返回:** `ScrapingResult` 对象列表

**示例:**
```python
results = await orchestrator.scrape_multiple_jobs(urls)
```

##### `get_supported_sites() -> List[str]`
获取支持的招聘网站列表

##### `is_url_supported(url: str) -> bool`
检查URL是否被支持

##### `get_performance_stats() -> Dict[str, Any]`
获取性能统计信息

##### `health_check() -> Dict[str, Any]`
执行健康检查

### ScrapingConfig

爬虫配置类，用于自定义爬虫行为。

#### 参数

- `max_retries: int = 3` - 最大重试次数
- `retry_delay: float = 2.0` - 重试延迟时间（秒）
- `timeout: int = 30` - 请求超时时间（秒）
- `concurrent_limit: int = 3` - 并发限制
- `use_proxy: bool = False` - 是否使用代理
- `proxy_pool: List[str] = []` - 代理池
- `enable_monitoring: bool = True` - 是否启用监控
- `data_validation: bool = True` - 是否启用数据验证
- `headless: bool = False` - 是否使用无头模式
- `user_data_dir: Optional[str] = None` - 用户数据目录

### ScrapingResult

爬取结果类，包含爬取的状态和数据。

#### 属性

- `success: bool` - 是否成功
- `job: Optional[Job]` - 职位对象（成功时）
- `error: Optional[str]` - 错误信息（失败时）
- `url: Optional[str]` - 原始URL
- `scraped_at: Optional[datetime]` - 爬取时间

## Streamlit Web界面集成

### EnhancedJobAdapter

增强的职位管理Web适配器，提供Streamlit友好的接口。

```python
from src.resume_assistant.web.enhanced_job_adapter import EnhancedJobAdapter

# 创建适配器
adapter = EnhancedJobAdapter(db_manager)

# 同步爬取（Streamlit兼容）
result = adapter.scrape_single_job_sync(url, config={
    'headless': False,
    'max_retries': 3
})

# 批量爬取
results = adapter.scrape_multiple_jobs_sync(urls)

# 获取支持的网站
sites = adapter.get_supported_sites()

# 性能统计
stats = adapter.get_performance_stats()
```

### UI 助手函数

```python
from src.resume_assistant.web.enhanced_job_adapter import (
    create_scraping_config_from_ui,
    display_scraping_result,
    display_batch_results,
    display_performance_stats
)

# 从UI创建配置
config = create_scraping_config_from_ui()

# 显示爬取结果
display_scraping_result(result)

# 显示批量结果
display_batch_results(results)

# 显示性能统计
display_performance_stats(stats)
```

## 具体网站使用

### BOSS直聘

**支持的URL格式:**
- `https://www.zhipin.com/job_detail/123456.html`

**特性:**
- 完整的反检测机制
- IP验证自动处理
- 完整的职位信息提取

**使用示例:**
```python
url = "https://www.zhipin.com/job_detail/123456.html"
result = await scrape_job_url(url)
```

### 拉勾网

**支持的URL格式:**
- `https://www.lagou.com/jobs/123456.html`
- `https://www.lagou.com/jobs/123456`

**特性:**
- 针对拉勾网的专门优化
- 智能技能提取
- 公司信息解析

**使用示例:**
```python
from src.resume_assistant.core.lagou_scraper import scrape_lagou_job

url = "https://www.lagou.com/jobs/123456.html"
result = scrape_lagou_job(url, headless=False)
```

## 性能优化建议

### 1. 并发控制

根据网站的承受能力调整并发数量：
- BOSS直聘：建议并发不超过3
- 拉勾网：建议并发不超过2

```python
config = ScrapingConfig(concurrent_limit=2)
```

### 2. 延迟设置

适当的延迟可以避免被检测：
- 高频爬取：1-3秒延迟
- 常规爬取：2-5秒延迟

```python
config = ScrapingConfig(retry_delay=3.0)
```

### 3. 错误处理

设置合理的重试次数：
- 网络不稳定：增加重试次数
- 目标网站稳定：减少重试次数

```python
config = ScrapingConfig(max_retries=5)
```

### 4. 资源管理

及时清理浏览器资源：

```python
orchestrator = ScrapingOrchestrator()
try:
    result = await orchestrator.scrape_single_job(url)
finally:
    orchestrator.cleanup()  # 重要：清理资源
```

## 错误处理

### 常见错误及解决方案

#### 1. 网络连接错误
```
错误: 网络连接超时
解决: 增加超时时间或检查网络连接
```

#### 2. 反爬验证
```
错误: 检测到人机验证
解决: 使用有头模式，手动完成验证
```

#### 3. 页面结构变化
```
错误: 无法提取职位信息
解决: 检查目标网站是否更新了页面结构
```

#### 4. 浏览器启动失败
```
错误: Playwright浏览器启动失败
解决: 确保已安装playwright浏览器
```

安装命令：
```bash
pip install playwright
playwright install chromium
```

### 调试技巧

#### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 使用有头模式

```python
config = ScrapingConfig(headless=False)
```

#### 3. 保存用户数据

```python
config = ScrapingConfig(user_data_dir="./browser_data")
```

## 性能监控

### 启用监控

```python
config = ScrapingConfig(enable_monitoring=True)
orchestrator = ScrapingOrchestrator(config)

# 获取统计信息
stats = orchestrator.get_performance_stats()
```

### 监控指标

- **总尝试次数**: 所有爬取尝试的总数
- **成功率**: 成功爬取的百分比
- **平均响应时间**: 爬取的平均耗时
- **按网站统计**: 每个网站的详细统计

### 性能报告示例

```json
{
  "overall": {
    "total_attempts": 100,
    "success_rate": "85.00%",
    "average_response_time": "3.25s",
    "successful_scrapes": 85,
    "failed_scrapes": 15
  },
  "by_site": {
    "boss": {
      "attempts": 60,
      "success_rate": "90.00%",
      "avg_response_time": "2.80s",
      "last_success": "2024-01-15T10:30:00",
      "last_failure": "2024-01-15T09:15:00"
    },
    "lagou": {
      "attempts": 40,
      "success_rate": "77.50%",
      "avg_response_time": "3.90s",
      "last_success": "2024-01-15T10:25:00",
      "last_failure": "2024-01-15T10:20:00"
    }
  }
}
```

## 扩展开发

### 添加新网站支持

1. **创建爬虫类**

```python
from src.resume_assistant.core.scraper import JobScraper

class NewSiteScraper(JobScraper):
    def scrape_job(self, url: str) -> ScrapingResult:
        # 实现爬取逻辑
        pass
```

2. **注册到协调器**

```python
# 在 MultiSiteScraper._initialize_scrapers() 中添加
self.scrapers['newsite'] = NewSiteScraper()
```

3. **更新网站检测**

```python
# 在 MultiSiteScraper.detect_site() 中添加
elif 'newsite.com' in domain:
    return SiteSupport.NEWSITE
```

### 自定义反检测策略

```python
class CustomAntiDetection(AntiDetectionManager):
    def calculate_delay(self) -> float:
        # 自定义延迟算法
        return super().calculate_delay() * 1.5
```

## 最佳实践

### 1. 配置管理

```python
# 生产环境配置
PRODUCTION_CONFIG = ScrapingConfig(
    headless=True,
    max_retries=3,
    concurrent_limit=2,
    enable_monitoring=True,
    data_validation=True
)

# 开发环境配置
DEVELOPMENT_CONFIG = ScrapingConfig(
    headless=False,
    max_retries=1,
    concurrent_limit=1,
    enable_monitoring=False
)
```

### 2. 错误处理

```python
async def safe_scrape(url: str) -> Optional[Job]:
    try:
        result = await scrape_job_url(url)
        if result.success:
            return result.job
        else:
            logger.error(f"爬取失败: {result.error}")
    except Exception as e:
        logger.exception(f"爬取异常: {e}")
    return None
```

### 3. 批量处理

```python
async def batch_scrape_with_progress(urls: List[str]):
    results = []
    
    for i, url in enumerate(urls):
        result = await scrape_job_url(url)
        results.append(result)
        
        # 显示进度
        progress = (i + 1) / len(urls)
        print(f"进度: {progress:.1%}")
        
        # 避免过快请求
        await asyncio.sleep(2)
    
    return results
```

## 故障排除

### 问题诊断步骤

1. **检查依赖安装**
```bash
pip install playwright beautifulsoup4 requests
playwright install
```

2. **验证URL格式**
```python
orchestrator = ScrapingOrchestrator()
print(orchestrator.is_url_supported(url))
```

3. **检查网络连接**
```python
health = await orchestrator.health_check()
print(health)
```

4. **查看详细日志**
```python
import logging
logging.getLogger('src.resume_assistant.core').setLevel(logging.DEBUG)
```

### 常见问题解答

**Q: 为什么爬取速度很慢？**
A: 这是为了避免被反爬机制检测。可以适当调整延迟时间，但不建议设置过快。

**Q: 如何处理验证码？**
A: 使用有头模式（headless=False），系统会暂停等待手动处理验证码。

**Q: 支持代理吗？**
A: 目前代理功能在开发中，可以通过配置启用（但需要自行实现代理逻辑）。

**Q: 如何提高成功率？**
A: 1) 使用有头模式 2) 增加重试次数 3) 适当增加延迟时间 4) 保持浏览器状态

**Q: 数据提取不准确怎么办？**
A: 目标网站可能更新了页面结构，需要更新对应的爬虫代码。

## 联系支持

如果遇到问题或需要添加新网站支持，请：

1. 查看日志文件获取详细错误信息
2. 检查网站是否有结构变化
3. 提交问题反馈，包含详细的错误信息和URL示例

---

**注意**: 使用爬虫时请遵守目标网站的 robots.txt 和使用条款，合理控制爬取频率，避免对目标网站造成过大负担。