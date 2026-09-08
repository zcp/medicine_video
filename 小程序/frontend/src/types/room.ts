/**
 * 房间相关类型定义
 * 包含直播房间、场次、观众等相关类型定义
 */

import { BaseEntity, StatsData } from './common'

/**
 * 房间状态
 */
export type RoomStatus = 'scheduled' | 'live' | 'ended' | 'cancelled'

/**
 * 房间类型
 */
export type RoomType = 'public' | 'private' | 'premium' | 'vip'

/**
 * 直播质量
 */
export type StreamQuality = 'auto' | 'low' | 'medium' | 'high' | 'ultra'

/**
 * 房间权限
 */
export type RoomPermission = 'view' | 'comment' | 'interact' | 'manage'

/**
 * 分类简要信息（遵循文档规范）
 */
export interface CategoryBrief {
  /** 分类ID */
  id: string
  /** 分类名称 */
  name: string
  /** 分类图标 */
  icon?: string
  /** 分类slug（详情接口使用） */
  slug?: string
}

/**
 * 直播房间信息
 * 遵循《后端新增api接口和模块设计文档-v2.md》4.11.2节规范
 */
export interface Room extends BaseEntity {
  /** 房间标题 */
  title: string
  /** 房间描述 */
  description: string
  /** 直播间简介摘要，用于卡片展示（遵循文档规范） */
  summary?: string
  /** 分类信息（遵循文档规范） */
  category?: CategoryBrief
  /** 分类ID（用于创建/更新） */
  category_id?: string
  /** 主分类展示名（多对多权威；无则空，勿硬编码假名） */
  primary_category_name?: string | null
  /** 主分类 ID（可选） */
  primary_category_id?: string | null
  /** 封面图 */
  coverImage: string
  /** 房间状态 */
  status: RoomStatus
  /** 房间类型 */
  type: RoomType
  /** 专家ID */
  expertId: string
  /** 专家信息 */
  expertInfo: {
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    department: string
    isVerified: boolean
  }
  /** 科室ID */
  departmentId: string
  /** 科室名称 */
  departmentName: string
  /** 标签列表 */
  tags: string[]
  /** 预计开始时间 */
  scheduledStartAt: string
  /** 预计结束时间 */
  scheduledEndAt: string
  /** 实际开始时间 */
  actualStartAt?: string
  /** 实际结束时间 */
  actualEndAt?: string
  /** 房间密码 */
  password?: string
  /** 最大观众数 */
  maxViewers: number
  /** 当前观众数 */
  currentViewers: number
  /** 是否允许评论 */
  allowComments: boolean
  /** 是否允许互动 */
  allowInteraction: boolean
  /** 是否录制 */
  isRecorded: boolean
  /** 录制文件URL */
  recordUrl?: string
  /** 推流地址 */
  streamUrl?: string
  /** 拉流地址 */
  playUrl?: string
  /** 统计数据 */
  stats: RoomStats
}

/**
 * 房间统计数据
 */
export interface RoomStats extends StatsData {
  /** 累计观看人数 */
  totalViewers: number
  /** 峰值观看人数 */
  peakViewers: number
  /** 平均观看时长 */
  avgWatchTime: number
  /** 互动数 */
  interactionCount: number
  /** 弹幕数 */
  danmuCount: number
}

/**
 * 创建房间请求
 * 遵循《后端新增api接口和模块设计文档-v2.md》4.11.2节规范
 */
export interface CreateRoomRequest {
  /** 房间标题 */
  title: string
  /** 房间描述 */
  description: string
  /** 直播间简介摘要，用于卡片展示（遵循文档规范） */
  summary?: string
  /** 分类ID（遵循文档规范：category_id） */
  category_id?: string
  /** 是否默认录制（遵循 v6 文档字段名） */
  record_by_default?: boolean
  /** 是否私密（对齐后端 LiveRoomUpdate；创建时可选） */
  is_private?: boolean
  /**
   * 封面 URL（对齐后端 LiveRoomCreate.cover_url）
   * 可为相对路径 `/media/...` 或绝对 `https?://` 外链；本地文件请走 uploadRoomCover
   */
  cover_url?: string
}

/**
 * 更新房间请求（部分更新 PATCH）
 */
export type UpdateRoomRequest = Partial<CreateRoomRequest>

