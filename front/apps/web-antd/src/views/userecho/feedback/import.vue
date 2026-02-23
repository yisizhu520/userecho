<script setup lang="ts">
import type { UploadProps } from 'ant-design-vue';
import type { ImportResult, ImportPreviewResult, ImportConfig } from '#/api';

import { ref, computed, h, resolveComponent, onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton } from '@vben/common-ui';

import { message, Modal } from 'ant-design-vue';
import {
  InboxOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue';

import { 
  previewImport, 
  importFeedbacksWithConfig, 
  downloadImportTemplate, 
  getBoardList 
} from '#/api';

const router = useRouter();

/**
 * 上传状态：idle -> parsing -> configuring -> importing -> success/error
 */
type UploadStatus = 'idle' | 'parsing' | 'configuring' | 'importing' | 'success' | 'error';
const uploadStatus = ref<UploadStatus>('idle');
const importResult = ref<ImportResult | null>(null);
const uploadProgress = ref(0);

/**
 * 预览和配置
 */
const previewResult = ref<ImportPreviewResult | null>(null);
const currentFile = ref<File | null>(null);
const importConfig = ref<ImportConfig>({
  default_board_id: undefined,
  author_type: 'customer',
  default_customer_name: undefined,
  default_source_platform: 'wechat',
  default_external_user_name: undefined,
});

// 看板列表
interface Board {
  id: string;
  name: string;
}
const boardList = ref<Board[]>([]);

// 加载看板列表
onMounted(async () => {
  try {
    const response = await getBoardList();
    // getBoardList 返回 { boards, total }，需要提取 boards 数组
    boardList.value = (response || []).map((b: any) => ({ id: b.id, name: b.name }));
  } catch (e) {
    console.error('Failed to load boards:', e);
  }
});

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
    return false;
  },
  onRemove: () => {
    handleReset();
  },
};

/**
 * 处理文件上传 - 第一阶段：预览
 */
const handleUpload = async (file: File) => {
  currentFile.value = file;
  uploadStatus.value = 'parsing';
  
  try {
    const preview = await previewImport(file);
    previewResult.value = preview;
    
    if (preview.status === 'error') {
      message.error(preview.message || '文件解析失败');
      uploadStatus.value = 'error';
      return;
    }
    
    // 判断是否需要配置
    if (preview.missing_optional.includes('看板名称') || preview.missing_optional.includes('客户名称')) {
      uploadStatus.value = 'configuring';
    } else {
      // 直接导入
      await doImport();
    }
  } catch (error: any) {
    uploadStatus.value = 'error';
    message.error(error.message || '文件解析失败');
  }
};

/**
 * 执行导入 - 第二阶段
 */
const doImport = async () => {
  if (!currentFile.value) return;
  
  uploadStatus.value = 'importing';
  uploadProgress.value = 0;
  
  const progressInterval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += 10;
    }
  }, 200);
  
  try {
    // 构建配置
    const config: ImportConfig = {
      author_type: importConfig.value.author_type,
    };
    
    if (previewResult.value?.missing_optional.includes('看板名称')) {
      config.default_board_id = importConfig.value.default_board_id;
    }
    
    if (previewResult.value?.missing_optional.includes('客户名称')) {
      if (importConfig.value.author_type === 'customer') {
        config.default_customer_name = importConfig.value.default_customer_name;
      } else {
        config.default_source_platform = importConfig.value.default_source_platform;
        config.default_external_user_name = importConfig.value.default_external_user_name;
      }
    }
    
    const result = await importFeedbacksWithConfig(currentFile.value, config);
    
    clearInterval(progressInterval);
    uploadProgress.value = 100;
    
    importResult.value = result;
    uploadStatus.value = 'success';
    
    if (result.failed === 0) {
      message.success(`成功导入 ${result.success} 条反馈！`);
    } else {
      message.warning(`导入完成：成功 ${result.success} 条，失败 ${result.failed} 条`);
    }
  } catch (error: any) {
    clearInterval(progressInterval);
    uploadStatus.value = 'error';
    message.error(error.message || '导入失败');
  }
};

/**
 * 校验是否可以导入
 */
const canImport = computed(() => {
  if (!previewResult.value) return false;
  
  // 如果缺少看板列，必须选择看板
  if (previewResult.value.missing_optional.includes('看板名称')) {
    if (!importConfig.value.default_board_id) return false;
  }
  
  // 如果缺少客户列，根据来源类型验证
  if (previewResult.value.missing_optional.includes('客户名称')) {
    if (importConfig.value.author_type === 'customer') {
      if (!importConfig.value.default_customer_name) return false;
    } else {
      if (!importConfig.value.default_external_user_name) return false;
    }
  }
  
  return true;
});

/**
 * 生成预览表格列
 */
