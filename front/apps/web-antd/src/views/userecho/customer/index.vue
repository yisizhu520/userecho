<script setup lang="ts">
import type {
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Customer,
  CreateCustomerParams,
  UpdateCustomerParams,
} from '#/api';

import { ref, computed } from 'vue';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message, Input, Select, Space, Tooltip, Drawer, Descriptions } from 'ant-design-vue';
import { SearchOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { z } from '#/adapter/form';
import {
  getCustomerList,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  CUSTOMER_TYPES,
  BUSINESS_VALUE_LEVELS,
} from '#/api';

// 配置 dayjs 相对时间
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

// 搜索筛选状态
const searchValue = ref('');
const filterType = ref<string | undefined>(undefined);

// 客户详情抽屉
const detailDrawerVisible = ref(false);
const selectedCustomer = ref<Customer | null>(null);

/**
 * 获取客户类型配置
 */
function getCustomerTypeConfig(type: string) {
  return CUSTOMER_TYPES.find((t) => t.value === type) || CUSTOMER_TYPES[0]!;
}

/**
 * 获取商业价值等级配置
 */
function getBusinessValueLevel(value: number) {
  return BUSINESS_VALUE_LEVELS.find(
    (level) => value >= level.min && value <= level.max
  ) || BUSINESS_VALUE_LEVELS[0]!;
}

/**
 * 格式化相对时间
 */
function formatRelativeTime(time: string | null | undefined) {
  if (!time) return '-';
  return dayjs(time).fromNow();
}

/**
 * 表格配置
 */
const gridOptions: VxeTableGridOptions<Customer> = {
  rowConfig: {
    keyField: 'id',
  },
  height: '100%',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: true,
    refreshOptions: {
      code: 'query',
    },
    custom: true,
    zoom: true,
  },
  columns: [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      fixed: 'left',
      width: 50,
    },
    {
      field: 'name',
      title: '客户名称',
      minWidth: 200,
      fixed: 'left',
      slots: { default: 'name' },
    },
    {
      field: 'customer_type',
      title: '客户类型',
      width: 120,
      slots: { default: 'customer_type' },
    },
    {
      field: 'business_value',
      title: '商业价值',
      width: 100,
      sortable: true,
      slots: { default: 'business_value' },
    },
    {
      field: 'created_time',
      title: '创建时间',
      width: 120,
      sortable: true,
      slots: { default: 'created_time' },
    },
    {
      field: 'updated_time',
      title: '更新时间',
      width: 120,
      sortable: true,
      slots: { default: 'updated_time' },
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 100,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'edit',
            icon: 'lucide:edit',
            text: '',
          },
          {
            code: 'delete',
            icon: 'lucide:trash-2',
            text: '',
            popconfirm: {
              title: '确认删除此客户？删除后关联的反馈将变为匿名',
            },
          },
        ],
      },
    },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        const data = await getCustomerList({
          skip: (page.currentPage - 1) * page.pageSize,
          limit: page.pageSize,
          search: searchValue.value || undefined,
          customer_type: filterType.value || undefined,
        });
        return {
          items: data.items,
          total: data.total,
        };
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

function onRefresh() {
  gridApi.query();
}

/**
 * 搜索和筛选处理
 */
function onSearch() {
  gridApi.query();
}

function onReset() {
  searchValue.value = '';
  filterType.value = undefined;
  gridApi.query();
}

/**
 * 显示客户详情
 */
function showCustomerDetail(customer: Customer) {
  selectedCustomer.value = customer;
  detailDrawerVisible.value = true;
}

/**
 * 操作按钮点击事件
 */
function onActionClick({ code, row }: { code: string; row: Customer }) {
  switch (code) {
    case 'edit': {
      editCustomerId.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
    case 'delete': {
      deleteCustomer(row.id).then(() => {
        message.success('删除成功');
        onRefresh();
      }).catch(() => {
        message.error('删除失败');
      });
      break;
    }
  }
}

/**
 * 表单 Schema
 */
const customerFormSchema = [
  {
    component: 'Input',
    fieldName: 'name',
    label: '客户名称',
    rules: z.string().min(1, '请输入客户名称').max(100, '名称长度不能超过100字'),
    componentProps: {
      placeholder: '输入客户名称',
      maxlength: 100,
    },
  },
  {
    component: 'Select',
    fieldName: 'customer_type',
    label: '客户类型',
    rules: 'selectRequired',
    componentProps: {
      options: CUSTOMER_TYPES,
      placeholder: '选择客户类型',
      onChange: (value: string) => {
        const type = CUSTOMER_TYPES.find((t) => t.value === value);
        if (type && (addFormApi || editFormApi)) {
          const formApi = addFormApi || editFormApi;
          formApi.setValues({ business_value: type.business_value });
        }
      },
    },
    defaultValue: 'normal',
  },
  {
    component: 'InputNumber',
    fieldName: 'business_value',
    label: '商业价值',
    helpMessage: '1=普通, 3=付费, 5=大客户, 10=战略客户',
    componentProps: {
      min: 1,
      max: 10,
      placeholder: '自动根据客户类型填充',
    },
    defaultValue: 1,
  },
];

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: customerFormSchema,
});

