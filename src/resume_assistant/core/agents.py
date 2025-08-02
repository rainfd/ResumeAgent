"""AI Agent 管理模块

本模块提供 AI Agent 的创建、管理和执行功能，包括：
- AgentManager: Agent 生命周期管理
- CustomizableAgent: 支持自定义 Prompt 的 Agent
- AgentFactory: Agent 工厂类
- 内置 Agent 配置和模板
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..data.models import AIAgent, AgentType, AgentUsageHistory, MatchAnalysis
from ..data.database import DatabaseManager
from ..utils.errors import ValidationError, AIAnalysisError
from ..utils import get_logger
from .ai_analyzer import DeepSeekClient

logger = get_logger(__name__)


class AIAnalyzer:
    """AI Agent 兼容的分析器包装类"""
    
    def __init__(self, deepseek_client: DeepSeekClient = None):
        """初始化分析器
        
        Args:
            deepseek_client: DeepSeek API客户端，如果为None则自动创建
        """
        if deepseek_client is None:
            self.client = DeepSeekClient()
        else:
            self.client = deepseek_client
    
    async def analyze_text(self, prompt: str, model: str = "deepseek-chat") -> str:
        """分析文本内容
        
        Args:
            prompt: 分析提示
            model: 使用的模型
            
        Returns:
            AI响应内容
            
        Raises:
            AIAnalysisError: 分析失败
        """
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # 调用DeepSeek API
            response = self.client.chat_completion(messages, model)
            return response
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise AIAnalysisError(f"AI analysis failed: {e}")
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        try:
            # 简单测试调用
            test_messages = [{"role": "user", "content": "Test"}]
            self.client.chat_completion(test_messages)
            return True
        except Exception:
            return False


@dataclass
class AnalysisContext:
    """分析上下文数据"""
    job_id: int
    resume_id: int
    job_description: str
    resume_content: str
    job_skills: List[str] = None
    resume_skills: List[str] = None
    additional_context: Dict[str, Any] = None


class LLMAgent(ABC):
    """AI Agent 抽象基类"""
    
    def __init__(self, agent: AIAgent, analyzer: AIAnalyzer):
        self.agent = agent
        self.analyzer = analyzer
        
    @abstractmethod
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """执行分析"""
        pass


class CustomizableAgent(LLMAgent):
    """支持自定义 Prompt 的 AI Agent"""
    
    def __init__(self, agent: AIAgent, analyzer: AIAnalyzer):
        super().__init__(agent, analyzer)
        self._validate_prompt_template()
    
    def _validate_prompt_template(self):
        """验证 Prompt 模板格式"""
        required_vars = ["job_description", "resume_content"]
        template = self.agent.prompt_template
        
        for var in required_vars:
            if f"{{{var}}}" not in template:
                raise ValidationError(f"Prompt template missing required variable: {var}")
    
    def _format_prompt(self, context: AnalysisContext) -> str:
        """格式化 Prompt"""
        template_vars = {
            "job_description": context.job_description,
            "resume_content": context.resume_content,
            "job_skills": ", ".join(context.job_skills or []),
            "resume_skills": ", ".join(context.resume_skills or [])
        }
        
        # 添加额外的上下文变量
        if context.additional_context:
            template_vars.update(context.additional_context)
        
        return self.agent.prompt_template.format(**template_vars)
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """执行分析"""
        try:
            start_time = time.time()
            
            # 格式化 Prompt
            formatted_prompt = self._format_prompt(context)
            
            # 调用 AI 分析器
            raw_response = await self.analyzer.analyze_text(formatted_prompt)
            
            execution_time = time.time() - start_time
            
            # 解析响应
            analysis_result = self._parse_response(raw_response)
            
            return {
                "analysis": analysis_result,
                "raw_response": raw_response,
                "execution_time": execution_time,
                "agent_id": self.agent.id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Agent {self.agent.name} analysis failed: {e}")
            return {
                "analysis": {},
                "raw_response": "",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent.id,
                "success": False,
                "error": str(e)
            }
    
    def _parse_response(self, raw_response: str) -> Dict[str, Any]:
        """解析 AI 响应为结构化数据"""
        try:
            # 尝试解析 JSON 响应
            if raw_response.strip().startswith("{"):
                return json.loads(raw_response)
            
            # 如果不是 JSON，提取关键信息
            return self._extract_analysis_info(raw_response)
            
        except json.JSONDecodeError:
            return self._extract_analysis_info(raw_response)
    
    def _extract_analysis_info(self, text: str) -> Dict[str, Any]:
        """从文本中提取分析信息"""
        # 基础文本解析逻辑
        analysis = {
            "overall_score": 0.0,
            "skill_match_score": 0.0,
            "experience_score": 0.0,
            "keyword_coverage": 0.0,
            "missing_skills": [],
            "strengths": [],
            "suggestions": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测分数
            if "匹配度" in line or "分数" in line or "评分" in line:
                # 尝试提取数字
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', line)
                if numbers:
                    score = float(numbers[0])
                    if "总体" in line or "整体" in line:
                        analysis["overall_score"] = min(score, 100.0)
                    elif "技能" in line:
                        analysis["skill_match_score"] = min(score, 100.0)
                    elif "经验" in line:
                        analysis["experience_score"] = min(score, 100.0)
                    elif "关键词" in line:
                        analysis["keyword_coverage"] = min(score, 100.0)
            
            # 检测缺失技能
            elif "缺失" in line or "不足" in line:
                current_section = "missing_skills"
            elif "优势" in line or "长处" in line:
                current_section = "strengths"
            elif "建议" in line or "改进" in line:
                current_section = "suggestions"
            elif current_section and (line.startswith(("-", "•", "1.", "2.")) or "经验不足" in line or "缺乏" in line):
                # 提取列表项
                item = line.lstrip("-•0123456789. ")
                if current_section in analysis and item:
                    analysis[current_section].append(item)
        
        return analysis


class AgentManager:
    """AI Agent 管理器"""
    
    def __init__(self, db_manager: DatabaseManager, ai_analyzer: AIAnalyzer):
        self.db_manager = db_manager
        self.ai_analyzer = ai_analyzer
        self._builtin_agents = None
    
    async def initialize(self):
        """初始化管理器，创建内置 Agent"""
        try:
            await self._ensure_builtin_agents()
            logger.info("AgentManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AgentManager: {e}")
            raise
    
    async def _ensure_builtin_agents(self):
        """确保内置 Agent 存在"""
        builtin_configs = self._get_builtin_agent_configs()
        
        for config in builtin_configs:
            # 检查是否已存在
            existing_agents = await self.db_manager.get_all_agents(
                agent_type=config["agent_type"],
                include_builtin=True
            )
            
            # 检查是否已有同名的内置 Agent
            exists = any(
                agent.name == config["name"] and agent.is_builtin 
                for agent in existing_agents
            )
            
            if not exists:
                agent = AIAgent(
                    name=config["name"],
                    description=config["description"],
                    agent_type=config["agent_type"],
                    prompt_template=config["prompt_template"],
                    is_builtin=True
                )
                await self.db_manager.save_agent(agent)
                logger.info(f"Created builtin agent: {agent.name}")
    
    def _get_builtin_agent_configs(self) -> List[Dict[str, Any]]:
        """获取内置 Agent 配置"""
        return [
            {
                "name": "通用分析Agent",
                "description": "适用于所有类型职位的通用分析",
                "agent_type": AgentType.GENERAL,
                "prompt_template": """请分析以下简历与职位的匹配度：

