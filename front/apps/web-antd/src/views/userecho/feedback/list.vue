<script setup lang="ts">
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { Feedback } from '#/api';

import { computed, onBeforeUnmount, ref, onMounted, watch } from 'vue';
import { formatToSmartTime, formatToDateTime } from '#/utils/dateUtil';
import { useRoute } from 'vue-router';

import { VbenButton } from '@vben/common-ui';

import { message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getFeedbackList,
  deleteFeedback,
  triggerClustering,
} from '#/api';
import { useBoardStore } from '#/store';
import { useColumns } from '#/views/userecho/feedback/data';
import FeedbackFilterSidebar from '#/layouts/components/sidebar/FeedbackFilterSidebar.vue';
import FeedbackToolbar from './components/FeedbackToolbar.vue';
import FeedbackModal from './components/FeedbackModal.vue';
import ClusteringProgressModal from './components/ClusteringProgressModal.vue';
import MergeSuggestionsModal from './components/MergeSuggestionsModal.vue';
import ClusteringStatusBanner from './components/ClusteringStatusBanner.vue';

import ScreenshotCell from './components/ScreenshotCell.vue';

import { useFilterStorage } from '#/composables/useFilterStorage';

const route = useRoute();

// 检测是否为"我的反馈"模式
const isMyFeedbacksMode = computed(() => route.query.creator === 'me');

/**
 * 响应式布局检测
 */
const isMobile = ref(false);
const drawerVisible = ref(false);

const handleMediaChange = (e: MediaQueryListEvent | MediaQueryList) => {
  isMobile.value = e.matches;
  if (!e.matches) {
    drawerVisible.value = false;
  }
};

/**
 * 筛选条件状态持久化
 */
const { state: filterValues } = useFilterStorage({
  key: 'feedback_filter_values',
  defaultValue: {
    search_query: '',
    is_urgent: ['true', 'false'],
    derived_status: [] as string[], // 空数组表示不筛选
    board_ids: [] as string[],
    date_range: null as [string, string] | null,
  },
});

/**
 * Board Store
 */
const boardStore = useBoardStore();

/**
 * 初始化逻辑：加载 Board 并处理默认选中
 */
const initBoardSelection = async () => {
  try {
    await boardStore.refreshBoards();
    const boards = boardStore.boards;
    const filters = filterValues.value;
    if (boards.length > 0 && filters && (filters.board_ids?.length ?? 0) === 0) {
      filters!.board_ids = [boards[0]!.id];
    }
  } catch (error) {
    console.error('Failed to init board selection:', error);
  }
};

/**
 * 格式化相对时间
 */


/**
 * 表格配置
 */
