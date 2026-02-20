<script setup lang="ts">
import { ref, computed } from 'vue';
import { Target, Headphones, Settings, ChevronUp } from 'lucide-vue-next';
import { requestClient } from '#/api/request';
import { useAccessStore } from '@vben/stores';

const accessStore = useAccessStore();
const expanded = ref(false);
const loading = ref(false);
const currentRole = ref('product_owner');

const roles = [
  { key: 'product_owner', name: '产品负责人', icon: Target, color: '#3b82f6' },
  { key: 'user_ops', name: '用户运营', icon: Headphones, color: '#10b981' },
  { key: 'admin', name: '系统管理员', icon: Settings, color: '#f59e0b' },
];

const currentRoleInfo = computed(() =>
  roles.find(r => r.key === currentRole.value) || roles[0]
);

const handleSwitchRole = async (roleKey: string) => {
  if (roleKey === currentRole.value || loading.value) return;

  loading.value = true;
  try {
    const response = await requestClient.post<{
      access_token: string;
      role: { key: string; name: string };
    }>('/api/v1/demo/switch-role', { role_key: roleKey });

    // 更新 token
    accessStore.setAccessToken(response.access_token);
    currentRole.value = roleKey;

    // 刷新页面以加载新权限
    window.location.reload();
  } catch (error) {
    console.error('角色切换失败:', error);
  } finally {
    loading.value = false;
    expanded.value = false;
  }
};
</script>

<template>
  <div class="demo-role-switcher" :class="{ expanded }">
    <!-- 收起状态：显示当前角色 -->
    <div class="current-role" @click="expanded = !expanded">
      <component
        :is="currentRoleInfo.icon"
        class="role-icon"
        :size="20"
        :style="{ color: currentRoleInfo.color }"
      />
      <span class="role-name">{{ currentRoleInfo.name }}</span>
      <ChevronUp class="expand-icon" :class="{ rotate: !expanded }" :size="16" />
    </div>

    <!-- 展开状态：显示所有角色 -->
    <Transition name="slide">
      <div v-if="expanded" class="role-list">
        <div
          v-for="role in roles"
          :key="role.key"
          class="role-item"
          :class="{ active: role.key === currentRole, loading }"
          @click="handleSwitchRole(role.key)"
        >
          <component :is="role.icon" :size="18" :style="{ color: role.color }" />
          <span>{{ role.name }}</span>
        </div>
      </div>
    </Transition>

    <!-- Demo 标识 -->
    <div class="demo-badge">演示模式</div>
  </div>
</template>

<style scoped>
.demo-role-switcher {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  background: var(--component-background, #fff);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
  padding: 12px;
  min-width: 180px;
}

.current-role {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.current-role:hover {
  background: var(--component-background-hover, #f5f5f5);
}

.role-icon {
  flex-shrink: 0;
}

.role-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-color);
}

.expand-icon {
  flex-shrink: 0;
  color: var(--text-color-secondary);
  transition: transform 0.2s;
}

.expand-icon.rotate {
  transform: rotate(180deg);
}

.role-list {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color, #eee);
}

.role-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-color);
}

.role-item:hover:not(.loading) {
  background: var(--component-background-hover, #f5f5f5);
}

.role-item.active {
  background: var(--primary-1, #eff6ff);
}

.role-item.loading {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-badge {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
