/**
 * Axios 单例 + 请求/响应拦截器 — Singleton Pattern + Template Pattern + Proxy Pattern
 *
 * Singleton: 全局唯一的 Axios 实例
 * Template: 统一的请求/响应处理模板
 * Proxy: 拦截器代理所有请求，自动注入 Token、统一处理错误
 */

import axios from 'axios'

// Singleton — 全局唯一 Axios 实例
const request = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// Proxy Pattern — 请求拦截器：自动携带 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Template Method Pattern — 响应拦截器：统一处理响应
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * 提取错误信息 — Template Method
 */
export function extractErrorMessage(error, fallback = '操作失败') {
  const data = error.response?.data
  if (!data) return fallback
  if (typeof data.message === 'string') return data.message
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.msg || JSON.stringify(e)).join('；')
  }
  if (data.error) return data.error
  return fallback
}

export default request
