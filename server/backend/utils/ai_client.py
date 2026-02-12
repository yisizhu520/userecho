"""AI 客户端封装

支持多个 AI 提供商：DeepSeek, OpenAI, GLM (智谱), Volcengine (火山引擎/豆包)
提供 embedding、摘要生成、主题提取等功能
"""

import json
from typing import Any

from openai import AsyncOpenAI

from backend.common.log import log
from backend.core.conf import settings


class AIClient:
    """AI 客户端 - 支持多模型降级
    
    通过配置驱动的方式支持多个 AI 提供商，避免硬编码的 if-elif 链。
    """

    # Provider 配置：统一管理所有提供商的参数
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
            'embedding_model': None,  # 火山引擎使用 endpoint ID，从环境变量读取
            'chat_model': None,
            'env_key': 'VOLCENGINE_API_KEY',
        },
    }

    def __init__(self):
        """初始化 AI 客户端 - 配置驱动，零硬编码"""
        self.clients = {}
        self.current_provider = settings.AI_DEFAULT_PROVIDER

        # 统一初始化所有配置的 provider
        for provider_name, config in self.PROVIDERS_CONFIG.items():
            api_key = getattr(settings, config['env_key'], None)
            if api_key:
                try:
                    client_kwargs = {'api_key': api_key, 'timeout': 60.0}
                    
                    # 只在 base_url 非空时设置
                    if config['base_url']:
                        client_kwargs['base_url'] = config['base_url']
                    
                    self.clients[provider_name] = AsyncOpenAI(**client_kwargs)
                    log.info(f'{provider_name.upper()} AI client initialized')
                except Exception as e:
                    log.warning(f'Failed to initialize {provider_name} client: {e}')

        if not self.clients:
            log.warning('No AI clients initialized. AI features will be disabled.')
        
        # 如果默认 provider 不可用，自动切换到第一个可用的
        if self.current_provider not in self.clients and self.clients:
            self.current_provider = next(iter(self.clients))
            log.info(f'Default provider unavailable, switched to {self.current_provider}')

    async def get_embedding(self, text: str, max_retries: int = 2) -> list[float] | None:
        """
        获取文本 embedding 向量

        Args:
            text: 输入文本
            max_retries: 最大重试次数

        Returns:
            embedding 向量 (768维) 或 None
        """
        if not text or not text.strip():
            return None

        # 截断超长文本
        text = text[:2000]

        for attempt in range(max_retries):
            # 确保当前 provider 可用
            if self.current_provider not in self.clients:
                break
            
            try:
                config = self.PROVIDERS_CONFIG[self.current_provider]
                
                # 获取 embedding model
                embedding_model = config['embedding_model']
                
                # 火山引擎特殊处理：从环境变量读取 endpoint ID
                if self.current_provider == 'volcengine':
                    embedding_model = getattr(settings, 'VOLCENGINE_EMBEDDING_ENDPOINT', None)
                    if not embedding_model:
                        log.warning('VOLCENGINE_EMBEDDING_ENDPOINT not configured')
                        self._fallback_to_next_provider()
                        continue
                
                # 如果当前 provider 不支持 embedding，跳到下一个
                # 注意：需要在火山引擎处理之后检查，因为火山引擎的 model 从环境变量读取
                if embedding_model is None:
                    log.info(f'{self.current_provider} does not support embedding, trying next provider')
                    self._fallback_to_next_provider()
                    continue
                
                response = await self.clients[self.current_provider].embeddings.create(
                    model=embedding_model,
                    input=text
                )
                return response.data[0].embedding

            except Exception as e:
                log.warning(f'AI embedding failed (attempt {attempt + 1}/{max_retries}): {e}')

                # 尝试降级到其他可用的 provider
                self._fallback_to_next_provider()

        log.error(f'Failed to get embedding after {max_retries} retries')
        return None
    
    def _fallback_to_next_provider(self):
        """降级到下一个可用的 provider"""
        available_providers = list(self.clients.keys())
        if not available_providers:
            return
        
        try:
            current_idx = available_providers.index(self.current_provider)
            # 切换到下一个（循环）
            next_idx = (current_idx + 1) % len(available_providers)
            next_provider = available_providers[next_idx]
            
            if next_provider != self.current_provider:
                log.info(f'Falling back from {self.current_provider} to {next_provider}')
                self.current_provider = next_provider
        except ValueError:
            # 当前 provider 不在可用列表中，切换到第一个
            self.current_provider = available_providers[0]
            log.info(f'Switched to {self.current_provider}')

    async def generate_topic_title(
        self,
        feedbacks: list[str],
        max_feedbacks: int = 10
    ) -> dict[str, Any]:
        """
        根据反馈列表生成需求主题

        Args:
            feedbacks: 反馈内容列表
            max_feedbacks: 最多分析的反馈数量

        Returns:
            包含 title, category, is_urgent 的字典
        """
        if not feedbacks:
            return {'title': '未分类主题', 'category': 'other', 'is_urgent': False}

        # 只取前 N 条反馈
        sample_feedbacks = feedbacks[:max_feedbacks]

        prompt = f"""你是一个产品经理助手，请分析以下用户反馈，提取核心需求主题。

用户反馈内容：
{chr(10).join(f'{i+1}. {f[:200]}' for i, f in enumerate(sample_feedbacks))}

要求：
1. 生成一个15字以内的主题标题（中文）
2. 判断类别：bug（缺陷）/improvement（体验优化）/feature（新功能）/performance（性能问题）/other（其他）
3. 判断是否紧急（包含"崩溃"、"无法使用"、"严重"等词）

返回 JSON 格式：
{{"title": "标题", "category": "分类", "is_urgent": true/false}}
"""

        try:
            if self.current_provider in self.clients:
                config = self.PROVIDERS_CONFIG[self.current_provider]
                
                # 获取 chat model
                chat_model = config['chat_model']
                
                # 火山引擎特殊处理
                if self.current_provider == 'volcengine':
                    chat_model = getattr(settings, 'VOLCENGINE_CHAT_ENDPOINT', None)
                    if not chat_model:
                        raise ValueError('VOLCENGINE_CHAT_ENDPOINT not configured')
                
                response = await self.clients[self.current_provider].chat.completions.create(
                    model=chat_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    response_format={'type': 'json_object'},
                    max_tokens=200,
                    temperature=0.7
                )

                result = json.loads(response.choices[0].message.content)
                return {
                    'title': result.get('title', '未分类主题')[:50],
                    'category': result.get('category', 'other'),
                    'is_urgent': result.get('is_urgent', False)
                }

        except Exception as e:
            log.error(f'Failed to generate topic title: {e}')

        # 降级方案：使用简单规则
        return {
            'title': f'用户反馈主题 ({len(feedbacks)}条)',
            'category': 'other',
            'is_urgent': any(word in ' '.join(feedbacks) for word in ['崩溃', '无法使用', '严重', '紧急'])
        }

    async def generate_summary(self, content: str, max_length: int = 20) -> str:
        """
        生成简短摘要

        Args:
            content: 原始内容
            max_length: 最大长度

        Returns:
            摘要文本
        """
        if not content:
            return ''

        # 如果已经很短，直接返回
        if len(content) <= max_length + 5:
            return content[:max_length]

        prompt = f"将以下反馈概括为{max_length}字以内的摘要（中文）：\n{content[:500]}"

        try:
            if self.current_provider in self.clients:
                config = self.PROVIDERS_CONFIG[self.current_provider]
                
                # 获取 chat model
                chat_model = config['chat_model']
                
                # 火山引擎特殊处理
                if self.current_provider == 'volcengine':
                    chat_model = getattr(settings, 'VOLCENGINE_CHAT_ENDPOINT', None)
                    if not chat_model:
                        raise ValueError('VOLCENGINE_CHAT_ENDPOINT not configured')
                
                response = await self.clients[self.current_provider].chat.completions.create(
                    model=chat_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=50,
                    temperature=0.5
                )
                return response.choices[0].message.content.strip()[:max_length]

        except Exception as e:
            log.warning(f'Failed to generate summary: {e}')

        # 降级方案：简单截断
        return content[:max_length] + ('...' if len(content) > max_length else '')


# 全局单例
ai_client = AIClient()
