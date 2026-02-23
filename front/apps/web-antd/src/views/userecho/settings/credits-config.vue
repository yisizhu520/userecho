<script setup lang="ts">
/**
 * 积分配置管理页面（Admin）
 */
import { onMounted, ref } from 'vue';
import {
  Card,
  Table,
  Button,
  InputNumber,
  Input,
  Modal,
  Tag,
  message,
  Descriptions,
  Spin,
  Tabs,
} from 'ant-design-vue';
import {
  getCreditsConfigs,
  updateCreditsConfig,
  getAllTenantCredits,
  adjustTenantCredits,
  type CreditsConfigItem,
  type TenantCreditsItem,
} from '#/api/userecho/credits';

// ==================== 数据 ====================

const loading = ref(false);
const operationCostConfigs = ref<CreditsConfigItem[]>([]);
const planQuotaConfigs = ref<CreditsConfigItem[]>([]);
const tenantCredits = ref<TenantCreditsItem[]>([]);
const activeTab = ref('config');

// 编辑状态
const editingId = ref<string | null>(null);
const editValue = ref(0);

// 调整积分弹窗
const adjustModalVisible = ref(false);
const adjustTenantId = ref('');
const adjustAmount = ref(0);
const adjustReason = ref('');

// ==================== 计算属性 ====================

const operationLabels: Record<string, string> = {
  cost_clustering: 'AI 聚类',
  cost_screenshot: '截图识别',
  cost_summary: 'AI 摘要',
  cost_embedding: '向量化',
  cost_insight: '洞察报告',
};

const planLabels: Record<string, string> = {
  quota_starter: '启航版',
  quota_pro: '专业版',
  quota_team: '团队版',
  quota_enterprise: '企业版',
};

const planColors: Record<string, string> = {
  starter: 'default',
  pro: 'blue',
  team: 'green',
  enterprise: 'gold',
};

// ==================== 方法 ====================

async function loadConfigs() {
  loading.value = true;
  try {
    const data = await getCreditsConfigs();
    operationCostConfigs.value = data.operation_cost || [];
    planQuotaConfigs.value = data.plan_quota || [];
  } catch (e) {
    message.error('加载配置失败');
  } finally {
    loading.value = false;
  }
}

async function loadTenants() {
  loading.value = true;
  try {
    const data = await getAllTenantCredits();
    tenantCredits.value = data || [];
  } catch (e) {
    message.error('加载租户积分失败');
  } finally {
    loading.value = false;
  }
}

function startEdit(config: CreditsConfigItem) {
  editingId.value = config.id;
  editValue.value = config.config_value;
}

async function saveEdit(config: CreditsConfigItem) {
  try {
    await updateCreditsConfig(config.id, { config_value: editValue.value });
    config.config_value = editValue.value;
    editingId.value = null;
    message.success('配置已更新');
  } catch (e) {
    message.error('更新失败');
  }
}

function cancelEdit() {
  editingId.value = null;
}

function openAdjustModal(tenantId: string) {
  adjustTenantId.value = tenantId;
  adjustAmount.value = 0;
  adjustReason.value = '';
  adjustModalVisible.value = true;
}

async function confirmAdjust() {
  if (!adjustReason.value.trim()) {
    message.warning('请填写调整原因');
    return;
  }
  try {
    const result = await adjustTenantCredits(adjustTenantId.value, {
      adjustment: adjustAmount.value,
      reason: adjustReason.value,
    });
    message.success(`积分已调整：${result.old_balance} → ${result.new_balance}`);
    adjustModalVisible.value = false;
    loadTenants();
  } catch (e) {
    message.error('调整失败');
  }
}

function asConfigItem(record: any): CreditsConfigItem {
  return record as CreditsConfigItem;
}

// ==================== 表格列 ====================

const configColumns = [
  {
    title: '配置项',
    dataIndex: 'config_key',
    key: 'config_key',
    customRender: ({ record }: { record: CreditsConfigItem }) => {
      const label = operationLabels[record.config_key] || planLabels[record.config_key] || record.config_key;
      return label;
    },
  },
  {
    title: '积分值',
    dataIndex: 'config_value',
    key: 'config_value',
    width: 150,
  },
  {
    title: '说明',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true,
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
  },
];

const tenantColumns = [
  {
    title: '租户ID',
    dataIndex: 'tenant_id',
    key: 'tenant_id',
    ellipsis: true,
    width: 280,
  },
  {
    title: '套餐',
    dataIndex: 'plan_type',
    key: 'plan_type',
    width: 100,
  },
  {
    title: '月度额度',
    dataIndex: 'monthly_quota',
    key: 'monthly_quota',
    width: 100,
    customRender: ({ text }: { text: number }) => (text === -1 ? '无限制' : text),
  },
  {
    title: '当前余额',
    dataIndex: 'current_balance',
    key: 'current_balance',
    width: 100,
  },
  {
    title: '累计使用',
    dataIndex: 'total_used',
    key: 'total_used',
    width: 100,
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
  },
];

