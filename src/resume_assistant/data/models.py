"""Data models for Resume Assistant."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


@dataclass
class JobInfo:
    """职位信息模型"""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    company: str = ""
    description: str = ""
    requirements: str = ""
    skills: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResumeContent:
    """简历内容模型"""
    id: Optional[int] = None
    name: str = ""
    file_path: str = ""
    content: str = ""
    personal_info: Dict[str, str] = field(default_factory=dict)
    education: List[Dict[str, str]] = field(default_factory=list)
    experience: List[Dict[str, str]] = field(default_factory=list)
    projects: List[Dict[str, str]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class AgentType(Enum):
    """AI Agent 类型枚举"""
    GENERAL = "general"
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    CREATIVE = "creative"
    SALES = "sales"
    CUSTOM = "custom"


@dataclass
class AIAgent:
    """AI Agent 配置模型"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    agent_type: AgentType = AgentType.GENERAL
    prompt_template: str = ""
    is_builtin: bool = False
    usage_count: int = 0
    average_rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type.value if isinstance(self.agent_type, AgentType) else self.agent_type,
            'prompt_template': self.prompt_template,
            'is_builtin': self.is_builtin,
            'usage_count': self.usage_count,
            'average_rating': self.average_rating,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'AIAgent':
        """从字典创建实例"""
        # 处理日期时间字段
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
            
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()
        
        # 处理 agent_type 枚举
        agent_type = data.get('agent_type', 'general')
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type)
            except ValueError:
                agent_type = AgentType.GENERAL
        
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            agent_type=agent_type,
            prompt_template=data.get('prompt_template', ''),
            is_builtin=data.get('is_builtin', False),
            usage_count=data.get('usage_count', 0),
            average_rating=data.get('average_rating', 0.0),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class AgentUsageHistory:
    """Agent 使用历史模型"""
    id: Optional[int] = None
    agent_id: int = 0
    analysis_id: int = 0
    rating: Optional[float] = None  # 用户评分 1-5
    feedback: str = ""  # 用户反馈
    execution_time: float = 0.0  # 执行时间（秒）
    success: bool = True  # 是否执行成功
    error_message: str = ""  # 错误信息（如果有）
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'analysis_id': self.analysis_id,
            'rating': self.rating,
            'feedback': self.feedback,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'AgentUsageHistory':
        """从字典创建实例"""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
        
        return cls(
            id=data.get('id'),
            agent_id=data.get('agent_id', 0),
            analysis_id=data.get('analysis_id', 0),
            rating=data.get('rating'),
            feedback=data.get('feedback', ''),
            execution_time=data.get('execution_time', 0.0),
            success=data.get('success', True),
            error_message=data.get('error_message', ''),
            created_at=created_at
        )


@dataclass
class MatchAnalysis:
    """匹配分析结果模型"""
    id: Optional[int] = None
    job_id: int = 0
    resume_id: int = 0
    agent_id: Optional[int] = None  # 使用的 Agent ID
    overall_score: float = 0.0
    skill_match_score: float = 0.0
    experience_score: float = 0.0
    keyword_coverage: float = 0.0
    missing_skills: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    raw_response: str = ""  # AI 原始响应
    execution_time: float = 0.0  # 分析执行时间
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationSuggestion:
    """优化建议模型"""
    section: str = ""
    original_text: str = ""
    suggested_text: str = ""
    reason: str = ""
    priority: int = 0


@dataclass
class GreetingMessage:
    """打招呼语模型"""
    id: Optional[int] = None
    job_id: int = 0
    resume_id: int = 0
    content: str = ""
    version: int = 1
    is_custom: bool = False
    created_at: datetime = field(default_factory=datetime.now)