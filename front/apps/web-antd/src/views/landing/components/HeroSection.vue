<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, computed } from 'vue';
import { useLandingTheme } from '#/composables/useLandingTheme';

interface Props {
  title?: string;
  subtitle?: string;
  description?: string;
}

withDefaults(defineProps<Props>(), {
  title: '用户反馈的',
  subtitle: 'AI 智能引擎',
  description: '10倍速度洞察需求 | 产品经理的决策外脑',
});

const emit = defineEmits<{
  (e: 'getStarted'): void;
}>();

const { theme } = useLandingTheme();
const canvasRef = ref<HTMLCanvasElement>();
const animationId = ref<number>();

const isDark = computed(() => theme.value === 'dark');

// Split description for better styling
const descriptionParts = [
  '10倍速度洞察需求',
  '产品经理的决策外脑'
];

// Particle colors for each theme
// Particle colors for each theme - Professional Blue Palette
  const getParticleColors = (dark: boolean) => {
    if (dark) {
      return [
        'rgba(59, 130, 246, 0.8)',   // Blue 500
        'rgba(37, 99, 235, 0.8)',    // Blue 600
        'rgba(96, 165, 250, 0.8)',   // Blue 400
        'rgba(147, 197, 253, 0.6)',  // Blue 300
        'rgba(255, 255, 255, 0.4)',  // White accent
      ];
    } else {
      // Light theme
      return [
        'rgba(29, 78, 216, 0.8)',    // Blue 700
        'rgba(37, 99, 235, 0.8)',    // Blue 600
        'rgba(59, 130, 246, 0.8)',   // Blue 500
        'rgba(96, 165, 250, 0.6)',   // Blue 400
        'rgba(15, 23, 42, 0.3)',     // Slate accent
      ];
    }
  };

// Particle class for cluster animation
class Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  targetX: number;
  targetY: number;
  clusterId: number;
  size: number;
  color: string;
  particleColors: string[];

  constructor(x: number, y: number, clusterId: number, colors: string[]) {
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 2;
    this.vy = (Math.random() - 0.5) * 2;
    this.targetX = x;
    this.targetY = y;
    this.clusterId = clusterId;
    this.size = Math.random() * 4 + 3;
    this.particleColors = colors;
    this.color = this.getClusterColor(clusterId);
  }

  getClusterColor(id: number): string {
    return this.particleColors[id % this.particleColors.length];
  }

  updateColors(colors: string[]) {
    this.particleColors = colors;
    this.color = this.getClusterColor(this.clusterId);
  }

  update(clustering: boolean, progress: number) {
    if (clustering) {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;
      this.vx += dx * 0.02 * progress;
      this.vy += dy * 0.02 * progress;
      this.vx *= 0.92;
      this.vy *= 0.92;
    } else {
      this.vx += (Math.random() - 0.5) * 0.3;
      this.vy += (Math.random() - 0.5) * 0.3;
      this.vx *= 0.98;
      this.vy *= 0.98;
    }

    this.x += this.vx;
    this.y += this.vy;

    if (this.x < 20) this.vx = Math.abs(this.vx);
    if (this.x > 380) this.vx = -Math.abs(this.vx);
    if (this.y < 20) this.vy = Math.abs(this.vy);
    if (this.y > 380) this.vy = -Math.abs(this.vy);
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size * 2, 0, Math.PI * 2);
    const gradient = ctx.createRadialGradient(
      this.x,
      this.y,
      0,
      this.x,
      this.y,
      this.size * 2
    );
    gradient.addColorStop(0, this.color.replace('0.9', '0.3').replace('0.85', '0.25'));
    gradient.addColorStop(1, 'transparent');
    ctx.fillStyle = gradient;
    ctx.fill();
  }
}

let particles: Particle[] = [];
let clusters: { x: number; y: number }[] = [];
let isClustering = true;
let clusterProgress = 0;
let animationTime = 0;

const initParticles = () => {
  const colors = getParticleColors(isDark.value);

  particles = [];
  clusters = [
    { x: 100, y: 120 },
    { x: 280, y: 100 },
    { x: 180, y: 250 },
    { x: 320, y: 280 },
    { x: 80, y: 300 },
  ];

  clusters.forEach((cluster, clusterId) => {
    const particleCount = 8 + Math.floor(Math.random() * 6);
    for (let i = 0; i < particleCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * 40;
      const x = cluster.x + Math.cos(angle) * radius;
      const y = cluster.y + Math.sin(angle) * radius;
      const particle = new Particle(x, y, clusterId, colors);
      particle.targetX = cluster.x + (Math.random() - 0.5) * 30;
      particle.targetY = cluster.y + (Math.random() - 0.5) * 30;
      particles.push(particle);
    }
  });

  for (let i = 0; i < 12; i++) {
    const x = Math.random() * 360 + 20;
    const y = Math.random() * 360 + 20;
    const particle = new Particle(x, y, Math.floor(Math.random() * clusters.length), colors);
    particles.push(particle);
  }
};

