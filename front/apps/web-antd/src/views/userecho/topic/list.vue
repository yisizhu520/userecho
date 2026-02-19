<script setup lang="ts">
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Topic,
  CreateTopicParams,
  UpdateTopicParams,
} from '#/api';

import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getTopicList,
  createTopic,
  updateTopic,
} from '#/api';
import { getBoardList } from '#/api/userecho/board';
import { TOPIC_CATEGORIES } from '#/api';
import {
  categoryIcons,
  getCategoryConfig,
  getStatusConfig,
  topicFormSchema,
  useColumns,
} from '#/views/userecho/topic/data';
import { useFilterStorage } from '#/composables/useFilterStorage';
import TopicFilterSidebar from '#/layouts/components/sidebar/TopicFilterSidebar.vue';

const router = useRouter();

/**
 * 响应式布局检测
 */
const isMobile = ref(false);
const drawerVisible = ref(false);

const handleMediaChange = (e: MediaQueryListEvent | MediaQueryList) => {
  isMobile.value = e.matches;
  if (!e.matches) {
    drawerVisible.value = false; // 切换到桌面端时关闭抽屉
  }
};

/**
 * 筛选条件状态
 */
/**
 * 筛选条件状态
 */
const { state: filterValues } = useFilterStorage({
  key: 'topic_filter_values',
  defaultValue: {
    search_query: '',
    status: ['pending', 'planned', 'in_progress'],
    category: TOPIC_CATEGORIES.map((c) => c.value),
    board_ids: [] as string[],
    date_range: null as [string, string] | null,
  },
});

/**
 * 初始化逻辑：加载 Board 并处理默认选中
 */
const initBoardSelection = async () => {
  try {
    const response = await getBoardList();
    const boards = response || [];
    if (boards.length > 0 && filterValues.value && (filterValues.value.board_ids?.length ?? 0) === 0) {
      // 只有在没有存储值时才默认选中第一个
      filterValues.value.board_ids = [boards[0].id];
    }
  } catch (error) {
    console.error('Failed to init board selection:', error);
  }
};

/**
 * 优先级颜色计算
 */
function getPriorityColor(score: number): string {
  if (score >= 15) return 'red';
  if (score >= 10) return 'orange';
  if (score >= 5) return 'blue';
  return 'gray';
}



/**
 * 表格配置
 */
const gridOptions: VxeTableGridOptions<Topic> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  height: '100%',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: true,
    refreshOptions: {
      code: 'query',
    },
    custom: true,
    zoom: true,
  },
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          // 过滤掉空字符串值，只传递有效的筛选参数
          const queryParams: any = {
            skip: (page.currentPage - 1) * page.pageSize,
            limit: page.pageSize,
          };
          
          if (filterValues.value.search_query) {
            queryParams.search_query = filterValues.value.search_query;
            queryParams.search_mode = 'keyword'; // MVP阶段只用关键词搜索
          }
          if (filterValues.value.status && filterValues.value.status.length > 0) {
            queryParams.status = filterValues.value.status;
          }
          if (filterValues.value.category && filterValues.value.category.length > 0) {
            queryParams.category = filterValues.value.category;
          }
          if (filterValues.value.board_ids && filterValues.value.board_ids.length > 0) {
            queryParams.board_ids = filterValues.value.board_ids;
          }
          if (filterValues.value.date_range && filterValues.value.date_range.length === 2) {
            queryParams.date_from = filterValues.value.date_range[0];
            queryParams.date_to = filterValues.value.date_range[1];
          }
          
          const data = await getTopicList(queryParams);

          // vxe-table 期望的返回格式（根据全局 response 配置）
          return {
            items: data,           // 数据数组
            total: data.length,    // 当前查询到的记录数
          };
        } catch (error: any) {
          message.error(error.message || '查询失败，请稍后重试');
          throw error;
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

/**
 * 触发搜索
 */
function handleSearch() {
  gridApi.query();
}

/**
 * 监听筛选条件变化，自动触发查询
 */
watch(
  () => [
    filterValues.value.status,
    filterValues.value.category,
    filterValues.value.board_ids,
    filterValues.value.date_range,
  ],
  () => {
    handleSearch();
  },
  { deep: true }
);

function onRefresh() {
  gridApi.query();
}

/**
 * 操作按钮点击事件
 */
function onActionClick({ code, row }: OnActionClickParams<Topic>) {
  switch (code) {
    case 'detail': {
      router.push(`/app/topic/detail/${row.id}`);
      break;
    }
    case 'edit': {
      editTopicId.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
    case 'delete': {
      // TODO: 实现删除逻辑
      message.info('删除功能待实现');
      break;
    }
  }
}

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: topicFormSchema,
});

