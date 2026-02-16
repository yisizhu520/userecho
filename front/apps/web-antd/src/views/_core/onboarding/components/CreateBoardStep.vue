<script lang="ts" setup>
/**
 * 创建看板步骤组件
 *
 * 功能：
 * 1. 输入看板名称
 * 2. 输入看板描述（可选）
 * 3. 选择访问模式
 */
import { computed, reactive } from 'vue';

import {
  Alert,
  Button,
  Form,
  FormItem,
  Input,
  message,
  Radio,
  RadioGroup,
  Typography,
} from 'ant-design-vue';

import { useOnboardingStore } from '#/store';

defineOptions({ name: 'CreateBoardStep' });

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const onboardingStore = useOnboardingStore();

// 表单状态
const formState = reactive({
  name: '',
  description: '',
  access_mode: 'private' as 'private' | 'public' | 'restricted',
});

// 访问模式选项
const accessModeOptions = [
  {
    value: 'private',
    label: '仅内部可见',
    description: '只有团队成员可以查看和管理',
  },
  {
    value: 'public',
    label: '公开',
    description: '任何人都可以查看（需要登录才能提交反馈）',
  },
];

// 验证规则
const rules = {
  name: [
    { required: true, message: '请输入看板名称', trigger: 'blur' },
    {
      min: 2,
      max: 100,
      message: '名称长度应在 2-100 个字符之间',
      trigger: 'blur',
    },
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' },
  ],
};

// 是否可以提交
const canSubmit = computed(() => {
  return formState.name.length >= 2 && !onboardingStore.isLoading;
});

// 返回上一步
function handleBack() {
  onboardingStore.prevStep();
}

// 提交表单
async function handleSubmit() {
  if (!canSubmit.value) return;

  const success = await onboardingStore.createBoard({
    name: formState.name,
    description: formState.description || undefined,
    access_mode: formState.access_mode,
  });

  if (success) {
    message.success('看板创建成功！');
  } else if (onboardingStore.error) {
    message.error(onboardingStore.error);
  }
}
</script>

<template>
  <div class="create-board-step">
    <div class="step-header">
      <Title :level="3" class="step-title">创建第一个看板</Title>
      <Paragraph class="step-desc">
        看板用于收集和组织用户反馈，您可以按产品线、功能模块或渠道来分类
      </Paragraph>
    </div>

    <Form
      :model="formState"
      :rules="rules"
      layout="vertical"
      class="board-form"
    >
      <!-- 看板名称 -->
      <FormItem label="看板名称" name="name" required>
        <Input
          v-model:value="formState.name"
          placeholder="例如：产品反馈、移动端问题、客户建议"
          size="large"
          :maxlength="100"
          show-count
        />
        <Text type="secondary" class="field-hint">
          💡 建议：可以按产品、平台或用途来命名，如"iOS 端反馈"、"新功能建议"
        </Text>
      </FormItem>

      <!-- 看板描述 -->
      <FormItem label="看板描述" name="description">
        <template #label>
          <span>看板描述</span>
          <Text type="secondary" class="label-hint">（选填）</Text>
        </template>
        <TextArea
          v-model:value="formState.description"
          placeholder="简单描述这个看板的用途..."
          :rows="3"
          :maxlength="500"
          show-count
        />
      </FormItem>

      <!-- 访问模式 -->
      <FormItem label="访问权限" name="access_mode">
        <RadioGroup v-model:value="formState.access_mode" class="access-modes">
          <div
            v-for="option in accessModeOptions"
            :key="option.value"
            class="access-option"
            :class="{ selected: formState.access_mode === option.value }"
          >
            <Radio :value="option.value">
              <div class="option-content">
                <span class="option-label">{{ option.label }}</span>
                <span class="option-desc">{{ option.description }}</span>
              </div>
            </Radio>
          </div>
        </RadioGroup>
      </FormItem>

      <!-- 错误提示 -->
      <Alert
        v-if="onboardingStore.error"
        :message="onboardingStore.error"
        type="error"
        show-icon
        closable
        class="error-alert"
      />

      <!-- 操作按钮 -->
      <FormItem class="actions-item">
        <div class="form-actions">
          <Button size="large" @click="handleBack"> ← 返回上一步 </Button>
          <Button
            type="primary"
            size="large"
            :loading="onboardingStore.isLoading"
            :disabled="!canSubmit"
            @click="handleSubmit"
          >
            创建看板
          </Button>
        </div>
      </FormItem>
    </Form>
  </div>
</template>

<style scoped>
.create-board-step {
  padding: 20px 0;
}

.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-title {
  margin-bottom: 8px !important;
  color: #1f1f1f;
}

.step-desc {
  color: #666;
  margin-bottom: 0 !important;
}

.board-form {
  max-width: 450px;
  margin: 0 auto;
}

.label-hint {
  margin-left: 8px;
  font-size: 12px;
}

.field-hint {
  display: block;
  margin-top: 8px;
  font-size: 12px;
}

.access-modes {
  width: 100%;
}

.access-option {
  padding: 12px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.access-option:hover {
  border-color: #667eea;
}

.access-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.access-option:last-child {
  margin-bottom: 0;
}

.option-content {
  display: flex;
  flex-direction: column;
}

.option-label {
  font-weight: 500;
  color: #1f1f1f;
}

.option-desc {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.error-alert {
  margin-bottom: 16px;
}

.actions-item {
  margin-top: 24px;
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.form-actions .ant-btn {
  flex: 1;
  height: 48px;
  font-size: 15px;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
}

:deep(.ant-btn-primary:hover) {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
}

:deep(.ant-radio-wrapper) {
  width: 100%;
}
</style>
