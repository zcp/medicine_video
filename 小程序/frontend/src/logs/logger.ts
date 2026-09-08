/**
 * 日志系统核心实现
 * 为微信小程序环境优化的专业日志记录器
 */

import type {
  LogLevel,
  LogCategory,
  LogEntry,
  BaseLogEntry,
  ApiLogEntry,
  PerformanceLogEntry,
  UserActionLogEntry,
  LiveLogEntry,
  LogAppender,
  LogFilter,
  LogFormatter,
  LogQuery,
  LogQueryResult,
  LogStats,
  LogEvent,
  LogEventListener,
  DeviceInfo
} from './logTypes'

import { getLogConfig, type LogConfig } from './logConfig'

/**
 * 日志级别数值（内联在本文件，避免 mp-weixin 对独立 logTypes.js 偶发「module is not defined」）
 * 原定义见 logTypes.ts 注释；运行时勿再 require ./logTypes
 */
const LogLevelValues: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  fatal: 4
}

// Helpers: safe serialization / shallow copy to avoid enumerating Vue proxies or component instances
function isPlainObject(obj: any): boolean {
  return Object.prototype.toString.call(obj) === '[object Object]'
}

/** 微信控制台无法友好展示对象，统一转成可阅读字符串，避免出现 [] [object Object] */
function safeConsoleText(value: unknown): string {
  if (value == null) return String(value)
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (value instanceof Error) {
    return `${value.name}: ${value.message}`
  }
  try {
    return JSON.stringify(value)
  } catch {
    return Object.prototype.toString.call(value)
  }
}

function safeCopy(value: any): any {
  try {
    if (value == null) return value
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return value
    if (Array.isArray(value)) return value.map(safeCopy)
    if (isPlainObject(value)) {
      const out: any = {}
      Object.keys(value).forEach(k => {
        try { out[k] = safeCopy((value as any)[k]) } catch { out[k] = '[unserializable]' }
      })
      return out
    }
    // For unknown objects (Vue proxies, component instances, DOM nodes), return a short descriptor
    return { _type: value && value.constructor ? value.constructor.name : typeof value }
  } catch (e) {
    return '[unserializable]'
  }
}

/**
 * 主日志记录器类
 */
export class Logger {
  private config: LogConfig
  private appenders: Map<string, LogAppender> = new Map()
  private filters: LogFilter[] = []
  private formatter: LogFormatter
  private sessionId: string
  private deviceInfo: DeviceInfo
  private eventListeners: Map<LogEvent, LogEventListener[]> = new Map()
  private isInitialized = false

  constructor(config?: Partial<LogConfig>) {
    this.config = config ? { ...getLogConfig(), ...config } : getLogConfig()
    this.sessionId = this.generateSessionId()
    this.deviceInfo = this.collectDeviceInfo()
    this.formatter = new DefaultLogFormatter()
    
    this.initializeAppenders()
    this.setupGlobalErrorHandling()
  }

  /**
   * 初始化日志系统
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return

    try {
      // 初始化所有输出器
      for (const appender of this.appenders.values()) {
        if (appender.initialize) {
          await appender.initialize()
        }
      }

      // 清理过期日志
      await this.cleanupExpiredLogs()

      this.isInitialized = true
      this.info('system', 'Logger initialized successfully', {
        sessionId: this.sessionId,
        appenders: Array.from(this.appenders.keys())
      })

      this.emitEvent('logger_initialized')
    } catch (error) {
      console.error('Failed to initialize logger:', error)
      throw error
    }
  }

  /**
   * 记录调试日志
   */
  debug(category: LogCategory, message: string, data?: any): void {
    this.log('debug', category, message, data)
  }

  /**
   * 记录信息日志
   */
  info(category: LogCategory, message: string, data?: any): void {
    this.log('info', category, message, data)
  }

  /**
   * 记录警告日志
   */
  warn(category: LogCategory, message: string, data?: any): void {
    this.log('warn', category, message, data)
  }

