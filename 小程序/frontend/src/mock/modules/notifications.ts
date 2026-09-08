/**
 * Notifications 模块 Mock 数据
 */

import { registerMockRule, mockSuccess } from '../index'

// Mock 数据
let mockNotifications = [
  {
    id: 'notif_1',
    title: '系统通知',
    content: '欢迎使用医学直播平台',
    notification_type: 'system',
    is_read: false,
    created_at: '2024-12-01T10:00:00Z'
  },
  {
    id: 'notif_2',
    title: '直播提醒',
    content: '您关注的专家即将开播',
    notification_type: 'live',
    related_id: 'session_123',
    related_type: 'session',
    is_read: false,
    created_at: '2024-12-01T09:30:00Z'
  },
  {
    id: 'notif_3',
    title: '关注通知',
    content: '张医生关注了你',
    notification_type: 'follow',
    is_read: true,
    created_at: '2024-11-30T15:20:00Z'
  },
  {
    id: 'notif_4',
    title: '互动消息',
    content: '您的评论收到了回复',
    notification_type: 'comment',
    is_read: true,
    created_at: '2024-11-30T12:00:00Z'
  },
  {
    id: 'notif_5',
    title: '系统维护',
    content: '系统将于今晚进行维护',
    notification_type: 'system',
    is_read: false,
    created_at: '2024-12-01T08:00:00Z'
  }
]

export function setupNotificationsMock() {
  // 获取通知详情
  registerMockRule({
    pattern: /\/api\/v1\/users\/me\/notifications\/[^/]+$/,
    method: 'GET',
    handler: (params) => {
      const notifId = params?.notificationId || 'notif_1'
      const notification = mockNotifications.find(n => n.id === notifId)
      return mockSuccess(notification || mockNotifications[0])
    }
  })

  // 全部标记为已读
  registerMockRule({
    pattern: '/api/v1/users/me/notifications/read-all',
    method: 'POST',
    handler: () => {
      const unreadCount = mockNotifications.filter(n => !n.is_read).length
      mockNotifications = mockNotifications.map(n => ({ ...n, is_read: true }))
      return mockSuccess({ updated_count: unreadCount })
    }
  })

  // 批量标记为已读
  registerMockRule({
    pattern: '/api/v1/users/me/notifications/batch-read',
    method: 'POST',
    handler: (params) => {
      const ids = params?.notification_ids || []
      mockNotifications = mockNotifications.map(n => 
        ids.includes(n.id) ? { ...n, is_read: true } : n
      )
      return mockSuccess({
        updated_count: ids.length,
        notification_ids: ids
      })
    }
  })

  // 删除通知
  registerMockRule({
    pattern: /\/api\/v1\/users\/me\/notifications\/[^/]+$/,
    method: 'DELETE',
    handler: (params) => {
      const notifId = params?.notificationId
      mockNotifications = mockNotifications.filter(n => n.id !== notifId)
      return mockSuccess({
        notification_id: notifId,
        status: 'deleted'
      })
    }
  })

  // 获取未读数量
  registerMockRule({
    pattern: '/api/v1/users/me/notifications/unread-count',
    method: 'GET',
    handler: () => {
      const unread = mockNotifications.filter(n => !n.is_read)
      const byType = unread.reduce((acc, n) => {
        acc[n.notification_type] = (acc[n.notification_type] || 0) + 1
        return acc
      }, {} as Record<string, number>)
      
      return mockSuccess({
        unread: unread.length,
        by_type: byType
      })
    }
  })

  // 获取通知统计
  registerMockRule({
    pattern: '/api/v1/users/me/notifications/statistics',
    method: 'GET',
    handler: () => {
      const unread = mockNotifications.filter(n => !n.is_read).length
      const byType = mockNotifications.reduce((acc, n) => {
        acc[n.notification_type] = (acc[n.notification_type] || 0) + 1
        return acc
      }, {} as Record<string, number>)
      
      return mockSuccess({
        total: mockNotifications.length,
        unread,
        read: mockNotifications.length - unread,
        by_type: byType
      })
    }
  })

  // 获取通知设置
  registerMockRule({
    pattern: '/api/v1/users/me/notification-settings',
    method: 'GET',
    handler: () => {
      return mockSuccess({
        system_enabled: true,
        live_enabled: true,
        follow_enabled: true,
        email_enabled: false,
        push_enabled: true
      })
    }
  })

  // 更新通知设置
  registerMockRule({
    pattern: '/api/v1/users/me/notification-settings',
    method: 'PATCH',
    handler: (params) => {
      return mockSuccess(params)
    }
  })

  console.log('  ✓ Notifications Mock 已注册')
}
