<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Card, Select, Spin, message } from 'ant-design-vue';

import {
  exportReport,
  getInsightTaskStatus,
  type WeeklyReportResponse,
} from '#/api/userecho/insight';

const loading = ref(false);
const timeRange = ref<'this_week' | 'this_month'>('this_week');
const reportData = ref<WeeklyReportResponse | null>(null);
const loadingTip = ref('正在生成报告...');

let pollingTimer: ReturnType<typeof setTimeout> | null = null;

// 加载报告（异步）
async function loadReport() {
  try {
    loading.value = true;
    loadingTip.value = '正在提交任务...';
    
    // 提交异步任务
    const response = await exportReport(timeRange.value, 'markdown');
    
    // 开始轮询任务状态
    loadingTip.value = '正在生成报告...';
    await pollTaskStatus(response.task_id);
  } catch (error) {
    console.error('Failed to load report:', error);
    message.error('加载报告失败');
    loading.value = false;
  }
}

// 轮询任务状态
async function pollTaskStatus(taskId: string) {
  const maxAttempts = 60; // 最多轮询 60 次（60 秒）
  let attempts = 0;
  
  const poll = async () => {
    try {
      attempts++;
      const status = await getInsightTaskStatus(taskId);
      
      if (status.state === 'SUCCESS') {
        // 任务成功
        if (status.result) {
          reportData.value = {
            markdown: status.result.content,
            data: {},
            generated_at: new Date().toISOString(),
          };
          message.success('报告生成成功');
        }
        loading.value = false;
        return;
      } else if (status.state === 'FAILURE') {
        // 任务失败
        message.error(`报告生成失败: ${status.error || '未知错误'}`);
        loading.value = false;
        return;
      } else if (status.state === 'PROGRESS' && status.progress) {
        // 更新进度提示
        loadingTip.value = status.progress.status || '正在生成报告...';
      }
      
      // 继续轮询
      if (attempts < maxAttempts) {
        pollingTimer = setTimeout(poll, 1000); // 每秒轮询一次
      } else {
        message.error('报告生成超时，请稍后重试');
        loading.value = false;
      }
    } catch (error) {
      console.error('Failed to poll task status:', error);
      // 继续轮询，除非达到最大次数
      if (attempts < maxAttempts) {
        pollingTimer = setTimeout(poll, 1000);
      } else {
        message.error('查询任务状态失败');
        loading.value = false;
      }
    }
  };
  
  // 开始轮询
  poll();
}

// 导出为文本文件
function exportAsFile() {
  if (!reportData.value) return;

  const blob = new Blob([reportData.value.markdown], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `report-${timeRange.value}-${new Date().toISOString().split('T')[0]}.md`;
  a.click();
  URL.revokeObjectURL(url);

  message.success('报告已导出');
}

// 复制到剪贴板
async function copyToClipboard() {
  if (!reportData.value) return;

  try {
    await navigator.clipboard.writeText(reportData.value.markdown);
    message.success('已复制到剪贴板');
  } catch (error) {
    message.error('复制失败');
  }
}

onMounted(() => {
  loadReport();
});

// 清理定时器
onUnmounted(() => {
  if (pollingTimer) {
    clearTimeout(pollingTimer);
  }
});
</script>

<template>
  <div class="insights-report">
    <Card title="📊 洞察报告" :bordered="false">
      <template #extra>
        <div class="report-actions">
          <Select
            v-model:value="timeRange"
            style="width: 120px; margin-right: 8px;"
            @change="loadReport"
          >
            <Select.Option value="this_week">本周</Select.Option>
            <Select.Option value="this_month">本月</Select.Option>
          </Select>

          <VbenButton variant="outline" @click="copyToClipboard" :disabled="loading">
            <span class="iconify lucide--copy" />
            复制
          </VbenButton>

          <VbenButton variant="outline" class="ml-2" @click="exportAsFile" :disabled="loading">
            <span class="iconify lucide--download" />
            导出
          </VbenButton>

          <VbenButton type="primary" class="ml-2" @click="loadReport" :loading="loading">
            <span class="iconify lucide--refresh-cw" />
            刷新
          </VbenButton>
        </div>
      </template>

      <div v-if="loading" class="text-center py-8">
        <Spin size="large" :tip="loadingTip" />
      </div>

      <div v-else-if="reportData" class="report-content">
        <!-- Markdown 渲染 -->
        <div class="markdown-body" v-html="renderMarkdown(reportData.markdown)"></div>
      </div>

      <div v-else class="text-center py-8">
        <p class="text-gray-500">加载失败，请稍后重试</p>
      </div>
    </Card>
  </div>
</template>

<script lang="ts">
// 简单的 Markdown 渲染（实际项目中应使用 markdown-it 等库）
function renderMarkdown(markdown: string): string {
  let html = markdown;

  // 标题
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // 加粗
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // 列表
  html = html.replace(/^\- (.*)$/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // 换行
  html = html.replace(/\n/g, '<br>');

  return html;
}

// 导出函数供模板使用
export { renderMarkdown };
</script>

<style scoped lang="scss">
.insights-report {
  padding: 20px;
}

.report-actions {
  display: flex;
  align-items: center;
}

.report-content {
  padding: 20px;
  background: #fafafa;
  border-radius: 4px;
  min-height: 400px;
}

.markdown-body {
  line-height: 1.6;

  :deep(h1) {
    margin-top: 24px;
    margin-bottom: 16px;
    font-size: 2em;
    font-weight: 600;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
  }

  :deep(h2) {
    margin-top: 24px;
    margin-bottom: 16px;
    font-size: 1.5em;
    font-weight: 600;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
  }

  :deep(h3) {
    margin-top: 24px;
    margin-bottom: 16px;
    font-size: 1.25em;
    font-weight: 600;
  }

  :deep(ul) {
    margin-top: 0;
    margin-bottom: 16px;
    padding-left: 2em;
  }

  :deep(li) {
    margin-top: 0.25em;
  }

  :deep(strong) {
    font-weight: 600;
  }
}
</style>
