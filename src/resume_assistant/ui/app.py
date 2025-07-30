"""主TUI应用程序"""

import asyncio
from typing import Dict, Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.align import Align

from ..config import get_settings
from ..utils import get_logger
from ..core.resume_processor import ResumeProcessor
from ..core.ai_analyzer import AIAnalyzer, JobInfo
from ..core.job_manager import JobManager
from ..data.sample_data import (
    get_sample_jobs, get_sample_resumes, get_sample_analysis,
    get_sample_greetings, get_sample_settings, DEMO_JOBS, 
    DEMO_RESUMES, DEMO_ANALYSIS, DEMO_GREETINGS
)
from .components import (
    DataTable, InfoPanel, StatusBar, MenuList, 
    ComponentFactory, KeyBindingDisplay, InputDialog,
    FileUploadDialog, ResumeTable, ResumeDetailPanel,
    AnalysisTable, AnalysisDetailPanel, JobTable, AIAnalysisDialog
)


class ResumeAssistantApp:
    """Resume Assistant 主应用程序"""
    
    def __init__(self):
        self.console = Console()
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.current_panel = "主页"
        self.running = False
        self.command_mode = False  # 默认为浏览模式
        self.scroll_offset = 0  # 滚动偏移量
        
        # 初始化核心组件
        self.resume_processor = ResumeProcessor()
        self.job_manager = JobManager()
        self.ai_analyzer = AIAnalyzer()
        
        # 初始化示例数据（如果需要）
        self._ensure_sample_data()
        
        # 初始化布局
        self.layout = self._create_layout()
        
        # 面板选项
        self.panels = {
            "主页": "🏠",
            "职位管理": "💼", 
            "简历管理": "📄",
            "AI分析": "🤖",
            "打招呼语": "💬",
            "设置": "⚙️"
        }
        
        # 面板数据缓存（用于滚动）
        self.panel_data = {}
        
        # 初始化组件
        self.main_menu = ComponentFactory.create_main_menu()
        self.status_bar = StatusBar()
        self.key_bindings = KeyBindingDisplay()
        self._init_key_bindings()
    
    def _create_layout(self) -> Layout:
        """创建主布局"""
        layout = Layout()
        
        # 分割为三个区域：标题、主体、状态栏
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # 主体区域分割为导航和内容
        layout["main"].split_row(
            Layout(name="sidebar", size=25),
            Layout(name="content")
        )
        
        return layout
    
    def _init_key_bindings(self):
        """初始化快捷键绑定"""
        self.key_bindings = (KeyBindingDisplay()
                           .add_binding("1-6", "直接切换面板")
                           .add_binding("j/k/↑/↓", "滚动内容")
                           .add_binding(":", "命令模式")
                           .add_binding("q", "退出程序")
                           .add_binding("h", "显示帮助")
                           .add_binding("r", "刷新界面"))
    
    def _create_header(self) -> Panel:
        """创建标题栏"""
        title = Text("🚀 Resume Assistant", style="bold magenta")
        subtitle = Text("AI-powered resume optimization tool", style="dim")
        header_content = Align.center(f"{title}\n{subtitle}")
        
        return Panel(
            header_content,
            style="bright_blue",
            height=3
        )
    
    def _create_sidebar(self) -> Panel:
        """创建侧边栏导航"""
        # 更新主菜单选中状态
        panel_names = list(self.panels.keys())
        if self.current_panel in panel_names:
            selected_index = panel_names.index(self.current_panel)
            self.main_menu.select_item(selected_index)
        
        return self.main_menu.render()
    
    def _create_content(self) -> Panel:
        """创建内容区域"""
        if self.current_panel == "主页":
            return self._create_home_panel()
        elif self.current_panel == "职位管理":
            return self._create_jobs_panel()
        elif self.current_panel == "简历管理":
            return self._create_resumes_panel()
        elif self.current_panel == "AI分析":
            return self._create_analysis_panel()
        elif self.current_panel == "打招呼语":
            return self._create_greeting_panel()
        elif self.current_panel == "设置":
            return self._create_settings_panel()
        else:
            return Panel("未知面板", title="错误")
    
    def _create_home_panel(self) -> Panel:
        """创建主页面板"""
        welcome_text = Text()
        welcome_text.append("欢迎使用 Resume Assistant! 🎉\n\n", style="bold green")
        welcome_text.append("功能特性:\n", style="bold")
        welcome_text.append("• 🤖 AI 驱动的简历分析\n", style="cyan")
        welcome_text.append("• 📊 职位匹配度评估\n", style="cyan")
        welcome_text.append("• 💡 智能优化建议\n", style="cyan")
        welcome_text.append("• 💬 个性化打招呼语生成\n", style="cyan")
        welcome_text.append("• 📋 完整的数据管理\n\n", style="cyan")
        
        welcome_text.append("使用说明:\n", style="bold")
        welcome_text.append("1. 直接按数字键 1-6 切换不同功能面板（无需回车）\n", style="yellow")
        welcome_text.append("2. 使用 j/k 或 ↑/↓ 键滚动内容（vim风格）\n", style="yellow")
        welcome_text.append("3. 按 : 进入命令模式（需要回车确认命令）\n", style="yellow")
        welcome_text.append("4. 在简历管理面板中：按u上传、v查看、d删除\n", style="yellow")
        welcome_text.append("5. 在职位管理中添加目标职位\n", style="yellow")
        welcome_text.append("6. 使用AI分析获得优化建议\n", style="yellow")
        welcome_text.append("7. 生成个性化的打招呼语\n", style="yellow")
        
        return Panel(
            Align.center(welcome_text),
            title="🏠 主页",
            border_style="green"
        )
    
    def _create_jobs_panel(self) -> Panel:
        """创建职位管理面板"""
        # 创建职位表格
        job_table = ComponentFactory.create_job_table()
        
        # 获取真实职位数据
        try:
            jobs = self.job_manager.list_jobs()
            if jobs:
                for job in jobs:
                    job_data = {
                        'id': job.id,
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'status': job.status
                    }
                    job_table.add_job_row(job_data)
            else:
                job_table.add_row("无数据", "请添加职位信息", "-", "-", "等待添加")
        except Exception as e:
            self.logger.error(f"加载职位列表失败: {e}")
            job_table.add_row("错误", f"加载失败: {str(e)}", "-", "-", "❌ 错误")
        
        # 创建功能说明
        info_panel = (InfoPanel("功能操作", "blue")
                     .add_header("当前功能")
                     .add_line("• 职位列表展示", "green")
                     .add_line("• 示例职位数据", "green")
                     .add_line("• 职位状态管理", "green")
                     .add_separator()
                     .add_header("操作说明")
                     .add_line("a - 添加新职位", "yellow")
                     .add_line("v - 查看职位详情", "yellow")
                     .add_line("d - 删除职位", "yellow")
                     .add_separator()
                     .add_header("支持功能")
                     .add_line("• 职位信息管理", "cyan")
                     .add_line("• AI分析配对", "cyan")
                     .add_line("• 状态跟踪", "cyan"))
        
        # 组合内容
        from rich.columns import Columns
        content = Columns([job_table.render(), info_panel.render()], equal=True)
        
        return Panel(content, title="💼 职位管理", border_style="blue")
    
    def _create_resumes_panel(self) -> Panel:
        """创建简历管理面板"""
        # 创建简历表格
        resume_table = ComponentFactory.create_resume_table()
        
        # 获取真实的简历数据
        try:
            resumes = self.resume_processor.list_resumes()
            if resumes:
                for resume in resumes:
                    resume_data = {
                        'id': resume.id,
                        'filename': resume.filename,
                        'file_type': resume.file_type,
                        'file_size': resume.file_size,
                        'created_at': resume.created_at,
                        'metadata': resume.metadata
                    }
                    resume_table.add_resume_row(resume_data)
            else:
                # 如果没有简历，显示提示信息
                resume_table.add_row("无数据", "请上传简历文件", "-", "-", "-", "等待上传")
        except Exception as e:
            self.logger.error(f"加载简历列表失败: {e}")
            resume_table.add_row("错误", f"加载失败: {str(e)}", "-", "-", "-", "❌ 错误")
        
        # 创建功能说明和操作指南
        info_panel = (InfoPanel("功能操作", "green")
                     .add_header("当前功能")
                     .add_line("• 简历列表展示", "green")
                     .add_line("• PDF/Markdown解析", "green")
                     .add_line("• 文件信息统计", "green")
                     .add_separator()
                     .add_header("操作说明")
                     .add_line("u - 上传新简历", "yellow")
                     .add_line("d - 删除选中简历", "yellow")
                     .add_line("v - 查看简历详情", "yellow")
                     .add_separator()
                     .add_header("支持格式")
                     .add_line("• PDF文件 (.pdf)", "cyan")
                     .add_line("• Markdown文件 (.md)", "cyan")
                     .add_line("• 文本文件 (.txt)", "cyan"))
        
        # 组合内容
        from rich.columns import Columns
        content = Columns([resume_table.render(), info_panel.render()], equal=True)
        
        return Panel(content, title="📄 简历管理", border_style="green")
    
    def _create_analysis_panel(self) -> Panel:
        """创建AI分析面板"""
        # 创建分析历史表格
        analysis_table = ComponentFactory.create_analysis_table()
        
        # 获取分析历史数据
        try:
            analyses = self.ai_analyzer.list_analysis()
            if analyses:
                for analysis in analyses[:10]:  # 显示最近10条
                    # 获取职位标题
                    job = self.job_manager.get_job(analysis.job_id)
                    job_title = job.title if job else "未知职位"
                    
                    analysis_data = {
                        'id': analysis.id,
                        'job_title': job_title,
                        'overall_score': analysis.overall_score,
                        'created_at': analysis.created_at
                    }
                    analysis_table.add_analysis_row(analysis_data)
            else:
                analysis_table.add_row("无数据", "请先进行AI分析", "-", "-", "等待分析")
        except Exception as e:
            self.logger.error(f"加载分析历史失败: {e}")
            analysis_table.add_row("错误", f"加载失败: {str(e)}", "-", "-", "❌ 错误")
        
        # 创建功能说明和状态
        ai_status = "🟢 可用" if self.ai_analyzer.is_available() else "🟡 模拟模式"
        
        info_panel = (InfoPanel("AI分析功能", "magenta")
                     .add_header("功能状态")
                     .add_key_value("AI服务", ai_status)
                     .add_key_value("分析引擎", "DeepSeek API")
                     .add_separator()
                     .add_header("操作说明")
                     .add_line("s - 开始新的分析", "yellow")
                     .add_line("v - 查看分析详情", "yellow")
                     .add_line("d - 删除分析记录", "yellow")
                     .add_separator()
                     .add_header("分析维度")
                     .add_line("• 技能匹配度评估", "cyan")
                     .add_line("• 经验背景分析", "cyan")
                     .add_line("• 岗位契合度", "cyan")
                     .add_line("• 优化建议生成", "cyan"))
        
        # 组合内容
        from rich.columns import Columns
        content = Columns([analysis_table.render(), info_panel.render()], equal=True)
        
        return Panel(content, title="🤖 AI 分析", border_style="magenta")
    
    def _create_greeting_panel(self) -> Panel:
        """创建打招呼语面板"""
        # 使用示例数据
        greetings_data = DEMO_GREETINGS
        
        # 创建打招呼语展示面板
        greeting_panel = ComponentFactory.create_greeting_panel()
        greeting_panel.set_scroll_offset(self.scroll_offset)
        greeting_panel.add_header("当前推荐版本：专业型")
        
        # 分行显示打招呼语
        lines = greetings_data["专业型"].split("。")
        for line in lines:
            if line.strip():
                greeting_panel.add_line(f"{line.strip()}。", "white")
        
        greeting_panel.add_separator()
        greeting_panel.add_header("其他版本预览")
        
        for version, content in greetings_data.items():
            if version != "专业型":
                preview = content[:30] + "..." if len(content) > 30 else content
                color = "green" if version == "项目导向" else "yellow"
                greeting_panel.add_line(f"{version}: {preview}", color)
        
        greeting_panel.add_separator()
        greeting_panel.add_header("完整版本内容")
        
        # 添加所有版本的完整内容用于滚动测试
        for version, content in greetings_data.items():
            greeting_panel.add_line(f"\n[{version}]", "bold cyan")
            lines = content.split("。")
            for line in lines:
                if line.strip():
                    greeting_panel.add_line(f"  {line.strip()}。", "white")
        
        # 创建功能说明
        info_panel = (InfoPanel("功能说明", "cyan")
                     .add_header("当前功能")
                     .add_line("• 示例打招呼语展示", "green")
                     .add_line("• 多版本方案展示", "green")
                     .add_separator()
                     .add_header("开发中功能")
                     .add_line("• 基于职位和简历生成开场白", "yellow")
                     .add_line("• 多版本方案提供", "yellow")
                     .add_line("• 个性化定制", "yellow")
                     .add_line("• 历史记录管理", "yellow"))
        
        # 组合内容
        from rich.columns import Columns
        content = Columns([greeting_panel.render(), info_panel.render()], equal=True)
        
        return Panel(content, title="💬 打招呼语", border_style="cyan")
    
    def _create_settings_panel(self) -> Panel:
        """创建设置面板"""
        settings_table = Table(show_header=True, header_style="bold magenta")
        settings_table.add_column("设置项", style="cyan", no_wrap=True)
        settings_table.add_column("当前值", style="yellow")
        
        settings_table.add_row("主题", self.settings.theme)
        settings_table.add_row("日志级别", self.settings.log_level)
        settings_table.add_row("Agent类型", self.settings.agent_type)
        settings_table.add_row("自动保存", "启用" if self.settings.auto_save else "禁用")
        
        content = Text()
        content.append("⚙️ 系统设置\n\n", style="bold")
        
        return Panel(
            settings_table,
            title="⚙️ 设置",
            border_style="yellow"
        )
    
    def _create_footer(self) -> Panel:
        """创建状态栏"""
        # 更新状态栏
        self.status_bar.clear()
        
        # 显示当前模式
        mode = "命令模式" if self.command_mode else "浏览模式"
        mode_color = "red" if self.command_mode else "green"
        self.status_bar.add_item(f"模式: {mode}", f"bold {mode_color}")
        self.status_bar.add_separator()
        
        self.status_bar.add_item(f"当前面板: {self.current_panel}", "bold cyan")
        self.status_bar.add_separator()
        
        if self.command_mode:
            self.status_bar.add_item("输入'esc'并回车退出命令模式", "yellow")
        else:
            self.status_bar.add_item("1-6 面板", "green")
            self.status_bar.add_separator()
            self.status_bar.add_item("j/k ↑/↓ 滚动", "green")
            self.status_bar.add_separator()
            self.status_bar.add_item(": 命令", "yellow")
            self.status_bar.add_separator()
            self.status_bar.add_item("q 退出", "red")
        
        return self.status_bar.render()
    
    def _update_layout(self):
        """更新布局内容"""
        self.layout["header"].update(self._create_header())
        self.layout["sidebar"].update(self._create_sidebar())
        self.layout["content"].update(self._create_content())
        self.layout["footer"].update(self._create_footer())
    
    def _handle_key(self, key: str) -> bool:
        """处理按键输入
        
        Returns:
            bool: True表示继续运行，False表示退出
        """
        # 处理退出
        if key == 'q' and not self.command_mode:
            return False
        
        # 处理命令模式切换
        if key == ':' and not self.command_mode:
            self.command_mode = True
            self.logger.info("进入命令模式")
            # 显示命令模式提示
            self.console.print("\n[yellow]进入命令模式...[/yellow]")
            return True
        
        # 在命令模式下的处理
        if self.command_mode:
            return self._handle_command_key(key)
        else:
            return self._handle_normal_key(key)
    
    def _handle_normal_key(self, key: str) -> bool:
        """处理浏览模式下的按键"""
        if key == 'r':
            # 刷新界面
            self.scroll_offset = 0
            self.logger.info("刷新界面")
            return True
        elif key in '123456':
            # 直接切换面板
            panel_names = list(self.panels.keys())
            panel_index = int(key) - 1
            if 0 <= panel_index < len(panel_names):
                old_panel = self.current_panel
                self.current_panel = panel_names[panel_index]
                self.scroll_offset = 0  # 重置滚动偏移
                self.logger.info(f"切换面板: {old_panel} -> {self.current_panel}")
        elif key in ('up', 'k'):
            # 向上滚动，只有成功滚动时才刷新界面
            if self._scroll_up():
                return True
            else:
                return None  # 滚动失败，不刷新界面
        elif key in ('down', 'j'):
            # 向下滚动，只有成功滚动时才刷新界面
            if self._scroll_down():
                return True
            else:
                return None  # 滚动失败，不刷新界面
        elif key == 'h':
            # 显示帮助
            return True
        elif key == 'u' and self.current_panel == "简历管理":
            # 上传简历
            self._handle_resume_upload()
            return True
        elif key == 'd' and self.current_panel == "简历管理":
            # 删除简历
            self._handle_resume_delete()
            return True
        elif key == 'v' and self.current_panel == "简历管理":
            # 查看简历详情
            self._handle_resume_view()
            return True
        elif key == 's' and self.current_panel == "AI分析":
            # 开始新的分析
            self._handle_ai_analysis_start()
            return True
        elif key == 'v' and self.current_panel == "AI分析":
            # 查看分析详情
            self._handle_analysis_view()
            return True
        elif key == 'd' and self.current_panel == "AI分析":
            # 删除分析记录
            self._handle_analysis_delete()
            return True
        
        return True
    
    def _handle_command_key(self, key: str) -> bool:
        """处理命令模式下的按键"""
        if key == 'q':
            # 在命令模式下也可以退出
            return False
        elif key == 'escape':
            # ESC键退出命令模式
            self.command_mode = False
            self.logger.info("通过ESC退出命令模式")
            return True
        elif key in '123456':
            # 在命令模式下切换面板
            panel_names = list(self.panels.keys())
            panel_index = int(key) - 1
            if 0 <= panel_index < len(panel_names):
                old_panel = self.current_panel
                self.current_panel = panel_names[panel_index]
                self.scroll_offset = 0
                self.command_mode = False  # 切换后退出命令模式
                self.logger.info(f"命令模式切换面板: {old_panel} -> {self.current_panel}")
        elif key == 'r':
            # 刷新
            self.scroll_offset = 0
            self.command_mode = False
            self.logger.info("命令模式刷新界面")
        
        return True
    
    def _scroll_up(self) -> bool:
        """向上滚动
        
        Returns:
            bool: True表示成功滚动，False表示已到顶部
        """
        if self.scroll_offset > 0:
            self.scroll_offset -= 1
            self.logger.info(f"向上滚动，当前偏移: {self.scroll_offset}")
            return True
        return False
    
    def _scroll_down(self) -> bool:
        """向下滚动
        
        Returns:
            bool: True表示成功滚动，False表示已到底部
        """
        # 设置一个合理的最大滚动量（可以根据面板内容动态调整）
        max_scroll = self._get_max_scroll_for_current_panel()
        if self.scroll_offset < max_scroll:
            self.scroll_offset += 1
            self.logger.info(f"向下滚动，当前偏移: {self.scroll_offset}")
            return True
        return False
    
    def _get_max_scroll_for_current_panel(self) -> int:
        """获取当前面板的最大滚动量"""
        # 根据不同面板返回不同的最大滚动量
        scroll_limits = {
            "主页": 0,  # 主页不需要滚动
            "职位管理": 5,  # 职位管理可以滚动5行
            "简历管理": 3,  # 简历管理可以滚动3行
            "AI分析": 8,   # AI分析内容较多，可以滚动8行
            "打招呼语": 4,  # 打招呼语可以滚动4行
            "设置": 2      # 设置可以滚动2行
        }
        return scroll_limits.get(self.current_panel, 0)
    
    def _next_panel(self):
        """切换到下一个面板"""
        panel_names = list(self.panels.keys())
        current_index = panel_names.index(self.current_panel)
        next_index = (current_index + 1) % len(panel_names)
        old_panel = self.current_panel
        self.current_panel = panel_names[next_index]
        self.logger.info(f"切换到下一个面板: {old_panel} -> {self.current_panel}")
    
    def _previous_panel(self):
        """切换到上一个面板"""
        panel_names = list(self.panels.keys())
        current_index = panel_names.index(self.current_panel)
        prev_index = (current_index - 1) % len(panel_names)
        old_panel = self.current_panel
        self.current_panel = panel_names[prev_index]
        self.logger.info(f"切换到上一个面板: {old_panel} -> {self.current_panel}")
    
    def run(self):
        """运行应用程序"""
        self.logger.info("启动Resume Assistant TUI应用")
        self.running = True
        
        try:
            import termios
            import sys
            import tty
            
            # 保存原始终端设置
            try:
                old_settings = termios.tcgetattr(sys.stdin)
                has_terminal = True
            except (termios.error, OSError) as e:
                self.logger.warning(f"无法获取终端设置，使用简化模式: {e}")
                has_terminal = False
                old_settings = None
            
            # 显示初始界面
            self._update_layout()
            self.console.print(self.layout)
            
            # 实时交互循环
            while self.running:
                try:
                    # 根据当前模式显示不同的提示
                    if self.command_mode:
                        prompt = "\n[red]命令模式[/red] [cyan](输入命令并按回车确认, 或输入'esc'退出): [/cyan]"
                        self.console.print(prompt, end="")
                        
                        # 命令模式总是使用input()等待回车确认，支持多字符命令
                        user_input = input().strip().lower()
                        
                        # 处理特殊命令
                        if user_input in ('esc', 'escape', '\x1b'):
                            user_input = 'escape'
                    else:
                        if has_terminal:
                            # 浏览模式默认不显示命令提示栏，直接等待按键
                            tty.setraw(sys.stdin.fileno())
                            try:
                                ch = sys.stdin.read(1)
                                user_input = ch.lower()
                                # 处理特殊按键（方向键等）
                                if ch == '\x1b':  # ESC或方向键序列开始
                                    seq = sys.stdin.read(2)
                                    if seq == '[A':
                                        user_input = 'up'
                                    elif seq == '[B':
                                        user_input = 'down'
                                    elif seq == '[C':
                                        user_input = 'right'
                                    elif seq == '[D':
                                        user_input = 'left'
                                    else:
                                        user_input = 'escape'
                            finally:
                                # 恢复终端设置
                                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        else:
                            # 简化模式，显示提示并使用input()
                            prompt = "\n[green]浏览模式[/green] [cyan](1-6切换面板, :命令模式, q退出): [/cyan]"
                            self.console.print(prompt, end="")
                            user_input = input().strip().lower()
                    
                    # 处理特殊输入
                    if user_input == 'h':
                        self._show_help()
                        continue
                    
                    result = self._handle_key(user_input)
                    if result is False:
                        # 退出程序
                        break
                    elif result is True:
                        # 需要刷新界面
                        self.console.clear()
                        self._update_layout()
                        self.console.print(self.layout)
                    # result为None或其他值时，不刷新界面
                        
                except (EOFError, KeyboardInterrupt):
                    break
            
            # 恢复终端设置
            if has_terminal and old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        
        except Exception as e:
            self.logger.error(f"TUI运行错误: {e}")
            # 确保恢复终端设置
            if has_terminal and old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except:
                    pass
            
        self.logger.info("Resume Assistant TUI应用已退出")
        self.console.print("\n[green]感谢使用 Resume Assistant！[/green]")
    
    def _show_help(self):
        """显示帮助信息"""
        help_panel = ComponentFactory.create_help_panel()
        help_panel.add_separator()
        help_panel.add_header("面板导航")
        for i, (panel_name, icon) in enumerate(self.panels.items(), 1):
            help_panel.add_key_value(str(i), f"{icon} {panel_name}")
        
        help_panel.add_separator()
        help_panel.add_header("滚动和导航")
        help_panel.add_key_value("j/k", "向下/向上滚动（vim风格）")
        help_panel.add_key_value("↑/↓", "向上/向下滚动")
        
        help_panel.add_separator()
        help_panel.add_header("其他快捷键")
        help_panel.add_key_value(":", "进入命令模式")
        help_panel.add_key_value("r", "刷新界面")
        help_panel.add_key_value("q", "退出程序")
        
        self.console.print(help_panel.render())
    
    def _ensure_sample_data(self):
        """确保有示例数据可用"""
        try:
            # 检查是否有职位数据
            jobs = self.job_manager.list_jobs()
            if not jobs:
                self.logger.info("创建示例职位数据")
                self.job_manager.create_sample_jobs()
        except Exception as e:
            self.logger.warning(f"初始化示例数据失败: {e}")
    
    def _handle_resume_upload(self):
        """处理简历上传"""
        try:
            # 创建文件上传对话框
            upload_dialog = ComponentFactory.create_file_upload_dialog(
                supported_formats=self.resume_processor.supported_formats
            )
            
            # 显示文件输入对话框
            file_path = upload_dialog.show_file_input()
            if not file_path:
                return
            
            # 显示处理进度
            import os
            filename = os.path.basename(file_path)
            progress = upload_dialog.show_upload_progress(filename)
            
            try:
                # 上传并处理简历
                resume = self.resume_processor.upload_resume(file_path)
                
                # 显示成功消息
                resume_info = {
                    'filename': resume.filename,
                    'file_type': resume.file_type,
                    'file_size': resume.file_size,
                    'word_count': resume.metadata.get('word_count', 0)
                }
                upload_dialog.show_success_message(resume_info)
                
                self.logger.info(f"简历上传成功: {resume.filename}")
                
            except Exception as e:
                # 显示错误消息
                upload_dialog.show_error_message(str(e))
                self.logger.error(f"简历上传失败: {e}")
                
        except Exception as e:
            self.logger.error(f"上传对话框错误: {e}")
    
    def _handle_resume_delete(self):
        """处理简历删除"""
        try:
            resumes = self.resume_processor.list_resumes()
            if not resumes:
                self.console.print("[yellow]没有可删除的简历[/yellow]")
                return
            
            # 显示简历列表供选择
            self.console.print("\n[bold]选择要删除的简历:[/bold]")
            for i, resume in enumerate(resumes, 1):
                self.console.print(f"{i}. {resume.filename} ({resume.file_type})")
            
            # 获取用户选择
            from rich.prompt import IntPrompt
            try:
                choice = IntPrompt.ask(
                    "输入简历序号",
                    default=1,
                    choices=[str(i) for i in range(1, len(resumes) + 1)]
                )
                
                selected_resume = resumes[choice - 1]
                
                # 确认删除
                from rich.prompt import Confirm
                if Confirm.ask(f"确定要删除 '{selected_resume.filename}' 吗？"):
                    if self.resume_processor.delete_resume(selected_resume.id):
                        self.console.print(f"[green]✅ 已删除: {selected_resume.filename}[/green]")
                        self.logger.info(f"简历删除成功: {selected_resume.filename}")
                    else:
                        self.console.print("[red]❌ 删除失败[/red]")
                        
            except (KeyboardInterrupt, EOFError):
                self.console.print("[yellow]取消删除操作[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]删除操作失败: {e}[/red]")
            self.logger.error(f"简历删除失败: {e}")
    
    def _handle_resume_view(self):
        """处理简历查看"""
        try:
            resumes = self.resume_processor.list_resumes()
            if not resumes:
                self.console.print("[yellow]没有可查看的简历[/yellow]")
                return
            
            # 显示简历列表供选择
            self.console.print("\n[bold]选择要查看的简历:[/bold]")
            for i, resume in enumerate(resumes, 1):
                self.console.print(f"{i}. {resume.filename} ({resume.file_type})")
            
            # 获取用户选择
            from rich.prompt import IntPrompt
            try:
                choice = IntPrompt.ask(
                    "输入简历序号",
                    default=1,
                    choices=[str(i) for i in range(1, len(resumes) + 1)]
                )
                
                selected_resume = resumes[choice - 1]
                
                # 创建详情面板
                detail_panel = ComponentFactory.create_resume_detail_panel()
                resume_data = {
                    'id': selected_resume.id,
                    'filename': selected_resume.filename,
                    'file_type': selected_resume.file_type,
                    'file_size': selected_resume.file_size,
                    'created_at': selected_resume.created_at,
                    'updated_at': selected_resume.updated_at,
                    'metadata': selected_resume.metadata
                }
                detail_panel.set_resume_data(resume_data)
                
                # 显示详情
                self.console.print(detail_panel.render())
                
                # 显示内容预览（前500字符）
                if selected_resume.content:
                    preview = selected_resume.content[:500]
                    if len(selected_resume.content) > 500:
                        preview += "..."
                    
                    content_panel = InfoPanel("内容预览", "blue")
                    content_panel.add_line(preview, "white")
                    self.console.print(content_panel.render())
                
                # 等待用户按键继续
                input("\n按回车键继续...")
                
            except (KeyboardInterrupt, EOFError):
                self.console.print("[yellow]取消查看操作[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]查看操作失败: {e}[/red]")
            self.logger.error(f"简历查看失败: {e}")
    
    def _handle_ai_analysis_start(self):
        """处理开始AI分析"""
        try:
            # 获取简历和职位数据
            resumes = self.resume_processor.list_resumes()
            jobs = self.job_manager.list_jobs()
            
            # 创建AI分析对话框
            analysis_dialog = ComponentFactory.create_ai_analysis_dialog()
            
            # 显示选择对话框
            selection = analysis_dialog.show_analysis_selection(resumes, jobs)
            if not selection:
                return
            
            selected_resume, selected_job = selection
            
            # 显示分析进度
            analysis_dialog.show_analysis_progress(selected_resume.filename, selected_job.title)
            
            try:
                # 转换职位信息格式
                from ..core.ai_analyzer import JobInfo
                job_info = JobInfo(
                    id=selected_job.id,
                    title=selected_job.title,
                    company=selected_job.company,
                    description=selected_job.description,
                    requirements=selected_job.requirements,
                    location=selected_job.location,
                    salary=selected_job.salary,
                    experience_level=selected_job.experience_level
                )
                
                # 进行AI分析
                result = self.ai_analyzer.analyze_resume_job_match(
                    selected_resume.content,
                    selected_resume.id,
                    job_info
                )
                
                # 显示分析结果
                result_data = {
                    'match_scores': result.match_scores,
                    'overall_score': result.overall_score,
                    'suggestions': result.suggestions,
                    'matching_skills': result.matching_skills,
                    'missing_skills': result.missing_skills,
                    'strengths': result.strengths,
                    'weaknesses': result.weaknesses
                }
                analysis_dialog.show_analysis_result(result_data)
                
                self.logger.info(f"AI分析完成: {selected_resume.filename} vs {selected_job.title}")
                
                # 等待用户按键继续
                input("\n按回车键继续...")
                
            except Exception as e:
                # 显示错误消息
                analysis_dialog.show_error_message(str(e))
                self.logger.error(f"AI分析失败: {e}")
                
        except Exception as e:
            self.logger.error(f"分析对话框错误: {e}")
            self.console.print(f"[red]分析功能暂时不可用: {e}[/red]")
    
    def _handle_analysis_view(self):
        """处理查看分析详情"""
        try:
            analyses = self.ai_analyzer.list_analysis()
            if not analyses:
                self.console.print("[yellow]没有可查看的分析记录[/yellow]")
                return
            
            # 显示分析列表供选择
            self.console.print("\n[bold]选择要查看的分析记录:[/bold]")
            for i, analysis in enumerate(analyses, 1):
                # 获取职位名称
                job = self.job_manager.get_job(analysis.job_id)
                job_title = job.title if job else "未知职位"
                
                time_str = analysis.created_at.strftime('%m-%d %H:%M')
                self.console.print(f"{i}. {job_title} - {analysis.overall_score:.1f}% ({time_str})")
            
            # 获取用户选择
            from rich.prompt import IntPrompt
            try:
                choice = IntPrompt.ask(
                    "输入分析记录序号",
                    default=1,
                    choices=[str(i) for i in range(1, len(analyses) + 1)]
                )
                
                selected_analysis = analyses[choice - 1]
                
                # 创建详情面板
                detail_panel = ComponentFactory.create_analysis_detail_panel()
                analysis_data = {
                    'match_scores': selected_analysis.match_scores,
                    'overall_score': selected_analysis.overall_score,
                    'suggestions': selected_analysis.suggestions,
                    'matching_skills': selected_analysis.matching_skills,
                    'missing_skills': selected_analysis.missing_skills,
                    'strengths': selected_analysis.strengths,
                    'weaknesses': selected_analysis.weaknesses
                }
                detail_panel.set_analysis_data(analysis_data)
                
                # 显示详情
                self.console.print(detail_panel.render())
                
                # 显示建议和技能对比
                if selected_analysis.suggestions:
                    suggestion_panel = InfoPanel("优化建议", "yellow")
                    suggestion_panel.add_header("AI建议")
                    for i, suggestion in enumerate(selected_analysis.suggestions, 1):
                        suggestion_panel.add_line(f"{i}. {suggestion}", "white")
                    self.console.print(suggestion_panel.render())
                
                # 等待用户按键继续
                input("\n按回车键继续...")
                
            except (KeyboardInterrupt, EOFError):
                self.console.print("[yellow]取消查看操作[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]查看操作失败: {e}[/red]")
            self.logger.error(f"分析查看失败: {e}")
    
    def _handle_analysis_delete(self):
        """处理删除分析记录"""
        try:
            analyses = self.ai_analyzer.list_analysis()
            if not analyses:
                self.console.print("[yellow]没有可删除的分析记录[/yellow]")
                return
            
            # 显示分析列表供选择
            self.console.print("\n[bold]选择要删除的分析记录:[/bold]")
            for i, analysis in enumerate(analyses, 1):
                # 获取职位名称
                job = self.job_manager.get_job(analysis.job_id)
                job_title = job.title if job else "未知职位"
                
                time_str = analysis.created_at.strftime('%m-%d %H:%M')
                self.console.print(f"{i}. {job_title} - {analysis.overall_score:.1f}% ({time_str})")
            
            # 获取用户选择
            from rich.prompt import IntPrompt
            try:
                choice = IntPrompt.ask(
                    "输入分析记录序号",
                    default=1,
                    choices=[str(i) for i in range(1, len(analyses) + 1)]
                )
                
                selected_analysis = analyses[choice - 1]
                
                # 获取职位名称用于确认
                job = self.job_manager.get_job(selected_analysis.job_id)
                job_title = job.title if job else "未知职位"
                
                # 确认删除
                from rich.prompt import Confirm
                if Confirm.ask(f"确定要删除关于 '{job_title}' 的分析记录吗？"):
                    if self.ai_analyzer.delete_analysis(selected_analysis.id):
                        self.console.print(f"[green]✅ 已删除分析记录[/green]")
                        self.logger.info(f"分析记录删除成功: {selected_analysis.id}")
                    else:
                        self.console.print("[red]❌ 删除失败[/red]")
                        
            except (KeyboardInterrupt, EOFError):
                self.console.print("[yellow]取消删除操作[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]删除操作失败: {e}[/red]")
            self.logger.error(f"分析删除失败: {e}")


if __name__ == "__main__":
    app = ResumeAssistantApp()
    app.run()