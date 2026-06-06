<template>
  <div class="app-shell" :class="{ dark: darkMode }">
    <main class="main-panel">
      <header class="main-header">
        <div>
          <p class="eyebrow">学术选课平台</p>
          <h1>智能课程目录与选课助手</h1>
        </div>
        <div class="header-actions">
          <button class="chat-toggle" @click="chatOpen = !chatOpen" aria-label="打开智能助理">
            💬
            <span v-if="!chatOpen && conversation.length > 1" class="badge-dot"></span>
          </button>
          <button class="icon-button-theme" @click="toggleDarkMode" aria-label="切换主题">
            {{ darkMode ? '🌙' : '☀️' }}
          </button>
          <button v-if="token" class="logout-button" @click="logout">退出登录</button>
        </div>
      </header>

      <section v-if="!token" class="auth-panel">
        <h2>请先登录或注册</h2>
        <form @submit.prevent="authMode === 'login' ? login() : register()">
          <div class="field-row">
            <label for="username">用户名</label>
            <input id="username" v-model="authForm.username" autocomplete="username" required minlength="2" maxlength="100" />
          </div>
          <div class="field-row">
            <label for="password">密码</label>
            <input id="password" type="password" v-model="authForm.password" autocomplete="current-password" required minlength="6" maxlength="128" />
          </div>
          <button type="submit">{{ authMode === 'login' ? '登录' : '注册' }}</button>
        </form>
        <button class="switch-button" @click="authMode = authMode === 'login' ? 'register' : 'login'">
          {{ authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
        </button>
      </section>

      <section v-else-if="user && !user.major" class="profile-panel">
        <h2>请补充你的专业和年级</h2>
        <form @submit.prevent="saveProfile()">
          <div class="field-row">
            <label for="major">专业</label>
            <input id="major" v-model="profileForm.major" placeholder="例如：计算机科学与技术" />
          </div>
          <div class="field-row">
            <label for="grade">年级</label>
            <select id="grade" v-model="profileForm.grade">
              <option value="">请选择年级</option>
              <option value="大一">大一</option>
              <option value="大二">大二</option>
              <option value="大三">大三</option>
              <option value="大四">大四</option>
            </select>
          </div>
          <div class="field-row full-width">
            <label for="interests">兴趣爱好（可选）</label>
            <input id="interests" v-model="profileForm.interests" placeholder="例如：人工智能, 数据分析, 艺术" />
          </div>
          <button type="submit">保存资料并生成推荐</button>
        </form>
      </section>

      <template v-else>
        <div class="content-layout">
          <CatalogView
            :courses="courses"
            :selected-courses="selectedCourses"
            :filters="filters"
            :search-query="searchQuery"
            :dark-mode="darkMode"
            @update-filters="filters = $event"
            @update-search="searchQuery = $event"
            @add-course="addCourse"
            @show-detail="openCourseDetail"
          />

          <CartSummary
            :selected-courses="selectedCourses"
            :warnings="conflictWarnings"
            @remove-course="removeCourse"
            @confirm-selection="confirmSelection"
          />
        </div>
      </template>
    </main>

    <Sidebar
      :open="chatOpen"
      :conversation="conversation"
      :recommendations="recommendations"
      :dark-mode="darkMode"
      @close="chatOpen = false"
      @send-message="handleAgentMessage"
      @show-course="openCourseDetail"
      @add-course="addCourse"
    />

    <CourseModal
      v-if="activeCourse"
      :course="activeCourse"
      :dark-mode="darkMode"
      @close="activeCourse = null"
      @add-course="addCourse"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Sidebar from './components/Sidebar.vue'
import CatalogView from './views/CatalogView.vue'
import CartSummary from './components/CartSummary.vue'
import CourseModal from './components/CourseModal.vue'

const courses = ref([])
const selectedCourses = ref([])
const activeCourse = ref(null)
const conversation = ref([
  { from: 'agent', text: '你好！我是你的选课助手。你可以告诉我"帮我选CS101"、"退掉数学课"、"我选了哪些课"等，我来帮你操作。' }
])
const recommendations = ref([])
const darkMode = ref(false)
const chatOpen = ref(false)
const searchQuery = ref('')
const filters = ref({ faculty: 'All', courseType: 'All', level: 'All', credit: 'All' })
const token = ref(localStorage.getItem('token') || '')
const user = ref(null)
const authMode = ref('login')
const authForm = ref({ username: '', password: '' })
const profileForm = ref({ major: '', grade: '', interests: '' })

function extractErrorMessage(error, fallback) {
  const data = error.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.msg || JSON.stringify(e)).join('；')
  }
  if (data.error) return data.error
  return fallback
}

