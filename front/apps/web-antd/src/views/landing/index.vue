<script lang="ts" setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

import HeroSection from './components/HeroSection.vue';
import PainPointsSection from './components/PainPointsSection.vue';
import FeaturesSection from './components/FeaturesSection.vue';
import WorkflowSection from './components/WorkflowSection.vue';
import PricingSection from './components/pricing/index.vue';
import CTASection from './components/CTASection.vue';
import LandingNavbar from './components/LandingNavbar.vue';
import { useLandingTheme } from '#/composables/useLandingTheme';

const router = useRouter();
const { theme, initTheme } = useLandingTheme();

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
        <p>&copy; 2025 回响. All rights reserved.</p>
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

  /* Primary colors - Professional Blue */
  --lp-primary-50: #f0f5ff;
  --lp-primary-100: #e0ebff;
  --lp-primary-200: #c2dbff;
  --lp-primary-300: #94c2ff;
  --lp-primary-400: #5c9eff;
  --lp-primary-500: #3b82f6;
  --lp-primary-600: #2563eb;
  --lp-primary-700: #1d4ed8;
  --lp-primary-800: #1e40af;
  --lp-primary-900: #1e3a8a;

  /* Accent colors - Reserved for status/highlights only */
  --lp-accent-cyan: #0ea5e9;
  --lp-accent-cyan-bright: #38bdf8;
  --lp-accent-emerald: #10b981;
  --lp-accent-amber: #f59e0b;
  --lp-accent-purple: #6366f1; /* More corporate indigo than purple */
  --lp-accent-pink: #ec4899;
  --lp-accent-red: #ef4444;

  /* Background colors - Deep Blue Professional */
  --lp-bg-primary: #020617; /* Very dark slate blue */
  --lp-bg-secondary: #0f172a;
  --lp-bg-tertiary: #1e293b;
  --lp-bg-card: rgba(15, 23, 42, 0.8);
  --lp-bg-card-hover: rgba(30, 41, 59, 0.9);
  --lp-bg-elevated: rgba(30, 41, 59, 0.95);

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
  --lp-gradient-primary: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
  --lp-gradient-hero: linear-gradient(135deg, #eff6ff 0%, #bfdbfe 100%); /* White/Blue for text */
  --lp-gradient-warm: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  --lp-gradient-cool: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  --lp-gradient-radial: radial-gradient(ellipse at 50% 0%, rgba(59, 130, 246, 0.1) 0%, transparent 60%);
  --lp-gradient-bg: linear-gradient(180deg, #020617 0%, #0f172a 100%);

  /* Canvas background */
  --lp-canvas-bg: rgba(15, 23, 42, 0.6);

  /* Special effects - Reduced intensity */
  --lp-glow-primary: rgba(59, 130, 246, 0.3);
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

  /* Primary colors - Corporate Blue */
  --lp-primary-50: #eff6ff;
  --lp-primary-100: #dbeafe;
  --lp-primary-200: #bfdbfe;
  --lp-primary-300: #93c5fd;
  --lp-primary-400: #60a5fa;
  --lp-primary-500: #3b82f6;
  --lp-primary-600: #2563eb;
  --lp-primary-700: #1d4ed8;
  --lp-primary-800: #1e40af;
  --lp-primary-900: #1e3a8a;

  /* Accent colors */
  --lp-accent-cyan: #0ea5e9;
  --lp-accent-cyan-bright: #0284c7;
  --lp-accent-emerald: #059669;
  --lp-accent-amber: #d97706;
  --lp-accent-purple: #4f46e5;
  --lp-accent-pink: #db2777;
  --lp-accent-red: #dc2626;

  /* Background colors - Crisp Light */
  --lp-bg-primary: #ffffff;
  --lp-bg-secondary: #f8fafc;
  --lp-bg-tertiary: #f1f5f9;
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

  /* Gradients - Minimalist */
  --lp-gradient-primary: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  --lp-gradient-hero: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); /* Dark Blue for text */
  --lp-gradient-warm: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  --lp-gradient-cool: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  --lp-gradient-radial: radial-gradient(ellipse at 50% 0%, rgba(37, 99, 235, 0.05) 0%, transparent 50%);
  --lp-gradient-bg: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);

  /* Canvas background */
  --lp-canvas-bg: #ffffff;

  /* Special effects - Subtle */
  --lp-glow-primary: rgba(37, 99, 235, 0.15);
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
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(59, 130, 246, 0.12), transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 20%, rgba(6, 182, 212, 0.08), transparent 50%),
    radial-gradient(ellipse 50% 30% at 40% 80%, rgba(16, 185, 129, 0.06), transparent 50%),
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
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(59, 130, 246, 0.04), transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 20%, rgba(6, 182, 212, 0.03), transparent 50%),
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
