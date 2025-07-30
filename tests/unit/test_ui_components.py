"""TUI组件单元测试"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, 'src')

from resume_assistant.ui.components import (
    FileUploadDialog, ResumeTable, ResumeDetailPanel,
    ComponentFactory, DataTable, InfoPanel
)


class TestFileUploadDialog(unittest.TestCase):
    """文件上传对话框测试"""
    
    def setUp(self):
        self.dialog = FileUploadDialog()
    
    def test_init_with_default_formats(self):
        """测试默认支持格式初始化"""
        dialog = FileUploadDialog()
        self.assertEqual(dialog.supported_formats, ['pdf', 'md', 'markdown'])
    
    def test_init_with_custom_formats(self):
        """测试自定义支持格式初始化"""
        formats = ['pdf', 'txt']
        dialog = FileUploadDialog(supported_formats=formats)
        self.assertEqual(dialog.supported_formats, formats)
    
    @patch('rich.prompt.Prompt.ask')
    def test_show_file_input_success(self, mock_ask):
        """测试文件输入成功"""
        mock_ask.return_value = '/path/to/resume.pdf'
        
        result = self.dialog.show_file_input()
        self.assertEqual(result, '/path/to/resume.pdf')
    
    @patch('rich.prompt.Prompt.ask')
    def test_show_file_input_empty(self, mock_ask):
        """测试空输入"""
        mock_ask.return_value = ''
        
        result = self.dialog.show_file_input()
        self.assertIsNone(result)
    
    @patch('rich.prompt.Prompt.ask')
    def test_show_file_input_cancelled(self, mock_ask):
        """测试取消输入"""
        mock_ask.side_effect = KeyboardInterrupt()
        
        result = self.dialog.show_file_input()
        self.assertIsNone(result)
    
    def test_show_upload_progress(self):
        """测试显示上传进度"""
        progress = self.dialog.show_upload_progress("test.pdf")
        self.assertIsNotNone(progress)
        self.assertIn("test.pdf", progress.title)
    
    @patch('rich.console.Console.print')
    def test_show_success_message(self, mock_print):
        """测试显示成功消息"""
        resume_info = {
            'filename': 'test.pdf',
            'file_type': 'pdf',
            'file_size': 1024,
            'word_count': 100
        }
        
        self.dialog.show_success_message(resume_info)
        mock_print.assert_called_once()
    
    @patch('rich.console.Console.print')
    def test_show_error_message(self, mock_print):
        """测试显示错误消息"""
        error_msg = "文件不存在"
        
        self.dialog.show_error_message(error_msg)
        mock_print.assert_called_once()


class TestResumeTable(unittest.TestCase):
    """简历表格测试"""
    
    def setUp(self):
        self.table = ResumeTable()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.table.title, "简历列表")
        self.assertEqual(len(self.table.headers), 6)
        self.assertIn("文件名", self.table.headers)
        self.assertIn("格式", self.table.headers)
    
    def test_add_resume_row(self):
        """测试添加简历行"""
        resume_data = {
            'id': 'test-123',
            'filename': 'resume.pdf',
            'file_type': 'pdf',
            'file_size': 2048,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'metadata': {'word_count': 150}
        }
        
        self.table.add_resume_row(resume_data)
        self.assertEqual(len(self.table.rows), 1)
        
        # 验证行内容
        row = self.table.rows[0]
        self.assertEqual(row[1], 'resume.pdf')  # 文件名
        self.assertEqual(row[2], 'PDF')  # 格式（大写）
        self.assertEqual(row[3], '2.0 KB')  # 文件大小格式化
        self.assertEqual(row[5], '✅ 已解析')  # 状态
    
    def test_file_size_formatting(self):
        """测试文件大小格式化"""
        # 测试字节
        resume_data = {'id': '1', 'filename': 'small.pdf', 'file_size': 500, 'created_at': datetime.now()}
        self.table.add_resume_row(resume_data)
        self.assertEqual(self.table.rows[0][3], '500 B')
        
        # 清空并测试KB
        self.table.clear()
        resume_data['file_size'] = 1536  # 1.5 KB
        self.table.add_resume_row(resume_data)
        self.assertEqual(self.table.rows[0][3], '1.5 KB')
        
        # 清空并测试MB
        self.table.clear()
        resume_data['file_size'] = 2097152  # 2 MB
        self.table.add_resume_row(resume_data)
        self.assertEqual(self.table.rows[0][3], '2.0 MB')


class TestResumeDetailPanel(unittest.TestCase):
    """简历详情面板测试"""
    
    def setUp(self):
        self.panel = ResumeDetailPanel()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.panel.title, "简历详情")
        self.assertEqual(self.panel.border_style, "blue")
    
    def test_set_resume_data(self):
        """测试设置简历数据"""
        resume_data = {
            'filename': 'test_resume.pdf',
            'file_type': 'pdf',
            'file_size': 1024,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'metadata': {
                'char_count': 1000,
                'word_count': 200
            }
        }
        
        result = self.panel.set_resume_data(resume_data)
        self.assertEqual(result, self.panel)  # 返回自身用于链式调用
        
        # 验证内容被添加
        self.assertGreater(len(self.panel.lines), 0)
    
    def test_format_file_size(self):
        """测试文件大小格式化"""
        # 测试字节
        self.assertEqual(self.panel._format_file_size(500), '500 B')
        
        # 测试KB
        self.assertEqual(self.panel._format_file_size(1536), '1.5 KB')
        
        # 测试MB
        self.assertEqual(self.panel._format_file_size(2097152), '2.0 MB')
    
    def test_format_datetime(self):
        """测试日期时间格式化"""
        dt = datetime(2023, 1, 1, 12, 30, 45)
        formatted = self.panel._format_datetime(dt)
        self.assertEqual(formatted, '2023-01-01 12:30:45')
        
        # 测试非datetime对象
        formatted = self.panel._format_datetime('2023-01-01')
        self.assertEqual(formatted, '2023-01-01')
        
        # 测试None
        formatted = self.panel._format_datetime(None)
        self.assertEqual(formatted, 'N/A')


class TestComponentFactory(unittest.TestCase):
    """组件工厂测试"""
    
    def test_create_resume_table(self):
        """测试创建简历表格"""
        table = ComponentFactory.create_resume_table()
        self.assertIsInstance(table, ResumeTable)
    
    def test_create_file_upload_dialog(self):
        """测试创建文件上传对话框"""
        dialog = ComponentFactory.create_file_upload_dialog()
        self.assertIsInstance(dialog, FileUploadDialog)
        
        # 测试自定义格式
        formats = ['pdf', 'txt']
        dialog = ComponentFactory.create_file_upload_dialog(formats)
        self.assertEqual(dialog.supported_formats, formats)
    
    def test_create_resume_detail_panel(self):
        """测试创建简历详情面板"""
        panel = ComponentFactory.create_resume_detail_panel()
        self.assertIsInstance(panel, ResumeDetailPanel)
    
    def test_create_data_table(self):
        """测试创建数据表格"""
        table = ComponentFactory.create_data_table("测试表格")
        self.assertIsInstance(table, DataTable)
        self.assertEqual(table.title, "测试表格")
    
    def test_create_info_panel(self):
        """测试创建信息面板"""
        panel = ComponentFactory.create_info_panel("测试信息", "blue")
        self.assertIsInstance(panel, InfoPanel)
        self.assertEqual(panel.title, "测试信息")
        self.assertEqual(panel.border_style, "blue")


class TestDataTable(unittest.TestCase):
    """数据表格基础测试"""
    
    def setUp(self):
        self.table = DataTable("测试表格", "cyan")
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.table.title, "测试表格")
        self.assertEqual(self.table.style, "cyan")
        self.assertEqual(len(self.table.headers), 0)
        self.assertEqual(len(self.table.rows), 0)
    
    def test_add_column(self):
        """测试添加列"""
        result = self.table.add_column("测试列", "white")
        self.assertEqual(result, self.table)  # 返回自身
        self.assertIn("测试列", self.table.headers)
    
    def test_add_row(self):
        """测试添加行"""
        self.table.add_column("列1").add_column("列2")
        result = self.table.add_row("值1", "值2")
        self.assertEqual(result, self.table)  # 返回自身
        self.assertEqual(len(self.table.rows), 1)
        self.assertEqual(self.table.rows[0], ["值1", "值2"])
    
    def test_add_rows(self):
        """测试批量添加行"""
        self.table.add_column("列1").add_column("列2")
        rows_data = [["a", "b"], ["c", "d"]]
        result = self.table.add_rows(rows_data)
        self.assertEqual(result, self.table)  # 返回自身
        self.assertEqual(len(self.table.rows), 2)
    
    def test_clear(self):
        """测试清空数据"""
        self.table.add_column("列1").add_row("值1")
        self.assertEqual(len(self.table.rows), 1)
        
        result = self.table.clear()
        self.assertEqual(result, self.table)  # 返回自身
        self.assertEqual(len(self.table.rows), 0)


class TestInfoPanel(unittest.TestCase):
    """信息面板基础测试"""
    
    def setUp(self):
        self.panel = InfoPanel("测试面板", "green")
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.panel.title, "测试面板")
        self.assertEqual(self.panel.border_style, "green")
        self.assertEqual(len(self.panel.lines), 0)
    
    def test_add_header(self):
        """测试添加标题"""
        result = self.panel.add_header("测试标题")
        self.assertEqual(result, self.panel)  # 返回自身
        self.assertGreater(len(self.panel.lines), 0)
    
    def test_add_line(self):
        """测试添加行"""
        result = self.panel.add_line("测试内容", "white")
        self.assertEqual(result, self.panel)  # 返回自身
        self.assertGreater(len(self.panel.lines), 0)
    
    def test_add_key_value(self):
        """测试添加键值对"""
        result = self.panel.add_key_value("键", "值")
        self.assertEqual(result, self.panel)  # 返回自身
        self.assertGreater(len(self.panel.lines), 0)
    
    def test_add_separator(self):
        """测试添加分隔符"""
        result = self.panel.add_separator()
        self.assertEqual(result, self.panel)  # 返回自身
        self.assertGreater(len(self.panel.lines), 0)
    
    def test_clear(self):
        """测试清空内容"""
        self.panel.add_line("测试")
        self.assertGreater(len(self.panel.lines), 0)
        
        result = self.panel.clear()
        self.assertEqual(result, self.panel)  # 返回自身
        self.assertEqual(len(self.panel.lines), 0)


if __name__ == '__main__':
    unittest.main()