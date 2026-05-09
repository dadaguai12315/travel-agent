# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Travel Advisor frontend with minimalist white design, dual-mode input (free text + guided 3-step selection), and polished chat interface.

**Architecture:** Vue 3 CDN single-page app. Three static files (index.html, style.css, chat.js) serve a state-driven UI with two views: home (dual-mode input) and chat (streaming messages). Backend unchanged.

**Tech Stack:** Vue 3 Composition API (CDN), vanilla CSS, SSE streaming, FastAPI backend (unchanged)

---

### Task 1: Rewrite style.css — Minimalist White Design System

**Files:**
- Modify: `app/static/style.css` (complete rewrite)

Complete CSS covering reset, layout, header, home screen (hero, tab switch, quick prompts, guided steps), chat messages, input bar, and responsive breakpoint at 600px. No colorful gradients — black/white/gray palette only.

- [ ] **Step 1: Write the complete style.css**

```css
/* ===== Reset & Base ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --c-bg: #fff;
  --c-surface: #f9fafb;
  --c-surface-hover: #f3f4f6;
  --c-border: #e5e7eb;
  --c-border-light: #f3f4f6;
  --c-text: #111;
  --c-text-secondary: #6b7280;
  --c-text-placeholder: #9ca3af;
  --c-accent: #111;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f5f5;
  color: var(--c-text);
  height: 100dvh;
  display: flex;
  justify-content: center;
  -webkit-font-smoothing: antialiased;
}

/* ===== App Shell ===== */
.app {
  width: 100%;
  max-width: 800px;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--c-bg);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.04), 0 2px 16px rgba(0,0,0,0.04);
}

/* ===== Header ===== */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--c-border-light);
  flex-shrink: 0;
  background: var(--c-bg);
}
.header h1 {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.header-btn {
  background: none;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 6px 14px;
  font-size: 0.8rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.header-btn:hover {
  border-color: var(--c-text);
  color: var(--c-text);
}

/* ===== Content Area ===== */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  -webkit-overflow-scrolling: touch;
}

/* ===== Hero ===== */
.hero {
  text-align: center;
  padding: 32px 16px 24px;
}
.hero-icon { font-size: 2.4rem; margin-bottom: 8px; line-height: 1; }
.hero h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 4px; letter-spacing: -0.01em; }
.hero p { font-size: 0.85rem; color: var(--c-text-secondary); }

/* ===== Tab Switch ===== */
.tab-switch {
  display: flex;
  background: var(--c-surface);
  border-radius: var(--radius-sm);
  padding: 3px;
  margin-bottom: 20px;
  flex-shrink: 0;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 9px 0;
  border-radius: 6px;
  font-size: 0.82rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
  border: none;
  background: none;
}
.tab.active {
  background: var(--c-bg);
  color: var(--c-text);
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* ===== Quick Prompts ===== */
.quick-prompts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.prompt-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--c-surface);
  border: 1px solid var(--c-border-light);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--c-text);
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  width: 100%;
}
.prompt-card:hover {
  border-color: var(--c-accent);
  background: #fafafa;
}
.prompt-card .prompt-icon { font-size: 1.1rem; flex-shrink: 0; }
.prompt-card .prompt-text { flex: 1; }
.prompt-card .prompt-desc {
  font-size: 0.72rem;
  color: var(--c-text-secondary);
  margin-top: 2px;
}

/* ===== Guided Steps ===== */
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 24px;
  flex-shrink: 0;
}
.step-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  transition: all 0.2s;
  flex-shrink: 0;
}
.step-dot.done {
  background: var(--c-accent);
  color: #fff;
}
.step-dot.current {
  background: var(--c-accent);
  color: #fff;
}
.step-dot.pending {
  background: #fff;
  border: 1px solid var(--c-border);
  color: var(--c-text-placeholder);
}
.step-line {
  width: 28px;
  height: 1px;
  background: var(--c-border);
  flex-shrink: 0;
}
.step-line.done { background: var(--c-accent); }

.step-question {
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 20px;
}

.option-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}
.option-card {
  padding: 20px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;
  font-size: 0.82rem;
  user-select: none;
}
.option-card:hover { border-color: var(--c-text); }
.option-card.selected {
  border-color: var(--c-accent);
  border-width: 2px;
  padding: 19px 11px;
  background: #fafafa;
}
.option-card .option-icon { font-size: 1.5rem; margin-bottom: 4px; }

.option-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  justify-content: center;
}
.chip {
  padding: 10px 18px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;
  user-select: none;
}
.chip:hover { border-color: var(--c-text); }
.chip.selected {
  background: var(--c-accent);
  color: #fff;
  border-color: var(--c-accent);
}

.step-nav {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 8px;
}
.btn-back, .btn-next {
  padding: 10px 0;
  border-radius: var(--radius-lg);
  font-size: 0.85rem;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  font-weight: 500;
}
.btn-back {
  flex: 1;
  background: #fff;
  border: 1px solid var(--c-border);
  color: var(--c-text-secondary);
}
.btn-back:hover { border-color: var(--c-text); color: var(--c-text); }
.btn-next {
  flex: 1;
  background: var(--c-accent);
  border: none;
  color: #fff;
}
.btn-next:hover { opacity: 0.85; }
.btn-next:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-next.go {
  flex: 2;
}

/* ===== Messages ===== */
.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: auto;
  padding-bottom: 4px;
}

.message {
  max-width: 82%;
  padding: 10px 14px;
  border-radius: 14px;
  line-height: 1.6;
  font-size: 0.88rem;
  word-break: break-word;
  animation: msgIn 0.2s ease-out;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  align-self: flex-end;
  background: var(--c-accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message.assistant {
  align-self: flex-start;
  background: var(--c-surface);
  color: var(--c-text);
  border-bottom-left-radius: 4px;
}
.message.assistant.streaming::after {
  content: "";
  display: inline-block;
  width: 6px;
  height: 14px;
  background: var(--c-accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursorBlink 1s infinite;
}
@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== Progress Indicator ===== */
.progress-indicator {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--c-surface);
  border-radius: var(--radius-lg);
  font-size: 0.78rem;
  color: var(--c-text-secondary);
}
.progress-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-accent);
  animation: progPulse 1.2s ease-in-out infinite;
}
@keyframes progPulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.1); }
}

/* ===== Input Bar ===== */
.input-bar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--c-border-light);
  background: var(--c-bg);
  flex-shrink: 0;
}
.input-bar input {
  flex: 1;
  min-width: 0;
  padding: 10px 16px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s;
  background: var(--c-surface);
}
.input-bar input:focus {
  border-color: var(--c-accent);
  background: #fff;
}
.input-bar input::placeholder { color: var(--c-text-placeholder); }
.input-bar button {
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--c-accent);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}
.input-bar button:hover { opacity: 0.85; }
.input-bar button:disabled { opacity: 0.25; cursor: not-allowed; }

/* ===== Responsive ===== */
@media (max-width: 600px) {
  .app {
    max-width: 100%;
    box-shadow: none;
  }
  .header { padding: 12px 14px; }
  .header h1 { font-size: 0.95rem; }
  .content-area { padding: 16px 14px; }
  .hero { padding: 24px 8px 20px; }
  .hero h2 { font-size: 1.15rem; }
  .prompt-card { padding: 10px 12px; font-size: 0.8rem; }
  .option-grid { gap: 8px; }
  .option-card { padding: 16px 10px; }
  .message { max-width: 88%; font-size: 0.84rem; }
  .input-bar { padding: 10px 12px; gap: 6px; }
  .input-bar input { padding: 9px 14px; font-size: 0.84rem; }
}
```

