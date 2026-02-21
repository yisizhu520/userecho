<script setup lang="ts">
import type { TopicDetail, UpdateTopicStatusParams } from '#/api';

import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';

import { VbenButton, useVbenModal } from '@vben/common-ui';

import { message, Modal } from 'ant-design-vue';
import {
  LeftOutlined,
  EditOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  UserOutlined,
  LinkOutlined,
  BellOutlined,
  DisconnectOutlined,
} from '@ant-design/icons-vue';

import { useVbenForm } from '#/adapter/form';
import {
  getTopicDetail,
  updateTopicStatus,
  unlinkFeedbackFromTopic,
} from '#/api';
import { getStatusConfig, getCategoryConfig, categoryIcons, statusFormSchema } from '#/views/userecho/topic/data';
import PriorityScoreCard from './components/PriorityScoreCard.vue';
import NotificationPanel from './components/NotificationPanel.vue';
import LinkFeedbackModal from './components/LinkFeedbackModal.vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const router = useRouter();
const route = useRoute();
const topicId = route.params.id as string;

// Tab 相关
const activeTab = ref('feedbacks');
const tabFromQuery = route.query.tab as string;
if (tabFromQuery) {
  activeTab.value = tabFromQuery;
}

/**
 * 数据加载
 */
const loading = ref(false);
const topicDetail = ref<TopicDetail | null>(null);

const loadTopicDetail = async () => {
  try {
    loading.value = true;
    topicDetail.value = await getTopicDetail(topicId);
  } catch (error: any) {
    message.error(error.message || '加载失败');
    // 如果加载失败，可能是ID不存在，返回列表页
    if (error.code === 400 || error.message.includes('不存在')) {
       router.push('/app/topic/list');
    }
  } finally {
    loading.value = false;
  }
};

/**
 * 计算属性
 */
const topic = computed(() => topicDetail.value?.topic);
const feedbacks = computed(() => topicDetail.value?.feedbacks || []);
const priorityScore = computed(() => topicDetail.value?.priority_score);
const statusHistory = computed(() => topicDetail.value?.status_history || []);

const statusConfig = computed(() => getStatusConfig(topic.value?.status ?? 'pending'));
const categoryConfig = computed(() => getCategoryConfig(topic.value?.category ?? 'other'));

const hasUrgentFeedback = computed(() => feedbacks.value.some((f: any) => f.is_urgent));

/**
 * 状态更新
 */
const [StatusForm, statusFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: statusFormSchema,
});

const [statusModal, statusModalApi] = useVbenModal({
  title: '更新主题状态',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await statusFormApi.validate();
    if (valid) {
      statusModalApi.lock();
      const data = await statusFormApi.getValues<UpdateTopicStatusParams>();
      try {
        await updateTopicStatus(topicId, data);
        message.success('状态更新成功');
        await statusModalApi.close();
        await loadTopicDetail();
      } catch {
        message.error('状态更新失败');
      } finally {
        statusModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      statusFormApi.resetForm();
      if (topic.value) {
        statusFormApi.setValues({ status: topic.value.status });
      }
    }
  },
});

/**
 * 快速状态更新
 */
const handleQuickStatusUpdate = (status: string) => {
  Modal.confirm({
    title: '确认更新状态？',
    content: `将主题状态更新为「${getStatusConfig(status).label}」`,
    onOk: async () => {
      try {
        await updateTopicStatus(topicId, { status });
        message.success('状态更新成功');
        await loadTopicDetail();
      } catch {
        message.error('状态更新失败');
      }
    },
  });
};

/**
 * 关联反馈弹窗
 */
const [LinkModal, linkModalApi] = useVbenModal({
    connectedComponent: LinkFeedbackModal,
});

/**
 * 移除反馈关联
 */
const handleUnlinkFeedback = async (feedbackId: string) => {
    try {
        await unlinkFeedbackFromTopic(topicId, feedbackId);
        message.success('已移除关联');
        // 重新加载详情
        await loadTopicDetail();
    } catch (error) {
        message.error('移除失败');
    }
};

/**
 * 反馈表格列
 */
const feedbackColumns = [
  {
    title: '反馈内容',
    dataIndex: 'content',
    ellipsis: true,
  },
  {
    title: '提交人',
    dataIndex: 'submitter_name',
    width: 120,
    customRender: ({ record }: any) => {
      return record.submitter_name || '-';
    }
  },
  {
    title: '客户名称',
    dataIndex: 'customer_name',
    width: 150,
    customRender: ({ record }: any) => {
      // 优先显示客户名称
      if (record.customer_name) {
        return record.customer_name;
      }
      // 其次显示外部用户信息
      if (record.external_user_name) {
        return record.external_user_name;
      }
      // 再次显示匿名作者
      if (record.anonymous_author) {
         return `${record.anonymous_author} (匿名)`;
      }
      return '-';
    }
  },
  {
    title: '提交时间',
    dataIndex: 'submitted_at',
    width: 120,
    customRender: ({ text }: any) => dayjs(text).fromNow(),
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    align: 'center',
  }
];

