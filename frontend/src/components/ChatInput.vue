<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ send: [text: string] }>()
const props = defineProps<{ disabled?: boolean; placeholder?: string }>()

const text = ref('')

function handleSubmit() {
  const trimmed = text.value.trim()
  if (!trimmed || props.disabled) return
  emit('send', trimmed)
  text.value = ''
}
</script>

<template>
  <form
    class="flex gap-2 px-4 py-3 border-t border-gray-100 bg-white flex-shrink-0"
    @submit.prevent="handleSubmit"
  >
    <input
      v-model="text"
      type="text"
      :placeholder="placeholder || '描述你的旅行需求...'"
      :disabled="disabled"
      class="flex-1 min-w-0 px-4 py-2.5 bg-surface border border-gray-200 rounded-full text-sm outline-none focus:border-accent focus:bg-white transition-colors disabled:opacity-50"
    />
    <button
      type="submit"
      :disabled="disabled || !text.trim()"
      class="px-5 py-2.5 bg-accent text-white rounded-full text-sm font-medium hover:opacity-85 transition-opacity disabled:opacity-25 disabled:cursor-not-allowed flex-shrink-0"
    >
      发送
    </button>
  </form>
</template>
