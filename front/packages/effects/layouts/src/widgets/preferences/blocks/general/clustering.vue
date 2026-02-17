<template>
  <div class="clustering-config-panel">
    <!-- 当前配置展示 -->
    <div v-if="currentConfig" class="mb-4 rounded-md bg-blue-50 p-3 text-sm dark:bg-blue-950">
      <span class="font-medium">当前策略：{{ getCurrentPresetName() }}</span>
    </div>

    <!-- 预设模式选择 -->
    <div class="space-y-3">
      <div
        v-for="(preset, key) in presets"
        :key="key"
        class="cursor-pointer rounded-md border p-3 transition-colors"
        :class="{
          'border-blue-500 bg-blue-50 dark:bg-blue-950': selectedPreset === key,
          'border-gray-200 hover:border-blue-300 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800': selectedPreset !== key
        }"
        @click="selectedPreset = key"
      >
        <div class="flex items-center">
          <input
            type="radio"
            :id="`preset-${key}`"
            v-model="selectedPreset"
            :value="key"
            class="mr-2"
          />
          <label
            :for="`preset-${key}`"
            class="flex-1 cursor-pointer text-sm font-semibold"
          >
            {{ preset.display_name }}
          </label>
          <span
            v-if="key === 'standard'"
            class="rounded bg-blue-500 px-2 py-0.5 text-xs text-white"
          >
            推荐
          </span>
        </div>
        <p class="ml-6 mt-1 text-xs text-gray-600 dark:text-gray-400">{{ preset.description }}</p>
        <p class="ml-6 text-xs text-gray-500 dark:text-gray-500">{{ preset.use_case }}</p>
      </div>
    </div>

    <!-- 预览结果展示 -->
    <div
      v-if="previewResult && previewResult.status === 'success'"
      class="mt-4 rounded-md bg-gray-50 p-3 dark:bg-gray-800"
    >
      <h4 class="mb-2 text-sm font-semibold">预览效果</h4>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span class="text-gray-600 dark:text-gray-400">预计形成簇数：</span>
          <span class="font-medium">{{ previewResult.preview?.clusters_range }} 个</span>
        </div>
        <div>
          <span class="text-gray-600 dark:text-gray-400">预计覆盖率：</span>
          <span class="font-medium">{{ previewResult.preview?.coverage_percentage }}</span>
        </div>
        <div>
          <span class="text-gray-600 dark:text-gray-400">聚类质量：</span>
          <span
            class="rounded px-1.5 py-0.5 text-xs font-medium"
            :class="getQualityClass(previewResult.preview?.quality_rating)"
          >
            {{ previewResult.preview?.quality_rating }}
          </span>
        </div>
        <div>
          <span class="text-gray-600 dark:text-gray-400">测试样本数：</span>
          <span class="font-medium">{{ previewResult.test_samples }} 条</span>
        </div>
      </div>
    </div>

    <div
      v-else-if="previewResult && previewResult.status === 'insufficient_data'"
      class="mt-4 rounded-md bg-yellow-50 p-3 text-xs text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200"
    >
      {{ previewResult.message }}
    </div>

    <!-- 操作按钮 -->
    <div class="mt-4 flex justify-end space-x-2">
      <button
        @click="handlePreview"
        :disabled="previewLoading"
        class="rounded-md bg-gray-200 px-4 py-1.5 text-sm transition-colors hover:bg-gray-300 disabled:opacity-50 dark:bg-gray-700 dark:hover:bg-gray-600"
      >
        <span v-if="previewLoading">预览中...</span>
        <span v-else>预览效果</span>
      </button>
      <button
        @click="handleSave"
        :disabled="!hasChanges || saveLoading"
        class="rounded-md bg-blue-500 px-4 py-1.5 text-sm text-white transition-colors hover:bg-blue-600 disabled:opacity-50"
      >
        <span v-if="saveLoading">保存中...</span>
        <span v-else>保存设置</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue';

defineOptions({
  name: 'Clustering',
});

// 类型定义
interface ClusteringPreset {
  display_name: string;
  description: string;
  use_case: string;
}

interface ClusteringPresets {
  [key: string]: ClusteringPreset;
}

interface ClusteringConfig {
  preset_mode: string;
}

interface PreviewResult {
  status: string;
  message?: string;
  test_samples?: number;
  preview?: {
    clusters_range?: string;
    coverage_percentage?: string;
    quality_rating?: string;
  };
}

// API 函数类型
interface ClusteringAPI {
  getPresets: () => Promise<ClusteringPresets>;
  getConfig: () => Promise<ClusteringConfig>;
  updatePreset: (preset: string) => Promise<ClusteringConfig>;
  preview: (preset: string) => Promise<PreviewResult>;
}

// 通过 inject 获取 API（由应用层 provide）
const clusteringAPI = inject<ClusteringAPI>('clusteringAPI', {
  getPresets: async () => ({}),
  getConfig: async () => ({ preset_mode: 'standard' }),
  updatePreset: async () => ({ preset_mode: 'standard' }),
  preview: async () => ({ status: 'insufficient_data' }),
});

const presets = ref<ClusteringPresets>({});
const currentConfig = ref<ClusteringConfig | null>(null);
const selectedPreset = ref('standard');
const previewResult = ref<PreviewResult | null>(null);
const previewLoading = ref(false);
const saveLoading = ref(false);

const hasChanges = computed(() => {
  return currentConfig.value?.preset_mode !== selectedPreset.value;
});

const getCurrentPresetName = () => {
  const mode = currentConfig.value?.preset_mode;
  if (!mode || !presets.value[mode]) {
    return mode;
  }
  return presets.value[mode].display_name;
};

const getQualityClass = (rating?: string) => {
  const classes = {
    '优秀': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    '良好': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    '一般': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    '较差': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return classes[rating as keyof typeof classes] || 'bg-gray-100 text-gray-800';
};

const loadPresets = async () => {
  try {
    const res = await clusteringAPI.getPresets();
    presets.value = res;
  } catch (error) {
    console.error('加载预设模式失败', error);
  }
};

const loadCurrentConfig = async () => {
  try {
    const res = await clusteringAPI.getConfig();
    currentConfig.value = res;
    selectedPreset.value = res.preset_mode;
  } catch (error) {
    console.error('加载配置失败', error);
  }
};

const handlePreview = async () => {
  previewLoading.value = true;
  try {
    const res = await clusteringAPI.preview(selectedPreset.value);
    previewResult.value = res;
  } catch (error) {
    console.error('预览失败', error);
  } finally {
    previewLoading.value = false;
  }
};

const handleSave = async () => {
  saveLoading.value = true;
  try {
    await clusteringAPI.updatePreset(selectedPreset.value);
    await loadCurrentConfig();
    previewResult.value = null;
  } catch (error) {
    console.error('保存失败', error);
  } finally {
    saveLoading.value = false;
  }
};

onMounted(async () => {
  await loadPresets();
  await loadCurrentConfig();
});
</script>

<style scoped>
.clustering-config-panel input[type="radio"] {
  cursor: pointer;
}
</style>
