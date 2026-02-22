<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsEdit } from '@vben/icons';
import { message, Modal, Table, Tag, Space, Select, Input, Form, FormItem } from 'ant-design-vue';

import {
  getTenantMembers,
  getTenantRoles,
  createTenantMember,
  updateTenantMemberRoles,
  deleteTenantMember,
  type TenantMember,
  type TenantRole,
} from '#/api/userecho/tenant-rbac';

const loading = ref(false);
const members = ref<TenantMember[]>([]);
const roles = ref<TenantRole[]>([]);

const columns = [
  { title: 'ID', dataIndex: 'user_id', key: 'user_id', width: 80 },
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname' },
  { title: '类型', dataIndex: 'user_type', key: 'user_type', width: 100 },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80,
    customRender: ({ record }: { record: TenantMember }) => {
      const color = record.status === 'active' ? 'green' : 'red';
      const text = record.status === 'active' ? '正常' : '停用';
      return { color, children: text };
    },
  },
  { title: '反馈数', dataIndex: 'feedback_count', key: 'feedback_count', width: 80 },
  { title: '操作', key: 'action', width: 180 },
];

async function fetchData() {
  loading.value = true;
  try {
    const [membersRes, rolesRes] = await Promise.all([
      getTenantMembers(),
      getTenantRoles(),
    ]);
    members.value = membersRes;
    roles.value = rolesRes;
  } finally {
    loading.value = false;
  }
}

// 创建成员表单
const createForm = ref({
  username: '',
  nickname: '',
  password: '',
  email: '',
  role_ids: [] as string[],
});

const [CreateModal, createModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!createForm.value.username || !createForm.value.nickname || !createForm.value.password) {
      message.error('请填写必填项');
      return;
    }
    createModalApi.lock();
    try {
      await createTenantMember(createForm.value);
      message.success('创建成功');
      await createModalApi.close();
      await fetchData();
    } finally {
      createModalApi.unlock();
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      createForm.value = {
        username: '',
        nickname: '',
        password: '',
        email: '',
        role_ids: [],
      };
    }
  },
});

// 编辑角色
const editMemberId = ref('');
const editRoleIds = ref<string[]>([]);

const [EditRolesModal, editRolesModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    editRolesModalApi.lock();
    try {
      await updateTenantMemberRoles(editMemberId.value, editRoleIds.value);
      message.success('更新成功');
      await editRolesModalApi.close();
      await fetchData();
    } finally {
      editRolesModalApi.unlock();
    }
  },
});

function openEditRoles(member: TenantMember) {
  editMemberId.value = member.id;
  editRoleIds.value = [];
  editRolesModalApi.open();
}

// 删除成员
function handleDelete(member: TenantMember) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要移除成员 ${member.user_id} 吗？`,
    async onOk() {
      await deleteTenantMember(member.id);
      message.success('删除成功');
      await fetchData();
    },
  });
}

const roleOptions = computed(() =>
  roles.value.map(r => ({ label: r.name, value: r.id }))
);

onMounted(fetchData);
</script>

<template>
  <Page auto-content-height title="成员管理" description="管理租户成员和分配角色">
    <template #extra>
      <VbenButton @click="createModalApi.open()">
        <MaterialSymbolsAdd class="size-5 mr-1" />
        添加成员
      </VbenButton>
    </template>

    <Table
      :columns="columns"
      :data-source="members"
      :loading="loading"
      row-key="id"
      :pagination="{ pageSize: 20 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <Tag :color="record.status === 'active' ? 'green' : 'red'">
            {{ record.status === 'active' ? '正常' : '停用' }}
          </Tag>
        </template>
        <template v-if="column.key === 'action'">
          <Space>
            <VbenButton size="small" @click="openEditRoles(record)">
              <MaterialSymbolsEdit class="size-4" />
              角色
            </VbenButton>
            <VbenButton size="small" danger @click="handleDelete(record)">
              <MaterialSymbolsDelete class="size-4" />
            </VbenButton>
          </Space>
        </template>
      </template>
    </Table>

    <!-- 创建成员 Modal -->
    <CreateModal title="添加成员">
      <Form layout="vertical" class="p-4">
        <FormItem label="用户名" required>
          <Input v-model:value="createForm.username" placeholder="请输入用户名" />
        </FormItem>
        <FormItem label="昵称" required>
          <Input v-model:value="createForm.nickname" placeholder="请输入昵称" />
        </FormItem>
        <FormItem label="密码" required>
          <Input.Password v-model:value="createForm.password" placeholder="请输入初始密码" />
        </FormItem>
        <FormItem label="邮箱">
          <Input v-model:value="createForm.email" placeholder="请输入邮箱" />
        </FormItem>
        <FormItem label="角色">
          <Select
            v-model:value="createForm.role_ids"
            mode="multiple"
            :options="roleOptions"
            placeholder="请选择角色"
            style="width: 100%"
          />
        </FormItem>
      </Form>
    </CreateModal>

    <!-- 编辑角色 Modal -->
    <EditRolesModal title="分配角色">
      <div class="p-4">
        <Select
          v-model:value="editRoleIds"
          mode="multiple"
          :options="roleOptions"
          placeholder="请选择角色"
          style="width: 100%"
        />
      </div>
    </EditRolesModal>
  </Page>
</template>
