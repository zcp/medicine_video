/**
 * 订阅相关API
 * @module api/subscription
 */

import { get, post, del } from '@/utils/request'
import type { SubscriptionWithTarget } from '@/types/subscription'
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common'

/**
 * 获取订阅列表
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<SubscriptionWithTarget>>>
 * @example
 * const subscriptions = await getSubscriptions({ page: 1, size: 20 });
 */
export const getSubscriptions = (
  params: QueryParams = {}
): Promise<ApiResponse<PaginatedResponse<SubscriptionWithTarget>>> => {
  return get<ApiResponse<PaginatedResponse<SubscriptionWithTarget>>>('/users/me/subscriptions', params, { auth: true })
}

/**
 * 添加订阅
 * @param data 订阅数据
 * @returns Promise<ApiResponse<void>>
 * @example
 * await addSubscription({ target_type: 'session', target_id: 'session-123' });
 */
export const addSubscription = (data: {
  target_type: 'room' | 'session'
  target_id: string
}): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/users/me/subscriptions', data, { auth: true })
}

/**
 * 取消订阅
 * @param targetType 订阅目标类型（room/session）
 * @param targetId 订阅目标ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await removeSubscription('room', 'room-uuid-123');
 */
export const removeSubscription = (
  targetType: 'room' | 'session',
  targetId: string
): Promise<ApiResponse<void>> => {
  // 使用查询参数而不是请求体传递删除参数
  const params = new URLSearchParams({
    target_type: targetType,
    target_id: targetId
  })
  
  return del<ApiResponse<void>>(
    `/users/me/subscriptions?${params.toString()}`,
    undefined,
    { auth: true }
  )
}

/**
 * 检查订阅状态
 * @param targetId 目标ID（房间ID或场次ID）
 * @returns Promise<ApiResponse<{ is_subscribed: boolean }>>
 * @deprecated 使用 checkSessionIsSubscribed 或 checkRoomIsSubscribed（端点不匹配后端标准）
 * @example
 * const { data } = await checkSubscription('session-123');
 * console.log(data.is_subscribed);
 */
export const checkSubscription = (targetId: string): Promise<ApiResponse<{ is_subscribed: boolean }>> => {
  return get<ApiResponse<{ is_subscribed: boolean }>>(`/users/me/subscriptions/check/${targetId}`, {}, { auth: true })
}

/**
 * 检查场次订阅状态
 * @param sessionId 场次ID
 * @returns Promise<ApiResponse<{ is_subscribed: boolean }>>
 * @description GET /api/v1/sessions/{session_id}/is-subscribed
 * @example
 * const { data } = await checkSessionIsSubscribed('session-uuid');
 * if (data.is_subscribed) console.log('已订阅该场次');
 */
export const checkSessionIsSubscribed = (sessionId: string): Promise<ApiResponse<{ is_subscribed: boolean }>> => {
  return get<ApiResponse<{ is_subscribed: boolean }>>(
    `/sessions/${sessionId}/is-subscribed`,
    undefined,
    { auth: true }
  )
}

/**
 * 检查房间订阅状态
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<{ is_subscribed: boolean }>>
 * @description GET /api/v1/rooms/{room_id}/is-subscribed
 * @example
 * const { data } = await checkRoomIsSubscribed('room-uuid');
 * if (data.is_subscribed) console.log('已订阅该房间');
 */
export const checkRoomIsSubscribed = (roomId: string): Promise<ApiResponse<{ is_subscribed: boolean }>> => {
  return get<ApiResponse<{ is_subscribed: boolean }>>(
    `/rooms/${roomId}/is-subscribed`,
    undefined,
    { auth: true }
  )
}

/**
 * 清除历史订阅（已通知和已过期的订阅）
 * @returns Promise<ApiResponse<void>>
 * @example
 * await clearSubscriptionHistory();
 */
export const clearSubscriptionHistory = (): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/users/me/subscriptions/clear-history', {}, { auth: true })
}
