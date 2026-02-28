/**
 * Board API
 */

import { requestClient } from '#/api/request';

/** Board 基础信息 */
export interface Board {
    id: string;
    tenant_id: string;
    name: string;
    url_name: string;
    description?: string;
    category?: string;
    feedback_count: number;
    topic_count: number;
    sort_order: number;
    is_archived: boolean;
    created_time: string;
}

/** Board 列表响应 */
export interface BoardListResponse {
    boards: Board[];
    total: number;
}

/** 创建看板 */
export interface BoardCreate {
    name: string;
    url_name: string;
    description?: string;
    category?: string;
    sort_order?: number;
}

/** 更新看板 */
export interface BoardUpdate {
    name?: string;
    description?: string;
    category?: string;
    sort_order?: number;
    is_archived?: boolean;
}

/**
 * 获取看板列表
 */
export async function getBoardList(): Promise<Board[]> {
    const response = await requestClient.get<BoardListResponse>('/api/v1/app/boards');
    return response.boards || [];
}

/**
 * 创建看板
 */
export async function createBoard(data: BoardCreate): Promise<Board> {
    return await requestClient.post<Board>('/api/v1/app/boards', data);
}

/**
 * 更新看板
 */
export async function updateBoard(id: string, data: BoardUpdate): Promise<Board> {
    return await requestClient.put<Board>(`/api/v1/app/boards/${id}`, data);
}

/**
 * 删除看板（软删除）
 */
export async function deleteBoard(id: string): Promise<void> {
    await requestClient.delete(`/api/v1/app/boards/${id}`);
}

/** 批量更新看板排序项 */
export interface BoardReorderItem {
    id: string;
    sort_order: number;
}

/**
 * 批量更新看板排序（拖拽排序）
 */
export async function reorderBoards(boards: BoardReorderItem[]): Promise<void> {
    await requestClient.patch('/api/v1/app/boards/reorder', { boards });
}

/**
 * Board API 命名空间（用于兼容旧代码）
 */
export const BoardApi = {
    getBoardList,
    createBoard,
    updateBoard,
    deleteBoard,
};
