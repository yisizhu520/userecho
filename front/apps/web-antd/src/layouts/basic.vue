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
  markNotificationAsRead,
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
// 细粒度权限控制：所有人可访问基础设置，高级功能按角色控制
provide('preferencesAccess', {
  // 所有人都可以访问设置入口
  canView: () => true,

  // 超级管理员 或 系统管理员（用于系统级配置：Footer、Copyright）
  isAdmin: () => {
    const userType = userStore.userInfo?.userType;
    return userType === 'admin' || userType === 'staff';
  },

  // 租户管理员（角色名称为"管理员"）
  isTenantAdmin: () => {
    return userStore.userRoles.includes('管理员');
  },

  // 产品经理
  isProductManager: () => {
    return userStore.userRoles.includes('产品经理');
  },

  // 是否可以配置聚类（管理员 + 产品经理）
  canConfigureClustering: () => {
    return userStore.userRoles.includes('管理员') ||
           userStore.userRoles.includes('产品经理');
  },
});

const userStore = useUserStore();
const authStore = useAuthStore();
const accessStore = useAccessStore();
const { destroyWatermark, updateWatermark } = useWatermark();

// 系统通知数据
const notifications = ref<NotificationItem[]>([]);
const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null);
const notificationRef = ref<{ openPopover: () => void } | null>(null);
const lastUnreadIds = ref<Set<string>>(new Set()); // 跟踪上次的未读消息 ID

// 加载系统通知（默认只显示未读）
async function loadNotifications() {
  try {
    const result = await getSystemNotifications(true); // 只获取未读通知
    const newNotifications = result.items.map((item) => ({
      avatar: item.avatar || 'https://avatar.vercel.sh/notification.svg?text=N',
      date: item.date || '',
      isRead: item.is_read,
      message: item.message,
      title: item.title,
      // 扩展字段用于点击跳转
      actionUrl: item.action_url,
      id: item.id,
    }));

    // 检测是否有新的未读消息
    const currentUnreadIds = new Set(newNotifications.map((n) => n.id));
    const hasNewMessages = Array.from(currentUnreadIds).some(
      (id) => !lastUnreadIds.value.has(id),
    );

    // 如果有新消息且不是首次加载，自动弹出 popover
    if (hasNewMessages && lastUnreadIds.value.size > 0) {
      notificationRef.value?.openPopover();
    }

    // 更新状态
    notifications.value = newNotifications;
    lastUnreadIds.value = currentUnreadIds;
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
      router.push('/app/profile');
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

// 处理点击单个通知
async function handleNotificationClick(item: NotificationItem) {
  try {
    // 1. 标记为已读
    await markNotificationAsRead(item.id);

    // 2. 更新本地状态
    const notification = notifications.value.find((n) => n.id === item.id);
    if (notification) {
      notification.isRead = true;
    }

    // 3. 跳转到目标页面
    if (item.actionUrl) {
      router.push(item.actionUrl);
    }
  } catch {
    // 静默处理
  }
}

// 处理"查看所有消息"按钮
async function handleViewAll() {
  try {
    // 加载所有通知（包括已读和未读）
    const result = await getSystemNotifications(false); // false 表示获取所有通知
    notifications.value = result.items.map((item) => ({
      id: item.id,
      avatar: item.avatar || 'https://avatar.vercel.sh/notification.svg?text=N',
      title: item.title,
      message: item.message,
      date: item.date || '',
      isRead: item.is_read,
      actionUrl: item.action_url,
    }));
  } catch {
    // 静默处理
  }
}

// 处理快速标记已读（不跳转）
async function handleNotificationMarkRead(item: NotificationItem) {
  try {
    // 1. 调用 API 标记为已读
    await markNotificationAsRead(item.id);

    // 2. 更新本地状态
    const notification = notifications.value.find((n) => n.id === item.id);
    if (notification) {
      notification.isRead = true;
    }
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
        :text="userStore.userInfo?.nickname || userStore.userInfo?.username"
        :description="userStore.userInfo?.email || ''"
        :tag-text="userStore.userInfo?.userType === 'admin' ? '超级管理员' : userStore.userInfo?.userType === 'staff' ? '系统管理员' : ''"
        @logout="handleLogout"
      />
    </template>
    <template #notification>
      <Notification
        ref="notificationRef"
        :dot="showDot"
        :notifications="notifications"
        @clear="handleNoticeClear"
        @make-all="handleMakeAll"
        @read="handleNotificationClick"
        @view-all="handleViewAll"
        @mark-read="handleNotificationMarkRead"
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
