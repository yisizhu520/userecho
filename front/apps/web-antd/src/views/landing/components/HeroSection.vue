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
  description: '10倍速度洞察需求 | 团队的智能决策助手',
});


const { theme } = useLandingTheme();
const canvasRef = ref<HTMLCanvasElement>();
const animationId = ref<number>();
const isCanvasVisible = ref(true); // 控制Canvas是否在视口内
const isMobile = ref(false); // 检测移动设备

const isDark = computed(() => theme.value === 'dark');

// 跳转到演示环境
const handleTryDemo = () => {
  window.open('https://demo.userecho.app/demo', '_blank');
};

// 滚动到联系区域
const scrollToContact = () => {
  const contactSection = document.getElementById('contact');
  if (contactSection) {
    contactSection.scrollIntoView({ behavior: 'smooth' });
  }
};

// Make STAGE_CONFIG available to template
const stageConfig = {
  INGEST: { label: '收集反馈', icon: '📥', color: '#10b981' },
  PROCESS: { label: '智能合并', icon: '🧠', color: '#059669' },
  INSIGHT: { label: '发现洞察', icon: '⚡', color: '#fbbf24' },
  SYNC: { label: '同步用户', icon: '✓', color: '#34d399' },
};
const STAGE_CONFIG = Object.values(stageConfig);

// Animation State Machine
type AnimationStage = 'INGEST' | 'PROCESS' | 'INSIGHT' | 'SYNC';
let currentStage: AnimationStage = 'INGEST';
let nextStage: AnimationStage = 'PROCESS';
let frameCount = 0;
let stageTransition: number = 0; // 0-1 during transition
let isTransitioning: boolean = false;
const TRANSITION_FRAMES = 36; // ~0.6s smooth transition

// Stage blend weights for crossfade [current, next]
let stageWeights = [1, 0];

// Constants
const CANVAS_WIDTH = 560;
const CANVAS_HEIGHT = 480;

// Cluster data - AI-parsed requirement themes with priority and value
type ClusterData = {
  label: string;
  priority: string;  // P0/P1/P2
  value: string;     // 高/中/低
  count: number;     // 反馈数量
  color: string;     // Display color
};

const CLUSTER_DATA: ClusterData[] = [
  { label: '数据导出需求', priority: 'P0', value: '高', count: 18, color: '#ef4444' },    // Red - Critical
  { label: '首屏加载优化', priority: 'P1', value: '高', count: 12, color: '#f97316' },    // Orange - High
  { label: '暗色主题适配', priority: 'P1', value: '中', count: 9,  color: '#eab308' },    // Yellow - Medium
  { label: '批量操作支持', priority: 'P2', value: '中', count: 7,  color: '#3b82f6' },    // Blue - Normal
  { label: '移动端体验',   priority: 'P2', value: '低', count: 5,  color: '#6b7280' },    // Gray - Low
];


// User data for SYNC stage - users who will receive updates
type UserData = {
  name: string;
  avatar: string;     // Emoji or initial
  x: number;
  y: number;
  notified: boolean;
  notificationTime: number;
};

