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

// Make STAGE_CONFIG available to template
const stageConfig = {
  INGEST: { label: '收集反馈', icon: '📥', color: '#60a5fa' },
  PROCESS: { label: '智能聚类', icon: '🧠', color: '#a78bfa' },
  INSIGHT: { label: '发现洞察', icon: '⚡', color: '#fbbf24' },
  SYNC: { label: '同步进度', icon: '✓', color: '#34d399' },
};
const STAGE_CONFIG = Object.values(stageConfig);

// Animation State Machine
type AnimationStage = 'INGEST' | 'PROCESS' | 'INSIGHT' | 'SYNC';
let currentStage: AnimationStage = 'INGEST';
let previousStage: AnimationStage | null = null;
let frameCount = 0;
let stageTransition: number = 0; // 0-1 for smooth transitions

// Constants
const CANVAS_WIDTH = 560;
const CANVAS_HEIGHT = 480;

// Cluster labels - AI-parsed requirement themes from feedback
const CLUSTER_LABELS = ['数据导出需求', '首屏加载优化', '暗色主题适配', '批量操作支持', '移动端体验'];

// Real feedback text samples for INGEST stage (grouped by cluster)
const FEEDBACK_SAMPLES = [
  // Cluster 1: 数据导出需求
  '希望能导出Excel报表',
  '需要PDF导出功能',
  '数据能导出就好了',
  '支持CSV导出吗',
  '想下载历史数据',

  // Cluster 2: 首屏加载优化
  '页面加载有点慢',
  '首屏等待时间太长',
  '希望能快点加载',
  '初始化太慢了',
  '打开页面要等好久',

  // Cluster 3: 暗色主题适配
  '想要暗色模式',
  '晚上用太刺眼了',
  '支持深色主题就好了',
  '有没有夜间模式',
  '暗色模式更护眼',

  // Cluster 4: 批量操作支持
  '需要一个批量删除',
  '批量编辑功能',
  '不支持批量操作吗',
  '一条条处理太慢',
  '希望能批量导入',

  // Cluster 5: 移动端体验
  '手机上不太好操作',
  '移动端适配问题',
  '响应式布局有bug',
  '手机字体太小',
  '触屏操作不便',
];

// Colors
const COLOR_PALETTE = {
  neutral: (dark: boolean) => dark ? 'rgba(148, 163, 184, 0.3)' : 'rgba(148, 163, 184, 0.5)',
  highlight: '#F59E0B', // Amber 500 for "Insight"
  sync: '#10B981',      // Emerald 500 for "Sync"
  scanLine: 'rgba(56, 189, 248, 0.5)',
};

