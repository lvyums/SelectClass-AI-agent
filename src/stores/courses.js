/**
 * 课程状态管理 — Observer Pattern (Pinia)
 *
 * 管理课程列表、搜索、筛选状态。
 * 当课程数据或筛选条件变化时，视图自动更新。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCoursesApi } from '../api/courses'

export const useCourseStore = defineStore('courses', () => {
  // State
  const courses = ref([])
  const searchQuery = ref('')
  const filters = ref({ faculty: 'All', courseType: 'All', level: 'All', credit: 'All' })
  const activeCourse = ref(null)
  const loading = ref(false)

  // Getters — Observer Pattern: 响应式计算属性，依赖变化时自动重算
  const filteredCourses = computed(() => {
    return courses.value.filter((course) => {
      const matchesQuery = [course.title, course.code, course.summary, course.faculty, course.course_type, course.instructor, course.keywords]
        .join(' ')
        .toLowerCase()
        .includes(searchQuery.value.toLowerCase())
      const matchesFaculty = filters.value.faculty === 'All' || course.faculty === filters.value.faculty
      const matchesType = filters.value.courseType === 'All' || course.course_type === filters.value.courseType
      const matchesLevel = filters.value.level === 'All' || course.level === filters.value.level
      const matchesCredit = filters.value.credit === 'All' || String(course.credits) === filters.value.credit
      return matchesQuery && matchesFaculty && matchesType && matchesLevel && matchesCredit
    })
  })

  // Actions
  async function fetchCourses() {
    loading.value = true
    try {
      const data = await getCoursesApi()
      courses.value = data.data || data
    } finally {
      loading.value = false
    }
  }

  function setSearchQuery(query) {
    searchQuery.value = query
  }

  function setFilters(newFilters) {
    filters.value = { ...newFilters }
  }

  function setActiveCourse(course) {
    activeCourse.value = course
  }

  return {
    courses, searchQuery, filters, activeCourse, loading,
    filteredCourses,
    fetchCourses, setSearchQuery, setFilters, setActiveCourse,
  }
})
