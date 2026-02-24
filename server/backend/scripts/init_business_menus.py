"""初始化业务菜单和角色

此脚本用于创建 UserEcho 业务功能的租户权限和角色。
执行方式: python scripts/init_business_menus.py
"""

import asyncio
import io
import os
import sys

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

from sqlalchemy import select

from backend.app.admin.model import Menu, Role
from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao
from backend.app.userecho.crud.crud_tenant_permission import tenant_permission_dao
from backend.app.userecho.crud.crud_tenant_role import tenant_role_dao
from backend.app.userecho.model.tenant import Tenant
from backend.app.userecho.model.tenant_permission import TenantPermission

# 从 tenant_role_service.py 导入角色定义
from backend.app.userecho.service.tenant_role_service import BUILTIN_ROLES
from backend.database.db import async_db_session, uuid4_str

# 从 init_business_permissions.py 导入权限定义
from backend.scripts.init_business_permissions import BUSINESS_PERMISSIONS
from backend.utils.timezone import timezone


async def init_tenant_permissions(db) -> dict[str, str]:
    """初始化租户权限点

    Returns:
        dict[str, str]: 权限码到权限ID的映射
    """
    print("\n1️⃣  初始化租户权限点...")

    # 获取现有权限
    stmt = select(TenantPermission)
    result = await db.execute(stmt)
    existing_permissions = {p.code: p for p in result.scalars().all()}

    # 用于存储权限 ID
    permission_ids: dict[str, str] = {code: p.id for code, p in existing_permissions.items()}

    created_count = 0
    updated_count = 0

    for perm_data in BUSINESS_PERMISSIONS:
        code = perm_data["code"]
        parent_code = perm_data.get("parent_code")

        # 计算 parent_id
        parent_id = None
        if parent_code and parent_code in permission_ids:
            parent_id = permission_ids[parent_code]

        if code in existing_permissions:
            # 更新现有权限
            existing = existing_permissions[code]
            need_update = False

            if existing.menu_path != perm_data.get("menu_path"):
                existing.menu_path = perm_data.get("menu_path")
                need_update = True
            if existing.menu_icon != perm_data.get("menu_icon"):
                existing.menu_icon = perm_data.get("menu_icon")
                need_update = True
            if existing.parent_id != parent_id:
                existing.parent_id = parent_id
                need_update = True
            if existing.sort != perm_data.get("sort", 0):
                existing.sort = perm_data.get("sort", 0)
                need_update = True

            if need_update:
                updated_count += 1
        else:
            # 创建新权限
            new_perm = TenantPermission(
                id=uuid4_str(),
                parent_id=parent_id,
                name=perm_data["name"],
                code=code,
                type=perm_data.get("type", "module"),
                menu_path=perm_data.get("menu_path"),
                menu_icon=perm_data.get("menu_icon"),
                sort=perm_data.get("sort", 0),
                created_time=timezone.now(),
            )
            db.add(new_perm)
            permission_ids[code] = new_perm.id
            created_count += 1

    await db.flush()

    if created_count > 0:
        print(f"   ✅ 创建 {created_count} 个权限点")
    if updated_count > 0:
        print(f"   🔄 更新 {updated_count} 个权限点")
    if created_count == 0 and updated_count == 0:
        print("   ⏭️  所有权限点已是最新")

    print(f"   📊 权限点总数: {len(permission_ids)}")

    return permission_ids


async def init_tenant_roles(db, tenant_id: str, permission_ids: dict[str, str]) -> None:
    """为租户初始化内置角色"""
    print("\n2️⃣  为租户初始化角色...")

    created_count = 0
    updated_count = 0

    for i, role_def in enumerate(BUILTIN_ROLES):
        # 检查是否已存在
        existing = await tenant_role_dao.get_by_code(db, tenant_id, role_def["code"])

        if existing:
            # 更新现有角色的权限
            perm_ids = [permission_ids[code] for code in role_def["permissions"] if code in permission_ids]
            if perm_ids:
                await tenant_permission_dao.set_role_permissions(db, existing.id, perm_ids)
                updated_count += 1
            continue

        # 创建角色
        role = await tenant_role_dao.create(
            db,
            tenant_id=tenant_id,
            name=role_def["name"],
            code=role_def["code"],
            description=role_def["description"],
            is_builtin=True,
            sort=i,
        )

        # 设置权限
        perm_ids = [permission_ids[code] for code in role_def["permissions"] if code in permission_ids]
        if perm_ids:
            await tenant_permission_dao.set_role_permissions(db, role.id, perm_ids)

        created_count += 1

    await db.flush()

    if created_count > 0:
        print(f"   ✅ 创建 {created_count} 个角色")
    if updated_count > 0:
        print(f"   🔄 更新 {updated_count} 个角色权限")
    if created_count == 0 and updated_count == 0:
        print("   ⏭️  所有角色已存在")


