"""检查并关闭登录验证码配置"""

import asyncio
from backend.database.db import async_db_session
from backend.plugin.config.crud.crud_config import config_dao
from backend.plugin.config.enums import ConfigType


async def main():
    async with async_db_session() as db:
        configs = await config_dao.get_all(db, ConfigType.login)
        if configs:
            print("当前登录配置:")
            for c in configs:
                if c:  # type guard
                    print(f"  {c.key} = {c.value}")

            # 查找验证码配置
            captcha_config = next((c for c in configs if c and c.key == "LOGIN_CAPTCHA_ENABLED"), None)
            if captcha_config:
                if captcha_config.value == "true":
                    print("\n正在关闭验证码...")
                    captcha_config.value = "false"
                    await db.commit()
                    print("✅ 验证码已关闭")
                else:
                    print("\n✅ 验证码已经是关闭状态")
            else:
                print("\n⚠️  未找到 LOGIN_CAPTCHA_ENABLED 配置")
        else:
            print("未找到登录配置")


if __name__ == "__main__":
    asyncio.run(main())
