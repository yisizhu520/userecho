/**
 * 需求主题 API
 */

import type { PriorityScore } from './priority';

import { requestClient } from '#/api/request';

/** 主题对象 */
export interface Topic {
  id: string;
  tenant_id: string;
  board_id?: string;
  title: string;
  category: string;
  status: string;
  description?: string;
  ai_generated: boolean;
  ai_confidence?: number;
  feedback_count: number;
  centroid?: number[] | null;
  cluster_quality?: Record<string, any> | null;
  is_noise?: boolean;
  priority_score?: {
    id: string;
    impact_scope: number;
    business_value: number;
    dev_cost: number;
    urgency_factor: number;
    total_score: number;
    details?: any; // JSON
    tenant_id: string;
    topic_id: string;
    created_time: string;
    updated_time?: string;
  } | null;
  created_time: string;
  updated_time: string;
  deleted_at?: string;
}

/** 主题详情（包含关联数据） */
export interface TopicDetail {
  topic: Topic;
  feedbacks: Array<{
    id: string;
    content: string;
    customer_name?: string;
    submitted_at: string;
  }>;
  priority_score?: PriorityScore | null;
  status_history: Array<{
    id: string;
    from_status: string;
    to_status: string;
    reason?: string;
    changed_by: number;
    changed_by_name?: string;
    changed_at: string;
  }>;
}

/** 创建主题参数 */
export interface CreateTopicParams {
  title: string;
  category?: string;
  status?: string;
  description?: string;
  board_id?: string;
}

/** 更新主题参数 */
export interface UpdateTopicParams {
  title?: string;
  category?: string;
  status?: string;
  description?: string;
  board_id?: string;
}

/** 主题列表查询参数 */
export interface TopicListParams {
  skip?: number;
  limit?: number;
  status?: string[];
  category?: string[];
  board_ids?: string[];
  sort_by?: string;
  sort_order?: string;
  search_query?: string;
  search_mode?: 'keyword' | 'semantic';
}

/** 更新主题状态参数 */
export interface UpdateTopicStatusParams {
  status: string;
  reason?: string;
}

/**
 * 获取主题列表
 */
export async function getTopicList(params: TopicListParams) {
  return requestClient.get<Topic[]>('/api/v1/app/topics', { params });
}

/**
 * 获取主题详情
 */
export async function getTopicDetail(id: string) {
  return requestClient.get<TopicDetail>(`/api/v1/app/topics/${id}`);
}

/**
 * 创建主题
 */
export async function createTopic(data: CreateTopicParams) {
  return requestClient.post<Topic>('/api/v1/app/topics', data);
}

/**
 * 更新主题
 */
export async function updateTopic(id: string, data: UpdateTopicParams) {
  return requestClient.put<Topic>(`/api/v1/app/topics/${id}`, data);
}

/**
 * 更新主题状态
 */
export async function updateTopicStatus(id: string, data: UpdateTopicStatusParams) {
  return requestClient.put<Topic>(`/api/v1/app/topics/${id}/status`, data);
}

/**
 * 获取待确认主题数量
 */
export async function getPendingTopicCount() {
  return requestClient.get<{ count: number }>('/api/v1/app/topics/stats/pending-count');
}

/**
 * 删除主题
 */
export async function deleteTopic(id: string) {
  return requestClient.delete(`/api/v1/app/topics/${id}`);
}

/**
 * 关联反馈到主题
 */
export async function linkFeedbacksToTopic(topicId: string, feedbackIds: string[]) {
  return requestClient.post<{ count: number }>(`/api/v1/app/topics/${topicId}/feedbacks`, {
    feedback_ids: feedbackIds,
  });
}

/**
 * 从主题移除反馈关联
 */
export async function unlinkFeedbackFromTopic(topicId: string, feedbackId: string) {
  return requestClient.delete(`/api/v1/app/topics/${topicId}/feedbacks/${feedbackId}`);
}

/** 主题分类选项 */
export const TOPIC_CATEGORIES = [
  { value: 'bug', label: 'Bug', color: 'red' },
  { value: 'improvement', label: '体验优化', color: 'blue' },
  { value: 'feature', label: '新功能', color: 'green' },
  { value: 'performance', label: '性能问题', color: 'orange' },
  { value: 'other', label: '其他', color: 'default' },
];

/** 主题状态选项 */
export const TOPIC_STATUSES = [
  { value: 'pending', label: '待处理', color: 'default' },
  { value: 'planned', label: '已规划', color: 'blue' },
  { value: 'in_progress', label: '进行中', color: 'orange' },
  { value: 'completed', label: '已完成', color: 'green' },
  { value: 'ignored', label: '已忽略', color: 'red' },
];
