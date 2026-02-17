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
  board_id: string;
  customer_id?: string;
  customer_name?: string;
  anonymous_author?: string;
  anonymous_source?: string;
  content: string;
  source?: string;
  is_urgent?: boolean;
  topic_id?: string;
  screenshots?: string[];
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
  is_urgent?: string[];
  has_topic?: string[];
  clustering_status?: string[];
  board_ids?: string[];
  search_query?: string;
  search_mode?: 'keyword' | 'semantic';
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

/** 截图识别提取的数据 */
export interface ExtractedScreenshotData {
  platform: 'wechat' | 'xiaohongshu' | 'appstore' | 'weibo' | 'other';
  user_name: string;
  user_id: string;
  content: string;
  feedback_type: 'bug' | 'feature' | 'complaint' | 'other';
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
}

/** 截图识别响应（异步模式） */
export interface ScreenshotAnalyzeResponse {
  task_id: string;
  status: 'processing';
  status_url: string;
}

/** 任务状态响应 */
export interface TaskStatusResponse {
  state: 'PENDING' | 'STARTED' | 'RETRY' | 'SUCCESS' | 'FAILURE';
  result?: {
    screenshot_url: string;
    extracted: ExtractedScreenshotData;
  };
  error?: string;
  info?: any;
}

/** 从截图创建反馈参数 */
export interface ScreenshotFeedbackCreateParams {
  content: string;
  screenshot_url: string;
  source_type: 'screenshot';
  source_platform: string;
  source_user_name?: string;
  source_user_id?: string;
  ai_confidence?: number;
  customer_id?: string | null;
}

/**
 * 获取反馈列表
 */
export async function getFeedbackList(params: FeedbackListParams) {
  return requestClient.get<Feedback[]>('/api/v1/app/feedbacks', {
    params,
    // 使用 repeat 格式序列化数组参数：is_urgent=true&is_urgent=false
    // 而不是默认的 is_urgent[]=true&is_urgent[]=false
    paramsSerializer: 'repeat',
  });
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

/**
 * 截图智能识别（异步）
 */
export async function analyzeScreenshot(formData: FormData) {
  return requestClient.post<ScreenshotAnalyzeResponse>('/api/v1/app/feedbacks/screenshot/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * 查询截图分析任务状态
 */
export async function getScreenshotTaskStatus(taskId: string) {
  return requestClient.get<TaskStatusResponse>(`/api/v1/app/feedbacks/screenshot/task/${taskId}`);
}

/**
 * 从截图创建反馈
 */
export async function createFeedbackFromScreenshot(data: ScreenshotFeedbackCreateParams) {
  return requestClient.post<Feedback>('/api/v1/app/feedbacks/screenshot/create', data);
}
