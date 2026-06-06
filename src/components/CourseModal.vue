<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card" :class="{ dark: darkMode }">
      <header class="modal-header">
        <div>
          <p class="eyebrow">课程详情</p>
          <h2>{{ course.title }}</h2>
          <p class="course-code">{{ course.code }} · {{ course.faculty }}</p>
          <p class="course-subtitle">{{ course.course_type }} · {{ course.instructor }}</p>
        </div>
        <button class="close-button" @click="$emit('close')">✕</button>
      </header>
      <div class="modal-body">
        <p>{{ course.summary }}</p>
        <dl>
          <div>
            <dt>学分</dt>
            <dd>{{ course.credits }}</dd>
          </div>
          <div>
            <dt>难度</dt>
            <dd>{{ course.level }}</dd>
          </div>
          <div>
            <dt>时间</dt>
            <dd>{{ course.schedule_display }}</dd>
          </div>
          <div>
            <dt>课程目标</dt>
            <dd>{{ course.objectives }}</dd>
          </div>
        </dl>
      </div>
      <footer class="modal-footer">
        <button type="button" @click="handleAdd">加入选课</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ course: Object, darkMode: Boolean })
const emit = defineEmits(['close', 'add-course'])

function handleAdd() {
  emit('add-course', props.course)
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.36);
  display: grid;
  place-items: center;
  padding: 20px;
  z-index: 30;
}

.modal-card {
  width: min(680px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  display: grid;
  gap: 18px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.82rem;
}

.course-code {
  margin: 8px 0 0;
  color: var(--muted);
}

.close-button {
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 1.35rem;
}

.modal-body {
  display: grid;
  gap: 18px;
  color: var(--text);
}

dl {
  display: grid;
  gap: 12px;
}

dt {
  font-weight: 700;
}

dd {
  margin: 0;
  color: var(--muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
}

.modal-footer button {
  padding: 14px 20px;
  border: none;
  border-radius: 16px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}
</style>
