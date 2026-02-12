import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'Feedalyze',
    path: '/feedalyze',
    meta: {
      title: $t('page.menu.feedalyze'),
      icon: 'lucide:messages-square',
      order: 0,
    },
    children: [
      {
        name: 'FeedbackList',
        path: '/feedalyze/feedback/list',
        component: () => import('#/views/feedalyze/feedback/list.vue'),
        meta: {
          title: $t('page.menu.feedbackList'),
          icon: 'lucide:inbox',
        },
      },
      {
        name: 'FeedbackImport',
        path: '/feedalyze/feedback/import',
        component: () => import('#/views/feedalyze/feedback/import.vue'),
        meta: {
          title: $t('page.menu.feedbackImport'),
          icon: 'lucide:upload',
        },
      },
      {
        name: 'TopicList',
        path: '/feedalyze/topic/list',
        component: () => import('#/views/feedalyze/topic/list.vue'),
        meta: {
          title: $t('page.menu.topicList'),
          icon: 'lucide:lightbulb',
        },
      },
      {
        name: 'TopicDetail',
        path: '/feedalyze/topic/detail/:id',
        component: () => import('#/views/feedalyze/topic/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('page.menu.topicDetail'),
          icon: 'lucide:file-text',
        },
      },
      {
        name: 'CustomerManage',
        path: '/feedalyze/customer',
        component: () => import('#/views/feedalyze/customer/index.vue'),
        meta: {
          title: $t('page.menu.customerManage'),
          icon: 'lucide:users',
        },
      },
    ],
  },
];

export default routes;
