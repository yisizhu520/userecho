<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Card, Progress, Tag, Button, Empty } from 'ant-design-vue';
import {
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  RightOutlined,
} from '@ant-design/icons-vue';
import { getBatchJobs, type BatchJob } from '#/api/userecho/batch';

const router = useRouter();

const jobs = ref<BatchJob[]>([]);
const loading = ref(false);

// 轮询定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null;

// 任务类型显示名称
const taskTypeNameMap: Record<string, string> = {
  screenshot_recognition: '批量截图识别',
  excel_import: 'Excel 导入',
  data_export: '数据导出',
};

// 状态配置
const statusConfig: Record<string, any> = {
  pending: { icon: ClockCircleOutlined, color: 'default', text: '待处理' },
  processing: { icon: SyncOutlined, color: 'processing', text: '处理中', spin: true },
  completed: { icon: CheckCircleOutlined, color: 'success', text: '已完成' },
};

// 进行中的任务（最多显示3个）
const activeJobs = computed(() => {
  return jobs.value
    .filter(job => job.status === 'processing' || job.status === 'pending')
    .slice(0, 3);
});

// 是否有活跃任务
const hasActiveJobs = computed(() => activeJobs.value.length > 0);

// 加载任务列表
async function loadJobs() {
  try {
    loading.value = true;
    const res = await getBatchJobs({
      page: 1,
      page_size: 10,
    });
    jobs.value = (res as any).data || [];
  } catch (error) {
    console.error('Failed to load batch jobs:', error);
  } finally {
    loading.value = false;
  }
}

// 跳转到任务列表页
function goToTaskList() {
  router.push('/app/batch-jobs');
}

// 跳转到任务详情
function goToDetail(jobId: string) {
  router.push(`/app/batch-jobs?job=${jobId}`);
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

// 启动轮询
function startPolling() {
  stopPolling();
  pollingTimer = setInterval(() => {
    if (hasActiveJobs.value) {
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

onMounted(() => {
  loadJobs();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <Card
    title="批处理任务"
    :loading="loading"
    class="mb-4"
  >
    <template #extra>
      <Button
        type="link"
        size="small"
        @click="goToTaskList"
      >
        查看全部
        <RightOutlined />
      </Button>
    </template>

    <div v-if="!hasActiveJobs" class="py-8">
      <Empty
        :image="Empty.PRESENTED_IMAGE_SIMPLE"
        description="暂无进行中的任务"
      >
        <Button type="primary" @click="goToTaskList">
          查看历史任务
        </Button>
      </Empty>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="job in activeJobs"
        :key="job.batch_id"
        class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
        @click="goToDetail(job.batch_id)"
      >
        <!-- 任务头部 -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <Tag color="blue" class="mb-0">
              {{ taskTypeNameMap[job.task_type] || job.task_type }}
            </Tag>

            <Tag
              :color="statusConfig[job.status]?.color"
              class="mb-0"
            >
              <component
                :is="statusConfig[job.status]?.icon"
                :spin="statusConfig[job.status]?.spin"
                class="mr-1"
              />
              {{ statusConfig[job.status]?.text }}
            </Tag>
          </div>

          <span class="text-xs text-gray-500">
            {{ formatTime(job.create_time) }}
          </span>
        </div>

        <!-- 任务名称 -->
        <div class="text-sm mb-3 text-gray-700 dark:text-gray-300">
          {{ job.name }}
        </div>

        <!-- 进度条 -->
        <Progress
          :percent="job.progress"
          :status="job.status === 'processing' ? 'active' : 'normal'"
          :stroke-color="job.status === 'processing' ? '#1890ff' : undefined"
          size="small"
        />

        <!-- 统计信息 -->
        <div class="flex items-center justify-between mt-2 text-xs text-gray-600 dark:text-gray-400">
          <span>
            总数: {{ job.total_count }}
          </span>
          <span class="text-green-600">
            成功: {{ job.completed_count }}
          </span>
          <span class="text-red-600">
            失败: {{ job.failed_count }}
          </span>
          <span class="text-gray-500">
            待处理: {{ job.pending_count }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
