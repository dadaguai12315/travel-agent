const { createApp, ref, reactive, nextTick, watch, onMounted } = Vue;

const CONVERSATIONS_KEY = "travel_conversations";
const ACTIVE_SESSION_KEY = "travel_active_session";

createApp({
  setup() {
    // ---- Persistent conversation list (localStorage) ----
    function loadConversations() {
      try {
        return JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || "[]");
      } catch { return []; }
    }
    function saveConversations() {
      localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
    }
    function addConversation(id, title) {
      if (conversations.find(c => c.id === id)) return;
      conversations.unshift({
        id,
        title: title || "新对话",
        timestamp: Date.now(),
        msgCount: 0,
      });
      saveConversations();
    }
    function updateConversation(id, updates) {
      const conv = conversations.find(c => c.id === id);
      if (!conv) return;
      Object.assign(conv, updates);
      conv.timestamp = Date.now();
      saveConversations();
    }
    function removeConversation(id) {
      const idx = conversations.findIndex(c => c.id === id);
      if (idx >= 0) {
        conversations.splice(idx, 1);
        saveConversations();
      }
    }
    function formatTime(ts) {
      const d = new Date(ts);
      const now = new Date();
      const isToday = d.toDateString() === now.toDateString();
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      if (isToday) return `${hh}:${mm}`;
      return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`;
    }

    // Markdown rendering (uses global `marked` from CDN)
    function renderMarkdown(text) {
      if (!text) return "";
      if (typeof marked === "undefined") return escapeHtml(text);
      try {
        const html = marked.parse(text, { breaks: true, gfm: true });
        return html;
      } catch {
        return escapeHtml(text);
      }
    }
    function escapeHtml(str) {
      const div = document.createElement("div");
      div.textContent = str;
      return div.innerHTML;
    }

    // ---- View state ----
    const currentView = ref("home");
    const activeMode = ref("free");
    const activeSessionId = ref(localStorage.getItem(ACTIVE_SESSION_KEY) || null);
    const conversations = reactive(loadConversations());
    const sidebarOpen = ref(false);

    function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value; }
    function closeSidebar() { sidebarOpen.value = false; }

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

    // ---- Validation ----
    const canAdvance = ref(false);

    function checkCanAdvance() {
      if (currentStep.value === 0) canAdvance.value = !!selections.destination;
      else if (currentStep.value === 1)
        canAdvance.value = !!(selections.budget && selections.season);
      else canAdvance.value = true;
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
      inputText.value = msg;
      await nextTick();
      handleSend();
    }

    // ---- Quick prompts ----
    const quickPrompts = [
      { icon: "🏖️", label: "冬季海滩度假", desc: "12月出发，预算中等", text: "推荐一个12月的海滩度假目的地，预算中等" },
      { icon: "🏛️", label: "文化古城穷游", desc: "预算有限，3-4天深度游", text: "我预算有限，想去有文化底蕴的古城，3-4天" },
      { icon: "💑", label: "蜜月浪漫之旅", desc: "奢华体验，难忘回忆", text: "推荐适合蜜月的浪漫目的地，奢华体验" },
      { icon: "👨‍👩‍👧", label: "家庭自然之旅", desc: "带孩子感受大自然", text: "我想带家人去自然风光好的地方，有哪些推荐？" },
    ];

    // ---- Chat state (display layer — points to active session) ----
    const messages = reactive([]);
    const inputText = ref("");
    const isStreaming = ref(false);
    const progressMsg = ref(null);

    // Per-session storage for background streaming
    const sessionStore = {}; // {sid: {messages: [], controller: AbortController|null}}
    function getStore(sid) {
      if (!sessionStore[sid]) {
        sessionStore[sid] = { messages: [], controller: null };
      }
      return sessionStore[sid];
    }
    function stashSession() {
      if (!activeSessionId.value) return;
      const store = getStore(activeSessionId.value);
      store.messages = messages.slice(); // shallow copy — shares message objects
      store.controller = messages._controller || null;
      store.isStreaming = isStreaming.value;
    }
    function unstashSession(sid) {
      const store = getStore(sid);
      messages.length = 0;
      messages.push(...store.messages);
      messages._controller = store.controller;
      const alive = store.controller && !store.controller.signal.aborted;
      isStreaming.value = alive;
      progressMsg.value = null;
    }

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
      // Save current session state (keep stream running in background)
      stashSession();
      if (activeSessionId.value) {
        updateConversation(activeSessionId.value, { msgCount: messages.length });
      }
      activeSessionId.value = null;
      localStorage.removeItem(ACTIVE_SESSION_KEY);
      currentView.value = "home";
      messages.length = 0;
      activeMode.value = "free";
      resetGuided();
      isStreaming.value = false;
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

    async function switchConversation(sid) {
      // Save current session (keep its stream running in background)
      stashSession();
      if (activeSessionId.value && activeSessionId.value !== sid) {
        updateConversation(activeSessionId.value, { msgCount: getStore(activeSessionId.value).messages.length });
      }

      activeSessionId.value = sid;
      localStorage.setItem(ACTIVE_SESSION_KEY, sid);
      messages.length = 0;
      currentView.value = "chat";
      closeSidebar();

      // Restore from local store if available
      const store = getStore(sid);
      if (store.messages.length > 0) {
        unstashSession(sid);
        await nextTick();
        scrollToBottom();
        return;
      }

      // Fetch from API
      try {
        const resp = await fetch(`/api/sessions/${sid}`);
        if (resp.ok) {
          const data = await resp.json();
          for (const msg of data.history) {
            messages.push({ role: msg.role, content: msg.content });
          }
          store.messages = messages.slice();
        }
        await nextTick();
        scrollToBottom();
      } catch {
        // Network error — stay in chat view with empty messages
      }
    }

    async function deleteConversation(sid) {
      // Abort the stream for this session if running
      const store = getStore(sid);
      if (store.controller && !store.controller.signal.aborted) {
        store.controller.abort();
      }
      delete sessionStore[sid];
      removeConversation(sid);
      fetch(`/api/sessions/${sid}`, { method: "DELETE" }).catch(() => {});
      if (activeSessionId.value === sid) {
        goHome();
      }
    }

    function sendQuickPrompt(text) {
      if (isStreaming.value) return;
      inputText.value = text;
      handleSend();
    }

    async function handleSend() {
      const text = inputText.value.trim();
      if (!text || isStreaming.value) return;

      inputText.value = "";
      const isNewSession = !activeSessionId.value;
      // Capture the session this stream belongs to
      const streamSid = activeSessionId.value;

      currentView.value = "chat";
      messages.push({ role: "user", content: text });
      scrollToBottom();

      isStreaming.value = true;
      const controller = new AbortController();
      messages._controller = controller;
      // Save controller to session store so it survives switching
      if (streamSid) {
        getStore(streamSid).controller = controller;
      }

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
          body: JSON.stringify({
            message: text,
            session_id: streamSid || null,
          }),
          signal: controller.signal,
        });

        const respSessionId = response.headers.get("X-Session-Id");
        if (respSessionId) {
          // Always update the store for the real session ID
          if (respSessionId !== activeSessionId.value) {
            activeSessionId.value = respSessionId;
            localStorage.setItem(ACTIVE_SESSION_KEY, respSessionId);
          }
          if (isNewSession || !conversations.find(c => c.id === respSessionId)) {
            addConversation(respSessionId, text.slice(0, 30));
          }
        }

        if (!response.body) throw new Error("No response body");
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
            let data;
            try { data = JSON.parse(line.slice(6)); } catch { continue; }

            const isActive = activeSessionId.value === respSessionId;

            switch (data.type) {
              case "tool_call": {
                if (isActive) {
                  progressMsg.value = toolProgressMap[data.name] || "正在查询...";
                  scrollToBottom();
                }
                break;
              }
              case "tool_result": {
                if (isActive) progressMsg.value = null;
                break;
              }
              case "content": {
                if (isActive) progressMsg.value = null;
                // Always update the shared assistantMsg object
                // (it persists in sessionStore even when not active)
                assistantMsg.content += data.content;
                if (isActive) scrollToBottom();
                break;
              }
              case "done": {
                assistantMsg.streaming = false;
                const realSid = respSessionId || activeSessionId.value;
                if (realSid) {
                  const store = getStore(realSid);
                  store.messages = isActive ? messages.slice() : store.messages;
                  store.isStreaming = false;
                  updateConversation(realSid, {
                    title: text.slice(0, 30),
                    msgCount: isActive ? messages.length : store.messages.length,
                  });
                }
                if (isActive) {
                  isStreaming.value = false;
                  progressMsg.value = null;
                }
                break;
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          assistantMsg.content = "抱歉，连接出错了。请重试。";
          assistantMsg.streaming = false;
          console.error("Stream error:", err);
        }
      } finally {
        // Only update display state if this session is still active
        if (activeSessionId.value === respSessionId) {
          isStreaming.value = false;
          progressMsg.value = null;
        }
        if (respSessionId) {
          const store = getStore(respSessionId);
          store.controller = null;
          store.isStreaming = false;
        }
      }
    }

    // Watch step changes and validate
    watch(currentStep, () => checkCanAdvance());
    watch(
      () => [selections.destination, selections.budget, selections.season],
      () => checkCanAdvance()
    );

    // Restore active session on mount
    onMounted(async () => {
      if (activeSessionId.value) {
        try {
          const resp = await fetch(`/api/sessions/${activeSessionId.value}`);
          if (resp.ok) {
            const data = await resp.json();
            for (const msg of data.history) {
              messages.push({ role: msg.role, content: msg.content });
            }
            const store = getStore(activeSessionId.value);
            store.messages = messages.slice();
            currentView.value = "chat";
            await nextTick();
            scrollToBottom();
            return;
          }
        } catch { /* session expired or network error, show home */ }
      }
      activeSessionId.value = null;
      localStorage.removeItem(ACTIVE_SESSION_KEY);
    });

    return {
      currentView,
      activeMode,
      activeSessionId,
      conversations,
      sidebarOpen,
      toggleSidebar,
      closeSidebar,
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
      switchConversation,
      deleteConversation,
      sendQuickPrompt,
      handleSend,
      formatTime,
      renderMarkdown,
    };
  },
}).mount("#app");