/**
 * 初始化
 */
onMounted(() => {
  loadTopicDetail();
});
</script>

<template>
  <div v-if="loading" class="loading-container">
    <a-spin size="large" />
  </div>

  <div v-else-if="topic" class="topic-detail-page">
    <!-- 面包屑导航 -->
    <div class="page-header">
      <a-breadcrumb>
        <a-breadcrumb-item>
          <router-link to="/app/topic/list">需求主题</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>主题详情</a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <a-row :gutter="24">
      <!-- 左侧：主内容区 -->
      <a-col :span="16">
        <!-- 主题信息卡片 -->
        <a-card class="topic-info-card mb-4" :bordered="false">
          <div class="topic-header">
             <div class="topic-title-row">
                <span class="category-icon">{{ categoryIcons[topic.category] }}</span>
                <h1 class="topic-title">{{ topic.title }}</h1>
                <a-tag :color="statusConfig?.color" class="status-tag check">
                  {{ statusConfig?.label }}
                </a-tag>
             </div>
             
             <div class="topic-meta">
                <a-tag :color="categoryConfig?.value === 'bug' ? 'red' : 'blue'">
                  {{ categoryConfig?.label }}
                </a-tag>
                <span class="meta-separator">|</span>
                <span class="meta-item">
                  <UserOutlined /> {{ topic.feedback_count }} 条反馈
                </span>
                <span class="meta-separator">|</span>
                <span class="meta-item">
                   创建于 {{ dayjs(topic.created_time).fromNow() }}
                </span>
             </div>
          </div>
          
          <a-divider />
          
          <div class="topic-description">
            <div v-if="topic.description" class="desc-content">
               {{ topic.description }}
            </div>
            <div v-else class="empty-desc">暂无描述</div>
          </div>
        </a-card>

        <!-- Tab 切换区域 -->
        <a-tabs v-model:activeKey="activeTab" class="detail-tabs">
          <template #tabBarExtraContent>
             <a-button 
               v-if="activeTab === 'feedbacks'" 
               type="primary" 
               size="small"
               @click="linkModalApi.open()"
               style="display: flex; align-items: center; gap: 6px;"
             >
               <LinkOutlined />
               <span>关联现有反馈</span>
             </a-button>
          </template>

          <!-- 关联反馈 Tab -->
          <a-tab-pane key="feedbacks" :tab="`📝 关联反馈 (${feedbacks.length})`">
            <a-table
              :columns="feedbackColumns"
              :data-source="feedbacks"
              :pagination="{ pageSize: 10 }"
              :row-key="(record: any) => record.id"
              size="middle"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'content'">
                  <span v-if="record.is_urgent" style="color: #ff4d4f; margin-right: 4px;">[紧急]</span>
                  {{ record.content }}
                </template>
                <template v-if="column.key === 'action'">
                    <a-popconfirm
                        title="确定要移除该反馈关联吗？"
                        @confirm="handleUnlinkFeedback(record.id)"
                    >
                        <a-button type="link" danger size="small">
                            <DisconnectOutlined /> 移除
                        </a-button>
                    </a-popconfirm>
                </template>
              </template>
            </a-table>
          </a-tab-pane>

          <!-- 通知反馈人 Tab -->
          <a-tab-pane key="notify">
            <template #tab>
              <span>
                <BellOutlined />
                通知反馈人
                <a-badge
                  v-if="topic.status === 'completed'"
                  :count="feedbacks.length"
                  :number-style="{ backgroundColor: '#52c41a' }"
                  style="margin-left: 6px;"
                />
              </span>
            </template>
            <NotificationPanel
              :topic-id="topicId"
              :topic-title="topic.title"
              :topic-status="topic.status"
              @refresh="loadTopicDetail"
            />
          </a-tab-pane>

          <!-- 状态历史 Tab -->
          <a-tab-pane key="history" tab="📊 状态历史">
            <a-timeline v-if="statusHistory.length > 0">
              <a-timeline-item
                v-for="history in statusHistory"
                :key="history.id"
                :color="getStatusConfig(history.to_status).color"
              >
                <div class="history-item">
                  <div class="history-title">
                    <a-tag :color="getStatusConfig(history.from_status).color" size="small">
                      {{ getStatusConfig(history.from_status).label }}
                    </a-tag>
                    <span class="history-arrow">→</span>
                    <a-tag :color="getStatusConfig(history.to_status).color" size="small">
                      {{ getStatusConfig(history.to_status).label }}
                    </a-tag>
                  </div>
                  <div class="history-meta">
                    <span>{{ history.changed_at }}</span>
                    <span v-if="history.changed_by_name" class="ml-2">操作人: {{ history.changed_by_name }}</span>
                  </div>
                  <div v-if="history.reason" class="history-reason">
                    原因: {{ history.reason }}
                  </div>
                </div>
              </a-timeline-item>
            </a-timeline>
            <a-empty v-else description="暂无状态变更记录" />
          </a-tab-pane>
        </a-tabs>

      </a-col>

      <!-- 右侧：决策与操作区 -->
      <a-col :span="8">
        <div class="sticky-sidebar">
          <!-- 优先级评分卡 -->
          <PriorityScoreCard 
            :topic-id="topicId"
            :existing-score="priorityScore"
            :feedback-count="feedbacks.length"
            :has-urgent-feedback="hasUrgentFeedback"
            @saved="loadTopicDetail"
          />
          
          <!-- 状态操作卡片 -->
          <a-card title="状态操作" class="actions-card" :bordered="false">
             <div class="status-actions">
                <VbenButton 
                  block 
                  class="mb-3"
                  @click="statusModalApi.open()"
                >
                  <EditOutlined /> 更新状态 & 原因
                </VbenButton>
                
                <a-divider style="margin: 12px 0;">快速操作</a-divider>
                
                <div class="quick-actions">
                  <VbenButton 
                    class="action-btn planned"
                    :disabled="topic.status === 'planned'"
                    @click="() => handleQuickStatusUpdate('planned')"
                  >
                    <ClockCircleOutlined /> 计划中
                  </VbenButton>
                  
                  <VbenButton 
                    class="action-btn in-progress"
                    :disabled="topic.status === 'in_progress'"
                    @click="() => handleQuickStatusUpdate('in_progress')"
                  >
                    <ThunderboltOutlined /> 进行中
                  </VbenButton>
                  
                  <VbenButton 
                     color="success"
                     class="action-btn completed"
                     :disabled="topic.status === 'completed'"
                     @click="() => handleQuickStatusUpdate('completed')"
                  >
                    <CheckCircleOutlined /> 已完成
                  </VbenButton>
                  
                  <VbenButton 
                    danger
                    class="action-btn ignored"
                    :disabled="topic.status === 'ignored'"
                    @click="() => handleQuickStatusUpdate('ignored')"
                  >
                    <CloseCircleOutlined /> 忽略
                  </VbenButton>
                </div>
             </div>
          </a-card>
        </div>
      </a-col>
    </a-row>

    <!-- 状态更新弹窗 -->
    <statusModal>
      <StatusForm />
    </statusModal>
    
    <LinkModal :topic-id="topicId" @success="loadTopicDetail" />
  </div>

  <a-empty v-else description="主题不存在" />
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.topic-detail-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.topic-header {
  padding: 0 12px;
}

