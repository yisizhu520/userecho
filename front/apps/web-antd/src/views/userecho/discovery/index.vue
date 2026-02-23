<script setup lang="ts">
import type { Topic } from '#/api';

import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';

import { Modal, message } from 'ant-design-vue';

import { getTopicList, updateTopicStatus } from '#/api';
import { useTopicStore } from '#/store';

const router = useRouter();
const topicStore = useTopicStore();

const loading = ref(false);
const topics = ref<Topic[]>([]);

const query = ref('');
const showNoise = ref(false);
const view = ref<'pending' | 'ignored' | 'all'>('pending');

const filteredTopics = computed(() => {
  const keyword = query.value.trim();
  return topics.value
    .filter((t) => t.ai_generated)
    .filter((t) => (showNoise.value ? true : !t.is_noise))
    .filter((t) => (view.value === 'all' ? true : t.status === view.value))
    .filter((t) => (keyword ? (t.title || '').includes(keyword) : true))
    .sort((a, b) => (b.feedback_count ?? 0) - (a.feedback_count ?? 0));
});

const stats = computed(() => {
  const all = topics.value.filter((t) => t.ai_generated);
  const pending = all.filter((t) => t.status === 'pending' && (showNoise.value ? true : !t.is_noise));
  const ignored = all.filter((t) => t.status === 'ignored' && (showNoise.value ? true : !t.is_noise));
  const totalFeedback = pending.reduce((acc, t) => acc + (t.feedback_count ?? 0), 0);
  return { all: all.length, pending: pending.length, ignored: ignored.length, totalFeedback };
});

async function refresh() {
  try {
    loading.value = true;
    topics.value = await getTopicList({
      skip: 0,
      limit: 200,
      sort_by: 'feedback_count',
      sort_order: 'desc',
    });
  } catch {
    message.error('加载失败，请稍后重试');
  } finally {
    loading.value = false;
  }
}





/** 状态中文化 */
function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待审核',
    ignored: '已忽略',
    planned: '已采纳',
    done: '已完成',
    completed: '已完成',
  };
  return map[status] || status;
}

/** 状态图标 */
function statusIcon(status: string) {
  const map: Record<string, string> = {
    pending: 'lucide--clock',
    ignored: 'lucide--eye-off',
    planned: 'lucide--check-circle',
    done: 'lucide--circle-check-big',
    completed: 'lucide--circle-check-big',
  };
  return map[status] || 'lucide--circle';
}

async function confirmTopic(t: Topic) {
  Modal.confirm({
    title: '采纳议题',
    content: `确认采纳「${t.title}」作为正式议题？`,
    okText: '确认采纳',
    cancelText: '取消',
    async onOk() {
      await updateTopicStatus(t.id, { status: 'planned', reason: 'AI发现中心确认' });
      message.success('已采纳为正式议题');
      await refresh();
      await topicStore.refreshPendingCount();
    },
  });
}

async function ignoreTopic(t: Topic) {
  Modal.confirm({
    title: '忽略议题',
    content: `确定忽略「${t.title}」吗？此议题不会删除，仍可在归档中查看。`,
    okText: '确定忽略',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      await updateTopicStatus(t.id, { status: 'ignored', reason: 'AI发现中心忽略' });
      message.success('已忽略');
      await refresh();
      await topicStore.refreshPendingCount();
    },
  });
}

onMounted(() => {
  refresh();
});
</script>

