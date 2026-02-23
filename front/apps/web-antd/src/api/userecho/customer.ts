/**
 * 客户管理 API
 */

import { requestClient } from '#/api/request';

/** 客户对象 */
export interface Customer {
  id: string;
  tenant_id: string;
  name: string;
  customer_type: string;
  business_value: number;
  created_time: string;
  updated_time: string;
  deleted_at?: string;
}

/** 创建客户参数 */
export interface CreateCustomerParams {
  name: string;
  customer_type?: string;
  business_value?: number;
}

/** 更新客户参数 */
export interface UpdateCustomerParams {
  name?: string;
  customer_type?: string;
  business_value?: number;
}

/** 客户列表查询参数 */
export interface CustomerListParams {
  skip?: number;
  limit?: number;
  search?: string;
  customer_type?: string;
}

/** 客户列表响应 */
export interface CustomerListResponse {
  items: Customer[];
  total: number;
}

/**
 * 获取客户列表
 */
export async function getCustomerList(params: CustomerListParams) {
  return requestClient.get<CustomerListResponse>('/api/v1/app/customers', { params });
}

/**
 * 搜索客户（模糊匹配）
 */
export async function searchCustomers(query: string, limit: number = 10) {
  return requestClient.get<Customer[]>('/api/v1/app/customers/search', { params: { query, limit } });
}

/**
 * 创建客户
 */
export async function createCustomer(data: CreateCustomerParams) {
  return requestClient.post<Customer>('/api/v1/app/customers', data);
}

/**
 * 更新客户
 */
export async function updateCustomer(id: string, data: UpdateCustomerParams) {
  return requestClient.put<Customer>(`/api/v1/app/customers/${id}`, data);
}

/**
 * 删除客户
 */
export async function deleteCustomer(id: string) {
  return requestClient.delete(`/api/v1/app/customers/${id}`);
}

/** 客户类型选项 */
export const CUSTOMER_TYPES = [
  { value: 'normal', label: '普通客户', business_value: 1, color: '#8c8c8c' },
  { value: 'paid', label: '付费客户', business_value: 3, color: '#1677ff' },
  { value: 'major', label: '大客户', business_value: 5, color: '#faad14' },
  { value: 'strategic', label: '战略客户', business_value: 10, color: '#722ed1' },
];

/** 商业价值等级配置 */
export const BUSINESS_VALUE_LEVELS = [
  { min: 1, max: 2, label: '低', color: '#8c8c8c', bgColor: 'rgba(140, 140, 140, 0.1)' },
  { min: 3, max: 4, label: '中', color: '#1677ff', bgColor: 'rgba(22, 119, 255, 0.1)' },
  { min: 5, max: 7, label: '高', color: '#faad14', bgColor: 'rgba(250, 173, 20, 0.1)' },
  { min: 8, max: 10, label: '核心', color: '#722ed1', bgColor: 'rgba(114, 46, 209, 0.15)' },
];
