"""Data models for Resume Assistant."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


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


@dataclass
class MatchAnalysis:
    """匹配分析结果模型"""
    id: Optional[int] = None
    job_id: int = 0
    resume_id: int = 0
    overall_score: float = 0.0
    skill_match_score: float = 0.0
    experience_score: float = 0.0
    keyword_coverage: float = 0.0
    missing_skills: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
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