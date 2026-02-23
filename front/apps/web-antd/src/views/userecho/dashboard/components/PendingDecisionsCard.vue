<script lang="ts" setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { Button, Card, message, Popconfirm, Tag, Tooltip } from 'ant-design-vue';

import { requestClient } from '#/api/request';

interface PendingDecision {
  id: string;
  title: string;
  category: string;
  status: string;
  priority_score: number;
  feedback_count: number;
  urgent_ratio: number;
  strategic_keywords_matched: string[];
  last_feedback_days: number | null;
  total_mrr: number;
  affected_customer_count: number;
}

interface Props {
  decisions: PendingDecision[];
}

defineProps<Props>();
const emit = defineEmits<{
  (e: 'refresh'): void;
}>();

const router = useRouter();
const loadingId = ref<string | null>(null);

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

// 优先级颜色
function getPriorityColor(score: number): string {
  if (score >= 70) return '#ff4d4f'; // 红色 - 高优先级
  if (score >= 50) return '#fa8c16'; // 橙色 - 中优先级
  return '#52c41a'; // 绿色 - 低优先级
}

// 快速决策
async function handleQuickDecision(topicId: string, action: 'confirm' | 'ignore') {
  loadingId.value = topicId;
  try {
    await requestClient.post(`/api/v1/app/dashboard/topic/${topicId}/quick-decision`, {
      action,
    });
    message.success(action === 'confirm' ? '已确认，进入排期' : '已忽略');
    emit('refresh');
  } catch (error: any) {
    message.error(error?.message || '操作失败');
  } finally {
    loadingId.value = null;
  }
}

// 跳转详情
function goToDetail(topicId: string) {
  router.push(`/app/topic/detail/${topicId}`);
}
</script>

<template>
  <Card class="w-full">
    <template #title>
      <div class="flex items-center gap-2">
        <span class="iconify lucide--target text-red-500" />
        <span>今日待决策</span>
        <Tag v-if="decisions.length > 0" color="red">{{ decisions.length }}</Tag>
      </div>
    </template>

    <div v-if="decisions.length === 0" class="text-center text-gray-400 py-8">
      <span class="iconify lucide--check-circle text-4xl mb-2" />
      <p>暂无待决策的需求</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="decision in decisions"
        :key="decision.id"
        class="border rounded-lg p-4 hover:border-primary transition-colors"
      >
        <!-- 标题行 -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium truncate cursor-pointer hover:text-primary" @click="goToDetail(decision.id)">
                {{ decision.title }}
              </span>
              <Tag :color="categoryColors[decision.category]" size="small">
                {{ categoryText[decision.category] }}
              </Tag>
            </div>
          </div>
          <!-- 优先级评分 -->
          <div class="flex-shrink-0 ml-4 text-right">
            <div
              class="text-2xl font-bold"
              :style="{ color: getPriorityColor(decision.priority_score) }"
            >
              {{ decision.priority_score }}
            </div>
            <div class="text-xs text-gray-400">优先级</div>
          </div>
        </div>

        <!-- 指标行 -->
        <div class="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-3">
          <Tooltip title="反馈数量">
            <span class="flex items-center gap-1">
              <span class="iconify lucide--message-square" />
              {{ decision.feedback_count }} 条反馈
            </span>
          </Tooltip>

          <Tooltip title="紧急反馈占比">
            <span class="flex items-center gap-1" :class="(decision.urgent_ratio ?? 0) > 0.3 ? 'text-red-500' : ''">
              <span class="iconify lucide--flame" />
              紧急 {{ Math.round((decision.urgent_ratio ?? 0) * 100) }}%
            </span>
          </Tooltip>

          <Tooltip v-if="Array.isArray(decision.strategic_keywords_matched) && decision.strategic_keywords_matched.length > 0" title="命中战略关键词">
            <span class="flex items-center gap-1 text-purple-500">
              <span class="iconify lucide--star" />
              {{ decision.strategic_keywords_matched.join('、') }}
            </span>
          </Tooltip>

          <Tooltip v-if="decision.last_feedback_days !== null" title="距最近反馈">
            <span class="flex items-center gap-1">
              <span class="iconify lucide--clock" />
              {{ decision.last_feedback_days === 0 ? '今天' : `${decision.last_feedback_days} 天前` }}
            </span>
          </Tooltip>

          <Tooltip v-if="decision.affected_customer_count > 0" title="受影响客户数">
            <span class="flex items-center gap-1 text-blue-500">
              <span class="iconify lucide--users" />
              {{ decision.affected_customer_count }} 家客户
            </span>
          </Tooltip>

          <Tooltip v-if="(decision.total_mrr ?? 0) > 0" title="关联 MRR">
            <span class="flex items-center gap-1 text-green-500">
              <span class="iconify lucide--dollar-sign" />
              ¥{{ Number(decision.total_mrr ?? 0).toLocaleString() }}
            </span>
          </Tooltip>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-2">
          <Popconfirm
            title="确认将此需求纳入排期？"
            ok-text="确认"
            cancel-text="取消"
            @confirm="handleQuickDecision(decision.id, 'confirm')"
          >
            <Button
              type="primary"
              size="small"
              :loading="loadingId === decision.id"
            >
              <template #icon>
                <span class="iconify lucide--check" />
              </template>
              确认
            </Button>
          </Popconfirm>

          <Popconfirm
            title="确认忽略此需求？"
            ok-text="忽略"
            cancel-text="取消"
            @confirm="handleQuickDecision(decision.id, 'ignore')"
          >
            <Button
              size="small"
              :loading="loadingId === decision.id"
            >
              <template #icon>
                <span class="iconify lucide--x" />
              </template>
              忽略
            </Button>
          </Popconfirm>

          <Button size="small" type="link" @click="goToDetail(decision.id)">
            查看详情
          </Button>
        </div>
      </div>
    </div>
  </Card>
</template>
