"""初始化 Demo 环境示例数据

创建用于演示的反馈、客户、议题等数据，所有数据围绕"回响"产品本身的功能和应用场景

数据包括：
- 10 个真实 SaaS 客户（Wolai、FlowUs、Cubox 等）
- 4 个看板（功能建议、Bug 反馈、体验优化、集成需求）
- 15 个议题（展示不同状态和优先级）
- 47 条反馈模板（涵盖 AI 聚类、截图识别、优先级评分等核心功能）

执行方式: python scripts/init_demo_data.py
"""

import asyncio
import io
import os
import random
import sys

from datetime import datetime, timedelta
from pathlib import Path

# 【重要】确保使用 .env.demo 配置文件（必须在导入 backend 模块之前设置）
if "ENV_FILE" not in os.environ:
    backend_path = Path(__file__).resolve().parent.parent
    env_demo_path = backend_path / ".env.demo"
    if env_demo_path.exists():
        os.environ["ENV_FILE"] = str(env_demo_path)

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import delete, select

from backend.app.userecho.model import Board, Customer, Feedback, Topic
from backend.database.db import async_db_session, uuid4_str

DEFAULT_TENANT_ID = "default-tenant"

# ==================== 示例数据 ====================

DEMO_BOARDS = [
    {"name": "功能建议", "url_name": "feature-request", "description": "用户提出的新功能需求"},
    {"name": "Bug 反馈", "url_name": "bug-report", "description": "产品 Bug 和异常问题"},
    {"name": "体验优化", "url_name": "ux-improvement", "description": "UI/UX 体验改进建议"},
    {"name": "集成需求", "url_name": "integration-request", "description": "第三方工具集成需求"},
]

DEMO_CUSTOMERS = [
    {
        "name": "Wolai",
        "company_name": "我来（Wolai）",
        "customer_type": "vip",
        "business_value": 5,
        "contact_email": "pm@wolai.com",
    },
    {
        "name": "FlowUs",
        "company_name": "FlowUs 息流",
        "customer_type": "vip",
        "business_value": 5,
        "contact_email": "feedback@flowus.cn",
    },
    {
        "name": "Cubox",
        "company_name": "Cubox 收藏夹",
        "customer_type": "vip",
        "business_value": 4,
        "contact_email": "support@cubox.pro",
    },
    {
        "name": "NotionNext",
        "company_name": "NotionNext 博客",
        "customer_type": "paid",
        "business_value": 4,
        "contact_email": "hello@tangly1024.com",
    },
    {
        "name": "竹白",
        "company_name": "竹白 Newsletter",
        "customer_type": "paid",
        "business_value": 4,
        "contact_email": "team@zhubai.love",
    },
    {
        "name": "Flomo",
        "company_name": "Flomo 浮墨笔记",
        "customer_type": "paid",
        "business_value": 4,
        "contact_email": "hi@flomoapp.com",
    },
    {
        "name": "滴答清单",
        "company_name": "滴答清单 TickTick",
        "customer_type": "normal",
        "business_value": 3,
        "contact_email": "feedback@dida365.com",
    },
    {
        "name": "幕布",
        "company_name": "幕布",
        "customer_type": "normal",
        "business_value": 3,
        "contact_email": "support@mubu.com",
    },
    {
        "name": "独立开发者张三",
        "company_name": "个人开发者",
        "customer_type": "trial",
        "business_value": 2,
        "contact_email": "zhangsan@indie.dev",
    },
    {
        "name": "李四的产品实验室",
        "company_name": "个人",
        "customer_type": "trial",
        "business_value": 2,
        "contact_email": "lisi@product-lab.cn",
    },
]

