# Travel Advisor — 项目全景总结

## 一、项目定位

**Travel Advisor** — 基于 LLM 的智能旅行规划助手。用户通过 Chat 界面输入旅行需求（目的地类型、预算、季节、偏好），Agent 输出结构化、可执行的旅行计划。

---

## 二、整体架构

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 CDN)                   │
│  index.html  ←→  style.css  ←→  chat.js                  │
│  双模式输入     极简白设计      SSE流式渲染 + 对话管理     │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /api/chat/stream (SSE)
┌──────────────────────▼───────────────────────────────────┐
│                  Backend (FastAPI)                        │
│  routes/chat.py  ←→  agent/agent.py  ←→  agent/tools.py │
│  SSE流式响应          Agent循环           Tavily搜索      │
│                       │                                   │
│                  llm/client.py (DeepSeek v4)              │
│                  memory/session.py (会话管理)              │
└──────────────────────────────────────────────────────────┘
```

**关键设计决策：** 前后端通过 SSE (Server-Sent Events) 流式通信。Agent 循环分为两个阶段——先工具调用（非流式），再最终回复（流式）。每个用户消息立即持久化到内存会话中。

---

## 三、各模块详解

### 3.1 Frontend — 151 行 HTML + 742 行 CSS + 484 行 JS

| 特性 | 实现方式 |
|------|----------|
| **双模式输入** | Tab 切换：自由输入（快捷提示词卡片 + 输入框）/ 快速选择（3步引导：目的地类型 → 预算季节 → 偏好标签） |
| **流式渲染** | SSE ReadableStream 解析，`tool_call`/`tool_result`/`content`/`done` 四种事件类型，`marked.js` 渲染 Markdown |
| **对话管理** | localStorage 持久化对话元数据，侧边栏显示历史对话列表，支持切换/删除/新建 |
| **后台流式** | 每个会话独立维护消息数组和 AbortController，切换对话时后台流继续渲染，切回时完整显示 |
| **自适应** | 4 断点 (`<380`/`380-600`/`600-900`/`900+`)，`clamp()` 流体尺寸，44px 触摸目标，safe-area 支持 |
| **视觉设计** | 极简白 + 黑/灰调色板，CSS 变量体系，暗色侧边栏。桌面端侧边栏常驻 260px，移动端汉堡菜单 + 滑入面板 |

### 3.2 Agent 引擎 — 189 行

```
用户消息 → [可选: web_search × N轮] → 流式输出旅行计划
```

- **双模式运行：** 配置了 Tavily Key → 先搜索互联网收集信息，再规划。未配置 → 直接用 LLM 内置知识。
- **System Prompt 约束：** 强制执行结构化输出模板——📍行程概览 → 🗺️每日行程（4时段：上午/中午/下午/晚上，明确时间+地名+交通）→ 💰逐项费用明细表 → 📋行前清单 → 💡贴士
- **核心原则：** 每一块钱精确到具体金额、每一个地名必须是真实名称、每一段交通必须有方案

### 3.3 Web Search 工具 — 92 行

- **工具：** `web_search(queries: list[str])` — 支持批量搜索，一次可提交多个查询词条
- **后端：** Tavily Search API（AI 优化，返回结构化结果：answer + results[title/url/content]）
- **降级：** 无 Tavily Key 时 `TOOL_SCHEMAS=[]`，Agent 跳过工具调用循环，直接基于 LLM 知识输出
- **已移除：** `app/data/` 下的全部假数据文件（destinations.py / hotels.py / attractions.py / weather.py），零残留引用

### 3.4 LLM 客户端 — 41 行

- DeepSeek v4（通过 OpenAI 兼容接口）
- `chat_completion()`: 非流式调用，用于工具调用轮次，返回完整 message dict
- `chat_completion_stream()`: 流式调用，用于最终回复，yield 文本 token

### 3.5 会话管理 — 109 行

- **存储结构：** 内存 dict `{session_id: {history: [...], created_at, last_accessed_at}}`
- **过期策略：** 基于 `last_accessed_at`（非 create_at）清理超过 TTL（默认 3600 秒）的会话
- **REST API：**
  - `GET /api/sessions` — 列出所有活跃会话（含标题、消息数、时间）
  - `GET /api/sessions/{id}` — 获取会话完整历史
  - `DELETE /api/sessions/{id}` — 删除会话
- **消息持久化：** 用户消息在 SSE 流开始**之前**立即保存，助手消息在流完成后保存。确保即使流中断，用户消息也不会丢失
- **历史裁剪：** 每个会话最多保留最近 20 条消息

### 3.6 配置 — 15 行

```python
DEEPSEEK_API_KEY      # 必填
DEEPSEEK_BASE_URL     # 默认 https://api.deepseek.com
DEEPSEEK_MODEL        # 默认 deepseek-v4-pro
TAVILY_API_KEY        # 可选，启用 Web Search
max_tool_rounds       # 默认 5
session_ttl_seconds   # 默认 3600（1小时）
```

---

## 四、数据流

### 4.1 发送消息（无 Web Search 模式）

```
用户输入 → handleSend()
  → POST /api/chat/stream {message, session_id}
    → memory.create_session() / memory.get_history()
    → memory.add_message(user)  ← 用户消息立即保存
    → agent.run(user_message, history)
      → chat_completion_stream(messages)
        → yield content tokens (SSE)
      → yield done
    → memory.add_message(assistant)  ← 助手消息完成后保存
  → 前端 SSE 解析 → 渲染 Markdown
