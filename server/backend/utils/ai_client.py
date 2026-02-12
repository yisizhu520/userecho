"""AI 客户端封装

支持 DeepSeek 和 OpenAI，提供 embedding、摘要生成、主题提取等功能
"""

import json
from typing import Any

from openai import AsyncOpenAI

from backend.common.log import log
from backend.core.conf import settings


class AIClient:
    """AI 客户端 - 支持多模型降级"""

    def __init__(self):
        """初始化 AI 客户端"""
        self.clients = {}
        self.current_provider = settings.AI_DEFAULT_PROVIDER

        # 初始化 DeepSeek 客户端
        if settings.DEEPSEEK_API_KEY:
            try:
                self.clients['deepseek'] = AsyncOpenAI(
                    base_url='https://api.deepseek.com',
                    api_key=settings.DEEPSEEK_API_KEY,
                    timeout=60.0
                )
                log.info('DeepSeek AI client initialized')
            except Exception as e:
                log.warning(f'Failed to initialize DeepSeek client: {e}')

        # 初始化 OpenAI 客户端
        if settings.OPENAI_API_KEY:
            try:
                self.clients['openai'] = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=60.0
                )
                log.info('OpenAI client initialized')
            except Exception as e:
                log.warning(f'Failed to initialize OpenAI client: {e}')

        if not self.clients:
            log.warning('No AI clients initialized. AI features will be disabled.')

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
            try:
                if self.current_provider == 'deepseek' and 'deepseek' in self.clients:
                    response = await self.clients['deepseek'].embeddings.create(
                        model='deepseek-embedding',
                        input=text
                    )
                    return response.data[0].embedding

                elif self.current_provider == 'openai' and 'openai' in self.clients:
                    response = await self.clients['openai'].embeddings.create(
                        model='text-embedding-3-small',
                        input=text
                    )
                    return response.data[0].embedding

            except Exception as e:
                log.warning(f'AI embedding failed (attempt {attempt + 1}/{max_retries}): {e}')

                # 尝试降级到备用模型
                if self.current_provider == 'deepseek' and 'openai' in self.clients:
                    log.info('Falling back to OpenAI')
                    self.current_provider = 'openai'
                elif self.current_provider == 'openai' and 'deepseek' in self.clients:
                    log.info('Falling back to DeepSeek')
                    self.current_provider = 'deepseek'
                else:
                    break

        log.error(f'Failed to get embedding after {max_retries} retries')
        return None

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
                response = await self.clients[self.current_provider].chat.completions.create(
                    model='deepseek-chat' if self.current_provider == 'deepseek' else 'gpt-3.5-turbo',
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
                response = await self.clients[self.current_provider].chat.completions.create(
                    model='deepseek-chat' if self.current_provider == 'deepseek' else 'gpt-3.5-turbo',
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
