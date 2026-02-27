"""Board API 端点"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from backend.app.userecho.crud.crud_board import crud_board
from backend.app.userecho.model.board import Board
from backend.app.userecho.schema.board import BoardCreate, BoardListOut, BoardOut, BoardUpdate
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession, uuid4_str
from backend.utils.timezone import timezone

router = APIRouter(prefix="/boards", tags=["UserEcho - 看板"])


@router.get("", summary="获取看板列表")
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
        .where(Board.is_archived == False)  # noqa: E712
        .order_by(Board.sort_order, Board.created_time.desc())
    )
    result = await db.execute(stmt)
    boards = result.scalars().all()

    return response_base.success(data=BoardListOut(boards=boards, total=len(boards)))


@router.post("", summary="创建看板")
async def create_board_management(
    create_data: BoardCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
) -> ResponseSchemaModel[BoardOut]:
    """
    创建新看板

    检查 url_name 唯一性，创建看板记录
    """
    # 检查 url_name 是否已存在
    existing = await crud_board.get_by_url_name(db, tenant_id, create_data.url_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL slug '{create_data.url_name}' 已被使用",
        )

    # 创建看板
    board = Board(
        id=uuid4_str(),
        tenant_id=tenant_id,
        name=create_data.name,
        url_name=create_data.url_name,
        description=create_data.description,
        category=create_data.category,
        sort_order=create_data.sort_order,
        created_time=timezone.now(),
    )
    db.add(board)
    await db.flush()

    return response_base.success(data=BoardOut.model_validate(board))


@router.put("/{board_id}", summary="更新看板")
async def update_board_management(
    board_id: str,
    update_data: BoardUpdate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
) -> ResponseSchemaModel[BoardOut]:
    """
    更新看板信息

    支持更新名称、描述、分类、排序和归档状态
    """
    # 获取看板
    stmt = select(Board).where(
        Board.id == board_id,
        Board.tenant_id == tenant_id,
        Board.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在",
        )

    # 更新字段
    if update_data.name is not None:
        board.name = update_data.name
    if update_data.description is not None:
        board.description = update_data.description
    if update_data.category is not None:
        board.category = update_data.category
    if update_data.sort_order is not None:
        board.sort_order = update_data.sort_order
    if update_data.is_archived is not None:
        board.is_archived = update_data.is_archived

    board.updated_time = timezone.now()
    await db.flush()

    return response_base.success(data=BoardOut.model_validate(board))


@router.delete("/{board_id}", summary="删除看板（软删除）")
async def delete_board_management(
    board_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
) -> ResponseSchemaModel[None]:
    """
    软删除看板

    设置 deleted_at 字段，不物理删除数据
    """
    success = await crud_board.soft_delete(db, board_id, tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在",
        )

    await db.flush()
    return response_base.success()
