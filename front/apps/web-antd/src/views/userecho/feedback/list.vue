<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Feedback,
  CreateFeedbackParams,
  UpdateFeedbackParams,
} from '#/api';

import { computed, onBeforeUnmount, ref, onMounted, watch } from 'vue';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';
import { PlusOutlined, LoadingOutlined } from '@ant-design/icons-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getFeedbackList,
  createFeedback,
  updateFeedback,
  deleteFeedback,
  triggerClustering,
  getClusteringTaskStatus,
  analyzeScreenshot,
  getScreenshotTaskStatus,
} from '#/api';
import { getBoardList } from '#/api/userecho/board';
import { getTopicList } from '#/api/userecho/topic';
import {
  useColumns,
  feedbackFormSchema,
} from '#/views/userecho/feedback/data';
import FeedbackFilterSidebar from '#/layouts/components/sidebar/FeedbackFilterSidebar.vue';

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
  is_urgent: [] as string[],
  has_topic: [] as string[],
  clustering_status: [] as string[],
  board_ids: [] as string[],
});

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
          // 过滤掉空字符串值，只传递有效的筛选参数
          const queryParams: any = {
            skip: (page.currentPage - 1) * page.pageSize,
            limit: page.pageSize,
          };
          
          // 只添加非空值
          if (filterValues.value.search_query) {
            queryParams.search_query = filterValues.value.search_query;
            queryParams.search_mode = 'keyword'; // MVP阶段只用关键词搜索
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

          // vxe-table 期望的返回格式（根据全局 response 配置）
          return {
            items: data,           // 数据数组
            total: data.length,    // 当前查询到的记录数（临时方案，理想情况下应该由后端返回总数）
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
 * 操作按钮点击处理
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
      editFeedbackId.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
  }
}

/**
 * 触发 AI 聚类
 */
const clusteringLoading = ref(false);
const clusteringModalOpen = ref(false);
const clusteringTaskId = ref<string>('');
const clusteringTaskState = ref<'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'>('PENDING');
const clusteringTaskError = ref<string>('');

let clusteringPollTimer: number | null = null;

const clusteringProgress = computed(() => {
  switch (clusteringTaskState.value) {
    case 'PENDING':
      return 10;
    case 'STARTED':
      return 60;
    case 'RETRY':
      return 60;
    case 'SUCCESS':
      return 100;
    case 'FAILURE':
      return 100;
    default:
      return 0;
  }
});

const clusteringStep = computed(() => {
  switch (clusteringTaskState.value) {
    case 'PENDING':
      return 0;
    case 'STARTED':
    case 'RETRY':
      return 1;
    case 'SUCCESS':
    case 'FAILURE':
      return 2;
    default:
      return 0;
  }
});

function stopClusteringPoll() {
  if (clusteringPollTimer !== null) {
    window.clearInterval(clusteringPollTimer);
    clusteringPollTimer = null;
  }
}

function closeClusteringModal() {
  stopClusteringPoll();
  clusteringLoading.value = false;
  clusteringModalOpen.value = false;
}

function onClusteringModalCancel() {
  closeClusteringModal();
}

onBeforeUnmount(() => {
  stopClusteringPoll();
});

async function pollClusteringTask(taskId: string) {
  const status = await getClusteringTaskStatus(taskId);
  clusteringTaskState.value = status.state;

  if (status.state === 'FAILURE') {
    clusteringTaskError.value = status.error || '任务执行失败';
    message.error(clusteringTaskError.value);
    closeClusteringModal();
    return;
  }

  if (status.state === 'SUCCESS') {
    const result: any = status.result;
    if (!result) {
      message.warning('聚类任务完成，但未返回结果');
      closeClusteringModal();
      return;
    }

    if (result.status === 'skipped') {
      message.warning(result.message || '聚类已跳过');
    } else {
      message.success(`聚类完成：创建 ${result.topics_created ?? 0} 个主题，噪声 ${result.noise_count ?? 0} 条`);
    }
    onRefresh();
    closeClusteringModal();
  }
}

