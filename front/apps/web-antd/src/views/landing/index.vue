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
  <div class="landing-page">
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
          <div class="footer-logo">Feedalyze</div>
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
        <p>&copy; 2025 Feedalyze. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Import unique fonts */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
  --font-display: 'Outfit', -apple-system, sans-serif;
  --font-body: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --primary-base: hsl(212, 100%, 45%);
  --primary-light: hsl(212, 100%, 55%);
  --primary-dark: hsl(212, 100%, 35%);
  --accent-amber: hsl(38, 92%, 60%);
  --accent-cyan: hsl(188, 78%, 55%);
  --bg-deep: hsl(220, 20%, 8%);
  --bg-card: hsl(220, 15%, 12%);
  --bg-card-hover: hsl(220, 15%, 16%);
  --text-primary: hsl(0, 0%, 100%);
  --text-secondary: hsl(220, 10%, 70%);
  --text-muted: hsl(220, 10%, 50%);
  --border-color: hsl(220, 20%, 20%);
}

.landing-page {
  min-height: 100vh;
  background: var(--bg-deep);
  font-family: var(--font-body);
  color: var(--text-primary);
  overflow-x: hidden;
}

.landing-main {
  position: relative;
}

/* Data flow background animation */
.landing-main::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(66, 133, 244, 0.15), transparent),
    radial-gradient(ellipse 60% 40% at 80% 60%, rgba(245, 158, 11, 0.05), transparent),
    radial-gradient(ellipse 50% 30% at 20% 80%, rgba(14, 165, 233, 0.05), transparent);
  pointer-events: none;
  z-index: 0;
}

/* Footer */
.landing-footer {
  position: relative;
  z-index: 1;
  background: hsl(220, 25%, 6%);
  border-top: 1px solid var(--border-color);
  padding: 4rem 0 2rem;
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
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--accent-cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.footer-tagline {
  color: var(--text-secondary);
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
  font-family: var(--font-display);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.footer-section a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

.footer-section a:hover {
  color: var(--primary-light);
}

.footer-bottom {
  max-width: 1200px;
  margin: 3rem auto 0;
  padding: 2rem 2rem 0;
  border-top: 1px solid var(--border-color);
  text-align: center;
  color: var(--text-muted);
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
