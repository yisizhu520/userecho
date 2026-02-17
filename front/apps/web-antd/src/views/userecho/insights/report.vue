<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';
import { Modal, Select, Spin, message, Input, Tag, Tooltip } from 'ant-design-vue';
import html2canvas from 'html2canvas';

import {
  exportReport,
  getInsight,
  getInsightTaskStatus,
  sendReportEmail,
  type WeeklyReportResponse,
} from '#/api/userecho/insight';

const loading = ref(false);
const router = useRouter();
const timeRange = ref<'this_week' | 'this_month'>('this_week');
const reportData = ref<WeeklyReportResponse | null>(null);
const loadingTip = ref('正在生成报告...');
const reportRef = ref<HTMLElement | null>(null);

// 邮件弹窗状态
const emailModalVisible = ref(false);
const emailRecipients = ref<string[]>([]);
const emailInput = ref('');
const sendingEmail = ref(false);

let pollingTimer: ReturnType<typeof setTimeout> | null = null;

// 计算属性：日期范围显示
const dateRangeText = computed(() => {
  const end = new Date();
  const start = new Date();
  if (timeRange.value === 'this_week') {
    const day = start.getDay() || 7;
    start.setDate(start.getDate() - day + 1);
  } else {
    start.setDate(1);
  }
  return `${start.getMonth() + 1}月${start.getDate()}日 - ${end.getMonth() + 1}月${end.getDate()}日`;
});

// 计算变化趋势
const feedbackTrend = computed(() => {
  const percent = reportData.value?.data?.change_percent || 0;
  return {
    value: Math.abs(percent),
    isUp: percent >= 0,
    color: percent >= 0 ? '#10b981' : '#ef4444',
    icon: percent >= 0 ? '↑' : '↓',
  };
});

// 完成率计算
const completionRate = computed(() => {
  const data = reportData.value?.data;
  if (!data) return { value: 0, status: 'normal' };
  const total = data.new_topics_count + data.completed_count;
  if (total === 0) return { value: 0, status: 'normal' };
  const rate = Math.round((data.completed_count / total) * 100);
  return {
    value: rate,
    status: rate >= 60 ? 'good' : rate >= 40 ? 'normal' : 'warning',
  };
});

// 加载报告（使用缓存）
async function loadReport(forceRefresh = false) {
  try {
    loading.value = true;
    loadingTip.value = '正在加载报告...';
    
    if (forceRefresh) {
      // 强制重新生成：使用 Celery 异步任务
      reportData.value = null;
      loadingTip.value = '正在重新生成报告...';
      const response = await exportReport(timeRange.value, 'markdown');
      loadingTip.value = '正在分析数据...';
      await pollTaskStatus(response.task_id);
    } else {
      // 优先使用缓存
      const result = await getInsight('weekly_report', timeRange.value, false);
      if (result) {
        reportData.value = result as unknown as WeeklyReportResponse;
      }
      loading.value = false;
    }
  } catch (error) {
    console.error('Failed to load report:', error);
    message.error('加载报告失败');
    loading.value = false;
  }
}

// 轮询任务状态
async function pollTaskStatus(taskId: string) {
  const maxAttempts = 60;
  let attempts = 0;
  
  const poll = async () => {
    try {
      attempts++;
      const status = await getInsightTaskStatus(taskId);
      
      if (status.state === 'SUCCESS') {
        if (status.result) {
          reportData.value = status.result as unknown as WeeklyReportResponse;
          message.success('报告生成成功');
        }
        loading.value = false;
        return;
      } else if (status.state === 'FAILURE') {
        message.error(`报告生成失败: ${status.error || '未知错误'}`);
        loading.value = false;
        return;
      } else if (status.state === 'PROGRESS' && status.progress) {
        loadingTip.value = status.progress.status || '正在生成报告...';
      }
      
      if (attempts < maxAttempts) {
        pollingTimer = setTimeout(poll, 1000);
      } else {
        message.error('报告生成超时，请稍后重试');
        loading.value = false;
      }
    } catch (error) {
      console.error('Failed to poll task status:', error);
      if (attempts < maxAttempts) {
        pollingTimer = setTimeout(poll, 1000);
      } else {
        message.error('查询任务状态失败');
        loading.value = false;
      }
    }
  };
  
  poll();
}

