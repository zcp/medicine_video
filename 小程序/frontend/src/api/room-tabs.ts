/**
 * 直播间Tab公开 API
 * 以后端设计文档为准：《06-直播间Tab管理-后端设计文档.md》
 * GET /api/v1/content/rooms/{roomId}/tabs（公开，仅 is_active=true）
 *
 * DDL: id, room_id, tab_key, title, content_type, text_content, image_url, sort_order, is_active, created_at, updated_at
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type { LiveRoomTab } from '@/api/tabs'

/**
 * 获取直播间公开Tab列表（仅is_active=true）
 * GET /api/v1/content/rooms/{roomId}/tabs
 */
export const getRoomTabs = (roomId: string): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { auth: false, showError: false })
}

export default {
  getRoomTabs
}
