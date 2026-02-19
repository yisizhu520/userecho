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
    is_archived: boolean;
    created_time: string;
}

/** Board 列表响应 */
export interface BoardListResponse {
    boards: Board[];
    total: number;
}

/**
 * 获取看板列表
 */
export async function getBoardList(): Promise<Board[]> {
    const response = await requestClient.get<BoardListResponse>('/api/v1/app/boards');
    return response.boards || [];
}
