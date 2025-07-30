"""AI分析模块

基于DeepSeek API实现简历与职位的智能匹配分析
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union
import re

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from ..utils import get_logger
from ..utils.errors import AIServiceError, ValidationError, ConfigurationError
from ..config import get_settings

logger = get_logger(__name__)


@dataclass
class JobInfo:
    """职位信息数据模型"""
    id: str
    title: str
    company: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None


@dataclass
class AnalysisResult:
    """分析结果数据模型"""
    id: str
    resume_id: str
    job_id: str
    match_scores: Dict[str, float]  # 各项匹配度评分
    overall_score: float  # 总体匹配度
    suggestions: List[str]  # 优化建议
    matching_skills: List[str]  # 匹配的技能
    missing_skills: List[str]  # 缺失的技能
    strengths: List[str]  # 优势点
    weaknesses: List[str]  # 薄弱环节
    created_at: datetime
    analysis_version: str = "1.0"


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """初始化DeepSeek客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        if not HAS_HTTPX:
            raise ImportError("需要安装httpx库: pip install httpx")
        
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
    def _get_api_key(self) -> str:
        """从配置中获取API密钥"""
        settings = get_settings()
        api_key = getattr(settings, 'deepseek_api_key', None) or \
                 getattr(settings, 'RESUME_ASSISTANT_DEEPSEEK_API_KEY', None)
        
        if not api_key:
            raise ConfigurationError(
                "DeepSeek API密钥未配置。请设置环境变量 RESUME_ASSISTANT_DEEPSEEK_API_KEY 或在配置文件中设置 deepseek_api_key"
            )
        
        return api_key
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "deepseek-chat") -> str:
        """调用聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称
            
        Returns:
            str: AI响应内容
            
        Raises:
            AIServiceError: API调用失败
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise AIServiceError(
                    f"API请求失败: {response.status_code} - {response.text}",
                    service="deepseek",
                    api_error_code=str(response.status_code)
                )
            
            result = response.json()
            
            if "error" in result:
                raise AIServiceError(
                    f"API返回错误: {result['error'].get('message', 'Unknown error')}",
                    service="deepseek",
                    api_error_code=result['error'].get('code', 'unknown')
                )
            
            if not result.get("choices") or len(result["choices"]) == 0:
                raise AIServiceError("API返回空响应", service="deepseek")
            
            return result["choices"][0]["message"]["content"]
            
        except httpx.RequestError as e:
            raise AIServiceError(f"网络请求失败: {e}", service="deepseek")
        except json.JSONDecodeError as e:
            raise AIServiceError(f"API响应解析失败: {e}", service="deepseek")
        except Exception as e:
            if isinstance(e, AIServiceError):
                raise
            raise AIServiceError(f"未知错误: {e}", service="deepseek")
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'client'):
            self.client.close()


class MatchingEngine:
    """简历职位匹配引擎"""
    
    def __init__(self, deepseek_client: DeepSeekClient):
        """初始化匹配引擎
        
        Args:
            deepseek_client: DeepSeek API客户端
        """
        self.client = deepseek_client
    
    def analyze_match(self, resume_content: str, job_info: JobInfo) -> AnalysisResult:
        """分析简历与职位的匹配度
        
        Args:
            resume_content: 简历内容
            job_info: 职位信息
            
        Returns:
            AnalysisResult: 分析结果
            
        Raises:
            ValidationError: 输入验证失败
            AIServiceError: AI分析失败
        """
        # 输入验证
        if not resume_content or not resume_content.strip():
            raise ValidationError("简历内容不能为空", field="resume_content")
        
        if not job_info.title or not job_info.description:
            raise ValidationError("职位信息不完整", field="job_info")
        
        try:
            # 构建分析提示
            system_prompt = self._build_system_prompt()
            analysis_prompt = self._build_analysis_prompt(resume_content, job_info)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]
            
            # 调用AI进行分析
            logger.info(f"开始AI分析: 简历 vs 职位 {job_info.title}")
            ai_response = self.client.chat_completion(messages)
            
            # 解析AI响应
            analysis_data = self._parse_ai_response(ai_response)
            
            # 创建分析结果
            result = AnalysisResult(
                id=str(uuid.uuid4()),
                resume_id="",  # 将由调用者设置
                job_id=job_info.id,
                match_scores=analysis_data.get("match_scores", {}),
                overall_score=analysis_data.get("overall_score", 0.0),
                suggestions=analysis_data.get("suggestions", []),
                matching_skills=analysis_data.get("matching_skills", []),
                missing_skills=analysis_data.get("missing_skills", []),
                strengths=analysis_data.get("strengths", []),
                weaknesses=analysis_data.get("weaknesses", []),
                created_at=datetime.now()
            )
            
            logger.info(f"AI分析完成，总体匹配度: {result.overall_score:.1f}%")
            return result
            
        except Exception as e:
            if isinstance(e, (ValidationError, AIServiceError)):
                raise
            logger.error(f"AI分析过程中发生错误: {e}")
            raise AIServiceError(f"分析失败: {e}", service="matching_engine")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是一个专业的HR和简历分析专家。你的任务是分析简历与职位的匹配度，并提供详细的分析报告。

请严格按照以下JSON格式返回分析结果：

{
    "match_scores": {
        "技能匹配度": 85.0,
        "经验匹配度": 75.0,
        "教育背景": 90.0,
        "岗位契合度": 80.0
    },
    "overall_score": 82.5,
    "suggestions": [
        "建议补充相关项目经验",
        "可以学习更多行业相关技能"
    ],
    "matching_skills": ["Python", "机器学习", "数据分析"],
    "missing_skills": ["Kubernetes", "Docker", "微服务"],
    "strengths": ["技术基础扎实", "学习能力强"],
    "weaknesses": ["缺乏大型项目经验", "团队协作经验较少"]
}

要求：
1. match_scores中的分数为0-100的浮点数
2. overall_score为所有分项的加权平均，保留1位小数
3. suggestions提供3-5条具体的改进建议
4. skills数组包含具体的技能名称
5. strengths和weaknesses各提供2-4个要点
6. 分析要客观、专业、有建设性"""
    
    def _build_analysis_prompt(self, resume_content: str, job_info: JobInfo) -> str:
        """构建分析提示"""
        return f"""请分析以下简历与职位的匹配度：

【职位信息】
职位名称：{job_info.title}
公司：{job_info.company}
职位描述：{job_info.description}
职位要求：{job_info.requirements}
{f"工作地点：{job_info.location}" if job_info.location else ""}
{f"薪资范围：{job_info.salary}" if job_info.salary else ""}
{f"经验要求：{job_info.experience_level}" if job_info.experience_level else ""}

【简历内容】
{resume_content}

请基于以上信息，从技能匹配度、经验匹配度、教育背景、岗位契合度等维度进行详细分析，并按照指定的JSON格式返回结果。"""
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应
        
        Args:
            response: AI响应文本
            
        Returns:
            Dict[str, Any]: 解析后的分析数据
            
        Raises:
            AIServiceError: 解析失败
        """
        try:
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                # 如果找不到JSON，尝试直接解析整个响应
                data = json.loads(response)
            
            # 验证必需字段
            required_fields = ["match_scores", "overall_score", "suggestions", 
                             "matching_skills", "missing_skills", "strengths", "weaknesses"]
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"AI响应缺少字段: {field}")
                    # 提供默认值
                    if field == "match_scores":
                        data[field] = {"总体匹配": 60.0}
                    elif field == "overall_score":
                        data[field] = 60.0
                    elif field in ["suggestions", "matching_skills", "missing_skills", "strengths", "weaknesses"]:
                        data[field] = []
            
            # 确保分数在合理范围内
            if isinstance(data.get("overall_score"), (int, float)):
                data["overall_score"] = max(0.0, min(100.0, float(data["overall_score"])))
            
            if isinstance(data.get("match_scores"), dict):
                for key, value in data["match_scores"].items():
                    if isinstance(value, (int, float)):
                        data["match_scores"][key] = max(0.0, min(100.0, float(value)))
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"AI响应JSON解析失败: {e}")
            logger.debug(f"原始响应: {response}")
            
            # 返回默认分析结果
            return {
                "match_scores": {"总体评估": 60.0},
                "overall_score": 60.0,
                "suggestions": ["建议重新进行详细分析"],
                "matching_skills": [],
                "missing_skills": [],
                "strengths": ["具备基础条件"],
                "weaknesses": ["需要更多信息进行分析"]
            }
        except Exception as e:
            raise AIServiceError(f"响应解析失败: {e}", service="matching_engine")


class AnalysisStorage:
    """分析结果存储管理"""
    
    def __init__(self, storage_dir: str = "data/analysis"):
        """初始化存储管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        from pathlib import Path
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 分析结果元数据存储文件
        self.metadata_file = self.storage_dir / "analysis_metadata.json"
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """加载分析元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载分析元数据失败: {e}")
        return {}
    
    def _save_metadata(self):
        """保存分析元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存分析元数据失败: {e}")
            raise
    
    def save_analysis(self, result: AnalysisResult) -> bool:
        """保存分析结果
        
        Args:
            result: 分析结果
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 保存分析内容到文件
            content_file = self.storage_dir / f"{result.id}.json"
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2, default=str)
            
            # 更新元数据
            self._metadata[result.id] = {
                'id': result.id,
                'resume_id': result.resume_id,
                'job_id': result.job_id,
                'overall_score': result.overall_score,
                'created_at': result.created_at.isoformat(),
                'analysis_version': result.analysis_version,
                'content_file': str(content_file)
            }
            
            self._save_metadata()
            logger.info(f"分析结果保存成功: {result.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False
    
    def load_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """加载分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            AnalysisResult: 分析结果，不存在返回None
        """
        if analysis_id not in self._metadata:
            return None
        
        try:
            meta = self._metadata[analysis_id]
            content_file = Path(meta['content_file'])
            
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换日期字符串
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                
                return AnalysisResult(**data)
            else:
                logger.warning(f"分析结果文件不存在: {content_file}")
                return None
                
        except Exception as e:
            logger.error(f"加载分析结果失败 {analysis_id}: {e}")
            return None
    
    def list_analysis(self, resume_id: Optional[str] = None, job_id: Optional[str] = None) -> List[AnalysisResult]:
        """获取分析结果列表
        
        Args:
            resume_id: 筛选特定简历的分析
            job_id: 筛选特定职位的分析
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        results = []
        for analysis_id, meta in self._metadata.items():
            # 应用筛选条件
            if resume_id and meta.get('resume_id') != resume_id:
                continue
            if job_id and meta.get('job_id') != job_id:
                continue
            
            analysis = self.load_analysis(analysis_id)
            if analysis:
                results.append(analysis)
        
        # 按创建时间倒序排列
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """删除分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            bool: 删除成功返回True
        """
        if analysis_id not in self._metadata:
            return False
        
        try:
            meta = self._metadata[analysis_id]
            
            # 删除内容文件
            content_file = Path(meta['content_file'])
            if content_file.exists():
                content_file.unlink()
            
            # 删除元数据
            del self._metadata[analysis_id]
            self._save_metadata()
            
            logger.info(f"分析结果删除成功: {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除分析结果失败 {analysis_id}: {e}")
            return False


