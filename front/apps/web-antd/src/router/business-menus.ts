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
 * 转换业务菜单项为路由格式
 */
function convertToRouteFormat(
    item: BusinessMenuItem,
): RouteRecordStringComponent {
    const route: RouteRecordStringComponent = {
        path: item.path,
        name: item.name,
        meta: {
            title: item.title,
            icon: item.icon,
            order: item.order,
        },
    };

    if (item.redirect) {
        route.redirect = item.redirect;
    }

    // 动态 badge
    if (item.badgeGetter) {
        Object.defineProperty(route.meta!, 'badge', {
            get: item.badgeGetter,
        });
        if (item.badgeType) route.meta!.badgeType = item.badgeType;
        if (item.badgeVariants) route.meta!.badgeVariants = item.badgeVariants;
    }

    // 子菜单
    if (item.children && item.children.length > 0) {
        route.children = item.children.map(convertToRouteFormat);
    }

    return route;
}

/**
 * 检查用户是否有权限访问菜单
 */
function hasPermission(
    item: BusinessMenuItem,
    tenantPermissions: string[],
): boolean {
    // 没有配置权限码，表示所有人可见
    if (!item.permissionCode) {
        return true;
    }
    return tenantPermissions.includes(item.permissionCode);
}

/**
 * 过滤业务菜单（根据租户权限）
 */
function filterMenusByPermission(
    menus: BusinessMenuItem[],
    tenantPermissions: string[],
): BusinessMenuItem[] {
    return menus
        .filter((item) => hasPermission(item, tenantPermissions))
        .map((item) => {
            if (item.children) {
                return {
                    ...item,
                    children: filterMenusByPermission(item.children, tenantPermissions),
                };
            }
            return item;
        })
        .filter((item) => {
            // 过滤掉没有子菜单的父菜单（除非父菜单本身可访问）
            if (item.children && item.children.length === 0 && item.redirect) {
                return false;
            }
            return true;
        });
}

/**
 * 获取业务菜单列表（根据当前用户权限过滤）
 */
export function getBusinessMenus(): RouteRecordStringComponent[] {
    const userStore = useUserStore();
    const userInfo = userStore.userInfo;

    // 获取用户的租户权限码
    const tenantPermissions: string[] =
        (userInfo as Record<string, unknown>)?.tenantPermissions as string[] || [];

    // 如果没有任何权限，返回工作台等默认菜单
    if (tenantPermissions.length === 0) {
        // 只返回不需要权限的菜单
        const publicMenus = BUSINESS_MENUS.filter((m) => !m.permissionCode);
        return publicMenus.map(convertToRouteFormat);
    }

    // 根据权限过滤菜单
    const filteredMenus = filterMenusByPermission(BUSINESS_MENUS, tenantPermissions);
    return filteredMenus.map(convertToRouteFormat);
}

/**
 * 检查用户是否有访问指定路径的权限
 */
export function hasBusinessMenuAccess(path: string): boolean {
    const userStore = useUserStore();
    const userInfo = userStore.userInfo;
    const tenantPermissions: string[] =
        (userInfo as Record<string, unknown>)?.tenantPermissions as string[] || [];

    // 查找对应的菜单配置
    const findMenu = (
        menus: BusinessMenuItem[],
        targetPath: string,
    ): BusinessMenuItem | undefined => {
        for (const menu of menus) {
            if (menu.path === targetPath) {
                return menu;
            }
            if (menu.children) {
                const found = findMenu(menu.children, targetPath);
                if (found) return found;
            }
        }
        return undefined;
    };

    const menu = findMenu(BUSINESS_MENUS, path);

    // 没找到菜单配置，默认允许访问
    if (!menu) {
        return true;
    }

    return hasPermission(menu, tenantPermissions);
}
