"""TUI基础组件库"""

from typing import List, Dict, Any, Optional, Callable
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, TaskID
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.box import ROUNDED


class DataTable:
    """数据表格组件"""
    
    def __init__(self, title: str = "", style: str = "cyan"):
        self.title = title
        self.style = style
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.column_styles: Dict[int, str] = {}
    
    def add_column(self, header: str, style: str = "white", no_wrap: bool = False) -> 'DataTable':
        """添加列"""
        self.headers.append(header)
        self.column_styles[len(self.headers) - 1] = style
        return self
    
    def add_row(self, *values: str) -> 'DataTable':
        """添加行"""
        self.rows.append(list(values))
        return self
    
    def add_rows(self, rows: List[List[str]]) -> 'DataTable':
        """批量添加行"""
        self.rows.extend(rows)
        return self
    
    def clear(self) -> 'DataTable':
        """清空数据"""
        self.rows.clear()
        return self
    
    def render(self) -> Table:
        """渲染表格"""
        table = Table(title=self.title, box=ROUNDED, show_header=True, header_style=f"bold {self.style}")
        
        # 添加列
        for i, header in enumerate(self.headers):
            style = self.column_styles.get(i, "white")
            table.add_column(header, style=style)
        
        # 添加行
        for row in self.rows:
            table.add_row(*row)
        
        return table


class InfoPanel:
    """信息面板组件"""
    
    def __init__(self, title: str = "", border_style: str = "blue"):
        self.title = title
        self.border_style = border_style
        self.content_lines: List[tuple] = []  # (text, style)
        self.scroll_offset = 0
    
    def add_line(self, text: str, style: str = "white") -> 'InfoPanel':
        """添加一行内容"""
        self.content_lines.append((text, style))
        return self
    
    def add_header(self, text: str, style: str = "bold cyan") -> 'InfoPanel':
        """添加标题行"""
        self.content_lines.append((f"\n{text}", style))
        return self
    
    def add_separator(self) -> 'InfoPanel':
        """添加分隔线"""
        self.content_lines.append(("─" * 50, "dim"))
        return self
    
    def add_key_value(self, key: str, value: str, key_style: str = "bold", value_style: str = "white") -> 'InfoPanel':
        """添加键值对"""
        self.content_lines.append((f"{key}: {value}", f"{key_style} {value_style}"))
        return self
    
    def clear(self) -> 'InfoPanel':
        """清空内容"""
        self.content_lines.clear()
        return self
    
    def set_scroll_offset(self, offset: int) -> 'InfoPanel':
        """设置滚动偏移"""
        self.scroll_offset = max(0, offset)
        return self
    
    def render(self, max_lines: int = 20) -> Panel:
        """渲染面板"""
        if not self.content_lines:
            content = Text("暂无数据", style="dim")
        else:
            content = Text()
            # 应用滚动偏移
            start_index = self.scroll_offset
            end_index = start_index + max_lines
            visible_lines = self.content_lines[start_index:end_index]
            
            for text, style in visible_lines:
                content.append(f"{text}\n", style=style)
            
            # 添加滚动指示器
            if self.scroll_offset > 0:
                content = Text(f"↑ ...更多内容...\n", style="dim") + content
            if end_index < len(self.content_lines):
                content.append(f"↓ ...更多内容...", style="dim")
        
        title = self.title
        if self.scroll_offset > 0:
            title += f" (滚动: {self.scroll_offset})"
        
        return Panel(content, title=title, border_style=self.border_style)


class StatusBar:
    """状态栏组件"""
    
    def __init__(self):
        self.items: List[tuple] = []  # (text, style)
    
    def add_item(self, text: str, style: str = "white") -> 'StatusBar':
        """添加状态项"""
        self.items.append((text, style))
        return self
    
    def add_separator(self) -> 'StatusBar':
        """添加分隔符"""
        self.items.append((" | ", "dim"))
        return self
    
    def clear(self) -> 'StatusBar':
        """清空状态"""
        self.items.clear()
        return self
    
    def render(self) -> Panel:
        """渲染状态栏"""
        if not self.items:
            content = Text("就绪", style="green")
        else:
            content = Text()
            for text, style in self.items:
                content.append(text, style=style)
        
        return Panel(Align.center(content), style="bright_black")


