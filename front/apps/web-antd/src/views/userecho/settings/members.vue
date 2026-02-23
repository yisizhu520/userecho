<script setup lang="ts">
import { computed, ref } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsEdit } from '@vben/icons';
import { message, Modal, Tag, Space, Select, Input, Form, FormItem } from 'ant-design-vue';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getTenantMembers,
  getTenantRoles,
  createTenantMember,
  updateTenantMember,
  deleteTenantMember,
  getTenantMemberRoles,
  type TenantMember,
  type TenantRole,
} from '#/api/userecho/tenant-rbac';

const roles = ref<TenantRole[]>([]);
const searchQuery = ref('');

// ==================== Grid 配置 ====================

const gridOptions: VxeTableGridOptions<TenantMember> = {
  rowConfig: {
    keyField: 'id',
  },
  columns: [
    { field: 'user_id', title: 'ID', width: 80 },
    { field: 'email', title: '邮箱', minWidth: 200 },
    { field: 'username', title: '用户名', minWidth: 120 },
    { field: 'nickname', title: '昵称', minWidth: 120 },
    { field: 'user_type', title: '类型', width: 120 },
    { 
      field: 'status', 
      title: '状态', 
      width: 100,
      slots: { default: 'status' }
    },
    { field: 'feedback_count', title: '反馈数', width: 100 },
    { title: '操作', width: 180, fixed: 'right', slots: { default: 'action' } },
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
          // 独立获取数据，避免 Promise.all 导致一个失败全失败
          const membersPromise = getTenantMembers();
          const rolesPromise = getTenantRoles().catch((e) => {
             console.error('Failed to fetch roles:', e);
             return [];
          });

          const [membersRes, rolesRes] = await Promise.all([
            membersPromise, 
            rolesPromise
          ]);
          
          roles.value = rolesRes;
          
          let data = membersRes;
          
          // 前端搜索过滤 - 增加空值保护
          if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase();
            data = data.filter(item => 
              (item.username || '').toLowerCase().includes(q) ||
              (item.nickname || '').toLowerCase().includes(q) ||
              String(item.user_id || '').includes(q)
            );
          }
          
          return {
            items: data,
            total: data.length,
          };
        } catch (error) {
          console.error(error);
          message.error('获取成员列表失败');
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

// 创建成员表单
const createForm = ref({
  email: '',
  nickname: '',
  password: '',
  username: '',
  role_ids: [] as string[],
});

const [CreateModal, createModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!createForm.value.email || !createForm.value.nickname || !createForm.value.password) {
      message.error('请填写必填项');
      return;
    }
    if (!createForm.value.role_ids || createForm.value.role_ids.length === 0) {
      message.error('请至少选择一个角色');
      return;
    }
    createModalApi.lock();
    try {
      await createTenantMember(createForm.value);
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
        email: '',
        nickname: '',
        password: '',
        username: '',
        role_ids: [],
      };
    }
  },
});

// 编辑成员
const editForm = ref({
  id: '',
  username: '',
  nickname: '',
  role_ids: [] as string[],
  status: '',
});

const [EditModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!editForm.value.username || !editForm.value.nickname) {
      message.error('请填写必填项');
      return;
    }
    if (!editForm.value.role_ids || editForm.value.role_ids.length === 0) {
      message.error('请至少选择一个角色');
      return;
    }
    editModalApi.lock();
    try {
      await updateTenantMember(editForm.value.id, {
        username: editForm.value.username,
        nickname: editForm.value.nickname,
        role_ids: editForm.value.role_ids,
        status: editForm.value.status,
      });
      message.success('更新成功');
      await editModalApi.close();
      gridApi.query();
    } finally {
      editModalApi.unlock();
    }
  },
});

function openEdit(member: TenantMember) {
  editForm.value.id = member.id;
  editForm.value.username = member.username || '';
  editForm.value.nickname = member.nickname || '';
  editForm.value.status = member.status;
  // 获取该成员的角色
  getTenantMemberRoles(member.id).then((ids) => {
    editForm.value.role_ids = ids;
    editModalApi.open();
  });
}

