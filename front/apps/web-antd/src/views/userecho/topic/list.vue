<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Topic,
  CreateTopicParams,
  UpdateTopicParams,
} from '#/api';

import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message, Drawer } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getTopicList,
  createTopic,
  updateTopic,
} from '#/api';
import {
  querySchema,
  useColumns,
  topicFormSchema,
  getStatusConfig,
  getCategoryConfig,
  categoryIcons,
} from '#/views/userecho/topic/data';
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
const filterValues = ref({
  search_query: '',
  search_mode: 'keyword' as 'keyword' | 'semantic',
  status: '',
  category: '',
  board_ids: [] as string[],
});

/**
 * 语义搜索 loading 状态
 */
const semanticSearchLoading = ref(false);
const currentSearchMode = ref<string>('keyword');

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
  height: 'auto',
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
        // 记录当前搜索模式
        currentSearchMode.value = filterValues.value.search_mode || 'keyword';

        // 如果是语义搜索且有搜索词，显示 loading 提示
        const isSemanticSearch = filterValues.value.search_mode === 'semantic' && filterValues.value.search_query;
        if (isSemanticSearch) {
          semanticSearchLoading.value = true;
          message.loading({
            content: '🤖 AI 正在理解搜索语义，请稍候...',
            key: 'semantic-search',
            duration: 0, // 不自动关闭
          });
        }

        try {
          // 过滤掉空字符串值，只传递有效的筛选参数
          const queryParams: any = {
            skip: (page.currentPage - 1) * page.pageSize,
            limit: page.pageSize,
          };
          
          if (filterValues.value.search_query) {
            queryParams.search_query = filterValues.value.search_query;
          }
          if (filterValues.value.search_mode) {
            queryParams.search_mode = filterValues.value.search_mode;
          }
          if (filterValues.value.status) {
            queryParams.status = filterValues.value.status;
          }
          if (filterValues.value.category) {
            queryParams.category = filterValues.value.category;
          }
          if (filterValues.value.board_ids && filterValues.value.board_ids.length > 0) {
            queryParams.board_ids = filterValues.value.board_ids;
          }
          
          const data = await getTopicList(queryParams);

          // 语义搜索完成，显示成功提示
          if (isSemanticSearch) {
            message.success({
              content: `找到 ${data.length} 个相关主题`,
              key: 'semantic-search',
              duration: 2,
            });
          }

          // vxe-table 期望的返回格式（根据全局 response 配置）
          return {
            items: data,           // 数据数组
            total: data.length,    // 当前查询到的记录数
          };
        } catch (error: any) {
          // 语义搜索失败，显示错误提示
          if (isSemanticSearch) {
            message.error({
              content: error.message || '搜索失败，请稍后重试',
              key: 'semantic-search',
              duration: 3,
            });
          }
          throw error;
        } finally {
          if (isSemanticSearch) {
            semanticSearchLoading.value = false;
          }
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
    <div class="flex h-full w-full">
      <!-- 左侧栏 - 仅桌面端显示 -->
      <div v-if="!isMobile" class="h-full w-[240px] flex-shrink-0 border-r border-border bg-sidebar">
        <TopicFilterSidebar
          v-model:search-query="filterValues.search_query"
          v-model:search-mode="filterValues.search_mode"
          v-model:status="filterValues.status"
          v-model:category="filterValues.category"
          v-model:board-ids="filterValues.board_ids"
          @search="handleSearch"
        />
      </div>
      
      <!-- 右侧内容区域 -->
      <div class="flex-1 h-full overflow-hidden bg-background" :class="isMobile ? 'p-2' : 'p-4'">
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
        
        <Grid>
          <template #toolbar-actions>
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
              <a-tag
                v-if="row.priority_score"
                :color="getPriorityColor(row.priority_score.total_score)"
                style="font-size: 14px; font-weight: bold; cursor: pointer"
                @click="router.push(`/app/topic/detail/${row.id}`)"
              >
                {{ row.priority_score.total_score.toFixed(1) }}
              </a-tag>
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
      
      <!-- 移动端抽屉 -->
      <a-drawer
        v-model:open="drawerVisible"
        title="筛选条件"
        placement="left"
        :width="280"
        :body-style="{ padding: 0 }"
      >
        <TopicFilterSidebar
          v-model:search-query="filterValues.search_query"
          v-model:search-mode="filterValues.search_mode"
          v-model:status="filterValues.status"
          v-model:category="filterValues.category"
          v-model:board-ids="filterValues.board_ids"
          @search="() => { handleSearch(); drawerVisible = false; }"
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