  /**
   * 记录错误日志
   */
  error(category: LogCategory, message: string, error?: Error | any): void {
    const data = error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack
    } : error

    this.log('error', category, message, data, error?.stack)
  }

  /**
   * 记录致命错误日志
   */
  fatal(category: LogCategory, message: string, error?: Error | any): void {
    const data = error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack
    } : error

    this.log('fatal', category, message, data, error?.stack)
  }

  /**
   * 记录API调用日志
   */
  logApi(apiLog: Omit<ApiLogEntry, keyof BaseLogEntry>): void {
    const entry: ApiLogEntry = {
      id: this.generateId(),
      level: apiLog.statusCode && apiLog.statusCode >= 400 ? 'error' : 'info',
      category: 'api',
      message: `${apiLog.method} ${apiLog.url}`,
      timestamp: Date.now(),
      timeString: this.formatTime(Date.now()),
      ...apiLog
    }

    this.appendLog(this.enrichLogEntry(entry))
  }

  /**
   * 记录性能日志
   */
  logPerformance(perfLog: Omit<PerformanceLogEntry, keyof BaseLogEntry>): void {
    if (!this.config.performance.enabled) return

    // 性能日志采样
    if (Math.random() > this.config.performance.samplingRate) return

    const entry: PerformanceLogEntry = {
      id: this.generateId(),
      level: 'info',
      category: 'performance',
      message: `Performance: ${perfLog.metric}`,
      timestamp: Date.now(),
      timeString: this.formatTime(Date.now()),
      ...perfLog
    }

    this.appendLog(this.enrichLogEntry(entry))
  }

  /**
   * 记录用户行为日志
   */
  logUserAction(actionLog: Omit<UserActionLogEntry, keyof BaseLogEntry>): void {
    if (!this.config.userTracking.enabled) return

    // 用户行为采样
    if (Math.random() > this.config.userTracking.samplingRate) return

    const entry: UserActionLogEntry = {
      id: this.generateId(),
      level: 'info',
      category: 'user',
      message: `User action: ${actionLog.action}`,
      timestamp: Date.now(),
      timeString: this.formatTime(Date.now()),
      ...actionLog
    }

    this.appendLog(this.enrichLogEntry(entry))
  }

  /**
   * 记录直播相关日志
   */
  logLive(liveLog: Omit<LiveLogEntry, keyof BaseLogEntry>): void {
    const entry: LiveLogEntry = {
      id: this.generateId(),
      level: 'info',
      category: 'live',
      message: `Live: ${liveLog.roomId} - ${liveLog.liveStatus}`,
      timestamp: Date.now(),
      timeString: this.formatTime(Date.now()),
      ...liveLog
    }

    this.appendLog(this.enrichLogEntry(entry))
  }

  /**
   * 核心日志记录方法
   */
  private log(level: LogLevel, category: LogCategory, message: string, data?: any, stack?: string): void {
    // 检查是否启用
    if (!this.config.enabled) return

    // 检查级别过滤
    if (!this.shouldLog(level, category)) return

    const entry: LogEntry = {
      id: this.generateId(),
      level,
      category,
      message,
      timestamp: Date.now(),
      timeString: this.formatTime(Date.now()),
      data,
      stack,
      platform: process.env.UNI_PLATFORM || 'unknown',
      pagePath: this.getCurrentPagePath(),
      sessionId: this.sessionId,
      appVersion: this.config.appVersion || '1.0.0',
      deviceInfo: this.deviceInfo
    }

    this.appendLog(entry)
    this.emitEvent('log_created', entry)
  }

  /**
   * 丰富日志条目信息
   */
  private enrichLogEntry<T extends BaseLogEntry>(entry: T): LogEntry {
    return {
      ...entry,
      platform: process.env.UNI_PLATFORM || 'unknown',
      pagePath: this.getCurrentPagePath(),
      sessionId: this.sessionId,
      appVersion: this.config.appVersion || '1.0.0',
      deviceInfo: this.deviceInfo
    } as LogEntry
  }

  /**
   * 输出日志到各个输出器
   */
  private appendLog(entry: LogEntry): void {
    // 应用过滤器
    const shouldAppend = this.filters.every(filter => filter.filter(entry))
    if (!shouldAppend) return

    // 获取该分类的输出器配置
    const categoryConfig = this.config.categories.find(c => c.category === entry.category)
    if (!categoryConfig || !categoryConfig.enabled) return

    // 应用采样
    if (categoryConfig.sampling) {
      if (Math.random() > categoryConfig.sampling.rate) return
    }

    // 输出到配置的输出器，传入已清理的副本以避免对 Vue proxy/组件实例做枚举
    const safeEntry: LogEntry = {
      ...entry,
      data: safeCopy(entry.data)
    }

    categoryConfig.appenders.forEach(appenderName => {
      const appender = this.appenders.get(appenderName)
      if (appender) {
        try {
          appender.append(safeEntry)
          this.emitEvent('log_appended', { entry: safeEntry, appender: appenderName })
        } catch (error) {
          console.error(`Appender ${appenderName} failed:`, error)
          this.emitEvent('appender_error', { appender: appenderName, error })
        }
      }
    })
  }

  /**
   * 检查是否应该记录日志
   */
  private shouldLog(level: LogLevel, category: LogCategory): boolean {
    // 全局级别检查
    if (LogLevelValues[level] < LogLevelValues[this.config.level]) {
      return false
    }

    // 分类级别检查
    const categoryConfig = this.config.categories.find(c => c.category === category)
    if (!categoryConfig || !categoryConfig.enabled) {
      return false
    }

    return LogLevelValues[level] >= LogLevelValues[categoryConfig.level]
  }

  /**
   * 初始化输出器
   */
  private initializeAppenders(): void {
    // 控制台输出器
    this.appenders.set('console', new ConsoleAppender(this.config.console))

    // 存储输出器
    this.appenders.set('storage', new StorageAppender(this.config.storage))

    // 网络输出器
    if (this.config.network.uploadUrl) {
      this.appenders.set('network', new NetworkAppender(this.config.network))
    }
  }

  /**
   * 设置全局错误处理
   */
  private setupGlobalErrorHandling(): void {
    if (!this.config.errorTracking.enabled) return
    // 微信小程序环境勿重写 console.error（会把原生参数拆成 [] [object Object]）
    // Promise / Vue 错误统一由 App.vue、main.ts 里字符串化后打印
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 生成会话ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 格式化时间
   */
  private formatTime(timestamp: number): string {
    const date = new Date(timestamp)
    return date.toISOString()
  }

  /**
   * 获取当前页面路径
   */
  private getCurrentPagePath(): string {
    try {
      const pages = getCurrentPages()
      if (pages.length > 0) {
        return pages[pages.length - 1].route || 'unknown'
      }
    } catch (error) {
      // 在某些环境下getCurrentPages可能不可用
    }
    return 'unknown'
  }

  /**
   * 收集设备信息
   */
  private collectDeviceInfo(): DeviceInfo {
    try {
      // #ifdef MP-WEIXIN
      const wxAny = typeof wx !== 'undefined' ? (wx as any) : undefined
      const deviceInfo = wxAny?.getDeviceInfo?.() || {}
      const windowInfo = wxAny?.getWindowInfo?.() || {}
      const appBaseInfo = wxAny?.getAppBaseInfo?.() || {}
      return {
        brand: deviceInfo.brand || 'unknown',
        model: deviceInfo.model || 'unknown',
        system: deviceInfo.system || 'unknown',
        version: appBaseInfo.SDKVersion || appBaseInfo.version || 'unknown',
        screen: {
          width: windowInfo.screenWidth || windowInfo.windowWidth || 0,
          height: windowInfo.screenHeight || windowInfo.windowHeight || 0,
          pixelRatio: windowInfo.pixelRatio || 1
        },
        networkType: 'unknown'
      }
      // #endif

      // #ifndef MP-WEIXIN
      const systemInfo = uni.getSystemInfoSync()
      return {
        brand: systemInfo.brand || 'unknown',
        model: systemInfo.model || 'unknown',
        system: systemInfo.system || 'unknown',
        version: systemInfo.version || 'unknown',
        screen: {
          width: systemInfo.screenWidth || 0,
          height: systemInfo.screenHeight || 0,
          pixelRatio: systemInfo.pixelRatio || 1
        },
        networkType: 'unknown' // 需要异步获取
      }
      // #endif
    } catch (error) {
      return {
        brand: 'unknown',
        model: 'unknown',
        system: 'unknown',
        version: 'unknown',
        screen: { width: 0, height: 0, pixelRatio: 1 },
        networkType: 'unknown'
      }
    }
  }

  /**
   * 清理过期日志
   */
  private async cleanupExpiredLogs(): Promise<void> {
    try {
      const storageAppender = this.appenders.get('storage') as StorageAppender
      if (storageAppender && storageAppender.cleanup) {
        await storageAppender.cleanup()
      }
    } catch (error) {
      console.error('Failed to cleanup expired logs:', error)
    }
  }

  /**
   * 发射事件
   */
  private emitEvent(event: LogEvent, data?: any): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener.listener(data)
        } catch (error) {
          console.error(`Event listener error for ${event}:`, error)
        }
      })
    }
  }

  /**
   * 添加事件监听器
   */
  addEventListener(event: LogEvent, listener: (data?: any) => void): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push({ event, listener })
  }

  /**
   * 移除事件监听器
   */
  removeEventListener(event: LogEvent, listener: (data?: any) => void): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      const index = listeners.findIndex(l => l.listener === listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * 销毁日志器
   */
  async dispose(): Promise<void> {
    for (const appender of this.appenders.values()) {
      if (appender.dispose) {
        try {
          await appender.dispose()
        } catch (error) {
          console.error('Failed to dispose appender:', error)
        }
      }
    }
    this.appenders.clear()
    this.eventListeners.clear()
    this.isInitialized = false
  }
}

