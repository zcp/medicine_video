/**
 * 用户相关类型定义
 * 包含用户资料、用户行为、用户统计等类型定义
 */

import { BaseEntity, MediaInfo, StatsData } from './common'

/**
 * 用户性别
 */
export type UserGender = 'male' | 'female' | 'unknown'

/**
 * 用户状态
 */
export type UserStatus = 'active' | 'inactive' | 'blocked' | 'pending'

/**
 * 认证状态
 */
export type VerificationStatus = 'pending' | 'verified' | 'rejected'

/**
 * 用户等级
 */
export type UserLevel = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond'

/**
 * 用户基础信息
 */
export interface User extends BaseEntity {
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname: string
  /** 头像URL */
  avatar: string
  /** 手机号 */
  phone: string
  /** 邮箱 */
  email: string
  /** 性别 */
  gender: UserGender
  /** 生日 */
  birthday: string
  /** 职业 */
  profession: string
  /** 医院 */
  hospital: string
  /** 科室 */
  department: string
  /** 职称 */
  title: string
  /** 个人简介 */
  bio: string
  /** 用户状态 */
  status: UserStatus
  /** 是否认证 */
  isVerified: boolean
  /** 认证时间 */
  verifiedAt: string
  /** 最后登录时间 */
  lastLoginAt: string
  /** 登录次数 */
  loginCount: number
  /** 用户等级 */
  level: UserLevel
  /** 经验值 */
  experience: number
}

/**
 * 用户详情资料（扩展信息）
 */
export interface UserProfile extends User {
  /** 关注列表 */
  following: Array<{
    id: string
    nickname: string
    avatar: string
    isVerified: boolean
  }>
  /** 粉丝列表 */
  followers: Array<{
    id: string
    nickname: string
    avatar: string
    isVerified: boolean
  }>
  /** 统计数据 */
  statistics: UserStats
  /** 偏好设置 */
  preferences: UserPreferences
  /** 等级信息 */
  levelInfo: UserLevelInfo
}

/**
 * 用户资料更新请求
 */
export interface UpdateUserProfileRequest {
  nickname?: string
  avatar?: string
  gender?: UserGender
  birthday?: string
  profession?: string
  hospital?: string
  department?: string
  title?: string
  bio?: string
}

/**
 * 用户资料更新请求（别名，API兼容性）
 */
export interface UpdateProfileRequest extends UpdateUserProfileRequest {}

/**
 * 上传头像请求
 */
export interface UploadAvatarRequest {
  /** 头像文件路径（小程序使用 filePath） */
  avatar: string
  /** 裁剪参数 */
  crop?: {
    x: number
    y: number
    width: number
    height: number
  }
  /** 压缩质量 0.1-1.0 */
  quality?: number
}

/**
 * 用户头像上传响应
 */
export interface AvatarUploadResponse {
  url: string
  size: number
  format: string
}

/**
 * 用户认证申请
 */
export interface UserVerificationRequest {
  realName: string
  idCard: string
  profession: string
  hospital: string
  department: string
  title: string
  licenseNumber: string
  licenseImage: string
  workImage: string
  description: string
}

/**
 * 用户认证信息
 */
export interface UserVerificationInfo extends BaseEntity {
  userId: string
  realName: string
  profession: string
  hospital: string
  department: string
  title: string
  licenseNumber: string
  licenseImage: string
  workImage: string
  description: string
  status: VerificationStatus
  reviewerId: string
  reviewerName: string
  reviewNote: string
  reviewedAt: string
}

/**
 * 用户列表查询参数
 */
export interface UserListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 用户状态筛选 */
  status?: UserStatus
  /** 用户等级筛选 */
  level?: UserLevel
  /** 是否已认证 */
  isVerified?: boolean
  /** 关键词搜索 */
  keyword?: string
  /** 排序字段 */
  sortBy?: 'createdAt' | 'lastLoginAt' | 'followersCount' | 'level'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 用户搜索参数
 */
export interface UserSearchParams extends UserListQuery {
  /** 职业筛选 */
  profession?: string
  /** 医院筛选 */
  hospital?: string
  /** 科室筛选 */
  department?: string
  /** 职称筛选 */
  title?: string
  /** 最小粉丝数 */
  minFollowers?: number
  /** 最大粉丝数 */
  maxFollowers?: number
  /** 注册时间范围 */
  registeredAfter?: string
  registeredBefore?: string
}

