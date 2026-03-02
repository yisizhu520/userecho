"""配置验证脚本

检查 API Keys 是否正确配置,并测试连通性

运行方式:
    cd server
    python scripts/embedding_comparison/00_verify_config.py
"""

import asyncio

from backend.common.log import log
from backend.core.conf import settings
from backend.utils.ai_client import AIClient


async def verify_provider(provider_name: str, api_key: str | None) -> dict:
    """
    验证单个 provider 的配置
    
    Args:
        provider_name: provider 名称
        api_key: API Key
        
    Returns:
        验证结果
    """
    if not api_key:
        return {
            "provider": provider_name,
            "status": "not_configured",
            "message": f"{provider_name.upper()}_API_KEY not set",
        }
    
    print(f"Testing {provider_name}...")
    
    try:
        # ✅ 直接使用 provider 参数，不修改全局状态
        client = AIClient()
        
        # 测试 embedding API
        test_text = "这是一条测试反馈"
        embedding = await client.get_embeddings_batch([test_text], provider=provider_name)
        
        if embedding and embedding[0]:
            return {
                "provider": provider_name,
                "status": "success",
                "message": f"✅ {provider_name} API working",
                "embedding_dim": len(embedding[0]),
            }
        else:
            return {
                "provider": provider_name,
                "status": "failed",
                "message": f"❌ {provider_name} API failed to return embedding",
            }
    
    except Exception as e:
        return {
            "provider": provider_name,
            "status": "failed",
            "message": f"❌ {provider_name} API error: {e}",
        }


async def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("配置验证".center(80))
    print("=" * 80 + "\n")
    
    # 1. 检查配置
    providers = {
        "volcengine": getattr(settings, "VOLCENGINE_API_KEY", None),
        "openai": getattr(settings, "OPENAI_API_KEY", None),
        "glm": getattr(settings, "GLM_API_KEY", None),
        "qwen": getattr(settings, "DASHSCOPE_API_KEY", None),
    }
    
    print("📋 配置检查:\n")
    for provider, api_key in providers.items():
        status = "✅ 已配置" if api_key else "❌ 未配置"
        print(f"  {provider.upper()}_API_KEY: {status}")
    
    print("\n" + "-" * 80 + "\n")
    
    # 2. 测试连通性
    print("🔍 测试 API 连通性:\n")
    
    results = []
    for provider, api_key in providers.items():
        result = await verify_provider(provider, api_key)
        results.append(result)
        
        status_icon = "✅" if result["status"] == "success" else "❌" if result["status"] == "failed" else "⚠️"
        print(f"  {status_icon} {provider.upper()}: {result['message']}")
        
        if result["status"] == "success":
            print(f"     - Embedding 维度: {result['embedding_dim']}")
        
        print()
    
    # 3. 总结
    print("-" * 80 + "\n")
    
    configured_count = sum(1 for r in results if r["status"] != "not_configured")
    working_count = sum(1 for r in results if r["status"] == "success")
    
    print(f"📊 总结:")
    print(f"  - 已配置: {configured_count}/{len(providers)}")
    print(f"  - 可用: {working_count}/{len(providers)}")
    
    if working_count >= 2:
        print("\n✅ 配置正常,可以运行实验!")
        print("\n下一步: python scripts/embedding_comparison/01_prepare_annotation_dataset.py")
    elif working_count == 1:
        print("\n⚠️  只有 1 个模型可用,建议配置至少 2 个模型进行对比")
        print("\n配置方法:")
        for provider, api_key in providers.items():
            if not api_key:
                if provider == "openai":
                    print(f"  - OpenAI: https://platform.openai.com/api-keys")
                elif provider == "glm":
                    print(f"  - GLM (智谱): https://bigmodel.cn/")
                elif provider == "qwen":
                    print(f"  - Qwen (阿里云): https://dashscope.console.aliyun.com/")
    else:
        print("\n❌ 没有可用的模型,请检查配置")
        print("\n配置方法: 编辑 server/backend/.env,添加以下配置:")
        print("  OPENAI_API_KEY=sk-xxx")
        print("  GLM_API_KEY=your-glm-key")
        print("  DASHSCOPE_API_KEY=your-dashscope-key")


if __name__ == "__main__":
    asyncio.run(main())
