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
  created_time: string;
  updated_time: string;
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
 * 创建/更新优先级评分
 */
export async function createOrUpdatePriorityScore(data: PriorityScoreParams) {
  return requestClient.post<PriorityScore>('/api/v1/app/priority/score', data);
}

/**
 * 获取优先级排行榜
 */
export async function getPriorityRanking(limit = 50) {
  return requestClient.get<PriorityRankingItem[]>('/api/v1/app/priority/ranking', {
    params: { limit },
  });
}
