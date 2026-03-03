<script lang="ts" setup>
/**
 * 完成步骤组件
 *
 * 功能：
 * 1. 显示创建成功信息
 * 2. 展示已创建的团队和看板信息
 * 3. 提供"开始使用"按钮
 */
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { Button, message, Result, Typography } from 'ant-design-vue';

import { useOnboardingStore } from '#/store';

defineOptions({ name: 'CompleteStep' });

const { Paragraph, Text } = Typography;

const router = useRouter();
const onboardingStore = useOnboardingStore();

const isCompleting = ref(false);

// 开始使用
async function handleStart() {
  isCompleting.value = true;

  try {
    const redirectPath = await onboardingStore.completeOnboarding();

    if (redirectPath) {
      message.success('欢迎使用回响！正在进入控制台...');

      // 短暂延迟让用户看到成功提示
      setTimeout(() => {
        router.replace(redirectPath);
      }, 1000);
    } else if (onboardingStore.error) {
      message.error(onboardingStore.error);
    }
  } finally {
    isCompleting.value = false;
  }
}
</script>

<template>
  <div class="complete-step">
    <Result status="success" class="success-result">
      <template #title>
        <span class="result-title">🎉 一切就绪！</span>
      </template>

      <template #subTitle>
        <span class="result-subtitle">
          您已成功创建团队和看板，现在可以开始收集用户反馈了
        </span>
      </template>

      <template #extra>
        <div class="completion-info">
          <!-- 创建的资源摘要 -->
          <div class="resource-summary">
            <div class="summary-item">
              <div class="summary-icon">🏢</div>
              <div class="summary-content">
                <Text strong>团队</Text>
                <Paragraph class="summary-value">
                  {{ onboardingStore.tenantData?.name || '已创建' }}
                </Paragraph>
              </div>
            </div>

            <div class="summary-divider"></div>

            <div class="summary-item">
              <div class="summary-icon">📋</div>
              <div class="summary-content">
                <Text strong>看板</Text>
                <Paragraph class="summary-value">
                  {{ onboardingStore.boardData?.name || '已创建' }}
                </Paragraph>
              </div>
            </div>
          </div>

          <!-- 下一步提示 -->
          <div class="next-steps">
            <Text type="secondary">接下来您可以：</Text>
            <ul class="steps-list">
              <li>📝 手动录入用户反馈</li>
              <li>📤 批量导入历史反馈数据</li>
              <li>🤖 使用 AI 自动分析和聚类反馈</li>
              <li>👥 邀请团队成员一起协作</li>
            </ul>
          </div>

          <!-- 开始使用按钮 -->
          <Button
            type="primary"
            size="large"
            :loading="isCompleting"
            class="start-button"
            @click="handleStart"
          >
            开始使用 →
          </Button>
        </div>
      </template>
    </Result>
  </div>
</template>

<style scoped>
.complete-step {
  padding: 20px 0;
}

.success-result {
  padding: 0;
}

.result-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f1f1f;
}

.result-subtitle {
  font-size: 16px;
  color: #666;
  display: inline-block;
  max-width: 500px;
}

.completion-info {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.resource-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 12px;
  margin-bottom: 24px;
  width: 100%;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-icon {
  font-size: 32px;
}

.summary-content {
  text-align: left;
}

.summary-value {
  margin: 0 !important;
  color: hsl(181, 84%, 32%);
  font-weight: 500;
}

.summary-divider {
  width: 1px;
  height: 48px;
  background: #e8e8e8;
}

.next-steps {
  text-align: left;
  padding: 16px 24px;
  background: rgba(13, 150, 137, 0.05);
  border-radius: 12px;
  margin-bottom: 24px;
  width: 100%;
}

.steps-list {
  margin: 12px 0 0 0;
  padding-left: 0;
  list-style: none;
}

.steps-list li {
  padding: 6px 0;
  color: #333;
  font-size: 14px;
}

.start-button {
  width: 100%;
  height: 52px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 8px;
}

:deep(.ant-result-icon) {
  margin-bottom: 16px;
}

:deep(.ant-result-icon .anticon) {
  font-size: 64px;
  color: hsl(181, 84%, 32%);
}
</style>
