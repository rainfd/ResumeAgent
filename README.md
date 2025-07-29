# Resume Assistant

AI-powered resume optimization tool with Rich TUI interface.

## 功能特性

- 🤖 **AI 驱动分析**: 使用 DeepSeek AI 分析简历与职位匹配度
- 🕷️ **智能爬取**: 自动获取 BOSS 直聘职位信息
- 📄 **多格式支持**: 支持 PDF 和 Markdown 格式简历解析
- 💬 **打招呼语生成**: 基于职位和简历生成个性化开场白
- 🎨 **Rich TUI 界面**: 现代化终端用户界面
- 📊 **数据管理**: 完整的职位、简历和分析历史管理

## 安装

### 环境要求

- Python 3.9+
- Poetry (推荐) 或 pip

### 使用 Poetry 安装

```bash
# 克隆项目
git clone <repository-url>
cd ResumeAgent

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 运行应用
resume-assistant
```

### 使用 pip 安装

```bash
# 克隆项目
git clone <repository-url>
cd ResumeAgent

# 安装依赖
pip install -e .

# 运行应用
resume-assistant
```

## 配置

1. 复制配置文件模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入必要的配置：
   - `RESUME_ASSISTANT_DEEPSEEK_API_KEY`: DeepSeek API 密钥
   - 其他配置项根据需要调整

## 使用方法

### 基本工作流程

1. **添加职位**: 输入 BOSS 直聘职位链接
2. **上传简历**: 支持 PDF 或 Markdown 格式
3. **AI 分析**: 获取匹配度分析和优化建议
4. **生成打招呼语**: 创建个性化的求职开场白
5. **管理数据**: 查看历史记录和版本管理

### 快捷键

- `1-5`: 切换不同功能面板
- `Ctrl+C`: 退出应用
- `Tab`: 在界面元素间切换
- `Enter`: 确认操作

## 开发

### 项目结构

```
src/resume_assistant/
├── __init__.py          # 包初始化
├── main.py              # 应用入口
├── config/              # 配置管理
├── ui/                  # 用户界面
│   ├── panels/          # UI 面板
│   └── components/      # UI 组件
├── core/                # 核心业务逻辑
├── data/                # 数据访问层
└── utils/               # 工具模块
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/unit/

# 生成覆盖率报告
poetry run pytest --cov=resume_assistant
```

### 代码格式化

```bash
# 使用 black 格式化代码
poetry run black .

# 使用 isort 整理导入
poetry run isort .

# 类型检查
poetry run mypy src/
```

## 许可证

[许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请通过以下方式联系：
- 提交 GitHub Issue
- 邮件: contact@resumeagent.dev