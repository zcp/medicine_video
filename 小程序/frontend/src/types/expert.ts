/**
 * 专家相关类型定义
 * 包含专家资料、专业认证、专家统计等类型定义
 */

import { BaseEntity, StatsData } from './common'

/**
 * 专家状态
 */
export type ExpertStatus = 'active' | 'inactive' | 'pending' | 'suspended'

/**
 * 专家等级
 */
export type ExpertLevel = 'junior' | 'intermediate' | 'senior' | 'chief' | 'master'

/**
 * 职称类型
 */
export type TitleType = 
  | 'resident'        // 住院医师
  | 'attending'       // 主治医师
  | 'associate'       // 副主任医师
  | 'chief'          // 主任医师
  | 'professor'      // 教授
  | 'researcher'     // 研究员
  | 'other'          // 其他

/**
 * 专家信息
 */
export interface Expert extends BaseEntity {
  /** 专家姓名 */
  name: string
  /** 头像 */
  avatar: string
  /** 职称 */
  title: string
  /** 职称类型 */
  titleType: TitleType
  /** 所属医院 */
  hospital: string
  /** 所属科室 */
  department: string
  /** 科室ID */
  departmentId: string
  /** 词表科室 ID（《20》权威；snake_case 对齐后端） */
  department_id?: string | null
  /** 词表科室名；展示优先于此，再回退 department */
  department_name?: string | null
  /** 由词表同步的主分类 ID */
  category_id?: string | null
  /** 由词表同步的主分类名 */
  category_name?: string | null
  /** 专业方向 */
  specialization: string[]
  /** 专家简介 */
  bio: string
  /** 详细介绍 */
  description: string
  /** 教育背景 */
  education: string[]
  /** 工作经历 */
  experience: string[]
  /** 学术成果 */
  achievements: string[]
  /** 专家等级 */
  level: ExpertLevel
  /** 专家状态 */
  status: ExpertStatus
  /** 是否认证 */
  isVerified: boolean
  /** 认证时间 */
  verifiedAt: string
  /** 执业证号 */
  licenseNumber: string
  /** 联系方式 */
  contact: {
    phone?: string
    email?: string
    wechat?: string
  }
  /** 坐诊时间 */
  consultationHours: ConsultationSchedule[]
  /** 专家标签 */
  tags: string[]
  /** 专家统计 */
  stats: ExpertStats
}

/**
 * 专家详情（扩展信息）
 */
export interface ExpertDetail extends Expert {
  /** 粉丝列表预览 */
  recentFollowers: Array<{
    id: string
    nickname: string
    avatar: string
    followTime: string
  }>
  /** 最新直播 */
  recentLives: Array<{
    id: string
    title: string
    startTime: string
    viewerCount: number
    status: string
  }>
  /** 最新评价 */
  recentReviews: Array<{
    id: string
    rating: number
    content: string
    reviewerName: string
    reviewTime: string
  }>
  /** 相关专家推荐 */
  relatedExperts: Array<{
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    followerCount: number
  }>
}

/**
 * 创建专家请求
 */
export interface CreateExpertRequest {
  /** 专家姓名 */
  name: string
  /** 头像 */
  avatar: string
  /** 职称 */
  title: string
  /** 职称类型 */
  titleType: TitleType
  /** 所属医院 */
  hospital: string
  /** 所属科室 */
  department: string
  /** 科室ID */
  departmentId: string
  /** 专业方向 */
  specialization: string[]
  /** 专家简介 */
  bio: string
  /** 详细介绍 */
  description?: string
  /** 教育背景 */
  education?: string[]
  /** 工作经历 */
  experience?: string[]
  /** 学术成果 */
  achievements?: string[]
  /** 专家等级 */
  level: ExpertLevel
  /** 是否认证 */
  isVerified?: boolean
  /** 执业证号 */
  licenseNumber?: string
  /** 联系方式 */
  contact?: {
    phone?: string
    email?: string
    wechat?: string
  }
  /** 坐诊时间 */
  consultationHours?: ConsultationSchedule[]
  /** 专家标签 */
  tags?: string[]
}

/**
 * 更新专家请求（部分更新）
 */
export interface UpdateExpertRequest {
  /** 专家姓名 */
  name?: string
  /** 头像 */
  avatar?: string
  /** 职称 */
  title?: string
  /** 职称类型 */
  titleType?: TitleType
  /** 所属医院 */
  hospital?: string
  /** 所属科室 */
  department?: string
  /** 科室ID */
  departmentId?: string
  /** 专业方向 */
  specialization?: string[]
  /** 专家简介 */
  bio?: string
  /** 详细介绍 */
  description?: string
  /** 教育背景 */
  education?: string[]
  /** 工作经历 */
  experience?: string[]
  /** 学术成果 */
  achievements?: string[]
  /** 专家等级 */
  level?: ExpertLevel
  /** 专家状态 */
  status?: ExpertStatus
  /** 是否认证 */
  isVerified?: boolean
  /** 执业证号 */
  licenseNumber?: string
  /** 联系方式 */
  contact?: {
    phone?: string
    email?: string
    wechat?: string
  }
  /** 坐诊时间 */
  consultationHours?: ConsultationSchedule[]
  /** 专家标签 */
  tags?: string[]
}

