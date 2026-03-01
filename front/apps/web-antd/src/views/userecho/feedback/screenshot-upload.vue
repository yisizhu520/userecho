<template>
  <div class="screenshot-upload-page">
    <!-- 面包屑导航 -->
    <div class="page-header">
      <a-breadcrumb>
        <a-breadcrumb-item>
          <router-link to="/app/feedback/list">反馈管理</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>截图识别</a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <Card title="截图智能识别" class="upload-card">
      <template v-if="!uploadedFile">
        <!-- 上传区域 -->
        <div
          class="upload-zone"
          :class="{ 'is-dragover': isDragOver }"
          @click="triggerFileSelect"
          @drop.prevent="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @paste="handlePaste"
        >
          <div class="upload-icon">
            <CloudUploadOutlined :style="{ fontSize: '48px', color: '#1890ff' }" />
          </div>
          <div class="upload-text">
            <p class="upload-hint">点击选择文件 或 拖拽文件到这里</p>
            <p class="upload-paste-hint">也可以直接粘贴截图 (Ctrl+V)</p>
          </div>
          <div class="upload-desc">
            <p>支持格式: PNG, JPG, JPEG, WEBP</p>
            <p>文件大小: 最大 10MB</p>
          </div>
        </div>

        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInputRef"
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          style="display: none"
          @change="handleFileSelect"
        />
      </template>

      <!-- 上传中/识别中状态 -->
      <template v-else-if="isUploading || isAnalyzing">
        <div class="upload-progress">
          <Spin size="large" />
          <p class="progress-text">{{ isUploading ? '上传中...' : 'AI 识别中...' }}</p>
          <Progress :percent="uploadProgress" />
        </div>
      </template>

      <!-- 识别完成 - 左右分栏审核界面 -->
      <template v-else-if="analysisResult">
        <div class="analysis-result">
          <Row :gutter="24">
            <!-- 左侧：截图预览 -->
            <Col :span="10">
              <div class="screenshot-preview">
                <Image
                  :src="screenshotUrl"
                  :preview="true"
                  alt="截图预览"
                  style="width: 100%; border-radius: 8px;"
                />
                <div class="preview-actions">
                  <Button type="link" @click="resetUpload">
                    <ReloadOutlined /> 重新上传
                  </Button>
                  <Button type="link" @click="reanalyze">
                    <SyncOutlined /> 重新识别
                  </Button>
                </div>
              </div>
            </Col>

            <!-- 右侧：反馈列表 + 公共设置 -->
            <Col :span="14">
              <!-- OCR 原始文本（可折叠） -->
              <Card v-if="rawText" size="small" class="raw-text-card" style="margin-bottom: 16px;">
                <template #title>
                  <span style="font-size: 14px;">📄 OCR 识别文本</span>
                </template>
                <div class="raw-text-content">
                  <Textarea
                    :value="rawText"
                    :rows="4"
                    readonly
                    placeholder="暂无识别文本"
                    style="font-size: 12px; color: #666; background: #fafafa;"
                  />
                  <div style="margin-top: 8px; text-align: right;">
                    <Button size="small" @click="copyRawText">
                      复制文本
                    </Button>
                  </div>
                </div>
              </Card>

              <!-- 公共设置 -->
              <Card size="small" class="common-settings-card" style="margin-bottom: 16px;">
                <template #title>
                  <span style="font-size: 14px;">⚙️ 公共设置</span>
                </template>
                <Form layout="vertical">
                  <FormItem label="目标看板">
                    <Select
                      v-model:value="formData.board_id"
                      placeholder="选择目标看板"
                      :loading="boardsLoading"
                    >
                      <SelectOption v-for="board in boards" :key="board.id" :value="board.id">
                        {{ board.name }}
                      </SelectOption>
                    </Select>
                  </FormItem>

                  <FormItem label="来源类型">
                    <RadioGroup v-model:value="formData.author_type">
                      <Radio value="customer">内部客户</Radio>
                      <Radio value="external">外部用户</Radio>
                    </RadioGroup>
                  </FormItem>

                  <!-- 内部客户模式 -->
                  <template v-if="formData.author_type === 'customer'">
                    <FormItem label="客户名称">
                      <CustomerAutoComplete
                        v-model="formData.customer_name"
                        v-model:customer-type="formData.customer_type"
                        placeholder="输入客户名称"
                        @customer-selected="onCustomerSelected"
                      />
                    </FormItem>
                  </template>

                  <!-- 外部用户模式 -->
                  <template v-else>
                    <FormItem label="联系方式">
                      <Input v-model:value="formData.external_contact" placeholder="邮箱/手机（可选）" />
                    </FormItem>
                  </template>
                </Form>
              </Card>

              <!-- 反馈列表 -->
              <div class="feedback-list">
                <div class="feedback-list-header">
                  <span style="font-weight: 500; font-size: 14px;">📝 识别到的反馈（{{ enabledCount }}/{{ feedbackItems.length }}）</span>
                  <Alert
                    v-if="aiConfidence > 0"
                    :type="confidenceInfo.color"
                    :message="confidenceInfo.text"
                    show-icon
                    style="flex: 1; margin-left: 16px;"
                  />
                </div>

                <div
                  v-for="(item, index) in feedbackItems"
                  :key="item.id"
                  class="feedback-item-card"
                  :class="{ 'feedback-item-disabled': !item.enabled }"
                >
                  <div class="feedback-item-header">
                    <Checkbox v-model:checked="item.enabled">
                      <span style="font-weight: 500;">反馈 {{ index + 1 }}</span>
                      <span v-if="item.confidence > 0" style="margin-left: 8px; color: #999; font-size: 12px;">
                        (置信度: {{ (item.confidence * 100).toFixed(0) }}%)
                      </span>
                    </Checkbox>
                    <Button
                      type="link"
                      danger
                      size="small"
                      @click="removeFeedbackItem(index)"
                    >
                      删除
                    </Button>
                  </div>

                  <div v-if="item.enabled" class="feedback-item-body">
                    <FormItem label="来源平台" style="margin-bottom: 12px;">
                      <Select v-model:value="item.platform" size="small">
                        <SelectOption value="wechat">微信</SelectOption>
                        <SelectOption value="xiaohongshu">小红书</SelectOption>
                        <SelectOption value="appstore">App Store</SelectOption>
                        <SelectOption value="weibo">微博</SelectOption>
                        <SelectOption value="qq">QQ</SelectOption>
                        <SelectOption value="other">其他</SelectOption>
                      </Select>
                    </FormItem>

                    <FormItem label="用户名称" style="margin-bottom: 12px;">
                      <Input v-model:value="item.user_name" size="small" placeholder="用户昵称" />
                    </FormItem>

                    <FormItem label="反馈内容" style="margin-bottom: 0;">
                      <Textarea
                        v-model:value="item.content"
                        :rows="4"
                        placeholder="请输入反馈内容"
                        size="small"
                      />
                    </FormItem>
                  </div>
                </div>
              </div>

              <!-- 批量操作 -->
              <div class="form-actions">
                <Button @click="resetUpload">取消</Button>
                <Button
                  type="primary"
                  :loading="isCreating"
                  :disabled="enabledCount === 0"
                  @click="handleBatchSubmit"
                >
                  确认创建 {{ enabledCount }} 条反馈
                </Button>
              </div>
            </Col>
          </Row>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  Card,
  Row,
  Col,
  Spin,
  Progress,
  Image,
  Button,
  Form,
  FormItem,
  Input,
  Textarea,
  Select,
  SelectOption,
  Radio,
  RadioGroup,
  Alert,
  Checkbox,
} from 'ant-design-vue'
import {
  CloudUploadOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue'
import { analyzeScreenshot, analyzeScreenshotByUrl, createFeedbackFromScreenshot, getScreenshotTaskStatus, type ScreenshotFeedbackCreateParams } from '#/api/userecho/feedback'
import { getUploadSign, uploadToSignedUrl } from '#/api/core/upload'
import { getBoardList, type Board } from '#/api/userecho/board'
import CustomerAutoComplete from './components/CustomerAutoComplete.vue'
import type { Customer } from '#/api'

const router = useRouter()
const fileInputRef = ref<HTMLInputElement>()

// 上传状态
const isDragOver = ref(false)
const uploadedFile = ref<File | null>(null)
const isUploading = ref(false)
const isAnalyzing = ref(false)
const uploadProgress = ref(0)

// 识别结果
const screenshotUrl = ref('')
const analysisResult = ref<any>(null)
const rawText = ref('')  // OCR 原始文本
const feedbackItems = ref<any[]>([])  // 多条反馈列表
const aiConfidence = ref(0)

// 看板列表
const boards = ref<Board[]>([])
const boardsLoading = ref(false)

// 加载看板列表
const loadBoards = async () => {
  try {
    boardsLoading.value = true
    boards.value = await getBoardList()
    // 默认选中第一个看板
    if (boards.value.length > 0 && !formData.board_id) {
      formData.board_id = boards.value[0]!.id
    }
  } catch (error) {
    console.error('加载看板列表失败', error)
  } finally {
    boardsLoading.value = false
  }
}

// 计算置信度等级信息
const confidenceInfo = computed(() => {
  if (aiConfidence.value >= 0.9) {
    return {
      text: '识别精准',
      desc: 'AI 对该识别结果非常有信心，请快速核对内容。',
      color: 'success' as const,
    }
  } else if (aiConfidence.value >= 0.6) {
    return {
      text: '建议核对',
      desc: '识别质量尚可，但建议您仔细检查“反馈内容”和“用户名称”。',
      color: 'warning' as const,
    }
  } else {
    return {
      text: '识别质量较低',
      desc: '由于截图较模糊或格式特殊，建议您根据左图手动修正提取信息。',
      color: 'error' as const,
    }
  }
})

// 计算启用的反馈数量
const enabledCount = computed(() => {
  return feedbackItems.value.filter(item => item.enabled).length
})

// 复制原始文本
const copyRawText = () => {
  if (!rawText.value) {
    message.warning('暂无文本可复制')
    return
  }
  
  navigator.clipboard.writeText(rawText.value).then(() => {
    message.success('已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

// 删除某条反馈
const removeFeedbackItem = (index: number) => {
  feedbackItems.value.splice(index, 1)
  
  if (feedbackItems.value.length === 0) {
    message.info('已删除所有反馈')
  }
}

onMounted(() => {
  loadBoards()
})

// 表单数据
const formData = reactive({
  board_id: '',
  author_type: 'external' as 'customer' | 'external',
  // 内部客户模式
  customer_name: '',
  customer_type: 'normal',
  // 外部用户模式
  source_platform: 'wechat',
  external_user_name: '',
  external_contact: '',
  source_user_id: '',
  // 公共
  content: '',
})

// 客户选择回调
const selectedCustomer = ref<Customer | null>(null)
const onCustomerSelected = (customer: Customer | null) => {
  selectedCustomer.value = customer
}

const isCreating = ref(false)

// 触发文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

// 处理拖拽上传
const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    processFile(file)
  }
}

// 处理粘贴上传
const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        processFile(file)
      }
      break
    }
  }
}

