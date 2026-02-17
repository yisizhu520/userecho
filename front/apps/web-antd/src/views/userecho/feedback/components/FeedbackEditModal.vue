<script setup lang="ts">
import { ref, watch } from 'vue';
import { useVbenModal } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { message } from 'ant-design-vue';
import { updateFeedback } from '#/api';
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