FEEDBACK_TEMPLATES = [
    # A. AI 聚类与分析相关
    {"content": "AI 聚类效果很好，但希望能手动调整聚类结果", "is_urgent": False, "source": "email"},
    {"content": "能否支持自定义聚类规则？比如强制将某些关键词归为一类", "is_urgent": False, "source": "wechat"},
    {"content": "聚类后的议题名称有时不够准确，希望能批量重命名", "is_urgent": False, "source": "crm"},
    {"content": "希望能看到每个议题的聚类置信度分数", "is_urgent": False, "source": "feishu"},
    # B. 截图识别与图片处理
    {"content": "微信截图识别准确率很高，但小红书截图偶尔识别不出来", "is_urgent": True, "source": "wechat"},
    {"content": "能否支持批量上传截图？现在只能一张张传", "is_urgent": False, "source": "email"},
    {"content": "截图识别后希望能自动提取关键信息（如版本号、错误码）", "is_urgent": False, "source": "crm"},
    # C. 优先级评分与决策
    {"content": "优先级评分公式能否自定义？我们更看重商业价值而不是影响范围", "is_urgent": False, "source": "email"},
    {"content": "希望能批量修改议题的优先级", "is_urgent": False, "source": "wechat"},
    {"content": "能否增加'开发成本'字段？现在只能手动估算", "is_urgent": False, "source": "crm"},
    {"content": "优先级排序希望支持拖拽手动调整", "is_urgent": False, "source": "feishu"},
    {"content": "能否给出 AI 推荐的优先级评分？", "is_urgent": False, "source": "email"},
    # D. 状态追踪与协作
    {"content": "状态流转能否发送通知？比如从'评审中'变为'已批准'时通知相关人", "is_urgent": False, "source": "wechat"},
    {"content": "希望在议题下方增加评论功能，方便团队讨论", "is_urgent": True, "source": "email"},
    {"content": "能否支持 @提醒同事？", "is_urgent": False, "source": "feishu"},
    # E. 公开路线图与透明化
    {"content": "希望能有公开路线图功能，让用户看到我们在做什么，提升信任度", "is_urgent": False, "source": "email"},
    {"content": "能否让用户对路线图的议题投票？", "is_urgent": False, "source": "wechat"},
    # F. 更新日志（Changelog）
    {"content": "希望能有更新日志功能，支持 Markdown 编辑和图片上传", "is_urgent": False, "source": "email"},
    {"content": "能否自动将'已完成'状态的议题生成 Changelog 草稿？", "is_urgent": False, "source": "crm"},
    {"content": "Changelog 希望支持 RSS 订阅", "is_urgent": False, "source": "wechat"},
    {
        "content": "能否在 Changelog 中展示关联的反馈数量？让用户知道这个功能有多少人想要",
        "is_urgent": False,
        "source": "feishu",
    },
    # G. 数据导入与集成
    {"content": "Excel 导入很方便，但能否支持 CSV 格式？", "is_urgent": False, "source": "email"},
    {"content": "希望能对接飞书多维表格，自动同步反馈", "is_urgent": True, "source": "feishu"},
    {"content": "能否提供 API 接口？我们想从客服系统自动推送反馈", "is_urgent": True, "source": "crm"},
    {"content": "批量导入时希望能预览数据，确认无误后再提交", "is_urgent": False, "source": "wechat"},
    {"content": "能否支持从 Canny / ProductBoard 导入历史数据？", "is_urgent": False, "source": "email"},
    # H. 客户管理与分群
    {"content": "客户列表希望能按 MRR 排序，优先看到大客户的反馈", "is_urgent": False, "source": "email"},
    {"content": "能否给客户打标签？比如'重点客户''流失风险'等", "is_urgent": False, "source": "crm"},
    {"content": "希望能按客户类型筛选反馈（VIP / Paid / Free）", "is_urgent": False, "source": "wechat"},
    {"content": "能否自动关联客户的历史反馈？方便了解客户的完整需求", "is_urgent": False, "source": "feishu"},
    # I. 通知与提醒
    {"content": "新反馈提交时希望能发送飞书通知", "is_urgent": True, "source": "feishu"},
    {"content": "能否支持钉钉 Webhook？", "is_urgent": True, "source": "wechat"},
    {"content": "邮件通知的内容希望能自定义模板", "is_urgent": False, "source": "email"},
    {"content": "能否设置通知规则？比如只有紧急反馈才通知我", "is_urgent": False, "source": "crm"},
    {"content": "希望能在微信接收通知推送", "is_urgent": False, "source": "wechat"},
    # J. 数据分析与可视化
    {"content": "希望能看到反馈趋势图（按周/月统计）", "is_urgent": False, "source": "email"},
    {
        "content": "能否增加仪表盘，展示关键指标（反馈总数、处理率、平均响应时间）？",
        "is_urgent": False,
        "source": "crm",
    },
    {"content": "希望能导出数据报表（Excel），给老板汇报用", "is_urgent": False, "source": "wechat"},
    {"content": "能否按来源渠道统计反馈（微信、邮件、CRM）？", "is_urgent": False, "source": "feishu"},
    # K. 移动端与体验优化
    {"content": "希望有移动端 App，方便随时查看反馈", "is_urgent": False, "source": "wechat"},
    {"content": "暗色模式什么时候能上线？晚上用太刺眼了", "is_urgent": False, "source": "email"},
    {"content": "列表页加载速度有点慢，数据多的时候卡顿", "is_urgent": True, "source": "crm"},
    {"content": "搜索功能希望支持模糊匹配", "is_urgent": False, "source": "wechat"},
    # L. 权限与安全
    {"content": "能否设置只读权限？我们的 CS 团队只需要查看，不需要编辑", "is_urgent": False, "source": "email"},
    {"content": "希望能看到操作日志（谁删除了哪条反馈）", "is_urgent": False, "source": "crm"},
    {"content": "能否支持 SSO 单点登录？", "is_urgent": False, "source": "feishu"},
]

