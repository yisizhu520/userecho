<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsEdit } from '@vben/icons';
import { message, Modal, Space, Input, Form, FormItem } from 'ant-design-vue';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getBoardList,
  createBoard,
  updateBoard,
  deleteBoard,
  type Board,
  type BoardCreate,
  type BoardUpdate,
} from '#/api/userecho/board';

const searchQuery = ref('');

// ==================== Grid 配置 ====================

const gridOptions: VxeTableGridOptions<Board> = {
  rowConfig: {
    keyField: 'id',
  },
  columns: [
    { field: 'name', title: '看板名称', minWidth: 150 },
    { field: 'url_name', title: 'URL Slug', width: 150 },
    { field: 'description', title: '描述', minWidth: 200 },
    { field: 'category', title: '分类', width: 120 },
    { field: 'feedback_count', title: '反馈数', width: 100 },
    { field: 'topic_count', title: '主题数', width: 100 },
    { field: 'sort_order', title: '排序', width: 80 },
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
          let data = await getBoardList();
          
          // 前端搜索过滤
          if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase();
            data = data.filter(item => 
              (item.name || '').toLowerCase().includes(q) ||
              (item.url_name || '').toLowerCase().includes(q) ||
              (item.category || '').toLowerCase().includes(q)
            );
          }
          
          return {
            items: data,
            total: data.length,
          };
        } catch (error) {
          console.error(error);
          message.error('获取看板列表失败');
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

// 创建看板表单
const createForm = ref<BoardCreate>({
  name: '',
  url_name: '',
  description: '',
  category: '',
  sort_order: 0,
});

const [CreateModal, createModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!createForm.value.name || !createForm.value.url_name) {
      message.error('请填写看板名称和 URL Slug');
      return;
    }
    createModalApi.lock();
    try {
      await createBoard(createForm.value);
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
        url_name: '',
        description: '',
        category: '',
        sort_order: 0,
      };
    }
  },
});

// 编辑看板
const editForm = ref<Board & BoardUpdate>({
  id: '',
  tenant_id: '',
  name: '',
  url_name: '',
  description: '',
  category: '',
  feedback_count: 0,
  topic_count: 0,
  sort_order: 0,
  is_archived: false,
  created_time: '',
});

const [EditBoardModal, editBoardModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    if (!editForm.value.name) {
      message.error('请填写看板名称');
      return;
    }
    editBoardModalApi.lock();
    try {
      await updateBoard(editForm.value.id, {
        name: editForm.value.name,
        description: editForm.value.description,
        category: editForm.value.category,
        sort_order: editForm.value.sort_order,
        is_archived: editForm.value.is_archived,
      });
      
      message.success('更新成功');
      await editBoardModalApi.close();
      gridApi.query();
    } finally {
      editBoardModalApi.unlock();
    }
  },
  onOpenChange(isOpen) {
    if (!isOpen) {
      // Clean up when closing
      editForm.value = {
        id: '',
        tenant_id: '',
        name: '',
        url_name: '',
        description: '',
        category: '',
        feedback_count: 0,
        topic_count: 0,
        sort_order: 0,
        is_archived: false,
        created_time: '',
      };
    }
  },
});

async function openEditBoard(board: Board) {
  editForm.value = { ...board };
  editBoardModalApi.open();
}

// 删除看板
function handleDelete(board: Board) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除看板 "${board.name}" 吗？此操作为软删除，不会丢失数据。`,
    async onOk() {
      await deleteBoard(board.id);
      message.success('删除成功');
      gridApi.query();
    },
  });
}

onMounted(() => {
  // 首次加载由 VxeGrid 代理处理，无需手动 call
});
</script>

<template>
  <div class="board-list-container">
    <div class="board-content-wrapper">
      <div class="board-main-content p-2">
        <div class="board-grid-wrapper">
          <Grid>
            <template #toolbar-actions>
              <div class="flex items-center gap-2">
                <Input.Search
                  v-model:value="searchQuery"
                  placeholder="搜索看板名称/URL/分类"
                  style="width: 280px"
                  allow-clear
                  @search="handleSearch"
                />
                <VbenButton type="primary" @click="createModalApi.open()">
                  <MaterialSymbolsAdd class="size-5 mr-1" />
                  新建看板
                </VbenButton>
              </div>
            </template>

            <template #action="{ row }">
              <Space>
                <VbenButton size="sm" @click="openEditBoard(row)">
                  <MaterialSymbolsEdit class="size-4" />
                  编辑
                </VbenButton>
                <VbenButton
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

        <!-- 创建看板 Modal -->
        <CreateModal title="新建看板">
          <Form layout="vertical" class="p-4">
            <FormItem label="看板名称" required>
              <Input v-model:value="createForm.name" placeholder="如：移动端反馈" />
            </FormItem>
            <FormItem label="URL Slug" required>
              <Input v-model:value="createForm.url_name" placeholder="如：mobile-feedback" />
              <div class="text-xs text-gray-500 mt-1">
                用于 URL 路径，仅支持英文、数字、连字符
              </div>
            </FormItem>
            <FormItem label="描述">
              <Input.TextArea v-model:value="createForm.description" placeholder="看板描述" :rows="3" />
            </FormItem>
            <FormItem label="分类">
              <Input v-model:value="createForm.category" placeholder="如：mobile, web, api" />
            </FormItem>
            <FormItem label="排序">
              <Input v-model:value="createForm.sort_order" type="number" placeholder="数字越小越靠前" />
            </FormItem>
          </Form>
        </CreateModal>

        <!-- 编辑看板 Modal -->
        <EditBoardModal :title="`编辑看板 - ${editForm.name}`">
          <Form layout="vertical" class="p-4">
            <FormItem label="看板名称" required>
              <Input v-model:value="editForm.name" placeholder="如：移动端反馈" />
            </FormItem>
            
            <FormItem label="URL Slug">
              <Input v-model:value="editForm.url_name" disabled />
              <div class="text-xs text-gray-500 mt-1">
                URL Slug 不可修改
              </div>
            </FormItem>
            
            <FormItem label="描述">
              <Input.TextArea 
                v-model:value="editForm.description" 
                placeholder="看板描述"
                :rows="3"
              />
            </FormItem>
            
            <FormItem label="分类">
              <Input v-model:value="editForm.category" placeholder="如：mobile, web, api" />
            </FormItem>
            
            <FormItem label="排序">
              <Input v-model:value="editForm.sort_order" type="number" placeholder="数字越小越靠前" />
            </FormItem>
          </Form>
        </EditBoardModal>
      </div>
    </div>
  </div>
</template>

<style scoped>
.board-list-container {
  height: calc(100vh - 64px);
  overflow: hidden;
  background: hsl(var(--background));
}

.board-content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background: hsl(var(--background));
}

.board-main-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.board-grid-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
</style>
