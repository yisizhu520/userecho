<script lang="ts" setup>
import FeedbackFilterPanel from './FeedbackFilterPanel.vue';

interface Props {
  searchQuery?: string;
  searchMode?: 'keyword' | 'semantic';
  isUrgent?: string[];
  derivedStatus?: string[];
  boardIds?: string[];
  dateRange?: [string, string] | null;
}

defineProps<Props>();

const emit = defineEmits<{
  'update:searchQuery': [value: string];
  'update:searchMode': [value: 'keyword' | 'semantic'];
  'update:isUrgent': [value: string[]];
  'update:derivedStatus': [value: string[]];
  'update:boardIds': [value: string[]];
  'update:dateRange': [value: [string, string] | null];
  'search': [];
}>();
</script>

<template>
  <div class="h-full flex flex-col bg-transparent">
    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <!-- BoardSelector 暂时注释，未来多看板功能时启用 -->
      <!-- <BoardSelector /> -->
      <!-- <div class="mx-4 my-2 border-t border-gray-100 dark:border-gray-800"></div> -->
      
      <FeedbackFilterPanel
        :search-query="searchQuery"
        :search-mode="searchMode"
        :is-urgent="isUrgent"
        :derived-status="derivedStatus"
        :board-ids="boardIds"
        :date-range="dateRange"
        @update:search-query="emit('update:searchQuery', $event)"
        @update:search-mode="emit('update:searchMode', $event)"
        @update:is-urgent="emit('update:isUrgent', $event)"
        @update:derived-status="emit('update:derivedStatus', $event)"
        @update:board-ids="emit('update:boardIds', $event)"
        @update:date-range="emit('update:dateRange', $event)"
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

