<template>
  <div class="screenshot-upload-page">
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

            <!-- 右侧：提取信息表单 -->
            <Col :span="14">
              <Form
                ref="formRef"
                :model="formData"
                :rules="formRules"
                layout="vertical"
              >
                <FormItem label="来源平台" name="source_platform">
                  <Select v-model:value="formData.source_platform" placeholder="选择平台">
                    <SelectOption value="wechat">微信</SelectOption>
                    <SelectOption value="xiaohongshu">小红书</SelectOption>
                    <SelectOption value="appstore">App Store</SelectOption>
                    <SelectOption value="weibo">微博</SelectOption>
                    <SelectOption value="other">其他</SelectOption>
                  </Select>
                </FormItem>

                <FormItem label="用户昵称" name="source_user_name">
                  <Input v-model:value="formData.source_user_name" placeholder="平台用户昵称" />
                </FormItem>

                <FormItem label="反馈内容" name="content">
                  <Textarea
                    v-model:value="formData.content"
                    :rows="8"
                    placeholder="提取的反馈内容"
                  />
                </FormItem>

                <FormItem label="反馈类型">
                  <RadioGroup v-model:value="formData.feedback_type">
                    <Radio value="bug">Bug</Radio>
                    <Radio value="feature">功能需求</Radio>
                    <Radio value="complaint">投诉</Radio>
                    <Radio value="other">其他</Radio>
                  </RadioGroup>
                </FormItem>

                <div class="confidence-info">
                  <span>AI 识别置信度:</span>
                  <Progress
                    :percent="Math.round(aiConfidence * 100)"
                    :status="aiConfidence > 0.8 ? 'success' : aiConfidence > 0.5 ? 'normal' : 'exception'"
                    :show-info="true"
                  />
                </div>

                <div class="form-actions">
                  <Button @click="resetUpload">取消</Button>
                  <Button type="primary" :loading="isCreating" @click="handleSubmit">
                    确认创建
                  </Button>
                </div>
              </Form>
            </Col>
          </Row>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
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
} from 'ant-design-vue'
import {
  CloudUploadOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue'
import { analyzeScreenshot, createFeedbackFromScreenshot, getScreenshotTaskStatus, type ScreenshotFeedbackCreateParams } from '#/api/userecho/feedback'

const router = useRouter()
const fileInputRef = ref<HTMLInputElement>()
const formRef = ref()

// 上传状态
const isDragOver = ref(false)
const uploadedFile = ref<File | null>(null)
const isUploading = ref(false)
const isAnalyzing = ref(false)
const uploadProgress = ref(0)

// 识别结果
const screenshotUrl = ref('')
const analysisResult = ref<any>(null)
const aiConfidence = ref(0)

// 表单数据
const formData = reactive({
  content: '',
  source_platform: 'wechat',
  source_user_name: '',
  source_user_id: '',
  feedback_type: 'other',
})

const formRules: any = {
  content: [{ required: true, message: '请输入反馈内容', trigger: 'blur' }],
  source_platform: [{ required: true, message: '请选择来源平台', trigger: 'change' }],
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

    // 1. 提交异步任务
    const formDataPayload = new FormData()
    formDataPayload.append('file', file)

    const response = await analyzeScreenshot(formDataPayload)
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
            aiConfidence.value = status.result.extracted.confidence

            // 填充表单
            formData.content = status.result.extracted.content || ''
            formData.source_platform = status.result.extracted.platform || 'wechat'
            formData.source_user_name = status.result.extracted.user_name || ''
            formData.source_user_id = status.result.extracted.user_id || ''
            formData.feedback_type = status.result.extracted.feedback_type || 'other'

            message.success('识别成功，请确认信息后提交')
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
  uploadProgress.value = 0
  formData.content = ''
  formData.source_platform = 'wechat'
  formData.source_user_name = ''
  formData.source_user_id = ''
  formData.feedback_type = 'other'
}

// 重新识别
const reanalyze = async () => {
  if (uploadedFile.value) {
    await processFile(uploadedFile.value)
  }
}

// 提交创建反馈
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    isCreating.value = true

    const payload: ScreenshotFeedbackCreateParams = {
      content: formData.content,
      screenshot_url: screenshotUrl.value,
      source_type: 'screenshot',
      source_platform: formData.source_platform as any,
      source_user_name: formData.source_user_name,
      source_user_id: formData.source_user_id,
      ai_confidence: aiConfidence.value,
      customer_id: null, // MVP 阶段不关联客户
    }

    await createFeedbackFromScreenshot(payload)

    message.success('反馈创建成功')

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

  .confidence-info {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    padding: 12px;
    background-color: #f5f5f5;
    border-radius: 4px;

    span {
      margin-right: 12px;
      font-weight: 500;
    }

    .ant-progress {
      flex: 1;
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 24px;
    border-top: 1px solid #f0f0f0;
  }
}
</style>
