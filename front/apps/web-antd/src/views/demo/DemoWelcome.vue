<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useHead } from '@vueuse/head';
import { Target, Headphones, Settings, ChevronRight, Activity, Zap } from 'lucide-vue-next';
import { requestClient } from '#/api/request';
import { useAccessStore } from '@vben/stores';
import { useLandingTheme } from '#/composables/useLandingTheme';

const router = useRouter();
const accessStore = useAccessStore();
const { theme, initTheme } = useLandingTheme();
const loading = ref(false);
const selectedRole = ref('');

// SEO Meta 标签配置
useHead({
  title: '在线演示 - 回响 AI 反馈分析平台',
  meta: [
    {
      name: 'description',
      content: '立即体验回响的 AI 反馈分析功能，无需注册即可试用智能聚类、自动洞察生成等核心功能。选择角色，开启产品反馈管理之旅。',
    },
    {
      name: 'keywords',
      content: '在线演示,Demo,用户反馈分析,AI 聚类,产品洞察,免费试用',
    },
    { name: 'robots', content: 'index, follow' },
    // Open Graph
    { property: 'og:type', content: 'website' },
    { property: 'og:url', content: 'https://userecho.app/demo' },
    { property: 'og:title', content: '在线演示 - 回响 AI 反馈分析平台' },
    {
      property: 'og:description',
      content: '立即体验回响的 AI 反馈分析功能，无需注册即可试用智能聚类、自动洞察生成等核心功能。选择角色，开启产品反馈管理之旅。',
    },
    { property: 'og:image', content: 'https://userecho.app/logo.png' },
    // Twitter
    { property: 'twitter:card', content: 'summary_large_image' },
    { property: 'twitter:url', content: 'https://userecho.app/demo' },
    { property: 'twitter:title', content: '在线演示 - 回响 AI 反馈分析平台' },
    {
      property: 'twitter:description',
      content: '立即体验回响的 AI 反馈分析功能，无需注册即可试用智能聚类、自动洞察生成等核心功能。选择角色，开启产品反馈管理之旅。',
    },
    { property: 'twitter:image', content: 'https://userecho.app/logo.png' },
  ],
  link: [{ rel: 'canonical', href: 'https://userecho.app/demo' }],
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        name: '在线演示 - 回响',
        description: '立即体验回响的 AI 反馈分析功能，无需注册即可试用智能聚类、自动洞察生成等核心功能',
        url: 'https://userecho.app/demo',
        isPartOf: {
          '@type': 'WebSite',
          name: '回响',
          url: 'https://userecho.app',
        },
      }),
    },
  ],
});

onMounted(() => {
  initTheme();
});

const roles = [
  {
    key: 'product_owner',
    name: '产品负责人',
    description: '查看优先级看板、AI 洞察、审批议题',
    icon: Target,
    color: '#3b82f6',
    features: ['需求优先级排序', '用户反馈聚类', '产品路线图规划'],
  },
  {
    key: 'user_ops',
    name: '用户运营',
    description: '录入反馈、管理客户、触发聚类',
    icon: Headphones,
    color: '#10b981',
    features: ['全渠道反馈录入', '客户画像分析', '自动化标签管理'],
  },
  {
    key: 'admin',
    name: '系统管理员',
    description: '用户管理、权限配置、看板设置',
    icon: Settings,
    color: '#f59e0b',
    features: ['团队权限控制', '自定义工作流', '系统配置管理'],
  },
];

