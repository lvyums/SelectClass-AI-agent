<template>
  <section class="catalog-view">
    <div class="catalog-toolbar">
      <div class="search-wrap">
        <label for="course-search" class="screen-reader-only">搜索课程</label>
        <input
          id="course-search"
          :value="courseStore.searchQuery"
          @input="courseStore.setSearchQuery($event.target.value)"
          placeholder="搜索课程、院系、老师或关键词"
        />
        <select :value="courseStore.filters.faculty" @change="courseStore.setFilters({ ...courseStore.filters, faculty: $event.target.value })">
          <option value="All">全部院系</option>
          <option v-for="f in faculties" :key="f" :value="f">{{ f }}</option>
        </select>
        <select :value="courseStore.filters.courseType" @change="courseStore.setFilters({ ...courseStore.filters, courseType: $event.target.value })">
          <option value="All">全部类型</option>
          <option value="专业课">专业课</option>
          <option value="公共课">公共课</option>
        </select>
        <select :value="courseStore.filters.level" @change="courseStore.setFilters({ ...courseStore.filters, level: $event.target.value })">
          <option value="All">全部难度</option>
          <option value="Beginner">入门</option>
          <option value="Intermediate">中级</option>
          <option value="Advanced">高级</option>
        </select>
      </div>
    </div>

    <div class="course-grid" @dragover.prevent @drop="handleDrop" aria-label="课程卡片列表">
      <CourseCard
        v-for="course in courseStore.filteredCourses"
        :key="course.id"
        :course="course"
        :is-selected="selectionStore.selectedCourses.some(c => c.id === course.id)"
        @add-course="handleAddCourse"
        @show-detail="courseStore.setActiveCourse"
      />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useCourseStore } from '../stores/courses'
import { useSelectionStore } from '../stores/selection'
import { extractErrorMessage } from '../api/request'
import CourseCard from '../components/CourseCard.vue'

const courseStore = useCourseStore()
const selectionStore = useSelectionStore()

const faculties = computed(() => {
  const set = new Set(courseStore.courses.map(c => c.faculty))
  return [...set].sort()
})

async function handleAddCourse(course) {
  try {
    await selectionStore.addCourse(course)
  } catch (err) {
    window.alert(extractErrorMessage(err, '添加课程失败'))
  }
}

function handleDrop(event) {
  const payload = event.dataTransfer.getData('application/course')
  if (!payload) return
  try {
    const course = JSON.parse(payload)
    if (course && course.id) {
      handleAddCourse(course)
    }
  } catch {
    // ignore invalid drag data
  }
}
</script>

<style scoped>
.catalog-view {
  display: grid;
  gap: 20px;
}

.catalog-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.search-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
}

.search-wrap input {
  flex: 1 1 240px;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: 0.9rem;
}

.search-wrap select {
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
  font-size: 0.9rem;
  min-width: 120px;
}

.course-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.screen-reader-only {
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

@media (max-width: 640px) {
  .search-wrap input {
    flex: 1 1 100%;
  }
  .search-wrap select {
    flex: 1 1 calc(50% - 5px);
  }
}
</style>
