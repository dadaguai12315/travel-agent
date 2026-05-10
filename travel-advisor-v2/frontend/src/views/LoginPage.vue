<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const displayName = ref('')
const isRegister = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  try {
    if (isRegister.value) {
      await auth.register(email.value, password.value, displayName.value)
    } else {
      await auth.login(email.value, password.value)
    }
    router.push('/chat')
  } catch (err: any) {
    error.value = err.response?.data?.error?.message || '操作失败，请重试'
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
      <div class="text-center mb-6">
        <div class="text-3xl mb-2">🌍</div>
        <h1 class="text-xl font-semibold">Travel Advisor</h1>
        <p class="text-sm text-gray-400 mt-1">智能旅行规划助手</p>
      </div>

      <form @submit.prevent="handleSubmit" class="flex flex-col gap-3">
        <input
          v-model="email"
          type="email"
          placeholder="邮箱"
          required
          class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:border-accent"
        />
        <input
          v-if="isRegister"
          v-model="displayName"
          placeholder="昵称"
          class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:border-accent"
        />
        <input
          v-model="password"
          type="password"
          placeholder="密码（至少8位）"
          required
          minlength="8"
          class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:border-accent"
        />

        <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>

        <button
          type="submit"
          :disabled="auth.loading"
          class="py-2.5 bg-accent text-white rounded-xl text-sm font-medium hover:opacity-85 transition-opacity disabled:opacity-50"
        >
          {{ isRegister ? '注册' : '登录' }}
        </button>
      </form>

      <p class="text-center text-xs text-gray-400 mt-4">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <button class="text-accent underline" @click="isRegister = !isRegister">
          {{ isRegister ? '去登录' : '去注册' }}
        </button>
      </p>
    </div>
  </div>
</template>
