/**
 * AI 聚类 API
 */

import { requestClient } from '#/api/request';

/** 合并建议（与已有需求重复） */
export interface MergeSuggestion {
  cluster_label: number;
  suggested_topic_id: string;
  suggested_topic_title: string;
  suggested_topic_status: string;
  suggested_topic_category: string;
  similarity: number;
  feedback_ids: string[];
  feedback_count: number;
  is_completed: boolean;
  ai_generated_title: string;
  warning?: string;
  suggested_actions: Array<{
    action: 'link_to_existing' | 'reopen_and_link' | 'mark_outdated' | 'create_new';
    label: string;
  }>;
}

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
  /** 合并建议（与已有需求重复的聚类） */
  merge_suggestions?: MergeSuggestion[];
  quality_metrics?: {
    silhouette: number;
    davies_bouldin: number | null;  // null 表示聚类质量太差无法计算
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
  board_ids?: string[];
}

/**
 * 触发聚类任务
 */
export async function triggerClustering(params: TriggerClusteringParams = {}) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { board_ids, ...restParams } = params;
  return requestClient.post<ClusteringResult | ClusteringTaskAccepted>('/api/v1/app/clustering/trigger',
    { board_ids }, // Pass board_ids in request body
    {
      params: {
        max_feedbacks: 100,
        force_recluster: false,
        async_mode: true,  // 默认使用异步模式，避免请求超时
        ...restParams
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
 * 获取聚类状态概览（支持按 boardIds 筛选）
 */
export async function getClusteringStatus(boardIds?: string[]) {
  return requestClient.get<{
    pending_count: number;
    processing_count: number;
    last_run_at: string | null;
  }>('/api/v1/app/clustering/status', {
    params: {
      board_ids: boardIds,
    },
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

/**
 * 【调试】查看反馈相似度矩阵
 */
export interface SimilarityMatrixDebug {
  feedbacks: Array<{
    id: string;
    content: string;
    full_content: string;
  }>;
  similarity_matrix: number[][];
  high_similarity_pairs: Array<{
    feedback1_id: string;
    feedback1_content: string;
    feedback2_id: string;
    feedback2_content: string;
    similarity: number;
  }>;
  stats: {
    total_feedbacks: number;
    avg_similarity: number;
    max_similarity: number;
    min_similarity: number;
    pairs_above_075: number;
  };
}

export async function getSimilarityMatrix(limit = 20) {
  return requestClient.get<SimilarityMatrixDebug>('/api/v1/app/clustering/debug/similarity-matrix', {
    params: { limit },
  });
}

/**
 * 获取待处理的合并建议
 */
export async function getPendingMergeSuggestions() {
  return requestClient.get<MergeSuggestion[]>('/api/v1/app/clustering/pending-suggestions');
}