/**
 * 专家列表查询参数
 */
export interface ExpertListQuery {
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 专家状态 */
  status?: ExpertStatus
  /** 专家等级 */
  level?: ExpertLevel
  /** 职称类型 */
  titleType?: TitleType
  /** 科室ID */
  departmentId?: string
  /** 医院名称 */
  hospital?: string
  /** 是否已认证 */
  isVerified?: boolean
  /** 关键词搜索 */
  keyword?: string
  /** 专业方向 */
  specialization?: string[]
  /** 排序字段 */
  sortBy?: 'createdAt' | 'followersCount' | 'averageRating' | 'liveCount'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 专家搜索查询参数
 */
export interface ExpertSearchQuery extends ExpertListQuery {
  /** 最小关注数 */
  minFollowers?: number
  /** 最大关注数 */
  maxFollowers?: number
  /** 最小评分 */
  minRating?: number
  /** 执业年限范围 */
  experienceRange?: [number, number]
  /** 是否在线 */
  isOnline?: boolean
  /** 地区筛选 */
  region?: string
  /** 直播时间筛选 */
  hasLiveSchedule?: boolean
}

/**
 * 专家预约信息
 */
export interface ExpertAppointment extends BaseEntity {
  /** 专家ID */
  expertId: string
  /** 专家信息 */
  expertInfo: {
    name: string
    avatar: string
    title: string
    hospital: string
    department: string
  }
  /** 预约用户ID */
  userId: string
  /** 用户信息 */
  userInfo: {
    nickname: string
    avatar: string
    phone: string
  }
  /** 预约时间 */
  appointmentTime: string
  /** 预约类型 */
  type: 'online' | 'offline' | 'phone'
  /** 预约状态 */
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show'
  /** 问题描述 */
  description: string
  /** 症状描述 */
  symptoms?: string[]
  /** 既往病史 */
  medicalHistory?: string
  /** 预约费用 */
  fee: number
  /** 预约备注 */
  note?: string
  /** 取消原因 */
  cancelReason?: string
  /** 完成时间 */
  completedAt?: string
}

/**
 * 专家统计数据
 */
export interface ExpertStats extends StatsData {
  /** 关注者数量 */
  followersCount: number
  /** 直播场次数 */
  liveCount: number
  /** 总直播时长 */
  totalLiveTime: number
  /** 总观看人数 */
  totalViewers: number
  /** 平均评分 */
  averageRating: number
  /** 评价数量 */
  reviewCount: number
  /** 咨询次数 */
  consultationCount: number
}

/**
 * 专家统计数据（别名，API兼容性）
 */
export interface ExpertStatistics {
  totalExperts: number
  activeExperts: number
  verifiedExperts: number
  expertsByLevel: Record<ExpertLevel, number>
  expertsByDepartment: Record<string, number>
  totalFollowers: number
  totalLives: number
  averageRating: number
  topExperts: Array<{
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    followerCount: number
    averageRating: number
    liveCount: number
  }>
  growthTrend: Array<{
    date: string
    newExperts: number
    totalExperts: number
    newFollowers: number
  }>
}

/**
 * 创建评价请求
 */
export interface CreateReviewRequest {
  /** 专家ID */
  expertId: string
  /** 评分 (1-5) */
  rating: number
  /** 评价内容 */
  content: string
  /** 评价标签 */
  tags?: string[]
  /** 相关直播ID */
  relatedRoomId?: string
  /** 是否匿名 */
  isAnonymous?: boolean
}

/**
 * 更新排班请求
 */
export interface UpdateScheduleRequest {
  /** 专家ID */
  expertId: string
  /** 坐诊时间安排 */
  schedules: ConsultationSchedule[]
  /** 特殊安排（节假日等） */
  specialSchedules?: Array<{
    date: string
    startTime: string
    endTime: string
    available: boolean
    note?: string
  }>
  /** 休假安排 */
  vacations?: Array<{
    startDate: string
    endDate: string
    reason: string
  }>
}

/**
 * 专家排班（别名，API兼容性）
 */
export interface ExpertSchedule extends ConsultationSchedule {}

/**
 * 坐诊时间安排
 */
export interface ConsultationSchedule {
  /** 星期几 (0-6, 0表示周日) */
  dayOfWeek: number
  /** 开始时间 */
  startTime: string
  /** 结束时间 */
  endTime: string
  /** 是否可预约 */
  available: boolean
  /** 科室 */
  department: string
  /** 备注 */
  note?: string
}

/**
 * 专家认证申请
 */
export interface ExpertVerificationRequest {
  /** 真实姓名 */
  realName: string
  /** 职称 */
  title: string
  /** 职称类型 */
  titleType: TitleType
  /** 医院 */
  hospital: string
  /** 科室 */
  department: string
  /** 执业证号 */
  licenseNumber: string
  /** 执业证照片 */
  licenseImage: string
  /** 工作证照片 */
  workIdImage: string
  /** 学历证明 */
  educationProof: string[]
  /** 专业证书 */
  certificates: string[]
  /** 申请说明 */
  description: string
}

/**
 * 专家认证信息
 */
export interface ExpertVerificationInfo extends BaseEntity {
  /** 专家ID */
  expertId: string
  /** 认证申请 */
  application: ExpertVerificationRequest
  /** 认证状态 */
  status: 'pending' | 'approved' | 'rejected' | 'resubmit'
  /** 审核员ID */
  reviewerId?: string
  /** 审核员姓名 */
  reviewerName?: string
  /** 审核意见 */
  reviewNote?: string
  /** 审核时间 */
  reviewedAt?: string
  /** 证书编号 */
  certificateNumber?: string
}

/**
 * 专家评价
 */
export interface ExpertReview extends BaseEntity {
  /** 专家ID */
  expertId: string
  /** 评价者ID */
  reviewerId: string
  /** 评价者信息 */
  reviewerInfo: {
    nickname: string
    avatar: string
  }
  /** 评分 (1-5) */
  rating: number
  /** 评价内容 */
  content: string
  /** 评价标签 */
  tags: string[]
  /** 相关直播ID */
  relatedRoomId?: string
  /** 是否匿名 */
  isAnonymous: boolean
  /** 点赞数 */
  likeCount: number
  /** 是否有用 */
  isHelpful: boolean
}

/**
 * 专家关注关系
 */
export interface ExpertFollow extends BaseEntity {
  /** 专家ID */
  expertId: string
  /** 关注者ID */
  followerId: string
  /** 关注者信息 */
  followerInfo: {
    nickname: string
    avatar: string
  }
  /** 专家信息 */
  expertInfo: {
    name: string
    avatar: string
    title: string
    hospital: string
  }
  /** 通知设置 */
  notifications: {
    newLive: boolean
    newContent: boolean
  }
}

/**
 * 专家直播安排
 */
export interface ExpertLiveSchedule extends BaseEntity {
  /** 专家ID */
  expertId: string
  /** 直播标题 */
  title: string
  /** 直播描述 */
  description: string
  /** 预定开始时间 */
  scheduledAt: string
  /** 预估时长 */
  estimatedDuration: number
  /** 直播类型 */
  type: 'lecture' | 'consultation' | 'surgery' | 'discussion'
  /** 目标观众 */
  targetAudience: string[]
  /** 是否定期直播 */
  isRecurring: boolean
  /** 重复规则 */
  recurringRule?: {
    frequency: 'daily' | 'weekly' | 'monthly'
    interval: number
    endDate?: string
  }
}

/**
 * 专家搜索参数
 */
export interface ExpertSearchParams {
  /** 关键词 */
  keyword?: string
  /** 医院 */
  hospital?: string
  /** 科室ID */
  departmentId?: string
  /** 职称类型 */
  titleType?: TitleType
  /** 专家等级 */
  level?: ExpertLevel
  /** 专业方向 */
  specialization?: string[]
  /** 是否认证 */
  isVerified?: boolean
  /** 是否在线 */
  isOnline?: boolean
  /** 排序字段 */
  sortBy?: 'created' | 'followers' | 'rating' | 'experience'
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
  /** 分页 */
  page?: number
  size?: number
}

/**
 * 专家推荐参数
 */
export interface ExpertRecommendParams {
  /** 用户ID */
  userId: string
  /** 推荐类型 */
  type: 'similar' | 'popular' | 'recent' | 'followed'
  /** 科室偏好 */
  departmentPreference?: string[]
  /** 数量限制 */
  limit?: number
}

/**
 * 专家统计报告
 */
export interface ExpertReport {
  /** 时间范围 */
  period: {
    start: string
    end: string
  }
  /** 基础数据 */
  overview: {
    totalLives: number
    totalViewers: number
    totalDuration: number
    averageRating: number
  }
  /** 观众分析 */
  audienceAnalysis: {
    demographics: {
      ageGroups: Record<string, number>
      genderDistribution: Record<string, number>
      regionDistribution: Record<string, number>
    }
    behavior: {
      avgWatchTime: number
      interactionRate: number
      retentionRate: number
    }
  }
  /** 内容表现 */
  contentPerformance: {
    topLives: Array<{
      title: string
      viewers: number
      rating: number
      date: string
    }>
    popularTopics: string[]
  }
}
