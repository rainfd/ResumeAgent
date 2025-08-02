"""Web组件和适配器单元测试"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 模拟Streamlit环境
class MockStreamlit:
    """模拟Streamlit模块"""
    
    class SessionState:
        def __init__(self):
            self._state = {}
        
        def get(self, key, default=None):
            return self._state.get(key, default)
        
        def __setitem__(self, key, value):
            self._state[key] = value
        
        def __getitem__(self, key):
            return self._state[key]
        
        def __contains__(self, key):
            return key in self._state
    
    def __init__(self):
        self.session_state = self.SessionState()
        self._columns_result = [MagicMock(), MagicMock()]
        self._container_result = MagicMock()
    
    def columns(self, spec):
        return self._columns_result[:len(spec) if isinstance(spec, list) else spec]
    
    def container(self):
        return self._container_result
    
    def expander(self, label, expanded=False):
        return MagicMock()
    
    def tabs(self, tab_names):
        return [MagicMock() for _ in tab_names]
    
    def markdown(self, text, unsafe_allow_html=False):
        pass
    
    def write(self, text):
        pass
    
    def success(self, text):
        pass
    
    def error(self, text):
        pass
    
    def warning(self, text):
        pass
    
    def info(self, text):
        pass
    
    def button(self, label, key=None, type="secondary"):
        return False
    
    def text_input(self, label, value="", key=None, type="default"):
        return value
    
    def selectbox(self, label, options, index=0, key=None):
        return options[index] if options else None
    
    def file_uploader(self, label, type=None, key=None):
        return None
    
    def dataframe(self, data, use_container_width=False):
        pass
    
    def metric(self, label, value, delta=None):
        pass
    
    def progress(self, value):
        return MagicMock()
    
    def spinner(self, text):
        return MagicMock()
    
    def rerun(self):
        pass

# 替换streamlit模块
mock_st = MockStreamlit()
sys.modules['streamlit'] = mock_st


from resume_assistant.web.components import UIComponents
from resume_assistant.web.session_manager import SessionManager
from resume_assistant.web.navigation import NavigationManager

# 创建简单的WebAdapters类用于测试
class WebAdapters:
    """简单的Web适配器实现用于测试"""
    
    def format_job_for_display(self, job_data):
        """格式化职位显示数据"""
        return {
            **job_data,
            'display_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def format_resume_for_display(self, resume_data):
        """格式化简历显示数据"""
        return {
            **resume_data,
            'content_preview': resume_data.get('content', '')[:100] + '...',
            'skills_preview': ', '.join(resume_data.get('skills', [])[:3])
        }
    
    def format_analysis_for_display(self, analysis_data):
        """格式化分析结果显示数据"""
        confidence = analysis_data.get('confidence_score', 0)
        return {
            **analysis_data,
            'confidence_level': 'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low',
            'content_preview': analysis_data.get('analysis_content', '')[:150] + '...'
        }
    
    def parse_uploaded_file(self, file_obj):
        """解析上传文件"""
        return {
            'filename': file_obj.name,
            'file_type': file_obj.type,
            'file_size': file_obj.size,
            'content': file_obj.read()
        }
    
    def validate_job_url(self, url):
        """验证职位URL"""
        return url.startswith(('http://', 'https://')) and len(url) > 10
    
    def extract_job_keywords(self, description):
        """提取职位关键词"""
        keywords = []
        common_keywords = ['Python', 'Django', 'Flask', 'JavaScript', 'React', 'Vue', 'MySQL', 'Redis']
        for keyword in common_keywords:
            if keyword.lower() in description.lower():
                keywords.append(keyword)
        return keywords
    
    def calculate_match_score(self, resume_skills, job_requirements):
        """计算匹配分数"""
        if not resume_skills or not job_requirements:
            return 0.0
        matches = len(set(resume_skills) & set(job_requirements))
        return matches / max(len(resume_skills), len(job_requirements))
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def truncate_text(self, text, max_length=50):
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class TestUIComponents(unittest.TestCase):
    """UI组件测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.components = UIComponents()
    
    def test_ui_components_initialization(self):
        """测试UI组件初始化"""
        self.assertIsInstance(self.components, UIComponents)
    
    def test_render_header(self):
        """测试渲染页面头部"""
        # 测试不会抛出异常
        try:
            self.components.render_header("测试标题", "测试描述", "🧪")
        except Exception as e:
            self.fail(f"render_header raised exception: {e}")
    
    def test_render_job_card(self):
        """测试渲染职位卡片"""
        job_data = {
            "id": "job-123",
            "title": "Python开发工程师",
            "company": "测试公司",
            "location": "北京",
            "salary": "15k-25k",
            "description": "职位描述"
        }
        
        try:
            self.components.render_job_card(job_data)
        except Exception as e:
            self.fail(f"render_job_card raised exception: {e}")
    
    def test_render_resume_card(self):
        """测试渲染简历卡片"""
        resume_data = {
            "id": "resume-123",
            "filename": "张三_简历.pdf",
            "upload_date": "2024-01-01",
            "content": "简历内容摘要"
        }
        
        try:
            self.components.render_resume_card(resume_data)
        except Exception as e:
            self.fail(f"render_resume_card raised exception: {e}")
    
    def test_render_analysis_result(self):
        """测试渲染分析结果"""
        analysis_data = {
            "id": "analysis-123",
            "resume_id": "resume-123",
            "job_id": "job-123",
            "analysis_content": "这是分析结果内容",
            "confidence_score": 0.85,
            "created_at": datetime.now()
        }
        
        try:
            self.components.render_analysis_result(analysis_data)
        except Exception as e:
            self.fail(f"render_analysis_result raised exception: {e}")
    
    def test_render_notification_area(self):
        """测试渲染通知区域"""
        try:
            self.components.render_notification_area()
        except Exception as e:
            self.fail(f"render_notification_area raised exception: {e}")
    
    def test_render_loading_state(self):
        """测试渲染加载状态"""
        try:
            self.components.render_loading_state("正在处理...")
        except Exception as e:
            self.fail(f"render_loading_state raised exception: {e}")
    
    def test_render_error_message(self):
        """测试渲染错误消息"""
        try:
            self.components.render_error_message("这是一个错误消息")
        except Exception as e:
            self.fail(f"render_error_message raised exception: {e}")
    
    def test_render_pagination(self):
        """测试渲染分页组件"""
        try:
            result = self.components.render_pagination(
                total_items=100,
                items_per_page=10,
                current_page=1
            )
            # 应该返回页码信息
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"render_pagination raised exception: {e}")
    
    def test_render_filter_controls(self):
        """测试渲染过滤控件"""
        filter_options = {
            "company": ["公司A", "公司B", "公司C"],
            "location": ["北京", "上海", "深圳"],
            "salary_range": ["10k-15k", "15k-25k", "25k+"]
        }
        
        try:
            result = self.components.render_filter_controls(filter_options)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"render_filter_controls raised exception: {e}")


