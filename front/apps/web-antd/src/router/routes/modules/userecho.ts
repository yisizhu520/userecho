import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';
import { useTopicStore } from '#/store';

const routes: RouteRecordRaw[] = [
  {
    name: 'UserEchoWorkspace',
    path: '/app/dashboard/workspace',
    component: () => import('#/views/userecho/dashboard/workspace.vue'),
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: '工作台',
      // 工作台对所有人可见，不需要权限
    },
  },
  {
    name: 'Profile',
    path: '/app/profile',
    component: () => import('#/views/_core/profile/index.vue'),
    meta: {
      title: $t('page.menu.profile'),
      icon: 'mingcute:profile-line',
      hideInMenu: true,
      // 个人中心对所有登录用户可见，不需要权限
    },
  },
  {
    name: 'FeedbackManagement',
    path: '/app/feedback',
    meta: {
      icon: 'lucide:inbox',
      order: 0,
      title: $t('page.userecho.feedback.list'),
      permissionCode: 'feedback',
    },
    redirect: '/app/feedback/list',
    children: [
      {
        name: 'FeedbackList',
        path: 'list',
        component: () => import('#/views/userecho/feedback/list.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          title: $t('page.userecho.feedback.list'),
        },
      },
      {
        name: 'ScreenshotUpload',
        path: 'screenshot',
        component: () => import('#/views/userecho/feedback/screenshot-upload.vue'),
        meta: {
          hideInMenu: true,
          title: '截图识别',
        },
      },
      {
        name: 'ScreenshotBatchUpload',
        path: 'screenshot-batch',
        component: () => import('#/views/userecho/feedback/screenshot-batch-upload.vue'),
        meta: {
          hideInMenu: true,
          title: '批量截图识别',
        },
      },
      {
        name: 'FeedbackImport',
        path: 'import',
        component: () => import('#/views/userecho/feedback/import.vue'),
        meta: {
          hideInMenu: true,
          title: $t('page.userecho.feedback.import'),
        },
      },
    ],
  },
  {
    name: 'AIDiscovery',
    path: '/app/ai/discovery',
    component: () => import('#/views/userecho/discovery/index.vue'),
    meta: {
      icon: 'lucide:sparkles',
      order: 2,
      title: $t('page.userecho.discovery.title'),
      permissionCode: 'discovery',
      // 显示具体数字（动态 badge）- 懒加载 store
      get badge() {
        const topicStore = useTopicStore();
        const count = topicStore.pendingCount;
        return count > 0 ? String(count) : undefined;
      },
      badgeType: 'normal',
      badgeVariants: 'destructive',
    },
  },
  {
    name: 'TopicList',
    path: '/app/topic/list',
    component: () => import('#/views/userecho/topic/list.vue'),
    meta: {
      icon: 'lucide:lightbulb',
      order: 4,
      title: $t('page.userecho.topic.list'),
      permissionCode: 'topic',
    },
  },
  {
    name: 'TopicDetail',
    path: '/app/topic/detail/:id',
    component: () => import('#/views/userecho/topic/detail.vue'),
    meta: {
      hideInMenu: true,
      title: $t('page.userecho.topic.detail'),
    },
  },
  {
    name: 'CustomerManage',
    path: '/app/customer',
    component: () => import('#/views/userecho/customer/index.vue'),
    meta: {
      icon: 'lucide:users',
      order: 4,
      title: $t('page.userecho.customer.title'),
      permissionCode: 'customer',
    },
  },
  {
    name: 'InsightReport',
    path: '/app/insights/report',
    component: () => import('#/views/userecho/insights/report.vue'),
    meta: {
      icon: 'lucide:file-bar-chart',
      order: 4.5,
      title: '洞察报告',
      permissionCode: 'insight',
    },
  },
  {
    name: 'UserTaskCenter',
    path: '/app/tasks',
    component: () => import('#/views/userecho/batch-jobs/index.vue'),
    meta: {
      icon: 'lucide:list-checks',
      order: 5,
      title: '我的任务',
      // 我的任务对所有人可见
    },
  },
  {
    name: 'Settings',
    path: '/app/settings',
    meta: {
      icon: 'lucide:settings',
      order: 99,
      title: '系统设置',
      permissionCode: 'settings',
    },
    redirect: '/app/settings/members',
    children: [
      {
        name: 'MembersManage',
        path: 'members',
        component: () => import('#/views/userecho/settings/members.vue'),
        meta: {
          icon: 'lucide:users',
          title: '成员管理',
          permissionCode: 'member',
        },
      },
      {
        name: 'RolesManage',
        path: 'roles',
        component: () => import('#/views/userecho/settings/roles.vue'),
        meta: {
          icon: 'lucide:shield',
          title: '角色管理',
          permissionCode: 'role',
        },
      },
      {
        name: 'BoardsManage',
        path: 'boards',
        component: () => import('#/views/userecho/settings/boards.vue'),
        meta: {
          icon: 'lucide:layout-dashboard',
          title: '看板管理',
          permissionCode: 'board_manage',
        },
      },
      {
        name: 'SubscriptionManage',
        path: 'subscription',
        component: () => import('#/views/userecho/settings/subscription.vue'),
        meta: {
          icon: 'lucide:credit-card',
          title: '订阅信息',
          // 任何租户成员都能查看订阅状态，还是只有管理员？
          // 暂时假设有 Settings 权限的都能看
        },
      },
    ],
  },
];

export default routes;
