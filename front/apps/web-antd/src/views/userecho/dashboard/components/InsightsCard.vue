<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';
import { Card, Alert, Tag, Spin } from 'ant-design-vue';

import { getDashboardInsights, type DashboardInsights } from '#/api/userecho/insight';

const router = useRouter();

const loading = ref(true);
const insights = ref<DashboardInsights | null>(null);

// 加载洞察数据
async function loadInsights() {
  try {
    loading.value = true;
    insights.value = await getDashboardInsights();
  } catch (error) {
    console.error('Failed to load insights:', error);
  } finally {
    loading.value = false;
  }
}

// 紧急程度颜色
const urgencyColors = {
  critical: 'red',
  high: 'orange',
  medium: 'blue',
  low: 'default',
};

// 风险等级颜色
const riskColors = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
};

// 跳转到需求详情
function goToTopic(topicId: string) {
  router.push(`/app/topic/detail/${topicId}`);
}

// 跳转到报告页
function goToReport() {
  router.push('/app/insights/report');
}

onMounted(() => {
  loadInsights();
});
</script>

<template>
  <div class="insights-section">
    <div class="insights-header">
      <h2 class="insights-title">
        <span class="iconify lucide--brain-circuit" style="font-size: 24px; margin-right: 8px;"></span>
        AI 洞察
      </h2>
      <VbenButton variant="outline" @click="loadInsights" :loading="loading">
        <span class="iconify lucide--refresh-cw" />
        刷新
      </VbenButton>
    </div>

    <div v-if="loading" class="text-center py-8">
      <Spin size="large" tip="正在生成洞察..." />
    </div>

    <div v-else-if="insights" class="insights-content">
      <!-- 优先级建议 -->
      <Card title="🎯 本周优先级建议" class="insight-card" :bordered="false">
        <template #extra>
          <VbenButton variant="link" @click="goToReport">
            查看完整报告
          </VbenButton>
        </template>

        <div v-if="insights.priority_suggestions?.top_recommendations?.length">
          <Alert
            :message="insights.priority_suggestions.summary"
            type="info"
            show-icon
            class="mb-4"
          />

          <div class="recommendations-list">
            <div
              v-for="(item, index) in insights.priority_suggestions.top_recommendations.slice(0, 3)"
              :key="item.topic_id"
              class="recommendation-item"
              @click="goToTopic(item.topic_id)"
            >
              <div class="recommendation-header">
                <span class="recommendation-rank">{{ index + 1 }}</span>
                <span class="recommendation-title">{{ item.title }}</span>
                <Tag :color="urgencyColors[item.urgency_level]">
                  {{ item.urgency_level }}
                </Tag>
              </div>
              <div class="recommendation-reason">{{ item.reason }}</div>
              <div class="recommendation-action">
                <Tag color="green">{{ item.suggested_action }}</Tag>
                <span class="recommendation-roi">ROI: {{ item.estimated_roi.toFixed(1) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="iconify lucide--check-circle" style="font-size: 48px; color: #52c41a;"></span>
          <p>暂无待处理的需求</p>
        </div>
      </Card>

      <!-- 高风险需求 -->
      <Card title="⚠️ 高风险需求" class="insight-card mt-4" :bordered="false">
        <div v-if="insights.high_risk_topics?.high_risk_topics?.length">
          <Alert
            :message="insights.high_risk_topics.summary"
            :type="insights.high_risk_topics.high_risk_topics.some(t => t.risk_level === 'critical') ? 'error' : 'warning'"
            show-icon
            class="mb-4"
          />

          <div class="risk-topics-list">
            <div
              v-for="topic in insights.high_risk_topics.high_risk_topics.slice(0, 5)"
              :key="topic.topic_id"
              class="risk-topic-item"
              @click="goToTopic(topic.topic_id)"
            >
              <div class="risk-topic-header">
                <span class="risk-topic-title">{{ topic.title }}</span>
                <Tag :color="riskColors[topic.risk_level]">
                  {{ topic.risk_level }}
                </Tag>
              </div>
              <div class="risk-topic-details">
                <span>已持续 {{ topic.days_unresolved }} 天</span>
                <span class="mx-2">|</span>
                <span>优先级: {{ topic.priority_score.toFixed(1) }}</span>
                <span class="mx-2">|</span>
                <span>影响 {{ topic.affected_customers.length }} 个客户</span>
              </div>
              <div class="risk-topic-customers">
                <Tag
                  v-for="customer in topic.affected_customers.slice(0, 3)"
                  :key="customer.name"
                  size="small"
                >
                  {{ customer.name }}
                </Tag>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="iconify lucide--shield-check" style="font-size: 48px; color: #52c41a;"></span>
          <p>✅ 暂无高风险需求</p>
        </div>
      </Card>

      <!-- 满意度趋势 -->
      <Card title="📈 客户满意度趋势" class="insight-card mt-4" :bordered="false">
        <div v-if="insights.sentiment_summary">
          <Alert
            :message="insights.sentiment_summary.summary"
            :type="parseFloat(insights.sentiment_summary.sentiment_trend.change) > 0 ? 'success' : 'warning'"
            show-icon
            class="mb-4"
          />

          <div class="sentiment-stats">
            <div class="sentiment-stat">
              <div class="sentiment-stat-label">本周正面占比</div>
              <div class="sentiment-stat-value" style="color: #52c41a;">
                {{ insights.sentiment_summary.sentiment_trend.this_week.positive_rate.toFixed(0) }}%
              </div>
            </div>
            <div class="sentiment-stat">
              <div class="sentiment-stat-label">环比变化</div>
              <div
                class="sentiment-stat-value"
                :style="{ color: parseFloat(insights.sentiment_summary.sentiment_trend.change) > 0 ? '#52c41a' : '#ff4d4f' }"
              >
                {{ insights.sentiment_summary.sentiment_trend.change }}
              </div>
            </div>
            <div class="sentiment-stat">
              <div class="sentiment-stat-label">负面反馈数</div>
              <div class="sentiment-stat-value" style="color: #ff4d4f;">
                {{ insights.sentiment_summary.sentiment_trend.this_week.negative }}
              </div>
            </div>
          </div>

          <div v-if="insights.sentiment_summary.negative_topics?.length" class="mt-4">
            <div class="negative-topics-label">负面反馈集中的主题：</div>
            <div class="negative-topics-list">
              <Tag
                v-for="topic in insights.sentiment_summary.negative_topics.slice(0, 5)"
                :key="topic.topic_id"
                color="red"
                class="cursor-pointer"
                @click="goToTopic(topic.topic_id)"
              >
                {{ topic.title }} ({{ topic.negative_count }})
              </Tag>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <div v-else class="text-center py-8">
      <p class="text-gray-500">加载失败，请稍后重试</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.insights-section {
  margin-top: 20px;
}

.insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.insights-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.insights-content {
  .insight-card {
    cursor: default;
    transition: box-shadow 0.3s;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
  }
}

.recommendations-list {
  .recommendation-item {
    padding: 12px;
    margin-bottom: 12px;
    background: #fafafa;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s;

    &:hover {
      background: #f0f0f0;
    }

    &:last-child {
      margin-bottom: 0;
    }
  }

  .recommendation-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .recommendation-rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: #1890ff;
    color: white;
    border-radius: 50%;
    font-size: 12px;
    font-weight: bold;
  }

  .recommendation-title {
    flex: 1;
    font-size: 14px;
    font-weight: 500;
  }

  .recommendation-reason {
    margin-left: 32px;
    margin-bottom: 8px;
    color: #666;
    font-size: 13px;
  }

  .recommendation-action {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 32px;
  }

  .recommendation-roi {
    color: #1890ff;
    font-size: 12px;
  }
}

.risk-topics-list {
  .risk-topic-item {
    padding: 12px;
    margin-bottom: 12px;
    background: #fff1f0;
    border-left: 3px solid #ff4d4f;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s;

    &:hover {
      background: #ffe7e6;
    }

    &:last-child {
      margin-bottom: 0;
    }
  }

  .risk-topic-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .risk-topic-title {
    font-size: 14px;
    font-weight: 500;
  }

  .risk-topic-details {
    margin-bottom: 8px;
    color: #666;
    font-size: 12px;
  }

  .risk-topic-customers {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
}

.sentiment-stats {
  display: flex;
  justify-content: space-around;
  gap: 16px;
}

.sentiment-stat {
  flex: 1;
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.sentiment-stat-label {
  margin-bottom: 8px;
  color: #666;
  font-size: 12px;
}

.sentiment-stat-value {
  font-size: 24px;
  font-weight: bold;
}

.negative-topics-label {
  margin-bottom: 8px;
  color: #666;
  font-size: 13px;
}

.negative-topics-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;

  p {
    margin-top: 16px;
    font-size: 14px;
  }
}
</style>
