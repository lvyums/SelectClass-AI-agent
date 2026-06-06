<template>
  <div class="login-page">
    <div class="auth-panel">
      <h2>{{ authMode === 'login' ? '登录' : '注册' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="field-row">
          <label for="username">用户名</label>
          <input id="username" v-model="authForm.username" autocomplete="username" required minlength="2" maxlength="100" />
        </div>
        <div class="field-row">
          <label for="password">密码</label>
          <input id="password" type="password" v-model="authForm.password" autocomplete="current-password" required minlength="6" maxlength="128" />
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? '处理中...' : (authMode === 'login' ? '登录' : '注册') }}
        </button>
      </form>
      <button class="switch-button" @click="toggleMode">
        {{ authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
      </button>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { extractErrorMessage } from '../api/request'

const router = useRouter()
const authStore = useAuthStore()

const authMode = ref('login')
const authForm = ref({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

function toggleMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login'
  error.value = ''
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    authStore.authForm = authForm.value
    if (authMode.value === 'login') {
      await authStore.login()
    } else {
      await authStore.register()
    }
    router.push('/')
  } catch (err) {
    error.value = extractErrorMessage(err, authMode.value === 'login' ? '登录失败' : '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
  min-height: 80vh;
}

.auth-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  max-width: 400px;
  width: 100%;
}

.auth-panel h2 {
  margin: 0 0 20px;
  text-align: center;
}

.field-row {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.field-row label {
  font-weight: 700;
  font-size: 0.9rem;
}

.field-row input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
  box-sizing: border-box;
}

button[type='submit'] {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch-button {
  display: block;
  margin-top: 12px;
  padding: 8px;
  border: none;
  background: transparent;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  text-align: center;
}

.error-text {
  color: var(--danger, #ef4444);
  font-size: 0.85rem;
  margin-top: 12px;
  text-align: center;
}
</style>
