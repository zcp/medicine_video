/**
 * 专家相关API
 * 阶段一新建：2025
 * 封装专家信息相关的API请求
 */

import { get, post, patch, del } from '@/utils/request';
import type { Expert, ExpertCreatePayload, ExpertUpdatePayload } from '@/types/expert';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';

/**
 * 获取专家列表（公开接口）
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<Expert>>>
 * @example
 * const response = await getExperts({ page: 1, size: 10 });
 */
export const getExperts = (params: QueryParams = {}): Promise<ApiResponse<PaginatedResponse<Expert>>> => {
  return get<ApiResponse<PaginatedResponse<Expert>>>('/experts', params);
};

/**
 * 获取首页推荐专家（公开接口）
 * @param params 查询参数
 * @returns Promise<ApiResponse<Expert[]>>
 * @example
 * const response = await getFeaturedExperts({ limit: 5 });
 */
export const getFeaturedExperts = (params: { limit?: number } = {}): Promise<ApiResponse<Expert[]>> => {
  return get<ApiResponse<Expert[]>>('/featured-experts', params);
};

/**
 * 获取专家详情（公开接口）
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<Expert>>
 * @example
 * const response = await getExpertById('cc67874b-fb5e-4ec4-afed-a5724702f48c');
 */
export const getExpertById = (expertId: string): Promise<ApiResponse<Expert>> => {
  return get<ApiResponse<Expert>>(`/experts/${expertId}`);
};

/**
 * 获取专家场次列表（公开接口）
 * @param expertId 专家ID
 * @param params 查询参数
 * @returns Promise<ApiResponse<any>>
 * @example
 * const response = await getExpertSessions('cc67874b-fb5e-4ec4-afed-a5724702f48c', { page: 1, size: 10 });
 */
export const getExpertSessions = (
  expertId: string, 
  params: { page?: number; size?: number; role?: string } = {}
): Promise<ApiResponse<any>> => {
  return get<ApiResponse<any>>(`/experts/${expertId}/sessions`, params);
};

/**
 * 获取专家粉丝数（公开接口，Optional Auth）
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<{ follower_count: number }>>
 */
export const getExpertFollowerCount = (
  expertId: string
): Promise<ApiResponse<{ follower_count: number }>> => {
  return get<ApiResponse<{ follower_count: number }>>(`/experts/${expertId}/follower-count`);
};

/**
 * 创建专家（管理员接口）
 * @param data 专家创建数据
 * @returns Promise<ApiResponse<Expert>>
 * @example
 * const response = await createExpert({
 *   name: '张三',
 *   title: '主任医师',
 *   hospital: '北京协和医院'
 * });
 */
export const createExpert = (data: ExpertCreatePayload): Promise<ApiResponse<Expert>> => {
  return post<ApiResponse<Expert>>('/admin/experts', data, { auth: true });
};

/**
 * 更新专家（管理员接口）
 * @param expertId 专家ID
 * @param data 专家更新数据
 * @returns Promise<ApiResponse<Expert>>
 * @example
 * const response = await updateExpert('550e8400-e29b-41d4-a716-446655440001', {
 *   title: '教授、主任医师'
 * });
 */
export const updateExpert = (expertId: string, data: ExpertUpdatePayload): Promise<ApiResponse<Expert>> => {
  return patch<ApiResponse<Expert>>(`/admin/experts/${expertId}`, data, { auth: true });
};

/**
 * 删除专家（管理员接口）
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await deleteExpert('550e8400-e29b-41d4-a716-446655440001');
 */
export const deleteExpert = (expertId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/experts/${expertId}`, undefined, { auth: true });
};

/**
 * 获取专家列表（管理员接口，包含所有状态）
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<Expert>>>
 */
export const getAdminExperts = (params: QueryParams & { is_featured?: boolean } = {}, options?: { showLoading?: boolean }): Promise<ApiResponse<PaginatedResponse<Expert>>> => {
  return get<ApiResponse<PaginatedResponse<Expert>>>('/admin/experts', params, { auth: true, ...options }, { retry: 1, timeout: 8000 });
};

/**
 * 获取场次专家列表（公开接口）
 * @param sessionId 场次ID
 * @param params 查询参数（可选role筛选）
 * @returns Promise<ApiResponse<Expert[]>>
 * @example
 * const response = await getSessionExperts('550e8400-e29b-41d4-a716-446655440001');
 */
export const getSessionExperts = (
  sessionId: string,
  params: { role?: string } = {},
  options: { showLoading?: boolean } = {}
): Promise<ApiResponse<Expert[]>> => {
  return get<ApiResponse<Expert[]>>(`/experts/sessions/${sessionId}/experts`, params, { ...options });
};

/**
 * 设置场次专家列表（管理员接口）
 * @param sessionId 场次ID
 * @param experts 专家列表
 * @returns Promise<ApiResponse<{ session_id: string; experts_count: number }>>
 * @example
 * const response = await setSessionExperts('session-uuid', [
 *   { expert_id: 'expert-uuid-1', role: '主讲', sort_order: 0 }
 * ]);
 */
export const setSessionExperts = (
  sessionId: string, 
  experts: Array<{ expert_id: string; role: string; sort_order: number }>
): Promise<ApiResponse<{ session_id: string; experts_count: number }>> => {
  return post<ApiResponse<{ session_id: string; experts_count: number }>>(
    `/experts/sessions/${sessionId}/experts`, 
    experts, 
    { auth: true }
  );
};

/**
 * 获取房间专家列表（公开接口）
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<Expert[]>>
 * @example
 * const response = await getRoomExperts('room-uuid');
 */
export const getRoomExperts = (roomId: string): Promise<ApiResponse<Expert[]>> => {
  return get<ApiResponse<Expert[]>>(`/rooms/${roomId}/experts`);
};
