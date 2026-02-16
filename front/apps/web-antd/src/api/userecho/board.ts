/**
 * Board API
 */

import { requestClient } from '#/api/request';

export namespace BoardApi {
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
}

/**
 * 获取看板列表
 */
export async function getBoardList() {
    return requestClient.get<BoardApi.BoardListResponse>('/app/boards');
}
