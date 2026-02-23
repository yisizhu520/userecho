<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getMyFeedbacks, type MyFeedbacksStats } from '#/api/userecho/dashboard';

const router = useRouter();
const loading = ref(false);
const stats = ref<MyFeedbacksStats | null>(null);

// 标准化 API 返回的数据，确保所有值都是 primitive 类型
const normalizeData = (data: any): MyFeedbacksStats | null => {
  if (!data) return null;
  
  try {
    // 确保 summary 字段存在且为数字
    const summary = {
      submitted_count: Number(data.summary?.submitted_count ?? 0),
      in_progress_count: Number(data.summary?.in_progress_count ?? 0),
      completed_count: Number(data.summary?.completed_count ?? 0),
    };

    // 确保 recent_updates 是一个数组，且每个元素的字段都是 primitive
    const recent_updates = Array.isArray(data.recent_updates)
      ? data.recent_updates.map((item: any) => ({
          feedback_id: String(item.feedback_id ?? ''),
          content_summary: String(item.content_summary ?? ''),
          topic_id: item.topic_id ? String(item.topic_id) : null,
          topic_title: item.topic_title ? String(item.topic_title) : null,
          topic_status: item.topic_status ? String(item.topic_status) : null,
          updated_at: String(item.updated_at ?? ''),
        }))
      : [];

    return { summary, recent_updates };
  } catch (e) {
    console.error('normalizeData failed:', e, 'original data:', data);
    return null;
  }
};

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    const rawData = await getMyFeedbacks(5);
    stats.value = normalizeData(rawData);
  } catch (error) {
    console.error('Failed to load my feedbacks:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});

// 状态颜色映射
const statusColorMap: Record<string, string> = {
  pending: 'orange',
  planned: 'blue',
  in_progress: 'cyan',
  completed: 'green',
  ignored: 'default',
};

// 状态名称映射
const statusNameMap: Record<string, string> = {
  pending: '待确认',
  planned: '已排期',
  in_progress: '进行中',
  completed: '已完成',
  ignored: '已忽略',
};

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString('zh-CN');
};

// 跳转到我的反馈列表
const goToMyFeedbacks = () => {
  router.push('/app/feedback/list?creator=me');
};

// 跳转到主题详情
const goToTopic = (topicId: string) => {
  router.push(`/app/topic/detail/${topicId}`);
};

// 刷新数据
const refresh = () => {
  loadData();
};

defineExpose({ refresh });
</script>

<template>
  <a-card title="📋 我的反馈" class="my-feedbacks-card" :loading="loading">
    <template #extra>
      <a-button type="link" size="small" @click="goToMyFeedbacks">
        查看全部 →
      </a-button>
    </template>

    <template v-if="stats && stats.summary">
      <!-- 统计摘要 -->
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-value">{{ stats.summary.submitted_count ?? 0 }}</span>
          <span class="stat-label">已录入</span>
        </div>
        <div class="stat-item">
          <span class="stat-value in-progress">{{ stats.summary.in_progress_count ?? 0 }}</span>
          <span class="stat-label">处理中</span>
        </div>
        <div class="stat-item">
          <span class="stat-value completed">{{ stats.summary.completed_count ?? 0 }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>

      <!-- 最近更新列表 -->
      <a-divider style="margin: 16px 0" />
      
      <div class="recent-title">最近更新</div>
      
      <a-list
        v-if="stats.recent_updates && stats.recent_updates.length > 0"
        :data-source="stats.recent_updates"
        size="small"
        :split="false"
      >
        <template #renderItem="{ item }">
          <a-list-item class="update-item">
            <div class="update-content">
              <div class="content-text">{{ item.content_summary }}</div>
              <div class="update-meta">
                <a-tag 
                  v-if="item && item.topic_status" 
                  :color="statusColorMap[item.topic_status] || 'default'"
                  size="small"
                  class="status-tag"
                  @click="item.topic_id ? goToTopic(item.topic_id) : null"
                  style="cursor: pointer"
                >
                  {{ item.topic_title || statusNameMap[item.topic_status] || '未知状态' }}
                </a-tag>
                <span v-else class="muted">待聚类</span>
                <span class="update-time">{{ formatTime(item.updated_at) }}</span>
              </div>
            </div>
          </a-list-item>
        </template>
      </a-list>
      
      <div v-else class="empty-state">
        <a-empty description="暂无反馈记录" />
      </div>
    </template>
  </a-card>
</template>

<style scoped>
.my-feedbacks-card {
  margin-bottom: 16px;
}

.stats-row {
  display: flex;
  justify-content: space-around;
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1890ff;
  line-height: 1.2;
}

.stat-value.in-progress {
  color: #13c2c2;
}

.stat-value.completed {
  color: #52c41a;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.recent-title {
  font-size: 13px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 8px;
}

.update-item {
  padding: 8px 0 !important;
}

.update-content {
  width: 100%;
}

.content-text {
  font-size: 13px;
  color: #262626;
  line-height: 1.4;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.update-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  font-size: 11px;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
}

.muted {
  font-size: 12px;
  color: #bfbfbf;
}

.update-time {
  font-size: 11px;
  color: #8c8c8c;
  margin-left: auto;
}

.empty-state {
  padding: 20px 0;
  color: #8c8c8c;
  text-align: center;
}
</style>
