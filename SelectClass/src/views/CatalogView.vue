<template>
  <section class="catalog-view">
    <div class="catalog-toolbar">
      <div class="search-wrap">
        <label for="course-search" class="screen-reader-only">搜索课程</label>
        <input
          id="course-search"
          v-model="localQuery"
          @input="emitSearch"
          placeholder="搜索课程、院系、老师或关键词"
        />
        <select v-model="localFilters.faculty" @change="emitFilters">
          <option value="All">全部院系</option>
          <option value="计算机学院">计算机学院</option>
          <option value="数学学院">数学学院</option>
          <option value="外国语学院">外国语学院</option>
          <option value="人文学院">人文学院</option>
          <option value="统计与数据科学学院">统计与数据科学学院</option>
        </select>
        <select v-model="localFilters.courseType" @change="emitFilters">
          <option value="All">全部类型</option>
          <option value="专业课">专业课</option>
          <option value="公共课">公共课</option>
        </select>
        <select v-model="localFilters.level" @change="emitFilters">
          <option value="All">全部难度</option>
          <option value="Beginner">入门</option>
          <option value="Intermediate">中级</option>
          <option value="Advanced">高级</option>
        </select>
      </div>
    </div>

    <div
      class="course-grid"
      @dragover.prevent
      @drop="handleDrop"
      aria-label="课程卡片列表"
    >
      <CourseCard
        v-for="course in filteredCourses"
        :key="course.id"
        :course="course"
        @add-course="$emit('add-course', $event)"
        @show-detail="$emit('show-detail', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import CourseCard from '../components/CourseCard.vue'

const props = defineProps({ courses: Array, filters: Object, searchQuery: String, darkMode: Boolean })
const emit = defineEmits(['update-filters', 'update-search', 'add-course', 'show-detail'])

const localFilters = ref({ ...props.filters })
const localQuery = ref(props.searchQuery)

watch(
  () => props.filters,
  (value) => {
    localFilters.value = { ...value }
  }
)

watch(
  () => props.searchQuery,
  (value) => {
    localQuery.value = value
  }
)

const filteredCourses = computed(() => {
  return props.courses.filter((course) => {
    const matchesQuery = [course.title, course.code, course.summary, course.faculty, course.course_type, course.instructor, course.keywords]
      .join(' ')
      .toLowerCase()
      .includes(props.searchQuery.toLowerCase())
    const matchesFaculty = props.filters.faculty === 'All' || course.faculty === props.filters.faculty
    const matchesType = props.filters.courseType === 'All' || course.course_type === props.filters.courseType
    const matchesLevel = props.filters.level === 'All' || course.level === props.filters.level
    const matchesCredit = props.filters.credit === 'All' || String(course.credits) === props.filters.credit
    return matchesQuery && matchesFaculty && matchesType && matchesLevel && matchesCredit
  })
})

function emitFilters() {
  emit('update-filters', { ...localFilters.value })
}

function emitSearch() {
  emit('update-search', localQuery.value)
}

function handleDrop(event) {
  const payload = event.dataTransfer.getData('application/course')
  if (!payload) return
  const course = JSON.parse(payload)
  emit('add-course', course)
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

@media (max-width: 640px) {
  .search-wrap input {
    flex: 1 1 100%;
  }

  .search-wrap select {
    flex: 1 1 calc(50% - 5px);
  }
}
</style>