// Particle Class
class Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  targetX: number;
  targetY: number;
  clusterId: number;
  baseColor: string;
  clusterColor: string;
  currentColor: string;
  size: number;
  
  // State flags
  isIngested: boolean = false;
  isHighValue: boolean = false;
  isSynced: boolean = false;

  constructor(clusterId: number, clusterColor: string, isDark: boolean) {
    // Start from random edge
    const edge = Math.floor(Math.random() * 4);
    if (edge === 0) { this.x = Math.random() * CANVAS_WIDTH; this.y = -20; } // Top
    else if (edge === 1) { this.x = CANVAS_WIDTH + 20; this.y = Math.random() * CANVAS_HEIGHT; } // Right
    else if (edge === 2) { this.x = Math.random() * CANVAS_WIDTH; this.y = CANVAS_HEIGHT + 20; } // Bottom
    else { this.x = -20; this.y = Math.random() * CANVAS_HEIGHT; } // Left

    this.vx = (Math.random() - 0.5) * 2;
    this.vy = (Math.random() - 0.5) * 2;
    
    this.clusterId = clusterId;
    this.clusterColor = clusterColor;
    this.baseColor = COLOR_PALETTE.neutral(isDark);
    this.currentColor = this.baseColor;
    this.size = Math.random() * 3 + 2;
    
    // Target position set later
    this.targetX = CANVAS_WIDTH / 2;
    this.targetY = CANVAS_HEIGHT / 2;
  }

  update(stage: AnimationStage, progress: number) {
    const centerX = CANVAS_WIDTH / 2;
    const centerY = CANVAS_HEIGHT / 2;

    // Smooth easing function
    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
    const easeInOutQuad = (t: number) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

    // 1. INGEST: Particles orbit slowly in background (texts take focus)
    if (stage === 'INGEST') {
      // Slow orbital motion around center - subtle background effect
      const angle = Math.atan2(this.y - centerY, this.x - centerX);
      const dist = Math.sqrt((this.x - centerX) ** 2 + (this.y - centerY) ** 2);
      const targetDist = 150 + this.clusterId * 30;

      // Gentle drift towards orbital position
      const targetX = centerX + Math.cos(angle + 0.002) * targetDist;
      const targetY = centerY + Math.sin(angle + 0.002) * targetDist;

      this.x += (targetX - this.x) * 0.02;
      this.y += (targetY - this.y) * 0.02;

      // Subtle opacity - particles are background during INGEST
      this.currentColor = this.baseColor;
    }

    // 2. PROCESS: Smooth move to Cluster Target
    else if (stage === 'PROCESS') {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;
      const easedProgress = easeOutCubic(progress);

      this.x += dx * 0.08 * (1 + easedProgress);
      this.y += dy * 0.08 * (1 + easedProgress);
    }

    // 3. INSIGHT: Gentle drift, High Value pulse
    else if (stage === 'INSIGHT') {
      const time = frameCount * 0.03;
      this.x += Math.sin(time + this.clusterId) * 0.2;
      this.y += Math.cos(time + this.clusterId * 0.7) * 0.2;

      if (this.isHighValue) {
        this.currentColor = COLOR_PALETTE.highlight;
        // Smooth pulse
        const pulse = Math.sin(frameCount * 0.08) * 0.5 + 0.5;
        this.size = 4 + pulse * 2;
      } else {
        // Subtle dim for others
        const dimFactor = 0.2 + Math.sin(frameCount * 0.02 + this.clusterId) * 0.1;
        this.currentColor = this.clusterColor.replace('1)', `${dimFactor})`).replace('0.9)', `${dimFactor})`);
      }
    }

    // 4. SYNC: Smooth flyout for High Value
    else if (stage === 'SYNC') {
      if (this.isHighValue && !this.isSynced) {
        const flyoutProgress = Math.min(1, progress * 2);
        const easedFlyout = easeInOutQuad(flyoutProgress);

        this.x += easedFlyout * 6;
        this.y -= easedFlyout * 1.5;
        this.currentColor = COLOR_PALETTE.sync;

        if (flyoutProgress >= 1) {
          this.isSynced = true;
        }
      }
    }
  }

  draw(ctx: CanvasRenderingContext2D, scanX: number) {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    
    // Special coloring for PROCESS stage
    if (currentStage === 'PROCESS') {
      // If scanline passed, show cluster color
      if (this.x < scanX) {
        ctx.fillStyle = this.clusterColor;
      } else {
        ctx.fillStyle = this.baseColor;
      }
    } else {
      ctx.fillStyle = this.currentColor;
    }
    
    ctx.fill();
    
    // Glue glow for high value
    if (this.isHighValue && (currentStage === 'INSIGHT' || currentStage === 'SYNC')) {
      ctx.shadowBlur = 10;
      ctx.shadowColor = this.currentColor;
    } else {
      ctx.shadowBlur = 0;
    }
  }
}

// Flying Feedback Text Class for INGEST stage
class FeedbackText {
  text: string;
  x: number;
  y: number;
  z: number; // Depth: 0 (far) to 1 (near)
  vx: number;
  vy: number;
  vz: number;
  opacity: number;
  scale: number;
  collected: boolean = false;
  spawnDelay: number;

  constructor(text: string, isDark: boolean) {
    this.text = text;

    // Start from random position outside canvas
    const edge = Math.floor(Math.random() * 4);
    const margin = 200; // Start further away for depth effect

    if (edge === 0) {
      this.x = Math.random() * CANVAS_WIDTH;
      this.y = -margin;
    } else if (edge === 1) {
      this.x = CANVAS_WIDTH + margin;
      this.y = Math.random() * CANVAS_HEIGHT;
    } else if (edge === 2) {
      this.x = Math.random() * CANVAS_WIDTH;
      this.y = CANVAS_HEIGHT + margin;
    } else {
      this.x = -margin;
      this.y = Math.random() * CANVAS_HEIGHT;
    }

    // Depth (z) creates perspective - farther objects move slower
    this.z = Math.random() * 0.5 + 0.5;
    this.vx = (CANVAS_WIDTH / 2 - this.x) * 0.003 * this.z;
    this.vy = (CANVAS_HEIGHT / 2 - this.y) * 0.003 * this.z;
    this.vz = 0.002;

    this.opacity = 0;
    this.scale = 0.3 + this.z * 0.4;
    this.spawnDelay = Math.floor(Math.random() * 60);
  }

