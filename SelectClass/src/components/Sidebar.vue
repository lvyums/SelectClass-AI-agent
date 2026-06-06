<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div v-if="open" class="chat-overlay" @click.self="$emit('close')"></div>
    </Transition>
    <Transition name="drawer">
      <aside v-if="open" class="chat-drawer" :class="{ dark: darkMode }">
        <div class="drawer-header">
          <div>
            <h2>智能助理</h2>
            <p>选课咨询与推荐</p>
          </div>
          <button class="close-btn" @click="$emit('close')" aria-label="关闭">✕</button>
        </div>

        <div class="conversation" ref="conversationEl" aria-live="polite">
          <div v-for="(message, index) in conversation" :key="index" :class="['bubble', message.from]">
            <p>{{ message.text }}</p>
          </div>
        </div>

        <form class="chat-form" @submit.prevent="submitMessage">
          <label for="assistant-query" class="sr-only">输入你的选课问题</label>
          <input
            id="assistant-query"
            v-model="query"
            placeholder="例如：推荐必修课、帮我选CS101"
            autocomplete="off"
          />
          <button type="submit">发送</button>
        </form>

        <section class="recommendations" v-if="recommendations.length">
          <h3>推荐课程</h3>
          <ul>
            <li v-for="course in recommendations" :key="course.id">
              <button type="button" class="rec-link" @click="$emit('show-course', course)">
                <strong>{{ course.code }}</strong>
                <span>{{ course.title }}</span>
              </button>
              <button type="button" class="add-btn" @click.stop="$emit('add-course', course)">加入</button>
            </li>
          </ul>
        </section>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
const props = defineProps({ open: Boolean, conversation: Array, recommendations: Array, darkMode: Boolean })
const emit = defineEmits(['close', 'send-message', 'show-course', 'add-course'])
const query = ref('')
const conversationEl = ref(null)

watch(() => props.conversation.length, async () => {
  await nextTick()
  if (conversationEl.value) {
    conversationEl.value.scrollTop = conversationEl.value.scrollHeight
  }
})

function submitMessage() {
  if (!query.value.trim()) return
  emit('send-message', query.value.trim())
  query.value = ''
}
</script>

<style scoped>
.chat-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.2);
  z-index: 90;
}

.chat-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 100vw;
  height: 100vh;
  background: var(--panel);
  border-left: 1px solid var(--border);
  z-index: 100;
  display: flex;
  flex-direction: column;
  padding: 0;
  box-shadow: -8px 0 30px rgba(0, 0, 0, 0.08);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.drawer-header h2 {
  margin: 0 0 2px;
  font-size: 1.15rem;
}

.drawer-header p {
  margin: 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: var(--surface);
  color: var(--muted);
  font-size: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.conversation {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bubble {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--surface);
  color: var(--text);
  max-width: 90%;
  font-size: 0.92rem;
  line-height: 1.5;
}

.bubble p {
  margin: 0;
}

.bubble.agent {
  align-self: flex-start;
  background: rgba(63, 131, 248, 0.08);
}

.bubble.user {
  align-self: flex-end;
  background: rgba(16, 185, 129, 0.1);
}

.chat-form {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.chat-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
  font-size: 0.9rem;
}

.chat-form button {
  padding: 10px 16px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
}

.recommendations {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  max-height: 240px;
  overflow-y: auto;
}

.recommendations h3 {
  margin: 0 0 10px;
  font-size: 0.95rem;
}

.recommendations ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.recommendations li {
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--surface);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.rec-link {
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  padding: 0;
  display: grid;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.rec-link strong {
  font-size: 0.82rem;
  color: var(--primary);
}

.rec-link span {
  font-size: 0.88rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.add-btn {
  border: none;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(63, 131, 248, 0.12);
  color: var(--primary);
  font-weight: 700;
  font-size: 0.8rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Transitions */
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.25s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}

@media (max-width: 480px) {
  .chat-drawer {
    width: 100vw;
  }
}
</style>
