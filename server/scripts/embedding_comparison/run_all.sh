#!/bin/bash

# Embedding 模型对比实验 - 一键运行脚本
#
# 使用方法:
#   bash scripts/embedding_comparison/run_all.sh

set -e

echo "=================================="
echo "Embedding 模型对比实验"
echo "=================================="
echo ""

# 检查是否在 server 目录
if [ ! -f "backend/main.py" ]; then
    echo "❌ 请在 server 目录下运行此脚本"
    exit 1
fi

# 步骤 0: 验证配置
echo "步骤 0: 验证配置..."
echo ""
python scripts/embedding_comparison/00_verify_config.py

read -p "配置验证完成,按 Enter 继续..."

# 步骤 1: 准备标注数据
echo ""
echo "=================================="
echo "步骤 1: 准备标注数据"
echo "=================================="
echo ""
echo "⚠️  这一步需要人工标注,预计耗时 30-60 分钟"
echo ""
read -p "按 Enter 开始..."

python scripts/embedding_comparison/01_prepare_annotation_dataset.py

if [ ! -f "scripts/embedding_comparison/data/annotation_dataset.json" ]; then
    echo ""
    echo "❌ 标注数据未生成,退出"
    exit 1
fi

# 步骤 2: 对比模型
echo ""
echo "=================================="
echo "步骤 2: 对比 Embedding 模型"
echo "=================================="
echo ""
read -p "按 Enter 开始..."

python scripts/embedding_comparison/02_compare_embedding_models.py

# 步骤 3: 真实聚类测试 (可选)
echo ""
echo "=================================="
echo "步骤 3: 真实聚类质量测试 (可选)"
echo "=================================="
echo ""
read -p "是否运行真实聚类测试? (y/n): " run_clustering

if [ "$run_clustering" = "y" ] || [ "$run_clustering" = "Y" ]; then
    python scripts/embedding_comparison/03_test_clustering_quality.py
fi

# 完成
echo ""
echo "=================================="
echo "实验完成!"
echo "=================================="
echo ""
echo "📄 查看报告:"
echo "  - scripts/embedding_comparison/data/comparison_report.md"
if [ "$run_clustering" = "y" ] || [ "$run_clustering" = "Y" ]; then
    echo "  - scripts/embedding_comparison/data/clustering_quality_report.md"
fi
echo ""
echo "下一步: 根据报告选择最优模型,更新 .env 配置"
echo ""