/**
 * 控制台输出器
 */
class ConsoleAppender implements LogAppender {
  name = 'console'
  minLevel: LogLevel = 'debug'

  constructor(private config: any) {}

  append(entry: LogEntry): void {
    const message = this.formatMessage(entry)
    const text = typeof message === 'string' ? message : safeConsoleText(message)

    switch (entry.level) {
      case 'debug':
        console.debug(text)
        break
      case 'info':
        console.info(text)
        break
      case 'warn':
        console.warn(text)
        break
      case 'error':
      case 'fatal':
        console.error(text)
        if (entry.stack) {
          console.error(String(entry.stack))
        }
        break
    }
  }

  private formatMessage(entry: LogEntry): string {
    const parts: string[] = []

    if (this.config.showTimestamp) {
      parts.push(`[${entry.timeString}]`)
    }

    if (this.config.showLevel) {
      parts.push(`[${String(entry.level).toUpperCase()}]`)
    }

    if (this.config.showCategory) {
      parts.push(`[${entry.category}]`)
    }

    parts.push(typeof entry.message === 'string' ? entry.message : safeConsoleText(entry.message))

    if (entry.data !== undefined && entry.data !== null) {
      parts.push(safeConsoleText(entry.data))
    }

    return parts.join(' ')
  }
}

