/**
 * 选课 API — 封装选课、退课、查看已选课程接口
 */

import request from './request'

export function getSelectionsApi() {
  return request.get('/api/selection/')
}

export function enrollApi(courseIds) {
  return request.post('/api/selection/', { courseIds })
}

export function dropCourseApi(courseId) {
  return request.delete(`/api/selection/${courseId}`)
}
