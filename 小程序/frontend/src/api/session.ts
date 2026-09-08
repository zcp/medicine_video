/**
 * 场次(Session)相关 API
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import type {
  Session,
  SessionDetail,
  SessionListQuery,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionStatistics
} from '@/types/session'

export const getSessionList = (params?: SessionListQuery): Promise<ApiResponse<PaginatedResponse<Session>>> => {
  // 兼容：pageSize -> size
  const data: any = { ...(params || {}) }
  if (data.pageSize !== undefined && data.size === undefined) data.size = data.pageSize
  return request.get(API_PATHS.SESSION.LIST, { data })
}

export const getSessionDetail = (sessionId: string): Promise<ApiResponse<SessionDetail>> => {
  return request.get(API_PATHS.SESSION.DETAIL(sessionId), { showError: false })
}

export const createSession = (data: CreateSessionRequest & { room_id?: string }): Promise<ApiResponse<{ sessionId: string } & any>> => {
  const roomId: string = (data as any).room_id
  if (!roomId) return Promise.reject(new Error('createSession: room_id is required'))
  return request.post(API_PATHS.SESSION.CREATE(roomId), data, { loading: true, loadingText: '创建中...' })
}

export const updateSession = (sessionId: string, data: UpdateSessionRequest): Promise<ApiResponse<any>> => {
  return request.patch(API_PATHS.SESSION.DETAIL(sessionId), data, { loading: true, loadingText: '保存中...' })
}

export const deleteSession = (sessionId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.SESSION.DETAIL(sessionId), { loading: true, loadingText: '删除中...' })
}

export const getSessionStatistics = (sessionId: string): Promise<ApiResponse<SessionStatistics>> => {
  return request.get(API_PATHS.SESSION.STATISTICS(sessionId), { showError: false })
}

export const getRoomSessions = (
  roomId: string,
  params?: {
    page?: number
    size?: number
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }
): Promise<ApiResponse<PaginatedResponse<any>>> => {
  return request.get(API_PATHS.ROOM.SESSIONS(roomId), { data: params, showError: false })
}

export const createRoomSession = (roomId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ROOM.SESSIONS(roomId), data, { loading: true, loadingText: '创建中...' })
}

export const importSession = (roomId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.SESSION.IMPORT(roomId), data, { loading: true, loadingText: '导入中...' })
}

export const startSession = (sessionId: string): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.SESSION.START(sessionId), {}, { loading: true, loadingText: '开播中...', showError: false })
}

export const recordWatchSession = (sessionId: string, data: any): Promise<ApiResponse<any>> => {
  // 观看记录API - 使用history模块
  return request.post(API_PATHS.HISTORY.RECORD_WATCH(sessionId), data, { loading: false, showError: false })
}

export default {
  getSessionList,
  getSessionDetail,
  createSession,
  updateSession,
  deleteSession,
  getSessionStatistics,
  getRoomSessions,
  createRoomSession,
  importSession,
  startSession,
  recordWatchSession
}
