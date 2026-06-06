/**
 * 认证 API — 封装登录、注册、获取用户信息接口
 */

import request from './request'

export function loginApi(data) {
  return request.post('/api/auth/login', data)
}

export function registerApi(data) {
  return request.post('/api/auth/register', data)
}

export function getMeApi() {
  return request.get('/api/auth/me')
}
