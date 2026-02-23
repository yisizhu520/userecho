"""
手动添加截图相关字段到 feedbacks 表
执行: python scripts/add_screenshot_fields.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from backend.database.db import async_engine


async def add_screenshot_fields() -> bool:
    """添加截图相关字段"""
    print("=" * 70)
    print("📦 添加截图相关字段到 feedbacks 表")
    print("=" * 70)

    sqls = [
        # 添加新字段
        """
        ALTER TABLE feedbacks
        ADD COLUMN IF NOT EXISTS screenshot_url TEXT,
        ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50),
        ADD COLUMN IF NOT EXISTS source_user_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS source_user_id VARCHAR(255),
        ADD COLUMN IF NOT EXISTS ai_confidence FLOAT,
        ADD COLUMN IF NOT EXISTS submitter_id BIGINT
        """,
        # 添加外键约束
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'feedbacks_submitter_id_fkey'
            ) THEN
                ALTER TABLE feedbacks
                ADD CONSTRAINT feedbacks_submitter_id_fkey
                FOREIGN KEY (submitter_id) REFERENCES sys_user(id) ON DELETE SET NULL;
            END IF;
        END$$
        """,
        # 添加注释
        "COMMENT ON COLUMN feedbacks.screenshot_url IS '截图 OSS 地址'",
        "COMMENT ON COLUMN feedbacks.source_platform IS '来源平台: wechat, xiaohongshu, appstore, weibo, other'",
        "COMMENT ON COLUMN feedbacks.source_user_name IS '来源平台用户昵称'",
        "COMMENT ON COLUMN feedbacks.source_user_id IS '来源平台用户 ID'",
        "COMMENT ON COLUMN feedbacks.ai_confidence IS 'AI 识别置信度 (0.00-1.00)'",
        "COMMENT ON COLUMN feedbacks.submitter_id IS '内部提交者（员工）ID'",
        "COMMENT ON COLUMN feedbacks.source IS '来源: manual, import, api, screenshot'",
    ]

    try:
        async with async_engine.begin() as conn:
            for sql in sqls:
                await conn.execute(sa.text(sql))

        print("✅ 字段添加成功！")
        print()
        print("新增字段:")
        print("  - screenshot_url (TEXT): 截图 OSS 地址")
        print("  - source_platform (VARCHAR(50)): 来源平台")
        print("  - source_user_name (VARCHAR(255)): 来源平台用户昵称")
        print("  - source_user_id (VARCHAR(255)): 来源平台用户 ID")
        print("  - ai_confidence (FLOAT): AI 识别置信度")
        print("  - submitter_id (BIGINT): 内部提交者 ID (外键 → sys_user.id)")

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    import sqlalchemy as sa

    success = asyncio.run(add_screenshot_fields())
    sys.exit(0 if success else 1)