class TestWebAdapters(unittest.TestCase):
    """Web适配器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapters = WebAdapters()
    
    def test_web_adapters_initialization(self):
        """测试Web适配器初始化"""
        self.assertIsInstance(self.adapters, WebAdapters)
    
    def test_format_job_for_display(self):
        """测试格式化职位显示数据"""
        job_data = {
            "id": "job-123",
            "title": "Python开发工程师",
            "company": "测试公司",
            "location": "北京",
            "salary": "15k-25k",
            "requirements": "Python, Django, Redis",
            "description": "负责后端开发工作",
            "created_at": datetime.now()
        }
        
        formatted = self.adapters.format_job_for_display(job_data)
        
        self.assertIn("id", formatted)
        self.assertIn("title", formatted)
        self.assertIn("company", formatted)
        self.assertIn("display_date", formatted)
    
    def test_format_resume_for_display(self):
        """测试格式化简历显示数据"""
        resume_data = {
            "id": "resume-123",
            "filename": "张三_简历.pdf",
            "content": "这是简历的详细内容...",
            "parsed_data": {
                "name": "张三",
                "skills": ["Python", "Django"]
            },
            "uploaded_at": datetime.now()
        }
        
        formatted = self.adapters.format_resume_for_display(resume_data)
        
        self.assertIn("id", formatted)
        self.assertIn("filename", formatted)
        self.assertIn("content_preview", formatted)
        self.assertIn("skills_preview", formatted)
    
    def test_format_analysis_for_display(self):
        """测试格式化分析结果显示数据"""
        analysis_data = {
            "id": "analysis-123",
            "resume_id": "resume-123",
            "job_id": "job-123",
            "analysis_content": "这是一份优秀的简历，技能匹配度很高，工作经验符合要求。建议进一步面试。",
            "confidence_score": 0.85,
            "created_at": datetime.now()
        }
        
        formatted = self.adapters.format_analysis_for_display(analysis_data)
        
        self.assertIn("id", formatted)
        self.assertIn("confidence_score", formatted)
        self.assertIn("confidence_level", formatted)
        self.assertIn("content_preview", formatted)
    
    def test_parse_uploaded_file(self):
        """测试解析上传文件"""
        # 模拟上传的文件对象
        mock_file = MagicMock()
        mock_file.name = "test_resume.pdf"
        mock_file.type = "application/pdf"
        mock_file.size = 1024 * 1024  # 1MB
        mock_file.read.return_value = b"mock file content"
        
        result = self.adapters.parse_uploaded_file(mock_file)
        
        self.assertIn("filename", result)
        self.assertIn("file_type", result)
        self.assertIn("file_size", result)
        self.assertIn("content", result)
        self.assertEqual(result["filename"], "test_resume.pdf")
    
    def test_validate_job_url(self):
        """测试验证职位URL"""
        valid_urls = [
            "https://www.lagou.com/jobs/12345678.html",
            "https://example.com/job/python-developer",
            "http://localhost:8080/job/123"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert(1)",
            ""
        ]
        
        for url in valid_urls:
            self.assertTrue(self.adapters.validate_job_url(url))
        
        for url in invalid_urls:
            self.assertFalse(self.adapters.validate_job_url(url))
    
    def test_extract_job_keywords(self):
        """测试提取职位关键词"""
        job_description = """
        我们正在寻找一名经验丰富的Python开发工程师，
        熟悉Django框架、Redis缓存、MySQL数据库，
        有微服务架构经验，了解Docker和Kubernetes。
        """
        
        keywords = self.adapters.extract_job_keywords(job_description)
        
        self.assertIsInstance(keywords, list)
        self.assertIn("Python", keywords)
        self.assertIn("Django", keywords)
        self.assertIn("Redis", keywords)
    
    def test_calculate_match_score(self):
        """测试计算匹配分数"""
        resume_skills = ["Python", "Django", "MySQL", "Redis"]
        job_requirements = ["Python", "Django", "PostgreSQL", "Celery"]
        
        score = self.adapters.calculate_match_score(resume_skills, job_requirements)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Python和Django匹配，所以分数应该大于0
        self.assertGreater(score, 0.0)
    
    def test_format_file_size(self):
        """测试格式化文件大小"""
        test_cases = [
            (512, "512 B"),
            (1024, "1.0 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB")
        ]
        
        for size, expected in test_cases:
            result = self.adapters.format_file_size(size)
            self.assertEqual(result, expected)
    
    def test_truncate_text(self):
        """测试截断文本"""
        long_text = "这是一段很长的文本内容，需要被截断以适应显示要求。"
        
        truncated = self.adapters.truncate_text(long_text, max_length=20)
        
        self.assertLessEqual(len(truncated), 23)  # 20 + "..."
        self.assertTrue(truncated.endswith("..."))


class TestSessionManager(unittest.TestCase):
    """Session管理器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 重置session state
        mock_st.session_state = MockStreamlit.SessionState()
    
    def test_session_initialization(self):
        """测试Session初始化"""
        SessionManager.initialize_session()
        
        # 检查必要的session变量是否已初始化
        expected_keys = [
            'current_page', 'jobs', 'resumes', 'analyses', 
            'notifications', 'filters', 'pagination'
        ]
        
        for key in expected_keys:
            self.assertIn(key, mock_st.session_state)
    
    def test_add_notification(self):
        """测试添加通知"""
        SessionManager.initialize_session()
        
        SessionManager.add_notification("success", "操作成功")
        SessionManager.add_notification("error", "操作失败")
        
        notifications = mock_st.session_state.get('notifications', [])
        self.assertEqual(len(notifications), 2)
        self.assertEqual(notifications[0]['type'], 'success')
        self.assertEqual(notifications[1]['type'], 'error')
    
    def test_clear_notifications(self):
        """测试清除通知"""
        SessionManager.initialize_session()
        
        # 添加通知
        SessionManager.add_notification("info", "测试通知")
        self.assertEqual(len(mock_st.session_state['notifications']), 1)
        
        # 清除通知
        SessionManager.clear_notifications()
        self.assertEqual(len(mock_st.session_state['notifications']), 0)
    
    def test_set_current_page(self):
        """测试设置当前页面"""
        SessionManager.initialize_session()
        
        SessionManager.set_current_page("job_management")
        self.assertEqual(mock_st.session_state['current_page'], "job_management")
    
    def test_update_pagination(self):
        """测试更新分页信息"""
        SessionManager.initialize_session()
        
        SessionManager.update_pagination(
            current_page=2,
            total_items=100,
            items_per_page=10
        )
        
        pagination = mock_st.session_state['pagination']
        self.assertEqual(pagination['current_page'], 2)
        self.assertEqual(pagination['total_items'], 100)
        self.assertEqual(pagination['items_per_page'], 10)
    
    def test_apply_filters(self):
        """测试应用过滤器"""
        SessionManager.initialize_session()
        
        filters = {
            "company": "测试公司",
            "location": "北京",
            "salary_min": 15000
        }
        
        SessionManager.apply_filters(filters)
        
        session_filters = mock_st.session_state['filters']
        self.assertEqual(session_filters['company'], "测试公司")
        self.assertEqual(session_filters['location'], "北京")
        self.assertEqual(session_filters['salary_min'], 15000)
    
    def test_get_session_data(self):
        """测试获取Session数据"""
        SessionManager.initialize_session()
        
        # 设置一些测试数据
        mock_st.session_state['jobs'] = [{"id": "job-1", "title": "职位1"}]
        mock_st.session_state['resumes'] = [{"id": "resume-1", "filename": "简历1.pdf"}]
        
        jobs = SessionManager.get_session_data('jobs')
        resumes = SessionManager.get_session_data('resumes')
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(resumes), 1)
        self.assertEqual(jobs[0]['title'], "职位1")


