"""Board API 端点"""

from fastapi import APIRouter
from sqlalchemy import select

from backend.app.userecho.model.board import Board
from backend.app.userecho.schema.board import BoardListOut
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/boards', tags=['UserEcho - 看板'])


@router.get('', summary='获取看板列表')
async def get_boards(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
) -> ResponseSchemaModel[BoardListOut]:
    """
    获取当前租户的所有看板列表

    返回未归档的看板，按创建时间排序
    """
    # 查询当前租户的所有未归档看板
    stmt = (
        select(Board)
        .where(Board.tenant_id == tenant_id)
        .where(not Board.is_archived)
        .order_by(Board.sort_order, Board.created_time.desc())
    )
    result = await db.execute(stmt)
    boards = result.scalars().all()

    return response_base.success(data=BoardListOut(boards=boards, total=len(boards)))
