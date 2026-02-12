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

import { ref, onMounted } from 'vue';

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
} from '#/api';
import {
  querySchema,
  useColumns,
  feedbackFormSchema,
} from '#/views/feedalyze/feedback/data';

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
        return await getFeedbackList({
          skip: (page.currentPage - 1) * page.pageSize,
          limit: page.pageSize,
          ...formValues,
        });
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
const handleTriggerClustering = async () => {
  try {
    clusteringLoading.value = true;
    const result = await triggerClustering();
    message.success(`聚类完成！创建了 ${result.topics_created} 个需求主题`);
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
</template>

<style scoped>
/* 自定义样式 */
</style>