<template>
  <div class="discovery-page">
    <!-- 紧凑 Header：标题 + 统计 + 操作按钮同行 -->
    <div class="compact-header">
      <div class="header-left">
        <div class="title-section">
          <span class="kicker">AI 发现中心</span>
          <h1 class="headline">把噪声挡在门外，把价值推到你面前</h1>
        </div>
        <div class="stats-inline">
          <div class="stat-chip pending">
            <span class="stat-icon iconify lucide--clock" />
            <span class="stat-num">{{ stats.pending }}</span>
            <span class="stat-text">待确认</span>
          </div>
          <div class="stat-chip ignored">
            <span class="stat-icon iconify lucide--eye-off" />
            <span class="stat-num">{{ stats.ignored }}</span>
            <span class="stat-text">已忽略</span>
          </div>
          <div class="stat-chip total">
            <span class="stat-icon iconify lucide--sparkles" />
            <span class="stat-num">{{ stats.all }}</span>
            <span class="stat-text">AI 识别总数</span>
          </div>
          <div class="stat-chip feedback">
            <span class="stat-icon iconify lucide--message-square" />
            <span class="stat-num">{{ stats.totalFeedback }}</span>
            <span class="stat-text">条相关反馈</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <VbenButton variant="outline" size="sm" @click="refresh" :loading="loading">
          <span class="iconify lucide--refresh-cw" />
          刷新
        </VbenButton>
        <VbenButton size="sm" @click="() => router.push('/app/topic/list')">
          <span class="iconify lucide--lightbulb" />
          进入主题列表
        </VbenButton>
      </div>
    </div>

    <!-- 列表面板 -->
    <a-card :bordered="false" class="panel">
      <div class="toolbar">
        <a-input
          v-model:value="query"
          allowClear
          placeholder="搜索议题标题…"
          style="max-width: 280px"
        >
          <template #prefix>
            <span class="iconify lucide--search" style="opacity: 0.4" />
          </template>
        </a-input>

        <a-segmented
          v-model:value="view"
          :options="[
            { label: '待确认', value: 'pending' },
            { label: '已忽略', value: 'ignored' },
            { label: '全部', value: 'all' },
          ]"
        />

        <a-space>
          <span class="muted">显示噪声</span>
          <a-switch v-model:checked="showNoise" size="small" />
        </a-space>
      </div>

      <a-list
        :loading="loading"
        :data-source="filteredTopics"
        item-layout="horizontal"
        class="topic-list"
        :locale="{ emptyText: '暂无待审议题，继续收集反馈吧 🎉' }"
      >
        <template #renderItem="{ item }">
          <div class="topic-row">
            <div class="topic-main" @click="router.push(`/app/topic/detail/${item.id}`)">
              <div class="topic-title">
                <span class="topic-name">{{ item.title }}</span>
                <a-tag v-if="item.is_noise" size="small">建议隐藏</a-tag>
              </div>
              <div class="topic-meta">
                <span class="meta-item">
                  <span class="iconify lucide--message-square" />
                  {{ item.feedback_count }} 条反馈
                </span>
                <span :class="['meta-item', 'status-tag', `status-${item.status}`]">
                  <span :class="['iconify', statusIcon(item.status)]" />
                  {{ statusLabel(item.status) }}
                </span>
              </div>
            </div>
            <div class="topic-actions">
              <a-button type="text" size="small" @click.stop="router.push(`/app/topic/detail/${item.id}`)">
                <span class="iconify lucide--eye" />
                查看
              </a-button>
              <a-button 
                v-if="item.status === 'pending'" 
                type="primary" 
                size="small"
                ghost
                @click.stop="confirmTopic(item)"
              >
                <span class="iconify lucide--check" />
                采纳
              </a-button>
              <a-button 
                v-if="item.status === 'pending'" 
                danger 
                size="small"
                ghost
                @click.stop="ignoreTopic(item)"
              >
                <span class="iconify lucide--x" />
                忽略
              </a-button>
            </div>
          </div>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<style scoped>
.discovery-page {
  padding: 20px 24px;
  background: hsl(var(--background));
  min-height: 100%;
}

/* ===== 紧凑 Header ===== */
.compact-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(82, 196, 26, 0.06) 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.header-left {
  flex: 1;
  min-width: 0;
}

.title-section {
  margin-bottom: 12px;
}

.kicker {
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.45);
  font-weight: 500;
}

.headline {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  margin: 4px 0 0;
  color: rgba(0, 0, 0, 0.85);
}

/* 统计卡片横向紧凑 */
.stats-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 13px;
  transition: all 0.2s;
}

.stat-chip:hover {
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  font-size: 14px;
  opacity: 0.7;
}

.stat-num {
  font-weight: 700;
  font-size: 15px;
}

.stat-text {
  color: rgba(0, 0, 0, 0.55);
  font-size: 12px;
}

/* 数值颜色语义化 */
.stat-chip.pending .stat-num { color: #f59e0b; }
.stat-chip.ignored .stat-num { color: #6b7280; }
.stat-chip.total .stat-num { color: #10b981; }
.stat-chip.feedback .stat-num { color: #3b82f6; }

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ===== 面板 ===== */
.panel {
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.muted {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

/* ===== 议题列表 ===== */
.topic-list :deep(.ant-list-item) {
  padding: 0;
  border-bottom: none;
}

.topic-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}

.topic-row:hover {
  background: rgba(0, 0, 0, 0.02);
}

.topic-row:not(:last-child) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.topic-main {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.topic-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.topic-name {
  font-weight: 600;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
  transition: color 0.15s;
}

.topic-main:hover .topic-name {
  color: #1890ff;
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.55);
}

.meta-item .iconify {
  font-size: 12px;
  opacity: 0.6;
}

/* 状态标签 */
.status-tag {
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.status-tag .iconify {
  font-size: 13px;
  opacity: 1;
}

.status-pending {
  color: #fa8c16;
  background: rgba(250, 140, 22, 0.1);
}

.status-ignored {
  color: #8c8c8c;
  background: rgba(0, 0, 0, 0.04);
}

.status-planned {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.status-done {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

.status-completed {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

/* 操作按钮 */
.topic-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.topic-actions .ant-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.topic-actions .iconify {
  font-size: 14px;
}
</style>
