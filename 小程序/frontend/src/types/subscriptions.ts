/**
 * 订阅提醒类型定义
 * 包含用户订阅、提醒设置等类型定义
 */

import { BaseEntity } from './common'

/**
 * 订阅类型
 */
export type SubscriptionType = 'expert' | 'department' | 'room' | 'tag'

/**
 * 提醒频率
 */
export type ReminderFrequency = 'immediate' | 'daily' | 'weekly' | 'never'

/**
 * 订阅信息
 */
export interface Subscription extends BaseEntity {
  /** 用户ID */
  userId: string
  /** 订阅类型 */
  type: SubscriptionType
  /** 目标ID */
  targetId: string
  /** 目标信息 */
  targetInfo: {
    name: string
    avatar?: string
    description?: string
  }
  /** 提醒设置 */
  reminders: {
    liveStart: ReminderFrequency
    newContent: ReminderFrequency
    updates: ReminderFrequency
  }
  /** 是否活跃 */
  isActive: boolean
}

/**
 * 房间订阅（room 口径）——与后端当前用户订阅列表返回一致的最小字段集合
 */
export interface RoomSubscription extends BaseEntity {
  id: string
  /** 订阅的房间 ID */
  room_id: string
  /** 订阅时保留的房间标题（可选） */
  room_title?: string
  /** 房间封面 URL（可选） */
  room_cover_url?: string
  /** 若订阅来源为 session，则保留 session id（兼容） */
  session_id?: string
  created_at: string
}

/**
 * 订阅列表查询参数
 */
export interface SubscriptionListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 订阅类型筛选 */
  type?: SubscriptionType
  /** 是否活跃 */
  isActive?: boolean
  /** 目标ID */
  targetId?: string
  /** 关键词搜索 */
  keyword?: string
  /** 排序字段 */
  sortBy?: 'createdAt' | 'updatedAt' | 'targetName'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 创建订阅请求
 */
export interface CreateSubscriptionRequest {
  /** 订阅类型 */
  type: SubscriptionType
  /**
   * 目标ID（旧口径）——保留以兼容非房间泛用订阅
   * 优先使用 `room_id` 字段进行房间订阅请求（后端契约优先）
   */
  targetId?: string
  /** 房间订阅专用字段（优先使用） */
  room_id?: string
  /** 提醒设置 */
  reminders?: {
    liveStart?: ReminderFrequency
    newContent?: ReminderFrequency
    updates?: ReminderFrequency
  }
  /** 自定义标签 */
  customTags?: string[]
  /** 备注 */
  note?: string
}

/**
 * 更新订阅请求
 */
export interface UpdateSubscriptionRequest {
  /** 订阅ID */
  subscriptionId: string
  /** 提醒设置 */
  reminders?: {
    liveStart?: ReminderFrequency
    newContent?: ReminderFrequency
    updates?: ReminderFrequency
  }
  /** 是否活跃 */
  isActive?: boolean
  /** 自定义标签 */
  customTags?: string[]
  /** 备注 */
  note?: string
}

/**
 * 订阅提醒（别名，API兼容性）
 */
export interface SubscriptionReminder extends ReminderRecord {}

/**
 * 订阅统计数据
 */
export interface SubscriptionStatistics {
  /** 总订阅数 */
  totalSubscriptions: number
  /** 活跃订阅数 */
  activeSubscriptions: number
  /** 按类型统计 */
  subscriptionsByType: Record<SubscriptionType, number>
  /** 热门订阅目标 */
  popularTargets: Array<{
    targetId: string
    targetName: string
    type: SubscriptionType
    subscriberCount: number
  }>
  /** 订阅趋势 */
  subscriptionTrend: Array<{
    date: string
    newSubscriptions: number
    canceledSubscriptions: number
    totalActive: number
  }>
  /** 提醒统计 */
  reminderStats: {
    totalSent: number
    delivered: number
    clicked: number
    deliveryRate: number
    clickRate: number
  }
  /** 用户活跃度 */
  userActivity: {
    dailyActiveSubscribers: number
    weeklyActiveSubscribers: number
    monthlyActiveSubscribers: number
  }
}

/**
 * 提醒设置
 */
export interface ReminderSettings {
  /** 全局提醒开关 */
  enabled: boolean
  /** 推送方式 */
  methods: {
    push: boolean
    email: boolean
    sms: boolean
    inApp: boolean
  }
  /** 免打扰时间 */
  quietHours: {
    enabled: boolean
    start: string
    end: string
  }
  /** 频率限制 */
  rateLimit: {
    maxPerHour: number
    maxPerDay: number
  }
  /** 个性化设置 */
  personalization: {
    smartTiming: boolean
    contentFiltering: boolean
    priorityBased: boolean
  }
}

/**
 * 提醒记录
 */
export interface ReminderRecord extends BaseEntity {
  subscriptionId: string
  userId: string
  type: 'live_start' | 'new_content' | 'update'
  content: string
  sentAt: string
  isDelivered: boolean
  clickedAt?: string
}

/**
 * 订阅分组
 */
export interface SubscriptionGroup {
  id: string
  name: string
  description?: string
  color: string
  subscriptionIds: string[]
  userId: string
  isDefault: boolean
  createdAt: string
  updatedAt: string
}

/**
 * 批量订阅操作请求
 */
export interface BatchSubscriptionRequest {
  /** 操作类型 */
  action: 'subscribe' | 'unsubscribe' | 'activate' | 'deactivate' | 'updateReminders'
  /** 目标列表 */
  targets?: Array<{
    type: SubscriptionType
    targetId: string
  }>
  /** 订阅ID列表（取消订阅时使用） */
  subscriptionIds?: string[]
  /** 新的提醒设置（批量更新时使用） */
  reminders?: {
    liveStart?: ReminderFrequency
    newContent?: ReminderFrequency
    updates?: ReminderFrequency
  }
}

/**
 * 订阅推荐
 */
export interface SubscriptionRecommendation {
  /** 推荐订阅列表 */
  recommendations: Array<{
    type: SubscriptionType
    targetId: string
    targetInfo: {
      name: string
      avatar?: string
      description?: string
    }
    score: number
    reason: string
    category: string
  }>
  /** 推荐算法 */
  algorithm: 'collaborative' | 'content' | 'trending' | 'hybrid'
  /** 推荐时间 */
  timestamp: string
}
