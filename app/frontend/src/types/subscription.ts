/**
 * 订阅相关类型定义
 * @module types/subscription
 */

/**
 * 订阅目标类型
 */
export type SubscriptionTargetType = 'room' | 'session'

/**
 * 基础订阅记录（对应数据库表 user_subscriptions）
 */
export interface Subscription {
  /** 订阅ID */
  id: string
  /** 用户ID */
  user_id: string
  /** 订阅目标类型 */
  target_type: SubscriptionTargetType
  /** 目标ID（房间ID或场次ID） */
  target_id: string
  /** 是否有效 */
  is_active: boolean
  /** 订阅时间 */
  created_at: string
}

/**
 * 场次基本信息（后端返回的嵌套对象）
 */
export interface SessionInfo {
  /** 场次ID */
  id: string
  /** 场次标题 */
  title: string
  /** 开始时间（ISO 8601格式） */
  start_time: string
  /** 结束时间（ISO 8601格式） */
  end_time: string
  /** 场次状态 */
  status: 'scheduled' | 'live' | 'ended' | 'cancelled'
  /** 封面URL（可选） */
  cover_url?: string
}

/**
 * 订阅列表项（前端展示用，包含关联的房间和场次信息）
 * 卡片字段（title/cover_url/status/expert_* 等）由后端聚合返回，无真实数据时为 null
 */
export interface SubscriptionWithTarget extends Subscription {
  /** 房间标题（后端聚合返回，可能为 null） */
  room_title?: string
  /** 房间封面URL（后端聚合返回，可能为 null） */
  room_cover_url?: string
  /** 下一场次信息（🆕后端需要新增） */
  next_session?: SessionInfo
  /** 是否已发送开播通知（🆕后端需要新增字段） */
  is_notified?: boolean
  /** 用户是否已读通知（🆕后端需要新增字段） */
  is_read?: boolean
  
  // 卡片展示字段（由后端聚合填充）
  /** 标题（房间订阅取房间标题，场次订阅取场次标题） */
  title?: string
  /** 封面URL */
  cover_url?: string
  /** 状态（场次状态） */
  status?: string
  /** 专家姓名 */
  expert_name?: string
  /** 专家职称 */
  expert_title?: string
  /** 专家头像 */
  expert_avatar?: string
  /** 专家医院 */
  expert_hospital?: string
}

/**
 * 分组订阅列表（前端使用）
 */
export interface GroupedSubscriptions {
  /** 待开播（start_time > now && status='scheduled'） */
  pending: SubscriptionWithTarget[]
  /** 已通知（is_notified=true 或 status='live'） */
  notified: SubscriptionWithTarget[]
  /** 已过期（end_time < now && status='ended'） */
  expired: SubscriptionWithTarget[]
}
