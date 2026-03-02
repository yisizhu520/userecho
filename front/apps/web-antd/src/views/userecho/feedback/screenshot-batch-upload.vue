<template>
  <div class="screenshot-batch-upload-page">
    <!-- 面包屑导航 -->
    <div class="page-header">
      <a-breadcrumb>
        <a-breadcrumb-item>
          <router-link to="/app/feedback/list">反馈管理</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>批量截图识别</a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <!-- 导入指南 -->
    <Card title="📋 批量识别说明" class="mb-4">
      <a-steps :current="currentStep" size="small" class="mb-4">
        <a-step title="上传截图" description="批量选择截图文件" />
        <a-step title="配置信息" description="设置默认看板和来源" />
        <a-step title="AI 识别" description="自动识别反馈内容" />
        <a-step title="完成" description="创建反馈成功" />
      </a-steps>

      <a-divider />

      <div class="guide-content">
        <h4>🎯 使用场景：</h4>
        <ul>
          <li>从微信、小红书等平台收集了大量用户反馈截图</li>
          <li>需要快速批量录入，无需逐个审核</li>
          <li>反馈来源和看板相同，可统一配置</li>
        </ul>

        <h4>⚙️ 工作原理：</h4>
        <ul>
          <li><strong>预设配置</strong>：先配置目标看板、来源信息（类似 Excel 导入）</li>
          <li><strong>AI 识别</strong>：自动提取反馈内容和用户名</li>
          <li><strong>自动创建</strong>：高置信度直接创建，低置信度标记待审核</li>
        </ul>

        <a-alert
          message="💡 提示"
          description="如需逐个审核内容，请使用「截图识别」功能（单张模式）"
          type="info"
          show-icon
          class="mt-3"
        />
      </div>
    </Card>

    <!-- 主内容卡片 -->
    <Card title="📤 批量上传截图">
      <!-- 步骤1：上传截图 -->
      <template v-if="uploadStatus === 'idle' || uploadStatus === 'uploading'">
        <a-upload
          v-model:file-list="fileList"
          list-type="picture-card"
          :multiple="true"
          :max-count="50"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          :before-upload="handleBeforeUpload"
          :show-upload-list="{
            showPreviewIcon: true,
            showRemoveIcon: uploadStatus === 'idle',
          }"
          @preview="handlePreview"
        >
          <div v-if="fileList.length < 50">
            <PlusOutlined />
            <div style="margin-top: 8px">选择截图</div>
          </div>
        </a-upload>
        <p class="upload-hint">
          支持格式: PNG, JPG, WEBP | 最多 50 张 | 单张最大 10MB
        </p>

        <!-- 上传进度 -->
        <div v-if="uploadStatus === 'uploading'" class="upload-progress-panel">
          <a-spin size="large" />
          <p class="mt-3">正在上传截图到云存储...</p>
          <a-progress
            :percent="uploadProgress"
            :status="uploadError ? 'exception' : 'active'"
          />
          <p class="progress-text">
            已完成: {{ uploadedCount }} / {{ fileList.length }}
          </p>
        </div>

        <!-- 操作按钮 -->
        <div v-if="uploadStatus === 'idle' && fileList.length > 0" class="action-buttons mt-4">
          <VbenButton type="primary" @click="nextToConfig">
            下一步：配置信息（{{ fileList.length }} 张）
          </VbenButton>
          <VbenButton @click="handleReset">清空重选</VbenButton>
        </div>
      </template>

      <!-- 步骤2：配置信息 -->
      <template v-if="uploadStatus === 'configuring'">
        <a-alert type="success" show-icon class="mb-4">
          <template #message>截图上传成功！</template>
          <template #description>
            已上传 {{ uploadedUrls.length }} 张截图，请配置批量识别的默认信息
          </template>
        </a-alert>

        <!-- 已上传截图预览 -->
        <Card title="📸 已上传截图" size="small" class="mb-4">
          <div class="uploaded-preview-grid">
            <Image
              v-for="(url, index) in uploadedUrls"
              :key="index"
              :src="url"
              :width="80"
              :height="80"
              :preview="true"
              style="object-fit: cover; border-radius: 4px;"
            />
          </div>
          <p class="text-gray-500 mt-2">共 {{ uploadedUrls.length }} 张</p>
        </Card>

        <!-- 配置表单 -->
        <Card title="⚙️ 批量配置" size="small">
          <Form
            ref="configFormRef"
            :model="batchConfig"
            :rules="configRules"
            layout="vertical"
          >
            <FormItem label="目标看板" name="board_id">
              <Select
                v-model:value="batchConfig.board_id"
                placeholder="选择目标看板"
                :loading="boardsLoading"
                size="large"
              >
                <SelectOption v-for="board in boards" :key="board.id" :value="board.id">
                  {{ board.name }}
                </SelectOption>
              </Select>
            </FormItem>

            <FormItem label="来源类型" name="author_type">
              <RadioGroup v-model:value="batchConfig.author_type" size="large">
                <Radio value="customer">内部客户</Radio>
                <Radio value="external">外部用户</Radio>
              </RadioGroup>
            </FormItem>

            <!-- 内部客户模式 -->
            <template v-if="batchConfig.author_type === 'customer'">
              <FormItem label="默认客户名称" name="default_customer_name">
                <Input
                  v-model:value="batchConfig.default_customer_name"
                  placeholder="AI 无法识别客户时使用此默认值"
                  size="large"
                />
              </FormItem>
            </template>

            <!-- 外部用户模式 -->
            <template v-else>
              <FormItem label="来源平台" name="source_platform">
                <Select v-model:value="batchConfig.source_platform" placeholder="选择平台" size="large">
                  <SelectOption value="wechat">微信</SelectOption>
                  <SelectOption value="xiaohongshu">小红书</SelectOption>
                  <SelectOption value="appstore">App Store</SelectOption>
                  <SelectOption value="weibo">微博</SelectOption>
                  <SelectOption value="other">其他</SelectOption>
                </Select>
              </FormItem>

              <FormItem label="默认用户名称" name="default_user_name">
                <Input
                  v-model:value="batchConfig.default_user_name"
                  placeholder="AI 无法识别用户名时使用此默认值（可选）"
                  size="large"
                />
              </FormItem>
            </template>
          </Form>

          <div class="action-buttons mt-4">
            <VbenButton type="primary" :loading="isSubmitting" @click="handleSubmit">
              开始批量识别
            </VbenButton>
            <VbenButton @click="backToUpload">返回上一步</VbenButton>
          </div>
        </Card>
      </template>

      <!-- 步骤3：识别中 -->
      <template v-if="uploadStatus === 'processing'">
        <div class="batch-progress">
          <a-spin size="large" />
          <h3 class="mt-4">AI 正在批量识别中...</h3>
          <p class="text-gray-500">这可能需要几分钟时间，您可以离开此页面</p>

          <a-progress
            type="circle"
            :percent="batchProgress"
            :width="120"
            class="mt-4"
          />

          <a-row :gutter="16" class="statistics mt-4">
            <a-col :span="6">
              <a-statistic title="总计" :value="progressData?.total_count || 0" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="已完成" :value="progressData?.completed_count || 0" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="处理中" :value="progressData?.processing_count || 0" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="失败" :value="progressData?.failed_count || 0" />
            </a-col>
          </a-row>

          <div class="action-buttons mt-4">
            <VbenButton danger @click="handleCancelBatch">
              取消任务
            </VbenButton>
          </div>
        </div>
      </template>

      <!-- 步骤4：完成 -->
      <template v-if="uploadStatus === 'success'">
        <div class="batch-result success">
          <div class="result-header-section">
            <CheckCircleOutlined class="result-icon success-icon" />
            <h3>批量识别完成！</h3>
          </div>

          <div class="result-content-section">
            <a-row :gutter="16" class="statistics mb-6">
              <a-col :span="6">
                <a-statistic title="总计" :value="progressData?.total_count || 0" />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="成功"
                  :value="progressData?.completed_count || 0"
                  :value-style="{ color: '#3f8600' }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="失败"
                  :value="progressData?.failed_count || 0"
                  :value-style="{ color: (progressData?.failed_count || 0) > 0 ? '#cf1322' : undefined }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="成功率"
                  :value="successRate"
                  suffix="%"
                />
              </a-col>
            </a-row>

            <!-- 反馈列表 -->
            <Card v-if="batchResults.length > 0" title="📋 识别结果列表" class="result-list-card" size="small">
            <template #extra>
              <a-statistic
                title="共识别反馈"
                :value="totalCreatedFeedbacks"
                suffix="条"
                :value-style="{ fontSize: '16px', color: '#1890ff' }"
              />
            </template>

            <a-tabs v-model:activeKey="resultTab">
              <a-tab-pane key="all" tab="全部">
                <div class="result-list">
                  <a-empty v-if="batchResults.length === 0" description="暂无数据" />
                  <div
                    v-for="(item, index) in batchResults"
                    :key="item.task_item_id"
                    class="result-item"
                  >
                    <div class="result-header">
                      <span class="result-index">#{{ index + 1 }}</span>
                      <a-tag v-if="item.status === 'completed'" color="success">
                        <CheckOutlined /> 成功
                      </a-tag>
                      <a-tag v-else-if="item.status === 'failed'" color="error">
                        <CloseOutlined /> 失败
                      </a-tag>
                      <a-tag v-else>{{ item.status }}</a-tag>

                      <!-- 显示该截图识别出的反馈数量 -->
                      <a-tag
                        v-if="item.output_data?.total_feedbacks"
                        color="purple"
                      >
                        识别 {{ item.output_data.total_feedbacks }} 条反馈
                      </a-tag>

                      <a-tag
                        v-if="item.output_data?.overall_confidence !== undefined"
                        :color="item.output_data.overall_confidence > 0.8 ? 'blue' : 'warning'"
                      >
                        置信度: {{ (item.output_data.overall_confidence * 100).toFixed(0) }}%
                      </a-tag>
                    </div>

                    <div class="result-content">
                      <div class="screenshot-preview">
                        <Image
                          :src="item.output_data?.screenshot_url || item.input_data?.image_url"
                          :width="60"
                          :height="60"
                          style="object-fit: cover; border-radius: 4px;"
                        >
                          <template #preview-mask>
                            <div><EyeOutlined /> 预览</div>
                          </template>
                        </Image>
                      </div>

                      <div class="feedback-info">
                        <template v-if="item.status === 'completed' && item.output_data?.feedbacks">
                          <!-- 展示该截图识别出的所有反馈 -->
                          <div
                            v-for="(feedback, fbIndex) in item.output_data.feedbacks"
                            :key="feedback.feedback_id"
                            class="feedback-item"
                            :class="{ 'mt-3': fbIndex > 0 }"
                          >
                            <div class="feedback-item-header">
                              <a-tag size="small" color="cyan">反馈 {{ fbIndex + 1 }}</a-tag>
                              <a-tag
                                size="small"
                                :color="feedback.confidence > 0.8 ? 'green' : 'orange'"
                              >
                                {{ (feedback.confidence * 100).toFixed(0) }}%
                              </a-tag>
                            </div>
                            <div class="feedback-content">
                              {{ feedback.content || '（无内容）' }}
                            </div>
                            <div class="feedback-meta">
                              <span class="text-gray-500">
                                ID: {{ feedback.feedback_id.slice(0, 8) }}...
                              </span>
                            </div>
                          </div>
                        </template>
                        <template v-else-if="item.error_message">
                          <div class="error-info">
                            <a-alert type="error" :message="item.error_message" banner />
                          </div>
                        </template>
                        <div v-else class="text-gray-500">处理中...</div>
                      </div>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
              <a-tab-pane key="completed" :tab="`成功 (${completedResults.length})`">
                <div class="result-list">
                  <a-empty v-if="completedResults.length === 0" description="暂无数据" />
                  <div
                    v-for="(item, index) in completedResults"
                    :key="item.task_item_id"
                    class="result-item"
                  >
                    <div class="result-header">
                      <span class="result-index">#{{ index + 1 }}</span>
                      <a-tag color="success"><CheckOutlined /> 成功</a-tag>
                      <a-tag
                        v-if="item.output_data?.total_feedbacks"
                        color="purple"
                      >
                        识别 {{ item.output_data.total_feedbacks }} 条反馈
                      </a-tag>
                      <a-tag
                        v-if="item.output_data?.overall_confidence !== undefined"
                        :color="item.output_data.overall_confidence > 0.8 ? 'blue' : 'warning'"
                      >
                        置信度: {{ (item.output_data.overall_confidence * 100).toFixed(0) }}%
                      </a-tag>
                    </div>

                    <div class="result-content">
                      <div class="screenshot-preview">
                        <Image
                          :src="item.output_data?.screenshot_url || item.input_data?.image_url"
                          :width="60"
                          :height="60"
                          style="object-fit: cover; border-radius: 4px;"
                        >
                          <template #preview-mask>
                            <div><EyeOutlined /> 预览</div>
                          </template>
                        </Image>
                      </div>

                      <div class="feedback-info">
                        <div
                          v-for="(feedback, fbIndex) in item.output_data?.feedbacks || []"
                          :key="feedback.feedback_id"
                          class="feedback-item"
                          :class="{ 'mt-3': fbIndex > 0 }"
                        >
                          <div class="feedback-item-header">
                            <a-tag size="small" color="cyan">反馈 {{ fbIndex + 1 }}</a-tag>
                            <a-tag
                              size="small"
                              :color="feedback.confidence > 0.8 ? 'green' : 'orange'"
                            >
                              {{ (feedback.confidence * 100).toFixed(0) }}%
                            </a-tag>
                          </div>
                          <div class="feedback-content">
                            {{ feedback.content || '（无内容）' }}
                          </div>
                          <div class="feedback-meta">
                            <span class="text-gray-500">
                              ID: {{ feedback.feedback_id.slice(0, 8) }}...
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
              <a-tab-pane v-if="failedResults.length > 0" key="failed" :tab="`失败 (${failedResults.length})`">
                <div class="result-list">
                  <div
                    v-for="(item, index) in failedResults"
                    :key="item.task_item_id"
                    class="result-item"
                  >
                    <div class="result-header">
                      <span class="result-index">#{{ index + 1 }}</span>
                      <a-tag color="error"><CloseOutlined /> 失败</a-tag>
                    </div>

                    <div class="result-content">
                      <div class="screenshot-preview">
                        <Image
                          :src="item.output_data?.screenshot_url || item.input_data?.image_url"
                          :width="60"
                          :height="60"
                          style="object-fit: cover; border-radius: 4px;"
                        >
                          <template #preview-mask>
                            <div><EyeOutlined /> 预览</div>
                          </template>
                        </Image>
                      </div>

                      <div class="feedback-info">
                        <div class="error-info">
                          <a-alert type="error" :message="item.error_message || '未知错误'" banner />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </Card>

            <div class="action-buttons mt-6">
              <VbenButton type="primary" @click="goToFeedbackList">
                查看反馈列表
              </VbenButton>
              <VbenButton @click="handleReset">
                继续批量识别
              </VbenButton>
            </div>
          </div>
        </div>
      </template>

      <!-- 失败状态 -->
      <template v-if="uploadStatus === 'error'">
        <div class="batch-result error">
          <CloseCircleOutlined class="result-icon error-icon" />
          <h3>批量识别失败</h3>
          <p class="error-message">{{ errorMessage }}</p>

          <div class="action-buttons mt-4">
            <VbenButton type="primary" @click="handleReset">
              重新开始
            </VbenButton>
          </div>
        </div>
      </template>
    </Card>

    <!-- 图片预览 Modal -->
    <a-modal :open="previewVisible" :footer="null" @cancel="previewVisible = false">
      <img :src="previewImage" style="width: 100%" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  Card,
  Form,
  FormItem,
  Input,
  Select,
  SelectOption,
  Radio,
  RadioGroup,
  Image,
} from 'ant-design-vue'
import {
  PlusOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import { VbenButton } from '@vben/common-ui'
import { uploadScreenshot } from '#/api/core/upload'
import {
  screenshotBatchUpload,
  getBatchJobProgress,
  getBatchJobResults,
  cancelBatchJob,
  type ScreenshotBatchUploadRequest,
  type BatchJobProgress,
  type BatchTaskItemResult,
} from '#/api/userecho/feedback'
import { getBoardList, type Board } from '#/api/userecho/board'

const router = useRouter()
const configFormRef = ref()

// 上传状态
type UploadStatus = 'idle' | 'uploading' | 'configuring' | 'processing' | 'success' | 'error'
const uploadStatus = ref<UploadStatus>('idle')
const fileList = ref<any[]>([])
const uploadedUrls = ref<string[]>([])
const uploadProgress = ref(0)
const uploadedCount = ref(0)
const uploadError = ref(false)

// 看板列表
const boards = ref<Board[]>([])
const boardsLoading = ref(false)

// 批量任务
const batchJobId = ref<string>('')
const progressData = ref<BatchJobProgress | null>(null)
const batchResults = ref<BatchTaskItemResult[]>([])
const resultTab = ref('all')
const isSubmitting = ref(false)
const errorMessage = ref('')

// 轮询定时器
let pollTimer: number | null = null

// 计算完成和失败的结果
const completedResults = computed(() =>
  batchResults.value.filter(r => r.status === 'completed')
)

const failedResults = computed(() =>
  batchResults.value.filter(r => r.status === 'failed')
)

// 计算所有识别出的反馈总数
const totalCreatedFeedbacks = computed(() => {
  return batchResults.value.reduce((total, item) => {
    if (item.status === 'completed' && item.output_data?.feedbacks) {
      return total + item.output_data.feedbacks.length
    }
    return total
  }, 0)
})

// 计算当前步骤
const currentStep = computed(() => {
  switch (uploadStatus.value) {
    case 'idle':
    case 'uploading':
      return 0
    case 'configuring':
      return 1
    case 'processing':
      return 2
    case 'success':
    case 'error':
      return 3
    default:
      return 0
  }
})

// 计算批量进度
const batchProgress = computed(() => {
  if (!progressData.value) return 0
  return Math.round(progressData.value.progress)
})

// 计算成功率
const successRate = computed(() => {
  if (!progressData.value || progressData.value.total_count === 0) return 0
  return ((progressData.value.completed_count / progressData.value.total_count) * 100).toFixed(1)
})

// 批量配置
const batchConfig = reactive<ScreenshotBatchUploadRequest>({
  image_urls: [],
  board_id: '',
  author_type: 'external',
  source_platform: 'wechat',
  default_user_name: undefined,
  default_customer_name: undefined,
})

// 表单验证规则
const configRules: any = {
  board_id: [{ required: true, message: '请选择目标看板', trigger: 'change' }],
  author_type: [{ required: true, message: '请选择来源类型', trigger: 'change' }],
  source_platform: [{ required: true, message: '请选择来源平台', trigger: 'change' }],
}

// 图片预览
const previewVisible = ref(false)
const previewImage = ref('')

// 加载看板列表
const loadBoards = async () => {
  try {
    boardsLoading.value = true
    boards.value = await getBoardList()
    if (boards.value.length > 0 && !batchConfig.board_id) {
      batchConfig.board_id = boards.value[0]!.id
    }
  } catch (error) {
    console.error('加载看板列表失败', error)
  } finally {
    boardsLoading.value = false
  }
}

onMounted(() => {
  loadBoards()
})

// 清理定时器
onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

// 文件上传前验证
const handleBeforeUpload = (file: File) => {
  // 验证文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    message.error(`${file.name}: 不支持的文件格式`)
    return false
  }

  // 验证文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    message.error(`${file.name}: 文件过大（最大 10MB）`)
    return false
  }

  // 阻止自动上传，由我们手动控制
  return false
}

