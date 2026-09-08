/**
 * 科室相关类型定义
 * 包含医院科室、分类管理等类型定义
 */

import { BaseEntity, StatsData } from './common'

/**
 * 科室状态
 */
export type DepartmentStatus = 'active' | 'inactive' | 'pending'

/**
 * 科室级别
 */
export type DepartmentLevel = 'primary' | 'secondary' | 'tertiary'

/**
 * 科室类型
 */
export type DepartmentType = 
  | 'clinical'      // 临床科室
  | 'medical'       // 医技科室  
  | 'nursing'       // 护理科室
  | 'administration'// 行政科室
  | 'research'      // 科研科室

/**
 * 科室信息
 */
export interface Department extends BaseEntity {
  /** 科室名称 */
  name: string
  /** 科室代码 */
  code: string
  /** 科室描述 */
  description: string
  /** 科室图标 */
  icon: string
  /** 科室封面 */
  cover: string
  /** 父科室ID */
  parentId?: string
  /** 科室级别 */
  level: DepartmentLevel
  /** 科室类型 */
  type: DepartmentType
  /** 科室状态 */
  status: DepartmentStatus
  /** 排序权重 */
  sortOrder: number
  /** 是否热门 */
  isHot: boolean
  /** 是否推荐 */
  isRecommended: boolean
  /** 科室标签 */
  tags: string[]
  /** 相关疾病 */
  diseases: string[]
  /** 常见症状 */
  symptoms: string[]
  /** 科室统计 */
  stats: DepartmentStats
}

/**
 * 科室统计数据
 */
export interface DepartmentStats extends StatsData {
  /** 专家数量 */
  expertCount: number
  /** 关注数量 */
  followCount: number
  /** 直播场次 */
  liveCount: number
  /** 总观看人数 */
  totalViewers: number
  /** 平均评分 */
  averageRating: number
}

/**
 * 科室树结构
 */
export interface DepartmentTree extends Department {
  /** 子科室列表 */
  children?: DepartmentTree[]
  /** 科室路径 */
  path: string[]
  /** 层级深度 */
  depth: number
}

/**
 * 科室专家关联
 */
export interface DepartmentExpert extends BaseEntity {
  /** 科室ID */
  departmentId: string
  /** 专家ID */
  expertId: string
  /** 专家信息 */
  expertInfo: {
    name: string
    avatar: string
    title: string
    isVerified: boolean
  }
  /** 是否主要科室 */
  isPrimary: boolean
  /** 职务 */
  position: string
  /** 排序权重 */
  sortOrder: number
}

/**
 * 创建科室请求
 */
export interface CreateDepartmentRequest {
  name: string
  code: string
  description: string
  icon?: string
  cover?: string
  parentId?: string
  level: DepartmentLevel
  type: DepartmentType
  tags?: string[]
  diseases?: string[]
  symptoms?: string[]
}

/**
 * 更新科室请求
 */
export interface UpdateDepartmentRequest extends Partial<CreateDepartmentRequest> {
  id: string
  status?: DepartmentStatus
  isHot?: boolean
  isRecommended?: boolean
  sortOrder?: number
}

/**
 * 科室详情（扩展信息）
 */
export interface DepartmentDetail extends Department {
  /** 专家列表 */
  experts: Array<{
    id: string
    name: string
    avatar: string
    title: string
    level: string
    rating: number
    isOnline: boolean
  }>
  /** 最新直播 */
  recentLives: Array<{
    id: string
    title: string
    expertName: string
    startTime: string
    status: string
  }>
  /** 科室新闻/文章 */
  articles: Array<{
    id: string
    title: string
    summary: string
    publishTime: string
    author: string
  }>
}

/**
 * 科室列表查询参数
 */
export interface DepartmentListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 状态筛选 */
  status?: DepartmentStatus
  /** 类型筛选 */
  type?: DepartmentType
  /** 等级筛选 */
  level?: DepartmentLevel
  /** 关键词搜索 */
  keyword?: string
  /** 排序字段 */
  sortBy?: 'createdAt' | 'name' | 'expertCount' | 'followCount'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 科室搜索查询参数
 */
export interface DepartmentSearchQuery extends DepartmentListQuery {
  /** 地区筛选 */
  region?: string
  /** 是否有在线专家 */
  hasOnlineExperts?: boolean
  /** 最小专家数量 */
  minExpertCount?: number
  /** 最小评分 */
  minRating?: number
}

/**
 * 科室统计数据
 */
export interface DepartmentStatistics {
  totalDepartments: number
  activeDepartments: number
  departmentsByType: Record<DepartmentType, number>
  departmentsByLevel: Record<DepartmentLevel, number>
  totalExperts: number
  totalFollowers: number
  totalLives: number
  topDepartments: Array<{
    id: string
    name: string
    type: DepartmentType
    expertCount: number
    followCount: number
    liveCount: number
  }>
  growthData: Array<{
    date: string
    newDepartments: number
    totalDepartments: number
  }>
}

/**
 * 科室搜索参数
 */
export interface DepartmentSearchParams {
  /** 搜索关键词 */
  keyword?: string
  /** 科室类型 */
  type?: DepartmentType[]
  /** 科室等级 */
  level?: DepartmentLevel[]
  /** 科室状态 */
  status?: DepartmentStatus[]
  /** 最小专家数 */
  minExpertCount?: number
  /** 最大专家数 */
  maxExpertCount?: number
  /** 最小评分 */
  minRating?: number
  /** 地区 */
  region?: string
  /** 是否有在线专家 */
  hasOnlineExperts?: boolean
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
  /** 分页 */
  page?: number
  size?: number
}

/**
 * 科室关注
 */
export interface DepartmentFollow extends BaseEntity {
  /** 科室ID */
  departmentId: string
  /** 关注者ID */
  followerId: string
  /** 关注者信息 */
  followerInfo: {
    nickname: string
    avatar: string
  }
  /** 科室信息 */
  departmentInfo: {
    name: string
    icon: string
    cover: string
  }
  /** 通知设置 */
  notifications: {
    newExpert: boolean
    newLive: boolean
    hotContent: boolean
  }
}

/**
 * 科室配置
 */
export interface DepartmentConfig {
  /** 最大层级深度 */
  maxDepth: number
  /** 是否允许重复名称 */
  allowDuplicateName: boolean
  /** 默认图标 */
  defaultIcon: string
  /** 默认封面 */
  defaultCover: string
  /** 自动排序规则 */
  autoSortRule: 'name' | 'created' | 'expert_count'
}

/**
 * 科室推荐算法参数
 */
export interface DepartmentRecommendParams {
  /** 用户ID */
  userId: string
  /** 推荐类型 */
  type: 'personalized' | 'popular' | 'trending' | 'similar'
  /** 基于的科室ID */
  baseDepartmentId?: string
  /** 推荐数量 */
  limit?: number
  /** 排除的科室ID */
  excludeIds?: string[]
}
