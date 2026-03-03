<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import {
  Alert,
  Button,
  Descriptions,
  DescriptionsItem,
  Divider,
  Progress,
  Spin,
  Table,
  Tag,
  message,
} from 'ant-design-vue';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import { getBatchJobProgress, getBatchJobItems, retryBatchJob, type BatchJobProgress, type BatchTaskItem } from '#/api/userecho/batch';
import { getUnifiedTask, type UnifiedTask } from '#/api/userecho/batch';

const props = defineProps<{
  jobId: string;
}>();

const progress = ref<BatchJobProgress | null>(null);
const unifiedTask = ref<UnifiedTask | null>(null);
const items = ref<BatchTaskItem[]>([]);
const loading = ref(true);
const itemsLoading = ref(false);
const retrying = ref(false);
const isBatchJob = ref(true); // 是否为批处理任务

// 轮询定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null;

// 任务类型显示名称
const taskTypeNameMap: Record<string, string> = {
  screenshot_recognition: '批量截图识别',
  excel_import: 'Excel 导入',
  data_export: '数据导出',
};

// 状态配置
const statusConfig = {
  pending: { color: 'default', text: '待处理' },
  processing: { color: 'processing', text: '处理中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
  skipped: { color: 'warning', text: '已跳过' },
};

// 失败的任务项
const failedItems = computed(() => items.value.filter(item => item.status === 'failed'));

// 表格列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'sequence_no',
    key: 'sequence_no',
    width: 80,
    customRender: ({ record }: { record: BatchTaskItem }) => record.sequence_no !== null ? record.sequence_no + 1 : '-',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
  },
  {
    title: '输入数据',
    dataIndex: 'input_data',
    key: 'input_data',
    ellipsis: true,
  },
  {
    title: '输出数据',
    dataIndex: 'output_data',
    key: 'output_data',
    ellipsis: true,
  },
  {
    title: '错误信息',
    dataIndex: 'error_message',
    key: 'error_message',
    ellipsis: true,
  },
  {
    title: '重试次数',
    dataIndex: 'retry_count',
    key: 'retry_count',
    width: 100,
  },
];

// 加载任务进度
async function loadProgress() {
  try {
    loading.value = true;

    // 使用统一任务接口（支持批处理任务和单任务）
    const task = await getUnifiedTask(props.jobId);
    unifiedTask.value = task;

    // 判断是否为批处理任务
    const batchTypes = ['batch_screenshot_recognition', 'batch_ai_clustering', 'batch_export'];
    isBatchJob.value = batchTypes.includes(task.type);

    if (isBatchJob.value) {
      // 批处理任务：继续加载批处理详情
      const res = await getBatchJobProgress(props.jobId);
      progress.value = res;
    }
  } catch (error) {
    console.error('Failed to load job progress:', error);
  } finally {
    loading.value = false;
  }
}

// 加载任务项列表
async function loadItems() {
  // 只有批处理任务才有任务项
  if (!isBatchJob.value) {
    items.value = [];
    return;
  }

  try {
    itemsLoading.value = true;
    const res = await getBatchJobItems(props.jobId);
    items.value = res || [];
  } catch (error) {
    console.error('Failed to load job items:', error);
  } finally {
    itemsLoading.value = false;
  }
}

// 重试失败的任务
async function handleRetry() {
  try {
    retrying.value = true;
    await retryBatchJob(props.jobId);
    message.success('已提交重试任务');
    await loadProgress();
    await loadItems();
  } catch (error) {
    console.error('Failed to retry job:', error);
    message.error('重试失败');
  } finally {
    retrying.value = false;
  }
}

// 下载结果
function handleDownload() {
  if (progress.value?.summary?.export_file_url) {
    window.open(progress.value.summary.export_file_url, '_blank');
  }
}

