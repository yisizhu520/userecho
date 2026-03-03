<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { Button, Card, Progress, Select, Spin, Tag, Empty, Drawer, Tooltip } from 'ant-design-vue';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  EyeOutlined,
  StopOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { getUnifiedTasks, cancelUnifiedTask, type UnifiedTask, type TaskType, type TaskStatus } from '#/api/userecho/batch';
import BatchJobDetail from './components/BatchJobDetail.vue';

// 任务列表
const jobs = ref<UnifiedTask[]>([]);
const loading = ref(true);
const taskTypeFilter = ref<TaskType | undefined>(undefined);
const statusFilter = ref<TaskStatus | undefined>(undefined);

// 详情抽屉
const detailVisible = ref(false);
const currentJobId = ref<string | null>(null);

// 轮询定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null;

// 任务类型选项
const taskTypeOptions = [
  { label: '全部类型', value: undefined },
  { label: '批量截图识别', value: 'batch_screenshot_recognition' },
  { label: '批量AI聚类', value: 'batch_ai_clustering' },
  { label: '批量导出', value: 'batch_export' },
  { label: 'Excel导入', value: 'excel_import' },
  { label: 'AI聚类', value: 'clustering' },
  { label: '截图识别', value: 'screenshot_recognition' },
  { label: 'AI截图分析', value: 'ai_screenshot' },
  { label: '批处理任务', value: 'batch' },
];

// 状态选项
const statusOptions = [
  { label: '全部状态', value: undefined },
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' },
];

// 任务类型显示名称
const taskTypeNameMap: Record<string, string> = {
  batch_screenshot_recognition: '批量截图识别',
  batch_ai_clustering: '批量AI聚类',
  batch_export: '批量导出',
  excel_import: 'Excel导入',
  clustering: 'AI聚类',
  screenshot_recognition: '截图识别',
  ai_screenshot: 'AI截图分析',
  batch: '批处理任务',
  data_export: '数据导出',
};

// 状态配置
const statusConfig = {
  pending: { icon: ClockCircleOutlined, color: 'default', text: '待处理' },
  processing: { icon: SyncOutlined, color: 'processing', text: '处理中', spin: true },
  completed: { icon: CheckCircleOutlined, color: 'success', text: '已完成' },
  failed: { icon: CloseCircleOutlined, color: 'error', text: '失败' },
  cancelled: { icon: StopOutlined, color: 'default', text: '已取消' },
};

// 加载任务列表
async function loadJobs() {
  try {
    loading.value = true;
    const res = await getUnifiedTasks({
      task_type: taskTypeFilter.value,
      status: statusFilter.value,
      page: 1,
      page_size: 100,
    });
    // 处理响应：后端返回 { data: { total: number, items: [] } }
    if (Array.isArray(res)) {
      jobs.value = res;
    } else if ('items' in res && Array.isArray(res.items)) {
      // 直接返回 { total, items } 的情况
      jobs.value = res.items;
    } else if (res.data && 'items' in res.data && Array.isArray(res.data.items)) {
      // 嵌套 data 的情况
      jobs.value = res.data.items;
    } else if (res.data && Array.isArray(res.data)) {
      jobs.value = res.data;
    } else {
      jobs.value = [];
      console.warn('Unexpected response format:', res);
    }
  } catch (error) {
    console.error('Failed to load unified tasks:', error);
    jobs.value = [];
  } finally {
    loading.value = false;
  }
}

// 筛选后的任务列表
const filteredJobs = computed(() => {
  let result = jobs.value;

  if (taskTypeFilter.value) {
    result = result.filter(job => job.type === taskTypeFilter.value);
  }

  if (statusFilter.value) {
    result = result.filter(job => job.status === statusFilter.value);
  }

  return result;
});

// 查看详情
function viewDetail(jobId: string) {
  currentJobId.value = jobId;
  detailVisible.value = true;
}

// 取消任务
async function handleCancelJob(jobId: string) {
  try {
    await cancelUnifiedTask(jobId);
    await loadJobs();
  } catch (error) {
    console.error('Failed to cancel task:', error);
  }
}

