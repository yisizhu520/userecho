/**
 * 业务菜单配置模块
 *
 * 业务菜单 (/app/*) 由前端定义，根据租户权限码动态渲染
 * 系统菜单 (/admin/*) 由后端返回
 */

import type { RouteRecordStringComponent } from '@vben/types';

import { useUserStore } from '@vben/stores';

import { $t } from '#/locales';
import { useTopicStore } from '#/store';

// 导入完整的业务路由定义
import userechoRoutes from './routes/modules/userecho';

/**
 * 业务菜单定义
 * permissionCode 为空表示所有人可见
 */
interface BusinessMenuItem {
    path: string;
    name: string;
    title: string;
    icon?: string;
    permissionCode?: string;
    order?: number;
    redirect?: string;
    children?: BusinessMenuItem[];
    /** 动态 badge */
    badgeGetter?: () => string | undefined;
    badgeType?: string;
    badgeVariants?: string;
}

const BUSINESS_MENUS: BusinessMenuItem[] = [
    {
        path: '/app/dashboard/workspace',
        name: 'UserEchoWorkspace',
        title: '工作台',
        icon: 'lucide:layout-dashboard',
        order: -1,
        // 工作台对所有人可见，不需要权限
    },
    {
        path: '/app/feedback',
        name: 'FeedbackManagement',
        title: $t('page.userecho.feedback.list'),
        icon: 'lucide:inbox',
        permissionCode: 'feedback',
        order: 0,
        redirect: '/app/feedback/list',
    },
    {
        path: '/app/ai/discovery',
        name: 'AIDiscovery',
        title: $t('page.userecho.discovery.title'),
        icon: 'lucide:sparkles',
        permissionCode: 'discovery',
        order: 2,
        badgeGetter: () => {
            const topicStore = useTopicStore();
            const count = topicStore.pendingCount;
            return count > 0 ? String(count) : undefined;
        },
        badgeType: 'normal',
        badgeVariants: 'destructive',
    },
    {
        path: '/app/topic/list',
        name: 'TopicList',
        title: $t('page.userecho.topic.list'),
        icon: 'lucide:lightbulb',
        permissionCode: 'topic',
        order: 4,
    },
    {
        path: '/app/customer',
        name: 'CustomerManage',
        title: $t('page.userecho.customer.title'),
        icon: 'lucide:users',
        permissionCode: 'customer',
        order: 4,
    },
    {
        path: '/app/insights/report',
        name: 'InsightReport',
        title: '洞察报告',
        icon: 'lucide:file-bar-chart',
        permissionCode: 'insight',
        order: 4.5,
    },
    {
        path: '/app/settings',
        name: 'Settings',
        title: '系统设置',
        icon: 'lucide:settings',
        permissionCode: 'settings',
        order: 99,
        redirect: '/app/settings/members',
        children: [
            {
                path: '/app/settings/members',
                name: 'MembersManage',
                title: '成员管理',
                icon: 'lucide:users',
                permissionCode: 'member',
            },
            {
                path: '/app/settings/roles',
                name: 'RolesManage',
                title: '角色管理',
                icon: 'lucide:shield',
                permissionCode: 'role',
            },
            {
                path: '/app/settings/credits',
                name: 'CreditsConfig',
                title: '积分配置',
                icon: 'lucide:coins',
                permissionCode: 'credits',
            },
        ],
    },
];



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
    return filterRoutesByPermission(userechoRoutes, tenantPermissions);
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

    const route = findRoute(userechoRoutes, path);

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
