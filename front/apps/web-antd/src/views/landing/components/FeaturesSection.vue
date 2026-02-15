<script lang="ts" setup>
import { ref, onMounted } from 'vue';

const sectionRef = ref<HTMLElement>();
const isVisible = ref(false);
const features = ref([
  {
    icon: 'lucide:sparkles',
    iconEmoji: '✨',
    title: 'AI 智能聚类',
    description: '使用语义相似度自动将反馈分组，无需手动分类，准确率高达95%',
    gradient: 'from-blue-500 to-cyan-500',
    color: 'hsl(212, 100%, 45%)',
    delay: 0,
  },
  {
    icon: 'lucide:sliders',
    iconEmoji: '📊',
    title: '优先级评分',
    description: '基于影响范围、商业价值和开发成本，自动计算需求优先级分数',
    gradient: 'from-amber-500 to-orange-500',
    color: 'hsl(38, 92%, 60%)',
    delay: 100,
  },
  {
    icon: 'lucide:scan',
    iconEmoji: '📸',
    title: '截图智能识别',
    description: '支持微信、小红书、App Store等平台的截图OCR识别',
    gradient: 'from-emerald-500 to-teal-500',
    color: 'hsl(144, 70%, 50%)',
    delay: 200,
  },
  {
    icon: 'lucide:search',
    iconEmoji: '🔍',
    title: '语义搜索',
    description: '自然语言搜索反馈，"用户说登录有问题"即可找到所有相关反馈',
    gradient: 'from-purple-500 to-pink-500',
    color: 'hsl(280, 70%, 55%)',
    delay: 300,
  },
]);

onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true;
        }
      });
    },
    { threshold: 0.1 }
  );

  if (sectionRef.value) {
    observer.observe(sectionRef.value);
  }
});
</script>

<template>
  <section id="features" ref="sectionRef" class="features-section">
    <div class="section-container">
      <div class="section-header">
        <div class="section-badge">
          <span class="badge-icon">⚡</span>
          <span class="badge-text">核心功能</span>
        </div>
        <h2 class="section-title">
          全能的<span class="title-gradient">反馈分析</span>工具
        </h2>
        <p class="section-subtitle">
          四大核心能力，让产品决策更加智能高效
        </p>
      </div>

      <div class="features-grid" :class="{ 'is-visible': isVisible }">
        <div
          v-for="(feature, index) in features"
          :key="index"
          class="feature-card"
          :style="{ '--delay': `${feature.delay}ms`, '--feature-color': feature.color }"
        >
          <div class="feature-card-inner">
            <div class="feature-icon-wrapper">
              <span class="feature-icon-emoji">{{ feature.iconEmoji }}</span>
              <div class="feature-icon-glow" :style="{ background: feature.color }"></div>
            </div>

            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>

            <div class="feature-divider"></div>

            <div class="feature-list">
              <div class="feature-list-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>智能分析</span>
              </div>
              <div class="feature-list-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>实时更新</span>
              </div>
              <div class="feature-list-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>一键导出</span>
              </div>
            </div>
          </div>

          <!-- Background decoration -->
          <div class="card-bg-gradient"></div>
          <div class="card-bg-grid"></div>
        </div>
      </div>

      <!-- Feature highlight banner -->
      <div class="feature-banner" :class="{ 'is-visible': isVisible }">
        <div class="banner-content">
          <div class="banner-text">
            <span class="banner-icon">🚀</span>
            <span>处理 100+ 条反馈只需不到 30 秒</span>
          </div>
          <div class="banner-stats">
            <div class="banner-stat">
              <span class="banner-stat-value">10x</span>
              <span class="banner-stat-label">效率提升</span>
            </div>
            <div class="banner-stat-divider"></div>
            <div class="banner-stat">
              <span class="banner-stat-value">95%</span>
              <span class="banner-stat-label">准确率</span>
            </div>
            <div class="banner-stat-divider"></div>
            <div class="banner-stat">
              <span class="banner-stat-value">&lt;30s</span>
              <span class="banner-stat-label">处理时间</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.features-section {
  position: relative;
  padding: 6rem 2rem;
  overflow: hidden;
}

