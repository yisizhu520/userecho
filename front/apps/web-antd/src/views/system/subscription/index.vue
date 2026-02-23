<script lang="ts" setup>
import type { SubscriptionPlan, TenantSubscription, SubscriptionUpdateReq } from '#/api/sys-subscription';

import { onMounted, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { Tag, message, Descriptions } from 'ant-design-vue';

import { getAllPlans, getTenantSubscription, updateTenantSubscription } from '#/api/sys-subscription';
import { useVbenForm } from '#/adapter/form';

const loading = ref(false);
const plans = ref<SubscriptionPlan[]>([]);
const searchTenantId = ref('');
const currentSubscription = ref<TenantSubscription | null>(null);

async function fetchPlans() {
    plans.value = await getAllPlans();
}

async function handleSearch() {
    if (!searchTenantId.value) return;
    loading.value = true;
    try {
        currentSubscription.value = await getTenantSubscription(searchTenantId.value);
    } catch (e) {
        currentSubscription.value = null;
    } finally {
        loading.value = false;
    }
}

// --- Form & Modal Definition ---

const [Form, formApi] = useVbenForm({
    layout: 'vertical',
    schema: [
        {
            fieldName: 'plan_code',
            label: '套餐',
            component: 'Select',
            componentProps: {
                options: [], // Will be updated dynamically
            },
            rules: 'required',
        },
        {
            fieldName: 'status',
            label: '状态',
            component: 'Select',
            componentProps: {
                options: [
                    { label: 'Trial', value: 'trial' },
                    { label: 'Active', value: 'active' },
                    { label: 'Expired', value: 'expired' },
                    { label: 'Canceled', value: 'canceled' },
                ],
            },
            rules: 'required',
        },
        {
            fieldName: 'expires_at',
            label: '过期时间',
            component: 'DatePicker',
            componentProps: {
                showTime: true,
                valueFormat: 'YYYY-MM-DD HH:mm:ss',
            },
            rules: 'required',
        },
        {
            fieldName: 'notes',
            label: '备注',
            component: 'InputTextArea',
        }
    ],
});

const [Modal, modalApi] = useVbenModal({
    title: '编辑订阅',
    async onConfirm() {
        const { valid } = await formApi.validate();
        if (valid) {
            modalApi.lock();
            try {
                const values = await formApi.getValues();
                await updateTenantSubscription(searchTenantId.value, values as SubscriptionUpdateReq);
                message.success('更新成功');
                modalApi.close();
                handleSearch(); // Refresh
            } catch(e) {
                console.error(e);
            } finally {
                modalApi.unlock();
            }
        }
    },
    onOpenChange(isOpen) {
        if (isOpen) {
            // Update Plan Options
            formApi.updateSchema([
                {
                    fieldName: 'plan_code',
                    componentProps: {
                        options: plans.value.map(p => ({ label: `${p.name} (${p.code})`, value: p.code })),
                    },
                }
            ]);

            // Set Initial Values
            if (currentSubscription.value) {
                formApi.setValues({
                    plan_code: currentSubscription.value.plan?.code,
                    status: currentSubscription.value.status,
                    expires_at: currentSubscription.value.expires_at,
                    notes: '', // Notes typically aren't stored in the main sub object in a way we want to show back exactly here, or need to fetch details. keeping empty for now.
                });
            }
        }
    }
});

function openEditModal() {
    modalApi.open();
}

onMounted(() => {
    fetchPlans();
});
</script>

<template>
  <Page title="订阅管理">
    <div class="p-4 bg-white dark:bg-[#151515]">
        <div class="mb-4 flex gap-2 items-center">
            <span class="font-bold">查询租户:</span>
            <input 
                v-model="searchTenantId" 
                class="border p-2 rounded w-64 dark:bg-black dark:border-gray-700" 
                placeholder="输入 Tenant ID" 
                @keyup.enter="handleSearch"
            />
            <VbenButton type="primary" :loading="loading" @click="handleSearch">查询</VbenButton>
        </div>

        <div v-if="currentSubscription" class="bg-gray-50 dark:bg-black p-4 rounded border dark:border-gray-800">
            <div class="flex justify-between items-center mb-4">
                 <h3 class="text-lg font-bold">订阅详情</h3>
                 <VbenButton type="primary" @click="openEditModal">编辑订阅</VbenButton>
            </div>
           
            <Descriptions bordered size="small" :column="2">
                <Descriptions.Item label="套餐">{{ currentSubscription.plan?.name }} ({{ currentSubscription.plan?.code }})</Descriptions.Item>
                <Descriptions.Item label="状态">
                    <Tag :color="currentSubscription.status === 'active' ? 'green' : 'red'">
                        {{ currentSubscription.status }}
                    </Tag>
                </Descriptions.Item>
                 <Descriptions.Item label="生效时间">{{ currentSubscription.started_at }}</Descriptions.Item>
                 <Descriptions.Item label="过期时间">{{ currentSubscription.expires_at }}</Descriptions.Item>
                 <Descriptions.Item label="来源">{{ currentSubscription.source }}</Descriptions.Item>
                 <Descriptions.Item label="试用结束">{{ currentSubscription.trial_ends_at || '-' }}</Descriptions.Item>
            </Descriptions>
        </div>
        <div v-else-if="!loading && searchTenantId && !currentSubscription" class="text-gray-500 mt-4">
            未找到该租户的订阅信息
        </div>
    </div>
    <Modal>
        <Form />
    </Modal>
  </Page>
</template>
