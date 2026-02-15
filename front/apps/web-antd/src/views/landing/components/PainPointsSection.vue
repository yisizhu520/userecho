<script lang="ts" setup>
import { ref, onMounted } from 'vue';

const sectionRef = ref<HTMLElement>();
const isVisible = ref(false);

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
</script>

<template>
  <section id="pain-points" ref="sectionRef" class="pain-points-section">
    <div class="section-container">
      <div class="section-header">
        <h2 class="section-title">
          从<span class="title-text-wrong">混乱</span>到<span class="title-text-right">有序</span>
        </h2>
        <p class="section-subtitle">
          告别手动整理反馈的繁琐，让 AI 为你智能聚类
        </p>
      </div>

      <div class="comparison-container" :class="{ 'is-visible': isVisible }">
        <!-- Before -->
        <div class="comparison-panel panel-before">
          <div class="panel-header">
            <div class="panel-icon panel-icon-wrong">✗</div>
            <h3>传统方式</h3>
          </div>
          <div class="panel-content">
            <div class="feedback-scatter">
              <div class="scatter-item" style="top: 10%; left: 15%;">#128 登录报错</div>
              <div class="scatter-item" style="top: 25%; left: 60%;">#95 希望加暗色模式</div>
              <div class="scatter-item" style="top: 40%; left: 30%;">#156 页面加载慢</div>
              <div class="scatter-item" style="top: 55%; left: 75%;">#201 需要导出功能</div>
              <div class="scatter-item" style="top: 70%; left: 20%;">#88 登录按钮不明显</div>
              <div class="scatter-item" style="top: 15%; left: 80%;">#112 暗色主题</div>
              <div class="scatter-item" style="top: 85%; left: 65%;">#177 性能优化</div>
              <div class="scatter-item" style="top: 35%; left: 45%;">#134 导出Excel</div>
              <div class="scatter-item" style="top: 60%; left: 10%;">#99 登录问题</div>
              <div class="scatter-item" style="top: 80%; left: 40%;">#145 太慢了</div>
              <div class="scatter-item" style="top: 5%; left: 50%;">#167 黑色背景</div>
              <div class="scatter-item" style="top: 45%; left: 85%;">#123 数据导出</div>
            </div>
            <div class="panel-stats">
              <div class="stat-item">
                <span class="stat-value stat-wrong">8+ 小时</span>
                <span class="stat-label">整理时间</span>
              </div>
              <div class="stat-item">
                <span class="stat-value stat-wrong">60%</span>
                <span class="stat-label">遗漏率</span>
              </div>
            </div>
          </div>
          <div class="panel-footer">
            <div class="footer-item">
              <span class="footer-icon">✗</span>
              <span>手动分类耗时耗力</span>
            </div>
            <div class="footer-item">
              <span class="footer-icon">✗</span>
              <span>容易遗漏重要反馈</span>
            </div>
            <div class="footer-item">
              <span class="footer-icon">✗</span>
              <span>难以发现潜在趋势</span>
            </div>
          </div>
        </div>

        <!-- VS divider -->
        <div class="vs-divider">
          <div class="vs-circle">VS</div>
        </div>

        <!-- After -->
        <div class="comparison-panel panel-after">
          <div class="panel-header">
            <div class="panel-icon panel-icon-right">✓</div>
            <h3>Feedalyze</h3>
          </div>
          <div class="panel-content">
            <div class="cluster-container">
              <div class="cluster-group cluster-1">
                <div class="cluster-label">登录问题</div>
                <div class="cluster-dots">
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                </div>
              </div>
              <div class="cluster-group cluster-2">
                <div class="cluster-label">主题功能</div>
                <div class="cluster-dots">
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                </div>
              </div>
              <div class="cluster-group cluster-3">
                <div class="cluster-label">性能优化</div>
                <div class="cluster-dots">
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                </div>
              </div>
              <div class="cluster-group cluster-4">
                <div class="cluster-label">数据导出</div>
                <div class="cluster-dots">
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                  <div class="cluster-dot"></div>
                </div>
              </div>
            </div>
            <div class="panel-stats">
              <div class="stat-item">
                <span class="stat-value stat-right">&lt;30 分钟</span>
                <span class="stat-label">AI 自动聚类</span>
              </div>
              <div class="stat-item">
                <span class="stat-value stat-right">0%</span>
                <span class="stat-label">智能覆盖</span>
              </div>
            </div>
          </div>
          <div class="panel-footer">
            <div class="footer-item">
              <span class="footer-icon footer-icon-right">✓</span>
              <span>AI 语义自动聚类</span>
            </div>
            <div class="footer-item">
              <span class="footer-icon footer-icon-right">✓</span>
              <span>智能优先级评分</span>
            </div>
            <div class="footer-item">
              <span class="footer-icon footer-icon-right">✓</span>
              <span>洞察潜在需求趋势</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pain-points-section {
  position: relative;
  padding: 6rem 2rem;
  background: hsla(220, 20%, 6%, 0.5);
}

