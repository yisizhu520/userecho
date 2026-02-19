<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { Card } from 'ant-design-vue';

interface ConversionFunnel {
  total_feedbacks: number;
  clustered: number;
  pending_review: number;
  planned: number;
  in_progress: number;
  completed: number;
  conversion_rates: {
    clustering_rate: number;
    review_rate: number;
    planning_rate: number;
    completion_rate: number;
  };
}

interface Props {
  data?: ConversionFunnel;
}

const props = withDefaults(defineProps<Props>(), {
  data: () => ({
    total_feedbacks: 0,
    clustered: 0,
    pending_review: 0,
    planned: 0,
    in_progress: 0,
    completed: 0,
    conversion_rates: {
      clustering_rate: 0,
      review_rate: 0,
      planning_rate: 0,
      completion_rate: 0,
    },
  }),
});

const router = useRouter();

// 漏斗阶段配置
const funnelStages = computed(() => [
  {
    key: 'total',
    label: '总反馈',
    count: props.data.total_feedbacks,
    rate: 100,
    color: '#1890ff',
    route: '/app/feedback/list',
  },
  {
    key: 'clustered',
    label: '已聚类',
    count: props.data.clustered,
    rate: props.data.conversion_rates.clustering_rate,
    color: '#52c41a',
    route: '/app/feedback/list?clustered=true',
  },
  {
    key: 'pending',
    label: '待审议题',
    count: props.data.pending_review,
    rate: props.data.conversion_rates.review_rate,
    color: '#faad14',
    route: '/app/topic/list?status=pending',
  },
  {
    key: 'planned',
    label: '已排期',
    count: props.data.planned,
    rate: props.data.conversion_rates.planning_rate,
    color: '#13c2c2',
    route: '/app/topic/list?status=planned',
  },
  {
    key: 'in_progress',
    label: '进行中',
    count: props.data.in_progress,
    rate: props.data.conversion_rates.planning_rate,
    color: '#722ed1',
    route: '/app/topic/list?status=in_progress',
  },
  {
    key: 'completed',
    label: '已完成',
    count: props.data.completed,
    rate: props.data.conversion_rates.completion_rate,
    color: '#52c41a',
    route: '/app/topic/list?status=completed',
  },
]);

// 获取转化率颜色
const getRateColor = (rate: number) => {
  if (rate >= 60) return '#52c41a'; // 绿色
  if (rate >= 40) return '#faad14'; // 黄色
  return '#ff4d4f'; // 红色
};

// 跳转到对应列表
const goToList = (route: string) => {
  router.push(route);
};
</script>

<template>
  <Card title="📊 需求转化漏斗" class="conversion-funnel-card">
    <div class="funnel-container">
      <div
        v-for="(stage, index) in funnelStages"
        :key="stage.key"
        class="funnel-stage-wrapper"
      >
        <!-- 梯形漏斗块 -->
        <div
          class="funnel-trapezoid"
          :style="{
            width: `${stage.rate}%`,
            backgroundColor: stage.color,
          }"
          @click="goToList(stage.route)"
        >
          <div class="trapezoid-content">
            <span class="stage-label">{{ stage.label }}</span>
            <span class="stage-count">{{ stage.count }}</span>
          </div>
        </div>

        <!-- 转化率标签 -->
        <div class="conversion-info" v-if="index > 0">
          <span class="conversion-rate" :style="{ color: getRateColor(stage.rate) }">
            {{ stage.rate }}%
          </span>
        </div>

        <!-- 连接箭头 -->
        <div v-if="index < funnelStages.length - 1" class="funnel-arrow">
          <svg width="20" height="20" viewBox="0 0 20 20">
            <path d="M10 2 L10 14 M10 14 L6 10 M10 14 L14 10" 
                  stroke="#bfbfbf" 
                  stroke-width="2" 
                  fill="none" 
                  stroke-linecap="round"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- 关键指标提示 -->
    <div class="funnel-summary">
      <div class="summary-item">
        <span class="summary-label">聚类效率</span>
        <span
          class="summary-value"
          :style="{ color: getRateColor(data.conversion_rates.clustering_rate) }"
        >
          {{ data.conversion_rates.clustering_rate }}%
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">完成率</span>
        <span
          class="summary-value"
          :style="{ color: getRateColor(data.conversion_rates.completion_rate) }"
        >
          {{ data.conversion_rates.completion_rate }}%
        </span>
      </div>
    </div>
  </Card>
</template>

<style scoped>
.conversion-funnel-card {
  margin-bottom: 16px;
}

.funnel-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  padding: 16px 0;
}

.funnel-stage-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.funnel-trapezoid {
  position: relative;
  height: 50px;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  clip-path: polygon(8% 0%, 92% 0%, 100% 100%, 0% 100%);
  margin: 4px 0;
}

.funnel-trapezoid:hover {
  transform: translateY(-2px);
  filter: brightness(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.funnel-trapezoid:first-child {
  clip-path: polygon(0% 0%, 100% 0%, 92% 100%, 8% 100%);
}

.trapezoid-content {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-weight: 500;
  z-index: 1;
}

.stage-label {
  font-size: 13px;
}

.stage-count {
  font-size: 18px;
  font-weight: 600;
}

.conversion-info {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  padding: 0 20px;
  margin-top: -2px;
}

.conversion-rate {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.funnel-arrow {
  display: flex;
  justify-content: center;
  margin: 2px 0;
}

.funnel-summary {
  display: flex;
  justify-content: space-around;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: #8c8c8c;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
}
</style>
