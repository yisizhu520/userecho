<script lang="ts" setup>
import { Checkbox, CheckboxGroup } from 'ant-design-vue';
import { ref, onMounted } from 'vue';
import { TOPIC_STATUSES, TOPIC_CATEGORIES, getBoardList, type BoardApi } from '#/api';

interface Props {
  status?: string[];
  category?: string[];
  boardIds?: string[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: string[]];
  'update:category': [value: string[]];
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
        @update:value="(val: any) => emit('update:boardIds', val)"
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
            <span class="text-xs text-gray-400 ml-1">({{ board.topic_count }})</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- 主题状态 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        主题状态
      </label>
      <CheckboxGroup
        :value="status"
        @update:value="(val: any) => emit('update:status', val)"
        class="w-full"
      >
        <div class="flex flex-col gap-2">
          <Checkbox
            v-for="item in TOPIC_STATUSES"
            :key="item.value"
            :value="item.value"
            class="ml-0"
          >
            <span class="text-sm">{{ item.label }}</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- 主题分类 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        主题分类
      </label>
      <CheckboxGroup
        :value="category"
        @update:value="(val: any) => emit('update:category', val)"
        class="w-full"
      >
        <div class="flex flex-col gap-2">
          <Checkbox
            v-for="item in TOPIC_CATEGORIES"
            :key="item.value"
            :value="item.value"
            class="ml-0"
          >
            <span class="text-sm">{{ item.label }}</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>
  </div>
</template>
