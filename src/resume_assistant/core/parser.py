#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简历解析模块
支持PDF和Markdown格式的简历解析和结构化提取
"""

import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from ..utils.logging import logger
from ..utils.errors import ResumeParsingError


@dataclass
class ResumeSection:
    """简历章节数据结构"""
    title: str
    content: str
    start_pos: int
    end_pos: int


@dataclass
class ParsedResume:
    """解析后的简历数据结构"""
    file_path: str
    file_type: str
    raw_text: str
    sections: List[ResumeSection]
    metadata: Dict[str, Any]
    parsed_at: datetime
    
    # 结构化字段
    personal_info: Dict[str, str]
    skills: List[str]
    work_experience: List[Dict[str, str]]
    education: List[Dict[str, str]]
    projects: List[Dict[str, str]]


class ResumeParser:
    """简历解析器主类"""
    
    # 常见简历章节标题模式
    SECTION_PATTERNS = {
        'personal_info': [
            r'基本信息', r'个人信息', r'联系方式', r'Personal Information', 
            r'Contact', r'基础信息'
        ],
        'skills': [
            r'专业技能', r'技能清单', r'技术技能', r'Skills', r'Technical Skills',
            r'核心技能', r'技能特长'
        ],
        'work_experience': [
            r'工作经历', r'工作经验', r'职业经历', r'Work Experience', 
            r'Professional Experience', r'Employment History'
        ],
        'education': [
            r'教育经历', r'教育背景', r'学历信息', r'Education', 
            r'Educational Background', r'Academic Background'
        ],
        'projects': [
            r'项目经历', r'项目经验', r'主要项目', r'Projects', 
            r'Project Experience', r'Key Projects'
        ]
    }
    
    def __init__(self):
        self.logger = logger
        
    def parse_file(self, file_path: str) -> ParsedResume:
        """解析简历文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ResumeParsingError(f"文件不存在: {file_path}")
            
        file_type = file_path.suffix.lower()
        
        try:
            if file_type == '.pdf':
                return self._parse_pdf(file_path)
            elif file_type in ['.md', '.markdown']:
                return self._parse_markdown(file_path)
            elif file_type == '.txt':
                return self._parse_text(file_path)
            else:
                raise ResumeParsingError(f"不支持的文件格式: {file_type}")
                
        except Exception as e:
            self.logger.error(f"解析简历文件失败: {file_path}, 错误: {str(e)}")
            raise ResumeParsingError(f"解析失败: {str(e)}")
    
    def _parse_pdf(self, file_path: Path) -> ParsedResume:
        """解析PDF简历"""
        if not PYMUPDF_AVAILABLE:
            raise ResumeParsingError("PyMuPDF未安装，无法解析PDF文件")
            
        try:
            doc = fitz.open(str(file_path))
            raw_text = ""
            
            # 提取所有页面的文本
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                raw_text += page.get_text()
                
            doc.close()
            
            # 清理文本
            raw_text = self._clean_text(raw_text)
            
            if not raw_text.strip():
                raise ResumeParsingError("PDF文件中未提取到有效文本")
            
            return self._create_parsed_resume(
                file_path=str(file_path),
                file_type='pdf',
                raw_text=raw_text
            )
            
        except Exception as e:
            raise ResumeParsingError(f"PDF解析失败: {str(e)}")
    
    def _parse_markdown(self, file_path: Path) -> ParsedResume:
        """解析Markdown简历"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
                
            if not raw_text.strip():
                raise ResumeParsingError("Markdown文件为空")
            
            return self._create_parsed_resume(
                file_path=str(file_path),
                file_type='markdown',
                raw_text=raw_text
            )
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    raw_text = f.read()
                return self._create_parsed_resume(
                    file_path=str(file_path),
                    file_type='markdown',
                    raw_text=raw_text
                )
            except Exception as e:
                raise ResumeParsingError(f"无法读取Markdown文件: {str(e)}")
        except Exception as e:
            raise ResumeParsingError(f"Markdown解析失败: {str(e)}")
    
    def _parse_text(self, file_path: Path) -> ParsedResume:
        """解析纯文本简历"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
                
            if not raw_text.strip():
                raise ResumeParsingError("文本文件为空")
            
            return self._create_parsed_resume(
                file_path=str(file_path),
                file_type='text',
                raw_text=raw_text
            )
            
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    raw_text = f.read()
                return self._create_parsed_resume(
                    file_path=str(file_path),
                    file_type='text',
                    raw_text=raw_text
                )
            except Exception as e:
                raise ResumeParsingError(f"无法读取文本文件: {str(e)}")
        except Exception as e:
            raise ResumeParsingError(f"文本解析失败: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """清理和标准化文本"""
        if not text:
            return ""
            
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        text = text.strip()
        # 标准化换行符
        text = re.sub(r'\r\n|\r', '\n', text)
        
        return text
    
    def _create_parsed_resume(self, file_path: str, file_type: str, raw_text: str) -> ParsedResume:
        """创建解析后的简历对象"""
        
        # 提取章节
        sections = self._extract_sections(raw_text)
        
        # 提取结构化信息
        personal_info = self._extract_personal_info(raw_text, sections)
        skills = self._extract_skills(raw_text, sections)
        work_experience = self._extract_work_experience(raw_text, sections)
        education = self._extract_education(raw_text, sections)
        projects = self._extract_projects(raw_text, sections)
        
        # 创建元数据
        metadata = {
            'file_size': os.path.getsize(file_path),
            'text_length': len(raw_text),
            'sections_count': len(sections),
            'extraction_method': 'automatic'
        }
        
        return ParsedResume(
            file_path=file_path,
            file_type=file_type,
            raw_text=raw_text,
            sections=sections,
            metadata=metadata,
            parsed_at=datetime.now(),
            personal_info=personal_info,
            skills=skills,
            work_experience=work_experience,
            education=education,
            projects=projects
        )
    
    def _extract_sections(self, text: str) -> List[ResumeSection]:
        """提取简历章节"""
        sections = []
        
        # 查找所有可能的章节标题
        all_patterns = []
        for category, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                all_patterns.append((pattern, category))
        
        # 使用正则表达式查找章节标题
        section_matches = []
        for pattern, category in all_patterns:
            # 匹配章节标题（通常在行首或有特殊格式）
            regex = rf'(?:^|\n)\s*(?:#{{1,6}}\s*)?({pattern})\s*(?:\n|$|:)'
            matches = re.finditer(regex, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                section_matches.append({
                    'title': match.group(1),
                    'category': category,
                    'start': match.start(),
                    'end': match.end()
                })
        
        # 按位置排序
        section_matches.sort(key=lambda x: x['start'])
        
        # 创建章节对象
        for i, match in enumerate(section_matches):
            start_pos = match['end']
            end_pos = section_matches[i + 1]['start'] if i + 1 < len(section_matches) else len(text)
            
            content = text[start_pos:end_pos].strip()
            if content:
                sections.append(ResumeSection(
                    title=match['title'],
                    content=content,
                    start_pos=start_pos,
                    end_pos=end_pos
                ))
        
        return sections
    
    def _extract_personal_info(self, text: str, sections: List[ResumeSection]) -> Dict[str, str]:
        """提取个人信息"""
        personal_info = {}
        
        # 查找姓名（通常在简历开头）
        name_patterns = [
            r'(?:姓名[:：]?\s*)?([^\n\s]+(?:\s+[^\n\s]+)?)\s*(?:\n|$)',
            r'^([^\n]+)(?:\n|$)',  # 第一行通常是姓名
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text[:200], re.MULTILINE)
            if match:
                potential_name = match.group(1).strip()
                # 简单验证是否为姓名（排除明显不是姓名的内容）
                if len(potential_name) < 20 and not re.search(r'[0-9@]', potential_name):
                    personal_info['name'] = potential_name
                    break
        
        # 查找电话
        phone_pattern = r'(?:电话|手机|Tel|Phone)[:：]?\s*([1-9]\d{2}[*\-\s]*\d{4}[*\-\s]*\d{4})'
        match = re.search(phone_pattern, text, re.IGNORECASE)
        if match:
            personal_info['phone'] = match.group(1)
        
        # 查找邮箱
        email_pattern = r'(?:邮箱|Email|E-mail)[:：]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(email_pattern, text, re.IGNORECASE)
        if match:
            personal_info['email'] = match.group(1)
        
        # 查找年龄
        age_pattern = r'(?:年龄|Age)[:：]?\s*(\d{1,2})\s*岁?'
        match = re.search(age_pattern, text, re.IGNORECASE)
        if match:
            personal_info['age'] = match.group(1)
        
        return personal_info
    
    def _extract_skills(self, text: str, sections: List[ResumeSection]) -> List[str]:
        """提取技能列表"""
        skills = []
        
        # 查找技能相关章节
        skill_sections = [s for s in sections if any(
            re.search(pattern, s.title, re.IGNORECASE) 
            for pattern in self.SECTION_PATTERNS['skills']
        )]
        
        for section in skill_sections:
            # 提取技能项
            # 匹配列表项
            list_items = re.findall(r'[-*•]\s*([^\n]+)', section.content)
            skills.extend([item.strip() for item in list_items])
            
            # 匹配冒号分隔的技能
            colon_items = re.findall(r'([^:\n]+)[:：][^\n]+', section.content)
            skills.extend([item.strip() for item in colon_items])
        
        # 去重并过滤
        skills = list(set([skill for skill in skills if len(skill) > 1 and len(skill) < 50]))
        
        return skills
    
    def _extract_work_experience(self, text: str, sections: List[ResumeSection]) -> List[Dict[str, str]]:
        """提取工作经历"""
        work_exp = []
        
        # 查找工作经历章节
        work_sections = [s for s in sections if any(
            re.search(pattern, s.title, re.IGNORECASE) 
            for pattern in self.SECTION_PATTERNS['work_experience']
        )]
        
        for section in work_sections:
            # 简单的工作经历提取
            # 查找包含公司名称和职位的行
            exp_pattern = r'([^\n|]+)\s*[|]\s*([^\n|]+)\s*[|]\s*([^\n]+)'
            matches = re.findall(exp_pattern, section.content)
            
            for match in matches:
                work_exp.append({
                    'company': match[0].strip(),
                    'position': match[1].strip(),
                    'duration': match[2].strip()
                })
        
        return work_exp
    
    def _extract_education(self, text: str, sections: List[ResumeSection]) -> List[Dict[str, str]]:
        """提取教育经历"""
        education = []
        
        # 查找教育经历章节
        edu_sections = [s for s in sections if any(
            re.search(pattern, s.title, re.IGNORECASE) 
            for pattern in self.SECTION_PATTERNS['education']
        )]
        
        for section in edu_sections:
            # 查找教育信息
            # 匹配大学和专业信息
            edu_pattern = r'(\d{4}[.\-/]\d{1,2}[.\-/~]\d{4}[.\-/]\d{1,2})\s*([^\n]+?)\s*([^\n]+?)\s*([^\n]+)'
            matches = re.findall(edu_pattern, section.content)
            
            for match in matches:
                education.append({
                    'duration': match[0].strip(),
                    'school': match[1].strip(),
                    'major': match[2].strip(),
                    'degree': match[3].strip() if len(match) > 3 else ''
                })
        
        return education
    
    def _extract_projects(self, text: str, sections: List[ResumeSection]) -> List[Dict[str, str]]:
        """提取项目经历"""
        projects = []
        
        # 查找项目经历章节
        project_sections = [s for s in sections if any(
            re.search(pattern, s.title, re.IGNORECASE) 
            for pattern in self.SECTION_PATTERNS['projects']
        )]
        
        for section in project_sections:
            # 简单的项目提取
            # 查找项目标题
            project_titles = re.findall(r'(?:^|\n)([^:\n]+?)(?:[:：]|\|)', section.content, re.MULTILINE)
            
            for title in project_titles:
                if len(title.strip()) > 5:  # 过滤太短的标题
                    projects.append({
                        'name': title.strip(),
                        'description': ''  # 可以进一步提取描述
                    })
        
        return projects


def create_parser() -> ResumeParser:
    """创建简历解析器实例"""
    return ResumeParser()