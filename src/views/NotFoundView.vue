<template>
  <div class="not-found">
    <h2>404</h2>
    <p>页面未找到</p>
    <button @click="router.push('/')">返回首页</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.not-found {
  display: grid;
  place-items: center;
  min-height: 60vh;
  text-align: center;
}

.not-found h2 {
  font-size: 4rem;
  margin: 0;
  color: var(--muted);
}

.not-found p {
  color: var(--muted);
  margin: 8px 0 20px;
}

.not-found button {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}
</style>
