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
    # Tenant Config
    'TenantConfigCreate',
    'TenantConfigOut',
    'TenantConfigUpdate',
    # Tenant
    'TenantCreate',
    'TenantOut',
    'TenantUpdate',
    # Topic
    'TopicCreate',
    'TopicDetailOut',
    'TopicListParams',
    'TopicOut',
    'TopicStatusUpdateParam',
    'TopicUpdate',
]
