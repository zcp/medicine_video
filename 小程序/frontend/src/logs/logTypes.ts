/**
 * 日志系统类型定义
 * 为微信小程序环境设计的专业日志类型系统
 */

/**
 * 日志级别枚举
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal'

/**
 * 日志级别数值映射（用于级别比较）
 * 运行时常量已内联到 logger.ts，避免 mp-weixin 单独加载本文件失败。
 * 若其他模块需要数值表，从 logger 侧复用或在本文件仅保留类型。
 */

/**
 * 日志分类
 */
export type LogCategory = 
  | 'system'       // 系统日志
  | 'user'         // 用户行为日志
  | 'api'          // API调用日志
  | 'performance'  // 性能日志
  | 'error'        // 错误日志
  | 'business'     // 业务逻辑日志
  | 'ui'           // UI交互日志
  | 'network'      // 网络请求日志
  | 'storage'      // 存储操作日志
  | 'live'         // 直播相关日志

/**
 * 基础日志条目接口
 */
export interface BaseLogEntry {
  /** 日志唯一标识 */
  id: string
  /** 日志级别 */
  level: LogLevel
  /** 日志分类 */
  category: LogCategory
  /** 日志消息 */
  message: string
  /** 创建时间戳 */
  timestamp: number
  /** 时间字符串 */
  timeString: string
  /** 附加数据 */
  data?: Record<string, any>
  /** 错误堆栈（仅错误级别） */
  stack?: string
  /** 日志标签 */
  tags?: string[]
}

/**
 * 扩展日志条目（包含环境信息）
 */
export interface LogEntry extends BaseLogEntry {
  /** 平台信息 */
  platform: string
  /** 页面路径 */
  pagePath?: string
  /** 用户ID */
  userId?: string
  /** 会话ID */
  sessionId: string
  /** 应用版本 */
  appVersion: string
  /** 设备信息 */
  deviceInfo: DeviceInfo
}

/**
 * 设备信息接口
 */
export interface DeviceInfo {
  /** 设备品牌 */
  brand: string
  /** 设备型号 */
  model: string
  /** 系统版本 */
  system: string
  /** 微信版本 */
  version: string
  /** 屏幕信息 */
  screen: {
    width: number
    height: number
    pixelRatio: number
  }
  /** 网络类型 */
  networkType: string
}

/**
 * API调用日志接口
 */
export interface ApiLogEntry extends BaseLogEntry {
  /** 请求方法 */
  method: string
  /** 请求URL */
  url: string
  /** 请求参数 */
  requestData?: any
  /** 响应数据 */
  responseData?: any
  /** 响应状态码 */
  statusCode?: number
  /** 请求耗时（毫秒） */
  duration?: number
  /** 错误信息 */
  error?: string
}

/**
 * 性能日志接口
 */
export interface PerformanceLogEntry extends BaseLogEntry {
  /** 性能指标类型 */
  metric: 'page_load' | 'api_response' | 'render_time' | 'memory_usage' | 'fps'
  /** 指标值 */
  value: number
  /** 单位 */
  unit: 'ms' | 'kb' | 'mb' | 'fps' | 'count'
  /** 详细信息 */
  details?: Record<string, any>
}

/**
 * 用户行为日志接口
 */
export interface UserActionLogEntry extends BaseLogEntry {
  /** 行为类型 */
  action: string
  /** 目标元素 */
  target?: string
  /** 页面路径 */
  pagePath: string
  /** 行为参数 */
  params?: Record<string, any>
  /** 行为结果 */
  result?: 'success' | 'failure' | 'cancel'
}

/**
 * 直播相关日志接口
 */
export interface LiveLogEntry extends BaseLogEntry {
  /** 直播间ID */
  roomId: string
  /** 直播状态 */
  liveStatus: 'live' | 'offline' | 'replay'
  /** 观看时长（秒） */
  watchDuration?: number
  /** 播放质量 */
  quality?: 'low' | 'medium' | 'high' | 'ultra'
  /** 网络状态 */
  networkStatus?: 'good' | 'poor' | 'disconnected'
}

