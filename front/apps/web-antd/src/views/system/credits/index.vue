<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { message, Descriptions } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';

// 积分配置数据
const creditConfig = ref({
  feedback_submit: 10,
  screenshot_upload: 5,
  topic_create: 20,
  daily_login: 3,
  invite_user: 50,
});

const loading = ref(false);

// 加载配置
async function loadConfig() {
  loading.value = true;
  try {
    // TODO: 调用后端API获取配置
    // const data = await getCreditsConfig();
    // creditConfig.value = data;
    message.info('加载配置成功（模拟数据）');
  } catch (e) {
    message.error('加载配置失败');
  } finally {
    loading.value = false;
  }
}

// --- Form & Modal Definition ---

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: [
    {
      fieldName: 'feedback_submit',
      label: '提交反馈',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: '提交反馈获得的积分',
      },
      rules: 'required',
    },
    {
      fieldName: 'screenshot_upload',
      label: '上传截图',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: '上传截图获得的积分',
      },
      rules: 'required',
    },
    {
      fieldName: 'topic_create',
      label: '创建主题',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: '创建主题获得的积分',
      },
      rules: 'required',
    },
    {
      fieldName: 'daily_login',
      label: '每日登录',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: '每日登录获得的积分',
      },
      rules: 'required',
    },
    {
      fieldName: 'invite_user',
      label: '邀请用户',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: '邀请新用户获得的积分',
      },
      rules: 'required',
    },
  ],
});

const [Modal, modalApi] = useVbenModal({
  title: '编辑积分配置',
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      try {
        const values = await formApi.getValues();
        // TODO: 调用后端API保存配置
        // await updateCreditsConfig(values);
        creditConfig.value = values as any;
        message.success('更新成功');
        modalApi.close();
      } catch (e) {
        console.error(e);
        message.error('更新失败');
      } finally {
        modalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      // 设置初始值
      formApi.setValues(creditConfig.value);
    }
  },
});

function openEditModal() {
  modalApi.open();
}

onMounted(() => {
  loadConfig();
});
</script>

<template>
  <Page title="积分管理">
    <div class="p-4 bg-white dark:bg-[#151515]">
      <div class="bg-gray-50 dark:bg-black p-4 rounded border dark:border-gray-800">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">积分规则配置</h3>
          <VbenButton type="primary" @click="openEditModal">编辑配置</VbenButton>
        </div>

        <Descriptions bordered size="small" :column="2">
          <Descriptions.Item label="提交反馈">{{ creditConfig.feedback_submit }} 积分</Descriptions.Item>
          <Descriptions.Item label="上传截图">{{ creditConfig.screenshot_upload }} 积分</Descriptions.Item>
          <Descriptions.Item label="创建主题">{{ creditConfig.topic_create }} 积分</Descriptions.Item>
          <Descriptions.Item label="每日登录">{{ creditConfig.daily_login }} 积分</Descriptions.Item>
          <Descriptions.Item label="邀请用户">{{ creditConfig.invite_user }} 积分</Descriptions.Item>
        </Descriptions>

        <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            💡 提示：积分系统用于激励用户参与反馈和互动。可以根据实际需求调整各项积分奖励。
          </p>
        </div>
      </div>
    </div>
    <Modal>
      <Form />
    </Modal>
  </Page>
</template>
