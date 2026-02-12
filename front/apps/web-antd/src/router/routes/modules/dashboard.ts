import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: $t('page.dashboard.title'),
    },
    name: 'Dashboard',
    path: '/app/dashboard',
    redirect: '/app/analytics',
    children: [
      {
        name: 'Analytics',
        path: '/app/dashboard/analytics',
        alias: '/app/analytics',
        component: () => import('#/views/dashboard/analytics/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:area-chart',
          link: '/app/analytics',
          title: $t('page.dashboard.analytics'),
        },
      },
      {
        name: 'Workspace',
        path: '/app/dashboard/workspace',
        alias: '/app/workspace',
        component: () => import('#/views/dashboard/workspace/index.vue'),
        meta: {
          icon: 'carbon:workspace',
          link: '/app/workspace',
          title: $t('page.dashboard.workspace'),
        },
      },
    ],
  },
];

export default routes;
