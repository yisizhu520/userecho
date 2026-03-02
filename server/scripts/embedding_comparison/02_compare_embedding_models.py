"""步骤 2: 对比 Embedding 模型

在标注数据集上对比 Volcengine, OpenAI, GLM, Qwen3 的效果

运行方式：
    cd server
    python scripts/embedding_comparison/02_compare_embedding_models.py
"""

import asyncio
import json
import os
import random
from pathlib import Path

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from backend.common.log import log
from backend.core.conf import settings
from backend.utils.ai_client import AIClient


async def get_embeddings_for_model(
    model_provider: str,
    texts: list[str],
) -> list[list[float]]:
    """
    为指定模型获取 embeddings
    
    Args:
        model_provider: 模型提供商 (volcengine, openai, glm, qwen)
        texts: 文本列表
        
    Returns:
        embeddings 列表
    """
    # ✅ 直接使用 provider 参数，不修改全局状态
    client = AIClient()
    
    print(f"Fetching embeddings from {model_provider}...")
    embeddings = await client.get_embeddings_batch(texts, batch_size=50, provider=model_provider)
    
    # 过滤 None
    valid_embeddings = [emb for emb in embeddings if emb is not None]
    
    if len(valid_embeddings) != len(texts):
        print(f"{model_provider}: {len(texts) - len(valid_embeddings)} embeddings failed")
    
    return embeddings


def calculate_similarity(emb1: list[float], emb2: list[float]) -> float:
    """计算余弦相似度"""
    if emb1 is None or emb2 is None:
        return 0.0
    
    arr1 = np.array(emb1)
    arr2 = np.array(emb2)
    
    return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2)))


async def evaluate_model(
    model_provider: str,
    annotations: list[dict],
    threshold: float = 0.85,
) -> dict:
    """
    评估单个模型
    
    Args:
        model_provider: 模型提供商
        annotations: 标注数据集
        threshold: 相似度阈值
        
    Returns:
        评估指标
    """
    print(f"\n{'=' * 80}")
    print(f"评估模型: {model_provider}".center(80))
    print(f"{'=' * 80}\n")
    
    # 1. 准备文本
    texts = []
    for ann in annotations:
        texts.append(ann['feedback1_content'])
        texts.append(ann['feedback2_content'])
    
    # 2. 获取 embeddings
    try:
        embeddings = await get_embeddings_for_model(model_provider, texts)
    except Exception as e:
        log.error(f"Failed to get embeddings from {model_provider}: {e}")
        return {
            "model": model_provider,
            "status": "failed",
            "error": str(e),
        }
    
    # 3. 计算相似度并评估
    y_true = []
    y_pred = []
    y_scores = []
    suspicious_pairs = []
    
    for i, ann in enumerate(annotations):
        emb1 = embeddings[i * 2]
        emb2 = embeddings[i * 2 + 1]
        
        if emb1 is None or emb2 is None:
            continue
        
        # 计算相似度
        sim = calculate_similarity(emb1, emb2)
        
        y_true.append(ann['label'])
        y_pred.append(1 if sim >= threshold else 0)
        y_scores.append(sim)
        
        # 记录可疑对（高相似度但标注为不相似）
        if sim >= threshold and ann['label'] == 0:
            suspicious_pairs.append({
                'text1': ann['feedback1_content'][:50] + "...",
                'text2': ann['feedback2_content'][:50] + "...",
                'similarity': float(sim),
                'label': ann['label'],
            })
    
    if not y_true:
        return {
            "model": model_provider,
            "status": "failed",
            "error": "No valid embeddings",
        }
    
    # 4. 计算指标
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_scores) if len(set(y_true)) > 1 else 0.0
    
    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    
    # 相似度分布统计
    similar_scores = [s for s, label in zip(y_scores, y_true) if label == 1]
    dissimilar_scores = [s for s, label in zip(y_scores, y_true) if label == 0]
    
    result = {
        "model": model_provider,
        "status": "success",
        "threshold": threshold,
        "metrics": {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc": float(auc),
        },
        "confusion_matrix": {
            "true_positive": int(tp),
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
        },
        "similarity_distribution": {
            "similar_mean": float(np.mean(similar_scores)) if similar_scores else 0.0,
            "similar_std": float(np.std(similar_scores)) if similar_scores else 0.0,
            "dissimilar_mean": float(np.mean(dissimilar_scores)) if dissimilar_scores else 0.0,
            "dissimilar_std": float(np.std(dissimilar_scores)) if dissimilar_scores else 0.0,
        },
        "suspicious_pairs_count": len(suspicious_pairs),
        "suspicious_pairs_sample": suspicious_pairs[:5],  # 只保存前5个
    }
    
    # 打印结果
    print(f"模型: {model_provider}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1 Score: {f1:.3f}")
    print(f"AUC: {auc:.3f}")
    print(f"可疑对数量: {len(suspicious_pairs)}")
    print(f"相似对平均相似度: {result['similarity_distribution']['similar_mean']:.3f}")
    print(f"不相似对平均相似度: {result['similarity_distribution']['dissimilar_mean']:.3f}")
    
    return result


