<script lang="ts" setup>
import { ref, onMounted } from 'vue';

const sectionRef = ref<HTMLElement>();
const isVisible = ref(false);

const roadmapItems = ref([
  {
    phase: 'P1',
    status: 'development', // development, planned
    statusLabel: '开发中',
    title: '客户流失预警',
    description: 'AI 识别高危客户行为，提前预警流失风险，挽回高价值客户。',
    icon: '🚨',
    color: 'var(--lp-primary-500)',
  },
  {
    phase: 'P1',
    status: 'development',
    statusLabel: '开发中',
    title: '竞品分析',
    description: '自动收集竞品动态与差异化功能，辅助制定竞争策略。',
    icon: '🕵️',
    color: 'var(--lp-primary-600)',
  },
  {
    phase: 'P2',
    status: 'planned',
    statusLabel: '规划中',
    title: '语音识别',
    description: '会议录音直接转文字，自动提取其中的反馈点与需求。',
    icon: '🎙️',
    color: 'var(--lp-text-secondary)',
  },
  {
    phase: 'P2',
    status: 'planned',
    statusLabel: '规划中',
    title: '反馈预测',
    description: '基于历史数据趋势，预测未来可能爆发的需求热点。',
    icon: '🔮',
    color: 'var(--lp-text-secondary)',
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
  <section id="roadmap" ref="sectionRef" class="roadmap-section">
    <div class="section-container">
      <div class="section-header">
        <div class="section-badge">
          <span class="badge-icon">🚀</span>
          <span class="badge-text">未来规划</span>
        </div>
        <h2 class="section-title">
          持续进化的 <span class="title-gradient">AI 引擎</span>
        </h2>
        <p class="section-subtitle">
          我们正在构建更强大的功能，助你始终领先一步
        </p>
      </div>

      <div class="roadmap-container" :class="{ 'is-visible': isVisible }">
        <div class="roadmap-line"></div>

        <div
          v-for="(item, index) in roadmapItems"
          :key="index"
          class="roadmap-item"
          :class="`status-${item.status}`"
          :style="{ '--delay': `${index * 150}ms`, '--item-color': item.color }"
        >
          <div class="roadmap-dot">
            <div class="dot-inner"></div>
            <div class="dot-ring"></div>
          </div>

          <div class="roadmap-content">
            <div class="roadmap-meta">
              <span class="phase-badge">{{ item.phase }}</span>
              <span class="status-badge" :class="item.status">{{ item.statusLabel }}</span>
            </div>
            <h3 class="roadmap-title">
              <span class="title-icon">{{ item.icon }}</span>
              {{ item.title }}
            </h3>
            <p class="roadmap-desc">{{ item.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.roadmap-section {
  padding: 6rem 2rem;
  background: linear-gradient(to bottom, var(--lp-bg-main), var(--lp-bg-card-hover));
}

.section-container {
  max-width: 800px;
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
  background: hsla(220, 14%, 96%, 0.8);
  border: 1px solid hsla(220, 14%, 90%, 1);
  border-radius: 100px;
  margin-bottom: 1.5rem;
}

.badge-icon {
  font-size: 1rem;
}

.badge-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: hsla(220, 20%, 20%, 1);
}

.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: var(--lp-text-primary);
}

.title-gradient {
  color: var(--lp-primary-500);
}

.section-subtitle {
  font-size: 1.15rem;
  color: var(--lp-text-secondary);
}

/* Roadmap Timeline */
.roadmap-container {
  position: relative;
  padding-left: 2rem;
}

.roadmap-line {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--lp-border-subtle);
  border-radius: 2px;
}

/* Roadmap Item */
.roadmap-item {
  position: relative;
  margin-bottom: 3rem;
  padding-left: 2rem;
  opacity: 0;
  transform: translateX(-20px);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  transition-delay: var(--delay);
}

.roadmap-container.is-visible .roadmap-item {
  opacity: 1;
  transform: translateX(0);
}

.roadmap-item:last-child {
  margin-bottom: 0;
}

/* Dot */
.roadmap-dot {
  position: absolute;
  left: -2rem; /* Center on line (line is at 0 relative to child, but container has padding-left 2rem. So -2rem puts it at line) */
  left: -29px; /* Fine tuning based on padding: 2rem = 32px. Line width 2px. */
  top: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--lp-bg-main);
}

.dot-inner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--lp-border-default);
  z-index: 2;
  transition: all 0.3s ease;
}

.status-development .dot-inner {
  background: var(--lp-primary-500);
  box-shadow: 0 0 0 4px var(--lp-primary-100);
}

.status-planned .dot-inner {
  background: var(--lp-text-secondary);
}

/* Content Card */
.roadmap-content {
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-subtle);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.roadmap-item:hover .roadmap-content {
  transform: translateY(-4px);
  border-color: var(--lp-primary-200);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05);
}

.roadmap-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.phase-badge {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--lp-text-secondary);
  background: var(--lp-bg-subtle);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
}

.status-badge.development {
  background: var(--lp-primary-100);
  color: var(--lp-primary-600);
}

.status-badge.planned {
  background: var(--lp-bg-subtle);
  color: var(--lp-text-secondary);
}

.roadmap-title {
  font-family: var(--lp-font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--lp-text-primary);
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.roadmap-desc {
  font-size: 0.95rem;
  color: var(--lp-text-secondary);
  line-height: 1.6;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .roadmap-section {
    padding: 4rem 1.5rem;
  }
}
</style>