职位描述：{job_description}
简历内容：{resume_content}

请从以下维度进行分析：
1. 技能匹配度 (0-100分)
2. 经验匹配度 (0-100分)  
3. 关键词覆盖率 (0-100分)
4. 总体匹配度 (0-100分)
5. 缺失的关键技能
6. 简历优势
7. 改进建议

请以JSON格式返回结果，或者清晰地列出各项评分和建议。"""
            },
            {
                "name": "技术岗位专用Agent",
                "description": "专门针对技术开发岗位的深度分析",
                "agent_type": AgentType.TECHNICAL,
                "prompt_template": """作为技术招聘专家，请深度分析以下技术岗位简历匹配度：

职位技能要求：{job_skills}
职位描述：{job_description}
简历技能：{resume_skills}
简历内容：{resume_content}

重点分析：
1. 编程语言匹配度
2. 技术栈相关性
3. 项目经验技术含量
4. 技术深度评估
5. 学习能力体现
6. 具体的技术改进建议

请提供详细的技术评估和具体的技能提升建议。"""
            },
            {
                "name": "管理岗位专用Agent",
                "description": "专门针对管理类岗位的领导力分析",
                "agent_type": AgentType.MANAGEMENT,
                "prompt_template": """作为管理岗位招聘专家，请分析以下管理岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 领导力体现
