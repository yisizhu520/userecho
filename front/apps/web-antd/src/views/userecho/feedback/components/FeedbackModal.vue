<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { message } from 'ant-design-vue';
import { createFeedback, updateFeedback } from '#/api';
import { useBoardStore } from '#/store';
import type { CreateFeedbackParams, UpdateFeedbackParams, Customer, Feedback } from '#/api';
import { feedbackFormSchema } from '#/views/userecho/feedback/data';
import ScreenshotUpload from './ScreenshotUpload.vue';
import SimilarTopicsPanel from './SimilarTopicsPanel.vue';
import CustomerAutoComplete from './CustomerAutoComplete.vue';

interface Emits {
  (e: 'success', boardId?: string): void;
}

const emit = defineEmits<Emits>();

// 模式控制
const mode = ref<'create' | 'edit'>('create');
const editingFeedback = ref<Feedback | null>(null);

const isCreateMode = computed(() => mode.value === 'create');
const isEditMode = computed(() => mode.value === 'edit');

const selectedTopicId = ref<string>('');
const screenshotUploadRef = ref<InstanceType<typeof ScreenshotUpload> | null>(null);
const currentTitle = ref<string>('');

// 客户信息
const customerName = ref<string>('');
const customerType = ref<string>('normal');
const selectedCustomer = ref<Customer | null>(null);

// localStorage key for remembering the last selected board
const LAST_SELECTED_BOARD_KEY = 'feedback_create_last_board_id';

// 将表单字段拆分为两组
const topFormSchema = computed(() => feedbackFormSchema.slice(0, 2)); // 看板 + 反馈内容
const bottomFormSchema = computed(() => feedbackFormSchema.slice(2)); // is_urgent 等其余字段

// 监听表单值变化的回调
const handleValuesChange = (values: Record<string, any>, changedFields: string[]) => {
  if (changedFields.includes('content')) {
    currentTitle.value = values.content || '';
  }
  // 记住用户选择的看板（仅创建模式）
  if (isCreateMode.value && changedFields.includes('board_id') && values.board_id) {
    localStorage.setItem(LAST_SELECTED_BOARD_KEY, values.board_id);
  }
};

// 创建两个独立的表单实例
const [TopForm, topFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: topFormSchema.value,
  handleValuesChange,
});

const [BottomForm, bottomFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: bottomFormSchema.value,
});

// Modal 标题
const modalTitle = computed(() => isCreateMode.value ? '新建反馈' : '编辑反馈');

const [Modal, modalApi] = useVbenModal({
  title: modalTitle,
  destroyOnClose: true,
  class: 'w-[1000px]',
  async onConfirm() {
    // 验证表单
    const topValid = await topFormApi.validate();
    const bottomValid = await bottomFormApi.validate();
    
    // 创建模式需要验证客户名称
    if (isCreateMode.value) {
      const customerValid = customerName.value.trim().length > 0;
      if (!customerValid) {
        message.warning('请输入客户名称');
        return;
      }
    }
    
    if (topValid.valid && bottomValid.valid) {
      await handleSubmit(false);
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      topFormApi.resetForm();
      bottomFormApi.resetForm();
      selectedTopicId.value = '';
      screenshotUploadRef.value?.reset();
      currentTitle.value = '';
      customerName.value = '';
      customerType.value = 'normal';
      selectedCustomer.value = null;
      loadBoardList();
      
      // 编辑模式：填充初始数据
      if (isEditMode.value && editingFeedback.value) {
        const data = editingFeedback.value;
        topFormApi.setValues({
          board_id: data.board_id,
          content: data.content,
        });
        bottomFormApi.setValues({
          is_urgent: data.is_urgent,
        });
        currentTitle.value = data.content || '';
        customerName.value = data.customer_name || '';
        // 填充现有的主题关联
        selectedTopicId.value = data.topic_id || '';
        // 填充现有的图片（使用 nextTick 确保组件已挂载）
        if (data.images_metadata?.images && data.images_metadata.images.length > 0) {
          const urls = data.images_metadata.images.map((img: { url: string }) => img.url);
          nextTick(() => {
            screenshotUploadRef.value?.initWithUrls(urls);
          });
        }
      }
    }
  },
});

// Board Store
const boardStore = useBoardStore();

