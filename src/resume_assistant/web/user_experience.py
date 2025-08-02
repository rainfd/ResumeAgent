"""用户体验优化工具

提供统一的用户确认、提示和反馈功能。
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from ..utils import get_logger

logger = get_logger(__name__)

class ConfirmationManager:
    """确认对话框管理器"""
    
    @staticmethod
    def confirm_delete(item_name: str, item_type: str = "项目") -> bool:
        """显示删除确认对话框"""
        if f"confirm_delete_{item_name}" not in st.session_state:
            st.session_state[f"confirm_delete_{item_name}"] = False
        
        if not st.session_state[f"confirm_delete_{item_name}"]:
            if st.button(f"🗑️ 删除", key=f"delete_btn_{item_name}"):
                st.session_state[f"confirm_delete_{item_name}"] = True
                st.rerun()
            return False
        else:
            st.warning(f"⚠️ 确定要删除{item_type} '{item_name}' 吗？此操作无法撤销。")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认删除", key=f"confirm_delete_btn_{item_name}", type="primary"):
                    st.session_state[f"confirm_delete_{item_name}"] = False
                    return True
            
            with col2:
                if st.button("❌ 取消", key=f"cancel_delete_btn_{item_name}"):
                    st.session_state[f"confirm_delete_{item_name}"] = False
                    st.rerun()
            
            return False
    
    @staticmethod
    def confirm_action(action_name: str, description: str, 
                      confirm_text: str = "确认", cancel_text: str = "取消") -> bool:
        """通用确认对话框"""
        if f"confirm_action_{action_name}" not in st.session_state:
            st.session_state[f"confirm_action_{action_name}"] = False
        
        if not st.session_state[f"confirm_action_{action_name}"]:
            if st.button(f"🔄 {action_name}", key=f"action_btn_{action_name}"):
                st.session_state[f"confirm_action_{action_name}"] = True
                st.rerun()
            return False
        else:
            st.warning(f"⚠️ {description}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ {confirm_text}", key=f"confirm_action_btn_{action_name}", type="primary"):
                    st.session_state[f"confirm_action_{action_name}"] = False
                    return True
            
            with col2:
                if st.button(f"❌ {cancel_text}", key=f"cancel_action_btn_{action_name}"):
                    st.session_state[f"confirm_action_{action_name}"] = False
                    st.rerun()
            
            return False

class NotificationManager:
    """通知管理器"""
    
    @staticmethod
    def show_success(message: str, duration: int = 3):
        """显示成功通知"""
        st.success(f"✅ {message}")
        NotificationManager._auto_clear_notification("success", duration)
    
    @staticmethod
    def show_error(message: str, details: str = None):
        """显示错误通知"""
        st.error(f"❌ {message}")
        if details:
            with st.expander("查看详细错误信息"):
                st.code(details)
    
    @staticmethod
    def show_warning(message: str):
        """显示警告通知"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info(message: str):
        """显示信息通知"""
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def _auto_clear_notification(type: str, duration: int):
        """自动清除通知（实验性功能）"""
        # 在Streamlit中，消息会自动消失，这里只是做个记录
        logger.info(f"Notification shown: {type} (duration: {duration}s)")

class ProgressManager:
    """进度管理器"""
    
    @staticmethod
    def create_progress_tracker(total_steps: int, task_name: str = "Processing"):
        """创建进度追踪器"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        class ProgressTracker:
            def __init__(self, bar, text, total, name):
                self.bar = bar
                self.text = text
                self.total = total
                self.current = 0
                self.task_name = name
            
            def update(self, step_description: str = None):
                self.current += 1
                progress = self.current / self.total
                self.bar.progress(progress)
                
                if step_description:
                    self.text.text(f"{self.task_name}: {step_description} ({self.current}/{self.total})")
                else:
                    self.text.text(f"{self.task_name}: {self.current}/{self.total}")
            
            def finish(self, final_message: str = "完成"):
                self.bar.progress(1.0)
                self.text.text(f"{self.task_name}: {final_message}")
                
            def cleanup(self):
                self.bar.empty()
                self.text.empty()
        
        return ProgressTracker(progress_bar, status_text, total_steps, task_name)

class ValidationManager:
    """验证管理器"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> tuple[bool, list]:
        """验证必填字段"""
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field] or str(data[field]).strip() == "":
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def validate_agent_prompt(prompt: str) -> tuple[bool, str]:
        """验证Agent Prompt模板"""
        if not prompt or len(prompt.strip()) < 10:
            return False, "Prompt模板太短，至少需要10个字符"
        
        required_placeholders = ["{job_description}", "{resume_content}"]
        missing_placeholders = []
        
        for placeholder in required_placeholders:
            if placeholder not in prompt:
                missing_placeholders.append(placeholder)
        
        if missing_placeholders:
            return False, f"Prompt模板缺少必要的占位符: {', '.join(missing_placeholders)}"
        
        return True, "Prompt模板验证通过"
    
    @staticmethod
    def validate_agent_data(agent_data: Dict[str, Any]) -> tuple[bool, list]:
        """验证Agent数据"""
        errors = []
        
        # 检查必填字段
        required_fields = ["name", "description", "agent_type", "prompt_template"]
        is_valid, missing_fields = ValidationManager.validate_required_fields(agent_data, required_fields)
        
        if not is_valid:
            errors.append(f"缺少必填字段: {', '.join(missing_fields)}")
        
        # 检查名称长度
        if "name" in agent_data and len(agent_data["name"]) > 50:
            errors.append("Agent名称不能超过50个字符")
        
        # 检查描述长度
        if "description" in agent_data and len(agent_data["description"]) > 200:
            errors.append("Agent描述不能超过200个字符")
        
        # 验证Prompt模板
        if "prompt_template" in agent_data:
            prompt_valid, prompt_error = ValidationManager.validate_agent_prompt(agent_data["prompt_template"])
            if not prompt_valid:
                errors.append(f"Prompt模板错误: {prompt_error}")
        
        return len(errors) == 0, errors

