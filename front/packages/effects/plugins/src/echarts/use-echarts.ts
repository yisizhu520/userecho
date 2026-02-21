import type { EChartsOption } from 'echarts';

import type { Ref } from 'vue';

import type { Nullable } from '@vben/types';

import type EchartsUI from './echarts-ui.vue';

import { computed, nextTick, watch } from 'vue';

import { usePreferences } from '@vben/preferences';

import {
  tryOnUnmounted,
  useDebounceFn,
  useResizeObserver,
  useTimeoutFn,
  useWindowSize,
} from '@vueuse/core';

import echarts from './echarts';

type EchartsUIType = typeof EchartsUI | undefined;

type EchartsThemeType = 'dark' | 'light' | null;

function useEcharts(chartRef: Ref<EchartsUIType>) {
  let chartInstance: echarts.ECharts | null = null;
  let cacheOptions: EChartsOption = {};
  let isUnmounted = false;

  const { isDark } = usePreferences();
  const { height, width } = useWindowSize();
  const resizeHandler: () => void = useDebounceFn(resize, 200);

  const getOptions = computed((): EChartsOption => {
    if (!isDark.value) {
      return {};
    }

    return {
      backgroundColor: 'transparent',
    };
  });

  const initCharts = (t?: EchartsThemeType) => {
    if (isUnmounted) return;
    const el = chartRef?.value?.$el;
    if (!el) {
      return;
    }
    chartInstance = echarts.init(el, t || isDark.value ? 'dark' : null);

    return chartInstance;
  };

  const renderEcharts = (
    options: EChartsOption,
    clear = true,
  ): Promise<Nullable<echarts.ECharts>> => {
    cacheOptions = options;
    const currentOptions = {
      ...options,
      ...getOptions.value,
    };
    return new Promise((resolve) => {
      if (isUnmounted) {
        resolve(null);
        return;
      }
      if (chartRef.value?.offsetHeight === 0) {
        useTimeoutFn(async () => {
          if (isUnmounted) {
            resolve(null);
            return;
          }
          resolve(await renderEcharts(currentOptions));
        }, 30);
        return;
      }
      nextTick(() => {
        if (isUnmounted) {
          resolve(null);
          return;
        }
        useTimeoutFn(() => {
          if (isUnmounted) {
            resolve(null);
            return;
          }
          if (!chartInstance) {
            const instance = initCharts();
            if (!instance) return;
          }
          clear && chartInstance?.clear();
          chartInstance?.setOption(currentOptions);
          resolve(chartInstance);
        }, 30);
      });
    });
  };

  function resize() {
    if (isUnmounted) return;
    chartInstance?.resize({
      animation: {
        duration: 300,
        easing: 'quadraticIn',
      },
    });
  }

  watch([width, height], () => {
    if (isUnmounted) return;
    resizeHandler?.();
  });

  useResizeObserver(chartRef as never, resizeHandler);

  watch(isDark, () => {
    if (isUnmounted) return;
    if (chartInstance) {
      chartInstance.dispose();
      initCharts();
      renderEcharts(cacheOptions);
      resize();
    }
  });

  tryOnUnmounted(() => {
    // 标记为已卸载，阻止所有后续的异步操作
    isUnmounted = true;
    // 销毁实例，释放资源
    chartInstance?.dispose();
  });
  return {
    renderEcharts,
    resize,
    getChartInstance: () => chartInstance,
  };
}

export { useEcharts };

export type { EchartsUIType };