/**
 * POST /rooms/{正式间id}/test-room 响应 data（对齐《18》后端）
 */
export interface TestRoomPayload {
  source_room_id: string
  test_room: {
    id: string
    title: string
    is_private: boolean
    stream_key: string
    cover_url?: string | null
    created_at?: string
  }
  created: boolean
}

/**
 * 房间场次信息
 */
export interface RoomSession extends BaseEntity {
  /** 房间ID */
  roomId: string
  /** 场次标题 */
  title: string
  /** 场次描述 */
  description: string
  /** 专家ID */
  expertId: string
  /** 开始时间 */
  startAt: string
  /** 结束时间 */
  endAt: string
  /** 场次状态 */
  status: 'scheduled' | 'live' | 'ended' | 'cancelled'
  /** 观看人数 */
  viewerCount: number
  /** 录制URL */
  recordUrl?: string
  /** 场次统计 */
  stats: SessionStats
}

/**
 * 场次统计数据
 */
export interface SessionStats {
  /** 观看人数 */
  viewerCount: number
  /** 观看时长 */
  duration: number
  /** 互动数 */
  interactionCount: number
  /** 评论数 */
  commentCount: number
  /** 点赞数 */
  likeCount: number
}

/**
 * 房间观众信息
 */
export interface RoomViewer extends BaseEntity {
  /** 房间ID */
  roomId: string
  /** 用户ID */
  userId: string
  /** 用户信息 */
  userInfo: {
    id: string
    nickname: string
    avatar: string
    level: string
  }
  /** 进入时间 */
  joinedAt: string
  /** 离开时间 */
  leftAt?: string
  /** 观看时长（秒） */
  watchTime: number
  /** 是否在线 */
  isOnline: boolean
  /** 权限 */
  permissions: RoomPermission[]
}

/**
 * 房间评论
 */
export interface RoomComment extends BaseEntity {
  /** 房间ID */
  roomId: string
  /** 用户ID */
  userId: string
  /** 用户信息 */
  userInfo: {
    id: string
    nickname: string
    avatar: string
  }
  /** 评论内容 */
  content: string
  /** 父评论ID */
  parentId?: string
  /** 点赞数 */
  likeCount: number
  /** 是否置顶 */
  isPinned: boolean
  /** 是否被删除 */
  isDeleted: boolean
}

/**
 * 房间弹幕
 */
export interface RoomDanmu extends BaseEntity {
  /** 房间ID */
  roomId: string
  /** 用户ID */
  userId: string
  /** 用户昵称 */
  userNickname: string
  /** 弹幕内容 */
  content: string
  /** 弹幕类型 */
  type: 'normal' | 'gift' | 'system'
  /** 颜色 */
  color: string
  /** 位置 */
  position: 'top' | 'bottom' | 'scroll'
  /** 时间点（秒） */
  timestamp: number
}

/**
 * 房间互动消息
 */
export interface RoomInteraction extends BaseEntity {
  /** 房间ID */
  roomId: string
  /** 用户ID */
  userId: string
  /** 用户信息 */
  userInfo: {
    id: string
    nickname: string
    avatar: string
  }
  /** 互动类型 */
  type: 'like' | 'gift' | 'question' | 'applause'
  /** 互动内容 */
  content: string
  /** 附加数据 */
  metadata?: Record<string, any>
}

/**
 * 房间设置
 */
export interface RoomSettings {
  /** 是否允许评论 */
  allowComments: boolean
  /** 是否允许弹幕 */
  allowDanmu: boolean
  /** 是否允许互动 */
  allowInteraction: boolean
  /** 评论审核 */
  commentModeration: boolean
  /** 弹幕审核 */
  danmuModeration: boolean
  /** 禁言用户列表 */
  mutedUsers: string[]
  /** 拉黑用户列表 */
  blockedUsers: string[]
  /** 房间公告 */
  announcement?: string
}

/**
 * 房间搜索参数
 */
export interface RoomSearchParams {
  /** 关键词 */
  keyword?: string
  /** 科室ID */
  departmentId?: string
  /** 专家ID */
  expertId?: string
  /** 房间状态 */
  status?: RoomStatus
  /** 房间类型 */
  type?: RoomType
  /** 标签 */
  tags?: string[]
  /** 排序字段 */
  sortBy?: 'created' | 'viewers' | 'likes' | 'start_time'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
  /** 分页 */
  page?: number
  size?: number
}

