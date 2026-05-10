<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()
const { messages, isStreaming, progressMsg, activeSessionId } = storeToRefs(chat)
const menuOpen = ref(false)
const isDark = ref(localStorage.getItem('theme') === 'dark')

function applyTheme() {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
applyTheme() // Apply on mount

function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme()
}

function toggleMenu() { menuOpen.value = !menuOpen.value }
function logout() {
  auth.logout()
  router.push('/login')
}

const quickPrompts = [
  { icon: '🏖️', label: '冬季海滩度假', text: '推荐一个12月的海滩度假目的地，预算中等' },
  { icon: '🏛️', label: '文化古城穷游', text: '我预算有限，想去有文化底蕴的古城，3-4天' },
  { icon: '💑', label: '蜜月浪漫之旅', text: '推荐适合蜜月的浪漫目的地，奢华体验' },
  { icon: '👨‍👩‍👧', label: '家庭自然之旅', text: '我想带家人去自然风光好的地方，有哪些推荐？' },
]

onMounted(async () => {
  await chat.loadSessions()
  if (activeSessionId.value) {
    await chat.loadSessionHistory(activeSessionId.value)
  }
})
</script>

<template>
  <div class="flex h-screen w-full bg-white dark:bg-gray-900">
    <!-- Sidebar -->
    <ChatSidebar />

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="flex items-center justify-between px-5 py-3 border-b border-gray-100 flex-shrink-0">
        <h1 class="text-base font-semibold">🌍 Travel Advisor</h1>
        <div class="flex items-center gap-3">
          <button
            class="px-3 py-1.5 border border-gray-200 rounded-full text-xs text-gray-500 hover:border-gray-900 hover:text-gray-900 transition-colors"
            @click="chat.newChat()"
          >
            + 新对话
          </button>

          <!-- User avatar -->
          <div class="relative">
            <button
              class="w-8 h-8 rounded-full bg-accent text-white text-xs font-medium flex items-center justify-center hover:opacity-80 transition-opacity"
              @click="toggleMenu"
            >
              {{ auth.user?.display_name?.[0] || '?' }}
            </button>

            <!-- Dropdown -->
            <div
              v-if="menuOpen"
              class="absolute right-0 top-10 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50"
              @click="menuOpen = false"
            >
              <div class="px-4 py-2 border-b border-gray-50 dark:border-gray-700">
                <div class="text-sm font-medium truncate">{{ auth.user?.display_name || '用户' }}</div>
                <div class="text-xs text-gray-400 truncate">{{ auth.user?.email || '' }}</div>
              </div>
              <button
                class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
                @click="toggleTheme"
              >
                <span>主题</span>
                <span class="text-xs text-gray-400">{{ isDark ? '🌙 暗色' : '☀️ 亮色' }}</span>
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                @click="logout"
              >
                退出登录
              </button>
            </div>

            <!-- Backdrop -->
            <div v-if="menuOpen" class="fixed inset-0 z-40" @click="menuOpen = false"></div>
          </div>
        </div>
      </header>

      <!-- Messages -->
      <div class="chat-messages flex-1 overflow-y-auto px-4 py-4">
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
          <div class="text-4xl mb-3">🌍</div>
          <h2 class="text-lg font-semibold mb-1">发现你的完美旅行</h2>
          <p class="text-sm text-gray-400 mb-6">告诉我你的偏好——目的地、预算、季节、兴趣</p>
          <div class="flex flex-wrap gap-2 justify-center max-w-md">
            <button
              v-for="p in quickPrompts"
              :key="p.label"
              class="px-4 py-2 bg-surface border border-gray-100 rounded-xl text-sm hover:border-accent transition-colors text-left"
              @click="chat.sendMessage(p.text)"
            >
              {{ p.icon }} {{ p.label }}
            </button>
          </div>
        </div>

        <div v-else class="flex flex-col gap-3">
          <ChatMessage
            v-for="(msg, idx) in messages"
            :key="idx"
            :message="msg"
          />
          <div
            v-if="progressMsg"
            class="self-start flex items-center gap-2 px-3 py-2 bg-surface rounded-full text-xs text-gray-500"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
            {{ progressMsg }}
          </div>
        </div>
      </div>

      <!-- Input -->
      <ChatInput
        :disabled="isStreaming"
        placeholder="描述你的旅行需求..."
        @send="chat.sendMessage"
      />
    </div>
  </div>
</template>