/**
 * 日志输出器接口
 */
export interface LogAppender {
  /** 输出器名称 */
  name: string
  /** 最小日志级别 */
  minLevel: LogLevel
  /** 初始化输出器 */
  initialize?(): void | Promise<void>
  /** 输出日志 */
  append(entry: LogEntry): void | Promise<void>
  /** 批量输出日志 */
  batchAppend?(entries: LogEntry[]): void | Promise<void>
  /** 清理资源 */
  dispose?(): void | Promise<void>
}

/**
 * 控制台输出器配置
 */
export interface ConsoleAppenderConfig {
  /** 是否启用颜色 */
  colorEnabled: boolean
  /** 是否显示时间戳 */
  showTimestamp: boolean
  /** 是否显示级别 */
  showLevel: boolean
  /** 是否显示分类 */
  showCategory: boolean
  /** 日期格式 */
  timestampFormat: string
}

/**
 * 存储输出器配置
 */
export interface StorageAppenderConfig {
  /** 存储键前缀 */
  keyPrefix: string
  /** 最大存储条数 */
  maxSize: number
  /** 是否压缩存储 */
  compress: boolean
  /** 过期时间（毫秒） */
  expireTime: number
}

/**
 * 网络输出器配置
 */
export interface NetworkAppenderConfig {
  /** 上传URL */
  uploadUrl: string
  /** 批量大小 */
  batchSize: number
  /** 上传间隔（毫秒） */
  uploadInterval: number
  /** 重试次数 */
  retryCount: number
  /** 请求头 */
  headers?: Record<string, string>
}

/**
 * 日志过滤器接口
 */
export interface LogFilter {
  /** 过滤器名称 */
  name: string
  /** 过滤函数 */
  filter(entry: LogEntry): boolean
}

/**
 * 日志格式化器接口
 */
export interface LogFormatter {
  /** 格式化器名称 */
  name: string
  /** 格式化函数 */
  format(entry: LogEntry): string
}

/**
 * 日志查询条件
 */
export interface LogQuery {
  /** 级别过滤 */
  levels?: LogLevel[]
  /** 分类过滤 */
  categories?: LogCategory[]
  /** 时间范围 */
  timeRange?: {
    start: number
    end: number
  }
  /** 关键词搜索 */
  keyword?: string
  /** 标签过滤 */
  tags?: string[]
  /** 页面路径过滤 */
  pagePath?: string
  /** 用户ID过滤 */
  userId?: string
  /** 分页信息 */
  pagination?: {
    page: number
    size: number
  }
}

/**
 * 日志查询结果
 */
export interface LogQueryResult {
  /** 日志条目列表 */
  items: LogEntry[]
  /** 总数 */
  total: number
  /** 当前页 */
  page: number
  /** 页大小 */
  size: number
  /** 查询耗时 */
  queryTime: number
}

/**
 * 日志统计信息
 */
export interface LogStats {
  /** 总日志数 */
  total: number
  /** 按级别分组统计 */
  byLevel: Record<LogLevel, number>
  /** 按分类分组统计 */
  byCategory: Record<LogCategory, number>
  /** 时间范围 */
  timeRange: {
    earliest: number
    latest: number
  }
  /** 存储大小（KB） */
  storageSize: number
}

/**
 * 日志事件类型
 */
export type LogEvent = 
  | 'log_created'       // 日志创建
  | 'log_appended'      // 日志输出
  | 'log_cleared'       // 日志清理
  | 'logger_initialized'// 日志系统初始化完成
  | 'appender_error'    // 输出器错误
  | 'storage_full'      // 存储已满
  | 'upload_success'    // 上传成功
  | 'upload_failed'     // 上传失败

/**
 * 日志事件监听器
 */
export interface LogEventListener {
  /** 事件类型 */
  event: LogEvent
  /** 监听器函数 */
  listener: (data?: any) => void
}