// 加载 Board 列表
const loadBoardList = async () => {
  try {
    await boardStore.refreshBoards();
    const boardList = boardStore.boards.map((board: any) => ({
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

    // 创建模式：智能选择默认看板
    if (isCreateMode.value && boardList.length > 0) {
      const lastSelectedBoardId = localStorage.getItem(LAST_SELECTED_BOARD_KEY);
      const boardExists = lastSelectedBoardId && boardList.some((b: { value: string }) => b.value === lastSelectedBoardId);
      const defaultBoardId = boardExists ? lastSelectedBoardId : boardList[0].value;
      topFormApi.setValues({ board_id: defaultBoardId });
    }
  } catch (error: any) {
    message.error('加载 Board 列表失败');
  }
};

// 提交处理
const handleSubmit = async (continueCreating: boolean) => {
  try {
    modalApi.lock();
    const topData = await topFormApi.getValues();
    const bottomData = await bottomFormApi.getValues();
    
    if (isCreateMode.value) {
      // 创建模式
      const data = { ...topData, ...bottomData } as CreateFeedbackParams;
      
      // 添加客户信息
      data.customer_name = customerName.value;
      if (!selectedCustomer.value) {
        data.customer_type = customerType.value;
      }
      
      // 添加 Topic 关联
      if (selectedTopicId.value) {
        data.topic_id = selectedTopicId.value;
      }
      
      // 上传截图
      if (screenshotUploadRef.value?.hasFiles) {
        const urls = await screenshotUploadRef.value.uploadAll();
        if (urls.length > 0) {
          data.screenshots = urls;
        }
      }
      
      await createFeedback(data);
      message.success('创建成功');
      emit('success', data.board_id);
      boardStore.forceRefresh();
      
      if (continueCreating) {
        // 重置表单但保持弹窗打开
        topFormApi.resetForm();
        bottomFormApi.resetForm();
        selectedTopicId.value = '';
        screenshotUploadRef.value?.reset();
        currentTitle.value = '';
        customerName.value = '';
        customerType.value = 'normal';
        selectedCustomer.value = null;
      } else {
        await modalApi.close();
      }
    } else {
      // 编辑模式
      if (!editingFeedback.value) {
        message.error('缺少反馈数据');
        return;
      }
      
      const data = { ...topData, ...bottomData } as UpdateFeedbackParams;
      // 添加主题关联更新
      if (selectedTopicId.value) {
        data.topic_id = selectedTopicId.value;
      } else {
        data.topic_id = null;  // 清除关联
      }
      // 添加客户名称更新
      data.customer_name = customerName.value;
      // 上传截图
      if (screenshotUploadRef.value?.hasFiles) {
        const urls = await screenshotUploadRef.value.uploadAll();
        if (urls.length > 0) {
          data.screenshots = urls;
        }
      }
      await updateFeedback(editingFeedback.value.id, data);
      message.success('更新成功');
      emit('success');
      await modalApi.close();
    }
  } catch {
    message.error(isCreateMode.value ? '创建失败' : '更新失败');
  } finally {
    modalApi.unlock();
  }
};

// 创建并继续
const handleCreateAndContinue = async () => {
  const topValid = await topFormApi.validate();
  const bottomValid = await bottomFormApi.validate();
  const customerValid = customerName.value.trim().length > 0;
  if (!customerValid) {
    message.warning('请输入客户名称');
    return;
  }
  if (topValid.valid && bottomValid.valid) {
    await handleSubmit(true);
  }
};

// 客户选择回调
const onCustomerSelected = (customer: Customer | null) => {
  selectedCustomer.value = customer;
};

// 暴露 API 给父组件
defineExpose({
  openCreate: () => {
    mode.value = 'create';
    editingFeedback.value = null;
    modalApi.open();
  },
  openEdit: (feedback: Feedback) => {
    mode.value = 'edit';
    editingFeedback.value = feedback;
    modalApi.open();
  },
  close: () => modalApi.close(),
});
</script>

<template>
  <Modal>
    <div class="feedback-modal-layout">
      <a-row :gutter="24">
        <!-- 左侧表单区域 -->
        <a-col :span="14">
          <div class="left-content-area">
            <!-- 顶部表单：看板 + 反馈内容 -->
            <TopForm />
            
            <!-- 截图上传组件 -->
            <div class="screenshot-upload-section">
              <ScreenshotUpload ref="screenshotUploadRef" />
            </div>
            
            <!-- 客户名称 -->
            <div class="customer-field">
              <label class="customer-label">客户名称</label>
              <div class="customer-input">
                <CustomerAutoComplete
                  v-model="customerName"
                  v-model:customer-type="customerType"
                  placeholder="输入客户名称"
                  @customer-selected="onCustomerSelected"
                />
              </div>
            </div>
            
            <!-- 底部表单：紧急标记等 -->
            <BottomForm />
          </div>
        </a-col>
        
        <!-- 右侧相似主题面板（创建和编辑模式都显示） -->
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
        <template v-if="isCreateMode">
          <VbenButton @click="handleCreateAndContinue">创建并继续</VbenButton>
          <VbenButton type="primary" @click="() => modalApi.onConfirm?.()">创建</VbenButton>
        </template>
        <template v-else>
          <VbenButton type="primary" @click="() => modalApi.onConfirm?.()">保存</VbenButton>
        </template>
      </div>
    </template>
  </Modal>
</template>

<style scoped>
.feedback-modal-layout {
  padding: 0;
}

.left-content-area {
  max-height: 600px;
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
  gap: 9px;
}

.screenshot-upload-section :deep(.upload-label) {
  width: 100px;
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

/* 客户名称字段 - 与表单布局对齐 */
.customer-field {
  display: flex;
  align-items: center;  /* 垂直居中对齐 */
  gap: 8px;
  margin-bottom: 16px;
}

.customer-label {
  width: 100px;
  flex-shrink: 0;
  text-align: right;
  font-weight: 500;
  line-height: 1.5;
}

.customer-label::before {
  content: '* ';
  color: #ff4d4f;
}

.customer-input {
  flex: 1;
}

.customer-readonly {
  display: inline-block;
  line-height: 1.5;
  color: hsl(var(--foreground));
}
</style>
