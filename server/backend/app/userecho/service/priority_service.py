"""优先级评分服务"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_priority import crud_priority_score
from backend.app.userecho.model.customer import Customer
from backend.app.userecho.model.feedback import Feedback
from backend.common.log import log


class PriorityService:
    """优先级评分服务"""

    async def calculate_business_value(
        self,
        db: AsyncSession,
        topic_id: str,
        tenant_id: str,
        allow_override: int | None = None,
    ) -> int:
        """
        自动计算商业价值

        规则：
        1. 获取 Topic 关联的所有客户
        2. 取最高客户等级的权重
        3. 多客户加成 (+1)
        4. 大客户加成 (+2)
        5. 支持手动微调（allow_override）

        Args:
            db: 数据库会话
            topic_id: 主题ID
            tenant_id: 租户ID
            allow_override: 手动微调值（1-10），如果提供则直接返回

        Returns:
            商业价值分数 (1-10)
        """
        # 手动微调优先
        if allow_override is not None:
            return min(10, max(1, allow_override))

        # 从 Topic 关联的 Feedback 获取所有客户
        customers = await self._get_related_customers(db, topic_id, tenant_id)

        if not customers:
            log.warning(f'Topic {topic_id} has no related customers, using default business_value=1')
            return 1  # 匿名反馈默认最低价值

        # 客户类型映射
        type_scores = {
            'normal': 1,  # 普通客户
            'paid': 3,  # 付费客户
            'major': 5,  # 大客户
            'strategic': 10,  # 战略客户
        }

        max_score = max(type_scores.get(c.customer_type, 1) for c in customers)

        # 多客户加成（3+ 客户 +1 分）
        unique_customers = {c.id for c in customers}
        if len(unique_customers) >= 3:
            max_score += 1
            log.debug(f'Multi-customer bonus: {len(unique_customers)} customers, +1 point')

        # 大客户加成（+2 分）
        has_major_customer = any(c.customer_type in ['major', 'strategic'] for c in customers)
        if has_major_customer:
            max_score += 2
            log.debug('Major customer bonus: +2 points')

        final_score = min(10, max_score)
        log.info(f'Calculated business_value for topic {topic_id}: {final_score}')
        return final_score

    async def _get_related_customers(
        self,
        db: AsyncSession,
        topic_id: str,
        tenant_id: str,
    ) -> list[Customer]:
        """
        获取 Topic 关联的所有客户（通过 Feedback）

        Args:
            db: 数据库会话
            topic_id: 主题ID
            tenant_id: 租户ID

        Returns:
            客户列表（去重）
        """
        # 通过 Feedback 查询关联的客户（使用 JOIN 去重）
        query = (
            select(Customer)
            .join(Feedback, Feedback.customer_id == Customer.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.topic_id == topic_id,
                Feedback.customer_id.is_not(None),
                Feedback.deleted_at.is_(None),
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
            .distinct()
        )

        result = await db.execute(query)
        customers = list(result.scalars().all())

        log.debug(f'Found {len(customers)} related customers for topic {topic_id}')
        return customers

    async def suggest_impact_scope_fast(
        self,
        customer_count: int,
        feedback_count: int,
    ) -> dict:
        """
        快速规则判断影响范围（不调用 AI）

        用于聚类时生成默认评分，节省成本

        Args:
            customer_count: 涉及客户数量
            feedback_count: 反馈数量

        Returns:
            {
                "scope": 1/3/5/10,
                "confidence": 0.0-1.0,
                "reason": "原因"
            }
        """
        # 基于客户数量的规则判断
        if customer_count >= 10:
            return {'scope': 10, 'confidence': 0.7, 'reason': f'影响 {customer_count} 个客户，判定为全部用户'}
        if customer_count >= 5:
            return {'scope': 5, 'confidence': 0.7, 'reason': f'影响 {customer_count} 个客户，判定为大多数用户'}
        if customer_count >= 2:
            return {'scope': 3, 'confidence': 0.6, 'reason': f'影响 {customer_count} 个客户，判定为部分用户'}
        # 仅 1 个客户，但反馈数量较多也可能是高影响
        if feedback_count >= 5:
            return {'scope': 3, 'confidence': 0.5, 'reason': f'1 个客户提交 {feedback_count} 条反馈，可能影响范围较大'}
        return {'scope': 1, 'confidence': 0.6, 'reason': '仅影响 1 个客户，判定为个别用户'}

    async def suggest_dev_cost_fast(
        self,
        category: str,
        title: str,
    ) -> dict:
        """
        快速规则判断开发成本（不调用 AI）

        用于聚类时生成默认评分，节省成本

        Args:
            category: 分类（bug/improvement/feature/performance）
            title: 主题标题

        Returns:
            {
                "days": 1/3/5/10,
                "confidence": 0.0-1.0,
                "reason": "原因"
            }
        """
        # 关键词匹配（紧急问题）
        urgent_keywords = ['崩溃', '闪退', '无法', '不能', '失败', 'crash', 'bug']
        if any(keyword in title.lower() for keyword in urgent_keywords):
            return {'days': 1, 'confidence': 0.7, 'reason': '检测到紧急问题关键词，预估 1 天可修复'}

        # 新功能关键词
        feature_keywords = ['新增', '增加', '添加', '支持', 'add', 'new']
        if any(keyword in title.lower() for keyword in feature_keywords):
            return {'days': 5, 'confidence': 0.6, 'reason': '检测到新功能关键词，预估 5 天开发'}

        # 基于分类的默认成本
        category_costs = {
            'bug': (1, '紧急 Bug 修复'),
            'improvement': (1, '体验优化'),
            'feature': (5, '新功能开发'),
            'performance': (3, '性能优化'),
            'other': (3, '其他需求'),
        }

        days, reason = category_costs.get(category, (3, '未分类需求'))

        return {'days': days, 'confidence': 0.5, 'reason': f'基于分类 {category} 的经验值：{reason}'}

    async def create_default_priority_score(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        category: str,
        title: str,
        customer_count: int,
        feedback_count: int,
        is_urgent: bool = False,
    ) -> None:
        """
        为新创建的 Topic 生成默认优先级评分

        用于聚类时自动生成建议评分（使用快速规则，不调用 AI）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            category: 分类
            title: 主题标题
            customer_count: 涉及客户数量
            feedback_count: 反馈数量
            is_urgent: 是否紧急
        """
        # 商业价值：自动计算
        business_value = await self.calculate_business_value(db, topic_id, tenant_id)

        # 影响范围：快速规则判断
        impact_suggestion = await self.suggest_impact_scope_fast(customer_count, feedback_count)
        impact_scope = impact_suggestion['scope']

        # 开发成本：快速规则判断
        dev_cost_suggestion = await self.suggest_dev_cost_fast(category, title)
        dev_cost = dev_cost_suggestion['days']

        # 紧急系数
        urgency_factor = 1.5 if is_urgent else 1.0

        # 创建评分
        await crud_priority_score.upsert(
            db=db,
            tenant_id=tenant_id,
            topic_id=topic_id,
            impact_scope=impact_scope,
            business_value=business_value,
            dev_cost=dev_cost,
            urgency_factor=urgency_factor,
        )

        log.info(
            f'Created default priority score for topic {topic_id}: '
            f'impact={impact_scope}, business={business_value}, cost={dev_cost}, urgent={urgency_factor}'
        )

    async def create_or_update_priority_score(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        impact_scope: int,
        business_value: int,
        dev_cost: int,
        urgency_factor: float = 1.0,
        details: dict | None = None,
    ) -> None:
        """
        创建或更新优先级评分（手动确认后保存）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            impact_scope: 影响范围 (1/3/5/10)
            business_value: 商业价值 (1-10)
            dev_cost: 开发成本 (1/3/5/10)
            urgency_factor: 紧急系数 (1.0-2.0)
        """
        await crud_priority_score.upsert(
            db=db,
            tenant_id=tenant_id,
            topic_id=topic_id,
            impact_scope=impact_scope,
            business_value=business_value,
            dev_cost=dev_cost,
            urgency_factor=urgency_factor,
            details=details,
        )

        log.info(f'Updated priority score for topic {topic_id}')


priority_service = PriorityService()
