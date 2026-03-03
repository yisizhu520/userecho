<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { Button, Input, Select, Spin, Drawer, Tooltip, Progress, Empty } from 'ant-design-vue';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  StopOutlined,
  SearchOutlined,
  CalendarOutlined,
  RightOutlined,
  CloudServerOutlined,
  FileExcelOutlined,
  FileImageOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { getUnifiedTasks, cancelUnifiedTask, type UnifiedTask, type TaskType, type TaskStatus } from '#/api/userecho/batch';
import BatchJobDetail from './components/BatchJobDetail.vue';

// 任务列表
const jobs = ref<UnifiedTask[]>([]);
const loading = ref(true);
const taskTypeFilter = ref<TaskType | undefined>(undefined);
const statusFilter = ref<TaskStatus | undefined>(undefined);
const searchText = ref('');

// 详情抽屉
const detailVisible = ref(false);
const currentJobId = ref<string | null>(null);

// 轮询定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null;

// 任务类型选项
const taskTypeOptions = [
  { label: '全部类型', value: undefined },
  { label: '截图识别', value: 'batch_screenshot_recognition' },
  { label: 'AI 聚类分析', value: 'batch_ai_clustering' },
  { label: '数据导出', value: 'batch_export' },
  { label: '数据导入', value: 'excel_import' },
];

// 状态选项
const statusOptions = [
  { label: '全部状态', value: undefined },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' },
];

// 类型定义
interface TaskConfig {
  icon: any;
  color: string;
  bg: string;
  label: string;
}

interface StatusConfigItem {
  icon: any;
  color: string;
  bg: string;
  text: string;
  border: string;
  spin?: boolean;
}

// 任务类型配置（图标和颜色）
const taskTypeConfig: Record<string, TaskConfig> = {
  batch_screenshot_recognition: { icon: FileImageOutlined, color: 'text-purple-600', bg: 'bg-purple-50', label: '批量截图识别' },
  batch_ai_clustering: { icon: ExperimentOutlined, color: 'text-indigo-600', bg: 'bg-indigo-50', label: '批量 AI 聚类' },
  batch_export: { icon: CloudServerOutlined, color: 'text-blue-600', bg: 'bg-blue-50', label: '批量导出' },
  excel_import: { icon: FileExcelOutlined, color: 'text-green-600', bg: 'bg-green-50', label: 'Excel 导入' },
  clustering: { icon: ExperimentOutlined, color: 'text-indigo-600', bg: 'bg-indigo-50', label: 'AI 聚类' },
  screenshot_recognition: { icon: FileImageOutlined, color: 'text-purple-600', bg: 'bg-purple-50', label: '截图识别' },
  ai_screenshot: { icon: ThunderboltOutlined, color: 'text-orange-600', bg: 'bg-orange-50', label: 'AI 截图分析' },
  default: { icon: CloudServerOutlined, color: 'text-gray-600', bg: 'bg-gray-50', label: '通用任务' },
};

// 状态配置
const statusConfig: Record<string, StatusConfigItem> = {
  pending: { icon: ClockCircleOutlined, color: 'text-gray-500', bg: 'bg-gray-100', text: '等待开始', border: 'border-gray-200' },
  processing: { icon: SyncOutlined, color: 'text-blue-600', bg: 'bg-blue-50', text: '正在处理', spin: true, border: 'border-blue-200' },
  completed: { icon: CheckCircleOutlined, color: 'text-green-600', bg: 'bg-green-50', text: '已完成', border: 'border-green-200' },
  failed: { icon: CloseCircleOutlined, color: 'text-red-600', bg: 'bg-red-50', text: '执行失败', border: 'border-red-200' },
  cancelled: { icon: StopOutlined, color: 'text-gray-400', bg: 'bg-gray-50', text: '已取消', border: 'border-gray-200' },
};

function getTaskConfig(type: string): TaskConfig {
  return taskTypeConfig[type] || taskTypeConfig['default']!;
}

function getStatusConfig(status: string): StatusConfigItem {
  return statusConfig[status] || statusConfig['pending']!;
}

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
    // 处理响应结构兼容性
    if (Array.isArray(res)) {
      jobs.value = res;
    } else if ('items' in res && Array.isArray(res.items)) {
      jobs.value = res.items;
    } else if (res.data && 'items' in res.data && Array.isArray(res.data.items)) {
      jobs.value = res.data.items;
    } else if (res.data && Array.isArray(res.data)) {
      jobs.value = res.data;
    } else {
      jobs.value = [];
    }
  } catch (error) {
    console.error('Failed to load tasks:', error);
    jobs.value = [];
  } finally {
    loading.value = false;
  }
}

