import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'System',
    path: '/admin/system',
    redirect: '/admin/system/overview',
    meta: {
      title: $t('page.menu.system'),
      icon: 'grommet-icons:system',
      order: 1,
    },
    children: [
      {
        name: 'SysOverview',
        path: '/admin/system/overview',
        component: () => import('#/views/system/overview/index.vue'),
        meta: {
          title: $t('page.menu.sysOverview'),
          icon: 'lucide:layout-dashboard',
        },
      },
      {
        name: 'SysDept',
        path: '/admin/system/dept',
        component: () => import('#/views/system/dept/index.vue'),
        meta: {
          title: $t('page.menu.sysDept'),
          icon: 'mingcute:department-line',
        },
      },
      {
        name: 'SysUser',
        path: '/admin/system/user',
        component: () => import('#/views/system/user/index.vue'),
        meta: {
          title: $t('page.menu.sysUser'),
          icon: 'ant-design:user-outlined',
        },
      },
      {
        name: 'SysRole',
        path: '/admin/system/role',
        component: () => import('#/views/system/role/index.vue'),
        meta: {
          title: $t('page.menu.sysRole'),
          icon: 'carbon:user-role',
        },
      },
      {
        name: 'SysMenu',
        path: '/admin/system/menu',
        component: () => import('#/views/system/menu/index.vue'),
        meta: {
          title: $t('page.menu.sysMenu'),
          icon: 'material-symbols:menu',
        },
      },
      {
        name: 'SysDataPermission',
        path: '/admin/system/data-permission',
        meta: {
          title: $t('page.menu.sysDataPermission'),
          icon: 'icon-park-outline:permissions',
        },
        children: [
          {
            name: 'SysDataScope',
            path: '/admin/system/data-scope',
            component: () =>
              import('#/views/system/data-permission/scope/index.vue'),
            meta: {
              title: $t('page.menu.sysDataScope'),
              icon: 'cuida:scope-outline',
            },
          },
          {
            name: 'SysDataRule',
            path: '/admin/system/data-rule',
            component: () =>
              import('#/views/system/data-permission/rule/index.vue'),
            meta: {
              title: $t('page.menu.sysDataRule'),
              icon: 'material-symbols:rule',
            },
          },
        ],
      },
      {
        name: 'SysPlugin',
        path: '/admin/system/plugin',
        component: () => import('#/views/system/plugin/index.vue'),
        meta: {
          title: $t('page.menu.sysPlugin'),
          icon: 'clarity:plugin-line',
        },
      },
      {
        name: 'SysSubscription',
        path: '/admin/system/subscription',
        component: () => import('#/views/system/subscription/index.vue'),
        meta: {
          title: '订阅管理',
          icon: 'eos-icons:subscription-management-outlined',
        },
      },
      {
        name: 'SysInvitation',
        path: '/admin/system/invitation',
        component: () => import('#/views/system/invitation/index.vue'),
        meta: {
          title: '邀请管理',
          icon: 'mdi:invitation',
        },
      },
      {
        name: 'SysInvitationDetail',
        path: '/admin/system/invitation/:id',
        component: () => import('#/views/system/invitation/detail.vue'),
        meta: {
          title: '邀请详情',
          hideInMenu: true,
        },
      },
    ],
  },
];

export default routes;
