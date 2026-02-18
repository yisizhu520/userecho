<script lang="ts" setup>
/**
 * 引导流程主页面
 *
 * 功能：
 * 1. 显示步骤进度条
 * 2. 根据当前步骤渲染对应组件
 * 3. 管理步骤间的切换
 */
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { Card, Spin } from 'ant-design-vue';

import { useOnboardingStore } from '#/store';

import CompleteStep from './components/CompleteStep.vue';
import CreateBoardStep from './components/CreateBoardStep.vue';
import CreateTenantStep from './components/CreateTenantStep.vue';
import StepProgress from './components/StepProgress.vue';

defineOptions({ name: 'OnboardingPage' });

const router = useRouter();
const onboardingStore = useOnboardingStore();

// 步骤组件映射
const stepComponents = {
  'create-tenant': CreateTenantStep,
  'create-board': CreateBoardStep,
  complete: CompleteStep,
};

// 当前步骤组件
const currentStepComponent = computed(() => {
  const stepId = onboardingStore.currentStepId;
  return stepId ? stepComponents[stepId as keyof typeof stepComponents] : null;
});

// 初始化
onMounted(async () => {
  // 检查是否需要引导
  const needsOnboarding = await onboardingStore.checkOnboardingStatus();

  if (!needsOnboarding) {
    // 不需要引导，跳转到首页
    router.replace('/');
  }
});
</script>

<template>
  <div class="onboarding-page">
    <!-- 品牌标识 -->
    <div class="brand-header">
      <div class="brand-logo">
        <span class="logo-icon">📊</span>
        <span class="logo-text">回响</span>
      </div>
      <p class="brand-subtitle">AI 驱动的用户反馈智能分析平台</p>
    </div>

    <!-- 主内容区 -->
    <div class="onboarding-content">
      <Spin :spinning="onboardingStore.isLoading" size="large">
        <Card class="step-card" :bordered="false">
          <!-- 步骤进度条 -->
          <StepProgress
            :steps="onboardingStore.steps"
            :current-index="onboardingStore.currentStepIndex"
            class="step-progress"
          />

          <!-- 步骤内容 -->
          <div class="step-content">
            <component :is="currentStepComponent" v-if="currentStepComponent" />
            <div v-else class="loading-placeholder">
              <Spin tip="加载中..." />
            </div>
          </div>
        </Card>
      </Spin>
    </div>

    <!-- 底部信息 -->
    <div class="footer-info">
      <p>© 2025 回响 userecho. 让每一条反馈都有价值。</p>
    </div>
  </div>
</template>

<style scoped>
.onboarding-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f5f7f9;
  padding: 40px 20px;
}

.brand-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.logo-icon {
  font-size: 40px;
}

.logo-text {
  font-size: 36px;
  font-weight: 700;
  color: #1f1f1f;
  letter-spacing: 2px;
}

.brand-subtitle {
  margin-top: 8px;
  color: #666;
  font-size: 16px;
}

.onboarding-content {
  width: 100%;
  max-width: 600px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.step-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  padding: 24px;
}

.step-progress {
  margin-bottom: 32px;
}

.step-content {
  min-height: 300px;
}

.loading-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.footer-info {
  margin-top: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.footer-info p {
  margin: 0;
}
</style>
