<script lang="ts" setup>
import { onMounted, onUnmounted, ref } from 'vue';

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

const canvasRef = ref<HTMLCanvasElement>();
const animationId = ref<number>();

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

  constructor(x: number, y: number, clusterId: number) {
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 2;
    this.vy = (Math.random() - 0.5) * 2;
    this.targetX = x;
    this.targetY = y;
    this.clusterId = clusterId;
    this.size = Math.random() * 4 + 3;
    this.color = this.getClusterColor(clusterId);
  }

  getClusterColor(id: number): string {
    const colors = [
      'hsla(212, 100%, 55%, 0.8)',
      'hsla(38, 92%, 60%, 0.8)',
      'hsla(188, 78%, 55%, 0.8)',
      'hsla(144, 70%, 50%, 0.8)',
      'hsla(280, 70%, 55%, 0.8)',
    ];
    return colors[id % colors.length];
  }

  update(clustering: boolean, progress: number) {
    if (clustering) {
      // Move towards cluster center
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;
      this.vx += dx * 0.02 * progress;
      this.vy += dy * 0.02 * progress;
      this.vx *= 0.92;
      this.vy *= 0.92;
    } else {
      // Random movement
      this.vx += (Math.random() - 0.5) * 0.3;
      this.vy += (Math.random() - 0.5) * 0.3;
      this.vx *= 0.98;
      this.vy *= 0.98;
    }

    this.x += this.vx;
    this.y += this.vy;

    // Boundary check
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

    // Glow effect
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
    gradient.addColorStop(0, this.color.replace('0.8', '0.3'));
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
  particles = [];
  clusters = [
    { x: 100, y: 120 },
    { x: 280, y: 100 },
    { x: 180, y: 250 },
    { x: 320, y: 280 },
    { x: 80, y: 300 },
  ];

  // Create particles for each cluster
  clusters.forEach((cluster, clusterId) => {
    const particleCount = 8 + Math.floor(Math.random() * 6);
    for (let i = 0; i < particleCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * 40;
      const x = cluster.x + Math.cos(angle) * radius;
      const y = cluster.y + Math.sin(angle) * radius;
      const particle = new Particle(x, y, clusterId);
      particle.targetX = cluster.x + (Math.random() - 0.5) * 30;
      particle.targetY = cluster.y + (Math.random() - 0.5) * 30;
      particles.push(particle);
    }
  });

  // Add some outlier particles
  for (let i = 0; i < 12; i++) {
    const x = Math.random() * 360 + 20;
    const y = Math.random() * 360 + 20;
    const particle = new Particle(x, y, Math.floor(Math.random() * clusters.length));
    particles.push(particle);
  }
};

