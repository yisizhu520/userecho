<script lang="ts" setup>
import type { TenantSubscription } from '#/api/userecho/subscription';

import { onMounted, ref, computed } from 'vue';

import { Page } from '@vben/common-ui';
import { Card, Tag, Progress, Statistic, Row, Col, Divider, Button } from 'ant-design-vue';

import { getCurrentSubscription } from '#/api/userecho/subscription';
import { getCreditsBalance } from '#/api/userecho/credits';

const loading = ref(false);
const subscription = ref<TenantSubscription | null>(null);
const creditsInfo = ref<any>(null);

async function fetchData() {
    loading.value = true;
    try {
        const [subData, creditData] = await Promise.all([
            getCurrentSubscription(),
            getCreditsBalance()
        ]);
        subscription.value = subData;
        creditsInfo.value = creditData;
    } finally {
        loading.value = false;
    }
}

const statusColor = computed(() => {
    switch(subscription.value?.status) {
        case 'active': return 'success';
        case 'trial': return 'processing';
        case 'expired': return 'error';
        case 'canceled': return 'default';
        default: return 'default';
    }
});

const statusText = computed(() => {
    switch(subscription.value?.status) {
        case 'active': return '正式生效中';
        case 'trial': return '试用期';
        case 'expired': return '已过期';
        case 'canceled': return '已取消';
        default: return '未知';
    }
});

onMounted(() => {
    fetchData();
});
</script>

<template>
  <Page title="我的订阅">
    <div class="p-4 space-y-4">
        <!-- 订阅状态卡片 -->
        <Card :loading="loading" title="当前套餐">
            <template #extra>
                 <Tag :color="statusColor" class="text-base px-3 py-1">{{ statusText }}</Tag>
            </template>
            
            <div class="flex flex-col md:flex-row gap-8">
                <div class="flex-1">
                    <h2 class="text-2xl font-bold mb-2">{{ subscription?.plan?.name || 'Loading...' }}</h2>
                    <p class="text-gray-500 mb-4">{{ subscription?.plan?.description }}</p>
                    
                    <div class="flex gap-8 mb-4">
                        <div>
                            <div class="text-gray-500 text-sm">生效时间</div>
                            <div class="font-medium">{{ subscription?.started_at }}</div>
                        </div>
                        <div>
                             <div class="text-gray-500 text-sm">过期时间</div>
                             <div class="font-medium">{{ subscription?.expires_at }}</div>
                        </div>
                    </div>
                </div>

                <div class="w-full md:w-1/3 bg-gray-50 p-4 rounded-lg">
                     <h3 class="font-bold mb-4">包含权益</h3>
                     <ul class="space-y-2">
                        <li class="flex justify-between">
                            <span>席位限制</span>
                            <span class="font-medium">{{ subscription?.plan?.seat_limit }} 人</span>
                        </li>
                        <li class="flex justify-between">
                            <span>反馈存储</span>
                            <span class="font-medium">{{ subscription?.plan?.feedback_limit }} 条</span>
                        </li>
                        <li class="flex justify-between">
                            <span>每月 AI 积分</span>
                            <span class="font-medium">{{ subscription?.plan?.ai_credits_monthly }}</span>
                        </li>
                     </ul>
                </div>
            </div>
            
             <Divider />
             
             <div class="flex justify-end gap-2">
                <Button type="primary">升级套餐</Button>
                <Button>续费</Button>
             </div>
        </Card>

        <!-- 资源使用情况 -->
        <Card :loading="loading" title="资源使用情况">
             <Row :gutter="24">
                <Col :span="8">
                    <Statistic title="积分余额" :value="creditsInfo?.current_balance" :precision="0" />
                    <Progress 
                        :percent="creditsInfo?.usage_percentage" 
                        :status="creditsInfo?.usage_percentage > 90 ? 'exception' : 'active'" 
                        class="mt-2"
                    />
                    <div class="text-xs text-gray-500 mt-1">
                        月度额度: {{ creditsInfo?.monthly_quota === -1 ? '无限' : creditsInfo?.monthly_quota }}
                        (下次刷新: {{ creditsInfo?.next_refresh_at?.split('T')[0] }})
                    </div>
                </Col>
                <Col :span="8">
                     <Statistic title="已用席位" :value="0" suffix="/ 5" />
                     <Progress :percent="0" class="mt-2" />
                </Col>
                 <Col :span="8">
                     <Statistic title="已存反馈" :value="0" suffix="/ 1000" />
                     <Progress :percent="0" class="mt-2" />
                </Col>
             </Row>
        </Card>
    </div>
  </Page>
</template>