// 格式化 JSON 数据
function formatJson(data: any): string {
  if (!data) return '-';
  if (typeof data === 'string') return data;

  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

// 启动轮询
function startPolling() {
  stopPolling();
  const isProcessing = progress.value?.status === 'processing' || unifiedTask.value?.status === 'processing';
  if (isProcessing) {
    pollingTimer = setInterval(() => {
      loadProgress();
      loadItems();
    }, 3000); // 每3秒轮询一次
  }
}

// 停止轮询
function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

// 监听进度变化
watch(() => progress.value?.status || unifiedTask.value?.status, (newStatus) => {
  if (newStatus === 'processing') {
    startPolling();
  } else {
    stopPolling();
  }
});

// 监听 jobId 变化
watch(() => props.jobId, () => {
  loadProgress();
  loadItems();
}, { immediate: true });

onMounted(() => {
  loadProgress();
  loadItems();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <Spin :spinning="loading">
    <!-- 批处理任务详情 -->
    <div v-if="progress">
      <!-- 任务概览 -->
      <Descriptions
        bordered
        :column="2"
      >
        <DescriptionsItem label="任务名称">
          {{ progress.name }}
        </DescriptionsItem>

        <DescriptionsItem label="任务类型">
          <Tag color="blue">
            {{ taskTypeNameMap[progress.task_type] || progress.task_type }}
          </Tag>
        </DescriptionsItem>

        <DescriptionsItem label="任务状态">
          <Tag :color="statusConfig[progress.status]?.color">
            {{ statusConfig[progress.status]?.text }}
          </Tag>
        </DescriptionsItem>

        <DescriptionsItem label="总进度">
          <Progress
            :percent="progress.progress"
            :status="progress.status === 'failed' ? 'exception' : progress.status === 'completed' ? 'success' : 'active'"
          />
        </DescriptionsItem>

        <DescriptionsItem label="创建时间">
          {{ progress.create_time ? new Date(progress.create_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="开始时间">
          {{ progress.started_time ? new Date(progress.started_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="完成时间">
          {{ progress.completed_time ? new Date(progress.completed_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="Celery 任务 ID">
          <code class="text-xs">{{ progress.celery_task_id || '-' }}</code>
        </DescriptionsItem>
      </Descriptions>

      <!-- 统计信息 -->
      <div class="my-6 grid grid-cols-5 gap-4">
        <div class="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded">
          <div class="text-2xl font-bold">{{ progress.total_count }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">总数</div>
        </div>

        <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded">
          <div class="text-2xl font-bold text-blue-600">{{ progress.pending_count }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">待处理</div>
        </div>

        <div class="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded">
          <div class="text-2xl font-bold text-yellow-600">{{ progress.processing_count }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">处理中</div>
        </div>

        <div class="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded">
          <div class="text-2xl font-bold text-green-600">{{ progress.completed_count }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">成功</div>
        </div>

        <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded">
          <div class="text-2xl font-bold text-red-600">{{ progress.failed_count }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">失败</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="mb-6 flex gap-2">
        <Button
          v-if="failedItems.length > 0"
          type="primary"
          :loading="retrying"
          @click="handleRetry"
        >
          <ReloadOutlined />
          重试失败项 ({{ failedItems.length }})
        </Button>

        <Button
          v-if="progress.summary?.export_file_url"
          type="default"
          @click="handleDownload"
        >
          <DownloadOutlined />
          下载结果
        </Button>
      </div>

      <!-- 失败项提示 -->
      <Alert
        v-if="failedItems.length > 0"
        type="error"
        show-icon
        closable
        class="mb-4"
      >
        <template #message>
          有 {{ failedItems.length }} 个任务项执行失败，可以查看详细错误信息并重试
        </template>
      </Alert>

      <!-- 任务项列表 -->
      <Divider>任务项详情</Divider>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="itemsLoading"
        :pagination="{ pageSize: 20 }"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="(statusConfig as any)[record.status]?.color">
              <CheckCircleOutlined v-if="record.status === 'completed'" />
              <CloseCircleOutlined v-if="record.status === 'failed'" />
              {{ (statusConfig as any)[record.status]?.text }}
            </Tag>
          </template>

          <template v-if="column.key === 'input_data'">
            <div class="text-xs font-mono max-w-md truncate">
              {{ formatJson(record.input_data) }}
            </div>
          </template>

          <template v-if="column.key === 'output_data'">
            <div v-if="record.output_data" class="text-xs font-mono max-w-md truncate">
              {{ formatJson(record.output_data) }}
            </div>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-if="column.key === 'error_message'">
            <div v-if="record.error_message" class="text-xs text-red-600 max-w-md truncate">
              {{ record.error_message }}
            </div>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-if="column.key === 'retry_count'">
            <span :class="{ 'text-yellow-600': record.retry_count > 0 }">
              {{ record.retry_count }} / {{ record.max_retries }}
            </span>
          </template>
        </template>
      </Table>
    </div>

    <!-- 单任务详情 -->
    <div v-else-if="unifiedTask">
      <!-- 任务概览 -->
      <Descriptions
        bordered
        :column="2"
      >
        <DescriptionsItem label="任务名称">
          {{ unifiedTask.name }}
        </DescriptionsItem>

        <DescriptionsItem label="任务类型">
          <Tag color="blue">
            {{ taskTypeNameMap[unifiedTask.type] || unifiedTask.type }}
          </Tag>
        </DescriptionsItem>

        <DescriptionsItem label="任务状态">
          <Tag :color="statusConfig[unifiedTask.status]?.color">
            {{ statusConfig[unifiedTask.status]?.text }}
          </Tag>
        </DescriptionsItem>

        <DescriptionsItem label="总进度">
          <Progress
            :percent="unifiedTask.progress"
            :status="unifiedTask.status === 'failed' ? 'exception' : unifiedTask.status === 'completed' ? 'success' : 'active'"
          />
        </DescriptionsItem>

        <DescriptionsItem label="创建时间">
          {{ unifiedTask.created_time ? new Date(unifiedTask.created_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="开始时间">
          {{ unifiedTask.started_time ? new Date(unifiedTask.started_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="完成时间">
          {{ unifiedTask.completed_time ? new Date(unifiedTask.completed_time).toLocaleString('zh-CN') : '-' }}
        </DescriptionsItem>

        <DescriptionsItem label="Celery 任务 ID">
          <code class="text-xs">{{ unifiedTask.celery_task_id || '-' }}</code>
        </DescriptionsItem>
      </Descriptions>

      <!-- 任务结果摘要 -->
      <div v-if="unifiedTask.result_summary" class="mt-6">
        <Divider>任务结果</Divider>
        <pre class="bg-gray-50 dark:bg-gray-800 p-4 rounded text-xs overflow-auto">{{ JSON.stringify(unifiedTask.result_summary, null, 2) }}</pre>
      </div>

      <!-- 错误信息 -->
      <Alert
        v-if="unifiedTask.error_message"
        type="error"
        show-icon
        class="mt-4"
      >
        <template #message>
          执行失败
        </template>
        <template #description>
          {{ unifiedTask.error_message }}
        </template>
      </Alert>
    </div>
  </Spin>
</template>
