/**
 * 直播间Tab管理 API
 * 以后端设计文档为准：《06-直播间Tab管理-后端设计文档.md》
 *
 * DDL: live_room_tabs 表（V1.1）
 *   id UUID PK, room_id UUID FK, tab_key VARCHAR(64) NOT NULL,
 *   title VARCHAR(128) NOT NULL, content_type ENUM('text','image','mixed') NOT NULL,
 *   text_content TEXT, image_url TEXT, sort_order INTEGER, is_active BOOLEAN,
 *   created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
 *
 * 端点清单（7个）:
 *   GET  /content/admin/rooms/{roomId}/tabs         管理端列表（JWT+Admin）
 *   POST /content/admin/rooms/{roomId}/tabs         创建（JWT+Admin）
 *   PATCH /content/admin/tabs/{tabId}               更新（JWT+Admin）
 *   DELETE /content/admin/tabs/{tabId}              软删除（JWT+Admin）
 *   POST /content/admin/rooms/{roomId}/tabs/image   上传图片（JWT+Admin）
 *   PATCH /content/admin/rooms/{roomId}/tabs/sort   批量排序（JWT+Admin）
 *   GET  /content/rooms/{roomId}/tabs               公开列表（Public）
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'

/**
 * Tab内容类型枚举（对应后端 live_room_tab_content_type）
 */
export type LiveRoomTabContentType = 'text' | 'image' | 'mixed'

/**
 * 直播间Tab项（对应后端 LiveRoomTabItem Schema）
 */
export interface LiveRoomTab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: LiveRoomTabContentType
  text_content?: string | null
  image_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 创建Tab请求（对应后端 LiveRoomTabCreate Schema）
 */
export interface LiveRoomTabCreate {
  tab_key: string
  title: string
  content_type: LiveRoomTabContentType
  text_content?: string
  image_url?: string
  sort_order?: number
  is_active?: boolean
}

/**
 * 更新Tab请求（对应后端 LiveRoomTabUpdate Schema）
 * 所有字段可选，部分更新
 */
export interface LiveRoomTabUpdate {
  tab_key?: string
  title?: string
  content_type?: LiveRoomTabContentType
  text_content?: string
  image_url?: string
  sort_order?: number
  is_active?: boolean
}

/**
 * 批量排序请求（对应后端 LiveRoomTabSortRequest Schema）
 */
export interface LiveRoomTabSortRequest {
  tab_ids: string[]
}

// ============ 管理端接口 ============

/**
 * 获取直播间的所有Tab（含禁用）
 * GET /api/v1/admin/rooms/{roomId}/tabs
 */
export const getTabs = (roomId: string): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ADMIN.ROOM_TABS(roomId), { showError: false })
}

/**
 * 创建Tab
 * POST /api/v1/admin/rooms/{roomId}/tabs
 */
export const createTab = (roomId: string, data: LiveRoomTabCreate): Promise<ApiResponse<LiveRoomTab>> => {
  return request.post(API_PATHS.ADMIN.CREATE_TAB(roomId), data, {
    loading: true,
    loadingText: '创建中...',
    showError: false
  })
}

/**
 * 更新Tab（部分更新）
 * PATCH /api/v1/admin/tabs/{tabId}
 */
export const updateTab = (tabId: string, data: LiveRoomTabUpdate): Promise<ApiResponse<LiveRoomTab>> => {
  return request.patch(API_PATHS.ADMIN.UPDATE_TAB(tabId), data, {
    loading: true,
    loadingText: '保存中...',
    showError: false
  })
}

/**
 * 删除Tab（软删除）
 * DELETE /api/v1/admin/tabs/{tabId}
 */
export const deleteTab = (tabId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.ADMIN.DELETE_TAB(tabId), {
    loading: true,
    loadingText: '删除中...'
  })
}

/**
 * 上传Tab图片
 * POST /api/v1/admin/rooms/{roomId}/tabs/image
 * 注意：小程序环境使用 uni.uploadFile，不支持 FormData
 */
export const uploadTabImage = (
  roomId: string,
  filePath: string
): Promise<ApiResponse<{ image_url: string }>> => {
  return request.upload({
    url: API_PATHS.ADMIN.UPLOAD_TAB_IMAGE(roomId),
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传中...'
  })
}

/**
 * 批量排序Tab（零偏差：使用后端专用排序端点，非逐个PATCH）
 * PATCH /api/v1/admin/rooms/{roomId}/tabs/sort
 */
export const sortTabs = (roomId: string, data: LiveRoomTabSortRequest): Promise<ApiResponse<null>> => {
  return request.patch(API_PATHS.ADMIN.SORT_TABS(roomId), data, {
    loading: true,
    loadingText: '排序中...'
  })
}

// ============ 公开接口 ============

/**
 * 获取直播间公开Tab列表（仅is_active=true）
 * GET /api/v1/rooms/{roomId}/tabs
 */
export const getPublicTabs = (roomId: string): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { auth: false, showError: false })
}

export default {
  getTabs,
  createTab,
  updateTab,
  deleteTab,
  uploadTabImage,
  sortTabs,
  getPublicTabs
}
