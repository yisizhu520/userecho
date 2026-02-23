#!/usr/bin/env python3
"""
为 default-tenant 租户中的 boss 用户设置租户管理员角色

用法：
    python set_boss_as_admin.py
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao
from backend.app.userecho.crud.crud_tenant_role import tenant_role_dao
from backend.common.log import log
from backend.database.db import async_db_session, async_engine


async def set_boss_as_admin(db: AsyncSession) -> None:
    """为 boss 用户设置租户管理员角色"""
    tenant_id = "default-tenant"
    username = "boss"

    log.info(f"开始为租户 {tenant_id} 中的用户 {username} 设置管理员角色")

    # 1. 查找 boss 用户
    boss_user = await user_dao.get_by_username(db, username)
    if not boss_user:
        log.error(f"❌ 用户 {username} 不存在")
        raise ValueError(f"用户 {username} 不存在")

    log.info(f"✅ 找到用户: {boss_user.username} (ID: {boss_user.id})")

    # 2. 查找或创建租户成员关联
    tenant_member = await tenant_member_dao.get_by_user_id(db, tenant_id, boss_user.id)

    if not tenant_member:
        log.info(f"用户 {username} 还不是租户 {tenant_id} 的成员，正在创建关联...")
        tenant_member = await tenant_member_dao.create(db, tenant_id=tenant_id, user_id=boss_user.id, user_type="admin")
        log.info(f"✅ 创建租户成员关联成功 (ID: {tenant_member.id})")
    else:
        log.info(f"✅ 找到租户成员关联 (ID: {tenant_member.id})")
        # 更新 user_type 为 admin
        if tenant_member.user_type != "admin":
            await tenant_member_dao.update(db, tenant_member, user_type="admin")
            log.info("✅ 更新用户类型为 admin")

    # 3. 查找租户管理员角色
    admin_role = await tenant_role_dao.get_by_code(db, tenant_id, "admin")

    if not admin_role:
        log.error(f"❌ 租户 {tenant_id} 中不存在 admin 角色")
        log.info("💡 提示: 请先运行 init_tenant_roles.py 初始化租户角色")
        raise ValueError(f"租户 {tenant_id} 中不存在 admin 角色")

    log.info(f"✅ 找到管理员角色: {admin_role.name} (ID: {admin_role.id})")

    # 4. 为用户分配管理员角色
    await tenant_member_dao.set_member_roles(db, tenant_member.id, [admin_role.id], assigned_by=boss_user.id)

    log.info(f"✅ 成功为用户 {username} 分配管理员角色")

    # 5. 提交事务
    await db.commit()
    log.info("✅ 事务提交成功")

    # 6. 验证结果
    member_roles = await tenant_member_dao.get_member_roles(db, tenant_member.id)
    log.info(f"📋 用户当前拥有的角色: {[r.role_id for r in member_roles]}")


async def main() -> None:
    """主函数"""
    try:
        async with async_db_session() as db:
            await set_boss_as_admin(db)

        log.info("🎉 设置完成！boss 用户现在是 default-tenant 的租户管理员")
    except Exception as e:
        log.error(f"❌ 设置失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
