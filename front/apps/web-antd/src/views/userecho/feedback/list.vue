<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Feedback,
  CreateFeedbackParams,
  UpdateFeedbackParams,
} from '#/api';

import { computed, onBeforeUnmount, ref, onMounted } from 'vue';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getFeedbackList,
  createFeedback,
  updateFeedback,
  deleteFeedback,
  triggerClustering,
  getClusteringTaskStatus,
} from '#/api';
import {
  querySchema,
  useColumns,
  feedbackFormSchema,
} from '#/views/userecho/feedback/data';

/**
 * 查询表单配置
 */
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('common.form.query'),
  },
  schema: querySchema,
};

/**
 * 表格配置
 */
const gridOptions: VxeTableGridOptions<Feedback> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: true,
    refreshOptions: {
      code: 'query',
    },
    custom: true,
    zoom: true,
  },
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const data = await getFeedbackList({
          skip: (page.currentPage - 1) * page.pageSize,
          limit: page.pageSize,
          ...formValues,
        });
        // vxe-table 期望的返回格式（根据全局 response 配置）
        return {
          items: data,           // 数据数组
          total: data.length,    // 当前查询到的记录数（临时方案，理想情况下应该由后端返回总数）
        };
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

/**
 * 操作按钮点击事件
 */
function onActionClick({ code, row }: OnActionClickParams<Feedback>) {
  switch (code) {
    case 'delete': {
      deleteFeedback(row.id).then(() => {
        message.success('删除成功');
        onRefresh();
      }).catch(() => {
        message.error('删除失败');
      });
      break;
    }
    case 'edit': {
      editFeedbackId.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
  }
}

/**
 * 触发 AI 聚类
 */
const clusteringLoading = ref(false);
const clusteringModalOpen = ref(false);
const clusteringTaskId = ref<string>('');
const clusteringTaskState = ref<'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'>('PENDING');
const clusteringTaskError = ref<string>('');

let clusteringPollTimer: number | null = null;

const clusteringProgress = computed(() => {
  switch (clusteringTaskState.value) {
    case 'PENDING':
      return 10;
    case 'STARTED':
      return 60;
    case 'RETRY':
      return 60;
    case 'SUCCESS':
      return 100;
    case 'FAILURE':
      return 100;
    default:
      return 0;
  }
});

const clusteringStep = computed(() => {
  switch (clusteringTaskState.value) {
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

function stopClusteringPoll() {
  if (clusteringPollTimer !== null) {
    window.clearInterval(clusteringPollTimer);
    clusteringPollTimer = null;
  }
}

function onClusteringModalCancel() {
  clusteringModalOpen.value = false;
  stopClusteringPoll();
}

onBeforeUnmount(() => {
  stopClusteringPoll();
});

async function pollClusteringTask(taskId: string) {
  const status = await getClusteringTaskStatus(taskId);
  clusteringTaskState.value = status.state;

  if (status.state === 'FAILURE') {
    stopClusteringPoll();
    clusteringLoading.value = false;
    clusteringTaskError.value = status.error || '任务执行失败';
    message.error(clusteringTaskError.value);
    return;
  }

  if (status.state === 'SUCCESS') {
    stopClusteringPoll();
    clusteringLoading.value = false;

    const result: any = status.result;
    if (!result) {
      message.warning('聚类任务完成，但未返回结果');
      return;
    }

    if (result.status === 'skipped') {
      message.warning(result.message || '聚类已跳过');
    } else {
      message.success(`聚类完成：创建 ${result.topics_created ?? 0} 个主题，噪声 ${result.noise_count ?? 0} 条`);
    }
    onRefresh();
  }
}

const handleTriggerClustering = async () => {
  try {
    clusteringLoading.value = true;
    clusteringModalOpen.value = true;
    clusteringTaskError.value = '';
    clusteringTaskState.value = 'PENDING';

    const resp: any = await triggerClustering({ async_mode: true });
    if (resp?.status === 'accepted' && resp?.task_id) {
      clusteringTaskId.value = resp.task_id;

      // 先拉一次，避免用户看到空转
      await pollClusteringTask(resp.task_id);
      clusteringPollTimer = window.setInterval(() => pollClusteringTask(resp.task_id), 2000);
      return;
    }

    // 兼容同步模式返回
    const result: any = resp;
    if (result?.status === 'skipped') {
      message.warning(result.message || '聚类已跳过');
    } else {
      message.success(`聚类完成：创建 ${result.topics_created ?? 0} 个主题，噪声 ${result.noise_count ?? 0} 条`);
    }
    onRefresh();
  } catch (error: any) {
    message.error(error.message || '聚类失败，请稍后重试');
  } finally {
    clusteringLoading.value = false;
  }
};

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: feedbackFormSchema,
});

const editFeedbackId = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  title: '编辑反馈',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await editFormApi.getValues<UpdateFeedbackParams>();
      try {
        await updateFeedback(editFeedbackId.value, data);
        message.success('更新成功');
        await editModalApi.close();
        onRefresh();
      } catch {
        message.error('更新失败');
      } finally {
        editModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<any>();
      editFormApi.resetForm();
      if (data) {
        editFormApi.setValues(data);
      }
    }
  },
});