def evaluate_random_baseline(annotations: list[dict]) -> dict:
    """
    随机基线 - 证明实验有效性
    
    如果你的最好模型 F1 Score 只比随机猜测好一点点,说明模型几乎没用。
    
    Args:
        annotations: 标注数据集
        
    Returns:
        评估指标
    """
    print(f"\n{'=' * 80}")
    print("评估随机基线 (Random Baseline)".center(80))
    print(f"{'=' * 80}\n")
    
    y_true = [ann['label'] for ann in annotations]
    y_pred = [random.choice([0, 1]) for _ in y_true]
    y_scores = [random.random() for _ in y_true]  # 随机相似度得分
    
    # 计算指标
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_scores) if len(set(y_true)) > 1 else 0.0
    
    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    
    result = {
        "model": "random_baseline",
        "status": "success",
        "threshold": 0.5,  # 随机阈值
        "metrics": {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc": float(auc),
        },
        "confusion_matrix": {
            "true_positive": int(tp),
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
        },
        "similarity_distribution": {
            "similar_mean": 0.5,
            "similar_std": 0.29,
            "dissimilar_mean": 0.5,
            "dissimilar_std": 0.29,
        },
        "suspicious_pairs_count": 0,
        "suspicious_pairs_sample": [],
    }
    
    # 打印结果
    print(f"模型: Random Baseline")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1 Score: {f1:.3f}")
    print(f"AUC: {auc:.3f}")
    print(f"\n⚠️  随机基线用于证明实验有效性")
    print(f"   如果最好模型的 F1 Score 接近随机基线,说明模型几乎没用\n")
    
    return result


async def compare_all_models(annotations: list[dict]) -> list[dict]:
    """
    对比所有模型
    
    Args:
        annotations: 标注数据集
        
    Returns:
        所有模型的评估结果
    """
    # 检查 API Keys
    models_to_test = []
    
    if getattr(settings, "VOLCENGINE_API_KEY", None):
        models_to_test.append("volcengine")
    else:
        log.warning("VOLCENGINE_API_KEY not found, skipping volcengine")
    
    if getattr(settings, "OPENAI_API_KEY", None):
        models_to_test.append("openai")
    else:
        log.warning("OPENAI_API_KEY not found, skipping openai")
    
    if getattr(settings, "GLM_API_KEY", None):
        models_to_test.append("glm")
    else:
        log.warning("GLM_API_KEY not found, skipping glm")
    
    if getattr(settings, "DASHSCOPE_API_KEY", None):
        models_to_test.append("qwen")
    else:
        log.warning("DASHSCOPE_API_KEY not found, skipping qwen")
    
    if not models_to_test:
        log.error("No API keys configured. Please set at least one of: VOLCENGINE_API_KEY, OPENAI_API_KEY, GLM_API_KEY")
        return []
    
    print(f"\n将测试以下模型: {', '.join(models_to_test)}\n")
    
    # ✅ 添加随机基线
    print("\n🎲 首先评估随机基线...\n")
    baseline_result = evaluate_random_baseline(annotations)
    results = [baseline_result]
    
    # 评估所有模型
    for model in models_to_test:
        try:
            result = await evaluate_model(model, annotations, threshold=0.85)
            results.append(result)
        except Exception as e:
            log.error(f"Failed to evaluate {model}: {e}")
            results.append({
                "model": model,
                "status": "failed",
                "error": str(e),
            })
    
    return results


