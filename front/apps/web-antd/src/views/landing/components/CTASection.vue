<script lang="ts" setup>
interface Props {
  title?: string;
  subtitle?: string;
  ctaText?: string;
}

withDefaults(defineProps<Props>(), {
  title: '准备好提升产品决策效率了吗？',
  subtitle: '加入数千名产品经理的行列，开始使用 AI 驱动的反馈分析',
  ctaText: '免费开始使用',
});

const emit = defineEmits<{
  (e: 'getStarted'): void;
}>();
</script>

<template>
  <section class="cta-section">
    <div class="cta-container">
      <!-- Background effects -->
      <div class="cta-bg-gradient"></div>
      <div class="cta-bg-grid"></div>
      <div class="cta-glow cta-glow-1"></div>
      <div class="cta-glow cta-glow-2"></div>

      <div class="cta-content">
        <div class="cta-badge">
          <span class="cta-badge-dot"></span>
          <span class="cta-badge-text">立即开始</span>
        </div>

        <h2 class="cta-title">{{ title }}</h2>
        <p class="cta-subtitle">{{ subtitle }}</p>

        <div class="cta-actions">
          <button class="cta-primary" @click="emit('getStarted')">
            <span>{{ ctaText }}</span>
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
          <button class="cta-secondary">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <span>预约演示</span>
          </button>
        </div>

        <div class="cta-features">
          <div class="cta-feature">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>免费试用 14 天</span>
          </div>
          <div class="cta-feature">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>无需信用卡</span>
          </div>
          <div class="cta-feature">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>随时取消</span>
          </div>
        </div>
      </div>

      <!-- Floating elements -->
      <div class="cta-float cta-float-1">
        <div class="float-card">
          <span class="float-value">127</span>
          <span class="float-label">反馈已聚类</span>
        </div>
      </div>
      <div class="cta-float cta-float-2">
        <div class="float-card">
          <span class="float-value">8</span>
          <span class="float-label">高优先主题</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cta-section {
  position: relative;
  padding: 6rem 2rem;
  overflow: hidden;
}

.cta-container {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  background: hsla(220, 20%, 10%, 0.8);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 32px;
  overflow: hidden;
  backdrop-filter: blur(12px);
}

/* Background effects */
.cta-bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, hsla(212, 100%, 45%, 0.15) 0%, hsla(144, 70%, 50%, 0.1) 100%);
}

.cta-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(hsla(220, 20%, 20%, 0.2) 1px, transparent 1px),
    linear-gradient(90deg, hsla(220, 20%, 20%, 0.2) 1px, transparent 1px);
  background-size: 40px 40px;
}

.cta-glow {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}

.cta-glow-1 {
  top: -200px;
  left: -100px;
  background: hsl(212, 100%, 45%);
}

.cta-glow-2 {
  bottom: -200px;
  right: -100px;
  background: hsl(144, 70%, 50%);
}

.cta-content {
  position: relative;
  z-index: 1;
  padding: 4rem 3rem;
  text-align: center;
}

.cta-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: hsla(220, 20%, 15%, 0.8);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 100px;
  margin-bottom: 2rem;
}

.cta-badge-dot {
  width: 6px;
  height: 6px;
  background: hsl(144, 70%, 50%);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.cta-badge-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: hsl(220, 10%, 70%);
}

.cta-title {
  font-family: 'Outfit', sans-serif;
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: hsl(0, 0%, 100%);
}

.cta-subtitle {
  font-size: 1.1rem;
  color: hsl(220, 10%, 70%);
  max-width: 600px;
  margin: 0 auto 2.5rem;
  line-height: 1.6;
}

.cta-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}

.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, hsl(212, 100%, 45%) 0%, hsl(212, 100%, 35%) 100%);
  border: none;
  border-radius: 12px;
  color: hsl(0, 0%, 100%);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px hsla(212, 100%, 45%, 0.4);
}

.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px hsla(212, 100%, 45%, 0.5);
}

.cta-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.75rem;
  background: hsla(220, 20%, 15%, 0.8);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 12px;
  color: hsl(0, 0%, 100%);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-secondary:hover {
  background: hsla(220, 20%, 18%, 0.9);
  border-color: hsla(212, 100%, 45%, 0.5);
}

.cta-features {
  display: flex;
  gap: 2rem;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: hsl(220, 10%, 65%);
}

.cta-feature svg {
  color: hsl(144, 70%, 50%);
}

/* Floating elements */
.cta-float {
  position: absolute;
  animation: float-cta 6s ease-in-out infinite;
}

.cta-float-1 {
  top: 2rem;
  right: 3rem;
}

.cta-float-2 {
  bottom: 2rem;
  left: 3rem;
  animation-delay: -3s;
}

@keyframes float-cta {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.float-card {
  padding: 0.75rem 1rem;
  background: hsla(220, 20%, 15%, 0.9);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  backdrop-filter: blur(8px);
}

.float-value {
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, hsl(212, 100%, 55%), hsl(144, 70%, 50%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.float-label {
  font-size: 0.75rem;
  color: hsl(220, 10%, 60%);
}

/* Responsive */
@media (max-width: 640px) {
  .cta-content {
    padding: 3rem 2rem;
  }

  .cta-actions {
    flex-direction: column;
  }

  .cta-primary,
  .cta-secondary {
    width: 100%;
    justify-content: center;
  }

  .cta-float {
    display: none;
  }
}
</style>
