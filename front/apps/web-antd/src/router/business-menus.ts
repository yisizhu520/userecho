/**
 * 业务菜单配置模块
 *
 * 业务菜单 (/app/*) 由前端定义，根据租户权限码动态渲染
 * 系统菜单 (/admin/*) 由后端返回
 */

import type { RouteRecordStringComponent } from '@vben/types';

import { useUserStore } from '@vben/stores';


// 导入完整的业务路由定义
import userechoRoutes from './routes/modules/userecho';





/**
 * 过滤路由（根据租户权限）
 */
function filterRoutesByPermission(
    routes: RouteRecordStringComponent[],
    tenantPermissions: string[],
): RouteRecordStringComponent[] {
    return routes
        .filter((route) => {
            const permCode = route.meta?.permissionCode as string | undefined;
            // 没有权限码 = 公开路由（如工作台）
            if (!permCode) return true;
            return tenantPermissions.includes(permCode);
        })
        .map((route) => {
            // 递归过滤子路由
            if (route.children && route.children.length > 0) {
                return {
                    ...route,
                    children: filterRoutesByPermission(
                        route.children as RouteRecordStringComponent[],
                        tenantPermissions,
                    ),
                };
            }
            return route;
        })
        .filter((route) => {
            // 过滤掉没有子路由的父路由（如果父路由本身需要 redirect）
            if (
                route.children &&
                route.children.length === 0 &&
                route.redirect &&
                route.meta?.permissionCode
            ) {
                return false;
            }
            return true;
        });
}

/**
 * 获取业务菜单列表（根据当前用户权限过滤）
 * 
 * 从 userecho.ts 导入路由定义，根据租户权限过滤
 */
export function getBusinessMenus(): RouteRecordStringComponent[] {
    const userStore = useUserStore();
    const userInfo = userStore.userInfo;

    // 获取用户的租户权限码
    const tenantPermissions: string[] =
        (userInfo as Record<string, unknown>)?.tenantPermissions as string[] || [];

    // 根据权限过滤路由，直接返回（component 已是字符串，无需转换）
    return filterRoutesByPermission(userechoRoutes as any as RouteRecordStringComponent[], tenantPermissions);
}

/**
 * 检查用户是否有访问指定路径的权限
 */
export function hasBusinessMenuAccess(path: string): boolean {
    const userStore = useUserStore();
    const userInfo = userStore.userInfo;
    const tenantPermissions: string[] =
        (userInfo as Record<string, unknown>)?.tenantPermissions as string[] || [];

    // 递归查找路由
    const findRoute = (
        routes: RouteRecordStringComponent[],
        targetPath: string,
    ): RouteRecordStringComponent | undefined => {
        for (const route of routes) {
            if (route.path === targetPath) {
                return route;
            }
            if (route.children) {
                const found = findRoute(
                    route.children as RouteRecordStringComponent[],
                    targetPath,
                );
                if (found) return found;
            }
        }
        return undefined;
    };

    const route = findRoute(userechoRoutes as any as RouteRecordStringComponent[], path);

    // 没找到路由配置，默认允许访问
    if (!route) {
        return true;
    }

    const permCode = route.meta?.permissionCode as string | undefined;
    // 没有权限码 = 公开路由
    if (!permCode) {
        return true;
    }

    return tenantPermissions.includes(permCode);
}
