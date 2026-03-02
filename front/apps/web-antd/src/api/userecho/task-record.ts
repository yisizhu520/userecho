/**
 * 任务追踪 API
 */

import { requestClient } from '#/api/request';

/** 任务记录 */
export interface TaskRecord {
  id: number;
  celery_task_id: string;
  celery_task_name: string;
  task_category: string;
  task_display_name: string;
  status: string;
  context: Record<string, any> | null;
  result_summary: Record<string, any> | null;
  batch_job_id: string | null;
  duration_ms: number | null;
  error_message: string | null;
  created_time: string | null;
  started_time: string | null;
  completed_time: string | null;
}

/** 任务列表响应 */
export interface TaskRecordListResult {
  items: TaskRecord[];
  total: number;
  page: number;
  page_size: number;
}

/** 任务分类统计 */
export interface TaskCategoryStat {
  category: string;
  total: number;
  success: number;
  failure: number;
  avg_duration_ms: number | null;
}

/** 任务统计响应 */
export interface TaskStatsResult {
  status_counts: Record<string, number>;
  categories: TaskCategoryStat[];
  recent_failures: Array<{
    celery_task_id: string;
    task_display_name: string;
    error_message: string;
    created_time: string | null;
  }>;
  total: number;
}

/** 任务分类选项 */
export interface TaskCategoryOption {
  category: string;
  count: number;
}

/** 任务元数据 */
export interface TaskMetadata {
  task_name: string;
  category: string;
  display_name: string;
}

/** 查询任务列表 */
export async function getTaskRecordListApi(params?: {
  category?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<TaskRecordListResult>(
    '/api/v1/task-records',
    { params },
  );
}

/** 获取任务统计 */
export async function getTaskStatsApi(params?: {
  start_time?: string;
  end_time?: string;
}) {
  return requestClient.get<TaskStatsResult>(
    '/api/v1/task-records/stats',
    { params },
  );
}

/** 获取任务分类列表 */
export async function getTaskCategoriesApi() {
  return requestClient.get<TaskCategoryOption[]>(
    '/api/v1/task-records/categories',
  );
}

/** 获取任务元数据 */
export async function getTaskMetadataApi() {
  return requestClient.get<TaskMetadata[]>(
    '/api/v1/task-records/metadata',
  );
}

/** 获取单个任务详情 */
export async function getTaskRecordDetailApi(celeryTaskId: string) {
  return requestClient.get<TaskRecord>(
    `/api/v1/task-records/${celeryTaskId}`,
  );
}
