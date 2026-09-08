/**
 * 直播间留言 API
 * 严格对齐《07-直播间留言-后端设计文档.md》V1.1
 *
 * 用户端（3）:
 *   GET    /api/v1/rooms/{roomId}/messages
 *   POST   /api/v1/rooms/{roomId}/messages
 *   DELETE /api/v1/rooms/{roomId}/messages/{messageId}
 *
 * 管理端（3，仅 admin）:
 *   GET    /api/v1/admin/messages
 *   POST   /api/v1/admin/messages/batch-delete
 *   DELETE /api/v1/admin/rooms/{roomId}/messages
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  RoomMessageItem,
  RoomMessageCreate,
  RoomMessageQueryParams,
  RoomMessagePageResult,
  AdminMessageQueryParams,
  AdminMessagePageResult,
  BatchDeleteRequest,
  BatchDeleteResult,
  ClearRoomMessagesResult
} from '@/types/roomMessage'

/**
 * 获取直播间留言列表（公开/可选 JWT，分页，created_at DESC）
 */
export const getRoomMessages = (
  roomId: string,
  params?: RoomMessageQueryParams
): Promise<ApiResponse<RoomMessagePageResult>> => {
  const page = params?.page
  const size = params?.size ?? params?.page_size
  return request.get(API_PATHS.MESSAGE.ROOM_MESSAGES(roomId), {
    data: {
      ...(page != null ? { page } : {}),
      ...(size != null ? { size, page_size: size } : {})
    },
    // 公开可读；有 Token 时带上，便于私密房/身份相关展示
    auth: true,
    showError: false
  })
}

/**
 * 发送留言（JWT，内容 1-500 字符）
 */
export const sendRoomMessage = (
  roomId: string,
  data: RoomMessageCreate
): Promise<ApiResponse<RoomMessageItem>> => {
  return request.post(API_PATHS.MESSAGE.ROOM_MESSAGES(roomId), data, {
    // 直播评论：禁止全屏 showLoading，否则真机像「卡住」；由页面乐观更新反馈
    loading: false,
    showError: false
  })
}

/**
 * 删除留言（JWT，物理删除；admin 可删任意，普通用户仅本人）
 */
export const deleteMessage = (
  roomId: string,
  messageId: string
): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.MESSAGE.MESSAGE_DETAIL(roomId, messageId), {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

/**
 * 管理端全局留言列表（JWT，仅 admin）
 */
export const getAdminMessages = (
  params?: AdminMessageQueryParams
): Promise<ApiResponse<AdminMessagePageResult>> => {
  return request.get(API_PATHS.MESSAGE.ADMIN_LIST, {
    data: params,
    showError: false
  })
}

/**
 * 管理端批量删除留言（JWT，仅 admin，最多 200 条/次）
 */
export const batchDeleteMessages = (
  data: BatchDeleteRequest
): Promise<ApiResponse<BatchDeleteResult>> => {
  return request.post(API_PATHS.MESSAGE.ADMIN_BATCH_DELETE, data, {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

/**
 * 管理端清空指定直播间全部留言（JWT，仅 admin）
 */
export const clearRoomMessages = (
  roomId: string
): Promise<ApiResponse<ClearRoomMessagesResult>> => {
  return request.delete(API_PATHS.MESSAGE.ADMIN_CLEAR_ROOM(roomId), {
    loading: true,
    loadingText: '清空中...',
    showError: false
  })
}

export default {
  getRoomMessages,
  sendRoomMessage,
  deleteMessage,
  getAdminMessages,
  batchDeleteMessages,
  clearRoomMessages
}