def generate_comparison_report(results: list[dict], output_file: Path) -> None:
    """
    生成对比报告
    
    Args:
        results: 评估结果列表
        output_file: 输出文件路径
    """
    report_lines = [
        "=" * 100,
        "Embedding 模型对比实验报告".center(100),
        "=" * 100,
        "",
    ]
    
    # 1. 总览表格
    report_lines.extend([
        "## 1. 模型性能对比",
        "",
        "| 模型 | Precision | Recall | F1 Score | AUC | 可疑对数量 |",
        "|------|-----------|--------|----------|-----|-----------|",
    ])
    
    for result in results:
        if result["status"] == "success":
            m = result["metrics"]
            model = result["model"]
            suspicious = result["suspicious_pairs_count"]
            
            report_lines.append(
                f"| {model:<12} | {m['precision']:.3f} | {m['recall']:.3f} | "
                f"{m['f1_score']:.3f} | {m['auc']:.3f} | {suspicious} |"
            )
        else:
            report_lines.append(f"| {result['model']:<12} | FAILED | - | - | - | - |")
    
    report_lines.append("")
    
    # 2. 相似度分布
    report_lines.extend([
        "## 2. 相似度分布分析",
        "",
        "（理想情况：相似对平均相似度高，不相似对平均相似度低，两者差距大）",
        "",
        "| 模型 | 相似对均值 | 相似对标准差 | 不相似对均值 | 不相似对标准差 | 分离度 |",
        "|------|-----------|-------------|-------------|---------------|-------|",
    ])
    
    for result in results:
        if result["status"] == "success":
            dist = result["similarity_distribution"]
            model = result["model"]
            separation = dist["similar_mean"] - dist["dissimilar_mean"]
            
            report_lines.append(
                f"| {model:<12} | {dist['similar_mean']:.3f} | {dist['similar_std']:.3f} | "
                f"{dist['dissimilar_mean']:.3f} | {dist['dissimilar_std']:.3f} | {separation:.3f} |"
            )
    
    report_lines.append("")
    
    # 3. 推荐结论
    report_lines.extend([
        "## 3. 推荐结论",
        "",
    ])
    
    # 找出最佳模型（F1 Score 最高）
    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        best_model = max(successful_results, key=lambda r: r["metrics"]["f1_score"])
        
        report_lines.append(f"🏆 **最佳模型**: {best_model['model']}")
        report_lines.append(f"   - F1 Score: {best_model['metrics']['f1_score']:.3f}")
        report_lines.append(f"   - 可疑对数量: {best_model['suspicious_pairs_count']}")
        report_lines.append(f"   - 相似度分离度: {best_model['similarity_distribution']['similar_mean'] - best_model['similarity_distribution']['dissimilar_mean']:.3f}")
        report_lines.append("")
        
        # 对比基线（volcengine）
        baseline = next((r for r in results if r["model"] == "volcengine" and r["status"] == "success"), None)
        if baseline and best_model["model"] != "volcengine":
            f1_improvement = (best_model["metrics"]["f1_score"] - baseline["metrics"]["f1_score"]) / baseline["metrics"]["f1_score"] * 100
            suspicious_reduction = (baseline["suspicious_pairs_count"] - best_model["suspicious_pairs_count"]) / max(baseline["suspicious_pairs_count"], 1) * 100
            
            report_lines.append(f"📊 **相比 Volcengine 基线**:")
            report_lines.append(f"   - F1 Score 提升: {f1_improvement:+.1f}%")
            report_lines.append(f"   - 可疑对减少: {suspicious_reduction:+.1f}%")
            report_lines.append("")
    
    # 4. 详细指标
    report_lines.extend([
        "## 4. 详细指标",
        "",
    ])
    
    for result in results:
        if result["status"] == "success":
            report_lines.extend([
                f"### {result['model']}",
                "",
                f"**混淆矩阵**:",
                f"- True Positive: {result['confusion_matrix']['true_positive']}",
                f"- True Negative: {result['confusion_matrix']['true_negative']}",
                f"- False Positive: {result['confusion_matrix']['false_positive']}",
                f"- False Negative: {result['confusion_matrix']['false_negative']}",
                "",
                f"**可疑对样本** (高相似度但标注为不相似):",
                "",
            ])
            
            for i, pair in enumerate(result["suspicious_pairs_sample"], 1):
                report_lines.append(f"{i}. 相似度: {pair['similarity']:.3f}")
                report_lines.append(f"   - {pair['text1']}")
                report_lines.append(f"   - {pair['text2']}")
                report_lines.append("")
    
    # 保存报告
    report_content = "\n".join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 同时打印到控制台
    print("\n" + report_content)


async def main():
    """主流程"""
    # 输入输出目录
    data_dir = Path(__file__).parent / "data"
    annotation_file = data_dir / "annotation_dataset.json"
    
    if not annotation_file.exists():
        print(f"❌ 标注文件不存在: {annotation_file}")
        print("请先运行: 01_prepare_annotation_dataset.py")
        return
    
    # 1. 加载标注数据
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    print(f"\n✅ 加载标注数据: {len(annotations)} 对")
    similar_count = sum(1 for a in annotations if a['label'] == 1)
    dissimilar_count = sum(1 for a in annotations if a['label'] == 0)
    print(f"   - 相似对: {similar_count}")
    print(f"   - 不相似对: {dissimilar_count}")
    
    # 2. 对比所有模型
    print("\n🚀 开始对比实验...\n")
    results = await compare_all_models(annotations)
    
    if not results:
        print("❌ 没有完成任何模型评估")
        return
    
    # 3. 保存结果
    results_file = data_dir / "model_comparison_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 评估结果已保存: {results_file}")
    
    # 4. 生成报告
    report_file = data_dir / "comparison_report.md"
    generate_comparison_report(results, report_file)
    
    print(f"📄 对比报告已保存: {report_file}")
    print("\n✅ 实验完成！")
    print(f"\n下一步: 根据报告选择最优模型，更新 .env 配置")


if __name__ == "__main__":
    asyncio.run(main())
