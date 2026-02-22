import type {
  ComponentRecordType,
  GenerateMenuAndRoutesOptions,
} from '@vben/types';

import { generateAccessible } from '@vben/access';
import { preferences } from '@vben/preferences';

import { message } from 'ant-design-vue';

import { getAllMenusApi } from '#/api';
import { BasicLayout, IFrameView } from '#/layouts';
import { $t } from '#/locales';

import { getBusinessMenus } from './business-menus';

const forbiddenComponent = () => import('#/views/_core/fallback/forbidden.vue');

async function generateAccess(options: GenerateMenuAndRoutesOptions) {
  const pageMap: ComponentRecordType = {
    ...import.meta.glob('/src/views/**/*.vue'),
    ...import.meta.glob('/src/plugins/**/*.vue'),
  };

  const layoutMap: ComponentRecordType = {
    BasicLayout,
    IFrameView,
  };

  const accessMode = preferences.app.accessMode;

  const baseOptions: GenerateMenuAndRoutesOptions = {
    ...options,
    fetchMenuListAsync: async () => {
      message.loading({
        content: `${$t('common.loadingMenu')}...`,
        duration: 1.5,
      });

      // 1. 获取后端系统菜单 (/admin/*)
      const backendMenus = await getAllMenusApi();

      // 2. 获取前端业务菜单 (/app/*) - 根据租户权限过滤
      const businessMenus = getBusinessMenus();

      // 3. 合并菜单：业务菜单在前，系统菜单在后
      return [...businessMenus, ...backendMenus];
    },
    // 可以指定没有权限跳转403页面
    forbiddenComponent,
    // 如果 route.meta.menuVisibleWithForbidden = true
    layoutMap,
    pageMap,
  };

  const result = await generateAccessible(accessMode, baseOptions);
  if (accessMode === 'backend' && result.accessibleRoutes.length === 0) {
    console.warn(
      '[access] Backend menus are empty, fallback to frontend routes to avoid 404 after login.',
    );
    return await generateAccessible('frontend', baseOptions);
  }

  return result;
}

export { generateAccess };