/**
 * 用户搜索查询（别名，API兼容性）
 */
export interface UserSearchQuery extends UserSearchParams {}

/**
 * 关注请求参数
 */
export interface FollowRequest {
  /** 目标用户ID */
  targetUserId: string
  /** 关注类型 */
  type?: 'follow' | 'unfollow'
  /** 分组ID（可选） */
  groupId?: string
}

/**
 * 用户统计信息
 */
export interface UserStats {
  /** 关注数 */
  followingCount: number
  /** 粉丝数 */
  followersCount: number
  /** 收藏数 */
  favoritesCount: number
  /** 观看历史数 */
  historyCount: number
  /** 总观看时长（秒） */
  totalWatchTime: number
  /** 点赞数 */
  likesCount: number
  /** 评论数 */
  commentsCount: number
  /** 分享数 */
  sharesCount: number
}

/**
 * 用户统计信息（别名，API兼容性）
 */
export interface UserStatistics extends UserStats {
  /** 平台总用户数 */
  totalUsers?: number
  /** 活跃用户数 */
  activeUsers?: number
  /** 新注册用户数 */
  newUsers?: number
  /** 认证用户数 */
  verifiedUsers?: number
  /** 用户增长趋势 */
  growthTrend?: Array<{
    date: string
    newUsers: number
    activeUsers: number
  }>
}

/**
 * 用户认证（别名，API兼容性）
 */
export interface UserVerification extends UserVerificationInfo {}

/**
 * 用户行为记录
 */
export interface UserAction extends BaseEntity {
  userId: string
  action: UserActionType
  targetType: 'room' | 'expert' | 'user' | 'content'
  targetId: string
  metadata: Record<string, any>
  deviceInfo: string
  ipAddress: string
}

/**
 * 用户行为类型
 */
export type UserActionType = 
  | 'login'           // 登录
  | 'logout'          // 登出
  | 'view_room'       // 查看房间
  | 'join_room'       // 进入房间
  | 'leave_room'      // 离开房间
  | 'follow_expert'   // 关注专家
  | 'unfollow_expert' // 取关专家
  | 'like_content'    // 点赞内容
  | 'unlike_content'  // 取消点赞
  | 'share_content'   // 分享内容
  | 'comment'         // 评论
  | 'favorite'        // 收藏
  | 'unfavorite'      // 取消收藏
  | 'search'          // 搜索
  | 'view_profile'    // 查看资料

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  /** 语言 */
  language: 'zh-CN' | 'en-US'
  /** 主题 */
  theme: 'light' | 'dark' | 'auto'
  /** 通知设置 */
  notifications: {
    push: boolean
    email: boolean
    sms: boolean
    inApp: boolean
  }
  /** 隐私设置 */
  privacy: {
    showPhone: boolean
    showEmail: boolean
    allowFollow: boolean
    allowMessage: boolean
  }
  /** 播放设置 */
  playback: {
    autoplay: boolean
    quality: 'auto' | 'low' | 'medium' | 'high'
    volume: number
  }
}

/**
 * 用户关注关系
 */
export interface UserFollow extends BaseEntity {
  followerId: string
  followingId: string
  followerInfo: {
    nickname: string
    avatar: string
  }
  followingInfo: {
    nickname: string
    avatar: string
    isVerified: boolean
  }
}

/**
 * 用户等级信息
 */
export interface UserLevelInfo {
  currentLevel: UserLevel
  currentExperience: number
  nextLevel: UserLevel | null
  nextLevelExperience: number
  progressPercentage: number
  levelBenefits: string[]
}

/**
 * 用户积分记录
 */
export interface UserPointRecord extends BaseEntity {
  userId: string
  type: 'earn' | 'spend'
  action: string
  points: number
  description: string
  relatedId?: string
  relatedType?: string
}

/**
 * 用户在线状态
 */
export interface UserOnlineStatus {
  userId: string
  isOnline: boolean
  lastActiveAt: string
  currentRoomId?: string
  device: 'mobile' | 'desktop' | 'tablet'
}