2. 团队管理经验
3. 项目管理能力
4. 战略思维展现
5. 沟通协调能力
6. 业绩管理经验
7. 管理经验的提升建议

请从管理者角度提供专业评估和发展建议。"""
            },
            {
                "name": "创意行业专用Agent",
                "description": "专门针对创意设计类岗位的创新能力分析",
                "agent_type": AgentType.CREATIVE,
                "prompt_template": """作为创意行业招聘专家，请分析以下创意岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 创意思维体现
2. 设计能力展现
3. 作品集质量
4. 创新项目经验
5. 美学素养体现
6. 跨媒体技能
7. 创意能力提升建议

请从创意专业角度提供评估和作品优化建议。"""
            },
            {
                "name": "销售岗位专用Agent",
                "description": "专门针对销售类岗位的业绩和沟通能力分析",
                "agent_type": AgentType.SALES,
                "prompt_template": """作为销售招聘专家，请分析以下销售岗位简历匹配度：

职位描述：{job_description}
简历内容：{resume_content}

重点评估：
1. 销售业绩数据
2. 客户关系管理能力
3. 沟通谈判技巧
4. 市场开拓经验
5. 目标达成能力
6. 抗压能力体现
7. 销售技能提升建议

请从销售专业角度提供评估和业绩优化建议。"""
            }
        ]
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> int:
        """创建新的 Agent"""
        try:
            # 验证输入数据
            self._validate_agent_data(agent_data)
            
            # 创建 Agent 实例
            agent = AIAgent(
                name=agent_data["name"],
                description=agent_data.get("description", ""),
                agent_type=AgentType(agent_data["agent_type"]),
                prompt_template=agent_data["prompt_template"],
                is_builtin=agent_data.get("is_builtin", False)
            )
            
            # 验证 Prompt 模板
            temp_agent = CustomizableAgent(agent, self.ai_analyzer)
            
            # 保存到数据库
            agent_id = await self.db_manager.save_agent(agent)
            logger.info(f"Created agent: {agent.name} (ID: {agent_id})")
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise ValidationError(f"Failed to create agent: {e}")
    
    def _validate_agent_data(self, data: Dict[str, Any]):
        """验证 Agent 数据"""
        required_fields = ["name", "agent_type", "prompt_template"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Missing required field: {field}")
        
        # 验证 agent_type
        try:
            AgentType(data["agent_type"])
        except ValueError:
            valid_types = [t.value for t in AgentType]
            raise ValidationError(f"Invalid agent_type. Must be one of: {valid_types}")
        
        # 验证 prompt_template
        template = data["prompt_template"]
        if "{job_description}" not in template or "{resume_content}" not in template:
            raise ValidationError("Prompt template must contain {job_description} and {resume_content}")
    
    async def get_agent(self, agent_id: int) -> Optional[AIAgent]:
        """获取 Agent"""
        return await self.db_manager.get_agent(agent_id)
    
    async def get_all_agents(
        self, 
        agent_type: Optional[AgentType] = None,
        include_builtin: bool = True,
        include_custom: bool = True
    ) -> List[AIAgent]:
        """获取所有 Agent"""
        all_agents = await self.db_manager.get_all_agents(agent_type=agent_type)
        
        # 根据参数过滤
        filtered_agents = []
        for agent in all_agents:
            if agent.is_builtin and include_builtin:
                filtered_agents.append(agent)
            elif not agent.is_builtin and include_custom:
                filtered_agents.append(agent)
        
        return filtered_agents
    
    async def update_agent(self, agent_id: int, updates: Dict[str, Any]) -> bool:
        """更新 Agent"""
        try:
            # 获取现有 Agent
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValidationError(f"Agent not found: {agent_id}")
            
            if agent.is_builtin:
                raise ValidationError("Cannot update builtin agent")
            
            # 应用更新
            if "name" in updates:
                agent.name = updates["name"]
            if "description" in updates:
                agent.description = updates["description"]
            if "agent_type" in updates:
                agent.agent_type = AgentType(updates["agent_type"])
            if "prompt_template" in updates:
                agent.prompt_template = updates["prompt_template"]
                # 验证新的 Prompt 模板
                temp_agent = CustomizableAgent(agent, self.ai_analyzer)
            
            agent.updated_at = datetime.now()
            
            success = await self.db_manager.update_agent(agent)
            if success:
                logger.info(f"Updated agent: {agent.name} (ID: {agent_id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise ValidationError(f"Failed to update agent: {e}")
    
    async def delete_agent(self, agent_id: int) -> bool:
        """删除 Agent"""
        try:
            agent = await self.get_agent(agent_id)
            if not agent:
                return False
            
            if agent.is_builtin:
                raise ValidationError("Cannot delete builtin agent")
            
            success = await self.db_manager.delete_agent(agent_id)
            if success:
                logger.info(f"Deleted agent: {agent.name} (ID: {agent_id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise ValidationError(f"Failed to delete agent: {e}")
    
    async def analyze_with_agent(
        self, 
        agent_id: int, 
        context: AnalysisContext
    ) -> Dict[str, Any]:
        """使用指定 Agent 进行分析"""
        try:
            # 获取 Agent
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValidationError(f"Agent not found: {agent_id}")
            
            # 创建 Agent 实例
            agent_instance = CustomizableAgent(agent, self.ai_analyzer)
            
            # 执行分析
            result = await agent_instance.analyze(context)
            
            # 记录使用历史（如果分析成功）
            if result["success"]:
                usage_history = AgentUsageHistory(
                    agent_id=agent_id,
                    analysis_id=0,  # 分析ID将在保存后设置
                    execution_time=result["execution_time"],
                    success=True
                )
                await self.db_manager.save_agent_usage_history(usage_history)
                
                # 更新使用统计
                await self.db_manager.update_agent_usage(agent_id)
            else:
                # 记录失败的使用历史
                usage_history = AgentUsageHistory(
                    agent_id=agent_id,
                    analysis_id=0,
                    execution_time=result["execution_time"],
                    success=False,
                    error_message=result.get("error", "")
                )
                await self.db_manager.save_agent_usage_history(usage_history)
            
            return result
            
        except Exception as e:
            logger.error(f"Agent analysis failed: {e}")
            raise AIAnalysisError(f"Agent analysis failed: {e}")
    
    async def get_agent_statistics(self, agent_id: int) -> Dict[str, Any]:
        """获取 Agent 统计信息"""
        return await self.db_manager.get_agent_statistics(agent_id)
    
    async def rate_agent_usage(
        self, 
        usage_history_id: int, 
        rating: float, 
        feedback: str = ""
    ) -> bool:
        """为 Agent 使用记录评分"""
        try:
            if not (1.0 <= rating <= 5.0):
                raise ValidationError("Rating must be between 1.0 and 5.0")
            
            # 获取使用历史记录
            history = await self.db_manager.get_agent_usage_history_by_id(usage_history_id)
            if not history:
                return False
            
            # 更新评分和反馈
            history.rating = rating
            history.feedback = feedback
            
            # 保存更新
            success = await self.db_manager.update_agent_usage_history(history)
            
            if success:
                # 更新 Agent 的平均评分
                await self.db_manager.update_agent_usage(history.agent_id, rating)
                logger.info(f"Rated agent usage {usage_history_id}: {rating}/5.0")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rate agent usage: {e}")
            return False


class AgentFactory:
    """Agent 工厂类"""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
    async def create_agent_instance(self, agent_id: int) -> Optional[CustomizableAgent]:
        """创建 Agent 实例"""
        agent = await self.agent_manager.get_agent(agent_id)
        if not agent:
            return None
        
        return CustomizableAgent(agent, self.agent_manager.ai_analyzer)
    
    async def get_recommended_agent(
        self, 
        job_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AIAgent]:
        """根据职位描述推荐最合适的 Agent"""
        try:
            # 获取所有可用的内置 Agent
            agents = await self.agent_manager.get_all_agents(include_custom=False)
            
            # 简单的关键词匹配推荐逻辑
            job_desc_lower = job_description.lower()
            
            # 技术岗位关键词
            tech_keywords = ["开发", "程序员", "工程师", "技术", "编程", "代码", "软件", "算法"]
            if any(keyword in job_desc_lower for keyword in tech_keywords):
                tech_agent = next((a for a in agents if a.agent_type == AgentType.TECHNICAL), None)
                if tech_agent:
                    return tech_agent
            
            # 管理岗位关键词
            mgmt_keywords = ["经理", "主管", "总监", "管理", "领导", "团队"]
            if any(keyword in job_desc_lower for keyword in mgmt_keywords):
                mgmt_agent = next((a for a in agents if a.agent_type == AgentType.MANAGEMENT), None)
                if mgmt_agent:
                    return mgmt_agent
            
            # 创意岗位关键词
            creative_keywords = ["设计", "创意", "美术", "UI", "UX", "视觉"]
            if any(keyword in job_desc_lower for keyword in creative_keywords):
                creative_agent = next((a for a in agents if a.agent_type == AgentType.CREATIVE), None)
                if creative_agent:
                    return creative_agent
            
            # 销售岗位关键词
            sales_keywords = ["销售", "客户", "业务", "市场", "BD"]
            if any(keyword in job_desc_lower for keyword in sales_keywords):
                sales_agent = next((a for a in agents if a.agent_type == AgentType.SALES), None)
                if sales_agent:
                    return sales_agent
            
            # 默认返回通用 Agent
            general_agent = next((a for a in agents if a.agent_type == AgentType.GENERAL), None)
            return general_agent
            
        except Exception as e:
            logger.error(f"Failed to get recommended agent: {e}")
            return None


class AgentAnalysisIntegrator:
    """Agent分析集成器 - 将Agent系统与现有分析流程集成"""
    
    def __init__(self, agent_manager: AgentManager, db_manager: DatabaseManager):
        self.agent_manager = agent_manager
        self.db_manager = db_manager
    
    async def analyze_with_recommended_agent(
        self,
        job_description: str,
        resume_content: str,
        job_id: int,
        resume_id: int,
        job_skills: List[str] = None,
        resume_skills: List[str] = None,
        force_agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """使用推荐的或指定的Agent进行分析
        
        Args:
            job_description: 职位描述
            resume_content: 简历内容
            job_id: 职位ID
            resume_id: 简历ID
            job_skills: 职位技能要求
            resume_skills: 简历技能
            force_agent_id: 强制使用的AgentID，如果为None则自动推荐
            
        Returns:
            包含分析结果的字典
        """
        try:
            # 选择Agent
            if force_agent_id:
                agent = await self.agent_manager.get_agent(force_agent_id)
                if not agent:
                    raise ValidationError(f"Agent not found: {force_agent_id}")
            else:
                # 使用AgentFactory获取推荐Agent
                factory = AgentFactory(self.agent_manager)
                agent = await factory.get_recommended_agent(job_description)
                if not agent:
                    raise AIAnalysisError("No suitable agent found")
            
            # 构建分析上下文
            context = AnalysisContext(
                job_id=job_id,
                resume_id=resume_id,
                job_description=job_description,
                resume_content=resume_content,
                job_skills=job_skills or [],
                resume_skills=resume_skills or []
            )
            
            # 执行分析
            result = await self.agent_manager.analyze_with_agent(agent.id, context)
            
            if result["success"]:
                # 将结果保存到数据库
                match_analysis = MatchAnalysis(
                    job_id=job_id,
                    resume_id=resume_id,
                    agent_id=agent.id,
                    overall_score=result["analysis"].get("overall_score", 0.0),
                    skill_match_score=result["analysis"].get("skill_match_score", 0.0),
                    experience_score=result["analysis"].get("experience_score", 0.0),
                    keyword_coverage=result["analysis"].get("keyword_coverage", 0.0),
                    missing_skills=result["analysis"].get("missing_skills", []),
                    strengths=result["analysis"].get("strengths", []),
                    raw_response=result["raw_response"],
                    execution_time=result["execution_time"]
                )
                
                analysis_id = await self.db_manager.save_analysis(match_analysis)
                
                # 返回完整结果
                return {
                    "success": True,
                    "analysis_id": analysis_id,
                    "agent_name": agent.name,
                    "agent_type": agent.agent_type.value,
                    "analysis": result["analysis"],
                    "raw_response": result["raw_response"],
                    "execution_time": result["execution_time"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Analysis failed"),
                    "agent_name": agent.name,
                    "agent_type": agent.agent_type.value
                }
                
        except Exception as e:
            logger.error(f"Agent analysis integration failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_agents(
        self,
        job_description: str,
        resume_content: str,
        job_id: int,
        resume_id: int,
        agent_ids: List[int],
        job_skills: List[str] = None,
        resume_skills: List[str] = None
    ) -> Dict[str, Any]:
        """使用多个Agent对比分析
        
        Args:
            job_description: 职位描述
            resume_content: 简历内容
            job_id: 职位ID
            resume_id: 简历ID
            agent_ids: 要对比的Agent ID列表
            job_skills: 职位技能要求
            resume_skills: 简历技能
            
        Returns:
            包含对比结果的字典
        """
        try:
            context = AnalysisContext(
                job_id=job_id,
                resume_id=resume_id,
                job_description=job_description,
                resume_content=resume_content,
                job_skills=job_skills or [],
                resume_skills=resume_skills or []
            )
            
            results = []
            
            # 并行分析（简化版，实际可以使用asyncio.gather）
            for agent_id in agent_ids:
                agent = await self.agent_manager.get_agent(agent_id)
                if not agent:
                    continue
                
                result = await self.agent_manager.analyze_with_agent(agent_id, context)
                
                if result["success"]:
                    results.append({
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "agent_type": agent.agent_type.value,
                        "analysis": result["analysis"],
                        "execution_time": result["execution_time"]
                    })
            
            # 分析结果对比
            comparison = self._compare_analysis_results(results)
            
            return {
                "success": True,
                "results": results,
                "comparison": comparison
            }
            
        except Exception as e:
            logger.error(f"Agent comparison failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _compare_analysis_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对比分析结果"""
        if not results:
            return {}
        
        # 计算平均分数
        scores = {
            "overall_score": [],
            "skill_match_score": [],
            "experience_score": [],
            "keyword_coverage": []
        }
        
        for result in results:
            analysis = result["analysis"]
            for score_type in scores:
                if score_type in analysis:
                    scores[score_type].append(analysis[score_type])
        
        # 计算统计信息
        comparison = {}
        for score_type, values in scores.items():
            if values:
                comparison[score_type] = {
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "variance": sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)
                }
        
        # 找出最佳Agent
        if results:
            best_agent = max(results, key=lambda x: x["analysis"].get("overall_score", 0))
            comparison["best_agent"] = {
                "agent_name": best_agent["agent_name"],
                "agent_type": best_agent["agent_type"],
                "overall_score": best_agent["analysis"].get("overall_score", 0)
            }
        
        return comparison