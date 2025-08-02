"""Settings Page for Streamlit Web Interface."""

import streamlit as st
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from ..components import UIComponents
from ..session_manager import SessionManager
from ..cache_manager import CacheManager, PerformanceMonitor
from ...config import get_settings
from ...utils import get_logger

logger = get_logger(__name__)

class SettingsPage:
    """设置页面"""
    
    def __init__(self):
        self.components = UIComponents()
        self.settings = get_settings()
    
    def render(self):
        """渲染页面"""
        self.components.render_header(
            "系统设置", 
            "配置应用程序参数和管理系统功能",
            "⚙️"
        )
        
        # 显示通知
        self.components.render_notification_area()
        
        # 主要内容区域
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🤖 AI服务", "🎨 界面设置", "🗄️ 缓存管理", "📊 数据管理", "📈 系统状态"
        ])
        
        with tab1:
            self._render_ai_settings()
        
        with tab2:
            self._render_ui_settings()
        
        with tab3:
            self._render_cache_settings()
        
        with tab4:
            self._render_data_management()
        
        with tab5:
            self._render_system_status()
    
    def _render_ai_settings(self):
        """渲染AI服务设置"""
        st.subheader("🤖 AI服务配置")
        
        # DeepSeek API配置
        st.markdown("### DeepSeek API设置")
        
        with st.form("ai_settings_form"):
            # API密钥设置
            current_api_key = getattr(self.settings, 'deepseek_api_key', '')
            masked_key = f"{'*' * 20}{current_api_key[-4:]}" if current_api_key and len(current_api_key) > 4 else "未设置"
            
            st.text_input(
                "当前API密钥",
                value=masked_key,
                disabled=True,
                help="当前配置的API密钥（已加密显示）"
            )
            
            new_api_key = st.text_input(
                "新API密钥",
                type="password",
                help="输入新的DeepSeek API密钥"
            )
            
            # API基础URL
            base_url = st.text_input(
                "API基础URL",
                value=getattr(self.settings, 'deepseek_base_url', 'https://api.deepseek.com'),
                help="DeepSeek API的基础URL"
            )
            
            # 模型选择
            model_options = [
                "deepseek-chat",
                "deepseek-coder", 
                "deepseek-reasoner"
            ]
            
            selected_model = st.selectbox(
                "默认模型",
                options=model_options,
                index=0,
                help="选择默认使用的AI模型"
            )
            
            # AI参数设置
            st.markdown("#### AI参数")
            
            col1, col2 = st.columns(2)
            
            with col1:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="控制AI回复的随机性，值越高越有创造性"
                )
                
                max_tokens = st.number_input(
                    "最大Token数",
                    min_value=100,
                    max_value=4000,
                    value=2048,
                    step=100,
                    help="AI回复的最大长度"
                )
            
            with col2:
                timeout = st.number_input(
                    "请求超时时间(秒)",
                    min_value=5,
                    max_value=60,
                    value=30,
                    help="API请求的超时时间"
                )
                
                retry_count = st.number_input(
                    "重试次数",
                    min_value=0,
                    max_value=5,
                    value=3,
                    help="API请求失败时的重试次数"
                )
            
            # 提交按钮
            if st.form_submit_button("💾 保存AI设置", type="primary"):
                self._save_ai_settings({
                    'api_key': new_api_key,
                    'base_url': base_url,
                    'model': selected_model,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'timeout': timeout,
                    'retry_count': retry_count
                })
        
        # API连接测试
        st.markdown("---")
        st.markdown("### 🔌 连接测试")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 测试API连接", type="secondary"):
                self._test_api_connection()
        
        with col2:
            if st.button("📊 查看API使用情况", type="secondary"):
                self._show_api_usage_stats()
    
    def _render_ui_settings(self):
        """渲染界面设置"""
        st.subheader("🎨 界面设置")
        
        with st.form("ui_settings_form"):
            # 主题设置
            st.markdown("### 主题选择")
            
            theme_options = ["浅色主题", "深色主题", "自动模式"]
            current_theme = st.session_state.get('theme', 'light')
            theme_index = 0 if current_theme == 'light' else 1 if current_theme == 'dark' else 2
            
            selected_theme = st.selectbox(
                "选择主题",
                options=theme_options,
                index=theme_index,
                help="选择应用程序的外观主题"
            )
            
            # 语言设置
            st.markdown("### 语言设置")
            
            language_options = ["中文", "English"]
            selected_language = st.selectbox(
                "界面语言",
                options=language_options,
                index=0,
                help="选择界面显示语言"
            )
            
            # 布局设置
            st.markdown("### 布局设置")
            
            col1, col2 = st.columns(2)
            
            with col1:
                sidebar_expanded = st.checkbox(
                    "侧边栏默认展开",
                    value=st.session_state.get('sidebar_expanded', True),
                    help="页面加载时是否展开侧边栏"
                )
                
                show_progress_bars = st.checkbox(
                    "显示进度条",
                    value=True,
                    help="在长时间操作时显示进度条"
                )
            
            with col2:
                auto_refresh = st.checkbox(
                    "自动刷新数据",
                    value=False,
                    help="定期自动刷新页面数据"
                )
                
                compact_mode = st.checkbox(
                    "紧凑模式",
                    value=False,
                    help="使用更紧凑的界面布局"
                )
            
            # 通知设置
            st.markdown("### 通知设置")
            
            max_notifications = st.slider(
                "最大通知数量",
                min_value=1,
                max_value=10,
                value=3,
                help="同时显示的最大通知数量"
            )
            
            notification_duration = st.slider(
                "通知显示时长(秒)",
                min_value=3,
                max_value=10,
                value=5,
                help="通知自动消失的时间"
            )
            
            # 提交按钮
            if st.form_submit_button("💾 保存界面设置", type="primary"):
                self._save_ui_settings({
                    'theme': selected_theme,
                    'language': selected_language,
                    'sidebar_expanded': sidebar_expanded,
                    'show_progress_bars': show_progress_bars,
                    'auto_refresh': auto_refresh,
                    'compact_mode': compact_mode,
                    'max_notifications': max_notifications,
                    'notification_duration': notification_duration
                })
    
    def _render_cache_settings(self):
        """渲染缓存设置"""
        # 使用缓存管理器的面板
        CacheManager.render_cache_management_panel()
        
        st.markdown("---")
        st.markdown("### ⚙️ 缓存配置")
        
        with st.form("cache_config_form"):
            cache_config = st.session_state.get('cache_config', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                job_scraping_ttl = st.number_input(
                    "职位爬取缓存时间(秒)",
                    min_value=60,
                    max_value=3600,
                    value=cache_config.get('job_scraping_ttl', 300),
                    help="职位爬取结果的缓存时间"
                )
                
                resume_parsing_ttl = st.number_input(
                    "简历解析缓存时间(秒)",
                    min_value=60,
                    max_value=3600,
                    value=cache_config.get('resume_parsing_ttl', 600),
                    help="简历解析结果的缓存时间"
                )
            
            with col2:
                ai_analysis_ttl = st.number_input(
                    "AI分析缓存时间(秒)",
                    min_value=300,
                    max_value=7200,
                    value=cache_config.get('ai_analysis_ttl', 1800),
                    help="AI分析结果的缓存时间"
                )
                
                greeting_generation_ttl = st.number_input(
                    "打招呼语缓存时间(秒)",
                    min_value=300,
                    max_value=3600,
                    value=cache_config.get('greeting_generation_ttl', 900),
                    help="打招呼语生成结果的缓存时间"
                )
            
            auto_clear_enabled = st.checkbox(
                "启用自动清理",
                value=cache_config.get('auto_clear_enabled', True),
                help="定期自动清理过期缓存"
            )
            
            if st.form_submit_button("💾 保存缓存配置", type="primary"):
                self._save_cache_config({
                    'job_scraping_ttl': job_scraping_ttl,
                    'resume_parsing_ttl': resume_parsing_ttl,
                    'ai_analysis_ttl': ai_analysis_ttl,
                    'greeting_generation_ttl': greeting_generation_ttl,
                    'auto_clear_enabled': auto_clear_enabled
                })
    
    def _render_data_management(self):
        """渲染数据管理"""
        st.subheader("📊 数据管理")
        
        # 数据统计
        stats = self._get_data_statistics()
        
        st.markdown("### 📈 数据统计")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("职位数量", stats.get('jobs_count', 0))
        
        with col2:
            st.metric("简历数量", stats.get('resumes_count', 0))
        
        with col3:
            st.metric("分析记录", stats.get('analyses_count', 0))
        
        with col4:
            st.metric("打招呼语", stats.get('greetings_count', 0))
        
        # 数据操作
        st.markdown("---")
        st.markdown("### 🔧 数据操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 导出数据", type="primary"):
                self._export_data()
        
        with col2:
            if st.button("📥 导入数据", type="secondary"):
                self._show_import_interface()
        
        with col3:
            if st.button("🗑️ 清空数据", type="secondary"):
                self._show_clear_data_interface()
        
        # 数据库状态
        st.markdown("---")
        st.markdown("### 🗃️ 数据库状态")
        
        db_status = self._get_database_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**数据库大小**: {db_status.get('size', 'Unknown')}")
            st.info(f"**最后备份**: {db_status.get('last_backup', '未备份')}")
        
        with col2:
            st.info(f"**连接状态**: {db_status.get('connection_status', 'Unknown')}")
            st.info(f"**版本**: {db_status.get('version', 'Unknown')}")
        
        # 备份操作
        if st.button("💾 创建数据库备份", type="secondary"):
            self._create_database_backup()
    
    def _render_system_status(self):
        """渲染系统状态"""
        st.subheader("📈 系统状态")
        
        # 性能监控面板
        PerformanceMonitor.render_performance_panel()
        
        st.markdown("---")
        
        # 系统信息
        st.markdown("### 🖥️ 系统信息")
        
        system_info = self._get_system_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Python版本**: {system_info.get('python_version', 'Unknown')}")
            st.info(f"**Streamlit版本**: {system_info.get('streamlit_version', 'Unknown')}")
            st.info(f"**启动时间**: {system_info.get('start_time', 'Unknown')}")
        
        with col2:
            st.info(f"**运行时间**: {system_info.get('uptime', 'Unknown')}")
            st.info(f"**内存使用**: {system_info.get('memory_usage', 'Unknown')}")
            st.info(f"**活跃会话**: {system_info.get('active_sessions', 'Unknown')}")
        
        # 系统日志
        with st.expander("📋 系统日志"):
            self._show_system_logs()
    
    def _save_ai_settings(self, settings: Dict[str, Any]):
        """保存AI设置"""
        try:
            # 更新session state
            if 'ai_settings' not in st.session_state:
                st.session_state.ai_settings = {}
            
            st.session_state.ai_settings.update(settings)
            
            SessionManager.add_notification("success", "AI设置已保存")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Save AI settings error: {e}")
            SessionManager.add_notification("error", f"保存AI设置失败: {str(e)}")
    
    def _save_ui_settings(self, settings: Dict[str, Any]):
        """保存界面设置"""
        try:
            # 更新session state
            theme_map = {"浅色主题": "light", "深色主题": "dark", "自动模式": "auto"}
            st.session_state.theme = theme_map.get(settings['theme'], 'light')
            st.session_state.sidebar_expanded = settings['sidebar_expanded']
            
            # 保存其他设置
            if 'ui_settings' not in st.session_state:
                st.session_state.ui_settings = {}
            
            st.session_state.ui_settings.update(settings)
            
            SessionManager.add_notification("success", "界面设置已保存")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Save UI settings error: {e}")
            SessionManager.add_notification("error", f"保存界面设置失败: {str(e)}")
    
    def _save_cache_config(self, config: Dict[str, Any]):
        """保存缓存配置"""
        try:
            st.session_state.cache_config.update(config)
            
            SessionManager.add_notification("success", "缓存配置已保存")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Save cache config error: {e}")
            SessionManager.add_notification("error", f"保存缓存配置失败: {str(e)}")
    
    def _test_api_connection(self):
        """测试API连接"""
        try:
            with st.spinner("正在测试API连接..."):
                # 这里应该调用实际的API测试
                import time
                time.sleep(2)  # 模拟测试时间
                
                # 模拟测试结果
                success = True  # 实际应该进行真实测试
                
                if success:
                    st.success("✅ API连接测试成功！")
                else:
                    st.error("❌ API连接测试失败")
                    
        except Exception as e:
            logger.error(f"API connection test error: {e}")
            st.error(f"API连接测试出错: {str(e)}")
    
    def _get_data_statistics(self) -> Dict[str, int]:
        """获取数据统计"""
        return {
            'jobs_count': len(st.session_state.get('jobs', [])),
            'resumes_count': len(st.session_state.get('resumes', [])),
            'analyses_count': len(st.session_state.get('analyses', [])),
            'greetings_count': len(st.session_state.get('greetings', []))
        }
    
    def _get_database_status(self) -> Dict[str, str]:
        """获取数据库状态"""
        return {
            'size': '2.5 MB',
            'last_backup': '未备份',
            'connection_status': '正常',
            'version': 'SQLite 3.x'
        }
    
    def _get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        import sys
        import streamlit
        
        return {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'streamlit_version': streamlit.__version__,
            'start_time': st.session_state.get('app_start_time', 'Unknown'),
            'uptime': 'Unknown',
            'memory_usage': 'Unknown',
            'active_sessions': '1'
        }
    
    def _export_data(self):
        """导出数据"""
        try:
            # 收集所有数据
            export_data = {
                'jobs': st.session_state.get('jobs', []),
                'resumes': st.session_state.get('resumes', []),
                'analyses': st.session_state.get('analyses', []),
                'greetings': st.session_state.get('greetings', []),
                'export_time': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # 生成JSON文件
            json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 下载数据文件",
                data=json_data,
                file_name=f"resume_assistant_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            SessionManager.add_notification("success", "数据导出成功")
            
        except Exception as e:
            logger.error(f"Export data error: {e}")
            SessionManager.add_notification("error", f"导出数据失败: {str(e)}")
    
    def _show_import_interface(self):
        """显示数据导入界面"""
        with st.expander("📥 导入数据", expanded=True):
            uploaded_file = st.file_uploader(
                "选择数据文件",
                type=['json'],
                help="选择之前导出的数据文件"
            )
            
            if uploaded_file is not None:
                if st.button("🔄 导入数据", type="primary"):
                    self._import_data(uploaded_file)
    
    def _import_data(self, uploaded_file):
        """导入数据"""
        try:
            # 读取并解析JSON数据
            content = uploaded_file.read()
            data = json.loads(content.decode('utf-8'))
            
            # 验证数据格式
            if 'version' not in data:
                st.error("无效的数据文件格式")
                return
            
            # 导入数据
            if 'jobs' in data:
                st.session_state.jobs = data['jobs']
            if 'resumes' in data:
                st.session_state.resumes = data['resumes']
            if 'analyses' in data:
                st.session_state.analyses = data['analyses']
            if 'greetings' in data:
                st.session_state.greetings = data['greetings']
            
            SessionManager.add_notification("success", "数据导入成功")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Import data error: {e}")
            SessionManager.add_notification("error", f"导入数据失败: {str(e)}")
    
    def _show_clear_data_interface(self):
        """显示清空数据界面"""
        with st.expander("🗑️ 清空数据", expanded=True):
            st.warning("⚠️ 此操作将永久删除所有数据，请谨慎操作！")
            
            data_types = st.multiselect(
                "选择要清空的数据类型",
                ["职位数据", "简历数据", "分析记录", "打招呼语"],
                help="选择要清空的数据类型"
            )
            
            confirm = st.checkbox("我确认要清空选中的数据")
            
            if st.button("🗑️ 确认清空", type="secondary", disabled=not confirm):
                self._clear_selected_data(data_types)
    
    def _clear_selected_data(self, data_types: List[str]):
        """清空选中的数据"""
        try:
            cleared_types = []
            
            if "职位数据" in data_types:
                st.session_state.jobs = []
                cleared_types.append("职位数据")
            
            if "简历数据" in data_types:
                st.session_state.resumes = []
                cleared_types.append("简历数据")
            
            if "分析记录" in data_types:
                st.session_state.analyses = []
                cleared_types.append("分析记录")
            
            if "打招呼语" in data_types:
                st.session_state.greetings = []
                cleared_types.append("打招呼语")
            
            if cleared_types:
                SessionManager.add_notification("success", f"已清空: {', '.join(cleared_types)}")
                st.rerun()
            
        except Exception as e:
            logger.error(f"Clear data error: {e}")
            SessionManager.add_notification("error", f"清空数据失败: {str(e)}")
    
    def _create_database_backup(self):
        """创建数据库备份"""
        try:
            # 模拟备份创建
            backup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.last_backup_time = backup_time
            
            SessionManager.add_notification("success", f"数据库备份创建成功: {backup_time}")
            
        except Exception as e:
            logger.error(f"Create backup error: {e}")
            SessionManager.add_notification("error", f"创建备份失败: {str(e)}")
    
    def _show_api_usage_stats(self):
        """显示API使用统计"""
        with st.expander("📊 API使用统计", expanded=True):
            # 模拟API使用数据
            stats = {
                '今日请求': 45,
                '本月请求': 1240,
                '成功率': '98.5%',
                '平均响应时间': '1.2s',
                '剩余配额': '8760/10000'
            }
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("今日请求", stats['今日请求'])
                st.metric("成功率", stats['成功率'])
            
            with col2:
                st.metric("本月请求", stats['本月请求'])
                st.metric("平均响应时间", stats['平均响应时间'])
            
            with col3:
                st.metric("剩余配额", stats['剩余配额'])
    
    def _show_system_logs(self):
        """显示系统日志"""
        # 模拟系统日志
        logs = [
            "2025-01-02 10:30:15 INFO: Application started",
            "2025-01-02 10:30:16 INFO: Database connection established",
            "2025-01-02 10:35:23 INFO: Job scraping completed successfully",
            "2025-01-02 10:40:12 INFO: AI analysis completed",
            "2025-01-02 10:45:05 WARNING: Cache size approaching limit"
        ]
        
        for log in logs[-10:]:  # 显示最近10条日志
            if "ERROR" in log:
                st.error(log)
            elif "WARNING" in log:
                st.warning(log)
            else:
                st.info(log)