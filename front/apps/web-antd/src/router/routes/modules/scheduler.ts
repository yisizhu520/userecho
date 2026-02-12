import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'Scheduler',
    path: '/admin/scheduler',
    meta: {
      title: $t('page.menu.scheduler'),
      icon: 'ix:scheduler',
      order: 5,
    },
    children: [
      {
        name: 'SchedulerManage',
        path: '/admin/scheduler/manage',
        component: () => import('#/views/scheduler/manage/index.vue'),
        meta: {
          title: $t('page.menu.schedulerManage'),
          icon: 'ix:scheduler',
        },
      },
      {
        name: 'SchedulerRecord',
        path: '/admin/scheduler/record',
        component: () => import('#/views/scheduler/record/index.vue'),
        meta: {
          title: $t('page.menu.schedulerRecord'),
          icon: 'ix:scheduler',
        },
      },
    ],
  },
];

export default routes;
