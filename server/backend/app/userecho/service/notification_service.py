"""通知服务 - AI 回复生成和通知管理"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_topic_notification import crud_topic_notification
from backend.app.userecho.model.topic_notification import TopicNotification
from backend.common.log import log


class NotificationService:
    """通知服务"""

    # AI 回复生成 Prompt
    SYSTEM_PROMPT = """你是一位专业的客户成功经理，负责向用户通知他们反馈的需求已完成开发。

你的任务是根据以下信息生成一条个性化的通知消息：
- 用户姓名
- 客户等级（普通/付费/大客户/战略）
- 原始反馈内容
- 需求主题标题
- 发布日期（如有）

生成规则：
1. 开头称呼用户姓名
2. 感谢用户提供的反馈
3. 告知用户需求已实现
4. 简要说明实现的功能
5. 邀请用户体验并提供反馈
6. 根据客户等级调整语气（大客户更正式，普通客户更亲切）
7. 控制在 150 字以内
"""

    TONE_GUIDES = {
        "formal": "请使用正式商务风格，措辞严谨，体现专业感。",
        "friendly": "请使用亲切友好的语气，自然随和，像朋友交流。",
        "concise": "请使用简洁高效的风格，只说重点，不废话。",
    }

    TIER_NAMES = {
        "free": "普通用户",
        "normal": "普通客户",
        "paid": "付费客户",
        "vip": "大客户",
        "strategic": "战略客户",
    }

    async def generate_reply(
        self,
        db: AsyncSession,
        tenant_id: str,
        notification_id: str,
        tone: str = "friendly",
        language: str = "zh-CN",
        custom_context: str | None = None,
    ) -> str:
        """生成单条 AI 回复"""
        from backend.app.userecho.model.customer import Customer
        from backend.app.userecho.model.feedback import Feedback
        from backend.app.userecho.model.topic import Topic
        from backend.utils.ai_client import ai_client

        # 获取通知记录
        notification = await crud_topic_notification.get_by_id(db, tenant_id, notification_id)
        if not notification:
            raise ValueError("通知记录不存在")

        # 获取关联数据
        from sqlalchemy import select

        # 获取反馈
        feedback_result = await db.execute(select(Feedback).where(Feedback.id == notification.feedback_id))
        feedback = feedback_result.scalar_one_or_none()

        # 获取议题
        topic_result = await db.execute(select(Topic).where(Topic.id == notification.topic_id))
        topic = topic_result.scalar_one_or_none()

        # 获取客户（如果有）
        customer = None
        if notification.customer_id:
            customer_result = await db.execute(select(Customer).where(Customer.id == notification.customer_id))
            customer = customer_result.scalar_one_or_none()

        # 构建 Prompt
        user_prompt = self._build_user_prompt(
            recipient_name=notification.recipient_name,
            customer_tier=customer.customer_tier if customer else "normal",
            company_name=customer.company_name if customer else None,
            feedback_content=feedback.content if feedback else "",
            topic_title=topic.title if topic else "",
            topic_description=topic.description if topic else "",
            release_date=str(topic.actual_release_date) if topic and topic.actual_release_date else None,
            tone=tone,
            language=language,
            custom_context=custom_context,
        )

        # 调用 AI 生成
        ai_reply = await ai_client.chat(
            prompt=f"{self.SYSTEM_PROMPT}\n\n{user_prompt}",
            max_tokens=300,
            temperature=0.7,
        )

        # 保存生成结果
        await crud_topic_notification.update_reply(
            db=db,
            tenant_id=tenant_id,
            notification_id=notification_id,
            ai_reply=ai_reply,
            reply_tone=tone,
            reply_language=language,
        )

        return ai_reply

    async def batch_generate_replies(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        tone: str = "friendly",
        language: str = "zh-CN",
    ) -> dict:
        """批量生成 AI 回复"""
        # 获取待处理的通知记录
        notifications = await crud_topic_notification.get_pending_by_topic_id(
            db=db, tenant_id=tenant_id, topic_id=topic_id
        )

        success_count = 0
        failed_count = 0
        errors = []

        for notification in notifications:
            try:
                await self.generate_reply(
                    db=db,
                    tenant_id=tenant_id,
                    notification_id=notification.id,
                    tone=tone,
                    language=language,
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"id": notification.id, "error": str(e)})
                log.error(f"Failed to generate reply for notification {notification.id}: {e}")

        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(notifications),
            "errors": errors or None,
        }

    async def create_notifications_for_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> int:
        """为议题创建通知记录（Topic 状态变为 completed 时调用）"""
        from sqlalchemy import select

        from backend.app.userecho.model.customer import Customer
        from backend.app.userecho.model.feedback import Feedback

        # 获取议题关联的所有反馈
        feedback_result = await db.execute(
            select(Feedback, Customer)
            .outerjoin(Customer, Feedback.customer_id == Customer.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.topic_id == topic_id,
                Feedback.deleted_at.is_(None),
            )
        )
        rows = feedback_result.all()

        # 去重：同一个客户或同一个外部用户只创建一条通知
        seen_recipients = set()
        created_count = 0

        for feedback, customer in rows:
            # 确定收件人标识
            if customer:
                recipient_key = f"customer:{customer.id}"
                recipient_name = customer.name
                recipient_contact = customer.contact_email or customer.contact_phone
                recipient_type = "customer"
                customer_id = customer.id
            elif feedback.external_user_name:
                recipient_key = f"external:{feedback.external_user_name}"
                recipient_name = feedback.external_user_name
                recipient_contact = feedback.external_contact
                recipient_type = "external"
                customer_id = None
            else:
                continue  # 无法识别收件人，跳过

            # 去重
            if recipient_key in seen_recipients:
                continue
            seen_recipients.add(recipient_key)

            # 创建通知记录
            notification = TopicNotification(
                tenant_id=tenant_id,
                topic_id=topic_id,
                feedback_id=feedback.id,
                customer_id=customer_id,
                recipient_name=recipient_name,
                recipient_contact=recipient_contact,
                recipient_type=recipient_type,
            )
            db.add(notification)
            created_count += 1

        await db.commit()
        return created_count

    def _build_user_prompt(
        self,
        recipient_name: str,
        customer_tier: str,
        company_name: str | None,
        feedback_content: str,
        topic_title: str,
        topic_description: str | None,
        release_date: str | None,
        tone: str,
        language: str,
        custom_context: str | None,
    ) -> str:
        """构建用户 Prompt"""
        tier_name = self.TIER_NAMES.get(customer_tier, "客户")
        tone_guide = self.TONE_GUIDES.get(tone, self.TONE_GUIDES["friendly"])

        prompt = f"""请为以下用户生成通知消息：

用户姓名：{recipient_name}
客户等级：{tier_name}
客户公司：{company_name or "未知"}
原始反馈：{feedback_content[:200]}...
需求主题：{topic_title}
需求描述：{topic_description or "无"}
发布日期：{release_date or "最新版本"}

语气风格：{tone_guide}
输出语言：{"中文" if language == "zh-CN" else "English"}
"""

        if custom_context:
            prompt += f"\n额外说明：{custom_context}"

        return prompt


notification_service = NotificationService()