const previewColumns = computed(() => {
  if (!previewResult.value?.detected_columns) return [];
  return previewResult.value.detected_columns.map(col => ({
    title: col,
    dataIndex: col,
    ellipsis: true,
  }));
});

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

  const ATable = resolveComponent('a-table') as any;

  Modal.info({
    title: '导入错误详情',
    width: 800,
    content: () =>
      h('div', [
        h('p', '以下数据导入失败，请检查后重新导入：'),
        h(ATable, {
          dataSource: errorList,
          columns: [
            { title: '行号', dataIndex: 'row', width: 80 },
            { title: '错误信息', dataIndex: 'error', width: 200 },
            { title: '反馈内容', dataIndex: 'content', ellipsis: true },
          ],
          size: 'small',
          pagination: false,
          scroll: { y: 400 },
        }),
        importResult.value?.has_more_errors
          ? h(
              'p',
              { style: { color: '#ff4d4f', marginTop: '12px' } },
              '* 仅显示前 20 条错误',
            )
          : null,
      ]),
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
 * 重置
 */
const handleReset = () => {
  fileList.value = [];
  uploadStatus.value = 'idle';
  importResult.value = null;
  previewResult.value = null;
  currentFile.value = null;
  uploadProgress.value = 0;
  importConfig.value = {
    default_board_id: undefined,
    author_type: 'customer',
    default_customer_name: undefined,
    default_source_platform: 'wechat',
    default_external_user_name: undefined,
  };
};

/**
 * 前往列表
 */
const goToList = () => {
  router.push('/app/feedback/list');
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
    <!-- 面包屑导航 -->
    <div class="page-header">
      <a-breadcrumb>
        <a-breadcrumb-item>
          <router-link to="/app/feedback/list">反馈管理</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>批量导入</a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <!-- 导入指南 -->
    <a-card title="📋 导入说明" class="mb-4">
      <a-steps :current="uploadStatus === 'idle' ? 0 : uploadStatus === 'configuring' ? 2 : 3" size="small">
        <a-step title="上传文件" description="上传 Excel 或 CSV 文件" />
        <a-step title="解析预览" description="系统自动检测列" />
        <a-step title="补全配置" description="配置缺失的字段" />
        <a-step title="完成导入" description="数据入库成功" />
      </a-steps>

      <a-divider />

      <div class="guide-content">
        <h4>🔖 必填字段：</h4>
        <ul>
          <li><strong>反馈内容</strong>：用户的原始反馈文本</li>
        </ul>

        <h4>📌 可选字段（可在上传后补全）：</h4>
        <ul>
          <li><strong>看板名称</strong>：反馈所属看板（缺失时可选择默认看板）</li>
          <li><strong>客户名称</strong>：必须提供客户名称</li>
          <li><strong>客户类型</strong>、<strong>提交时间</strong>、<strong>是否紧急</strong></li>
        </ul>

        <VbenButton type="primary" @click="handleDownloadTemplate" class="mt-4">
          <DownloadOutlined />
          下载标准模板
        </VbenButton>
      </div>
    </a-card>

    <!-- 上传区域 -->
    <a-card title="📤 上传文件">
      <!-- 初始状态：上传 -->
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

      <!-- 解析中 -->
      <div v-if="uploadStatus === 'parsing'" class="upload-progress">
        <a-spin size="large" />
        <p class="mt-4">正在解析文件...</p>
      </div>

      <!-- 配置面板 -->
      <div v-if="uploadStatus === 'configuring'" class="config-panel">
        <a-alert type="info" show-icon class="mb-4">
          <template #message>检测到以下列缺失，请补充配置</template>
          <template #description>
            缺失列：{{ previewResult?.missing_optional.join('、') }}
          </template>
        </a-alert>

        <!-- 数据预览 -->
        <a-card title="📊 数据预览（前 5 行）" size="small" class="mb-4">
          <a-table
            :dataSource="previewResult?.sample_data"
            :columns="previewColumns"
            size="small"
            :pagination="false"
            :scroll="{ x: 'max-content' }"
          />
          <p class="text-gray-500 mt-2">共 {{ previewResult?.total_rows }} 行数据</p>
        </a-card>

        <!-- 配置表单 -->
        <a-card title="⚙️ 补全配置" size="small">
          <a-form layout="vertical">
            <!-- 看板选择 -->
            <a-form-item
              v-if="previewResult?.missing_optional.includes('看板名称')"
              label="目标看板"
              required
            >
              <a-select
                v-model:value="importConfig.default_board_id"
                placeholder="请选择导入到哪个看板"
                :options="boardList.map(b => ({ value: b.id, label: b.name }))"
                style="width: 100%"
              />
            </a-form-item>

            <!-- 客户名称 -->
            <template v-if="previewResult?.missing_optional.includes('客户名称')">
              <a-form-item label="来源类型" required>
                <a-radio-group v-model:value="importConfig.author_type">
                  <a-radio value="customer">内部客户</a-radio>
                  <a-radio value="external">外部用户</a-radio>
                </a-radio-group>
              </a-form-item>
              
              <!-- 内部客户模式 -->
              <template v-if="importConfig.author_type === 'customer'">
                <a-form-item label="默认客户名称" required>
                  <a-input
                    v-model:value="importConfig.default_customer_name"
                    placeholder="输入客户名称（必填）"
                  />
                </a-form-item>
              </template>
              
              <!-- 外部用户模式 -->
              <template v-else>
                <a-form-item label="来源平台" required>
                  <a-select v-model:value="importConfig.default_source_platform" style="width: 100%">
                    <a-select-option value="wechat">微信</a-select-option>
                    <a-select-option value="xiaohongshu">小红书</a-select-option>
                    <a-select-option value="appstore">App Store</a-select-option>
                    <a-select-option value="weibo">微博</a-select-option>
                    <a-select-option value="other">其他</a-select-option>
                  </a-select>
                </a-form-item>
                <a-form-item label="用户名称" required>
                  <a-input
                    v-model:value="importConfig.default_external_user_name"
                    placeholder="外部用户名称（用于回访）"
                  />
                </a-form-item>
              </template>
            </template>
          </a-form>

          <div class="action-buttons mt-4">
            <VbenButton type="primary" @click="doImport" :disabled="!canImport">
              <SettingOutlined />
              确认导入
            </VbenButton>
            <VbenButton @click="handleReset">取消</VbenButton>
          </div>
        </a-card>
      </div>

      <!-- 导入中 -->
      <div v-if="uploadStatus === 'importing'" class="upload-progress">
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

.config-panel {
  padding: 16px;
}

.text-gray-500 {
  color: #666;
  font-size: 12px;
}
</style>