// 预览图片
const handlePreview = (file: any) => {
  previewImage.value = file.url || file.thumbUrl
  previewVisible.value = true
}

// 下一步：开始上传
const nextToConfig = async () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择截图')
    return
  }

  uploadStatus.value = 'uploading'
  uploadProgress.value = 0
  uploadedCount.value = 0
  uploadedUrls.value = []
  uploadError.value = false

  try {
    // 并发上传所有文件
    const uploadPromises = fileList.value.map(async (fileItem, index) => {
      try {
        const url = await uploadScreenshot(fileItem.originFileObj as File)
        uploadedUrls.value.push(url)
        uploadedCount.value++
        uploadProgress.value = Math.round((uploadedCount.value / fileList.value.length) * 100)
        return url
      } catch (error: any) {
        console.error(`上传失败 [${index}]:`, error)
        throw error
      }
    })

    await Promise.all(uploadPromises)

    uploadProgress.value = 100
    message.success(`成功上传 ${uploadedUrls.value.length} 张截图`)

    // 进入配置页面
    uploadStatus.value = 'configuring'
  } catch (error: any) {
    uploadError.value = true
    uploadStatus.value = 'idle'
    message.error(`上传失败: ${error.message || '请重试'}`)
  }
}

// 返回上一步
const backToUpload = () => {
  uploadStatus.value = 'idle'
  uploadedUrls.value = []
}

