/**
 * 通知相关类型定义
 * @module types/notification
 */

/**
 * 通知类型枚举
 */
export type NotificationType = 'system' | 'subscription' | 'interaction'

/**
 * 关联资源类型
 */
export type RelatedType = 'room' | 'session' | 'expert' | 'brand'

/**
 * 通知项
 */
export interface NotificationItem {
  /** 通知ID */
  id: string
  /** 接收通知的用户ID */
  user_id: string
  /** 通知标题 */
  title: string
  /** 通知内容 */
  content?: string
  /** 通知类型：system=系统通知, subscription=订阅通知, interaction=互动通知 */
  notification_type: NotificationType
  /** 关联资源ID */
  related_id?: string
  /** 关联资源类型 */
  related_type?: RelatedType
  /** 是否已读 */
  is_read: boolean
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 通知类型（模板展示用，与 notification_type 对齐） */
  type?: string
  /** 通知附带数据（跳转用，如 session_id / room_id） */
  extra?: {
    session_id?: string
    room_id?: string
    [key: string]: unknown
  }
}

/**
 * 创建通知请求（对齐后端 POST /admin/notifications：user_ids 必填数组，后端不支持"全站推送"）
 */
export interface CreateNotificationRequest {
  /** 接收通知的用户ID列表（必填，后端不支持空列表=全站） */
  user_ids: string[]
  /** 通知标题 */
  title: string
  /** 通知内容 */
  content?: string
  /** 通知类型 */
  notification_type?: NotificationType
  /** 关联资源ID */
  related_id?: string
  /** 关联资源类型 */
  related_type?: RelatedType
}

/**
 * 通知列表查询参数
 */
export interface NotificationListParams {
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 排序规则 */
  sort?: string
  /** 筛选已读/未读 */
  is_read?: boolean
  /** 按类型筛选 */
  notification_type?: NotificationType
}

/**
 * 未读通知数量统计
 */
export interface UnreadCounts {
  /** 全部未读数量 */
  all: number
  /** 系统通知未读数量 */
  system: number
  /** 订阅通知未读数量 */
  subscription: number
  /** 互动通知未读数量 */
  interaction: number
}

/**
 * 分页响应
 */
export interface PaginatedNotifications {
  /** 总数 */
  total: number
  /** 当前页 */
  page: number
  /** 每页数量 */
  size: number
  /** 通知列表 */
  items: NotificationItem[]
}

/**
 * 通知分页信息
 */
export interface NotificationPagination {
  /** 当前页 */
  page: number
  /** 每页数量 */
  size: number
  /** 总数 */
  total: number
  /** 是否还有更多 */
  hasMore: boolean
}

/**
 * 通知Store状态
 */
export interface NotificationState {
  /** 当前通知列表 */
  currentList: NotificationItem[]
  /** 加载状态 */
  loading: boolean
  /** 分页信息 */
  pagination: NotificationPagination
  /** 当前激活的标签 */
  activeTab: 'all' | 'system' | 'subscription' | 'interaction'
  /** 总未读数量 */
  unreadCount: number
  /** 各类型未读数量 */
  unreadCounts: UnreadCounts
  /** 轮询定时器ID */
  pollingTimer: number | null
}
