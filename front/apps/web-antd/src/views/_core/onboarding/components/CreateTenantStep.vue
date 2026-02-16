<script lang="ts" setup>
/**
 * 创建团队步骤组件
 *
 * 功能：
 * 1. 输入公司/团队名称
 * 2. 自动生成并可编辑 URL 标识 (slug)
 * 3. 验证 slug 可用性
 */
import { computed, reactive, ref, watch } from 'vue';

import {
  Alert,
  Button,
  Form,
  FormItem,
  Input,
  message,
  Typography,
} from 'ant-design-vue';
import { debounce } from 'lodash-es';

import { useOnboardingStore } from '#/store';

defineOptions({ name: 'CreateTenantStep' });

const { Title, Paragraph, Text } = Typography;

const onboardingStore = useOnboardingStore();

// 表单状态
const formState = reactive({
  name: '',
  slug: '',
});

// Slug 验证状态
const slugStatus = ref<'idle' | 'checking' | 'available' | 'unavailable'>(
  'idle',
);
const slugSuggestion = ref<string | null>(null);
const isSlugManuallyEdited = ref(false);

// 验证规则
const rules = {
  name: [
    { required: true, message: '请输入公司或团队名称', trigger: 'blur' },
    { min: 2, max: 100, message: '名称长度应在 2-100 个字符之间', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: '请输入 URL 标识', trigger: 'blur' },
    { min: 2, max: 100, message: 'URL 标识长度应在 2-100 个字符之间', trigger: 'blur' },
    {
      pattern: /^[a-z\d][a-z\d-]*[a-z\d]$|^[a-z\d]$/,
      message: '只能包含小写字母、数字和连字符，且不能以连字符开头或结尾',
      trigger: 'blur',
    },
  ],
};

// 是否可以提交
const canSubmit = computed(() => {
  return (
    formState.name.length >= 2 &&
    formState.slug.length >= 2 &&
    slugStatus.value === 'available' &&
    !onboardingStore.isLoading
  );
});

// 当名称变化时自动生成 slug
watch(
  () => formState.name,
  async (newName) => {
    if (!isSlugManuallyEdited.value && newName) {
      const slug = await onboardingStore.generateSlug(newName);
      formState.slug = slug;
      // 检查生成的 slug 可用性
      checkSlugAvailability(slug);
    }
  },
);

// 检查 slug 可用性（防抖）
const checkSlugAvailability = debounce(async (slug: string) => {
  if (!slug || slug.length < 2) {
    slugStatus.value = 'idle';
    return;
  }

  slugStatus.value = 'checking';
  const result = await onboardingStore.checkSlugAvailable(slug);

  if (result.available) {
    slugStatus.value = 'available';
    slugSuggestion.value = null;
  } else {
    slugStatus.value = 'unavailable';
    slugSuggestion.value = result.suggestion;
  }
}, 500);

// 当用户手动编辑 slug 时
function onSlugInput() {
  isSlugManuallyEdited.value = true;
  checkSlugAvailability(formState.slug);
}

// 使用建议的 slug
function useSuggestion() {
  if (slugSuggestion.value) {
    formState.slug = slugSuggestion.value;
    isSlugManuallyEdited.value = true;
    checkSlugAvailability(slugSuggestion.value);
  }
}

// 提交表单
async function handleSubmit() {
  if (!canSubmit.value) return;

  const success = await onboardingStore.createTenant({
    name: formState.name,
    slug: formState.slug,
  });

  if (success) {
    message.success('团队创建成功！');
  } else if (onboardingStore.error) {
    message.error(onboardingStore.error);
  }
}
</script>

<template>
  <div class="create-tenant-step">
    <div class="step-header">
      <Title :level="3" class="step-title">创建您的团队</Title>
      <Paragraph class="step-desc">
        输入您的公司或团队名称，开始使用回响管理用户反馈
      </Paragraph>
    </div>

    <Form
      :model="formState"
      :rules="rules"
      layout="vertical"
      class="tenant-form"
    >
      <!-- 团队名称 -->
      <FormItem label="公司/团队名称" name="name" required>
        <Input
          v-model:value="formState.name"
          placeholder="例如：某科技有限公司、产品研发部"
          size="large"
          :maxlength="100"
          show-count
        />
      </FormItem>

      <!-- URL 标识 -->
      <FormItem name="slug" required>
        <template #label>
          <span>URL 标识</span>
          <Text type="secondary" class="label-hint">（用于访问链接）</Text>
        </template>

        <Input
          v-model:value="formState.slug"
          placeholder="例如：acme-tech"
          size="large"
          :maxlength="100"
          @input="onSlugInput"
        >
          <template #addonAfter>
            <span class="slug-suffix">.feedalyze.com</span>
          </template>
        </Input>

        <!-- Slug 状态提示 -->
        <div class="slug-status">
          <div v-if="slugStatus === 'checking'" class="status-checking">
            <span class="status-icon">⏳</span>
            <Text type="secondary">正在检查可用性...</Text>
          </div>
          <div v-else-if="slugStatus === 'available'" class="status-available">
            <span class="status-icon">✅</span>
            <Text type="success">该标识可用</Text>
          </div>
          <div
            v-else-if="slugStatus === 'unavailable'"
            class="status-unavailable"
          >
            <span class="status-icon">❌</span>
            <Text type="danger">该标识已被使用</Text>
            <Button
              v-if="slugSuggestion"
              type="link"
              size="small"
              @click="useSuggestion"
            >
              使用 {{ slugSuggestion }}
            </Button>
          </div>
        </div>
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

      <!-- 提交按钮 -->
      <FormItem class="submit-item">
        <Button
          type="primary"
          size="large"
          block
          :loading="onboardingStore.isLoading"
          :disabled="!canSubmit"
          @click="handleSubmit"
        >
          创建团队并继续
        </Button>
      </FormItem>
    </Form>
  </div>
</template>

<style scoped>
.create-tenant-step {
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

.tenant-form {
  max-width: 400px;
  margin: 0 auto;
}

.label-hint {
  margin-left: 8px;
  font-size: 12px;
}

.slug-suffix {
  color: #999;
  font-size: 13px;
}

.slug-status {
  margin-top: 8px;
  min-height: 24px;
}

.slug-status > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 14px;
}

.error-alert {
  margin-bottom: 16px;
}

.submit-item {
  margin-top: 24px;
  margin-bottom: 0;
}

:deep(.ant-btn-primary) {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}
</style>
