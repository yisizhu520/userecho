<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type {
  Customer,
  CreateCustomerParams,
  UpdateCustomerParams,
} from '#/api';

import { ref } from 'vue';

import { useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { z } from '#/adapter/form';
import {
  getCustomerList,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  CUSTOMER_TYPES,
} from '#/api';

/**
 * 表格配置
 */
const gridOptions: VxeTableGridOptions<Customer> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  height: 'auto',
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
      width: 120,
      sortable: true,
      slots: { default: 'business_value' },
    },
    {
      field: 'created_time',
      title: '创建时间',
      width: 168,
      sortable: true,
    },
    {
      field: 'updated_time',
      title: '更新时间',
      width: 168,
      sortable: true,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 120,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          'edit',
          {
            code: 'delete',
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
        return await getCustomerList({
          skip: (page.currentPage - 1) * page.pageSize,
          limit: page.pageSize,
        });
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

function onRefresh() {
  gridApi.query();
}

/**
 * 操作按钮点击事件
 */
function onActionClick({ code, row }: OnActionClickParams<Customer>) {
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

/**
 * 获取客户类型配置
 */
function getCustomerTypeConfig(type: string) {
  return CUSTOMER_TYPES.find((t) => t.value === type) || CUSTOMER_TYPES[0];
}
</script>

<template>
  <div>
    <Grid>
      <template #toolbar-actions>
        <VbenButton @click="() => addModalApi.open()">
          <MaterialSymbolsAdd class="size-5" />
          新建客户
        </VbenButton>
      </template>

      <!-- 客户类型 -->
      <template #customer_type="{ row }">
        <a-tag 
          :color="getCustomerTypeConfig(row.customer_type).business_value >= 5 ? 'gold' : 'blue'"
        >
          {{ getCustomerTypeConfig(row.customer_type).label }}
        </a-tag>
      </template>

      <!-- 商业价值 -->
      <template #business_value="{ row }">
        <a-rate 
          :value="row.business_value" 
          :count="10" 
          disabled 
          style="font-size: 14px"
        />
        <span class="ml-2">{{ row.business_value }}</span>
      </template>
    </Grid>

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
/* 自定义样式 */
</style>
