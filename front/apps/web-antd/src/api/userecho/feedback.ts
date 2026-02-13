/**
 * 反馈管理 API
 */

import { requestClient } from '#/api/request';

/** 反馈对象 */
export interface Feedback {
  id: string;
  tenant_id: string;
  customer_id?: string;
  customer_name?: string;
  anonymous_author?: string;
  anonymous_source?: string;
  topic_id?: string;
  topic_title?: string;
  content: string;
  source: string;
  ai_summary?: string;
  is_urgent: boolean;
  ai_metadata?: Record<string, any>;
  clustering_status?: 'pending' | 'processing' | 'clustered' | 'failed';
  clustering_metadata?: Record<string, any>;
  submitted_at: string;
  created_time: string;
  updated_time: string;
  deleted_at?: string;
}

/** 创建反馈参数 */
export interface CreateFeedbackParams {
  customer_id?: string;
  anonymous_author?: string;
  anonymous_source?: string;
  content: string;
  source?: string;
  is_urgent?: boolean;
}

/** 更新反馈参数 */
export interface UpdateFeedbackParams {
  content?: string;
  topic_id?: string;
  is_urgent?: boolean;
}

/** 反馈列表查询参数 */
export interface FeedbackListParams {
  skip?: number;
  limit?: number;
  topic_id?: string;
  customer_id?: string;
  is_urgent?: boolean;
  has_topic?: boolean;
  clustering_status?: 'pending' | 'processing' | 'clustered' | 'failed';
}

/** 导入结果 */
export interface ImportResult {
  status: string;
  total: number;
  success: number;
  failed: number;
  errors?: Array<{
    row: number;
    error: string;
    content: string;
  }>;
  has_more_errors?: boolean;
}

/**
 * 获取反馈列表
 */
export async function getFeedbackList(params: FeedbackListParams) {
  return requestClient.get<Feedback[]>('/api/v1/app/feedbacks', { params });
}

/**
 * 创建反馈
 */
export async function createFeedback(data: CreateFeedbackParams) {
  return requestClient.post<Feedback>('/api/v1/app/feedbacks', data);
}

/**
 * 更新反馈
 */
export async function updateFeedback(id: string, data: UpdateFeedbackParams) {
  return requestClient.put<Feedback>(`/api/v1/app/feedbacks/${id}`, data);
}

/**
 * 删除反馈
 */
export async function deleteFeedback(id: string) {
  return requestClient.delete(`/api/v1/app/feedbacks/${id}`);
}

/**
 * 导入 Excel 反馈
 */
export async function importFeedbacks(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post<ImportResult>('/api/v1/app/feedbacks/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * 下载导入模板
 */
export function downloadImportTemplate() {
  window.open('/api/v1/app/feedbacks/import/template', '_blank');
}
