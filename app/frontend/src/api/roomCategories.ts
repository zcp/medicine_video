/**
 * 直播间分类关联API
 * 封装直播间与分类关联相关的API请求
 */

import { get, del } from '@/utils/request';
import type { Category } from '@/types/category';
import type { ApiResponse } from '@/types/common';

/**
 * 获取直播间的分类列表（公开）
 * @param roomId 直播间ID
 * @returns Promise<ApiResponse<Category[]>>
 * @example
 * const response = await getRoomCategories('room_uuid_123');
 */
export const getRoomCategories = (roomId: string): Promise<ApiResponse<Category[]>> => {
  return get<ApiResponse<Category[]>>(`/rooms/${roomId}/categories`);
};

/**
 * 删除直播间的单个分类关联（登录用户，需为房间创建者或管理员）
 * @param roomId 直播间ID
 * @param categoryId 分类ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await removeRoomCategory('room_uuid_123', 'cat_uuid_1');
 */
export const removeRoomCategory = (roomId: string, categoryId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/rooms/${roomId}/categories/${categoryId}`, undefined, { auth: true });
};
