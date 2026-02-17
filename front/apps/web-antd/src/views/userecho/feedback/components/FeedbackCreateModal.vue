<script setup lang="ts">
import { ref, computed } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { message } from 'ant-design-vue';
import { createFeedback } from '#/api';
import { getBoardList } from '#/api/userecho/board';
import type { CreateFeedbackParams } from '#/api';
import { feedbackFormSchema } from '#/views/userecho/feedback/data';
import ScreenshotUpload from './ScreenshotUpload.vue';
import SimilarTopicsPanel from './SimilarTopicsPanel.vue';

interface Emits {
  (e: 'success'): void;
}

const emit = defineEmits<Emits>();

const selectedTopicId = ref<string>('');
const uploadedScreenshots = ref<string[]>([]);
const currentTitle = ref<string>('');

// 将表单字段拆分为两组
const topFormSchema = computed(() => feedbackFormSchema.slice(0, 2)); // 看板 + 反馈内容
const bottomFormSchema = computed(() => feedbackFormSchema.slice(2)); // 客户信息等其余字段

// 创建两个独立的表单实例
const [TopForm, topFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: topFormSchema.value,
});

const [BottomForm, bottomFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: bottomFormSchema.value,
});

const [Modal, modalApi] = useVbenModal({
  title: '新建反馈',
  destroyOnClose: true,
  class: 'w-[1000px]',
  async onConfirm() {
    // 验证两个表单
    const topValid = await topFormApi.validate();
    const bottomValid = await bottomFormApi.validate();
    if (topValid.valid && bottomValid.valid) {
      await handleCreate(false);
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      topFormApi.resetForm();
      bottomFormApi.resetForm();
      selectedTopicId.value = '';
      uploadedScreenshots.value = [];
      currentTitle.value = '';
      loadBoardList();
    }
  },
});

// 加载 Board 列表
const loadBoardList = async () => {
  try {
    const response = await getBoardList();
    const boardList = response.boards.map((board: any) => ({
      label: board.name,
      value: board.id,
    }));
    
    // 更新顶部表单的 board_id 字段选项
    topFormApi.updateSchema([
      {
        fieldName: 'board_id',
        componentProps: {
          options: boardList,
        },
      },
    ]);
  } catch (error: any) {
    message.error('加载 Board 列表失败');
  }
};

// 创建反馈
const handleCreate = async (continueCreating: boolean) => {
  try {
    modalApi.lock();
    // 合并两个表单的数据
    const topData = await topFormApi.getValues();
    const bottomData = await bottomFormApi.getValues();
    const data = { ...topData, ...bottomData } as CreateFeedbackParams;
    
    // 验证：客户名称和匿名作者至少填写一个
    if (!data.customer_name && !data.anonymous_author) {
      message.error('客户名称和匿名作者至少填写一个');
      return;
    }
    
    // 添加 Topic 关联和截图
    if (selectedTopicId.value) {
      data.topic_id = selectedTopicId.value;
    }
    if (uploadedScreenshots.value.length > 0) {
      data.screenshots = uploadedScreenshots.value;
    }
    
    await createFeedback(data);
    message.success('创建成功');
    emit('success');
    
    if (continueCreating) {
      // 重置表单但保持弹窗打开
      topFormApi.resetForm();
      bottomFormApi.resetForm();
      selectedTopicId.value = '';
      uploadedScreenshots.value = [];
      currentTitle.value = '';
    } else {
      await modalApi.close();
    }
  } catch {
    message.error('创建失败');
  } finally {
    modalApi.unlock();
  }
};

// 创建并继续
const handleCreateAndContinue = async () => {
  const topValid = await topFormApi.validate();
  const bottomValid = await bottomFormApi.validate();
  if (topValid.valid && bottomValid.valid) {
    await handleCreate(true);
  }
};

// 监听表单值变化
const handleValuesChange = (changedValues: any) => {
  if (changedValues.content !== undefined) {
    currentTitle.value = changedValues.content;
  }
};

// 暴露 API 给父组件
defineExpose({
  open: () => modalApi.open(),
  close: () => modalApi.close(),
});
</script>

<template>
  <Modal>
    <div class="feedback-create-layout">
      <a-row :gutter="24">
        <!-- 左侧表单区域 -->
        <a-col :span="14">
          <div class="left-content-area">
            <!-- 顶部表单：看板 + 反馈内容 -->
            <TopForm @values-change="handleValuesChange" />
            
            <!-- 截图上传组件 -->
            <div class="screenshot-upload-section">
              <ScreenshotUpload v-model="uploadedScreenshots" />
            </div>
            
            <!-- 底部表单：客户信息等其余字段 -->
            <BottomForm />
          </div>
        </a-col>
        
        <!-- 右侧相似主题面板 -->
        <a-col :span="10">
          <SimilarTopicsPanel
            :search-title="currentTitle"
            v-model:selected-topic-id="selectedTopicId"
          />
        </a-col>
      </a-row>
    </div>
    
    <template #footer>
      <div class="modal-footer-actions">
        <VbenButton @click="() => modalApi.close()">取消</VbenButton>
        <VbenButton @click="handleCreateAndContinue">创建并继续</VbenButton>
        <VbenButton type="primary" @click="() => modalApi.onConfirm?.()">创建</VbenButton>
      </div>
    </template>
  </Modal>
</template>

<style scoped>
.feedback-create-layout {
  padding: 0;
}

.left-content-area {
  height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

/* 截图上传区域 - 与表单字段对齐 */
.screenshot-upload-section {
  margin: 16px 0;
}

/* 覆盖 ScreenshotUpload 组件的样式，使其与表单字段对齐 */
.screenshot-upload-section :deep(.screenshot-upload-section) {
  display: flex;
  align-items: flex-start;
  gap: 9px; /* 与标准表单字段的间距一致 */
}

.screenshot-upload-section :deep(.upload-label) {
  width: 100px; /* 与标准表单 label 宽度一致 */
  flex-shrink: 0;
  text-align: right;
  font-weight: 500;
  padding-top: 4px;
  line-height: 1.5;
}

.screenshot-upload-section :deep(.upload-content) {
  flex: 1;
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0 0 0;
}
</style>