const conflictWarnings = computed(() => {
  const warnings = []

  const slots = selectedCourses.value.map((course) => {
    return (course.schedule_json || []).map((item) => item.code)
  })

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

function normalizeToken(value) {
  if (!value) {
    return ''
  }
  return value.toString().replace(/^Bearer\s+/i, '').trim()
}

function setAuthToken(value) {
  const normalized = normalizeToken(value)
  token.value = normalized
  if (normalized) {
    localStorage.setItem('token', normalized)
    axios.defaults.headers.common.Authorization = `Bearer ${normalized}`
  } else {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common.Authorization
  }
}

// 设置默认的Authorization头部
if (token.value) {
  axios.defaults.headers.common.Authorization = `Bearer ${token.value}`
}

axios.interceptors.request.use((config) => {
  if (token.value) {
    config.headers = config.headers || {}
    if (!config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token.value}`
    }
  }
  return config
})

async function fetchCourses() {
  try {
    const response = await axios.get('/api/courses/')
    courses.value = response.data
  } catch (error) {
    console.error('获取课程失败', error)
  }
}

async function fetchUser() {
  if (!token.value) {
    return
  }
  try {
    const response = await axios.get('/api/auth/me')
    user.value = response.data.user
    if (user.value) {
      profileForm.major = user.value.major || ''
      profileForm.grade = user.value.grade || ''
      profileForm.interests = user.value.interests || ''
    }
  } catch (error) {
    if (error.response?.status === 401) {
      window.alert('登录已过期，请重新登录。')
    }
    console.warn('获取用户信息失败，已清除本地登录状态。', error)
    logout()
  }
}

async function fetchSelections() {
  if (!token.value) {
    return
  }

  try {
    const response = await axios.get('/api/selection/')
    selectedCourses.value = response.data
  } catch (error) {
    console.error('获取选课记录失败', error)
  }
}

async function login() {
  try {
    const response = await axios.post('/api/auth/login', authForm.value)
    const tokenValue = response.data.access_token || response.data.token
    setAuthToken(tokenValue)

    await fetchUser()
    await fetchCourses()
    await fetchSelections()
  } catch (error) {
    window.alert(extractErrorMessage(error, '登录失败，请检查用户名和密码。'))
  }
}

async function register() {
  try {
    const response = await axios.post('/api/auth/register', authForm.value)
    const tokenValue = response.data.access_token || response.data.token
    setAuthToken(tokenValue)
    await fetchUser()
    await fetchCourses()
    await fetchSelections()
  } catch (error) {
    window.alert(extractErrorMessage(error, '注册失败，请稍后重试。'))
  }
}

async function saveProfile() {
  if (!profileForm.value.major || !profileForm.value.grade) {
    window.alert('专业和年级不能为空。')
    return
  }
  try {
    const response = await axios.post('/api/profile/', profileForm.value)
    user.value = response.data.user
    conversation.value.push({ from: 'agent', text: '已保存你的专业和年级，开始为你推荐更符合学业规划的课程。' })
    await fetchRecommendations('')
  } catch (error) {
    window.alert(extractErrorMessage(error, '保存资料失败。'))
  }
}

async function fetchRecommendations(query) {
  if (!token.value) {
    return
  }
  try {
    const response = await axios.post('/api/recommendations/', { query })
    recommendations.value = response.data.recommendations || []
    const explanation = response.data.explanation || '已生成推荐课程。'
    conversation.value.push({ from: 'agent', text: explanation })
  } catch (error) {
    console.error('获取推荐失败', error)
    conversation.value.push({ from: 'agent', text: '推荐暂时不可用，请稍后再试。' })
  }
}

function getSlotCodes(course) {
  return new Set((course.schedule_json || []).map((item) => item.code))
}

async function addCourse(course) {
  if (!course || !course.id) {
    return
  }
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
    `确认添加以下课程？\n\n课程：${course.code} ${course.title}\n学分：${course.credits}\n教师：${course.instructor}\n时间：${course.schedule_display || course.schedule || '待定'}`
  )
  if (!confirmed) return

  selectedCourses.value.push(course)

  try {
    const response = await axios.post('/api/selection/', { courseIds: [course.id] })
    selectedCourses.value = response.data
  } catch (error) {
    await fetchSelections()
    window.alert(extractErrorMessage(error, '添加课程失败。'))
  }
}

async function removeCourse(courseId) {
  const prev = selectedCourses.value
  selectedCourses.value = prev.filter((course) => course.id !== courseId)
  try {
    const response = await axios.delete(`/api/selection/${courseId}`)
    selectedCourses.value = response.data
  } catch (error) {
    selectedCourses.value = prev
    window.alert(extractErrorMessage(error, '移除课程失败。'))
  }
}

function openCourseDetail(course) {
  activeCourse.value = course
}

async function confirmSelection() {
  if (conflictWarnings.value.length) {
    window.alert('存在课程冲突，请先处理冲突后再确认。')
    return
  }

  try {
    const response = await axios.post('/api/selection/', {
      courseIds: selectedCourses.value.map((course) => course.id),
    })
    selectedCourses.value = response.data
    window.alert('选课已提交，课程已保存到你的账户。')
  } catch (error) {
    window.alert(extractErrorMessage(error, '确认选课失败。'))
  }
}

async function handleAgentMessage(message) {
  if (!token.value) {
    window.alert('请先登录后再咨询智能助理。')
    return
  }

  conversation.value.push({ from: 'user', text: message })

  try {
    const response = await axios.post('/api/chat/', { message })
    const data = response.data
    conversation.value.push({ from: 'agent', text: data.answer })
    if (data.selected_courses) {
      selectedCourses.value = data.selected_courses
    }
    if (data.recommendations) {
      recommendations.value = data.recommendations
    }
  } catch (error) {
    const errorMsg = extractErrorMessage(error, '智能助理暂时不可用，请稍后再试。')
    conversation.value.push({ from: 'agent', text: errorMsg })
  }

  // Always sync selected courses from server to ensure UI is up-to-date
  await fetchSelections()
}

function toggleDarkMode() {
  darkMode.value = !darkMode.value
}

function logout() {
  setAuthToken('')
  user.value = null
  selectedCourses.value = []
  recommendations.value = []
}

onMounted(async () => {
  if (token.value) {
    setAuthToken(token.value)
    await fetchUser()
    await fetchCourses()
    await fetchSelections()
    if (user.value && user.value.major) {
      await fetchRecommendations('')
    }
  } else {
    await fetchCourses()
  }
})
</script>

<style scoped>
.auth-panel,
.profile-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  max-width: 480px;
}

.field-row {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.field-row label {
  font-weight: 700;
  font-size: 0.9rem;
}

.field-row input,
.field-row select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
}

.full-width {
  width: 100%;
}

button[type='submit'],
.switch-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  margin-top: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}

.icon-button-theme {
  width: 44px;
  height: 44px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel);
  color: var(--primary);
  font-size: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
