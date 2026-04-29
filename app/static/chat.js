const { createApp, ref, reactive, nextTick, onMounted } = Vue;

createApp({
  setup() {
    const messages = reactive([]);
    const inputText = ref("");
    const isStreaming = ref(false);
    const chatContainer = ref(null);

    let sessionId = sessionStorage.getItem("travel_session_id") || null;

    const quickPrompts = [
      { label: "🏖️ 冬季海滩度假", text: "推荐一个12月的海滩度假目的地，预算中等" },
      { label: "🏛️ 文化古城穷游", text: "我预算有限，想去有文化底蕴的古城，3-4天" },
      { label: "💑 蜜月浪漫之旅", text: "推荐适合蜜月的浪漫目的地，奢华体验" },
      { label: "🏔️ 家庭自然之旅", text: "我想带家人去自然风光好的地方，有哪些推荐？" },
    ];

    const toolIcons = {
      search_destinations: "🔍",
      get_hotels: "🏨",
      get_attractions: "🎯",
      get_weather: "🌤️",
      get_travel_tips: "📋",
    };

    function getToolIcon(name) {
      return toolIcons[name] || "🔧";
    }

    function scrollToBottom() {
      nextTick(() => {
        const el = chatContainer.value;
        if (el) el.scrollTop = el.scrollHeight;
      });
    }

    function sendQuickPrompt(text) {
      inputText.value = text;
      handleSend();
    }

    async function handleSend() {
      const text = inputText.value.trim();
      if (!text || isStreaming.value) return;

      inputText.value = "";
      messages.push({ role: "user", content: text });
      scrollToBottom();

      isStreaming.value = true;

      const assistantMsg = reactive({
        role: "assistant",
        content: "",
        streaming: true,
      });
      messages.push(assistantMsg);

      const toolIndexes = []; // track tool event positions in messages

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
                const toolMsg = reactive({
                  role: "tool",
                  toolName: data.name,
                  content: "正在查询...",
                  done: false,
                });
                const idx = messages.length;
                messages.push(toolMsg);
                toolIndexes.push(idx);
                scrollToBottom();
                break;
              }
              case "tool_result": {
                const idx = toolIndexes.shift();
                if (idx !== undefined && messages[idx]) {
                  messages[idx].content = data.result_preview;
                  messages[idx].done = true;
                }
                break;
              }
              case "content": {
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
      }
    }

    return {
      messages,
      inputText,
      isStreaming,
      chatContainer,
      quickPrompts,
      getToolIcon,
      sendQuickPrompt,
      handleSend,
    };
  },
}).mount("#app");
