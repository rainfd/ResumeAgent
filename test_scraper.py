#!/usr/bin/env python3
"""
爬虫模块测试脚本

测试Playwright和requests两种爬取方式对BOSS直聘职位页面的爬取效果
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from resume_assistant.core.scraper import (
    create_scraper, 
    JobScraper, 
    PlaywrightScraper, 
    BossZhipinScraper,
    ScrapingResult
)
from resume_assistant.utils import get_logger

# 设置日志
logger = get_logger(__name__)

class ScraperTestSuite:
    """爬虫测试套件"""
    
    def __init__(self):
        self.test_url = "https://www.zhipin.com/job_detail/29090ef211bc5eeb03Fz3dq0GFJT.html?securityId=bJzOfMuGJ2F22-61vKFksunOnKBpKMBvBxLCosBmd6oKgS-VKgAqEw7kDzXQdLe4VeIEz6q1iod1iRUkjA1tp9iHqBweo0KuhI9goLnJv-Rbe1Cs96KMmw~~&ka=personal_added_job_29090ef211bc5eeb03Fz3dq0GFJT"
        self.results = {}
        
    def print_header(self, title: str):
        """打印测试标题"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_result(self, result: ScrapingResult, scraper_name: str):
        """打印爬取结果"""
        print(f"\n📊 {scraper_name} 爬取结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败'}")
        
        if result.success and result.job:
            job = result.job
            print(f"   职位ID: {job.id}")
            print(f"   职位标题: {job.title}")
            print(f"   公司名称: {job.company}")
            print(f"   工作地点: {job.location}")
            print(f"   薪资范围: {job.salary}")
            print(f"   经验要求: {job.experience_level}")
            print(f"   学历要求: {job.education_level}")
            print(f"   职位类型: {job.job_type}")
            print(f"   职位标签: {', '.join(job.tags) if job.tags else '无'}")
            print(f"   职位描述: {job.description[:100]}..." if len(job.description) > 100 else f"   职位描述: {job.description}")
            print(f"   爬取时间: {result.scraped_at}")
        else:
            print(f"   错误信息: {result.error}")
            
        print(f"   来源URL: {result.url}")
    
    def test_playwright_scraper(self):
        """测试Playwright爬虫"""
        self.print_header("测试 Playwright 爬虫")
        
        try:
            print("🚀 初始化Playwright爬虫...")
            scraper = PlaywrightScraper()
            
            print(f"🌐 开始爬取URL: {self.test_url}")
            start_time = time.time()
            
            result = scraper.scrape_job(self.test_url)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"⏱️  耗时: {elapsed_time:.2f}秒")
            
            self.print_result(result, "Playwright")
            self.results['playwright'] = {
                'result': result,
                'elapsed_time': elapsed_time,
                'scraper_type': 'Playwright'
            }
            
        except Exception as e:
            error_msg = f"Playwright爬虫测试异常: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.results['playwright'] = {
                'result': ScrapingResult(success=False, error=error_msg, url=self.test_url),
                'elapsed_time': 0,
                'scraper_type': 'Playwright'
            }
    
    def test_requests_scraper(self):
        """测试requests爬虫"""
        self.print_header("测试 Requests + BeautifulSoup 爬虫")
        
        try:
            print("🚀 初始化BossZhipin爬虫...")
            scraper = BossZhipinScraper()
            
            print(f"🌐 开始爬取URL: {self.test_url}")
            start_time = time.time()
            
            result = scraper.scrape_job(self.test_url)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"⏱️  耗时: {elapsed_time:.2f}秒")
            
            self.print_result(result, "Requests")
            self.results['requests'] = {
                'result': result,
                'elapsed_time': elapsed_time,
                'scraper_type': 'Requests+BeautifulSoup'
            }
            
        except Exception as e:
            error_msg = f"Requests爬虫测试异常: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.results['requests'] = {
                'result': ScrapingResult(success=False, error=error_msg, url=self.test_url),
                'elapsed_time': 0,
                'scraper_type': 'Requests+BeautifulSoup'
            }
    
    def test_generic_scraper(self):
        """测试通用爬虫"""
        self.print_header("测试 通用爬虫")
        
        try:
            print("🚀 初始化通用爬虫...")
            scraper = JobScraper()
            
            print(f"🌐 开始爬取URL: {self.test_url}")
            start_time = time.time()
            
            result = scraper.scrape_job(self.test_url)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"⏱️  耗时: {elapsed_time:.2f}秒")
            
            self.print_result(result, "Generic")
            self.results['generic'] = {
                'result': result,
                'elapsed_time': elapsed_time,
                'scraper_type': 'Generic'
            }
            
        except Exception as e:
            error_msg = f"通用爬虫测试异常: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.results['generic'] = {
                'result': ScrapingResult(success=False, error=error_msg, url=self.test_url),
                'elapsed_time': 0,
                'scraper_type': 'Generic'
            }
    
    def compare_results(self):
        """对比测试结果"""
        self.print_header("爬虫性能对比分析")
        
        if not self.results:
            print("❌ 没有测试结果可供对比")
            return
        
        print("\n📈 测试结果汇总:")
        print(f"{'爬虫类型':^20} | {'状态':^8} | {'耗时(秒)':^10} | {'数据完整性':^12}")
        print("-" * 60)
        
        success_count = 0
        total_time = 0
        
        for name, data in self.results.items():
            result = data['result']
            elapsed = data['elapsed_time']
            scraper_type = data['scraper_type']
            
            status = "✅ 成功" if result.success else "❌ 失败"
            
            # 评估数据完整性
            completeness = "无数据"
            if result.success and result.job:
                job = result.job
                fields = [job.title, job.company, job.description, job.salary, job.location]
                filled_fields = sum(1 for field in fields if field and field.strip())
                completeness = f"{filled_fields}/5"
                if filled_fields >= 4:
                    completeness += " 优秀"
                elif filled_fields >= 2:
                    completeness += " 一般"
                else:
                    completeness += " 较差"
            
            print(f"{scraper_type:^20} | {status:^8} | {elapsed:^10.2f} | {completeness:^12}")
            
            if result.success:
                success_count += 1
            total_time += elapsed
        
        print("\n📊 统计信息:")
        print(f"   成功率: {success_count}/{len(self.results)} ({success_count/len(self.results)*100:.1f}%)")
        print(f"   平均耗时: {total_time/len(self.results):.2f}秒")
        
        # 推荐最佳爬虫
        best_scraper = None
        best_score = 0
        
        for name, data in self.results.items():
            result = data['result']
            elapsed = data['elapsed_time']
            
            # 计算综合评分 (成功=100分, 速度加分, 数据完整性加分)
            score = 0
            if result.success:
                score += 100
                # 速度加分 (越快越好，最多20分)
                if elapsed > 0:
                    speed_score = max(0, 20 - elapsed)
                    score += speed_score
                
                # 数据完整性加分
                if result.job:
                    job = result.job
                    fields = [job.title, job.company, job.description, job.salary, job.location]
                    filled_fields = sum(1 for field in fields if field and field.strip())
                    score += filled_fields * 4  # 每个字段4分
            
            if score > best_score:
                best_score = score
                best_scraper = data['scraper_type']
        
        if best_scraper:
            print(f"\n🏆 推荐爬虫: {best_scraper} (综合评分: {best_score:.1f})")
        
        # 错误分析
        print("\n🔍 错误分析:")
        for name, data in self.results.items():
            result = data['result']
            if not result.success:
                print(f"   {data['scraper_type']}: {result.error}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎯 Resume Assistant 爬虫模块测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试URL: {self.test_url}")
        
        # 依次测试各种爬虫
        self.test_playwright_scraper()
        time.sleep(2)  # 避免请求过于频繁
        
        self.test_requests_scraper()
        time.sleep(2)
        
        self.test_generic_scraper()
        
        # 对比分析
        self.compare_results()
        
        self.print_header("测试完成")
        print("💡 建议:")
        print("   1. 如果Playwright成功，优先使用Playwright爬虫")
        print("   2. 如果都失败，可能需要手动添加职位信息")
        print("   3. 对于BOSS直聘等反爬网站，建议结合多种策略")

def main():
    """主函数"""
    print("🔧 检查依赖库...")
    
    # 检查依赖
    missing_deps = []
    
    try:
        import requests
        import bs4
        print("✅ requests + beautifulsoup4 可用")
    except ImportError:
        missing_deps.append("requests beautifulsoup4")
        print("❌ requests + beautifulsoup4 不可用")
    
    try:
        import playwright
        print("✅ playwright 可用")
    except ImportError:
        missing_deps.append("playwright")
        print("❌ playwright 不可用")
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖: {', '.join(missing_deps)}")
        print("请安装: pip install " + " ".join(missing_deps))
        return
    
    # 运行测试
    test_suite = ScraperTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()