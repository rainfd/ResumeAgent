"""职位管理模块

管理目标职位信息，支持AI分析功能
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path

from ..utils import get_logger
from ..utils.errors import ValidationError, ResumeProcessingError

logger = get_logger(__name__)


@dataclass
class Job:
    """职位数据模型"""
    id: str
    title: str
    company: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    source_url: Optional[str] = None  # 职位来源链接
    status: str = "active"  # active, archived, applied
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class JobStorage:
    """职位存储管理器"""
    
    def __init__(self, storage_dir: str = "data/jobs"):
        """初始化存储管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 职位元数据存储文件
        self.metadata_file = self.storage_dir / "jobs_metadata.json"
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """加载职位元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载职位元数据失败: {e}")
        return {}
    
    def _save_metadata(self):
        """保存职位元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存职位元数据失败: {e}")
            raise ResumeProcessingError(f"保存职位元数据失败: {e}")
    
    def save_job(self, job: Job) -> bool:
        """保存职位到存储
        
        Args:
            job: 职位对象
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 保存职位内容到文件
            content_file = self.storage_dir / f"{job.id}.json"
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(job), f, ensure_ascii=False, indent=2, default=str)
            
            # 更新元数据
            self._metadata[job.id] = {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'updated_at': job.updated_at.isoformat(),
                'content_file': str(content_file)
            }
            
            self._save_metadata()
            logger.info(f"职位保存成功: {job.title} @ {job.company}")
            return True
            
        except Exception as e:
            logger.error(f"保存职位失败: {e}")
            return False
    
    def load_job(self, job_id: str) -> Optional[Job]:
        """加载指定ID的职位
        
        Args:
            job_id: 职位ID
            
        Returns:
            Job: 职位对象，不存在返回None
        """
        if job_id not in self._metadata:
            return None
        
        try:
            meta = self._metadata[job_id]
            
            # 读取职位内容
            content_file = Path(meta['content_file'])
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换日期字符串
                if isinstance(data.get('created_at'), str):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if isinstance(data.get('updated_at'), str):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                return Job(**data)
            else:
                logger.warning(f"职位内容文件不存在: {content_file}")
                return None
            
        except Exception as e:
            logger.error(f"加载职位失败 {job_id}: {e}")
            return None
    
    def list_jobs(self, status: Optional[str] = None) -> List[Job]:
        """获取所有职位列表
        
        Args:
            status: 筛选特定状态的职位
            
        Returns:
            List[Job]: 职位列表
        """
        jobs = []
        for job_id in self._metadata:
            # 应用状态筛选
            if status and self._metadata[job_id].get('status') != status:
                continue
                
            job = self.load_job(job_id)
            if job:
                jobs.append(job)
        
        # 按创建时间倒序排列
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs
    
    def delete_job(self, job_id: str) -> bool:
        """删除指定职位
        
        Args:
            job_id: 职位ID
            
        Returns:
            bool: 删除成功返回True
        """
        if job_id not in self._metadata:
            return False
        
        try:
            meta = self._metadata[job_id]
            
            # 删除内容文件
            content_file = Path(meta['content_file'])
            if content_file.exists():
                content_file.unlink()
            
            # 删除元数据
            del self._metadata[job_id]
            self._save_metadata()
            
            logger.info(f"职位删除成功: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除职位失败 {job_id}: {e}")
            return False


class JobManager:
    """职位管理器主类"""
    
    def __init__(self, storage_dir: str = "data/jobs"):
        """初始化职位管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage = JobStorage(storage_dir)
    
    def create_job(self, title: str, company: str, description: str, requirements: str,
                   location: Optional[str] = None, salary: Optional[str] = None,
                   experience_level: Optional[str] = None, source_url: Optional[str] = None) -> Job:
        """创建新职位
        
        Args:
            title: 职位名称
            company: 公司名称
            description: 职位描述
            requirements: 职位要求
            location: 工作地点
            salary: 薪资范围
            experience_level: 经验要求
            source_url: 来源链接
            
        Returns:
            Job: 创建的职位对象
            
        Raises:
            ValidationError: 输入验证失败
        """
        # 输入验证
        if not title or not title.strip():
            raise ValidationError("职位名称不能为空", field="title")
        
        if not company or not company.strip():
            raise ValidationError("公司名称不能为空", field="company")
        
        if not description or not description.strip():
            raise ValidationError("职位描述不能为空", field="description")
        
        if not requirements or not requirements.strip():
            raise ValidationError("职位要求不能为空", field="requirements")
        
        # 创建职位对象
        job = Job(
            id=str(uuid.uuid4()),
            title=title.strip(),
            company=company.strip(),
            description=description.strip(),
            requirements=requirements.strip(),
            location=location.strip() if location else None,
            salary=salary.strip() if salary else None,
            experience_level=experience_level.strip() if experience_level else None,
            source_url=source_url.strip() if source_url else None
        )
        
        # 保存到存储
        if not self.storage.save_job(job):
            raise ResumeProcessingError("职位保存失败")
        
        logger.info(f"职位创建成功: {job.title} @ {job.company}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取指定职位
        
        Args:
            job_id: 职位ID
            
        Returns:
            Job: 职位对象，不存在返回None
        """
        return self.storage.load_job(job_id)
    
    def list_jobs(self, status: Optional[str] = None) -> List[Job]:
        """获取职位列表
        
        Args:
            status: 筛选特定状态的职位
            
        Returns:
            List[Job]: 职位列表
        """
        return self.storage.list_jobs(status)
    
    def update_job(self, job_id: str, **kwargs) -> bool:
        """更新职位信息
        
        Args:
            job_id: 职位ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新成功返回True
        """
        job = self.storage.load_job(job_id)
        if not job:
            return False
        
        # 更新字段
        updateable_fields = ['title', 'company', 'description', 'requirements', 
                           'location', 'salary', 'experience_level', 'source_url', 'status']
        
        updated = False
        for field, value in kwargs.items():
            if field in updateable_fields and hasattr(job, field):
                setattr(job, field, value)
                updated = True
        
        if updated:
            job.updated_at = datetime.now()
            return self.storage.save_job(job)
        
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """删除职位
        
        Args:
            job_id: 职位ID
            
        Returns:
            bool: 删除成功返回True
        """
        return self.storage.delete_job(job_id)
    
    def create_sample_jobs(self) -> List[Job]:
        """创建示例职位数据
        
        Returns:
            List[Job]: 创建的示例职位列表
        """
        sample_jobs_data = [
            {
                "title": "Python后端开发工程师",
                "company": "科技有限公司A",
                "description": "负责公司核心业务系统的后端开发，包括API设计、数据库优化、微服务架构等工作。",
                "requirements": "1. 3年以上Python开发经验；2. 熟悉Django/Flask框架；3. 熟悉MySQL/Redis；4. 了解微服务架构；5. 有团队协作经验。",
                "location": "北京",
                "salary": "20-35K",
                "experience_level": "3-5年"
            },
            {
                "title": "AI算法工程师",
                "company": "人工智能科技B",
                "description": "负责机器学习算法的研发和优化，包括深度学习模型训练、算法性能优化等。",
                "requirements": "1. 硕士以上学历，计算机相关专业；2. 熟悉Python、TensorFlow/PyTorch；3. 有深度学习项目经验；4. 了解NLP或CV领域；5. 英语读写能力强。",
                "location": "上海",
                "salary": "25-45K",
                "experience_level": "2-4年"
            },
            {
                "title": "全栈开发工程师",
                "company": "互联网公司C",
                "description": "负责Web应用的前后端开发，包括用户界面设计、后端API开发、数据库设计等。",
                "requirements": "1. 熟悉JavaScript、HTML/CSS；2. 了解React/Vue.js框架；3. 有Node.js或Python后端经验；4. 熟悉Git版本控制；5. 有产品思维。",
                "location": "深圳",
                "salary": "18-30K",
                "experience_level": "2-3年"
            }
        ]
        
        created_jobs = []
        for job_data in sample_jobs_data:
            try:
                job = self.create_job(**job_data)
                created_jobs.append(job)
            except Exception as e:
                logger.error(f"创建示例职位失败: {e}")
        
        logger.info(f"创建了 {len(created_jobs)} 个示例职位")
        return created_jobs