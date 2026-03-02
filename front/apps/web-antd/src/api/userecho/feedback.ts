/**
 * 反馈管理 API
 */

import { requestClient } from '#/api/request';

/** 反馈对象 */
export interface Feedback {
  id: string;
  tenant_id: string;
  board_id?: string;
  board_name?: string;
  customer_id?: string;
  customer_name?: string;
  anonymous_author?: string;
  anonymous_source?: string;
  submitter_id?: number;
  submitter_name?: string;
  topic_id?: string;
  topic_title?: string;
  topic_status?: 'review' | 'planned' | 'in_progress' | 'completed' | 'ignored';
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
  images_metadata?: {
    images?: Array<{ url: string; uploaded_at?: string }>;
  } | null;
  screenshot_url?: string | null; // 截图识别模式的单张截图URL
  source_platform?: string | null; // 来源平台
  source_user_name?: string | null; // 来源平台用户昵称
  source_user_id?: string | null; // 来源平台用户ID
  ai_confidence?: number | null; // AI识别置信度
  author_type?: 'customer' | 'external'; // 来源类型
  external_user_name?: string | null; // 外部用户名称
  external_contact?: string | null; // 外部用户联系方式
}

/** 创建反馈参数 */
export interface CreateFeedbackParams {
  board_id: string;
  content: string;
  source?: string;
  is_urgent?: boolean;
  topic_id?: string;
  screenshots?: string[];
  // 来源类型枚举
  author_type: 'customer' | 'external';
  // 内部客户模式字段
  customer_id?: string;
  customer_name?: string;
  customer_type?: string;
  // 外部用户模式字段
  external_user_name?: string;
  external_contact?: string;
  source_platform?: string;
}

