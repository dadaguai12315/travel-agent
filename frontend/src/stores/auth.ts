import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const user = ref<User | null>(loadUser())
  const loading = ref(false)

  function loadUser(): User | null {
    try {
      const raw = localStorage.getItem('auth_user')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  }

  function saveUser(u: User | null) {
    if (u) {
      localStorage.setItem('auth_user', JSON.stringify(u))
    } else {
      localStorage.removeItem('auth_user')
    }
  }

  const isAuthenticated = computed(() => !!token.value)

  async function register(email: string, password: string, displayName: string) {
    loading.value = true
    try {
      const { data } = await apiClient.post('/auth/register', {
        email, password, display_name: displayName,
      })
      token.value = data.access_token
      user.value = data.user
      saveUser(data.user)
      localStorage.setItem('auth_token', data.access_token)
    } finally {
      loading.value = false
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const { data } = await apiClient.post('/auth/login', { email, password })
      token.value = data.access_token
      user.value = data.user
      saveUser(data.user)
      localStorage.setItem('auth_token', data.access_token)
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    saveUser(null)
    localStorage.removeItem('auth_token')
  }

  return { token, user, loading, isAuthenticated, register, login, logout }
})
