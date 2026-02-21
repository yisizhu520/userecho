/**
 * 积分管理 API
 */

import { requestClient } from '#/api/request';

/** 积分余额信息 */
export interface CreditsBalance {
    plan_type: string;
    monthly_quota: number;
    current_balance: number;
    total_used: number;
    next_refresh_at: string | null;
    usage_percentage: number;
    is_unlimited: boolean;
}

/** 积分使用记录 */
export interface CreditsUsageLog {
    id: string;
    operation_type: string;
    credits_cost: number;
    description: string;
    created_at: string;
}

/** 积分配置项 */
export interface CreditsConfigItem {
    id: string;
    config_key: string;
    config_value: number;
    description: string;
}

/** 租户积分状态 */
export interface TenantCreditsItem {
    id: string;
    tenant_id: string;
    plan_type: string;
    monthly_quota: number;
    current_balance: number;
    total_used: number;
    next_refresh_at: string | null;
}

// ==================== 用户 API ====================

/**
 * 获取积分余额
 */
export async function getCreditsBalance() {
    return requestClient.get<CreditsBalance>('/api/v1/app/credits/balance');
}

/**
 * 获取积分使用记录
 */
export async function getCreditsUsage(params?: {
    operation_type?: string;
    limit?: number;
}) {
    return requestClient.get<CreditsUsageLog[]>('/api/v1/app/credits/usage', {
        params,
    });
}

/**
 * 获取积分统计
 */
export async function getCreditsStats() {
    return requestClient.get<{
        breakdown: Record<string, number>;
        total: number;
    }>('/api/v1/app/credits/stats');
}

// ==================== Admin API ====================

/**
 * 获取所有积分配置（Admin）
 */
export async function getCreditsConfigs() {
    return requestClient.get<{
        operation_cost: CreditsConfigItem[];
        plan_quota: CreditsConfigItem[];
    }>('/api/v1/credits/configs');
}

/**
 * 更新积分配置（Admin）
 */
export async function updateCreditsConfig(
    configId: string,
    data: { config_value: number; description?: string }
) {
    return requestClient.put<CreditsConfigItem>(
        `/api/v1/credits/configs/${configId}`,
        data
    );
}

/**
 * 获取所有租户积分状态（Admin）
 */
export async function getAllTenantCredits() {
    return requestClient.get<TenantCreditsItem[]>('/api/v1/credits/tenants');
}

/**
 * 调整租户积分（Admin）
 */
export async function adjustTenantCredits(
    tenantId: string,
    data: { adjustment: number; reason: string }
) {
    return requestClient.post<{
        tenant_id: string;
        old_balance: number;
        new_balance: number;
        adjustment: number;
    }>(`/api/v1/credits/tenants/${tenantId}/adjust`, data);
}

/**
 * 变更租户套餐（Admin）
 */
export async function updateTenantPlan(tenantId: string, planType: string) {
    return requestClient.put<{
        tenant_id: string;
        old_plan: string;
        new_plan: string;
        monthly_quota: number;
    }>(`/api/v1/credits/tenants/${tenantId}/plan`, null, {
        params: { plan_type: planType },
    });
}