async def assign_default_roles(db, tenant_id: str) -> None:
    """为租户用户分配默认角色"""
    print("\n3️⃣  为租户用户分配默认角色...")

    # 获取 admin 角色
    admin_role = await tenant_role_dao.get_by_code(db, tenant_id, "admin")
    if not admin_role:
        print("   ⚠️  警告: admin 角色不存在，跳过用户角色分配")
        return

    # 获取租户的所有活跃用户
    members = await tenant_member_dao.get_list(db, tenant_id, status="active")

    if not members:
        print("   ⏭️  租户暂无用户")
        return

    assigned_count = 0
    for member in members:
        # 检查用户是否已有角色
        existing_roles = await tenant_member_dao.get_member_roles(db, member.id)
        if existing_roles:
            continue

        # 分配 admin 角色
        await tenant_member_dao.set_member_roles(db, member.id, [admin_role.id])
        assigned_count += 1

    await db.flush()

    if assigned_count > 0:
        print(f"   ✅ 为 {assigned_count} 个用户分配 admin 角色")
    else:
        print("   ⏭️  所有用户已有角色")


async def cleanup_system_roles(db) -> None:
    """清理系统角色，只保留超级管理员"""
    print("\n4️⃣  清理系统角色...")

    # 获取所有系统角色
    stmt = select(Role).where(Role.role_type == "system")
    result = await db.execute(stmt)
    system_roles = result.scalars().all()

    deleted_count = 0
    kept_roles = []

    for role in system_roles:
        # 保留超级管理员角色（通过名称判断）
        if role.name in ["admin", "超级管理员", "Admin", "Administrator"]:
            kept_roles.append(role.name)
            continue

        # 删除其他系统角色
        await db.delete(role)
        deleted_count += 1

    await db.flush()

    if deleted_count > 0:
        print(f"   🗑️  删除 {deleted_count} 个系统角色")
    print(f"   ✅ 保留角色: {', '.join(kept_roles) if kept_roles else '无'}")


async def cleanup_old_business_menus(db) -> None:
    """清理旧的业务菜单（sys_menus 表中的 /app/* 菜单）"""
    print("\n5️⃣  清理旧的业务菜单...")

    # 获取所有 /app/* 菜单
    stmt = select(Menu).where(Menu.path.like("/app/%"))
    result = await db.execute(stmt)
    old_menus = result.scalars().all()

    if not old_menus:
        print("   ⏭️  无需清理")
        return

    deleted_count = 0
    for menu in old_menus:
        await db.delete(menu)
        deleted_count += 1

    await db.flush()
    print(f"   🗑️  删除 {deleted_count} 个旧菜单")


async def get_default_tenant(db):
    """获取默认租户"""
    # 优先获取状态为 active 的租户
    stmt = select(Tenant).where(Tenant.status == "active").limit(1)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        # 如果没有 active 租户，获取任意租户
        stmt = select(Tenant).limit(1)
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()

    return tenant


