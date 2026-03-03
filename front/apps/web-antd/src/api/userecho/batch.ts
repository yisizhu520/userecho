import { requestClient } from '#/api/request';

// ============================================
// 统一任务中心类型定义
// ============================================

// 任务类型
export type TaskType =
  | 'batch_screenshot_recognition' // 批量截图识别
  | 'batch_ai_clustering' // 批量AI聚类
  | 'batch_export' // 批量导出
  | 'excel_import' // Excel导入
  | 'clustering' // 单次AI聚类
  | 'screenshot_recognition' // 单次截图识别
  | 'ai_screenshot' // AI截图分析
  | 'batch'; // 通用批处理任务

// 任务状态
export type TaskStatus =
  | 'pending' // 待处理
  | 'processing' // 处理中
  | 'completed' // 已完成
  | 'failed' // 失败
  | 'cancelled'; // 已取消

// 统一任务
export interface UnifiedTask {
  id: string; // 后端返回 id 而不是 task_id
  type: TaskType; // 后端返回 type 而不是 task_type
  name: string;
  description: string | null;
  status: TaskStatus;
  progress: number;
  total_count: number | null;
  completed_count: number | null;
  failed_count: number | null;
  pending_count: number | null;
  created_time: string;
  started_time: string | null;
  completed_time: string | null;
  celery_task_id: string | null;
  result_summary: Record<string, any> | null;
  error_message: string | null;
  can_cancel: boolean;
  can_retry: boolean;
  can_view_detail: boolean;
  detail_url: string | null;
  // 兼容字段（用于后续可能的扩展）
  metadata?: Record<string, any>;
  summary?: Record<string, any>;
  is_batch?: boolean;
}

// 统一任务列表响应
export interface UnifiedTaskListResponse {
  data: UnifiedTask[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================
// 旧版批处理任务类型（兼容性保留）
// ============================================

// 批处理任务类型
export interface BatchJob {
  batch_id: string;
  task_type: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  total_count: number;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  progress: number;
  summary: Record<string, any>;
  create_time: string; // 后端返回 create_time
  started_time: string | null;
  completed_time: string | null;
  celery_task_id: string | null;
}

// 批处理任务进度
export interface BatchJobProgress {
  batch_id: string;
  task_type: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  total_count: number;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  progress: number;
  summary: Record<string, any>;
  create_time: string; // 后端返回 create_time
  started_time: string | null;
  completed_time: string | null;
  celery_task_id: string | null;
}

// 批处理任务项
export interface BatchTaskItem {
  id: string;
  batch_job_id: string;
  sequence_no: number | null;
  input_data: Record<string, any>;
  output_data: Record<string, any> | null;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped';
  error_message: string | null;
  error_code: string | null;
  retry_count: number;
  max_retries: number;
  created_time: string;
  started_time: string | null;
  completed_time: string | null;
}

// ============================================
// 统一任务中心 API
// ============================================

/**
 * 获取统一任务列表
 */
export async function getUnifiedTasks(params?: {
  task_type?: TaskType;
  status?: TaskStatus;
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<UnifiedTaskListResponse>('/api/v1/app/tasks', {
    params,
  });
}

/**
 * 获取统一任务详情
 */
export async function getUnifiedTask(taskId: string) {
  return requestClient.get<UnifiedTask>(`/api/v1/app/tasks/${taskId}`);
}

/**
 * 取消统一任务
 */
export async function cancelUnifiedTask(taskId: string) {
  return requestClient.post(`/api/v1/app/tasks/${taskId}/cancel`);
}

/**
 * 重试统一任务
 */
export async function retryUnifiedTask(taskId: string) {
  return requestClient.post(`/api/v1/app/tasks/${taskId}/retry`);
}

// ============================================
// 旧版批处理任务 API（兼容性保留）
// ============================================

/**
 * 获取批处理任务列表
 */
export async function getBatchJobs(params?: {
  task_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<BatchJob[]>('/api/v1/app/batch/jobs', {
    params,
  });
}

/**
 * 获取批处理任务进度
 */
export async function getBatchJobProgress(jobId: string) {
  return requestClient.get<BatchJobProgress>(`/api/v1/app/batch/jobs/${jobId}`);
}

/**
 * 获取批处理任务项列表
 */
export async function getBatchJobItems(jobId: string) {
  return requestClient.get<BatchTaskItem[]>(`/api/v1/app/batch/jobs/${jobId}/items`);
}

/**
 * 取消批处理任务
 */
export async function cancelBatchJob(jobId: string) {
  return requestClient.delete(`/api/v1/app/batch/jobs/${jobId}`);
}

/**
 * 重试失败的任务项
 */
export async function retryBatchJob(jobId: string) {
  return requestClient.post(`/api/v1/app/batch/jobs/${jobId}/retry`);
}

/**
 * 批量上传截图
 */
export async function batchUploadScreenshots(formData: FormData) {
  return requestClient.post<{
    batch_id: string;
    celery_task_id: string;
    total_count: number;
  }>('/api/v1/app/batch/feedbacks/screenshot-batch-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}
