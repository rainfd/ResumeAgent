"""示例数据模块"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import random


class SampleDataGenerator:
    """示例数据生成器"""
    
    def __init__(self):
        self.job_titles = [
            "Python开发工程师", "后端开发工程师", "全栈工程师", 
            "数据分析师", "机器学习工程师", "DevOps工程师",
            "前端开发工程师", "算法工程师", "大数据工程师"
        ]
        
        self.companies = [
            "科技公司A", "互联网公司B", "创业公司C", "大厂D",
            "金融科技E", "AI公司F", "游戏公司G", "电商平台H"
        ]
        
        self.job_statuses = ["已申请", "待申请", "已投递", "面试中", "已通过", "已拒绝"]
        
        self.resume_files = [
            "我的简历_v1.pdf", "技术简历.md", "英文简历.pdf",
            "项目简历_final.docx", "简历_2024.pdf", "个人简历.md"
        ]
        
        self.resume_statuses = ["已解析", "待解析", "解析中", "解析失败"]
        
        self.skills = [
            "Python", "Django", "Flask", "FastAPI", "Docker", "Kubernetes",
            "MySQL", "PostgreSQL", "Redis", "MongoDB", "AWS", "Git",
            "Linux", "JavaScript", "React", "Vue.js", "Node.js", "Machine Learning"
        ]
        
    def generate_jobs(self, count: int = 10) -> List[List[str]]:
        """生成职位示例数据"""
        jobs = []
        for i in range(1, count + 1):
            job = [
                str(i),
                random.choice(self.job_titles),
                random.choice(self.companies),
                random.choice(self.job_statuses)
            ]
            jobs.append(job)
        return jobs
    
    def generate_resumes(self, count: int = 6) -> List[List[str]]:
        """生成简历示例数据"""
        resumes = []
        for i in range(1, count + 1):
            # 生成随机日期（最近30天）
            date = datetime.now() - timedelta(days=random.randint(1, 30))
            resume = [
                str(i),
                random.choice(self.resume_files),
                date.strftime("%Y-%m-%d"),
                random.choice(self.resume_statuses)
            ]
            resumes.append(resume)
        return resumes
    
    def generate_analysis_data(self) -> Dict[str, Any]:
        """生成分析结果示例数据"""
        return {
            "match_scores": {
                "总体匹配度": f"{random.randint(70, 95)}%",
                "技能匹配": f"{random.randint(80, 95)}%",
                "经验匹配": f"{random.randint(70, 90)}%",
                "关键词覆盖": f"{random.randint(60, 85)}%"
            },
            "suggestions": [
                "增加Python web开发经验描述",
                "补充Docker容器化技能",
                "强化数据库设计经验",
                "添加云服务使用经历",
                "完善项目管理经验"
            ],
            "missing_skills": random.sample(self.skills, 3),
            "matching_skills": random.sample(self.skills, 5)
        }
    
    def generate_greetings(self) -> Dict[str, str]:
        """生成打招呼语示例数据"""
        greetings = {
            "技术导向型": (
                "您好！我是一名具有5年Python开发经验的工程师，"
                "看到贵公司的后端开发岗位非常符合我的背景。"
                "我在微服务架构和数据库优化方面有丰富经验，"
                "期待能为贵司贡献自己的技术能力。"
            ),
            "经验导向型": (
                "您好！我在软件开发领域有着丰富的项目经验，"
                "曾主导过多个大型项目的架构设计和开发工作。"
                "贵公司的技术栈与我的技能非常匹配，"
                "相信能够快速融入团队并创造价值。"
            ),
            "简洁型": (
                "您好！我对贵公司的职位很感兴趣，"
                "我的技术背景和项目经验与岗位要求高度匹配，"
                "期待有机会详细交流。"
            )
        }
        return greetings
    
    def generate_history_data(self) -> List[Dict[str, Any]]:
        """生成历史记录示例数据"""
        history = []
        for i in range(10):
            record = {
                "id": i + 1,
                "type": random.choice(["分析", "打招呼语"]),
                "job_title": random.choice(self.job_titles),
                "company": random.choice(self.companies),
                "date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M"),
                "score": f"{random.randint(70, 95)}%" if random.choice([True, False]) else "N/A"
            }
            history.append(record)
        return history
    
    def generate_settings_data(self) -> Dict[str, str]:
        """生成设置数据"""
        return {
            "主题": "dark",
            "日志级别": "INFO",
            "Agent类型": "deepseek",
            "自动保存": "启用",
            "缓存TTL": "3600秒",
            "请求超时": "30秒",
            "最大重试": "3次"
        }


# 全局示例数据生成器实例
sample_data = SampleDataGenerator()


def get_sample_jobs(count: int = 8) -> List[List[str]]:
    """获取职位示例数据"""
    return sample_data.generate_jobs(count)


def get_sample_resumes(count: int = 5) -> List[List[str]]:
    """获取简历示例数据"""
    return sample_data.generate_resumes(count)


def get_sample_analysis() -> Dict[str, Any]:
    """获取分析结果示例数据"""
    return sample_data.generate_analysis_data()


def get_sample_greetings() -> Dict[str, str]:
    """获取打招呼语示例数据"""
    return sample_data.generate_greetings()


def get_sample_history() -> List[Dict[str, Any]]:
    """获取历史记录示例数据"""
    return sample_data.generate_history_data()


def get_sample_settings() -> Dict[str, str]:
    """获取设置示例数据"""
    return sample_data.generate_settings_data()


# 为了增加数据的真实性，创建一些具体的示例
DEMO_JOBS = [
    ["1", "Python后端开发工程师", "字节跳动", "已申请"],
    ["2", "全栈工程师", "腾讯", "面试中"],
    ["3", "机器学习工程师", "百度", "待申请"],
    ["4", "DevOps工程师", "阿里巴巴", "已投递"],
    ["5", "数据分析师", "美团", "已通过"],
    ["6", "算法工程师", "滴滴", "已拒绝"],
    ["7", "前端开发工程师", "小红书", "待申请"],
    ["8", "大数据工程师", "京东", "已申请"]
]

DEMO_RESUMES = [
    ["1", "张三_Python工程师_2024.pdf", "2024-01-15 09:30", "已解析"],
    ["2", "个人简历_技术栈详细版.md", "2024-01-18 14:20", "已解析"],
    ["3", "Resume_English_v2.pdf", "2024-01-20 16:45", "待解析"],
    ["4", "项目经历_完整版.docx", "2024-01-22 11:10", "解析中"],
    ["5", "简历_校招版本.pdf", "2024-01-25 08:55", "已解析"]
]

DEMO_ANALYSIS = {
    "match_scores": {
        "总体匹配度": "87%",
        "技能匹配": "92%",
        "经验匹配": "83%",
        "关键词覆盖": "79%"
    },
    "suggestions": [
        "增加微服务架构项目经验描述",
        "补充Kubernetes容器编排技能",
        "强化高并发系统设计经验",
        "添加分布式系统开发经历",
        "完善团队协作和项目管理经验"
    ],
    "missing_skills": ["Kubernetes", "Redis集群", "消息队列"],
    "matching_skills": ["Python", "Django", "MySQL", "Docker", "AWS"]
}

DEMO_GREETINGS = {
    "专业型": (
        "您好！我是一名有着6年Python开发经验的后端工程师，"
        "专注于高并发系统架构设计和性能优化。看到贵公司的"
        "技术栈与我的专业背景高度匹配，特别是在微服务架构"
        "和云原生技术方面，我有丰富的实战经验。期待能够"
        "加入贵团队，共同打造优秀的技术产品。"
    ),
    "项目导向": (
        "您好！我曾主导开发过日活千万级的互联网产品后端系统，"
        "在系统架构、数据库优化、缓存设计等方面积累了宝贵经验。"
        "看到贵公司正在寻找有实战经验的开发工程师，我相信我的"
        "项目经历能够为团队带来价值。"
    ),
    "简洁直接": (
        "您好！我对贵公司的Python开发职位很感兴趣。"
        "我有6年相关开发经验，技术栈与岗位要求完全匹配，"
        "希望有机会进一步沟通交流。"
    )
}