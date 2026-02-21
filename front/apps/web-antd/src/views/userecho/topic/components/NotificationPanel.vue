<script setup lang="ts">
import type { TopicNotification, GenerateReplyParams } from '#/api/userecho/notification';

import { ref, computed, onMounted } from 'vue';

import { VbenButton, VbenLoading } from '@vben/common-ui';

import { message, Modal, Tooltip, Tag, Drawer, Input, Select, Switch, Table } from 'ant-design-vue';
import {
  SendOutlined,
  CopyOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';

import {
  getTopicNotifications,
  generateReply,
  batchGenerateReplies,
  markNotified,
} from '#/api/userecho/notification';

const props = defineProps<{
  topicId: string;
  topicTitle: string;
  topicStatus: string;
}>();

const emit = defineEmits<{
  (e: 'refresh'): void;
}>();

// 数据状态
const loading = ref(false);
const notifications = ref<TopicNotification[]>([]);
const stats = ref({ total: 0, pending: 0, generated: 0, sent: 0 });

// 生成回复抽屉
const drawerVisible = ref(false);
const currentNotification = ref<TopicNotification | null>(null);
const generating = ref(false);
const generatedReply = ref('');
const replyTone = ref<'formal' | 'friendly' | 'concise'>('friendly');
const replyLanguage = ref('zh-CN');
const customContext = ref('');

// 批量生成状态
const batchGenerating = ref(false);

// 加载通知列表
const loadNotifications = async () => {
  try {
    loading.value = true;
    const result = await getTopicNotifications(props.topicId);
    notifications.value = result.items;
    stats.value = result.stats;
  } catch (error: any) {
    message.error(error.message || '加载失败');
  } finally {
    loading.value = false;
  }
};

// 状态标签配置
const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: '待生成', color: 'default' },
  generated: { label: '已生成', color: 'blue' },
  copied: { label: '已复制', color: 'cyan' },
  sent: { label: '已通知', color: 'green' },
};

// 客户等级配置
const tierConfig: Record<string, { label: string; color: string }> = {
  free: { label: '免费', color: 'default' },
  normal: { label: '普通', color: 'blue' },
  paid: { label: '付费', color: 'gold' },
  vip: { label: 'VIP', color: 'purple' },
  strategic: { label: '战略', color: 'red' },
};

// 语气选项
const toneOptions = [
  { value: 'formal', label: '正式商务' },
  { value: 'friendly', label: '亲切友好' },
  { value: 'concise', label: '简洁高效' },
];

// 打开生成回复抽屉
const openGenerateDrawer = (notification: TopicNotification) => {
  currentNotification.value = notification;
  generatedReply.value = notification.ai_reply || '';
  replyTone.value = (notification.reply_tone as 'formal' | 'friendly' | 'concise') || 'friendly';
  replyLanguage.value = notification.reply_language || 'zh-CN';
  customContext.value = '';
  drawerVisible.value = true;
};

// 生成回复
const handleGenerateReply = async () => {
  if (!currentNotification.value) return;

  try {
    generating.value = true;
    const params: GenerateReplyParams = {
      tone: replyTone.value,
      language: replyLanguage.value,
      custom_context: customContext.value || undefined,
    };
    const result = await generateReply(
      props.topicId,
      currentNotification.value.id,
      params,
    );
    generatedReply.value = result.ai_reply;
    message.success(`生成成功（耗时 ${result.generation_time_ms}ms）`);
    await loadNotifications();
  } catch (error: any) {
    message.error(error.message || '生成失败');
  } finally {
    generating.value = false;
  }
};

// 复制回复内容
const handleCopyReply = async () => {
  if (!generatedReply.value || !currentNotification.value) return;

  try {
    await navigator.clipboard.writeText(generatedReply.value);
    message.success('已复制到剪贴板');

    // 标记为已复制
    await markNotified(props.topicId, currentNotification.value.id, {
      status: 'copied',
    });
    await loadNotifications();
  } catch (error: any) {
    message.error('复制失败');
  }
};

// 标记为已通知
const handleMarkSent = async (notification: TopicNotification) => {
  try {
    await markNotified(props.topicId, notification.id, {
      status: 'sent',
      notification_channel: 'manual',
    });
    message.success('已标记为已通知');
    await loadNotifications();
  } catch (error: any) {
    message.error(error.message || '操作失败');
  }
};

