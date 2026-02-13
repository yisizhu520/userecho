import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
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
    name: 'AIDiscovery',
    path: '/app/ai/discovery',
    component: () => import('#/views/userecho/discovery/index.vue'),
    meta: {
      icon: 'lucide:sparkles',
      order: 1,
      title: $t('page.userecho.discovery.title'),
    },
  },
  {
    name: 'FeedbackImport',
    path: '/app/feedback/import',
    component: () => import('#/views/userecho/feedback/import.vue'),
    meta: {
      icon: 'lucide:upload',
      order: 2,
      title: $t('page.userecho.feedback.import'),
    },
  },
  {
    name: 'TopicList',
    path: '/app/topic/list',
    component: () => import('#/views/userecho/topic/list.vue'),
    meta: {
      icon: 'lucide:lightbulb',
      order: 3,
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
    name: 'Settings',
    path: '/app/settings',
    meta: {
      icon: 'lucide:settings',
      order: 5,
      title: $t('page.userecho.settings.title'),
    },
    children: [
      {
        name: 'ClusteringConfig',
        path: '/app/settings/clustering',
        component: () => import('#/views/userecho/settings/clustering-config.vue'),
        meta: {
          icon: 'lucide:layers',
          title: $t('page.userecho.settings.clustering'),
        },
      },
    ],
  },
];

export default routes;
