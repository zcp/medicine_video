/**
 * 通知Mock数据
 * @module mock/notification
 */

import type { NotificationItem, PaginatedNotifications } from '@/types/notification'

/**
 * 生成Mock通知数据
 */
export function mockNotifications(): PaginatedNotifications {
  const notifications: NotificationItem[] = [
    // 系统通知
    {
      id: 'notif_001',
      user_id: 'user_123',
      title: '支付小助手',
      content: '大会员服务开通成功通知',
      notification_type: 'system',
      related_id: undefined,
      related_type: undefined,
      is_read: false,
      created_at: '2026-01-14T10:30:00Z'
    },
    {
      id: 'notif_002',
      user_id: 'user_123',
      title: '哔哩哔哩智能机',
      content: '登录操作通知',
      notification_type: 'system',
      related_id: undefined,
      related_type: undefined,
      is_read: true,
      created_at: '2026-01-13T15:20:00Z'
    },
    {
      id: 'notif_003',
      user_id: 'user_123',
      title: '系统通知',
      content: '哔哩哔哩防沉迷订阅通知',
      notification_type: 'system',
      related_id: undefined,
      related_type: undefined,
      is_read: true,
      created_at: '2025-05-07T09:15:00Z'
    },

    // 订阅通知
    {
      id: 'notif_004',
      user_id: 'user_123',
      title: 'Allen老师前端技术分享',
      content: '[自动回复] 感谢你的关注，要想快速找到我...',
      notification_type: 'subscription',
      related_id: 'session_001',
      related_type: 'session',
      is_read: false,
      created_at: '2025-07-25T14:30:00Z'
    },
    {
      id: 'notif_005',
      user_id: 'user_123',
      title: '程序员鱼皮',
      content: '[自动回复] 感谢关注鱼皮，前大厂程序员...',
      notification_type: 'subscription',
      related_id: 'room_001',
      related_type: 'room',
      is_read: false,
      created_at: '2025-07-24T16:45:00Z'
    },
    {
      id: 'notif_006',
      user_id: 'user_123',
      title: 'vue3入门到精通',
      content: '[自动回复] 感谢关注，资料地址：https://...',
      notification_type: 'subscription',
      related_id: 'session_002',
      related_type: 'session',
      is_read: true,
      created_at: '2025-07-23T11:20:00Z'
    },

    // 互动通知
    {
      id: 'notif_007',
      user_id: 'user_123',
      title: '医学直播间互动',
      content: '您在"心血管外科手术演示"直播中的评论收到了3个赞',
      notification_type: 'interaction',
      related_id: 'session_003',
      related_type: 'session',
      is_read: false,
      created_at: '2026-01-14T08:15:00Z'
    },
    {
      id: 'notif_008',
      user_id: 'user_123',
      title: '专家回复',
      content: '张主任回复了您的提问："这个手术方式确实比较先进..."',
      notification_type: 'interaction',
      related_id: 'expert_001',
      related_type: 'expert',
      is_read: false,
      created_at: '2026-01-13T20:30:00Z'
    },
    {
      id: 'notif_009',
      user_id: 'user_123',
      title: '新增关注',
      content: '李医生关注了您，快去看看TA的直播吧',
      notification_type: 'interaction',
      related_id: 'expert_002',
      related_type: 'expert',
      is_read: true,
      created_at: '2026-01-12T14:20:00Z'
    },

    // 更多系统通知
    {
      id: 'notif_010',
      user_id: 'user_123',
      title: '平台维护通知',
      content: '系统将于今晚22:00-24:00进行维护升级，期间可能影响部分功能使用',
      notification_type: 'system',
      related_id: undefined,
      related_type: undefined,
      is_read: true,
      created_at: '2026-01-10T18:00:00Z'
    },
    {
      id: 'notif_011',
      user_id: 'user_123',
      title: '新功能上线',
      content: '直播回放功能已上线，您可以随时回看错过的精彩内容',
      notification_type: 'system',
      related_id: undefined,
      related_type: undefined,
      is_read: true,
      created_at: '2026-01-08T10:00:00Z'
    },

    // 更多订阅通知
    {
      id: 'notif_012',
      user_id: 'user_123',
      title: '订阅提醒',
      content: '您订阅的"神经外科手术直播"将在30分钟后开始',
      notification_type: 'subscription',
      related_id: 'session_004',
      related_type: 'session',
      is_read: false,
      created_at: '2026-01-14T09:30:00Z'
    },
    {
      id: 'notif_013',
      user_id: 'user_123',
      title: '直播预告',
      content: '明天上午10:00，著名心外科专家将进行"微创心脏手术"直播演示',
      notification_type: 'subscription',
      related_id: 'session_005',
      related_type: 'session',
      is_read: false,
      created_at: '2026-01-13T17:00:00Z'
    }
  ]

  return {
    total: notifications.length,
    page: 1,
    size: 20,
    items: notifications
  }
}

/**
 * 生成特定类型的Mock通知数据
 */
export function mockNotificationsByType(type: 'system' | 'subscription' | 'interaction'): PaginatedNotifications {
  const allNotifications = mockNotifications()
  const filteredItems = allNotifications.items.filter(item => item.notification_type === type)
  
  return {
    total: filteredItems.length,
    page: 1,
    size: 20,
    items: filteredItems
  }
}

/**
 * 生成未读通知数量统计
 */
export function mockUnreadCounts() {
  const notifications = mockNotifications().items
  
  return {
    all: notifications.filter(item => !item.is_read).length,
    system: notifications.filter(item => item.notification_type === 'system' && !item.is_read).length,
    subscription: notifications.filter(item => item.notification_type === 'subscription' && !item.is_read).length,
    interaction: notifications.filter(item => item.notification_type === 'interaction' && !item.is_read).length
  }
}

/**
 * 模拟标记通知为已读
 */
export function mockMarkAsRead(notificationId: string): boolean {
  console.log(`[Mock] 标记通知 ${notificationId} 为已读`)
  return true
}

/**
 * 模拟标记所有通知为已读
 */
export function mockMarkAllAsRead(): boolean {
  console.log('[Mock] 标记所有通知为已读')
  return true
}
