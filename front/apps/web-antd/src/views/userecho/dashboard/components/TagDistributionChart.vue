<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, onBeforeUnmount, ref, watch } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

interface TagDistribution {
  category: string;
  name: string;
  topic_count: number;
  feedback_count: number;
  avg_priority_score: number | null;
}

interface Props {
  data: TagDistribution[];
}

const props = defineProps<Props>();

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);
const isUnmounted = ref(false);

// 标签颜色映射
const categoryColors: Record<string, string> = {
  bug: '#f56c6c',        // 红色 - Bug
  improvement: '#67c23a', // 绿色 - 体验优化
  feature: '#409eff',     // 蓝色 - 新功能
  performance: '#e6a23c', // 橙色 - 性能问题
  other: '#909399',       // 灰色 - 其他
};

function renderChart() {
  // 防止组件卸载后继续渲染
  if (isUnmounted.value) return;
  
  if (!props.data || props.data.length === 0) {
    return;
  }

  // 准备饼图数据
  const chartData = props.data.map((item) => ({
    name: item.name,
    value: item.topic_count,
    itemStyle: {
      color: categoryColors[item.category] || '#909399',
    },
  }));

  renderEcharts({
    legend: {
      bottom: '5%',
      left: 'center',
      type: 'scroll',
    },
    series: [
      {
        center: ['50%', '45%'],
        data: chartData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
            shadowOffsetX: 0,
          },
        },
        label: {
          formatter: '{b}: {c} ({d}%)',
          fontSize: 12,
        },
        radius: ['40%', '60%'],
        type: 'pie',
      },
    ],
    tooltip: {
      formatter: (params: any) => {
        const dataItem = props.data.find((item) => item.name === params.name);
        if (!dataItem) return '';
        
        const lines = [
          `<strong>${params.name}</strong>`,
          `需求数: ${dataItem.topic_count}`,
          `反馈数: ${dataItem.feedback_count}`,
        ];
        
        if (dataItem.avg_priority_score !== null) {
          lines.push(`平均评分: ${dataItem.avg_priority_score}`);
        }
        
        return lines.join('<br/>');
      },
      trigger: 'item',
    },
  });
}

onMounted(() => {
  renderChart();
});

onBeforeUnmount(() => {
  isUnmounted.value = true;
});

watch(() => props.data, renderChart, { deep: true });
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
