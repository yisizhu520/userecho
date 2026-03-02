"""
可视化不同 provider 的聚类效果对比

使用 t-SNE 将高维 embedding 降维到 2D，然后绘制聚类结果
"""

import asyncio
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.manifold import TSNE

from backend.utils.ai_client import AIClient

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 硬编码 48 条测试反馈（与生成脚本一致）
TEST_FEEDBACKS = [
    # 组1: 导出功能 (4 条)
    "希望能导出反馈数据为 Excel，方便做离线分析",
    "可以支持导出 CSV 格式吗？Excel 有时候打开慢",
    "能不能加个一键导出所有反馈的功能？",
    "导出功能能否支持自定义字段？",
    # 组2: 邮件通知 (4 条)
    "新反馈提交时希望能发送邮件通知",
    "可以加个邮件提醒功能吗？现在总是忘记查看反馈",
    "希望有新反馈时能收到邮件",
    "邮件通知能否支持自定义模板？",
    # 组3: 权限管理 (4 条)
    "希望能设置不同角色的权限，不是所有人都能删除反馈",
    "能否添加权限控制？我不想让所有人都能看到反馈",
    "权限管理功能太简单了，希望能支持更细粒度的控制",
    "可以加个审批流程吗？某些操作需要多人确认",
    # 组4: 移动端 (4 条)
    "手机端界面太难用了，希望优化一下",
    "移动端能不能做个 App？网页版在手机上体验不好",
    "希望移动端能支持推送通知",
    "手机上传图片经常失败，能否优化？",
    # 组5: 搜索功能 (4 条)
    "搜索功能太弱了，希望能支持模糊搜索和关键词高亮",
    "希望搜索能支持多个关键词，AND/OR 逻辑",
    "全文搜索功能不太好用，经常搜不到明明存在的内容",
    "搜索结果能否按相关性排序？",
    # 组6: API (4 条)
    "希望能提供 API 接口，方便集成到其他系统",
    "能否开放 Webhook？我想在反馈提交时触发自动化流程",
    "API 文档在哪里？想对接到我们的内部系统",
    "希望 API 支持批量操作，一次创建多条反馈",
    # 组7: 标签功能 (4 条)
    "希望能给反馈打标签，方便分类管理",
    "能否支持多标签？一个反馈可能属于多个类别",
    "标签能否支持嵌套？比如 '功能/导出/Excel'",
    "希望标签能自动推荐，根据反馈内容智能建议",
    # 组8: 评论功能 (4 条)
    "能否添加回复功能？方便和用户沟通",
    "希望支持内部备注，只有团队成员能看到",
    "评论能否支持 @ 提及功能？",
    "希望评论支持 Markdown 格式",
    # 组9: 数据可视化 (4 条)
    "希望能看到反馈趋势图，按周/月统计数量变化",
    "能否添加数据分析看板？想看反馈的分类分布",
    "希望有反馈来源统计，看看哪个渠道反馈最多",
    "能否支持自定义报表？",
    # 组10: 国际化 (4 条)
    "希望支持多语言，我们的用户来自不同国家",
    "能否添加英文界面？现在全中文不太方便",
    "需要国际化支持，至少要有中英文切换",
    "希望能根据用户浏览器语言自动切换界面语言",
    # 噪声点 (8 条) - 各种不相关的反馈
    "登录有时候很慢，能优化吗？",
    "界面配色能否支持暗色模式？",
    "这个产品很好用，谢谢！",
    "能否集成微信登录？",
    "数据备份功能在哪里？",
    "反馈列表能否支持拖拽排序？",
    "希望能添加快捷键支持",
    "团队协作功能能否加强？",
]


def load_clustering_results():
    """加载聚类结果"""
    data_file = Path(__file__).parent / "data" / "clustering_comparison_detailed.json"
    with open(data_file, encoding="utf-8") as f:
        return json.load(f)


async def get_embeddings_for_provider(feedbacks: list[str], provider: str):
    """获取指定 provider 的 embeddings"""
    print(f"  📊 获取 {len(feedbacks)} 条反馈的 {provider} embeddings...")

    ai_client = AIClient()
    embeddings = await ai_client.get_embeddings_batch(feedbacks, provider=provider)

    print(f"  ✅ 获取完成: {len(embeddings)} 条, 维度 {len(embeddings[0])}")
    return embeddings


