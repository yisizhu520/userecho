"""生成真实的测试数据

造一些相似但不完全相同的反馈，用于测试聚类效果
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.userecho.model.feedback import Feedback
from backend.database.db import async_db_session

# 真实的测试数据：每组包含相似反馈（不完全相同）
TEST_FEEDBACKS = [
    # 组1: 关于导出功能的反馈（应该聚在一起）
    "希望能导出反馈数据为 Excel，方便做离线分析",
    "能否支持批量导出反馈？现在一条条复制太麻烦了",
    "需要导出功能，想把反馈数据拿到 Google Sheets 分析",
    "导出反馈到 CSV 格式会很有用",
    # 组2: 关于邮件通知的反馈（应该聚在一起）
    "新反馈提交时希望能发送邮件通知",
    "可以加个邮件提醒功能吗？现在总是忘记查看反馈",
    "希望有新反馈时能收到邮件",
    "能否支持邮件订阅？这样有新内容就不会错过了",
    # 组3: 关于权限管理的反馈（应该聚在一起）
    "希望能设置团队成员的访问权限，不是所有人都能看到敏感反馈",
    "需要角色权限控制，让不同成员有不同的操作权限",
    "能否添加权限管理？现在所有人都是管理员不太合适",
    "希望有细粒度的权限设置，比如只读、编辑、管理等",
    # 组4: 关于移动端的反馈（应该聚在一起）
    "有手机 App 吗？电脑不在身边时很不方便",
    "希望能出个移动端应用，随时查看反馈",
    "能否开发 iOS/Android 客户端？",
    "移动端适配太差了，希望能优化一下手机浏览体验",
    # 组5: 关于搜索功能的反馈（应该聚在一起）
    "搜索功能太弱了，希望能支持模糊搜索和关键词高亮",
    "能否改进搜索？现在找个反馈要翻好久",
    "希望搜索能支持多个关键词，AND/OR 逻辑",
    "全文搜索功能不太好用，经常搜不到明明存在的内容",
    # 组6: 关于 API 的反馈（应该聚在一起）
    "希望提供 API 接口，方便和我们的系统集成",
    "需要 RESTful API 来同步反馈数据",
    "能否开放 API？想自动化一些操作",
    "希望有 Webhook 支持，反馈变化时自动通知我们的系统",
    # 组7: 关于标签功能的反馈（应该聚在一起）
    "希望能给反馈打标签，方便分类管理",
    "需要标签系统，现在分类全靠看板太粗糙了",
    "能否支持多标签？一个反馈可能属于多个类别",
    "标签功能很重要，可以更灵活地组织反馈",
    # 组8: 关于评论功能的反馈（应该聚在一起）
    "希望能在反馈下评论讨论，现在只能私聊太麻烦",
    "需要评论区功能，团队成员可以在反馈下交流想法",
    "能否添加回复功能？方便和用户沟通",
    "希望支持内部评论和外部回复分开",
    # 组9: 关于数据可视化的反馈（应该聚在一起）
    "希望能看到反馈趋势图，按周/月统计数量变化",
    "需要数据看板，可视化展示反馈统计数据",
    "能否增加图表功能？看看哪类反馈最多",
    "希望有分析报表，了解用户反馈的热点",
    # 组10: 关于国际化的反馈（应该聚在一起）
    "希望支持多语言，我们的用户来自不同国家",
    "能否添加英文界面？现在全中文不太方便",
    "需要国际化支持，至少要有中英文切换",
    "希望能自动翻译反馈内容",
    # 不相似的单独反馈（噪声点）
    "价格有点贵，能否提供更多套餐选择？",
    "登录后页面加载很慢，需要优化性能",
    "UI 设计不错，但配色可以更现代一些",
    "客服响应很及时，体验很好",
    "文档写得太简单了，很多功能不知道怎么用",
    "希望能集成钉钉/企业微信",
    "数据导入功能有 bug，上传后部分内容丢失",
    "能否支持暗黑模式？晚上用眼睛累",
]


async def clear_old_data(tenant_id: str):
    """清除旧的测试数据"""
    async with async_db_session.begin() as db:
        result = await db.execute(select(Feedback).where(Feedback.tenant_id == tenant_id))
        feedbacks = result.scalars().all()

        for feedback in feedbacks:
            await db.delete(feedback)

        print(f"✅ 清除了 {len(feedbacks)} 条旧数据")


async def generate_test_data(tenant_id: str):
    """生成测试数据"""
    print("\n" + "=" * 80)
    print("生成测试数据".center(80))
    print("=" * 80 + "\n")

    # 1. 清除旧数据
    await clear_old_data(tenant_id)

    # 2. 确保有 board
    from backend.app.userecho.model.board import Board
    from uuid import uuid4
    from sqlalchemy import text

    board_id = None
    async with async_db_session.begin() as db:
        result = await db.execute(select(Board).where(Board.tenant_id == tenant_id).limit(1))
        board = result.scalars().first()

        if not board:
            board = Board(
                id=str(uuid4()),
                tenant_id=tenant_id,
                name="测试看板",
            )
            db.add(board)
            print(f"✅ 创建了测试看板: {board.id}")

        board_id = board.id

    # 3. 使用 SQL 直接插入（绕过约束检查问题）
    async with async_db_session.begin() as db:
        from uuid import uuid4

        for idx, content in enumerate(TEST_FEEDBACKS, 1):
            sql = text("""
                INSERT INTO feedbacks (
                    id, tenant_id, board_id, content, source, author_type,
                    external_user_name, is_urgent, clustering_status, submitted_at, created_time
                ) VALUES (
                    :id, :tenant_id, :board_id, :content, :source, :author_type,
                    :external_user_name, :is_urgent, :clustering_status, :submitted_at, :created_time
                )
            """)

            await db.execute(
                sql,
                {
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "board_id": board_id,
                    "content": content,
                    "source": "web",
                    "author_type": "external",  # 使用 external，需要 external_user_name
                    "external_user_name": f"test_user_{idx}",
                    "is_urgent": False,
                    "clustering_status": "pending",
                    "submitted_at": datetime.now(timezone.utc),
                    "created_time": datetime.now(timezone.utc),
                },
            )

        print(f"✅ 插入了 {len(TEST_FEEDBACKS)} 条新反馈")
        print("\n数据分组：")
        print("  - 导出功能: 4 条")
        print("  - 邮件通知: 4 条")
        print("  - 权限管理: 4 条")
        print("  - 移动端: 4 条")
        print("  - 搜索功能: 4 条")
        print("  - API: 4 条")
        print("  - 标签功能: 4 条")
        print("  - 评论功能: 4 条")
        print("  - 数据可视化: 4 条")
        print("  - 国际化: 4 条")
        print("  - 噪声点: 8 条（不应该聚类）")
        print("\n预期聚类数: 10 个（阈值 0.90）")


async def main():
    TENANT_ID = "default-tenant"

    await generate_test_data(TENANT_ID)

    print("\n✅ 数据生成完成！")
    print("\n下一步: python scripts/embedding_comparison/compare_clustering_providers.py")


if __name__ == "__main__":
    asyncio.run(main())
