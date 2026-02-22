<script setup lang="ts">
import { VbenButton } from '@vben/common-ui';

interface Props {
  searchQuery: string;
  clusteringLoading?: boolean;
}

interface Emits {
  (e: 'update:searchQuery', value: string): void;
  (e: 'search'): void;
  (e: 'create'): void;
  (e: 'screenshot'): void;
  (e: 'import'): void;
  (e: 'clustering'): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const handleSearchQueryUpdate = (value: string) => {
  emit('update:searchQuery', value);
};

const handleSearch = () => {
  emit('search');
};
</script>

<template>
  <div class="feedback-actions-group">
    <!-- 搜索框 -->
    <a-input
      :value="searchQuery"
      placeholder="搜索反馈内容..."
      allow-clear
      @update:value="handleSearchQueryUpdate"
      @pressEnter="handleSearch"
      style="width: 300px;"
      class="mr-3"
    >
      <template #prefix>
        <span class="iconify lucide--search" />
      </template>
    </a-input>
    
    <div class="add-actions">
      <VbenButton type="primary" @click="emit('create')">
        <span class="iconify lucide--pencil mr-2" />
        手动录入
      </VbenButton>
      <VbenButton @click="emit('screenshot')">
        <span class="iconify lucide--camera mr-2" />
        截图识别
      </VbenButton>
      <VbenButton @click="emit('import')">
        <span class="iconify lucide--upload mr-2" />
        批量导入
      </VbenButton>
    </div>
    <VbenButton
      variant="outline"
      @click="emit('clustering')"
      :loading="clusteringLoading"
    >
      <span class="iconify lucide--sparkles mr-2" />
      AI 智能整理
    </VbenButton>
  </div>
</template>

<style scoped>
.feedback-actions-group {
  display: flex;
  gap: 16px;
  align-items: center;
  width: 100%;
}

.add-actions {
  display: flex;
  gap: 12px;
  flex: 1;
}

.add-actions > button {
  flex: 1;
  min-width: 120px;
}
</style>
