<template>
  <div class="profile-page">
    <div class="profile-panel">
      <h2>个人资料</h2>
      <form @submit.prevent="handleSave">
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
        <div class="field-row">
          <label for="interests">兴趣爱好（可选）</label>
          <input id="interests" v-model="profileForm.interests" placeholder="例如：人工智能, 数据分析, 艺术" />
        </div>
        <button type="submit" :disabled="saving">
          {{ saving ? '保存中...' : '保存资料' }}
        </button>
      </form>
      <p v-if="message" class="message-text">{{ message }}</p>
      <button class="back-button" @click="router.push('/')">返回课程目录</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSelectionStore } from '../stores/selection'
import { extractErrorMessage } from '../api/request'

const router = useRouter()
const authStore = useAuthStore()
const selectionStore = useSelectionStore()

const profileForm = ref({ major: '', grade: '', interests: '' })
const saving = ref(false)
const message = ref('')

onMounted(() => {
  if (authStore.user) {
    profileForm.value.major = authStore.user.major || ''
    profileForm.value.grade = authStore.user.grade || ''
    profileForm.value.interests = authStore.user.interests || ''
  }
})

async function handleSave() {
  if (!profileForm.value.major || !profileForm.value.grade) {
    message.value = '专业和年级不能为空。'
    return
  }
  saving.value = true
  message.value = ''
  try {
    authStore.profileForm = profileForm.value
    await authStore.saveProfile()
    message.value = '资料已保存！'
    await selectionStore.fetchRecommendations('')
  } catch (err) {
    message.value = extractErrorMessage(err, '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-page {
  display: grid;
  place-items: center;
  min-height: 80vh;
}

.profile-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  max-width: 480px;
  width: 100%;
}

.profile-panel h2 {
  margin: 0 0 20px;
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
  box-sizing: border-box;
}

button[type='submit'] {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-button {
  display: block;
  margin-top: 12px;
  padding: 8px;
  border: none;
  background: transparent;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  text-align: center;
}

.message-text {
  color: var(--success, #10b981);
  font-size: 0.85rem;
  margin-top: 12px;
  text-align: center;
}
</style>
