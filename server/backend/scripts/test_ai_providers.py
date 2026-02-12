#!/usr/bin/env python3
"""AI Provider 配置测试脚本

用于验证 AI 提供商配置是否正确。
这是一个独立脚本，不依赖 backend 框架，只需要 openai 和 python-dotenv 两个包。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from openai import AsyncOpenAI
except ImportError:
    print("❌ 错误：缺少 openai 包，请运行：pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ 错误：缺少 python-dotenv 包，请运行：pip install python-dotenv")
    sys.exit(1)


# Provider 配置：与 ai_client.py 保持一致
PROVIDERS_CONFIG = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com',
        'embedding_model': None,  # DeepSeek 不提供 embedding API
        'chat_model': 'deepseek-chat',
        'env_key': 'DEEPSEEK_API_KEY',
    },
    'openai': {
        'base_url': None,  # 使用默认 OpenAI base_url
        'embedding_model': 'text-embedding-3-small',
        'chat_model': 'gpt-3.5-turbo',
        'env_key': 'OPENAI_API_KEY',
    },
    'glm': {
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
        'embedding_model': 'embedding-3',
        'chat_model': 'glm-4-flash',
        'env_key': 'GLM_API_KEY',
    },
    'volcengine': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'embedding_model': None,  # 从环境变量读取
        'chat_model': None,
        'env_key': 'VOLCENGINE_API_KEY',
    },
}


class SimpleAIClient:
    """简化版 AI 客户端 - 仅用于测试"""

    def __init__(self):
        """初始化 AI 客户端"""
        self.clients = {}
        self.current_provider = os.getenv('AI_DEFAULT_PROVIDER', 'deepseek')

        # 统一初始化所有配置的 provider
        for provider_name, config in PROVIDERS_CONFIG.items():
            api_key = os.getenv(config['env_key'])
            if api_key:
                try:
                    client_kwargs = {'api_key': api_key, 'timeout': 60.0}
                    
                    if config['base_url']:
                        client_kwargs['base_url'] = config['base_url']
                    
                    self.clients[provider_name] = AsyncOpenAI(**client_kwargs)
                    print(f"✓ {provider_name.upper()} 客户端初始化成功")
                except Exception as e:
                    print(f"✗ {provider_name} 初始化失败: {e}")

        # 如果默认 provider 不可用，切换到第一个可用的
        if self.current_provider not in self.clients and self.clients:
            self.current_provider = next(iter(self.clients))
            print(f"ℹ 默认 provider 不可用，切换到 {self.current_provider}")

    async def test_embedding(self, text: str):
        """测试 embedding 功能"""
        if self.current_provider not in self.clients:
            return None
        
        try:
            config = PROVIDERS_CONFIG[self.current_provider]
            embedding_model = config['embedding_model']
            
            # 火山引擎特殊处理：从环境变量读取 endpoint ID
            if self.current_provider == 'volcengine':
                embedding_model = os.getenv('VOLCENGINE_EMBEDDING_ENDPOINT')
                if not embedding_model:
                    print("⚠️  VOLCENGINE_EMBEDDING_ENDPOINT 未配置")
                    return None
            
            # 检查当前 provider 是否支持 embedding
            # 注意：需要在火山引擎处理之后检查
            if embedding_model is None:
                print(f"⚠️  {self.current_provider.upper()} 不支持 embedding API")
                return None
            
            response = await self.clients[self.current_provider].embeddings.create(
                model=embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Embedding 失败: {e}")
            return None

    async def test_chat(self, prompt: str):
        """测试 chat 功能"""
        if self.current_provider not in self.clients:
            return None
        
        try:
            config = PROVIDERS_CONFIG[self.current_provider]
            chat_model = config['chat_model']
            
            # 火山引擎特殊处理
            if self.current_provider == 'volcengine':
                chat_model = os.getenv('VOLCENGINE_CHAT_ENDPOINT')
                if not chat_model:
                    print("⚠️  VOLCENGINE_CHAT_ENDPOINT 未配置")
                    return None
            
            response = await self.clients[self.current_provider].chat.completions.create(
                model=chat_model,
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Chat 失败: {e}")
            return None


async def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("AI Provider 配置测试")
    print("=" * 60)
    print()
    
    # 初始化客户端
    client = SimpleAIClient()
    
    if not client.clients:
        print("❌ 错误：没有配置任何 AI 提供商！")
        print()
        print("请在 .env 文件中配置至少一个提供商的 API Key：")
        print("  DEEPSEEK_API_KEY=sk-your-key")
        print("  或")
        print("  OPENAI_API_KEY=sk-your-key")
        print()
        return False
    
    print(f"✅ 已初始化的提供商: {list(client.clients.keys())}")
    print(f"📌 当前默认提供商: {client.current_provider}")
    print()
    
    # 测试 1: Embedding
    print("=" * 60)
    print("测试 1: Embedding 功能")
    print("=" * 60)
    
    test_text = "这是一个测试文本，用于验证 embedding 功能。"
    print(f"测试文本: {test_text}")
    
    embedding = await client.test_embedding(test_text)
    
    if embedding:
        print(f"✅ Embedding 成功")
        print(f"   - 使用提供商: {client.current_provider}")
        print(f"   - 向量维度: {len(embedding)}")
        print(f"   - 前5个值: {embedding[:5]}")
    else:
        print("❌ Embedding 失败")
        print()
        print("💡 提示：")
        print("   - DeepSeek 不支持 Embedding API")
        print("   - 如需 Embedding 功能，请配置以下任一提供商：")
        print("     • OpenAI: OPENAI_API_KEY=sk-xxx")
        print("     • GLM: GLM_API_KEY=xxx")
        print("     • Volcengine: VOLCENGINE_API_KEY=xxx")
        print()
        print("   推荐配置（DeepSeek + OpenAI 组合）：")
        print("     DEEPSEEK_API_KEY=sk-xxx  # Chat 用")
        print("     OPENAI_API_KEY=sk-xxx    # Embedding 用")
        return False
    
    print()
    
    # 测试 2: Chat/主题生成
    print("=" * 60)
    print("测试 2: Chat 功能（主题生成）")
    print("=" * 60)
    
    prompt = """你是一个产品经理助手，请分析以下用户反馈，提取核心需求主题。

