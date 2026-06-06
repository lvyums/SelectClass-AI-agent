/**
 * 选课状态管理 — Observer Pattern (Pinia)
 *
 * 管理已选课程、冲突检测、推荐课程、聊天对话。
 * 状态变化自动触发视图更新。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSelectionsApi, enrollApi, dropCourseApi } from '../api/selection'
import { chatApi } from '../api/chat'
import { getRecommendationsApi } from '../api/recommendations'

export const useSelectionStore = defineStore('selection', () => {
  // State
  const selectedCourses = ref([])
  const recommendations = ref([])
  const conversation = ref([
    { from: 'agent', text: '你好！我是你的选课助手。你可以告诉我"帮我选CS101"、"退掉数学课"、"我选了哪些课"等，我来帮你操作。' }
  ])
  const chatOpen = ref(false)
  const loading = ref(false)

  // Getters — Observer Pattern: 冲突检测自动响应已选课程变化
  const totalCredits = computed(() =>
    selectedCourses.value.reduce((sum, course) => sum + course.credits, 0)
  )

  const conflictWarnings = computed(() => {
    const warnings = []
    const slots = selectedCourses.value.map((course) =>
      (course.schedule_json || []).map((item) => item.code)
    )
    for (let i = 0; i < slots.length; i += 1) {
      for (let j = i + 1; j < slots.length; j += 1) {
        const overlap = slots[i].some((code) => slots[j].includes(code))
        if (overlap) {
          warnings.push(`课程 ${selectedCourses.value[i].code} 与 ${selectedCourses.value[j].code} 存在时间冲突。`)
        }
      }
    }
    return warnings
  })

  // Actions
  async function fetchSelections() {
    try {
      const data = await getSelectionsApi()
      selectedCourses.value = data.data || data
    } catch (error) {
      console.error('获取选课记录失败', error)
    }
  }

  function getSlotCodes(course) {
    return new Set((course.schedule_json || []).map((item) => item.code))
  }

  async function addCourse(course) {
    if (!course || !course.id) return
    if (selectedCourses.value.some((item) => item.id === course.id)) {
      window.alert('该课程已加入选课列表。')
      return
    }

    const courseSlots = getSlotCodes(course)
    const conflict = selectedCourses.value.find((existing) => {
      const existingSlots = getSlotCodes(existing)
      return [...courseSlots].some((code) => existingSlots.has(code))
    })
    if (conflict) {
      window.alert(`课程 ${course.code} 与已选课程 ${conflict.code} 存在时间冲突。`)
      return
    }

    const confirmed = window.confirm(
      `确认添加以下课程？\n\n课程：${course.code} ${course.title}\n学分：${course.credits}\n教师：${course.instructor}\n时间：${course.schedule_display || '待定'}`
    )
    if (!confirmed) return

    selectedCourses.value.push(course)
    try {
      const data = await enrollApi([course.id])
      selectedCourses.value = data.data || data
    } catch (error) {
      await fetchSelections()
      throw error
    }
  }

  async function removeCourse(courseId) {
    const prev = selectedCourses.value
    selectedCourses.value = prev.filter((course) => course.id !== courseId)
    try {
      const data = await dropCourseApi(courseId)
      selectedCourses.value = data.data || data
    } catch (error) {
      selectedCourses.value = prev
      throw error
    }
  }

  async function confirmSelection() {
    if (conflictWarnings.value.length) {
      window.alert('存在课程冲突，请先处理冲突后再确认。')
      return
    }
    const data = await enrollApi(selectedCourses.value.map((c) => c.id))
    selectedCourses.value = data.data || data
    window.alert('选课已提交，课程已保存到你的账户。')
  }

  async function sendMessage(message) {
    conversation.value.push({ from: 'user', text: message })
    try {
      const data = await chatApi(message)
      const result = data.data || data
      conversation.value.push({ from: 'agent', text: result.answer })
      if (result.selected_courses) {
        selectedCourses.value = result.selected_courses
      }
      if (result.recommendations) {
        recommendations.value = result.recommendations
      }
      await fetchSelections()
    } catch (error) {
      conversation.value.push({ from: 'agent', text: '智能助理暂时不可用，请稍后再试。' })
    }
  }

  async function fetchRecommendations(query = '') {
    try {
      const data = await getRecommendationsApi(query)
      const result = data.data || data
      recommendations.value = result.recommendations || []
      const explanation = result.explanation || '已生成推荐课程。'
      conversation.value.push({ from: 'agent', text: explanation })
    } catch (error) {
      console.error('获取推荐失败', error)
      conversation.value.push({ from: 'agent', text: '推荐暂时不可用，请稍后再试。' })
    }
  }

  function toggleChat() {
    chatOpen.value = !chatOpen.value
  }

  return {
    selectedCourses, recommendations, conversation, chatOpen, loading,
    totalCredits, conflictWarnings,
    fetchSelections, addCourse, removeCourse, confirmSelection,
    sendMessage, fetchRecommendations, toggleChat,
  }
})
