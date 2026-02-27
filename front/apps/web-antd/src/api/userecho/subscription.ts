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
 * 获取当前订阅
 */
export async function getCurrentSubscription() {
    return requestClient.get<TenantSubscription>('/api/v1/app/subscription/me');
}
