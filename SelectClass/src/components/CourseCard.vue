<template>
  <article class="course-card" :draggable="true" @dragstart="onDragStart" @click="emitDetail">
    <header class="course-card__header">
      <span class="course-tag">{{ course.faculty }}</span>
      <strong>{{ course.code }}</strong>
    </header>
    <h3>{{ course.title }}</h3>
    <p class="course-description">{{ course.summary }}</p>
    <div class="course-meta">
      <span>{{ course.credits }} 学分</span>
      <span>{{ course.level }}</span>
      <span>{{ course.course_type }}</span>
    </div>
    <div class="course-footer">
      <div>
        <p>{{ course.instructor }}</p>
        <p>{{ course.schedule_display || course.schedule }}</p>
      </div>
      <button type="button" @click.stop="addCourse">加入</button>
    </div>
  </article>
</template>

<script setup>
const props = defineProps({ course: Object })
const emit = defineEmits(['add-course', 'show-detail'])

function onDragStart(event) {
  event.dataTransfer.setData('application/course', JSON.stringify(props.course))
}

function addCourse() {
  emit('add-course', props.course)
}

function emitDetail() {
  emit('show-detail', props.course)
}
</script>

<style scoped>
.course-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.course-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.course-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.course-tag {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(63, 131, 248, 0.12);
  color: var(--primary);
  font-size: 0.78rem;
}

h3 {
  margin: 0;
  font-size: 1rem;
}

.course-description {
  margin: 0;
  color: var(--muted);
  font-size: 0.88rem;
  min-height: 36px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-meta {
  display: flex;
  gap: 10px;
  color: var(--muted);
  font-size: 0.82rem;
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.course-footer button {
  padding: 8px 14px;
  border: none;
  border-radius: 10px;
  background: var(--primary);
  color: white;
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