DEMO_TOPICS = [
    {
        "title": "自定义聚类规则",
        "description": "支持手动调整 AI 聚类结果，增加自定义规则配置",
        "status": "review",
        "priority_score": 78.5,
    },
    {
        "title": "截图批量上传",
        "description": "支持一次性上传多张截图，提升导入效率",
        "status": "new",
        "priority_score": 65.2,
    },
    {
        "title": "优先级评分公式自定义",
        "description": "允许 PM 自定义优先级计算公式",
        "status": "approved",
        "priority_score": 82.3,
    },
    {
        "title": "议题评论与讨论",
        "description": "在议题下方增加评论功能，支持 @提醒",
        "status": "in_progress",
        "priority_score": 88.7,
    },
    {
        "title": "路线图投票功能",
        "description": "允许用户对公开路线图的议题进行投票",
        "status": "new",
        "priority_score": 75.8,
    },
    {
        "title": "Changelog 自动生成",
        "description": "根据已完成议题自动生成更新日志草稿",
        "status": "review",
        "priority_score": 71.4,
    },
    {
        "title": "飞书多维表格集成",
        "description": "自动同步反馈到飞书多维表格",
        "status": "approved",
        "priority_score": 68.9,
    },
    {
        "title": "API 接口开放",
        "description": "提供 RESTful API，支持第三方系统推送反馈",
        "status": "approved",
        "priority_score": 85.6,
    },
    {
        "title": "客户标签系统",
        "description": "支持给客户打标签（重点客户、流失风险等）",
        "status": "new",
        "priority_score": 62.7,
    },
    {
        "title": "飞书/钉钉通知",
        "description": "新反馈提交时自动发送飞书/钉钉 Webhook 通知",
        "status": "in_progress",
        "priority_score": 79.3,
    },
    {
        "title": "反馈趋势分析",
        "description": "数据可视化图表，展示反馈趋势和关键指标",
        "status": "review",
        "priority_score": 73.1,
    },
    {
        "title": "暗色模式",
        "description": "增加暗色主题切换功能",
        "status": "new",
        "priority_score": 55.4,
    },
    {
        "title": "列表性能优化",
        "description": "优化大数据量时的列表加载速度",
        "status": "in_progress",
        "priority_score": 91.2,
    },
    {
        "title": "权限管理增强",
        "description": "支持只读、编辑、管理员等多级权限",
        "status": "review",
        "priority_score": 66.8,
    },
    {
        "title": "小红书截图识别优化",
        "description": "提升小红书评论截图的识别准确率",
        "status": "new",
        "priority_score": 58.9,
    },
]


async def clear_demo_data() -> None:
    """清除现有 Demo 数据"""
    async with async_db_session.begin() as db:
        print("🗑️  清除现有 Demo 数据...")

        # 按外键依赖顺序删除
        await db.execute(delete(Feedback).where(Feedback.tenant_id == DEFAULT_TENANT_ID))
        await db.execute(delete(Topic).where(Topic.tenant_id == DEFAULT_TENANT_ID))
        await db.execute(delete(Customer).where(Customer.tenant_id == DEFAULT_TENANT_ID))

        # 保留 default-board，删除其他看板
        await db.execute(delete(Board).where(Board.tenant_id == DEFAULT_TENANT_ID, Board.id != "default-board"))

        await db.commit()
        print("   ✅ 清除完成")