  update(centerX: number, centerY: number) {
    if (this.spawnDelay > 0) {
      this.spawnDelay--;
      return;
    }

    // Move towards center
    this.x += this.vx;
    this.y += this.vy;

    // Accelerate as they get closer (gravity effect)
    this.vx *= 1.02;
    this.vy *= 1.02;

    // Fade in then fade out near center
    const dist = Math.sqrt((centerX - this.x) ** 2 + (centerY - this.y) ** 2);
    if (dist > 300) {
      this.opacity = Math.min(1, this.opacity + 0.05);
    } else if (dist < 80) {
      this.opacity = Math.max(0, this.opacity - 0.08);
    }

    // Scale up as approaching (perspective)
    this.scale = Math.min(1, this.scale + 0.005);

    // Mark as collected when very close to center
    if (dist < 30) {
      this.collected = true;
    }
  }

  draw(ctx: CanvasRenderingContext2D, isDark: boolean) {
    if (this.spawnDelay > 0 || this.opacity <= 0.01) return;

    ctx.save();
    ctx.globalAlpha = this.opacity;
    ctx.translate(this.x, this.y);
    ctx.scale(this.scale, this.scale);

    // Text with subtle glow
    ctx.font = '500 14px "Outfit", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Subtle shadow for depth
    ctx.shadowColor = isDark ? 'rgba(96, 165, 250, 0.3)' : 'rgba(59, 130, 246, 0.2)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 2;

    // Background pill
    const metrics = ctx.measureText(this.text);
    const padding = 12;
    const pillWidth = metrics.width + padding * 2;
    const pillHeight = 26;

    ctx.fillStyle = isDark
      ? `rgba(30, 41, 59, ${0.6 * this.opacity})`
      : `rgba(255, 255, 255, ${0.8 * this.opacity})`;
    ctx.beginPath();
    ctx.roundRect(-pillWidth / 2, -pillHeight / 2, pillWidth, pillHeight, 8);
    ctx.fill();

    // Border
    ctx.strokeStyle = isDark
      ? `rgba(96, 165, 250, ${0.3 * this.opacity})`
      : `rgba(59, 130, 246, ${0.2 * this.opacity})`;
    ctx.lineWidth = 1;
    ctx.stroke();

    // Text
    ctx.shadowBlur = 0;
    ctx.fillStyle = isDark
      ? `rgba(226, 232, 240, ${this.opacity})`
      : `rgba(30, 41, 59, ${this.opacity})`;
    ctx.fillText(this.text, 0, 0);

    ctx.restore();
  }
}

// Variables
let particles: Particle[] = [];
let feedbackTexts: FeedbackText[] = [];
let clusters: { x: number; y: number }[] = [];
const activeStageIndex = ref(0);
const stageProgress = ref(0);

// Stage progress bars
const stageProgressBars = ref([0, 0, 0, 0]);

const getClusterColors = (dark: boolean) => {
  if (dark) {
    return ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#ffffff'];
  } else {
    return ['#1d4ed8', '#2563eb', '#3b82f6', '#60a5fa', '#0f172a'];
  }
};

const initParticles = () => {
  const colors = getClusterColors(isDark.value);
  particles = [];
  feedbackTexts = [];

  // Define 5 clusters spread out more due to larger canvas
  const cx = CANVAS_WIDTH / 2;
  const cy = CANVAS_HEIGHT / 2;

  clusters = [
    { x: cx, y: cy - 80 },      // Top Center
    { x: cx + 100, y: cy },     // Right
    { x: cx + 60, y: cy + 100 }, // Bottom Right
    { x: cx - 60, y: cy + 100 }, // Bottom Left
    { x: cx - 100, y: cy },     // Left
  ];

  clusters.forEach((cluster, id) => {
    // High value cluster? Let's say id 0 (Top Center) is high value "Critical"
    const isHighValueCluster = id === 0;

    for (let i = 0; i < 15; i++) {
      const p = new Particle(id, colors[id % colors.length], isDark.value);

      // Target position
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * 30;
      p.targetX = cluster.x + Math.cos(angle) * radius;
      p.targetY = cluster.y + Math.sin(angle) * radius;

      // Mark high value particles
      if (isHighValueCluster && i < 5) { // Only kernel is high value
        p.isHighValue = true;
      }

      particles.push(p);
    }
  });

  // Create flying feedback texts (use all samples, staggered)
  FEEDBACK_SAMPLES.forEach((text) => {
    feedbackTexts.push(new FeedbackText(text, isDark.value));
  });
};

