<script lang="ts" setup>
import { ref } from 'vue';
import { Checkbox, Divider } from 'ant-design-vue';

const boards = ref([
  { label: 'Feature Requests', value: 'feature-requests', count: 12 },
  { label: 'Bug Reports', value: 'bug-reports', count: 5 },
  { label: 'General Feedback', value: 'general', count: 8 },
]);

const state = ref({
  indeterminate: true,
  checkAll: false,
  checkedList: ['feature-requests'],
});

const onCheckAllChange = (e: any) => {
  Object.assign(state.value, {
    checkedList: e.target.checked ? boards.value.map(b => b.value) : [],
    indeterminate: false,
  });
};
</script>

<template>
  <div class="px-4 py-4">
    <div class="flex items-center justify-between mb-2">
      <span class="text-xs font-semibold text-gray-500 uppercase">Boards</span>
      <span class="text-xs text-primary cursor-pointer hover:underline">Select All</span>
    </div>

    <div class="flex flex-col gap-2">
       <Checkbox 
        v-for="board in boards" 
        :key="board.value"
        class="!ml-0"
       >
        <div class="flex items-center justify-between w-full">
           <span>{{ board.label }}</span>
           <span class="text-xs text-gray-400">{{ board.count }}</span>
        </div>
       </Checkbox>
    </div>
  </div>
</template>
