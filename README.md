# Resume Assistant

基于AI的智能简历优化工具，采用Streamlit Web界面。

## 🌟 功能特性

- 🕷️ **职位管理**: 从BOSS直聘等网站抓取职位信息
- 📄 **简历管理**: 上传和管理PDF/Markdown格式简历
- 🤖 **AI分析**: 智能分析简历与职位的匹配度
- 💡 **优化建议**: 获得针对性的简历改进建议
- 💬 **打招呼语**: 生成个性化的求职开场白

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd ResumeAgent

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行应用

#### 方式1: 完整版Streamlit应用

```bash
streamlit run streamlit_app.py
```

然后在浏览器中访问: http://localhost:8501

#### 方式2: 演示版本

```bash
python demo_app.py
# 或
streamlit run demo_app.py
```

#### 方式3: 快速预览

```bash
# 文本界面演示
python interface_demo.py

# HTML页面演示
open demo.html
```

## 📁 项目结构

```
📦 Resume Assistant
├── streamlit_app.py           # 🚀 主Streamlit应用
├── demo_app.py                # 🎯 演示版本应用
├── interface_demo.py          # 📱 文本界面演示
├── demo.html                  # 🌐 HTML演示页面
├── requirements.txt           # 📋 项目依赖
├── pyproject.toml            # 🔧 项目配置
└── src/resume_assistant/
    ├── web/                   # 🌐 Web界面模块
    │   ├── session_manager.py # 🔄 Session State管理
    │   ├── navigation.py      # 🧭 导航管理
    │   ├── components.py      # 🎨 UI组件库
    │   ├── adapters.py        # 🔌 Web适配器
    │   └── pages/             # 📄 页面模块
    │       ├── job_management.py      # 💼 职位管理页面
    │       ├── resume_management.py   # 📝 简历管理页面
    │       └── analysis_results.py    # 📊 分析结果页面
    ├── data/                  # 🗃️ 数据层
    │   ├── database.py        # 🗄️ SQLite数据库管理器
    │   ├── models.py          # 📋 数据模型定义
    │   └── migrations/        # 🔄 数据库迁移
    ├── core/                  # ⚙️ 核心功能
    │   ├── scraper.py         # 🕷️ 网页爬虫
    │   ├── parser.py          # 📄 简历解析器
    │   └── ai_analyzer.py     # 🤖 AI分析器
    ├── config/                # ⚙️ 配置管理
    └── utils/                 # 🔧 工具模块
```

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下环境变量：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/resume_assistant.log

# 数据库配置
DATABASE_PATH=data/resume_assistant.db
```

### API密钥获取

1. 访问 [DeepSeek API](https://platform.deepseek.com) 注册账号
2. 获取API密钥
3. 将密钥配置到 `.env` 文件或应用设置页面

## 🎯 使用指南

### 1. 职位管理
- 在"职位管理"页面输入招聘网站的职位链接
- 系统自动爬取职位信息并存储
- 支持职位列表展示、搜索和删除

### 2. 简历管理
- 在"简历管理"页面上传PDF或Markdown格式的简历
- 系统自动解析简历内容和结构
- 支持简历预览和管理

### 3. AI分析
- 在"分析结果"页面选择目标职位和简历
- 点击开始分析，获得匹配度评分
- 查看详细的分析报告和优化建议

### 4. 打招呼语生成
- 基于选定的职位和简历
- AI生成个性化的求职开场白
- 支持多版本生成和一键复制

## 🔧 开发说明

### 技术栈

- **前端**: Streamlit Web框架
- **后端**: Python + FastAPI概念
- **数据库**: SQLite + aiosqlite
- **爬虫**: Playwright + BeautifulSoup
- **AI集成**: DeepSeek API
- **文档解析**: PyMuPDF
- **数据可视化**: Plotly

### 开发环境搭建

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black src/
ruff check src/ --fix
```

## 📈 项目状态

### 完成度总结
- **总体进度**: 85% 完成
- **Web界面**: 100% 完成 ✅
- **数据层**: 100% 完成 ✅
- **核心功能**: 90% 完成 ✅
- **测试**: 20% 完成 ⏳
- **文档**: 70% 完成 ✅

### 重要里程碑
1. ✅ **完整Web应用可运行** - streamlit_app.py 已完全实现
2. ✅ **数据库层完整** - 支持数据持久化和CRUD操作
3. ✅ **演示版本就绪** - 多种运行方式可选
4. ✅ **核心业务逻辑** - 职位爬取、简历解析、AI分析均已集成
5. ✅ **用户界面完善** - 响应式设计、实时状态更新

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v0.8.0 (2025-01-01)
- ✅ 完成Streamlit Web界面框架
- ✅ 实现完整的数据库层
- ✅ 集成所有核心功能模块
- ✅ 添加演示版本和多种运行方式

### v0.5.0 (2024-12-31)
- 实现基础的爬虫和解析功能
- 添加AI分析模块
- 建立项目基础架构

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持与反馈

如果您遇到问题或有建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 提交 [Issue](https://github.com/username/ResumeAgent/issues)
3. 联系开发团队

---

**🚀 Resume Assistant - 让简历匹配更智能！**