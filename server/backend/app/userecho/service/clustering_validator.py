"""聚类验证服务

使用 LLM 验证聚类的语义一致性
"""

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.app.userecho.model.feedback import Feedback
from backend.common.log import log
from backend.utils.ai_client import ai_client


class SubCluster(BaseModel):
    """子聚类信息"""
    
    theme: str = Field(..., description="主题名称")
    feedback_indices: list[int] = Field(..., description="反馈索引列表（从1开始）")
    description: str = Field("", description="主题描述")


class ClusterValidationResult(BaseModel):
    """聚类验证结果"""
    
    is_valid: bool = Field(..., description="聚类是否有效")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 0.0-1.0")
    common_theme: str | None = Field(None, description="共同主题")
    reason: str = Field(..., description="验证理由")
    suggested_action: str = Field(..., description="建议操作: keep | split | review")
    sub_clusters: list[SubCluster] | None = Field(None, description="如果需要拆分，建议的子聚类")


class ClusteringValidator:
    """聚类验证器"""
    
    async def validate_cluster_with_llm(
        self,
        cluster_feedbacks: list[Feedback],
    ) -> ClusterValidationResult:
        """
        使用 LLM 验证聚类的语义一致性
        
        Args:
            cluster_feedbacks: 聚类中的反馈列表
        
        Returns:
            验证结果
        """
        try:
            # 1. 构建验证 prompt
            feedbacks_text = "\n".join([
                f"{i+1}. {f.content}"
                for i, f in enumerate(cluster_feedbacks)
            ])
            
            prompt = f"""
你是一个产品经理，需要判断以下用户反馈是否在讨论同一个需求或主题。

**反馈列表**：
{feedbacks_text}

**判断标准**：
- 是：如果它们讨论的是同一个功能、同一个问题、或者是同一需求的细化
- 否：如果它们讨论的是不同功能、不同问题、或者主题不一致

**回答格式（JSON）**：
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "common_theme": "如果是，用一句话概括共同主题",
    "reason": "判断理由",
    "suggested_action": "keep/split/review",
    "sub_clusters": [
        {{
            "theme": "主题名称",
            "feedback_indices": [1, 2, 3],
            "description": "主题描述"
        }}
    ]  // 仅当 suggested_action=split 时提供，按主题分组反馈索引
}}

**示例 1（主题一致）**：
输入：
1. 希望能导出反馈数据为 Excel
2. 能否支持导出为 CSV 格式？
3. 可以批量导出所有反馈吗？

输出：
{{
    "is_valid": true,
    "confidence": 0.95,
    "common_theme": "数据导出功能",
    "reason": "三条反馈都在讨论导出功能，只是格式和范围有差异",
    "suggested_action": "keep",
    "sub_clusters": null
}}

**示例 2（需要拆分）**：
输入：
1. 希望能导出反馈数据为 Excel
2. 新反馈提交时希望能发送邮件通知
3. 能否支持导出为 CSV 格式？
4. 可以加个邮件提醒功能吗？

输出：
{{
    "is_valid": false,
    "confidence": 0.90,
    "common_theme": null,
    "reason": "包含两个独立主题：数据导出（1、3）和邮件通知（2、4）",
    "suggested_action": "split",
    "sub_clusters": [
        {{
            "theme": "数据导出功能",
            "feedback_indices": [1, 3],
            "description": "用户希望导出反馈数据"
        }},
        {{
            "theme": "邮件通知",
            "feedback_indices": [2, 4],
            "description": "用户希望通过邮件接收反馈通知"
        }}
    ]
}}

现在请分析上述反馈：
"""
            
            # 2. 调用 LLM
            response = await ai_client.chat(
                prompt=prompt,
                response_format="json",
                max_tokens=1000,  # 增加 token 数以支持返回子聚类
                temperature=0.3,
            )
            
            # 3. 解析结果
            result_data = json.loads(response)
            result = ClusterValidationResult(**result_data)
            
            log.info(
                f"LLM validation completed: is_valid={result.is_valid}, "
                f"confidence={result.confidence:.2f}, theme={result.common_theme}, "
                f"sub_clusters={len(result.sub_clusters or [])}"
            )
            
            return result
        
        except Exception as e:
            log.error(f"Failed to validate cluster with LLM: {e}")
            # 验证失败时返回低置信度的结果
            return ClusterValidationResult(
                is_valid=False,
                confidence=0.0,
                common_theme=None,
                reason=f"验证失败: {str(e)}",
                suggested_action="review",
                sub_clusters=None
            )
    
    async def refine_clusters_with_llm(
        self,
        initial_clusters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        用 LLM 优化初步聚类结果
        
        Args:
            initial_clusters: 初步聚类结果，每个聚类包含 'feedbacks' 列表
        
        Returns:
            优化后的聚类结果:
            {
                'validated': [...],  # 验证通过的聚类
                'uncertain': [...],  # 置信度低的聚类
                'to_recluster': [...],  # 需要重新聚类的反馈
            }
        """
        validated_clusters = []
        uncertain_clusters = []
        split_feedbacks = []
        
        for cluster in initial_clusters:
            feedbacks = cluster['feedbacks']
            
            # 只验证大聚类（5条以上）或多样性高的聚类
            if len(feedbacks) >= 5:
                validation = await self.validate_cluster_with_llm(feedbacks)
                
                if validation.is_valid and validation.confidence >= 0.8:
                    # 高置信度，保留
                    cluster['validation'] = validation.model_dump()
                    validated_clusters.append(cluster)
                    
                elif validation.suggested_action == 'split':
                    # 需要拆分，返回单独处理
                    split_feedbacks.extend(feedbacks)
                    
                else:
                    # 置信度低，标记为待人工复核
                    cluster['validation'] = validation.model_dump()
                    uncertain_clusters.append(cluster)
            else:
                # 小聚类，直接保留（小聚类相似度高，通常不会误判）
                validated_clusters.append(cluster)
        
        log.info(
            f"LLM refinement completed: validated={len(validated_clusters)}, "
            f"uncertain={len(uncertain_clusters)}, to_recluster={len(split_feedbacks)}"
        )
        
        return {
            'validated': validated_clusters,
            'uncertain': uncertain_clusters,
            'to_recluster': split_feedbacks,
        }


# 全局单例
clustering_validator = ClusteringValidator()
