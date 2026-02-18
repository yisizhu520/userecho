<script setup lang="ts">
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { PlusOutlined, LoadingOutlined } from '@ant-design/icons-vue';
import { uploadFeedbackImage } from '#/api';

interface FileItem {
  file: File;
  previewUrl: string;
}

interface ExistingImage {
  url: string;
  uid: string;
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
const existingImages = ref<ExistingImage[]>([]);  // 存储已有的远程图片

// 用于 a-upload 的 fileList（本地预览 + 已有图片）
const fileList = computed(() => {
  const existingList = existingImages.value.map((item) => ({
    uid: item.uid,
    name: item.url.split('/').pop() || 'image',
    status: 'done' as const,
    url: item.url,
  }));
  
  const localList = localFiles.value.map((item, index) => ({
    uid: `local-${index}`,
    name: item.file.name,
    status: 'done' as const,
    url: item.previewUrl,
  }));
  
  return [...existingList, ...localList];
});

// 当前总图片数
const totalCount = computed(() => existingImages.value.length + localFiles.value.length);

// 处理图片选择（本地预览，不上传）
const handleBeforeUpload = (file: File) => {
  if (totalCount.value >= props.maxCount) {
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
  // 检查是否是已有图片
  const existingIndex = existingImages.value.findIndex(img => img.uid === file.uid);
  if (existingIndex !== -1) {
    existingImages.value.splice(existingIndex, 1);
    return;
  }
  
  // 检查是否是本地新增图片
  if (file.uid.startsWith('local-')) {
    const index = Number(file.uid.replace('local-', ''));
    if (localFiles.value[index]) {
      URL.revokeObjectURL(localFiles.value[index].previewUrl);
      localFiles.value.splice(index, 1);
    }
  }
};

// 初始化已有图片（编辑模式使用）
const initWithUrls = (urls: string[]) => {
  reset();
  existingImages.value = urls.map((url, index) => ({
    url,
    uid: `existing-${index}`,
  }));
};

// 上传所有新增图片并返回完整 URL 列表（已有图片 + 新上传图片）
const uploadAll = async (): Promise<string[]> => {
  // 收集已有图片的 URL
  const allUrls: string[] = existingImages.value.map(img => img.url);
  
  // 上传新增的本地图片
  if (localFiles.value.length > 0) {
    uploading.value = true;
    try {
      for (const item of localFiles.value) {
        const result = await uploadFeedbackImage(item.file);
        allUrls.push(result.url);
      }
    } catch (error: any) {
      message.error(error.message || '图片上传失败');
      throw error;
    } finally {
      uploading.value = false;
    }
  }
  
  return allUrls;
};

// 重置
const reset = () => {
  // 释放所有本地预览 URL
  for (const item of localFiles.value) {
    URL.revokeObjectURL(item.previewUrl);
  }
  localFiles.value = [];
  existingImages.value = [];
};

// 暴露方法给父组件
defineExpose({
  uploadAll,
  reset,
  initWithUrls,
  hasFiles: computed(() => totalCount.value > 0),
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
        <div v-if="totalCount < maxCount">
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