async def init_business_menus() -> None:
    """初始化业务菜单和角色

    主要功能：
    1. 初始化租户权限点（TenantPermission）
    2. 为默认租户初始化内置角色（TenantRole）
    3. 关联角色和权限（TenantRolePermission）
    4. 清理系统角色，只保留超级管理员
    5. 清理旧的业务菜单（sys_menus 表中的 /app/* 菜单）
    """
    async with async_db_session.begin() as db:
        print("=" * 60)
        print("🚀 UserEcho 业务菜单和角色初始化脚本")
        print("=" * 60)

        # 1. 初始化租户权限点
        permission_ids = await init_tenant_permissions(db)

        # 2. 获取默认租户
        default_tenant = await get_default_tenant(db)

        if not default_tenant:
            print("\n⚠️  警告: 未找到租户，跳过角色初始化")
            print("   请先运行: python backend/scripts/init_default_tenant.py")
        else:
            print(f"\n📌 默认租户: {default_tenant.name} (ID: {default_tenant.id})")

            # 3. 初始化租户角色
            await init_tenant_roles(db, default_tenant.id, permission_ids)

            # 4. 为租户用户分配默认角色
            await assign_default_roles(db, default_tenant.id)

        # 5. 清理系统角色
        await cleanup_system_roles(db)

        # 6. 清理旧的业务菜单
        await cleanup_old_business_menus(db)

        print("\n" + "=" * 60)
        print("✅ 初始化完成！")
        print("=" * 60)
        print("\n📝 初始化内容：")
        print(f"   - {len(permission_ids)} 个租户权限点")
        if default_tenant:
            print(f"   - {len(BUILTIN_ROLES)} 个内置角色（租户: {default_tenant.name}）")
            print("   - 为租户用户分配默认角色")
        print("   - 清理系统角色（只保留超级管理员）")
        print("   - 清理旧的业务菜单（/app/*）")
        print("\n💡 提示：")
        print("   - 业务菜单现在由前端 business-menus.ts 定义")
        print("   - 根据租户权限码动态渲染")
        print("   - 系统菜单（/admin/*）仍由后端数据库管理")


async def verify_initialization() -> None:
    """验证初始化结果"""
    async with async_db_session() as db:
        print("\n\n🔍 验证初始化结果...")

        # 检查租户权限点
        stmt = select(TenantPermission)
        result = await db.execute(stmt)
        permissions = list(result.scalars().all())
        print(f"\n📋 租户权限点数量: {len(permissions)}")
        for perm in sorted(permissions, key=lambda p: p.sort):
            parent_info = f" (父级: {perm.parent_id[:8]}...)" if perm.parent_id else ""
            print(f"   - {perm.code}: {perm.name}{parent_info}")

        # 检查默认租户的角色
        default_tenant = await get_default_tenant(db)
        if default_tenant:
            from backend.app.userecho.model.tenant_role import TenantRole

            stmt = select(TenantRole).where(TenantRole.tenant_id == default_tenant.id)
            result = await db.execute(stmt)
            roles = list(result.scalars().all())
            print(f"\n👥 租户角色数量 (租户: {default_tenant.name}): {len(roles)}")
            for role in sorted(roles, key=lambda r: r.sort):
                # 获取角色权限
                role_perms = await tenant_permission_dao.get_role_permission_codes(db, role.id)
                print(f"   - {role.name} ({role.code}): {', '.join(role_perms)}")

            # 检查用户角色分配
            members = await tenant_member_dao.get_list(db, default_tenant.id, status="active")
            print(f"\n👤 租户用户角色分配 (租户: {default_tenant.name}): {len(members)} 个用户")
            for member in members:
                member_roles = await tenant_member_dao.get_member_roles(db, member.id)
                role_names = []
                for ur in member_roles:
                    role = await db.get(TenantRole, ur.role_id)
                    if role:
                        role_names.append(role.name)
                print(f"   - 用户 ID {member.user_id}: {', '.join(role_names) if role_names else '无角色'}")

        # 检查系统角色
        stmt = select(Role).where(Role.role_type == "system")
        result = await db.execute(stmt)
        system_roles = list(result.scalars().all())
        print(f"\n🔧 系统角色数量: {len(system_roles)}")
        for role in system_roles:
            print(f"   - {role.name}")

        # 检查业务菜单
        stmt = select(Menu).where(Menu.path.like("/app/%"))
        result = await db.execute(stmt)
        business_menus = list(result.scalars().all())
        print(f"\n📱 业务菜单数量 (sys_menus 表): {len(business_menus)}")
        if business_menus:
            print("   ⚠️  警告: 仍有业务菜单在 sys_menus 表中")
            for menu in business_menus:
                print(f"   - {menu.title} ({menu.path})")


async def main() -> None:
    """主函数：合并初始化和验证到同一个 event loop"""
    await init_business_menus()
    await verify_initialization()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
