<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Drawer,
  Empty,
  message,
  Progress,
  Row,
  Select,
  SelectOption,
  Statistic,
  Table,
  Tag,
  Tooltip,
} from 'ant-design-vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

import type {
  TaskCategoryOption,
  TaskRecord,
  TaskStatsResult,
} from '#/api/userecho/task-record';

import {
  getTaskCategoriesApi,
  getTaskRecordDetailApi,
  getTaskRecordListApi,
  getTaskStatsApi,
} from '#/api/userecho/task-record';

// ============================================================
// 状态定义
// ============================================================
const loading = ref(false);
const records = ref<TaskRecord[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterCategory = ref<string | undefined>(undefined);
const filterStatus = ref<string | undefined>(undefined);
const categories = ref<TaskCategoryOption[]>([]);
const stats = ref<TaskStatsResult | null>(null);
const statsLoading = ref(false);

// 详情抽屉
const detailVisible = ref(false);
const detailRecord = ref<TaskRecord | null>(null);
const detailLoading = ref(false);

// ECharts 图表 refs
const statusChartRef = ref<HTMLDivElement>();
const categoryChartRef = ref<HTMLDivElement>();
const durationChartRef = ref<HTMLDivElement>();

let statusChart: echarts.ECharts | null = null;
let categoryChart: echarts.ECharts | null = null;
let durationChart: echarts.ECharts | null = null;

// ============================================================
// 分类中文映射
// ============================================================
const categoryLabelMap: Record<string, string> = {
  ai_embedding: 'AI 向量化',
  ai_clustering: 'AI 聚类',
  ai_screenshot: '截图识别',
  ai_insight: '洞察报告',
  ai_summary: 'AI 摘要',
  batch: '批量任务',
  maintenance: '系统维护',
};

const statusLabelMap: Record<string, { label: string; color: string }> = {
  pending: { label: '等待中', color: 'default' },
  started: { label: '执行中', color: 'processing' },
  success: { label: '成功', color: 'success' },
  failure: { label: '失败', color: 'error' },
  retry: { label: '重试中', color: 'warning' },
};

function getCategoryLabel(cat: string) {
  return categoryLabelMap[cat] || cat;
}

function getStatusInfo(status: string) {
  return statusLabelMap[status] || { label: status, color: 'default' };
}

// ============================================================
// 数据加载
// ============================================================
async function loadRecords() {
  loading.value = true;
  try {
    const res = await getTaskRecordListApi({
      category: filterCategory.value,
      status: filterStatus.value,
      page: page.value,
      page_size: pageSize.value,
    });
    records.value = res.items;
    total.value = res.total;
  } catch {
    message.error('加载任务列表失败');
  } finally {
    loading.value = false;
  }
}

async function loadStats() {
  statsLoading.value = true;
  try {
    stats.value = await getTaskStatsApi();
  } catch {
    // 统计加载失败不影响主流程
  } finally {
    statsLoading.value = false;
  }
}

async function loadCategories() {
  try {
    categories.value = await getTaskCategoriesApi();
  } catch {
    // 分类加载失败不影响主流程
  }
}

async function handleRefresh() {
  await Promise.all([loadRecords(), loadStats()]);
  message.success('已刷新');
}

function handlePageChange(p: number, ps: number) {
  page.value = p;
  pageSize.value = ps;
  loadRecords();
}

function handleFilterChange() {
  page.value = 1;
  loadRecords();
}

async function showDetail(record: Record<string, any>) {
  detailVisible.value = true;
  detailLoading.value = true;
  try {
    const celeryId = record.celery_task_id as string;
    const detail = await getTaskRecordDetailApi(celeryId);
    detailRecord.value = detail as TaskRecord;
  } catch {
    detailRecord.value = record as unknown as TaskRecord;
  } finally {
    detailLoading.value = false;
  }
}

// ============================================================
// 统计面板计算
// ============================================================
const totalCount = computed(() => stats.value?.total || 0);
const successCount = computed(
  () => stats.value?.status_counts?.success || 0,
);
const failureCount = computed(
  () => stats.value?.status_counts?.failure || 0,
);
const runningCount = computed(
  () =>
    (stats.value?.status_counts?.started || 0) +
    (stats.value?.status_counts?.pending || 0),
);
const successRate = computed(() => {
  if (totalCount.value === 0) return 0;
  return Math.round((successCount.value / totalCount.value) * 100);
});

// ============================================================
// 表格列定义
// ============================================================
const columns = [
  {
    title: '任务名称',
    dataIndex: 'task_display_name',
    key: 'task_display_name',
    width: 160,
  },
  {
    title: '分类',
    dataIndex: 'task_category',
    key: 'task_category',
    width: 120,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
  },
  {
    title: '耗时',
    dataIndex: 'duration_ms',
    key: 'duration_ms',
    width: 100,
  },
  {
    title: '创建时间',
    dataIndex: 'created_time',
    key: 'created_time',
    width: 180,
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    fixed: 'right' as const,
  },
];

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60_000).toFixed(1)}min`;
}

function formatTime(iso: string | null): string {
  if (!iso) return '-';
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return iso;
  }
}

// ============================================================
// ECharts 图表初始化
// ============================================================
function initCharts() {
  // 状态分布饼图
  if (statusChartRef.value && !statusChart) {
    statusChart = echarts.init(statusChartRef.value);
  }

  // 分类统计柱状图
  if (categoryChartRef.value && !categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value);
  }

  // 耗时分布图
  if (durationChartRef.value && !durationChart) {
    durationChart = echarts.init(durationChartRef.value);
  }

  updateCharts();
}

function updateCharts() {
  if (!stats.value) return;

  // 状态分布饼图
  if (statusChart) {
    const statusData = [
      { value: stats.value.status_counts?.success || 0, name: '成功', itemStyle: { color: '#52c41a' } },
      { value: stats.value.status_counts?.failure || 0, name: '失败', itemStyle: { color: '#ff4d4f' } },
      { value: stats.value.status_counts?.started || 0, name: '执行中', itemStyle: { color: '#1890ff' } },
      { value: stats.value.status_counts?.pending || 0, name: '等待中', itemStyle: { color: '#d9d9d9' } },
      { value: stats.value.status_counts?.retry || 0, name: '重试中', itemStyle: { color: '#faad14' } },
    ].filter(item => item.value > 0);

    const option: EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
      },
      series: [
        {
          name: '任务状态',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          data: statusData,
        },
      ],
    };
    statusChart.setOption(option);
  }

  // 分类统计柱状图
  if (categoryChart && stats.value.categories?.length) {
    const categories = stats.value.categories.map(c => getCategoryLabel(c.category));
    const successData = stats.value.categories.map(c => c.success);
    const failureData = stats.value.categories.map(c => c.failure);

    const option: EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['成功', '失败'],
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: categories,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '成功',
          type: 'bar',
          stack: 'total',
          itemStyle: { color: '#52c41a' },
          data: successData,
        },
        {
          name: '失败',
          type: 'bar',
          stack: 'total',
          itemStyle: { color: '#ff4d4f' },
          data: failureData,
        },
      ],
    };
    categoryChart.setOption(option);
  }

  // 平均耗时柱状图
  if (durationChart && stats.value.categories?.length) {
    const categories = stats.value.categories.map(c => getCategoryLabel(c.category));
    const durations = stats.value.categories.map(c =>
      c.avg_duration_ms ? (c.avg_duration_ms / 1000).toFixed(2) : 0
    );

    const option: EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: '{b}: {c}s',
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: categories,
      },
      yAxis: {
        type: 'value',
        name: '平均耗时(s)',
      },
      series: [
        {
          name: '平均耗时',
          type: 'bar',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' },
            ]),
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#2378f7' },
                { offset: 0.7, color: '#2378f7' },
                { offset: 1, color: '#83bff6' },
              ]),
            },
          },
          data: durations,
        },
      ],
    };
    durationChart.setOption(option);
  }
}

// 监听 stats 变化自动更新图表
watch(() => stats.value, () => {
  if (stats.value) {
    updateCharts();
  }
});

// ============================================================
// 初始化
// ============================================================
onMounted(() => {
  loadRecords();
  loadStats();
  loadCategories();

  // 延迟初始化图表，确保 DOM 已渲染
  setTimeout(() => {
    initCharts();
  }, 100);
});
</script>

<template>
  <div class="task-center-page">
    <!-- 统计面板 - 单行显示 -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="4">
        <Card :loading="statsLoading" size="small" class="stat-card">
          <Statistic title="总任务数" :value="totalCount">
            <template #prefix>
              <ClockCircleOutlined style="color: #1890ff" />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="4">
        <Card :loading="statsLoading" size="small" class="stat-card">
          <Statistic
            title="成功"
            :value="successCount"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <CheckCircleOutlined />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="4">
        <Card :loading="statsLoading" size="small" class="stat-card">
          <Statistic
            title="失败"
            :value="failureCount"
            :value-style="{ color: '#ff4d4f' }"
          >
            <template #prefix>
              <CloseCircleOutlined />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="4">
        <Card :loading="statsLoading" size="small" class="stat-card">
          <Statistic
            title="执行中"
            :value="runningCount"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <LoadingOutlined />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="8">
        <Card :loading="statsLoading" size="small" class="stat-card">
          <Statistic title="成功率" :value="successRate" suffix="%">
            <template #prefix>
              <CheckCircleOutlined
                :style="{ color: successRate >= 90 ? '#52c41a' : '#faad14' }"
              />
            </template>
          </Statistic>
        </Card>
      </Col>
    </Row>

    <!-- 数据可视化 -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="8">
        <Card title="任务状态分布" size="small" :loading="statsLoading">
          <div ref="statusChartRef" style="height: 280px"></div>
        </Card>
      </Col>
      <Col :span="8">
        <Card title="分类执行统计" size="small" :loading="statsLoading">
          <div ref="categoryChartRef" style="height: 280px"></div>
        </Card>
      </Col>
      <Col :span="8">
        <Card title="平均耗时分析" size="small" :loading="statsLoading">
          <div ref="durationChartRef" style="height: 280px"></div>
        </Card>
      </Col>
    </Row>

    <!-- 任务列表 -->
    <Card size="small">
      <template #title>
        <div style="display: flex; align-items: center; gap: 12px">
          <span>任务记录</span>
          <Select
            v-model:value="filterCategory"
            allow-clear
            placeholder="所有分类"
            style="width: 150px"
            size="small"
            @change="handleFilterChange"
          >
            <SelectOption
              v-for="cat in categories"
              :key="cat.category"
              :value="cat.category"
            >
              {{ getCategoryLabel(cat.category) }} ({{ cat.count }})
            </SelectOption>
          </Select>
          <Select
            v-model:value="filterStatus"
            allow-clear
            placeholder="所有状态"
            style="width: 120px"
            size="small"
            @change="handleFilterChange"
          >
            <SelectOption value="pending">等待中</SelectOption>
            <SelectOption value="started">执行中</SelectOption>
            <SelectOption value="success">成功</SelectOption>
            <SelectOption value="failure">失败</SelectOption>
            <SelectOption value="retry">重试中</SelectOption>
          </Select>
        </div>
      </template>
      <template #extra>
        <Button size="small" @click="handleRefresh">
          <template #icon><ReloadOutlined /></template>
          刷新
        </Button>
      </template>

      <Table
        :columns="columns"
        :data-source="records"
        :loading="loading"
        :pagination="{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t: number) => `共 ${t} 条`,
          onChange: handlePageChange,
        }"
        row-key="id"
        size="small"
        :scroll="{ x: 800 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_category'">
            <Tag color="blue">{{ getCategoryLabel(record.task_category) }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Tag :color="getStatusInfo(record.status).color">
              <template #icon>
                <LoadingOutlined
                  v-if="record.status === 'started'"
                  spin
                />
                <SyncOutlined
                  v-else-if="record.status === 'retry'"
                  spin
                />
                <CheckCircleOutlined
                  v-else-if="record.status === 'success'"
                />
                <CloseCircleOutlined
                  v-else-if="record.status === 'failure'"
                />
                <ClockCircleOutlined v-else />
              </template>
              {{ getStatusInfo(record.status).label }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'duration_ms'">
            {{ formatDuration(record.duration_ms) }}
          </template>
          <template v-else-if="column.key === 'created_time'">
            {{ formatTime(record.created_time) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Button type="link" size="small" @click="showDetail(record)">
              详情
            </Button>
          </template>
        </template>

        <template #emptyText>
          <Empty description="暂无任务记录" />
        </template>
      </Table>
    </Card>

    <!-- 最近失败 -->
    <Card
      v-if="stats?.recent_failures?.length"
      size="small"
      title="最近失败"
      style="margin-top: 16px"
    >
      <div
        v-for="(fail, idx) in stats.recent_failures"
        :key="idx"
        class="failure-item"
      >
        <div class="failure-name">
          <CloseCircleOutlined style="color: #ff4d4f; margin-right: 6px" />
          {{ fail.task_display_name }}
        </div>
        <div class="failure-error">
          <Tooltip :title="fail.error_message">
            {{ fail.error_message?.slice(0, 80) || '未知错误' }}
          </Tooltip>
        </div>
        <div class="failure-time">{{ formatTime(fail.created_time) }}</div>
      </div>
    </Card>

    <!-- 详情抽屉 -->
    <Drawer
      v-model:open="detailVisible"
      title="任务详情"
      width="520"
      :destroy-on-close="true"
    >
      <div v-if="detailLoading" style="text-align: center; padding: 40px">
        <LoadingOutlined spin style="font-size: 24px" />
      </div>
      <template v-else-if="detailRecord">
        <Descriptions :column="1" bordered size="small">
          <DescriptionsItem label="任务名称">
            {{ detailRecord.task_display_name }}
          </DescriptionsItem>
          <DescriptionsItem label="分类">
            <Tag color="blue">
              {{
                getCategoryLabel(
                  detailRecord.task_category || '',
                )
              }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="getStatusInfo(detailRecord.status).color">
              {{ getStatusInfo(detailRecord.status).label }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="Celery Task ID">
            <span style="font-family: monospace; font-size: 12px">
              {{ detailRecord.celery_task_id }}
            </span>
          </DescriptionsItem>
          <DescriptionsItem label="Celery Task Name">
            {{ detailRecord.celery_task_name }}
          </DescriptionsItem>
          <DescriptionsItem v-if="detailRecord.duration_ms" label="耗时">
            {{ formatDuration(detailRecord.duration_ms) }}
          </DescriptionsItem>
          <DescriptionsItem label="创建时间">
            {{ formatTime(detailRecord.created_time) }}
          </DescriptionsItem>
          <DescriptionsItem v-if="detailRecord.started_time" label="开始时间">
            {{ formatTime(detailRecord.started_time) }}
          </DescriptionsItem>
          <DescriptionsItem
            v-if="detailRecord.completed_time"
            label="完成时间"
          >
            {{ formatTime(detailRecord.completed_time) }}
          </DescriptionsItem>
          <DescriptionsItem
            v-if="detailRecord.batch_job_id"
            label="批量任务ID"
          >
            <span style="font-family: monospace; font-size: 12px">
              {{ detailRecord.batch_job_id }}
            </span>
          </DescriptionsItem>
        </Descriptions>

        <!-- 业务上下文 -->
        <Card
          v-if="detailRecord.context"
          size="small"
          title="业务上下文"
          style="margin-top: 16px"
        >
          <pre style="margin: 0; font-size: 12px; white-space: pre-wrap">{{
            JSON.stringify(detailRecord.context, null, 2)
          }}</pre>
        </Card>

        <!-- 执行结果 -->
        <Card
          v-if="detailRecord.result_summary"
          size="small"
          title="执行结果"
          style="margin-top: 12px"
        >
          <pre style="margin: 0; font-size: 12px; white-space: pre-wrap">{{
            JSON.stringify(detailRecord.result_summary, null, 2)
          }}</pre>
        </Card>

        <!-- 错误信息 -->
        <Card
          v-if="detailRecord.error_message"
          size="small"
          title="错误信息"
          style="margin-top: 12px"
        >
          <pre
            style="
              margin: 0;
              font-size: 12px;
              white-space: pre-wrap;
              color: #ff4d4f;
            "
            >{{ detailRecord.error_message }}</pre
          >
        </Card>
      </template>
    </Drawer>
  </div>
</template>

<style scoped>
.task-center-page {
  padding: 16px;
}

.stat-card :deep(.ant-statistic-title) {
  font-size: 13px;
  margin-bottom: 4px;
}

.stat-card :deep(.ant-statistic-content) {
  font-size: 20px;
}

.category-stat-card {
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.category-stat-name {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 4px;
}

.category-stat-numbers {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.stat-total {
  color: #333;
  font-weight: 600;
}

.stat-success {
  color: #52c41a;
}

.stat-failure {
  color: #ff4d4f;
}

.category-stat-duration {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.failure-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}

.failure-item:last-child {
  border-bottom: none;
}

.failure-name {
  flex-shrink: 0;
  font-weight: 500;
  font-size: 13px;
  min-width: 120px;
}

.failure-error {
  flex: 1;
  color: #999;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.failure-time {
  flex-shrink: 0;
  color: #bbb;
  font-size: 12px;
}
</style>
