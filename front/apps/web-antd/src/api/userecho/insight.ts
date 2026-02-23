/**
 * 洞察 API
 */
import { requestClient } from '#/api/request';

// 洞察类型
export type InsightType = 'priority_suggestion' | 'high_risk' | 'weekly_report' | 'sentiment_trend';

// 时间范围
export type TimeRange = 'this_week' | 'this_month' | 'custom';

// 优先级建议
export interface PrioritySuggestion {
  topic_id: string;
  title: string;
  reason: string;
  urgency_level: 'critical' | 'high' | 'medium' | 'low';
  estimated_roi: number;
  suggested_action: string;
  category: string;
  feedback_count: number;
}

export interface PrioritySuggestionsResponse {
  top_recommendations: PrioritySuggestion[];
  summary: string;
  generated_at: string;
}

// 高风险需求
export interface HighRiskTopic {
  topic_id: string;
  title: string;
  risk_level: 'critical' | 'high' | 'medium';
  affected_customers: Array<{
    name: string;
    type: string;
  }>;
  days_unresolved: number;
  priority_score: number;
  suggested_action: string;
}

export interface HighRiskResponse {
  high_risk_topics: HighRiskTopic[];
  summary: string;
  generated_at: string;
}

// 满意度趋势
export interface SentimentTrend {
  this_week: {
    positive: number;
    neutral: number;
    negative: number;
    positive_rate: number;
  };
  last_week: {
    positive: number;
    neutral: number;
    negative: number;
    positive_rate: number;
  };
  change: string;
}

export interface SentimentTrendResponse {
  sentiment_trend: SentimentTrend;
  summary: string;
  negative_topics: Array<{
    topic_id: string;
    title: string;
    negative_count: number;
  }>;
  generated_at: string;
}

// 周报数据
export interface TopTopic {
  id: string;
  title: string;
  status: string;
  customer_count: number;
  score: number;
  estimated_days: number;
  category: string;
}

export interface WeeklyReportData {
  new_feedbacks_count: number;
  change_percent: number;
  new_topics_count: number;
  completed_count: number;
  tag_distribution: [string, number][];
  top_topics: TopTopic[];
  total_topics: number;
}

// 周报数据
export interface WeeklyReportResponse {
  markdown: string;
  data: WeeklyReportData;
  generated_at: string;
  task_id?: string;
  status?: string;
}

// 异步任务响应
export interface TaskResponse {
  status: 'accepted';
  task_id: string;
}

// 异步生成中的响应
export interface AsyncGeneratingResponse {
  status: 'generating';
  task_id: string;
}

// 任务状态响应
export interface TaskStatusResponse {
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'RETRY';
  result?: {
    // 新结构：同时包含 markdown 和 data
    markdown?: string;
    data?: WeeklyReportData;
    generated_at?: string;
    format?: string;
    status?: string;
    // 兼容旧结构 (可选)
    content?: string;
  };
  error?: string;
  progress?: {
    current: number;
    total: number;
    status: string;
  };
}

// 工作台洞察
export interface DashboardInsights {
  priority_suggestions: PrioritySuggestionsResponse | null;
  high_risk_topics: HighRiskResponse | null;
  sentiment_summary: SentimentTrendResponse | null;
}

/**
 * 获取单个洞察
 * 
 * 返回类型：
 * - weekly_report: 可能返回 WeeklyReportResponse（缓存命中）或 AsyncGeneratingResponse（无缓存，触发异步生成）
 * - 其他类型: 直接返回对应的响应类型
 */
export async function getInsight(
  insightType: 'weekly_report',
  timeRange?: TimeRange,
  forceRefresh?: boolean,
): Promise<WeeklyReportResponse | AsyncGeneratingResponse>;
export async function getInsight(
  insightType: 'priority_suggestion',
  timeRange?: TimeRange,
  forceRefresh?: boolean,
): Promise<PrioritySuggestionsResponse>;
export async function getInsight(
  insightType: 'high_risk',
  timeRange?: TimeRange,
  forceRefresh?: boolean,
): Promise<HighRiskResponse>;
export async function getInsight(
  insightType: 'sentiment_trend',
  timeRange?: TimeRange,
  forceRefresh?: boolean,
): Promise<SentimentTrendResponse>;
export async function getInsight(
  insightType: InsightType,
  timeRange: TimeRange = 'this_week',
  forceRefresh: boolean = false,
) {
  return requestClient.get(`/api/v1/app/insights/${insightType}`, {
    params: {
      time_range: timeRange,
      force_refresh: forceRefresh,
    },
  });
}

/**
 * 获取工作台洞察（批量）
 */
export async function getDashboardInsights() {
  return requestClient.get<DashboardInsights>('/api/v1/app/insights/dashboard/summary');
}

/**
 * 导出周报/月报（异步）
 */
export async function exportReport(
  timeRange: TimeRange = 'this_week',
  format: 'markdown' | 'html' = 'markdown',
) {
  return requestClient.post<TaskResponse>('/api/v1/app/insights/report/export', {
    params: {
      time_range: timeRange,
      format,
    },
  });
}

/**
 * 查询洞察生成任务状态
 */
export async function getInsightTaskStatus(taskId: string) {
  return requestClient.get<TaskStatusResponse>(`/api/v1/app/insights/task/${taskId}`);
}

/**
 * 忽略洞察
 */
export async function dismissInsight(insightId: string, reason: string) {
  return requestClient.post(`/api/v1/app/insights/${insightId}/dismiss`, {
    params: {
      reason,
    },
  });
}

// 发送报告邮件请求
export interface SendReportEmailRequest {
  recipients: string[];
  time_range: TimeRange;
}

/**
 * 发送报告邮件
 */
export async function sendReportEmail(data: SendReportEmailRequest) {
  return requestClient.post('/api/v1/app/insights/report/send-email', data);
}

// 报告时间段
export interface ReportPeriod {
  period_key: string;    // 唯一标识：2026-W02 或 2026-01
  start_date: string;    // 开始日期：2026-01-06
  end_date: string;      // 结束日期：2026-01-12
  label: string;         // 显示标签：本周 / 上周 / 12月第4周
  sub_label: string;     // 副标签：1/6 - 1/12
  has_cache: boolean;    // 是否有缓存
  is_current: boolean;   // 是否当前周期
  time_range: string;    // 用于查询报告的时间范围参数
}

/**
 * 获取报告时间段列表
 */
export async function getReportPeriods(
  periodType: 'week' | 'month' = 'week',
  limit: number = 12,
) {
  return requestClient.get<ReportPeriod[]>('/api/v1/app/insights/report/periods', {
    params: {
      period_type: periodType,
      limit,
    },
  });
}
