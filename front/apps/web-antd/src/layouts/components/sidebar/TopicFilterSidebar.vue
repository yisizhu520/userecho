<script lang="ts" setup>
import TopicFilterPanel from './TopicFilterPanel.vue';

interface Props {
  searchQuery?: string;
  searchMode?: 'keyword' | 'semantic';
  status?: string[];
  category?: string[];
  boardIds?: string[];
  dateRange?: [string, string] | null;
  viewMode?: 'list' | 'kanban';
}

defineProps<Props>();

const emit = defineEmits<{
  'update:searchQuery': [value: string];
  'update:searchMode': [value: 'keyword' | 'semantic'];
  'update:status': [value: string[]];
  'update:category': [value: string[]];
  'update:boardIds': [value: string[]];
  'update:dateRange': [value: [string, string] | null];
  'update:viewMode': [value: 'list' | 'kanban'];
  'search': [];
}>();
</script>

<template>
  <div class="h-full flex flex-col bg-transparent">
    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <!-- BoardSelector 暂时注释，未来多看板功能时启用 -->
      <!-- <BoardSelector /> -->
      <!-- <div class="mx-4 my-2 border-t border-gray-100 dark:border-gray-800"></div> -->
      
      <TopicFilterPanel
        :search-query="searchQuery"
        :search-mode="searchMode"
        :status="status"
        :category="category"
        :board-ids="boardIds"
        :date-range="dateRange"
        :view-mode="viewMode"
        @update:search-query="emit('update:searchQuery', $event)"
        @update:search-mode="emit('update:searchMode', $event)"
        @update:status="emit('update:status', $event)"
        @update:category="emit('update:category', $event)"
        @update:board-ids="emit('update:boardIds', $event)"
        @update:date-range="emit('update:dateRange', $event)"
        @update:view-mode="emit('update:viewMode', $event)"
        @search="emit('search')"
      />
    </div>
    
    <div class="p-4 text-xs text-center text-gray-400">
      Powered by userecho
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 4px;
}
</style>
