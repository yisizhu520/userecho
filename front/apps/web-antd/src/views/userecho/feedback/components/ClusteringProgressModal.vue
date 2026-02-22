<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch } from 'vue';
import { message } from 'ant-design-vue';
import { getClusteringTaskStatus } from '#/api';

interface Props {
  open: boolean;
  taskId: string;
}

interface Emits {
  (e: 'update:open', value: boolean): void;
  (e: 'success', result: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const taskState = ref<'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'>('PENDING');
const taskError = ref<string>('');

let pollTimer: number | null = null;

const progress = computed(() => {
  switch (taskState.value) {
    case 'PENDING':
      return 10;
    case 'STARTED':
    case 'RETRY':
      return 60;
    case 'SUCCESS':
    case 'FAILURE':
      return 100;
    default:
      return 0;
  }
});

const step = computed(() => {
  switch (taskState.value) {
    case 'PENDING':
      return 0;
    case 'STARTED':
    case 'RETRY':
      return 1;
    case 'SUCCESS':
    case 'FAILURE':
      return 2;
    default:
      return 0;
  }
});

const stopPoll = () => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
};

const close = () => {
  stopPoll();
  emit('update:open', false);
};

const pollTask = async () => {
  if (!props.taskId) return;
  
  try {
    const status = await getClusteringTaskStatus(props.taskId);
    taskState.value = status.state;

    if (status.state === 'FAILURE') {
      taskError.value = status.error || '任务执行失败';
      message.error(taskError.value);
      close();
      return;
    }

    if (status.state === 'SUCCESS') {
      const result: any = status.result;
      if (!result) {
        message.warning('智能整理任务完成，但未返回结果');
        close();
        return;
      }

      if (result.status === 'skipped') {
        message.warning(result.message || '整理已跳过');
      } else {
        // 检查是否有合并建议
        const mergeSuggestionsCount = result.merge_suggestions?.length ?? 0;
        if (mergeSuggestionsCount > 0) {
          message.info(`整理完成：创建 ${result.topics_created ?? 0} 个主题，发现 ${mergeSuggestionsCount} 个相似需求待处理`);
        } else {
          message.success(`整理完成：创建 ${result.topics_created ?? 0} 个主题，未关联 ${result.noise_count ?? 0} 条`);
        }
      }
      emit('success', result);
      close();
    }

  } catch (error: any) {
    message.error(error.message || '查询任务状态失败');
    close();
  }
};

// 监听 taskId 变化，开始轮询
watch(() => props.taskId, async (newTaskId) => {
  if (newTaskId && props.open) {
    taskState.value = 'PENDING';
    taskError.value = '';
    stopPoll();
    
    // 先拉一次
    await pollTask();
    // 开始轮询
    pollTimer = window.setInterval(pollTask, 2000);
  }
}, { immediate: true });

// 监听 open 变化
watch(() => props.open, (isOpen) => {
  if (!isOpen) {
    stopPoll();
  }
});

onBeforeUnmount(() => {
  stopPoll();
});

const handleCancel = () => {
  close();
};
</script>

<template>
  <a-modal
    :open="open"
    title="AI 智能整理"
    :footer="null"
    :maskClosable="false"
    @cancel="handleCancel"
  >
    <a-steps :current="step" size="small">
      <a-step title="任务提交" />
      <a-step title="处理中" />
      <a-step title="完成" />
    </a-steps>

    <div class="mt-4">
      <a-progress :percent="progress" :status="taskState === 'FAILURE' ? 'exception' : 'active'" />
      <div class="text-gray-500 mt-2">
        <div v-if="taskId">任务 ID：{{ taskId }}</div>
        <div v-if="taskError" class="text-red-500 mt-1">错误：{{ taskError }}</div>
      </div>
    </div>
  </a-modal>
</template>
