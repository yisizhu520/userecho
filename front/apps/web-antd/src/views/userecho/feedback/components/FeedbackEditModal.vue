<script setup lang="ts">
import { ref, watch } from 'vue';
import { useVbenModal } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { message } from 'ant-design-vue';
import { updateFeedback } from '#/api';
import { getBoardList } from '#/api/userecho/board';
import type { UpdateFeedbackParams, Feedback } from '#/api';
import { feedbackFormSchema } from '#/views/userecho/feedback/data';

interface Props {
  feedbackId: string;
  initialData?: Feedback;
}

interface Emits {
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const [Form, formApi] = useVbenForm({
  showDefaultActions: false,
  schema: feedbackFormSchema,
});

// 加载 Board 列表
const loadBoardList = async () => {
  try {
    const response = await getBoardList();
    const boardList = response.boards.map((board: any) => ({
      label: board.name,
      value: board.id,
    }));
    
    // 更新表单 Schema 中的 Board 选项
    const boardField = feedbackFormSchema.find(f => f.fieldName === 'board_id');
    if (boardField && boardField.componentProps) {
      (boardField.componentProps as any).options = boardList;
    }
  } catch (error: any) {
    message.error('加载 Board 列表失败');
  }
};

const [Modal, modalApi] = useVbenModal({
  title: '编辑反馈',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      const data = await formApi.getValues<UpdateFeedbackParams>();
      try {
        await updateFeedback(props.feedbackId, data);
        message.success('更新成功');
        await modalApi.close();
        emit('success');
      } catch {
        message.error('更新失败');
      } finally {
        modalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      formApi.resetForm();
      loadBoardList();
      if (props.initialData) {
        formApi.setValues(props.initialData);
      }
    }
  },
});

// 暴露 API 给父组件
defineExpose({
  open: (data?: Feedback) => {
    if (data) {
      modalApi.setData(data);
    }
    modalApi.open();
  },
  close: () => modalApi.close(),
});
</script>

<template>
  <Modal>
    <Form />
  </Modal>
</template>
