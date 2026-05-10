import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import apiClient from '@/api/client'
import type { ChatMessage, SessionSummary } from '@/types'

// Per-session storage for background streaming
interface SessionData {
  messages: ChatMessage[]
  controller: AbortController | null
}

export const useChatStore = defineStore('chat', () => {
  // ---- State ----
  const sessions = ref<SessionSummary[]>([])
  const activeSessionId = ref<string | null>(localStorage.getItem('active_session'))
  const messages = reactive<ChatMessage[]>([])
  const inputText = ref('')
  const isStreaming = ref(false)
  const progressMsg = ref('')
  const sidebarOpen = ref(false)

  // Per-session storage: { sid: { messages, controller } }
  const store: Record<string, SessionData> = {}

  function getStore(sid: string): SessionData {
    if (!store[sid]) store[sid] = { messages: [], controller: null }
    return store[sid]
  }

  // Save current display to session store
  function stash() {
    if (!activeSessionId.value) return
    const s = getStore(activeSessionId.value)
    s.messages = messages.slice()
  }

  // Load session store to display
  function unstash(sid: string) {
    const s = getStore(sid)
    messages.length = 0
    messages.push(...s.messages)
    isStreaming.value = !!(s.controller && !s.controller.signal.aborted)
    progressMsg.value = ''
  }

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

  async function deleteSession(sessionId: string) {
    // Abort stream if active
    const s = getStore(sessionId)
    if (s.controller && !s.controller.signal.aborted) {
      s.controller.abort()
    }
    delete store[sessionId]
    await apiClient.delete(`/sessions/${sessionId}`).catch(() => {})
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (activeSessionId.value === sessionId) {
      newChat()
    }
  }

  async function generateTitle(sessionId: string) {
    // Only generate title if it's still the default
    const session = sessions.value.find(s => s.id === sessionId)
    if (!session || session.title !== session.title) return

    try {
      const { data } = await apiClient.patch(`/sessions/${sessionId}`, {
        title: session.title,  // Keep current title — generation happens below via the backend
      })
      // Update local state
      const idx = sessions.value.findIndex(s => s.id === sessionId)
      if (idx >= 0) sessions.value[idx].title = data.title
    } catch { /* ignore */ }
  }

  async function loadSessionHistory(sessionId: string) {
    try {
      const { data } = await apiClient.get(`/sessions/${sessionId}`)
      const msgs: ChatMessage[] = data.messages.map((m: any) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }))
      // Update both display and store
      messages.length = 0
      messages.push(...msgs)
      getStore(sessionId).messages = msgs
    } catch { /* expired */ }
  }

  // ---- Chat Flow ----

  async function switchSession(sessionId: string) {
    if (activeSessionId.value === sessionId) return
    // Save current display (keep stream running in background)
    stash()

    activeSessionId.value = sessionId
    localStorage.setItem('active_session', sessionId)

    // Restore from local store if available, else fetch from API
    const s = getStore(sessionId)
    if (s.messages.length > 0) {
      unstash(sessionId)
      return
    }
    await loadSessionHistory(sessionId)
    unstash(sessionId)
  }

  function newChat() {
    // Save current session (keep its stream running!)
    stash()
    activeSessionId.value = null
    localStorage.removeItem('active_session')
    messages.length = 0
    isStreaming.value = false
    progressMsg.value = ''
  }

  async function sendMessage(text: string) {
    if (!text.trim() || isStreaming.value) return

    inputText.value = ''
    const streamSid = activeSessionId.value

    // Add user message
    messages.push({ role: 'user', content: text })

    // Create session if needed
    if (!streamSid) {
      const sid = await createSession(text.slice(0, 30))
      activeSessionId.value = sid
      localStorage.setItem('active_session', sid)
    }

    const currentSid = activeSessionId.value
    isStreaming.value = true
    progressMsg.value = ''

    // Add assistant placeholder (reactive — mutations trigger re-render)
    const assistantMsg = reactive<ChatMessage>({ role: 'assistant', content: '', streaming: true })
    messages.push(assistantMsg)

    const controller = new AbortController()
    getStore(currentSid).controller = controller

    // Throttle: batch content updates to avoid blocking main thread
    let contentBuffer = ''
    let flushTimer: ReturnType<typeof setTimeout> | null = null

    function flushContent() {
      if (contentBuffer) {
        assistantMsg.content += contentBuffer
        contentBuffer = ''
      }
      flushTimer = null
      if (activeSessionId.value === currentSid) {
        progressMsg.value = ''
        scrollToBottom()
      }
    }

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          session_id: currentSid,
          message: text,
          stream: true,
        }),
        signal: controller.signal,
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

          const isActive = activeSessionId.value === currentSid

          switch (eventType) {
            case 'status':
              if (isActive) progressMsg.value = data.msg || ''
              break
            case 'tool_call':
              if (isActive) progressMsg.value = `🔍 ${data.query || '搜索中...'}`
              break
            case 'content':
              contentBuffer += data.text || ''
              if (!flushTimer) {
                flushTimer = setTimeout(flushContent, 33) // 30FPS (Rule 5)
              }
              break
            case 'error':
              assistantMsg.content += `\n\n> ⚠️ ${data.msg || '出错了'}`
              break
            case 'done':
              // Flush remaining buffered content
              if (flushTimer) { clearTimeout(flushTimer); flushTimer = null }
              flushContent()
              assistantMsg.streaming = false
              const s = getStore(currentSid)
              s.messages = isActive ? messages.slice() : s.messages
              s.controller = null
              if (isActive) {
                isStreaming.value = false
                progressMsg.value = ''
              }
              await loadSessions()
              break
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        assistantMsg.content = '抱歉，连接出错了。请重试。'
        assistantMsg.streaming = false
      }
    } finally {
      if (flushTimer) { clearTimeout(flushTimer); flushTimer = null }
      flushContent()
      getStore(currentSid).controller = null
      if (activeSessionId.value === currentSid) {
        isStreaming.value = false
        progressMsg.value = ''
      }
    }
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      const el = document.querySelector('.chat-messages') as HTMLElement | null
      if (!el) return
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight
      if (dist < 150) {
        el.scrollTop = el.scrollHeight
      }
    })
  }

  return {
    sessions, activeSessionId, messages, inputText,
    isStreaming, progressMsg, sidebarOpen,
    loadSessions, createSession, loadSessionHistory,
    switchSession, newChat, deleteSession, sendMessage,
  }
})
