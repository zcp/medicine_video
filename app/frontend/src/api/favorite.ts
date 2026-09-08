/**
 * 用户收藏相关API
 * 阶段一新建：2025
 * 封装用户收藏直播间相关的API请求
 */

import { get, post, del } from '@/utils/request';
import type { Favorite, FavoriteCreatePayload, FavoriteWithRoom } from '@/types/favorite';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';

/**
 * 获取用户收藏列表
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<FavoriteWithRoom>>>
 * @example
 * const response = await getFavorites({ page: 1, size: 10 });
 */
export const getFavorites = (params: QueryParams = {}): Promise<ApiResponse<PaginatedResponse<FavoriteWithRoom>>> => {
  return get<ApiResponse<PaginatedResponse<FavoriteWithRoom>>>('/users/me/favorites', params, { auth: true });
};

/**
 * 添加收藏
 * @param data 收藏数据
 * @returns Promise<ApiResponse<Favorite>>
 * @example
 * const response = await addFavorite({ room_id: '550e8400-e29b-41d4-a716-446655440001' });
 */
export const addFavorite = (data: FavoriteCreatePayload): Promise<ApiResponse<Favorite>> => {
  return post<ApiResponse<Favorite>>('/users/me/favorites', data, { auth: true });
};

/**
 * 取消收藏
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await removeFavorite('550e8400-e29b-41d4-a716-446655440001');
 */
export const removeFavorite = (roomId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/users/me/favorites/${roomId}`, undefined, { auth: true });
};

/**
 * 检查是否已收藏（旧端点，保留兼容）
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<{ is_favorited: boolean }>>
 * @deprecated 建议使用 checkIsFavorited
 * @example
 * const response = await checkFavorite('550e8400-e29b-41d4-a716-446655440001');
 * if (response.data.is_favorited) {
 *   console.log('已收藏');
 * }
 */
export const checkFavorite = (roomId: string): Promise<ApiResponse<{ is_favorited: boolean }>> => {
  return get<ApiResponse<{ is_favorited: boolean }>>(`/users/me/favorites/${roomId}/check`, undefined, { auth: true });
};

/**
 * 检查是否已收藏指定直播间（标准端点）
 * @param roomId 直播间ID
 * @returns Promise<ApiResponse<{ is_favorited: boolean }>>
 * @description 对齐用户行为模块标准API：GET /api/v1/rooms/{room_id}/is-favorited
 * @example
 * const response = await checkIsFavorited('550e8400-e29b-41d4-a716-446655440001');
 * if (response.data.is_favorited) {
 *   console.log('已收藏该直播间');
 * }
 */
export const checkIsFavorited = (roomId: string): Promise<ApiResponse<{ is_favorited: boolean }>> => {
  return get<ApiResponse<{ is_favorited: boolean }>>(
    `/rooms/${roomId}/is-favorited`,
    undefined,
    { auth: true }
  );
};