// 提交批量任务
const handleSubmit = async () => {
  try {
    await configFormRef.value.validate()

    isSubmitting.value = true

    // 构建请求数据
    const requestData: ScreenshotBatchUploadRequest = {
      image_urls: uploadedUrls.value,
      board_id: batchConfig.board_id,
      author_type: batchConfig.author_type,
    }

    if (batchConfig.author_type === 'customer') {
      requestData.default_customer_name = batchConfig.default_customer_name
    } else {
      requestData.source_platform = batchConfig.source_platform
      requestData.default_user_name = batchConfig.default_user_name
    }

    const response = await screenshotBatchUpload(requestData)
    batchJobId.value = response.batch_id

    message.success('批量任务已提交，正在识别中...')

    uploadStatus.value = 'processing'

    // 开始轮询进度
    startPolling()
  } catch (error: any) {
    if (error.errorFields) {
      message.warning('请完善配置信息')
    } else {
      message.error(error.message || '提交失败，请重试')
    }
  } finally {
    isSubmitting.value = false
  }
}

// 开始轮询批量任务进度
const startPolling = () => {
  const pollProgress = async () => {
    try {
      const progress = await getBatchJobProgress(batchJobId.value)
      progressData.value = progress

      // 根据状态判断是否完成
      if (progress.status === 'completed') {
        if (pollTimer) clearInterval(pollTimer)

        // 加载详细结果
        await loadBatchResults()

        uploadStatus.value = 'success'
        message.success('批量识别完成！')
      } else if (progress.status === 'failed' || progress.status === 'cancelled') {
        if (pollTimer) clearInterval(pollTimer)
        uploadStatus.value = 'error'
        errorMessage.value = progress.status === 'cancelled' ? '任务已取消' : '任务失败'
      }
    } catch (error: any) {
      console.error('查询进度失败', error)
    }
  }

  // 立即查询一次
  pollProgress()

  // 每 2 秒轮询一次
  pollTimer = window.setInterval(pollProgress, 2000)
}

