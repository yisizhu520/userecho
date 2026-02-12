<script setup lang="ts">
import type { UploadProps } from 'ant-design-vue';
import type { ImportResult } from '#/api';

import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { message, Modal } from 'ant-design-vue';
import {
  InboxOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  LeftOutlined,
} from '@ant-design/icons-vue';

import { importFeedbacks, downloadImportTemplate } from '#/api';

const router = useRouter();

/**
 * 上传状态
 */
const uploadStatus = ref<'idle' | 'uploading' | 'success' | 'error'>('idle');
const importResult = ref<ImportResult | null>(null);
const uploadProgress = ref(0);

/**
 * 文件上传配置
 */
const fileList = ref<any[]>([]);

const uploadProps: UploadProps = {
  name: 'file',
  multiple: false,
  accept: '.xlsx,.xls,.csv',
  maxCount: 1,
  fileList: fileList.value,
  beforeUpload: (file) => {
    const isExcel = file.type === 'application/vnd.ms-excel' ||
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.name.endsWith('.csv');
    
    if (!isExcel) {
      message.error('只能上传 Excel 或 CSV 文件！');
      return false;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过 10MB！');
      return false;
    }

    handleUpload(file);
    return false; // 阻止自动上传
  },
  onRemove: () => {
    fileList.value = [];
    uploadStatus.value = 'idle';
    importResult.value = null;
  },
};

/**
 * 处理文件上传
 */
const handleUpload = async (file: File) => {
  try {
    uploadStatus.value = 'uploading';
    uploadProgress.value = 0;

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10;
      }
    }, 200);

    const result = await importFeedbacks(file);
    
    clearInterval(progressInterval);
    uploadProgress.value = 100;
    
    importResult.value = result;
    uploadStatus.value = 'success';
    
    if (result.failed === 0) {
      message.success(`成功导入 ${result.success} 条反馈！`);
    } else {
      message.warning(`导入完成：成功 ${result.success} 条，失败 ${result.failed} 条`);
      showErrorDetails();
    }
  } catch (error: any) {
    uploadStatus.value = 'error';
    message.error(error.message || '导入失败，请检查文件格式');
  }
};

/**
 * 显示错误详情
 */
const showErrorDetails = () => {
  if (!importResult.value?.errors) return;

  const errorList = importResult.value.errors.map((err) => ({
    row: err.row,
    error: err.error,
    content: err.content || '-',
  }));

  Modal.info({
    title: '导入错误详情',
    width: 800,
    content: () => (
      <div>
        <p>以下数据导入失败，请检查后重新导入：</p>
        <a-table
          dataSource={errorList}
          columns={[
            { title: '行号', dataIndex: 'row', width: 80 },
            { title: '错误信息', dataIndex: 'error', width: 200 },
            { title: '反馈内容', dataIndex: 'content', ellipsis: true },
          ]}
          size="small"
          pagination={false}
          scroll={{ y: 400 }}
        />
        {importResult.value?.has_more_errors && (
          <p style="color: #ff4d4f; margin-top: 12px;">
            * 仅显示前 10 条错误，完整错误列表请下载日志文件
          </p>
        )}
      </div>
    ),
  });
};

/**
 * 下载模板
 */
const handleDownloadTemplate = () => {
  downloadImportTemplate();
  message.success('模板下载中...');
};

/**
 * 重新导入
 */
const handleReset = () => {
  fileList.value = [];
  uploadStatus.value = 'idle';
  importResult.value = null;
  uploadProgress.value = 0;
};

/**
 * 前往列表
 */
const goToList = () => {
  router.push('/feedalyze/feedback/list');
};

/**
 * 计算统计信息
 */
const statistics = computed(() => {
  if (!importResult.value) return null;
  
  const { total, success, failed } = importResult.value;
  const successRate = total > 0 ? ((success / total) * 100).toFixed(1) : '0';
  
  return {
    total,
    success,
    failed,
    successRate,
  };
});
</script>

