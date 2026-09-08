/**
 * 通用类型定义
 * 定义全局通用的数据结构和枚举类型
 */

/**
 * 语言类型
 */
export type Language = 'zh-CN' | 'zh-TW' | 'en-US' | 'ja-JP' | 'ko-KR'

/**
 * 统一API响应结构
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T | null
  timestamp: string
}

/**
 * 分页响应格式
 */
export interface PaginatedResponse<T = any> {
  total: number
  page: number
  size: number
  items: T[]
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number
  size?: number
  sort?: string
  order?: 'asc' | 'desc'
}

/**
 * 搜索参数
 */
export interface SearchParams extends PaginationParams {
  keyword?: string
  category?: string
  tags?: string[]
  dateRange?: {
    start: string
    end: string
  }
}

/**
 * 时间范围
 */
export interface TimeRange {
  start: string
  end: string
}

/**
 * 地理位置信息
 */
export interface LocationInfo {
  latitude: number
  longitude: number
  address?: string
  city?: string
  province?: string
  country?: string
}

/**
 * 文件信息
 */
export interface FileInfo {
  id: string
  name: string
  url: string
  size: number
  type: string
  uploadTime: string
  hash?: string
}

/**
 * 媒体资源信息
 */
export interface MediaInfo {
  id: string
  type: 'image' | 'video' | 'audio'
  url: string
  thumbnailUrl?: string
  width?: number
  height?: number
  duration?: number
  size: number
  format: string
  quality?: 'low' | 'medium' | 'high' | 'ultra'
}

/**
 * 统计数据
 */
export interface StatsData {
  views: number
  likes: number
  shares: number
  comments: number
  collections: number
  duration?: number
}

/**
 * 操作结果
 */
export interface OperationResult<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
}

/**
 * 网络请求状态
 */
export type RequestStatus = 'idle' | 'loading' | 'success' | 'error'

/**
 * 通用状态类型
 */
export type CommonStatus = 'active' | 'inactive' | 'pending' | 'disabled'

/**
 * 排序方向
 */
export type SortOrder = 'asc' | 'desc'

/**
 * 性别类型
 */
export type Gender = 'male' | 'female' | 'other' | 'unknown'

 

/**
 * 主题模式
 */
export type ThemeMode = 'light' | 'dark' | 'auto'

/**
 * 设备类型
 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop'

/**
 * 平台类型
 */
export type Platform = 'mp-weixin' | 'mp-alipay' | 'mp-baidu' | 'mp-toutiao' | 'mp-qq' | 'h5' | 'app'

/**
 * 错误类型
 */
export interface ErrorInfo {
  code: string
  message: string
  details?: Record<string, any>
  timestamp: string
}

/**
 * 键值对类型
 */
export type KeyValuePair<T = string> = Record<string, T>

/**
 * 选项类型
 */
export interface SelectOption<T = string> {
  label: string
  value: T
  disabled?: boolean
  extra?: any
}

/**
 * 树形数据节点
 */
export interface TreeNode<T = any> {
  id: string
  label: string
  children?: TreeNode<T>[]
  data?: T
  expanded?: boolean
  selected?: boolean
  disabled?: boolean
}

/**
 * 表单字段类型
 */
export interface FormField {
  name: string
  label: string
  type: 'text' | 'password' | 'email' | 'number' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'file'
  value?: any
  required?: boolean
  disabled?: boolean
  placeholder?: string
  options?: SelectOption[]
  rules?: FormRule[]
}

/**
 * 表单验证规则
 */
export interface FormRule {
  required?: boolean
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (value: any) => boolean | string
  message?: string
}

/**
 * 基础实体接口
 */
export interface BaseEntity {
  id: string
  createdAt: string
  updatedAt: string
}

/**
 * 审核状态
 */
export type AuditStatus = 'pending' | 'approved' | 'rejected' | 'reviewing'

/**
 * 发布状态
 */
export type PublishStatus = 'draft' | 'published' | 'unpublished' | 'scheduled'

/**
 * 可见性级别
 */
export type VisibilityLevel = 'public' | 'private' | 'protected' | 'members'

/**
 * 优先级级别
 */
export type PriorityLevel = 'low' | 'medium' | 'high' | 'urgent'

/**
 * 颜色值类型
 */
export type ColorValue = string // CSS颜色值：hex, rgb, rgba, hsl等

/**
 * 尺寸值类型
 */
export type SizeValue = string | number // CSS尺寸值：px, rem, %, vw, vh等

/**
 * 通用ID类型
 */
export type ID = string | number

/**
 * 可选字段工具类型
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * 必需字段工具类型
 */
export type RequiredKeys<T, K extends keyof T> = T & Required<Pick<T, K>>

/**
 * 深度Partial工具类型
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * 深度Required工具类型  
 */
export type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object | undefined ? DeepRequired<Required<NonNullable<T[P]>>> : T[P]
}
