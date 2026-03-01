<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { requestClient } from '#/api/request';
import { getClusteringStatus } from '#/api/userecho/clustering';

const props = defineProps<{
  boardIds?: string[];
}>();

const loading = ref(false);
const status = ref<{
  pending_count: number;
  processing_count: number;
  last_run_at: string | null;
} | null>(null);

// 加载状态
const loadStatus = async () => {
  loading.value = true;
  try {
    status.value = await getClusteringStatus(props.boardIds);
  } catch (error) {
    console.error('Failed to load clustering status:', error);
  } finally {
    loading.value = false;
  }
};

watch(() => props.boardIds, () => {
    loadStatus();
}, { deep: true });

onMounted(() => {
  loadStatus();
});

// 是否显示横幅
const showBanner = computed(() => {
  if (!status.value) return false;
  return status.value.pending_count > 0 || status.value.processing_count > 0;
});

// 状态类型
const bannerType = computed(() => {
  if (!status.value) return 'info';
  if (status.value.processing_count > 0) return 'info';
  if (status.value.pending_count > 0) return 'warning';
  return 'success';
});

// 状态文本
const statusText = computed(() => {
  if (!status.value) return '';
  
  const pending = status.value.pending_count;
  const processing = status.value.processing_count;
  const parts = [];

  // 看板上下文提示
  let contextPrefix = '';
  if (props.boardIds && props.boardIds.length > 0) {
      if (props.boardIds.length === 1) {
          // TODO: 这里最好能拿到 board name，但 status 接口没返回，前端 store 里有
          // 暂时简单处理
          contextPrefix = '当前看板：';
      } else {
          contextPrefix = `当前 ${props.boardIds.length} 个看板：`;
      }
  }

  if (pending > 0) {
    parts.push(`${pending} 条反馈待整理`);
  }
  if (processing > 0) {
    parts.push(`${processing} 条正在处理`);
  }
  
  if (parts.length === 0) return '所有反馈已整理完成';

  return (contextPrefix ? contextPrefix : '') + parts.join('，');
});

// 格式化时间
const formattedLastRun = computed(() => {
  if (!status.value?.last_run_at) return '从未运行';
  
  const date = new Date(status.value.last_run_at);
  return date.toLocaleString('zh-CN', { 
    month: 'numeric', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
});

// 触发聚类
const emit = defineEmits<{
  (e: 'trigger-clustering'): void;
}>();

const handleTrigger = () => {
  emit('trigger-clustering');
};

// 刷新状态
const refresh = () => {
  loadStatus();
};

defineExpose({ refresh });
</script>

<template>
  <div v-if="showBanner" class="clustering-status-banner">
    <a-alert
      :type="bannerType"
      show-icon
      closable
    >
      <template #message>
        <div class="banner-content">
          <span class="status-text">
            <span class="icon" :class="bannerType">
              <span v-if="status?.processing_count" class="processing-icon">⏳</span>
              <span v-else>📊</span>
            </span>
            {{ statusText }}
          </span>
          <span class="last-run">
            上次运行: {{ formattedLastRun }}
          </span>
        </div>
      </template>
      <template #action>
        <a-button 
          size="small" 
          type="primary"
          :loading="(status?.processing_count ?? 0) > 0"
          :disabled="(status?.processing_count ?? 0) > 0"
          @click="handleTrigger"
        >
          {{ (status?.processing_count ?? 0) > 0 ? '处理中...' : '立即处理' }}
        </a-button>
      </template>
    </a-alert>
  </div>
</template>

<style scoped>
.clustering-status-banner {
  margin-bottom: 16px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.icon {
  font-size: 16px;
}

.icon.warning {
  color: #faad14;
}

.icon.info {
  color: #1890ff;
}

.processing-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.last-run {
  font-size: 12px;
  color: #8c8c8c;
}
</style>
