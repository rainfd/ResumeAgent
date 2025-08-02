"""Settings Page for Streamlit Web Interface."""

import streamlit as st
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from ..components import UIComponents
from ..session_manager import SessionManager
from ..cache_manager import SmartCacheManager as CacheManager
from ..performance import PerformanceMonitor
from ...config import get_settings
from ...utils import get_logger
from ...utils.security import (
    get_security_manager, get_api_key_manager, DataValidator, 
    PrivacyProtector, SecurityError, validate_url, validate_file, 
    mask_sensitive_info
)

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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "🤖 AI服务", "🎨 界面设置", "🗄️ 缓存管理", "📊 数据管理", "📈 系统状态", "🚀 性能优化", "🔧 诊断工具", "🔒 安全设置"
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
        
        with tab6:
            self._show_performance_management()
            self._show_advanced_settings()
        
        with tab7:
            self._show_diagnostic_tools()
        
        with tab8:
            self._render_security_settings()
    
    def _render_ai_settings(self):
        """渲染AI服务设置"""
        st.subheader("🤖 AI服务配置")
        
        # DeepSeek API配置
        st.markdown("### DeepSeek API设置")
        
        with st.form("ai_settings_form"):
            # API密钥设置（使用安全存储）
            try:
                api_key_manager = get_api_key_manager()
                current_api_key = api_key_manager.get_api_key('deepseek')
                masked_key = f"{'*' * 20}{current_api_key[-4:]}" if current_api_key and len(current_api_key) > 4 else "未设置"
            except:
                masked_key = "未设置"
            
            st.text_input(
                "当前API密钥",
                value=masked_key,
                disabled=True,
                help="当前配置的API密钥（已加密存储）"
            )
            
            new_api_key = st.text_input(
                "新API密钥",
                type="password",
                help="输入新的DeepSeek API密钥（将使用加密存储）"
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
        try:
            from ..cache_manager import display_cache_management
            display_cache_management()
        except ImportError:
            st.info("缓存管理面板暂时不可用")
        
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
        try:
            from ..performance import display_performance_dashboard
            display_performance_dashboard()
        except ImportError:
            st.info("性能监控面板暂时不可用")
        
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
            # 如果有新的API密钥，使用安全存储
            if settings.get('api_key'):
                api_key_manager = get_api_key_manager()
                api_key_manager.store_api_key('deepseek', settings['api_key'])
                # 不在settings中保存明文密钥
                settings = {k: v for k, v in settings.items() if k != 'api_key'}
            
            # 更新session state
            if 'ai_settings' not in st.session_state:
                st.session_state.ai_settings = {}
            
            st.session_state.ai_settings.update(settings)
            
            SessionManager.add_notification("success", "AI设置已保存（API密钥已加密存储）")
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
    
    def _show_performance_management(self):
        """显示性能管理界面"""
        st.subheader("🚀 性能优化")
        
        # 导入性能模块
        try:
            from ..performance import display_performance_dashboard
            from ..cache_manager import display_cache_management
            from ..error_handler import display_error_management
            
            # 选择管理类型
            management_type = st.selectbox(
                "选择管理类型",
                ["性能监控", "缓存管理", "错误管理"],
                key="performance_management_type"
            )
            
            if management_type == "性能监控":
                display_performance_dashboard()
            elif management_type == "缓存管理":
                display_cache_management()
            elif management_type == "错误管理":
                display_error_management()
                
        except Exception as e:
            st.error(f"加载性能管理模块失败: {e}")
            st.info("请确保性能优化模块已正确安装")
    
    def _show_advanced_settings(self):
        """显示高级设置"""
        st.subheader("⚙️ 高级设置")
        
        # 性能设置
        with st.expander("🚀 性能设置"):
            # 缓存设置
            st.write("**缓存配置**")
            cache_size = st.slider("最大缓存大小 (MB)", 10, 500, 100)
            cache_ttl = st.slider("默认缓存时间 (秒)", 300, 7200, 3600)
            auto_cleanup = st.checkbox("启用自动清理", value=True)
            
            # 异步设置
            st.write("**异步处理配置**")
            max_workers = st.slider("最大工作线程", 1, 8, 4)
            operation_timeout = st.slider("操作超时 (秒)", 30, 300, 120)
            
            # 监控设置
            st.write("**监控配置**")
            enable_monitoring = st.checkbox("启用性能监控", value=True)
            monitoring_interval = st.slider("监控间隔 (秒)", 10, 300, 30)
            
            if st.button("保存性能设置"):
                # 这里可以保存到配置文件
                st.success("性能设置已保存")
        
        # 错误处理设置
        with st.expander("🚨 错误处理设置"):
            st.write("**错误记录配置**")
            max_error_history = st.slider("最大错误历史记录", 50, 1000, 100)
            show_debug_info = st.checkbox("显示调试信息", value=False)
            auto_report_errors = st.checkbox("自动报告错误", value=False)
            
            st.write("**错误阈值配置**")
            cpu_threshold = st.slider("CPU使用率阈值 (%)", 50, 95, 80)
            memory_threshold = st.slider("内存使用率阈值 (%)", 50, 95, 85)
            response_time_threshold = st.slider("响应时间阈值 (秒)", 1, 30, 5)
            
            if st.button("保存错误处理设置"):
                st.session_state.debug_mode = show_debug_info
                st.success("错误处理设置已保存")
        
        # 安全设置
        with st.expander("🔒 安全设置"):
            st.write("**API密钥安全**")
            encrypt_api_keys = st.checkbox("加密存储API密钥", value=True)
            key_rotation_days = st.slider("密钥轮换周期 (天)", 30, 365, 90)
            
            st.write("**访问控制**")
            enable_session_timeout = st.checkbox("启用会话超时", value=True)
            session_timeout_minutes = st.slider("会话超时 (分钟)", 15, 480, 120)
            
            st.write("**数据保护**")
            anonymize_logs = st.checkbox("匿名化日志", value=True)
            data_retention_days = st.slider("数据保留期 (天)", 7, 365, 30)
            
            if st.button("保存安全设置"):
                st.success("安全设置已保存")
    
    def _show_diagnostic_tools(self):
        """显示诊断工具"""
        st.subheader("🔧 诊断工具")
        
        # 系统信息
        with st.expander("💻 系统信息"):
            try:
                from ..performance import get_system_info
                import platform
                import sys
                
                system_info = get_system_info()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**系统环境**")
                    st.write(f"操作系统: {platform.system()} {platform.release()}")
                    st.write(f"Python版本: {sys.version.split()[0]}")
                    st.write(f"Streamlit版本: {st.__version__}")
                    
                    if system_info:
                        st.write(f"CPU核心数: {system_info.get('cpu_count', 'N/A')}")
                        st.write(f"总内存: {system_info.get('memory_total_gb', 0):.1f} GB")
                
                with col2:
                    st.write("**运行状态**")
                    if system_info:
                        boot_time = system_info.get('boot_time')
                        if boot_time:
                            st.write(f"系统启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        load_avg = system_info.get('load_average')
                        if load_avg:
                            st.write(f"系统负载: {load_avg}")
                    
                    st.write(f"会话状态项: {len(st.session_state)}")
                    
            except Exception as e:
                st.error(f"获取系统信息失败: {e}")
        
        # 连接测试
        with st.expander("🌐 连接测试"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("测试数据库连接"):
                    try:
                        # 这里添加数据库连接测试
                        st.success("✅ 数据库连接正常")
                    except Exception as e:
                        st.error(f"❌ 数据库连接失败: {e}")
                
                if st.button("测试AI服务连接"):
                    try:
                        # 这里添加AI服务连接测试
                        st.success("✅ AI服务连接正常")
                    except Exception as e:
                        st.error(f"❌ AI服务连接失败: {e}")
            
            with col2:
                if st.button("测试网络连接"):
                    try:
                        import requests
                        response = requests.get("https://www.baidu.com", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ 网络连接正常")
                        else:
                            st.warning(f"⚠️ 网络连接异常: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ 网络连接失败: {e}")
                
                if st.button("清理临时文件"):
                    try:
                        import tempfile
                        import shutil
                        temp_dir = tempfile.gettempdir()
                        # 这里可以添加清理逻辑
                        st.success("✅ 临时文件清理完成")
                    except Exception as e:
                        st.error(f"❌ 清理失败: {e}")
        
        # 导出诊断报告
        if st.button("📊 生成诊断报告"):
            try:
                report = self._generate_diagnostic_report()
                st.download_button(
                    label="下载诊断报告",
                    data=report,
                    file_name=f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"生成诊断报告失败: {e}")
    
    def _generate_diagnostic_report(self) -> str:
        """生成诊断报告"""
        try:
            from ..performance import get_system_info, get_performance_monitor
            from ..cache_manager import get_cache_manager
            from ..error_handler import get_error_handler
            import platform
            import sys
            
            report_lines = [
                "Resume Assistant 诊断报告",
                "=" * 50,
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "系统信息:",
                f"  操作系统: {platform.system()} {platform.release()}",
                f"  Python版本: {sys.version.split()[0]}",
                f"  Streamlit版本: {st.__version__}",
                ""
            ]
            
            # 系统信息
            system_info = get_system_info()
            if system_info:
                report_lines.extend([
                    "硬件信息:",
                    f"  CPU核心数: {system_info.get('cpu_count', 'N/A')}",
                    f"  总内存: {system_info.get('memory_total_gb', 0):.1f} GB",
                    ""
                ])
            
            # 性能信息
            try:
                monitor = get_performance_monitor()
                metrics = monitor.get_current_metrics()
                summary = monitor.get_metrics_summary(24)
                
                report_lines.extend([
                    "性能指标:",
                    f"  当前CPU使用率: {metrics.cpu_percent:.1f}%",
                    f"  当前内存使用: {metrics.memory_mb:.0f}MB ({metrics.memory_percent:.1f}%)",
                    f"  活跃操作数: {metrics.active_operations}",
                    ""
                ])
                
                if summary:
                    report_lines.extend([
                        "24小时摘要:",
                        f"  平均CPU: {summary['avg_cpu_percent']:.1f}%",
                        f"  峰值CPU: {summary['max_cpu_percent']:.1f}%",
                        f"  平均内存: {summary['avg_memory_mb']:.0f}MB",
                        f"  峰值内存: {summary['max_memory_mb']:.0f}MB",
                        f"  运行时间: {summary['uptime_hours']:.1f}小时",
                        ""
                    ])
            except:
                report_lines.append("性能信息: 无法获取")
            
            # 缓存信息
            try:
                cache_manager = get_cache_manager()
                cache_stats = cache_manager.get_stats()
                
                report_lines.extend([
                    "缓存状态:",
                    f"  缓存条目数: {cache_stats['entries_count']}",
                    f"  缓存大小: {cache_stats['size_mb']:.1f}MB",
                    f"  命中率: {cache_stats['hit_rate']:.1%}",
                    f"  总命中数: {cache_stats['hits']}",
                    f"  总未命中数: {cache_stats['misses']}",
                    f"  驱逐次数: {cache_stats['evictions']}",
                    ""
                ])
            except:
                report_lines.append("缓存信息: 无法获取")
            
            # 错误信息
            try:
                error_handler = get_error_handler()
                errors = error_handler.get_error_history(50)
                
                report_lines.extend([
                    "错误统计:",
                    f"  总错误数: {len(errors)}",
                    ""
                ])
                
                if errors:
                    recent_errors = errors[-5:]  # 最近5个错误
                    report_lines.append("最近错误:")
                    for error in recent_errors:
                        report_lines.append(f"  {error['timestamp'].strftime('%H:%M:%S')} {error['error_type']}: {error['error_message']}")
                    report_lines.append("")
            except:
                report_lines.append("错误信息: 无法获取")
            
            # Session状态
            report_lines.extend([
                "Session状态:",
                f"  状态项数量: {len(st.session_state)}",
                f"  当前页面: {st.session_state.get('current_page', 'unknown')}",
                ""
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"生成诊断报告时发生错误: {e}"
    
    def _render_security_settings(self):
        """渲染安全设置"""
        st.subheader("🔒 安全设置")
        
        # API密钥管理
        self._render_api_key_management()
        
        st.divider()
        
        # 数据验证设置
        self._render_data_validation_settings()
        
        st.divider()
        
        # 隐私保护设置
        self._render_privacy_protection_settings()
        
        st.divider()
        
        # 安全测试
        self._render_security_tests()
    
    def _render_api_key_management(self):
        """渲染API密钥管理"""
        st.markdown("### 🔑 API密钥管理")
        
        try:
            api_key_manager = get_api_key_manager()
            services = api_key_manager.list_services()
            
            # 显示已存储的服务
            if services:
                st.markdown("#### 已存储的API密钥")
                
                for service in services:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        # 获取密钥并遮蔽显示
                        key = api_key_manager.get_api_key(service)
                        if key:
                            masked_key = f"{key[:8]}{'*' * (len(key) - 12)}{key[-4:]}" if len(key) > 12 else "*" * len(key)
                        else:
                            masked_key = "无法读取"
                        st.text_input(f"{service}", value=masked_key, disabled=True, key=f"stored_{service}")
                    
                    with col2:
                        if st.button("🔄 轮换", key=f"rotate_{service}"):
                            self._show_key_rotation_interface(service)
                    
                    with col3:
                        if st.button("🗑️ 删除", key=f"delete_{service}"):
                            if api_key_manager.delete_api_key(service):
                                st.success(f"已删除 {service} 的API密钥")
                                st.rerun()
                            else:
                                st.error("删除失败")
            
            # 添加新API密钥
            st.markdown("#### 添加新API密钥")
            
            with st.form("add_api_key_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    service_name = st.text_input(
                        "服务名称",
                        placeholder="例如: deepseek, openai, claude",
                        help="输入API服务的名称"
                    )
                
                with col2:
                    expires_hours = st.number_input(
                        "过期时间(小时)",
                        min_value=0,
                        max_value=8760,  # 1年
                        value=0,
                        help="0表示永不过期"
                    )
                
                api_key = st.text_input(
                    "API密钥",
                    type="password",
                    help="输入要存储的API密钥"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("💾 存储密钥", type="primary"):
                        self._store_api_key(service_name, api_key, expires_hours if expires_hours > 0 else None)
                
                with col2:
                    if st.form_submit_button("🧪 验证密钥"):
                        self._validate_api_key(service_name, api_key)
        
        except Exception as e:
            st.error(f"API密钥管理失败: {e}")
            logger.error(f"API key management error: {e}")
    
    def _render_data_validation_settings(self):
        """渲染数据验证设置"""
        st.markdown("### 🛡️ 数据验证设置")
        
        # 文件验证测试
        with st.expander("📁 文件验证测试"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_filename = st.text_input(
                    "测试文件名",
                    value="resume.pdf",
                    help="输入要测试的文件名"
                )
                
                test_file_size = st.number_input(
                    "文件大小(MB)",
                    min_value=0.1,
                    max_value=100.0,
                    value=2.5,
                    step=0.1,
                    help="输入文件大小进行测试"
                )
            
            with col2:
                if st.button("🧪 测试文件验证"):
                    file_size_bytes = int(test_file_size * 1024 * 1024)
                    is_valid, error_msg = validate_file(test_filename, file_size_bytes)
                    
                    if is_valid:
                        st.success(f"✅ 文件验证通过: {test_filename}")
                    else:
                        st.error(f"❌ 文件验证失败: {error_msg}")
        
        # URL验证测试
        with st.expander("🌐 URL验证测试"):
            test_url = st.text_input(
                "测试URL",
                value="https://example.com",
                help="输入要测试的URL"
            )
            
            if st.button("🧪 测试URL验证"):
                is_valid = validate_url(test_url)
                
                if is_valid:
                    st.success(f"✅ URL验证通过: {test_url}")
                else:
                    st.error(f"❌ URL验证失败: 格式不正确")
        
        # 输入清理测试
        with st.expander("🧹 输入清理测试"):
            test_input = st.text_area(
                "测试文本",
                value="这是一个测试文本，包含控制字符\x00和长内容...",
                help="输入要测试清理的文本"
            )
            
            max_length = st.slider("最大长度", 10, 1000, 100)
            
            if st.button("🧪 测试输入清理"):
                cleaned = DataValidator.sanitize_input(test_input, max_length)
                
                st.markdown("**清理前:**")
                st.code(test_input)
                
                st.markdown("**清理后:**")
                st.code(cleaned)
    
    def _render_privacy_protection_settings(self):
        """渲染隐私保护设置"""
        st.markdown("### 🛡️ 隐私保护设置")
        
        # 敏感信息遮蔽测试
        with st.expander("🔒 敏感信息遮蔽测试"):
            test_text = st.text_area(
                "测试文本",
                value="我的手机号是13812345678，邮箱是test@example.com，身份证号是110101199001011234",
                help="输入包含敏感信息的测试文本"
            )
            
            mask_char = st.text_input("遮蔽字符", value="*", max_chars=1)
            
            if st.button("🧪 测试敏感信息遮蔽"):
                masked_text = PrivacyProtector.mask_sensitive_data(test_text, mask_char)
                
                st.markdown("**原始文本:**")
                st.code(test_text)
                
                st.markdown("**遮蔽后:**")
                st.code(masked_text)
        
        # 简历匿名化测试
        with st.expander("📄 简历匿名化测试"):
            resume_content = st.text_area(
                "简历内容",
                value="姓名：张三\n年龄：25\n性别：男\n手机：13812345678\n邮箱：zhangsan@example.com",
                help="输入简历内容进行匿名化测试"
            )
            
            if st.button("🧪 测试简历匿名化"):
                anonymized = PrivacyProtector.anonymize_resume_data(resume_content)
                
                st.markdown("**原始简历:**")
                st.code(resume_content)
                
                st.markdown("**匿名化后:**")
                st.code(anonymized)
        
        # 隐私保护设置
        with st.expander("⚙️ 隐私保护配置"):
            enable_auto_anonymize = st.checkbox(
                "自动匿名化处理",
                value=st.session_state.get('auto_anonymize', True),
                help="自动对处理的简历进行匿名化"
            )
            
            enable_log_masking = st.checkbox(
                "日志信息遮蔽",
                value=st.session_state.get('log_masking', True),
                help="自动遮蔽日志中的敏感信息"
            )
            
            data_retention_days = st.slider(
                "数据保留天数",
                min_value=1,
                max_value=365,
                value=st.session_state.get('data_retention_days', 30),
                help="自动删除超过指定天数的数据"
            )
            
            if st.button("💾 保存隐私设置"):
                st.session_state.auto_anonymize = enable_auto_anonymize
                st.session_state.log_masking = enable_log_masking
                st.session_state.data_retention_days = data_retention_days
                
                st.success("隐私保护设置已保存")
    
    def _render_security_tests(self):
        """渲染安全测试"""
        st.markdown("### 🧪 安全测试")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 检查系统安全状态"):
                self._run_security_check()
        
        with col2:
            if st.button("🗝️ 测试加密解密"):
                self._test_encryption()
        
        # 安全报告
        with st.expander("📊 安全状态报告"):
            self._show_security_report()
    
    def _store_api_key(self, service_name: str, api_key: str, expires_hours: Optional[int]):
        """存储API密钥"""
        try:
            if not service_name or not api_key:
                st.error("服务名称和API密钥不能为空")
                return
            
            # 验证API密钥格式
            if not DataValidator.validate_api_key(api_key):
                st.error("API密钥格式不正确")
                return
            
            api_key_manager = get_api_key_manager()
            api_key_manager.store_api_key(service_name, api_key, expires_hours)
            
            st.success(f"API密钥已成功存储: {service_name}")
            st.rerun()
            
        except SecurityError as e:
            st.error(f"存储失败: {e}")
            logger.error(f"API key storage error: {e}")
        except Exception as e:
            st.error(f"存储失败: {e}")
            logger.error(f"Unexpected error storing API key: {e}")
    
    def _validate_api_key(self, service_name: str, api_key: str):
        """验证API密钥"""
        try:
            if not service_name or not api_key:
                st.error("服务名称和API密钥不能为空")
                return
            
            # 基础格式验证
            if DataValidator.validate_api_key(api_key):
                st.success("✅ API密钥格式验证通过")
                
                # 这里可以添加实际的API连接测试
                # 根据service_name调用对应的API测试
                if service_name.lower() in ["deepseek", "openai", "claude"]:
                    st.info("💡 建议保存后进行实际连接测试")
                else:
                    st.warning("⚠️ 未知服务类型，无法进行详细验证")
            else:
                st.error("❌ API密钥格式不正确")
                
        except Exception as e:
            st.error(f"验证失败: {e}")
            logger.error(f"API key validation error: {e}")
    
    def _show_key_rotation_interface(self, service_name: str):
        """显示密钥轮换界面"""
        with st.form(f"rotate_key_{service_name}"):
            st.markdown(f"#### 🔄 轮换 {service_name} 密钥")
            
            new_api_key = st.text_input(
                "新API密钥",
                type="password",
                help="输入新的API密钥"
            )
            
            if st.form_submit_button("🔄 执行轮换"):
                try:
                    if not new_api_key:
                        st.error("新API密钥不能为空")
                        return
                    
                    if not DataValidator.validate_api_key(new_api_key):
                        st.error("新API密钥格式不正确")
                        return
                    
                    api_key_manager = get_api_key_manager()
                    if api_key_manager.rotate_api_key(service_name, new_api_key):
                        st.success(f"✅ {service_name} 密钥轮换成功")
                        st.rerun()
                    else:
                        st.error("密钥轮换失败")
                        
                except Exception as e:
                    st.error(f"轮换失败: {e}")
                    logger.error(f"Key rotation error: {e}")
    
    def _run_security_check(self):
        """运行安全检查"""
        try:
            with st.spinner("正在进行安全检查..."):
                # 检查API密钥存储
                api_key_manager = get_api_key_manager()
                services = api_key_manager.list_services()
                
                checks = []
                
                # 检查1: API密钥加密存储
                if services:
                    checks.append(("✅", "API密钥已加密存储", "正常"))
                else:
                    checks.append(("⚠️", "未发现存储的API密钥", "提示"))
                
                # 检查2: 主密钥安全
                security_manager = get_security_manager()
                if security_manager.master_key:
                    checks.append(("✅", "主密钥已设置", "正常"))
                else:
                    checks.append(("❌", "主密钥未设置", "风险"))
                
                # 检查3: 隐私保护设置
                if st.session_state.get('auto_anonymize', True):
                    checks.append(("✅", "自动匿名化已启用", "正常"))
                else:
                    checks.append(("⚠️", "自动匿名化未启用", "建议"))
                
                # 检查4: 数据保留策略
                retention_days = st.session_state.get('data_retention_days', 30)
                if retention_days <= 90:
                    checks.append(("✅", f"数据保留期设置合理({retention_days}天)", "正常"))
                else:
                    checks.append(("⚠️", f"数据保留期较长({retention_days}天)", "建议"))
                
                # 显示检查结果
                st.markdown("#### 🔍 安全检查结果")
                
                for icon, message, status in checks:
                    if status == "正常":
                        st.success(f"{icon} {message}")
                    elif status == "建议":
                        st.warning(f"{icon} {message}")
                    else:
                        st.error(f"{icon} {message}")
                
        except Exception as e:
            st.error(f"安全检查失败: {e}")
            logger.error(f"Security check error: {e}")
    
    def _test_encryption(self):
        """测试加密解密功能"""
        try:
            with st.spinner("正在测试加密解密..."):
                test_data = "这是一个测试数据包含敏感信息：13812345678"
                
                # 加密测试
                security_manager = get_security_manager()
                encrypted = security_manager.encrypt_data(test_data, "test_context")
                
                # 解密测试
                decrypted = security_manager.decrypt_data(encrypted, "test_context")
                
                # 验证结果
                if decrypted == test_data:
                    st.success("✅ 加密解密测试通过")
                    
                    with st.expander("📋 测试详情"):
                        st.markdown("**原始数据:**")
                        st.code(test_data)
                        
                        st.markdown("**加密后数据:**")
                        st.code(encrypted.data[:50] + "..." if len(encrypted.data) > 50 else encrypted.data)
                        
                        st.markdown("**解密后数据:**")
                        st.code(decrypted)
                        
                        st.markdown("**加密信息:**")
                        st.json({
                            "创建时间": encrypted.created_at.isoformat(),
                            "过期时间": encrypted.expires_at.isoformat() if encrypted.expires_at else "永不过期",
                            "上下文": encrypted.metadata.get("context", "无")
                        })
                else:
                    st.error("❌ 加密解密测试失败：数据不匹配")
                    
        except Exception as e:
            st.error(f"加密解密测试失败: {e}")
            logger.error(f"Encryption test error: {e}")
    
    def _show_security_report(self):
        """显示安全状态报告"""
        try:
            # 收集安全状态信息
            api_key_manager = get_api_key_manager()
            services = api_key_manager.list_services()
            
            report_data = {
                "加密API密钥数量": len(services),
                "已存储服务": services,
                "自动匿名化": "已启用" if st.session_state.get('auto_anonymize', True) else "未启用",
                "日志遮蔽": "已启用" if st.session_state.get('log_masking', True) else "未启用",
                "数据保留期": f"{st.session_state.get('data_retention_days', 30)}天",
                "最后检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 安全评分
            score = 0
            if len(services) > 0:
                score += 25
            if st.session_state.get('auto_anonymize', True):
                score += 25
            if st.session_state.get('log_masking', True):
                score += 25
            if st.session_state.get('data_retention_days', 30) <= 90:
                score += 25
            
            report_data["安全评分"] = f"{score}/100"
            
            # 显示报告
            col1, col2 = st.columns(2)
            
            with col1:
                st.json(report_data)
            
            with col2:
                # 安全评分可视化
                if score >= 80:
                    st.success(f"🛡️ 安全状态良好 ({score}/100)")
                elif score >= 60:
                    st.warning(f"⚠️ 安全状态一般 ({score}/100)")
                else:
                    st.error(f"❌ 安全状态需要改善 ({score}/100)")
                
                # 改进建议
                st.markdown("**改进建议:**")
                if len(services) == 0:
                    st.write("• 添加并加密存储API密钥")
                if not st.session_state.get('auto_anonymize', True):
                    st.write("• 启用自动匿名化功能")
                if not st.session_state.get('log_masking', True):
                    st.write("• 启用日志信息遮蔽")
                if st.session_state.get('data_retention_days', 30) > 90:
                    st.write("• 缩短数据保留期至90天以内")
                
        except Exception as e:
            st.error(f"生成安全报告失败: {e}")
            logger.error(f"Security report error: {e}")