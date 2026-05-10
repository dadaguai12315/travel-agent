// ---- API Types ----

export interface User {
  id: string
  email: string
  display_name: string
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface SessionSummary {
  id: string
  title: string
  status: string
  msg_count: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  token_count: number
  created_at: string
}

export interface SessionDetail {
  id: string
  title: string
  status: string
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

// ---- SSE Event Types ----

export interface SSEEvent {
  event: 'status' | 'tool_call' | 'content' | 'error' | 'done'
  data: {
    msg?: string
    tool?: string
    query?: string
    text?: string
    code?: number
    session_id?: string
    usage?: { tokens?: number; elapsed_seconds?: number }
  }
}
