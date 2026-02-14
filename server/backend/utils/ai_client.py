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
        获取文本 embedding 向量（单条）

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

    async def get_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 50,
        max_retries: int = 2
    ) -> list[list[float] | None]:
        """
        批量获取文本 embedding 向量

        所有 AI 提供商（OpenAI, GLM, Volcengine）都支持批量 embedding API。
        参考：https://www.volcengine.com/docs/82379/1521766

        Args:
            texts: 输入文本列表
            batch_size: 单次请求的批量大小（默认 50，避免请求过大）
            max_retries: 最大重试次数

        Returns:
            embedding 向量列表，失败的返回 None
        """
        if not texts:
            return []

        # 过滤和截断文本
        processed_texts = []
        for text in texts:
            if text and text.strip():
                processed_texts.append(text[:2000])  # 截断超长文本
            else:
                processed_texts.append('')  # 空文本用空字符串占位

        results: list[list[float] | None] = []

        # 分批处理
        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]
            batch_results = await self._get_embeddings_batch_single(batch, max_retries)
            results.extend(batch_results)

        return results

    async def _get_embeddings_batch_single(
        self,
        texts: list[str],
        max_retries: int = 2
    ) -> list[list[float] | None]:
        """
        单次批量获取 embedding（内部方法）

        Args:
            texts: 输入文本列表
            max_retries: 最大重试次数

        Returns:
            embedding 向量列表
        """
        # 过滤空文本，记录索引
        non_empty_texts = []
        non_empty_indices = []
        for idx, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                non_empty_indices.append(idx)

        # 如果全是空文本，直接返回 None 列表
        if not non_empty_texts:
            return [None] * len(texts)

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
                if embedding_model is None:
                    log.info(f'{self.current_provider} does not support embedding, trying next provider')
                    self._fallback_to_next_provider()
                    continue

                # 批量调用 embedding API
                # 所有 provider（OpenAI, GLM, Volcengine）都支持 input 为数组
                response = await self.clients[self.current_provider].embeddings.create(
                    model=embedding_model,
                    input=non_empty_texts  # 批量输入
                )

                # 提取 embedding 向量
                embeddings_map = {idx: item.embedding for idx, item in enumerate(response.data)}

                # 重建完整结果（包含空文本的 None）
                results = []
                embedding_idx = 0
                for original_idx in range(len(texts)):
                    if original_idx in non_empty_indices:
                        results.append(embeddings_map.get(embedding_idx))
                        embedding_idx += 1
                    else:
                        results.append(None)

                log.info(f'Batch embedding completed: {len(non_empty_texts)}/{len(texts)} texts, provider: {self.current_provider}')
                return results

            except Exception as e:
                log.warning(f'Batch embedding failed (attempt {attempt + 1}/{max_retries}): {e}')

                # 尝试降级到其他可用的 provider
                self._fallback_to_next_provider()

        log.error(f'Failed to get batch embeddings after {max_retries} retries')
        return [None] * len(texts)
    
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

    async def chat(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        response_format: str | None = None,
        max_retries: int = 2,
    ) -> str:
        """
        通用 Chat 接口
        
        Args:
            prompt: 用户输入提示词
            max_tokens: 最大返回 token 数
            temperature: 温度参数（0-1）
            response_format: 返回格式，'json' 表示 JSON 格式
            max_retries: 最大重试次数
        
        Returns:
            AI 生成的文本
        """
        if not prompt:
            return ''
        
        for attempt in range(max_retries):
            try:
                if self.current_provider not in self.clients:
                    self._fallback_to_next_provider()
                    continue
                
                config = self.PROVIDERS_CONFIG[self.current_provider]
                
                # 获取 chat model
                chat_model = config['chat_model']
                
                # 火山引擎特殊处理
                if self.current_provider == 'volcengine':
                    chat_model = getattr(settings, 'VOLCENGINE_CHAT_ENDPOINT', None)
                    if not chat_model:
                        log.warning('VOLCENGINE_CHAT_ENDPOINT not configured')
                        self._fallback_to_next_provider()
                        continue
                
                # 构建请求参数
                create_params = {
                    'model': chat_model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                }
                
                # 添加 response_format（如果需要）
                if response_format == 'json':
                    create_params['response_format'] = {'type': 'json_object'}
                
                response = await self.clients[self.current_provider].chat.completions.create(**create_params)
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                log.warning(f'Chat failed (attempt {attempt + 1}/{max_retries}, provider: {self.current_provider}): {e}')
                self._fallback_to_next_provider()
        
        # 所有重试都失败
        log.error(f'Failed to chat after {max_retries} retries')
        return ''

    async def analyze_screenshot(
        self,
        image_url: str,
        max_retries: int = 2
    ) -> dict[str, Any]:
        """
        分析截图，提取反馈信息
        
        Args:
            image_url: 截图 URL（需要公开可访问）
            max_retries: 最大重试次数
            
        Returns:
            包含 platform, user_name, content, feedback_type, sentiment, confidence 的字典
        """
        prompt = """你是一个专业的反馈分析助手。分析这张社交媒体截图，提取以下信息：

1. **平台类型** (platform)
   - 观察 UI 特征（气泡样式、导航栏、Logo）
   - 可能值：wechat | xiaohongshu | appstore | weibo | other

2. **用户昵称** (user_name)
   - 提取发表反馈的用户昵称
   - 如果无法识别，返回空字符串

3. **用户 ID** (user_id)
   - 如果截图中有用户 ID（如小红书的 @id），提取
   - 如果没有，返回空字符串

4. **反馈内容** (content)
   - 提取核心反馈内容
   - 去除寒暄语、表情符号
   - 保留关键信息（版本号、设备型号、错误描述）

5. **反馈类型** (feedback_type)
   - bug: 功能异常、闪退、卡顿
   - feature: 功能需求、建议
   - complaint: 投诉、差评
   - other: 其他

6. **情感倾向** (sentiment)
   - positive: 正面评价
   - neutral: 中性反馈
   - negative: 负面反馈

7. **识别置信度** (confidence)
   - 0.0-1.0 之间的浮点数
   - 基于 UI 特征的清晰度和文字识别准确度

返回 JSON 格式，不要包含任何其他文字。

示例：
{
  "platform": "wechat",
  "user_name": "小王",
  "user_id": "",
  "content": "产品闪退了，iOS 16.3，iPhone 14 Pro",
  "feedback_type": "bug",
  "sentiment": "negative",
  "confidence": 0.95
}"""

        for attempt in range(max_retries):
            # 确保当前 provider 可用
            if self.current_provider not in self.clients:
                break

            try:
                config = self.PROVIDERS_CONFIG[self.current_provider]
                
                # 获取 chat model (支持 vision 的模型)
                chat_model = config['chat_model']
                
                # 针对不同提供商使用不同的 vision 模型
                if self.current_provider == 'openai':
                    chat_model = 'gpt-4o'
                elif self.current_provider == 'deepseek':
                    chat_model = 'deepseek-chat'  # DeepSeek 支持图像
                elif self.current_provider == 'glm':
                    chat_model = 'glm-4v-flash'  # GLM-4V 支持图像
                elif self.current_provider == 'volcengine':
                    # 火山引擎使用 endpoint（优先 VISION，回退 CHAT）
                    chat_model = (
                        getattr(settings, 'VOLCENGINE_VISION_ENDPOINT', None) or
                        getattr(settings, 'VOLCENGINE_CHAT_ENDPOINT', None)
                    )
                    if not chat_model:
                        log.warning('VOLCENGINE_VISION_ENDPOINT or VOLCENGINE_CHAT_ENDPOINT not configured, falling back')
                        self._fallback_to_next_provider()
                        continue

                # 调用 vision API
                response = await self.clients[self.current_provider].chat.completions.create(
                    model=chat_model,
                    messages=[
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': prompt},
                                {'type': 'image_url', 'image_url': {'url': image_url}}
                            ]
                        }
                    ],
                    response_format={'type': 'json_object'},
                    max_tokens=500,
                    temperature=0.3
                )

                result = json.loads(response.choices[0].message.content)
                
                # 验证和规范化结果
                return {
                    'platform': result.get('platform', 'other'),
                    'user_name': result.get('user_name', ''),
                    'user_id': result.get('user_id', ''),
                    'content': result.get('content', ''),
                    'feedback_type': result.get('feedback_type', 'other'),
                    'sentiment': result.get('sentiment', 'neutral'),
                    'confidence': float(result.get('confidence', 0.5))
                }

            except Exception as e:
                log.warning(f'Screenshot analysis failed (attempt {attempt + 1}/{max_retries}, provider: {self.current_provider}): {e}')
                
                # 尝试降级到其他可用的 provider
                self._fallback_to_next_provider()

        # 所有重试都失败，返回降级结果
        log.error(f'Failed to analyze screenshot after {max_retries} retries')
        return {
            'platform': 'other',
            'user_name': '',
            'user_id': '',
            'content': '图像识别失败，请手动填写',
            'feedback_type': 'other',
            'sentiment': 'neutral',
            'confidence': 0.0
        }

    async def suggest_impact_scope_ai(
        self,
        feedbacks: list[str],
        customer_count: int,
        title: str,
        category: str,
        max_retries: int = 2,
    ) -> dict:
        """
        AI 完整分析影响范围（详情页点击「AI 重新分析」时调用）
        
        Args:
            feedbacks: 反馈内容列表
            customer_count: 涉及客户数量
            title: 主题标题
            category: 分类
            max_retries: 最大重试次数
        
        Returns:
            {
                "scope": 1/3/5/10,
                "confidence": 0.0-1.0,
                "reason": "原因"
            }
        """
        # 快速降级方案（基于规则）
        def fallback_result():
            if customer_count >= 10:
                return {'scope': 10, 'confidence': 0.6, 'reason': f'基于 {customer_count} 个客户的规则判断'}
            elif customer_count >= 5:
                return {'scope': 5, 'confidence': 0.6, 'reason': f'基于 {customer_count} 个客户的规则判断'}
            elif customer_count >= 2:
                return {'scope': 3, 'confidence': 0.6, 'reason': f'基于 {customer_count} 个客户的规则判断'}
            else:
                return {'scope': 1, 'confidence': 0.6, 'reason': '仅 1 个客户反馈'}
        
        # 关键词匹配增强
        keywords_high_impact = ['所有用户', '所有人', '每个人', '全部', 'all users', 'everyone']
        keywords_medium_impact = ['大部分', '很多人', '多个用户', 'most users', 'many users']
        keywords_low_impact = ['部分', '个别', '少数', 'some users', 'few users']
        
        title_lower = title.lower()
        feedback_text = ' '.join(feedbacks[:5]).lower()  # 前5条
        
        # 关键词快速判断
        if any(kw in title_lower or kw in feedback_text for kw in keywords_high_impact):
            return {'scope': 10, 'confidence': 0.8, 'reason': '检测到"所有用户"等关键词'}
        elif any(kw in title_lower or kw in feedback_text for kw in keywords_medium_impact):
            return {'scope': 5, 'confidence': 0.7, 'reason': '检测到"大部分用户"等关键词'}
        elif any(kw in title_lower or kw in feedback_text for kw in keywords_low_impact):
            return {'scope': 3, 'confidence': 0.7, 'reason': '检测到"部分用户"等关键词'}
        
        # 只对重要需求调用 AI（客户数量 >= 5）
        if customer_count < 5:
            log.debug(f'Customer count {customer_count} < 5, using fallback for impact_scope')
            return fallback_result()
        
        # AI 分析
        prompt = f"""分析用户反馈的影响范围：

标题：{title}
分类：{category}
反馈数量：{len(feedbacks)} 条
涉及客户：{customer_count} 个

反馈样本：
{chr(10).join(feedbacks[:5])}

请判断影响范围：
1 - 个别用户（1-2个客户，小范围问题）
3 - 部分用户（3-10个客户，局部影响）
5 - 大多数用户（10+个客户，广泛影响）
10 - 全部用户（核心功能崩溃或所有人都遇到）

返回 JSON 格式：
{{"scope": 1/3/5/10, "confidence": 0.8, "reason": "判断理由"}}"""

        for attempt in range(max_retries):
            try:
                response = await self._chat(
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.3,
                    max_tokens=200,
                )
                
                # 解析 JSON 响应
                result = self._parse_json_response(response)
                
                # 验证结果
                scope = result.get('scope', 3)
                if scope not in [1, 3, 5, 10]:
                    scope = 3  # 默认值
                
                return {
                    'scope': scope,
                    'confidence': float(result.get('confidence', 0.7)),
                    'reason': result.get('reason', 'AI 分析结果')
                }
            
            except Exception as e:
                log.warning(f'AI impact_scope analysis failed (attempt {attempt + 1}/{max_retries}): {e}')
                self._fallback_to_next_provider()
        
        # 所有重试失败，返回降级结果
        log.error('AI impact_scope analysis failed, using fallback')
        return fallback_result()

    async def suggest_dev_cost_ai(
        self,
        title: str,
        category: str,
        feedbacks: list[str],
        max_retries: int = 2,
    ) -> dict:
        """
        AI 建议开发成本（详情页点击「AI 重新分析」时调用）
        
        Args:
            title: 主题标题
            category: 分类
            feedbacks: 反馈内容列表（前5条样本）
            max_retries: 最大重试次数
        
        Returns:
            {
                "days": 1/3/5/10,
                "confidence": 0.0-1.0,
                "reason": "原因"
            }
        """
        # 快速降级方案（基于规则）
        def fallback_result():
            category_costs = {
                'bug': 1,
                'improvement': 1,
                'feature': 5,
                'performance': 3,
                'other': 3,
            }
            days = category_costs.get(category, 3)
            return {
                'days': days,
                'confidence': 0.5,
                'reason': f'基于分类 {category} 的经验值'
            }
        
        # 关键词匹配
        title_lower = title.lower()
        urgent_keywords = ['崩溃', '闪退', '无法', '不能', 'crash', 'bug']
        feature_keywords = ['新增', '增加', '添加', '支持', 'add', 'new']
        
        if any(kw in title_lower for kw in urgent_keywords):
            return {'days': 1, 'confidence': 0.7, 'reason': '检测到紧急问题关键词'}
        elif any(kw in title_lower for kw in feature_keywords):
            return {'days': 5, 'confidence': 0.6, 'reason': '检测到新功能关键词'}
        
        # AI 分析（可选，成本高）
        if len(feedbacks) >= 5:  # 只对重要需求调用 AI
            prompt = f"""估算开发成本（工作日）：

标题：{title}
分类：{category}

反馈样本：
{chr(10).join(feedbacks[:3])}

参考标准：
1 天 - 简单 Bug 修复、界面微调
3 天 - 中等功能、多处调整
5 天 - 新功能开发、前后端联动
10 天+ - 复杂架构调整、大功能

返回 JSON 格式：
{{"days": 1/3/5/10, "confidence": 0.7, "reason": "判断理由"}}"""

            for attempt in range(max_retries):
                try:
                    response = await self._chat(
                        messages=[{'role': 'user', 'content': prompt}],
                        temperature=0.3,
                        max_tokens=200,
                    )
                    
                    result = self._parse_json_response(response)
                    
                    # 验证结果
                    days = result.get('days', 3)
                    if days not in [1, 3, 5, 10]:
                        days = 3
                    
                    return {
                        'days': days,
                        'confidence': float(result.get('confidence', 0.6)),
                        'reason': result.get('reason', 'AI 分析结果')
                    }
                
                except Exception as e:
                    log.warning(f'AI dev_cost analysis failed (attempt {attempt + 1}/{max_retries}): {e}')
                    self._fallback_to_next_provider()
        
        # 降级结果
        return fallback_result()