def visualize_provider(ax, provider_name: str, embeddings: list, clusters: list, feedbacks: list[str]):
    """可视化单个 provider 的聚类结果

    Args:
        clusters: 聚类结果，格式为 [{'cluster_id': 1, 'feedbacks': [{'content': '...'}]}]
    """

    # 1. t-SNE 降维到 2D
    print(f"  🔍 正在降维 {provider_name} ({len(embeddings)} 条, {len(embeddings[0])} 维)...")
    embeddings_array = np.array(embeddings)

    # t-SNE 参数：perplexity 一般设为 5-50，数据少时用小值
    perplexity = min(30, len(embeddings) - 1)
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    embeddings_2d = tsne.fit_transform(embeddings_array)

    # 2. 准备颜色映射
    colors = [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#FFA07A",
        "#98D8C8",
        "#F7DC6F",
        "#BB8FCE",
        "#85C1E2",
        "#F8B88B",
        "#AAB7B8",
    ]

    # 3. 构建 content -> index 映射
    content_to_index = {content: idx for idx, content in enumerate(feedbacks)}

    # 4. 标记聚类
    cluster_labels = np.full(len(feedbacks), -1)  # -1 表示噪声点
    for cluster in clusters:
        cluster_id = cluster["cluster_id"]
        for feedback in cluster["feedbacks"]:
            content = feedback["content"]
            # 匹配 content（可能有空格差异，使用 strip）
            matched_idx = None
            for test_content, idx in content_to_index.items():
                if test_content.strip() == content.strip():
                    matched_idx = idx
                    break

            if matched_idx is not None:
                cluster_labels[matched_idx] = cluster_id

    # 5. 绘制散点图
    # 先画噪声点（灰色，小，透明）
    noise_mask = cluster_labels == -1
    if noise_mask.any():
        ax.scatter(
            embeddings_2d[noise_mask, 0],
            embeddings_2d[noise_mask, 1],
            c="lightgray",
            s=30,
            alpha=0.3,
            label="噪声点",
            edgecolors="gray",
            linewidths=0.5,
        )

    # 再画聚类点（彩色，大，实心）
    unique_clusters = [c["cluster_id"] for c in clusters]
    for cluster_id in unique_clusters:
        mask = cluster_labels == cluster_id
        if mask.any():
            ax.scatter(
                embeddings_2d[mask, 0],
                embeddings_2d[mask, 1],
                c=colors[cluster_id % len(colors)],
                s=100,
                alpha=0.8,
                label=f"聚类 #{cluster_id} ({mask.sum()} 条)",
                edgecolors="black",
                linewidths=1,
            )

    # 6. 设置图表样式
    ax.set_title(f"{provider_name}\n聚类数: {len(clusters)}, 噪声: {noise_mask.sum()}", fontsize=14, fontweight="bold")
    ax.set_xlabel("t-SNE 维度 1", fontsize=10)
    ax.set_ylabel("t-SNE 维度 2", fontsize=10)
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle="--")

    print(f"  ✅ {provider_name} 可视化完成")


async def main():
    print("=" * 80)
    print(" " * 25 + "聚类效果可视化对比")
    print("=" * 80)
    print()

    # 加载聚类结果
    print("📥 加载聚类结果...")
    clustering_data = load_clustering_results()

    providers = list(clustering_data.keys())
    print(f"✅ 加载了 {len(providers)} 个 provider 的结果: {', '.join(providers)}")
    print(f"✅ 反馈数量: {len(TEST_FEEDBACKS)} 条")
    print()

    # 创建画布（1 行 3 列）
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Embedding Provider 聚类效果对比 (t-SNE 降维)", fontsize=16, fontweight="bold", y=0.98)

    # 绘制每个 provider
    for idx, provider_name in enumerate(providers):
        print(f"🎨 正在可视化 {provider_name.upper()}...")

        # 获取该 provider 的 embeddings
        embeddings = await get_embeddings_for_provider(TEST_FEEDBACKS, provider_name)

        # 获取聚类结果
        provider_data = clustering_data[provider_name]
        clusters = provider_data["clusters"]

        visualize_provider(axes[idx], provider_name.upper(), embeddings, clusters, TEST_FEEDBACKS)
        print()

    # 调整布局
    plt.tight_layout()

    # 保存图片
    output_file = Path(__file__).parent / "data" / "clustering_comparison_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    print("=" * 80)
    print(f"✅ 可视化图片已保存: {output_file}")
    print("=" * 80)

    # 显示图片
    plt.show()


if __name__ == "__main__":
    asyncio.run(main())
