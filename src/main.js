/**
 * 应用入口 — Factory Pattern (createApp)
 *
 * 使用 Vue 的 createApp 工厂函数创建应用实例，
 * 注册 Pinia（状态管理）和 Vue Router（路由）。
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/styles.css'

// Factory Pattern — 创建应用实例
const app = createApp(App)

// 注册 Pinia — Observer Pattern 的基础设施
const pinia = createPinia()
app.use(pinia)

// 注册路由 — Blueprint Pattern 的前端实现
app.use(router)

// 挂载应用
app.mount('#app')
