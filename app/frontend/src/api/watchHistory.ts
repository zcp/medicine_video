/**
 * 观看历史相关API
 * @module api/watchHistory
 */

import { get, post, del } from '@/utils/request'
import type { WatchHistoryItem } from '@/types/watchHistory'
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common'

/**
 * 记录观看行为
 * @param sessionId 场次ID
 * @param data 观看数据
 * @returns Promise<ApiResponse<void>>
 * @example
 * await recordWatch('session-123', { progress: 120, extra: { device: 'web', quality: '1080p' } });
 */
export const recordWatch = (
  sessionId: string,
  data: { progress?: number; extra?: Record<string, any> }
): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(
    '/users/me/watch-history',
    {
      session_id: sessionId,
      progress: data.progress || 0,
      ...(data.extra && Object.keys(data.extra).length > 0 ? { extra: data.extra } : {})
    },
    { auth: true }
  )
}

/**
 * 获取观看历史列表
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<WatchHistoryItem>>>
 * @example
 * const history = await getWatchHistory({ page: 1, size: 20 });
 */
export const getWatchHistory = (
  params: QueryParams = {}
): Promise<ApiResponse<PaginatedResponse<WatchHistoryItem>>> => {
  return get<ApiResponse<PaginatedResponse<WatchHistoryItem>>>('/users/me/watch-history', params, { auth: true })
}

/**
 * 删除单条观看历史
 * @param historyId 历史记录ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await deleteWatchHistory('history-123');
 */
export const deleteWatchHistory = (historyId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/users/me/watch-history/${historyId}`, undefined, { auth: true })
}
