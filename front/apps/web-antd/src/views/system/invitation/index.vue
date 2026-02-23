<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { Button, message, Modal, Tag } from 'ant-design-vue';
import dayjs from 'dayjs';

import type { InvitationInfo } from '#/api/system/invitation';

import {
  createInvitation,
  deleteInvitation,
  getInvitationList,
} from '#/api/system/invitation';

defineOptions({ name: 'SystemInvitation' });

const router = useRouter();

const loading = ref(false);
const invitations = ref<InvitationInfo[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const queryForm = reactive({
  status: undefined as string | undefined,
  source: undefined as string | undefined,
  campaign: undefined as string | undefined,
});

const createModalVisible = ref(false);
const createForm = reactive({
  usage_limit: 10,
  expires_days: 90,
  plan_code: 'pro',
  trial_days: 90,
  source: '',
  campaign: '',
  notes: '',
});

const columns = [
  {
    title: 'Token',
    dataIndex: 'token',
    width: 200,
    ellipsis: true,
    customRender: ({ text }: any) => text?.substring(0, 12) + '...',
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    customRender: ({ record }: any) => {
      const statusMap: any = {
        active: { color: 'success', text: '活跃' },
        expired: { color: 'default', text: '已过期' },
        disabled: { color: 'error', text: '已禁用' },
      };
      const status = statusMap[record.status] || { color: 'default', text: record.status };
      return h(Tag, { color: status.color }, () => status.text);
    },
  },
  {
    title: '使用情况',
    dataIndex: 'used_count',
    width: 120,
    customRender: ({ record }: any) => `${record.used_count} / ${record.usage_limit}`,
  },
  {
    title: '套餐',
    dataIndex: 'plan_code',
    width: 100,
  },
  {
    title: '试用天数',
    dataIndex: 'trial_days',
    width: 100,
  },
  {
    title: '来源',
    dataIndex: 'source',
    width: 100,
  },
  {
    title: '活动',
    dataIndex: 'campaign',
    width: 150,
    ellipsis: true,
  },
  {
    title: '过期时间',
    dataIndex: 'expires_at',
    width: 180,
    customRender: ({ text }: any) => dayjs(text).format('YYYY-MM-DD HH:mm'),
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 180,
    customRender: ({ text }: any) => dayjs(text).format('YYYY-MM-DD HH:mm'),
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 180,
  },
];

async function fetchData() {
  try {
    loading.value = true;
    const result = await getInvitationList({
      ...queryForm,
      page: pagination.current,
      size: pagination.pageSize,
    });

    invitations.value = result.items || [];
    pagination.total = result.total || 0;
  } catch (error: any) {
    message.error(error.message || '获取列表失败');
  } finally {
    loading.value = false;
  }
}

function handleTableChange(paginationInfo: any) {
  pagination.current = paginationInfo.current;
  pagination.pageSize = paginationInfo.pageSize;
  fetchData();
}

function handleSearch() {
  pagination.current = 1;
  fetchData();
}

function handleReset() {
  queryForm.status = undefined;
  queryForm.source = undefined;
  queryForm.campaign = undefined;
  pagination.current = 1;
  fetchData();
}

function handleCreate() {
  createModalVisible.value = true;
}

async function handleSubmitCreate() {
  try {
    await createInvitation(createForm);
    message.success('创建成功');
    createModalVisible.value = false;
    fetchData();
  } catch (error: any) {
    message.error(error.message || '创建失败');
  }
}

function handleViewDetail(record: InvitationInfo) {
  router.push(`/admin/system/invitation/${record.id}`);
}

function handleCopyUrl(record: InvitationInfo) {
  const url = `${window.location.origin}/auth/register-invite?invite=${record.token}`;
  navigator.clipboard.writeText(url);
  message.success('链接已复制');
}

async function handleDelete(record: InvitationInfo) {
  Modal.confirm({
    title: '确认删除',
    content: '删除后将标记为已禁用，确定要删除吗？',
    onOk: async () => {
      try {
        await deleteInvitation(record.id);
        message.success('删除成功');
        fetchData();
      } catch (error: any) {
        message.error(error.message || '删除失败');
      }
    },
  });
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <Page
    auto-content-height
    content-class="flex flex-col"
    description="管理邀请链接，追踪使用情况"
    title="邀请管理"
  >
    <!-- 查询表单 -->
    <div class="mb-4 rounded-lg bg-white p-4 dark:bg-gray-800">
      <div class="mb-4 flex gap-4">
        <a-select
          v-model:value="queryForm.status"
          allow-clear
          placeholder="状态"
          style="width: 120px"
        >
          <a-select-option value="active">
            活跃
          </a-select-option>
          <a-select-option value="expired">
            已过期
          </a-select-option>
          <a-select-option value="disabled">
            已禁用
          </a-select-option>
        </a-select>
        <a-input
          v-model:value="queryForm.source"
          allow-clear
          placeholder="来源"
          style="width: 200px"
        />
        <a-input
          v-model:value="queryForm.campaign"
          allow-clear
          placeholder="活动"
          style="width: 200px"
        />
        <Button @click="handleSearch">
          查询
        </Button>
        <Button @click="handleReset">
          重置
        </Button>
      </div>
      <div>
        <Button type="primary" @click="handleCreate">
          创建邀请
        </Button>
      </div>
    </div>

    <!-- 数据表格 -->
    <a-table
      :columns="columns"
      :data-source="invitations"
      :loading="loading"
      :pagination="pagination"
      :scroll="{ x: 1500 }"
      row-key="id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <div class="flex gap-2">
            <a @click="handleViewDetail(record)">详情</a>
            <a @click="handleCopyUrl(record)">复制链接</a>
            <a class="text-red-500" @click="handleDelete(record)">删除</a>
          </div>
        </template>
      </template>
    </a-table>

    <!-- 创建弹窗 -->
    <Modal
      v-model:visible="createModalVisible"
      title="创建邀请"
      @ok="handleSubmitCreate"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="使用次数限制">
          <a-input-number
            v-model:value="createForm.usage_limit"
            :min="1"
            :max="1000"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="过期天数">
          <a-input-number
            v-model:value="createForm.expires_days"
            :min="1"
            :max="365"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="套餐代号">
          <a-select v-model:value="createForm.plan_code" style="width: 100%">
            <a-select-option value="starter">
              启航版
            </a-select-option>
            <a-select-option value="pro">
              专业版
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="试用天数">
          <a-input-number
            v-model:value="createForm.trial_days"
            :min="1"
            :max="365"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="来源">
          <a-input v-model:value="createForm.source" />
        </a-form-item>
        <a-form-item label="活动">
          <a-input v-model:value="createForm.campaign" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="createForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </Modal>
  </Page>
</template>
