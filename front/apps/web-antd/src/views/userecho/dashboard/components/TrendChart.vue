<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, onBeforeUnmount, ref, watch } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

interface TrendData {
  date: string;
  count: number;
}

interface Props {
  data: TrendData[];
}

const props = defineProps<Props>();

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);
const isUnmounted = ref(false);

function renderChart() {
  // 防止组件卸载后继续渲染
  if (isUnmounted.value) return;
  
  if (!props.data || props.data.length === 0) {
    return;
  }

  // 提取日期和数量
  const dates = props.data.map((item) => {
    // 格式化日期为 MM-DD
    const date = new Date(item.date);
    return `${date.getMonth() + 1}-${date.getDate()}`;
  });
  const counts = props.data.map((item) => item.count);

  // 计算最大值，用于 y 轴范围
  const maxCount = Math.max(...counts, 10);
  const yMax = Math.ceil(maxCount * 1.2);

  renderEcharts({
    grid: {
      bottom: '10%',
      containLabel: true,
      left: '3%',
      right: '3%',
      top: '10%',
    },
    series: [
      {
        areaStyle: {
          color: {
            colorStops: [
              { color: 'rgba(90, 177, 239, 0.3)', offset: 0 },
              { color: 'rgba(90, 177, 239, 0.05)', offset: 1 },
            ],
            type: 'linear',
            x: 0,
            x2: 0,
            y: 0,
            y2: 1,
          },
        },
        data: counts,
        itemStyle: {
          color: '#5ab1ef',
        },
        smooth: true,
        type: 'line',
      },
    ],
    tooltip: {
      axisPointer: {
        lineStyle: {
          color: '#5ab1ef',
          width: 1,
        },
        type: 'line',
      },
      formatter: '{b}: {c} 条反馈',
      trigger: 'axis',
    },
    xAxis: {
      axisTick: {
        show: false,
      },
      boundaryGap: false,
      data: dates,
      type: 'category',
    },
    yAxis: {
      axisTick: {
        show: false,
      },
      max: yMax,
      minInterval: 1,
      splitNumber: 4,
      type: 'value',
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