// 批量生成回复
const handleBatchGenerate = () => {
  Modal.confirm({
    title: '批量生成回复',
    content: `将为 ${stats.value.pending} 个待处理用户生成 AI 回复，是否继续？`,
    onOk: async () => {
      try {
        batchGenerating.value = true;
        const result = await batchGenerateReplies(props.topicId, {
          tone: 'friendly',
          language: 'zh-CN',
        });
        message.success(`成功生成 ${result.success} 条，失败 ${result.failed} 条`);
        await loadNotifications();
      } catch (error: any) {
        message.error(error.message || '批量生成失败');
      } finally {
        batchGenerating.value = false;
      }
    },
  });
};

// 表格列定义
const columns = [
  {
    title: '用户',
    dataIndex: 'user',
    key: 'user',
    width: 250,
  },
  {
    title: '反馈内容',
    dataIndex: 'feedback_content',
    key: 'feedback',
    ellipsis: true,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    align: 'center',
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    align: 'center',
  },
];

// 是否显示操作提示
const showCompletedHint = computed(() => props.topicStatus === 'completed' && stats.value.pending > 0);

onMounted(() => {
  loadNotifications();
});
</script>

<template>
  <div class="notification-panel">
    <!-- 统计概览 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总计</span>
        <span class="stat-value">{{ stats.total }}</span>
      </div>
      <div class="stat-item pending">
        <span class="stat-label">待生成</span>
        <span class="stat-value">{{ stats.pending }}</span>
      </div>
      <div class="stat-item generated">
        <span class="stat-label">已生成</span>
        <span class="stat-value">{{ stats.generated }}</span>
      </div>
      <div class="stat-item sent">
        <span class="stat-label">已通知</span>
        <span class="stat-value">{{ stats.sent }}</span>
      </div>

      <div class="stat-actions">
        <VbenButton
          v-if="stats.pending > 0"
          :loading="batchGenerating"
          @click="handleBatchGenerate"
        >
          <RobotOutlined /> 批量生成
        </VbenButton>
        <VbenButton variant="ghost" @click="loadNotifications">
          <ReloadOutlined /> 刷新
        </VbenButton>
      </div>
    </div>

    <!-- 完成提示 -->
    <div v-if="showCompletedHint" class="completed-hint">
      <CheckCircleOutlined />
      <span>需求「{{ topicTitle }}」已完成，请通知以下用户</span>
    </div>

    <!-- 通知列表表格 -->
    <Table
      class="mt-4"
      :columns="columns"
      :data-source="notifications"
      :loading="loading"
      :pagination="{ pageSize: 10 }"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <!-- 用户列 -->
        <template v-if="column.key === 'user'">
           <div class="user-info">
              <div class="user-avatar">
                <UserOutlined />
              </div>
              <div class="user-detail">
                <div class="user-name">
                  {{ record.recipient_name }}
                  <Tag
                    v-if="record.customer_tier"
                    :color="tierConfig[record.customer_tier]?.color"
                    size="small"
                    style="margin-left: 4px;"
                  >
                    {{ tierConfig[record.customer_tier]?.label }}
                  </Tag>
                </div>
                <div class="user-meta">
                  <span v-if="record.customer_company" style="margin-right: 8px;">{{ record.customer_company }}</span>
                  <span v-if="record.recipient_contact">{{ record.recipient_contact }}</span>
                </div>
              </div>
           </div>
        </template>

        <!-- 反馈内容列 -->
        <template v-if="column.key === 'feedback'">
           <Tooltip :title="record.feedback_content">
             <span class="preview-text">
               {{ record.feedback_summary || record.feedback_content }}
             </span>
           </Tooltip>
        </template>

        <!-- 状态列 -->
        <template v-if="column.key === 'status'">
           <Tag :color="statusConfig[record.status]?.color">
             {{ statusConfig[record.status]?.label }}
           </Tag>
        </template>

        <!-- 操作列 -->
        <template v-if="column.key === 'action'">
           <div class="item-actions">
              <VbenButton
                variant="link"
                size="small"
                @click="openGenerateDrawer(record)"
                style="text-decoration: underline;"
              >
                {{ record.status === 'sent' ? '查看回复' : (record.ai_reply ? '修改回复' : '回复') }}
              </VbenButton>
              
              <VbenButton
                v-if="record.ai_reply && record.status !== 'sent'"
                variant="link"
                size="small"
                color="success"
                @click="handleMarkSent(record)"
                style="text-decoration: underline;"
              >
                标记已通知
              </VbenButton>
           </div>
        </template>
      </template>
    </Table>

    <!-- 生成回复抽屉 -->
    <Drawer
      v-model:open="drawerVisible"
      title="生成回复"
      placement="right"
      :width="520"
    >
      <template v-if="currentNotification">
        <div class="drawer-content">
          <!-- 收件人信息 -->
          <div class="section">
            <div class="section-title">收件人</div>
            <div class="recipient-info">
              <strong>{{ currentNotification.recipient_name }}</strong>
              <Tag
                v-if="currentNotification.customer_tier"
                :color="tierConfig[currentNotification.customer_tier]?.color"
                size="small"
              >
                {{ tierConfig[currentNotification.customer_tier]?.label }}
              </Tag>
              <span v-if="currentNotification.customer_company" class="company">
                {{ currentNotification.customer_company }}
              </span>
            </div>
          </div>

          <!-- 原始反馈 -->
          <div class="section">
            <div class="section-title">原始反馈</div>
            <div class="feedback-box">
              {{ currentNotification.feedback_content || '无反馈内容' }}
            </div>
          </div>

          <!-- 生成选项 -->
          <div class="section">
            <div class="section-title">生成选项</div>
            <div class="options-row">
              <div class="option-item">
                <label>语气风格</label>
                <Select v-model:value="replyTone" :options="toneOptions" style="width: 140px" :disabled="currentNotification.status === 'sent'" />
              </div>
              <div class="option-item">
                <label>输出语言</label>
                <Select v-model:value="replyLanguage" style="width: 140px" :disabled="currentNotification.status === 'sent'">
                  <a-select-option value="zh-CN">中文</a-select-option>
                  <a-select-option value="en-US">English</a-select-option>
                </Select>
              </div>
            </div>
            <div class="option-item full">
              <label>额外说明（可选）</label>
              <Input.TextArea
                v-model:value="customContext"
                :rows="2"
                placeholder="例如：强调新功能的使用方式"
                :disabled="currentNotification.status === 'sent'"
              />
            </div>
          </div>

          <!-- 生成按钮 -->
          <div class="generate-action">
            <VbenButton
              :loading="generating"
              :disabled="currentNotification.status === 'sent'"
              block
              @click="handleGenerateReply"
            >
              <RobotOutlined /> {{ generatedReply ? (currentNotification.status === 'sent' ? '不可编辑 (已通知)' : '重新生成') : '生成回复' }}
            </VbenButton>
          </div>

          <!-- 生成结果 -->
          <div v-if="generatedReply" class="section result-section">
            <div class="section-title">
              生成结果
              <VbenButton
                variant="link"
                size="small"
                @click="handleCopyReply"
              >
                <CopyOutlined /> 复制
              </VbenButton>
            </div>
            <div class="reply-box">
              {{ generatedReply }}
            </div>
          </div>
        </div>
      </template>
    </Drawer>
  </div>
