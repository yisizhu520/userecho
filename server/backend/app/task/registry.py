"""任务元数据注册表

为每个 Celery 任务声明业务元数据，TaskBase 钩子自动从这里查找。
现有任务代码零改动，只需在此注册。

用法：
    TASK_METADATA["celery.task.name"] = TaskMeta(
        category="ai_embedding",
        display_name="反馈向量生成",
        tenant_id_arg_index=2,
    )
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TaskMeta:
    """单个任务的元数据"""

    category: str
    display_name: str
    # tenant_id 在 args 中的位置索引（None 表示无法从参数提取，如 batch 任务）
    tenant_id_arg_index: int | None = None
    # 需要提取到 context 中的 kwargs 键名
    context_keys: tuple[str, ...] = field(default_factory=tuple)


# ============================================================
# 注册所有任务元数据
# key = Celery task name（@shared_task 的 name 参数）
# ============================================================
TASK_METADATA: dict[str, TaskMeta] = {
    # --- AI 向量化 ---
    "userecho.generate_feedback_embedding": TaskMeta(
        category="ai_embedding",
        display_name="反馈向量生成",
        tenant_id_arg_index=2,  # args: (feedback_id, content, tenant_id)
    ),
    "userecho.generate_topic_centroid": TaskMeta(
        category="ai_embedding",
        display_name="需求质心生成",
        tenant_id_arg_index=1,  # args: (topic_id, tenant_id)
    ),
    # --- AI 聚类 ---
    "userecho_clustering_batch": TaskMeta(
        category="ai_clustering",
        display_name="AI 智能聚类",
        tenant_id_arg_index=0,  # args: (tenant_id, ...)
    ),
    # --- AI 截图识别 ---
    "userecho_analyze_screenshot": TaskMeta(
        category="ai_screenshot",
        display_name="截图智能识别",
        tenant_id_arg_index=2,  # args: (file_path, content_type, tenant_id, ...)
    ),
    "userecho_analyze_screenshot_url": TaskMeta(
        category="ai_screenshot",
        display_name="截图URL识别",
        tenant_id_arg_index=1,  # kwargs: screenshot_url, tenant_id
    ),
    # --- AI 洞察报告 ---
    "userecho.generate_insight_report": TaskMeta(
        category="ai_insight",
        display_name="洞察报告生成",
        tenant_id_arg_index=0,  # args: (tenant_id, time_range, format)
    ),
    # --- AI 摘要 ---
    "userecho.generate_feedback_summary": TaskMeta(
        category="ai_summary",
        display_name="AI 摘要生成",
        tenant_id_arg_index=2,  # args: (feedback_id, content, tenant_id)
    ),
    # --- 批量任务 ---
    "batch.process_batch_job": TaskMeta(
        category="batch",
        display_name="批量任务",
        tenant_id_arg_index=None,  # 从 batch_job 表获取
    ),
    # --- 定时清理任务 ---
    "backend.app.task.tasks.db_log.tasks.delete_db_opera_log": TaskMeta(
        category="maintenance",
        display_name="清理操作日志",
        tenant_id_arg_index=None,
    ),
    "backend.app.task.tasks.db_log.tasks.delete_db_login_log": TaskMeta(
        category="maintenance",
        display_name="清理登录日志",
        tenant_id_arg_index=None,
    ),
    # --- 定时洞察 ---
    "userecho.generate_weekly_insights": TaskMeta(
        category="ai_insight",
        display_name="每周洞察生成",
        tenant_id_arg_index=None,
    ),
    "userecho.generate_daily_insights": TaskMeta(
        category="ai_insight",
        display_name="每日洞察生成",
        tenant_id_arg_index=None,
    ),
}


def get_task_meta(task_name: str) -> TaskMeta | None:
    """获取任务元数据，未注册返回 None"""
    return TASK_METADATA.get(task_name)


def extract_tenant_id(meta: TaskMeta, args: tuple, kwargs: dict) -> str | None:
    """从任务参数中提取 tenant_id"""
    # 优先从 kwargs 提取
    if "tenant_id" in kwargs:
        return str(kwargs["tenant_id"])

    # 从 args 提取
    if meta.tenant_id_arg_index is not None and args and len(args) > meta.tenant_id_arg_index:
        return str(args[meta.tenant_id_arg_index])

    return None


def extract_context(meta: TaskMeta, args: tuple, kwargs: dict) -> dict:
    """从任务参数中提取业务上下文"""
    context: dict = {}

    # 提取指定的 kwargs 键
    for key in meta.context_keys:
        if key in kwargs:
            context[key] = kwargs[key]

    # 根据分类提取标准参数
    if meta.category == "ai_embedding" and args:
        context["target_id"] = str(args[0])  # feedback_id 或 topic_id
    elif meta.category == "ai_screenshot" and args:
        if meta.tenant_id_arg_index == 2 and len(args) > 0:
            context["file_path"] = str(args[0])
        elif meta.tenant_id_arg_index == 1:
            context["screenshot_url"] = kwargs.get("screenshot_url", str(args[0]) if args else "")
    elif meta.category == "ai_summary" and args:
        context["feedback_id"] = str(args[0])
    elif meta.category == "ai_clustering" and args:
        if len(args) > 1:
            context["max_feedbacks"] = args[1]
    elif meta.category == "ai_insight" and args:
        if len(args) > 1:
            context["time_range"] = str(args[1])
    elif meta.category == "batch" and args:
        context["batch_job_id"] = str(args[0])

    return context
