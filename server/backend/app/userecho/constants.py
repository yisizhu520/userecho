"""UserEcho 常量定义"""

# 聚类预设模式
CLUSTERING_PRESETS = {
    'strict': {
        'display_name': '严格聚类',
        'description': '只将高度相似的反馈聚在一起，适合需求差异明显的场景',
        'use_case': '适用于：产品初期、反馈类型明确、需要精准分类',
        'params': {
            'similarity_threshold': 0.90,
            'min_samples': 3,
            'min_silhouette': 0.4,
            'max_noise_ratio': 0.6,
        },
    },
    'standard': {
        'display_name': '标准聚类',
        'description': '平衡聚类质量和覆盖范围，适合大多数场景（推荐）',
        'use_case': '适用于：日常使用、反馈量适中、需要平衡质量与效率',
        'params': {
            'similarity_threshold': 0.85,
            'min_samples': 2,
            'min_silhouette': 0.3,
            'max_noise_ratio': 0.5,
        },
    },
    'relaxed': {
        'display_name': '宽松聚类',
        'description': '尽可能将相似反馈聚在一起，适合反馈量大且需要快速分类的场景',
        'use_case': '适用于：反馈量大、需要快速归纳、容忍一定的分类误差',
        'params': {
            'similarity_threshold': 0.75,
            'min_samples': 2,
            'min_silhouette': 0.2,
            'max_noise_ratio': 0.7,
        },
    },
}

# 默认聚类配置
DEFAULT_CLUSTERING_CONFIG = {
    'preset_mode': 'standard',
    **CLUSTERING_PRESETS['standard']['params'],
}