# ============= Lazy Initialization Proxy =============
# "Never initialize expensive resources at module import time!" - Linus
#
# Problem: AIClient.__init__() creates AsyncOpenAI clients which may do:
#   - DNS resolution
#   - Network connections  
#   - Connection pool warmup
# This can take 60-120 seconds during module import!
#
# Solution: Use proxy pattern for lazy initialization
# - First access triggers initialization
# - Zero cost at import time
# - Fully compatible with existing code

class _AIClientLazyProxy:
    """Lazy initialization proxy for AIClient
    
    Delays expensive AI client initialization until first use.
    """
    
    def __init__(self):
        self._instance: AIClient | None = None
        self._initializing = False
    
    def _ensure_initialized(self) -> AIClient:
        """Initialize client on first access"""
        if self._instance is None and not self._initializing:
            self._initializing = True
            try:
                log.info('Initializing AI clients (lazy)...')
                self._instance = AIClient()
                log.info('AI clients initialized successfully')
            finally:
                self._initializing = False
        
        return self._instance
    
    def __getattr__(self, name):
        """Forward all attribute access to real AIClient instance"""
        instance = self._ensure_initialized()
        if instance is None:
            raise RuntimeError('AIClient initialization failed')
        return getattr(instance, name)
    
    def __bool__(self):
        """Support truthiness check"""
        instance = self._ensure_initialized()
        return instance is not None


# Global singleton (lazy initialized)
ai_client = _AIClientLazyProxy()