/**
 * 存储输出器
 */
class StorageAppender implements LogAppender {
  name = 'storage'
  minLevel: LogLevel = 'info'
  private logBuffer: LogEntry[] = []

  constructor(private config: any) {}

  async append(entry: LogEntry): Promise<void> {
    this.logBuffer.push(entry)
    
    // 达到批量大小时写入存储
    if (this.logBuffer.length >= 10) {
      await this.flush()
    }
  }

  async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return

    try {
      const existingLogs = this.getStoredLogs()
      const newLogs = [...existingLogs, ...this.logBuffer]
      
      // 限制存储数量
      if (newLogs.length > this.config.maxSize) {
        newLogs.splice(0, newLogs.length - this.config.maxSize)
      }
      
      uni.setStorageSync(`${this.config.keyPrefix}_logs`, JSON.stringify(newLogs))
      this.logBuffer = []
    } catch (error) {
      console.error('Failed to save logs to storage:', error)
    }
  }

  async cleanup(): Promise<void> {
    try {
      const logs = this.getStoredLogs()
      const now = Date.now()
      const validLogs = logs.filter(log => 
        now - log.timestamp < this.config.expireTime
      )
      
      if (validLogs.length !== logs.length) {
        uni.setStorageSync(`${this.config.keyPrefix}_logs`, JSON.stringify(validLogs))
      }
    } catch (error) {
      console.error('Failed to cleanup logs:', error)
    }
  }

  private getStoredLogs(): LogEntry[] {
    try {
      const data = uni.getStorageSync(`${this.config.keyPrefix}_logs`)
      return data ? JSON.parse(data) : []
    } catch (error) {
      return []
    }
  }

  async dispose(): Promise<void> {
    await this.flush()
  }
}