const handleTriggerClustering = async () => {
  try {
    clusteringLoading.value = true;
    clusteringModalOpen.value = true;
    clusteringTaskError.value = '';
    clusteringTaskState.value = 'PENDING';

    const resp: any = await triggerClustering({ async_mode: true });
    if (resp?.status === 'accepted' && resp?.task_id) {
      clusteringTaskId.value = resp.task_id;

      // 先拉一次，避免用户看到空转
      await pollClusteringTask(resp.task_id);
      clusteringPollTimer = window.setInterval(() => pollClusteringTask(resp.task_id), 2000);
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
  } catch (error: any) {
    message.error(error.message || '聚类失败，请稍后重试');
  } finally {
    clusteringLoading.value = false;
  }
};

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: feedbackFormSchema,
});

const editFeedbackId = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  title: '编辑反馈',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await editFormApi.getValues<UpdateFeedbackParams>();
      try {
        await updateFeedback(editFeedbackId.value, data);
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
const boardList = ref<any[]>([]);
const selectedTopicId = ref<string>('');
const similarTopics = ref<any[]>([]);
const titleSearchLoading = ref(false);
const uploadedScreenshots = ref<string[]>([]);
const uploadingScreenshot = ref(false);

// 加载 Board 列表
const loadBoardList = async () => {
  try {
    const response = await getBoardList();
    boardList.value = response.boards.map((board: any) => ({
      label: board.name,
      value: board.id,
    }));
    
    // 更新表单 Schema 中的 Board 选项
    const boardField = feedbackFormSchema.find(f => f.fieldName === 'board_id');
    if (boardField && boardField.componentProps) {
      (boardField.componentProps as any).options = boardList.value;
    }
  } catch (error: any) {
    message.error('加载 Board 列表失败');
  }
};

// 监听 Title 输入,搜索相似 Topic
const handleTitleChange = async (title: string) => {
  if (!title || title.trim().length < 2) {
    similarTopics.value = [];
    return;
  }
  
  try {
    titleSearchLoading.value = true;
    const topics = await getTopicList({
      search_query: title,
      search_mode: 'keyword',
      limit: 10,
    });
    similarTopics.value = topics;
  } catch (error: any) {
    console.error('搜索 Topic 失败', error);
  } finally {
    titleSearchLoading.value = false;
  }
};

// 选择 Topic
const handleTopicSelect = (topicId: string) => {
  selectedTopicId.value = topicId;
};

// 处理图片上传
const handleScreenshotUpload = async (file: File) => {
  if (uploadedScreenshots.value.length >= 3) {
    message.warning('最多只能上传3张截图');
    return false;
  }
  
  try {
    uploadingScreenshot.value = true;
    const formData = new FormData();
    formData.append('file', file);
    
    // 调用上传接口（复用截图识别的上传逻辑）
    const response = await analyzeScreenshot(formData);
    
    // 轮询获取上传结果
    const taskId = response.task_id;
    let pollCount = 0;
    const maxPolls = 15;
    
    const pollUpload = async (): Promise<string | null> => {
      pollCount++;
      const status = await getScreenshotTaskStatus(taskId);
      
      if (status.state === 'SUCCESS' && status.result) {
        return status.result.screenshot_url;
      } else if (status.state === 'FAILURE') {
        throw new Error(status.error || '上传失败');
      } else if (pollCount < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        return pollUpload();
      } else {
        throw new Error('上传超时');
      }
    };
    
    const screenshotUrl = await pollUpload();
    if (screenshotUrl) {
      uploadedScreenshots.value.push(screenshotUrl);
      message.success('图片上传成功');
    }
    
    return false; // 阻止默认上传行为
  } catch (error: any) {
    message.error(error.message || '图片上传失败');
    return false;
  } finally {
    uploadingScreenshot.value = false;
  }
};

// 移除已上传的截图
const handleRemoveScreenshot = (index: number) => {
  uploadedScreenshots.value.splice(index, 1);
};

const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: feedbackFormSchema,
});

const [addModal, addModalApi] = useVbenModal({
  title: '新建反馈',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      await handleCreateFeedback(false);
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      addFormApi.resetForm();
      selectedTopicId.value = '';
      similarTopics.value = [];
      uploadedScreenshots.value = [];
      loadBoardList();
    }
  },
});

