/**
 * 认证状态管理 — Observer Pattern (Pinia)
 *
 * 管理用户登录状态、Token、用户信息。
 * 当状态变化时，所有订阅的组件自动更新视图。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getMeApi } from '../api/auth'
import { updateProfileApi } from '../api/profile'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const authMode = ref('login') // 'login' | 'register'
  const authForm = ref({ username: '', password: '' })
  const profileForm = ref({ major: '', grade: '', interests: '' })

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const needsProfile = computed(() => isLoggedIn.value && !user.value?.major)

  // Actions
  function setToken(value) {
    token.value = value
    if (value) {
      localStorage.setItem('token', value)
    } else {
      localStorage.removeItem('token')
    }
  }

  async function login() {
    const data = await loginApi(authForm.value)
    const accessToken = data.data?.access_token || data.access_token
    setToken(accessToken)
    await fetchUser()
    return data
  }

  async function register() {
    const data = await registerApi(authForm.value)
    const accessToken = data.data?.access_token || data.access_token
    setToken(accessToken)
    await fetchUser()
    return data
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const data = await getMeApi()
      user.value = data.data?.user || data.user
      if (user.value) {
        profileForm.value.major = user.value.major || ''
        profileForm.value.grade = user.value.grade || ''
        profileForm.value.interests = user.value.interests || ''
      }
    } catch (error) {
      logout()
      throw error
    }
  }

  async function saveProfile() {
    const data = await updateProfileApi(profileForm.value)
    user.value = data.data || data
    return data
  }

  function logout() {
    setToken('')
    user.value = null
  }

  return {
    token, user, authMode, authForm, profileForm,
    isLoggedIn, needsProfile,
    setToken, login, register, fetchUser, saveProfile, logout,
  }
})