const animate = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Clear canvas
  ctx.fillStyle = 'hsla(220, 20%, 8%, 0.1)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Animation cycle
  animationTime += 0.016;
  if (animationTime > 5) {
    animationTime = 0;
    isClustering = !isClustering;
    clusterProgress = 0;
  }

  // Progress
  if (isClustering && clusterProgress < 1) {
    clusterProgress += 0.008;
  } else if (!isClustering && clusterProgress > 0) {
    clusterProgress -= 0.008;
  }
  clusterProgress = Math.max(0, Math.min(1, clusterProgress));

  // Draw connections between particles in same cluster
  particles.forEach((p1, i) => {
    particles.slice(i + 1).forEach((p2) => {
      if (p1.clusterId === p2.clusterId) {
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
        if (dist < 60) {
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          const alpha = (1 - dist / 60) * 0.3 * clusterProgress;
          ctx.strokeStyle = p1.color.replace('0.8', String(alpha));
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    });
  });

  // Update and draw particles
  particles.forEach((particle) => {
    particle.update(isClustering, clusterProgress);
    particle.draw(ctx);
  });

  // Draw cluster labels when clustered
  if (clusterProgress > 0.5) {
    const labels = ['性能问题', '新功能', 'UI优化', 'Bug修复', '体验改进'];
    const labelAlpha = (clusterProgress - 0.5) * 2;
    clusters.forEach((cluster, i) => {
      ctx.font = '600 12px "Outfit", sans-serif';
      ctx.fillStyle = `hsla(0, 0%, 100%, ${labelAlpha * 0.7})`;
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
          {{ description }}
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
              stroke-width="2"
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
              stroke-width="2"
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
              stroke-width="2"
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
              stroke-width="2"
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
              stroke-width="2"
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

        <!-- Floating elements -->
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

    <!-- Scroll indicator -->
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
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -20%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, hsla(212, 100%, 45%, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(60px);
  animation: float 20s ease-in-out infinite;
}

.hero-section::after {
  content: '';
  position: absolute;
  bottom: -10%;
  left: -5%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, hsla(188, 78%, 55%, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(40px);
  animation: float 15s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -30px); }
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
  background: hsla(212, 100%, 45%, 0.15);
  border: 1px solid hsla(212, 100%, 45%, 0.3);
  border-radius: 100px;
  width: fit-content;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: hsl(212, 100%, 55%);
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
  color: hsl(212, 100%, 65%);
}

.hero-title {
  font-family: 'Outfit', -apple-system, sans-serif;
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.title-line {
  display: block;
  color: hsl(0, 0%, 100%);
}

.title-highlight {
  display: block;
  background: linear-gradient(135deg, hsl(212, 100%, 55%) 0%, hsl(188, 78%, 55%) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 1.1rem;
  color: hsl(220, 10%, 70%);
  line-height: 1.6;
  max-width: 480px;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.75rem;
  background: linear-gradient(135deg, hsl(212, 100%, 45%) 0%, hsl(212, 100%, 35%) 100%);
  border: none;
  border-radius: 10px;
  color: hsl(0, 0%, 100%);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px hsla(212, 100%, 45%, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px hsla(212, 100%, 45%, 0.5);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  background: hsla(220, 20%, 15%, 0.8);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 10px;
  color: hsl(0, 0%, 100%);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}

.btn-secondary:hover {
  background: hsla(220, 20%, 18%, 0.9);
  border-color: hsla(212, 100%, 45%, 0.5);
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
  padding: 0.5rem 0.75rem;
  background: hsla(220, 20%, 12%, 0.8);
  border: 1px solid hsla(220, 20%, 20%, 0.5);
  border-radius: 6px;
  font-size: 0.85rem;
  color: hsl(220, 10%, 70%);
}

.feature-tag svg {
  color: hsl(144, 70%, 50%);
}

/* Visual */
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
  background: hsla(220, 20%, 10%, 0.8);
  border: 1px solid hsla(220, 20%, 20%, 0.5);
  border-radius: 24px;
  backdrop-filter: blur(12px);
  box-shadow: 0 20px 60px hsla(0, 0%, 0%, 0.3);
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
  font-family: 'Outfit', sans-serif;
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, hsl(212, 100%, 55%) 0%, hsl(188, 78%, 55%) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.85rem;
  color: hsl(220, 10%, 60%);
}

.overlay-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150px;
  height: 150px;
  border: 2px solid hsla(212, 100%, 45%, 0.2);
  border-radius: 50%;
  animation: ring-pulse 3s ease-in-out infinite;
}

@keyframes ring-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.2; }
}

/* Floating cards */
.floating-card {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: hsla(220, 20%, 12%, 0.95);
  border: 1px solid hsla(220, 20%, 25%, 0.5);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px hsla(0, 0%, 0%, 0.3);
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
  50% { transform: translateY(-10px); }
}

.card-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, hsl(212, 100%, 45%), hsl(144, 70%, 50%));
  border-radius: 8px;
  font-size: 1rem;
  color: white;
  font-weight: 700;
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 0.75rem;
  color: hsl(220, 10%, 60%);
}

.card-value {
  font-family: 'Outfit', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: hsl(0, 0%, 100%);
}

/* Scroll indicator */
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
  background: linear-gradient(to bottom, hsl(212, 100%, 45%), transparent);
}

.scroll-text {
  font-size: 0.75rem;
  color: hsl(220, 10%, 50%);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Responsive */
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
