<script lang="ts" setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useHead } from '@vueuse/head';

import HeroSection from './components/HeroSection.vue';
import PainPointsSection from './components/PainPointsSection.vue';
import FeaturesSection from './components/FeaturesSection.vue';
import WorkflowSection from './components/WorkflowSection.vue';
import PricingSection from './components/pricing/index.vue';
import CTASection from './components/CTASection.vue';
import LandingNavbar from './components/LandingNavbar.vue';
import { useLandingTheme } from '#/composables/useLandingTheme';

const router = useRouter();
const currentYear = new Date().getFullYear();
const { theme, initTheme } = useLandingTheme();

// SEO Meta 标签配置
useHead({
  title: '回响 - AI 驱动的用户反馈智能分析平台',
  meta: [
    {
      name: 'description',
      content: '回响是一款 AI 驱动的用户反馈智能分析平台，帮助创业者、产品经理和中小企业高效收集、分析和管理用户反馈，自动生成产品洞察，加速产品迭代。',
    },
    {
      name: 'keywords',
      content: '用户反馈收集,反馈分析,反馈管理,AI 洞察,产品反馈,客户反馈,用户体验,产品管理工具',
    },
    // Open Graph
    { property: 'og:type', content: 'website' },
    { property: 'og:url', content: 'https://userecho.app/' },
    { property: 'og:title', content: '回响 - AI 驱动的用户反馈智能分析平台' },
    {
      property: 'og:description',
      content: '回响是一款 AI 驱动的用户反馈智能分析平台，帮助创业者、产品经理和中小企业高效收集、分析和管理用户反馈，自动生成产品洞察，加速产品迭代。',
    },
    { property: 'og:image', content: 'https://userecho.app/logo.png' },
    // Twitter
    { property: 'twitter:card', content: 'summary_large_image' },
    { property: 'twitter:url', content: 'https://userecho.app/' },
    { property: 'twitter:title', content: '回响 - AI 驱动的用户反馈智能分析平台' },
    {
      property: 'twitter:description',
      content: '回响是一款 AI 驱动的用户反馈智能分析平台，帮助创业者、产品经理和中小企业高效收集、分析和管理用户反馈，自动生成产品洞察，加速产品迭代。',
    },
    { property: 'twitter:image', content: 'https://userecho.app/logo.png' },
  ],
  link: [{ rel: 'canonical', href: 'https://userecho.app/' }],
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: '回响',
        applicationCategory: 'BusinessApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'CNY',
        },
        description: 'AI 驱动的用户反馈智能分析平台，帮助创业者、产品经理和中小企业高效收集、分析和管理用户反馈',
        keywords: '用户反馈收集,反馈分析,反馈管理,AI 洞察',
        aggregateRating: {
          '@type': 'AggregateRating',
          ratingValue: '4.8',
          ratingCount: '150',
        },
      }),
    },
  ],
});

const handleGetStarted = () => {
  // 简单的处理：直接跳转到工作台，未登录会被重定向到登录页
  router.push('/app/dashboard/workspace');
};

onMounted(() => {
  // Add smooth scroll behavior
  document.documentElement.style.scrollBehavior = 'smooth';
  // Initialize theme
  initTheme();
});
</script>

<template>
  <div class="landing-page" :class="`theme-${theme}`">
    <LandingNavbar @get-started="handleGetStarted" />

    <main class="landing-main">
      <HeroSection @get-started="handleGetStarted" />
      <PainPointsSection />
      <FeaturesSection />
      <WorkflowSection />
      <PricingSection />
      <CTASection @get-started="handleGetStarted" />
    </main>

    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <div class="footer-logo">回响</div>
          <p class="footer-tagline">AI 驱动的用户反馈智能分析平台</p>
        </div>
        <div class="footer-links">
          <div class="footer-section">
            <h4>产品</h4>
            <a href="#features">功能</a>
            <a href="#workflow">工作流程</a>
            <a href="/auth/login">开始使用</a>
          </div>
          <div class="footer-section">
            <h4>资源</h4>
            <a href="#">文档</a>
            <a href="#">API</a>
            <a href="#">博客</a>
          </div>
          <div class="footer-section">
            <h4>公司</h4>
            <a href="#">关于</a>
            <a href="#">联系</a>
            <a href="#">隐私</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; {{ currentYear }} 回响. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<!-- Non-scoped styles for global CSS variables and fonts -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* ============================================
   DARK THEME (default)
   ============================================ */
