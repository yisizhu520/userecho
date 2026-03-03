/**
 * 邀请相关 API
 */

import { requestClient } from '#/api/request';

/**
 * 邀请验证响应
 */
export interface InvitationValidateResponse {
  valid: boolean;
  plan?: {
    code: string;
    name: string;
    trial_days: number;
  };
  expires_at?: string;
  remaining_usage?: number;
  error_code?: string;
  error_message?: string;
}

/**
 * 邀请注册请求
 */
export interface RegisterWithInvitationRequest {
  invitation_token: string;
  email: string;
  password: string;
  nickname: string;
}

/**
 * 邀请注册响应
 */
export interface RegisterWithInvitationResponse {
  user: {
    id: number;
    email: string;
    nickname: string;
    email_verified: boolean;
  };
  access_token: string;
  session_uuid: string;
  access_token_expire_time: string;
  verification_email_sent: boolean;
  next_step: string;
}

/**
 * 验证邮箱请求
 */
export interface VerifyEmailRequest {
  verification_code: string;
}

/**
 * 验证邮箱响应
 */
export interface VerifyEmailResponse {
  verified: boolean;
  message: string;
}

/**
 * 重发验证邮件请求
 */
export interface ResendVerificationRequest {
  email: string;
}

/**
 * 验证邀请有效性
 */
export async function validateInvitation(token: string) {
  return requestClient.get<InvitationValidateResponse>(
    `/api/v1/invitations/${token}/validate`,
  );
}

/**
 * 通过邀请码注册
 */
export async function registerWithInvitation(
  data: RegisterWithInvitationRequest,
) {
  return requestClient.post<RegisterWithInvitationResponse>(
    '/api/v1/auth/register/invite',
    data,
  );
}

/**
 * 验证邮箱
 */
export async function verifyEmail(data: VerifyEmailRequest) {
  return requestClient.post<VerifyEmailResponse>(
    '/api/v1/auth/email/verify',
    data,
  );
}

/**
 * 重新发送验证邮件
 */
export async function resendVerificationEmail(data: ResendVerificationRequest) {
  return requestClient.post('/api/v1/auth/email/resend', data);
}