- [ ] **Step 2: Commit**

```bash
git add app/static/style.css
git commit -m "feat: rewrite CSS with minimalist white design system"
```

---

### Task 2: Rewrite index.html — Vue 3 Template with Dual-Mode

**Files:**
- Modify: `app/static/index.html` (complete rewrite)

- [ ] **Step 1: Write the complete index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Travel Advisor</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌍</text></svg>">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div id="app">
  <div class="app">
    <!-- Header -->
    <header class="header">
      <h1>🌍 Travel Advisor</h1>
      <button
        v-if="currentView === 'chat'"
        class="header-btn"
        @click="goHome"
      >+ 新对话</button>
      <span v-else class="header-btn" style="border:none;cursor:default;">智能旅行助手</span>
    </header>

    <!-- Home View -->
    <div v-if="currentView === 'home'" class="content-area">
      <!-- Hero -->
      <div class="hero">
        <div class="hero-icon">🌍</div>
        <h2>发现你的完美旅行</h2>
        <p>智能推荐，一步到位</p>
      </div>

      <!-- Tab Switch -->
      <div class="tab-switch">
        <button
          class="tab"
          :class="{ active: activeMode === 'free' }"
          @click="activeMode = 'free'"
        >✏️ 自由输入</button>
        <button
          class="tab"
          :class="{ active: activeMode === 'guided' }"
          @click="activeMode = 'guided'"
        >🎯 快速选择</button>
      </div>

      <!-- Free Input Mode -->
      <div v-if="activeMode === 'free'">
        <div class="quick-prompts">
          <button
            v-for="p in quickPrompts"
            :key="p.label"
            class="prompt-card"
            @click="sendQuickPrompt(p.text)"
          >
            <span class="prompt-icon">{{ p.icon }}</span>
            <span>
              <div class="prompt-text">{{ p.label }}</div>
              <div class="prompt-desc">{{ p.desc }}</div>
            </span>
          </button>
        </div>
        <form class="input-bar" @submit.prevent="handleSend">
          <input
            type="text"
            v-model="inputText"
            placeholder="描述你的旅行偏好..."
            autocomplete="off"
            :disabled="isStreaming"
          />
          <button type="submit" :disabled="isStreaming || !inputText.trim()">发送</button>
        </form>
      </div>

      <!-- Guided Selection Mode -->
      <div v-if="activeMode === 'guided'" style="display:flex;flex-direction:column;flex:1;">
        <!-- Step Indicator -->
        <div class="step-indicator">
          <template v-for="(s, idx) in guidedSteps" :key="idx">
            <span
              class="step-dot"
              :class="{
                done: idx < currentStep,
                current: idx === currentStep,
                pending: idx > currentStep
              }"
            >{{ idx < currentStep ? '✓' : idx + 1 }}</span>
            <span v-if="idx < guidedSteps.length - 1" class="step-line" :class="{ done: idx < currentStep }"></span>
          </template>
        </div>

        <!-- Step Content -->
        <div class="step-question">{{ guidedSteps[currentStep]?.question }}</div>

        <!-- Step 0: Destination Type (grid) -->
        <div v-if="currentStep === 0" class="option-grid">
          <div
            v-for="opt in destinationTypes"
            :key="opt.value"
            class="option-card"
            :class="{ selected: selections.destination === opt.value }"
            @click="selections.destination = opt.value"
          >
            <div class="option-icon">{{ opt.icon }}</div>
            <div>{{ opt.label }}</div>
          </div>
        </div>

        <!-- Step 1: Budget & Season -->
        <div v-if="currentStep === 1">
          <div style="font-size:0.78rem;color:var(--c-text-secondary);text-align:center;margin-bottom:10px;">预算</div>
          <div class="option-chips">
            <span
              v-for="opt in budgetOptions"
              :key="opt.value"
              class="chip"
              :class="{ selected: selections.budget === opt.value }"
              @click="selections.budget = opt.value"
            >{{ opt.label }}</span>
          </div>
          <div style="font-size:0.78rem;color:var(--c-text-secondary);text-align:center;margin-bottom:10px;">季节</div>
          <div class="option-chips">
            <span
              v-for="opt in seasonOptions"
              :key="opt.value"
              class="chip"
              :class="{ selected: selections.season === opt.value }"
              @click="selections.season = opt.value"
            >{{ opt.label }}</span>
          </div>
        </div>

        <!-- Step 2: Travel Vibe -->
        <div v-if="currentStep === 2" class="option-chips" style="margin-top:8px;">
          <span
            v-for="opt in vibeOptions"
            :key="opt.value"
            class="chip"
            :class="{ selected: selections.vibe.includes(opt.value) }"
            @click="toggleVibe(opt.value)"
          >{{ opt.label }}</span>
        </div>

        <!-- Step Nav -->
        <div class="step-nav">
          <button
            v-if="currentStep > 0"
            class="btn-back"
            @click="currentStep--"
          >上一步</button>
          <button
            v-if="currentStep < 2"
            class="btn-next"
            :disabled="!canAdvance"
            @click="currentStep++"
          >下一步</button>
          <button
            v-if="currentStep === 2"
            class="btn-next go"
            @click="submitGuided"
          >✈️ 开始推荐</button>
        </div>
      </div>
    </div>

    <!-- Chat View -->
    <div v-if="currentView === 'chat'" class="content-area">
      <div class="messages">
        <template v-for="(item, idx) in messages" :key="idx">
          <div
            class="message"
            :class="[item.role, { streaming: item.streaming }]"
          >{{ item.content }}</div>
        </template>
        <div v-if="progressMsg" class="progress-indicator">
          <span class="progress-dot"></span>
          {{ progressMsg }}
        </div>
      </div>
    </div>

    <!-- Input bar (chat view only) -->
    <form v-if="currentView === 'chat'" class="input-bar" @submit.prevent="handleSend">
      <input
        type="text"
        v-model="inputText"
        placeholder="继续提问..."
        autocomplete="off"
        :disabled="isStreaming"
      />
      <button type="submit" :disabled="isStreaming || !inputText.trim()">发送</button>
    </form>
  </div>
