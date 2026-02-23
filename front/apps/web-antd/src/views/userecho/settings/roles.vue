<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsEdit } from '@vben/icons';
import { message, Modal, Tag, Space, Input, Form, FormItem, CheckboxGroup, Radio } from 'ant-design-vue';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getTenantRoles,
  getTenantPermissions,
  getTenantRolePermissions,
  createTenantRole,
  updateTenantRole,
  updateTenantRolePermissions,
  deleteTenantRole,
  type TenantRole,
  type TenantPermission,
} from '#/api/userecho/tenant-rbac';

const permissions = ref<TenantPermission[]>([]);
const searchQuery = ref('');

// ==================== Grid 配置 ====================

const gridOptions: VxeTableGridOptions<TenantRole> = {
  rowConfig: {
    keyField: 'id',
  },
  columns: [
    { field: 'name', title: '角色名称', minWidth: 150 },
    { field: 'code', title: '角色代码', width: 150 },
    { field: 'description', title: '描述', minWidth: 200 },
    { 
      field: 'is_builtin', 
      title: '类型', 
      width: 100,
      slots: { default: 'is_builtin' }
    },
    { 
      field: 'status', 
      title: '状态', 
      width: 100,
      slots: { default: 'status' }
    },
    { title: '操作', width: 200, fixed: 'right', slots: { default: 'action' } },
  ],
  toolbarConfig: {
    custom: true,
    refresh: true,
    zoom: true,
  },
  height: '100%',
  proxyConfig: {
    ajax: {
      query: async () => {
        try {
          // 获取角色和权限（权限仅初始加载一次或按需加载，这里随角色列表一起触发以简化）
          const [rolesRes, permsRes] = await Promise.all([
            getTenantRoles(),
            permissions.value.length === 0 ? getTenantPermissions() : Promise.resolve(permissions.value),
          ]);
          
          permissions.value = permsRes;
          let data = rolesRes;
          
          // 前端搜索过滤
          if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase();
            data = data.filter(item => 
              (item.name || '').toLowerCase().includes(q) ||
              (item.code || '').toLowerCase().includes(q)
            );
          }
          
          return {
            items: data,
            total: data.length,
          };
        } catch (error) {
          console.error(error);
          message.error('获取角色列表失败');
          return {
            items: [],
            total: 0,
          };
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

function handleSearch() {
  gridApi.query();
}

// ==================== 模态框逻辑 ====================

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
      gridApi.query();
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

// 编辑角色
const editForm = ref({
  id: '',
  name: '',
  code: '',
  description: '',
  status: 'active',
  permission_ids: [] as string[],
});

const [EditRoleModal, editRoleModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!editForm.value.name) {
      message.error('请填写角色名称');
      return;
    }
    editRoleModalApi.lock();
    try {
      // 1. 更新角色基本信息
      await updateTenantRole(editForm.value.id, {
        name: editForm.value.name,
        description: editForm.value.description,
        status: editForm.value.status,
      });
      
      // 2. 更新角色权限
      await updateTenantRolePermissions(editForm.value.id, editForm.value.permission_ids);
      
      message.success('更新成功');
      await editRoleModalApi.close();
      gridApi.query();
    } finally {
      editRoleModalApi.unlock();
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      // Reset form when opening
    } else {
      // Clean up when closing
      editForm.value = {
        id: '',
        name: '',
        code: '',
        description: '',
        status: 'active',
        permission_ids: [],
      };
    }
  },
});

async function openEditRole(role: TenantRole) {
  editForm.value.id = role.id;
  editForm.value.name = role.name;
  editForm.value.code = role.code;
  editForm.value.description = role.description || '';
  editForm.value.status = role.status;
  editForm.value.permission_ids = [];
  
  try {
    const perms = await getTenantRolePermissions(role.id);
    editForm.value.permission_ids = perms.map(p => p.id);
  } catch {
    // ignore
  }
  
  editRoleModalApi.open();
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
      gridApi.query();
    },
  });
}

const permissionOptions = computed(() =>
  permissions.value.map(p => ({ label: p.name, value: p.id }))
);

onMounted(() => {
  // 首次加载由 VxeGrid 代理处理，无需手动 call
});
</script>

<template>
  <div class="role-list-container">
    <div class="role-content-wrapper">
      <div class="role-main-content p-2">
        <div class="role-grid-wrapper">
          <Grid>
            <template #toolbar-actions>
              <div class="flex items-center gap-2">
                <Input.Search
                  v-model:value="searchQuery"
                  placeholder="搜索角色名称/代码"
                  style="width: 260px"
                  allow-clear
                  @search="handleSearch"
                />
                <VbenButton type="primary" @click="createModalApi.open()">
                  <MaterialSymbolsAdd class="size-5 mr-1" />
                  新建角色
                </VbenButton>
              </div>
            </template>

            <template #is_builtin="{ row }">
              <Tag :color="row.is_builtin ? 'blue' : 'default'">
                {{ row.is_builtin ? '内置' : '自定义' }}
              </Tag>
            </template>

            <template #status="{ row }">
              <Tag :color="row.status === 'active' ? 'green' : 'red'">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </Tag>
            </template>

            <template #action="{ row }">
              <Space>
                <VbenButton size="sm" @click="openEditRole(row)">
                  <MaterialSymbolsEdit class="size-4" />
                  编辑
                </VbenButton>
                <VbenButton
                  v-if="!row.is_builtin"
                  size="sm"
                  danger
                  @click="handleDelete(row)"
                >
                  <MaterialSymbolsDelete class="size-4" />
                </VbenButton>
              </Space>
            </template>
          </Grid>
        </div>

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
              <div class="max-h-[300px] overflow-y-auto border rounded p-2 bg-gray-50/50">
                <CheckboxGroup
                  v-model:value="createForm.permission_ids"
                  :options="permissionOptions"
                  class="flex flex-col gap-2"
                />
              </div>
            </FormItem>
          </Form>
        </CreateModal>

        <!-- 编辑角色 Modal -->
        <EditRoleModal :title="`编辑角色 - ${editForm.name}`">
          <Form layout="vertical" class="p-4">
            <FormItem label="角色名称" required>
              <Input v-model:value="editForm.name" placeholder="如：产品助理" />
            </FormItem>
            
            <FormItem label="角色代码">
              <Input v-model:value="editForm.code" disabled />
              <div class="text-xs text-gray-500 mt-1">
                角色代码不可修改
              </div>
            </FormItem>
            
            <FormItem label="描述">
              <Input.TextArea 
                v-model:value="editForm.description" 
                placeholder="角色描述"
                :rows="3"
              />
            </FormItem>
            
            <FormItem label="状态" required>
              <Radio.Group v-model:value="editForm.status">
                <Radio value="active">启用</Radio>
                <Radio value="disabled">停用</Radio>
              </Radio.Group>
            </FormItem>
            
            <FormItem label="权限">
              <div class="max-h-[300px] overflow-y-auto border rounded p-2 bg-gray-50/50">
                <CheckboxGroup
                  v-model:value="editForm.permission_ids"
                  :options="permissionOptions"
                  class="flex flex-col gap-2"
                />
              </div>
            </FormItem>
          </Form>
        </EditRoleModal>
      </div>
    </div>
  </div>
</template>

<style scoped>
.role-list-container {
  height: calc(100vh - 64px);
  overflow: hidden;
  background: hsl(var(--background));
}

.role-content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background: hsl(var(--background));
}

.role-main-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.role-grid-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
</style>
