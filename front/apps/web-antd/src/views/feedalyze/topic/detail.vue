<script setup lang="ts">
import type { TopicDetail, UpdateTopicStatusParams, PriorityScoreParams } from '#/api';

import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

import { VbenButton, useVbenModal } from '@vben/common-ui';

import { message, Modal } from 'ant-design-vue';
import {
  LeftOutlined,
  EditOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons-vue';

import { useVbenForm } from '#/adapter/form';
import {
  getTopicDetail,
  updateTopicStatus,
  createOrUpdatePriorityScore,
  TOPIC_STATUSES,
} from '#/api';
import { getStatusConfig, getCategoryConfig, categoryIcons, statusFormSchema } from '#/views/feedalyze/topic/data';

const router = useRouter();
const route = useRoute();
const topicId = route.params.id as string;

/**
 * 数据加载
 */
const loading = ref(false);
const topicDetail = ref<TopicDetail | null>(null);

const loadTopicDetail = async () => {
  try {
    loading.value = true;
    topicDetail.value = await getTopicDetail(topicId);
  } catch (error: any) {
    message.error(error.message || '加载失败');
  } finally {
    loading.value = false;
  }
};

/**
 * 计算属性
 */
const topic = computed(() => topicDetail.value?.topic);
const feedbacks = computed(() => topicDetail.value?.feedbacks || []);
const priorityScore = computed(() => topicDetail.value?.priority_score);
const statusHistory = computed(() => topicDetail.value?.status_history || []);

const statusConfig = computed(() => 
  topic.value ? getStatusConfig(topic.value.status) : null
);

const categoryConfig = computed(() =>
  topic.value ? getCategoryConfig(topic.value.category) : null
);

/**
 * 优先级评分表单
 */
const scoreForm = ref({
  impact_scope: 1,
  business_value: 1,
  dev_cost: 1,
});

const calculatedScore = computed(() => {
  const { impact_scope, business_value, dev_cost } = scoreForm.value;
  const base = (impact_scope * business_value) / dev_cost;
  // 如果反馈中有紧急的,系数 1.5
  const urgencyFactor = feedbacks.value.some((f: any) => f.is_urgent) ? 1.5 : 1.0;
  return (base * urgencyFactor).toFixed(2);
});

const scoringLoading = ref(false);
const handleCalculateScore = async () => {
  if (!topic.value) return;
  
  try {
    scoringLoading.value = true;
    await createOrUpdatePriorityScore({
      topic_id: topic.value.id,
      ...scoreForm.value,
    });
    message.success('评分成功！');
    await loadTopicDetail(); // 重新加载数据
  } catch (error: any) {
    message.error(error.message || '评分失败');
  } finally {
    scoringLoading.value = false;
  }
};

/**
 * 状态更新
 */
const [StatusForm, statusFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: statusFormSchema,
});

const [statusModal, statusModalApi] = useVbenModal({
  title: '更新主题状态',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await statusFormApi.validate();
    if (valid) {
      statusModalApi.lock();
      const data = await statusFormApi.getValues<UpdateTopicStatusParams>();
      try {
        await updateTopicStatus(topicId, data);
        message.success('状态更新成功');
        await statusModalApi.close();
        await loadTopicDetail();
      } catch {
        message.error('状态更新失败');
      } finally {
        statusModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      statusFormApi.resetForm();
      if (topic.value) {
        statusFormApi.setValues({ status: topic.value.status });
      }
    }
  },
});

/**
 * 快速状态更新
 */
const handleQuickStatusUpdate = (status: string) => {
  Modal.confirm({
    title: '确认更新状态？',
    content: `将主题状态更新为「${getStatusConfig(status).label}」`,
    onOk: async () => {
      try {
        await updateTopicStatus(topicId, { status });
        message.success('状态更新成功');
        await loadTopicDetail();
      } catch {
        message.error('状态更新失败');
      }
    },
  });
};

/**
 * 反馈表格列
 */
const feedbackColumns = [
  {
    title: '反馈内容',
    dataIndex: 'content',
    ellipsis: true,
  },
  {
    title: '客户/作者',
    dataIndex: 'customer_name',
    width: 150,
  },
  {
    title: '提交时间',
    dataIndex: 'submitted_at',
    width: 180,
  },
];

