<script setup lang="ts">
/**
 * 合并建议弹窗（Linus 简化版）
 *
 * 展示聚类后发现的与已有需求重复的反馈聚类，让用户选择操作：
 * - 关联到已有需求（推荐）
 * - 创建新需求
 *
 * ✅ 删除无用选项：mark_outdated, reopen_and_link
 * ✅ 统一逻辑：不区分 completed vs non-completed
 */
import type { MergeSuggestion } from '#/api';

import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';

import { linkFeedbacksToTopic } from '#/api';
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
  // ✅ Linus 简化：按相似度排序，不区分 completed vs non-completed
  return [...props.suggestions].sort((a, b) => b.similarity - a.similarity);
});

const close = () => {
  emit('update:open', false);
};

/**
 * 关联到已有需求（推荐操作）
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
 * 创建新需求
 */
async function handleCreateNew(suggestion: MergeSuggestion) {
  // 跳转到需求创建页面，预填标题
  close();
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

        <!-- 操作按钮（✅ Linus 简化：统一逻辑，只有2个按钮） -->
        <div class="suggestion-actions">
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
