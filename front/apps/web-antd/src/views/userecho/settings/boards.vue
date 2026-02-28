<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDelete, MaterialSymbolsEdit, MaterialSymbolsDragIndicator } from '@vben/icons';
import { message, Modal, Space, Input, Form, FormItem } from 'ant-design-vue';
import Sortable from 'sortablejs';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getBoardList,
  createBoard,
  updateBoard,
  deleteBoard,
  reorderBoards,
  type Board,
  type BoardCreate,
  type BoardUpdate,
} from '#/api/userecho/board';

const searchQuery = ref('');
const isDragging = ref(false);

// 拖拽开始
function handleDragStart() {
  console.log('🚀 [BoardSort] Drag Start');
  isDragging.value = true;
}

// 拖拽排序处理
async function handleDragEnd(params: any) {
  console.log('🚀 [BoardSort] Drag End');
  isDragging.value = false;
  const $grid = params.$grid;
  try {
    // 延迟一丁点确保数据已同步
    await nextTick();
    const records = $grid.getTableData().fullData as Board[];
    console.log('📦 [BoardSort] New Order Records:', records.map((r: Board) => r.name));
    
    const reorderData = records.map((board, index) => ({
      id: board.id,
      sort_order: index,
    }));
    
    console.log('📡 [BoardSort] Sending to API:', reorderData);
    await reorderBoards(reorderData);
    message.success('排序已保存');
  } catch (error) {
    console.error('❌ [BoardSort] Save Error:', error);
    message.error('保存排序失败');
    $grid.commitProxy('query');
  }
}

// ==================== Grid 配置 ====================

const gridOptions: VxeTableGridOptions<Board> = {
  rowConfig: {
    keyField: 'id',
  },
  columns: [
    { type: 'seq', width: 60, title: '序号', align: 'center' },
    { width: 50, title: '', fixed: 'left', align: 'center', slots: { default: 'drag-handle' } },
    { field: 'name', title: '看板名称', minWidth: 150 },
    { field: 'url_name', title: 'URL Slug', width: 150 },
    { field: 'description', title: '描述', minWidth: 200 },
    { field: 'category', title: '分类', width: 120 },
    { field: 'feedback_count', title: '反馈数', width: 100 },
    { field: 'topic_count', title: '主题数', width: 100 },
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
          
          // 去重处理（防止后端返回重复数据）
          const idMap = new Map();
          const uniqueData = [];
          for (const board of data) {
            if (!idMap.has(board.id)) {
              idMap.set(board.id, true);
              uniqueData.push(board);
            }
          }
          
          // 显式排序：按 sort_order 升序，确保顺序正确
          uniqueData.sort((a, b) => {
            if (a.sort_order !== b.sort_order) {
              return a.sort_order - b.sort_order;
            }
            // sort_order 相同时，按创建时间降序
            return new Date(b.created_time).getTime() - new Date(a.created_time).getTime();
          });
          
          console.log('🔍 [Debug] Final sorted data:', uniqueData.map(b => ({ name: b.name, sort_order: b.sort_order })));
          
          return {
            items: uniqueData,
            total: uniqueData.length,
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

const [Grid, gridApi] = useVbenVxeGrid({});

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
  // 延迟初始化 Sortable，确保表格已渲染
  setTimeout(() => {
    const tableBody = document.querySelector('.vxe-table--body tbody');
    if (tableBody) {
      console.log('✅ [Sortable] Initializing Sortable on tbody');
      Sortable.create(tableBody as HTMLElement, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: async (evt: any) => {
          console.log('🚀 [Sortable] Drag End', evt);
          isDragging.value = false;
          
          const { newIndex, oldIndex } = evt;
          if (newIndex === oldIndex) return;

          try {
            // 1. 获取当前数据
            const gridInstance = gridApi.grid;
            const fullData = gridInstance.getTableData().fullData as Board[];
            
            // 2. 调整数据顺序
            const currRow = fullData.splice(oldIndex, 1)[0];
            fullData.splice(newIndex, 0, currRow);

            // 3. 更新表格数据（重要：让 VxeTable 感知到数据变化）
            await gridInstance.loadData(fullData);

            console.log('📦 [Sortable] New Order Records:', fullData.map((r: Board) => r.name));
            
            // 4. 构建排序请求数据
            const reorderData = fullData.map((board, index) => ({
              id: board.id,
              sort_order: index,
            }));
            
            console.log('📡 [Sortable] Sending to API:', reorderData);
            await reorderBoards(reorderData);
            message.success('排序已保存');
          } catch (error) {
            console.error('❌ [Sortable] Save Error:', error);
            message.error('保存排序失败');
            gridApi.query();
          }
        },
        onStart: () => {
          console.log('🚀 [Sortable] Drag Start');
          isDragging.value = true;
        },
      });
    } else {
      console.error('❌ [Sortable] Table tbody not found');
    }
  }, 500);
});
</script>

<template>
  <div class="board-list-container">
    <div class="board-content-wrapper">
      <div class="board-main-content p-2">
        <div class="board-grid-wrapper" :class="{ 'is-dragging': isDragging }">
          <Grid :grid-options="gridOptions">
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

            <template #drag-handle>
              <div class="drag-handle" style="cursor: move; padding: 8px; text-align: center;">
                <MaterialSymbolsDragIndicator class="size-5 text-gray-400 hover:text-primary" />
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
  transition: all 0.3s ease;
}

/* 拖拽时的视觉反馈 */
.board-grid-wrapper.is-dragging {
  background: hsl(var(--primary) / 0.02);
}


/* 增强行悬停效果 */
:deep(.vxe-table--render-default .vxe-body--row:hover) {
  background-color: hsl(var(--primary) / 0.05);
  transition: background-color 0.2s ease;
}

/* 拖拽中的行样式 */
:deep(.vxe-table--render-default .vxe-body--row.row--drag-moving) {
  background-color: hsl(var(--primary) / 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
  transition: all 0.2s ease;
  opacity: 0.9;
}

/* 拖拽目标位置提示线 */
:deep(.vxe-table--render-default .vxe-body--row.row--drag-insert) {
  border-top: 2px solid hsl(var(--primary));
}

/* 行号列样式 */
:deep(.vxe-table--render-default .vxe-body--column.col--seq) {
  color: hsl(var(--foreground) / 0.5);
  font-size: 0.875rem;
}

/* 动画：拖拽完成后的闪烁效果 */
@keyframes drag-complete {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: hsl(var(--success) / 0.2);
  }
}

:deep(.vxe-table--render-default .vxe-body--row.drag-just-dropped) {
  animation: drag-complete 0.5s ease;
}

</style>