// 加载批量结果详情
const loadBatchResults = async () => {
  try {
    const results = await getBatchJobResults(batchJobId.value)
    batchResults.value = results
  } catch (error: any) {
    console.error('加载结果失败', error)
  }
}

// 取消批量任务
const handleCancelBatch = async () => {
  try {
    await cancelBatchJob(batchJobId.value)
    if (pollTimer) clearInterval(pollTimer)
    message.info('任务已取消')
    uploadStatus.value = 'error'
    errorMessage.value = '任务已取消'
  } catch (error: any) {
    message.error(error.message || '取消失败')
  }
}

// 重置
const handleReset = () => {
  fileList.value = []
  uploadedUrls.value = []
  uploadStatus.value = 'idle'
  uploadProgress.value = 0
  uploadedCount.value = 0
  batchJobId.value = ''
  progressData.value = null
  batchResults.value = []
  resultTab.value = 'all'
  errorMessage.value = ''

  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }

  // 重置配置
  batchConfig.author_type = 'external'
  batchConfig.source_platform = 'wechat'
  batchConfig.default_user_name = undefined
  batchConfig.default_customer_name = undefined
}

// 前往反馈列表
const goToFeedbackList = () => {
  router.push('/app/feedback/list')
}
</script>

<style scoped lang="less">
.screenshot-batch-upload-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
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

