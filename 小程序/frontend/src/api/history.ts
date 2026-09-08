/**
 * 观看历史API - 重构版本
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'

// ===== 观看历史记录 (core服务) =====

/**
 * 获取观看历史列表
 * 设计文档：GET /users/me/watch-history
 */
export const getWatchHistory = (params?: {
  page?: number
  size?: number
  sessionType?: string
}): Promise<any> => {
  return request.get(API_PATHS.WATCH_HISTORY.LIST, {
    data: params,
    showError: false
  })
}

/**
 * 删除单条观看历史
 * 设计文档：DELETE /users/me/watch-history/{historyId}
 */
export const deleteWatchHistory = (historyId: string): Promise<any> => {
  return request.delete(API_PATHS.WATCH_HISTORY.DELETE(historyId), {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

/**
 * 记录观看历史
 * 设计文档：POST /users/me/watch-history
 */
export const recordWatchHistory = (data: {
  session_id: string
  progress?: number
}): Promise<any> => {
  return request.post(API_PATHS.WATCH_HISTORY.RECORD, data, { loading: false, showError: false })
}

/**
 * 清空观看历史
 * POST /users/me/watch-history/clear
 */
export const clearWatchHistory = (): Promise<any> => {
  return request.post(API_PATHS.WATCH_HISTORY.CLEAR, {}, { loading: true, loadingText: '清除中...' })
}

// ===== 兼容旧版本API =====
export const getHistoryList = (params?: any) => getWatchHistory(params)
export const removeHistory = (id: string) => deleteWatchHistory(id)

export default {
  getWatchHistory,
  deleteWatchHistory,
  recordWatchHistory,
  clearWatchHistory,
  getHistoryList,
  removeHistory
}
