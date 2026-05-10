<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()
const { sessions, activeSessionId } = storeToRefs(chat)

const collapsed = ref(false)
const width = ref(Number(localStorage.getItem('sidebar_width') || 260))
const isDragging = ref(false)

function formatTime(ts: string) {
  const d = new Date(ts)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`
}

async function handleDelete(sid: string, event: Event) {
  event.stopPropagation()
  if (!confirm('确定删除这个对话？')) return
  try { await chat.deleteSession(sid) } catch { /* ignore */ }
}

// ---- Resize ----
function onDragStart(e: MouseEvent) {
  e.preventDefault()
  isDragging.value = true
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e: MouseEvent) {
  if (!isDragging.value) return
  const w = Math.max(180, Math.min(500, e.clientX))
  width.value = w
}

function onDragEnd() {
  isDragging.value = false
  localStorage.setItem('sidebar_width', String(width.value))
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<template>
  <aside
    class="relative flex-shrink-0 border-r border-gray-100 dark:border-gray-800 bg-surface dark:bg-gray-800 flex flex-col overflow-hidden"
    :class="{ 'transition-[width] duration-200': !isDragging }"
    :style="{ width: collapsed ? '48px' : width + 'px' }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-3 border-b border-gray-100 dark:border-gray-700 flex-shrink-0">
      <span v-if="!collapsed" class="text-xs font-semibold text-gray-400 uppercase tracking-wider">对话历史</span>
      <button
        class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex-shrink-0"
        :class="{ 'mx-auto': collapsed }"
        @click="collapsed = !collapsed"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <svg v-if="collapsed" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
    </div>

    <!-- Session list -->
    <div v-if="!collapsed" class="flex-1 overflow-y-auto">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="group flex items-center justify-between px-4 py-3 cursor-pointer border-b border-gray-100 dark:border-gray-700 hover:bg-surface-hover dark:hover:bg-gray-700 transition-colors"
        :class="{ 'bg-white dark:bg-gray-900': s.id === activeSessionId }"
        @click="chat.switchSession(s.id)"
      >
        <div class="min-w-0 flex-1">
          <div class="text-sm text-gray-900 dark:text-gray-100 truncate">{{ s.title }}</div>
          <div class="text-xs text-gray-400 mt-0.5">
            {{ s.msg_count }} 条消息 · {{ formatTime(s.updated_at) }}
          </div>
        </div>
        <button
          class="ml-2 w-6 h-6 flex items-center justify-center rounded text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
          @click="handleDelete(s.id, $event)"
          title="删除"
        >×</button>
      </div>
      <div v-if="sessions.length === 0" class="px-4 py-8 text-center text-sm text-gray-400">
        暂无历史对话
      </div>
    </div>

    <!-- New chat button -->
    <button
      v-if="!collapsed"
      class="mx-3 mb-3 py-2.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:border-accent dark:hover:border-gray-400 hover:text-accent dark:hover:text-gray-200 transition-colors"
      @click="chat.newChat()"
    >+ 新对话</button>

    <!-- Resize handle -->
    <div
      class="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-accent/20 dark:hover:bg-white/10 transition-colors z-10"
      :class="{ 'bg-accent/30 dark:bg-white/20': isDragging }"
      @mousedown="onDragStart"
    ></div>
  </aside>
</template>