// 处理文件
const processFile = async (file: File) => {
  // 验证文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    message.error('不支持的文件格式，请上传 PNG, JPG 或 WEBP 格式的图片')
    return
  }

  // 验证文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    message.error(`文件过大（${(file.size / 1024 / 1024).toFixed(1)}MB），最大支持 10MB`)
    return
  }

  uploadedFile.value = file

  // 上传并识别（异步模式）
  try {
    isUploading.value = true
    uploadProgress.value = 10

    // 1. 尝试直传到对象存储
    let screenshotUploadedUrl = ''
    let useDirectUpload = false

    try {
      const sign = await getUploadSign({
        filename: file.name,
        upload_type: 'screenshot',
        content_type: file.type,
      })

      uploadProgress.value = 20
      await uploadToSignedUrl(sign, file)
      screenshotUploadedUrl = sign.cdn_url
      useDirectUpload = true
      console.log('✅ 直传成功:', screenshotUploadedUrl)
    } catch (error) {
      console.warn('❌ 直传失败，回退到后端上传', error)
      useDirectUpload = false
    }

    // 2. 提交异步任务
    let response
    if (useDirectUpload) {
      console.log('→ 使用直传 URL 识别（不重复上传）')
      response = await analyzeScreenshotByUrl(screenshotUploadedUrl)
    } else {
      console.log('→ 使用后端上传识别（回退模式）')
      const formDataPayload = new FormData()
      formDataPayload.append('file', file)
      response = await analyzeScreenshot(formDataPayload)
    }
    const taskId = response.task_id

    message.info('已提交识别任务，正在处理中...')

    isUploading.value = false
    isAnalyzing.value = true
    uploadProgress.value = 30

    // 2. 轮询任务状态
    let pollCount = 0
    const maxPolls = 30  // 最多轮询 30 次（60秒）
    let pollTimer: number | null = null

    const pollTaskStatus = async () => {
      pollCount++

      try {
        const status = await getScreenshotTaskStatus(taskId)

        // 根据状态更新进度
        if (status.state === 'PENDING') {
          uploadProgress.value = 40
        } else if (status.state === 'STARTED' || status.state === 'RETRY') {
          uploadProgress.value = 70
        } else if (status.state === 'SUCCESS') {
          // 识别成功
          if (pollTimer) clearInterval(pollTimer)

          uploadProgress.value = 100
          isAnalyzing.value = false

          if (status.result) {
            // 保存结果
            screenshotUrl.value = status.result.screenshot_url
            analysisResult.value = status.result.extracted
            rawText.value = status.result.extracted.raw_text || ''
            
            // 处理反馈列表
            const extractedList = status.result.extracted.feedback_list || []
            if (extractedList.length === 0) {
              message.warning('未识别到有效反馈内容，请手动填写')
              // 创建空白表单项
              feedbackItems.value = [{
                id: Date.now(),
                content: '',
                platform: 'wechat',
                user_name: '',
                user_id: '',
                confidence: 0,
                enabled: true,
              }]
            } else {
              // 转换为前端可编辑的格式
              feedbackItems.value = extractedList.map((item: any, index: number) => ({
                id: Date.now() + index,  // 唯一 ID
                content: item.content || '',
                platform: item.platform || 'wechat',
                user_name: item.user_name || '',
                user_id: item.user_id || '',
                confidence: item.confidence || 0,
                enabled: true,  // 默认全部启用
              }))

              aiConfidence.value = status.result.extracted.overall_confidence || 0
              message.success(`识别成功，共识别到 ${feedbackItems.value.length} 条反馈`)
            }
          } else {
            message.warning('识别完成，但未返回结果')
          }
        } else if (status.state === 'FAILURE') {
          // 识别失败
          if (pollTimer) clearInterval(pollTimer)

          isAnalyzing.value = false
          uploadedFile.value = null
          uploadProgress.value = 0

          const errorMsg = status.error || '识别失败'
          message.error(`识别失败: ${errorMsg}`)
        }

        // 超时保护
        if (pollCount >= maxPolls) {
          if (pollTimer) clearInterval(pollTimer)

          isAnalyzing.value = false
          uploadProgress.value = 0

          message.warning('识别超时，请稍后重试')
        }

      } catch (error: any) {
        console.error('轮询状态失败', error)

        // 轮询失败但不影响继续轮询（可能是临时网络问题）
        if (pollCount >= maxPolls) {
          if (pollTimer) clearInterval(pollTimer)

          isAnalyzing.value = false
          uploadProgress.value = 0

          message.error('查询状态失败，请重试')
        }
      }
    }

    // 立即查询一次，然后每 2 秒轮询一次
    await pollTaskStatus()

    if (isAnalyzing.value) {
      pollTimer = window.setInterval(pollTaskStatus, 2000)
    }

  } catch (error: any) {
    isUploading.value = false
    isAnalyzing.value = false
    uploadedFile.value = null
    uploadProgress.value = 0
    message.error(error.message || '提交任务失败，请重试')
  }
}