/**
 * 初始化
 */
onMounted(() => {
  loadTopicDetail().then(() => {
    // 如果已有评分,填充表单
    if (priorityScore.value) {
      scoreForm.value = {
        impact_scope: priorityScore.value.impact_scope,
        business_value: priorityScore.value.business_value,
        dev_cost: priorityScore.value.dev_cost,
      };
    }
  });
});
</script>

<template>
  <div v-if="loading" class="loading-container">
    <a-spin size="large" />
  </div>

  <div v-else-if="topic" class="topic-detail-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <VbenButton variant="ghost" @click="() => router.push('/feedalyze/topic/list')">
        <LeftOutlined />
        返回列表
      </VbenButton>
    </div>

    <!-- 主题信息卡片 -->
    <a-card class="topic-info-card mb-4" :loading="loading">
      <template #title>
        <div class="card-title">
          <span class="category-icon">{{ categoryIcons[topic.category] }}</span>
          <span class="topic-title">{{ topic.title }}</span>
          <a-tag v-if="topic.ai_generated" color="purple" size="small" class="ml-2">
            <span class="iconify lucide--sparkles" /> AI 生成
          </a-tag>
        </div>
      </template>

      <template #extra>
        <a-tag :color="statusConfig?.color" class="status-tag">
          {{ statusConfig?.label }}
        </a-tag>
      </template>

      <a-descriptions :column="2" bordered>
        <a-descriptions-item label="分类">
          <a-tag :color="categoryConfig?.value === 'bug' ? 'red' : 'blue'">
            {{ categoryConfig?.label }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="反馈数量">
          <a-badge :count="topic.feedback_count" :number-style="{ backgroundColor: '#52c41a' }" />
        </a-descriptions-item>
        <a-descriptions-item label="AI 置信度" v-if="topic.ai_confidence">
          <a-progress 
            :percent="Number((topic.ai_confidence * 100).toFixed(0))" 
            size="small"
            :stroke-color="{ '0%': '#108ee9', '100%': '#87d068' }"
          />
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">
          {{ topic.created_time }}
        </a-descriptions-item>
        <a-descriptions-item label="最后更新" :span="2">
          {{ topic.updated_time }}
        </a-descriptions-item>
        <a-descriptions-item label="主题描述" :span="2" v-if="topic.description">
          {{ topic.description }}
        </a-descriptions-item>
      </a-descriptions>

      <a-divider />

      <div class="action-buttons">
        <VbenButton type="primary" @click="statusModalApi.open()">
          <EditOutlined />
          更新状态
        </VbenButton>
        <VbenButton @click="() => handleQuickStatusUpdate('planned')" :disabled="topic.status === 'planned'">
          <ClockCircleOutlined />
          计划中
        </VbenButton>
        <VbenButton @click="() => handleQuickStatusUpdate('in_progress')" :disabled="topic.status === 'in_progress'">
          <ThunderboltOutlined />
          进行中
        </VbenButton>
        <VbenButton @click="() => handleQuickStatusUpdate('completed')" :disabled="topic.status === 'completed'">
          <CheckCircleOutlined />
          已完成
        </VbenButton>
        <VbenButton danger @click="() => handleQuickStatusUpdate('ignored')" :disabled="topic.status === 'ignored'">
          <CloseCircleOutlined />
          忽略
        </VbenButton>
      </div>
    </a-card>

    <!-- 优先级评分卡片 -->
    <a-card title="🎯 优先级评分" class="priority-card mb-4">
      <div class="score-form">
        <a-form layout="inline" :model="scoreForm">
          <a-form-item label="影响范围">
            <a-select v-model:value="scoreForm.impact_scope" style="width: 150px">
              <a-select-option :value="1">个别用户 (1x)</a-select-option>
              <a-select-option :value="3">部分用户 (3x)</a-select-option>
              <a-select-option :value="5">大多数用户 (5x)</a-select-option>
              <a-select-option :value="10">全部用户 (10x)</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="商业价值">
            <a-select v-model:value="scoreForm.business_value" style="width: 150px">
              <a-select-option :value="1">普通客户 (1x)</a-select-option>
              <a-select-option :value="3">付费客户 (3x)</a-select-option>
              <a-select-option :value="5">大客户 (5x)</a-select-option>
              <a-select-option :value="10">战略客户 (10x)</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="开发成本">
            <a-select v-model:value="scoreForm.dev_cost" style="width: 150px">
              <a-select-option :value="1">1天 (1÷)</a-select-option>
              <a-select-option :value="3">3天 (3÷)</a-select-option>
              <a-select-option :value="5">1周 (5÷)</a-select-option>
              <a-select-option :value="10">2周+ (10÷)</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <VbenButton 
              type="primary" 
              @click="handleCalculateScore"
              :loading="scoringLoading"
            >
              计算评分
            </VbenButton>
          </a-form-item>
        </a-form>

        <a-alert v-if="calculatedScore" type="success" class="mt-4" show-icon>
          <template #message>
            <div class="score-result">
              <span class="score-label">优先级总分:</span>
              <span class="score-value">{{ calculatedScore }}</span>
            </div>
            <div class="score-formula">
              公式: ({{ scoreForm.impact_scope }} × {{ scoreForm.business_value }}) ÷ {{ scoreForm.dev_cost }}
              <span v-if="feedbacks.some((f: any) => f.is_urgent)"> × 1.5 (包含紧急反馈)</span>
            </div>
          </template>
        </a-alert>

        <a-alert
          v-if="priorityScore"
          message="已保存的评分"
          type="info"
          class="mt-2"
          show-icon
        >
          <template #description>
            上次评分时间: {{ priorityScore.updated_time }} | 总分: {{ priorityScore.total_score }}
          </template>
        </a-alert>
      </div>
    </a-card>

    <!-- 关联反馈列表 -->
    <a-card :title="`📝 关联反馈 (${feedbacks.length})`" class="feedbacks-card mb-4">
      <a-table
        :columns="feedbackColumns"
        :data-source="feedbacks"
        :pagination="{ pageSize: 10 }"
        :row-key="(record: any) => record.id"
        size="middle"
      />
    </a-card>

    <!-- 状态变更历史 -->
    <a-card title="📊 状态变更历史" class="history-card">
      <a-timeline v-if="statusHistory.length > 0">
        <a-timeline-item
          v-for="history in statusHistory"
          :key="history.id"
          :color="getStatusConfig(history.to_status).color"
        >
          <div class="history-item">
            <div class="history-title">
              <a-tag :color="getStatusConfig(history.from_status).color" size="small">
                {{ getStatusConfig(history.from_status).label }}
              </a-tag>
              <span class="history-arrow">→</span>
              <a-tag :color="getStatusConfig(history.to_status).color" size="small">
                {{ getStatusConfig(history.to_status).label }}
              </a-tag>
            </div>
            <div class="history-meta">
              <span>{{ history.changed_at }}</span>
              <span v-if="history.changed_by_name" class="ml-2">操作人: {{ history.changed_by_name }}</span>
            </div>
            <div v-if="history.reason" class="history-reason">
              原因: {{ history.reason }}
            </div>
          </div>
        </a-timeline-item>
      </a-timeline>
      <a-empty v-else description="暂无状态变更记录" />
    </a-card>

    <!-- 状态更新弹窗 -->
    <statusModal>
      <StatusForm />
    </statusModal>
  </div>

  <a-empty v-else description="主题不存在" />
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.topic-detail-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-icon {
  font-size: 24px;
}

.topic-title {
  font-size: 20px;
  font-weight: 600;
}

.status-tag {
  font-size: 14px;
  padding: 4px 12px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.score-form :deep(.ant-form-inline) {
  gap: 16px;
}

.score-result {
  font-size: 18px;
  margin-bottom: 8px;
}

.score-label {
  margin-right: 12px;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #52c41a;
}

.score-formula {
  color: #666;
  font-size: 14px;
}

.history-item {
  margin-bottom: 12px;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-arrow {
  color: #999;
}

.history-meta {
  color: #666;
  font-size: 13px;
}

.history-reason {
  margin-top: 4px;
  color: #333;
  font-size: 14px;
  padding-left: 12px;
  border-left: 2px solid #d9d9d9;
}
</style>
