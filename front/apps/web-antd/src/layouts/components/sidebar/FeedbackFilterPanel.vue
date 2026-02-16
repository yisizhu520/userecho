<script lang="ts" setup>
import { Input, RadioGroup, RadioButton, Select, SelectOption, Button, Checkbox, CheckboxGroup } from 'ant-design-vue';
import { ref, onMounted } from 'vue';
import { getBoardList, type BoardApi } from '#/api';

interface Props {
  isUrgent?: string[];
  hasTopic?: string[];
  clusteringStatus?: string[];
  boardIds?: string[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:isUrgent': [value: string[]];
  'update:hasTopic': [value: string[]];
  'update:clusteringStatus': [value: string[]];
  'update:boardIds': [value: string[]];
}>();

// Board 列表
const boards = ref<BoardApi.Board[]>([]);
const boardsLoading = ref(false);

// 加载 Board 列表
async function loadBoards() {
  try {
    boardsLoading.value = true;
    const response = await getBoardList();
    boards.value = response.boards || [];
  } catch (error) {
    console.error('Failed to load boards:', error);
  } finally {
    boardsLoading.value = false;
  }
}

onMounted(() => {
  loadBoards();
});
</script>

<template>
  <div class="px-4 py-4 bg-transparent">
    <!-- Board 筛选 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        看板筛选
      </label>
      <CheckboxGroup
        :value="boardIds"
        @update:value="emit('update:boardIds', $event)"
        class="w-full"
      >
        <div v-if="boardsLoading" class="text-xs text-gray-400 py-2">
          加载中...
        </div>
        <div v-else-if="boards.length === 0" class="text-xs text-gray-400 py-2">
          暂无看板
        </div>
        <div v-else class="flex flex-col gap-2">
          <Checkbox
            v-for="board in boards"
            :key="board.id"
            :value="board.id"
            class="ml-0"
          >
            <span class="text-sm">{{ board.name }}</span>
            <span class="text-xs text-gray-400 ml-1">({{ board.feedback_count }})</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- 紧急程度 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        紧急程度
      </label>
      <CheckboxGroup
        :value="isUrgent"
        @update:value="emit('update:isUrgent', $event)"
        class="w-full"
      >
        <div class="flex flex-col gap-2">
          <Checkbox value="true" class="ml-0">
            <span class="text-sm">紧急</span>
          </Checkbox>
          <Checkbox value="false" class="ml-0">
            <span class="text-sm">常规</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- 是否已归类 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        归类状态
      </label>
      <CheckboxGroup
        :value="hasTopic"
        @update:value="emit('update:hasTopic', $event)"
        class="w-full"
      >
        <div class="flex flex-col gap-2">
          <Checkbox value="true" class="ml-0">
            <span class="text-sm">已归类</span>
          </Checkbox>
          <Checkbox value="false" class="ml-0">
            <span class="text-sm">未归类</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- AI 状态 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        AI 状态
      </label>
      <CheckboxGroup
        :value="clusteringStatus"
        @update:value="emit('update:clusteringStatus', $event)"
        class="w-full"
      >
        <div class="flex flex-col gap-2">
          <Checkbox value="pending" class="ml-0">
            <span class="text-sm">待处理</span>
          </Checkbox>
          <Checkbox value="processing" class="ml-0">
            <span class="text-sm">处理中</span>
          </Checkbox>
          <Checkbox value="clustered" class="ml-0">
            <span class="text-sm">已处理</span>
          </Checkbox>
          <Checkbox value="failed" class="ml-0">
            <span class="text-sm">失败</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>
  </div>
</template>
