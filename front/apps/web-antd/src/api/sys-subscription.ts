import { requestClient } from '#/api/request';

/**
 * 订阅套餐
 */
export interface SubscriptionPlan {
    id: string;
    code: string;
    name: string;
    description: string;
    price_monthly: number;
    price_yearly: number;
    seat_limit: number;
    feedback_limit: number;
    ai_credits_monthly: number;
    features: Record<string, any>;
    is_active: boolean;
    sort_order: number;
}

/**
 * 租户订阅详情
 */
export interface TenantSubscription {
    tenant_id: string;
    plan_id: string;
    status: 'trial' | 'active' | 'expired' | 'canceled';
    started_at: string;
    expires_at: string;
    trial_ends_at?: string;
    canceled_at?: string;
    source: string;
    plan?: SubscriptionPlan;
}

/**
 * 更新订阅请求
 */
export interface SubscriptionUpdateReq {
    plan_code: string;
    expires_at: string;
    status: string;
    notes?: string;
}

/**
 * 获取所有可用套餐
 */
export async function getAllPlans() {
    return requestClient.get<SubscriptionPlan[]>('/subscription/plans');
}

/**
 * 获取租户订阅详情
 */
export async function getTenantSubscription(tenantId: string) {
    return requestClient.get<TenantSubscription>(`/subscription/tenant/${tenantId}`);
}

/**
 * 更新租户订阅
 */
export async function updateTenantSubscription(tenantId: string, data: SubscriptionUpdateReq) {
    return requestClient.post<TenantSubscription>(`/subscription/tenant/${tenantId}`, data);
}
