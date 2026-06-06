/**
 * 推荐 API — 封装课程推荐接口
 */

import request from './request'

export function getRecommendationsApi(query = '') {
  return request.post('/api/recommendations/', { query })
}
