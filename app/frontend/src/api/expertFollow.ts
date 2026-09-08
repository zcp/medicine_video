/**
 * 关注专家相关API
 * 封装用户关注专家相关的API请求
 */

import { get, post, del } from '@/utils/request';
import type { 
  ExpertFollowRequest, 
  ExpertFollowResponse, 
  FollowedExpertItem,
  CheckFollowStatusResponse 
} from '@/types/expertFollow';
import type { ApiResponse } from '@/types/common';

/**
 * 关注专家
 * @param data 关注请求数据
 * @returns Promise<ApiResponse<ExpertFollowResponse>>
 * @example
 * const response = await followExpert({ expert_id: '550e8400-e29b-41d4-a716-446655440001' });
 * if (response.code === 200) {
 *   console.log('关注成功');
 * }
 */
export const followExpert = (data: ExpertFollowRequest): Promise<ApiResponse<ExpertFollowResponse>> => {
  return post<ApiResponse<ExpertFollowResponse>>('/users/me/followed-experts', data, { auth: true });
};

/**
 * 取消关注专家
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * const response = await unfollowExpert('550e8400-e29b-41d4-a716-446655440001');
 * if (response.code === 200) {
 *   console.log('取消关注成功');
 * }
 */
export const unfollowExpert = (expertId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/users/me/followed-experts/${expertId}`, undefined, { auth: true });
};

/**
 * 获取关注的专家列表
 * @param includeLiveStatus 是否包含直播状态，默认true
 * @returns Promise<ApiResponse<FollowedExpertItem[]>>
 * @example
 * const response = await getFollowedExperts(true);
 * console.log('关注的专家:', response.data);
 */
export const getFollowedExperts = (includeLiveStatus: boolean = true): Promise<ApiResponse<FollowedExpertItem[]>> => {
  return get<ApiResponse<FollowedExpertItem[]>>(
    '/users/me/followed-experts', 
    { include_live_status: includeLiveStatus }, 
    { auth: true }
  );
};

/**
 * 检查是否已关注某个专家（旧端点，保留兼容）
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<CheckFollowStatusResponse>>
 * @deprecated 建议使用 checkIsFollowed
 * @example
 * const response = await checkFollowStatus('550e8400-e29b-41d4-a716-446655440001');
 * if (response.data.is_followed) {
 *   console.log('已关注');
 * }
 */
export const checkFollowStatus = (expertId: string): Promise<ApiResponse<CheckFollowStatusResponse>> => {
  return get<ApiResponse<CheckFollowStatusResponse>>(
    `/users/me/followed-experts/${expertId}/check`, 
    undefined, 
    { auth: true }
  );
};

/**
 * 检查是否已关注指定专家（标准端点）
 * @param expertId 专家ID
 * @returns Promise<ApiResponse<{ is_followed: boolean }>>
 * @description 对齐专家模块标准API：GET /api/v1/experts/{expert_id}/is-followed
 * @example
 * const response = await checkIsFollowed('cc67874b-fb5e-4ec4-afed-a5724702f48c');
 * if (response.data.is_followed) {
 *   console.log('已关注该专家');
 * }
 */
export const checkIsFollowed = (expertId: string): Promise<ApiResponse<{ is_followed: boolean }>> => {
  return get<ApiResponse<{ is_followed: boolean }>>(
    `/experts/${expertId}/is-followed`,
    undefined,
    { auth: true }
  );
};
