<script setup lang="ts">
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { PlusOutlined, LoadingOutlined } from '@ant-design/icons-vue';
import { uploadFeedbackImage } from '#/api';

interface FileItem {
  file: File;
  previewUrl: string;
}

interface Props {
  maxCount?: number;
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  maxCount: 3,
});

defineEmits<Emits>();

const uploading = ref(false);
const localFiles = ref<FileItem[]>([]);

// 用于 a-upload 的 fileList（本地预览）
const fileList = computed(() =>
  localFiles.value.map((item, index) => ({
    uid: String(index),
    name: item.file.name,
    status: 'done' as const,
    url: item.previewUrl,
  }))
);

// 处理图片选择（本地预览，不上传）
const handleBeforeUpload = (file: File) => {
  if (localFiles.value.length >= props.maxCount) {
    message.warning(`最多只能上传${props.maxCount}张截图`);
    return false;
  }

  // 创建本地预览 URL
  const previewUrl = URL.createObjectURL(file);
  localFiles.value.push({ file, previewUrl });

  return false; // 阻止默认上传行为
};

// 移除图片
const handleRemove = (file: { uid: string }) => {
  const index = Number(file.uid);
  if (localFiles.value[index]) {
    // 释放预览 URL
    URL.revokeObjectURL(localFiles.value[index].previewUrl);
    localFiles.value.splice(index, 1);
  }
};

// 上传所有图片并返回 URL 列表（供父组件调用）
const uploadAll = async (): Promise<string[]> => {
  if (localFiles.value.length === 0) {
    return [];
  }

  uploading.value = true;
  const urls: string[] = [];

  try {
    for (const item of localFiles.value) {
      const result = await uploadFeedbackImage(item.file);
      urls.push(result.url);
    }
    return urls;
  } catch (error: any) {
    message.error(error.message || '图片上传失败');
    throw error;
  } finally {
    uploading.value = false;
  }
};

// 重置
const reset = () => {
  // 释放所有预览 URL
  for (const item of localFiles.value) {
    URL.revokeObjectURL(item.previewUrl);
  }
  localFiles.value = [];
};

// 暴露方法给父组件
defineExpose({
  uploadAll,
  reset,
  hasFiles: computed(() => localFiles.value.length > 0),
});
</script>

<template>
  <div class="screenshot-upload-section">
    <div class="upload-label">截图（最多{{ maxCount }}张）</div>
    <div class="upload-content">
      <a-upload
        :file-list="fileList"
        list-type="picture-card"
        :before-upload="handleBeforeUpload"
        @remove="handleRemove"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        :max-count="maxCount"
      >
        <div v-if="localFiles.length < maxCount">
          <loading-outlined v-if="uploading" />
          <plus-outlined v-else />
          <div class="upload-text">选择图片</div>
        </div>
      </a-upload>
    </div>
  </div>
</template>

<style scoped>
.screenshot-upload-section {
  /* 由父组件控制布局 */
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
