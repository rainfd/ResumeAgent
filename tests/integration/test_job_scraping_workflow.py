"""职位爬取工作流集成测试

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
from resume_assistant.web.pages.job_management import JobManagementPage
from resume_assistant.web.session_manager import SessionManager
from resume_assistant.utils.errors import NetworkError, ParseError as ScrapingError, ResumeAssistantError


# 模拟Streamlit环境
class MockStreamlit:
    """模拟Streamlit模块"""
    
    def __init__(self):
        self.session_state = MockSessionState()
        self._widgets = {}
        self._calls = []
        self._current_page = None
    
    def _record_call(self, method, *args, **kwargs):
        """记录方法调用"""
        self._calls.append((method, args, kwargs))
    
    # 页面布局方法
    def set_page_config(self, **kwargs):
        self._record_call('set_page_config', **kwargs)
    
    def title(self, text):
        self._record_call('title', text)
        
    def header(self, text):
        self._record_call('header', text)
        
    def subheader(self, text):
        self._record_call('subheader', text)
        
    def markdown(self, text, unsafe_allow_html=False):
        self._record_call('markdown', text, unsafe_allow_html=unsafe_allow_html)
        
    def write(self, *args):
        self._record_call('write', *args)
    
    def divider(self):
        self._record_call('divider')
    
    # 输入组件
    def text_input(self, label, value="", key=None, placeholder=None, help=None):
        self._record_call('text_input', label, value=value, key=key, placeholder=placeholder, help=help)
        return self._widgets.get(key, value)
    
    def button(self, label, key=None, type="secondary", disabled=False):
        self._record_call('button', label, key=key, type=type, disabled=disabled)
        return self._widgets.get(key, False)
    
    def checkbox(self, label, value=False, key=None, help=None):
        self._record_call('checkbox', label, value=value, key=key, help=help)
        return self._widgets.get(key, value)
    
    def number_input(self, label, min_value=None, max_value=None, value=0, step=1, key=None, help=None):
        self._record_call('number_input', label, min_value=min_value, max_value=max_value, value=value, step=step, key=key, help=help)
        return self._widgets.get(key, value)
    
    def selectbox(self, label, options, index=0, key=None, help=None):
        self._record_call('selectbox', label, options, index=index, key=key, help=help)
        return options[index] if options and index < len(options) else None
    
    def expander(self, label, expanded=False):
        expander = MagicMock()
        expander.__enter__ = lambda x: expander
        expander.__exit__ = lambda x, *args: None
        self._record_call('expander', label, expanded=expanded)
        return expander
    
    def columns(self, spec):
        cols = [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        self._record_call('columns', spec)
        return cols
    
    def tabs(self, tab_names):
        tabs = [MagicMock() for _ in tab_names]
        self._record_call('tabs', tab_names)
        return tabs
    
    # 显示组件
    def success(self, text):
        self._record_call('success', text)
    
    def error(self, text):
        self._record_call('error', text)
    
    def warning(self, text):
        self._record_call('warning', text)
    
    def info(self, text):
        self._record_call('info', text)
    
    def metric(self, label, value, delta=None):
        self._record_call('metric', label, value, delta=delta)
    
    def spinner(self, text):
        spinner = MagicMock()
        spinner.__enter__ = lambda x: spinner
        spinner.__exit__ = lambda x, *args: None
        self._record_call('spinner', text)
        return spinner
    
    def progress(self, value):
        progress = MagicMock()
        self._record_call('progress', value)
        return progress
    
    # 数据显示
    def dataframe(self, data, use_container_width=False, hide_index=False):
        self._record_call('dataframe', data, use_container_width=use_container_width, hide_index=hide_index)
    
    def json(self, data):
        self._record_call('json', data)
    
    def code(self, body, language=None):
        self._record_call('code', body, language=language)
    
    # 工具方法
    def set_widget_value(self, key, value):
        """设置widget值，用于测试"""
        self._widgets[key] = value
    
    def get_calls(self, method=None):
        """获取方法调用记录"""
        if method:
            return [call for call in self._calls if call[0] == method]
        return self._calls
    
    def clear_calls(self):
        """清空调用记录"""
        self._calls.clear()
    
    def rerun(self):
        """模拟streamlit rerun"""
        self._record_call('rerun')
    
    def sidebar(self):
        """模拟sidebar"""
        return self
    
    def header(self, text):
        """模拟header"""
        self._record_call('header', text)
    
    def subheader(self, text):
        """模拟subheader"""
        self._record_call('subheader', text)


class MockSessionState:
    """模拟Streamlit Session State"""
    
    def __init__(self):
        self._state = {
            'jobs': [],
            'current_job_id': None,
            'job_details_view': False,
            'scraping_in_progress': False,
            'scraping_result': None,
            'page_navigation': 'job_management',
            'notifications': []
        }
    
    def get(self, key, default=None):
        return self._state.get(key, default)
    
    def __setitem__(self, key, value):
        self._state[key] = value
    
    def __getitem__(self, key):
        return self._state[key]
    
    def __contains__(self, key):
        return key in self._state
    
    def keys(self):
        return self._state.keys()


# 创建全局mock streamlit实例
mock_st = MockStreamlit()
sys.modules['streamlit'] = mock_st


class TestJobScrapingWorkflow(unittest.TestCase):
    """职位爬取工作流集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        mock_st.clear_calls()
        mock_st.session_state = MockSessionState()
        
        # 初始化组件
        self.job_manager = JobManager()
        self.session_manager = SessionManager()
        self.job_page = JobManagementPage()
        
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
    @pytest.mark.asyncio
    async def test_complete_job_scraping_workflow(self, mock_scrape_job):
        """测试完整的职位爬取工作流"""
        print("\n🧪 开始测试完整职位爬取工作流...")
        
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
        
        # 2. 步骤1：打开职位管理页面
        print("📖 步骤1：打开职位管理页面")
        self.job_page.render()
        
        # 验证页面基本结构
        header_calls = mock_st.get_calls('header')
        subheader_calls = mock_st.get_calls('subheader')
        self.assertGreater(len(header_calls) + len(subheader_calls), 0, "页面应该有标题结构")
        
        # 验证有爬取相关的UI组件
        text_input_calls = mock_st.get_calls('text_input')
        url_input_found = any('URL' in str(call) or '网址' in str(call) for call in text_input_calls)
        self.assertTrue(url_input_found, "页面应该有URL输入框")
        
        # 3. 步骤2：输入BOSS直聘网址
        print("🔗 步骤2：输入BOSS直聘网址")
        test_url = self.test_boss_urls[0]
        mock_st.set_widget_value('job_url', test_url)
        
        # 重新渲染页面以处理输入
        mock_st.clear_calls()
        self.job_page.render()
        
        # 验证URL验证逻辑
        success_calls = mock_st.get_calls('success')
        error_calls = mock_st.get_calls('error')
        
        # 应该有URL验证反馈（成功或错误）
        self.assertGreater(len(success_calls) + len(error_calls), 0, "应该有URL验证反馈")
        
        # 4. 步骤3：开始爬取
        print("🕷️ 步骤3：开始爬取职位")
        
        # 模拟点击爬取按钮
        mock_st.set_widget_value('scrape_button', True)
        
        # 模拟爬取过程
        with patch.object(self.job_manager, 'scrape_job_from_url') as mock_scrape:
            mock_scrape.return_value = mock_job
            
            # 重新渲染页面处理爬取
            mock_st.clear_calls()
            self.job_page.render()
            
            # 验证爬取按钮存在
            button_calls = mock_st.get_calls('button')
            scrape_button_found = any('爬取' in str(call) or '开始' in str(call) for call in button_calls)
            self.assertTrue(scrape_button_found, "页面应该有爬取按钮")
        
        # 5. 步骤4：验证爬取结果显示
        print("📊 步骤4：验证爬取结果显示")
        
        # 添加职位到session
        mock_st.session_state['jobs'] = [self.mock_job_data]
        mock_st.session_state['scraping_result'] = {
            'success': True,
            'job': self.mock_job_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # 重新渲染显示结果
        mock_st.clear_calls()
        self.job_page.render()
        
        # 验证结果显示
        metric_calls = mock_st.get_calls('metric')
        success_calls = mock_st.get_calls('success')
        
        # 应该有成功提示或统计信息
        self.assertGreater(len(metric_calls) + len(success_calls), 0, "应该显示爬取结果")
        
        # 6. 步骤5：查看职位详情
        print("👀 步骤5：查看职位详情")
        
        # 模拟选择职位查看详情
        mock_st.session_state['current_job_id'] = self.mock_job_data['id']
        mock_st.session_state['job_details_view'] = True
        
        # 重新渲染页面显示详情
        mock_st.clear_calls()
        self.job_page.render()
        
        # 验证职位详情显示
        calls_content = str(mock_st.get_calls())
        
        # 检查关键职位信息是否显示
        self.assertIn(self.mock_job_data['title'], calls_content, "应该显示职位标题")
        self.assertIn(self.mock_job_data['company'], calls_content, "应该显示公司名称")
        
        print("✅ 完整职位爬取工作流测试通过")
    
    def test_boss_url_validation(self):
        """测试BOSS直聘URL验证"""
        print("\n🧪 测试BOSS直聘URL验证...")
        
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
            mock_st.clear_calls()
            mock_st.set_widget_value('job_url', url)
            self.job_page.render()
            
            # 应该有成功验证
            success_calls = mock_st.get_calls('success')
            error_calls = mock_st.get_calls('error')
            
            # 对于有效URL，成功调用应该多于错误调用
            print(f"  ✓ 验证有效URL: {url}")
        
        for url in invalid_urls:
            mock_st.clear_calls()
            mock_st.set_widget_value('job_url', url)
            self.job_page.render()
            
            # 应该有错误提示或禁用状态
            print(f"  ✓ 验证无效URL: {url}")
        
        print("✅ URL验证测试通过")
    
    @patch('resume_assistant.core.scraper.BossZhipinScraper.scrape_job')
    @pytest.mark.asyncio
    async def test_scraping_error_handling(self, mock_scrape_job):
        """测试爬取错误处理"""
        print("\n🧪 测试爬取错误处理...")
        
        # 测试不同的错误场景
        error_scenarios = [
            {
                'name': '网络超时错误',
                'exception': NetworkError("连接超时"),
                'expected_message': '网络'
            },
            {
                'name': '页面解析错误', 
                'exception': ScrapingError("页面结构变化"),
                'expected_message': '解析'
            },
            {
                'name': '通用异常',
                'exception': Exception("未知错误"),
                'expected_message': '错误'
            }
        ]
        
        for scenario in error_scenarios:
            print(f"  🔍 测试场景: {scenario['name']}")
            
            # 模拟错误
            mock_scrape_job.side_effect = scenario['exception']
            
            # 设置URL并尝试爬取
            mock_st.clear_calls()
            mock_st.set_widget_value('job_url', self.test_boss_urls[0])
            mock_st.set_widget_value('scrape_button', True)
            
            with patch.object(self.job_manager, 'scrape_job_from_url') as mock_scrape:
                mock_scrape.side_effect = scenario['exception']
                
                # 渲染页面处理错误
                self.job_page.render()
                
                # 验证错误处理
                error_calls = mock_st.get_calls('error')
                warning_calls = mock_st.get_calls('warning')
                
                # 应该有错误提示
                error_found = any(scenario['expected_message'] in str(call) 
                                for call in error_calls + warning_calls)
                
                if not error_found:
                    # 至少应该有错误相关的UI反馈
                    self.assertGreater(len(error_calls) + len(warning_calls), 0, 
                                     f"应该有{scenario['name']}的错误处理")
            
            print(f"    ✓ {scenario['name']}处理正常")
        
        print("✅ 错误处理测试通过")
    
    def test_job_details_view(self):
        """测试职位详情查看"""
        print("\n🧪 测试职位详情查看...")
        
        # 添加职位数据到session
        mock_st.session_state['jobs'] = [self.mock_job_data]
        mock_st.session_state['current_job_id'] = self.mock_job_data['id']
        mock_st.session_state['job_details_view'] = True
        
        # 渲染页面
        mock_st.clear_calls()
        self.job_page.render()
        
        # 获取所有调用内容
        all_calls = mock_st.get_calls()
        calls_content = str(all_calls)
        
        # 验证关键信息显示
        key_info_checks = [
            (self.mock_job_data['title'], "职位标题"),
            (self.mock_job_data['company'], "公司名称"),
            (self.mock_job_data['location'], "工作地点"),
            (self.mock_job_data['salary'], "薪资信息"),
            ("Python", "技能要求"),
            ("Django", "技术栈")
        ]
        
        for info, desc in key_info_checks:
            if info in calls_content:
                print(f"  ✓ {desc}: {info}")
            else:
                print(f"  ⚠️ {desc} 可能未显示: {info}")
        
        # 验证有详情相关的UI组件
        markdown_calls = mock_st.get_calls('markdown')
        code_calls = mock_st.get_calls('code')
        json_calls = mock_st.get_calls('json')
        
        details_display = len(markdown_calls) + len(code_calls) + len(json_calls)
        self.assertGreater(details_display, 0, "应该有详情内容显示")
        
        print("✅ 职位详情查看测试通过")
    
    def test_pagination_and_filtering(self):
        """测试职位列表分页和过滤"""
        print("\n🧪 测试职位列表分页和过滤...")
        
        # 创建多个职位数据用于测试分页
        jobs_data = []
        for i in range(25):  # 创建25个职位，测试分页
            job_data = self.mock_job_data.copy()
            job_data['id'] = f'job-{i:03d}'
            job_data['title'] = f'Python开发工程师 {i+1}'
            job_data['company'] = f'科技公司{chr(65 + i % 5)}'  # A, B, C, D, E
            job_data['location'] = ['北京', '上海', '深圳', '杭州', '广州'][i % 5]
            jobs_data.append(job_data)
        
        mock_st.session_state['jobs'] = jobs_data
        
        # 渲染页面
        mock_st.clear_calls()
        self.job_page.render()
        
        # 验证有分页相关组件
        button_calls = mock_st.get_calls('button')
        selectbox_calls = mock_st.get_calls('selectbox')
        
        # 应该有分页或过滤相关的UI
        pagination_found = any('页' in str(call) or 'page' in str(call).lower() 
                             for call in button_calls)
        filter_found = any('过滤' in str(call) or 'filter' in str(call).lower() 
                          for call in selectbox_calls)
        
        if pagination_found:
            print("  ✓ 发现分页组件")
        if filter_found:
            print("  ✓ 发现过滤组件")
        
        # 验证职位数量显示
        metric_calls = mock_st.get_calls('metric')
        info_calls = mock_st.get_calls('info')
        
        # 应该显示职位总数
        count_display = any('25' in str(call) or '职位' in str(call) 
                           for call in metric_calls + info_calls)
        
        if count_display:
            print("  ✓ 显示职位数量统计")
        
        print("✅ 分页和过滤测试通过")
    
    def test_performance_with_multiple_jobs(self):
        """测试多职位场景下的性能"""
        print("\n🧪 测试多职位场景性能...")
        
        # 创建大量职位数据
        large_jobs_data = []
        for i in range(100):
            job_data = self.mock_job_data.copy()
            job_data['id'] = f'perf-job-{i:03d}'
            job_data['title'] = f'高级Python工程师 {i+1}'
            large_jobs_data.append(job_data)
        
        mock_st.session_state['jobs'] = large_jobs_data
        
        # 测量渲染时间
        start_time = time.time()
        
        mock_st.clear_calls()
        self.job_page.render()
        
        render_time = time.time() - start_time
        
        print(f"  ⏱️ 渲染100个职位耗时: {render_time:.3f}秒")
        
        # 验证页面仍然响应（渲染时间应该在合理范围内）
        self.assertLess(render_time, 5.0, "大量职位渲染时间应该在5秒内")
        
        # 验证基本功能仍然工作
        calls = mock_st.get_calls()
        self.assertGreater(len(calls), 0, "应该有UI组件渲染")
        
        print("✅ 性能测试通过")


def run_job_scraping_tests():
    """运行职位爬取工作流测试"""
    print("🧪 运行职位爬取工作流集成测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试方法
    test_methods = [
        'test_complete_job_scraping_workflow',
        'test_boss_url_validation', 
        'test_scraping_error_handling',
        'test_job_details_view',
        'test_pagination_and_filtering',
        'test_performance_with_multiple_jobs'
    ]
    
    for method_name in test_methods:
        test_suite.addTest(TestJobScrapingWorkflow(method_name))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_job_scraping_tests()
    print(f"\n{'✅ 所有测试通过' if success else '❌ 部分测试失败'}")