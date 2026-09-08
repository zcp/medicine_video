/**
 * 焦点图相关类型定义
 * 包含轮播图、广告位、推广内容等类型定义
 */

import { BaseEntity } from './common'

/**
 * 焦点图类型
 */
export type BannerType = 'carousel' | 'popup' | 'floating' | 'inline'

/**
 * 焦点图状态
 */
export type BannerStatus = 'active' | 'inactive' | 'scheduled' | 'expired'

/**
 * 焦点图信息
 */
export interface Banner extends BaseEntity {
  /** 标题 */
  title: string
  /** 描述 */
  description: string
  /** 图片URL */
  imageUrl: string
  /** 链接URL */
  linkUrl?: string
  /** 链接类型 */
  linkType: 'internal' | 'external' | 'none'
  /** 类型 */
  type: BannerType
  /** 状态 */
  status: BannerStatus
  /** 开始时间 */
  startAt: string
  /** 结束时间 */
  endAt: string
  /** 排序权重 */
  sortOrder: number
  /** 目标用户 */
  targetUsers: string[]
  /** 点击数 */
  clickCount: number
  /** 曝光数 */
  viewCount: number
}

/**
 * 创建焦点图请求
 */
export interface CreateBannerRequest {
  title: string
  description: string
  imageUrl: string
  linkUrl?: string
  linkType: 'internal' | 'external' | 'none'
  type: BannerType
  startAt: string
  endAt: string
  targetUsers?: string[]
}

/**
 * 焦点图详情（扩展信息）
 */
export interface BannerDetail extends Banner {
  /** 创建者信息 */
  creatorInfo: {
    id: string
    name: string
    avatar: string
  }
  /** 审核信息 */
  auditInfo?: {
    status: 'pending' | 'approved' | 'rejected'
    reviewer?: string
    auditTime?: string
    comment?: string
  }
  /** 投放数据 */
  performanceData: {
    clickCount: number
    viewCount: number
    clickRate: number
    conversionRate: number
  }
}

/**
 * 焦点图列表查询参数
 */
export interface BannerListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 状态筛选 */
  status?: BannerStatus
  /** 类型筛选 */
  type?: BannerType
  /** 关键词搜索 */
  keyword?: string
  /** 开始时间 */
  startTime?: string
  /** 结束时间 */
  endTime?: string
  /** 排序字段 */
  sortBy?: 'createdAt' | 'startAt' | 'sortOrder' | 'clickCount'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 更新焦点图请求
 */
export interface UpdateBannerRequest extends Partial<CreateBannerRequest> {
  /** 状态更新 */
  status?: BannerStatus
  /** 排序权重 */
  sortOrder?: number
}

/**
 * 焦点图统计数据
 */
export interface BannerStatistics {
  totalBanners: number
  activeBanners: number
  totalClicks: number
  totalViews: number
  averageClickRate: number
  uniqueVisitors: number
  conversionRate: number
  topPerformingBanners: Array<{
    id: string
    title: string
    clickCount: number
    viewCount: number
    clickRate: number
  }>
  clicksByDate: Array<{
    date: string
    clicks: number
    views: number
  }>
  clicksByDevice: Record<string, number>
}

/**
 * 焦点图点击记录
 */
export interface BannerClick {
  id: string
  bannerId: string
  userId?: string
  sessionId: string
  clickTime: string
  deviceType: 'desktop' | 'mobile' | 'tablet'
  browser: string
  ip: string
  location?: {
    country: string
    region: string
    city: string
  }
  referrer?: string
  userAgent: string
}

/**
 * 焦点图统计（旧版本兼容）
 */
export interface BannerStats {
  totalClicks: number
  totalViews: number
  clickRate: number
  uniqueVisitors: number
  conversionRate: number
}
