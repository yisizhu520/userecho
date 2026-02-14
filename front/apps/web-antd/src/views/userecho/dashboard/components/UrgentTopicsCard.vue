<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { Card } from 'ant-design-vue';

interface Topic {
  id: string;
  title: string;
  feedback_count: number;
  priority_score: number | null;
  category: string;
  status: string;
}

interface Props {
  topics: Topic[];
}

defineProps<Props>();
const router = useRouter();

// 分类标签颜色映射
const categoryColors: Record<string, string> = {
  bug: 'red',
  feature: 'blue',
  improvement: 'green',
  performance: 'orange',
  other: 'default',
};

// 状态标签颜色映射
const statusColors: Record<string, string> = {
  pending: 'orange',
  planned: 'blue',
  in_progress: 'processing',
  completed: 'success',
  ignored: 'default',
};

// 状态文本映射
const statusText: Record<string, string> = {
  pending: '待处理',
  planned: '已计划',
  in_progress: '进行中',
  completed: '已完成',
  ignored: '已忽略',
};

// 分类文本映射
const categoryText: Record<string, string> = {
  bug: 'Bug',
  feature: '新功能',
  improvement: '体验优化',
  performance: '性能问题',
  other: '其他',
};

// 点击跳转到需求详情
function goToDetail(topicId: string) {
  router.push(`/app/topic/detail/${topicId}`);
}
</script>

<template>
  <Card title="紧急需求" class="w-full">
    <div v-if="topics.length === 0" class="text-center text-gray-400 py-8">
      暂无紧急需求
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="topic in topics"
        :key="topic.id"
        class="flex items-center justify-between p-3 hover:bg-gray-50 rounded cursor-pointer transition-colors"
        @click="goToDetail(topic.id)"
      >
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-medium truncate">{{ topic.title }}</span>
            <a-tag :color="categoryColors[topic.category]" size="small">
              {{ categoryText[topic.category] }}
            </a-tag>
          </div>
          <div class="flex items-center gap-3 text-sm text-gray-500">
            <span>{{ topic.feedback_count }} 条反馈</span>
            <a-tag :color="statusColors[topic.status]" size="small">
              {{ statusText[topic.status] }}
            </a-tag>
          </div>
        </div>
        <div v-if="topic.priority_score" class="ml-4 flex-shrink-0">
          <div class="text-right">
            <div class="text-xl font-bold text-red-500">
              {{ topic.priority_score }}
            </div>
            <div class="text-xs text-gray-400">优先级</div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