watch(theme, initParticles);

const animate = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const dark = isDark.value;

  // Clear with subtle fade trail for motion blur effect
  ctx.fillStyle = dark ? 'rgba(15, 23, 42, 0.15)' : 'rgba(255, 255, 255, 0.15)';
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  frameCount++;

  // Cycle Logic (Total Cycle ~ 12s = 720 frames at 60fps)
  let scanX = 0;
  const cycleTime = frameCount % 720;
  const stages: AnimationStage[] = ['INGEST', 'PROCESS', 'INSIGHT', 'SYNC'];
  const stageDurations = [180, 140, 200, 200]; // frames per stage
  const stageBreaks = [0, 180, 320, 520, 720];

  // Determine current stage
  let newStage: AnimationStage = 'INGEST';
  let stageIdx = 0;
  let localProgress = 0;

  for (let i = 0; i < stages.length; i++) {
    if (cycleTime >= stageBreaks[i] && cycleTime < stageBreaks[i + 1]) {
      newStage = stages[i];
      stageIdx = i;
      localProgress = (cycleTime - stageBreaks[i]) / stageDurations[i];
      break;
    }
  }

  // Handle stage transition
  if (newStage !== currentStage) {
    previousStage = currentStage;
    currentStage = newStage;
    stageTransition = 0;
  }
  stageTransition = Math.min(1, stageTransition + 0.03);

  // Update reactive state
  activeStageIndex.value = stageIdx;
  stageProgress.value = localProgress;

  // Update progress bars
  const newProgressBars = [0, 0, 0, 0];
  for (let i = 0; i < stageIdx; i++) newProgressBars[i] = 1;
  newProgressBars[stageIdx] = localProgress;
  stageProgressBars.value = newProgressBars;

  // Stage-specific rendering
  if (currentStage === 'INGEST') {
    // Draw flying feedback texts
    const centerX = CANVAS_WIDTH / 2;
    const centerY = CANVAS_HEIGHT / 2;

    // Update and draw feedback texts
    feedbackTexts.forEach(ft => {
      ft.update(centerX, centerY);
      ft.draw(ctx, dark);
    });

    // Remove collected texts
    feedbackTexts = feedbackTexts.filter(ft => !ft.collected);
  } else if (currentStage === 'PROCESS') {
    // Scanline progress
    scanX = localProgress * CANVAS_WIDTH;

    // Draw elegant scanline
    const gradient = ctx.createLinearGradient(scanX - 80, 0, scanX + 20, 0);
    gradient.addColorStop(0, 'rgba(96, 165, 250, 0)');
    gradient.addColorStop(0.8, 'rgba(96, 165, 250, 0.3)');
    gradient.addColorStop(1, 'rgba(96, 165, 250, 0.6)');

    ctx.beginPath();
    ctx.moveTo(scanX, 0);
    ctx.lineTo(scanX, CANVAS_HEIGHT);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Glow effect
    ctx.fillStyle = gradient;
    ctx.fillRect(scanX - 80, 0, 100, CANVAS_HEIGHT);
  } else if (currentStage === 'INSIGHT') {
    // Pulsing highlight effect
    const pulseIntensity = Math.sin(frameCount * 0.05) * 0.2 + 0.8;
  } else if (currentStage === 'SYNC') {
    // Sync flyout
  }

  // Reset particles and feedback texts at cycle end
  if (cycleTime === 0 && frameCount > 10) {
    particles.forEach(p => {
      const edge = Math.floor(Math.random() * 4);
      if (edge === 0) { p.x = Math.random() * CANVAS_WIDTH; p.y = -20; }
      else if (edge === 1) { p.x = CANVAS_WIDTH + 20; p.y = Math.random() * CANVAS_HEIGHT; }
      else if (edge === 2) { p.x = Math.random() * CANVAS_WIDTH; p.y = CANVAS_HEIGHT + 20; }
      else { p.x = -20; p.y = Math.random() * CANVAS_HEIGHT; }
      p.vx = (Math.random() - 0.5) * 2;
      p.vy = (Math.random() - 0.5) * 2;
      p.isSynced = false;
    });

    // Reset feedback texts
    feedbackTexts = [];
    FEEDBACK_SAMPLES.forEach((text) => {
      feedbackTexts.push(new FeedbackText(text, dark));
    });
  }

  // Update and draw particles with smooth easing
  particles.forEach(p => {
    p.update(currentStage, localProgress);
    p.draw(ctx, scanX);
  });

  // Draw cluster labels with smooth fade
  if (currentStage === 'PROCESS' || currentStage === 'INSIGHT') {
    const fadeInProgress = currentStage === 'PROCESS'
      ? Math.min(1, (cycleTime - stageBreaks[1]) / 40)
      : 1;

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '500 12px "Outfit", sans-serif';

    clusters.forEach((c, i) => {
      const isHighValue = i === 0;
      let alpha = fadeInProgress;

      if (currentStage === 'INSIGHT' && !isHighValue) {
        alpha = 0.25;
      }

      ctx.globalAlpha = alpha;
      const text = CLUSTER_LABELS[i];

      // Minimal label design
      const metrics = ctx.measureText(text);
      const w = metrics.width + 16;
      const h = 24;

      // Subtle background
      ctx.fillStyle = dark
        ? `rgba(30, 41, 59, ${isHighValue && currentStage === 'INSIGHT' ? 0.95 : 0.7})`
        : `rgba(255, 255, 255, ${isHighValue && currentStage === 'INSIGHT' ? 0.95 : 0.8})`;
      ctx.beginPath();
      ctx.roundRect(c.x - w/2, c.y - h/2 - 38, w, h, 6);
      ctx.fill();

      // Accent border for high value
      if (isHighValue && currentStage === 'INSIGHT') {
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Text
      ctx.fillStyle = dark
        ? (isHighValue && currentStage === 'INSIGHT' ? '#fbbf24' : '#cbd5e1')
        : (isHighValue && currentStage === 'INSIGHT' ? '#d97706' : '#475569');
      ctx.fillText(text, c.x, c.y - 38);

      ctx.globalAlpha = 1;
    });
  }

  animationId.value = requestAnimationFrame(animate);
};

