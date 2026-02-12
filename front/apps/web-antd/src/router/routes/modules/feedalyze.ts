import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:messages-square',
      order: 0,
      title: $t('page.feedalyze.title'),
    },
    name: 'Feedalyze',
    path: '/app/feedalyze',
    children: [
      {
        name: 'FeedbackList',
        path: '/app/feedback/list',
        component: () => import('#/views/feedalyze/feedback/list.vue'),
        meta: {
          icon: 'lucide:inbox',
          title: $t('page.feedalyze.feedback.list'),
        },
      },
      {
        name: 'FeedbackImport',
        path: '/app/feedback/import',
        component: () => import('#/views/feedalyze/feedback/import.vue'),
        meta: {
          icon: 'lucide:upload',
          title: $t('page.feedalyze.feedback.import'),
        },
      },
      {
        name: 'TopicList',
        path: '/app/topic/list',
        component: () => import('#/views/feedalyze/topic/list.vue'),
        meta: {
          icon: 'lucide:lightbulb',
          title: $t('page.feedalyze.topic.list'),
        },
      },
      {
        name: 'TopicDetail',
        path: '/app/topic/detail/:id',
        component: () => import('#/views/feedalyze/topic/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('page.feedalyze.topic.detail'),
        },
      },
      {
        name: 'CustomerManage',
        path: '/app/customer',
        component: () => import('#/views/feedalyze/customer/index.vue'),
        meta: {
          icon: 'lucide:users',
          title: $t('page.feedalyze.customer.title'),
        },
      },
    ],
  },
];

export default routes;