class AIAnalyzer:
    """AI分析器主类"""
    
    def __init__(self, storage_dir: str = "data/analysis"):
        """初始化AI分析器
        
        Args:
            storage_dir: 存储目录路径
        """
        try:
            self.deepseek_client = DeepSeekClient()
            self.matching_engine = MatchingEngine(self.deepseek_client)
            self.storage = AnalysisStorage(storage_dir)
            self._available = True
            logger.info("AI分析器初始化成功")
        except Exception as e:
            logger.warning(f"AI分析器初始化失败，将使用模拟模式: {e}")
            self._available = False
            self.storage = AnalysisStorage(storage_dir)
    
    def is_available(self) -> bool:
        """检查AI分析功能是否可用
        
        Returns:
            bool: 功能可用返回True
        """
        return self._available
    
    def analyze_resume_job_match(self, resume_content: str, resume_id: str, job_info: JobInfo) -> AnalysisResult:
        """分析简历与职位匹配度
        
        Args:
            resume_content: 简历内容
            resume_id: 简历ID
            job_info: 职位信息
            
        Returns:
            AnalysisResult: 分析结果
            
        Raises:
            ValidationError: 输入验证失败
            AIServiceError: AI分析失败
        """
        if self._available:
            # 使用真实AI分析
            result = self.matching_engine.analyze_match(resume_content, job_info)
            result.resume_id = resume_id
        else:
            # 使用模拟分析结果
            result = self._create_mock_analysis(resume_id, job_info)
        
        # 保存分析结果
        if self.storage.save_analysis(result):
            logger.info(f"分析完成并保存: {result.id}")
        else:
            logger.warning("分析结果保存失败")
        
        return result
    
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """获取分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            AnalysisResult: 分析结果，不存在返回None
        """
        return self.storage.load_analysis(analysis_id)
    
    def list_analysis(self, resume_id: Optional[str] = None, job_id: Optional[str] = None) -> List[AnalysisResult]:
        """获取分析结果列表
        
        Args:
            resume_id: 筛选特定简历的分析
            job_id: 筛选特定职位的分析
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        return self.storage.list_analysis(resume_id, job_id)
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """删除分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            bool: 删除成功返回True
        """
        return self.storage.delete_analysis(analysis_id)
    
    def _create_mock_analysis(self, resume_id: str, job_info: JobInfo) -> AnalysisResult:
        """创建模拟分析结果（当AI不可用时）
        
        Args:
            resume_id: 简历ID
            job_info: 职位信息
            
        Returns:
            AnalysisResult: 模拟分析结果
        """
        return AnalysisResult(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            job_id=job_info.id,
            match_scores={
                "技能匹配度": 75.0,
                "经验匹配度": 68.0,
                "教育背景": 82.0,
                "岗位契合度": 71.0
            },
            overall_score=74.0,
            suggestions=[
                "建议补充与该职位相关的项目经验",
                "可以学习职位要求中提到的新技术",
                "完善简历中的量化成果描述",
                "增加行业相关的认证或培训经历"
            ],
            matching_skills=["Python", "数据分析", "项目管理", "团队协作"],
            missing_skills=["Docker", "Kubernetes", "云计算", "大数据处理"],
            strengths=[
                "技术基础扎实，学习能力强",
                "有相关行业工作经验",
                "具备良好的沟通协调能力"
            ],
            weaknesses=[
                "缺乏大型项目的技术架构经验",
                "对新兴技术的实践应用较少",
                "行业深度理解有待提升"
            ],
            created_at=datetime.now(),
            analysis_version="1.0-mock"
        )