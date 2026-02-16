<script lang="ts" setup>
import { Input, RadioGroup, RadioButton, Select, SelectOption, Button, Checkbox, CheckboxGroup } from 'ant-design-vue';
import { ref, onMounted } from 'vue';
import { TOPIC_STATUSES, TOPIC_CATEGORIES, getBoardList, type BoardApi } from '#/api';

interface Props {
  searchQuery?: string;
  searchMode?: 'keyword' | 'semantic';
  status?: string;
  category?: string;
  boardIds?: string[];
}

defineProps<Props>();

const emit = defineEmits<{
  'update:searchQuery': [value: string];
  'update:searchMode': [value: 'keyword' | 'semantic'];
  'update:status': [value: string];
  'update:category': [value: string];
  'update:boardIds': [value: string[]];
  'search': [];
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
  <div class="px-4 py-4">
    <!-- 主题搜索 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        主题搜索
      </label>
      <Input
        :value="searchQuery"
        @update:value="emit('update:searchQuery', $event)"
        @pressEnter="emit('search')"
        placeholder="搜索主题标题..."
        allow-clear
        size="small"
      />
    </div>

    <!-- 搜索模式 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        搜索模式
      </label>
      <RadioGroup
        :value="searchMode"
        @update:value="emit('update:searchMode', $event)"
        button-style="solid"
        size="small"
        class="w-full flex"
      >
        <RadioButton value="keyword" class="flex-1 text-center">
          关键词 ⚡
        </RadioButton>
        <RadioButton value="semantic" class="flex-1 text-center">
          语义 🤖
        </RadioButton>
      </RadioGroup>
    </div>

    <!-- 主题状态 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        主题状态
      </label>
      <Select
        :value="status"
        @update:value="emit('update:status', $event)"
        allow-clear
        size="small"
        class="w-full"
      >
        <SelectOption
          v-for="item in TOPIC_STATUSES"
          :key="item.value"
          :value="item.value"
        >
          {{ item.label }}
        </SelectOption>
      </Select>
    </div>

    <!-- 主题分类 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        主题分类
      </label>
      <Select
        :value="category"
        @update:value="emit('update:category', $event)"
        allow-clear
        size="small"
        class="w-full"
      >
        <SelectOption
          v-for="item in TOPIC_CATEGORIES"
          :key="item.value"
          :value="item.value"
        >
          {{ item.label }}
        </SelectOption>
      </Select>
    </div>

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
            <span class="text-xs text-gray-400 ml-1">({{ board.topic_count }})</span>
          </Checkbox>
        </div>
      </CheckboxGroup>
    </div>

    <!-- 搜索按钮 -->
    <Button
      type="primary"
      block
      size="small"
      @click="emit('search')"
    >
      搜索
    </Button>
  </div>
</template>
