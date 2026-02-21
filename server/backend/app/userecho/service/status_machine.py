"""需求状态机

定义需求（Topic）的状态流转规则，确保状态变更的合法性。

状态流转规则（经用户确认）：
- pending → planned, ignored
- planned → pending, in_progress, ignored
- in_progress → planned, completed
- completed → (终态，不可变更)
- ignored → pending, planned
"""


class TopicStatusMachine:
    """需求状态机"""

    # 所有合法状态
    VALID_STATUSES = {'pending', 'planned', 'in_progress', 'completed', 'ignored'}

    # 状态流转规则：key 为当前状态，value 为允许流转的目标状态集合
    TRANSITIONS: dict[str, set[str]] = {
        'pending': {'planned', 'ignored'},
        'planned': {'pending', 'in_progress', 'ignored'},
        'in_progress': {'planned', 'completed'},
        'completed': set(),  # 终态，不可变更
        'ignored': {'pending', 'planned'},
    }

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """
        检查状态流转是否合法

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Returns:
            True 如果流转合法，False 否则
        """
        if from_status == to_status:
            return False
        if from_status not in cls.VALID_STATUSES or to_status not in cls.VALID_STATUSES:
            return False
        allowed = cls.TRANSITIONS.get(from_status, set())
        return to_status in allowed

    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> list[str]:
        """
        获取当前状态允许流转的目标状态列表

        Args:
            current_status: 当前状态

        Returns:
            允许的目标状态列表
        """
        return list(cls.TRANSITIONS.get(current_status, set()))

    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> None:
        """
        校验状态流转，非法时抛出异常

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Raises:
            ValueError: 状态流转非法时抛出
        """
        if not cls.can_transition(from_status, to_status):
            allowed = cls.get_allowed_transitions(from_status)
            if not allowed:
                raise ValueError(f'状态 {from_status} 为终态，不可变更')
            raise ValueError(
                f'非法状态流转: {from_status} → {to_status}。'
                f'允许的目标状态: {allowed}'
            )
