<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

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
const isScrolled = ref(false);

const handleScroll = () => {
  isScrolled.value = window.scrollY > props.showOnScroll;
};

const handleGetStarted = () => {
  emit('getStarted');
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
          src="https://wu-clan.github.io/picx-images-hosting/logo/fba.png"
          alt="Feedalyze"
          class="navbar-logo"
        />
        <span class="navbar-name">Feedalyze</span>
      </div>

      <div class="navbar-links">
        <a href="#features" class="nav-link">功能</a>
        <a href="#workflow" class="nav-link">工作流程</a>
        <a href="#" class="nav-link">定价</a>
        <a href="#" class="nav-link">文档</a>
      </div>

      <div class="navbar-actions">
        <button class="btn-login" @click="router.push('/auth/login')">
          登录
        </button>
        <button class="btn-primary" @click="handleGetStarted">
          免费试用
        </button>
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
  background: hsla(220, 25%, 6%, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid hsla(220, 20%, 20%, 0.5);
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
  font-family: 'Outfit', -apple-system, sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  background: linear-gradient(135deg, hsl(212, 100%, 55%) 0%, hsl(188, 78%, 55%) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.navbar-links {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  color: hsl(220, 10%, 75%);
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
  background: linear-gradient(90deg, hsl(212, 100%, 55%), hsl(188, 78%, 55%));
  transition: width 0.2s ease;
}

.nav-link:hover {
  color: hsl(0, 0%, 100%);
}

.nav-link:hover::after {
  width: 100%;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-login {
  padding: 0.6rem 1.25rem;
  background: transparent;
  border: 1px solid hsla(220, 20%, 30%, 0.5);
  border-radius: 8px;
  color: hsl(220, 10%, 75%);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-login:hover {
  border-color: hsl(212, 100%, 45%);
  color: hsl(0, 0%, 100%);
}

.btn-primary {
  padding: 0.6rem 1.5rem;
  background: linear-gradient(135deg, hsl(212, 100%, 45%) 0%, hsl(212, 100%, 35%) 100%);
  border: none;
  border-radius: 8px;
  color: hsl(0, 0%, 100%);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px hsla(212, 100%, 45%, 0.3);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px hsla(212, 100%, 45%, 0.4);
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