// 创建反馈（支持创建并继续）
const handleCreateFeedback = async (continueCreating: boolean) => {
  try {
    addModalApi.lock();
    const data = await addFormApi.getValues<CreateFeedbackParams>();
    
    // 添加 Topic 关联和截图
    if (selectedTopicId.value) {
      data.topic_id = selectedTopicId.value;
    }
    if (uploadedScreenshots.value.length > 0) {
      data.screenshots = uploadedScreenshots.value;
    }
    
    await createFeedback(data);
    message.success('创建成功');
    onRefresh();
    
    if (continueCreating) {
      // 重置表单但保持弹窗打开
      addFormApi.resetForm();
      selectedTopicId.value = '';
      similarTopics.value = [];
      uploadedScreenshots.value = [];
    } else {
      await addModalApi.close();
    }
  } catch {
    message.error('创建失败');
  } finally {
    addModalApi.unlock();
  }
};

// 创建并继续
const handleCreateAndContinue = async () => {
  const { valid } = await addFormApi.validate();
  if (valid) {
    await handleCreateFeedback(true);
  }
};

onMounted(() => {
  // 初始化响应式检测
  const mediaQuery = window.matchMedia('(max-width: 767px)');
  handleMediaChange(mediaQuery);
  mediaQuery.addEventListener('change', handleMediaChange);
  
  // 保存 mediaQuery 引用以便清理
  (window as any).__feedbackMediaQuery = mediaQuery;
});

onBeforeUnmount(() => {
  // 清理响应式检测监听器
  const mediaQuery = (window as any).__feedbackMediaQuery;
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleMediaChange);
    delete (window as any).__feedbackMediaQuery;
  }
  
  // 清理聚类轮询
  stopClusteringPoll();
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
            <div class="feedback-actions-group">
              <!-- 搜索框 -->
              <a-input
                v-model:value="filterValues.search_query"
                placeholder="搜索反馈内容..."
                allow-clear
                @pressEnter="handleSearch"
                style="width: 300px;"
                class="mr-3"
              >
                <template #prefix>
                  <span class="iconify lucide--search" />
                </template>
              </a-input>
              
              <div class="add-actions">
                <VbenButton type="primary" @click="() => addModalApi.open()">
                  <span class="iconify lucide--pencil mr-2" />
                  手动录入
                </VbenButton>
                <VbenButton @click="() => $router.push('/app/feedback/screenshot')">
                  <span class="iconify lucide--camera mr-2" />
                  截图识别
                </VbenButton>
                <VbenButton @click="() => $router.push('/app/feedback/import')">
                  <span class="iconify lucide--upload mr-2" />
                  批量导入
                </VbenButton>
              </div>
              <VbenButton
                variant="outline"
                @click="handleTriggerClustering"
                :loading="clusteringLoading"
              >
                <span class="iconify lucide--sparkles mr-2" />
                AI 智能聚类
              </VbenButton>
            </div>
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

        <!-- 编辑弹窗 -->
        <editModal>
          <EditForm />
        </editModal>

        <!-- 新建弹窗 -->
        <addModal class="w-[1000px]">
          <div class="feedback-create-layout">
            <a-row :gutter="24">
              <!-- 左侧表单区域 -->
              <a-col :span="14">
                <div class="left-content-area">
                  <AddForm @values-change="(changedValues: any) => {
                    if (changedValues.title !== undefined) {
                      handleTitleChange(changedValues.title);
                    }
                  }" />
                  
                  <!-- 图片上传组件 -->
                  <div class="screenshot-upload-section">
                    <div class="upload-label">截图上传（最多3张）</div>
                    <a-upload
                      :file-list="uploadedScreenshots.map((url, index) => ({
                        uid: String(index),
                        name: `screenshot-${index + 1}.png`,
                        status: 'done',
                        url: url,
                      }))"
                      list-type="picture-card"
                      :before-upload="handleScreenshotUpload"
                      :on-remove="(file: any) => handleRemoveScreenshot(Number(file.uid))"
                      accept="image/png,image/jpeg,image/jpg,image/webp"
                      :max-count="3"
                    >
                      <div v-if="uploadedScreenshots.length < 3">
                        <loading-outlined v-if="uploadingScreenshot" />
                        <plus-outlined v-else />
                        <div class="upload-text">上传图片</div>
                      </div>
                    </a-upload>
                  </div>
                </div>
              </a-col>
              
              <!-- 右侧 Topic 列表 -->
              <a-col :span="10">
                <div class="similar-topics-panel">
                  <div class="panel-header">
                    <span class="iconify lucide--lightbulb mr-2" />
                    相似主题
                  </div>
                  
                  <div v-if="titleSearchLoading" class="panel-loading">
                    <a-spin />
                    <p>搜索中...</p>
                  </div>
                  
                  <div v-else-if="similarTopics.length === 0" class="panel-empty">
                    <span class="iconify lucide--search text-4xl mb-2" />
                    <p>输入标题以搜索相似主题</p>
                  </div>
                  
                  <div v-else class="topic-list">
                    <div
                      v-for="topic in similarTopics"
                      :key="topic.id"
                      class="topic-item"
                      :class="{ 'topic-item-selected': selectedTopicId === topic.id }"
                      @click="handleTopicSelect(topic.id)"
                    >
                      <div class="topic-title">{{ topic.title }}</div>
                      <div class="topic-meta">
                        <a-tag :color="topic.status === 'pending' ? 'default' : 'blue'" size="small">
                          {{ topic.status }}
                        </a-tag>
                        <span class="topic-feedback-count">
                          {{ topic.feedback_count }} 条反馈
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </a-col>
            </a-row>
          </div>
          <template #footer>
            <div class="modal-footer-actions">
              <VbenButton @click="() => addModalApi.close()">取消</VbenButton>
              <VbenButton @click="handleCreateAndContinue">创建并继续</VbenButton>
              <VbenButton type="primary" @click="() => addModalApi.onConfirm?.()">创建</VbenButton>
            </div>
          </template>
        </addModal>

        <a-modal
          v-model:open="clusteringModalOpen"
          title="AI 智能聚类"
          :footer="null"
          :maskClosable="false"
          @cancel="onClusteringModalCancel"
        >
          <a-steps :current="clusteringStep" size="small">
            <a-step title="任务提交" />
            <a-step title="处理中" />
            <a-step title="完成" />
          </a-steps>

          <div class="mt-4">
            <a-progress :percent="clusteringProgress" :status="clusteringTaskState === 'FAILURE' ? 'exception' : 'active'" />
            <div class="text-gray-500 mt-2">
              <div v-if="clusteringTaskId">任务 ID：{{ clusteringTaskId }}</div>
              <div v-if="clusteringTaskError" class="text-red-500 mt-1">错误：{{ clusteringTaskError }}</div>
            </div>
          </div>
        </a-modal>
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
  height: calc(100vh - 64px); /* 减去顶部导航栏高度 */
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
  min-height: 0; /* 重要：允许 flex 子元素收缩 */
}

