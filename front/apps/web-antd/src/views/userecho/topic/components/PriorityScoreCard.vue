<script setup lang="ts">
import type { AIAnalysisResult, PriorityScore } from '#/api';

import { ref, computed, watch } from 'vue';

import { message } from 'ant-design-vue';
import { ReloadOutlined, CheckCircleOutlined } from '@ant-design/icons-vue';

import { analyzePriority, createOrUpdatePriorityScore } from '#/api';

const props = defineProps<{
  topicId: string;
  existingScore?: PriorityScore | null;
  feedbackCount: number;
  hasUrgentFeedback: boolean;
}>();

const emit = defineEmits<{
  saved: [];
}>();

/**
 * 数据状态
 */
const analyzing = ref(false);
const saving = ref(false);
const aiSuggestion = ref<AIAnalysisResult | null>(null);

const scoreForm = ref({
  impact_scope: 1,
  business_value: 1,
  dev_cost: 1,
});

/**
 * 实时计算总分
 */
const calculatedScore = computed(() => {
  const { impact_scope, business_value, dev_cost } = scoreForm.value;
  const base = (impact_scope * business_value) / dev_cost;
  const urgencyFactor = props.hasUrgentFeedback ? 1.5 : 1.0;
  return (base * urgencyFactor).toFixed(1);
});

/**
 * 优先级颜色
 */
const priorityColor = computed(() => {
  const score = parseFloat(calculatedScore.value);
  if (score >= 15) return 'red';
  if (score >= 10) return 'orange';
  if (score >= 5) return 'blue';
  return 'gray';
});

/**
 * 是否已有评分
 */
const hasScore = computed(() => props.existingScore !== null && props.existingScore !== undefined);

const matchedKeywords = computed(() => {
  if (!props.existingScore?.details?.strategic_keywords_matched) return [];
  return props.existingScore.details.strategic_keywords_matched as string[];
});

/**
 * AI 重新分析
 */
const handleAIAnalyze = async () => {
  try {
    analyzing.value = true;
    aiSuggestion.value = await analyzePriority(props.topicId);
    
    // 自动填充 AI 建议值
    scoreForm.value = {
      impact_scope: aiSuggestion.value.impact_scope.scope || 1,
      business_value: aiSuggestion.value.business_value.value || 1,
      dev_cost: aiSuggestion.value.dev_cost.days || 1,
    };
    
    message.success('AI 分析完成！');
  } catch (error: any) {
    message.error(error.message || 'AI 分析失败');
  } finally {
    analyzing.value = false;
  }
};

/**
 * 保存评分
 */
