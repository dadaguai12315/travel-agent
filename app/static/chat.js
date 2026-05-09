const { createApp, ref, reactive, nextTick, watch } = Vue;

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

    // ---- Validation ----
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
      inputText.value = msg;
      await nextTick();
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
    let streamAbortController = null;

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
      if (streamAbortController) {
        streamAbortController.abort();
        streamAbortController = null;
      }
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
      if (isStreaming.value) return;
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
      streamAbortController = new AbortController();

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
          signal: streamAbortController.signal,
        });

        const respSessionId = response.headers.get("X-Session-Id");
        if (respSessionId) {
          sessionId = respSessionId;
          sessionStorage.setItem("travel_session_id", sessionId);
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
            try {
              data = JSON.parse(line.slice(6));
            } catch {
              continue;
            }

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
        if (err.name !== "AbortError") {
          assistantMsg.content = "抱歉，连接出错了。请重试。";
          assistantMsg.streaming = false;
          console.error("Stream error:", err);
        }
      } finally {
        isStreaming.value = false;
        progressMsg.value = null;
        streamAbortController = null;
      }
    }

    // Watch step changes and validate
    watch(currentStep, () => checkCanAdvance());
    watch(
      () => [selections.destination, selections.budget, selections.season],
      () => checkCanAdvance()
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
