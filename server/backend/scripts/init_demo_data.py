"""初始化 Demo 环境示例数据

创建用于演示的反馈、客户、议题等数据

执行方式: python scripts/init_demo_data.py
"""

import asyncio
import io
import random
import sys

from datetime import datetime, timedelta
from pathlib import Path

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
    {"name": "产品反馈", "description": "收集用户对产品功能的反馈和建议", "color": "#3b82f6"},
    {"name": "客户投诉", "description": "处理客户投诉和问题报告", "color": "#ef4444"},
    {"name": "功能需求", "description": "用户提出的新功能需求", "color": "#10b981"},
]

DEMO_CUSTOMERS = [
    {
        "name": "腾讯游戏",
        "customer_type": "enterprise",
        "business_value": 5,
        "contact_name": "张三",
        "contact_email": "zhangsan@tencent.com",
    },
    {
        "name": "阿里云",
        "customer_type": "enterprise",
        "business_value": 5,
        "contact_name": "李四",
        "contact_email": "lisi@alibaba.com",
    },
    {
        "name": "字节跳动",
        "customer_type": "enterprise",
        "business_value": 4,
        "contact_name": "王五",
        "contact_email": "wangwu@bytedance.com",
    },
    {
        "name": "美团点评",
        "customer_type": "enterprise",
        "business_value": 4,
        "contact_name": "赵六",
        "contact_email": "zhaoliu@meituan.com",
    },
    {
        "name": "小米科技",
        "customer_type": "enterprise",
        "business_value": 4,
        "contact_name": "钱七",
        "contact_email": "qianqi@xiaomi.com",
    },
    {
        "name": "京东商城",
        "customer_type": "enterprise",
        "business_value": 4,
        "contact_name": "孙八",
        "contact_email": "sunba@jd.com",
    },
    {
        "name": "网易有道",
        "customer_type": "enterprise",
        "business_value": 3,
        "contact_name": "周九",
        "contact_email": "zhoujiu@netease.com",
    },
    {
        "name": "哔哩哔哩",
        "customer_type": "enterprise",
        "business_value": 3,
        "contact_name": "吴十",
        "contact_email": "wushi@bilibili.com",
    },
    {
        "name": "创业公司A",
        "customer_type": "startup",
        "business_value": 2,
        "contact_name": "陈一",
        "contact_email": "chenyi@startup-a.com",
    },
    {
        "name": "创业公司B",
        "customer_type": "startup",
        "business_value": 2,
        "contact_name": "林二",
        "contact_email": "liner@startup-b.com",
    },
]

FEEDBACK_TEMPLATES = [
    # 数据导出相关
    {"content": "希望能支持导出 Excel 报表，方便做数据分析", "is_urgent": False, "source": "crm"},
    {"content": "需要 PDF 导出功能，用于给领导汇报", "is_urgent": False, "source": "zendesk"},
    {"content": "数据导出太慢了，等了好久才下载完", "is_urgent": True, "source": "intercom"},
    {"content": "希望导出的报表能包含图表", "is_urgent": False, "source": "email"},
    # 性能优化相关
    {"content": "页面加载速度有点慢，首屏需要 5 秒以上", "is_urgent": True, "source": "crm"},
    {"content": "列表数据多的时候卡顿明显", "is_urgent": True, "source": "zendesk"},
    {"content": "搜索功能响应太慢，影响工作效率", "is_urgent": False, "source": "intercom"},
    {"content": "希望能优化移动端的加载速度", "is_urgent": False, "source": "wechat"},
    # 暗色主题
    {"content": "希望有暗色模式，晚上使用太刺眼了", "is_urgent": False, "source": "crm"},
    {"content": "能不能加个夜间模式？", "is_urgent": False, "source": "email"},
    {"content": "深色主题什么时候上线？", "is_urgent": False, "source": "wechat"},
    # 批量操作
    {"content": "需要批量删除功能，一条条删太麻烦", "is_urgent": False, "source": "crm"},
    {"content": "希望支持批量导入数据", "is_urgent": True, "source": "zendesk"},
    {"content": "批量编辑功能什么时候能有？", "is_urgent": False, "source": "intercom"},
    # 移动端体验
    {"content": "手机上操作不太方便，按钮太小", "is_urgent": False, "source": "wechat"},
    {"content": "iPad 上的布局有点奇怪", "is_urgent": False, "source": "email"},
    {"content": "移动端什么时候能支持手势操作？", "is_urgent": False, "source": "crm"},
    # 权限管理
    {"content": "希望能更细粒度地控制权限", "is_urgent": False, "source": "crm"},
    {"content": "角色权限配置太复杂了", "is_urgent": False, "source": "zendesk"},
    # 通知提醒
    {"content": "能不能加个消息通知功能？", "is_urgent": False, "source": "intercom"},
    {"content": "希望重要事件能发邮件提醒", "is_urgent": False, "source": "email"},
    {"content": "想要微信通知推送", "is_urgent": False, "source": "wechat"},
    # 数据统计
    {"content": "希望有更详细的数据统计报表", "is_urgent": False, "source": "crm"},
    {"content": "能不能加个仪表盘展示关键指标？", "is_urgent": False, "source": "zendesk"},
    # 功能建议
    {"content": "希望能支持自定义字段", "is_urgent": False, "source": "crm"},
    {"content": "能不能集成钉钉？", "is_urgent": True, "source": "email"},
    {"content": "希望支持 API 对接", "is_urgent": True, "source": "intercom"},
    {"content": "标签功能能不能支持多层级？", "is_urgent": False, "source": "wechat"},
    # BUG 反馈
    {"content": "登录偶尔会自动退出", "is_urgent": True, "source": "crm"},
    {"content": "上传图片有时候会失败", "is_urgent": True, "source": "zendesk"},
]

DEMO_TOPICS = [
    {
        "title": "数据导出功能优化",
        "description": "支持 Excel、PDF 等多种格式导出",
        "status": "new",
        "priority_score": 85.5,
    },
    {
        "title": "首屏加载性能优化",
        "description": "优化首屏加载时间，提升用户体验",
        "status": "review",
        "priority_score": 92.3,
    },
    {"title": "暗色主题支持", "description": "添加暗色/深色模式切换功能", "status": "approved", "priority_score": 68.7},
    {"title": "批量操作功能", "description": "支持批量删除、批量编辑等操作", "status": "new", "priority_score": 75.2},
    {"title": "移动端体验优化", "description": "优化移动端布局和交互体验", "status": "review", "priority_score": 62.8},
    {"title": "权限管理增强", "description": "支持更细粒度的权限控制", "status": "new", "priority_score": 55.4},
    {
        "title": "消息通知系统",
        "description": "支持站内消息、邮件、微信等多渠道通知",
        "status": "approved",
        "priority_score": 78.9,
    },
    {"title": "数据统计仪表盘", "description": "提供可视化的数据统计报表", "status": "new", "priority_score": 71.5},
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
                description=board_data["description"],
                color=board_data["color"],
                status="active",
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
                customer_type=customer_data["customer_type"],
                business_value=customer_data["business_value"],
                contact_name=customer_data.get("contact_name"),
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
                priority_score=topic_data["priority_score"],
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

                # 随机生成提交时间（最近 30 天）
                days_ago = random.randint(0, 30)
                submitted_at = datetime.now() - timedelta(days=days_ago)

                feedback = Feedback(
                    id=feedback_id,
                    tenant_id=DEFAULT_TENANT_ID,
                    board_id=board_id,
                    customer_id=customer_id,
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
