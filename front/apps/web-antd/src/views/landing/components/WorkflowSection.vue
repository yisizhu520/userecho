<script lang="ts" setup>
import { ref, onMounted } from 'vue';

const sectionRef = ref<HTMLElement>();
const isVisible = ref(false);
const activeStep = ref(0);

const steps = ref([
  {
    // Professional blue/slate palette
    number: '01',
    title: '导入反馈',
    description: '支持 Excel/CSV 批量导入，或使用截图识别功能从社交媒体直接采集',
    icon: '📥',
    color: 'var(--lp-primary-500)',
  },
  {
    number: '02',
    title: 'AI 处理',
    description: '自动语义聚类、智能标签分类、优先级评分，全方位分析反馈',
    icon: '🤖',
    color: 'var(--lp-primary-600)',
  },
  {
    number: '03',
    title: '获得洞察',
    description: '可视化展示反馈趋势、主题分布、客户分层，一目了然',
    icon: '💡',
    color: 'var(--lp-primary-500)',
  },
  {
    number: '04',
    title: '智能决策',
    description: '基于数据驱动做出产品决策，优先处理高价值需求',
    icon: '🎯',
    color: 'var(--lp-primary-700)',
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
    { threshold: 0.2 }
  );

  if (sectionRef.value) {
    observer.observe(sectionRef.value);
  }
});

const setStep = (index: number) => {
  activeStep.value = index;
};
</script>

<template>
  <section id="workflow" ref="sectionRef" class="workflow-section">
    <div class="section-container">
      <div class="section-header">
        <h2 class="section-title">
          简单<span class="title-accent">四步</span>，从反馈到洞察
        </h2>
        <p class="section-subtitle">
          无需复杂配置，导入即用，AI 自动完成分析
        </p>
      </div>

      <div class="workflow-container" :class="{ 'is-visible': isVisible }">
        <!-- Steps navigation -->
        <div class="steps-nav">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{ 'is-active': activeStep === index }"
            @click="setStep(index)"
            @mouseenter="setStep(index)"
          >
            <div class="step-number" :style="{ '--step-color': step.color }">
              {{ step.number }}
            </div>
            <div class="step-info">
              <span class="step-icon">{{ step.icon }}</span>
              <span class="step-title">{{ step.title }}</span>
            </div>
          </div>
        </div>

        <!-- Step detail -->
        <div class="step-detail">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-content"
            :class="{ 'is-active': activeStep === index }"
          >
            <div class="step-visual" :style="{ '--step-color': step.color }">
              <div class="step-visual-circle">
                <span class="step-visual-icon">{{ step.icon }}</span>
                <div class="step-visual-glow"></div>
              </div>
              <div class="step-visual-ring"></div>
              <div class="step-visual-ring step-visual-ring-2"></div>
            </div>

            <div class="step-text">
              <h3 class="step-content-title">{{ step.title }}</h3>
              <p class="step-content-description">{{ step.description }}</p>

              <div class="step-features">
                <div class="step-feature">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>自动化处理</span>
                </div>
                <div class="step-feature">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>实时同步</span>
                </div>
                <div class="step-feature">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>智能分析</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Connection line -->
        <div class="connection-line">
          <div class="connection-progress" :style="{ width: `${(activeStep + 1) * 25}%` }"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.workflow-section {
  position: relative;
  padding: 6rem 2rem;
  background: var(--lp-bg-secondary);
}

.workflow-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, hsla(144, 70%, 50%, 0.3), transparent);
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: var(--lp-text-primary);
}

.title-accent {
  color: var(--lp-primary-500);
  /* Removed gradient text */
}

.section-subtitle {
  font-size: 1.1rem;
  color: var(--lp-text-tertiary);
}

/* Workflow */
.workflow-container {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s ease-out;
}

.workflow-container.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.steps-nav {
  display: flex;
  justify-content: space-between;
  margin-bottom: 3rem;
  position: relative;
  z-index: 2;
}

.step-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.step-item:hover {
  transform: translateY(-4px);
}

.step-number {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--lp-font-display);
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
  background: var(--step-color);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.step-item.is-active .step-number {
  transform: scale(1.1);
}

.step-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.step-icon {
  font-size: 1.5rem;
}

.step-title {
  font-family: var(--lp-font-display);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--lp-text-tertiary);
  transition: color 0.3s ease;
}

.step-item.is-active .step-title {
  color: var(--lp-text-primary);
}

/* Connection line */
.connection-line {
  position: absolute;
  top: 56px;
  left: 10%;
  right: 10%;
  height: 4px;
  background: var(--lp-bg-card);
  border-radius: 2px;
  overflow: hidden;
  z-index: 1;
}

.connection-progress {
  height: 100%;
  background: var(--lp-gradient-primary);
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Step detail */
.step-detail {
  position: relative;
  min-height: 280px;
}

.step-content {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 3rem;
  align-items: center;
  opacity: 0;
  transform: translateX(30px);
  transition: all 0.5s ease;
  pointer-events: none;
}

.step-content.is-active {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.step-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
}

.step-visual-circle {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--lp-bg-card);
  border: 2px solid var(--step-color);
  border-radius: 50%;
  z-index: 2;
}

.step-visual-icon {
  font-size: 3rem;
}

.step-visual-glow {
  position: absolute;
  inset: -20px;
  background: var(--step-color);
  border-radius: 50%;
  opacity: 0.1;
  filter: blur(24px);
  animation: glow-pulse 2s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(1.05); }
}

.step-visual-ring {
  position: absolute;
  width: 200px;
  height: 200px;
  border: 1px solid var(--step-color);
  border-radius: 50%;
  opacity: 0.3;
  animation: ring-rotate 10s linear infinite;
}

.step-visual-ring-2 {
  width: 240px;
  height: 240px;
  opacity: 0.15;
  animation-direction: reverse;
  animation-duration: 15s;
}

@keyframes ring-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Step text */
.step-text {
  padding: 2rem;
}

.step-content-title {
  font-family: var(--lp-font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--lp-text-primary);
  margin-bottom: 1rem;
}

.step-content-description {
  font-size: 1.1rem;
  color: var(--lp-text-tertiary);
  line-height: 1.7;
  margin-bottom: 2rem;
}

.step-features {
  display: flex;
  gap: 2rem;
}

.step-feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--lp-text-tertiary);
}

.step-feature svg {
  color: #10b981;
}

/* Responsive */
@media (max-width: 768px) {
  .steps-nav {
    flex-wrap: wrap;
    gap: 1rem;
  }

  .step-item {
    flex: 0 0 calc(50% - 0.5rem);
  }

  .connection-line {
    display: none;
  }

  .step-content {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .step-visual {
    height: 180px;
  }

  .step-visual-circle {
    width: 100px;
    height: 100px;
  }

  .step-visual-icon {
    font-size: 2rem;
  }

  .step-visual-ring {
    width: 140px;
    height: 140px;
  }

  .step-visual-ring-2 {
    width: 170px;
    height: 170px;
  }

  .step-features {
    justify-content: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .step-content-title {
    font-size: 1.5rem;
  }

  .step-content-description {
    font-size: 1rem;
  }
}
</style>
