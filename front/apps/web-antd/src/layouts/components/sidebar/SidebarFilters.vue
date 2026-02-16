<script lang="ts" setup>
import { Checkbox, Select } from 'ant-design-vue';
</script>

<template>
  <div class="px-4 py-2">
    <!-- Status Filter -->
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold text-gray-500 uppercase">Status</span>
        <span class="text-xs text-gray-400 cursor-pointer hover:text-primary">Reset</span>
      </div>
      <div class="flex flex-col gap-2">
        <Checkbox class="!ml-0">Open</Checkbox>
        <Checkbox class="!ml-0">Under Review</Checkbox>
        <Checkbox class="!ml-0">Planned</Checkbox>
        <Checkbox class="!ml-0">In Progress</Checkbox>
        <Checkbox class="!ml-0">Completed</Checkbox>
        <Checkbox class="!ml-0">Closed</Checkbox>
      </div>
    </div>

    <!-- Date Range -->
    <div class="mb-6">
      <div class="mb-2">
        <span class="text-xs font-semibold text-gray-500 uppercase">Date Range</span>
      </div>
        <Select
          class="w-full"
          default-value="all"
          size="small"
        >
          <Select.Option value="all">All time</Select.Option>
          <Select.Option value="30days">Last 30 days</Select.Option>
          <Select.Option value="7days">Last 7 days</Select.Option>
        </Select>
    </div>
  </div>
</template>