const gridOptions: VxeTableGridOptions<Feedback> = {
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
  pagination: true,
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const queryParams: any = {
            skip: (page.currentPage - 1) * page.pageSize,
            limit: page.pageSize,
          };
          
          if (filterValues.value.search_query) {
            queryParams.search_query = filterValues.value.search_query;
            queryParams.search_mode = 'keyword';
          }
          if (filterValues.value.is_urgent && filterValues.value.is_urgent.length > 0) {
            queryParams.is_urgent = filterValues.value.is_urgent;
          }
          if (filterValues.value.derived_status && filterValues.value.derived_status.length > 0) {
            queryParams.derived_status = filterValues.value.derived_status;
          }
          if (filterValues.value.board_ids && filterValues.value.board_ids.length > 0) {
            queryParams.board_ids = filterValues.value.board_ids;
          }
          if (filterValues.value.date_range && filterValues.value.date_range.length === 2) {
            queryParams.date_from = filterValues.value.date_range[0];
            queryParams.date_to = filterValues.value.date_range[1];
          }
          // 支持"我的反馈"模式
          if (isMyFeedbacksMode.value) {
            queryParams.creator_me = true;
          }
          
          const data: any = await getFeedbackList(queryParams);

          return {
            items: data.items,
            total: data.total,
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
  filterValues,
  (newVal) => {
    console.log('[DEBUG] Filter values changed:', newVal);
    handleSearch();
  },
  { deep: true }
);

/**
 * 刷新表格
 * @param boardId 可选，如果传入则确保该 board 在筛选条件中
 */
function onRefresh(boardId?: string) {
  // 刷新聚类状态 Banner
  clusteringBannerRef.value?.refresh();

  // 如果传入了 boardId，且不在当前筛选条件中，则将其加入
  if (boardId && filterValues.value.board_ids && !filterValues.value.board_ids.includes(boardId)) {
    filterValues.value.board_ids = [...filterValues.value.board_ids, boardId];
    // filterValues 的 watch 会自动触发刷新，无需手动调用
    return;
  }
  gridApi.query();
}

/**
 * 操作按钮点击事件
 */
function onActionClick({ code, row }: OnActionClickParams<Feedback>) {
  switch (code) {
    case 'delete': {
      deleteFeedback(row.id).then(() => {
        message.success('删除成功');
        onRefresh();
        // 刷新 Board 数量
        boardStore.forceRefresh();
      }).catch(() => {
        message.error('删除失败');
      });
      break;
    }
    case 'edit': {
      feedbackModalRef.value?.openEdit(row);
      break;
    }
  }
}

/**
 * 组件引用
 */
const feedbackModalRef = ref<InstanceType<typeof FeedbackModal>>();
const clusteringBannerRef = ref<InstanceType<typeof ClusteringStatusBanner>>();

/**
 * AI 聚类
 */
const clusteringLoading = ref(false);
const clusteringModalOpen = ref(false);
const clusteringTaskId = ref<string>('');
const mergeSuggestionsOpen = ref(false);
const mergeSuggestions = ref<any[]>([]);

const handleTriggerClustering = async () => {
  try {
    clusteringLoading.value = true;
    clusteringModalOpen.value = true;
    clusteringTaskId.value = '';

    const resp: any = await triggerClustering({ async_mode: true });
    if (resp?.status === 'accepted' && resp?.task_id) {
      clusteringTaskId.value = resp.task_id;
      return;
    }

    // 兼容同步模式返回
    const result: any = resp;
    if (result?.status === 'skipped') {
      message.warning(result.message || '整理已跳过');
    } else {
      // 检查是否有合并建议
      if (result.merge_suggestions?.length > 0) {
        mergeSuggestions.value = result.merge_suggestions;
        // 稍后打开建议弹窗（等待进度弹窗关闭或用户点击）
        setTimeout(() => {
          mergeSuggestionsOpen.value = true;
        }, 500);
      }
      message.success(`整理完成：创建 ${result.topics_created ?? 0} 个需求，未关联 ${result.noise_count ?? 0} 条`);
    }
    onRefresh();
    clusteringModalOpen.value = false;
  } catch (error: any) {
    message.error(error.message || '整理失败，请稍后重试');
    clusteringModalOpen.value = false;
  } finally {
    clusteringLoading.value = false;
  }
};

const handleClusteringSuccess = (result: any) => {
  onRefresh();
  // 如果有合并建议，打开弹窗
  if (result.merge_suggestions?.length > 0) {
    mergeSuggestions.value = result.merge_suggestions;
    // 稍微延迟一下，体验更好
    setTimeout(() => {
      mergeSuggestionsOpen.value = true;
    }, 500);
  }
};


onMounted(() => {
  initBoardSelection();

  const mediaQuery = window.matchMedia('(max-width: 767px)');
  handleMediaChange(mediaQuery);
  mediaQuery.addEventListener('change', handleMediaChange);
  
  (window as any).__feedbackMediaQuery = mediaQuery;
});

onBeforeUnmount(() => {
  const mediaQuery = (window as any).__feedbackMediaQuery;
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleMediaChange);
    delete (window as any).__feedbackMediaQuery;
  }
});</script>

