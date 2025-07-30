"""简历处理器单元测试"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from resume_assistant.core.resume_processor import (
    ResumeProcessor, PDFParser, MarkdownParser, 
    ResumeStorage, Resume
)
from resume_assistant.utils.errors import (
    ResumeProcessingError, UnsupportedFormatError
)


class TestPDFParser(unittest.TestCase):
    """PDF解析器测试"""
    
    def setUp(self):
        self.parser = PDFParser()
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        with self.assertRaises(ResumeProcessingError):
            self.parser.parse("nonexistent.pdf")
    
    @patch('resume_assistant.core.resume_processor.HAS_PDF_SUPPORT', False)
    def test_parse_without_pdf_support(self):
        """测试没有PDF支持库时的错误"""
        with self.assertRaises(UnsupportedFormatError):
            self.parser.parse("dummy.pdf")


class TestMarkdownParser(unittest.TestCase):
    """Markdown解析器测试"""
    
    def setUp(self):
        self.parser = MarkdownParser()
    
    def test_parse_markdown_file(self):
        """测试解析Markdown文件"""
        # 创建临时Markdown文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_content = "# 测试简历\n\n这是一个测试简历内容。"
            f.write(test_content)
            temp_path = f.name
        
        try:
            content = self.parser.parse(temp_path)
            self.assertEqual(content, test_content)
        finally:
            os.unlink(temp_path)
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        with self.assertRaises(ResumeProcessingError):
            self.parser.parse("nonexistent.md")


class TestResumeStorage(unittest.TestCase):
    """简历存储测试"""
    
    def setUp(self):
        # 创建临时存储目录
        self.temp_dir = tempfile.mkdtemp()
        self.storage = ResumeStorage(self.temp_dir)
    
    def tearDown(self):
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_resume(self):
        """测试保存和加载简历"""
        # 创建测试简历
        resume = Resume(
            id="test-123",
            filename="test_resume.md",
            file_type="md",
            content="# 测试简历\n\n测试内容",
            metadata={"word_count": 4, "char_count": 15},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            file_path="/tmp/test.md",
            file_size=100
        )
        
        # 保存简历
        result = self.storage.save_resume(resume)
        self.assertTrue(result)
        
        # 加载简历
        loaded_resume = self.storage.load_resume("test-123")
        self.assertIsNotNone(loaded_resume)
        self.assertEqual(loaded_resume.id, "test-123")
        self.assertEqual(loaded_resume.filename, "test_resume.md")
        self.assertEqual(loaded_resume.content, "# 测试简历\n\n测试内容")
    
    def test_list_resumes(self):
        """测试列出所有简历"""
        # 创建多个测试简历
        resumes = []
        for i in range(3):
            resume = Resume(
                id=f"test-{i}",
                filename=f"resume_{i}.md",
                file_type="md",
                content=f"简历内容 {i}",
                metadata={"word_count": 2},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            resumes.append(resume)
            self.storage.save_resume(resume)
        
        # 获取列表
        resume_list = self.storage.list_resumes()
        self.assertEqual(len(resume_list), 3)
        
        # 验证按时间倒序排列
        self.assertTrue(resume_list[0].created_at >= resume_list[1].created_at)
    
    def test_delete_resume(self):
        """测试删除简历"""
        # 创建测试简历
        resume = Resume(
            id="test-delete",
            filename="delete_me.md",
            file_type="md",
            content="要删除的简历",
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存并验证存在
        self.storage.save_resume(resume)
        self.assertIsNotNone(self.storage.load_resume("test-delete"))
        
        # 删除并验证不存在
        result = self.storage.delete_resume("test-delete")
        self.assertTrue(result)
        self.assertIsNone(self.storage.load_resume("test-delete"))
    
    def test_delete_nonexistent_resume(self):
        """测试删除不存在的简历"""
        result = self.storage.delete_resume("nonexistent")
        self.assertFalse(result)


class TestResumeProcessor(unittest.TestCase):
    """简历处理器测试"""
    
    def setUp(self):
        # 创建临时存储目录
        self.temp_dir = tempfile.mkdtemp()
        self.processor = ResumeProcessor(self.temp_dir)
    
    def tearDown(self):
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_upload_markdown_resume(self):
        """测试上传Markdown简历"""
        # 创建临时Markdown文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_content = "# 张三简历\n\n## 工作经验\n\n- 软件工程师"
            f.write(test_content)
            temp_path = f.name
        
        try:
            # 上传简历
            resume = self.processor.upload_resume(temp_path)
            
            # 验证结果
            self.assertIsNotNone(resume)
            self.assertEqual(resume.file_type, "md")
            self.assertEqual(resume.content, test_content)
            self.assertGreater(resume.metadata['word_count'], 0)
            self.assertGreater(resume.metadata['char_count'], 0)
            
            # 验证保存到存储
            loaded_resume = self.processor.get_resume(resume.id)
            self.assertIsNotNone(loaded_resume)
            self.assertEqual(loaded_resume.content, test_content)
            
        finally:
            os.unlink(temp_path)
    
    def test_upload_unsupported_format(self):
        """测试上传不支持的格式"""
        # 创建临时文件（不支持的格式）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("测试内容")
            temp_path = f.name
        
        try:
            with self.assertRaises(UnsupportedFormatError):
                self.processor.upload_resume(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_upload_nonexistent_file(self):
        """测试上传不存在的文件"""
        with self.assertRaises(ResumeProcessingError):
            self.processor.upload_resume("nonexistent.md")
    
    def test_list_resumes(self):
        """测试获取简历列表"""
        # 上传几个简历
        resumes = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(f"# 简历 {i}")
                temp_path = f.name
            
            try:
                resume = self.processor.upload_resume(temp_path, f"resume_{i}.md")
                resumes.append(resume)
            finally:
                os.unlink(temp_path)
        
        # 获取列表
        resume_list = self.processor.list_resumes()
        self.assertEqual(len(resume_list), 2)
    
    def test_delete_resume(self):
        """测试删除简历"""
        # 上传简历
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("要删除的简历")
            temp_path = f.name
        
        try:
            resume = self.processor.upload_resume(temp_path)
            resume_id = resume.id
            
            # 验证存在
            self.assertIsNotNone(self.processor.get_resume(resume_id))
            
            # 删除
            result = self.processor.delete_resume(resume_id)
            self.assertTrue(result)
            
            # 验证已删除
            self.assertIsNone(self.processor.get_resume(resume_id))
            
        finally:
            os.unlink(temp_path)
    
    def test_update_resume_content(self):
        """测试更新简历内容"""
        # 上传简历
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("原始内容")
            temp_path = f.name
        
        try:
            resume = self.processor.upload_resume(temp_path)
            resume_id = resume.id
            
            # 更新内容
            new_content = "更新后的内容"
            result = self.processor.update_resume_content(resume_id, new_content)
            self.assertTrue(result)
            
            # 验证内容已更新
            updated_resume = self.processor.get_resume(resume_id)
            self.assertEqual(updated_resume.content, new_content)
            
        finally:
            os.unlink(temp_path)
    
    def test_supported_formats(self):
        """测试支持的格式列表"""
        formats = self.processor.supported_formats
        self.assertIsInstance(formats, list)
        self.assertIn('md', formats)
        self.assertIn('markdown', formats)
    
    def test_format_info(self):
        """测试格式支持信息"""
        info = self.processor.get_format_info()
        self.assertIsInstance(info, dict)
        self.assertIn('pdf', info)
        self.assertIn('markdown', info)
        self.assertTrue(info['markdown'])


if __name__ == '__main__':
    unittest.main()