.feedback-actions-group {
  display: flex;
  gap: 16px;
  align-items: center;
  width: 100%;
}

.add-actions {
  display: flex;
  gap: 12px;
  flex: 1;
}

.add-actions > button {
  flex: 1;
  min-width: 120px;
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

/* 新建反馈 Modal 样式 */
.feedback-create-layout {
  padding: 0;
}

/* 左侧内容区域 - 与右侧高度对齐 */
.left-content-area {
  height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.screenshot-upload-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid hsl(var(--border) / 0.2);
}

.upload-label {
  font-weight: 500;
  margin-bottom: 12px;
  color: hsl(var(--foreground));
}

.upload-text {
  margin-top: 8px;
  font-size: 12px;
  color: hsl(var(--muted-foreground));
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0 0 0;
}

/* 相似主题面板 */
.similar-topics-panel {
  height: 600px;
  border: 1px solid hsl(var(--border) / 0.3);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: hsl(var(--background));
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid hsl(var(--border) / 0.3);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  background: hsl(var(--muted) / 0.3);
}

.panel-loading,
.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: hsl(var(--muted-foreground));
  padding: 32px;
  text-align: center;
}

.panel-loading p,
.panel-empty p {
  margin-top: 12px;
  font-size: 14px;
}

.topic-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.topic-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid hsl(var(--border) / 0.3);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: hsl(var(--background));
}

.topic-item:hover {
  border-color: hsl(var(--primary) / 0.5);
  background: hsl(var(--muted) / 0.2);
  transform: translateX(2px);
}

.topic-item-selected {
  border-color: hsl(var(--primary));
  background: hsl(var(--primary) / 0.1);
  box-shadow: 0 0 0 1px hsl(var(--primary) / 0.2);
}

.topic-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 8px;
  color: hsl(var(--foreground));
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: hsl(var(--muted-foreground));
}

.topic-feedback-count {
  display: flex;
  align-items: center;
}

</style>