```

### 4.2 发送消息（Web Search 模式）

```
用户输入 → ... → agent.run(user_message, history)
  → 第1轮: chat_completion(messages, tools=[web_search])
    → LLM 决定搜索 "贵州 7月 避暑 旅行 攻略"
    → execute_web_search(["贵州 7月 避暑..."])
      → Tavily API → 返回搜索结果
    → 搜索结果注入 messages
  → 第2轮: LLM 决定继续搜索或开始规划
  → ...最多5轮...
  → chat_completion_stream(messages) → 流式输出最终计划
```

### 4.3 切换对话（后台流式）

```
对话A 流式进行中 → 用户点击对话B
  → stashSession() — 保存A的消息引用和AbortController
  → unstashSession(B) — 加载B的消息（来自 sessionStore 或 API）
  → A的SSE回调继续更新 shared message objects
  → 用户切回A → unstashSession(A) — 看到已完成的内容
```

---

## 五、项目状态

| 维度 | 状态 |
|------|------|
| **可用性** | ✅ 可运行，前后端功能完整 |
| **Agent 模式** | ✅ LLM-only 模式正常工作。Web Search 模式待配置 Tavily Key 后启用 |
| **前端渲染** | ✅ Markdown 正确渲染（标题/加粗/列表/表格/代码） |
| **响应式** | ✅ 4 断点覆盖手机/平板/桌面，触摸目标 ≥44px |
| **对话管理** | ✅ 侧边栏历史、切换对话、后台流式不中断 |
| **布局** | ✅ 长内容不挤压输入框，`height: 100dvh` 约束容器 |
| **数据来源** | ⚠️ 当前无 Tavily Key → 纯 LLM 知识（无实时价格/天气） |
| **会话存储** | ⚠️ 纯内存 dict，服务器重启后所有对话丢失 |
| **并发安全** | ⚠️ 无 asyncio.Lock，同一会话的多并发请求存在竞态条件 |
| **错误处理** | ⚠️ 前端有 try-catch，但无超时反馈 / 自动重试机制 |
| **测试** | ❌ 无自动化测试（单元测试 / 集成测试均无） |

---

## 六、优化方向

### 高优先级

1. **配置 Tavily API Key**  
   注册 https://tavily.com → 获取免费 Key → 写入 `.env` 的 `TAVILY_API_KEY`。Agent 将自动启用实时搜索，输出包含最新价格和天气。

2. **会话持久化**  
   将 `_sessions` 从内存 dict 改为 JSON 文件或 SQLite 存储。服务器重启后对话不丢失。

3. **超时与重试**  
   LLM 调用超过 60 秒时向前端发送 `progress` 事件提示用户等待，而非静默阻塞。网络错误时自动重试 1 次。

### 中优先级

4. **Agent 多轮规划能力**  
   当用户回复"太贵了"、"换一个目的地"、"多加一天"时，Agent 应基于历史对话理解上下文并重新规划，而非从零开始。

5. **输出缓存**  
   对相同或相似的旅行查询缓存结果，减少 LLM 调用次数和成本。

6. **并发锁**  
   在 `add_message` 等写操作上加 `asyncio.Lock`，防止多请求竞争导致消息乱序。

### 低优先级

7. **Markdown 流式渲染优化**  
   流式输出时部分 Markdown（如未闭合的表格）可能出现短暂渲染异常。可通过延迟渲染或逐段解析优化。

8. **导出功能**  
   一键导出旅行计划为 Markdown 文件或 PDF。

9. **多 LLM 适配**  
   抽象 LLM 客户端接口，支持配置化切换 DeepSeek / Claude / GPT 等不同模型。
