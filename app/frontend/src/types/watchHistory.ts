/**
 * 观看历史相关类型定义
 * @module types/watchHistory
 */

/**
 * 观看历史记录项
 */
export interface WatchHistoryItem {
  /** 记录ID */
  id: string
  /** 场次ID */
  session_id: string
  /** 直播间ID */
  room_id?: string
  /** 直播标题 */
  title?: string
  /** 封面URL */
  cover_url?: string
  /** 专家名称 */
  expert_name?: string
  /** 观看时间（ISO 8601格式） */
  watched_at: string
  /** 观看进度（秒） */
  progress?: number
  /** 视频总时长（秒） */
  duration?: number
  /** 场次状态（后端枚举：scheduled/live/finished/processing/ready/error） */
  status?: string
  
  // 后端返回的字段（通过JOIN获取）
  /** 场次标题（后端返回） */
  session_title?: string
  /** 房间标题（后端返回） */
  room_title?: string
  /** 房间封面URL（后端返回） */
  room_cover_url?: string
  
  // 前端扩展字段（后端聚合返回）
  /** 专家职称 */
  expert_title?: string
  /** 专家头像 */
  expert_avatar?: string
  /** 专家医院 */
  expert_hospital?: string
}

/**
 * 分组的观看历史
 */
export interface GroupedHistory {
  /** 分组标题：今天/昨天/更早 */
  date: string
  /** 分组标签（用于显示） */
  dateLabel?: string
  /** 该分组的历史记录 */
  items: WatchHistoryItem[]
}
