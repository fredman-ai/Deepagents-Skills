# DeepAgents Skills Demo

基于 LangGraph 和 DeepAgents 框架的智能体 Skills 能力演示项目。

## 项目简介

本项目演示了如何使用 **DeepAgents** 框架构建具有 **Skills（技能）** 能力的智能体系统。通过 Skills 机制，智能体可以动态加载和使用各种预定义的技能模块，实现更强大、更灵活的任务执行能力。

### 核心特性

- 🛠️ **Skills 技能系统**：实现 Anthropic 的 Agent Skills 模式，支持技能的动态加载和渐进式披露
- 🔧 **Middleware 中间件架构**：通过 SkillsMiddleware 和 ShellMiddleware 扩展智能体能力
- 🤖 **子智能体协作**：支持主智能体与专业子智能体（如搜索智能体）的协作
- 📁 **文件系统后端**：支持虚拟文件系统，便于管理生成的内容
- 🌐 **Web 搜索集成**：集成 Tavily 和 SearXNG 搜索引擎

## Skills 系统说明

Skills 是一种让智能体具备专业能力的机制：

1. **渐进式披露**：智能体只知道技能的名称和描述，需要时才读取完整指令
2. **目录结构**：
   - 用户级 Skills: `~/.deepagents/{AGENT_NAME}/skills/`
   - 项目级 Skills: `{PROJECT_ROOT}/agent/skills/`

### 内置 Skills 示例

- **web-research**：结构化的 Web 研究技能，支持多子任务并行研究
- **fullstack-template-generator**：全栈应用模板生成器（FastAPI + React + Vite）

## 项目结构

```
.
├── research_skills_deep_agent.py    # Skills 演示 Agent（主入口）
├── research_stock_deep_agent.py     # 股票分析 Agent（多智能体协作）
├── skills/                          # Skills 模块
│   ├── __init__.py
│   ├── load.py                      # Skills 加载器
│   └── middleware.py                # Skills 中间件
├── shell.py                         # Shell 中间件
├── tools.py                         # 工具集
├── agent/skills/                    # 项目内置 Skills
│   ├── web-research/
│   │   └── SKILL.md
│   └── fullstack-template-generator/
│       ├── SKILL.md
│       └── templates/
├── pyproject.toml                   # 项目依赖配置
└── fs/                              # 文件系统后端存储目录
```

## 工具集

### 搜索工具
- `search` - 通用网络搜索（Tavily + SearXNG）
- `fetch_url` - 获取 URL 内容并转换为 Markdown

### 股票数据工具（可选）
- `get_stock_price` - 获取 A 股历史行情数据
- `get_technical_indicators` - 计算技术指标
- `get_financial_statements` - 获取财务报表
- `get_stock_detailed_info` - 获取公司详细信息
- `get_stock_news` - 获取个股新闻
- `get_stock_research_report` - 获取机构研究报告

数据来源：AKShare、Baostock

## 快速开始

### 1. 环境要求

- Python >= 3.13
- OpenAI API Key（或兼容的 API）
- Tavily API Key（可选，用于网络搜索）

### 2. 安装依赖

推荐使用 [uv](https://github.com/astral-sh/uv) 进行包管理：

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API 配置
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Tavily 搜索 API（可选）
TAVILY_API_KEY=your_tavily_api_key_here

# SearXNG 搜索引擎（可选）
SEARXNG_URL=http://localhost:8080

# Agent 配置
RECURSION_LIMIT=25
```

### 4. 运行示例

#### Skills 演示版本（推荐）

```bash
python research_skills_deep_agent.py
```

然后在交互式对话中输入任务，例如：

```
帮我研究 2025 年 AI 智能体的发展趋势
```

或者使用 LangGraph Dev 模式：

```bash
langgraph dev
```

#### 股票分析版本（多智能体协作）

```bash
python research_stock_deep_agent.py
```

## 使用说明

### Skills 技能使用

智能体会自动识别合适的 Skill 并使用：

1. **web-research**：当用户请求研究某个主题时
   - 自动创建研究计划
   - 分解为多个子任务并行研究
   - 综合生成研究报告

2. **fullstack-template-generator**：当用户需要创建全栈应用时
   - 生成 FastAPI 后端
   - 生成 React + Vite + Tailwind 前端
   - 包含 OpenAI 集成和完整配置

### 分析师角色（股票分析版本）

1. **基本面分析师**
   - 公司基本情况和主营业务
   - 财务报表深度分析
   - 盈利能力、偿债能力、成长性评估
   - 行业趋势和估值水平

2. **技术面分析师**
   - 价格趋势判断
   - 技术指标分析（均线、MACD、KDJ、RSI 等）
   - 支撑位和阻力位识别
   - 买卖时机建议

3. **消息面分析师**
   - 重大新闻梳理
   - 机构研报观点汇总
   - 市场情绪分析
   - 催化剂识别

### 输出结果

生成的文件将保存在 `fs/` 目录下，例如：
- 研究报告：`fs/research_xxx/research_report.md`
- 应用模板：`fs/my-app/` 目录结构

## 技术栈

- **LangGraph** - 多智能体编排框架
- **DeepAgents** - 深度智能体框架（Skills、Middleware、Backend）
- **LangChain** - LLM 应用开发框架
- **Tavily** - AI 搜索引擎
- **AKShare/Baostock** - A 股数据接口（可选）

## 注意事项

- 本项目用于演示 DeepAgents 框架的 Skills 能力
- Skills 系统支持自定义扩展，可创建自己的技能模块
- 股票分析功能仅供参考，不构成投资建议
- API Key 请妥善保管，不要泄露

## License

MIT

## 相关链接

- [DeepAgents 框架](https://github.com/langchain-ai/deepagents)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)

## 免责声明

本项目提供的功能仅供学习和研究使用。股票分析结果仅供参考，不构成任何投资建议。
