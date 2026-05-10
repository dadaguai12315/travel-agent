# 🌍 Travel Advisor

基于 LLM 的智能旅行规划助手。支持多轮对话、流式输出、Web 搜索增强，可生成结构化、可执行的旅行计划。

## 效果预览

### 登录页面
![登录](https://via.placeholder.com/800x500/f9fafb/111?text=Login+Page)

### 旅行规划
![聊天](https://via.placeholder.com/800x500/ffffff/111?text=Travel+Plan+Generation)

### 暗色模式
![暗色](https://via.placeholder.com/800x500/111827/f3f4f6?text=Dark+Mode)

## 核心特性

- **流式输出** — SSE 实时推送，Markdown 渲染，30FPS 节流刷新
- **Web 搜索增强** — 集成 Tavily Search API，获取实时天气、价格、签证信息
- **多会话管理** — 侧边栏历史对话，支持切换/删除/后台流式
- **旅行计划模板** — 结构化输出：行程概览 → 每日行程(4时段) → 费用明细 → 行前清单 → 贴士
- **JWT 多租户** — 邮箱注册/登录，用户数据隔离
- **双模式 Agent** — 配置搜索 Key 启用实时检索，未配置则使用 LLM 内置知识
- **亮色/暗色主题** — 一键切换
- **响应式设计** — 移动端/平板/桌面全适配

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia |
| 后端 | FastAPI + Pydantic v2 + SQLAlchemy + Alembic |
| 数据库 | PostgreSQL 16 |
| 缓存 | Redis 7 |
| LLM | DeepSeek v4 (OpenAI 兼容接口) |
| 搜索 | Tavily Search API |
| 部署 | Docker Compose |

## 快速开始

### 前置条件

- Docker Desktop
- DeepSeek API Key ([获取地址](https://platform.deepseek.com))

### 1. 克隆项目

```bash
git clone <repo-url>
cd travel-agent
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填入必填项：

```env
LLM_API_KEY=sk-your-deepseek-key     # 必填
# TAVILY_API_KEY=tvly-xxx           # 可选，启用 Web 搜索
```

### 3. 启动服务

```bash
docker compose up -d --build
```

### 4. 数据库迁移

```bash
docker compose exec backend alembic upgrade head
```

### 5. 打开浏览器

- 前端：http://localhost:5173
- 后端文档：http://localhost:8000/docs（需设置 `DEBUG=true`）

### 6. 使用

1. 注册账号（邮箱 + 密码）
2. 输入旅行需求，如"推荐一个 7 月避暑目的地，预算 2000/人"
3. Agent 自动搜索信息并生成结构化旅行计划
4. 左侧边栏管理历史对话

## 项目结构

```
travel-agent/
├── backend/
│   ├── app/
│   │   ├── agent/          # Agent 引擎 (State Graph)
│   │   │   ├── graph.py    # 工作流控制器
│   │   │   ├── nodes/      # Analyzer, Researcher, Planner, Reviewer, Streamer
│   │   │   ├── state.py    # 状态定义
│   │   │   └── tools.py    # Tavily Web Search
│   │   ├── api/            # REST + SSE 路由
│   │   ├── core/           # 配置, JWT, Redis, LLM Client
│   │   ├── db/             # SQLAlchemy async engine
│   │   ├── models/         # User, Session, Message
│   │   ├── schemas/        # Pydantic v2 验证
│   │   └── services/       # 业务逻辑层
│   ├── alembic/            # 数据库迁移
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios client + JWT interceptor
│   │   ├── components/     # ChatMessage, ChatInput, ChatSidebar
│   │   ├── stores/         # Pinia: auth, chat
│   │   ├── views/          # LoginPage, ChatWorkspace
│   │   └── utils/          # Markdown renderer
│   ├── vite.config.ts
│   └── tailwind.config.js
└── docker-compose.yml
```

## API 概览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/health` | 健康检查 | - |
| `POST` | `/api/v1/auth/register` | 注册 | - |
| `POST` | `/api/v1/auth/login` | 登录 | - |
| `GET` | `/api/v1/sessions` | 对话列表 | JWT |
| `POST` | `/api/v1/sessions` | 创建对话 | JWT |
| `GET` | `/api/v1/sessions/{id}` | 对话历史 | JWT |
| `DELETE` | `/api/v1/sessions/{id}` | 删除对话 | JWT |
| `POST` | `/api/v1/chat/stream` | SSE 流式聊天 | JWT |

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LLM_API_KEY` | **是** | - | DeepSeek API Key |
| `LLM_BASE_URL` | 否 | `https://api.deepseek.com` | LLM 接口地址 |
| `LLM_MODEL` | 否 | `deepseek-v4-pro` | 模型名称 |
| `TAVILY_API_KEY` | 否 | - | Tavily 搜索 Key |
| `DATABASE_URL` | 否 | `postgresql+asyncpg://...` | 数据库连接 |
| `REDIS_URL` | 否 | `redis://localhost:6379/0` | Redis 连接 |
| `JWT_SECRET_KEY` | 否 | `change-me...` | JWT 签名密钥 |
| `DEBUG` | 否 | `false` | 调试模式 |

## License

MIT
