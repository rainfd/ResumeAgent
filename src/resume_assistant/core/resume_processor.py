"""简历文件处理器

提供PDF和Markdown格式简历的解析、存储和管理功能。
"""

import os
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

# 第三方库导入
try:
    import PyPDF2
    HAS_PDF_SUPPORT = True
except ImportError:
    try:
        import pdfplumber
        HAS_PDF_SUPPORT = True
        USE_PDFPLUMBER = True
    except ImportError:
        HAS_PDF_SUPPORT = False
        USE_PDFPLUMBER = False

try:
    import markdown
    HAS_MARKDOWN_SUPPORT = True
except ImportError:
    HAS_MARKDOWN_SUPPORT = False

from ..utils import get_logger
from ..utils.errors import ResumeProcessingError, UnsupportedFormatError

logger = get_logger(__name__)


@dataclass
class Resume:
    """简历数据模型"""
    id: str
    filename: str
    file_type: str  # 'pdf' | 'markdown'
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None
    file_size: Optional[int] = None


class PDFParser:
    """PDF文件解析器"""
    
    @staticmethod
    def parse(file_path: str) -> str:
        """解析PDF文件内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            str: 提取的文本内容
            
        Raises:
            ResumeProcessingError: PDF解析失败
            UnsupportedFormatError: 不支持PDF格式
        """
        if not HAS_PDF_SUPPORT:
            raise UnsupportedFormatError("PDF解析库未安装。请安装: pip install PyPDF2 或 pdfplumber")
        
        if not os.path.exists(file_path):
            raise ResumeProcessingError(f"文件不存在: {file_path}")
        
        try:
            if 'USE_PDFPLUMBER' in globals() and USE_PDFPLUMBER:
                return PDFParser._parse_with_pdfplumber(file_path)
            else:
                return PDFParser._parse_with_pypdf2(file_path)
        except Exception as e:
            logger.error(f"PDF解析失败 {file_path}: {e}")
            raise ResumeProcessingError(f"PDF解析失败: {e}")
    
    @staticmethod
    def _parse_with_pypdf2(file_path: str) -> str:
        """使用PyPDF2解析PDF"""
        content = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                content.append(page.extract_text())
        return '\n'.join(content)
    
    @staticmethod
    def _parse_with_pdfplumber(file_path: str) -> str:
        """使用pdfplumber解析PDF"""
        import pdfplumber
        content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content.append(text)
        return '\n'.join(content)


class MarkdownParser:
    """Markdown文件解析器"""
    
    @staticmethod
    def parse(file_path: str) -> str:
        """解析Markdown文件内容
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            str: 文件内容
            
        Raises:
            ResumeProcessingError: 文件读取失败
        """
        if not os.path.exists(file_path):
            raise ResumeProcessingError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 如果安装了markdown库，可以转换为HTML或提取纯文本
            if HAS_MARKDOWN_SUPPORT:
                # 这里可以添加Markdown处理逻辑，如转换为纯文本
                pass
            
            return content
        except Exception as e:
            logger.error(f"Markdown解析失败 {file_path}: {e}")
            raise ResumeProcessingError(f"Markdown解析失败: {e}")


class ResumeStorage:
    """简历存储管理器"""
    
    def __init__(self, storage_dir: str = "data/resumes"):
        """初始化存储管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 简历元数据存储文件
        self.metadata_file = self.storage_dir / "resumes_metadata.json"
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """加载简历元数据"""
        import json
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
        
        return {}
    
    def _save_metadata(self):
        """保存简历元数据"""
        import json
        
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise ResumeProcessingError(f"保存元数据失败: {e}")
    
    def save_resume(self, resume: Resume) -> bool:
        """保存简历到存储
        
        Args:
            resume: 简历对象
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 保存简历内容到文件
            content_file = self.storage_dir / f"{resume.id}.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(resume.content)
            
            # 更新元数据
            self._metadata[resume.id] = {
                'id': resume.id,
                'filename': resume.filename,
                'file_type': resume.file_type,
                'metadata': resume.metadata,
                'created_at': resume.created_at.isoformat(),
                'updated_at': resume.updated_at.isoformat(),
                'file_path': resume.file_path,
                'file_size': resume.file_size,
                'content_file': str(content_file)
            }
            
            self._save_metadata()
            logger.info(f"简历保存成功: {resume.filename}")
            return True
            
        except Exception as e:
            logger.error(f"保存简历失败: {e}")
            return False
    
    def load_resume(self, resume_id: str) -> Optional[Resume]:
        """加载指定ID的简历
        
        Args:
            resume_id: 简历ID
            
        Returns:
            Resume: 简历对象，不存在返回None
        """
        if resume_id not in self._metadata:
            return None
        
        try:
            meta = self._metadata[resume_id]
            
            # 读取简历内容
            content_file = Path(meta['content_file'])
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                logger.warning(f"简历内容文件不存在: {content_file}")
                content = ""
            
            return Resume(
                id=meta['id'],
                filename=meta['filename'],
                file_type=meta['file_type'],
                content=content,
                metadata=meta['metadata'],
                created_at=datetime.fromisoformat(meta['created_at']),
                updated_at=datetime.fromisoformat(meta['updated_at']),
                file_path=meta.get('file_path'),
                file_size=meta.get('file_size')
            )
            
        except Exception as e:
            logger.error(f"加载简历失败 {resume_id}: {e}")
            return None
    
    def list_resumes(self) -> List[Resume]:
        """获取所有简历列表
        
        Returns:
            List[Resume]: 简历列表
        """
        resumes = []
        for resume_id in self._metadata:
            resume = self.load_resume(resume_id)
            if resume:
                resumes.append(resume)
        
        # 按创建时间倒序排列
        resumes.sort(key=lambda x: x.created_at, reverse=True)
        return resumes
    
    def delete_resume(self, resume_id: str) -> bool:
        """删除指定简历
        
        Args:
            resume_id: 简历ID
            
        Returns:
            bool: 删除成功返回True
        """
        if resume_id not in self._metadata:
            return False
        
        try:
            meta = self._metadata[resume_id]
            
            # 删除内容文件
            content_file = Path(meta['content_file'])
            if content_file.exists():
                content_file.unlink()
            
            # 删除元数据
            del self._metadata[resume_id]
            self._save_metadata()
            
            logger.info(f"简历删除成功: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除简历失败 {resume_id}: {e}")
            return False


