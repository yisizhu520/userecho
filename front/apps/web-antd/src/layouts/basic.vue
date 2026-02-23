<script lang="ts" setup>
import type { NotificationItem } from '@vben/layouts';

import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue';

import { AuthenticationLoginExpiredModal } from '@vben/common-ui';
import { useWatermark } from '@vben/hooks';
import { MingcuteProfileLine } from '@vben/icons';
import {
  BasicLayout,
  LockScreen,
  Notification,
  UserDropdown,
} from '@vben/layouts';
import { $t } from '@vben/locales';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';

import {
  getClusteringConfig,
  getClusteringPresets,
  previewClusteringConfig,
  updateClusteringPreset,
  getSystemNotifications,
  markAllNotificationsAsRead,
  clearAllNotifications,
} from '#/api';
import { router } from '#/router';
import { useAuthStore } from '#/store';
import LoginForm from '#/views/_core/authentication/login.vue';

// Provide 聚类 API 给 preferences 组件使用
provide('clusteringAPI', {
  getPresets: getClusteringPresets,
  getConfig: getClusteringConfig,
  updatePreset: updateClusteringPreset,
  preview: previewClusteringConfig,
});

// Provide 权限检查函数给 preferences 组件使用
provide('preferencesAccess', {
  isAdmin: () => userStore.userRoles.includes('admin'),
  isTenantAdmin: () => userStore.userRoles.includes('boss'),
});

const userStore = useUserStore();
const authStore = useAuthStore();
const accessStore = useAccessStore();
const { destroyWatermark, updateWatermark } = useWatermark();

// 系统通知数据
const notifications = ref<NotificationItem[]>([]);
const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null);

// 加载系统通知
async function loadNotifications() {
  try {
    const result = await getSystemNotifications();
    notifications.value = result.items.map((item) => ({
      avatar: item.avatar || 'https://avatar.vercel.sh/notification.svg?text=N',
      date: item.date || '',
      isRead: item.is_read,
      message: item.message,
      title: item.title,
      // 扩展字段用于点击跳转
      actionUrl: item.action_url,
      id: item.id,
    }));
  } catch {
    // 静默处理错误，不打断用户
  }
}


const showDot = computed(() =>
  notifications.value.some((item) => !item.isRead),
);

const menus = computed(() => [
  {
    handler: () => {
      router.push('/profile');
    },
    icon: MingcuteProfileLine,
    text: $t('page.menu.profile'),
  },
]);

const avatar = computed(() => {
  return userStore.userInfo?.avatar ?? preferences.app.defaultAvatar;
});

async function handleLogout() {
  await authStore.logout(false);
}

async function handleNoticeClear() {
  try {
    await clearAllNotifications();
    notifications.value = [];
  } catch {
    // 静默处理
  }
}

async function handleMakeAll() {
  try {
    await markAllNotificationsAsRead();
    notifications.value.forEach((item) => (item.isRead = true));
  } catch {
    // 静默处理
  }
}

// 启动轮询
function startPolling() {
  // 每 60 秒刷新一次
  pollingTimer.value = setInterval(loadNotifications, 60000);
}

// 停止轮询
function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
}

// 组件挂载时加载通知并启动轮询
onMounted(() => {
  loadNotifications();
  startPolling();
});

// 组件卸载时停止轮询
onUnmounted(() => {
  stopPolling();
});

watch(
  () => preferences.app.watermark,
  async (enable) => {
    if (enable) {
      await updateWatermark({
        content: `${userStore.userInfo?.username} - ${userStore.userInfo?.realName}`,
      });
    } else {
      destroyWatermark();
    }
  },
  {
    immediate: true,
  },
);
</script>

<template>
  <BasicLayout @clear-preferences-and-logout="handleLogout">

    <template #user-dropdown>
      <UserDropdown
        :avatar
        :menus
        :text="userStore.userInfo?.realName"
        description="ann.vben@gmail.com"
        tag-text="Pro"
        @logout="handleLogout"
      />
    </template>
    <template #notification>
      <Notification
        :dot="showDot"
        :notifications="notifications"
        @clear="handleNoticeClear"
        @make-all="handleMakeAll"
      />
    </template>
    <template #extra>
      <AuthenticationLoginExpiredModal
        v-model:open="accessStore.loginExpired"
        :avatar
      >
        <LoginForm />
      </AuthenticationLoginExpiredModal>
    </template>
    <template #lock-screen>
      <LockScreen :avatar @to-login="handleLogout" />
    </template>
  </BasicLayout>
</template>
