<template>
  <section class="cart-summary" aria-label="选课摘要">
    <div class="summary-header">
      <div>
        <p class="eyebrow">选课摘要</p>
        <h2>已选课程</h2>
      </div>
      <span class="credit-chip">{{ totalCredits }} 学分</span>
    </div>

    <div class="course-list" :class="{ empty: !selectedCourses.length }">
      <template v-if="selectedCourses.length">
        <article v-for="course in selectedCourses" :key="course.id" class="selected-course">
          <div class="course-info">
            <strong>{{ course.title }}</strong>
            <p>{{ course.code }} · {{ course.schedule_display || course.schedule }}</p>
          </div>
          <button type="button" class="remove-btn" @click="$emit('remove-course', course.id)">移除</button>
        </article>
      </template>
      <p v-else class="empty-text">点击课程卡片上的"加入"按钮开始选课。</p>
    </div>

    <div class="warnings" v-if="warnings.length">
      <h3>冲突提示</h3>
      <ul>
        <li v-for="(warning, index) in warnings" :key="index">{{ warning }}</li>
      </ul>
    </div>

    <button class="confirm-button" :disabled="!selectedCourses.length" @click="$emit('confirm-selection')">
      确认选课
    </button>
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ selectedCourses: Array, warnings: Array })
const totalCredits = computed(() => props.selectedCourses.reduce((sum, course) => sum + course.credits, 0))
</script>

<style scoped>
.cart-summary {
  position: sticky;
  top: 24px;
  padding: 20px;
  border-radius: 16px;
  background: var(--panel);
  border: 1px solid var(--border);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
}

.summary-header h2 {
  margin: 0;
  font-size: 1.1rem;
}

.credit-chip {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
  font-weight: 700;
  font-size: 0.85rem;
  white-space: nowrap;
}

.course-list {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
  max-height: 340px;
  overflow-y: auto;
}

.selected-course {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  background: var(--surface);
}

.course-info {
  min-width: 0;
}

.course-info strong {
  display: block;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-info p {
  margin: 2px 0 0;
  font-size: 0.8rem;
  color: var(--muted);
}

.remove-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 10px;
  background: var(--danger);
  color: white;
  font-weight: 600;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.empty-text {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
  text-align: center;
  padding: 20px 0;
}

.warnings {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.08);
  color: var(--warning);
  font-size: 0.85rem;
}

.warnings h3 {
  margin: 0 0 6px;
  font-size: 0.9rem;
}

.warnings ul {
  margin: 0;
  padding-left: 18px;
}

.confirm-button {
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
}

.confirm-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
