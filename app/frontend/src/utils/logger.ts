/**
 * 日志工具
 * 提供生产环境日志控制和错误上报功能
 */

/**
 * 日志级别
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

/**
 * 日志管理器类
 */
class Logger {
  /** 是否为开发环境 */
  private isDev: boolean

  constructor() {
    // @ts-ignore - uni-app 环境变量
    this.isDev = import.meta.env.DEV || process.env.NODE_ENV === 'development'
  }

  /**
   * 初始化日志（占位，兼容调用方）
   */
  initialize(): Promise<void> {
    return Promise.resolve()
  }

  /**
   * 信息日志（与 log 一致，仅开发环境）
   */
  info(...args: any[]) {
    this.log(...args)
  }

  /**
   * 调试日志（仅开发环境）
   * @param args - 日志参数
   */
  debug(...args: any[]) {
    if (this.isDev) {
      console.log('[DEBUG]', ...args)
    }
  }

  /**
   * 信息日志（仅开发环境）
   * @param args - 日志参数
   */
  log(...args: any[]) {
    if (this.isDev) {
      console.log('[INFO]', ...args)
    }
  }

  /**
   * 警告日志（所有环境）
   * @param args - 日志参数
   */
  warn(...args: any[]) {
    console.warn('[WARN]', ...args)
    
    if (!this.isDev) {
      // 生产环境可以上报警告到监控服务
      this.reportToMonitor('warn', args)
    }
  }

  /**
   * 错误日志（所有环境）
   * @param args - 日志参数
   */
  error(...args: any[]) {
    console.error('[ERROR]', ...args)
    
    if (!this.isDev) {
      // 生产环境上报错误到监控服务
      this.reportError(args)
    }
  }

  /**
   * 上报错误到监控服务
   * @param args - 错误信息
   */
  private reportError(args: any[]) {
    try {
      // 构建错误信息
      const errorInfo = {
        level: 'error',
        message: args.map(arg => this.stringify(arg)).join(' '),
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      }

      // TODO: 集成实际的监控服务（如 Sentry、阿里云日志服务等）
      // 示例：
      // Sentry.captureException(errorInfo);
      // 或者发送到自己的日志服务器
      // fetch('/api/logs/error', {
      //   method: 'POST',
      //   body: JSON.stringify(errorInfo)
      // });

      console.log('[Logger] 错误已记录（待集成监控服务）:', errorInfo)
    } catch (e) {
      // 上报失败也不影响主流程
      console.error('[Logger] 上报错误失败:', e)
    }
  }

  /**
   * 上报到监控服务（通用）
   * @param level - 日志级别
   * @param args - 日志参数
   */
  private reportToMonitor(level: string, args: any[]) {
    try {
      const logInfo = {
        level,
        message: args.map(arg => this.stringify(arg)).join(' '),
        timestamp: new Date().toISOString()
      }

      // TODO: 集成实际的监控服务
      console.log('[Logger] 日志已记录（待集成监控服务）:', logInfo)
    } catch (e) {
      console.error('[Logger] 上报日志失败:', e)
    }
  }

  /**
   * 将任意类型转换为字符串
   * @param value - 任意值
   * @returns 字符串表示
   */
  private stringify(value: any): string {
    if (value === null) return 'null'
    if (value === undefined) return 'undefined'
    if (typeof value === 'string') return value
    if (typeof value === 'number' || typeof value === 'boolean') return String(value)
    
    try {
      return JSON.stringify(value)
    } catch (e) {
      return String(value)
    }
  }

  /**
   * 性能日志（记录函数执行时间）
   * @param label - 标签
   * @param fn - 要执行的函数
   * @returns 函数执行结果
   */
  async performance<T>(label: string, fn: () => Promise<T>): Promise<T> {
    const start = Date.now()
    
    try {
      const result = await fn()
      const duration = Date.now() - start
      
      if (this.isDev) {
        console.log(`[Performance] ${label}: ${duration}ms`)
      }
      
      return result
    } catch (error) {
      const duration = Date.now() - start
      this.error(`[Performance] ${label} 失败 (${duration}ms):`, error)
      throw error
    }
  }
}

/**
 * 导出单例实例
 */
export const logger = new Logger()

/**
 * 默认导出
 */
export default logger
