/**
 * 工作台统计 API
 */

import { requestClient } from '#/api/request';

/**
 * 待决策主题数据结构
 */
export interface PendingDecision {
  id: string;
  title: string;
  category: string;
  status: string;
  priority_score: number;
  feedback_count: number;
  urgent_ratio: number;
  strategic_keywords_matched: string[];
  last_feedback_days: number | null;
  total_mrr: number;
  affected_customer_count: number;
}

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
  customer_stats: {
    total: number;
    new_count: number;
    active_7d: number;
    type_distribution: Array<{
      type: string;
      name: string;
      count: number;
    }>;
    total_mrr: number;
    top_customers: Array<{
      id: string;
      name: string;
      customer_type: string;
      mrr: number;
      feedback_count: number;
    }>;
  };
  urgent_topics: Array<{
    id: string;
    title: string;
    feedback_count: number;
    priority_score: number | null;
    category: string;
    status: string;
  }>;
  pending_decisions: PendingDecision[];
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
  conversion_funnel: {
    total_feedbacks: number;
    clustered: number;
    pending_review: number;
    planned: number;
    in_progress: number;
    completed: number;
    conversion_rates: {
      clustering_rate: number;
      review_rate: number;
      planning_rate: number;
      completion_rate: number;
    };
  };
}

/**
 * 获取工作台统计数据
 */
export async function getDashboardStats() {
  return requestClient.get<DashboardStats>('/api/v1/app/dashboard/stats');
}

/**
 * 我的反馈统计数据结构
 */
export interface MyFeedbacksStats {
  summary: {
    submitted_count: number;
    in_progress_count: number;
    completed_count: number;
  };
  recent_updates: Array<{
    feedback_id: string;
    content_summary: string;
    topic_id: string | null;
    topic_title: string | null;
    topic_status: string | null;
    updated_at: string;
  }>;
}

/**
 * 获取我录入的反馈统计
 */
export async function getMyFeedbacks(limit: number = 10) {
  return requestClient.get<MyFeedbacksStats>(
    `/api/v1/app/dashboard/my-feedbacks?limit=${limit}`,
  );
}

/**
 * 通知统计数据结构
 */
export interface NotificationStats {
  total_notifications: number;
  pending_count: number;
  generated_count: number;
  sent_count: number;
  generation_rate: number;
  notification_rate: number;
  recent_notifications: Array<{
    id: string;
    recipient_name: string;
    topic_title: string;
    notified_at: string | null;
    status: string;
  }>;
}

/**
 * 获取通知统计数据
 */
export async function getNotificationStats() {
  return requestClient.get<NotificationStats>(
    '/api/v1/app/dashboard/notification-stats',
  );
}

