<script setup lang="ts">
import { ref, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { getTopicList } from '#/api/userecho/topic';

interface Props {
  searchTitle: string;
  selectedTopicId?: string;
}

interface Emits {
  (e: 'update:selectedTopicId', value: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const similarTopics = ref<any[]>([]);
const loading = ref(false);

// 防抖搜索函数
const searchTopics = useDebounceFn(async (title: string) => {
  if (!title || title.trim().length < 2) {
    similarTopics.value = [];
    return;
  }

  try {
    loading.value = true;
    const result = await getTopicList({
      search_query: title,
      search_mode: 'keyword',
      limit: 10,
    });
    similarTopics.value = result.items || [];
  } catch (error: any) {
    console.error('搜索 Topic 失败', error);
  } finally {
    loading.value = false;
  }
}, 300);

// 监听标题变化
watch(() => props.searchTitle, (title) => {
  searchTopics(title);
}, { immediate: true });

// 选择主题
const handleTopicSelect = (topicId: string) => {
  emit('update:selectedTopicId', topicId);
};
</script>

<template>
  <div class="similar-topics-panel">
    <div class="panel-header">
      <span class="iconify lucide--lightbulb mr-2" />
      相似主题
    </div>

    <div v-if="loading" class="panel-loading">
      <a-spin />
      <p>搜索中...</p>
    </div>

    <div v-else-if="similarTopics.length === 0" class="panel-empty">
      <span class="iconify lucide--search text-4xl mb-2" />
      <p>输入标题以搜索相似主题</p>
    </div>

    <div v-else class="topic-list">
      <div
        v-for="topic in similarTopics"
        :key="topic.id"
        class="topic-item"
        :class="{ 'topic-item-selected': selectedTopicId === topic.id }"
        @click="handleTopicSelect(topic.id)"
      >
        <div class="topic-title">{{ topic.title }}</div>
        <div class="topic-meta">
          <a-tag :color="topic.status === 'pending' ? 'default' : 'blue'" size="small">
            {{ topic.status }}
          </a-tag>
          <span class="topic-feedback-count">
            {{ topic.feedback_count }} 条反馈
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.similar-topics-panel {
  height: 600px;
  border: 1px solid hsl(var(--border) / 0.3);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: hsl(var(--background));
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid hsl(var(--border) / 0.3);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  background: hsl(var(--muted) / 0.3);
}

.panel-loading,
.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: hsl(var(--muted-foreground));
  padding: 32px;
  text-align: center;
}

.panel-loading p,
.panel-empty p {
  margin-top: 12px;
  font-size: 14px;
}

.topic-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.topic-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid hsl(var(--border) / 0.3);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: hsl(var(--background));
}

.topic-item:hover {
  border-color: hsl(var(--primary) / 0.5);
  background: hsl(var(--muted) / 0.2);
  transform: translateX(2px);
}

.topic-item-selected {
  border-color: hsl(var(--primary));
  background: hsl(var(--primary) / 0.1);
  box-shadow: 0 0 0 1px hsl(var(--primary) / 0.2);
}

.topic-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 8px;
  color: hsl(var(--foreground));
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: hsl(var(--muted-foreground));
}

.topic-feedback-count {
  display: flex;
  align-items: center;
}
</style>
