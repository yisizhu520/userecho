<script setup lang="ts">
import type { Topic } from '#/api';

import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';

import { Modal, message } from 'ant-design-vue';

import { getTopicList, updateTopicStatus } from '#/api';

const router = useRouter();

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

function confidenceOf(t: Topic) {
  const q: any = t.cluster_quality || {};
  const c = Number.isFinite(q.confidence) ? Number(q.confidence) : (t.ai_confidence ?? 0);
  return Math.max(0, Math.min(1, c));
}

function qualityLabel(t: Topic) {
  const c = confidenceOf(t);
  if (t.is_noise) return '噪声/低质量';
  if (c >= 0.8) return '高置信';
  if (c >= 0.6) return '中等';
  return '待验证';
}

function qualityColor(t: Topic) {
  const c = confidenceOf(t);
  if (t.is_noise) return 'default';
  if (c >= 0.8) return 'green';
  if (c >= 0.6) return 'blue';
  return 'orange';
}

async function confirmTopic(t: Topic) {
  Modal.confirm({
    title: '确认主题',
    content: `确认将「${t.title}」加入计划？`,
    okText: '确认',
    cancelText: '取消',
    async onOk() {
      await updateTopicStatus(t.id, { status: 'planned', reason: 'AI发现中心确认' });
      message.success('已加入计划');
      await refresh();
    },
  });
}

async function ignoreTopic(t: Topic) {
  Modal.confirm({
    title: '忽略主题',
    content: `忽略「${t.title}」？（仍可在主题列表中查看）`,
    okText: '忽略',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      await updateTopicStatus(t.id, { status: 'ignored', reason: 'AI发现中心忽略' });
      message.success('已忽略');
      await refresh();
    },
  });
}

onMounted(() => {
  refresh();
});
</script>

<template>
  <div class="discovery-page">
    <div class="header">
      <div class="title">
        <div class="kicker">AI 发现中心</div>
        <div class="headline">把噪声挡在门外，把价值推到你面前</div>
      </div>

      <div class="actions">
        <VbenButton variant="outline" @click="refresh" :loading="loading">
          <span class="iconify lucide--refresh-cw" />
          刷新
        </VbenButton>
        <VbenButton type="primary" @click="() => router.push('/app/topic/list')">
          <span class="iconify lucide--lightbulb" />
          进入主题列表
        </VbenButton>
      </div>
    </div>

    <a-card class="hero" :bordered="false">
      <div class="hero-inner">
        <div class="stat">
          <div class="stat-label">待确认主题</div>
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-hint">覆盖反馈 {{ stats.totalFeedback }} 条</div>
        </div>
        <div class="stat">
          <div class="stat-label">已忽略</div>
          <div class="stat-value">{{ stats.ignored }}</div>
          <div class="stat-hint">可随时回看</div>
        </div>
        <div class="stat">
          <div class="stat-label">AI 生成总数</div>
          <div class="stat-value">{{ stats.all }}</div>
          <div class="stat-hint">仅展示 ai_generated=true</div>
        </div>
      </div>
    </a-card>

    <a-card :bordered="false" class="panel">
      <div class="toolbar">
        <a-input
          v-model:value="query"
          allowClear
          placeholder="搜索主题标题…"
          style="max-width: 360px"
        />

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
          <a-switch v-model:checked="showNoise" />
        </a-space>
      </div>

      <a-list
        :loading="loading"
        :data-source="filteredTopics"
        item-layout="horizontal"
        class="list"
      >
        <template #renderItem="{ item }">
          <a-list-item class="row">
            <template #actions>
              <a-space>
                <a-button type="link" @click="router.push(`/app/topic/detail/${item.id}`)">查看</a-button>
                <a-button v-if="item.status === 'pending'" type="primary" @click="confirmTopic(item)">确认</a-button>
                <a-button v-if="item.status === 'pending'" danger @click="ignoreTopic(item)">忽略</a-button>
              </a-space>
            </template>

            <a-list-item-meta>
              <template #title>
                <div class="row-title">
                  <span class="name" @click="router.push(`/app/topic/detail/${item.id}`)">{{ item.title }}</span>
                  <a-tag :color="qualityColor(item)" class="ml-2">{{ qualityLabel(item) }}</a-tag>
                  <a-tag v-if="item.is_noise" color="default" class="ml-2">建议隐藏</a-tag>
                </div>
              </template>
              <template #description>
                <div class="row-desc">
                  <span class="chip">
                    <span class="iconify lucide--message-square" />
                    {{ item.feedback_count }} 条反馈
                  </span>
                  <span class="chip">
                    <span class="iconify lucide--sparkles" />
                    置信度 {{ Math.round(confidenceOf(item) * 100) }}%
                  </span>
                  <span class="muted">状态：{{ item.status }}</span>
                </div>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<style scoped>
.discovery-page {
  padding: 24px;
}

.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.55);
}

.headline {
  font-size: 24px;
  font-weight: 650;
  line-height: 1.2;
  margin-top: 6px;
}

.actions {
  display: flex;
  gap: 12px;
}

.hero {
  margin-bottom: 16px;
  background: radial-gradient(1200px 600px at 15% 0%, rgba(24, 144, 255, 0.18), rgba(255, 255, 255, 0)),
    radial-gradient(900px 520px at 85% 10%, rgba(82, 196, 26, 0.12), rgba(255, 255, 255, 0));
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.hero-inner {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stat {
  padding: 14px 14px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: rgba(0, 0, 0, 0.55);
  font-size: 13px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 6px;
}

.stat-hint {
  margin-top: 6px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.panel {
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.muted {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.row {
  padding: 10px 4px;
}

.row-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.name {
  cursor: pointer;
  font-weight: 650;
}

.row-desc {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}
</style>