.topic-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.category-icon {
  font-size: 28px;
  line-height: 1;
}

.topic-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f1f1f;
  flex: 1; /* 让标题占据剩余空间 */
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #8c8c8c;
  font-size: 14px;
}

.meta-separator {
  color: #d9d9d9;
}

.ai-confidence {
  cursor: help;
  border-bottom: 1px dashed #d9d9d9;
}

.topic-description {
  padding: 12px;
  font-size: 15px;
  line-height: 1.6;
  color: #262626;
}

.empty-desc {
  color: #999;
  font-style: italic;
}

.sticky-sidebar {
  position: sticky;
  top: 24px;
}

.actions-card {
  margin-top: 24px;
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* 状态按钮样式微调 */
.action-btn {
  color: white; /* 默认白色文字 */
  border: 1px solid transparent;
}

.action-btn.planned {
  background-color: #1890ff;
  border-color: #1890ff;
}
.action-btn.planned:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.action-btn.in-progress {
  background-color: #13c2c2; /* 使用 Teal 主色 */
  border-color: #13c2c2;
}
.action-btn.in-progress:hover {
  background-color: #36cfc9;
  border-color: #36cfc9;
}

.action-btn.completed {
  background-color: #52c41a;
  border-color: #52c41a;
}
.action-btn.completed:hover {
  background-color: #73d13d;
  border-color: #73d13d;
}

.action-btn.ignored {
  background-color: #ff4d4f;
  border-color: #ff4d4f;
}
.action-btn.ignored:hover {
  background-color: #ff7875;
  border-color: #ff7875;
}

/* 统一处理禁用状态（当前选中状态） */
.action-btn:disabled {
  opacity: 0.5; /* 降低透明度表示不可点 */
  color: white !important; /* 保持白色文字 */
  cursor: not-allowed;
}

/* 需要强制覆盖 ant-design 的默认 disabled 样式 */
.action-btn.planned:disabled {
  background-color: #1890ff !important;
  border-color: #1890ff !important;
}
.action-btn.in-progress:disabled {
  background-color: #13c2c2 !important;
  border-color: #13c2c2 !important;
}
.action-btn.completed:disabled {
  background-color: #52c41a !important;
  border-color: #52c41a !important;
}
.action-btn.ignored:disabled {
  background-color: #ff4d4f !important;
  border-color: #ff4d4f !important;
}

.history-item {
  margin-bottom: 12px;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-arrow {
  color: #999;
}

.history-meta {
  color: #999;
  font-size: 12px;
}

.history-reason {
  margin-top: 4px;
  color: #595959;
  font-size: 13px;
  padding: 4px 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.detail-tabs {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.detail-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}
</style>

