<template>
  <div class="clustering-config-container p-6">
    <div class="card bg-white rounded-lg shadow-md p-6">
      <h2 class="text-2xl font-bold mb-6">聚类策略设置</h2>
      
      <!-- 当前配置展示 -->
      <div v-if="currentConfig" class="alert alert-info mb-4 p-4 bg-blue-50 rounded-md">
        <span class="font-medium">当前策略：{{ getCurrentPresetName() }}</span>
      </div>
      
      <!-- 预设模式选择 -->
      <div class="preset-selection space-y-4">
        <div
          v-for="(preset, key) in presets"
          :key="key"
          class="preset-item p-4 border rounded-md cursor-pointer transition-colors"
          :class="{
            'border-blue-500 bg-blue-50': selectedPreset === key,
            'border-gray-200 hover:border-blue-300 hover:bg-gray-50': selectedPreset !== key
          }"
          @click="selectedPreset = key"
        >
          <div class="flex items-center mb-2">
            <input
              type="radio"
              :id="`preset-${key}`"
              v-model="selectedPreset"
              :value="key"
              class="mr-3"
            />
            <label
              :for="`preset-${key}`"
              class="text-lg font-semibold cursor-pointer flex-1"
            >
              {{ preset.display_name }}
            </label>
            <span
              v-if="key === 'standard'"
              class="badge bg-blue-500 text-white px-2 py-1 rounded text-sm"
            >
              推荐
            </span>
          </div>
          <p class="text-gray-700 mb-2 ml-8">{{ preset.description }}</p>
          <p class="text-gray-500 text-sm ml-8">{{ preset.use_case }}</p>
        </div>
      </div>
      
      <!-- 预览结果展示 -->
      <div
        v-if="previewResult && previewResult.status === 'success'"
        class="preview-result mt-6 p-4 bg-gray-50 rounded-md"
      >
        <h3 class="text-lg font-semibold mb-3">预览效果</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="text-gray-600">预计形成簇数：</span>
            <span class="font-medium">{{ previewResult.preview?.clusters_range }} 个</span>
          </div>
          <div>
            <span class="text-gray-600">预计覆盖率：</span>
            <span class="font-medium">{{ previewResult.preview?.coverage_percentage }}</span>
          </div>
          <div>
            <span class="text-gray-600">聚类质量：</span>
            <span
              class="font-medium px-2 py-1 rounded text-sm"
              :class="getQualityClass(previewResult.preview?.quality_rating)"
            >
              {{ previewResult.preview?.quality_rating }}
            </span>
          </div>
          <div>
            <span class="text-gray-600">测试样本数：</span>
            <span class="font-medium">{{ previewResult.test_samples }} 条反馈</span>
          </div>
        </div>
      </div>
      
      <div
        v-else-if="previewResult && previewResult.status === 'insufficient_data'"
        class="alert alert-warning mt-6 p-4 bg-yellow-50 rounded-md text-yellow-800"
      >
        {{ previewResult.message }}
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-buttons mt-6 flex justify-end space-x-4">
        <button
          @click="handlePreview"
          :disabled="previewLoading"
          class="btn btn-secondary px-6 py-2 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors disabled:opacity-50"
        >
          <span v-if="previewLoading">预览中...</span>
          <span v-else>预览效果</span>
        </button>
        <button
          @click="handleSave"
          :disabled="!hasChanges || saveLoading"
          class="btn btn-primary px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors disabled:opacity-50"
        >
          <span v-if="saveLoading">保存中...</span>
          <span v-else>保存设置</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { 
  getClusteringPresets, 
  getClusteringConfig,
  updateClusteringPreset,
  previewClusteringConfig,
  type ClusteringPresets,
  type ClusteringConfig,
  type PreviewResult,
} from '#/api';

const presets = ref<ClusteringPresets>({} as ClusteringPresets);
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
  if (!mode || !presets.value[mode as keyof ClusteringPresets]) {
    return mode;
  }
  return presets.value[mode as keyof ClusteringPresets].display_name;
};

const getQualityClass = (rating?: string) => {
  const classes = {
    '优秀': 'bg-green-100 text-green-800',
    '良好': 'bg-blue-100 text-blue-800',
    '一般': 'bg-yellow-100 text-yellow-800',
    '较差': 'bg-red-100 text-red-800',
  };
  return classes[rating as keyof typeof classes] || 'bg-gray-100 text-gray-800';
};

const loadPresets = async () => {
  try {
    const res = await getClusteringPresets();
    presets.value = res;
  } catch (error) {
    message.error('加载预设模式失败');
    console.error(error);
  }
};

const loadCurrentConfig = async () => {
  try {
    const res = await getClusteringConfig();
    currentConfig.value = res;
    selectedPreset.value = res.preset_mode;
  } catch (error) {
    message.error('加载配置失败');
    console.error(error);
  }
};

const handlePreview = async () => {
  previewLoading.value = true;
  try {
    const res = await previewClusteringConfig(selectedPreset.value);
    previewResult.value = res;
    if (res.status === 'success') {
      message.success('预览生成成功');
    }
  } catch (error) {
    message.error('预览失败');
    console.error(error);
  } finally {
    previewLoading.value = false;
  }
};

const handleSave = async () => {
  saveLoading.value = true;
  try {
    await updateClusteringPreset(selectedPreset.value);
    message.success('配置已更新');
    await loadCurrentConfig();
    previewResult.value = null;
  } catch (error) {
    message.error('保存失败');
    console.error(error);
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
.clustering-config-container {
  max-width: 800px;
  margin: 0 auto;
}

.preset-item {
  transition: all 0.2s;
}

.preset-item input[type="radio"] {
  cursor: pointer;
}
</style>