/**
 * 网络输出器
 */
class NetworkAppender implements LogAppender {
  name = 'network'
  minLevel: LogLevel = 'warn'
  private uploadBuffer: LogEntry[] = []
  private uploadTimer?: number

  constructor(private config: any) {
    this.startUploadTimer()
  }

  append(entry: LogEntry): void {
    this.uploadBuffer.push(entry)
    
    if (this.uploadBuffer.length >= this.config.batchSize) {
      this.uploadLogs()
    }
  }

  private startUploadTimer(): void {
    this.uploadTimer = setInterval(() => {
      if (this.uploadBuffer.length > 0) {
        this.uploadLogs()
      }
    }, this.config.uploadInterval) as any
  }

  private async uploadLogs(): Promise<void> {
    if (this.uploadBuffer.length === 0) return

    const logsToUpload = [...this.uploadBuffer]
    this.uploadBuffer = []

    try {
      await uni.request({
        url: this.config.uploadUrl,
        method: 'POST',
        data: { logs: logsToUpload },
        header: this.config.headers
      })
    } catch (error) {
      console.error('Failed to upload logs:', error)
      // 上传失败时重新加入缓冲区
      this.uploadBuffer.unshift(...logsToUpload)
    }
  }

  dispose(): void {
    if (this.uploadTimer) {
      clearInterval(this.uploadTimer)
    }
    if (this.uploadBuffer.length > 0) {
      this.uploadLogs()
    }
  }
}

/**
 * 默认日志格式化器
 */
class DefaultLogFormatter implements LogFormatter {
  name = 'default'

  format(entry: LogEntry): string {
    return `[${entry.timeString}] [${entry.level.toUpperCase()}] [${entry.category}] ${entry.message}`
  }
}

/**
 * 全局日志实例
 */
export const logger = new Logger()

/**
 * 快捷日志方法
 */
export const log = {
  debug: (category: LogCategory, message: string, data?: any) => logger.debug(category, message, data),
  info: (category: LogCategory, message: string, data?: any) => logger.info(category, message, data),
  warn: (category: LogCategory, message: string, data?: any) => logger.warn(category, message, data),
  error: (category: LogCategory, message: string, error?: any) => logger.error(category, message, error),
  fatal: (category: LogCategory, message: string, error?: any) => logger.fatal(category, message, error),
  api: (apiLog: Omit<ApiLogEntry, keyof BaseLogEntry>) => logger.logApi(apiLog),
  performance: (perfLog: Omit<PerformanceLogEntry, keyof BaseLogEntry>) => logger.logPerformance(perfLog),
  userAction: (actionLog: Omit<UserActionLogEntry, keyof BaseLogEntry>) => logger.logUserAction(actionLog),
  live: (liveLog: Omit<LiveLogEntry, keyof BaseLogEntry>) => logger.logLive(liveLog)
}

// 导出类型以供其他模块使用
export type { LogLevel, LogCategory, LogEntry, LogConfig }