onMounted(() => {
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.width = CANVAS_WIDTH;
    canvas.height = CANVAS_HEIGHT;
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
          <div class="canvas-stage-indicator">
            <div class="stage-dots">
              <div
                v-for="(stage, idx) in STAGE_CONFIG"
                :key="idx"
                class="stage-dot"
                :class="{ active: activeStageIndex === idx, completed: activeStageIndex > idx }"
              >
                <span class="dot-icon">{{ stage.icon }}</span>
                <span class="dot-label">{{ stage.label }}</span>
                <div
                  v-if="activeStageIndex === idx"
                  class="dot-progress"
                  :style="{ width: `${stageProgress * 100}%` }"
                ></div>
              </div>
            </div>
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
  width: 560px;
  height: 480px;
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

.canvas-stage-indicator {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.stage-dots {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--lp-bg-elevated, rgba(15, 23, 42, 0.6));
  backdrop-filter: blur(12px);
  border: 1px solid var(--lp-border-subtle, rgba(255, 255, 255, 0.08));
  border-radius: 20px;
}

.stage-dot {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.stage-dot .dot-icon {
  font-size: 14px;
  opacity: 0.5;
  filter: grayscale(0.3);
  transition: all 0.4s ease;
}

.stage-dot .dot-label {
  font-size: 10px;
  font-weight: 500;
  color: var(--lp-text-muted, rgba(255, 255, 255, 0.4));
  letter-spacing: 0.02em;
  text-transform: uppercase;
  transition: all 0.4s ease;
}

.stage-dot.active .dot-icon {
  opacity: 1;
  filter: grayscale(0);
  transform: scale(1.15);
}

.stage-dot.active .dot-label {
  color: var(--lp-text-primary, rgba(255, 255, 255, 0.95));
}

.stage-dot.completed .dot-icon {
  opacity: 0.65;
  filter: grayscale(0);
}

.stage-dot.completed .dot-label {
  color: var(--lp-text-secondary, rgba(255, 255, 255, 0.6));
}

.dot-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, #60a5fa, #a78bfa);
  border-radius: 1px;
  transition: width 0.1s linear;
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

  .stage-dots {
    padding: 6px 12px;
    gap: 6px;
  }

  .stage-dot {
    padding: 4px 8px;
  }

  .stage-dot .dot-icon {
    font-size: 12px;
  }

  .stage-dot .dot-label {
    font-size: 9px;
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
