<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { Card } from 'ant-design-vue';

interface Topic {
  id: string;
  title: string;
  feedback_count: number;
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
  <Card title="TOP 需求主题" class="w-full">
    <div v-if="topics.length === 0" class="text-center text-gray-400 py-8">
      暂无需求主题
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="(topic, index) in topics"
        :key="topic.id"
        class="flex items-center gap-3 p-3 hover:bg-gray-50 rounded cursor-pointer transition-colors"
        @click="goToDetail(topic.id)"
      >
        <!-- 排名 -->
        <div class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full" :class="{
          'bg-yellow-400 text-white font-bold': index === 0,
          'bg-gray-300 text-white font-bold': index === 1,
          'bg-orange-300 text-white font-bold': index === 2,
          'bg-gray-100 text-gray-600': index > 2,
        }">
          {{ index + 1 }}
        </div>

        <!-- 内容 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-medium truncate">{{ topic.title }}</span>
          </div>
          <div class="flex items-center gap-2">
            <a-tag :color="categoryColors[topic.category]" size="small">
              {{ categoryText[topic.category] }}
            </a-tag>
            <span class="text-sm text-gray-500">
              {{ topic.feedback_count }} 条反馈
            </span>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
