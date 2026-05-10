import { defineStore } from 'pinia'
import { ref, reactive, nextTick } from 'vue'
import apiClient from '@/api/client'
import type { ChatMessage, SessionSummary, SSEEvent, Message } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // ---- State ----
  const sessions = ref<SessionSummary[]>([])
  const activeSessionId = ref<string | null>(localStorage.getItem('active_session'))
  const messages = reactive<ChatMessage[]>([])
  const inputText = ref('')
  const isStreaming = ref(false)
  const progressMsg = ref('')
  const sidebarOpen = ref(false)

  // ---- Session Management ----

  async function loadSessions() {
    try {
      const { data } = await apiClient.get('/sessions', { params: { limit: 50 } })
      sessions.value = data.sessions
    } catch { /* silently fail */ }
  }

  async function createSession(title = 'New Trip') {
    const { data } = await apiClient.post('/sessions', { title })
    sessions.value.unshift(data)
    return data.id
  }

  async function loadSessionHistory(sessionId: string) {
    try {
      const { data } = await apiClient.get(`/sessions/${sessionId}`)
      messages.length = 0
      for (const msg of data.messages) {
        messages.push({ role: msg.role as 'user' | 'assistant', content: msg.content })
      }
    } catch { /* expired or not found */ }
  }

  // ---- Chat Flow ----

  async function switchSession(sessionId: string) {
    activeSessionId.value = sessionId
    localStorage.setItem('active_session', sessionId)
    messages.length = 0
    await loadSessionHistory(sessionId)
  }

  function newChat() {
    activeSessionId.value = null
    localStorage.removeItem('active_session')
    messages.length = 0
    isStreaming.value = false
    progressMsg.value = ''
  }

  async function sendMessage(text: string) {
    if (!text.trim() || isStreaming.value) return

    inputText.value = ''

    // Add user message to display
    messages.push({ role: 'user', content: text })

    // Create session if needed
    if (!activeSessionId.value) {
      const sid = await createSession(text.slice(0, 30))
      activeSessionId.value = sid
      localStorage.setItem('active_session', sid)
    }

    isStreaming.value = true
    progressMsg.value = ''

    // Add assistant placeholder
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', streaming: true }
    messages.push(assistantMsg)

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          session_id: activeSessionId.value,
          message: text,
          stream: true,
        }),
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE frames: "event: <type>\ndata: <json>\n\n"
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let eventType = ''
          let dataStr = ''

          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataStr = line.slice(6).trim()
          }

          if (!dataStr) continue
          let data: any
          try { data = JSON.parse(dataStr) } catch { continue }

          switch (eventType) {
            case 'status':
              progressMsg.value = data.msg || ''
              break
            case 'tool_call':
              progressMsg.value = `🔍 ${data.query || '搜索中...'}`
              break
            case 'content':
              progressMsg.value = ''
              assistantMsg.content += data.text || ''
              await nextTick()
              scrollToBottom()
              break
            case 'error':
              assistantMsg.content += `\n\n> ⚠️ ${data.msg || '出错了'}`
              break
            case 'done':
              assistantMsg.streaming = false
              if (data.session_id) {
                activeSessionId.value = data.session_id
              }
              await loadSessions()
              break
          }
        }
      }
    } catch (err: any) {
      assistantMsg.content = '抱歉，连接出错了。请重试。'
      assistantMsg.streaming = false
    } finally {
      isStreaming.value = false
      progressMsg.value = ''
    }
  }

  function scrollToBottom() {
    nextTick(() => {
      const el = document.querySelector('.chat-messages')
      if (el) el.scrollTop = el.scrollHeight
    })
  }

  return {
    sessions,
    activeSessionId,
    messages,
    inputText,
    isStreaming,
    progressMsg,
    sidebarOpen,
    loadSessions,
    createSession,
    loadSessionHistory,
    switchSession,
    newChat,
    sendMessage,
  }
})
