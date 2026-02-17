<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { Feedback } from '#/api';

import { computed, onBeforeUnmount, ref, onMounted, watch } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getFeedbackList,
  deleteFeedback,
  triggerClustering,
} from '#/api';
import { getBoardList } from '#/api/userecho/board';
import { useColumns } from '#/views/userecho/feedback/data';
import FeedbackFilterSidebar from '#/layouts/components/sidebar/FeedbackFilterSidebar.vue';
import FeedbackToolbar from './components/FeedbackToolbar.vue';
import FeedbackCreateModal from './components/FeedbackCreateModal.vue';
import FeedbackEditModal from './components/FeedbackEditModal.vue';
import ClusteringProgressModal from './components/ClusteringProgressModal.vue';

import { useFilterStorage } from '#/composables/useFilterStorage';

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
    has_topic: ['true', 'false'],
    clustering_status: [] as string[],
    board_ids: [] as string[],
  },
});

/**
 * 初始化逻辑：加载 Board 并处理默认选中
 */
const initBoardSelection = async () => {
  try {
    const response = await getBoardList();
    const boards = response.boards || [];
    if (boards.length > 0 && (filterValues.value?.board_ids?.length ?? 0) === 0) {
      filterValues.value.board_ids = [boards[0].id];
    }
  } catch (error) {
    console.error('Failed to init board selection:', error);
  }
};

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
          if (filterValues.value.has_topic && filterValues.value.has_topic.length > 0) {
            queryParams.has_topic = filterValues.value.has_topic;
          }
          if (filterValues.value.clustering_status && filterValues.value.clustering_status.length > 0) {
            queryParams.clustering_status = filterValues.value.clustering_status;
          }
          if (filterValues.value.board_ids && filterValues.value.board_ids.length > 0) {
            queryParams.board_ids = filterValues.value.board_ids;
          }
          
          const data = await getFeedbackList(queryParams);

          return {
            items: data,
            total: data.length,
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
    filterValues.value.is_urgent,
    filterValues.value.has_topic,
    filterValues.value.clustering_status,
    filterValues.value.board_ids,
  ],
  () => {
    handleSearch();
  },
  { deep: true }
);

/**
 * 刷新表格
 */
function onRefresh() {
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
      }).catch(() => {
        message.error('删除失败');
      });
      break;
    }
    case 'edit': {
      editModalRef.value?.open(row);
      break;
    }
  }
}

/**
 * 组件引用
 */
const createModalRef = ref<InstanceType<typeof FeedbackCreateModal>>();
const editModalRef = ref<InstanceType<typeof FeedbackEditModal>>();

/**
 * AI 聚类
 */
const clusteringLoading = ref(false);
const clusteringModalOpen = ref(false);
const clusteringTaskId = ref<string>('');

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
      message.warning(result.message || '聚类已跳过');
    } else {
      message.success(`聚类完成：创建 ${result.topics_created ?? 0} 个主题，噪声 ${result.noise_count ?? 0} 条`);
    }
    onRefresh();
    clusteringModalOpen.value = false;
  } catch (error: any) {
    message.error(error.message || '聚类失败，请稍后重试');
    clusteringModalOpen.value = false;
  } finally {
    clusteringLoading.value = false;
  }
};

const handleClusteringSuccess = () => {
  onRefresh();
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
          v-model:has-topic="filterValues.has_topic"
          v-model:clustering-status="filterValues.clustering_status"
          v-model:board-ids="filterValues.board_ids"
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
        
        <div class="feedback-grid-wrapper">
          <Grid>
          <template #toolbar-actions>
            <FeedbackToolbar
              v-model:search-query="filterValues.search_query"
              :clustering-loading="clusteringLoading"
              @search="handleSearch"
              @create="createModalRef?.open()"
              @screenshot="$router.push('/app/feedback/screenshot')"
              @import="$router.push('/app/feedback/import')"
              @clustering="handleTriggerClustering"
            />
          </template>

          <template #topic="{ row }">
            <span v-if="row.topic_id && row.topic_title">
              <a-tag color="blue" style="cursor: pointer" @click="$router.push(`/app/topic/detail/${row.topic_id}`)">
                {{ row.topic_title }}
              </a-tag>
            </span>
            <span v-else class="text-gray-400">未聚类</span>
          </template>

          <template #clustering_status="{ row }">
            <a-tag v-if="row.clustering_status === 'processing'" color="blue">处理中</a-tag>
            <a-tag v-else-if="row.clustering_status === 'failed'" color="red">失败</a-tag>
            <a-tag v-else-if="row.clustering_status === 'pending'" color="default">待处理</a-tag>
            <a-tag
              v-else-if="row.clustering_status === 'clustered'"
              :color="row.topic_id ? 'green' : 'default'"
            >
              {{ row.topic_id ? '已归类' : '待观察' }}
            </a-tag>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template #urgent="{ row }">
            <a-tag v-if="row.is_urgent" color="red">紧急</a-tag>
            <a-tag v-else color="default">常规</a-tag>
          </template>
        </Grid>
        </div>

        <!-- 新建弹窗 -->
        <FeedbackCreateModal ref="createModalRef" @success="onRefresh" />

        <!-- 编辑弹窗 -->
        <FeedbackEditModal ref="editModalRef" feedback-id="" @success="onRefresh" />

        <!-- AI 聚类进度弹窗 -->
        <ClusteringProgressModal
          v-model:open="clusteringModalOpen"
          :task-id="clusteringTaskId"
          @success="handleClusteringSuccess"
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
          v-model:has-topic="filterValues.has_topic"
          v-model:clustering-status="filterValues.clustering_status"
          v-model:board-ids="filterValues.board_ids"
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
