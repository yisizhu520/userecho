import type { Component, DefineComponent } from 'vue';

import type {
  AccessModeType,
  GenerateMenuAndRoutesOptions,
  RouteRecordRaw,
} from '@vben/types';

import { defineComponent, h } from 'vue';

import {
  cloneDeep,
  generateMenus,
  generateRoutesByBackend,
  generateRoutesByFrontend,
  isHttpUrl,
  isFunction,
  isString,
  mapTree,
} from '@vben/utils';

async function generateAccessible(
  mode: AccessModeType,
  options: GenerateMenuAndRoutesOptions,
) {
  const { router } = options;

  options.routes = cloneDeep(options.routes);
  // 生成路由
  const accessibleRoutes = await generateRoutes(mode, options);

  const root = router.getRoutes().find((item) => item.path === '/app') ||
    router.getRoutes().find((item) => item.path === '/');

  // 获取已有的路由名称列表
  const names = root?.children?.map((item) => item.name) ?? [];

  // 动态添加到router实例内
  accessibleRoutes.forEach((route) => {
    if (root && !route.meta?.noBasicLayout) {
      // 为了兼容之前的版本用法，如果包含子路由，则将component移除，以免出现多层BasicLayout
      // 如果你的项目已经跟进了本次修改，移除了所有自定义菜单首级的BasicLayout，可以将这段if代码删除
      if (route.children && route.children.length > 0) {
        delete route.component;
      }

      // 当父路由不是 '/' 时，需要将所有绝对路径转换为相对路径
      // Vue Router 要求子路由使用相对路径才能正确拼接父路由
      // 示例：父路由 /app + 子路由 /app/dashboard -> 子路由应为 dashboard
      //       父路由 /app + 子路由 /admin/xxx -> 子路由应为 admin/xxx
      const rootPath = root.path;
      if (rootPath !== '/' && route.path.startsWith('/')) {
        if (route.path.startsWith(`${rootPath}/`)) {
          // 去掉父路由前缀（包括斜杠）
          route.path = route.path.slice(rootPath.length + 1);
        } else {
          // 其他绝对路径只去掉开头的 /
          route.path = route.path.slice(1);
        }
      }

      // 根据router name判断，如果路由已经存在，则不再添加
      if (names?.includes(route.name)) {
        // 找到已存在的路由索引并更新，不更新会造成切换用户时，一级目录未更新，homePath 在二级目录导致的404问题
        const index = root.children?.findIndex(
          (item) => item.name === route.name,
        );
        if (index !== undefined && index !== -1 && root.children) {
          root.children[index] = route;
        }
      } else {
        root.children?.push(route);
      }
    } else {
      router.addRoute(route);
    }
  });

  if (root) {
    if (root.name) {
      router.removeRoute(root.name);
    }
    router.addRoute(root);
  }

  // 生成菜单
  const accessibleMenus = generateMenus(accessibleRoutes, options.router);

  return { accessibleMenus, accessibleRoutes };
}

/**
 * Generate routes
 * @param mode
 * @param options
 */
async function generateRoutes(
  mode: AccessModeType,
  options: GenerateMenuAndRoutesOptions,
) {
  const { forbiddenComponent, roles, routes } = options;

  let resultRoutes: RouteRecordRaw[] = routes;
  switch (mode) {
    case 'backend': {
      resultRoutes = await generateRoutesByBackend(options);
      break;
    }
    case 'frontend': {
      resultRoutes = await generateRoutesByFrontend(
        routes,
        roles || [],
        forbiddenComponent,
      );
      break;
    }
    case 'mixed': {
      const [frontend_resultRoutes, backend_resultRoutes] = await Promise.all([
        generateRoutesByFrontend(routes, roles || [], forbiddenComponent),
        generateRoutesByBackend(options),
      ]);

      resultRoutes = [...frontend_resultRoutes, ...backend_resultRoutes];
      break;
    }
  }

  /**
   * 调整路由树，做以下处理：
   * 1. 将懒加载的组件名称修改为当前路由的名称（如果启用了keep-alive的话）
   * 2. 对未添加redirect的路由添加redirect（兼容子路由相对路径）
   */
  resultRoutes = mapTree(resultRoutes, (route) => {
    // 重新包装component，使用与路由名称相同的name以支持keep-alive的条件缓存。
    if (
      route.meta?.keepAlive &&
      isFunction(route.component) &&
      route.name &&
      isString(route.name)
    ) {
      const originalComponent = route.component as () => Promise<{
        default: Component | DefineComponent;
      }>;
      route.component = async () => {
        const component = await originalComponent();
        if (!component.default) return component;
        return defineComponent({
          name: route.name as string,
          setup(props, { attrs, slots }) {
            return () => h(component.default, { ...props, ...attrs }, slots);
          },
        });
      };
    }
    return route;
  });

  applyDefaultRedirect(resultRoutes);
  return resultRoutes;
}

function resolveFullPath(
  parentFullPath: string,
  routePath: string | undefined,
): string {
  if (!routePath) {
    return parentFullPath || '/';
  }

  if (isHttpUrl(routePath)) {
    return routePath;
  }

  if (routePath.startsWith('/')) {
    return routePath;
  }

  const normalizedParent =
    parentFullPath === '/'
      ? ''
      : (parentFullPath || '').replace(/\/+$/, '');
  const normalizedChild = routePath.replace(/^\/+/, '');

  if (!normalizedChild) {
    return normalizedParent || '/';
  }

  return `${normalizedParent}/${normalizedChild}` || '/';
}

function applyDefaultRedirect(routes: RouteRecordRaw[], parentFullPath = '') {
  for (const route of routes) {
    const currentFullPath = resolveFullPath(parentFullPath, route.path);
    const children = route.children;

    if (!children || children.length === 0) {
      continue;
    }

    applyDefaultRedirect(children, currentFullPath);

    if (route.redirect) {
      continue;
    }

    const firstChild = children[0];
    if (firstChild?.path && isHttpUrl(firstChild.path)) {
      continue;
    }

    route.redirect = resolveFullPath(currentFullPath, firstChild?.path);
  }
}

export { generateAccessible };
