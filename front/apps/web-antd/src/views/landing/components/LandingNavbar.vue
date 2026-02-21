<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAccessStore } from '@vben/stores';
import { useLandingTheme } from '#/composables/useLandingTheme';

interface Props {
  showOnScroll?: number;
}

const props = withDefaults(defineProps<Props>(), {
  showOnScroll: 50,
});

const emit = defineEmits<{
  (e: 'getStarted'): void;
}>();

const router = useRouter();
const accessStore = useAccessStore();
const { theme, toggleTheme } = useLandingTheme();
const isScrolled = ref(false);

const isDark = computed(() => theme.value === 'dark');
const isLoggedIn = computed(() => !!accessStore.accessToken);

const handleScroll = () => {
  isScrolled.value = window.scrollY > props.showOnScroll;
};

const handleGetStarted = () => {
  emit('getStarted');
};

const handleGoToWorkspace = () => {
  router.push('/app');
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <nav class="navbar" :class="{ 'navbar-scrolled': isScrolled }">
    <div class="navbar-container">
      <div class="navbar-brand" @click="router.push('/')">
        <img
          src="/logo.png"
          alt="回响"
          class="navbar-logo"
        />
        <span class="navbar-name">回响</span>
      </div>

      <div class="navbar-links">
        <a href="#features" class="nav-link">功能</a>
        <a href="#workflow" class="nav-link">工作流程</a>
        <a href="#pricing" class="nav-link">定价</a>
        <a href="#" class="nav-link">文档</a>
      </div>

      <div class="navbar-actions">
        <button
          class="theme-toggle-btn"
          :class="{ 'is-dark': isDark, 'is-light': !isDark }"
          @click="toggleTheme"
          :title="isDark ? '切换到浅色主题' : '切换到深色主题'"
        >
          <svg v-if="isDark" class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
          <svg v-else class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="5"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
        </button>
        <!-- 已登录：显示进入工作台按钮 -->
        <template v-if="isLoggedIn">
          <button class="btn-primary" @click="handleGoToWorkspace">
            进入工作台
          </button>
        </template>
        <!-- 未登录：显示登录和免费试用按钮 -->
        <template v-else>
          <button class="btn-login" @click="router.push('/auth/login')">
            登录
          </button>
          <button class="btn-primary" @click="handleGetStarted">
            免费试用
          </button>
        </template>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: 1rem 0;
  transition: all 0.3s ease;
}

.navbar-scrolled {
  background: var(--lp-bg-elevated);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--lp-border-subtle);
  padding: 0.75rem 0;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.navbar-brand:hover {
  opacity: 0.9;
}

.navbar-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.navbar-name {
  font-family: var(--lp-font-display);
  font-size: 1.35rem;
  font-weight: 700;
  background: transparent;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: var(--lp-text-primary);
  background-clip: unset;
  color: var(--lp-text-primary);
}

.navbar-links {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  color: var(--lp-text-secondary);
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  transition: color 0.2s ease;
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--lp-primary-500);
  transition: width 0.2s ease;
}

.nav-link:hover {
  color: var(--lp-text-primary);
}

.nav-link:hover::after {
  width: 100%;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.theme-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--lp-text-secondary);
}

.theme-toggle-btn:hover {
  background: var(--lp-bg-card-hover);
  border-color: var(--lp-primary-400);
  color: var(--lp-text-primary);
}

.theme-toggle-btn svg {
  width: 20px;
  height: 20px;
}

.btn-login {
  padding: 0.6rem 1.25rem;
  background: transparent;
  border: 1px solid var(--lp-border-default);
  border-radius: 8px;
  color: var(--lp-text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-login:hover {
  border-color: var(--lp-primary-400);
  color: var(--lp-text-primary);
}

.btn-primary {
  padding: 0.6rem 1.5rem;
  background: var(--lp-gradient-primary);
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px var(--lp-glow-primary);
}

@media (max-width: 768px) {
  .navbar-links {
    display: none;
  }

  .navbar-name {
    display: none;
  }
}
</style>