async def init_demo_data() -> None:
    """初始化 Demo 示例数据"""
    async with async_db_session.begin() as db:
        print("=" * 60)
        print("🚀 Demo 示例数据初始化")
        print("=" * 60)
        print()

        # 1. 创建看板
        print("📋 创建看板...")
        board_ids = []

        # 获取默认看板
        default_board = await db.scalar(select(Board).where(Board.id == "default-board"))
        if default_board:
            board_ids.append(default_board.id)

        for board_data in DEMO_BOARDS:
            board_id = uuid4_str()
            board = Board(
                id=board_id,
                tenant_id=DEFAULT_TENANT_ID,
                name=board_data["name"],
                url_name=board_data["url_name"],
                description=board_data["description"],
            )
            db.add(board)
            board_ids.append(board_id)
            print(f"   ✅ {board_data['name']}")

        await db.flush()

        # 2. 创建客户
        print()
        print("👥 创建客户...")
        customer_ids = []

        for customer_data in DEMO_CUSTOMERS:
            customer_id = uuid4_str()
            customer = Customer(
                id=customer_id,
                tenant_id=DEFAULT_TENANT_ID,
                name=customer_data["name"],
                company_name=customer_data.get("company_name"),
                customer_type=customer_data["customer_type"],
                business_value=customer_data["business_value"],
                contact_email=customer_data.get("contact_email"),
            )
            db.add(customer)
            customer_ids.append(customer_id)
            print(f"   ✅ {customer_data['name']}")

        await db.flush()

        # 3. 创建议题
        print()
        print("📑 创建议题...")
        topic_ids = []

        for topic_data in DEMO_TOPICS:
            topic_id = uuid4_str()
            topic = Topic(
                id=topic_id,
                tenant_id=DEFAULT_TENANT_ID,
                board_id=random.choice(board_ids),
                title=topic_data["title"],
                description=topic_data["description"],
                status=topic_data["status"],
                ai_generated=True,
            )
            db.add(topic)
            topic_ids.append(topic_id)
            print(f"   ✅ {topic_data['title']}")

        await db.flush()

        # 4. 创建反馈
        print()
        print("💬 创建反馈...")
        feedback_count = 0

        for feedback_data in FEEDBACK_TEMPLATES:
            # 为每个模板创建 2-5 条相似反馈
            for _ in range(random.randint(2, 5)):
                feedback_id = uuid4_str()

                # 随机选择看板、客户、议题
                board_id = random.choice(board_ids)
                customer_id = random.choice(customer_ids) if random.random() > 0.3 else None
                topic_id = random.choice(topic_ids) if random.random() > 0.4 else None

                # 根据是否有customer_id设置author_type
                if customer_id:
                    author_type = "customer"
                    external_user_name = None
                else:
                    author_type = "external"
                    external_user_name = f"匿名用户{random.randint(1000, 9999)}"

                # 随机生成提交时间（最近 30 天）
                days_ago = random.randint(0, 30)
                submitted_at = datetime.now() - timedelta(days=days_ago)

                feedback = Feedback(
                    id=feedback_id,
                    tenant_id=DEFAULT_TENANT_ID,
                    board_id=board_id,
                    customer_id=customer_id,
                    author_type=author_type,
                    external_user_name=external_user_name,
                    topic_id=topic_id,
                    content=feedback_data["content"],
                    source=feedback_data["source"],
                    is_urgent=feedback_data["is_urgent"],
                    submitted_at=submitted_at,
                    clustering_status="clustered" if topic_id else "pending",
                )
                db.add(feedback)
                feedback_count += 1

        print(f"   ✅ 创建 {feedback_count} 条反馈")

        await db.commit()

        print()
        print("=" * 60)
        print("✅ Demo 示例数据初始化完成！")
        print("=" * 60)
        print()
        print("📊 数据统计：")
        print(f"   看板: {len(DEMO_BOARDS) + 1} 个")
        print(f"   客户: {len(DEMO_CUSTOMERS)} 个")
        print(f"   议题: {len(DEMO_TOPICS)} 个")
        print(f"   反馈: {feedback_count} 条")


async def main(reset: bool = False) -> None:
    """主函数"""
    if reset:
        await clear_demo_data()
        print()

    await init_demo_data()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="初始化 Demo 示例数据")
    parser.add_argument("--reset", action="store_true", help="重置模式：先清除现有数据再重建")
    args = parser.parse_args()

    try:
        asyncio.run(main(reset=args.reset))
        print()
        print("🎉 初始化完成！")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