/** 更新反馈参数 */
export interface UpdateFeedbackParams {
  content?: string;
  topic_id?: string | null;
  is_urgent?: boolean;
  screenshots?: string[];
  customer_name?: string;
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

/** 导入预览结果 */
export interface ImportPreviewResult {
  status: 'ready' | 'error';
  message?: string;
  total_rows: number;
  sample_data: Record<string, string>[];
  detected_columns: string[];
  missing_required: string[];
  missing_optional: string[];
}

/** 导入配置 */
export interface ImportConfig {
  default_board_id?: string;
  author_type: 'customer' | 'external';
  // 内部客户模式
  default_customer_name?: string;
  // 外部用户模式
  default_source_platform?: string;
  default_external_user_name?: string;
}

/** 单条反馈数据 */
export interface FeedbackItem {
  platform: 'wechat' | 'xiaohongshu' | 'appstore' | 'weibo' | 'qq' | 'other';
  user_name: string;
  user_id: string;
  content: string;
  feedback_type: 'bug' | 'feature' | 'improvement' | 'performance' | 'complaint' | 'other';
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
}

/** 截图识别提取的数据（新版：支持多条反馈） */
export interface ExtractedScreenshotData {
  raw_text: string;                // OCR 提取的原始文本
  feedback_list: FeedbackItem[];   // 反馈列表（支持多条）
  overall_confidence: number;      // 整体置信度
}

/** 截图识别响应（异步模式） */
export interface ScreenshotAnalyzeResponse {
  task_id: string;
  status: 'processing';
  status_url: string;
}

/** 直传签名请求 */
export interface UploadImageSignRequest {
  filename: string;
  content_type?: string;
}

/** 直传签名响应 */
export interface UploadImageSignResponse {
  upload_url: string;
  method: 'PUT';
  headers: Record<string, string>;
  cdn_url: string;
  object_key: string;
  expires_in: number;
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
  board_id: string;
  content: string;
  screenshot_url: string;
  source_type: 'screenshot';
  ai_confidence?: number;
  // 来源类型枚举
  author_type: 'customer' | 'external';
  // 内部客户模式字段
  customer_id?: string | null;
  customer_name?: string;
  customer_type?: string;
  // 外部用户模式字段
  source_platform?: string;
  external_user_name?: string;
  external_contact?: string;
  source_user_id?: string;
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
 * 预览导入文件
 */
export async function previewImport(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post<ImportPreviewResult>(
    '/api/v1/app/feedbacks/import/preview',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
}

/**
 * 导入反馈（带配置）
 */
export async function importFeedbacksWithConfig(file: File, config: ImportConfig) {
  const formData = new FormData();
  formData.append('file', file);

  const params = new URLSearchParams();
  if (config.default_board_id) params.append('default_board_id', config.default_board_id);
  params.append('author_type', config.author_type);

  if (config.author_type === 'customer') {
    if (config.default_customer_name) params.append('default_customer_name', config.default_customer_name);
  } else {
    if (config.default_source_platform) params.append('default_source_platform', config.default_source_platform);
    if (config.default_external_user_name) params.append('default_external_user_name', config.default_external_user_name);
  }

  const queryString = params.toString();
  const url = queryString
    ? `/api/v1/app/feedbacks/import?${queryString}`
    : '/api/v1/app/feedbacks/import';

  return requestClient.post<ImportResult>(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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
 * 截图智能识别（URL）
 */
export async function analyzeScreenshotByUrl(screenshotUrl: string) {
  return requestClient.post<ScreenshotAnalyzeResponse>('/api/v1/app/feedbacks/screenshot/analyze-url', {
    screenshot_url: screenshotUrl,
  });
}

/**
 * 获取截图直传签名
 * @deprecated 请使用 getUploadSign from '#/api/core/upload'
 */
export async function getFeedbackImageUploadSign(data: UploadImageSignRequest) {
  return requestClient.post<UploadImageSignResponse>('/api/v1/app/feedbacks/upload-image/sign', data);
}

/**
 * 直传到对象存储
 * @deprecated 请使用 uploadToSignedUrl from '#/api/core/upload'
 */
export async function uploadImageToSignedUrl(sign: UploadImageSignResponse, file: File) {
  const headers = new Headers(sign.headers || {});
  if (!headers.has('Content-Type') && file.type) {
    headers.set('Content-Type', file.type);
  }

  const response = await fetch(sign.upload_url, {
    method: sign.method || 'PUT',
    headers,
    body: file,
  });

  if (!response.ok) {
    throw new Error(`直传失败: ${response.status}`);
  }
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

/**
 * 上传反馈截图（同步，用于手动创建反馈）
 */
export async function uploadFeedbackImage(file: File): Promise<{ url: string }> {
  try {
    // 使用通用上传 API
    const { uploadScreenshot } = await import('#/api/core/upload');
    const url = await uploadScreenshot(file);
    return { url };
  } catch (error) {
    // 回退到后端中转上传
    const formData = new FormData();
    formData.append('file', file);
    return requestClient.post('/api/v1/app/feedbacks/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }
}

/** 批量截图识别请求 */
export interface ScreenshotBatchUploadRequest {
  image_urls: string[];
  board_id: string;
  author_type: 'customer' | 'external';
  // 内部客户模式
  default_customer_name?: string;
  // 外部用户模式
  source_platform?: string;
  default_user_name?: string;
}

/** 批量任务响应 */
export interface BatchJobResponse {
  batch_id: string;
  celery_task_id: string | null;
  total_count: number;
}

/** 批量任务进度 */
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
  summary?: any;
  create_time: string;
  started_time?: string;
  completed_time?: string;
  celery_task_id?: string;
}

/** 批量任务项结果 */
export interface BatchTaskItemResult {
  task_item_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped';
  input_data: any;
  output_data?: {
    screenshot_url: string;
    feedbacks: Array<{
      feedback_id: string;
      content: string;
      confidence: number;
    }>;
    total_feedbacks: number;
    overall_confidence: number;
  };
  error_message?: string;
  retry_count: number;
  started_time?: string;
  completed_time?: string;
}

/**
 * 批量截图识别（前端直传模式）
 */
export async function screenshotBatchUpload(data: ScreenshotBatchUploadRequest) {
  return requestClient.post<BatchJobResponse>('/api/v1/app/batch/feedbacks/screenshot-batch-upload', data);
}

/**
 * 查询批量任务进度
 */
export async function getBatchJobProgress(batchId: string) {
  return requestClient.get<BatchJobProgress>(`/api/v1/app/batch/jobs/${batchId}`);
}

/**
 * 获取批量任务详细结果
 */
export async function getBatchJobResults(batchId: string, status?: string) {
  return requestClient.get<BatchTaskItemResult[]>(`/api/v1/app/batch/jobs/${batchId}/results`, {
    params: { status },
  });
}

/**
 * 取消批量任务
 */
export async function cancelBatchJob(batchId: string) {
  return requestClient.delete(`/api/v1/app/batch/jobs/${batchId}`);
}
