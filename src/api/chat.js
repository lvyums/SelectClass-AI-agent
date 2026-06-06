/**
 * 聊天 API — 封装智能助手对话接口
 */

import request from './request'

export function chatApi(message) {
  return request.post('/api/chat/', { message })
}