</template>

<style scoped>
.notification-panel {
  padding: 16px;
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.stat-item.pending .stat-value {
  color: #faad14;
}

.stat-item.generated .stat-value {
  color: #1890ff;
}

.stat-item.sent .stat-value {
  color: #52c41a;
}

.stat-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.completed-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  color: #52c41a;
  margin-bottom: 16px;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: all 0.2s;
}

.notification-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.notification-item.is-sent {
  opacity: 0.7;
  background: #fafafa;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  font-size: 18px;
}

.user-name {
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-meta {
  font-size: 12px;
  color: #8c8c8c;
}

.contact {
  margin-left: 8px;
}

.feedback-preview {
  flex: 1;
  min-width: 0;
}

.preview-text {
  color: #595959;
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-status {
  min-width: 80px;
  text-align: center;
}

.item-actions {
  display: flex;
  gap: 4px;
}

/* 抽屉样式 */
.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.section-title {
  font-weight: 500;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.recipient-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.company {
  color: #8c8c8c;
  margin-left: 8px;
}

.feedback-box {
  padding: 12px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
}

.options-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-item label {
  font-size: 12px;
  color: #8c8c8c;
}

.option-item.full {
  width: 100%;
}

.generate-action {
  padding: 12px 0;
}

.result-section {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
}

.reply-box {
  padding: 16px;
  background: white;
  border-radius: 4px;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
