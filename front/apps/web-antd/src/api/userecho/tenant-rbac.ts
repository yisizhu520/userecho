/**
 * 租户角色与成员管理 API
 */

import { requestClient } from '#/api/request';

/** 租户角色 */
export interface TenantRole {
    id: string;
    tenant_id: string;
    name: string;
    code: string;
    description: string | null;
    is_builtin: boolean;
    sort: number;
    status: string;
}

/** 租户权限 */
export interface TenantPermission {
    id: string;
    parent_id: string | null;
    name: string;
    code: string;
    type: string;
    sort: number;
}

/** 租户成员 */
export interface TenantMember {
    id: string;
    tenant_id: string;
    user_id: number;
    user_type: string;
    status: string;
    feedback_count: number;
    // 前端补充字段
    username?: string;
    nickname?: string;
    email?: string;
    roles?: TenantRole[];
}

/** 创建角色参数 */
export interface CreateRoleParams {
    name: string;
    code: string;
    description?: string;
    permission_ids?: string[];
}

/** 更新角色参数 */
export interface UpdateRoleParams {
    name?: string;
    description?: string;
    status?: string;
}

/** 创建成员参数 */
export interface CreateMemberParams {
    username: string;
    nickname: string;
    password: string;
    email?: string;
    role_ids?: string[];
}

/** 更新成员参数 */
export interface UpdateMemberParams {
    user_type?: string;
    status?: string;
}

// ==================== 角色 API ====================

/** 获取角色列表 */
export async function getTenantRoles(status?: string) {
    return requestClient.get<TenantRole[]>('/api/v1/app/tenant/roles', {
        params: { status },
    });
}

/** 获取权限列表 */
export async function getTenantPermissions() {
    return requestClient.get<TenantPermission[]>('/api/v1/app/tenant/roles/permissions');
}

/** 获取角色详情 */
export async function getTenantRole(roleId: string) {
    return requestClient.get<TenantRole>(`/api/v1/app/tenant/roles/${roleId}`);
}

/** 获取角色权限 */
export async function getTenantRolePermissions(roleId: string) {
    return requestClient.get<TenantPermission[]>(`/api/v1/app/tenant/roles/${roleId}/permissions`);
}

/** 创建角色 */
export async function createTenantRole(data: CreateRoleParams) {
    return requestClient.post<TenantRole>('/api/v1/app/tenant/roles', data);
}

/** 更新角色 */
export async function updateTenantRole(roleId: string, data: UpdateRoleParams) {
    return requestClient.put<TenantRole>(`/api/v1/app/tenant/roles/${roleId}`, data);
}

/** 更新角色权限 */
export async function updateTenantRolePermissions(roleId: string, permissionIds: string[]) {
    return requestClient.put(`/api/v1/app/tenant/roles/${roleId}/permissions`, {
        permission_ids: permissionIds,
    });
}

/** 删除角色 */
export async function deleteTenantRole(roleId: string) {
    return requestClient.delete(`/api/v1/app/tenant/roles/${roleId}`);
}

// ==================== 成员 API ====================

/** 获取成员列表 */
export async function getTenantMembers(status?: string) {
    return requestClient.get<TenantMember[]>('/api/v1/app/tenant/members', {
        params: { status },
    });
}

/** 获取我的权限 */
export async function getMyPermissions() {
    return requestClient.get<string[]>('/api/v1/app/tenant/members/my-permissions');
}

/** 获取成员详情 */
export async function getTenantMember(memberId: string) {
    return requestClient.get<TenantMember>(`/api/v1/app/tenant/members/${memberId}`);
}

/** 获取成员角色 */
export async function getTenantMemberRoles(memberId: string) {
    return requestClient.get<string[]>(`/api/v1/app/tenant/members/${memberId}/roles`);
}

/** 创建成员 */
export async function createTenantMember(data: CreateMemberParams) {
    return requestClient.post<TenantMember>('/api/v1/app/tenant/members', data);
}

/** 更新成员 */
export async function updateTenantMember(memberId: string, data: UpdateMemberParams) {
    return requestClient.put<TenantMember>(`/api/v1/app/tenant/members/${memberId}`, data);
}

/** 更新成员角色 */
export async function updateTenantMemberRoles(memberId: string, roleIds: string[]) {
    return requestClient.put(`/api/v1/app/tenant/members/${memberId}/roles`, {
        role_ids: roleIds,
    });
}

/** 删除成员 */
export async function deleteTenantMember(memberId: string) {
    return requestClient.delete(`/api/v1/app/tenant/members/${memberId}`);
}