// Update particle colors when theme changes
watch(theme, () => {
  const colors = getParticleColors(isDark.value);
  particles.forEach(p => p.updateColors(colors));
});

const animate = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dark = isDark.value;

  // Clear canvas with theme-aware background
  ctx.fillStyle = dark ? 'rgba(15, 20, 41, 0.15)' : 'rgba(255, 255, 255, 0.5)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  animationTime += 0.016;
  if (animationTime > 5) {
    animationTime = 0;
    isClustering = !isClustering;
    clusterProgress = 0;
  }

  if (isClustering && clusterProgress < 1) {
    clusterProgress += 0.008;
  } else if (!isClustering && clusterProgress > 0) {
    clusterProgress -= 0.008;
  }
  clusterProgress = Math.max(0, Math.min(1, clusterProgress));

  particles.forEach((p1, i) => {
    particles.slice(i + 1).forEach((p2) => {
      if (p1.clusterId === p2.clusterId) {
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
        if (dist < 60) {
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          const alpha = (1 - dist / 60) * 0.3 * clusterProgress;
          ctx.strokeStyle = p1.color.replace('0.9', String(alpha)).replace('0.85', String(alpha));
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    });
  });

  particles.forEach((particle) => {
    particle.update(isClustering, clusterProgress);
    particle.draw(ctx);
  });

  if (clusterProgress > 0.5) {
    const labels = ['性能问题', '新功能', 'UI优化', 'Bug修复', '体验改进'];
    const labelAlpha = (clusterProgress - 0.5) * 2;
    clusters.forEach((cluster, i) => {
      ctx.font = '600 12px "Outfit", sans-serif';
      ctx.fillStyle = dark
        ? `rgba(255, 255, 255, ${labelAlpha * 0.7})`
        : `rgba(15, 23, 42, ${labelAlpha * 0.7})`;
      ctx.textAlign = 'center';
      ctx.fillText(labels[i], cluster.x, cluster.y + 5);
    });
  }

  animationId.value = requestAnimationFrame(animate);
};

onMounted(() => {
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.width = 400;
    canvas.height = 400;
    initParticles();
    animate();
  }
});

onUnmounted(() => {
  if (animationId.value) {
    cancelAnimationFrame(animationId.value);
  }
});
</script>

<template>
  <section class="hero-section">
    <div class="hero-container">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span class="badge-text">AI 驱动的反馈分析</span>
        </div>

        <h1 class="hero-title">
          <span class="title-line">{{ title }}</span>
          <span class="title-highlight">{{ subtitle }}</span>
        </h1>

        <p class="hero-description">
          <span class="desc-main">10倍速度洞察需求</span>
          <span class="desc-divider"> — </span>
          <span class="desc-sub">产品经理的决策外脑</span>
        </p>

        <div class="hero-actions">
          <button class="btn-primary" @click="emit('getStarted')">
            <span>开始使用</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
          <button class="btn-secondary">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
            <span>观看演示</span>
          </button>
        </div>

        <div class="hero-features">
          <div class="feature-tag">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>AI 聚类</span>
          </div>
          <div class="feature-tag">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>智能评分</span>
          </div>
          <div class="feature-tag">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>截图识别</span>
          </div>
          <div class="feature-tag">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>语义搜索</span>
          </div>
        </div>
      </div>

      <div class="hero-visual">
        <div class="canvas-container">
          <canvas ref="canvasRef" class="cluster-canvas"></canvas>
          <div class="canvas-overlay">
            <div class="overlay-stat">
              <span class="stat-value">10x</span>
              <span class="stat-label">处理速度</span>
            </div>
            <div class="overlay-ring"></div>
          </div>
        </div>

        <div class="floating-card card-1">
          <div class="card-icon">✓</div>
          <div class="card-content">
            <div class="card-title">已聚类</div>
            <div class="card-value">127 条反馈</div>
          </div>
        </div>
        <div class="floating-card card-2">
          <div class="card-icon">⚡</div>
          <div class="card-content">
            <div class="card-title">高优先级</div>
            <div class="card-value">8 个主题</div>
          </div>
        </div>
      </div>
    </div>

    <div class="scroll-indicator">
      <div class="scroll-line"></div>
      <div class="scroll-text">向下滚动</div>
    </div>
  </section>