用户反馈内容：
1. 应用经常崩溃，体验很差
2. 希望能支持暗色模式
3. 登录速度太慢了

要求：
1. 生成一个15字以内的主题标题（中文）
2. 判断类别：bug/improvement/feature/performance/other
3. 判断是否紧急

返回 JSON 格式：
{"title": "标题", "category": "分类", "is_urgent": true/false}
"""
    
    result = await client.test_chat(prompt)
    
    if result:
        print(f"✅ Chat 成功")
        print(f"   - 使用提供商: {client.current_provider}")
        print(f"   - 返回结果:")
        try:
            # 尝试解析 JSON
            parsed = json.loads(result)
            for key, value in parsed.items():
                print(f"     {key}: {value}")
        except:
            # 如果不是 JSON，直接打印
            print(f"     {result[:200]}")
    else:
        print("❌ Chat 失败")
        return False
    
    print()
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    # 加载 .env 文件
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    env_file = backend_dir / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ 已加载配置文件: {env_file}")
        print()
    else:
        print(f"⚠️  警告：找不到 .env 文件: {env_file}")
        print("将尝试从系统环境变量读取配置")
        print()
    
    # 运行测试
    try:
        success = asyncio.run(run_tests())
        if success:
            print()
            print("🎉 所有测试完成！AI Provider 配置正确。")
            sys.exit(0)
        else:
            print()
            print("❌ 测试失败，请检查配置！")
            sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print()
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
