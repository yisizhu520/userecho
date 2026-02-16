/**
 * 引导流程 API
 * 
 * 用于新用户创建租户和看板的引导流程
 */

import { requestClient } from '#/api/request';

/** 引导状态 */
export interface OnboardingStatus {
    needs_onboarding: boolean;
    current_step: string | null;
    tenant_id: string | null;
    board_id: string | null;
    completed_steps: string[];
}

/** 创建租户参数 */
export interface CreateTenantParams {
    name: string;
    slug: string;
}

/** 创建租户返回 */
export interface CreateTenantResult {
    id: string;
    name: string;
    slug: string;
    created_time: string;
}

/** 创建看板参数 */
export interface CreateBoardParams {
    name: string;
    description?: string;
    access_mode: 'private' | 'public' | 'restricted';
}

/** 创建看板返回 */
export interface CreateBoardResult {
    id: string;
    tenant_id: string;
    name: string;
    url_name: string;
    description: string | null;
    access_mode: string;
    created_time: string;
}

/** Slug 检查结果 */
export interface SlugCheckResult {
    slug: string;
    available: boolean;
    suggestion: string | null;
}

/** 引导完成返回 */
export interface OnboardingCompleteResult {
    success: boolean;
    tenant_id: string;
    board_id: string;
    redirect_path: string;
}

/**
 * 获取引导状态
 */
export async function getOnboardingStatusApi() {
    return requestClient.get<OnboardingStatus>('/api/v1/app/onboarding/status');
}

/**
 * 检查 Slug 可用性
 */
export async function checkSlugApi(slug: string) {
    return requestClient.get<SlugCheckResult>('/api/v1/app/onboarding/check-slug', {
        params: { slug },
    });
}

/**
 * 根据名称生成 Slug
 */
export async function generateSlugApi(name: string) {
    return requestClient.get<{ slug: string }>('/api/v1/app/onboarding/generate-slug', {
        params: { name },
    });
}

/**
 * 创建租户
 */
export async function createTenantApi(data: CreateTenantParams) {
    return requestClient.post<CreateTenantResult>('/api/v1/app/onboarding/tenant', data);
}

/**
 * 创建看板
 */
export async function createBoardApi(data: CreateBoardParams) {
    return requestClient.post<CreateBoardResult>('/api/v1/app/onboarding/board', data);
}

/**
 * 完成引导
 */
export async function completeOnboardingApi() {
    return requestClient.post<OnboardingCompleteResult>('/api/v1/app/onboarding/complete');
}
