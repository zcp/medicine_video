/**
 * 收藏功能API - 重构版本
 * 使用统一的API配置和简化的request系统
 */

import { request } from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import { API_PATHS } from '@/config/api'

// ================== 4.8 User Favorites 模块API ==================

/**
 * 4.8.1 添加收藏（用户）
 * @description 当前用户收藏指定直播间
 * @param roomId 直播间ID
 * @returns 收藏信息
 */
/**
 * 添加收藏
 * 标准路径: POST /api/v1/users/me/favorites
 */
export const addFavorite = (roomId: string): Promise<ApiResponse<{
  id: string
  room_id: string
  room_title: string
  created_at: string
}>> => {
  return request.post(API_PATHS.FAVORITE.ADD,
    { room_id: roomId }, 
    { loading: true, loadingText: '收藏中...' }
  )
}

/**
 * 获取收藏列表
 * 标准路径: GET /api/v1/users/me/favorites
 */
export const getFavoriteList = (params?: {
  page?: number
  size?: number
}): Promise<ApiResponse<PaginatedResponse<{
  id: string
  room_id: string
  room_title: string
  room_cover_url: string
  created_at: string
}>>> => {
  return request.get(API_PATHS.FAVORITE.LIST, { data: params })
}

/**
 * 取消收藏
 * 标准路径: DELETE /api/v1/users/me/favorites/{roomId}
 */
export const removeFavorite = (roomId: string): Promise<ApiResponse<{
  room_id: string
  status: string
}>> => {
  return request.delete(API_PATHS.FAVORITE.REMOVE(roomId), {
    loading: true,
    loadingText: '取消收藏中...'
  })
}

// ================== 导出默认对象 ==================

export default {
  addFavorite,
  getFavoriteList,
  removeFavorite
}
