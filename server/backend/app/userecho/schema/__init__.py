"""UserEcho Schema 模块

包含所有业务数据模型的 Pydantic Schema 定义
"""

from .customer import CustomerCreate, CustomerOut, CustomerUpdate
from .feedback import (
    FeedbackCreate,
    FeedbackImportRow,
    FeedbackListParams,
    FeedbackOut,
    FeedbackUpdate,
)

# 必须在 topic 之前导入 priority，因为 TopicDetailOut.model_rebuild() 需要 PriorityScoreOut
from .priority import PriorityScoreCreate, PriorityScoreOut, PriorityScoreUpdate
from .status_history import StatusHistoryOut
from .subscription import (
    SubscriptionCreateReq,
    SubscriptionHistorySchema,
    SubscriptionPlanSchema,
    SubscriptionUpdateReq,
    TenantSubscriptionSchema,
)
from .tenant import TenantCreate, TenantOut, TenantUpdate
from .tenant_config import TenantConfigCreate, TenantConfigOut, TenantConfigUpdate
from .topic import (
    TopicCreate,
    TopicDetailOut,
    TopicListParams,
    TopicOut,
    TopicStatusUpdateParam,
    TopicUpdate,
)

__all__ = [
    # Customer
    'CustomerCreate',
    'CustomerOut',
    'CustomerUpdate',
    # Feedback
    'FeedbackCreate',
    'FeedbackImportRow',
    'FeedbackListParams',
    'FeedbackOut',
    'FeedbackUpdate',
    # Priority
    'PriorityScoreCreate',
    'PriorityScoreOut',
    'PriorityScoreUpdate',
    # Status History
    'StatusHistoryOut',
    # Subscription
    'SubscriptionCreateReq',
    'SubscriptionHistorySchema',
    'SubscriptionPlanSchema',
    'SubscriptionUpdateReq',
    # Tenant Config
    'TenantConfigCreate',
    'TenantConfigOut',
    'TenantConfigUpdate',
    # Tenant
    'TenantCreate',
    'TenantOut',
    'TenantSubscriptionSchema',
    'TenantUpdate',
    # Topic
    'TopicCreate',
    'TopicDetailOut',
    'TopicListParams',
    'TopicOut',
    'TopicStatusUpdateParam',
    'TopicUpdate',
]

# ✅ 统一解析前向引用（此时 PriorityScoreOut、FeedbackOut、StatusHistoryOut 都已加载）
TopicOut.model_rebuild()
TopicDetailOut.model_rebuild()
