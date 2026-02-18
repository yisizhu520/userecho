<script setup lang="ts">
import { computed } from 'vue';

interface ImageItem {
  url: string;
  uploaded_at?: string;
}

interface Props {
  images?: ImageItem[] | null;
}

const props = defineProps<Props>();

const imageList = computed(() => props.images ?? []);
const hasImages = computed(() => imageList.value.length > 0);
</script>

<template>
  <div v-if="hasImages" class="screenshot-cell">
    <a-popover
      trigger="hover"
      placement="right"
      :overlay-style="{ maxWidth: '800px' }"
    >
      <template #content>
        <a-image-preview-group>
          <div class="preview-grid">
            <a-image
              v-for="(img, idx) in imageList"
              :key="idx"
              :src="img.url"
              :preview="{ mask: false }"
              :style="{ maxWidth: '320px', maxHeight: '320px', objectFit: 'contain' }"
            />
          </div>
        </a-image-preview-group>
      </template>

      <!-- 表格单元格内并排展示所有缩略图 -->
      <div class="thumb-row">
        <img
          v-for="(img, idx) in imageList"
          :key="idx"
          :src="img.url"
          class="thumb-img"
          alt="截图"
        />
      </div>
    </a-popover>
  </div>
  <span v-else class="text-gray-400">-</span>
</template>

<style scoped>
.screenshot-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.thumb-row {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.thumb-img {
  width: 24px;
  height: 24px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid hsl(var(--border) / 0.3);
  background: hsl(var(--muted) / 0.3);
}

.preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-thumb {
  border-radius: 4px;
}

.preview-thumb :deep(img) {
  max-width: 320px;
  max-height: 320px;
  object-fit: contain;
}
</style>