/**
 * 新建表单
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: feedbackFormSchema,
});

const [addModal, addModalApi] = useVbenModal({
  title: '新建反馈',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateFeedbackParams>();
      try {
        await createFeedback(data);
        message.success('创建成功');
        await addModalApi.close();
        onRefresh();
      } catch {
        message.error('创建失败');
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      addFormApi.resetForm();
    }
  },
});

onMounted(() => {
  // 初始化加载数据
});
</script>

<template>
  <Grid>
    <template #toolbar-actions>
      <VbenButton @click="() => addModalApi.open()">
        <MaterialSymbolsAdd class="size-5" />
        新建反馈
      </VbenButton>
      <VbenButton
        variant="outline"
        @click="handleTriggerClustering"
        :loading="clusteringLoading"
      >
        <span class="iconify lucide--sparkles" />
        AI 智能聚类
      </VbenButton>
      <VbenButton variant="outline" @click="() => $router.push('/app/feedback/import')">
        <span class="iconify lucide--upload" />
        导入 Excel
      </VbenButton>
    </template>

    <template #topic="{ row }">
      <span v-if="row.topic_id && row.topic_title">
        <a-tag color="blue" style="cursor: pointer" @click="$router.push(`/app/topic/detail/${row.topic_id}`)">
          {{ row.topic_title }}
        </a-tag>
      </span>
      <span v-else class="text-gray-400">未聚类</span>
    </template>

    <template #clustering_status="{ row }">
      <a-tag v-if="row.clustering_status === 'processing'" color="blue">处理中</a-tag>
      <a-tag v-else-if="row.clustering_status === 'failed'" color="red">失败</a-tag>
      <a-tag v-else-if="row.clustering_status === 'pending'" color="default">待处理</a-tag>
      <a-tag
        v-else-if="row.clustering_status === 'clustered'"
        :color="row.topic_id ? 'green' : 'default'"
      >
        {{ row.topic_id ? '已归类' : '待观察' }}
      </a-tag>
      <span v-else class="text-gray-400">-</span>
    </template>

    <template #urgent="{ row }">
      <a-tag v-if="row.is_urgent" color="red">🔥 紧急</a-tag>
      <a-tag v-else color="default">📝 常规</a-tag>
    </template>
  </Grid>

  <!-- 编辑弹窗 -->
  <editModal>
    <EditForm />
  </editModal>

  <!-- 新建弹窗 -->
  <addModal>
    <AddForm />
  </addModal>

  <a-modal
    v-model:open="clusteringModalOpen"
    title="AI 智能聚类"
    :footer="null"
    :maskClosable="false"
    @cancel="onClusteringModalCancel"
  >
    <a-steps :current="clusteringStep" size="small">
      <a-step title="任务提交" />
      <a-step title="处理中" />
      <a-step title="完成" />
    </a-steps>

    <div class="mt-4">
      <a-progress :percent="clusteringProgress" :status="clusteringTaskState === 'FAILURE' ? 'exception' : 'active'" />
      <div class="text-gray-500 mt-2">
        <div v-if="clusteringTaskId">任务 ID：{{ clusteringTaskId }}</div>
        <div v-if="clusteringTaskError" class="text-red-500 mt-1">错误：{{ clusteringTaskError }}</div>
      </div>
    </div>
  </a-modal>
</template>

<style scoped>
/* 自定义样式 */
</style>
