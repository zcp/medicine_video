/**
 * 观看历史类型定义
 * 包含用户观看记录、学习进度等类型定义
 */

import { BaseEntity } from './common'

/**
 * 观看历史
 */
export interface WatchHistory extends BaseEntity {
  /** 用户ID */
  userId: string
  /** 房间ID */
  roomId: string
  /** 房间信息 */
  roomInfo: {
    title: string
    cover: string
    expertName: string
    department: string
  }
  /** 观看时长（秒） */
  watchDuration: number
  /** 总时长（秒） */
  totalDuration: number
  /** 观看进度 */
  progress: number
  /** 最后观看位置（秒） */
  lastPosition: number
  /** 是否看完 */
  isCompleted: boolean
  /** 设备信息 */
  deviceInfo: string
}

/**
 * 观看历史（别名，API兼容性）
 */
export interface ViewHistory extends WatchHistory {}

/**
 * 历史列表查询参数
 */
export interface HistoryListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 房间类型筛选 */
  roomType?: 'live' | 'replay'
  /** 科室筛选 */
  departmentId?: string
  /** 专家筛选 */
  expertId?: string
  /** 关键词搜索 */
  keyword?: string
  /** 开始时间 */
  startTime?: string
  /** 结束时间 */
  endTime?: string
  /** 是否已完成 */
  isCompleted?: boolean
  /** 排序字段 */
  sortBy?: 'createdAt' | 'watchDuration' | 'progress'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 创建历史记录请求
 */
export interface CreateHistoryRequest {
  /** 房间ID */
  roomId: string
  /** 观看时长（秒） */
  watchDuration: number
  /** 总时长（秒） */
  totalDuration: number
  /** 最后观看位置（秒） */
  lastPosition: number
  /** 观看进度 0-1 */
  progress: number
  /** 是否看完 */
  isCompleted?: boolean
  /** 设备信息 */
  deviceInfo?: string
  /** 播放质量 */
  quality?: 'low' | 'medium' | 'high' | 'ultra'
  /** 观看来源 */
  source?: 'direct' | 'search' | 'recommendation' | 'share'
}

/**
 * 更新历史记录请求
 */
export interface UpdateHistoryRequest {
  /** 历史记录ID */
  historyId: string
  /** 观看时长（秒） */
  watchDuration?: number
  /** 最后观看位置（秒） */
  lastPosition?: number
  /** 观看进度 0-1 */
  progress?: number
  /** 是否看完 */
  isCompleted?: boolean
}

/**
 * 历史统计数据
 */
export interface HistoryStatistics {
  /** 总观看记录数 */
  totalRecords: number
  /** 总观看时长（秒） */
  totalWatchTime: number
  /** 平均观看时长（秒） */
  averageWatchTime: number
  /** 已完成观看数 */
  completedCount: number
  /** 完成率 */
  completionRate: number
  /** 最活跃科室 */
  topDepartments: Array<{
    departmentId: string
    departmentName: string
    watchTime: number
    recordCount: number
  }>
  /** 最喜欢的专家 */
  topExperts: Array<{
    expertId: string
    expertName: string
    watchTime: number
    recordCount: number
  }>
  /** 观看趋势 */
  watchTrend: Array<{
    date: string
    watchTime: number
    recordCount: number
  }>
  /** 设备分布 */
  deviceDistribution: Record<string, number>
  /** 观看时段分布 */
  timeDistribution: Array<{
    hour: number
    watchTime: number
    recordCount: number
  }>
}

/**
 * 观看进度（别名，API兼容性）
 */
export interface WatchProgress extends LearningProgress {}

/**
 * 学习进度
 */
export interface LearningProgress {
  userId: string
  totalWatchTime: number
  completedSessions: number
  currentStreak: number
  longestStreak: number
  avgDailyTime: number
}

/**
 * 批量历史记录操作请求
 */
export interface BatchHistoryRequest {
  /** 操作类型 */
  action: 'delete' | 'mark_completed' | 'export'
  /** 历史记录ID列表 */
  historyIds: string[]
  /** 导出格式（仅当action为export时） */
  exportFormat?: 'json' | 'csv' | 'pdf'
}

/**
 * 历史记录详情（扩展信息）
 */
export interface HistoryDetail extends WatchHistory {
  /** 相关推荐 */
  recommendations: Array<{
    roomId: string
    title: string
    cover: string
    expertName: string
    department: string
    duration: number
    viewCount: number
  }>
  /** 同主题内容 */
  relatedContent: Array<{
    roomId: string
    title: string
    cover: string
    expertName: string
    tags: string[]
  }>
}
