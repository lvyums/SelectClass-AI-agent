/**
 * 个人资料 API — 封装资料更新接口
 */

import request from './request'

export function updateProfileApi(data) {
  return request.put('/api/profile/', data)
}