// 导出为图片
async function exportAsImage() {
  if (!reportRef.value) return;
  
  try {
    message.loading({ content: '正在生成图片...', key: 'export' });
    
    const canvas = await html2canvas(reportRef.value, {
      backgroundColor: '#ffffff',
      scale: 2,
      useCORS: true,
      logging: false,
    });
    
    const link = document.createElement('a');
    link.download = `周报-${new Date().toISOString().split('T')[0]}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    
    message.success({ content: '图片已下载', key: 'export' });
  } catch (error) {
    console.error('Failed to export image:', error);
    message.error({ content: '导出失败', key: 'export' });
  }
}

// 邮件相关方法
function showEmailModal() {
  emailModalVisible.value = true;
}

function handleEmailInputConfirm() {
  const email = emailInput.value.trim();
  if (email && !emailRecipients.value.includes(email)) {
    // 简单的邮箱验证
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      emailRecipients.value.push(email);
      emailInput.value = '';
    } else {
      message.warning('请输入有效的邮箱地址');
    }
  }
}

function removeRecipient(email: string) {
  emailRecipients.value = emailRecipients.value.filter(e => e !== email);
}

async function handleSendEmail() {
  if (emailRecipients.value.length === 0) {
    message.warning('请至少添加一个收件人');
    return;
  }
  
  try {
    sendingEmail.value = true;
    await sendReportEmail({
      recipients: emailRecipients.value,
      time_range: timeRange.value,
    });
    message.success('邮件发送成功');
    emailModalVisible.value = false;
    emailRecipients.value = [];
  } catch (error) {
    console.error('Failed to send email:', error);
    message.error('邮件发送失败');
  } finally {
    sendingEmail.value = false;
  }
}

onMounted(() => {
  loadReport();
});

onUnmounted(() => {
  if (pollingTimer) {
    clearTimeout(pollingTimer);
  }
});
</script>

<template>
  <div class="weekly-brief p-6 max-w-[900px] mx-auto">
    <!-- 操作栏 -->
    <div class="actions-bar mb-6 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Select
          v-model:value="timeRange"
          style="width: 120px;"
          @change="() => loadReport(false)"
        >
          <Select.Option value="this_week">本周</Select.Option>
          <Select.Option value="this_month">本月</Select.Option>
        </Select>
        <VbenButton variant="ghost" size="small" @click="() => loadReport(true)" :loading="loading">
          <span class="iconify lucide--refresh-cw mr-1" />
          重新生成
        </VbenButton>
      </div>
      
      <div class="flex items-center gap-2">
        <Tooltip title="下载图片">
          <VbenButton variant="outline" size="small" @click="exportAsImage" :disabled="loading || !reportData">
            <span class="iconify lucide--image-down" />
          </VbenButton>
        </Tooltip>
        <Tooltip title="发送邮件">
          <VbenButton variant="outline" size="small" @click="showEmailModal" :disabled="loading || !reportData">
            <span class="iconify lucide--mail" />
          </VbenButton>
        </Tooltip>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state h-[500px] flex flex-col justify-center items-center bg-gray-50 rounded-2xl">
      <Spin size="large" />
      <p class="mt-4 text-gray-500">{{ loadingTip }}</p>
    </div>

    <!-- 报告内容 -->
    <div v-else-if="reportData" ref="reportRef" class="report-card bg-white rounded-2xl shadow-lg overflow-hidden">
      <!-- 头部 -->
      <div class="report-header bg-emerald-900 text-white p-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold mb-2">周度洞察简报</h1>
            <p class="text-emerald-300 text-sm">{{ dateRangeText }}</p>
          </div>
          <div class="text-right">
            <div class="text-xs text-emerald-300 uppercase tracking-wide">Feedalyze</div>
            <div class="text-xs text-emerald-400">AI Insights</div>
          </div>
        </div>
      </div>

      <!-- 核心洞察 -->
      <div class="insight-highlight p-6 bg-gray-50 border-b border-gray-100">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-10 h-10 bg-emerald-800 rounded-lg flex items-center justify-center">
            <span class="iconify lucide--lightbulb text-emerald-200 text-lg" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 mb-1 text-sm">本周核心洞察</h3>
            <p class="text-gray-700 leading-relaxed">
              {{ reportData.data?.top_topics?.[0] 
                ? `"${reportData.data.top_topics[0].title}" 影响 ${reportData.data.top_topics[0].customer_count} 位客户，建议优先处理。`
                : '本周暂无高优先级需求需要处理。' 
              }}
            </p>
          </div>
        </div>
      </div>

      <!-- 关键变化 -->
      <div class="key-metrics p-6">
        <h3 class="font-semibold text-gray-900 mb-4 text-sm">关键变化</h3>
        <div class="grid grid-cols-3 gap-4">
          <!-- 反馈量 -->
          <div class="metric-item bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500 text-sm">反馈量</span>
              <span 
                class="text-xs font-medium px-2 py-0.5 rounded-full"
                :style="{ backgroundColor: feedbackTrend.isUp ? '#dcfce7' : '#fee2e2', color: feedbackTrend.color }"
              >
                {{ feedbackTrend.icon }} {{ feedbackTrend.value }}%
              </span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ reportData.data?.new_feedbacks_count || 0 }}</div>
            <div class="text-xs text-gray-400 mt-1">vs 上周</div>
          </div>

          <!-- 满意度 (模拟数据，实际需要从 sentiment 获取) -->
          <div class="metric-item bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500 text-sm">新增需求</span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ reportData.data?.new_topics_count || 0 }}</div>
            <div class="text-xs text-gray-400 mt-1">个需求</div>
          </div>

          <!-- 完成率 -->
          <div class="metric-item bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500 text-sm">完成率</span>
              <span 
                class="text-xs font-medium px-2 py-0.5 rounded-full"
                :class="{
                  'bg-green-100 text-green-700': completionRate.status === 'good',
                  'bg-gray-100 text-gray-600': completionRate.status === 'normal',
                  'bg-red-100 text-red-700': completionRate.status === 'warning',
                }"
              >
                {{ completionRate.status === 'good' ? '良好' : completionRate.status === 'warning' ? '需关注' : '正常' }}
              </span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ completionRate.value }}%</div>
            <div class="text-xs text-gray-400 mt-1">{{ reportData.data?.completed_count || 0 }} 个已完成</div>
          </div>
        </div>
      </div>

      <!-- 风险预警 -->
      <div v-if="reportData.data?.top_topics?.some(t => t.status === 'pending')" class="risk-alert p-6 border-t border-gray-100">
        <h3 class="font-semibold text-gray-900 mb-4 text-sm">待处理事项</h3>
        <div class="space-y-3">
          <div 
            v-for="topic in reportData.data.top_topics.filter(t => t.status === 'pending').slice(0, 2)"
            :key="topic.id"
            class="risk-item flex items-center gap-3 bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors border border-gray-200"
            @click="router.push(`/app/topic/detail/${topic.id}`)"
          >
            <div class="flex-shrink-0 w-8 h-8 bg-amber-100 rounded flex items-center justify-center">
              <span class="iconify lucide--alert-circle text-amber-600" />
            </div>
            <div class="flex-1">
              <div class="font-medium text-gray-900 text-sm">{{ topic.title }}</div>
              <div class="text-xs text-gray-500">影响 {{ topic.customer_count }} 位客户</div>
            </div>
            <span class="iconify lucide--chevron-right text-gray-400" />
          </div>
        </div>
      </div>

      <!-- 无风险提示 -->
      <div v-else class="no-risk p-6 border-t border-gray-100">
        <div class="flex items-center gap-3 bg-green-50 rounded-lg p-4">
          <span class="text-green-500 text-lg">✅</span>
          <div>
            <div class="font-medium text-green-800">太棒了！</div>
            <div class="text-sm text-green-600">目前没有高风险的积压需求。</div>
          </div>
        </div>
      </div>

      <!-- 页脚 -->
      <div class="report-footer p-4 bg-gray-50 text-center text-xs text-gray-400">
        Generated by Feedalyze AI · {{ new Date().toLocaleDateString() }}
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state h-[500px] flex flex-col justify-center items-center text-center bg-gray-50 rounded-2xl">
      <span class="iconify lucide--file-question text-6xl text-gray-300 mb-4" />
      <h3 class="text-lg font-medium text-gray-900">准备生成报告</h3>
      <p class="text-gray-500 mt-2">点击上方刷新按钮开始分析最新数据</p>
    </div>

    <!-- 邮件发送弹窗 -->
    <Modal
      v-model:open="emailModalVisible"
      title="发送报告邮件"
      :confirmLoading="sendingEmail"
      okText="发送"
      cancelText="取消"
      @ok="handleSendEmail"
    >
      <div class="py-4">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">收件人</label>
          <div class="flex flex-wrap gap-2 mb-2">
            <Tag 
              v-for="email in emailRecipients" 
              :key="email" 
              closable 
              @close="removeRecipient(email)"
            >
              {{ email }}
            </Tag>
          </div>
          <Input
            v-model:value="emailInput"
            placeholder="输入邮箱地址后按回车添加"
            @pressEnter="handleEmailInputConfirm"
            @blur="handleEmailInputConfirm"
          />
        </div>
        <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
          <p class="font-medium mb-2">邮件内容预览</p>
          <p>📊 {{ timeRange === 'this_week' ? '本周' : '本月' }}洞察简报</p>
          <p>• 新增反馈：{{ reportData?.data?.new_feedbacks_count || 0 }} 条</p>
          <p>• 新增需求：{{ reportData?.data?.new_topics_count || 0 }} 个</p>
          <p>• 已完成：{{ reportData?.data?.completed_count || 0 }} 个</p>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped lang="scss">
.weekly-brief {
  min-height: 100vh;
  background-color: #f8fafc;
}

.report-card {
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.report-header {
  position: relative;
}

.metric-item {
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
}

.risk-item {
  // Clean border style
}
</style>
