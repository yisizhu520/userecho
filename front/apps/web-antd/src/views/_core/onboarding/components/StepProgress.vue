<script lang="ts" setup>
/**
 * 步骤进度条组件
 *
 * 显示引导流程的步骤进度
 */
import type { OnboardingStep } from '#/store';

import { computed } from 'vue';

import { CheckOutlined } from '@ant-design/icons-vue';

interface Props {
  steps: OnboardingStep[];
  currentIndex: number;
}

const props = defineProps<Props>();

// 计算进度
const progressPercent = computed(() => {
  return ((props.currentIndex + 1) / props.steps.length) * 100;
});
</script>

<template>
  <div class="step-progress">
    <div class="steps-container">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="step-item"
        :class="{
          active: index === currentIndex,
          completed: index < currentIndex,
          pending: index > currentIndex,
        }"
      >
        <!-- 步骤圆点 -->
        <div class="step-dot">
          <CheckOutlined v-if="index < currentIndex" class="check-icon" />
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>

        <!-- 步骤标题 -->
        <div class="step-info">
          <span class="step-name">{{ step.name }}</span>
        </div>

        <!-- 连接线 -->
        <div v-if="index < steps.length - 1" class="step-connector">
          <div
            class="connector-line"
            :class="{ filled: index < currentIndex }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: `${progressPercent}%` }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.step-progress {
  padding: 0 20px;
}

.steps-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: relative;
  margin-bottom: 16px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  z-index: 1;
  background: #fff;
}

.step-item.pending .step-dot {
  border: 2px solid #d9d9d9;
  color: #999;
}

.step-item.active .step-dot {
  border: 2px solid #667eea;
  color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2);
}

.step-item.completed .step-dot {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
}

.check-icon {
  font-size: 16px;
}

.step-number {
  font-size: 14px;
}

.step-info {
  margin-top: 12px;
  text-align: center;
}

.step-name {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.step-item.active .step-name {
  color: #667eea;
  font-weight: 600;
}

.step-item.completed .step-name {
  color: #52c41a;
}

.step-connector {
  position: absolute;
  top: 18px;
  left: calc(50% + 20px);
  right: calc(-50% + 20px);
  height: 2px;
}

.connector-line {
  height: 100%;
  background: #e8e8e8;
  transition: background 0.3s ease;
}

.connector-line.filled {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.progress-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s ease;
  border-radius: 2px;
}
</style>
