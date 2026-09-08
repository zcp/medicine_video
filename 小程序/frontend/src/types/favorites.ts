/**
 * 用户收藏类型定义
 * 包含收藏夹、收藏内容等类型定义
 */

import { BaseEntity } from './common'

/**
 * 收藏类型
 */
export type FavoriteType = 'room' | 'expert' | 'content' | 'article'

/**
 * 收藏信息
 */
export interface Favorite extends BaseEntity {
  /** 用户ID */
  userId: string
  /** 收藏类型 */
  type: FavoriteType
  /** 目标ID */
  targetId: string
  /** 收藏夹ID */
  folderId?: string
  /** 备注 */
  note?: string
  /** 标签 */
  tags: string[]
}

/**
 * 收藏夹信息
 */
export interface FavoriteFolder extends BaseEntity {
  /** 用户ID */
  userId: string
  /** 收藏夹名称 */
  name: string
  /** 描述 */
  description: string
  /** 是否公开 */
  isPublic: boolean
  /** 收藏数量 */
  itemCount: number
  /** 封面图 */
  cover?: string
}

/**
 * 收藏列表查询参数
 */
export interface FavoriteListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 收藏类型 */
  type?: FavoriteType
  /** 收藏夹ID */
  folderId?: string
  /** 关键词搜索 */
  keyword?: string
  /** 标签筛选 */
  tags?: string[]
  /** 排序字段 */
  sortBy?: 'createdAt' | 'updatedAt' | 'targetName'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
  /** 用户ID（管理员查看其他用户收藏） */
  userId?: string
}

/**
 * 创建收藏请求
 */
export interface CreateFavoriteRequest {
  /** 收藏类型 */
  type: FavoriteType
  /** 目标ID */
  targetId: string
  /** 收藏夹ID（可选） */
  folderId?: string
  /** 备注 */
  note?: string
  /** 标签 */
  tags?: string[]
  /** 目标信息（用于展示） */
  targetInfo?: {
    title: string
    image?: string
    description?: string
  }
}

/**
 * 创建收藏夹请求
 */
export interface CreateFolderRequest {
  /** 收藏夹名称 */
  name: string
  /** 描述 */
  description?: string
  /** 是否公开 */
  isPublic?: boolean
  /** 封面图 */
  cover?: string
}

/**
 * 更新收藏夹请求
 */
export interface UpdateFolderRequest {
  /** 收藏夹ID */
  id: string
  /** 收藏夹名称 */
  name?: string
  /** 描述 */
  description?: string
  /** 是否公开 */
  isPublic?: boolean
  /** 封面图 */
  cover?: string
}

/**
 * 收藏统计数据
 */
export interface FavoriteStatistics {
  /** 总收藏数 */
  totalFavorites: number
  /** 收藏夹数量 */
  totalFolders: number
  /** 按类型统计 */
  favoritesByType: Record<FavoriteType, number>
  /** 热门收藏内容 */
  popularItems: Array<{
    targetId: string
    targetType: FavoriteType
    title: string
    favoriteCount: number
    recentFavorites: number
  }>
  /** 收藏趋势 */
  favoriteTrend: Array<{
    date: string
    newFavorites: number
    totalFavorites: number
  }>
  /** 用户活跃度 */
  userActivity: {
    dailyActiveFavorites: number
    weeklyActiveFavorites: number
    monthlyActiveFavorites: number
  }
}

/**
 * 收藏详情（扩展信息）
 */
export interface FavoriteDetail extends Favorite {
  /** 目标详细信息 */
  targetDetail: {
    title: string
    description?: string
    image?: string
    author?: string
    publishTime?: string
    /** 根据type不同，包含不同的详细信息 */
    [key: string]: any
  }
  /** 收藏夹信息 */
  folderInfo?: {
    id: string
    name: string
    description: string
  }
}

/**
 * 批量操作收藏请求
 */
export interface BatchFavoriteRequest {
  /** 操作类型 */
  action: 'move' | 'delete' | 'addTags' | 'removeTags'
  /** 收藏ID列表 */
  favoriteIds: string[]
  /** 目标收藏夹ID（移动时使用） */
  targetFolderId?: string
  /** 标签（添加/移除标签时使用） */
  tags?: string[]
}