class MenuList:
    """菜单列表组件"""
    
    def __init__(self, title: str = "", border_style: str = "cyan"):
        self.title = title
        self.border_style = border_style
        self.items: List[tuple] = []  # (text, key, style, selected)
        self.selected_index = 0
    
    def add_item(self, text: str, key: str = "", style: str = "white") -> 'MenuList':
        """添加菜单项"""
        self.items.append((text, key, style, False))
        return self
    
    def select_item(self, index: int) -> 'MenuList':
        """选择菜单项"""
        if 0 <= index < len(self.items):
            self.selected_index = index
        return self
    
    def get_selected_key(self) -> str:
        """获取选中项的键"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index][1]
        return ""
    
    def render(self) -> Panel:
        """渲染菜单"""
        if not self.items:
            content = Text("无菜单项", style="dim")
        else:
            content = Text()
            for i, (text, key, style, _) in enumerate(self.items):
                if i == self.selected_index:
                    prefix = "▶ "
                    line_style = "bold white on blue"
                else:
                    prefix = "  "
                    line_style = style
                
                display_text = f"{prefix}{text}"
                if key:
                    display_text += f" ({key})"
                
                content.append(f"{display_text}\n", style=line_style)
        
        return Panel(content, title=self.title, border_style=self.border_style)


class ProgressDisplay:
    """进度显示组件"""
    
    def __init__(self, title: str = "进度"):
        self.title = title
        self.progress = Progress()
        self.tasks: Dict[str, TaskID] = {}
    
    def add_task(self, name: str, total: int = 100) -> str:
        """添加任务"""
        task_id = self.progress.add_task(name, total=total)
        self.tasks[name] = task_id
        return name
    
    def update_task(self, name: str, advance: int = 1) -> None:
        """更新任务进度"""
        if name in self.tasks:
            self.progress.update(self.tasks[name], advance=advance)
    
    def complete_task(self, name: str) -> None:
        """完成任务"""
        if name in self.tasks:
            self.progress.update(self.tasks[name], completed=True)
    
    def render(self) -> Panel:
        """渲染进度面板"""
        return Panel(self.progress, title=self.title, border_style="green")


class KeyBindingDisplay:
    """快捷键显示组件"""
    
    def __init__(self):
        self.bindings: List[tuple] = []  # (key, description)
    
    def add_binding(self, key: str, description: str) -> 'KeyBindingDisplay':
        """添加快捷键绑定"""
        self.bindings.append((key, description))
        return self
    
    def render(self) -> Panel:
        """渲染快捷键说明"""
        if not self.bindings:
            content = Text("无快捷键", style="dim")
        else:
            content = Text()
            for key, desc in self.bindings:
                content.append(f"[bold cyan]{key}[/bold cyan]: {desc}\n")
        
        return Panel(content, title="快捷键", border_style="yellow")


class InputDialog:
    """输入对话框组件"""
    
    @staticmethod
    def get_text(prompt: str, default: str = "") -> str:
        """获取文本输入"""
        return Prompt.ask(prompt, default=default)
    
    @staticmethod
    def get_choice(prompt: str, choices: List[str], default: str = "") -> str:
        """获取选择输入"""
        return Prompt.ask(prompt, choices=choices, default=default)
    
    @staticmethod
    def get_confirm(prompt: str, default: bool = True) -> bool:
        """获取确认输入"""
        return Confirm.ask(prompt, default=default)
    
    @staticmethod
    def get_number(prompt: str, default: int = 0) -> int:
        """获取数字输入"""
        while True:
            try:
                result = Prompt.ask(prompt, default=str(default))
                return int(result)
            except ValueError:
                print("请输入有效的数字")


class CardLayout:
    """卡片布局组件"""
    
    def __init__(self):
        self.cards: List[Panel] = []
    
    def add_card(self, title: str, content: str, style: str = "blue") -> 'CardLayout':
        """添加卡片"""
        card = Panel(content, title=title, border_style=style)
        self.cards.append(card)
        return self
    
    def render(self, columns: int = 2) -> Columns:
        """渲染卡片布局"""
        return Columns(self.cards, equal=True, expand=True)


class ComponentFactory:
    """组件工厂类"""
    
    @staticmethod
    def create_resume_table(selected_index: int = 0) -> 'ResumeTable':
        """创建简历表格"""
        return ResumeTable(selected_index)
    
    @staticmethod
    def create_file_upload_dialog(supported_formats: List[str] = None) -> 'FileUploadDialog':
        """创建文件上传对话框"""
        return FileUploadDialog(supported_formats=supported_formats)
    
    @staticmethod
    def create_resume_detail_panel() -> 'ResumeDetailPanel':
        """创建简历详情面板"""
        return ResumeDetailPanel()
    
    @staticmethod
    def create_analysis_table() -> 'AnalysisTable':
        """创建分析结果表格"""
        return AnalysisTable()
    
    @staticmethod
    def create_analysis_detail_panel() -> 'AnalysisDetailPanel':
        """创建分析详情面板"""
        return AnalysisDetailPanel()
    
    @staticmethod
    def create_job_table() -> 'JobTable':
        """创建职位表格"""
        return JobTable()
    
    @staticmethod
    def create_ai_analysis_dialog() -> 'AIAnalysisDialog':
        """创建AI分析对话框"""
        return AIAnalysisDialog()
    
    @staticmethod
    def create_analysis_panel() -> InfoPanel:
        """创建分析结果面板"""
        return InfoPanel("分析结果", "magenta")
    
    @staticmethod
    def create_greeting_panel() -> InfoPanel:
        """创建打招呼语面板"""
        return InfoPanel("打招呼语", "cyan")
    
    @staticmethod
    def create_main_menu() -> MenuList:
        """创建主菜单"""
        return (MenuList("主菜单", "cyan")
                .add_item("🏠 主页", "1", "white")
                .add_item("💼 职位管理", "2", "white")
                .add_item("📄 简历管理", "3", "white")
                .add_item("🤖 AI分析", "4", "white")
                .add_item("💬 打招呼语", "5", "white")
                .add_item("⚙️ 设置", "6", "white"))
    
    @staticmethod
    def create_help_panel() -> InfoPanel:
        """创建帮助面板"""
        return (InfoPanel("帮助信息", "yellow")
                .add_header("快捷键说明")
                .add_key_value("1-6", "切换面板")
                .add_key_value("q", "退出程序")
                .add_key_value("h", "显示帮助")
                .add_key_value("r", "刷新界面")
                .add_key_value("Ctrl+C", "强制退出"))


class FileUploadDialog:
    """文件上传对话框组件"""
    
    def __init__(self, title: str = "上传简历", supported_formats: List[str] = None):
        self.title = title
        self.supported_formats = supported_formats or ['pdf', 'md', 'markdown']
        self.console = Console()
    
    def show_file_input(self) -> Optional[str]:
        """显示文件输入对话框
        
        Returns:
            Optional[str]: 用户输入的文件路径，取消返回None
        """
        # 显示支持的格式信息
        format_text = Text()
        format_text.append("支持的格式: ", style="bold")
        format_text.append(", ".join(self.supported_formats), style="green")
        
        self.console.print(Panel(format_text, title="📁 文件上传", border_style="blue"))
        
        # 获取文件路径
        try:
            file_path = Prompt.ask(
                "[cyan]请输入文件路径[/cyan]",
                default="",
                show_default=False
            )
            
            if not file_path or file_path.strip() == "":
                return None
                
            return file_path.strip()
        except (KeyboardInterrupt, EOFError):
            return None
    
    def show_upload_progress(self, filename: str) -> ProgressDisplay:
        """显示上传进度
        
        Args:
            filename: 文件名
            
        Returns:
            ProgressDisplay: 进度显示组件
        """
        progress = ProgressDisplay(f"正在处理: {filename}")
        progress.add_task("解析文件", total=100)
        return progress
    
    def show_success_message(self, resume_info: Dict[str, Any]):
        """显示上传成功消息
        
        Args:
            resume_info: 简历信息
        """
        success_panel = InfoPanel("上传成功", "green")
        success_panel.add_header("文件信息")
        success_panel.add_key_value("文件名", resume_info.get('filename', 'N/A'))
        success_panel.add_key_value("格式", resume_info.get('file_type', 'N/A'))
        success_panel.add_key_value("大小", f"{resume_info.get('file_size', 0)} 字节")
        success_panel.add_key_value("字数", str(resume_info.get('word_count', 0)))
        
        self.console.print(success_panel.render())
    
    def show_error_message(self, error: str):
        """显示错误消息
        
        Args:
            error: 错误信息
        """
        error_text = Text()
        error_text.append("❌ 上传失败\n\n", style="bold red")
        error_text.append(f"错误: {error}", style="red")
        
        self.console.print(Panel(error_text, title="错误", border_style="red"))


class ResumeTable(DataTable):
    """简历表格组件（增强版）"""
    
    def __init__(self, selected_index: int = 0):
        super().__init__("简历列表", "cyan")
        # 设置列
        self.add_column("选择", "bold")
        self.add_column("ID", "dim")
        self.add_column("文件名", "white")
        self.add_column("格式", "yellow")
        self.add_column("大小", "cyan")
        self.add_column("创建时间", "green")
        self.add_column("状态", "bold")
        self.selected_index = selected_index
        self.resume_count = 0
    
    def add_resume_row(self, resume_data: Dict[str, Any]) -> 'ResumeTable':
        """添加简历行数据
        
        Args:
            resume_data: 简历数据字典
        """
        # 格式化文件大小
        file_size = resume_data.get('file_size', 0)
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} B"
        
        # 格式化创建时间
        created_at = resume_data.get('created_at', '')
        if hasattr(created_at, 'strftime'):
            time_str = created_at.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = str(created_at)[:16] if created_at else 'N/A'
        
        # 确定选中状态
        is_selected = self.resume_count == self.selected_index
        select_indicator = "▶ " if is_selected else "  "
        
        # 添加行
        self.add_row(
            select_indicator,
            resume_data.get('id', '')[:8] + '...',  # 短ID
            resume_data.get('filename', 'N/A'),
            resume_data.get('file_type', 'N/A').upper(),
            size_str,
            time_str,
            "✅ 已解析"
        )
        self.resume_count += 1
        return self


class ResumeDetailPanel(InfoPanel):
    """简历详情面板"""
    
    def __init__(self):
        super().__init__("简历详情", "blue")
    
    def set_resume_data(self, resume_data: Dict[str, Any]) -> 'ResumeDetailPanel':
        """设置简历数据
        
        Args:
            resume_data: 简历数据
        """
        self.clear()
        
        # 基本信息
        self.add_header("基本信息")
        self.add_key_value("文件名", resume_data.get('filename', 'N/A'))
        self.add_key_value("格式", resume_data.get('file_type', 'N/A').upper())
        self.add_key_value("文件大小", self._format_file_size(resume_data.get('file_size', 0)))
        
        # 内容统计
        self.add_separator()
        self.add_header("内容统计")
        metadata = resume_data.get('metadata', {})
        self.add_key_value("字符数", str(metadata.get('char_count', 0)))
        self.add_key_value("单词数", str(metadata.get('word_count', 0)))
        
        # 时间信息
        self.add_separator()
        self.add_header("时间信息")
        created_at = resume_data.get('created_at')
        updated_at = resume_data.get('updated_at')
        
        if created_at:
            self.add_key_value("创建时间", self._format_datetime(created_at))
        if updated_at:
            self.add_key_value("更新时间", self._format_datetime(updated_at))
        
        return self
    
    def _format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        if size > 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size} B"
    
    def _format_datetime(self, dt) -> str:
        """格式化日期时间"""
        if hasattr(dt, 'strftime'):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(dt) if dt else 'N/A'


class AnalysisTable(DataTable):
    """分析结果表格组件"""
    
    def __init__(self):
        super().__init__("分析历史", "magenta")
        # 设置列
        self.add_column("ID", "dim")
        self.add_column("职位", "white")
        self.add_column("匹配度", "bold")
        self.add_column("分析时间", "cyan")
        self.add_column("状态", "green")
    
    def add_analysis_row(self, analysis_data: Dict[str, Any]) -> 'AnalysisTable':
        """添加分析结果行数据
        
        Args:
            analysis_data: 分析数据字典
        """
        # 格式化匹配度
        overall_score = analysis_data.get('overall_score', 0)
        if overall_score >= 80:
            score_color = "✅"
        elif overall_score >= 60:
            score_color = "⚠️"
        else:
            score_color = "❌"
        
        # 格式化分析时间
        created_at = analysis_data.get('created_at', '')
        if hasattr(created_at, 'strftime'):
            time_str = created_at.strftime('%m-%d %H:%M')
        else:
            time_str = str(created_at)[:16] if created_at else 'N/A'
        
        # 添加行
        self.add_row(
            analysis_data.get('id', '')[:8] + '...',  # 短ID
            analysis_data.get('job_title', 'N/A'),
            f"{score_color} {overall_score:.1f}%",
            time_str,
            "已完成"
        )
        return self


class AnalysisDetailPanel(InfoPanel):
    """分析详情面板"""
    
    def __init__(self):
        super().__init__("分析详情", "magenta")
    
    def set_analysis_data(self, analysis_data: Dict[str, Any]) -> 'AnalysisDetailPanel':
        """设置分析数据
        
        Args:
            analysis_data: 分析数据
        """
        self.clear()
        
        # 总体评分
        overall_score = analysis_data.get('overall_score', 0)
        score_color = "green" if overall_score >= 80 else "yellow" if overall_score >= 60 else "red"
        
        self.add_header("总体匹配度")
        self.add_key_value("评分", f"{overall_score:.1f}%", "cyan", score_color)
        
        # 分项评分
        match_scores = analysis_data.get('match_scores', {})
        if match_scores:
            self.add_separator()
            self.add_header("分项评分")
            for category, score in match_scores.items():
                color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
                self.add_key_value(category, f"{score:.1f}%", "cyan", color)
        
        # 优势和劣势
        strengths = analysis_data.get('strengths', [])
        if strengths:
            self.add_separator()
            self.add_header("优势分析")
            for strength in strengths[:3]:  # 显示前3个
                self.add_line(f"✓ {strength}", "green")
        
        weaknesses = analysis_data.get('weaknesses', [])
        if weaknesses:
            self.add_separator()
            self.add_header("待改进")
            for weakness in weaknesses[:3]:  # 显示前3个
                self.add_line(f"⚠ {weakness}", "yellow")
        
        return self


class JobTable(DataTable):
    """职位表格组件"""
    
    def __init__(self):
        super().__init__("职位列表", "blue")
        # 设置列
        self.add_column("ID", "dim")
        self.add_column("职位名称", "white")
        self.add_column("公司", "cyan")
        self.add_column("地点", "yellow")
        self.add_column("状态", "bold")
    
    def add_job_row(self, job_data: Dict[str, Any]) -> 'JobTable':
        """添加职位行数据
        
        Args:
            job_data: 职位数据字典
        """
        # 状态图标
        status = job_data.get('status', 'active')
        status_icons = {
            'active': '🟢 活跃',
            'applied': '📤 已申请',
            'archived': '📁 已归档'
        }
        status_display = status_icons.get(status, status)
        
        # 添加行
        self.add_row(
            job_data.get('id', '')[:8] + '...',  # 短ID
            job_data.get('title', 'N/A'),
            job_data.get('company', 'N/A'),
            job_data.get('location', 'N/A'),
            status_display
        )
        return self


class AIAnalysisDialog:
    """AI分析对话框组件"""
    
    def __init__(self):
        from rich.console import Console
        self.console = Console()
    
    def show_analysis_selection(self, resumes: List, jobs: List) -> Optional[tuple]:
        """显示分析选择对话框
        
        Args:
            resumes: 简历列表
            jobs: 职位列表
            
        Returns:
            Optional[tuple]: (resume, job) 或 None
        """
        try:
            if not resumes:
                self.console.print("[yellow]没有可用的简历，请先上传简历[/yellow]")
                return None
            
            if not jobs:
                self.console.print("[yellow]没有可用的职位，请先添加职位[/yellow]")
                return None
            
            # 选择简历
            self.console.print("\n[bold]选择要分析的简历:[/bold]")
            for i, resume in enumerate(resumes, 1):
                self.console.print(f"{i}. {resume.filename}")
            
            from rich.prompt import IntPrompt
            resume_choice = IntPrompt.ask(
                "输入简历序号",
                default=1,
                choices=[str(i) for i in range(1, len(resumes) + 1)]
            )
            selected_resume = resumes[resume_choice - 1]
            
            # 选择职位
            self.console.print("\n[bold]选择目标职位:[/bold]")
            for i, job in enumerate(jobs, 1):
                self.console.print(f"{i}. {job.title} @ {job.company}")
            
            job_choice = IntPrompt.ask(
                "输入职位序号",
                default=1,
                choices=[str(i) for i in range(1, len(jobs) + 1)]
            )
            selected_job = jobs[job_choice - 1]
            
            return (selected_resume, selected_job)
            
        except (KeyboardInterrupt, EOFError):
            self.console.print("[yellow]取消分析操作[/yellow]")
            return None
    
    def show_analysis_progress(self, resume_name: str, job_title: str):
        """显示分析进度
        
        Args:
            resume_name: 简历名称
            job_title: 职位名称
        """
        progress_panel = InfoPanel("正在分析", "blue")
        progress_panel.add_header("分析进度")
        progress_panel.add_key_value("简历", resume_name)
        progress_panel.add_key_value("职位", job_title)
        progress_panel.add_line("🤖 AI正在分析中，请稍候...", "yellow")
        
        self.console.print(progress_panel.render())
    
    def show_analysis_result(self, result_data: Dict[str, Any]):
        """显示分析结果
        
        Args:
            result_data: 分析结果数据
        """
        # 创建结果面板
        result_panel = AnalysisDetailPanel()
        result_panel.set_analysis_data(result_data)
        
        self.console.print(result_panel.render())
        
        # 显示优化建议
        suggestions = result_data.get('suggestions', [])
        if suggestions:
            suggestion_panel = InfoPanel("优化建议", "yellow")
            suggestion_panel.add_header("AI建议")
            for i, suggestion in enumerate(suggestions, 1):
                suggestion_panel.add_line(f"{i}. {suggestion}", "white")
            
            self.console.print(suggestion_panel.render())
        
        # 技能对比
        matching_skills = result_data.get('matching_skills', [])
        missing_skills = result_data.get('missing_skills', [])
        
        if matching_skills or missing_skills:
            skill_panel = InfoPanel("技能分析", "cyan")
            
            if matching_skills:
                skill_panel.add_header("匹配技能")
                for skill in matching_skills[:5]:  # 显示前5个
                    skill_panel.add_line(f"✓ {skill}", "green")
            
            if missing_skills:
                skill_panel.add_separator()
                skill_panel.add_header("建议学习")
                for skill in missing_skills[:5]:  # 显示前5个
                    skill_panel.add_line(f"⚬ {skill}", "yellow")
            
            self.console.print(skill_panel.render())
    
    def show_error_message(self, error: str):
        """显示错误消息
        
        Args:
            error: 错误信息
        """
        from rich.text import Text
        error_text = Text()
        error_text.append("❌ 分析失败\n\n", style="bold red")
        error_text.append(f"错误: {error}", style="red")
        
        from rich.panel import Panel
        self.console.print(Panel(error_text, title="错误", border_style="red"))