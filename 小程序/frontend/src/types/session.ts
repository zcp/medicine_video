
// 场次状态枚举
export type SessionStatus = 'scheduled' | 'live' | 'ended' | 'cancelled'

// 标签信息
export interface TagItem {
  id: string
  name: string
}

// 专家简要信息
export interface ExpertBrief {
  id: string
  name: string
  title?: string
  hospital?: string
  avatar_url?: string
}

// 场次详情（主接口返回结构）
export interface SessionDetail {
  id: string
  room_id: string
  summary?: string
  featured_expert?: ExpertBrief
  tags: TagItem[]
  status: SessionStatus
  start_time: string
  /** 回放/播放地址（后端可能返回；LiveView 会从此字段提取播放地址） */
  playback_url?: string
  /** 直播地址（拉流/播放地址之一；直播模式可能使用该字段） */
  stream_url?: string
}

// 场次列表查询参数
export interface SessionListQuery {
  page?: number
  size?: number
  q?: string
  status?: SessionStatus
  // ...existing code...
  room_id?: string
  expert_id?: string
  tag_ids?: string[]
  start_time_from?: string
  start_time_to?: string
  free_only?: boolean
  sort_by?: 'start_time' | 'view_count' | 'like_count' | 'created_at'
  sort_order?: 'asc' | 'desc'
}

// 创建场次请求
export interface CreateSessionRequest {
  summary?: string
  featured_expert_id?: string
  start_time: string
  room_id: string
  tags?: string[]
}

// 更新场次请求
export interface UpdateSessionRequest {
  summary?: string
  featured_expert_id?: string
  start_time?: string
  room_id?: string
  tags?: string[]
  /** 回放/播放地址（回放模式需要） */
  playback_url?: string
  /** 直播地址（直播模式：后端拉流） */
  stream_url?: string
}

/**
 * 标签信息（遵循文档规范）
 */
export interface TagItem {
  /** 标签ID */
  id: string
  /** 标签名称 */
  name: string
}

/**
 * 专家简要信息（遵循文档规范）
 */
export interface ExpertBrief {
  /** 专家ID */
  id: string
  /** 专家姓名 */
  name: string
  /** 职称 */
  title?: string
  /** 所属医院 */
  hospital?: string
  /** 头像URL */
  avatar_url?: string
}

/**
 * 场次详情（完全遵循《后端新增api接口和模块设计文档-v2.md》4.11.1节返回结构）
 */
export interface SessionDetail {
  /** 场次ID */
  id: string
  /** 房间ID */
  room_id: string
  /** 场次摘要 */
  summary?: string
  /** 特邀专家 */
  featured_expert?: ExpertBrief
  /** 标签列表 */
  tags: TagItem[]
  /** 场次状态 */
  status: SessionStatus
  /** 开始时间 */
  start_time: string
  /** 回放/播放地址（回放模式） */
  playback_url?: string
  /** 直播地址（直播模式：后端拉流） */
  stream_url?: string
  /** 其他字段可根据后端补充 */
}

// 兼容别名：部分模块引用 `Session`
export type Session = SessionDetail

/**
 * 场次列表查询参数
 */
export interface SessionListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 关键词搜索 */
  q?: string
  /** 场次状态 */
  status?: SessionStatus
  // ...existing code...
  /** 房间ID */
  room_id?: string
  /** 专家ID */
  expert_id?: string
  /** 标签ID列表（逗号分隔字符串或数组，具体以后端为准） */
  tag_ids?: string[]
  /** 开始时间范围 */
  start_time_from?: string
  /** 结束时间范围 */
  start_time_to?: string
  /** 是否只看免费 */
  free_only?: boolean
  /** 排序字段 */
  sort_by?: 'start_time' | 'view_count' | 'like_count' | 'created_at'
  /** 排序方向 */
  sort_order?: 'asc' | 'desc'
}

// ...existing code...

// ...existing code...

/**
 * 场次统计数据
 */
export interface SessionStatistics {
  /** 总场次数 */
  totalCount: number
  /** 进行中场次数 */
  liveCount: number
  /** 预约场次数 */
  scheduledCount: number
  /** 已结束场次数 */
  endedCount: number
  /** 总观看人数 */
  totalViewCount: number
  /** 总点赞数 */
  totalLikeCount: number
  /** 平均观看时长（分钟） */
  averageWatchDuration: number
  /** 按日期分组的统计 */
  dailyStats: Array<{
    date: string
    sessionCount: number
    viewCount: number
    likeCount: number
  }>
}

/**
 * 场次预约记录
 */
export interface SessionReservation extends BaseEntity {
  /** 场次ID */
  sessionId: string
  /** 用户ID */
  userId: string
  /** 预约时间 */
  reservationTime: string
  /** 预约状态 */
  status: 'active' | 'cancelled'
  /** 取消时间 */
  cancelledAt?: string
  /** 取消原因 */
  cancelReason?: string
}

/**
 * 场次预约请求
 */
export interface CreateReservationRequest {
  /** 场次ID */
  sessionId: string
  /** 备注 */
  note?: string
}

/**
 * 场次观看记录
 */
export interface SessionWatchRecord extends BaseEntity {
  /** 场次ID */
  sessionId: string
  /** 用户ID */
  userId: string
  /** 开始观看时间 */
  startTime: string
  /** 结束观看时间 */
  endTime?: string
  /** 观看时长（秒） */
  duration: number
  /** 观看进度（百分比） */
  progress: number
  /** 最后观看位置（秒） */
  lastPosition: number
  /** 设备信息 */
  deviceInfo?: string
}

/**
 * 场次互动统计
 */
export interface SessionInteractionStats {
  /** 场次ID */
  sessionId: string
  /** 实时观看人数 */
  liveViewerCount: number
  /** 累计观看人数 */
  totalViewerCount: number
  /** 点赞数 */
  likeCount: number
  /** 评论数 */
  commentCount: number
  /** 分享数 */
  shareCount: number
  /** 提问数 */
  questionCount: number
  /** 互动率 */
  engagementRate: number
}
