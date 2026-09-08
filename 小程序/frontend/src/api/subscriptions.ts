/**
 * 订阅功能API - 重构版本
 */

import { request } from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import { API_PATHS } from '@/config/api'

// ================== 4.10 User Subscriptions 模块API ==================

// ===== 订阅管理 (core服务中的用户行为) =====

/**
 * 添加订阅
 * §4.10.1 POST /api/v1/users/me/subscriptions
 * 请求体: { target_id, target_type }  ← 后端 Pydantic SubscriptionCreate
 */
export const addSubscription = async (data: {
  target_id: string
  target_type: 'room' | 'session'
}): Promise<ApiResponse<{
  id: string
  target_id: string
  target_type: string
  is_active: boolean
  created_at: string
}>> => {
  const payload = {
    target_id: String(data?.target_id || '').trim(),
    target_type: data?.target_type || 'room'
  }

  try {
    return await request.post(API_PATHS.SUBSCRIPTION.ADD, payload, {
      loading: true,
      loadingText: '订阅中...',
      showError: false
    })
  } catch (e: any) {
    const statusCode = e?.statusCode
    const msg = String(e?.message || e?.raw?.data?.message || '')

    // 已存在视为幂等成功
    if ((statusCode === 400 || statusCode === 409) && /已订阅|订阅已存在|资源已存在|already/i.test(msg)) {
      return {
        code: 200,
        message: 'success',
        data: {
          id: '',
          target_id: payload.target_id,
          target_type: payload.target_type,
          is_active: true,
          created_at: ''
        },
        timestamp: new Date().toISOString()
      } as ApiResponse<{
        id: string
        target_id: string
        target_type: string
        is_active: boolean
        created_at: string
      }>
    }

    throw e
  }
}

/**
 * 获取订阅列表
 * §4.10.2 GET /api/v1/users/me/subscriptions
 * 后端返回 SubscriptionItem: { id, user_id, target_id, target_type, is_active, created_at }
 * 前端 store 层 normalizeUserSubscriptionRoom 负责映射为 room_id/room_title 等
 */
export const getSubscriptionList = (params?: {
  page?: number
  size?: number
}): Promise<ApiResponse<PaginatedResponse<{
  id: string
  user_id: string
  target_id: string
  target_type: string
  is_active: boolean
  created_at: string
}>>> => {
  return request.get(API_PATHS.SUBSCRIPTION.LIST, { data: params })
}

/**
 * 取消订阅
 * §4.10.3 DELETE /api/v1/users/me/subscriptions/{room_id}
 */
export const removeSubscription = (roomId: string): Promise<ApiResponse<{
  room_id: string
  status: string
}>> => {
  return request.delete(API_PATHS.SUBSCRIPTION.REMOVE(roomId), {
    loading: true,
    loadingText: '取消订阅中...',
    showError: false
  })
}

/**
 * 检查订阅状态
 * §4.10.4 GET /api/v1/users/me/subscriptions/check/{targetId}
 */
export const checkSubscription = (targetId: string): Promise<ApiResponse<{ is_subscribed: boolean }>> => {
  return request.get(API_PATHS.SUBSCRIPTION.CHECK(targetId), { showError: false })
}

/**
 * 清除订阅历史
 * POST /api/v1/users/me/subscriptions/clear-history
 */
export const clearSubscriptionHistory = (): Promise<ApiResponse<void>> => {
  return request.post(API_PATHS.SUBSCRIPTION.CLEAR_HISTORY, {}, { loading: true, loadingText: '清除中...' })
}

// ===== 统一订阅API =====
export const subscribe = (roomId: string) => addSubscription({ target_id: roomId, target_type: 'room' })
export const unsubscribe = (roomId: string) => removeSubscription(roomId)

// ================== 导出默认对象 ==================

export default {
  addSubscription,
  getSubscriptionList,
  removeSubscription,
  checkSubscription,
  clearSubscriptionHistory,
  subscribe,
  unsubscribe
}