const handleSelectRole = async (roleKey: string) => {
  if (loading.value) return;
  selectedRole.value = roleKey;
  loading.value = true;

  try {
    const response = await requestClient.post<{
      access_token: string;
      role: { key: string; name: string };
    }>('/api/v1/demo/switch-role', { role_key: roleKey });

    // 存储 token
    accessStore.setAccessToken(response.access_token);

    // 跳转到工作台
    router.push('/app/dashboard/workspace');
  } catch (error) {
    console.error('角色切换失败:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="demo-welcome" :class="'theme-' + theme">
    <!-- Background Decorators -->
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    
    <div class="glass-container">
      <div class="welcome-header">
        <div class="logo-wrapper">
          <div class="logo">
            <img src="/logo.png" alt="回响" class="logo-icon" />
            <span class="logo-text">回响</span>
          </div>
          <span class="demo-badge">
            <Zap :size="12" fill="currentColor" />
            Live Demo
          </span>
        </div>
        <h1>
          体验 
          <span class="text-gradient">AI 驱动</span> 
          的所有潜能
        </h1>
        <p class="subtitle">
          选择一个角色，立即开启智能反馈分析之旅。
          <br />沉浸式体验如何将海量反馈转化为产品洞察。
        </p>
      </div>

      <div class="role-cards">
        <div
          v-for="role in roles"
          :key="role.key"
          class="role-card"
          :class="{ active: selectedRole === role.key, loading: loading && selectedRole === role.key }"
          @click="handleSelectRole(role.key)"
        >
          <div class="card-glow" :style="{ '--glow-color': role.color }"></div>
          <div class="role-content">
            <div class="role-icon-wrapper">
              <component :is="role.icon" :size="24" stroke-width="2.5" />
            </div>
            <div class="role-info">
              <h3>{{ role.name }}</h3>
              <p>{{ role.description }}</p>
              <div class="features-list">
                <span v-for="(feature, idx) in role.features" :key="idx" class="feature-tag">
                  {{ feature }}
                </span>
              </div>
            </div>
            <div class="role-action">
              <span class="select-text">选择此角色</span>
              <div v-if="loading && selectedRole === role.key" class="loading-spinner"></div>
              <ChevronRight v-else :size="20" class="action-icon" />
            </div>
          </div>
        </div>
      </div>

      <div class="demo-footer">
        <div class="notice-card">
          <div class="notice-icon">
            <Activity :size="18" />
          </div>
          <div class="notice-text">
            <strong>演示环境说明：</strong> 数据将在每日凌晨 2:00 (UTC+8) 自动重置。
          </div>
          <a href="https://userecho.app" target="_blank" class="primary-link">
            访问官网
            <ChevronRight :size="14" />
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Base Layout & Backgrounds */
.demo-welcome {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  position: relative;
  overflow: hidden;
  transition: background 0.5s ease;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Theme Variables */
/* Polished Theme: Neutral Base + Emerald Accents */

/* Dark Theme (Professional Slate/Zinc) */
.demo-welcome.theme-dark {
  /* Background: Deep, rich neutral dark (Slate 950/900) */
  --bg-color: #020617; 
  /* Glass: Crystalline, very subtle tint */
  --glass-bg: rgba(15, 23, 42, 0.4); 
  --glass-border: rgba(255, 255, 255, 0.08); /* Crisp white border */
  --glass-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  
  /* Text: High Contrast */
  --text-primary: #f8fafc; /* Slate 50 */
  --text-secondary: #94a3b8; /* Slate 400 */
  
  /* Cards: Subtle surface */
  --card-bg: rgba(30, 41, 59, 0.3); /* Slate 800 alpha */
  --card-hover-bg: rgba(30, 41, 59, 0.6);
  --card-border: rgba(255, 255, 255, 0.05);
  
  /* Accents: Emerald (Strategic) */
  --orb-1: #059669; /* Emerald 600 (Darker for background) */
  --orb-2: #047857; /* Emerald 700 */
  --primary-accent: #10b981; /* Emerald 500 (Highlights) */
}

/* Light Theme (Clean Cool Gray) */
.demo-welcome.theme-light {
  /* Background: clean, cool gray/white structure */
  --bg-color: #f8fafc; /* Slate 50 */
  /* Glass: Frosted white */
  --glass-bg: rgba(255, 255, 255, 0.75);
  --glass-border: rgba(255, 255, 255, 0.8);
  --glass-shadow: 0 20px 40px -12px rgba(148, 163, 184, 0.15);
  
  /* Text */
  --text-primary: #0f172a; /* Slate 900 */
  --text-secondary: #64748b; /* Slate 500 */
  
  /* Cards */
  --card-bg: rgba(255, 255, 255, 0.6);
  --card-hover-bg: #ffffff;
  --card-border: rgba(148, 163, 184, 0.15); /* Slate 300 alpha */
  
  /* Accents */
  --orb-1: #6ee7b7; /* Emerald 300 (Softer) */
  --orb-2: #34d399; /* Emerald 400 */
  --primary-accent: #059669; /* Emerald 600 (Darker for readability) */
}

.demo-welcome {
  background-color: var(--bg-color);
}

/* Background Orbs - Reduced Intensity */
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px); /* Increased blur for smoother gradient */
  opacity: 0.25; /* Reduced opacity for subtlety */
  z-index: 0;
  animation: float 12s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: var(--orb-1);
  top: -200px;
  left: -100px;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: var(--orb-2);
  bottom: -150px;
  right: -150px;
  animation-delay: -6s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, 60px); }
}

