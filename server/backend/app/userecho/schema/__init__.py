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
from .priority import PriorityScoreCreate, PriorityScoreOut, PriorityScoreUpdate
from .status_history import StatusHistoryOut
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
    # Tenant
    'TenantCreate',
    'TenantUpdate',
    'TenantOut',
    # Tenant Config
    'TenantConfigCreate',
    'TenantConfigUpdate',
    'TenantConfigOut',
    # Customer
    'CustomerCreate',
    'CustomerUpdate',
    'CustomerOut',
    # Feedback
    'FeedbackCreate',
    'FeedbackUpdate',
    'FeedbackOut',
    'FeedbackImportRow',
    'FeedbackListParams',
    # Topic
    'TopicCreate',
    'TopicUpdate',
    'TopicOut',
    'TopicDetailOut',
    'TopicListParams',
    'TopicStatusUpdateParam',
    # Priority
    'PriorityScoreCreate',
    'PriorityScoreUpdate',
    'PriorityScoreOut',
    # Status History
    'StatusHistoryOut',
]
