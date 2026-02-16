<script lang="ts" setup>
import BoardSelector from './BoardSelector.vue';
import SidebarFilters from './SidebarFilters.vue';
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex-1 overflow-y-auto custom-scrollbar">
       <BoardSelector />
       <div class="mx-4 my-2 border-t border-gray-100 dark:border-gray-800"></div>
       <SidebarFilters />
    </div>
    
    <div class="p-4 text-xs text-center text-gray-400">
      Powered by Feedalyze
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
