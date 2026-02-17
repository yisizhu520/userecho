"""Board CRUD"""

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.board import Board


class CRUDBoard(TenantAwareCRUD[Board]):
    """看板 CRUD"""

    pass


crud_board = CRUDBoard(Board)
