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

const funnelStages = computed(() => [
  {
    key: 'total',
    label: '总反馈',
    count: props.data.total_feedbacks,
    rate: null as number | null,
    color: '#4096ff',
    route: '/app/feedback/list',
  },
  {
    key: 'clustered',
    label: '已聚类',
    count: props.data.clustered,
    rate: props.data.conversion_rates.clustering_rate as number | null,
    color: '#52c41a',
    route: '/app/feedback/list?clustered=true',
  },
  {
    key: 'pending',
    label: '待审议题',
    count: props.data.pending_review,
    rate: props.data.conversion_rates.review_rate as number | null,
    color: '#fa8c16',
    route: '/app/topic/list?status=pending',
  },
  {
    key: 'planned',
    label: '已排期',
    count: props.data.planned,
    rate: props.data.conversion_rates.planning_rate as number | null,
    color: '#13c2c2',
    route: '/app/topic/list?status=planned',
  },
  {
    key: 'in_progress',
    label: '进行中',
    count: props.data.in_progress,
    rate: props.data.conversion_rates.planning_rate as number | null,
    color: '#722ed1',
    route: '/app/topic/list?status=in_progress',
  },
  {
    key: 'completed',
    label: '已完成',
    count: props.data.completed,
    rate: props.data.conversion_rates.completion_rate as number | null,
    color: '#52c41a',
    route: '/app/topic/list?status=completed',
  },
]);

const maxCount = computed(() =>
  Math.max(...funnelStages.value.map((s) => s.count), 1),
);

// 条宽基于绝对数量，最小 3% 保证可见
const getBarWidth = (count: number) => {
  if (count === 0) return 0;
  return Math.max((count / maxCount.value) * 100, 3);
};

const getRateStyle = (rate: number | null) => {
  if (rate === null) return { color: '#8c8c8c', background: '#f5f5f5' };
  if (rate >= 60) return { color: '#389e0d', background: '#f6ffed' };
  if (rate >= 30) return { color: '#d46b08', background: '#fff7e6' };
  return { color: '#cf1322', background: '#fff1f0' };
};

const goToList = (route: string) => {
  router.push(route);
};
</script>

<template>
  <Card class="conversion-funnel-card" :bordered="false">
    <template #title>
      <span class="card-title">需求转化漏斗</span>
    </template>

    <div class="funnel-list">
      <template v-for="(stage, index) in funnelStages" :key="stage.key">
        <!-- 阶段行 -->
        <div class="stage-row" @click="goToList(stage.route)">
          <div class="stage-label-wrap">
            <span class="stage-dot" :style="{ background: stage.color }"></span>
            <span class="stage-name">{{ stage.label }}</span>
          </div>
          <div class="stage-bar-wrap">
            <div
              class="stage-bar"
              :style="{
                width: getBarWidth(stage.count) + '%',
                background: `linear-gradient(90deg, ${stage.color}, ${stage.color}99)`,
              }"
            ></div>
          </div>
          <div class="stage-count-wrap">
            <span class="stage-count">{{ stage.count }}</span>
          </div>
        </div>

        <!-- 转化率连接器 -->
        <div
          v-if="index < funnelStages.length - 1"
          class="rate-connector"
        >
          <span class="connector-arrow">↓</span>
          <span
            class="rate-badge"
            :style="getRateStyle(funnelStages[index + 1].rate)"
          >
            {{
              funnelStages[index + 1].rate !== null
                ? funnelStages[index + 1].rate + '%'
                : '—'
            }}
          </span>
        </div>
      </template>
    </div>

    <!-- 底部汇总指标 -->
    <div class="funnel-summary">
      <div class="summary-stat">
        <div
          class="stat-value"
          :style="getRateStyle(data.conversion_rates.clustering_rate)"
        >
          {{ data.conversion_rates.clustering_rate }}%
        </div>
        <div class="stat-label">聚类效率</div>
      </div>
      <div class="summary-divider"></div>
      <div class="summary-stat">
        <div
          class="stat-value"
          :style="getRateStyle(data.conversion_rates.completion_rate)"
        >
          {{ data.conversion_rates.completion_rate }}%
        </div>
        <div class="stat-label">完成率</div>
      </div>
    </div>
  </Card>
</template>

<style scoped>
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

/* ── 漏斗列表 ── */
.funnel-list {
  padding: 4px 0;
}

/* ── 阶段行 ── */
.stage-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.stage-row:hover {
  background: #fafafa;
}

.stage-label-wrap {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 82px;
  flex-shrink: 0;
}

.stage-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stage-name {
  font-size: 13px;
  color: #595959;
  white-space: nowrap;
}

.stage-bar-wrap {
  flex: 1;
  height: 22px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.stage-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.55s cubic-bezier(0.4, 0, 0.2, 1);
}

.stage-count-wrap {
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.stage-count {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  font-variant-numeric: tabular-nums;
}

/* ── 转化率连接器 ── */
.rate-connector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 1px 8px 1px 25px; /* 与 stage-name 左对齐 */
}

.connector-arrow {
  font-size: 11px;
  color: #d9d9d9;
  line-height: 1;
}

.rate-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}

/* ── 底部汇总 ── */
.funnel-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  padding: 0 6px;
  border-radius: 6px;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.summary-divider {
  width: 1px;
  height: 36px;
  background: #f0f0f0;
}
</style>
