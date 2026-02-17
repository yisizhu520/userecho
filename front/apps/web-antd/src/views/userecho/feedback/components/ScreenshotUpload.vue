<script setup lang="ts">
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { PlusOutlined, LoadingOutlined } from '@ant-design/icons-vue';
import { analyzeScreenshot, getScreenshotTaskStatus } from '#/api';

interface Props {
  modelValue?: string[];
  maxCount?: number;
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  maxCount: 3,
});

const emit = defineEmits<Emits>();

const uploading = ref(false);

// 处理图片上传
const handleBeforeUpload = async (file: File) => {
  if (props.modelValue.length >= props.maxCount) {
    message.warning(`最多只能上传${props.maxCount}张截图`);
    return false;
  }
  
  try {
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', file);
    
    // 调用上传接口
    const response = await analyzeScreenshot(formData);
    
    // 轮询获取上传结果
    const taskId = response.task_id;
    let pollCount = 0;
    const maxPolls = 15;
    
    const pollUpload = async (): Promise<string | null> => {
      pollCount++;
      const status = await getScreenshotTaskStatus(taskId);
      
      if (status.state === 'SUCCESS' && status.result) {
        return status.result.screenshot_url;
      } else if (status.state === 'FAILURE') {
        throw new Error(status.error || '上传失败');
      } else if (pollCount < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        return pollUpload();
      } else {
        throw new Error('上传超时');
      }
    };
    
    const screenshotUrl = await pollUpload();
    if (screenshotUrl) {
      emit('update:modelValue', [...props.modelValue, screenshotUrl]);
      message.success('图片上传成功');
    }
    
    return false; // 阻止默认上传行为
  } catch (error: any) {
    message.error(error.message || '图片上传失败');
    return false;
  } finally {
    uploading.value = false;
  }
};

// 移除已上传的截图
const handleRemove = (file: any) => {
  // 使用 URL 过滤而非索引，避免删除后索引错乱
  const newList = props.modelValue.filter(url => url !== file.url);
  emit('update:modelValue', newList);
};
</script>

<template>
  <div class="screenshot-upload-section">
    <div class="upload-label">截图上传（最多{{ maxCount }}张）</div>
    <div class="upload-content">
      <a-upload
        :file-list="modelValue.map((url, index) => ({
          uid: String(index),
          name: `screenshot-${index + 1}.png`,
          status: 'done',
          url: url,
        }))"
        list-type="picture-card"
        :before-upload="handleBeforeUpload"
        @remove="handleRemove"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        :max-count="maxCount"
      >
        <div v-if="modelValue.length < maxCount">
          <loading-outlined v-if="uploading" />
          <plus-outlined v-else />
          <div class="upload-text">上传图片</div>
        </div>
      </a-upload>
    </div>
  </div>
</template>

<style scoped>
.screenshot-upload-section {
  /* 移除原有的边框和间距，由父组件控制 */
}

.upload-label {
  font-weight: 500;
  color: hsl(var(--foreground));
}

.upload-content {
  /* 上传区域容器 */
}

.upload-text {
  margin-top: 8px;
  font-size: 12px;
  color: hsl(var(--muted-foreground));
}
</style>