</template>

<style scoped>
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6rem 2rem 4rem;
  overflow: hidden;
  background: transparent;
}

/* Circuit board pattern */
.hero-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--lp-circuit-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--lp-circuit-line) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.5;
}

.hero-section::after {
  content: '';
  position: absolute;
  top: -20%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--lp-glow-cyan) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(100px);
  animation: float-glow 20s ease-in-out infinite;
}

@keyframes float-glow {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
  50% { transform: translate(20px, -10px) scale(1.05); opacity: 0.2; }
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  position: relative;
  z-index: 1;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 100px;
  width: fit-content;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #60a5fa;
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

.hero-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.title-line {
  display: block;
  color: var(--lp-text-primary);
}

.title-highlight {
  display: block;
  background: var(--lp-gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  /* Removed strong drop-shadow for cleaner look */
}

.hero-description {
  font-size: 1.25rem;
  line-height: 1.6;
  max-width: 480px;
}

.desc-main {
  color: var(--lp-text-primary);
  font-weight: 500;
}

.desc-divider {
  color: var(--lp-text-tertiary);
  margin: 0 0.3rem;
}

.desc-sub {
  color: var(--lp-text-secondary);
}

.hero-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1rem 2rem;
  background: var(--lp-gradient-cool);
  border: none;
  border-radius: 12px;
  color: #ffffff;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px var(--lp-glow-cyan);
}

.btn-primary svg {
  color: #ffffff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px var(--lp-glow-primary);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1rem 1.75rem;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 12px;
  color: var(--lp-text-primary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}

.btn-secondary:hover {
  background: var(--lp-bg-card-hover);
  border-color: var(--lp-accent-cyan);
}

.hero-features {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.5rem;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--lp-text-secondary);
}

.feature-tag svg {
  color: var(--lp-accent-cyan-bright);
}

.hero-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-container {
  position: relative;
  width: 400px;
  height: 400px;
  background: var(--lp-canvas-bg);
  border: 1px solid var(--lp-border-default);
  border-radius: 24px;
  backdrop-filter: blur(12px);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.1),
    0 0 80px var(--lp-glow-cyan),
    inset 0 1px 0 var(--lp-border-subtle);
  transition: all 0.3s ease;
}

.cluster-canvas {
  width: 100%;
  height: 100%;
  border-radius: 24px;
}

.canvas-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.overlay-stat {
  text-align: center;
  z-index: 1;
}

.stat-value {
  display: block;
  font-family: var(--lp-font-display);
  font-size: 4rem;
  font-weight: 900;
  background: var(--lp-gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-clip: text;
  /* Removed text-shadow for professional clean look */
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--lp-text-tertiary);
  font-weight: 500;
  letter-spacing: 0.05em;
}

.overlay-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 180px;
  height: 180px;
  border: 2px solid var(--lp-border-default);
  border-radius: 50%;
  animation: ring-pulse 3s ease-in-out infinite;
  box-shadow: 0 0 30px var(--lp-glow-cyan);
}

@keyframes ring-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  50% { transform: translate(-50%, -50%) scale(1.08); opacity: 0.3; }
}

.floating-card {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  background: var(--lp-bg-elevated);
  border: 1px solid var(--lp-border-default);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 0 20px var(--lp-glow-cyan);
  animation: float-card 6s ease-in-out infinite;
}

.card-1 {
  top: 10%;
  right: -20px;
}

.card-2 {
  bottom: 15%;
  left: -30px;
  animation-delay: -3s;
}

@keyframes float-card {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--lp-gradient-cool);
  border-radius: 10px;
  font-size: 1.1rem;
  color: #ffffff;
  font-weight: 800;
  color: #ffffff;
  font-weight: 800;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2);
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 0.75rem;
  color: var(--lp-text-tertiary);
  font-weight: 500;
}

.card-value {
  font-family: var(--lp-font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--lp-text-primary);
}

.scroll-indicator {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(8px); }
}

.scroll-line {
  width: 1px;
  height: 32px;
  background: linear-gradient(to bottom, #3b82f6, transparent);
}

.scroll-text {
  font-size: 0.75rem;
  color: var(--lp-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

@media (max-width: 968px) {
  .hero-container {
    grid-template-columns: 1fr;
    gap: 3rem;
  }

  .hero-visual {
    order: -1;
  }

  .canvas-container {
    width: 320px;
    height: 320px;
  }

  .floating-card {
    display: none;
  }
}

@media (max-width: 640px) {
  .hero-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}
</style>
