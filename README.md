# 🎯 Resume Assistant

一个AI驱动的简历优化助手，提供TUI终端界面、网页爬虫、智能分析和简历优化建议。

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Rich](https://img.shields.io/badge/TUI-Rich-green.svg)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

## ✨ 主要特性

### 🖥️ 现代化TUI界面
- **Rich驱动的美观终端界面**
- **vim风格的快捷键操作**
- **实时响应的交互体验**
- **多面板管理系统**

### 🔍 智能网页爬虫
- **🤖 Playwright自动化引擎**
- **🛡️ 反检测机制**
- **🌐 支持BOSS直聘等主流招聘网站**
- **📊 完整的测试和诊断工具**

### 🤖 AI智能分析
- **📋 简历与职位匹配度分析**
- **💯 多维度评分系统**
- **💡 个性化优化建议**
- **🎯 技能缺口识别**

### 📄 简历管理系统
- **📁 支持PDF、Markdown、文本格式**
- **🔍 智能内容解析**
- **📊 版本管理和历史记录**
- **🏷️ 标签和分类系统**

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Linux/macOS/Windows WSL

### 安装和运行

```bash
# 克隆项目
git clone https://github.com/rainfd/ResumeAgent.git
cd ResumeAgent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
# 或使用Poetry: poetry install

# 安装Playwright浏览器
./venv/bin/python -m playwright install chromium

# 启动应用
./venv/bin/python src/resume_assistant/main.py
```

## 📖 使用指南

### 基本操作
- **数字键 1-6**: 快速切换面板
- **字母键 q**: 退出应用
- **字母键 h**: 显示帮助信息

### 职位管理 (按2)
- **a键**: 手动添加职位
- **c键**: 从URL爬取职位信息
- **v键**: 查看职位详情
- **d键**: 删除职位

### 简历管理 (按3)
- **u键**: 上传简历文件
- **v键**: 查看简历内容
- **d键**: 删除简历

### AI分析 (按4)
- **s键**: 开始新的匹配分析
- **v键**: 查看分析结果
- **d键**: 删除分析记录

## 🛠️ 爬虫功能

### 支持的网站
- ✅ **BOSS直聘** (zhipin.com)
- 🔄 **更多网站开发中...**

### 反爬机制应对
- 🎭 **浏览器指纹伪装**
- 🕐 **智能延时策略**
- 🔄 **自动重试机制**
- 🛡️ **反检测脚本注入**

### 使用建议
由于各招聘网站的反爬机制日益完善，推荐优先尝试自动爬取，失败时使用手动添加功能。

## 🧪 测试工具

项目包含完整的测试套件：

```bash
# 运行爬虫测试
./venv/bin/python test_scraper.py

# 运行调试工具
./venv/bin/python debug_scraper.py
```

## 📊 项目结构

```
ResumeAgent/
├── src/resume_assistant/          # 主要源码
│   ├── core/                      # 核心模块
│   │   ├── scraper.py            # 网页爬虫
│   │   ├── job_manager.py        # 职位管理
│   │   └── resume_processor.py   # 简历处理
│   ├── ui/                       # 用户界面
│   │   ├── app.py               # 主应用
│   │   └── components.py        # UI组件
│   └── utils/                    # 工具函数
├── data/                         # 数据存储
├── tests/                        # 测试文件
├── test_scraper.py              # 爬虫测试套件
├── debug_scraper.py             # 调试工具
└── scraper_test_report.md       # 测试报告
```

## 🔧 技术栈

- **🐍 Python 3.9+** - 主要开发语言
- **🎨 Rich** - 终端界面框架
- **🤖 Playwright** - 网页自动化
- **🍲 BeautifulSoup** - HTML解析
- **📄 PyMuPDF** - PDF处理
- **🔍 Requests** - HTTP客户端
- **⚙️ Pydantic** - 数据验证
- **📝 Loguru** - 日志系统

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📋 开发路线图

- [x] 🖥️ TUI界面框架
- [x] 📄 简历管理系统
- [x] 🤖 网页爬虫引擎
- [x] 🧪 测试和调试工具
- [ ] 🔌 更多招聘网站支持
- [ ] 🌐 浏览器插件开发
- [ ] 📱 Web界面版本
- [ ] 🔗 官方API集成
- [ ] ☁️ 云端数据同步

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Rich](https://github.com/Textualize/rich) - 强大的终端界面库
- [Playwright](https://playwright.dev/) - 现代化的网页自动化工具
- [PyMuPDF](https://pymupdf.readthedocs.io/) - 优秀的PDF处理库

## 📧 联系方式

- GitHub Issues: [问题反馈](https://github.com/rainfd/ResumeAgent/issues)
- 项目主页: [ResumeAgent](https://github.com/rainfd/ResumeAgent)

---

**⭐ 如果这个项目对你有帮助，请给个星标支持！**