const handleSaveScore = async () => {
  try {
    saving.value = true;
    
    const urgencyFactor = props.hasUrgentFeedback ? 1.5 : 1.0;
    
    await createOrUpdatePriorityScore(props.topicId, {
      impact_scope: scoreForm.value.impact_scope,
      business_value: scoreForm.value.business_value,
      dev_cost: scoreForm.value.dev_cost,
      urgency_factor: urgencyFactor,
    });
    
    message.success('评分已保存！');
    emit('saved');
  } catch (error: any) {
    message.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

/**
 * 初始化：加载已有评分或触发 AI 分析
 */
watch(
  () => props.existingScore,
  (score) => {
    if (score) {
      scoreForm.value = {
        impact_scope: score.impact_scope,
        business_value: score.business_value,
        dev_cost: score.dev_cost,
      };
    } else {
      // 没有评分时自动触发 AI 分析
      handleAIAnalyze();
    }
  },
  { immediate: true }
);
</script>

<template>
  <a-card title="🎯 优先级评分" class="priority-score-card">
    <template #extra>
      <a-button 
        type="link" 
        size="small"
        :loading="analyzing"
        @click="handleAIAnalyze"
      >
        <ReloadOutlined /> AI 重新分析
      </a-button>
    </template>

    <!-- 加载中 -->
    <div v-if="analyzing && !aiSuggestion" class="analyzing-container">
      <a-spin size="large" />
      <p class="analyzing-text">AI 正在分析中...</p>
    </div>

    <!-- 评分表单 -->
    <div v-else class="score-form-container">
      <!-- 已有评分：显示当前值 -->
      <a-alert v-if="hasScore" type="success" show-icon class="mb-4">
        <template #message>
          <div class="existing-score">
            <span>当前优先级总分：</span>
            <a-tag :color="priorityColor" style="font-size: 18px; font-weight: bold">
              {{ existingScore?.total_score.toFixed(1) }}
            </a-tag>
          </div>
        </template>
      </a-alert>

      <!-- AI 建议提示 -->
      <a-alert v-if="aiSuggestion && !hasScore" type="info" show-icon class="mb-4">
        <template #message>
          AI 已生成评分建议，您可以直接采纳或手动调整
        </template>
      </a-alert>

      <a-space direction="vertical" :size="24" style="width: 100%">
        <!-- 影响范围 -->
        <div class="score-item">
          <div class="score-item-header">
            <span class="score-label">影响范围</span>
            <a-select v-model:value="scoreForm.impact_scope" style="width: 200px">
              <a-select-option :value="1">
                <span>1分 - 个别用户</span>
              </a-select-option>
              <a-select-option :value="3">
                <span>3分 - 部分用户</span>
              </a-select-option>
              <a-select-option :value="5">
                <span>5分 - 大多数用户</span>
              </a-select-option>
              <a-select-option :value="10">
                <span>10分 - 全部用户</span>
              </a-select-option>
            </a-select>
          </div>
          <div v-if="aiSuggestion" class="ai-suggestion">
            <a-tag color="blue" size="small">
              置信度: {{ (aiSuggestion.impact_scope.confidence * 100).toFixed(0) }}%
            </a-tag>
            <span class="suggestion-reason">{{ aiSuggestion.impact_scope.reason }}</span>
          </div>
        </div>

        <!-- 商业价值 -->
        <div class="score-item">
          <div class="score-item-header">
            <span class="score-label">商业价值</span>
            <a-slider 
              v-model:value="scoreForm.business_value" 
              :min="1" 
              :max="10" 
              :marks="{ 1: '低', 5: '中', 10: '高' }"
              style="width: 300px"
            />
            <span class="score-value">{{ scoreForm.business_value }} 分</span>
          </div>
          <div v-if="aiSuggestion" class="ai-suggestion">
            <a-tag color="green" size="small">
              自动计算
            </a-tag>
            <span class="suggestion-reason">{{ aiSuggestion.business_value.reason }}</span>
          </div>
          <div v-if="matchedKeywords.length > 0" class="matched-keywords mt-2 pl-2">
            <span class="text-secondary text-xs mr-2">战略匹配:</span>
            <a-tag v-for="kw in matchedKeywords" :key="kw" color="purple" size="small">
              {{ kw }}
            </a-tag>
          </div>
        </div>

        <!-- 开发成本 -->
        <div class="score-item">
          <div class="score-item-header">
            <span class="score-label">开发成本</span>
            <a-radio-group v-model:value="scoreForm.dev_cost" button-style="solid">
              <a-radio-button :value="1">1天</a-radio-button>
              <a-radio-button :value="3">3天</a-radio-button>
              <a-radio-button :value="5">5天</a-radio-button>
              <a-radio-button :value="10">10天+</a-radio-button>
            </a-radio-group>
          </div>
          <div v-if="aiSuggestion" class="ai-suggestion">
            <a-tag color="orange" size="small">
              置信度: {{ (aiSuggestion.dev_cost.confidence * 100).toFixed(0) }}%
            </a-tag>
            <span class="suggestion-reason">{{ aiSuggestion.dev_cost.reason }}</span>
          </div>
        </div>

        <!-- 预计总分 -->
        <a-divider />
        <div class="score-summary">
          <div class="summary-row">
            <span class="summary-label">预计总分：</span>
            <a-tag :color="priorityColor" style="font-size: 24px; font-weight: bold; padding: 8px 16px">
              {{ calculatedScore }}
            </a-tag>
          </div>
          <div class="summary-formula">
            公式: ({{ scoreForm.impact_scope }} × {{ scoreForm.business_value }}) ÷ {{ scoreForm.dev_cost }}
            <span v-if="hasUrgentFeedback"> × 1.5 (包含紧急反馈)</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <a-button 
            type="primary" 
            size="large"
            :loading="saving"
            @click="handleSaveScore"
          >
            <CheckCircleOutlined /> {{ hasScore ? '更新评分' : '保存评分' }}
          </a-button>
        </div>
      </a-space>
    </div>
  </a-card>
</template>

<style scoped>
.priority-score-card {
  margin-bottom: 24px;
}

.analyzing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.analyzing-text {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}

.score-form-container {
  padding: 8px 0;
}

.existing-score {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}

.score-item {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.score-item-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.score-label {
  font-weight: 600;
  font-size: 15px;
  color: #333;
  min-width: 90px;
}

.score-value {
  font-weight: 600;
  color: #1890ff;
  font-size: 16px;
}

.ai-suggestion {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 106px;
  margin-top: 8px;
}

.suggestion-reason {
  color: #666;
  font-size: 13px;
}

.score-summary {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}

.summary-label {
  font-size: 18px;
  font-weight: 600;
}

.summary-formula {
  text-align: center;
  font-size: 14px;
  opacity: 0.9;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