// ==================== 生命周期 ====================

onMounted(() => {
  loadConfigs();
  loadTenants();
});
</script>

<template>
  <div class="credits-config-page">
    <Spin :spinning="loading">
      <Tabs v-model:activeKey="activeTab">
        <!-- 积分配置 Tab -->
        <Tabs.TabPane key="config" tab="积分配置">
          <div class="config-section">
            <Card title="操作消耗配置" size="small" class="mb-4">
              <Table
                :dataSource="operationCostConfigs"
                :columns="configColumns"
                :pagination="false"
                size="small"
                rowKey="id"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'config_value'">
                    <InputNumber
                      v-if="editingId === record.id"
                      v-model:value="editValue"
                      :min="0"
                      size="small"
                      style="width: 80px"
                    />
                    <span v-else>{{ record.config_value }} 积分</span>
                  </template>
                  <template v-if="column.key === 'action'">
                    <template v-if="editingId === record.id">
                      <Button type="link" size="small" @click="saveEdit(asConfigItem(record))">保存</Button>
                      <Button type="link" size="small" @click="cancelEdit">取消</Button>
                    </template>
                    <Button v-else type="link" size="small" @click="startEdit(asConfigItem(record))">编辑</Button>
                  </template>
                </template>
              </Table>
            </Card>

            <Card title="套餐额度配置" size="small">
              <Table
                :dataSource="planQuotaConfigs"
                :columns="configColumns"
                :pagination="false"
                size="small"
                rowKey="id"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'config_value'">
                    <InputNumber
                      v-if="editingId === record.id"
                      v-model:value="editValue"
                      :min="-1"
                      size="small"
                      style="width: 100px"
                    />
                    <span v-else>
                      {{ record.config_value === -1 ? '无限制' : `${record.config_value} 积分/月` }}
                    </span>
                  </template>
                  <template v-if="column.key === 'action'">
                    <template v-if="editingId === record.id">
                      <Button type="link" size="small" @click="saveEdit(asConfigItem(record))">保存</Button>
                      <Button type="link" size="small" @click="cancelEdit">取消</Button>
                    </template>
                    <Button v-else type="link" size="small" @click="startEdit(asConfigItem(record))">编辑</Button>
                  </template>
                </template>
              </Table>
            </Card>
          </div>
        </Tabs.TabPane>

        <!-- 租户积分 Tab -->
        <Tabs.TabPane key="tenants" tab="租户积分">
          <Card size="small">
            <Table
              :dataSource="tenantCredits"
              :columns="tenantColumns"
              :pagination="{ pageSize: 20 }"
              size="small"
              rowKey="id"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'plan_type'">
                  <Tag :color="planColors[record.plan_type] || 'default'">{{ record.plan_type }}</Tag>
                </template>
                <template v-if="column.key === 'current_balance'">
                  <Tag
                    :color="
                      record.current_balance < 50
                        ? 'red'
                        : record.current_balance < 200
                          ? 'orange'
                          : 'green'
                    "
                  >
                    {{ record.current_balance }}
                  </Tag>
                </template>
                <template v-if="column.key === 'action'">
                  <Button type="link" size="small" @click="openAdjustModal(record.tenant_id)">
                    调整
                  </Button>
                </template>
              </template>
            </Table>
          </Card>
        </Tabs.TabPane>
      </Tabs>
    </Spin>

    <!-- 调整积分弹窗 -->
    <Modal
      v-model:open="adjustModalVisible"
      title="调整租户积分"
      @ok="confirmAdjust"
      okText="确认调整"
      cancelText="取消"
    >
      <div class="adjust-form">
        <Descriptions :column="1" size="small" bordered>
          <Descriptions.Item label="租户ID">{{ adjustTenantId }}</Descriptions.Item>
          <Descriptions.Item label="调整积分">
            <InputNumber
              v-model:value="adjustAmount"
              :min="-10000"
              :max="10000"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500">正数增加，负数扣减</span>
          </Descriptions.Item>
          <Descriptions.Item label="调整原因">
            <Input v-model:value="adjustReason" placeholder="请填写调整原因" />
          </Descriptions.Item>
        </Descriptions>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.credits-config-page {
  padding: 16px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.text-gray-500 {
  color: #6b7280;
}

.adjust-form {
  padding: 16px 0;
}
</style>