const editCustomerId = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  title: '编辑客户',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await editFormApi.getValues<UpdateCustomerParams>();
      try {
        await updateCustomer(editCustomerId.value, data);
        message.success('更新成功');
        await editModalApi.close();
        onRefresh();
      } catch {
        message.error('更新失败');
      } finally {
        editModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<any>();
      editFormApi.resetForm();
      if (data) {
        editFormApi.setValues(data);
      }
    }
  },
});

/**
 * 新建表单
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: customerFormSchema,
});

const [addModal, addModalApi] = useVbenModal({
  title: '新建客户',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateCustomerParams>();
      try {
        await createCustomer(data);
        message.success('创建成功');
        await addModalApi.close();
        onRefresh();
      } catch {
        message.error('创建失败');
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      addFormApi.resetForm();
    }
  },
});

// 客户类型选项（用于筛选下拉框）
const typeOptions = computed(() => [
  { value: '', label: '全部类型' },
  ...CUSTOMER_TYPES.map((t) => ({ value: t.value, label: t.label })),
]);
</script>

<template>
  <div class="customer-page">
    <Grid>
      <template #toolbar-actions>
        <Space :size="12">
          <VbenButton @click="() => addModalApi.open()">
            <MaterialSymbolsAdd class="size-5" />
            新建客户
          </VbenButton>
          
          <!-- 搜索筛选区域 -->
          <Input
            v-model:value="searchValue"
            placeholder="搜索客户名称"
            style="width: 200px"
            allow-clear
            @press-enter="onSearch"
          >
            <template #prefix>
              <SearchOutlined class="text-gray-400" />
            </template>
          </Input>
          
          <Select
            v-model:value="filterType"
            :options="typeOptions"
            placeholder="客户类型"
            style="width: 140px"
            allow-clear
            @change="onSearch"
          />
          
          <VbenButton variant="outline" @click="onReset">
            重置
          </VbenButton>
        </Space>
      </template>

      <!-- 客户名称（可点击查看详情） -->
      <template #name="{ row }">
        <a 
          class="customer-name-link"
          @click="showCustomerDetail(row)"
        >
          {{ row.name }}
        </a>
      </template>

      <!-- 客户类型 -->
      <template #customer_type="{ row }">
        <a-tag 
          :color="getCustomerTypeConfig(row.customer_type).color"
          :style="{ borderColor: getCustomerTypeConfig(row.customer_type).color }"
        >
          {{ getCustomerTypeConfig(row.customer_type).label }}
        </a-tag>
      </template>

      <!-- 商业价值（语义标签） -->
      <template #business_value="{ row }">
        <Tooltip :title="`商业价值分: ${row.business_value}/10`">
          <span 
            class="business-value-tag"
            :style="{
              color: getBusinessValueLevel(row.business_value).color,
              backgroundColor: getBusinessValueLevel(row.business_value).bgColor,
            }"
          >
            {{ getBusinessValueLevel(row.business_value).label }}
          </span>
        </Tooltip>
      </template>

      <!-- 创建时间（相对时间） -->
      <template #created_time="{ row }">
        <Tooltip :title="row.created_time">
          <span class="text-gray-500">{{ formatRelativeTime(row.created_time) }}</span>
        </Tooltip>
      </template>

      <!-- 更新时间（相对时间） -->
      <template #updated_time="{ row }">
        <Tooltip :title="row.updated_time">
          <span class="text-gray-500">{{ formatRelativeTime(row.updated_time) }}</span>
        </Tooltip>
      </template>


    </Grid>

    <!-- 客户详情抽屉 -->
    <Drawer
      v-model:open="detailDrawerVisible"
      title="客户详情"
      :width="400"
    >
      <template v-if="selectedCustomer">
        <Descriptions :column="1" bordered size="small">
          <a-descriptions-item label="客户名称">
            {{ selectedCustomer.name }}
          </a-descriptions-item>
          <a-descriptions-item label="客户类型">
            <a-tag :color="getCustomerTypeConfig(selectedCustomer.customer_type).color">
              {{ getCustomerTypeConfig(selectedCustomer.customer_type).label }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="商业价值">
            <span 
              class="business-value-tag"
              :style="{
                color: getBusinessValueLevel(selectedCustomer.business_value).color,
                backgroundColor: getBusinessValueLevel(selectedCustomer.business_value).bgColor,
              }"
            >
              {{ getBusinessValueLevel(selectedCustomer.business_value).label }}
            </span>
            <span class="ml-2 text-gray-400">({{ selectedCustomer.business_value }}/10)</span>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ selectedCustomer.created_time || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="更新时间">
            {{ selectedCustomer.updated_time || '-' }}
          </a-descriptions-item>
        </Descriptions>
      </template>
    </Drawer>

    <!-- 编辑弹窗 -->
    <editModal>
      <EditForm />
    </editModal>

    <!-- 新建弹窗 -->
    <addModal>
      <AddForm />
    </addModal>
  </div>
</template>

<style scoped>
.customer-page {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px;
  background: hsl(var(--background));
}

.customer-name-link {
  color: var(--ant-color-primary);
  cursor: pointer;
  transition: color 0.2s;
}

.customer-name-link:hover {
  color: var(--ant-color-primary-hover);
  text-decoration: underline;
}

.business-value-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-gray-500 {
  color: #6b7280;
}

.text-blue-500 {
  color: #3b82f6;
}

.text-red-500 {
  color: #ef4444;
}

.ml-2 {
  margin-left: 8px;
}
</style>