.upload-hint {
  text-align: center;
  color: #8c8c8c;
  margin-top: 16px;
  font-size: 14px;
}

.upload-progress-panel {
  text-align: center;
  padding: 40px 0;
}

.progress-text {
  margin-top: 12px;
  color: #595959;
  font-size: 16px;
}

.uploaded-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.text-gray-500 {
  color: #8c8c8c;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.batch-progress {
  text-align: center;
  padding: 60px 0;
}

.batch-progress h3 {
  font-size: 20px;
  margin-top: 16px;
}

.statistics {
  max-width: 600px;
  margin: 0 auto;
}

.batch-result {
  padding: 20px 0;
}

.result-header-section {
  text-align: center;
  padding: 40px 0 20px;
}

.result-content-section {
  max-width: 1200px;
  margin: 0 auto;
  text-align: left;
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

.batch-result h3 {
  margin-top: 16px;
  font-size: 24px;
}

.error-message {
  color: #666;
  margin-top: 12px;
}

.result-list-card {
  text-align: left;
}

.result-list {
  max-height: 500px;
  overflow-y: auto;
}

.result-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
}

.result-item:hover {
  background-color: #fafafa;
}

.result-item:last-child {
  border-bottom: none;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.result-index {
  font-weight: 600;
  color: #1890ff;
  min-width: 40px;
}

.result-content {
  display: flex;
  gap: 16px;
}

.screenshot-preview {
  flex-shrink: 0;
}

.feedback-info {
  flex: 1;
  min-width: 0;
}

.feedback-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
}

.feedback-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.feedback-content {
  color: #262626;
  line-height: 1.6;
  margin-bottom: 8px;
  word-wrap: break-word;
}

.feedback-meta {
  font-size: 12px;
  color: #8c8c8c;
}

.error-info {
  margin-top: 4px;
}

</style>