.features-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 100px;
  background: linear-gradient(to bottom, transparent, hsla(212, 100%, 45%, 0.3));
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: hsla(220, 20%, 15%, 0.8);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 100px;
  margin-bottom: 1.5rem;
}

.badge-icon {
  font-size: 1rem;
}

.badge-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #94a3b8;
}

.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: #ffffff;
}

.title-gradient {
  background: linear-gradient(135deg, #00e5ff 0%, #06b6d4 50%, #10b981 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-subtitle {
  font-size: 1.15rem;
  color: #cbd5e1;
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.feature-card {
  position: relative;
  min-height: 280px;
  border-radius: 20px;
  overflow: hidden;
  opacity: 0;
  transform: translateY(40px);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  transition-delay: var(--delay);
}

.features-grid.is-visible .feature-card {
  opacity: 1;
  transform: translateY(0);
}

.feature-card:hover {
  transform: translateY(-8px);
}

.feature-card:hover .feature-card-inner {
  background: rgba(26, 32, 66, 0.95);
}

.feature-card-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  padding: 2rem;
  background: rgba(15, 20, 41, 0.9);
  border: 1px solid rgba(0, 229, 255, 0.15);
  border-radius: 20px;
  transition: all 0.3s ease;
  backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
}

.feature-icon-wrapper {
  position: relative;
  width: 64px;
  height: 64px;
  margin-bottom: 1.5rem;
}

.feature-icon-emoji {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 2rem;
  background: rgba(26, 32, 66, 0.9);
  border-radius: 16px;
  border: 1px solid rgba(0, 229, 255, 0.25);
}

.feature-icon-glow {
  position: absolute;
  inset: -8px;
  border-radius: 24px;
  opacity: 0.3;
  filter: blur(16px);
  transition: opacity 0.3s ease;
}

.feature-card:hover .feature-icon-glow {
  opacity: 0.5;
}

.feature-title {
  font-family: var(--lp-font-display);
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.75rem;
}

.feature-description {
  font-size: 0.95rem;
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

.feature-divider {
  height: 1px;
  background: linear-gradient(90deg, var(--feature-color), transparent);
  margin-bottom: 1.25rem;
  opacity: 0.5;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.feature-list-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #94a3b8;
}

.feature-list-item svg {
  color: var(--feature-color);
  flex-shrink: 0;
}

/* Card backgrounds */
.card-bg-gradient {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 0%, var(--feature-color), transparent 70%);
  opacity: 0.05;
  transition: opacity 0.3s ease;
}

.feature-card:hover .card-bg-gradient {
  opacity: 0.1;
}

.card-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.5;
}

/* Banner */
.feature-banner {
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.6s ease 0.3s;
}

.feature-banner.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.banner-content {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 20px;
  padding: 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1.5rem;
  backdrop-filter: blur(12px);
}

.banner-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: hsl(0, 0%, 100%);
}

.banner-icon {
  font-size: 1.5rem;
}

.banner-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.banner-stat {
  text-align: center;
}

.banner-stat-value {
  display: block;
  font-family: 'Outfit', sans-serif;
  font-size: 1.75rem;
  font-weight: 800;
  background: linear-gradient(135deg, hsl(212, 100%, 55%), hsl(144, 70%, 50%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.banner-stat-label {
  font-size: 0.75rem;
  color: hsl(220, 10%, 60%);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.banner-stat-divider {
  width: 1px;
  height: 32px;
  background: hsla(220, 20%, 25%, 0.5);
}

/* Responsive */
@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .banner-content {
    flex-direction: column;
    text-align: center;
  }

  .banner-text {
    justify-content: center;
  }

  .banner-stats {
    justify-content: center;
  }
}
</style>
