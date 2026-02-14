/**
 * 工作台统计 API
 */

import { requestClient } from '#/api/request';

/**
 * 工作台统计数据结构
 */
export interface DashboardStats {
  feedback_stats: {
    total: number;
    pending: number;
    weekly_count: number;
  };
  topic_stats: {
    total: number;
    pending: number;
    completed: number;
    weekly_count: number;
  };
  urgent_topics: Array<{
    id: string;
    title: string;
    feedback_count: number;
    priority_score: number | null;
    category: string;
    status: string;
  }>;
  top_topics: Array<{
    id: string;
    title: string;
    feedback_count: number;
    category: string;
    status: string;
  }>;
  weekly_trend: Array<{
    date: string;
    count: number;
  }>;
  tag_distribution: Array<{
    category: string;
    name: string;
    topic_count: number;
    feedback_count: number;
    avg_priority_score: number | null;
  }>;
}

/**
 * 获取工作台统计数据
 */
export async function getDashboardStats() {
  return requestClient.get<DashboardStats>('/api/v1/app/dashboard/stats');
}