<template>
  <div class="import-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <VbenButton variant="ghost" @click="goToList">
        <LeftOutlined />
        返回列表
      </VbenButton>
      <h2 class="page-title">导入反馈数据</h2>
    </div>

    <!-- 导入指南 -->
    <a-card title="📋 导入说明" class="mb-4">
      <a-steps :current="1" size="small">
        <a-step title="下载模板" description="下载标准 Excel 模板" />
        <a-step title="填写数据" description="按照模板格式填写反馈数据" />
        <a-step title="上传文件" description="上传填好的 Excel 文件" />
        <a-step title="完成导入" description="系统自动处理并生成反馈" />
      </a-steps>

      <a-divider />

      <div class="guide-content">
        <h4>🔖 必填字段：</h4>
        <ul>
          <li><strong>反馈内容</strong>：用户的原始反馈文本（1-1000 字）</li>
          <li><strong>客户名称</strong>：可以是客户名称或匿名作者（如：小红书用户@xxx）</li>
        </ul>

        <h4>📌 可选字段：</h4>
        <ul>
          <li><strong>客户类型</strong>：normal（普通）/ paid（付费）/ major（大客户）/ strategic（战略客户）</li>
          <li><strong>提交时间</strong>：格式如 2025-01-01 或 2025-01-01 12:00:00</li>
          <li><strong>来源平台</strong>：如微信、小红书、知乎等</li>
          <li><strong>是否紧急</strong>：填写 是/否 或 true/false</li>
        </ul>

        <h4>⚠️ 注意事项：</h4>
        <ul>
          <li>支持 .xlsx、.xls、.csv 格式</li>
          <li>文件大小不超过 10MB</li>
          <li>建议单次导入不超过 500 条数据</li>
          <li>系统会自动去重，相同内容的反馈只会保留一条</li>
        </ul>

        <VbenButton type="primary" @click="handleDownloadTemplate" class="mt-4">
          <DownloadOutlined />
          下载标准模板
        </VbenButton>
      </div>
    </a-card>

    <!-- 上传区域 -->
    <a-card title="📤 上传文件">
      <div v-if="uploadStatus === 'idle'">
        <a-upload-dragger v-bind="uploadProps">
          <p class="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p class="ant-upload-hint">
            支持 .xlsx、.xls、.csv 格式，单个文件不超过 10MB
          </p>
        </a-upload-dragger>
      </div>

      <!-- 上传中 -->
      <div v-if="uploadStatus === 'uploading'" class="upload-progress">
        <a-spin size="large" />
        <p class="mt-4">正在导入数据，请稍候...</p>
        <a-progress :percent="uploadProgress" status="active" />
      </div>

      <!-- 上传成功 -->
      <div v-if="uploadStatus === 'success' && statistics" class="upload-result success">
        <CheckCircleOutlined class="result-icon success-icon" />
        <h3>导入成功！</h3>
        
        <a-row :gutter="16" class="statistics mt-4">
          <a-col :span="6">
            <a-statistic title="总计" :value="statistics.total" />
          </a-col>
          <a-col :span="6">
            <a-statistic 
              title="成功" 
              :value="statistics.success" 
              :value-style="{ color: '#3f8600' }"
            />
          </a-col>
          <a-col :span="6">
            <a-statistic 
              title="失败" 
              :value="statistics.failed"
              :value-style="{ color: statistics.failed > 0 ? '#cf1322' : undefined }"
            />
          </a-col>
          <a-col :span="6">
            <a-statistic 
              title="成功率" 
              :value="statistics.successRate"
              suffix="%"
            />
          </a-col>
        </a-row>

        <div class="action-buttons mt-4">
          <VbenButton type="primary" @click="goToList">
            查看反馈列表
          </VbenButton>
          <VbenButton @click="handleReset">
            继续导入
          </VbenButton>
          <VbenButton 
            v-if="statistics.failed > 0"
            variant="outline"
            @click="showErrorDetails"
          >
            查看错误详情
          </VbenButton>
        </div>
      </div>

      <!-- 上传失败 -->
      <div v-if="uploadStatus === 'error'" class="upload-result error">
        <CloseCircleOutlined class="result-icon error-icon" />
        <h3>导入失败</h3>
        <p class="error-message">文件解析失败，请检查文件格式是否正确</p>
        
        <div class="action-buttons mt-4">
          <VbenButton type="primary" @click="handleReset">
            重新上传
          </VbenButton>
          <VbenButton variant="outline" @click="handleDownloadTemplate">
            下载模板
          </VbenButton>
        </div>
      </div>
    </a-card>

    <!-- 提示信息 -->
    <a-alert
      message="💡 提示"
      description="导入后，系统会自动为反馈生成 AI 摘要。您可以在反馈列表中点击「AI 智能聚类」按钮，将相似的反馈自动归类为需求主题。"
      type="info"
      show-icon
      class="mt-4"
    />
  </div>
</template>

<style scoped>
.import-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.guide-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #1890ff;
}

.guide-content ul {
  margin-left: 20px;
}

.guide-content li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.upload-progress {
  text-align: center;
  padding: 60px 0;
}

.upload-result {
  text-align: center;
  padding: 60px 0;
}

.result-icon {
  font-size: 72px;
}

.success-icon {
  color: #52c41a;
}

.error-icon {
  color: #ff4d4f;
}

.upload-result h3 {
  margin-top: 16px;
  font-size: 24px;
}

.error-message {
  color: #666;
  margin-top: 12px;
}

.statistics {
  max-width: 600px;
  margin: 0 auto;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
