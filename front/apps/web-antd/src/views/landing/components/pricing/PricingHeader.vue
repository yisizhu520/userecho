<script lang="ts" setup>
// 定价标题区域组件
// 无需 props，纯展示组件
</script>

<template>
  <div class="pricing-header">
    <div class="section-badge">
      <span class="badge-dot"></span>
      <span class="badge-text">灵活定价</span>
    </div>
    <h2 class="section-title">选择适合您的<span class="title-highlight">方案</span></h2>
    <p class="section-subtitle">
      从小团队到大型企业，我们都有匹配的解决方案
    </p>
  </div>
</template>

<style scoped>
.pricing-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 100px;
  margin-bottom: 1.5rem;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: var(--lp-accent-cyan);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.badge-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--lp-text-secondary);
}

.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: var(--lp-text-primary);
}

.title-highlight {
  background: var(--lp-gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-subtitle {
  font-size: 1.1rem;
  color: var(--lp-text-tertiary);
  max-width: 500px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .section-subtitle {
    font-size: 1rem;
  }
}
</style>
