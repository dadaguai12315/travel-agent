<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import type { ChatMessage } from '@/types'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')
// Rule 3 & 9: only render markdown for non-streaming messages.
// Streaming content uses raw text to avoid per-token full-parse.
const displayHtml = computed(() => {
  if (isUser.value) return ''
  return renderMarkdown(props.message.content)
})
</script>

<template>
  <div
    class="message max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed"
    :class="{
      'self-end bg-accent text-white rounded-br-sm': isUser,
      'self-start bg-surface text-gray-900 rounded-bl-sm': !isUser,
      'streaming-cursor': message.streaming,
    }"
  >
    <template v-if="isUser">{{ message.content }}</template>
    <div
      v-else
      v-memo="[message.streaming ? message.content : 'done']"
      v-html="displayHtml"
      class="md-content"
    ></div>
  </div>
</template>

<style scoped>
.streaming-cursor::after {
  content: '';
  display: inline-block;
  width: 6px;
  height: 14px;
  background: #111;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
