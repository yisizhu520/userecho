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
}

/**
 * 获取客户列表
 */
export async function getCustomerList(params: CustomerListParams) {
  return requestClient.get<Customer[]>('/feedalyze/customers', { params });
}

/**
 * 创建客户
 */
export async function createCustomer(data: CreateCustomerParams) {
  return requestClient.post<Customer>('/feedalyze/customers', data);
}

/**
 * 更新客户
 */
export async function updateCustomer(id: string, data: UpdateCustomerParams) {
  return requestClient.put<Customer>(`/feedalyze/customers/${id}`, data);
}

/**
 * 删除客户
 */
export async function deleteCustomer(id: string) {
  return requestClient.delete(`/feedalyze/customers/${id}`);
}

/** 客户类型选项 */
export const CUSTOMER_TYPES = [
  { value: 'normal', label: '普通客户', business_value: 1 },
  { value: 'paid', label: '付费客户', business_value: 3 },
  { value: 'major', label: '大客户', business_value: 5 },
  { value: 'strategic', label: '战略客户', business_value: 10 },
];
