<script setup lang="ts">
import type { AIAnalysisResult, PriorityScore } from '#/api';

import { ref, computed, watch } from 'vue';

import { message } from 'ant-design-vue';
import { ReloadOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';

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
 * 优先级等级配置
 */
const priorityConfig = computed(() => {
  const score = parseFloat(calculatedScore.value);
  if (score >= 15) return { label: '紧急', color: 'red', class: 'urgent' };
  if (score >= 10) return { label: '高', color: 'orange', class: 'high' };
  if (score >= 5) return { label: '中', color: 'blue', class: 'medium' };
  return { label: '低', color: 'gray', class: 'low' };
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
  <a-card class="priority-score-card">
    <template #title>
      <div class="card-header">
        <span>🎯 优先级评分</span>
        <a-button 
          v-if="!analyzing"
          size="small"
          type="default"
          class="ai-btn"
          @click="handleAIAnalyze"
        >
          <ReloadOutlined /> AI 分析
        </a-button>
      </div>
    </template>

    <!-- 加载中 -->
    <div v-if="analyzing && !aiSuggestion" class="analyzing-container">
      <a-spin size="large" />
      <p class="analyzing-text">AI 正在分析中...</p>
    </div>

    <!-- 评分表单 -->
    <div v-else class="score-container">
      <!-- 评分结果展示区 -->
      <div class="score-result-banner" :class="priorityConfig.class">
        <div class="score-main">
          <div class="score-value">{{ calculatedScore }}</div>
          <div class="score-label">{{ priorityConfig.label }}优先级</div>
        </div>
        <div class="score-model-name">
          <a-tooltip overlay-class-name="model-tooltip" max-width="300px">
            <template #title>
              <div class="model-tooltip-content">
                <p><strong>源自 WSJF (加权最短作业优先) 算法</strong></p>
                <p>这是敏捷开发中用于决策优先级的核心经济学模型。</p>
                <div class="model-divider"></div>
                <p>🔥 <strong>核心逻辑：</strong>优先做「价值高」且「成本低」的事。</p>
                <p>📈 <strong>计算公式：</strong>(影响范围 × 商业价值 × 紧急系数) ÷ 实施成本</p>
                <p>💡 <strong>解读：</strong>分数越高，代表单位开发资源的产出价值越高 (High ROI)。</p>
              </div>
            </template>
            <span class="model-name-text">
              基于 ROI (投入产出比) 效率模型 <InfoCircleOutlined />
            </span>
          </a-tooltip>
        </div>

        <div class="score-formula-visual">
          <!-- 分子：综合价值 -->
          <div class="formula-part">
             <div class="part-value">{{ scoreForm.impact_scope * scoreForm.business_value }}</div>
             <div class="part-label">综合价值</div>
             <div class="part-sub">影响 × 商业</div>
          </div>
          
          <!-- 除号 -->
          <div class="formula-operator">÷</div>

          <!-- 分母：成本 -->
          <div class="formula-part">
             <div class="part-value">{{ scoreForm.dev_cost }}</div>
             <div class="part-label">实施成本</div>
             <div class="part-sub">开发人天</div>
          </div>

          <!-- 紧急系数 -->
          <template v-if="hasUrgentFeedback">
            <div class="formula-operator">×</div>
            <div class="formula-part urgent">
              <div class="part-value">1.5</div>
              <div class="part-label">紧急系数</div>
              <div class="part-sub">Urgency</div>
            </div>
          </template>
        </div>
      </div>

      <!-- 评分阈值图例 -->
      <div class="score-legend">
        <div class="legend-item"><span class="dot urgent"></span>≥15 紧急</div>
        <div class="legend-item"><span class="dot high"></span>≥10 高</div>
        <div class="legend-item"><span class="dot medium"></span>≥5 中</div>
        <div class="legend-item"><span class="dot low"></span>&lt;5 低</div>
      </div>

      <a-divider style="margin: 16px 0" />

      <!-- 表单区域 -->
      <div class="form-section">
        <!-- 影响范围 -->
        <div class="form-item">
          <div class="form-label">
            <span>影响范围</span>
            <a-tooltip title="受此需求影响的用户规模">
              <InfoCircleOutlined class="info-icon" />
            </a-tooltip>
          </div>
          <a-select v-model:value="scoreForm.impact_scope" class="w-full">
            <a-select-option :value="1">1 - 个别用户</a-select-option>
            <a-select-option :value="3">3 - 部分用户</a-select-option>
            <a-select-option :value="5">5 - 大多数用户</a-select-option>
            <a-select-option :value="10">10 - 全部用户</a-select-option>
          </a-select>
          <div v-if="aiSuggestion" class="ai-hint">
            <span class="icon">🤖</span>
            <span>AI 建议: {{ aiSuggestion.impact_scope.reason }}</span>
          </div>
        </div>

        <!-- 商业价值 -->
        <div class="form-item">
          <div class="form-label">
            <span>商业价值 (1-10)</span>
            <a-tooltip title="对业务增长或客户留存的贡献">
              <InfoCircleOutlined class="info-icon" />
            </a-tooltip>
          </div>
          <a-slider 
            v-model:value="scoreForm.business_value" 
            :min="1" 
            :max="10" 
            :marks="{ 1: '低', 5: '中', 10: '高' }"
          />
          <div v-if="aiSuggestion" class="ai-hint">
            <span class="icon">🤖</span>
            <span>AI 建议: {{ aiSuggestion.business_value.reason }}</span>
          </div>
        </div>

        <!-- 开发成本 -->
        <div class="form-item">
          <div class="form-label">
            <span>开发成本</span>
            <a-tooltip title="预估开发人天">
              <InfoCircleOutlined class="info-icon" />
            </a-tooltip>
          </div>
          <a-radio-group v-model:value="scoreForm.dev_cost" button-style="solid" size="small" class="cost-radio">
            <a-radio-button :value="1">1天</a-radio-button>
            <a-radio-button :value="3">3天</a-radio-button>
            <a-radio-button :value="5">5天</a-radio-button>
            <a-radio-button :value="10">10+</a-radio-button>
          </a-radio-group>
          <div v-if="aiSuggestion" class="ai-hint">
            <span class="icon">🤖</span>
            <span>AI 建议: {{ aiSuggestion.dev_cost.reason }}</span>
          </div>
        </div>
      </div>

      <div class="action-footer">
        <a-button 
          type="primary" 
          block
          :loading="saving"
          @click="handleSaveScore"
        >
          <CheckCircleOutlined /> {{ hasScore ? '更新评分' : '保存评分' }}
        </a-button>
      </div>
    </div>
  </a-card>
</template>

<style scoped>
.priority-score-card {
  position: sticky;
  top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-btn {
  font-size: 12px;
}

.analyzing-container {
  padding: 40px 0;
  text-align: center;
}

.analyzing-text {
  margin-top: 10px;
  color: #999;
}

.score-result-banner {
  padding: 24px;
  border-radius: 8px;
  color: white;
  text-align: center;
  transition: all 0.3s;
  background: linear-gradient(135deg, #269a99 0%, #13c2c2 100%);
  margin-bottom: 12px;
}

/* 优先级颜色主题 */
.score-result-banner.urgent {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3);
}

.score-result-banner.high {
  background: linear-gradient(135deg, #fa8c16 0%, #ffc069 100%);
  box-shadow: 0 4px 12px rgba(250, 140, 22, 0.3);
}

.score-result-banner.medium {
  background: linear-gradient(135deg, #1890ff 0%, #69c0ff 100%);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.score-result-banner.low {
  background: linear-gradient(135deg, #8c8c8c 0%, #d9d9d9 100%);
}

.score-main {
  margin-bottom: 8px;
}

.score-value {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
}

.score-label {
  font-size: 16px;
  font-weight: 500;
  opacity: 0.9;
}

.score-model-name {
  font-size: 12px;
  opacity: 0.7;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  font-weight: 400;
}

.model-name-text {
  cursor: help;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.4);
  padding-bottom: 2px;
  transition: all 0.3s;
}

.model-name-text:hover {
  opacity: 1;
  border-bottom-color: rgba(255, 255, 255, 0.9);
}

.score-formula-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  backdrop-filter: blur(4px);
}

.formula-part {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.part-value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.part-label {
  font-size: 11px;
  opacity: 0.9;
  line-height: 1.4;
}

.part-sub {
  font-size: 10px;
  opacity: 0.6;
  transform: scale(0.9);
}

.formula-operator {
  font-size: 16px;
  opacity: 0.6;
  font-weight: 300;
  margin-top: -12px; /* Slight alignment fix */
}

.score-legend {
  display: flex;
  justify-content: center;
  gap: 12px;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot.urgent { background-color: #ff4d4f; }
.dot.high { background-color: #fa8c16; }
.dot.medium { background-color: #1890ff; }
.dot.low { background-color: #d9d9d9; }

.form-item {
  margin-bottom: 20px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.info-icon {
  color: #999;
  font-size: 12px;
  cursor: help;
}

.cost-radio {
  display: flex;
}
.cost-radio :deep(.ant-radio-button-wrapper) {
  flex: 1;
  text-align: center;
}

.ai-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  gap: 4px;
  align-items: flex-start;
  line-height: 1.4;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.action-footer {
  margin-top: 24px;
}
</style>

<style>
/* Global tooltip styles */
.model-tooltip .ant-tooltip-inner {
  max-width: 340px !important;
  text-align: left;
}

.model-tooltip-content {
  font-size: 13px;
  line-height: 1.6;
}

.model-tooltip-content p {
  margin-bottom: 6px;
}

.model-tooltip-content p:last-child {
  margin-bottom: 0;
}

.model-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.15);
  margin: 8px 0;
}
</style>