const editTopicId = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  title: '编辑主题',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await editFormApi.getValues<UpdateTopicParams>();
      try {
        await updateTopic(editTopicId.value, data);
        message.success('更新成功');
        await editModalApi.close();
        onRefresh();
      } catch {
        message.error('更新失败');
      } finally {
        editModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<any>();
      editFormApi.resetForm();
      if (data) {
        editFormApi.setValues(data);
      }
    }
  },
});

/**
 * 新建表单
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: topicFormSchema,
});

const [addModal, addModalApi] = useVbenModal({
  title: '新建主题',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateTopicParams>();
      try {
        await createTopic(data);
        message.success('创建成功');
        await addModalApi.close();
        onRefresh();
      } catch {
        message.error('创建失败');
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      addFormApi.resetForm();
    }
  },
});

onMounted(() => {
  // 初始化看板选中
  initBoardSelection();

  // 初始化响应式检测
  const mediaQuery = window.matchMedia('(max-width: 767px)');
  handleMediaChange(mediaQuery);
  mediaQuery.addEventListener('change', handleMediaChange);
  
  // 保存 mediaQuery 引用以便清理
  (window as any).__topicMediaQuery = mediaQuery;
});

onBeforeUnmount(() => {
  // 清理响应式检测监听器
  const mediaQuery = (window as any).__topicMediaQuery;
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleMediaChange);
    delete (window as any).__topicMediaQuery;
  }
});
</script>

<template>
  <div class="topic-list-container">
    <div class="topic-content-wrapper">
      <!-- 左侧栏 - 仅桌面端显示 -->
      <div v-if="!isMobile" class="topic-sidebar">
        <TopicFilterSidebar
          v-model:status="filterValues.status"
          v-model:category="filterValues.category"
          v-model:board-ids="filterValues.board_ids"
          v-model:date-range="filterValues.date_range"
        />
      </div>
      
      <!-- 右侧内容区域 -->
      <div class="topic-main-content" :class="isMobile ? 'p-2' : 'p-2'">
        <!-- 移动端汉堡菜单按钮 -->
        <VbenButton 
          v-if="isMobile" 
          class="mb-3"
          variant="outline"
          @click="drawerVisible = true"
        >
          <span class="iconify lucide--menu mr-2" />
          筛选条件
        </VbenButton>
        
        <div class="topic-grid-wrapper">
          <Grid>
          <template #toolbar-actions>
            <!-- 搜索框 -->
            <a-input
              v-model:value="filterValues.search_query"
              placeholder="搜索主题标题..."
              allow-clear
              @pressEnter="handleSearch"
              style="width: 300px;"
              class="mr-3"
            >
              <template #prefix>
                <span class="iconify lucide--search" />
              </template>
            </a-input>
            
            <VbenButton @click="() => addModalApi.open()">
              <MaterialSymbolsAdd class="size-5" />
              手动创建主题
            </VbenButton>
          <VbenButton variant="outline" @click="() => router.push('/app/feedback/list')">
            <span class="iconify lucide--inbox" />
            查看反馈列表
          </VbenButton>
          </template>

          <!-- 主题标题（带 AI 标识） -->
          <template #title="{ row }">
            <div class="topic-title">
              <span>{{ row.title }}</span>
              <a-tag v-if="row.ai_generated" color="purple" size="small" class="ml-2">
                <span class="iconify lucide--sparkles" /> AI
              </a-tag>
            </div>
          </template>

          <!-- 分类 -->
          <template #category="{ row }">
            <a-tag :color="getCategoryConfig(row.category).value === 'bug' ? 'red' : 'blue'">
              {{ categoryIcons[row.category] || '' }}
              {{ getCategoryConfig(row.category).label }}
            </a-tag>
          </template>

          <!-- 状态 -->
          <template #status="{ row }">
            <a-tag :color="getStatusConfig(row.status).color">
              {{ getStatusConfig(row.status).label }}
            </a-tag>
          </template>

          <!-- 优先级评分 -->
          <template #priority_score="{ row }">
            <div class="priority-score-cell">
              <!-- 已有评分：显示总分徽章 -->
              <a-popover v-if="row.priority_score" title="评分详情">
                <template #content>
                  <div class="w-48">
                    <div v-if="row.priority_score.details?.strategic_keywords_matched?.length" class="mb-2">
                      <div class="text-xs text-gray-500 mb-1">战略匹配:</div>
                      <div class="flex flex-wrap gap-1">
                        <a-tag v-for="kw in row.priority_score.details.strategic_keywords_matched" :key="kw" color="purple" size="small">
                          {{ kw }}
                        </a-tag>
                      </div>
                    </div>
                    <div v-if="row.priority_score.details?.urgent_ratio !== undefined">
                      <span class="text-xs text-gray-500">紧急反馈占比: </span>
                      <span :class="row.priority_score.details.urgent_ratio > 0.3 ? 'text-red-500 font-bold' : ''">
                        {{ (row.priority_score.details.urgent_ratio * 100).toFixed(0) }}%
                      </span>
                    </div>
                    <div class="mt-2 pt-2 border-t border-gray-100 flex justify-between text-xs text-gray-400">
                      <span>反馈数: {{ row.feedback_count }}</span>
                      <span>时效分: {{ row.priority_score.details?.recency_score ?? '-' }}</span>
                    </div>
                  </div>
                </template>
                <a-tag
                  :color="getPriorityColor(row.priority_score.total_score)"
                  style="font-size: 14px; font-weight: bold; cursor: pointer"
                  @click.stop="router.push(`/app/topic/detail/${row.id}`)"
                >
                  {{ row.priority_score.total_score.toFixed(1) }}
                </a-tag>
              </a-popover>
              <!-- 未评分：提示去评分 -->
              <span v-else style="color: #999; font-size: 12px">
                未评分
              </span>
            </div>
          </template>

          <!-- 反馈数量 -->
          <template #feedback_count="{ row }">
          <a-badge
            :count="row.feedback_count"
            :number-style="{ backgroundColor: '#52c41a' }"
            style="cursor: pointer"
            @click="router.push(`/app/topic/detail/${row.id}`)"
          />
          </template>

          <!-- AI 生成标识 -->
          <template #ai_generated="{ row }">
            <a-tag v-if="row.ai_generated" color="purple">
              <span class="iconify lucide--sparkles" /> AI
            </a-tag>
            <a-tag v-else color="default">手动</a-tag>
          </template>
          </Grid>
        </div>
      </div>
      
      <!-- 移动端抽屉 -->
      <a-drawer
        v-model:open="drawerVisible"
        title="筛选条件"
        placement="left"
        :width="280"
        :body-style="{ padding: 0 }"
      >
        <TopicFilterSidebar
          v-model:status="filterValues.status"
          v-model:category="filterValues.category"
          v-model:board-ids="filterValues.board_ids"
          v-model:date-range="filterValues.date_range"
        />
      </a-drawer>
    </div>

    <!-- 编辑弹窗 -->
    <editModal>
      <EditForm />
    </editModal>

    <!-- 新建弹窗 -->
    <addModal>
      <AddForm />
    </addModal>
  </div>
</template>

<style scoped>
/* 整体容器高度控制 */
.topic-list-container {
  height: calc(100vh - 64px); /* 减去顶部导航栏高度 */
  overflow: hidden;
  background: hsl(var(--background));
}

.topic-content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background: hsl(var(--background));
}

.topic-sidebar {
  height: 100%;
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid hsl(var(--border) / 0.3);
  overflow-y: auto;
  background: hsl(var(--background));
}

.topic-main-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: hsl(var(--background));
}

.topic-grid-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0; /* 重要：允许 flex 子元素收缩 */
}

.topic-title {
  display: flex;
  align-items: center;
}

/* 搜索模式切换动画 */
:deep(.search-mode-radio) {
  .ant-radio-button-wrapper {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  .ant-radio-button-wrapper::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: currentColor;
    opacity: 0;
    transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .ant-radio-button-wrapper:hover::before {
    opacity: 0.08;
  }

  .ant-radio-button-wrapper-checked {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .ant-radio-button-wrapper-checked::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
    transform: translate(-50%, -50%) scale(0);
    animation: ripple 0.6s ease-out;
  }
}

@keyframes ripple {
  to {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}
</style>