/* Glass Container - Cleaner */
.glass-container {
  width: 100%;
  max-width: 960px;
  background: var(--glass-bg);
  backdrop-filter: blur(40px) saturate(1.8); /* Increased blur & satire for 'crystal' look */
  -webkit-backdrop-filter: blur(40px) saturate(1.8);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  border-radius: 32px;
  padding: 64px;
  position: relative;
  z-index: 1;
}

/* Header */
.welcome-header {
  text-align: center;
  margin-bottom: 64px;
}

.logo-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  height: 30px; /* Slightly larger */
  width: auto;
  object-fit: contain;
}

.logo-text {
  font-family: 'Outfit', sans-serif;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.8px;
  color: var(--text-primary);
}

.demo-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(16, 185, 129, 0.1); /* Subtle green tint */
  color: #10b981; /* Emerald 500 */
  border: 1px solid rgba(16, 185, 129, 0.2);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 5px 12px;
  border-radius: 100px;
  letter-spacing: 0.5px;
}

.welcome-header h1 {
  font-size: 48px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 20px 0;
  letter-spacing: -1.2px;
  line-height: 1.1;
}

.text-gradient {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 18px;
  line-height: 1.6;
  color: var(--text-secondary);
  max-width: 520px;
  margin: 0 auto;
  font-weight: 400;
}

/* Role Cards */
.role-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 64px;
}

.role-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 20px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  position: relative;
  overflow: hidden;
  height: 100%;
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), var(--primary-accent), transparent 40%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  z-index: 0;
}

.role-card:hover {
  transform: translateY(-8px);
  background: var(--card-hover-bg);
  box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.15); /* More dramatic shadow */
  border-color: rgba(16, 185, 129, 0.3); /* Subtle green border on hover */
}

/* Light theme hover fix */
.theme-light .role-card:hover {
  box-shadow: 0 24px 48px -12px rgba(148, 163, 184, 0.25);
}

.role-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.role-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: rgba(148, 163, 184, 0.08); /* Neutral bg by default */
  color: var(--text-secondary);
}

/* Specific icon colors on hover or active */
.role-card:hover .role-icon-wrapper,
.role-card.active .role-icon-wrapper {
  transform: scale(1.1);
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.role-info {
  flex: 1;
}

.role-info h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.role-info p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.features-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  font-size: 11px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--card-border);
  color: var(--text-secondary);
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s;
}

.role-card:hover .feature-tag {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
  color: var(--text-primary);
}

.role-action {
  margin-top: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-secondary);
  border-top: 1px solid var(--card-border);
  padding-top: 20px;
}

.select-text {
  font-size: 13px;
  font-weight: 500;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.3s ease;
}

.action-icon {
  transition: all 0.3s ease;
  transform: translateX(0);
}

.role-card:hover .select-text {
  opacity: 1;
  transform: translateX(0);
  color: #10b981;
}

.role-card:hover .action-icon {
  color: #10b981;
  transform: translateX(4px);
}

/* Loading */
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.role-card.loading {
  pointer-events: none;
  opacity: 0.7;
}

/* Footer & Notice */
.demo-footer {
  border-top: 1px solid var(--glass-border);
  padding-top: 32px;
}

.notice-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--card-bg); /* Use card bg instead of green tint */
  border-radius: 12px;
  border: 1px solid var(--card-border);
  transition: border-color 0.3s;
}

.notice-card:hover {
  border-color: rgba(16, 185, 129, 0.3);
}

.notice-icon {
  color: #10b981;
  display: flex;
}

.notice-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
}

.notice-text strong {
  color: var(--text-primary);
  font-weight: 600;
}

.primary-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary); /* Neutral link by default */
  text-decoration: none;
  transition: all 0.2s ease;
}

.primary-link:hover {
  text-decoration: none;
  color: #10b981;
  gap: 6px;
}

/* Responsive */
@media (max-width: 768px) {
  .glass-container {
    padding: 32px 24px;
    border-radius: 24px;
  }
  
  .role-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .welcome-header h1 {
    font-size: 36px;
  }

  .logo-icon {
    height: 36px;
  }
  
  .logo-text {
    font-size: 24px;
  }
  
  .notice-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .orb-1, .orb-2 {
    width: 300px;
    height: 300px;
    opacity: 0.3;
  }
}
</style>
