/**
 * 房间相关 API
 * 目标：补齐被页面/Store 引用但缺失的模块，并保持与 favorites/subscriptions 一致的调用风格。
 */

import { request, upload } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import type {
  LiveRoom,
  LiveRoomDetail,
  CreateRoomRequest,
  UpdateRoomRequest,
  RoomStatistics,
  TestRoomPayload
} from '@/types/room'
import type { AdminRoomQueryParams, AdminRoomPageResult } from '@/types/adminRoom'

// ===== 房间基本管理 =====
export const getRooms = (params?: {
  page?: number
  size?: number
  category_id?: string
  sort?: string
}): Promise<ApiResponse<PaginatedResponse<LiveRoom>>> => {
  const cleanParams: Record<string, string | number> = {}
  if (params?.page !== undefined) cleanParams.page = params.page
  if (params?.size !== undefined) cleanParams.size = params.size
  if (params?.sort !== undefined) cleanParams.sort = params.sort
  if (params?.category_id !== undefined) cleanParams.category_id = params.category_id
  return request.get(API_PATHS.ROOM.LIST, { data: cleanParams })
}

export const getHomepageRooms = (params?: {
  page?: number
  size?: number
  category_id?: string
  sort?: string
}): Promise<ApiResponse<PaginatedResponse<any>>> => {
  const cleanParams: Record<string, string | number> = {}
  if (params?.page !== undefined) cleanParams.page = params.page
  if (params?.size !== undefined) cleanParams.size = params.size
  if (params?.sort !== undefined) cleanParams.sort = params.sort
  if (params?.category_id !== undefined) {
    if (!isValidUUID(params.category_id)) {
      console.warn(`Invalid category_id format: ${params.category_id}, removing from request`)
    } else {
      cleanParams.category_id = params.category_id
    }
  }
  return request.get(API_PATHS.OTHER.HOMEPAGE_ROOMS, { data: cleanParams, showError: false })
}

// UUID格式验证辅助函数
function isValidUUID(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(str)
}

export const getRoomById = (roomId: string): Promise<ApiResponse<LiveRoomDetail>> => {
  return request.get(API_PATHS.ROOM.DETAIL(roomId), { showError: false })
}

export const createRoom = (data: CreateRoomRequest): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ROOM.CREATE, data, {
    loading: true,
    loadingText: '创建中...',
    showError: false
  })
}

export const updateRoom = (roomId: string, data: UpdateRoomRequest): Promise<ApiResponse<any>> => {
  return request.patch(API_PATHS.ROOM.UPDATE(roomId), data, {
    loading: true,
    loadingText: '保存中...',
    showError: false
  })
}

export const deleteRoom = (roomId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.ROOM.DELETE(roomId), { loading: true, loadingText: '删除中...' })
}

export const deleteRoomSilent = (roomId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.ROOM.DELETE(roomId), { loading: false, showError: false })
}

// ===== 房间扩展功能 =====
export const getRoomSessions = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.SESSIONS(roomId), { showError: false })
}

export const getRoomSubVenues = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.SUB_VENUES(roomId), { showError: false })
}

export const getRoomBrands = (roomId: string, params?: Record<string, any>): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.BRANDS(roomId), { data: params, showError: false })
}

export const getRoomExperts = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.EXPERTS(roomId), { showError: false })
}

export const getRoomTopics = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.TOPICS(roomId), { showError: false })
}

export const checkRoomFavorited = (roomId: string): Promise<ApiResponse<{ is_favorited: boolean }>> => {
  return request.get(API_PATHS.ROOM.IS_FAVORITED(roomId), { showError: false })
}

export const getRoomMessages = (roomId: string, params?: Record<string, any>): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.MESSAGES(roomId), { data: params, showError: false })
}

export const sendRoomMessage = (roomId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ROOM.MESSAGES(roomId), data, { loading: true, loadingText: '发送中...' })
}

export const getRoomTabs = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { showError: false })
}

export const getRoomBrandsTab = (roomId: string, params?: Record<string, any>): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.BRANDS(roomId), { data: params, showError: false })
}

