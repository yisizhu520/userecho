<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Card, Progress, Tag, Tooltip } from 'ant-design-vue';

interface CustomerTypeDistribution {
  type: string;
  name: string;
  count: number;
}

interface TopCustomer {
  id: string;
  name: string;
  customer_type: string;
  mrr: number;
  feedback_count: number;
}

interface Props {
  total?: number;
  newCount?: number;
  active7d?: number;
  typeDistribution?: CustomerTypeDistribution[];
  totalMrr?: number;
  topCustomers?: TopCustomer[];
}

withDefaults(defineProps<Props>(), {
  total: 0,
  newCount: 0,
  active7d: 0,
  typeDistribution: () => [],
  totalMrr: 0,
  topCustomers: () => [],
});
const router = useRouter();

// 客户类型颜色映射
const typeColorMap: Record<string, string> = {
  strategic: '#722ed1',
  vip: '#eb2f96',
  paid: '#1890ff',
  normal: '#8c8c8c',
};

// 客户类型标签颜色
const typeTagColorMap: Record<string, string> = {
  strategic: 'purple',
  vip: 'magenta',
  paid: 'blue',
  normal: 'default',
};

// 客户类型名称
const typeNameMap: Record<string, string> = {
  strategic: '战略',
  vip: 'VIP',
  paid: '付费',
  normal: '普通',
};

// 格式化金额
const formatMoney = (value: number) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return `¥${value.toLocaleString()}`;
};

// 计算总客户数用于百分比
const getTotalCustomers = (distribution: CustomerTypeDistribution[]) => {
  return distribution.reduce((sum, item) => sum + item.count, 0);
};

// 跳转到客户详情
const goToCustomer = (customerId: string) => {
  router.push(`/app/customer/detail/${customerId}`);
};

// 跳转到客户列表
const goToCustomerList = () => {
  router.push('/app/customer');
};
</script>

<template>
  <Card title="👥 客户概览" class="customer-stats-card">
    <template #extra>
      <a-button type="link" size="small" @click="goToCustomerList">
        查看全部 →
      </a-button>
    </template>

    <!-- 核心指标 -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-value">{{ total }}</span>
        <span class="stat-label">总客户</span>
      </div>
      <div class="stat-item">
        <span class="stat-value new">+{{ newCount }}</span>
        <span class="stat-label">本周新增</span>
      </div>
      <div class="stat-item">
        <span class="stat-value mrr">{{ formatMoney(totalMrr) }}</span>
        <span class="stat-label">MRR 总额</span>
      </div>
    </div>

    <!-- 客户类型分布 -->
    <a-divider style="margin: 16px 0" />
    <div class="section-title">客户分布</div>
    <div class="type-distribution">
      <div
        v-for="item in typeDistribution"
        :key="item.type"
        class="type-item"
      >
        <div class="type-header">
          <span class="type-name">{{ item.name }}</span>
          <span class="type-count">{{ item.count }}家</span>
        </div>
        <Progress
          :percent="Math.round((item.count / getTotalCustomers(typeDistribution)) * 100)"
          :stroke-color="typeColorMap[item.type] || '#8c8c8c'"
          :show-info="false"
          size="small"
        />
      </div>
    </div>

    <!-- 高价值客户 TOP 5 -->
    <template v-if="topCustomers.length > 0">
      <a-divider style="margin: 16px 0" />
      <div class="section-title">高价值客户</div>
      <div class="top-customers">
        <div
          v-for="(customer, index) in topCustomers"
          :key="customer.id"
          class="customer-item"
          @click="goToCustomer(customer.id)"
        >
          <div class="customer-rank" :class="{ top3: index < 3 }">
            {{ index + 1 }}
          </div>
          <div class="customer-info">
            <div class="customer-name">
              <Tooltip :title="customer.name">
                <span class="name-text">{{ customer.name }}</span>
              </Tooltip>
              <Tag
                :color="typeTagColorMap[customer.customer_type]"
                size="small"
                class="type-tag"
              >
                {{ typeNameMap[customer.customer_type] || customer.customer_type }}
              </Tag>
            </div>
            <div class="customer-meta">
              <span class="mrr-value">{{ formatMoney(customer.mrr) }}/月</span>
              <span class="feedback-count">{{ customer.feedback_count }}条反馈</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 无高价值客户时的提示 -->
    <template v-else>
      <a-divider style="margin: 16px 0" />
      <div class="empty-hint">
        暂无 MRR 数据，请完善客户商业信息
      </div>
    </template>
  </Card>
</template>

<style scoped>
.customer-stats-card {
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
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
  line-height: 1.2;
}

.stat-value.new {
  color: #52c41a;
}

.stat-value.mrr {
  color: #722ed1;
  font-size: 20px;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 12px;
}

.type-distribution {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-name {
  font-size: 12px;
  color: #595959;
}

.type-count {
  font-size: 12px;
  color: #8c8c8c;
}

.top-customers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.customer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.customer-item:hover {
  background-color: #f5f5f5;
}

.customer-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0f0f0;
  color: #8c8c8c;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.customer-rank.top3 {
  background: linear-gradient(135deg, #ffd700 0%, #ffb800 100%);
  color: #fff;
}

.customer-info {
  flex: 1;
  min-width: 0;
}

.customer-name {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.name-text {
  font-size: 13px;
  color: #262626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.type-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 16px;
  line-height: 16px;
  flex-shrink: 0;
}

.customer-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #8c8c8c;
}

.mrr-value {
  color: #722ed1;
  font-weight: 500;
}

.empty-hint {
  text-align: center;
  color: #bfbfbf;
  font-size: 13px;
  padding: 16px 0;
}
</style>
