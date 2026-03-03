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

import BatchJobsCard from './components/BatchJobsCard.vue';
import ConversionFunnelCard from './components/ConversionFunnelCard.vue';
import CustomerStatsCard from './components/CustomerStatsCard.vue';
import MyFeedbacksCard from './components/MyFeedbacksCard.vue';
import PendingDecisionsCard from './components/PendingDecisionsCard.vue';
import TagDistributionChart from './components/TagDistributionChart.vue';
import TopTopicsCard from './components/TopTopicsCard.vue';
import TrendChart from './components/TrendChart.vue';

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
      title: '总客户',
      totalTitle: '本周活跃',
      totalValue: stats.value.customer_stats.active_7d,
      value: stats.value.customer_stats.total,
    },
  ];
});

// 顶部面板统计数据
const headerStats = computed(() => ({
  pendingTopics: stats.value?.topic_stats?.pending ?? 0,
  totalTopics: stats.value?.topic_stats?.total ?? 0,
  weeklyFeedbacks: stats.value?.feedback_stats?.weekly_count ?? 0,
  totalFeedbacks: stats.value?.feedback_stats?.total ?? 0,
}));

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
    color: '#8b5cf6',
    icon: 'lucide:scan',
    title: '截图识别',
    url: '/app/feedback/screenshot',
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
  {
    color: '#0ea5e9',
    icon: 'lucide:file-bar-chart',
    title: '洞察报告',
    url: '/app/insights/report',
  },
];

// 将所有 API 返回的数据规范化为 primitive 类型
// 这可以防止因后端返回了非标准对象而导致 Vue 渲染时的 TypeError
function normalizeStats(data: any): DashboardStats | null {
  if (!data) return null;

  try {
    return {
      feedback_stats: {
        total: Number(data.feedback_stats?.total ?? 0),
        pending: Number(data.feedback_stats?.pending ?? 0),
        weekly_count: Number(data.feedback_stats?.weekly_count ?? 0),
      },
      topic_stats: {
        total: Number(data.topic_stats?.total ?? 0),
        pending: Number(data.topic_stats?.pending ?? 0),
        completed: Number(data.topic_stats?.completed ?? 0),
        weekly_count: Number(data.topic_stats?.weekly_count ?? 0),
      },
      customer_stats: {
        total: Number(data.customer_stats?.total ?? 0),
        new_count: Number(data.customer_stats?.new_count ?? 0),
        active_7d: Number(data.customer_stats?.active_7d ?? 0),
        type_distribution: Array.isArray(data.customer_stats?.type_distribution)
          ? data.customer_stats.type_distribution.map((item: any) => ({
              type: String(item.type ?? ''),
              name: String(item.name ?? ''),
              count: Number(item.count ?? 0),
            }))
          : [],
        total_mrr: Number(data.customer_stats?.total_mrr ?? 0),
        top_customers: Array.isArray(data.customer_stats?.top_customers)
          ? data.customer_stats.top_customers.map((item: any) => ({
              id: String(item.id ?? ''),
              name: String(item.name ?? ''),
              customer_type: String(item.customer_type ?? ''),
              mrr: Number(item.mrr ?? 0),
              feedback_count: Number(item.feedback_count ?? 0),
            }))
          : [],
      },
      urgent_topics: Array.isArray(data.urgent_topics)
        ? data.urgent_topics.map((item: any) => ({
            id: String(item.id ?? ''),
            title: String(item.title ?? ''),
            feedback_count: Number(item.feedback_count ?? 0),
            priority_score: item.priority_score != null ? Number(item.priority_score) : null,
            category: String(item.category ?? ''),
            status: String(item.status ?? ''),
          }))
        : [],
      pending_decisions: Array.isArray(data.pending_decisions)
        ? data.pending_decisions.map((item: any) => ({
            id: String(item.id ?? ''),
            title: String(item.title ?? ''),
            category: String(item.category ?? ''),
            feedback_count: Number(item.feedback_count ?? 0),
            affected_customer_count: Number(item.affected_customer_count ?? 0),
            priority_score: Number(item.priority_score ?? 0),
            urgent_ratio: Number(item.urgent_ratio ?? 0),
            strategic_keywords_matched: Array.isArray(item.strategic_keywords_matched)
              ? item.strategic_keywords_matched.map((s: any) => String(s))
              : [],
            last_feedback_days: item.last_feedback_days != null ? Number(item.last_feedback_days) : null,
            total_mrr: Number(item.total_mrr ?? 0),
          }))
        : [],
      top_topics: Array.isArray(data.top_topics)
        ? data.top_topics.map((item: any) => ({
            id: String(item.id ?? ''),
            title: String(item.title ?? ''),
            feedback_count: Number(item.feedback_count ?? 0),
            category: String(item.category ?? ''),
            status: String(item.status ?? ''),
          }))
        : [],
      weekly_trend: Array.isArray(data.weekly_trend)
        ? data.weekly_trend.map((item: any) => ({
            date: String(item.date ?? ''),
            count: Number(item.count ?? 0),
          }))
        : [],
      tag_distribution: Array.isArray(data.tag_distribution)
        ? data.tag_distribution.map((item: any) => ({
            category: String(item.category ?? ''),
            name: String(item.name ?? ''),
            topic_count: Number(item.topic_count ?? 0),
            feedback_count: Number(item.feedback_count ?? 0),
            avg_priority_score: item.avg_priority_score != null ? Number(item.avg_priority_score) : null,
          }))
        : [],
      conversion_funnel: {
        total_feedbacks: Number(data.conversion_funnel?.total_feedbacks ?? 0),
        clustered: Number(data.conversion_funnel?.clustered ?? 0),
        pending_review: Number(data.conversion_funnel?.pending_review ?? 0),
        planned: Number(data.conversion_funnel?.planned ?? 0),
        in_progress: Number(data.conversion_funnel?.in_progress ?? 0),
        completed: Number(data.conversion_funnel?.completed ?? 0),
        conversion_rates: {
          clustering_rate: Number(data.conversion_funnel?.conversion_rates?.clustering_rate ?? 0),
          review_rate: Number(data.conversion_funnel?.conversion_rates?.review_rate ?? 0),
          planning_rate: Number(data.conversion_funnel?.conversion_rates?.planning_rate ?? 0),
          completion_rate: Number(data.conversion_funnel?.conversion_rates?.completion_rate ?? 0),
        },
      },
    };
  } catch (e) {
    console.error('normalizeStats failed:', e, 'original data:', data);
    return null;
  }
}

