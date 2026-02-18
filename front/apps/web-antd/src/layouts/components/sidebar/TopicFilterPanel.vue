<script lang="ts" setup>
import { Checkbox, CheckboxGroup, RangePicker, Select } from 'ant-design-vue';
import { ref, onMounted, watch } from 'vue';
import { TOPIC_STATUSES, TOPIC_CATEGORIES, getBoardList, type BoardApi } from '#/api';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';

interface Props {
  status?: string[];
  category?: string[];
  boardIds?: string[];
  dateRange?: [string, string] | null;
}

defineProps<Props>();

const emit = defineEmits<{
  'update:status': [value: string[]];
  'update:category': [value: string[]];
  'update:boardIds': [value: string[]];
  'update:dateRange': [value: [string, string] | null];
}>();

// Board 列表
const boards = ref<BoardApi.Board[]>([]);
const boardsLoading = ref(false);

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

// 当前选中的相对日期 key
const selectedDateKey = ref<string>('all');

// 自定义日期范围值
const customDateRange = ref<[Dayjs, Dayjs] | null>(null);

// 相对日期选项
const dateRangeOptions = [
  { label: '全部时间', value: 'all' },
  { label: '今天', value: 'today' },
  { label: '最近7天', value: 'last7days' },
  { label: '本周', value: 'thisWeek' },
  { label: '上周', value: 'lastWeek' },
  { label: '本月', value: 'thisMonth' },
  { label: '上月', value: 'lastMonth' },
  { label: '本季度', value: 'thisQuarter' },
  { label: '上季度', value: 'lastQuarter' },
  { label: '本半年', value: 'thisHalf' },
  { label: '上半年', value: 'lastHalf' },
  { label: '自定义范围', value: 'custom' },
];

// 计算相对日期范围
const getDateRange = (key: string): [string, string] | null => {
  const today = dayjs();
  switch (key) {
    case 'all':
      return null;
    case 'today':
      return [today.format('YYYY-MM-DD'), today.format('YYYY-MM-DD')];
    case 'last7days':
      return [today.subtract(6, 'day').format('YYYY-MM-DD'), today.format('YYYY-MM-DD')];
    case 'thisWeek':
      return [today.startOf('week').format('YYYY-MM-DD'), today.format('YYYY-MM-DD')];
    case 'lastWeek':
      return [
        today.subtract(1, 'week').startOf('week').format('YYYY-MM-DD'),
        today.subtract(1, 'week').endOf('week').format('YYYY-MM-DD'),
      ];
    case 'thisMonth':
      return [today.startOf('month').format('YYYY-MM-DD'), today.format('YYYY-MM-DD')];
    case 'lastMonth':
      return [
        today.subtract(1, 'month').startOf('month').format('YYYY-MM-DD'),
        today.subtract(1, 'month').endOf('month').format('YYYY-MM-DD'),
      ];
    case 'thisQuarter':
      return [today.startOf('quarter').format('YYYY-MM-DD'), today.format('YYYY-MM-DD')];
    case 'lastQuarter':
      return [
        today.subtract(1, 'quarter').startOf('quarter').format('YYYY-MM-DD'),
        today.subtract(1, 'quarter').endOf('quarter').format('YYYY-MM-DD'),
      ];
    case 'thisHalf':
      // 本半年：1-6月或7-12月
      const currentMonth = today.month();
      const halfStartMonth = currentMonth < 6 ? 0 : 6;
      return [
        today.month(halfStartMonth).startOf('month').format('YYYY-MM-DD'),
        today.format('YYYY-MM-DD'),
      ];
    case 'lastHalf':
      // 上半年：如果当前在下半年，返回上半年(1-6月)；如果在上半年，返回去年下半年(7-12月)
      const currentMonth2 = today.month();
      if (currentMonth2 < 6) {
        // 当前在上半年，返回去年下半年
        return [
          today.subtract(1, 'year').month(6).startOf('month').format('YYYY-MM-DD'),
          today.subtract(1, 'year').month(11).endOf('month').format('YYYY-MM-DD'),
        ];
      } else {
        // 当前在下半年，返回今年上半年
        return [
          today.month(0).startOf('month').format('YYYY-MM-DD'),
          today.month(5).endOf('month').format('YYYY-MM-DD'),
        ];
      }
    default:
      return null;
  }
};

// 点击相对日期选项
const handleQuickDateClick = (key: string) => {
  selectedDateKey.value = key;
  if (key === 'custom') {
    // 切换到自定义模式，等待用户选择
    return;
  }
  customDateRange.value = null;
  const range = getDateRange(key);
  emit('update:dateRange', range);
};

// 自定义日期范围变化
const handleCustomDateChange = (dates: [Dayjs, Dayjs] | null) => {
  customDateRange.value = dates;
  if (dates && dates[0] && dates[1]) {
    emit('update:dateRange', [
      dates[0].format('YYYY-MM-DD'),
      dates[1].format('YYYY-MM-DD'),
    ]);
  } else {
    emit('update:dateRange', null);
  }
};

// 监听下拉框选择，如果不是自定义，清空 RangePicker
watch(selectedDateKey, (key) => {
  if (key !== 'custom') {
    customDateRange.value = null;
  }
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

    <!-- 日期范围筛选 -->
    <div class="mb-4">
      <label class="text-xs font-semibold text-gray-500 uppercase mb-2 block">
        日期范围
      </label>
      <Select
        v-model:value="selectedDateKey"
        size="small"
        class="w-full"
        :options="dateRangeOptions"
        @change="handleQuickDateClick"
      />
      <!-- 自定义日期范围（仅当选择“自定义范围”时显示） -->
      <RangePicker
        v-if="selectedDateKey === 'custom'"
        v-model:value="customDateRange"
        size="small"
        class="w-full mt-2"
        :placeholder="['开始日期', '结束日期']"
        @change="handleCustomDateChange"
      />
    </div>
  </div>
</template>

<style scoped>
/* 无需额外样式 */
</style>
