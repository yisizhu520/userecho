<script setup lang="ts">
import type { Topic } from '#/api/userecho/topic';
import { computed } from 'vue';
import { getCategoryConfig } from '../data';
import { useBoardStore } from '#/store';
import { formatToSmartTime } from '#/utils/dateUtil';

import { useRouter } from 'vue-router';
import { MoreOutlined } from '@ant-design/icons-vue';

interface Props {
  topic: Topic;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  edit: [topic: Topic];
  delete: [topic: Topic];
}>();
const router = useRouter();
const boardStore = useBoardStore();

function handleCardClick() {
  router.push(`/app/topic/detail/${props.topic.id}`);
}

// 获取看板名称
const boardName = computed(() => {
  if (!props.topic.board_id) return '';
  const board = boardStore.boards.find(b => b.id === props.topic.board_id);
  return board?.name || '';
});

// 格式化时间
const createdTime = computed(() => {
  return formatToSmartTime(props.topic.created_time);
});

// 计算优先级颜色
const priorityConfig = computed(() => {
  const score = props.topic.priority_score?.total_score ?? 0;
  if (!props.topic.priority_score) return { color: 'text-gray-400', bg: 'bg-gray-100', label: '待评估' };

  if (score >= 15) return { color: 'text-red-500', bg: 'bg-red-50', label: '紧急' };
  if (score >= 10) return { color: 'text-orange-500', bg: 'bg-orange-50', label: '高' };
  if (score >= 5) return { color: 'text-blue-500', bg: 'bg-blue-50', label: '中' };
  return { color: 'text-gray-500', bg: 'bg-gray-50', label: '低' };
});

const categoryConfig = computed(() => getCategoryConfig(props.topic.category));

// 是否 AI 生成
const isAiGenerated = computed(() => props.topic.ai_generated);

</script>

<template>
  <div class="topic-card" :data-topic-id="topic.id" @click="handleCardClick">
    <!-- Header: 优先级点 + 看板 -->
    <div class="card-header">
      <div class="flex items-center gap-2">
        <!-- 优先级指示器 -->
        <div
          class="priority-indicator"
          :class="priorityConfig.bg"
          :title="`优先级: ${priorityConfig.label} (${topic.priority_score?.total_score ?? 0})`"
        >
          <div class="priority-dot" :class="priorityConfig.color.replace('text-', 'bg-')" />
          <span class="iconify lucide--signal text-[10px] opacity-70" />
          <span class="text-[10px] font-medium" :class="priorityConfig.color">{{ priorityConfig.label }}</span>
        </div>

        <!-- AI 标识 -->
        <div v-if="isAiGenerated" class="ai-badge" title="AI 自动生成">
          <span class="iconify lucide--sparkles text-[10px]" />
        </div>
      </div>

      <!-- 右侧：看板 Badge + 操作菜单 -->
      <div class="flex items-center gap-1" @click.stop>
        <div v-if="boardName" class="board-badge">
          {{ boardName }}
        </div>

        <a-dropdown :trigger="['click']" placement="bottomRight">
          <div class="action-btn p-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center justify-center">
            <MoreOutlined class="text-lg text-gray-500" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="edit" @click="emit('edit', topic)">
                <span class="flex items-center gap-2">
                  <span class="iconify lucide--edit size-3.5" />
                  编辑
                </span>
              </a-menu-item>
              <a-menu-item key="delete" danger @click="emit('delete', topic)">
                <span class="flex items-center gap-2">
                  <span class="iconify lucide--trash-2 size-3.5" />
                  删除
                </span>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- Body: 标题 -->
    <div class="card-body">
      <h4 class="topic-title" :title="topic.title">
        {{ topic.title }}
      </h4>
    </div>

    <!-- Footer: 元数据 -->
    <div class="card-footer">
      <!-- 左侧：分类 + 时间 -->
      <div class="flex items-center gap-2 overflow-hidden">
        <div class="category-icon" :class="categoryConfig.value === 'bug' ? 'text-red-500 bg-red-50' : 'text-blue-500 bg-blue-50'" :title="categoryConfig.label">
          <!-- 简单的图标映射 -->
          <span v-if="categoryConfig.value === 'bug'" class="iconify lucide--bug text-[10px]" />
          <span v-else-if="categoryConfig.value === 'feature'" class="iconify lucide--plus-circle text-[10px]" />
          <span v-else class="iconify lucide--zap text-[10px]" />
        </div>
        <span class="timestamp">{{ createdTime }}</span>
      </div>

      <!-- 右侧：数据指标 -->
      <div class="metrics">
        <!-- 反馈数 -->
        <div class="metric-item" title="反馈数量">
          <span class="iconify lucide--message-square text-gray-400 text-[10px]" />
          <span>{{ topic.feedback_count }}</span>
        </div>
        <!-- 投票数 (如果有字段，暂用 feedback_count 模拟或如果有 upvotes) -->
        <!-- <div class="metric-item ml-2" title="投票数">
          <span class="iconify lucide--thumbs-up text-gray-400 text-[10px]" />
          <span>{{ 0 }}</span>
        </div> -->
      </div>
    </div>
  </div>
</template>

<style scoped>
.topic-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: 8px; /* 更圆润的圆角 */
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.topic-card:hover {
  border-color: hsl(var(--primary) / 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* 悬浮阴影加深 */
  transform: translateY(-2px); /* 悬浮上浮 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.priority-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 12px;
}

.priority-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.ai-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  color: white;
}

.board-badge {
  font-size: 10px;
  color: hsl(var(--muted-foreground));
  background: hsl(var(--muted));
  padding: 2px 6px;
  border-radius: 4px;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-body {
  margin-bottom: 12px;
}

.topic-title {
  font-size: 14px;
  line-height: 1.5;
  color: hsl(var(--foreground));
  font-weight: 600; /* 加粗标题 */
  margin: 0;

  /* 多行截断 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid hsl(var(--border) / 0.4); /* 增加分割线 */
}

.category-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 4px;
}

.timestamp {
  font-size: 11px;
  color: hsl(var(--muted-foreground));
}

.metrics {
  display: flex;
  align-items: center;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: hsl(var(--muted-foreground));
  font-weight: 500;
}
</style>
