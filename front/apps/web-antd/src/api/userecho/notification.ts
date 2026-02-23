/**
 * 通知相关 API
 */

import { requestClient } from '#/api/request';

/** 议题通知记录 */
export interface TopicNotification {
    id: string;
    tenant_id: string;
    topic_id: string;
    feedback_id: string;
    customer_id?: string;
    recipient_name: string;
    recipient_contact?: string;
    recipient_type: 'customer' | 'external';
    ai_reply?: string;
    reply_tone: string;
    reply_language: string;
    status: 'pending' | 'generated' | 'copied' | 'sent';
    notified_at?: string;
    notified_by?: number;
    notification_channel?: string;
    notes?: string;
    created_time: string;
    updated_time?: string;
    // 关联信息
    customer_company?: string;
    customer_tier?: string;
    feedback_summary?: string;
    feedback_content?: string;
}

/** 通知列表响应 */
export interface TopicNotificationListResponse {
    items: TopicNotification[];
    stats: {
        total: number;
        pending: number;
        generated: number;
        sent: number;
    };
}

/** 生成回复请求参数 */
export interface GenerateReplyParams {
    tone?: 'formal' | 'friendly' | 'concise';
    language?: string;
    include_release_notes?: boolean;
    custom_context?: string;
}

/** 生成回复响应 */
export interface GenerateReplyResponse {
    ai_reply: string;
    tokens_used?: number;
    generation_time_ms?: number;
}

/** 批量生成请求参数 */
export interface BatchGenerateParams {
    tone?: 'formal' | 'friendly' | 'concise';
    language?: string;
}

/** 批量生成响应 */
export interface BatchGenerateResponse {
    success: number;
    failed: number;
    total: number;
    errors?: Array<{ id: string; error: string }>;
}

/** 标记已通知请求参数 */
export interface MarkNotifiedParams {
    status?: 'copied' | 'sent';
    notification_channel?: string;
    notes?: string;
}

/**
 * 获取议题的通知列表
 */
export async function getTopicNotifications(topicId: string, status?: string) {
    const params = status ? { status } : {};
    return requestClient.get<TopicNotificationListResponse>(
        `/api/v1/app/topics/${topicId}/notifications`,
        { params },
    );
}

/**
 * 生成 AI 回复
 */
export async function generateReply(
    topicId: string,
    notificationId: string,
    params: GenerateReplyParams,
) {
    return requestClient.post<GenerateReplyResponse>(
        `/api/v1/app/topics/${topicId}/notifications/${notificationId}/generate-reply`,
        params,
    );
}

/**
 * 批量生成 AI 回复
 */
export async function batchGenerateReplies(
    topicId: string,
    params: BatchGenerateParams,
) {
    return requestClient.post<BatchGenerateResponse>(
        `/api/v1/app/topics/${topicId}/notifications/batch-generate`,
        params,
    );
}

/**
 * 标记为已通知
 */
export async function markNotified(
    topicId: string,
    notificationId: string,
    params: MarkNotifiedParams,
) {
    return requestClient.patch<TopicNotification>(
        `/api/v1/app/topics/${topicId}/notifications/${notificationId}`,
        params,
    );
}

/** 系统提醒项 */
export interface SystemNotification {
    id: string;
    tenant_id: string;
    user_id?: number;
    type: string;
    title: string;
    message: string;
    avatar?: string;
    action_url?: string;
    extra_data?: Record<string, any>;
    is_read: boolean;
    read_at?: string;
    created_time: string;
    date?: string; // 相对时间
}

/** 系统提醒列表响应 */
export interface SystemNotificationListResponse {
    total: number;
    unread_count: number;
    items: SystemNotification[];
}

/**
 * 获取系统提醒列表
 */
export async function getSystemNotifications(unreadOnly: boolean = false) {
    const params = { unread_only: unreadOnly };
    return requestClient.get<SystemNotificationListResponse>(
        '/api/v1/app/notifications',
        { params },
    );
}

/**
 * 标记通知为已读
 */
export async function markNotificationAsRead(notificationId: string) {
    return requestClient.post(`/api/v1/app/notifications/${notificationId}/read`);
}

/**
 * 标记所有通知为已读
 */
export async function markAllNotificationsAsRead() {
    return requestClient.post<{ marked_count: number }>(
        '/api/v1/app/notifications/read-all',
    );
}

/**
 * 清空所有通知
 */
export async function clearAllNotifications() {
    return requestClient.delete<{ deleted_count: number }>(
        '/api/v1/app/notifications/clear',
    );
}

// ========== 回复模板 API ==========

/** 回复模板 */
export interface ReplyTemplate {
    id: string;
    tenant_id: string;
    name: string;
    description?: string;
    content: string;
    category: string;
    tone: string;
    language: string;
    is_system: boolean;
    is_active: boolean;
    usage_count: number;
    created_by?: number;
    created_time: string;
    updated_time?: string;
}

/** 回复模板列表响应 */
export interface ReplyTemplateListResponse {
    items: ReplyTemplate[];
    total: number;
}

/** 创建回复模板请求 */
export interface CreateReplyTemplateParams {
    name: string;
    description?: string;
    content: string;
    category?: string;
    tone?: string;
    language?: string;
    is_active?: boolean;
}

/**
 * 获取回复模板列表
 */
export async function getReplyTemplates(category?: string, tone?: string) {
    const params: Record<string, string> = {};
    if (category) params.category = category;
    if (tone) params.tone = tone;
    return requestClient.get<ReplyTemplateListResponse>(
        '/api/v1/app/reply-templates',
        { params },
    );
}

/**
 * 创建回复模板
 */
export async function createReplyTemplate(data: CreateReplyTemplateParams) {
    return requestClient.post<ReplyTemplate>('/api/v1/app/reply-templates', data);
}

/**
 * 删除回复模板
 */
export async function deleteReplyTemplate(templateId: string) {
    return requestClient.delete(`/api/v1/app/reply-templates/${templateId}`);
}

/**
 * 使用模板（增加使用次数）
 */
export async function useReplyTemplate(templateId: string) {
    return requestClient.post<{ content: string }>(
        `/api/v1/app/reply-templates/${templateId}/use`,
    );
}
