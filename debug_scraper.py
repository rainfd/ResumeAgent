#!/usr/bin/env python3
"""
爬虫调试脚本 - 诊断具体问题
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from resume_assistant.core.scraper import PlaywrightScraper
from resume_assistant.utils import get_logger

def debug_playwright_scraping():
    """调试Playwright爬取过程"""
    test_url = "https://www.zhipin.com/job_detail/29090ef211bc5eeb03Fz3dq0GFJT.html?securityId=bJzOfMuGJ2F22-61vKFksunOnKBpKMBvBxLCosBmd6oKgS-VKgAqEw7kDzXQdLe4VeIEz6q1iod1iRUkjA1tp9iHqBweo0KuhI9goLnJv-Rbe1Cs96KMmw~~&ka=personal_added_job_29090ef211bc5eeb03Fz3dq0GFJT"
    
    print("🔍 调试Playwright爬取过程")
    print(f"测试URL: {test_url}")
    
    scraper = PlaywrightScraper()
    
    try:
        # 设置浏览器
        scraper._setup_browser()
        page = scraper.context.new_page()
        
        print("\n📄 访问页面...")
        
        # 注入反检测脚本
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
        """)
        
        # 访问页面
        response = page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
        print(f"HTTP状态码: {response.status}")
        
        # 等待页面加载
        page.wait_for_timeout(5000)
        
        # 获取页面标题
        title = page.title()
        print(f"页面标题: {title}")
        
        # 检查页面内容
        body_text = page.inner_text('body') if page.query_selector('body') else ''
        print(f"页面内容长度: {len(body_text)}")
        print(f"页面内容预览: {body_text[:200]}...")
        
        # 检查是否被拦截
        blocked_keywords = ['验证码', '人机验证', '请登录', '访问受限', '机器人']
        is_blocked = any(keyword in body_text for keyword in blocked_keywords)
        print(f"是否被拦截: {is_blocked}")
        
        if is_blocked:
            for keyword in blocked_keywords:
                if keyword in body_text:
                    print(f"检测到拦截关键词: {keyword}")
        
        # 保存页面截图
        screenshot_path = "debug_screenshot.png"
        page.screenshot(path=screenshot_path)
        print(f"页面截图已保存: {screenshot_path}")
        
        # 保存HTML内容
        html_content = page.content()
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("页面HTML已保存: debug_page.html")
        
        # 尝试查找职位信息元素
        print("\n🔍 查找职位信息元素...")
        
        selectors = {
            'title': ['.job-title', '.job-name', 'h1.name', 'h1'],
            'company': ['.company-name', '.info-company h3'],
            'salary': ['.salary', '.job-salary'],
            'location': ['.job-area', '.job-location'],
        }
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for field, selector_list in selectors.items():
            print(f"\n查找 {field}:")
            found = False
            for selector in selector_list:
                elements = soup.select(selector)
                if elements:
                    print(f"  选择器 '{selector}' 找到 {len(elements)} 个元素:")
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        text = elem.get_text(strip=True)
                        print(f"    [{i+1}] {text[:50]}...")
                    found = True
                    break
            
            if not found:
                print(f"  未找到 {field} 信息")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
    finally:
        scraper._cleanup_browser()

if __name__ == "__main__":
    debug_playwright_scraping()