// 重新上传
const resetUpload = () => {
  uploadedFile.value = null
  screenshotUrl.value = ''
  analysisResult.value = null
  rawText.value = ''
  feedbackItems.value = []
  uploadProgress.value = 0
  aiConfidence.value = 0
  // 恢复表单默认值（保留 board_id）
  formData.author_type = 'external'
  formData.customer_name = ''
  formData.customer_type = 'normal'
  formData.source_platform = 'wechat'
  formData.external_user_name = ''
  formData.external_contact = ''
  formData.source_user_id = ''
  formData.content = ''
  selectedCustomer.value = null
}

// 重新识别
const reanalyze = async () => {
  if (uploadedFile.value) {
    await processFile(uploadedFile.value)
  }
}

// 批量提交创建反馈
const handleBatchSubmit = async () => {
  // 验证公共字段
  if (!formData.board_id) {
    message.warning('请选择目标看板')
    return
  }

  if (formData.author_type === 'customer' && !formData.customer_name.trim()) {
    message.warning('请输入客户名称')
    return
  }

  // 获取启用的反馈
  const enabledFeedbacks = feedbackItems.value.filter(item => item.enabled)
  
  if (enabledFeedbacks.length === 0) {
    message.warning('请至少选择一条反馈')
    return
  }

  // 验证每条反馈的内容
  for (const item of enabledFeedbacks) {
    if (!item.content.trim()) {
      message.warning('请填写所有反馈的内容')
      return
    }
    if (formData.author_type === 'external' && !item.user_name.trim()) {
      message.warning('请填写所有反馈的用户名称')
      return
    }
  }

  try {
    isCreating.value = true

    // 批量创建反馈
    const promises = enabledFeedbacks.map(async (item) => {
      const payload: ScreenshotFeedbackCreateParams = {
        board_id: formData.board_id,
        content: item.content,
        screenshot_url: screenshotUrl.value,
        source_type: 'screenshot',
        author_type: formData.author_type,
        ai_confidence: item.confidence,
      }

      if (formData.author_type === 'customer') {
        // 内部客户模式
        payload.customer_name = formData.customer_name
        payload.customer_type = formData.customer_type
        if (selectedCustomer.value) {
          payload.customer_id = selectedCustomer.value.id
        }
      } else {
        // 外部用户模式
        payload.source_platform = item.platform as any
        payload.external_user_name = item.user_name
        payload.external_contact = formData.external_contact || undefined
        payload.source_user_id = item.user_id || undefined
      }

      return createFeedbackFromScreenshot(payload)
    })

    await Promise.all(promises)

    message.success(`成功创建 ${enabledFeedbacks.length} 条反馈`)

    // 跳转到反馈列表
    setTimeout(() => {
      router.push('/app/feedback/list')
    }, 1000)
  } catch (error: any) {
    message.error(error.message || '创建失败，请重试')
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped lang="less">
.screenshot-upload-page {
  padding: 24px;
}

.page-header {
  max-width: 1200px;
  margin: 0 auto 24px;
}

.upload-card {
  max-width: 1200px;
  margin: 0 auto;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: #1890ff;
    background-color: #f0f5ff;
  }

  &.is-dragover {
    border-color: #1890ff;
    background-color: #e6f7ff;
  }

  .upload-icon {
    margin-bottom: 16px;
  }

  .upload-text {
    text-align: center;

    .upload-hint {
      font-size: 16px;
      color: #262626;
      margin-bottom: 8px;
    }

    .upload-paste-hint {
      font-size: 14px;
      color: #8c8c8c;
    }
  }

  .upload-desc {
    margin-top: 24px;
    text-align: center;

    p {
      font-size: 12px;
      color: #8c8c8c;
      margin: 4px 0;
    }
  }
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;

  .progress-text {
    margin: 24px 0 16px;
    font-size: 16px;
    color: #595959;
  }

  .ant-progress {
    width: 300px;
  }
}

.analysis-result {
  .screenshot-preview {
    .preview-actions {
      display: flex;
      justify-content: center;
      margin-top: 16px;
    }
  }

  .raw-text-card {
    border: 1px solid #e8e8e8;
  }

  .common-settings-card {
    border: 1px solid #e8e8e8;
  }

  .feedback-list {
    .feedback-list-header {
      display: flex;
      align-items: center;
      margin-bottom: 16px;
      padding: 12px 16px;
      background: #fafafa;
      border-radius: 8px;
    }

    .feedback-item-card {
      margin-bottom: 16px;
      padding: 16px;
      border: 1px solid #e8e8e8;
      border-radius: 8px;
      background: #fff;
      transition: all 0.3s;

      &:hover {
        border-color: #1890ff;
        box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
      }

      &.feedback-item-disabled {
        opacity: 0.5;
        background: #fafafa;
      }

      .feedback-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #f0f0f0;
      }

      .feedback-item-body {
        padding-top: 8px;
      }
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 24px;
    border-top: 1px solid #f0f0f0;
    margin-top: 24px;
  }
}
</style>
