/**
 * 通知类型定义
 * 包含系统通知、推送消息等类型定义
 */

import { BaseEntity } from './common'

/**
 * 通知类型
 */
export type NotificationType = 
  | 'system'      // 系统通知
  | 'live_start'  // 直播开始
  | 'live_end'    // 直播结束
  | 'follow'      // 关注
  | 'like'        // 点赞
  | 'comment'     // 评论
  | 'message'     // 私信
  | 'announcement'// 公告

/**
 * 通知状态
 */
export type NotificationStatus = 'unread' | 'read' | 'deleted'

/**
 * 通知信息
 */
export interface Notification extends BaseEntity {
  /** 接收用户ID */
  userId: string
  /** 通知类型 */
  type: NotificationType
  /** 标题 */
  title: string
  /** 内容 */
  content: string
  /** 相关数据 */
  data?: Record<string, any>
  /** 状态 */
  status: NotificationStatus
  /** 是否已读 */
  isRead: boolean
  /** 阅读时间 */
  readAt?: string
  /** 发送者ID */
  senderId?: string
}

/**
 * 通知列表查询参数
 */
export interface NotificationListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 通知类型筛选 */
  type?: NotificationType
  /** 状态筛选 */
  status?: NotificationStatus
  /** 是否已读 */
  isRead?: boolean
  /** 发送者ID */
  senderId?: string
  /** 开始时间 */
  startTime?: string
  /** 结束时间 */
  endTime?: string
  /** 关键词搜索 */
  keyword?: string
  /** 排序字段 */
  sortBy?: 'createdAt' | 'readAt' | 'type'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 创建通知请求
 */
export interface CreateNotificationRequest {
  /** 接收用户ID或用户ID列表 */
  userIds: string | string[]
  /** 通知类型 */
  type: NotificationType
  /** 标题 */
  title: string
  /** 内容 */
  content: string
  /** 相关数据 */
  data?: Record<string, any>
  /** 是否立即发送 */
  sendImmediately?: boolean
  /** 定时发送时间 */
  scheduledAt?: string
  /** 推送到设备 */
  pushToDevice?: boolean
}

/**
 * 更新通知请求
 */
export interface UpdateNotificationRequest {
  /** 通知ID */
  notificationId: string
  /** 标题 */
  title?: string
  /** 内容 */
  content?: string
  /** 状态 */
  status?: NotificationStatus
  /** 是否已读 */
  isRead?: boolean
  /** 相关数据 */
  data?: Record<string, any>
}

/**
 * 通知设置
 */
export interface NotificationSettings {
  /** 系统通知 */
  systemNotifications: boolean
  /** 直播开始通知 */
  liveStartNotifications: boolean
  /** 关注通知 */
  followNotifications: boolean
  /** 点赞通知 */
  likeNotifications: boolean
  /** 评论通知 */
  commentNotifications: boolean
  /** 私信通知 */
  messageNotifications: boolean
  /** 公告通知 */
  announcementNotifications: boolean
  /** 推送设置 */
  pushSettings: PushSettings
  /** 邮件通知 */
  emailNotifications: boolean
  /** 短信通知 */
  smsNotifications: boolean
  /** 免打扰时间 */
  quietHours: {
    enabled: boolean
    start: string
    end: string
  }
}

/**
 * 推送设置
 */
export interface PushSettings {
  enabled: boolean
  deviceToken: string
  platform: 'ios' | 'android' | 'web'
  timezone: string
  quietHours: {
    start: string
    end: string
  }
}

/**
 * 通知统计数据
 */
export interface NotificationStatistics {
  /** 总通知数 */
  totalNotifications: number
  /** 未读通知数 */
  unreadCount: number
  /** 已读通知数 */
  readCount: number
  /** 按类型统计 */
  notificationsByType: Record<NotificationType, number>
  /** 按状态统计 */
  notificationsByStatus: Record<NotificationStatus, number>
  /** 发送趋势 */
  sendTrend: Array<{
    date: string
    sent: number
    read: number
  }>
  /** 阅读率 */
  readRate: number
  /** 平均阅读时间 */
  averageReadTime: number
  /** 热门通知类型 */
  popularTypes: Array<{
    type: NotificationType
    count: number
    readRate: number
  }>
  /** 设备推送统计 */
  pushStatistics: {
    totalSent: number
    delivered: number
    clicked: number
    deliveryRate: number
    clickRate: number
  }
}

/**
 * 批量通知操作请求
 */
export interface BatchNotificationRequest {
  /** 操作类型 */
  action: 'read' | 'unread' | 'delete' | 'archive'
  /** 通知ID列表 */
  notificationIds: string[]
  /** 批量操作的筛选条件（可选，与IDs二选一） */
  filter?: {
    type?: NotificationType
    status?: NotificationStatus
    dateRange?: {
      start: string
      end: string
    }
  }
}

/**
 * 通知模板
 */
export interface NotificationTemplate {
  id: string
  type: NotificationType
  title: string
  content: string
  variables: string[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}
