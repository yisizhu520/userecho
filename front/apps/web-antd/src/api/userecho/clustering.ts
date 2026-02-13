/**
 * AI 聚类 API
 */

import { requestClient } from '#/api/request';

/** 聚类结果 */
export interface ClusteringResult {
  status: string;
  message?: string;
  feedbacks_count: number;
  clusters_count: number;
  topics_created: number;
  topics_failed?: number;
  noise_count?: number;
  elapsed_ms?: number;
  topics?: Array<{
    topic_id: string;
    title: string;
    feedback_count: number;
    is_noise: boolean;
  }>;
  quality_metrics?: {
    silhouette: number;
    davies_bouldin: number;
    noise_ratio: number;
  };
}

/** 异步聚类：任务已提交 */
export interface ClusteringTaskAccepted {
  status: 'accepted';
  task_id: string;
}

/** 异步聚类：任务状态 */
export interface ClusteringTaskStatus {
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY';
  result?: ClusteringResult;
  error?: string;
}

/** 聚类建议 */
export interface ClusteringSuggestion {
  feedback_id: string;
  content: string;
  similarity: number;
  topic_id?: string;
  topic_title?: string;
}

export interface TriggerClusteringParams {
  max_feedbacks?: number;
  force_recluster?: boolean;
  async_mode?: boolean;
}

/**
 * 触发聚类任务
 */
export async function triggerClustering(params: TriggerClusteringParams = {}) {
  return requestClient.post<ClusteringResult | ClusteringTaskAccepted>('/api/v1/app/clustering/trigger', null, {
    params: { 
      max_feedbacks: 100, 
      force_recluster: false, 
      async_mode: true,  // 默认使用异步模式，避免请求超时
      ...params 
    },
  });
}

/**
 * 查询聚类任务状态
 */
export async function getClusteringTaskStatus(taskId: string) {
  return requestClient.get<ClusteringTaskStatus>(`/api/v1/app/clustering/task/${taskId}`);
}

/**
 * 获取聚类建议
 */
export async function getClusteringSuggestions(feedbackId: string, topK = 5) {
  return requestClient.get<ClusteringSuggestion[]>(
    `/api/v1/app/clustering/suggestions/${feedbackId}`,
    {
      params: { top_k: topK },
    },
  );
}
