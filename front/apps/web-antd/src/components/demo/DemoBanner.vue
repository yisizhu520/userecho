<script setup lang="ts">
import { Info } from 'lucide-vue-next';
</script>

<template>
  <div class="demo-banner">
    <Info class="icon" :size="16" />
    <span class="banner-text">🔬 演示模式 - 数据每日凌晨 2 点自动重置</span>
    <a href="https://huixiang.app/auth/register" target="_blank" class="register-link">
      注册正式版
    </a>
  </div>
</template>

<style scoped>
.demo-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  color: white;
  font-size: 13px;
  padding: 8px 16px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.icon {
  flex-shrink: 0;
}

.banner-text {
  flex-shrink: 0;
}

.register-link {
  color: white;
  font-weight: 600;
  text-decoration: underline;
  margin-left: 8px;
  white-space: nowrap;
}

.register-link:hover {
  opacity: 0.9;
}
</style>
