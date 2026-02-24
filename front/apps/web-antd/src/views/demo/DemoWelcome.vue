<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Target, Headphones, Settings } from 'lucide-vue-next';
import { requestClient } from '#/api/request';
import { useAccessStore } from '@vben/stores';
import { useLandingTheme } from '#/composables/useLandingTheme';

const router = useRouter();
const accessStore = useAccessStore();
const { theme, initTheme } = useLandingTheme();
const loading = ref(false);
const selectedRole = ref('');

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
  },
  {
    key: 'user_ops',
    name: '用户运营',
    description: '录入反馈、管理客户、触发聚类',
    icon: Headphones,
    color: '#10b981',
  },
  {
    key: 'admin',
    name: '系统管理员',
    description: '用户管理、权限配置、看板设置',
    icon: Settings,
    color: '#f59e0b',
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
  <div class="demo-welcome" :class="`theme-${theme}`">
    <div class="welcome-container">
      <div class="welcome-header">
        <div class="logo">
          <img src="/logo.png" alt="回响" class="logo-icon" />
          <span class="logo-text">回响</span>
          <span class="demo-badge">演示版</span>
        </div>
        <h1>欢迎体验「回响」</h1>
        <p>选择一个角色，开始探索 AI 驱动的用户反馈分析平台</p>
      </div>

      <div class="role-cards">
        <div
          v-for="role in roles"
          :key="role.key"
          class="role-card"
          :class="{ active: selectedRole === role.key, loading: loading && selectedRole === role.key }"
          @click="handleSelectRole(role.key)"
        >
          <div class="role-icon" :style="{ backgroundColor: role.color + '15', color: role.color }">
            <component :is="role.icon" :size="28" />
          </div>
          <div class="role-info">
            <h3>{{ role.name }}</h3>
            <p>{{ role.description }}</p>
          </div>
          <div v-if="loading && selectedRole === role.key" class="loading-spinner" />
        </div>
      </div>

      <div class="demo-notice">
        <div class="notice-icon">🔬</div>
        <div class="notice-content">
          <span>这是演示环境，数据每日凌晨 2 点自动重置</span>
          <a href="https://huixiang.app" target="_blank" class="register-link">
            注册正式版 →
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Dark theme variables */
.demo-welcome.theme-dark {
  --demo-bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  --demo-text-primary: #f8fafc;
  --demo-text-secondary: #cbd5e1;
  --demo-text-muted: #94a3b8;
  --demo-card-bg: rgba(30, 41, 59, 0.8);
  --demo-card-hover-bg: rgba(30, 41, 59, 0.95);
  --demo-border: rgba(148, 163, 184, 0.15);
  --demo-border-hover: rgba(59, 130, 246, 0.4);
  --demo-badge-bg: linear-gradient(135deg, #3b82f6, #8b5cf6);
  --demo-notice-bg: rgba(59, 130, 246, 0.1);
  --demo-notice-border: rgba(59, 130, 246, 0.2);
}

/* Light theme variables */
.demo-welcome.theme-light {
  --demo-bg-gradient: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  --demo-text-primary: #0f172a;
  --demo-text-secondary: #334155;
  --demo-text-muted: #64748b;
  --demo-card-bg: #ffffff;
  --demo-card-hover-bg: #f8fafc;
  --demo-border: #cbd5e1;
  --demo-border-hover: #3b82f6;
  --demo-badge-bg: linear-gradient(135deg, #3b82f6, #8b5cf6);
  --demo-notice-bg: rgba(59, 130, 246, 0.08);
  --demo-notice-border: rgba(59, 130, 246, 0.2);
}
</style>

<style scoped>
.demo-welcome {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--demo-bg-gradient);
  padding: 24px;
  transition: background 0.3s ease;
}

.welcome-container {
  max-width: 800px;
  width: 100%;
}

.welcome-header {
  text-align: center;
  margin-bottom: 48px;
}

.logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.demo-badge {
  background: var(--demo-badge-bg);
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  margin-left: 8px;
}

.welcome-header h1 {
  font-size: 36px;
  font-weight: 700;
  color: var(--demo-text-primary);
  margin: 0 0 12px 0;
  transition: color 0.3s ease;
}

.welcome-header p {
  font-size: 16px;
  color: var(--demo-text-muted);
  margin: 0;
  transition: color 0.3s ease;
}

.role-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

.role-card {
  background: var(--demo-card-bg);
  border: 1px solid var(--demo-border);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.role-card:hover {
  background: var(--demo-card-hover-bg);
  border-color: var(--demo-border-hover);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.theme-light .role-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
}

.role-card.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.role-card.loading {
  pointer-events: none;
  opacity: 0.8;
}

.role-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.role-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--demo-text-primary);
  margin: 0 0 8px 0;
  transition: color 0.3s ease;
}

.role-info p {
  font-size: 13px;
  color: var(--demo-text-muted);
  margin: 0;
  line-height: 1.5;
  transition: color 0.3s ease;
}

.loading-spinner {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.demo-notice {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--demo-notice-bg);
  border: 1px solid var(--demo-notice-border);
  border-radius: 12px;
  padding: 16px 20px;
  transition: background 0.3s ease, border-color 0.3s ease;
}

.notice-icon {
  font-size: 24px;
}

.notice-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  color: var(--demo-text-muted);
  font-size: 14px;
  transition: color 0.3s ease;
}

.register-link {
  color: #3b82f6;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
}

.register-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .role-cards {
    grid-template-columns: 1fr;
  }

  .welcome-header h1 {
    font-size: 28px;
  }

  .notice-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
