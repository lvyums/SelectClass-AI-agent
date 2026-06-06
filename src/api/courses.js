/**
 * 课程 API — 封装课程查询接口
 */

import request from './request'

export function getCoursesApi(params = {}) {
  return request.get('/api/courses/', { params })
}

export function getCourseApi(courseId) {
  return request.get(`/api/courses/${courseId}`)
}