</div>

<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
<script src="/chat.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add app/static/index.html
git commit -m "feat: rewrite HTML with Vue 3 dual-mode template (free input + guided selection)"
```

---

### Task 3: Rewrite chat.js — Vue 3 Composition API Logic

**Files:**
- Modify: `app/static/chat.js` (complete rewrite)

- [ ] **Step 1: Write the complete chat.js**

```javascript
const { createApp, ref, reactive, nextTick } = Vue;

createApp({
  setup() {
    // ---- View state ----
    const currentView = ref("home"); // "home" | "chat"
    const activeMode = ref("free");   // "free" | "guided"

    // ---- Guided selection state ----
    const currentStep = ref(0);
    const selections = reactive({
      destination: null,
      budget: null,
      season: null,
      vibe: [],
    });

    const destinationTypes = [
      { icon: "🏖️", label: "海滩度假", value: "海滩度假" },
      { icon: "🏛️", label: "文化古城", value: "文化古城" },
      { icon: "🏔️", label: "自然风光", value: "自然风光" },
      { icon: "🌆", label: "都市探索", value: "都市探索" },
    ];

    const budgetOptions = [
      { label: "经济实惠", value: "经济实惠" },
      { label: "舒适中等", value: "舒适中等" },
      { label: "奢华高端", value: "奢华高端" },
    ];

    const seasonOptions = [
      { label: "春季", value: "春季" },
      { label: "夏季", value: "夏季" },
      { label: "秋季", value: "秋季" },
      { label: "冬季", value: "冬季" },
    ];

    const vibeOptions = [
      { label: "家庭亲子", value: "家庭亲子" },
      { label: "浪漫蜜月", value: "浪漫蜜月" },
      { label: "冒险探索", value: "冒险探索" },
      { label: "美食之旅", value: "美食之旅" },
      { label: "休闲放松", value: "休闲放松" },
    ];

    const guidedSteps = [
      { question: "你想去什么类型的目的地？" },
      { question: "预算和出行季节？" },
      { question: "有什么特别偏好？（可多选）" },
    ];

    const canAdvance = ref(false);

    function checkCanAdvance() {
      if (currentStep.value === 0) canAdvance.value = !!selections.destination;
      else if (currentStep.value === 1)
        canAdvance.value = !!(selections.budget && selections.season);
      else canAdvance.value = true; // step 2 is optional
    }

    function toggleVibe(val) {
      const idx = selections.vibe.indexOf(val);
      if (idx >= 0) selections.vibe.splice(idx, 1);
      else selections.vibe.push(val);
    }

    function buildGuidedMessage() {
      let msg = `推荐一个${selections.season || ""}的${selections.destination || ""}目的地`;
      if (selections.budget) msg += `，预算${selections.budget}`;
      if (selections.vibe.length) msg += `，偏好${selections.vibe.join("、")}`;
      return msg;
    }

    async function submitGuided() {
      const msg = buildGuidedMessage();
      currentView.value = "home";
      await nextTick();
      inputText.value = msg;
      handleSend();
    }

    // ---- Quick prompts ----
    const quickPrompts = [
      {
        icon: "🏖️",
        label: "冬季海滩度假",
        desc: "12月出发，预算中等",
        text: "推荐一个12月的海滩度假目的地，预算中等",
      },
      {
        icon: "🏛️",
        label: "文化古城穷游",
        desc: "预算有限，3-4天深度游",
        text: "我预算有限，想去有文化底蕴的古城，3-4天",
      },
      {
        icon: "💑",
        label: "蜜月浪漫之旅",
        desc: "奢华体验，难忘回忆",
        text: "推荐适合蜜月的浪漫目的地，奢华体验",
      },
      {
        icon: "👨‍👩‍👧",
        label: "家庭自然之旅",
        desc: "带孩子感受大自然",
        text: "我想带家人去自然风光好的地方，有哪些推荐？",
      },
    ];

    // ---- Chat state ----
    const messages = reactive([]);
    const inputText = ref("");
    const isStreaming = ref(false);
    const progressMsg = ref(null);

    let sessionId = sessionStorage.getItem("travel_session_id") || null;

    const toolProgressMap = {
      search_destinations: "正在搜索目的地...",
      get_hotels: "正在查找酒店...",
      get_attractions: "正在搜索景点...",
      get_weather: "正在查询天气...",
      get_travel_tips: "正在获取旅行贴士...",
    };

    function scrollToBottom() {
      nextTick(() => {
        const el = document.querySelector(".content-area");
        if (el) el.scrollTop = el.scrollHeight;
      });
    }

    function goHome() {
      currentView.value = "home";
      messages.length = 0;
      activeMode.value = "free";
      resetGuided();
      progressMsg.value = null;
    }

    function resetGuided() {
      currentStep.value = 0;
      selections.destination = null;
      selections.budget = null;
      selections.season = null;
      selections.vibe = [];
      canAdvance.value = false;
    }

    function sendQuickPrompt(text) {
      inputText.value = text;
      handleSend();
    }

    async function handleSend() {
      const text = inputText.value.trim();
      if (!text || isStreaming.value) return;

      inputText.value = "";
      currentView.value = "chat";
      messages.push({ role: "user", content: text });
      scrollToBottom();

      isStreaming.value = true;

      const assistantMsg = reactive({
        role: "assistant",
        content: "",
        streaming: true,
      });
      messages.push(assistantMsg);

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, session_id: sessionId }),
        });

        const respSessionId = response.headers.get("X-Session-Id");
        if (respSessionId) {
          sessionId = respSessionId;
          sessionStorage.setItem("travel_session_id", sessionId);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith("data: ")) continue;
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case "tool_call": {
                progressMsg.value = toolProgressMap[data.name] || "正在查询...";
                scrollToBottom();
                break;
              }
              case "tool_result": {
                progressMsg.value = null;
                break;
              }
              case "content": {
                progressMsg.value = null;
                assistantMsg.content += data.content;
                scrollToBottom();
                break;
              }
              case "done": {
                assistantMsg.streaming = false;
                break;
              }
            }
          }
        }
      } catch (err) {
        assistantMsg.content = "抱歉，连接出错了。请重试。";
        assistantMsg.streaming = false;
        console.error("Stream error:", err);
      } finally {
        isStreaming.value = false;
        progressMsg.value = null;
      }
    }

    // Watch step changes and validate
    const { watch } = Vue;
    watch(currentStep, () => checkCanAdvance());
    watch(
      () => [selections.destination, selections.budget, selections.season],
      () => checkCanAdvance(),
      { deep: true }
    );

    return {
      currentView,
      activeMode,
      currentStep,
      selections,
      destinationTypes,
      budgetOptions,
      seasonOptions,
      vibeOptions,
      guidedSteps,
      canAdvance,
      toggleVibe,
      submitGuided,
      quickPrompts,
      messages,
      inputText,
      isStreaming,
      progressMsg,
      goHome,
      sendQuickPrompt,
      handleSend,
    };
  },
}).mount("#app");
```

- [ ] **Step 2: Commit**

```bash
git add app/static/chat.js
git commit -m "feat: rewrite chat.js with Vue 3 dual-mode logic and guided selection"
```

---

### Task 4: Verify the Frontend Works

**Files:** None modified. Backend unchanged.

- [ ] **Step 1: Start the FastAPI server**

```bash
cd /Users/xy/Workspace/project/travel-agent && source .venv/bin/activate && cd app && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Start the server and open `http://localhost:8000` in the browser. Verify:
- Home page loads with minimalist white design
- Tab switch works (free input ↔ quick selection)
- Quick prompt cards are clickable and send messages
- Guided mode: 3-step selection works, "开始推荐" submits
- Chat view shows messages with streaming
- "新对话" button returns to home
- Responsive layout at <600px

- [ ] **Step 2: Commit any fixes if needed**

```bash
git add app/static/ && git commit -m "fix: frontend polish after visual verification"
```
