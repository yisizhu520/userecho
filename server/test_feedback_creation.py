"""测试手动创建反馈是否修复 submitted_at 问题"""

import asyncio

from backend.app.userecho.schema.feedback import FeedbackCreate
from backend.app.userecho.service import feedback_service
from backend.database.db import async_db_session


async def test_create_feedback():
    """测试创建反馈"""
    print("=" * 80)
    print("测试手动创建反馈（验证 submitted_at 自动注入）")
    print("=" * 80)
    print()

    # 测试数据（与前端请求一致）
    data = FeedbackCreate(
        board_id="67cce548-293e-4d3e-80da-f1bbdb91ceb5",
        content="暗黑模式+1",
        is_urgent=False,
        author_type="customer",
        customer_name="123",
        customer_type="normal",
        topic_id="df21ba3d-2e2c-4da5-ad90-4e46f8aba78b",
    )

    tenant_id = "default-tenant"  # 替换为实际 tenant_id
    submitter_id = 1  # 替换为实际用户ID

    try:
        async with async_db_session.begin() as db:
            feedback = await feedback_service.create_with_ai_processing(
                db=db,
                tenant_id=tenant_id,
                data=data,
                generate_summary=False,  # 测试时关闭摘要生成
                submitter_id=submitter_id,
            )

            print("✅ 反馈创建成功！")
            print(f"   - ID: {feedback.id}")
            print(f"   - Content: {feedback.content}")
            print(f"   - submitted_at: {feedback.submitted_at}")
            print(f"   - created_time: {feedback.created_time}")
            print(f"   - Customer: {feedback.customer_id}")
            print()

            # 验证时间字段是否都有值
            assert feedback.submitted_at is not None, "submitted_at 不应该是 None"
            assert feedback.created_time is not None, "created_time 不应该是 None"

            print("✅ 所有时间字段验证通过！")
            print()

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_create_feedback())
