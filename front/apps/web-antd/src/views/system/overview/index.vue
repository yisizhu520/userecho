<script setup lang="ts">
import type { AnalysisOverviewItem, WorkbenchQuickNavItem } from '@vben/common-ui';

import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { AnalysisOverview, WorkbenchQuickNav } from '@vben/common-ui';
import { SvgBellIcon, SvgCakeIcon, SvgCardIcon, SvgDownloadIcon } from '@vben/icons';

import {
  getSysDeptTreeApi,
  getSysMenuTreeApi,
  getSysRoleListApi,
  getSysUserListApi,
} from '#/api';

interface SystemOverviewStats {
  userTotal: number;
  roleTotal: number;
  deptTotal: number;
  menuTotal: number;
}

interface TreeNode {
  children?: TreeNode[];
}

const router = useRouter();
const loading = ref(true);
const stats = ref<SystemOverviewStats>({
  userTotal: 0,
  roleTotal: 0,
  deptTotal: 0,
  menuTotal: 0,
});

function countTreeNodes(nodes: TreeNode[] | undefined): number {
  if (!Array.isArray(nodes) || nodes.length === 0) {
    return 0;
  }

  return nodes.reduce((count, node) => {
    return count + 1 + countTreeNodes(node.children);
  }, 0);
}

function extractTotal(data: unknown): number {
  if (Array.isArray(data)) {
    return data.length;
  }
  if (data && typeof data === 'object' && 'total' in data) {
    return Number((data as { total?: number }).total ?? 0);
  }
  return 0;
}

async function loadOverviewStats() {
  loading.value = true;
  try {
    const [usersPage, rolesPage, deptTree, menuTree] = await Promise.all([
      getSysUserListApi({ page: 1, size: 1 }),
      getSysRoleListApi({ page: 1, size: 1 }),
      getSysDeptTreeApi({}),
      getSysMenuTreeApi({ status: 1 }),
    ]);

    stats.value = {
      userTotal: extractTotal(usersPage),
      roleTotal: extractTotal(rolesPage),
      deptTotal: countTreeNodes(deptTree),
      menuTotal: countTreeNodes(menuTree),
    };
  } catch (error) {
    console.error('Failed to load system overview stats:', error);
  } finally {
    loading.value = false;
  }
}

const overviewItems = computed<AnalysisOverviewItem[]>(() => [
  {
    icon: SvgCardIcon,
    title: '系统用户',
    totalTitle: '总计',
    totalValue: stats.value.userTotal,
    value: stats.value.userTotal,
  },
  {
    icon: SvgCakeIcon,
    title: '系统角色',
    totalTitle: '总计',
    totalValue: stats.value.roleTotal,
    value: stats.value.roleTotal,
  },
  {
    icon: SvgDownloadIcon,
    title: '部门节点',
    totalTitle: '总计',
    totalValue: stats.value.deptTotal,
    value: stats.value.deptTotal,
  },
  {
    icon: SvgBellIcon,
    title: '菜单节点',
    totalTitle: '总计',
    totalValue: stats.value.menuTotal,
    value: stats.value.menuTotal,
  },
]);

const quickActions: WorkbenchQuickNavItem[] = [
  { color: '#1677ff', icon: 'ant-design:user-outlined', title: '用户管理', url: '/admin/system/user' },
  { color: '#13c2c2', icon: 'carbon:user-role', title: '角色管理', url: '/admin/system/role' },
  { color: '#722ed1', icon: 'material-symbols:menu', title: '菜单管理', url: '/admin/system/menu' },
  { color: '#52c41a', icon: 'mingcute:department-line', title: '部门管理', url: '/admin/system/dept' },
  { color: '#fa8c16', icon: 'icon-park-outline:permissions', title: '数据权限', url: '/admin/system/data-scope' },
  { color: '#eb2f96', icon: 'mdi:invitation', title: '邀请管理', url: '/admin/system/invitation' },
];

function navTo(item: WorkbenchQuickNavItem) {
  if (!item.url) {
    return;
  }
  router.push(item.url).catch((error) => {
    console.error('Failed to navigate from system overview:', error);
  });
}

onMounted(() => {
  loadOverviewStats();
});
</script>

<template>
  <div class="p-5">
    <div class="mb-5 rounded-xl border border-border bg-card p-5 shadow-sm">
      <h2 class="text-xl font-semibold">系统管理概览</h2>
      <p class="mt-2 text-sm text-muted-foreground">
        聚合系统用户、角色、部门与菜单信息，作为系统管理员登录后的统一工作入口。
      </p>
    </div>

    <AnalysisOverview
      :items="overviewItems.map((item) => ({ ...item, value: loading ? 0 : item.value, totalValue: loading ? 0 : item.totalValue }))"
    />

    <div class="mt-5">
      <WorkbenchQuickNav :items="quickActions" title="快捷入口" @click="navTo" />
    </div>
  </div>
</template>
