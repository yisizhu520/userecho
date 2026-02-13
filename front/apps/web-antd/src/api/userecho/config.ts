/**
 * 租户配置 API
 */

import { requestClient } from '#/api/request';

/** 预设模式信息 */
export interface PresetInfo {
  display_name: string;
  description: string;
  use_case: string;
}

/** 预设模式列表 */
export interface ClusteringPresets {
  strict: PresetInfo;
  standard: PresetInfo;
  relaxed: PresetInfo;
}

/** 聚类配置 */
export interface ClusteringConfig {
  preset_mode: string;
  similarity_threshold: number;
  min_samples: number;
  min_silhouette: number;
  max_noise_ratio: number;
}

/** 预览结果 */
export interface PreviewResult {
  status: 'success' | 'insufficient_data' | 'embedding_failed';
  message?: string;
  test_samples?: number;
  valid_embeddings?: number;
  preview?: {
    clusters_count: number;
    clusters_range: string;
    coverage_rate: number;
    coverage_percentage: string;
    quality_rating: string;
    silhouette_score: number;
    noise_ratio: number;
  };
  config?: {
    similarity_threshold: number;
    min_samples: number;
    min_silhouette: number;
    max_noise_ratio: number;
  };
}

/**
 * 获取聚类预设模式列表
 */
export async function getClusteringPresets() {
  return requestClient.get<ClusteringPresets>('/api/v1/app/config/clustering/presets');
}

/**
 * 获取当前聚类配置
 */
export async function getClusteringConfig() {
  return requestClient.get<ClusteringConfig>('/api/v1/app/config/clustering');
}

/**
 * 更新聚类预设模式
 */
export async function updateClusteringPreset(presetMode: string) {
  return requestClient.post<ClusteringConfig>('/api/v1/app/config/clustering/preset', {
    preset_mode: presetMode,
  });
}

/**
 * 预览聚类配置效果
 */
export async function previewClusteringConfig(presetMode: string) {
  return requestClient.post<PreviewResult>('/api/v1/app/config/clustering/preview', {
    preset_mode: presetMode,
  });
}

/**
 * 微调聚类参数（高级功能）
 */
export async function updateClusteringParams(params: Record<string, any>) {
  return requestClient.put<ClusteringConfig>('/api/v1/app/config/clustering/params', {
    params,
  });
}