/**
 * 直播房间（别名，API兼容性）
 */
export interface LiveRoom extends Room {}

/**
 * Tab数据结构（对应后端 LiveRoomTabItem Schema）
 * DDL: id, room_id, tab_key, title, content_type, text_content, image_url, sort_order, is_active, created_at, updated_at
 */
export interface Tab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: 'text' | 'image' | 'mixed'
  text_content?: string | null
  image_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 兼容别名：历史代码中使用 RoomTab
 */
export type RoomTab = Tab

/**
 * 直播房间详情（扩展信息）
 */
export interface LiveRoomDetail extends Room {
  /**
   * Tab列表（遵循设计文档：GET /api/v1/rooms/{room_id} 返回）
   * 若未配置 Tab，必须返回空数组 []
   */
  tabs: Tab[]
  /** 主播详细信息 */
  hostDetail: {
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    department: string
    isVerified: boolean
    followerCount: number
    experience: string
    rating: number
  }
  /** 实时数据 */
  realTimeData: {
    currentViewers: number
    totalMessages: number
    likes: number
    duration: number
    quality: StreamQuality
  }
  /** 相关推荐 */
  relatedRooms: Array<{
    id: string
    title: string
    thumbnail: string
    hostName: string
    viewerCount: number
    status: RoomStatus
  }>
  /** 直播历史 */
  previousSessions: Array<{
    id: string
    title: string
    startTime: string
    endTime: string
    viewerCount: number
    duration: number
  }>
}

/**
 * 房间列表查询参数
 */
export interface RoomListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 状态筛选 */
  status?: RoomStatus
  /** 类型筛选 */
  type?: RoomType
  /** 科室ID */
  departmentId?: string
  /** 专家ID */
  expertId?: string
  /** 关键词搜索 */
  keyword?: string
  /** 标签筛选 */
  tags?: string[]
  /** 排序字段 */
  sortBy?: 'createdAt' | 'scheduledStartAt' | 'currentViewers' | 'totalViewers'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 房间搜索查询参数
 */
export interface RoomSearchQuery extends RoomListQuery {
  /** 最小观看人数 */
  minViewers?: number
  /** 最大观看人数 */
  maxViewers?: number
  /** 直播时长范围（分钟） */
  durationRange?: [number, number]
  /** 开始时间范围 */
  startTimeRange?: [string, string]
  /** 是否正在直播 */
  isLive?: boolean
  /** 是否有回放 */
  hasReplay?: boolean
}

/**
 * 房间消息
 */
export interface RoomMessage {
  id: string
  roomId: string
  userId: string
  userInfo: {
    nickname: string
    avatar: string
    level: number
    isVip: boolean
  }
  messageType: 'text' | 'image' | 'gif' | 'system' | 'gift'
  content: string
  timestamp: string
  isDeleted: boolean
  replyTo?: {
    messageId: string
    userNickname: string
  }
}


/**
 * 房间统计数据
 */
export interface RoomStatistics {
  totalRooms: number
  liveRooms: number
  totalViewers: number
  peakViewers: number
  totalDuration: number
  totalMessages: number
  averageWatchTime: number
  roomsByStatus: Record<RoomStatus, number>
  roomsByType: Record<RoomType, number>
  topRooms: Array<{
    id: string
    title: string
    hostName: string
    viewerCount: number
    duration: number
    rating: number
  }>
  viewerTrends: Array<{
    date: string
    totalViewers: number
    peakViewers: number
    newViewers: number
  }>
  popularTimes: Array<{
    hour: number
    averageViewers: number
  }>
}

/**
 * 推流配置（别名，API兼容性）
 */
export interface StreamConfig extends RoomStreamConfig {}

/**
 * 房间直播配置
 */
export interface RoomStreamConfig {
  /** 推流密钥 */
  streamKey: string
  /** 推流地址 */
  pushUrl: string
  /** 播放地址 */
  playUrls: {
    rtmp: string
    hls: string
    flv: string
  }
  /** 录制配置 */
  record: {
    enabled: boolean
    format: 'mp4' | 'flv'
    quality: StreamQuality
  }
  /** 转码配置 */
  transcode: {
    enabled: boolean
    qualities: StreamQuality[]
  }
}
