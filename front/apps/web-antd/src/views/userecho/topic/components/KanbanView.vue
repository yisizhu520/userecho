<script setup lang="ts">
import type { Topic } from '#/api/userecho/topic';
import { computed, onMounted, ref, watch } from 'vue';
import { message } from 'ant-design-vue';
import Sortable from 'sortablejs';
import { updateTopicStatus } from '#/api/userecho/topic';
import KanbanColumn from './KanbanColumn.vue';

interface Props {
  topics: Topic[];
  loading?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  refresh: [];
}>();

// 5个状态列配置 (增加视觉配色配置)
const statuses = [
  { 
    key: 'pending', 
    label: '待审核', 
    color: 'gray',
    bgColor: 'bg-gray-50/50 dark:bg-gray-900/20',
    borderColor: 'border-t-gray-400 dark:border-t-gray-600'
  },
  { 
    key: 'planned', 
    label: '已规划', 
    color: 'blue',
    bgColor: 'bg-blue-50/50 dark:bg-blue-900/20',
    borderColor: 'border-t-blue-500'
  },
  { 
    key: 'in_progress', 
    label: '进行中', 
    color: 'purple',
    bgColor: 'bg-purple-50/50 dark:bg-purple-900/20',
    borderColor: 'border-t-purple-500' 
  },
  { 
    key: 'completed', 
    label: '已完成', 
    color: 'green',
    bgColor: 'bg-green-50/50 dark:bg-green-900/20',
    borderColor: 'border-t-green-500'
  },
  { 
    key: 'ignored', 
    label: '已忽略', 
    color: 'rose',
    bgColor: 'bg-rose-50/50 dark:bg-rose-900/20',
    borderColor: 'border-t-rose-400'
  },
] as const;

// 按状态分组 Topics
const topicsByStatus = computed(() => {
  const grouped: Record<string, Topic[]> = {
    pending: [],
    planned: [],
    in_progress: [],
    completed: [],
    ignored: [],
  };

  props.topics.forEach((topic) => {
    if (grouped[topic.status]) {
      grouped[topic.status].push(topic);
    }
  });

  return grouped;
});

// Sortable 实例存储
const sortableInstances = ref<Sortable[]>([]);

// 初始化拖拽功能
function initSortable() {
  // 清理旧实例
  sortableInstances.value.forEach((instance) => instance.destroy());
  sortableInstances.value = [];

  // 为每个状态列初始化 Sortable
  statuses.forEach((status) => {
    const container = document.querySelector(
      `.sortable-container[data-status="${status.key}"]`,
    ) as HTMLElement;

    if (!container) {
      // console.warn(`Sortable container not found for status: ${status.key}`);
      return;
    }

    const sortable = Sortable.create(container, {
      group: 'topics', // 允许跨列拖拽
      animation: 200,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      handle: '.topic-card', // 整个卡片可拖拽
      delay: 0, // 移动端可能需要 adjusted delay
      forceFallback: false, // 默认使用原生拖拽
      onEnd: async (evt) => {
        const topicId = evt.item.dataset.topicId;
        const newStatus = evt.to.dataset.status;

        if (!topicId || !newStatus) {
          console.error('Invalid drag event:', { topicId, newStatus });
          return;
        }

        // 获取原始状态
        const topic = props.topics.find((t) => t.id === topicId);
        const oldStatus = topic?.status;

        if (oldStatus === newStatus) {
          return; // 同一列内拖拽，不触发更新
        }

        try {
          // 乐观更新：先在本地更新状态以提供即时反馈（可选，这里还是等待后端返回比较稳妥，或者用临时状态）
          // 调用 API 更新状态
          await updateTopicStatus(topicId, { status: newStatus });
          message.success(`已更新为「${statuses.find((s) => s.key === newStatus)?.label}」`);

          // 刷新数据
          emit('refresh');
        } catch (error: any) {
          console.error('Failed to update topic status:', error);
          message.error(error.message || '状态更新失败');

          // 回滚 DOM 操作
          emit('refresh');
        }
      },
    });

    sortableInstances.value.push(sortable);
  });
}

onMounted(() => {
  // 延迟初始化，确保 DOM 已渲染
  setTimeout(() => {
    initSortable();
  }, 300);
});

// 监听 topics 变化，重新初始化拖拽
watch(
  () => props.topics,
  () => {
    setTimeout(() => {
      initSortable();
    }, 100);
  },
  { deep: true },
);
</script>

<template>
  <div class="kanban-view">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <span class="iconify lucide--loader-2 animate-spin text-4xl text-primary" />
      <span class="text-gray-500 mt-4">加载中...</span>
    </div>

    <!-- 看板布局 -->
    <div v-else class="kanban-board">
      <KanbanColumn
        v-for="status in statuses"
        :key="status.key"
        :status="status"
        :topics="topicsByStatus[status.key] || []"
      />
    </div>
  </div>
</template>

<style scoped>
.kanban-view {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.kanban-board {
  display: flex;
  gap: 16px;
  height: 100%;
  padding: 16px 8px; /* 减少左右 padding */
  overflow-x: auto;
  overflow-y: hidden;
}

/* 拖拽中的样式 */
:deep(.sortable-ghost) {
  opacity: 0.2;
  background-color: hsl(var(--muted));
  border: 1px dashed hsl(var(--border));
}

:deep(.sortable-chosen) {
  cursor: grabbing;
}

:deep(.sortable-drag) {
  opacity: 1;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  transform: rotate(2deg) scale(1.02);
  cursor: grabbing;
  z-index: 9999;
}

/* 自定义滚动条 */
.kanban-board::-webkit-scrollbar {
  height: 8px;
}

.kanban-board::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.kanban-board::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}

.kanban-board::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
</style>
