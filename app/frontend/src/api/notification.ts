/**
 * 通知相关API
 * @module api/notification
 */

import { get, post, patch } from '@/utils/request'
import type { 
  NotificationItem, 
  NotificationListParams, 
  PaginatedNotifications,
  CreateNotificationRequest
} from '@/types/notification'
import type { ApiResponse, QueryParams } from '@/types/common'

/**
 * 获取通知列表
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedNotifications>>
 * @example
 * const notifications = await getNotifications({ page: 1, size: 20, notification_type: 'system' });
 */
export const getNotifications = (
  params: NotificationListParams = {}
): Promise<ApiResponse<PaginatedNotifications>> => {
  return get<ApiResponse<PaginatedNotifications>>('/users/me/notifications', params, { auth: true })
}

/**
 * 获取单条通知详情
 * @param notificationId 通知ID
 * @returns Promise<ApiResponse<NotificationItem>>（他人通知 → 404/2001）
 */
export const getNotificationDetail = (notificationId: string): Promise<ApiResponse<NotificationItem>> => {
  return get<ApiResponse<NotificationItem>>(`/users/me/notifications/${notificationId}`, undefined, { auth: true })
}

/**
 * 获取未读通知数量
 * @returns Promise<ApiResponse<{ unread_count: number }>>
 * @example
 * const { unread_count } = await getUnreadCount();
 */
export const getUnreadCount = (): Promise<ApiResponse<{ unread_count: number }>> => {
  return get<ApiResponse<{ unread_count: number }>>('/users/me/notifications/unread-count', {}, { auth: true })
}

/**
 * 标记单条通知为已读
 * @param notificationId 通知ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await markNotificationRead('notification-123');
 */
export const markNotificationRead = (notificationId: string): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(`/users/me/notifications/${notificationId}/read`, {}, { auth: true })
}

/**
 * 标记所有通知为已读
 * @returns Promise<ApiResponse<void>>
 * @example
 * await markAllNotificationsRead();
 */
export const markAllNotificationsRead = (): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/users/me/notifications/read-all', {}, { auth: true })
}

// ========== 管理员API（未来扩展） ==========

/**
 * 创建通知（管理员）
 * @description 后端 POST /admin/notifications 为唯一创建端点，payload 含 user_ids 数组（原生批量）；
 *   后端不支持"全站推送"（user_ids 为空 → 400）。原 /admin/notifications/batch 路由后端不存在（已移除）。
 * @param data 通知数据（含 user_ids）
 * @returns Promise<ApiResponse<NotificationItem>>
 */
export const createNotification = (data: CreateNotificationRequest): Promise<ApiResponse<NotificationItem>> => {
  return post<ApiResponse<NotificationItem>>('/admin/notifications', data, { auth: true })
}

/**
 * 获取所有通知列表（管理员）
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedNotifications>>
 */
export const getAllNotifications = (params: NotificationListParams = {}): Promise<ApiResponse<PaginatedNotifications>> => {
  return get<ApiResponse<PaginatedNotifications>>('/admin/notifications', params, { auth: true })
}

// ========== Mock API支持 ==========

/**
 * 检查是否使用Mock数据
 */
export const shouldUseMock = (): boolean => {
  // 在开发环境或未配置后端API时使用Mock
  return process.env.NODE_ENV === 'development' || !process.env.VUE_APP_API_BASE_URL
}
