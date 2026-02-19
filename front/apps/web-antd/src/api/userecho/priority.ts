/**
 * 优先级评分 API
 */

import { requestClient } from '#/api/request';

/** 优先级评分参数 */
export interface PriorityScoreParams {
  topic_id: string;
  impact_scope: number;
  business_value: number;
  dev_cost: number;
  urgency_factor?: number;
}

/** 优先级评分结果 */
export interface PriorityScore {
  id: string;
  tenant_id: string;
  topic_id: string;
  impact_scope: number;
  business_value: number;
  dev_cost: number;
  urgency_factor: number;
  total_score: number;
  details?: any; // JSON
  created_time: string;
  updated_time?: string;
}

/** AI 建议 */
export interface AISuggestion {
  scope?: number;
  days?: number;
  value?: number;
  confidence: number;
  reason: string;
}

/** AI 分析结果 */
export interface AIAnalysisResult {
  impact_scope: AISuggestion;
  business_value: AISuggestion;
  dev_cost: AISuggestion;
}

/** 优先级排行榜项 */
export interface PriorityRankingItem {
  rank: number;
  topic_id: string;
  topic_title: string;
  topic_status: string;
  category: string;
  feedback_count: number;
  total_score: number;
  impact_scope: number;
  business_value: number;
  dev_cost: number;
  urgency_factor: number;
}

/**
 * AI 分析优先级（详情页点击「AI 重新分析」）
 */
export async function analyzePriority(topicId: string) {
  return requestClient.post<AIAnalysisResult>(
    `/api/v1/app/topics/${topicId}/priority/analyze`
  );
}

/**
 * 创建或更新优先级评分
 */
export async function createOrUpdatePriorityScore(
  topicId: string,
  data: Omit<PriorityScoreParams, 'topic_id'>
) {
  return requestClient.post<void>(
    `/api/v1/app/topics/${topicId}/priority`,
    { ...data, topic_id: topicId }
  );
}

/**
 * 获取优先级评分
 */
export async function getPriorityScore(topicId: string) {
  return requestClient.get<PriorityScore | null>(
    `/api/v1/app/topics/${topicId}/priority`
  );
}

/**
 * 删除优先级评分
 */
export async function deletePriorityScore(topicId: string) {
  return requestClient.delete<void>(`/api/v1/app/topics/${topicId}/priority`);
}

/**
 * 获取优先级排行榜
 */
export async function getPriorityRanking(limit = 50) {
  return requestClient.get<PriorityRankingItem[]>('/api/v1/app/priority/ranking', {
    params: { limit },
  });
}