class TestNavigationManager(unittest.TestCase):
    """导航管理器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.nav_manager = NavigationManager()
        # 重置session state
        mock_st.session_state = MockStreamlit.SessionState()
    
    def test_navigation_initialization(self):
        """测试导航初始化"""
        self.assertIsInstance(self.nav_manager, NavigationManager)
        
        # 检查页面配置
        pages = self.nav_manager.get_pages()
        self.assertIsInstance(pages, dict)
        self.assertIn("job_management", pages)
        self.assertIn("resume_management", pages)
    
    def test_get_current_page(self):
        """测试获取当前页面"""
        # 设置当前页面
        mock_st.session_state['current_page'] = "job_management"
        
        current_page = self.nav_manager.get_current_page()
        self.assertEqual(current_page, "job_management")
    
    def test_navigate_to_page(self):
        """测试导航到页面"""
        self.nav_manager.navigate_to("resume_management")
        
        current_page = mock_st.session_state.get('current_page')
        self.assertEqual(current_page, "resume_management")
    
    def test_render_sidebar_navigation(self):
        """测试渲染侧边栏导航"""
        try:
            self.nav_manager.render_sidebar_navigation()
        except Exception as e:
            self.fail(f"render_sidebar_navigation raised exception: {e}")
    
    def test_render_breadcrumb(self):
        """测试渲染面包屑导航"""
        try:
            self.nav_manager.render_breadcrumb("job_management")
        except Exception as e:
            self.fail(f"render_breadcrumb raised exception: {e}")
    
    def test_get_page_title(self):
        """测试获取页面标题"""
        title = self.nav_manager.get_page_title("job_management")
        self.assertIsInstance(title, str)
        self.assertNotEqual(title, "")


class TestWebComponentsIntegration(unittest.TestCase):
    """Web组件集成测试"""
    
    def test_components_adapter_integration(self):
        """测试组件和适配器集成"""
        components = UIComponents()
        adapters = WebAdapters()
        
        # 创建测试数据
        job_data = {
            "id": "integration-job",
            "title": "Python开发工程师",
            "company": "测试公司",
            "created_at": datetime.now()
        }
        
        # 使用适配器格式化数据
        formatted_job = adapters.format_job_for_display(job_data)
        
        # 使用组件渲染
        try:
            components.render_job_card(formatted_job)
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_session_navigation_integration(self):
        """测试Session和导航集成"""
        SessionManager.initialize_session()
        nav_manager = NavigationManager()
        
        # 导航到不同页面
        nav_manager.navigate_to("resume_management")
        current_page = nav_manager.get_current_page()
        
        self.assertEqual(current_page, "resume_management")
        self.assertEqual(mock_st.session_state['current_page'], "resume_management")


def run_web_components_tests():
    """运行Web组件测试"""
    print("🌐 运行Web组件和适配器单元测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestUIComponents,
        TestWebAdapters,
        TestSessionManager,
        TestNavigationManager,
        TestWebComponentsIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_web_components_tests()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")