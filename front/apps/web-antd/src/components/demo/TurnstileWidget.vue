<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';

import { turnstileSiteKey } from '#/utils/env';

const props = defineProps<{
  siteKey?: string;
}>();

const emit = defineEmits<{
  (e: 'verify', token: string): void;
  (e: 'error'): void;
  (e: 'expire'): void;
}>();

const widgetId = ref<string | null>(null);
const containerRef = ref<HTMLElement | null>(null);

// Turnstile 全局对象类型声明
declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement | null, options: {
        sitekey: string;
        callback: (token: string) => void;
        'error-callback': () => void;
        'expired-callback': () => void;
        theme?: 'light' | 'dark' | 'auto';
      }) => string;
      remove: (widgetId: string) => void;
      reset: (widgetId: string) => void;
    };
  }
}

onMounted(() => {
  const siteKey = props.siteKey || turnstileSiteKey;

  if (!siteKey || !window.turnstile) {
    console.warn('Turnstile not configured or script not loaded');
    return;
  }

  widgetId.value = window.turnstile.render(containerRef.value, {
    sitekey: siteKey,
    callback: (token: string) => emit('verify', token),
    'error-callback': () => emit('error'),
    'expired-callback': () => emit('expire'),
    theme: 'auto',
  });
});

onUnmounted(() => {
  if (widgetId.value && window.turnstile) {
    window.turnstile.remove(widgetId.value);
  }
});

// 暴露重置方法
const reset = () => {
  if (widgetId.value && window.turnstile) {
    window.turnstile.reset(widgetId.value);
  }
};

defineExpose({ reset });
</script>

<template>
  <div ref="containerRef" class="turnstile-container"></div>
</template>

<style scoped>
.turnstile-container {
  display: flex;
  justify-content: center;
}
</style>