// 加载统计数据
async function loadStats() {
  try {
    loading.value = true;
    const response = await getDashboardStats();
    stats.value = normalizeStats(response);
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

// 刷新数据
function handleRefresh() {
  loadStats();
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
      :stats="headerStats"
    >
      <template #title>
        早安, {{ userStore.userInfo?.realName || userStore.userInfo?.nickname || userStore.userInfo?.username }}, 开始您一天的工作吧！
      </template>
      <template #description>
        <span v-if="stats && stats.topic_stats && stats.feedback_stats">
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
      <!-- 左侧：待决策 + 趋势图 -->
      <div class="mr-0 w-full lg:mr-4 lg:w-3/5">
        <!-- 今日待决策（新增核心组件） -->
        <PendingDecisionsCard
          :decisions="stats.pending_decisions || []"
          @refresh="handleRefresh"
        />

        <AnalysisChartCard class="mt-5" title="7天反馈趋势">
          <TrendChart :data="stats.weekly_trend" />
        </AnalysisChartCard>

        <!-- 标签分布统计 -->
        <AnalysisChartCard class="mt-5" title="需求标签分布">
          <TagDistributionChart :data="stats.tag_distribution" />
        </AnalysisChartCard>

        <!-- 需求转化漏斗 -->
        <ConversionFunnelCard :data="stats.conversion_funnel" class="mt-5" />
      </div>

      <!-- 右侧：快捷操作 + 批处理任务 + 我的反馈 + TOP 需求 -->
      <div class="w-full lg:w-2/5">
        <WorkbenchQuickNav
          :items="quickActions"
          class="mt-5 lg:mt-0"
          title="快捷操作"
          @click="navTo"
        />

        <!-- 批处理任务卡片 -->
        <BatchJobsCard class="mt-5" />

        <!-- 我的反馈卡片 -->
        <MyFeedbacksCard class="mt-5" />

        <!-- 客户统计卡片 -->
        <CustomerStatsCard
          :total="stats.customer_stats?.total ?? 0"
          :new-count="stats.customer_stats?.new_count ?? 0"
          :active7d="stats.customer_stats?.active_7d ?? 0"
          :type-distribution="stats.customer_stats?.type_distribution ?? []"
          :total-mrr="stats.customer_stats?.total_mrr ?? 0"
          :top-customers="stats.customer_stats?.top_customers ?? []"
          class="mt-5"
        />

        <TopTopicsCard :topics="stats.top_topics" class="mt-5" />
      </div>
    </div>

    <!-- AI 洞察区域 -->
    <!-- <InsightsCard v-if="!loading" /> -->
  </div>
</template>
