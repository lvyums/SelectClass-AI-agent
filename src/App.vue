<template>
  <div class="app-shell" :class="{ dark: darkMode }">
    <AppHeader :dark-mode="darkMode" @toggle-dark="toggleDarkMode" />

    <main class="main-panel">
      <router-view />
    </main>

    <Sidebar
      :open="selectionStore.chatOpen"
      :conversation="selectionStore.conversation"
      :recommendations="selectionStore.recommendations"
      :dark-mode="darkMode"
      @close="selectionStore.chatOpen = false"
      @send-message="handleSendMessage"
      @show-course="courseStore.setActiveCourse"
      @add-course="handleAddCourse"
    />

    <CourseModal
      v-if="courseStore.activeCourse"
      :course="courseStore.activeCourse"
      :dark-mode="darkMode"
      @close="courseStore.setActiveCourse(null)"
      @add-course="handleAddCourse"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useCourseStore } from './stores/courses'
import { useSelectionStore } from './stores/selection'
import { extractErrorMessage } from './api/request'
import AppHeader from './components/AppHeader.vue'
import Sidebar from './components/Sidebar.vue'
import CourseModal from './components/CourseModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const courseStore = useCourseStore()
const selectionStore = useSelectionStore()

const darkMode = ref(localStorage.getItem('darkMode') === 'true')

function toggleDarkMode() {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
}

async function handleAddCourse(course) {
  try {
    await selectionStore.addCourse(course)
  } catch (err) {
    window.alert(extractErrorMessage(err, '添加课程失败'))
  }
}

async function handleSendMessage(message) {
  if (!authStore.isLoggedIn) {
    window.alert('请先登录后再咨询智能助理。')
    return
  }
  await selectionStore.sendMessage(message)
}

onMounted(async () => {
  if (authStore.token) {
    try {
      await authStore.fetchUser()
    } catch {
      router.push('/login')
      return
    }
  }
  await courseStore.fetchCourses()
  if (authStore.isLoggedIn && authStore.user?.major) {
    await selectionStore.fetchSelections()
  }
})
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

.main-panel {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}
</style>