// 筛选逻辑
const filteredJobs = computed(() => {
  let result = jobs.value;

  if (taskTypeFilter.value) {
    result = result.filter(job => job.type === taskTypeFilter.value);
  }

  if (statusFilter.value) {
    result = result.filter(job => job.status === statusFilter.value);
  }

  if (searchText.value) {
    const query = searchText.value.toLowerCase();
    result = result.filter(job =>
      getTaskDescription(job).toLowerCase().includes(query) ||
      (taskTypeConfig[job.type]?.label || job.type).toLowerCase().includes(query)
    );
  }

  return result;
});

// 查看详情
function viewDetail(jobId: string) {
  currentJobId.value = jobId;
  detailVisible.value = true;
}

// 取消任务
async function handleCancelJob(jobId: string, event: Event) {
  event.stopPropagation(); // 防止触发卡片点击
  try {
    await cancelUnifiedTask(jobId);
    await loadJobs();
  } catch (error) {
    console.error('Failed to cancel task:', error);
  }
}

// 格式化相对时间
function formatRelativeTime(time: string | null): string {
  if (!time) return '';
  const date = new Date(time);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  if (diff < 2592000000) return `${Math.floor(diff / 86400000)} 天前`;

  return date.toLocaleDateString();
}

// 获取任务耗时友好显示
function getDurationText(job: UnifiedTask): string {
  if (!job.started_time) return '-';
  const start = new Date(job.started_time).getTime();
  const end = job.completed_time ? new Date(job.completed_time).getTime() : Date.now();
  const duration = end - start;

  if (duration < 1000) return '< 1秒';
  if (duration < 60000) return `${Math.floor(duration / 1000)}秒`;
  if (duration < 3600000) return `${Math.floor(duration / 60000)}分 ${Math.floor((duration % 60000) / 1000)}秒`;
  return `${Math.floor(duration / 3600000)}小时 ${Math.floor((duration % 3600000) / 60000)}分`;
}

// 获取任务描述（与之前逻辑一致，只需确保引用正确）
function getTaskDescription(job: UnifiedTask): string {
  if (job.description) return job.description;
  if (job.metadata?.description) return job.metadata.description;
  if (job.summary?.description) return job.summary.description;

  switch (job.type) {
    case 'excel_import':
      return job.metadata?.filename || job.metadata?.file_name || 'Excel 数据导入';
    case 'batch_ai_clustering':
      return `聚类分析任务`;
    case 'batch_screenshot_recognition':
      return `截图识别任务`;
    case 'batch_export':
      return `数据导出 - ${job.metadata?.export_type || '反馈数据'}`;
    default:
      return taskTypeConfig[job.type]?.label || '未知任务';
  }
}

