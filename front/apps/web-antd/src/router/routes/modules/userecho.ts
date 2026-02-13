import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:messages-square',
      order: 0,
      title: $t('page.userecho.title'),
    },
    name: 'UserEcho',
    path: '/app/userecho',
    children: [
      {
        name: 'FeedbackList',
        path: '/app/feedback/list',
        component: () => import('#/views/userecho/feedback/list.vue'),
        meta: {
          icon: 'lucide:inbox',
          title: $t('page.userecho.feedback.list'),
        },
      },
      {
        name: 'AIDiscovery',
        path: '/app/ai/discovery',
        component: () => import('#/views/userecho/discovery/index.vue'),
        meta: {
          icon: 'lucide:sparkles',
          title: 'AI 发现中心',
        },
      },
      {
        name: 'FeedbackImport',
        path: '/app/feedback/import',
        component: () => import('#/views/userecho/feedback/import.vue'),
        meta: {
          icon: 'lucide:upload',
          title: $t('page.userecho.feedback.import'),
        },
      },
      {
        name: 'TopicList',
        path: '/app/topic/list',
        component: () => import('#/views/userecho/topic/list.vue'),
        meta: {
          icon: 'lucide:lightbulb',
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
          title: $t('page.userecho.customer.title'),
        },
      },
    ],
  },
];

export default routes;
