(function () {
  const messagesEl = document.getElementById("messages");
  const welcomeEl = document.getElementById("welcome");
  const form = document.getElementById("inputForm");
  const input = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");

  let sessionId = sessionStorage.getItem("travel_session_id") || null;
  let isStreaming = false;

  // ---- Quick prompt chips ----
  document.querySelectorAll(".prompt-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      input.value = chip.dataset.prompt;
      form.dispatchEvent(new Event("submit"));
    });
  });

  // ---- Form submit ----
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || isStreaming) return;
    input.value = "";
    welcomeEl.style.display = "none";
    appendMessage("user", text);
    await sendMessage(text);
  });

  async function sendMessage(text) {
    isStreaming = true;
    sendBtn.disabled = true;
    input.disabled = true;

    const assistantEl = appendMessage("assistant", "", true);
    const toolEvents = [];

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      // Read X-Session-Id header
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
          handleSSEEvent(data, assistantEl, toolEvents);
        }
      }
    } catch (err) {
      assistantEl.textContent = "抱歉，连接出错了。请重试。";
      assistantEl.classList.remove("streaming");
      console.error("Stream error:", err);
    } finally {
      isStreaming = false;
      sendBtn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  function handleSSEEvent(data, assistantEl, toolEvents) {
    switch (data.type) {
      case "tool_call": {
        const el = document.createElement("div");
        el.className = "tool-event";
        const iconMap = {
          search_destinations: "🔍",
          get_hotels: "🏨",
          get_attractions: "🎯",
          get_weather: "🌤️",
          get_travel_tips: "📋",
        };
        el.innerHTML = `<span class="icon">${iconMap[data.name] || "🔧"}</span> 正在查询...`;
        messagesEl.appendChild(el);
        toolEvents.push({ el, name: data.name });
        scrollToBottom();
        break;
      }
      case "tool_result": {
        const last = toolEvents[toolEvents.length - 1];
        if (last) {
          last.el.classList.add("result");
          last.el.textContent = `✅ ${data.result_preview}`;
        }
        break;
      }
      case "content": {
        assistantEl.textContent += data.content;
        scrollToBottom();
        break;
      }
      case "done": {
        assistantEl.classList.remove("streaming");
        break;
      }
    }
  }

  function appendMessage(role, content, streaming) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    if (streaming) el.classList.add("streaming");
    el.textContent = content;
    messagesEl.appendChild(el);
    scrollToBottom();
    return el;
  }

  function scrollToBottom() {
    const container = document.querySelector(".chat-container");
    container.scrollTop = container.scrollHeight;
  }
})();
