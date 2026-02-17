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
    },
  },
  {
    name: 'FeedbackList',
    path: '/app/feedback/list',
    component: () => import('#/views/userecho/feedback/list.vue'),
    meta: {
      icon: 'lucide:inbox',
      order: 0,
      title: $t('page.userecho.feedback.list'),
    },
  },
  {
    name: 'ScreenshotUpload',
    path: '/app/feedback/screenshot',
    component: () => import('#/views/userecho/feedback/screenshot-upload.vue'),
    meta: {
      hideInMenu: true,
      title: '截图识别',
    },
  },
  {
    name: 'FeedbackImport',
    path: '/app/feedback/import',
    component: () => import('#/views/userecho/feedback/import.vue'),
    meta: {
      hideInMenu: true,
      title: $t('page.userecho.feedback.import'),
    },
  },
  {
    name: 'AIDiscovery',
    path: '/app/ai/discovery',
    component: () => import('#/views/userecho/discovery/index.vue'),
    meta: {
      icon: 'lucide:sparkles',
      order: 2,
      title: $t('page.userecho.discovery.title'),
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
    },
  },
  {
    name: 'ClusteringConfig',
    path: '/app/settings/clustering',
    component: () => import('#/views/userecho/settings/clustering-config.vue'),
    meta: {
      hideInMenu: true,
      icon: 'lucide:layers',
      title: $t('page.userecho.settings.clustering'),
    },
  },
];

export default routes;
