"""洞察生成服务 - 核心业务逻辑"""

import json
import time

from datetime import datetime, timedelta
from typing import Any

from jinja2 import Template
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_insight import crud_insight
from backend.app.userecho.model.customer import Customer
from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.model.topic import Topic
from backend.common.log import log
from backend.utils.ai_client import ai_client


class InsightService:
    """洞察生成服务（4 种类型统一入口）"""

    # 紧急程度优先级（用于排序）
    URGENCY_PRIORITY = {
        'critical': 0,
        'high': 1,
        'medium': 2,
        'low': 3,
    }

    async def generate_insight(
        self,
        db: AsyncSession,
        tenant_id: str,
        insight_type: str,
        time_range: str = 'this_week',
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        统一的洞察生成接口

        策略：
        1. 检查缓存（是否已生成过）
        2. 根据类型调用对应方法
        3. 持久化结果到 insights 表
        4. 返回结构化数据

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            insight_type: 洞察类型
            time_range: 时间范围
            force_refresh: 是否强制刷新

        Returns:
            洞察内容（dict）
        """
        start_time = time.time()

        # 1. 解析时间范围
        start_date, end_date = self._parse_time_range(time_range)

        # 2. 检查缓存
        if not force_refresh:
            cached = await crud_insight.get_cached_insight(
                db, tenant_id, insight_type, time_range, start_date, end_date
            )
            if cached:
                log.info(f'Using cached insight: {insight_type} for tenant {tenant_id}')
                return cached.content

        # 3. 根据类型生成洞察
        if insight_type == 'priority_suggestion':
            content = await self._generate_priority_suggestions(db, tenant_id)
        elif insight_type == 'high_risk':
            content = await self._identify_high_risk_topics(db, tenant_id)
        elif insight_type == 'weekly_report':
            content = await self._generate_weekly_report(db, tenant_id, start_date, end_date)
        elif insight_type == 'sentiment_trend':
            content = await self._calculate_sentiment_trend(db, tenant_id, start_date, end_date)
        else:
            raise ValueError(f'Unknown insight_type: {insight_type}')

        # 4. 计算执行时间
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 5. 持久化（数据库只存储日期，不存储时间）
        await crud_insight.create_insight(
            db=db,
            tenant_id=tenant_id,
            insight_type=insight_type,
            time_range=time_range,
            start_date=start_date.date(),
            end_date=end_date.date(),
            content=content,
            generated_by='hybrid',
            execution_time_ms=execution_time_ms,
        )

        log.info(f'Generated {insight_type} insight for tenant {tenant_id} in {execution_time_ms}ms')

        return content

    def _parse_time_range(self, time_range: str) -> tuple[datetime, datetime]:
        """解析时间范围"""
        now = datetime.now()
        today = now.date()

        if time_range == 'this_week':
            # 本周一到今天
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif time_range == 'this_month':
            # 本月1号到今天
            start_date = today.replace(day=1)
            end_date = today
        else:
            # 默认最近7天
            start_date = today - timedelta(days=7)
            end_date = today

        # 转换为 datetime：start_date 00:00:00, end_date 23:59:59
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        return start_datetime, end_datetime

    async def _generate_priority_suggestions(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict[str, Any]:
        """
        生成优先级建议（混合方案：规则引擎 + AI 增强）

        Returns:
            {
                "top_recommendations": [...],
                "summary": "...",
                "generated_at": "..."
            }
        """
        from backend.app.userecho.model.priority_score import PriorityScore

        # 1. 查询所有未完成的 Topic（有优先级评分）
        query = (
            select(Topic)
            .join(PriorityScore, Topic.id == PriorityScore.topic_id)
            .where(
                and_(
                    Topic.tenant_id == tenant_id,
                    Topic.status.in_(['pending', 'planned', 'in_progress']),
                    Topic.deleted_at.is_(None),
                )
            )
        )

        result = await db.execute(query)
        topics = result.scalars().all()

        if not topics:
            return {
                'top_recommendations': [],
                'summary': '暂无待处理的需求。',
                'generated_at': datetime.now().isoformat(),
            }

        # 2. 计算每个 Topic 的 ROI 和紧急程度
        scored_topics = []
        for topic in topics:
            if not topic.priority_score:
                continue

            priority_score = topic.priority_score.total_score
            dev_cost = topic.priority_score.dev_cost
            roi = priority_score / dev_cost if dev_cost > 0 else 0

            # 判断紧急程度
            urgency_level = await self._classify_urgency(db, topic)

            # 生成建议理由
            reason = await self._generate_reason_template(db, topic, urgency_level, roi)

            # 建议操作
            suggested_action = self._get_suggested_action(urgency_level)

            scored_topics.append({
                'topic_id': topic.id,
                'title': topic.title,
                'reason': reason,
                'urgency_level': urgency_level,
                'estimated_roi': round(roi, 2),
                'suggested_action': suggested_action,
                'category': topic.category,
                'feedback_count': topic.feedback_count,
            })

        # 3. 排序：critical > high > medium，同级按 ROI 降序
        scored_topics.sort(key=lambda x: (self.URGENCY_PRIORITY[x['urgency_level']], -x['estimated_roi']))

        # 4. 取前3个
        top_3 = scored_topics[:3]

        # 5. AI 生成总结（可选，失败不影响主流程）
        summary = await self._enhance_suggestions_with_ai(top_3)

        return {'top_recommendations': top_3, 'summary': summary, 'generated_at': datetime.now().isoformat()}

    async def _classify_urgency(self, db: AsyncSession, topic: Topic) -> str:
        """规则：判断紧急程度"""
        if not topic.priority_score:
            return 'low'

        score = topic.priority_score.total_score

        # 获取关联的客户
        query = (
            select(Customer)
            .join(Feedback, Customer.id == Feedback.customer_id)
            .where(and_(Feedback.topic_id == topic.id, Feedback.tenant_id == topic.tenant_id))
            .distinct()
        )
        result = await db.execute(query)
        customers = result.scalars().all()

        has_major_customer = any(c.customer_type in ['major', 'strategic'] for c in customers)
        is_bug = topic.category == 'bug'

        # 应用规则
        if score >= 50 and has_major_customer and is_bug:
            return 'critical'
        if score >= 20:
            return 'high'
        if score >= 5:
            return 'medium'
        return 'low'

    async def _generate_reason_template(
        self,
        db: AsyncSession,
        topic: Topic,
        urgency_level: str,
        roi: float,
    ) -> str:
        """生成建议理由（模板）"""
        # 获取客户数量
        query = (
            select(func.count(func.distinct(Customer.id)))
            .join(Feedback, Customer.id == Feedback.customer_id)
            .where(and_(Feedback.topic_id == topic.id, Feedback.tenant_id == topic.tenant_id))
        )
        result = await db.execute(query)
        customer_count = result.scalar() or 0

        # 获取大客户数量
        query_major = (
            select(func.count(func.distinct(Customer.id)))
            .join(Feedback, Customer.id == Feedback.customer_id)
            .where(
                and_(
                    Feedback.topic_id == topic.id,
                    Feedback.tenant_id == topic.tenant_id,
                    Customer.customer_type.in_(['major', 'strategic']),
                )
            )
        )
        result_major = await db.execute(query_major)
        major_customer_count = result_major.scalar() or 0

        # 构建理由
        parts = []

        if major_customer_count > 0:
            parts.append(f'影响 {major_customer_count} 个大客户')

        if customer_count > major_customer_count:
            parts.append(f'共 {customer_count} 个客户反馈')
        elif customer_count > 0 and major_customer_count == 0:
            parts.append(f'影响 {customer_count} 个客户')

        if topic.priority_score:
            parts.append(f'优先级 {topic.priority_score.total_score:.1f} 分')

            # 预计开发时间
            dev_cost = topic.priority_score.dev_cost
            if dev_cost == 1:
                parts.append('预计 1 天可完成')
            elif dev_cost == 3:
                parts.append('预计 3 天可完成')
            elif dev_cost == 5:
                parts.append('预计 1 周可完成')
            else:
                parts.append('预计 2 周以上')

        return '，'.join(parts)

    def _get_suggested_action(self, urgency_level: str) -> str:
        """获取建议操作"""
        actions = {'critical': '立即处理', 'high': '本周处理', 'medium': '下周考虑', 'low': '待评估'}
        return actions.get(urgency_level, '待评估')

    async def _enhance_suggestions_with_ai(self, suggestions: list[dict]) -> str:
        """AI 润色建议文案（可选，失败不影响主流程）"""
        if not suggestions:
            return '暂无需处理的需求。'

        try:
            top_item = suggestions[0]
            prompt = f"""
你是产品经理的智能助手。基于以下需求数据，生成一句话总结建议（不超过 50 字）：

1. {suggestions[0]['title']} - 优先级：{suggestions[0]['estimated_roi']:.1f}，{suggestions[0]['reason']}
{f'2. {suggestions[1]["title"]} - 优先级：{suggestions[1]["estimated_roi"]:.1f}' if len(suggestions) > 1 else ''}
{f'3. {suggestions[2]["title"]} - 优先级：{suggestions[2]["estimated_roi"]:.1f}' if len(suggestions) > 2 else ''}

要求：
- 直接给出建议，不要解释为什么
- 突出最重要的 1 个需求
- 包含具体的客户影响或预期收益
"""

            summary = await ai_client.chat(prompt, max_tokens=100)
            return summary.strip()
        except Exception as e:
            log.warning(f'AI 建议生成失败，使用默认文案: {e}')
            return f'建议本周优先处理"{top_item["title"]}"。'

    async def _identify_high_risk_topics(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict[str, Any]:
        """
        识别高风险需求（纯规则引擎）

        Returns:
            {
                "high_risk_topics": [...],
                "summary": "..."
            }
        """
        from backend.app.userecho.model.priority_score import PriorityScore

        # 1. 查询所有未完成的 Bug
        query = (
            select(Topic)
            .join(PriorityScore, Topic.id == PriorityScore.topic_id)
            .where(
                and_(
                    Topic.tenant_id == tenant_id,
                    Topic.category == 'bug',
                    Topic.status.in_(['pending', 'planned', 'in_progress']),
                    Topic.deleted_at.is_(None),
                )
            )
        )

        result = await db.execute(query)
        topics = result.scalars().all()

        high_risk = []

        for topic in topics:
            if not topic.priority_score:
                continue

            score = topic.priority_score.total_score

            # 获取关联客户
            query_customers = (
                select(Customer)
                .join(Feedback, Customer.id == Feedback.customer_id)
                .where(and_(Feedback.topic_id == topic.id, Feedback.tenant_id == tenant_id))
                .distinct()
            )
            result_customers = await db.execute(query_customers)
            customers = result_customers.scalars().all()

            if not customers:
                continue

            # 应用规则
            risk_level = None
            if any(c.customer_type == 'strategic' for c in customers) and score >= 50:
                risk_level = 'critical'
            elif any(c.customer_type == 'major' for c in customers) and score >= 20:
                risk_level = 'high'
            elif len([c for c in customers if c.customer_type == 'paid']) >= 3 and score >= 10:
                risk_level = 'medium'

            if risk_level:
                # 计算未解决天数
                days_unresolved = (datetime.now() - topic.created_time).days

                high_risk.append({
                    'topic_id': topic.id,
                    'title': topic.title,
                    'risk_level': risk_level,
                    'affected_customers': [
                        {'name': c.name, 'type': c.customer_type}
                        for c in customers
                        if c.customer_type in ['major', 'strategic', 'paid']
                    ],
                    'days_unresolved': days_unresolved,
                    'priority_score': score,
                    'suggested_action': '立即联系客户，安排紧急修复' if risk_level == 'critical' else '尽快处理',
                })

        # 排序：按风险等级和未解决天数
        high_risk.sort(
            key=lambda x: (
                0 if x['risk_level'] == 'critical' else 1 if x['risk_level'] == 'high' else 2,
                -x['days_unresolved'],
            )
        )

        # 生成总结
        if not high_risk:
            summary = '✅ 暂无高风险需求。'
        else:
            critical_count = len([x for x in high_risk if x['risk_level'] == 'critical'])
            high_count = len([x for x in high_risk if x['risk_level'] == 'high'])

            if critical_count > 0:
                summary = f'⚠️ 发现 {critical_count} 个极高风险需求，请立即处理！'
            elif high_count > 0:
                summary = f'发现 {high_count} 个高风险需求。'
            else:
                summary = f'发现 {len(high_risk)} 个中等风险需求。'

        return {'high_risk_topics': high_risk, 'summary': summary, 'generated_at': datetime.now().isoformat()}

    async def _generate_weekly_report(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        生成周报/月报（模板生成 + AI 润色）

        Returns:
            {
                "markdown": "...",
                "data": {...}
            }
        """
        # 1. 收集统计数据
        data = await self._collect_report_data(db, tenant_id, start_date, end_date)

        # 2. AI 生成建议
        ai_suggestion = await self._generate_ai_suggestion_for_report(data)

        # 3. 渲染 Markdown
        markdown = self._render_report_template(data, ai_suggestion, start_date, end_date)

        return {'markdown': markdown, 'data': data, 'generated_at': datetime.now().isoformat()}

    async def _collect_report_data(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """收集报告数据"""
        # 本周新增反馈数
        query_feedbacks = select(func.count(Feedback.id)).where(
            and_(Feedback.tenant_id == tenant_id, Feedback.submitted_at.between(start_date, end_date))
        )
        result = await db.execute(query_feedbacks)
        new_feedbacks_count = result.scalar() or 0

        # 上周反馈数（用于对比）
        last_start = start_date - timedelta(days=7)
        last_end = end_date - timedelta(days=7)
        query_last_feedbacks = select(func.count(Feedback.id)).where(
            and_(Feedback.tenant_id == tenant_id, Feedback.submitted_at.between(last_start, last_end))
        )
        result_last = await db.execute(query_last_feedbacks)
        last_feedbacks_count = result_last.scalar() or 0

        change_percent = 0.0
        if last_feedbacks_count > 0:
            change_percent = (new_feedbacks_count - last_feedbacks_count) / last_feedbacks_count * 100

        # 本周新增 Topic 数
        query_topics = select(func.count(Topic.id)).where(
            and_(Topic.tenant_id == tenant_id, Topic.created_time.between(start_date, end_date))
        )
        result_topics = await db.execute(query_topics)
        new_topics_count = result_topics.scalar() or 0

        # 本周完成的 Topic 数
        query_completed = select(func.count(Topic.id)).where(
            and_(
                Topic.tenant_id == tenant_id,
                Topic.status == 'completed',
                Topic.updated_time.between(start_date, end_date),
            )
        )
        result_completed = await db.execute(query_completed)
        completed_count = result_completed.scalar() or 0

        # 需求分布（按分类）
        query_distribution = (
            select(Topic.category, func.count(Topic.id))
            .where(and_(Topic.tenant_id == tenant_id, Topic.created_time.between(start_date, end_date)))
            .group_by(Topic.category)
        )
        result_distribution = await db.execute(query_distribution)
        # 转换 Row 对象为 tuple，确保可 JSON 序列化
        tag_distribution = [tuple(row) for row in result_distribution.all()]

        # TOP 3 需求（按反馈数量排序）
        from backend.app.userecho.model.priority_score import PriorityScore

        query_top = (
            select(Topic)
            .outerjoin(PriorityScore, Topic.id == PriorityScore.topic_id)
            .where(
                and_(
                    Topic.tenant_id == tenant_id,
                    Topic.created_time.between(start_date, end_date),
                    Topic.deleted_at.is_(None),
                )
            )
            .order_by(Topic.feedback_count.desc(), PriorityScore.total_score.desc())
            .limit(3)
        )
        result_top = await db.execute(query_top)
        top_topics_raw = result_top.scalars().all()

        top_topics = []
        for topic in top_topics_raw:
            # 获取客户数
            query_customers = (
                select(func.count(func.distinct(Customer.id)))
                .join(Feedback, Customer.id == Feedback.customer_id)
                .where(Feedback.topic_id == topic.id)
            )
            result_customers = await db.execute(query_customers)
            customer_count = result_customers.scalar() or 0

            # 预计开发时间
            estimated_days = 1
            if topic.priority_score:
                dev_cost = topic.priority_score.dev_cost
                if dev_cost == 1:
                    estimated_days = 1
                elif dev_cost == 3:
                    estimated_days = 3
                elif dev_cost == 5:
                    estimated_days = 7
                else:
                    estimated_days = 14

            top_topics.append({
                'title': topic.title,
                'customer_count': customer_count,
                'score': round(topic.priority_score.total_score, 1) if topic.priority_score else 0,
                'estimated_days': estimated_days,
                'category': topic.category,
            })

        return {
            'new_feedbacks_count': new_feedbacks_count,
            'change_percent': round(change_percent, 1),
            'new_topics_count': new_topics_count,
            'completed_count': completed_count,
            'tag_distribution': tag_distribution,
            'top_topics': top_topics,
            'total_topics': new_topics_count,
        }

    async def _generate_ai_suggestion_for_report(self, data: dict) -> str:
        """AI 生成报告建议"""
        if not data['top_topics']:
            return '暂无需处理的需求。'

        try:
            top_topics = data['top_topics']
            prompt = f"""
基于以下 TOP 3 需求，生成一句话建议（不超过 50 字）：
1. {top_topics[0]['title']} - 影响 {top_topics[0]['customer_count']} 个客户
{f'2. {top_topics[1]["title"]} - 影响 {top_topics[1]["customer_count"]} 个客户' if len(top_topics) > 1 else ''}
{f'3. {top_topics[2]["title"]} - 影响 {top_topics[2]["customer_count"]} 个客户' if len(top_topics) > 2 else ''}

要求：直接给出建议，不要解释。
"""

            suggestion = await ai_client.chat(prompt, max_tokens=80)
            return suggestion.strip()
        except Exception as e:
            log.warning(f'AI 报告建议生成失败: {e}')
            top = data['top_topics'][0]
            return f'建议优先处理"{top["title"]}"。'

    def _render_report_template(
        self,
        data: dict,
        ai_suggestion: str,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """渲染报告模板"""
        template_str = """## 本周反馈总结（{{ start_date }} ~ {{ end_date }}）

### 📊 数据概览
- 新增反馈：{{ data.new_feedbacks_count }} 条{% if data.change_percent > 0 %}（↑ {{ data.change_percent }}% vs 上周）{% elif data.change_percent < 0 %}（↓ {{ data.change_percent|abs }}% vs 上周）{% endif %}
- 生成需求主题：{{ data.new_topics_count }} 个
- 已完成需求：{{ data.completed_count }} 个

### 🏷️ 需求分布
{% for tag, count in data.tag_distribution %}
- {{ tag }}：{% if data.total_topics > 0 %}{{ (count / data.total_topics * 100)|round|int }}%{% else %}0%{% endif %}（{{ count }} 个）
{% endfor %}

### 🔥 客户反馈热度 TOP 3
{% for topic in data.top_topics %}
{{ loop.index }}. **{{ topic.title }}**（影响 {{ topic.customer_count }} 个客户，优先级：{{ topic.score }}）
   - 预计开发时间：{{ topic.estimated_days }} 天
{% endfor %}

### 💡 AI 建议
{{ ai_suggestion }}
"""

        template = Template(template_str)
        return template.render(
            data=data,
            ai_suggestion=ai_suggestion,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
        )

    async def _calculate_sentiment_trend(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        计算客户满意度趋势（规则 + AI 混合）

        Returns:
            {
                "sentiment_trend": {...},
                "summary": "...",
                "negative_topics": [...]
            }
        """
        # 1. 先确保有情感分析数据（异步调用，不阻塞）
        await self._ensure_sentiment_analyzed(db, tenant_id, start_date, end_date)

        # 2. 本周统计
        query_this_week = (
            select(Feedback.sentiment, func.count(Feedback.id))
            .where(and_(Feedback.tenant_id == tenant_id, Feedback.submitted_at.between(start_date, end_date)))
            .group_by(Feedback.sentiment)
        )
        result_this = await db.execute(query_this_week)
        this_week_data = dict(result_this.all())

        # 3. 上周统计
        last_start = start_date - timedelta(days=7)
        last_end = end_date - timedelta(days=7)
        query_last_week = (
            select(Feedback.sentiment, func.count(Feedback.id))
            .where(and_(Feedback.tenant_id == tenant_id, Feedback.submitted_at.between(last_start, last_end)))
            .group_by(Feedback.sentiment)
        )
        result_last = await db.execute(query_last_week)
        last_week_data = dict(result_last.all())

        # 4. 计算占比
        this_total = sum(this_week_data.values()) or 1
        last_total = sum(last_week_data.values()) or 1

        this_positive = this_week_data.get('positive', 0)
        last_positive = last_week_data.get('positive', 0)

        this_positive_rate = (this_positive / this_total) * 100
        last_positive_rate = (last_positive / last_total) * 100

        change = this_positive_rate - last_positive_rate

        # 5. 找出负面反馈最多的 Topic
        query_negative_topics = (
            select(Topic.id, Topic.title, func.count(Feedback.id).label('negative_count'))
            .join(Feedback, Topic.id == Feedback.topic_id)
            .where(
                and_(
                    Topic.tenant_id == tenant_id,
                    Feedback.sentiment == 'negative',
                    Feedback.submitted_at.between(start_date, end_date),
                )
            )
            .group_by(Topic.id, Topic.title)
            .order_by(func.count(Feedback.id).desc())
            .limit(5)
        )
        result_negative = await db.execute(query_negative_topics)
        negative_topics = [
            {'topic_id': row[0], 'title': row[1], 'negative_count': row[2]} for row in result_negative.all()
        ]

        # 6. 生成总结
        if change > 10:
            summary = f'本周正面反馈占比 {this_positive_rate:.0f}%，较上周上升 {change:.0f}%，客户满意度显著改善。'
        elif change > 0:
            summary = f'本周正面反馈占比 {this_positive_rate:.0f}%，较上周上升 {change:.0f}%，客户满意度略有改善。'
        elif change < -10:
            summary = (
                f'⚠️ 本周正面反馈占比 {this_positive_rate:.0f}%，较上周下降 {abs(change):.0f}%，需要关注客户满意度问题。'
            )
        elif change < 0:
            summary = f'本周正面反馈占比 {this_positive_rate:.0f}%，较上周下降 {abs(change):.0f}%。'
        else:
            summary = f'本周正面反馈占比 {this_positive_rate:.0f}%，与上周持平。'

        return {
            'sentiment_trend': {
                'this_week': {
                    'positive': this_week_data.get('positive', 0),
                    'neutral': this_week_data.get('neutral', 0),
                    'negative': this_week_data.get('negative', 0),
                    'positive_rate': round(this_positive_rate, 1),
                },
                'last_week': {
                    'positive': last_week_data.get('positive', 0),
                    'neutral': last_week_data.get('neutral', 0),
                    'negative': last_week_data.get('negative', 0),
                    'positive_rate': round(last_positive_rate, 1),
                },
                'change': f'{change:+.1f}%',
            },
            'summary': summary,
            'negative_topics': negative_topics,
            'generated_at': datetime.now().isoformat(),
        }

    async def _ensure_sentiment_analyzed(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """确保反馈已进行情感分析（AI 批量处理）"""
        # 查询未分析的反馈
        query = (
            select(Feedback)
            .where(
                and_(
                    Feedback.tenant_id == tenant_id,
                    Feedback.submitted_at.between(start_date, end_date),
                    Feedback.sentiment.is_(None),
                )
            )
            .limit(100)
        )  # 批量处理，最多100条

        result = await db.execute(query)
        to_analyze = result.scalars().all()

        if not to_analyze:
            return

        log.info(f'Analyzing sentiment for {len(to_analyze)} feedbacks')

        # 批量调用 AI
        try:
            contents = [f.content for f in to_analyze]

            prompt = f"""
分析以下用户反馈的情感倾向，返回 JSON 数组：

{json.dumps(contents[:20], ensure_ascii=False)}

返回格式：
[
  {{"sentiment": "positive", "score": 0.8, "reason": "用户表示满意"}},
  {{"sentiment": "negative", "score": -0.6, "reason": "投诉产品质量"}}
]

分类标准：
- positive：赞扬、感谢、满意
- neutral：中性描述、功能建议
- negative：抱怨、投诉、愤怒
"""

            results = await ai_client.chat(prompt, response_format='json')

            # 解析结果
            if isinstance(results, str):
                results = json.loads(results)

            # 更新数据库
            for i, feedback in enumerate(to_analyze[: len(results)]):
                if i < len(results):
                    result_item = results[i]
                    feedback.sentiment = result_item.get('sentiment', 'neutral')
                    feedback.sentiment_score = result_item.get('score', 0.0)
                    feedback.sentiment_reason = result_item.get('reason', '')

            await db.commit()
            log.info(f'Successfully analyzed sentiment for {len(results)} feedbacks')

        except Exception as e:
            log.error(f'Sentiment analysis failed: {e}')
            # 失败不影响主流程，继续执行


insight_service = InsightService()