// 删除成员
function handleDelete(member: TenantMember) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要移除成员 ${member.username || member.user_id} 吗？`,
    async onOk() {
      await deleteTenantMember(member.id);
      message.success('删除成功');
      gridApi.query();
    },
  });
}

const roleOptions = computed(() =>
  roles.value.map(r => ({ label: r.name, value: r.id }))
);

</script>

<template>
  <div class="member-list-container">
    <div class="member-content-wrapper">
      <div class="member-main-content p-2">
        <div class="member-grid-wrapper">
          <Grid>
            <template #toolbar-actions>
              <div class="flex items-center gap-2">
                <Input.Search
                  v-model:value="searchQuery"
                  placeholder="搜索用户名/昵称/ID"
                  style="width: 260px"
                  allow-clear
                  @search="handleSearch"
                />
                <VbenButton type="primary" @click="createModalApi.open()">
                  <MaterialSymbolsAdd class="size-5 mr-1" />
                  添加成员
                </VbenButton>
              </div>
            </template>

            <template #status="{ row }">
              <Tag :color="row.status === 'active' ? 'green' : 'red'">
                {{ row.status === 'active' ? '正常' : '停用' }}
              </Tag>
            </template>

            <template #action="{ row }">
              <Space>
                <VbenButton size="sm" @click="openEdit(row)">
                  <MaterialSymbolsEdit class="size-4" />
                  编辑
                </VbenButton>
                <VbenButton size="sm" danger @click="handleDelete(row)">
                  <MaterialSymbolsDelete class="size-4" />
                </VbenButton>
              </Space>
            </template>
          </Grid>
        </div>

        <!-- 创建成员 Modal -->
        <CreateModal title="添加成员">
          <Form layout="vertical" class="p-4">
            <FormItem label="邮箱" required>
              <Input v-model:value="createForm.email" placeholder="请输入邮箱" type="email" />
            </FormItem>
            <FormItem label="昵称" required>
              <Input v-model:value="createForm.nickname" placeholder="请输入昵称" />
            </FormItem>
            <FormItem label="密码" required>
              <Input.Password v-model:value="createForm.password" placeholder="请输入初始密码" />
            </FormItem>
            <FormItem label="角色" required>
              <Select
                v-model:value="createForm.role_ids"
                mode="multiple"
                :options="roleOptions"
                placeholder="请选择角色"
                style="width: 100%"
              />
            </FormItem>
            <FormItem label="用户名">
              <Input v-model:value="createForm.username" placeholder="可选，用于@提及" />
            </FormItem>
          </Form>
        </CreateModal>

        <!-- 编辑成员 Modal -->
        <EditModal title="编辑成员">
          <Form layout="vertical" class="p-4">
            <FormItem label="用户名" required>
              <Input v-model:value="editForm.username" placeholder="请输入用户名" />
            </FormItem>
            <FormItem label="昵称" required>
              <Input v-model:value="editForm.nickname" placeholder="请输入昵称" />
            </FormItem>
            <FormItem label="角色" required>
              <Select
                v-model:value="editForm.role_ids"
                mode="multiple"
                :options="roleOptions"
                placeholder="请选择角色"
                style="width: 100%"
              />
            </FormItem>
            <FormItem label="状态" required>
              <Select
                v-model:value="editForm.status"
                :options="[
                  { label: '正常', value: 'active' },
                  { label: '停用', value: 'inactive' },
                ]"
                placeholder="请选择状态"
                style="width: 100%"
              />
            </FormItem>
          </Form>
        </EditModal>
      </div>
    </div>
  </div>
</template>

<style scoped>
.member-list-container {
  height: calc(100vh - 64px);
  overflow: hidden;
  background: hsl(var(--background));
}

.member-content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background: hsl(var(--background));
}

.member-main-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