class ResumeProcessor:
    """简历处理器主类"""
    
    def __init__(self, storage_dir: str = "data/resumes"):
        """初始化简历处理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage = ResumeStorage(storage_dir)
        self.parsers = {
            'pdf': PDFParser(),
            'markdown': MarkdownParser(),
            'md': MarkdownParser()  # .md文件也使用Markdown解析器
        }
    
    def upload_resume(self, file_path: str, custom_filename: Optional[str] = None) -> Resume:
        """上传并处理简历文件
        
        Args:
            file_path: 简历文件路径
            custom_filename: 自定义文件名（可选）
            
        Returns:
            Resume: 处理后的简历对象
            
        Raises:
            ResumeProcessingError: 处理失败
            UnsupportedFormatError: 不支持的文件格式
        """
        if not os.path.exists(file_path):
            raise ResumeProcessingError(f"文件不存在: {file_path}")
        
        # 确定文件类型
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        if file_ext not in self.parsers:
            raise UnsupportedFormatError(f"不支持的文件格式: {file_ext}")
        
        # 解析文件内容
        try:
            content = self.parsers[file_ext].parse(file_path)
        except Exception as e:
            raise ResumeProcessingError(f"文件解析失败: {e}")
        
        # 创建简历对象
        resume_id = str(uuid.uuid4())
        filename = custom_filename or Path(file_path).name
        file_stats = os.stat(file_path)
        
        resume = Resume(
            id=resume_id,
            filename=filename,
            file_type=file_ext,
            content=content,
            metadata={
                'original_path': file_path,
                'file_extension': file_ext,
                'word_count': len(content.split()) if content else 0,
                'char_count': len(content) if content else 0
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            file_path=file_path,
            file_size=file_stats.st_size
        )
        
        # 保存到存储
        if not self.storage.save_resume(resume):
            raise ResumeProcessingError("简历保存失败")
        
        logger.info(f"简历上传成功: {filename} ({file_ext})")
        return resume
    
    def get_resume(self, resume_id: str) -> Optional[Resume]:
        """获取指定简历
        
        Args:
            resume_id: 简历ID
            
        Returns:
            Resume: 简历对象，不存在返回None
        """
        return self.storage.load_resume(resume_id)
    
    def list_resumes(self) -> List[Resume]:
        """获取所有简历列表
        
        Returns:
            List[Resume]: 简历列表
        """
        return self.storage.list_resumes()
    
    def delete_resume(self, resume_id: str) -> bool:
        """删除简历
        
        Args:
            resume_id: 简历ID
            
        Returns:
            bool: 删除成功返回True
        """
        return self.storage.delete_resume(resume_id)
    
    def update_resume_content(self, resume_id: str, new_content: str) -> bool:
        """更新简历内容
        
        Args:
            resume_id: 简历ID
            new_content: 新的简历内容
            
        Returns:
            bool: 更新成功返回True
        """
        resume = self.storage.load_resume(resume_id)
        if not resume:
            return False
        
        # 更新内容和元数据
        resume.content = new_content
        resume.updated_at = datetime.now()
        resume.metadata['word_count'] = len(new_content.split()) if new_content else 0
        resume.metadata['char_count'] = len(new_content) if new_content else 0
        
        return self.storage.save_resume(resume)
    
    @property
    def supported_formats(self) -> List[str]:
        """获取支持的文件格式列表
        
        Returns:
            List[str]: 支持的格式列表
        """
        formats = []
        if HAS_PDF_SUPPORT:
            formats.append('pdf')
        if HAS_MARKDOWN_SUPPORT or True:  # Markdown不需要额外库
            formats.extend(['markdown', 'md'])
        return formats
    
    def get_format_info(self) -> Dict[str, bool]:
        """获取格式支持信息
        
        Returns:
            Dict[str, bool]: 格式支持状态
        """
        return {
            'pdf': HAS_PDF_SUPPORT,
            'markdown': True,  # 总是支持
            'md': True
        }