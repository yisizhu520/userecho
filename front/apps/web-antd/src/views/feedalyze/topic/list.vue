<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Topic,
  CreateTopicParams,
  UpdateTopicParams,
} from '#/api';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getTopicList,
  createTopic,
  updateTopic,
  TOPIC_STATUSES,
} from '#/api';
import {
  querySchema,
  useColumns,
  topicFormSchema,
  getStatusConfig,
  getCategoryConfig,
  categoryIcons,
} from '#/views/feedalyze/topic/data';

const router = useRouter();

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
const gridOptions: VxeTableGridOptions<Topic> = {
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
        const data = await getTopicList({
          skip: (page.currentPage - 1) * page.pageSize,
          limit: page.pageSize,
          ...formValues,
        });
        // vxe-table 期望的返回格式（根据全局 response 配置）
        return {
          items: data,           // 数据数组
          total: data.length,    // 当前查询到的记录数
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
function onActionClick({ code, row }: OnActionClickParams<Topic>) {
  switch (code) {
    case 'detail': {
      router.push(`/app/topic/detail/${row.id}`);
      break;
    }
    case 'edit': {
      editTopicId.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
    case 'delete': {
      // TODO: 实现删除逻辑
      message.info('删除功能待实现');
      break;
    }
  }
}

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: topicFormSchema,
});

const editTopicId = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  title: '编辑主题',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await editFormApi.getValues<UpdateTopicParams>();
      try {
        await updateTopic(editTopicId.value, data);
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
  schema: topicFormSchema,
});

const [addModal, addModalApi] = useVbenModal({
  title: '新建主题',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateTopicParams>();
      try {
        await createTopic(data);
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
</script>

<template>
  <Grid>
    <template #toolbar-actions>
      <VbenButton @click="() => addModalApi.open()">
        <MaterialSymbolsAdd class="size-5" />
        手动创建主题
      </VbenButton>
      <VbenButton variant="outline" @click="() => router.push('/app/feedback/list')">
        <span class="iconify lucide--inbox" />
        查看反馈列表
      </VbenButton>
    </template>

    <!-- 主题标题（带 AI 标识） -->
    <template #title="{ row }">
      <div class="topic-title">
        <span>{{ row.title }}</span>
        <a-tag v-if="row.ai_generated" color="purple" size="small" class="ml-2">
          <span class="iconify lucide--sparkles" /> AI
        </a-tag>
      </div>
    </template>

    <!-- 分类 -->
    <template #category="{ row }">
      <a-tag :color="getCategoryConfig(row.category).value === 'bug' ? 'red' : 'blue'">
        {{ categoryIcons[row.category] || '' }}
        {{ getCategoryConfig(row.category).label }}
      </a-tag>
    </template>

    <!-- 状态 -->
    <template #status="{ row }">
      <a-tag :color="getStatusConfig(row.status).color">
        {{ getStatusConfig(row.status).label }}
      </a-tag>
    </template>

    <!-- 反馈数量 -->
    <template #feedback_count="{ row }">
      <a-badge 
        :count="row.feedback_count" 
        :number-style="{ backgroundColor: '#52c41a' }"
        style="cursor: pointer"
        @click="router.push(`/app/topic/detail/${row.id}`)"
      />
    </template>

    <!-- AI 生成标识 -->
    <template #ai_generated="{ row }">
      <a-tag v-if="row.ai_generated" color="purple">
        <span class="iconify lucide--sparkles" /> AI
      </a-tag>
      <a-tag v-else color="default">手动</a-tag>
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
.topic-title {
  display: flex;
  align-items: center;
}
</style>
