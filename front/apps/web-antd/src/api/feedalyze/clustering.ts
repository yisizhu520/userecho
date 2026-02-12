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

/** 聚类建议 */
export interface ClusteringSuggestion {
  feedback_id: string;
  content: string;
  similarity: number;
  topic_id?: string;
  topic_title?: string;
}

/**
 * 触发聚类任务
 */
export async function triggerClustering(maxFeedbacks = 100) {
  return requestClient.post<ClusteringResult>('/api/v1/app/clustering/trigger', null, {
    params: { max_feedbacks: maxFeedbacks },
  });
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
