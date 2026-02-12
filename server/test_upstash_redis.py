#!/usr/bin/env python
"""
Upstash Redis 连接测试脚本

测试 Upstash Redis 的连接、读写、性能等功能
"""
import asyncio
import time
from backend.database.redis import redis_client
from backend.core.conf import settings


async def test_basic_connection():
    """测试基本连接"""
    print("=" * 60)
    print("🔌 测试 1: 基本连接")
    print("=" * 60)
    
    try:
        start = time.time()
        await redis_client.ping()
        elapsed = time.time() - start
        print(f"✅ PING 成功 ({elapsed:.3f}s)")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


async def test_read_write():
    """测试读写操作"""
    print("\n" + "=" * 60)
    print("📝 测试 2: 读写操作")
    print("=" * 60)
    
    try:
        # 写入测试
        test_key = "feedalyze:test:timestamp"
        test_value = f"test_{int(time.time())}"
        
        await redis_client.set(test_key, test_value, ex=30)
        print(f"✅ 写入成功: {test_key} = {test_value}")
        
        # 读取测试
        value = await redis_client.get(test_key)
        if value == test_value:
            print(f"✅ 读取成功: {value}")
        else:
            print(f"❌ 读取失败: 期望 {test_value}, 实际 {value}")
            return False
        
        # 删除测试
        await redis_client.delete(test_key)
        value = await redis_client.get(test_key)
        if value is None:
            print("✅ 删除成功")
        else:
            print(f"❌ 删除失败: 键仍然存在")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 读写测试失败: {e}")
        return False


async def test_batch_operations():
    """测试批量操作"""
    print("\n" + "=" * 60)
    print("📦 测试 3: 批量操作")
    print("=" * 60)
    
    try:
        # 批量写入
        test_keys = {f"feedalyze:batch:key{i}": f"value{i}" for i in range(10)}
        
        pipe = redis_client.pipeline()
        for key, value in test_keys.items():
            pipe.set(key, value, ex=30)
        await pipe.execute()
        print(f"✅ 批量写入 {len(test_keys)} 个键")
        
        # 批量读取
        values = await redis_client.mget(*test_keys.keys())
        if all(v is not None for v in values):
            print(f"✅ 批量读取成功: {len(values)} 个键")
        else:
            print(f"❌ 批量读取失败")
            return False
        
        # 批量删除
        await redis_client.delete(*test_keys.keys())
        print(f"✅ 批量删除成功")
        
        return True
    except Exception as e:
        print(f"❌ 批量操作失败: {e}")
        return False


async def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("⚡ 测试 4: 性能测试")
    print("=" * 60)
    
    try:
        # 测试延迟
        latencies = []
        for _ in range(5):
            start = time.time()
            await redis_client.ping()
            latencies.append((time.time() - start) * 1000)  # 转为毫秒
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"✅ 平均延迟: {avg_latency:.2f}ms")
        
        if avg_latency < 100:
            print("   🚀 性能优秀 (< 100ms)")
        elif avg_latency < 300:
            print("   👍 性能良好 (< 300ms)")
        else:
            print("   ⚠️  延迟较高，建议检查网络")
        
        return True
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


async def test_plugin_cleanup():
    """测试插件缓存清理（模拟启动时的操作）"""
    print("\n" + "=" * 60)
    print("🔧 测试 5: 插件缓存清理")
    print("=" * 60)
    
    try:
        # 创建测试插件缓存
        test_prefix = "fba:plugin:test"
        test_keys = [f"{test_prefix}:plugin1", f"{test_prefix}:plugin2"]
        
        for key in test_keys:
            await redis_client.set(key, "test_data", ex=60)
        print(f"✅ 创建 {len(test_keys)} 个测试插件缓存")
        
        # 测试 delete_prefix（这是启动时会执行的操作）
        await redis_client.delete_prefix(test_prefix)
        
        # 验证清理
        remaining = await redis_client.get_prefix(test_prefix)
        if not remaining:
            print("✅ 插件缓存清理成功")
            return True
        else:
            print(f"❌ 清理失败，仍有 {len(remaining)} 个键")
            return False
            
    except Exception as e:
        print(f"❌ 插件缓存清理失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Upstash Redis 测试套件" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print(f"📍 REDIS_URL: {settings.REDIS_URL[:30]}..." if settings.REDIS_URL else "localhost")
    print(f"⏱️  超时设置: 30s (Upstash 云连接)")
    print()
    
    tests = [
        ("基本连接", test_basic_connection),
        ("读写操作", test_read_write),
        ("批量操作", test_batch_operations),
        ("性能测试", test_performance),
        ("插件清理", test_plugin_cleanup),
    ]
    
    results = []
    for name, test_func in tests:
        result = await test_func()
        results.append((name, result))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Upstash Redis 配置正确！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