const USER_DATA: UserData[] = [
  { name: '张经理', avatar: '👨‍💼', x: 80, y: 100, notified: false, notificationTime: 0 },
  { name: '李老板', avatar: '👩‍💻', x: 480, y: 80, notified: false, notificationTime: 0 },
  { name: '王先生', avatar: '👨‍🔧', x: 500, y: 350, notified: false, notificationTime: 0 },
  { name: '赵女士', avatar: '👩‍🎨', x: 60, y: 370, notified: false, notificationTime: 0 },
  // { name: '刘测试', avatar: '👨‍🔬', x: 280, y: 420, notified: false, notificationTime: 0 },
];

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
  scanLine: 'rgba(16, 185, 129, 0.5)',
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
  targetUserIndex: number = -1;  // Which user this particle flies to in SYNC
  syncedUserIndex: number = -1;  // Which user has received this particle

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

    // 1. INGEST: Particles orbit slowly in background (texts take focus)
    if (stage === 'INGEST') {
      // Slow orbital motion around center - subtle background effect
      const angle = Math.atan2(this.y - centerY, this.x - centerX);
      const targetDist = 150 + this.clusterId * 30;

      // Gentle drift towards orbital position
      const targetX = centerX + Math.cos(angle + 0.002) * targetDist;
      const targetY = centerY + Math.sin(angle + 0.002) * targetDist;

      this.x += (targetX - this.x) * 0.02;
      this.y += (targetY - this.y) * 0.02;

      // Subtle opacity - particles are background during INGEST
      this.currentColor = this.baseColor;
    }

    // 2. PROCESS: Smooth move to Cluster Target - slower and gentler
    else if (stage === 'PROCESS') {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;

      // Use a gentler easing curve - slow start, smooth middle, gentle end
      const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
      const easedProgress = easeOut(Math.min(1, progress * 1.5)); // Spread over more time

      // Much slower movement for smooth gathering
      const speed = 0.015 + easedProgress * 0.015; // 0.025 to 0.06 range
      this.x += dx * speed;
      this.y += dy * speed;
    }

    // 3. INSIGHT: Gentle drift, High Value pulse based on cluster priority
    else if (stage === 'INSIGHT') {
      const time = frameCount * 0.03;
      this.x += Math.sin(time + this.clusterId) * 0.2;
      this.y += Math.cos(time + this.clusterId * 0.7) * 0.2;

      // Get cluster priority for visual treatment
      const clusterPriority = CLUSTER_DATA[this.clusterId]?.priority || 'P2';
      const isHighPriority = clusterPriority === 'P0';
      const isMediumPriority = clusterPriority === 'P1';

      if (this.isHighValue || isHighPriority) {
        // Use cluster color for P0 particles
        this.currentColor = CLUSTER_DATA[this.clusterId]?.color || COLOR_PALETTE.highlight;
        const pulse = Math.sin(frameCount * 0.08) * 0.5 + 0.5;
        this.size = 4 + pulse * 2.5;
      } else if (isMediumPriority) {
        // Medium priority gets moderate treatment
        this.currentColor = this.clusterColor;
        this.size = 3.5 + Math.sin(frameCount * 0.05) * 0.5;
      } else {
        // Low priority gets dimmed
        const dimFactor = 0.15 + Math.sin(frameCount * 0.02 + this.clusterId) * 0.08;
        this.currentColor = this.clusterColor.replace('1)', `${dimFactor})`).replace('0.9)', `${dimFactor})`);
      }
    }

    // 4. SYNC: Fly to assigned users - slower and gentler
    else if (stage === 'SYNC') {
      // Assign target user if not yet assigned (only for particles that should sync)
      if (this.targetUserIndex === -1) {
        const clusterPriority = CLUSTER_DATA[this.clusterId]?.priority || 'P2';
        const isHighPriority = clusterPriority === 'P0';
        const isMediumPriority = clusterPriority === 'P1';

        // High and medium priority particles sync to users
        if ((isHighPriority || isMediumPriority) && Math.random() > 0.3) {
          this.targetUserIndex = Math.floor(Math.random() * USER_DATA.length);
        }
      }

      // Fly towards target user with gentle, smooth motion
      if (this.targetUserIndex >= 0 && this.syncedUserIndex === -1) {
        const targetUser = USER_DATA[this.targetUserIndex];
        if (!targetUser) return;
        const dx = targetUser.x - this.x;
        const dy = targetUser.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 15) {
          // Gentle easing - slower overall, subtle deceleration at end
          const easeOut = 1 - Math.min(1, (dist - 15) / 300);
          const speed = 1.5 + easeOut * 2; // Speed range: 1.5 to 3.5 (much slower than before)

          this.x += (dx / dist) * speed;
          this.y += (dy / dist) * speed;
          this.currentColor = COLOR_PALETTE.sync;
        } else {
          // Reached user - gentle arrival
          this.syncedUserIndex = this.targetUserIndex;
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

  constructor(text: string) {
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
    this.vx = (CANVAS_WIDTH / 2 - this.x) * 0.0015 * this.z;
    this.vy = (CANVAS_HEIGHT / 2 - this.y) * 0.0015 * this.z;
    this.vz = 0.002;

    this.opacity = 0;
    this.scale = 0.3 + this.z * 0.4;
    this.spawnDelay = Math.floor(Math.random() * 80);
  }

  update(centerX: number, centerY: number) {
    if (this.spawnDelay > 0) {
      this.spawnDelay--;
      return;
    }

    // Move towards center - slower speed for better readability
    this.x += this.vx;
    this.y += this.vy;

    // Gentler acceleration as they get closer
    this.vx *= 1.008;
    this.vy *= 1.008;

    // Fade in then fade out near center
    const dist = Math.sqrt((centerX - this.x) ** 2 + (centerY - this.y) ** 2);
    if (dist > 300) {
      this.opacity = Math.min(1, this.opacity + 0.03);
    } else if (dist < 80) {
      this.opacity = Math.max(0, this.opacity - 0.05);
    }

    // Scale up as approaching (perspective) - slower
    this.scale = Math.min(1, this.scale + 0.003);

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
    return ['#10b981', '#059669', '#34d399', '#6ee7b7', '#ffffff'];
  } else {
    return ['#047857', '#059669', '#10b981', '#34d399', '#064e3b'];
  }
};

const initParticles = () => {
  const colors = getClusterColors(isDark.value);
  particles = [];
  feedbackTexts = [];

  // Define 5 clusters spread out to accommodate insight cards
  const cx = CANVAS_WIDTH / 2;
  const cy = CANVAS_HEIGHT / 2;

  clusters = [
    { x: cx, y: cy - 70 },       // Top Center (P0 - main focus)
    { x: cx + 110, y: cy - 10 }, // Right Upper
    { x: cx + 70, y: cy + 90 },  // Right Lower
    { x: cx - 70, y: cy + 90 },  // Left Lower
    { x: cx - 110, y: cy - 10 }, // Left Upper
  ];

  clusters.forEach((cluster, id) => {
    // High value cluster? Let's say id 0 (Top Center) is high value "Critical"
    const isHighValueCluster = id === 0;

    for (let i = 0; i < 15; i++) {
      const p = new Particle(id, colors[id % colors.length]!, isDark.value);

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
    feedbackTexts.push(new FeedbackText(text));
  });
};

watch(theme, initParticles);

const animate = () => {
  // 性能优化：Canvas不可见时停止渲染
  if (!isCanvasVisible.value || isMobile.value) {
    return;
  }

  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const dark = isDark.value;

  // Clear with subtle fade trail for motion blur effect
  ctx.fillStyle = dark ? 'rgba(4, 13, 10, 0.15)' : 'rgba(255, 255, 255, 0.15)';
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  frameCount++;

  // Cycle Logic (Total Cycle ~ 15s = 900 frames at 60fps)
  let scanX = 0;
  const cycleTime = frameCount % 900;
  const stages: AnimationStage[] = ['INGEST', 'PROCESS', 'INSIGHT', 'SYNC'];
  const stageDurations = [300, 150, 220, 230]; // Extended PROCESS for smoother clustering
  const stageBreaks = [0, 300, 450, 670, 900];

  // Determine current stage
  let newStage: AnimationStage = 'INGEST';
  let stageIdx = 0;
  let localProgress = 0;

  for (let i = 0; i < stages.length; i++) {
    if (cycleTime >= stageBreaks[i]! && cycleTime < stageBreaks[i + 1]!) {
      newStage = stages[i]!;
      stageIdx = i;
      localProgress = (cycleTime - stageBreaks[i]!) / stageDurations[i]!;
      break;
    }
  }

  // Handle smooth stage transition
  if (newStage !== nextStage && !isTransitioning) {
    // Start transition to next stage
    nextStage = newStage;
    isTransitioning = true;
    stageTransition = 0;
  }

  // Update transition progress with easing
  if (isTransitioning) {
    stageTransition += 1 / TRANSITION_FRAMES;
    if (stageTransition >= 1) {
      // Transition complete
      stageTransition = 0;
      isTransitioning = false;
      currentStage = nextStage;
      stageWeights = [1, 0];
    } else {
      // Calculate smooth blend weights using easeInOut
      const t = stageTransition;
      const easeT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      stageWeights = [1 - easeT, easeT];
    }
  }

  // Update reactive state
  activeStageIndex.value = stageIdx;
  stageProgress.value = localProgress;

  // Update progress bars
  const newProgressBars = [0, 0, 0, 0];
  for (let i = 0; i < stageIdx; i++) newProgressBars[i] = 1;
  newProgressBars[stageIdx] = localProgress;
  stageProgressBars.value = newProgressBars;

  // Stage-specific rendering with smooth transition blend
  const renderStageElements = (stage: AnimationStage, blendWeight: number) => {
    if (blendWeight <= 0.01) return;

    ctx.globalAlpha = blendWeight;

    if (stage === 'INGEST') {
      const centerX = CANVAS_WIDTH / 2;
      const centerY = CANVAS_HEIGHT / 2;

      feedbackTexts.forEach(ft => {
        ft.update(centerX, centerY);
        ft.draw(ctx, dark);
      });

      feedbackTexts = feedbackTexts.filter(ft => !ft.collected);
    } else if (stage === 'PROCESS') {
      // Slower scanline with easing
      const scanEase = (t: number) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      scanX = scanEase(localProgress) * CANVAS_WIDTH;

      const gradient = ctx.createLinearGradient(scanX - 100, 0, scanX + 20, 0);
      gradient.addColorStop(0, 'rgba(16, 185, 129, 0)');
      gradient.addColorStop(0.75, 'rgba(16, 185, 129, 0.25)');
      gradient.addColorStop(1, 'rgba(16, 185, 129, 0.5)');

      ctx.beginPath();
      ctx.moveTo(scanX, 0);
      ctx.lineTo(scanX, CANVAS_HEIGHT);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = gradient;
      ctx.fillRect(scanX - 100, 0, 120, CANVAS_HEIGHT);
    }
  };

  // Render with transition blend
  if (isTransitioning) {
    renderStageElements(currentStage, stageWeights[0] ?? 1);
    renderStageElements(nextStage, stageWeights[1] ?? 0);
  } else {
    renderStageElements(currentStage, 1);
  }

  ctx.globalAlpha = 1;

  // Reset particles and feedback texts at cycle end
  if (cycleTime === 0 && frameCount > 10) {
    // Reset transition state
    currentStage = 'INGEST';
    nextStage = 'PROCESS';
    isTransitioning = false;
    stageTransition = 0;
    stageWeights = [1, 0];

    particles.forEach(p => {
      const edge = Math.floor(Math.random() * 4);
      if (edge === 0) { p.x = Math.random() * CANVAS_WIDTH; p.y = -20; }
      else if (edge === 1) { p.x = CANVAS_WIDTH + 20; p.y = Math.random() * CANVAS_HEIGHT; }
      else if (edge === 2) { p.x = Math.random() * CANVAS_WIDTH; p.y = CANVAS_HEIGHT + 20; }
      else { p.x = -20; p.y = Math.random() * CANVAS_HEIGHT; }
      p.vx = (Math.random() - 0.5) * 2;
      p.vy = (Math.random() - 0.5) * 2;
      p.isSynced = false;
      p.targetUserIndex = -1;
      p.syncedUserIndex = -1;
    });

    feedbackTexts = [];
    FEEDBACK_SAMPLES.forEach((text) => {
      feedbackTexts.push(new FeedbackText(text));
    });

    USER_DATA.forEach(user => {
      user.notified = false;
      user.notificationTime = 0;
    });
  }

  // Update and draw particles - use current stage during transition for continuity
  const particleStage = isTransitioning ? currentStage : currentStage;
  particles.forEach(p => {
    p.update(particleStage, localProgress);
    p.draw(ctx, scanX);
  });

  // Draw cluster labels with smooth fade and transition
  const showLabels = currentStage === 'PROCESS' || currentStage === 'INSIGHT' ||
                     (isTransitioning && (nextStage === 'PROCESS' || nextStage === 'INSIGHT'));

  if (showLabels) {
    const processStartTime = stageBreaks[1]!;
    // Slower, smoother fade in over 80 frames instead of 50
    const fadeTime = Math.max(0, cycleTime - processStartTime);
    const fadeInProgress = Math.min(1, fadeTime / 80);
    // Apply easing for even smoother appearance
    const easedFade = fadeInProgress < 0.5
      ? 2 * fadeInProgress * fadeInProgress
      : 1 - Math.pow(-2 * fadeInProgress + 2, 2) / 2;

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    clusters.forEach((c, i) => {
      const cluster = CLUSTER_DATA[i]!;
      const isP0 = cluster.priority === 'P0';
      const isP1 = cluster.priority === 'P1';

      let alpha = easedFade;
      let showInsightCard = false;

      // Determine display mode and alpha based on stage
      if (isTransitioning) {
        if (nextStage === 'INSIGHT') {
          // Transitioning TO insight - blend alpha towards target values
          const targetAlpha = isP0 ? 1 : (isP1 ? 0.7 : 0.4);
          alpha = alpha * (1 - (stageWeights[1] ?? 0)) + targetAlpha * (stageWeights[1] ?? 0);
          showInsightCard = (stageWeights[1] ?? 0) > 0.5;
        } else if (currentStage === 'INSIGHT') {
          // Transitioning FROM insight
          const baseAlpha = isP0 ? 1 : (isP1 ? 0.7 : 0.4);
          alpha = baseAlpha * (stageWeights[0] ?? 0);
          showInsightCard = (stageWeights[0] ?? 0) > 0.5;
        }
      } else if (currentStage === 'INSIGHT') {
        alpha = isP0 ? 1 : (isP1 ? 0.7 : 0.4);
        showInsightCard = true;
      }

      ctx.globalAlpha = alpha;

      // Determine if showing insight card or simple label
      const displayInsightCard = showInsightCard || currentStage === 'INSIGHT';

      if (!displayInsightCard) {
        // Simple label during PROCESS
        ctx.font = '500 12px "Outfit", sans-serif';
        const text = cluster.label;
        const metrics = ctx.measureText(text);
        const w = metrics.width + 16;
        const h = 24;

        ctx.fillStyle = dark
          ? `rgba(30, 41, 59, 0.7)`
          : `rgba(255, 255, 255, 0.8)`;
        ctx.beginPath();
        ctx.roundRect(c.x - w/2, c.y - h/2 - 38, w, h, 6);
        ctx.fill();

        ctx.fillStyle = dark ? '#cbd5e1' : '#475569';
        ctx.fillText(text, c.x, c.y - 38);
      } else {
        // Enhanced insight card
        const cardWidth = 120;
        const cardHeight = 54;
        const cardX = c.x - cardWidth / 2;
        const cardY = c.y - cardHeight / 2 - 38;

        ctx.fillStyle = dark
          ? `rgba(30, 41, 59, ${isP0 ? 0.95 : 0.8})`
          : `rgba(255, 255, 255, ${isP0 ? 0.98 : 0.9})`;
        ctx.beginPath();
        ctx.roundRect(cardX, cardY, cardWidth, cardHeight, 10);
        ctx.fill();

        if (isP0) {
          ctx.shadowColor = cluster.color;
          ctx.shadowBlur = 20;
        }

        ctx.strokeStyle = cluster.color;
        ctx.lineWidth = isP0 ? 2 : 1.5;
        ctx.stroke();
        ctx.shadowBlur = 0;

        const badgeSize = 20;
        const badgeX = cardX + cardWidth - badgeSize - 6;
        const badgeY = cardY + 6;

        ctx.fillStyle = cluster.color;
        ctx.beginPath();
        ctx.roundRect(badgeX, badgeY, badgeSize, badgeSize, 6);
        ctx.fill();

        ctx.font = 'bold 11px system-ui, sans-serif';
        ctx.fillStyle = '#fff';
        ctx.fillText(cluster.priority, badgeX + badgeSize/2, badgeY + badgeSize/2);

        ctx.font = '600 13px "Outfit", system-ui, sans-serif';
        ctx.fillStyle = dark ? '#e2e8f0' : '#0f172a';
        ctx.fillText(cluster.label, c.x, cardY + 18);

        ctx.font = '500 10px system-ui, sans-serif';
        const valueColor = cluster.value === '高' ? '#ef4444' : (cluster.value === '中' ? '#f97316' : '#6b7280');
        ctx.fillStyle = valueColor;
        ctx.fillText(`价值:${cluster.value}`, c.x - 25, cardY + 40);

        ctx.fillStyle = dark ? '#94a3b8' : '#64748b';
        ctx.fillText(`${cluster.count}条`, c.x + 30, cardY + 40);
      }

      ctx.globalAlpha = 1;
    });
  }

  // Draw users and notifications during SYNC stage
  const showUsers = currentStage === 'SYNC' || currentStage === 'INSIGHT' ||
                     (isTransitioning && (nextStage === 'SYNC' || nextStage === 'INSIGHT'));

  if (showUsers) {
    const syncProgress = currentStage === 'SYNC' ? localProgress : 0;

    // Calculate fade in with transition support
    let fadeIn = 0;
    if (currentStage === 'SYNC' || (isTransitioning && nextStage === 'SYNC')) {
      fadeIn = Math.min(1, localProgress * 2 + 0.3);
    } else if (currentStage === 'INSIGHT') {
      fadeIn = Math.max(0, (localProgress - 0.7) / 0.3);
    }

    ctx.globalAlpha = fadeIn;

    const centerX = CANVAS_WIDTH / 2;
    const centerY = CANVAS_HEIGHT / 2;

    USER_DATA.forEach((user, idx) => {
      // Check if any particle has reached this user
      const hasNotification = particles.some(p => p.syncedUserIndex === idx);

      // Update notification state
      if (hasNotification && !user.notified) {
        user.notified = true;
        user.notificationTime = frameCount;
      }

      // Draw connection line from center to user (subtle)
      if (currentStage === 'SYNC' || (isTransitioning && nextStage === 'SYNC')) {
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(user.x, user.y);
        ctx.strokeStyle = dark
          ? `rgba(96, 165, 250, ${0.1 * (1 - syncProgress)})`
          : `rgba(59, 130, 246, ${0.08 * (1 - syncProgress)})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Draw user avatar circle
      const avatarSize = 36;
      ctx.beginPath();
      ctx.arc(user.x, user.y, avatarSize / 2, 0, Math.PI * 2);

      // Avatar background gradient
      const avatarGrad = ctx.createRadialGradient(user.x, user.y, 0, user.x, user.y, avatarSize / 2);
      if (dark) {
        avatarGrad.addColorStop(0, 'rgba(96, 165, 250, 0.4)');
        avatarGrad.addColorStop(1, 'rgba(59, 130, 246, 0.15)');
      } else {
        avatarGrad.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
        avatarGrad.addColorStop(1, 'rgba(59, 130, 246, 0.08)');
      }
      ctx.fillStyle = avatarGrad;
      ctx.fill();

      // Avatar border - green when notified
      ctx.strokeStyle = user.notified
        ? '#10b981'
        : (dark ? 'rgba(96, 165, 250, 0.5)' : 'rgba(59, 130, 246, 0.4)');
      ctx.lineWidth = user.notified ? 2.5 : 2;
      ctx.stroke();

      // Avatar emoji
      ctx.font = '20px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(user.avatar, user.x, user.y);

      // User name below avatar
      ctx.font = '500 11px "Outfit", system-ui, sans-serif';
      ctx.fillStyle = dark ? 'rgba(226, 232, 240, 0.9)' : 'rgba(30, 41, 59, 0.9)';
      ctx.fillText(user.name, user.x, user.y + avatarSize / 2 + 16);

      // Notification indicator
      if (user.notified) {
        const timeSinceNotify = frameCount - user.notificationTime;
        const notifProgress = Math.min(1, timeSinceNotify / 30);

        // Expanding ring animation
        if (notifProgress < 1) {
          ctx.beginPath();
          ctx.arc(user.x, user.y, avatarSize / 2 + 5 + notifProgress * 25, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(52, 211, 153, ${1 - notifProgress})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Notification badge with pulse
        const pulse = Math.sin(frameCount * 0.1) * 0.2 + 0.8;
        const badgeX = user.x + avatarSize / 2 - 4;
        const badgeY = user.y - avatarSize / 2 + 4;
        const badgeSize = 18;

        // Badge glow
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 10 * pulse;

        ctx.beginPath();
        ctx.arc(badgeX, badgeY, badgeSize / 2 * pulse, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981';
        ctx.fill();

        ctx.shadowBlur = 0;

        ctx.strokeStyle = dark ? '#1e293b' : '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Checkmark
        ctx.font = 'bold 11px system-ui, sans-serif';
        ctx.fillStyle = '#fff';
        ctx.fillText('✓', badgeX, badgeY);
      }
    });

    ctx.globalAlpha = 1;
  }

  animationId.value = requestAnimationFrame(animate);
};

onMounted(() => {
  // 检测移动设备（性能优化）
  isMobile.value = window.innerWidth < 768 || 
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  // 初始化Canvas元素
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.width = CANVAS_WIDTH;
    canvas.height = CANVAS_HEIGHT;
  }
  
  // 移动端不启动Canvas动画
  if (isMobile.value) {
    return;
  }
  
  initParticles();
  
  // 使用 Intersection Observer 监听Canvas可见性（节省CPU）
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        isCanvasVisible.value = entry.isIntersecting;
        
        if (entry.isIntersecting) {
          // Canvas进入视口，恢复动画
          if (!animationId.value) {
            animationId.value = requestAnimationFrame(animate);
          }
        } else {
          // Canvas离开视口，暂停动画释放CPU
          if (animationId.value) {
            cancelAnimationFrame(animationId.value);
            animationId.value = undefined;
          }
        }
      });
    },
    { threshold: 0.1 } // 10%可见时触发
  );

  if (canvasRef.value) {
    observer.observe(canvasRef.value);
  }
  
  // 组件卸载时清理
  onUnmounted(() => {
    observer.disconnect();
    if (animationId.value) {
      cancelAnimationFrame(animationId.value);
    }
  });
  
  // 启动动画
  animationId.value = requestAnimationFrame(animate);
});

// 原有的onUnmounted已合并到上面的observer清理逻辑中
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
          <span class="desc-sub">团队的智能决策助手</span>
        </p>

        <div class="hero-actions">
          <button class="btn-primary" @click="scrollToContact">
            <span>免费试用</span>
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
          <button class="btn-secondary" @click="handleTryDemo">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <span>在线体验</span>
          </button>
        </div>

        <!-- 限时福利提示 -->
        <div class="promo-banner">
          <span class="promo-fire">🔥</span>
          <span class="promo-text">
            限时福利：前 20 名用户<strong>免费体验1个月</strong>专业版
            <br />
            <span class="promo-highlight">（已有 11 家团队加入，仅剩 9 个名额）</span>
          </span>
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
            <span>智能合并</span>
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
            <span>优先级评分</span>
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
            <span>智能洞察</span>
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
  background: #10b981;
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

/* 限时福利提示 */
.promo-banner {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.1));
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 12px;
  margin-top: 0.5rem;
}

.promo-fire {
  font-size: 1.25rem;
  animation: fire-pulse 1.5s ease-in-out infinite;
}

@keyframes fire-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.promo-text {
  font-size: 0.95rem;
  color: var(--lp-text-secondary);
  line-height: 1.5;
}

.promo-text strong {
  color: #f59e0b;
  font-weight: 600;
}

.promo-highlight {
  color: var(--lp-text-tertiary);
  font-size: 0.85rem;
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
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  width: calc(100% - 32px);
  max-width: 480px;
}

.stage-dots {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 10px 16px;
  background: var(--lp-bg-elevated, rgba(15, 23, 42, 0.25));
  backdrop-filter: blur(16px);
  border: 1px solid var(--lp-border-subtle, rgba(255, 255, 255, 0.04));
  border-radius: 16px;
  opacity: 0.35;
  transition: opacity 0.3s ease, background 0.3s ease;
}

.stage-dots:hover {
  opacity: 1;
  background: var(--lp-bg-elevated, rgba(15, 23, 42, 0.5));
}

.stage-dot {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.stage-dot .dot-icon {
  font-size: 13px;
  opacity: 0.4;
  filter: grayscale(0.4);
  transition: all 0.4s ease;
}

.stage-dot .dot-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--lp-text-muted, rgba(255, 255, 255, 0.4));
  letter-spacing: 0.02em;
  transition: all 0.4s ease;
  white-space: nowrap;
}

.stage-dot.active .dot-icon {
  opacity: 1;
  filter: grayscale(0);
  transform: scale(1.1);
}

.stage-dot.active .dot-label {
  color: var(--lp-text-primary, rgba(255, 255, 255, 0.95));
}

.stage-dot.completed .dot-icon {
  opacity: 0.6;
  filter: grayscale(0);
}

.stage-dot.completed .dot-label {
  color: var(--lp-text-secondary, rgba(255, 255, 255, 0.5));
}

.dot-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, #10b981, #34d399);
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
  background: linear-gradient(to bottom, #10b981, transparent);
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

  .canvas-stage-indicator {
    bottom: 12px;
    width: calc(100% - 16px);
    max-width: 320px;
  }

  .stage-dots {
    padding: 8px 10px;
    gap: 2px;
  }

  .stage-dot {
    padding: 5px 8px;
    gap: 4px;
    flex: 1;
    justify-content: center;
  }

  .stage-dot .dot-icon {
    font-size: 12px;
  }

  .stage-dot .dot-label {
    font-size: 10px;
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
