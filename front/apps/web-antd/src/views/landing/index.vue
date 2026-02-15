<script lang="ts" setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

import HeroSection from './components/HeroSection.vue';
import PainPointsSection from './components/PainPointsSection.vue';
import FeaturesSection from './components/FeaturesSection.vue';
import WorkflowSection from './components/WorkflowSection.vue';
import CTASection from './components/CTASection.vue';
import LandingNavbar from './components/LandingNavbar.vue';

const router = useRouter();

const handleGetStarted = () => {
  // 简单的处理：直接跳转到工作台，未登录会被重定向到登录页
  router.push('/app/dashboard/workspace');
};

onMounted(() => {
  // Add smooth scroll behavior
  document.documentElement.style.scrollBehavior = 'smooth';
});
</script>

<template>
  <div class="landing-page" style="background: linear-gradient(180deg, #0a0e27 0%, #0f1429 50%, #0a0e27 100%);">
    <LandingNavbar @get-started="handleGetStarted" />

    <main class="landing-main">
      <HeroSection @get-started="handleGetStarted" />
      <PainPointsSection />
      <FeaturesSection />
      <WorkflowSection />
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

/* Landing page theme - applied to landing-page container */
.landing-page {
  --lp-font-display: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  --lp-font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;

  /* Primary colors - Vibrant blue */
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
  --lp-accent-cyan: #06b6d4;
  --lp-accent-emerald: #10b981;
  --lp-accent-amber: #f59e0b;
  --lp-accent-purple: #8b5cf6;
  --lp-accent-pink: #ec4899;
  --lp-accent-red: #ef4444;

  /* Background colors - Deep dark theme */
  --lp-bg-primary: #0a0e27;
  --lp-bg-secondary: #111836;
  --lp-bg-tertiary: #1a2042;
  --lp-bg-card: rgba(26, 32, 66, 0.8);
  --lp-bg-card-hover: rgba(37, 48, 90, 0.9);

  /* Text colors - High contrast */
  --lp-text-primary: #ffffff;
  --lp-text-secondary: #94a3b8;
  --lp-text-tertiary: #64748b;
  --lp-text-muted: #475569;

  /* Border colors */
  --lp-border-subtle: rgba(148, 163, 184, 0.1);
  --lp-border-default: rgba(148, 163, 184, 0.2);
  --lp-border-strong: rgba(148, 163, 184, 0.3);

  /* Gradients */
  --lp-gradient-primary: linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%);
  --lp-gradient-warm: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  --lp-gradient-cool: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  --lp-gradient-radial: radial-gradient(ellipse at 50% 0%, rgba(59, 130, 246, 0.15) 0%, transparent 50%);
}

.landing-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a0e27 0%, #0f1429 50%, #0a0e27 100%);
  font-family: var(--lp-font-body);
  color: var(--lp-text-primary);
  overflow-x: hidden;
}

/* Animated background mesh */
.landing-page::before {
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

@keyframes mesh-move {
  0%, 100% { opacity: 1; transform: scale(1) translate(0, 0); }
  50% { opacity: 0.8; transform: scale(1.05) translate(-10px, 10px); }
}

.landing-main {
  position: relative;
  z-index: 1;
}

/* Footer styles */
.landing-footer {
  position: relative;
  z-index: 1;
  background: linear-gradient(180deg, rgba(10, 14, 39, 0.8) 0%, #0a0e27 100%);
  border-top: 1px solid var(--lp-border-subtle);
  padding: 4rem 0 2rem;
  backdrop-filter: blur(10px);
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
  color: var(--lp-primary-400);
}

.footer-bottom {
  max-width: 1200px;
  margin: 3rem auto 0;
  padding: 2rem 2rem 0;
  border-top: 1px solid var(--lp-border-subtle);
  text-align: center;
  color: var(--lp-text-tertiary);
  font-size: 0.85rem;
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
