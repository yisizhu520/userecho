<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { Button, Card, Descriptions, message, Statistic, Table, Tag } from 'ant-design-vue';
import dayjs from 'dayjs';

import type {
  InvitationDetail,
  InvitationUsageRecord,
} from '#/api/system/invitation';

import {
  getInvitationDetail,
  getInvitationUsage,
} from '#/api/system/invitation';

defineOptions({ name: 'SystemInvitationDetail' });

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const invitation = ref<InvitationDetail | null>(null);
const usageRecords = ref<InvitationUsageRecord[]>([]);
const statistics = ref({
  total_used: 0,
  completed_onboarding: 0,
  conversion_rate: 0,
});

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const invitationId = computed(() => route.params.id as string);

const usageColumns = [
  {
    title: '用户',
    key: 'user',
    width: 200,
    customRender: ({ record }: any) => {
      return `${record.user?.nickname || '-'} (${record.registered_email})`;
    },
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    width: 150,
  },
  {
    title: '完成引导',
    dataIndex: 'completed_onboarding',
    width: 100,
    customRender: ({ text }: any) => {
      return h(Tag, { color: text ? 'success' : 'default' }, () => text ? '是' : '否');
    },
  },
  {
    title: '创建租户',
    key: 'tenant',
    width: 200,
    customRender: ({ record }: any) => record.created_tenant?.name || '-',
  },
  {
    title: '使用时间',
    dataIndex: 'used_at',
    width: 180,
    customRender: ({ text }: any) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
  },
];

async function fetchDetail() {
  try {
    loading.value = true;
    const result = await getInvitationDetail(invitationId.value);
    invitation.value = result.data;
  } catch (error: any) {
    message.error(error.message || '获取详情失败');
  } finally {
    loading.value = false;
  }
}

async function fetchUsage() {
  try {
    const result = await getInvitationUsage(invitationId.value, {
      page: pagination.current,
      size: pagination.pageSize,
    });

    usageRecords.value = result.data.usage_records || [];
    statistics.value = result.data.statistics || {
      total_used: 0,
      completed_onboarding: 0,
      conversion_rate: 0,
    };
    pagination.total = result.data.total || 0;
  } catch (error: any) {
    message.error(error.message || '获取使用记录失败');
  }
}

function handleTableChange(paginationInfo: any) {
  pagination.current = paginationInfo.current;
  pagination.pageSize = paginationInfo.pageSize;
  fetchUsage();
}

function handleCopyUrl() {
  if (invitation.value) {
    navigator.clipboard.writeText(invitation.value.url);
    message.success('链接已复制');
  }
}

function handleCopyToken() {
  if (invitation.value) {
    navigator.clipboard.writeText(invitation.value.token);
    message.success('Token已复制');
  }
}

function handleBack() {
  router.back();
}

const statusConfig = computed(() => {
  const status = invitation.value?.status || '';
  const configs: any = {
    active: { color: 'success', text: '活跃' },
    expired: { color: 'default', text: '已过期' },
    disabled: { color: 'error', text: '已禁用' },
  };
  return configs[status] || { color: 'default', text: status };
});

onMounted(() => {
  fetchDetail();
  fetchUsage();
});
</script>

<template>
  <Page
    auto-content-height
    content-class="flex flex-col"
    title="邀请详情"
  >
    <template #header-actions>
      <Button @click="handleBack">
        返回
      </Button>
    </template>

    <div class="space-y-4">
      <!-- 基本信息 -->
      <Card title="基本信息" :loading="loading">
        <Descriptions :column="2" bordered>
          <Descriptions.Item label="Token">
            {{ invitation?.token }}
            <Button size="small" type="link" @click="handleCopyToken">
              复制
            </Button>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag :color="statusConfig.color">
              {{ statusConfig.text }}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="邀请链接" :span="2">
            <div class="flex items-center gap-2">
              <span class="flex-1 truncate">{{ invitation?.url }}</span>
              <Button size="small" type="link" @click="handleCopyUrl">
                复制
              </Button>
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="使用情况">
            {{ invitation?.used_count }} / {{ invitation?.usage_limit }}
          </Descriptions.Item>
          <Descriptions.Item label="剩余次数">
            {{ invitation?.remaining_usage }}
          </Descriptions.Item>
          <Descriptions.Item label="套餐">
            {{ invitation?.plan_code }}
          </Descriptions.Item>
          <Descriptions.Item label="试用天数">
            {{ invitation?.trial_days }} 天
          </Descriptions.Item>
          <Descriptions.Item label="来源">
            {{ invitation?.source || '-' }}
          </Descriptions.Item>
          <Descriptions.Item label="活动">
            {{ invitation?.campaign || '-' }}
          </Descriptions.Item>
          <Descriptions.Item label="过期时间">
            {{ invitation?.expires_at ? dayjs(invitation.expires_at).format('YYYY-MM-DD HH:mm:ss') : '-' }}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {{ invitation?.created_at ? dayjs(invitation.created_at).format('YYYY-MM-DD HH:mm:ss') : '-' }}
          </Descriptions.Item>
          <Descriptions.Item label="备注" :span="2">
            {{ invitation?.notes || '-' }}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <!-- 使用统计 -->
      <Card title="使用统计">
        <div class="grid grid-cols-3 gap-4">
          <Statistic
            title="总使用次数"
            :value="statistics.total_used"
          />
          <Statistic
            title="完成引导"
            :value="statistics.completed_onboarding"
          />
          <Statistic
            title="转化率"
            :value="(statistics.conversion_rate * 100).toFixed(1)"
            suffix="%"
          />
        </div>
      </Card>

      <!-- 使用记录 -->
      <Card title="使用记录">
        <Table
          :columns="usageColumns"
          :data-source="usageRecords"
          :pagination="pagination"
          row-key="id"
          @change="handleTableChange"
        />
      </Card>
    </div>
  </Page>
</template>
