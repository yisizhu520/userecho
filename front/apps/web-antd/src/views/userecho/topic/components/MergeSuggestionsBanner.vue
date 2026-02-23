<script setup lang="ts">
/**
 * 待处理合并建议 Banner
 * 
 * 在 Topic 列表顶部展示，提醒用户有待处理的相似需求聚类
 */
import type { MergeSuggestion } from '#/api';

import { ref, onMounted } from 'vue';

import { getPendingMergeSuggestions } from '#/api';
import MergeSuggestionsModal from '#/views/userecho/feedback/components/MergeSuggestionsModal.vue';

const suggestions = ref<MergeSuggestion[]>([]);
const modalOpen = ref(false);
const loading = ref(false);

const fetchSuggestions = async () => {
  loading.value = true;
  try {
    suggestions.value = await getPendingMergeSuggestions();
  } catch (error) {
    console.error('Failed to fetch pending suggestions:', error);
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  fetchSuggestions();
  // 此时父组件可能也需要刷新列表，但不强求，主要处理完建议就行
};

onMounted(() => {
  fetchSuggestions();
});

defineExpose({
  refresh: fetchSuggestions,
});
</script>

<template>
  <div v-if="suggestions.length > 0" class="merge-suggestions-banner">
    <div class="banner-content">
      <div class="banner-icon">
        <span class="iconify lucide--sparkles text-purple-600" />
      </div>
      <div class="banner-text">
        AI 发现 <strong>{{ suggestions.length }}</strong> 个聚类与已有需求高度相似，建议进行合并处理
      </div>
      <a-button
        type="primary"
        size="small"
        ghost
        @click="modalOpen = true"
      >
        查看建议
      </a-button>
    </div>

    <MergeSuggestionsModal
      v-model:open="modalOpen"
      :suggestions="suggestions"
      @refresh="handleRefresh"
    />
  </div>
</template>

<style scoped>
.merge-suggestions-banner {
  background: linear-gradient(90deg, #f9f0ff 0%, #f0f5ff 100%);
  border-bottom: 1px solid #e6e6e6;
  padding: 12px 24px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 1200px;
  margin: 0 auto;
}

.banner-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.banner-text {
  flex: 1;
  font-size: 14px;
  color: #333;
}
</style>