<template>
  <div class="feedback-list-container">
    <div class="feedback-content-wrapper">
      <!-- 左侧栏 - 仅桌面端显示 -->
      <div v-if="!isMobile" class="feedback-sidebar">
        <FeedbackFilterSidebar
          v-model:is-urgent="filterValues.is_urgent"
          v-model:derived-status="filterValues.derived_status"
          v-model:board-ids="filterValues.board_ids"
          v-model:date-range="filterValues.date_range"
        />
      </div>
      
      <!-- 右侧内容区域 -->
      <div class="feedback-main-content" :class="isMobile ? 'p-2' : 'p-2'">
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
        
        <!-- 智能整理状态横幅 -->
        <ClusteringStatusBanner 
          ref="clusteringBannerRef"
          @trigger-clustering="handleTriggerClustering"
        />
        
        <div class="feedback-grid-wrapper">
          <Grid>
          <template #toolbar-actions>
            <FeedbackToolbar
              v-model:search-query="filterValues.search_query"
              :clustering-loading="clusteringLoading"
              @search="handleSearch"
              @create="feedbackModalRef?.openCreate()"
              @screenshot="$router.push('/app/feedback/screenshot')"
              @import="$router.push('/app/feedback/import')"
              @clustering="handleTriggerClustering"
            />
          </template>

          <template #topic="{ row }">
            <span v-if="row.topic_id && row.topic_title">
              <a-tooltip :title="row.topic_title">
                <a-tag
                  color="blue"
                  style="cursor: pointer; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom;"
                  @click="$router.push(`/app/topic/detail/${row.topic_id}`)"
                >
                  {{ row.topic_title }}
                </a-tag>
              </a-tooltip>
            </span>
            <span v-else class="text-gray-400">未关联</span>
          </template>

          <template #derived_status="{ row }">
            <!-- 待处理: 未归类到需求 (pending/processing/failed/clustered无topic) -->
            <a-tag v-if="!row.topic_id" color="default">待处理</a-tag>
            <!-- 待评审: clustered + topic.status = 'review' -->
            <a-tag v-else-if="row.topic_status === 'review'" color="orange">待评审</a-tag>
            <!-- 已排期: clustered + topic.status = 'planned' -->
            <a-tag v-else-if="row.topic_status === 'planned'" color="purple">已排期</a-tag>
            <!-- 开发中: clustered + topic.status = 'in_progress' -->
            <a-tag v-else-if="row.topic_status === 'in_progress'" color="cyan">开发中</a-tag>
            <!-- 已解决: clustered + topic.status = 'completed' -->
            <a-tag v-else-if="row.topic_status === 'completed'" color="green">已解决</a-tag>
            <!-- 暂不处理: clustered + topic.status = 'ignored' -->
            <a-tag v-else-if="row.topic_status === 'ignored'" color="default">暂不处理</a-tag>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template #urgent="{ row }">
            <a-tag v-if="row.is_urgent" color="red">紧急</a-tag>
            <a-tag v-else color="default">常规</a-tag>
          </template>

          <template #screenshots="{ row }">
            <ScreenshotCell :images="row.images_metadata?.images" />
          </template>

          <template #submitted_at="{ row }">
            <a-tooltip :title="formatToDateTime(row.submitted_at)">
              <span class="text-gray-500">{{ formatToSmartTime(row.submitted_at) }}</span>
            </a-tooltip>
          </template>
        </Grid>
        </div>

        <!-- 反馈弹窗（创建/编辑统一） -->
        <FeedbackModal ref="feedbackModalRef" @success="onRefresh" />

        <!-- AI 智能整理进度弹窗 -->
        <ClusteringProgressModal
          v-model:open="clusteringModalOpen"
          :task-id="clusteringTaskId"
          @success="handleClusteringSuccess"
        />

        <!-- 合并建议弹窗 -->
        <MergeSuggestionsModal
          v-model:open="mergeSuggestionsOpen"
          :suggestions="mergeSuggestions"
          @refresh="onRefresh"
        />

      </div>
      
      <!-- 移动端抽屉 -->
      <a-drawer
        v-model:open="drawerVisible"
        title="筛选条件"
        placement="left"
        :width="280"
        :body-style="{ padding: 0 }"
      >
        <FeedbackFilterSidebar
          v-model:is-urgent="filterValues.is_urgent"
          v-model:derived-status="filterValues.derived_status"
          v-model:board-ids="filterValues.board_ids"
          v-model:date-range="filterValues.date_range"
        />
      </a-drawer>
    </div>
  </div>
</template>

<style scoped>
/* 整体容器高度控制 */
.feedback-list-container {
  height: calc(100vh - 64px);
  overflow: hidden;
  background: hsl(var(--background));
}

.feedback-content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background: hsl(var(--background));
}

.feedback-sidebar {
  height: 100%;
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid hsl(var(--border) / 0.3);
  overflow-y: auto;
  background: hsl(var(--background));
}

.feedback-main-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: hsl(var(--background));
}

.feedback-grid-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
</style>