// 轮询控制
function startPolling() {
  stopPolling();
  pollingTimer = setInterval(() => {
    const hasProcessing = jobs.value.some(job => job.status === 'processing');
    if (hasProcessing) loadJobs();
  }, 4000);
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

function handleDetailClose() {
  detailVisible.value = false;
  currentJobId.value = null;
  loadJobs(); // 刷新以获取最新状态
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
  <Page title="我的任务中心" description="实时监控和管理所有后台处理任务">
    <!-- 顶部工具栏 -->
    <div class="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-center gap-3 w-full md:w-auto">
        <Input
          v-model:value="searchText"
          placeholder="搜索任务..."
          class="w-full md:w-64"
          allow-clear
        >
          <template #prefix><SearchOutlined class="text-gray-400" /></template>
        </Input>

        <Select
          v-model:value="taskTypeFilter"
          :options="taskTypeOptions"
          placeholder="任务类型"
          class="w-40 hidden md:block"
          allow-clear
        />

        <Select
          v-model:value="statusFilter"
          :options="statusOptions"
          placeholder="执行状态"
          class="w-32 hidden md:block"
          allow-clear
        />
      </div>

      <div class="flex items-center gap-2">
        <Button class="bg-white" @click="loadJobs">
          <template #icon><SyncOutlined :spin="loading" /></template>
          刷新
        </Button>
      </div>
    </div>

    <!-- 任务网格 -->
    <Spin :spinning="loading">
      <div v-if="filteredJobs.length === 0" class="flex flex-col items-center justify-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-200">
        <Empty description="暂无符合条件的任务" />
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <div
          v-for="job in filteredJobs"
          :key="job.id"
          class="group relative bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden"
          @click="viewDetail(job.id)"
        >
          <!-- 顶部状态条 -->
          <div :class="`h-1 w-full ${getStatusConfig(job.status).color.replace('text-', 'bg-')}`"></div>

          <div class="p-6">
            <!-- 头部：图标与状态 -->
            <div class="flex justify-between items-start mb-4">
              <div :class="`w-12 h-12 rounded-xl flex items-center justify-center ${getTaskConfig(job.type).bg}`">
                <component :is="getTaskConfig(job.type).icon" class="text-xl" :class="getTaskConfig(job.type).color" />
              </div>

              <div :class="`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${getStatusConfig(job.status).bg} ${getStatusConfig(job.status).color}`">
                <component :is="getStatusConfig(job.status).icon" :spin="getStatusConfig(job.status).spin" />
                {{ getStatusConfig(job.status).text }}
              </div>
            </div>

            <!-- 内容：标题与描述 -->
            <div class="mb-5">
              <h3 class="font-bold text-gray-900 text-lg mb-1 truncate" :title="getTaskDescription(job)">
                {{ getTaskDescription(job) }}
              </h3>
              <p class="text-sm text-gray-500 line-clamp-2 min-h-[40px]">
                <span v-if="getDurationText(job) !== '-'" class="mr-2 inline-flex items-center text-xs bg-gray-50 px-2 py-0.5 rounded text-gray-400">
                  <ClockCircleOutlined class="mr-1 text-[10px]" /> 耗时 {{ getDurationText(job) }}
                </span>
                <span class="text-xs text-gray-400">ID: {{ job.id.slice(0, 8) }}</span>
              </p>
            </div>

            <!-- 进度区域 -->
            <div class="mb-5">
              <div class="flex justify-between text-xs text-gray-500 mb-1.5">
                <span>处理进度</span>
                <span class="font-medium text-gray-700">{{ Math.floor(job.progress) }}%</span>
              </div>
              <Progress
                :percent="job.progress"
                :show-info="false"
                :stroke-color="job.status === 'failed' ? '#ef4444' : job.status === 'completed' ? '#22c55e' : '#3b82f6'"
                track-color="#f3f4f6"
                size="small"
                class="!m-0"
              />
            </div>

            <!-- 底部：详细数据统计 -->
            <div v-if="job.total_count" class="grid grid-cols-3 gap-2 py-3 bg-gray-50/50 rounded-lg border border-gray-100/50">
              <div class="flex flex-col items-center">
                <span class="text-[10px] uppercase tracking-wider text-gray-400 font-medium">总数</span>
                <span class="text-sm font-semibold text-gray-700">{{ job.total_count }}</span>
              </div>
              <div class="flex flex-col items-center border-l border-gray-100">
                <span class="text-[10px] uppercase tracking-wider text-gray-400 font-medium">成功</span>
                <span class="text-sm font-semibold text-green-600">{{ job.completed_count }}</span>
              </div>
              <div class="flex flex-col items-center border-l border-gray-100">
                <span class="text-[10px] uppercase tracking-wider text-gray-400 font-medium">失败</span>
                <span class="text-sm font-semibold text-red-600">{{ job.failed_count }}</span>
              </div>
            </div>

            <div v-else class="flex items-center justify-center h-[54px] bg-gray-50/50 rounded-lg border border-gray-100/50 text-xs text-gray-400">
              单项任务
            </div>
          </div>

          <!-- 底部动作栏 (Hover时更明显) -->
          <div class="border-t border-gray-100 px-6 py-3 flex items-center justify-between bg-gray-50/30">
            <div class="flex items-center text-xs text-gray-400">
              <CalendarOutlined class="mr-1.5" />
              {{ formatRelativeTime(job.created_time) }}
            </div>

            <button class="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center transition-colors group-hover:translate-x-1 duration-300">
              查看详情
              <RightOutlined class="ml-1 text-xs" />
            </button>
          </div>

          <!-- 悬浮取消按钮 (仅处理中显示) -->
          <div v-if="job.status === 'processing'" class="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
            <Tooltip title="取消任务">
              <Button
                type="text"
                danger
                shape="circle"
                size="small"
                class="bg-white shadow-md border border-gray-100 flex items-center justify-center"
                @click="handleCancelJob(job.id, $event)"
              >
                <StopOutlined />
              </Button>
            </Tooltip>
          </div>
        </div>
      </div>
    </Spin>

    <Drawer
      v-model:open="detailVisible"
      title="任务详情"
      width="800"
      @close="handleDetailClose"
      class="task-detail-drawer"
    >
      <BatchJobDetail
        v-if="currentJobId"
        :job-id="currentJobId"
      />
    </Drawer>
  </Page>
</template>

<style scoped>
/* 自定义进度条高度 */
:deep(.ant-progress-bg) {
  height: 6px !important;
  border-radius: 4px !important;
}

:deep(.ant-progress-inner) {
  background-color: #f3f4f6;
  border-radius: 4px !important;
}

:deep(.ant-input-affix-wrapper) {
  border-radius: 8px;
  padding-top: 6px;
  padding-bottom: 6px;
  border-color: #e5e7eb;
}

:deep(.ant-select-selector) {
  border-radius: 8px !important;
  height: 38px !important;
  display: flex items-center;
  border-color: #e5e7eb !important;
}

:deep(.ant-select-selection-item) {
  line-height: 36px !important;
}
</style>
