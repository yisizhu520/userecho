<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { AutoComplete, Select } from 'ant-design-vue';
import { searchCustomers, CUSTOMER_TYPES, type Customer } from '#/api';
import { useDebounceFn } from '@vueuse/core';

interface Props {
  modelValue?: string;
  customerType?: string;
  placeholder?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string): void;
  (e: 'update:customerType', value: string): void;
  (e: 'customerSelected', customer: Customer | null): void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  customerType: 'normal',
  placeholder: '输入客户名称',
});

const emit = defineEmits<Emits>();

// 搜索状态
const searchValue = ref(props.modelValue);
const options = ref<{ value: string; label: string; customer?: Customer }[]>([]);
const loading = ref(false);
const isNewCustomer = ref(false);
const showTypeSelect = ref(false);
const selectedCustomerType = ref(props.customerType);

// 同步外部值
watch(() => props.modelValue, (val) => {
  searchValue.value = val;
});

// 搜索客户（防抖）
const doSearch = useDebounceFn(async (query: string) => {
  if (!query || query.length < 1) {
    options.value = [];
    isNewCustomer.value = false;
    return;
  }

  loading.value = true;
  try {
    const customers = await searchCustomers(query, 10);
    
    // 构建选项列表
    const customerOptions = customers.map((c) => ({
      value: c.name,
      label: `${c.name} (${CUSTOMER_TYPES.find((t) => t.value === c.customer_type)?.label || '普通客户'})`,
      customer: c,
    }));

    // 检查是否有精确匹配
    const exactMatch = customers.some((c) => c.name.toLowerCase() === query.toLowerCase());
    
    if (!exactMatch && query.trim()) {
      // 没有精确匹配，添加"新建"选项
      customerOptions.push({
        value: query,
        label: `✨ 新建客户「${query}」`,
        customer: undefined,
      });
    }

    options.value = customerOptions;
    isNewCustomer.value = !exactMatch && query.trim().length > 0;
  } catch {
    options.value = [];
  } finally {
    loading.value = false;
  }
}, 300);

// 输入变化时触发搜索
const onSearch = (value: string) => {
  searchValue.value = value;
  emit('update:modelValue', value);
  doSearch(value);
};

// 选择选项
const onSelect = (value: string, option: { customer?: Customer }) => {
  searchValue.value = value;
  emit('update:modelValue', value);
  
  if (option.customer) {
    // 选择了已有客户
    isNewCustomer.value = false;
    showTypeSelect.value = false;
    emit('customerSelected', option.customer);
    emit('update:customerType', option.customer.customer_type);
  } else {
    // 新建客户
    isNewCustomer.value = true;
    showTypeSelect.value = true;
    emit('customerSelected', null);
    emit('update:customerType', selectedCustomerType.value);
  }
};

// 客户类型变化
const onTypeChange = (type: string) => {
  selectedCustomerType.value = type;
  emit('update:customerType', type);
};

// 客户类型选项
const typeOptions = computed(() => CUSTOMER_TYPES.map((t) => ({
  value: t.value,
  label: t.label,
})));
</script>

<template>
  <div class="customer-autocomplete">
    <AutoComplete
      :value="searchValue"
      :options="options"
      :placeholder="placeholder"
      style="width: 100%"
      @search="onSearch"
      @select="onSelect"
    >
      <template #option="{ label }">
        <span>{{ label }}</span>
      </template>
    </AutoComplete>
    
    <!-- 新建客户时显示类型选择 -->
    <div v-if="showTypeSelect && isNewCustomer" class="customer-type-select">
      <span class="type-label">客户类型：</span>
      <Select
        :value="selectedCustomerType"
        :options="typeOptions"
        size="small"
        style="width: 120px"
        @change="onTypeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.customer-autocomplete {
  width: 100%;
}

.customer-type-select {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--ant-color-primary-bg);
  border-radius: 6px;
  font-size: 13px;
}

.type-label {
  color: var(--ant-color-text-secondary);
  white-space: nowrap;
}
</style>
