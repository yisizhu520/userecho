<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsShield } from '@vben/icons';
import { message, Modal, Table, Tag, Space, Input, Form, FormItem, CheckboxGroup } from 'ant-design-vue';

import {
  getTenantRoles,
  getTenantPermissions,
  getTenantRolePermissions,
  createTenantRole,
  updateTenantRolePermissions,
  deleteTenantRole,
  type TenantRole,
  type TenantPermission,
} from '#/api/userecho/tenant-rbac';

const loading = ref(false);
const roles = ref<TenantRole[]>([]);
const permissions = ref<TenantPermission[]>([]);

const columns = [
  { title: '角色名称', dataIndex: 'name', key: 'name' },
  { title: '角色代码', dataIndex: 'code', key: 'code' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  {
    title: '类型',
    dataIndex: 'is_builtin',
    key: 'is_builtin',
    width: 80,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80,
  },
  { title: '操作', key: 'action', width: 200 },
];

async function fetchData() {
  loading.value = true;
  try {
    const [rolesRes, permsRes] = await Promise.all([
      getTenantRoles(),
      getTenantPermissions(),
    ]);
    roles.value = rolesRes;
    permissions.value = permsRes;
  } finally {
    loading.value = false;
  }
}

// 创建角色表单
const createForm = ref({
  name: '',
  code: '',
  description: '',
  permission_ids: [] as string[],
});

const [CreateModal, createModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!createForm.value.name || !createForm.value.code) {
      message.error('请填写角色名称和代码');
      return;
    }
    createModalApi.lock();
    try {
      await createTenantRole(createForm.value);
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
        name: '',
        code: '',
        description: '',
        permission_ids: [],
      };
    }
  },
});

// 编辑权限
const editRoleId = ref('');
const editRoleName = ref('');
const editPermissionIds = ref<string[]>([]);

const [EditPermsModal, editPermsModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    editPermsModalApi.lock();
    try {
      await updateTenantRolePermissions(editRoleId.value, editPermissionIds.value);
      message.success('权限更新成功');
      await editPermsModalApi.close();
    } finally {
      editPermsModalApi.unlock();
    }
  },
});

async function openEditPerms(role: TenantRole) {
  editRoleId.value = role.id;
  editRoleName.value = role.name;
  editPermissionIds.value = [];
  
  try {
    const perms = await getTenantRolePermissions(role.id);
    editPermissionIds.value = perms.map(p => p.id);
  } catch {
    // ignore
  }
  editPermsModalApi.open();
}

// 删除角色
function handleDelete(role: TenantRole) {
  if (role.is_builtin) {
    message.warning('内置角色不可删除');
    return;
  }
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除角色 "${role.name}" 吗？`,
    async onOk() {
      await deleteTenantRole(role.id);
      message.success('删除成功');
      await fetchData();
    },
  });
}

const permissionOptions = computed(() =>
  permissions.value.map(p => ({ label: p.name, value: p.id }))
);

function asTenantRole(record: any): TenantRole {
  return record as TenantRole;
}

onMounted(fetchData);
</script>

<template>
  <Page auto-content-height title="角色管理" description="管理租户角色和权限配置">
    <template #extra>
      <VbenButton @click="createModalApi.open()">
        <MaterialSymbolsAdd class="size-5 mr-1" />
        新建角色
      </VbenButton>
    </template>

    <Table
      :columns="columns"
      :data-source="roles"
      :loading="loading"
      row-key="id"
      :pagination="{ pageSize: 20 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_builtin'">
          <Tag :color="record.is_builtin ? 'blue' : 'default'">
            {{ record.is_builtin ? '内置' : '自定义' }}
          </Tag>
        </template>
        <template v-if="column.key === 'status'">
          <Tag :color="record.status === 'active' ? 'green' : 'red'">
            {{ record.status === 'active' ? '启用' : '停用' }}
          </Tag>
        </template>
        <template v-if="column.key === 'action'">
          <Space>
            <VbenButton size="sm" @click="openEditPerms(asTenantRole(record))">
              <MaterialSymbolsShield class="size-4" />
              权限
            </VbenButton>
            <VbenButton
              v-if="!record.is_builtin"
              size="sm"
              danger
              @click="handleDelete(asTenantRole(record))"
            >
              <MaterialSymbolsDelete class="size-4" />
            </VbenButton>
          </Space>
        </template>
      </template>
    </Table>

    <!-- 创建角色 Modal -->
    <CreateModal title="新建角色">
      <Form layout="vertical" class="p-4">
        <FormItem label="角色名称" required>
          <Input v-model:value="createForm.name" placeholder="如：产品助理" />
        </FormItem>
        <FormItem label="角色代码" required>
          <Input v-model:value="createForm.code" placeholder="如：product_assistant" />
        </FormItem>
        <FormItem label="描述">
          <Input.TextArea v-model:value="createForm.description" placeholder="角色描述" />
        </FormItem>
        <FormItem label="权限">
          <CheckboxGroup
            v-model:value="createForm.permission_ids"
            :options="permissionOptions"
          />
        </FormItem>
      </Form>
    </CreateModal>

    <!-- 编辑权限 Modal -->
    <EditPermsModal :title="`配置权限 - ${editRoleName}`">
      <div class="p-4">
        <CheckboxGroup
          v-model:value="editPermissionIds"
          :options="permissionOptions"
          class="flex flex-col gap-2"
        />
      </div>
    </EditPermsModal>
  </Page>
</template>
