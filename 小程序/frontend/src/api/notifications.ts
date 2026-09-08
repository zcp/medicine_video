/**
 * 通知相关API - 重构版本
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { logger } from '@/logs/logger'

export const getNotificationList = (params?: any) => request.get(API_PATHS.NOTIFICATION.LIST, { data: params })

/** GET /users/me/notifications/unread-count */
export const getUnreadNotificationCount = () =>
  request.get(API_PATHS.NOTIFICATION.UNREAD_COUNT, { showError: false })

/**
 * 获取通知详情，兼容不同路径前缀和网关配置：
 * 1) 优先尝试配置中的 `API_PATHS.NOTIFICATION.DETAIL`
 * 2) 若返回 404，则回退到 `/me/notifications/{id}`（历史兼容路径）
 */
export async function getNotificationDetail(id: string) {
	const primaryUrl = API_PATHS.NOTIFICATION.DETAIL(id)
	logger.info('network', '请求通知详情 - 尝试主路径', { url: primaryUrl, notificationId: id })
	const start = Date.now()
	try {
		const resp = await request.get(primaryUrl)
		logger.info('network', '通知详情响应（主路径）', {
			url: primaryUrl,
			duration: Date.now() - start,
			preview: JSON.stringify(resp.data).slice(0, 300)
		})
		return resp
	} catch (err: any) {
		const status = err?.statusCode || (err && err.raw && err.raw.statusCode)
		logger.warn('network', '通知详情主路径请求失败，将尝试回退路径', { url: primaryUrl, status, err: err?.message || err })
		if (status === 404) {
			const alt = `/users/me/notifications/${id}`
			logger.info('network', '尝试回退通知详情路径', { alt, notificationId: id })
			try {
				const start2 = Date.now()
				const resp2 = await request.get(alt)
				logger.info('network', '通知详情响应（回退路径）', {
					url: alt,
					duration: Date.now() - start2,
					preview: JSON.stringify(resp2.data).slice(0, 300)
				})
				return resp2
			} catch (e: any) {
				logger.error('network', '回退路径请求也失败', e)
				throw err
			}
		}
		throw err
	}
}

// §4.12.2 POST /api/v1/users/me/notifications/{notification_id}/read
export const markNotificationAsRead = (id: string) => request.post(API_PATHS.NOTIFICATION.MARK_READ(id), {})

export default {
	getNotificationList,
	getUnreadNotificationCount,
	getNotificationDetail,
	markNotificationAsRead
}