export const uploadRoomCover = (roomId: string, filePath: string): Promise<ApiResponse<{ cover_url: string }>> => {
  return upload({
    url: API_PATHS.ROOM.COVER(roomId),
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传封面中...'
  })
}

export const getRoomStatistics = (roomId: string): Promise<ApiResponse<RoomStatistics>> => {
  return request.get(`/rooms/${roomId}/statistics`, { showError: false })
  // NOTE: 后端文档未显式列出此端点，调用方 store/room.ts 已处理 404 fallback
}

// NOTE: /users/me/rooms - core服务 (独立路由: /api/v1/users/me/rooms → core_api)
export const getMyRooms = (
  params?: Record<string, any>,
  page?: number,
  size?: number
): Promise<ApiResponse<PaginatedResponse<any>>> => {
  // 过滤掉undefined参数
  const cleanParams = {
    ...(params || {}),
    ...(page ? { page } : {}),
    ...(size ? { size } : {})
  }
  const filteredParams = Object.fromEntries(
    Object.entries(cleanParams).filter(([_, value]) => value !== undefined)
  )
  return request.get(API_PATHS.USER_ROOMS.MY_ROOMS, { data: filteredParams, showError: false })
}

// ===== 批量操作 =====
export const batchGetRoomStatus = (roomIds: string[]): Promise<ApiResponse<any[]>> => {
  return request.post(API_PATHS.ROOM.BATCH_STATUS, { room_ids: roomIds }, { showError: false })
}


// ===== 管理员房间操作 =====

/**
 * 管理端全站房间列表（含私密）
 * GET /api/v1/admin/rooms → 网关 /api/core/admin/rooms
 * 认证：JWT + ADMIN/SUPERADMIN（非 Admin → 3003）
 * ⚠️ q / owner_user_id 仅在有非空字符串时传入，避免 null/"" 被当成过滤条件导致空列表
 */
export const getAdminRooms = (
  params?: AdminRoomQueryParams
): Promise<ApiResponse<AdminRoomPageResult>> => {
  const clean: Record<string, string | number | boolean> = {}
  const q = typeof params?.q === 'string' ? params.q.trim() : ''
  if (q) clean.q = q
  const ownerId =
    typeof params?.owner_user_id === 'string' ? params.owner_user_id.trim() : ''
  if (ownerId) clean.owner_user_id = ownerId
  if (params?.is_private !== undefined && params?.is_private !== null) {
    clean.is_private = params.is_private
  }
  if (params?.page !== undefined && params?.page !== null) clean.page = params.page
  if (params?.size !== undefined && params?.size !== null) clean.size = params.size
  return request.get(API_PATHS.ADMIN.ROOMS, { data: clean, showError: false })
}

export const setAdminRoomBrands = (roomId: string, brandIds: string[]): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ADMIN.BIND_ROOM_BRAND(roomId), { brand_ids: brandIds }, { loading: true, loadingText: '保存中...' })
}

/**
 * 为正式间确保测播间（幂等）
 * POST /rooms/{room_id}/test-room → 网关 /api/core/rooms/{id}/test-room
 */
export const ensureTestRoom = (
  formalRoomId: string,
  body?: { title_suffix?: string }
): Promise<ApiResponse<TestRoomPayload>> => {
  return request.post(API_PATHS.ROOM.TEST_ROOM(formalRoomId), body || {}, {
    showError: false,
    loading: true,
    loadingText: '准备测试连接...'
  })
}

export default {
  getRooms,
  getHomepageRooms,
  getRoomById,
  createRoom,
  updateRoom,
  deleteRoom,
  deleteRoomSilent,
  getRoomStatistics,
  getMyRooms,
  getRoomSessions,
  getRoomSubVenues,
  getRoomBrands,
  getRoomBrandsTab,
  getRoomExperts,
  getRoomTopics,
  checkRoomFavorited,
  getRoomMessages,
  sendRoomMessage,
  getRoomTabs,
  uploadRoomCover,
  batchGetRoomStatus,
  getAdminRooms,
  setAdminRoomBrands,
  ensureTestRoom
}