.pain-points-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, hsla(212, 100%, 45%, 0.3), transparent);
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
  font-family: 'Outfit', sans-serif;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 800;
  margin-bottom: 1rem;
  color: hsl(0, 0%, 100%);
}

.title-text-wrong {
  color: hsl(0, 84%, 65%);
  position: relative;
}

.title-text-wrong::after {
  content: '';
  position: absolute;
  bottom: 0.1em;
  left: 0;
  width: 100%;
  height: 0.1em;
  background: hsl(0, 84%, 65%);
  transform: rotate(-2deg);
}

.title-text-right {
  background: linear-gradient(135deg, hsl(144, 70%, 50%), hsl(188, 78%, 55%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-subtitle {
  font-size: 1.1rem;
  color: hsl(220, 10%, 70%);
}

/* Comparison */
.comparison-container {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 2rem;
  align-items: stretch;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s ease-out;
}

.comparison-container.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.comparison-panel {
  background: hsla(220, 20%, 10%, 0.8);
  border: 1px solid hsla(220, 20%, 20%, 0.5);
  border-radius: 20px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.comparison-panel:hover {
  transform: translateY(-4px);
}

.panel-before:hover {
  box-shadow: 0 10px 40px hsla(0, 84%, 65%, 0.15);
}

.panel-after:hover {
  box-shadow: 0 10px 40px hsla(144, 70%, 50%, 0.15);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid hsla(220, 20%, 20%, 0.3);
}

.panel-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1.1rem;
}

.panel-icon-wrong {
  background: hsla(0, 84%, 65%, 0.2);
  color: hsl(0, 84%, 65%);
}

.panel-icon-right {
  background: hsla(144, 70%, 50%, 0.2);
  color: hsl(144, 70%, 50%);
}

.panel-header h3 {
  font-family: 'Outfit', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: hsl(0, 0%, 100%);
}

.panel-content {
  padding: 1.5rem;
  min-height: 280px;
}

/* Before - Scatter */
.feedback-scatter {
  position: relative;
  height: 200px;
  background: hsla(220, 20%, 8%, 0.8);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.scatter-item {
  position: absolute;
  padding: 0.35rem 0.65rem;
  background: hsla(220, 20%, 15%, 0.9);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 6px;
  font-size: 0.75rem;
  color: hsl(220, 10%, 70%);
  white-space: nowrap;
  animation: float-scatter 4s ease-in-out infinite;
}

.scatter-item:nth-child(odd) {
  animation-delay: -2s;
}

@keyframes float-scatter {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-4px) rotate(1deg); }
}

/* After - Clusters */
.cluster-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.cluster-group {
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.cluster-1 {
  background: hsla(212, 100%, 45%, 0.1);
  border: 1px solid hsla(212, 100%, 45%, 0.3);
}

.cluster-2 {
  background: hsla(280, 70%, 55%, 0.1);
  border: 1px solid hsla(280, 70%, 55%, 0.3);
}

.cluster-3 {
  background: hsla(38, 92%, 60%, 0.1);
  border: 1px solid hsla(38, 92%, 60%, 0.3);
}

.cluster-4 {
  background: hsla(188, 78%, 55%, 0.1);
  border: 1px solid hsla(188, 78%, 55%, 0.3);
}

.cluster-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: hsl(0, 0%, 100%);
}

.cluster-dots {
  display: flex;
  gap: 0.35rem;
}

.cluster-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.6;
}

.cluster-1 .cluster-dot { background: hsl(212, 100%, 45%); }
.cluster-2 .cluster-dot { background: hsl(280, 70%, 55%); }
.cluster-3 .cluster-dot { background: hsl(38, 92%, 60%); }
.cluster-4 .cluster-dot { background: hsl(188, 78%, 55%); }

/* Stats */
.panel-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 1rem;
  border-top: 1px solid hsla(220, 20%, 20%, 0.3);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
}

.stat-wrong {
  color: hsl(0, 84%, 65%);
}

.stat-right {
  background: linear-gradient(135deg, hsl(144, 70%, 50%), hsl(188, 78%, 55%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.8rem;
  color: hsl(220, 10%, 60%);
}

/* Footer */
.panel-footer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  background: hsla(220, 20%, 8%, 0.5);
  border-top: 1px solid hsla(220, 20%, 20%, 0.3);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: hsl(220, 10%, 65%);
}

.footer-icon {
  color: hsl(0, 84%, 65%);
}

.footer-icon-right {
  color: hsl(144, 70%, 50%);
}

/* VS divider */
.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
}

.vs-circle {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, hsl(212, 100%, 45%), hsl(144, 70%, 50%));
  border-radius: 50%;
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 1.1rem;
  color: hsl(0, 0%, 100%);
  box-shadow: 0 4px 20px hsla(212, 100%, 45%, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .comparison-container {
    grid-template-columns: 1fr;
  }

  .vs-divider {
    order: 1;
    padding: 1rem 0;
  }

  .vs-circle {
    width: 48px;
    height: 48px;
    font-size: 1rem;
  }

  .panel-before {
    order: 2;
  }

  .panel-after {
    order: 3;
  }
}
</style>
