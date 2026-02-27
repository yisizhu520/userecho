#!/usr/bin/env python3
"""测试 Redis 连接"""

import sys

try:
    import redis
except ImportError:
    print("❌ redis 模块未安装，尝试安装...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
    import redis

# Redis 配置
REDIS_CONFIG = {
    "host": "38.162.115.176",
    "port": 6379,
    "password": "maokutest",
    "db": 0,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
}

print(
    f"正在测试 Redis 连接: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']} (db={REDIS_CONFIG['db']})"
)
print("=" * 70)

try:
    # 创建连接
    r = redis.Redis(**REDIS_CONFIG)  # type: ignore[call-overload]

    # 测试 PING
    print("✓ PING 测试:", r.ping())

    # 获取服务器信息
    server_info = r.info("server")
    print(f"✓ Redis 版本: {server_info.get('redis_version', 'N/A')}")
    print(f"✓ 操作系统: {server_info.get('os', 'N/A')}")
    print(f"✓ 运行模式: {server_info.get('redis_mode', 'N/A')}")

    # 测试基本操作
    test_key = "__test_connection__"
    r.set(test_key, "test_value", ex=10)
    value = r.get(test_key)
    print(f"✓ SET/GET 测试: {value.decode() if value else 'FAILED'}")
    r.delete(test_key)

    # 测试数据库切换
    r.select(1)
    print("✓ 数据库切换测试: 成功切换到 db=1")
    r.select(0)

    print("=" * 70)
    print("✅ Redis 连接正常！所有测试通过！")
    sys.exit(0)

except redis.ConnectionError as e:
    print("=" * 70)
    print(f"❌ 连接失败: {e}")
    print("\n可能原因：")
    print("  1. Redis 服务器未启动")
    print("  2. 网络无法访问（防火墙/安全组）")
    print("  3. IP 地址错误")
    sys.exit(1)

except redis.AuthenticationError as e:
    print("=" * 70)
    print(f"❌ 认证失败: {e}")
    print("\n可能原因：")
    print("  1. 密码错误")
    print("  2. Redis 未配置密码但提供了密码")
    sys.exit(1)

except Exception as e:
    print("=" * 70)
    print(f"❌ 未知错误: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