.landing-page.theme-dark {
  /* Fonts */
  --lp-font-display: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  --lp-font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;

  /* Primary colors - Professional Emerald/Green */
  --lp-primary-50: #f0fdf4;
  --lp-primary-100: #dcfce7;
  --lp-primary-200: #bbf7d0;
  --lp-primary-300: #86efac;
  --lp-primary-400: #4ade80;
  --lp-primary-500: #10b981;
  --lp-primary-600: #059669;
  --lp-primary-700: #047857;
  --lp-primary-800: #065f46;
  --lp-primary-900: #064e3b;

  /* Accent colors - Reserved for status/highlights only */
  --lp-accent-cyan: #0ea5e9;
  --lp-accent-cyan-bright: #38bdf8;
  --lp-accent-emerald: #10b981;
  --lp-accent-amber: #f59e0b;
  --lp-accent-purple: #6366f1; /* More corporate indigo than purple */
  --lp-accent-pink: #ec4899;
  --lp-accent-red: #ef4444;

  /* Background colors - Deep Emerald Professional */
  --lp-bg-primary: #040d0a; /* Very dark emerald green black */
  --lp-bg-secondary: #06120e;
  --lp-bg-tertiary: #064e3b;
  --lp-bg-card: rgba(6, 18, 14, 0.8);
  --lp-bg-card-hover: rgba(6, 78, 59, 0.9);
  --lp-bg-elevated: rgba(6, 78, 59, 0.95);

  /* Text colors - High contrast */
  --lp-text-primary: #f8fafc;
  --lp-text-secondary: #cbd5e1;
  --lp-text-tertiary: #94a3b8;
  --lp-text-muted: #64748b;

  /* Border colors */
  --lp-border-subtle: rgba(148, 163, 184, 0.1);
  --lp-border-default: rgba(148, 163, 184, 0.15);
  --lp-border-strong: rgba(148, 163, 184, 0.25);

  /* Gradients - Subtle and Professional */
  --lp-gradient-primary: linear-gradient(135deg, #059669 0%, #10b981 100%);
  --lp-gradient-hero: linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 100%); /* White/Green for text */
  --lp-gradient-warm: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  --lp-gradient-cool: linear-gradient(135deg, #065f46 0%, #10b981 100%);
  --lp-gradient-radial: radial-gradient(ellipse at 50% 0%, rgba(16, 185, 129, 0.1) 0%, transparent 60%);
  --lp-gradient-bg: linear-gradient(180deg, #040d0a 0%, #06120e 100%);

  /* Canvas background */
  --lp-canvas-bg: rgba(15, 23, 42, 0.6);

  /* Special effects - Reduced intensity */
  --lp-glow-primary: rgba(16, 185, 129, 0.3);
  --lp-glow-cyan: rgba(14, 165, 233, 0.2);
  --lp-glow-emerald: rgba(16, 185, 129, 0.2);
  --lp-glow-amber: rgba(245, 158, 11, 0.2);

  /* Circuit board pattern */
  --lp-circuit-color: rgba(59, 130, 246, 0.03);
  --lp-circuit-line: rgba(59, 130, 246, 0.04);
}

/* ============================================
   LIGHT THEME - Clean Enterprise
   ============================================ */
.landing-page.theme-light {
  /* Fonts */
  --lp-font-display: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  --lp-font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;

  /* Primary colors - Corporate Emerald/Green */
  --lp-primary-50: #f0fdf4;
  --lp-primary-100: #dcfce7;
  --lp-primary-200: #bbf7d0;
  --lp-primary-300: #86efac;
  --lp-primary-400: #4ade80;
  --lp-primary-500: #10b981;
  --lp-primary-600: #059669;
  --lp-primary-700: #047857;
  --lp-primary-800: #065f46;
  --lp-primary-900: #064e3b;

  /* Accent colors */
  --lp-accent-cyan: #0ea5e9;
  --lp-accent-cyan-bright: #0284c7;
  --lp-accent-emerald: #059669;
  --lp-accent-amber: #d97706;
  --lp-accent-purple: #4f46e5;
  --lp-accent-pink: #db2777;
  --lp-accent-red: #dc2626;

  /* Background colors - Crisp Light Green */
  --lp-bg-primary: #ffffff;
  --lp-bg-secondary: #f0fdf4;
  --lp-bg-tertiary: #dcfce7;
  --lp-bg-card: #ffffff;
  --lp-bg-card-hover: #f8fafc;
  --lp-bg-elevated: #ffffff;

  /* Text colors - Strong contrast */
  --lp-text-primary: #0f172a;
  --lp-text-secondary: #334155;
  --lp-text-tertiary: #64748b;
  --lp-text-muted: #94a3b8;

  /* Border colors */
  --lp-border-subtle: #e2e8f0;
  --lp-border-default: #cbd5e1;
  --lp-border-strong: #94a3b8;

  /* Gradients - Minimalist Emerald */
  --lp-gradient-primary: linear-gradient(135deg, #059669 0%, #047857 100%);
  --lp-gradient-hero: linear-gradient(135deg, #064e3b 0%, #10b981 100%); /* Emerald Gradient for text */
  --lp-gradient-warm: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  --lp-gradient-cool: linear-gradient(135deg, #059669 0%, #10b981 100%);
  --lp-gradient-radial: radial-gradient(ellipse at 50% 0%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
  --lp-gradient-bg: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);

  /* Canvas background */
  --lp-canvas-bg: #ffffff;

  /* Special effects - Subtle Emerald */
  --lp-glow-primary: rgba(16, 185, 129, 0.15);
  --lp-glow-cyan: rgba(14, 165, 233, 0.1);
  --lp-glow-emerald: rgba(5, 150, 105, 0.1);
  --lp-glow-amber: rgba(217, 119, 6, 0.1);

  /* Circuit board pattern - Very subtle */
  --lp-circuit-color: rgba(30, 58, 138, 0.03);
  --lp-circuit-line: rgba(30, 58, 138, 0.04);
}

/* ============================================
   Base styles (theme-aware)
   ============================================ */
.landing-page {
  min-height: 100vh;
  background: var(--lp-gradient-bg);
  font-family: var(--lp-font-body);
  color: var(--lp-text-primary);
  overflow-x: hidden;
  transition: background 0.3s ease, color 0.3s ease;
}

/* Animated background mesh - dark theme only */
.landing-page.theme-dark::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(16, 185, 129, 0.12), transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 20%, rgba(16, 185, 129, 0.08), transparent 50%),
    radial-gradient(ellipse 50% 30% at 40% 80%, rgba(10, 185, 129, 0.06), transparent 50%),
    radial-gradient(ellipse 40% 40% at 90% 70%, rgba(245, 158, 11, 0.05), transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: mesh-move 30s ease-in-out infinite;
}

/* Light theme subtle background */
.landing-page.theme-light::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(16, 185, 129, 0.04), transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 20%, rgba(5, 150, 105, 0.03), transparent 50%),
    radial-gradient(ellipse 50% 30% at 40% 80%, rgba(16, 185, 129, 0.02), transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: mesh-move 30s ease-in-out infinite;
}

@keyframes mesh-move {
  0%, 100% { opacity: 1; transform: scale(1) translate(0, 0); }
  50% { opacity: 0.8; transform: scale(1.05) translate(-10px, 10px); }
}

.landing-main {
  position: relative;
  z-index: 1;
}

/* ============================================
   Footer styles (theme-aware)
   ============================================ */
.landing-footer {
  position: relative;
  z-index: 1;
  background: var(--lp-bg-secondary);
  border-top: 1px solid var(--lp-border-subtle);
  padding: 4rem 0 2rem;
  backdrop-filter: blur(10px);
  transition: background 0.3s ease, border-color 0.3s ease;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 4rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-logo {
  font-family: var(--lp-font-display);
  font-size: 1.75rem;
  font-weight: 800;
  background: var(--lp-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.footer-tagline {
  color: var(--lp-text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.footer-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-section h4 {
  font-family: var(--lp-font-display);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--lp-text-primary);
  margin-bottom: 0.25rem;
}

.footer-section a {
  color: var(--lp-text-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

.footer-section a:hover {
  color: var(--lp-primary-500);
}

.footer-bottom {
  max-width: 1200px;
  margin: 3rem auto 0;
  padding: 2rem 2rem 0;
  border-top: 1px solid var(--lp-border-subtle);
  text-align: center;
  color: var(--lp-text-tertiary);
  font-size: 0.85rem;
  transition: border-color 0.3s ease;
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
