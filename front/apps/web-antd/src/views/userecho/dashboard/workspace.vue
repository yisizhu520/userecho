<script lang="ts" setup>
import type { AnalysisOverviewItem } from '@vben/common-ui';

import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  AnalysisChartCard,
  AnalysisOverview,
  WorkbenchHeader,
  WorkbenchQuickNav,
} from '@vben/common-ui';
import type { WorkbenchQuickNavItem } from '@vben/common-ui';
import { SvgBellIcon, SvgCakeIcon, SvgCardIcon, SvgDownloadIcon } from '@vben/icons';
import { preferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';

import { getDashboardStats, type DashboardStats } from '#/api/userecho/dashboard';

import TagDistributionChart from './components/TagDistributionChart.vue';
import TopTopicsCard from './components/TopTopicsCard.vue';
import TrendChart from './components/TrendChart.vue';
import UrgentTopicsCard from './components/UrgentTopicsCard.vue';

const router = useRouter();
const userStore = useUserStore();

// 统计数据
const stats = ref<DashboardStats | null>(null);
const loading = ref(true);

// 顶部指标卡片
const overviewItems = computed<AnalysisOverviewItem[]>(() => {
  if (!stats.value) return [];

  return [
    {
      icon: SvgCardIcon,
      title: '总反馈',
      totalTitle: '待处理',
      totalValue: stats.value.feedback_stats.pending,
      value: stats.value.feedback_stats.total,
    },
    {
      icon: SvgCakeIcon,
      title: '本周新增',
      totalTitle: '反馈数',
      totalValue: stats.value.feedback_stats.weekly_count,
      value: stats.value.topic_stats.weekly_count,
    },
    {
      icon: SvgDownloadIcon,
      title: '总需求',
      totalTitle: '待处理',
      totalValue: stats.value.topic_stats.pending,
      value: stats.value.topic_stats.total,
    },
    {
      icon: SvgBellIcon,
      title: '已完成',
      totalTitle: '需求数',
      totalValue: stats.value.topic_stats.completed,
      value: stats.value.topic_stats.total,
    },
  ];
});

// 快捷操作
const quickActions: WorkbenchQuickNavItem[] = [
  {
    color: '#1fdaca',
    icon: 'lucide:upload',
    title: '导入反馈',
    url: '/app/feedback/import',
  },
  {
    color: '#bf0c2c',
    icon: 'lucide:plus',
    title: '录入反馈',
    url: '/app/feedback/list',
  },
  {
    color: '#e18525',
    icon: 'lucide:lightbulb',
    title: '查看需求',
    url: '/app/topic/list',
  },
  {
    color: '#3fb27f',
    icon: 'lucide:users',
    title: '客户管理',
    url: '/app/customer',
  },
];

// 加载统计数据
async function loadStats() {
  try {
    loading.value = true;
    const response = await getDashboardStats();
    stats.value = response;
  } catch (error) {
    console.error('Failed to load dashboard stats:', error);
  } finally {
    loading.value = false;
  }
}

// 导航处理
function navTo(item: WorkbenchQuickNavItem) {
  const url = item.url;
  if (!url) return;
  
  if (url.startsWith('http')) {
    window.open(url, '_blank');
  } else {
    router.push(url);
  }
}

onMounted(() => {
  loadStats();
});
</script>

<template>
  <div class="p-5">
    <!-- 欢迎头部 -->
    <WorkbenchHeader
      :avatar="userStore.userInfo?.avatar || preferences.app.defaultAvatar"
    >
      <template #title>
        早安, {{ userStore.userInfo?.realName }}, 开始您一天的工作吧！
      </template>
      <template #description>
        <span v-if="stats">
          今日待处理 {{ stats.topic_stats.pending }} 个需求，
          {{ stats.feedback_stats.pending }} 条反馈待聚类
        </span>
      </template>
    </WorkbenchHeader>

    <!-- 核心指标卡片 -->
    <AnalysisOverview v-if="!loading" :items="overviewItems" class="mt-5" />
    <div v-else class="mt-5 text-center">加载中...</div>

    <!-- 主内容区 -->
    <div v-if="!loading && stats" class="mt-5 flex flex-col lg:flex-row">
      <!-- 左侧：紧急需求 + 趋势图 -->
      <div class="mr-0 w-full lg:mr-4 lg:w-3/5">
        <UrgentTopicsCard :topics="stats.urgent_topics" />
        <AnalysisChartCard class="mt-5" title="7天反馈趋势">
          <TrendChart :data="stats.weekly_trend" />
        </AnalysisChartCard>
        
        <!-- 标签分布统计 -->
        <AnalysisChartCard class="mt-5" title="需求标签分布">
          <TagDistributionChart :data="stats.tag_distribution" />
        </AnalysisChartCard>
      </div>

      <!-- 右侧：快捷操作 + TOP 需求 -->
      <div class="w-full lg:w-2/5">
        <WorkbenchQuickNav
          :items="quickActions"
          class="mt-5 lg:mt-0"
          title="快捷操作"
          @click="navTo"
        />
        <TopTopicsCard :topics="stats.top_topics" class="mt-5" />
      </div>
    </div>
  </div>
</template>
