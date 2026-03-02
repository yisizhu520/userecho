<script setup lang="ts">
import type { Topic } from '#/api/userecho/topic';
import TopicCard from './TopicCard.vue';

interface StatusConfig {
  key: string;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

interface Props {
  status: StatusConfig;
  topics: Topic[];
}

defineProps<Props>();

const emit = defineEmits<{
  edit: [topic: Topic];
  delete: [topic: Topic];
}>();

// 状态卡片阴影映射
const shadowMap: Record<string, string> = {
  pending: 'shadow-sm',
  planned: 'shadow-md shadow-blue-500/10',
  in_progress: 'shadow-md shadow-purple-500/10',
  completed: 'shadow-sm',
  ignored: 'shadow-none opacity-80'
};
</script>

<template>
  <div class="kanban-column" :class="[status.bgColor]">
    <!-- 列头 -->
    <div class="column-header" :class="[status.borderColor]">
      <div class="header-content">
        <h3 class="status-label" :class="`text-${status.color}-700 dark:text-${status.color}-300`">
          {{ status.label }}
        </h3>
        <span class="topic-count">{{ topics.length }}</span>
      </div>
    </div>

    <!-- Topic 卡片列表 -->
    <div class="column-body sortable-container" :data-status="status.key">
      <TopicCard
        v-for="topic in topics"
        :key="topic.id"
        :topic="topic"
        @edit="(t) => emit('edit', t)"
        @delete="(t) => emit('delete', t)"
      />

      <!-- 空状态 -->
      <div v-if="topics.length === 0" class="empty-state">
        <span class="iconify lucide--inbox text-2xl text-gray-300 dark:text-gray-600" />
        <span class="text-xs text-gray-400 dark:text-gray-500 mt-2">暂无需求</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kanban-column {
  flex: 1;
  min-width: 300px;
  max-width: 340px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  transition: all 0.3s ease;
  background-color: hsl(var(--accent));
  border: 1px solid hsl(var(--border));
}

/* 状态颜色主题（Tailwind 类名映射） */
/* 注意：这些类需要确保被 Tailwind 扫描到，或者使用 style 绑定 */
/*
   Pending: bg-gray-50 border-gray-200
   Planned: bg-blue-50 border-blue-200
   In Progress: bg-purple-50 border-purple-200
   Completed: bg-green-50 border-green-200
   Ignored: bg-red-50 border-red-200
*/

.column-header {
  padding: 12px 16px;
  border-bottom: 1px solid hsl(var(--border) / 0.5);
  background: hsl(var(--background));
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.status-label {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.topic-count {
  font-size: 12px;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  background: hsl(var(--muted));
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 24px;
  text-align: center;
}

.column-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  opacity: 0.6;
}

/* 拖拽相关样式 */
.sortable-container.sortable-drag-over {
  background-color: hsl(var(--primary) / 0.05);
}

/* 自定义滚动条 */
.column-body::-webkit-scrollbar {
  width: 6px;
}
.column-body::-webkit-scrollbar-track {
  background: transparent;
}
.column-body::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 3px;
}
.column-body::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--border) / 0.8);
}
</style>
