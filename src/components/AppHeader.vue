<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo-link">
        <p class="eyebrow">学术选课平台</p>
        <h1>智能课程目录与选课助手</h1>
      </router-link>
    </div>
    <div class="header-actions">
      <button v-if="authStore.isLoggedIn" class="chat-toggle" @click="selectionStore.toggleChat()" aria-label="打开智能助理">
        💬
        <span v-if="!selectionStore.chatOpen && selectionStore.conversation.length > 1" class="badge-dot"></span>
      </button>
      <button class="icon-button-theme" @click="$emit('toggle-dark')" aria-label="切换主题">
        {{ darkMode ? '🌙' : '☀️' }}
      </button>
      <template v-if="authStore.isLoggedIn">
        <router-link to="/profile" class="profile-link">个人中心</router-link>
        <button class="logout-button" @click="handleLogout">退出登录</button>
      </template>
      <router-link v-else to="/login" class="login-link">登录</router-link>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSelectionStore } from '../stores/selection'

defineProps({ darkMode: Boolean })
defineEmits(['toggle-dark'])

const router = useRouter()
const authStore = useAuthStore()
const selectionStore = useSelectionStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.logo-link {
  text-decoration: none;
  color: inherit;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
}

h1 {
  margin: 0;
  font-size: 1.2rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.chat-toggle {
  position: relative;
  width: 44px;
  height: 44px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel);
  font-size: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.badge-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger, #ef4444);
}

.icon-button-theme {
  width: 44px;
  height: 44px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel);
  color: var(--primary);
  font-size: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.profile-link,
.login-link {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--panel);
  color: var(--text);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
}

.logout-button {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--panel);
  color: var(--danger, #ef4444);
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
