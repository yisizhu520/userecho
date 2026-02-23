"""优先级计算器服务

实现 MVP 优先级评分公式：
priority_score = feedback_count × 0.3 + urgent_ratio × 0.3 + strategic_match × 0.2 + recency × 0.2
"""

from datetime import datetime


class PriorityCalculator:
    """MVP 优先级计算器

    完全依赖系统内数据 + 简化版关键词识别，无需 CRM 对接
    """

    # 紧急关键词（简化版 AI 分析）
    URGENT_KEYWORDS = [
        # 中文
        "紧急",
        "急需",
        "尽快",
        "严重",
        "阻塞",
        "无法使用",
        "崩溃",
        "数据丢失",
        "安全漏洞",
        "生产环境",
        "线上问题",
        "客户投诉",
        "合同到期",
        # 英文
        "ASAP",
        "urgent",
        "critical",
        "blocker",
        "crash",
        "production",
    ]

    # 战略关键词（MVP 配置）
    STRATEGIC_KEYWORDS = [
        "信创",
        "国际化",
        "降本",
        "AI",
        "安全",
        "性能",
        "企业级",
        "SaaS",
        "私有化",
    ]

    # 权重配置
    WEIGHT_FEEDBACK_COUNT = 0.30
    WEIGHT_URGENT_RATIO = 0.30
    WEIGHT_STRATEGIC_MATCH = 0.20
    WEIGHT_RECENCY = 0.20

    # 反馈数量归一化阈值
    FEEDBACK_COUNT_MAX = 50  # 超过 50 条反馈得满分

    def calculate_score(
        self,
        topic_title: str,
        topic_description: str | None,
        feedback_contents: list[str],
        strategic_keywords: list[str] | None = None,
        last_feedback_time: datetime | None = None,
    ) -> dict:
        """
        计算 MVP 优先级评分

        Args:
            topic_title: 主题标题
            topic_description: 主题描述
            feedback_contents: 关联反馈内容列表
            strategic_keywords: 战略关键词列表 (默认使用类配置)
            last_feedback_time: 最近反馈时间

        Returns:
            {
                "total_score": 85.5,           # 总分 (0-100)
                "feedback_count": 23,          # 反馈数量
                "feedback_count_score": 30,    # 反馈数量分 (满分 30)
                "urgent_ratio": 0.4,           # 紧急反馈占比
                "urgent_score": 12,            # 紧急程度分 (满分 30)
                "strategic_keywords_matched": ["信创"], # 命中的战略关键词
                "strategic_score": 20,         # 战略匹配分 (满分 20)
                "recency_score": 18,           # 时效性分 (满分 20)
                "last_feedback_days": 2        # 距最近反馈天数
            }
        """
        if strategic_keywords is None:
            strategic_keywords = self.STRATEGIC_KEYWORDS

        feedback_count = len(feedback_contents)

        # 1. 反馈数量分数 (0-30)
        feedback_count_score = self._calculate_feedback_count_score(feedback_count)

        # 2. 紧急程度分数 (0-30)
        urgent_ratio, urgent_score = self._calculate_urgent_score(feedback_contents)

        # 3. 战略匹配分数 (0-20)
        matched_keywords, strategic_score = self._calculate_strategic_score(
            topic_title, topic_description, strategic_keywords
        )

        # 4. 时效性分数 (0-20)
        recency_score, last_feedback_days = self._calculate_recency_score(last_feedback_time)

        # 计算总分
        total_score = round(feedback_count_score + urgent_score + strategic_score + recency_score, 1)

        return {
            "total_score": total_score,
            "feedback_count": feedback_count,
            "feedback_count_score": round(feedback_count_score, 1),
            "urgent_ratio": round(urgent_ratio, 2),
            "urgent_score": round(urgent_score, 1),
            "strategic_keywords_matched": matched_keywords,
            "strategic_score": round(strategic_score, 1),
            "recency_score": round(recency_score, 1),
            "last_feedback_days": last_feedback_days,
        }

    def _calculate_feedback_count_score(self, count: int) -> float:
        """
        计算反馈数量分数

        归一化到 0-30 分，超过阈值得满分
        """
        max_score = self.WEIGHT_FEEDBACK_COUNT * 100
        if count >= self.FEEDBACK_COUNT_MAX:
            return max_score
        return (count / self.FEEDBACK_COUNT_MAX) * max_score

    def _calculate_urgent_score(self, feedback_contents: list[str]) -> tuple[float, float]:
        """
        计算紧急程度分数

        通过关键词匹配识别紧急反馈的占比
        返回 (紧急占比, 紧急分数)
        """
        if not feedback_contents:
            return 0.0, 0.0

        urgent_count = 0
        for content in feedback_contents:
            content_lower = content.lower()
            for keyword in self.URGENT_KEYWORDS:
                if keyword.lower() in content_lower:
                    urgent_count += 1
                    break  # 一条反馈只计一次

        urgent_ratio = urgent_count / len(feedback_contents)
        max_score = self.WEIGHT_URGENT_RATIO * 100
        urgent_score = urgent_ratio * max_score

        return urgent_ratio, urgent_score

    def _calculate_strategic_score(
        self,
        title: str,
        description: str | None,
        strategic_keywords: list[str],
    ) -> tuple[list[str], float]:
        """
        计算战略匹配分数

        匹配主题标题和描述中的战略关键词
        返回 (匹配的关键词列表, 战略分数)
        """
        if not strategic_keywords:
            return [], 0.0

        content = f"{title} {description or ''}".lower()
        matched_keywords = [kw for kw in strategic_keywords if kw.lower() in content]

        # 匹配到任意一个关键词即得满分（二元判断）
        # 如果想要更细粒度，可以改为 len(matched) / len(keywords)
        max_score = self.WEIGHT_STRATEGIC_MATCH * 100
        strategic_score = max_score if matched_keywords else 0.0

        return matched_keywords, strategic_score

    def _calculate_recency_score(self, last_feedback_time: datetime | None) -> tuple[float, int | None]:
        """
        计算时效性分数

        最近反馈时间越近，分数越高
        返回 (时效性分数, 距最近反馈天数)
        """
        max_score = self.WEIGHT_RECENCY * 100

        if not last_feedback_time:
            return 0.0, None

        now = datetime.now()
        # 处理时区：如果 last_feedback_time 有时区信息，转换为 naive datetime
        if last_feedback_time.tzinfo is not None:
            last_feedback_time = last_feedback_time.replace(tzinfo=None)

        days_ago = (now - last_feedback_time).days

        # 7 天内得满分，逐渐衰减，30 天后得 0 分
        if days_ago <= 7:
            recency_score = max_score
        elif days_ago >= 30:
            recency_score = 0.0
        else:
            # 线性衰减：7-30 天
            recency_score = max_score * (1 - (days_ago - 7) / 23)

        return recency_score, days_ago


# 全局单例
priority_calculator = PriorityCalculator()
