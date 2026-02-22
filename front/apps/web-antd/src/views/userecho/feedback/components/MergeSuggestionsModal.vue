<script setup lang="ts">
/**
 * 合并建议弹窗
 * 
 * 展示聚类后发现的与已有需求重复的反馈聚类，让用户选择操作：
 * - 关联到已有需求
 * - 创建新需求
 * - 重新打开需求（如果是已完成状态）
 */
import type { MergeSuggestion } from '#/api';

import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';

import { linkFeedbacksToTopic, updateTopicStatus } from '#/api';
import { getCategoryConfig, getStatusConfig, categoryIcons } from '#/views/userecho/topic/data';

interface Props {
  open: boolean;
  suggestions: MergeSuggestion[];
}

interface Emits {
  (e: 'update:open', value: boolean): void;
  (e: 'refresh'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const router = useRouter();
const processing = ref<string | null>(null);  // 当前正在处理的 suggestion cluster_label

const sortedSuggestions = computed(() => {
  // 已完成的需求排在前面（更需要用户关注）
  return [...props.suggestions].sort((a, b) => {
    if (a.is_completed && !b.is_completed) return -1;
    if (!a.is_completed && b.is_completed) return 1;
    return b.similarity - a.similarity;
  });
});

const close = () => {
  emit('update:open', false);
};

/**
 * 关联到已有需求
 */
async function handleLinkToExisting(suggestion: MergeSuggestion) {
  processing.value = String(suggestion.cluster_label);
  try {
    await linkFeedbacksToTopic(suggestion.suggested_topic_id, suggestion.feedback_ids);
    message.success(`已将 ${suggestion.feedback_count} 条反馈关联到「${suggestion.suggested_topic_title}」`);
    emit('refresh');
  } catch (error: any) {
    message.error(error.message || '关联失败');
  } finally {
    processing.value = null;
  }
}


/**
 * 重新打开需求并关联
 */
async function handleReopenAndLink(suggestion: MergeSuggestion) {
  processing.value = String(suggestion.cluster_label);
  try {
    // 1. 重新打开需求
    await updateTopicStatus(suggestion.suggested_topic_id, {
      status: 'in_progress',
      reason: '收到新的用户反馈，重新打开',
    });
    
    // 2. 关联反馈
    await linkFeedbacksToTopic(suggestion.suggested_topic_id, suggestion.feedback_ids);
    
    message.success(`已重新打开「${suggestion.suggested_topic_title}」并关联 ${suggestion.feedback_count} 条反馈`);
    emit('refresh');
  } catch (error: any) {
    message.error(error.message || '操作失败');
  } finally {
    processing.value = null;
  }
}


/**
 * 创建新需求
 */
async function handleCreateNew(suggestion: MergeSuggestion) {
  // 跳转到需求创建页面，预填标题
  close();
  // 通过 query 参数传递预填信息
  router.push({
    path: '/app/topic/list',
    query: {
      action: 'create',
      title: suggestion.ai_generated_title,
      feedback_ids: suggestion.feedback_ids.join(','),
    },
  });
}

/**
 * 查看需求详情
 */
function handleViewTopic(topicId: string) {
  router.push(`/app/topic/detail/${topicId}`);
}
</script>

<template>
  <a-modal
    :open="open"
    title="🔗 发现相似需求"
    :width="720"
    :footer="null"
    @cancel="close"
  >
    <a-alert
      type="info"
      show-icon
      class="mb-4"
    >
      <template #message>
        以下聚类与已有需求高度相似，建议关联而非创建新需求。
      </template>
    </a-alert>

    <div class="suggestions-list">
      <div
        v-for="suggestion in sortedSuggestions"
        :key="suggestion.cluster_label"
        class="suggestion-card"
        :class="{ 'is-completed': suggestion.is_completed }"
      >
        <!-- 头部：相似的需求信息 -->
        <div class="suggestion-header">
          <div class="topic-info" @click="handleViewTopic(suggestion.suggested_topic_id)">
            <a-tag :color="getCategoryConfig(suggestion.suggested_topic_category).color || 'blue'">
              {{ categoryIcons[suggestion.suggested_topic_category] || '' }}
              {{ getCategoryConfig(suggestion.suggested_topic_category).label }}
            </a-tag>
            <span class="topic-title">{{ suggestion.suggested_topic_title }}</span>
            <a-tag :color="getStatusConfig(suggestion.suggested_topic_status).color">
              {{ getStatusConfig(suggestion.suggested_topic_status).label }}
            </a-tag>
          </div>
          <a-tag color="green">
            相似度 {{ (suggestion.similarity * 100).toFixed(0) }}%
          </a-tag>
        </div>

        <!-- 警告信息（已完成的需求） -->
        <a-alert
          v-if="suggestion.warning"
          type="warning"
          :message="suggestion.warning"
          show-icon
          class="my-2"
        />

        <!-- 反馈信息 -->
        <div class="feedback-info">
          <span class="text-gray-500">
            AI 建议标题：{{ suggestion.ai_generated_title }}
          </span>
          <a-badge
            :count="suggestion.feedback_count"
            :number-style="{ backgroundColor: '#1890ff' }"
          />
          <span class="text-gray-400">条反馈</span>
        </div>

        <!-- 操作按钮 -->
        <div class="suggestion-actions">
          <template v-if="suggestion.is_completed">
            <!-- 已完成需求的操作 -->
            <a-button
              type="primary"
              :loading="processing === String(suggestion.cluster_label)"
              @click="handleReopenAndLink(suggestion)"
            >
              <span class="iconify lucide--redo-2 mr-1" />
              重新打开并关联
            </a-button>
            <a-button
              @click="handleCreateNew(suggestion)"
            >
              <span class="iconify lucide--plus mr-1" />
              创建新需求
            </a-button>
          </template>
          <template v-else>
            <!-- 进行中的需求操作 -->
            <a-button
              type="primary"
              :loading="processing === String(suggestion.cluster_label)"
              @click="handleLinkToExisting(suggestion)"
            >
              <span class="iconify lucide--link mr-1" />
              关联到此需求
            </a-button>
            <a-button
              @click="handleCreateNew(suggestion)"
            >
              <span class="iconify lucide--plus mr-1" />
              创建新需求
            </a-button>
          </template>
        </div>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="text-gray-400 text-xs mt-4">
      💡 提示：关联到已有需求可以帮助更好地追踪问题，避免需求池冗余。
    </div>
  </a-modal>
</template>

<style scoped>
.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 60vh;
  overflow-y: auto;
}

.suggestion-card {
  border: 1px solid hsl(var(--border));
  border-radius: 8px;
  padding: 16px;
  background: hsl(var(--card));
  transition: all 0.2s;
}

.suggestion-card:hover {
  border-color: hsl(var(--primary));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.suggestion-card.is-completed {
  border-color: #faad14;
  background: linear-gradient(135deg, hsl(var(--card)) 0%, #fffbe6 100%);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.topic-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.topic-info:hover .topic-title {
  color: hsl(var(--primary));
}

.topic-title {
  font-weight: 500;
  transition: color 0.2s;
}

.feedback-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 12px;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
}
</style>
