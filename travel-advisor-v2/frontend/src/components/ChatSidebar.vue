<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()
const { sessions, activeSessionId } = storeToRefs(chat)

function formatTime(ts: string) {
  const d = new Date(ts)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`
}
</script>

<template>
  <aside class="w-[260px] flex-shrink-0 border-r border-gray-100 bg-surface flex flex-col">
    <div class="px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
      对话历史
    </div>

    <div class="flex-1 overflow-y-auto">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="flex items-center justify-between px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-surface-hover transition-colors"
        :class="{ 'bg-white': s.id === activeSessionId }"
        @click="chat.switchSession(s.id)"
      >
        <div class="min-w-0 flex-1">
          <div class="text-sm text-gray-900 truncate">{{ s.title }}</div>
          <div class="text-xs text-gray-400 mt-0.5">
            {{ s.msg_count }} 条消息 · {{ formatTime(s.updated_at) }}
          </div>
        </div>
      </div>
      <div v-if="sessions.length === 0" class="px-4 py-8 text-center text-sm text-gray-400">
        暂无历史对话
      </div>
    </div>

    <button
      class="mx-3 mb-3 py-2.5 border border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-accent hover:text-accent transition-colors"
      @click="chat.newChat()"
    >
      + 新对话
    </button>
  </aside>
</template>
