/**
 * 邀请管理 API（管理端）
 */

import type { PageResult, Result } from '#/api';

import { requestClient } from '#/api/request';

/**
 * 邀请信息
 */
export interface InvitationInfo {
  id: string;
  token: string;
  usage_limit: number;
  used_count: number;
  expires_at: string;
  plan_code: string;
  trial_days: number;
  source?: string;
  campaign?: string;
  creator_id?: number;
  notes?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

/**
 * 邀请详情（包含URL）
 */
export interface InvitationDetail extends InvitationInfo {
  url: string;
  short_url?: string;
  qr_code_url: string;
  remaining_usage: number;
}

/**
 * 创建邀请请求
 */
export interface CreateInvitationRequest {
  usage_limit?: number;
  expires_days?: number;
  plan_code?: string;
  trial_days?: number;
  source?: string;
  campaign?: string;
  notes?: string;
}

/**
 * 更新邀请请求
 */
export interface UpdateInvitationRequest {
  status?: string;
  usage_limit?: number;
  expires_at?: string;
  notes?: string;
}

/**
 * 邀请使用记录
 */
export interface InvitationUsageRecord {
  id: string;
  invitation_id: string;
  user_id: number;
  registered_email: string;
  ip_address?: string;
  completed_onboarding: boolean;
  created_tenant_id?: string;
  used_at: string;
  user?: {
    id: number;
    email: string;
    nickname: string;
  };
  created_tenant?: {
    id: string;
    name: string;
  };
}

/**
 * 邀请使用详情响应
 */
export interface InvitationUsageResponse {
  invitation: InvitationInfo;
  usage_records: InvitationUsageRecord[];
  statistics: {
    total_used: number;
    completed_onboarding: number;
    conversion_rate: number;
  };
  total: number;
  page: number;
  size: number;
}

/**
 * 查询参数
 */
export interface InvitationQueryParams {
  status?: string;
  source?: string;
  campaign?: string;
  page?: number;
  size?: number;
}

/**
 * 获取邀请列表
 */
export async function getInvitationList(params?: InvitationQueryParams) {
  return requestClient.get<PageResult<InvitationInfo>>(
    '/api/v1/invitations',
    { params },
  );
}

/**
 * 创建邀请
 */
export async function createInvitation(data: CreateInvitationRequest) {
  return requestClient.post<Result<InvitationDetail>>(
    '/api/v1/invitations',
    data,
  );
}

/**
 * 获取邀请详情
 */
export async function getInvitationDetail(id: string) {
  return requestClient.get<Result<InvitationDetail>>(
    `/api/v1/invitations/${id}`,
  );
}

/**
 * 获取邀请使用详情
 */
export async function getInvitationUsage(id: string, params?: { page?: number; size?: number }) {
  return requestClient.get<Result<InvitationUsageResponse>>(
    `/api/v1/invitations/${id}/usage`,
    { params },
  );
}

/**
 * 更新邀请
 */
export async function updateInvitation(id: string, data: UpdateInvitationRequest) {
  return requestClient.patch<Result<InvitationInfo>>(
    `/api/v1/invitations/${id}`,
    data,
  );
}

/**
 * 删除邀请
 */
export async function deleteInvitation(id: string) {
  return requestClient.delete<Result<{ success: boolean }>>(
    `/api/v1/invitations/${id}`,
  );
}