class LoadingManager:
    """加载状态管理器"""
    
    @staticmethod
    def with_loading(func: Callable, loading_message: str = "处理中..."):
        """装饰器：显示加载状态"""
        def wrapper(*args, **kwargs):
            try:
                with st.spinner(loading_message):
                    return func(*args, **kwargs)
            except Exception as e:
                NotificationManager.show_error(f"操作失败: {str(e)}")
                logger.error(f"Operation failed: {e}")
                raise
        
        return wrapper
    
    @staticmethod
    def show_loading_spinner(message: str = "加载中..."):
        """显示加载旋转器"""
        return st.spinner(message)

class FormManager:
    """表单管理器"""
    
    @staticmethod
    def render_agent_form(agent_data: Dict[str, Any] = None, form_key: str = "agent_form") -> Optional[Dict[str, Any]]:
        """渲染Agent表单"""
        with st.form(form_key):
            # 基本信息
            st.subheader("基本信息")
            
            name = st.text_input(
                "Agent名称",
                value=agent_data.get("name", "") if agent_data else "",
                max_chars=50,
                help="为您的Agent起一个描述性的名称"
            )
            
            description = st.text_area(
                "Agent描述",
                value=agent_data.get("description", "") if agent_data else "",
                max_chars=200,
                help="简单描述这个Agent的用途和特点"
            )
            
            agent_type = st.selectbox(
                "Agent类型",
                options=["general", "technical", "management", "creative", "sales", "custom"],
                index=0,
                format_func=lambda x: {
                    "general": "通用分析",
                    "technical": "技术岗位",
                    "management": "管理岗位",
                    "creative": "创意行业",
                    "sales": "销售岗位",
                    "custom": "自定义"
                }.get(x, x),
                help="选择最适合的Agent类型"
            )
            
            # Prompt模板
            st.subheader("Prompt模板")
            
            prompt_template = st.text_area(
                "Prompt模板",
                value=agent_data.get("prompt_template", "") if agent_data else "",
                height=200,
                help="使用 {job_description} 和 {resume_content} 作为占位符"
            )
            
            # 示例Prompt
            with st.expander("📋 查看Prompt模板示例"):
                st.code("""
请分析以下简历与职位的匹配度：

【职位描述】
{job_description}

【简历内容】  
{resume_content}

请从以下维度进行分析：
1. 技能匹配度 (0-100分)
2. 经验匹配度 (0-100分)  
3. 教育背景匹配度 (0-100分)
4. 关键词覆盖率 (0-100分)
5. 总体匹配度 (0-100分)

并提供具体的优化建议。
                """, language="text")
            
            # 提交按钮
            submitted = st.form_submit_button("💾 保存Agent", type="primary")
            
            if submitted:
                form_data = {
                    "name": name,
                    "description": description,
                    "agent_type": agent_type,
                    "prompt_template": prompt_template
                }
                
                # 验证数据
                is_valid, errors = ValidationManager.validate_agent_data(form_data)
                
                if is_valid:
                    return form_data
                else:
                    for error in errors:
                        NotificationManager.show_error(error)
                    return None
            
            return None

class HelpManager:
    """帮助信息管理器"""
    
    @staticmethod
    def show_agent_help():
        """显示Agent帮助信息"""
        with st.expander("❓ 什么是AI Agent？"):
            st.markdown("""
            **AI Agent** 是可以定制的智能分析助手，它可以：
            
            - 🎯 **专门化分析**: 针对不同行业和职位类型提供专业分析
            - 🔧 **自定义Prompt**: 完全自定义分析逻辑和输出格式
            - 📊 **量化评分**: 提供客观的匹配度评分和建议
            - 🔄 **可复用**: 创建一次，反复使用
            
            **使用步骤**:
            1. 选择或创建适合的Agent类型
            2. 编写自定义的Prompt模板
            3. 在分析时选择对应的Agent
            4. 查看专业化的分析结果
            """)
    
    @staticmethod
    def show_prompt_help():
        """显示Prompt编写帮助"""
        with st.expander("✍️ 如何编写好的Prompt？"):
            st.markdown("""
            **Prompt模板必须包含**:
            - `{job_description}`: 职位描述占位符
            - `{resume_content}`: 简历内容占位符
            
            **编写技巧**:
            1. **明确指令**: 清楚地说明需要分析什么
            2. **结构化输出**: 要求按特定格式返回结果
            3. **量化评分**: 要求给出具体的分数和评级
            4. **针对性**: 根据不同行业调整分析重点
            
            **示例结构**:
            ```
            分析任务: [明确的分析要求]
            输入数据: {job_description} 和 {resume_content}
            输出格式: [具体的输出要求]
            评分标准: [评分的具体标准]
            ```
            """)
    
    @staticmethod
    def show_troubleshooting():
        """显示故障排除帮助"""
        with st.expander("🔧 常见问题解决"):
            st.markdown("""
            **Agent创建失败？**
            - 检查名称和描述是否填写完整
            - 确保Prompt模板包含必要的占位符
            - 检查字符长度限制
            
            **分析结果不理想？**
            - 优化Prompt模板的描述
            - 调整评分标准和要求
            - 尝试不同类型的Agent
            
            **Agent测试失败？**
            - 检查网络连接
            - 验证API密钥配置
            - 查看错误日志详情
            """)