// 格式化时间
function formatTime(time: string | null): string {
  if (!time) return '-';
  const date = new Date(time);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// 计算执行时长
function getExecutionDuration(job: UnifiedTask): string {
  if (!job.started_time) return '-';

  const start = new Date(job.started_time).getTime();
  const end = job.completed_time ? new Date(job.completed_time).getTime() : Date.now();
  const duration = end - start;

  if (duration < 60000) return `${Math.floor(duration / 1000)} 秒`;
  if (duration < 3600000) return `${Math.floor(duration / 60000)} 分钟`;
  return `${Math.floor(duration / 3600000)} 小时 ${Math.floor((duration % 3600000) / 60000)} 分钟`;
}

// 截断描述文本
function truncateDescription(text: string | undefined, maxLength: number = 50): { text: string; truncated: boolean } {
  if (!text) return { text: '-', truncated: false };
  if (text.length <= maxLength) return { text, truncated: false };
  return { text: text.substring(0, maxLength) + '...', truncated: true };
}

// 获取任务描述
function getTaskDescription(job: UnifiedTask): string {
  // 优先使用 description 字段
  if (job.description) return job.description;
  if (job.metadata?.description) return job.metadata.description;
  if (job.summary?.description) return job.summary.description;

  // 根据任务类型生成默认描述
  switch (job.type) {
    case 'excel_import':
      return job.metadata?.filename || job.metadata?.file_name || 'Excel 数据导入';
    case 'batch_ai_clustering':
      return `聚类分析 - ${job.total_count || 0} 条反馈`;
    case 'batch_screenshot_recognition':
      return `截图识别 - ${job.total_count || 0} 张图片`;
    case 'batch_export':
      return `数据导出 - ${job.metadata?.export_type || '反馈数据'}`;
    case 'clustering':
      return job.metadata?.board_name ? `${job.metadata.board_name} 聚类分析` : 'AI 聚类分析';
    case 'screenshot_recognition':
      return '单张截图识别';
    case 'ai_screenshot':
      return 'AI 截图分析';
    default:
      return job.name || '任务处理中';
  }
}

// 获取元数据关键信息（根据任务类型定制）
function getMetadataInfo(job: UnifiedTask): Array<{ label: string; value: string }> {
  const info: Array<{ label: string; value: string }> = [];

  switch (job.type) {
    case 'excel_import':
      if (job.metadata?.filename) info.push({ label: '文件名', value: job.metadata.filename });
      if (job.metadata?.sheet_name) info.push({ label: '工作表', value: job.metadata.sheet_name });
      break;

    case 'batch_ai_clustering':
    case 'clustering':
      if (job.metadata?.board_name) info.push({ label: '看板', value: job.metadata.board_name });
      if (job.summary?.cluster_count) info.push({ label: '聚类数', value: String(job.summary.cluster_count) });
      if (job.metadata?.min_similarity) info.push({ label: '相似度阈值', value: String(job.metadata.min_similarity) });
      break;

    case 'batch_screenshot_recognition':
    case 'screenshot_recognition':
      if (job.metadata?.board_name) info.push({ label: '看板', value: job.metadata.board_name });
      if (job.metadata?.recognition_type) info.push({ label: '识别类型', value: job.metadata.recognition_type });
      break;

    case 'batch_export':
      if (job.metadata?.export_type) info.push({ label: '导出类型', value: job.metadata.export_type });
      if (job.metadata?.format) info.push({ label: '格式', value: job.metadata.format });
      if (job.metadata?.board_name) info.push({ label: '看板', value: job.metadata.board_name });
      break;
  }

  return info;
}

// 启动轮询
function startPolling() {
  stopPolling();
  pollingTimer = setInterval(() => {
    const hasProcessing = jobs.value.some(job => job.status === 'processing');
    if (hasProcessing) {
      loadJobs();
    }
  }, 3000); // 每3秒轮询一次
}

// 停止轮询
function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

// 关闭详情抽屉时刷新列表
function handleDetailClose() {
  detailVisible.value = false;
  currentJobId.value = null;
  loadJobs();
}

onMounted(() => {
  loadJobs();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <Page
    title="我的任务"
    description="查看和管理我的所有异步任务"
  >
    <!-- 筛选器 -->
    <div class="mb-6 flex items-center gap-4">
      <Select
        v-model:value="taskTypeFilter"
        :options="taskTypeOptions"
        placeholder="选择任务类型"
        style="width: 200px"
        @change="loadJobs"
      />

      <Select
        v-model:value="statusFilter"
        :options="statusOptions"
        placeholder="选择状态"
        style="width: 200px"
        @change="loadJobs"
      />

      <Button @click="loadJobs">
        刷新
      </Button>
    </div>

    <!-- 任务列表 -->
    <Spin :spinning="loading">
      <div v-if="filteredJobs.length === 0" class="py-12">
        <Empty description="暂无任务" />
      </div>

      <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="job in filteredJobs"
          :key="job.id"
          class="hover:shadow-lg transition-shadow"
        >
          <!-- 任务头部：类型标签 + 状态标签 -->
          <div class="flex items-center gap-2 mb-3">
            <Tag color="blue">
              {{ taskTypeNameMap[job.type] || job.type }}
            </Tag>

            <Tag
              :color="statusConfig[job.status]?.color"
              :class="{ 'animate-pulse': job.status === 'processing' }"
            >
              <component
                :is="statusConfig[job.status]?.icon"
                :spin="(statusConfig[job.status] as any)?.spin"
                class="mr-1"
              />
              {{ statusConfig[job.status]?.text }}
            </Tag>
          </div>

          <!-- 任务描述：带 Tooltip 的截断文本 -->
          <div class="mb-3">
            <Tooltip
              v-if="truncateDescription(getTaskDescription(job)).truncated"
              :title="getTaskDescription(job)"
            >
              <div class="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-1 line-clamp-2">
                <FileTextOutlined class="mt-0.5 flex-shrink-0 text-gray-400" />
                <span>{{ truncateDescription(getTaskDescription(job)).text }}</span>
              </div>
            </Tooltip>
            <div
              v-else
              class="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-1 line-clamp-2"
            >
              <FileTextOutlined class="mt-0.5 flex-shrink-0 text-gray-400" />
              <span>{{ getTaskDescription(job) }}</span>
            </div>
          </div>

          <!-- 元数据关键信息（根据任务类型定制）-->
          <div v-if="getMetadataInfo(job).length > 0" class="mb-3 flex flex-wrap gap-2">
            <Tag
              v-for="(info, idx) in getMetadataInfo(job)"
              :key="idx"
              color="default"
              class="text-xs"
            >
              {{ info.label }}: {{ info.value }}
            </Tag>
          </div>

          <!-- 进度条 -->
          <div class="mb-4">
            <Progress
              :percent="job.progress"
              :status="job.status === 'failed' ? 'exception' : job.status === 'completed' ? 'success' : 'active'"
              :stroke-color="job.status === 'processing' ? '#1890ff' : undefined"
            />
          </div>

          <!-- 两列布局：左侧统计数据 + 右侧时间信息 -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <!-- 左侧：统计数据 -->
            <div>
              <!-- 判断是否为批量任务：如果 total_count 不为 null 则认为是批量任务 -->
              <div v-if="job.total_count !== null && job.total_count !== undefined" class="space-y-2">
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">总数</span>
                  <span class="font-semibold">{{ job.total_count ?? 0 }}</span>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">成功</span>
                  <span class="font-semibold text-green-600">{{ job.completed_count ?? 0 }}</span>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">失败</span>
                  <span class="font-semibold text-red-600">{{ job.failed_count ?? 0 }}</span>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">待处理</span>
                  <span class="font-semibold text-blue-600">
                    {{ job.pending_count ?? ((job.total_count ?? 0) - (job.completed_count ?? 0) - (job.failed_count ?? 0)) }}
                  </span>
                </div>
              </div>
              <div v-else class="text-xs text-gray-500">
                单次任务
              </div>
            </div>

            <!-- 右侧：时间信息 -->
            <div class="space-y-2">
              <div class="text-xs">
                <div class="text-gray-500 mb-0.5">创建时间</div>
                <div class="text-gray-700 dark:text-gray-300">{{ formatTime(job.created_time) }}</div>
              </div>
              <div v-if="job.started_time" class="text-xs">
                <div class="text-gray-500 mb-0.5">开始时间</div>
                <div class="text-gray-700 dark:text-gray-300">{{ formatTime(job.started_time) }}</div>
              </div>
              <div v-if="job.started_time" class="text-xs">
                <div class="text-gray-500 mb-0.5">执行耗时</div>
                <div class="text-gray-700 dark:text-gray-300 font-medium">{{ getExecutionDuration(job) }}</div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-2">
            <Button
              type="primary"
              size="small"
              block
              @click="viewDetail(job.id)"
            >
              <EyeOutlined />
              查看详情
            </Button>

            <Button
              v-if="job.status === 'processing'"
              danger
              size="small"
              @click.stop="handleCancelJob(job.id)"
            >
              <StopOutlined />
              取消
            </Button>
          </div>
        </Card>
      </div>
    </Spin>

    <!-- 详情抽屉 -->
    <Drawer
      v-model:open="detailVisible"
      title="任务详情"
      width="800"
      @close="handleDetailClose"
    >
      <BatchJobDetail
        v-if="currentJobId"
        :job-id="currentJobId"
      />
    </Drawer>
  </Page>
</template>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 限制描述文本为最多2行 */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
