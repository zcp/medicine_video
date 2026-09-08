/**
 * 轮询管理器
 * 提供智能轮询功能，支持页面可见性检测和网络状态检测
 */

import { logger } from './logger'

/**
 * 轮询配置选项
 */
export interface PollingOptions {
  /** 轮询间隔（毫秒） */
  interval: number
  /** 是否在页面不可见时停止轮询 */
  pauseWhenHidden?: boolean
  /** 是否在网络断开时停止轮询 */
  pauseWhenOffline?: boolean
  /** 页面重新可见时是否立即执行一次 */
  executeOnVisible?: boolean
  /** 网络恢复时是否立即执行一次 */
  executeOnOnline?: boolean
}

/**
 * 轮询管理器类
 */
export class PollingManager {
  /** 轮询间隔（毫秒） */
  private interval: number
  
  /** 定时器ID */
  private timerId: number | null = null
  
  /** 轮询回调函数 */
  private callback: (() => void | Promise<void>) | null = null
  
  /** 是否正在运行 */
  private running: boolean = false
  
  /** 配置选项 */
  private options: PollingOptions
  
  /** 页面可见性监听器 */
  private visibilityListener: (() => void) | null = null
  
  /** 网络状态监听器 */
  private onlineListener: (() => void) | null = null
  private offlineListener: (() => void) | null = null

  /**
   * 构造函数
   * @param interval - 轮询间隔（毫秒）
   * @param options - 配置选项
   */
  constructor(interval: number, options?: Partial<PollingOptions>) {
    this.interval = interval
    this.options = {
      interval,
      pauseWhenHidden: true,
      pauseWhenOffline: true,
      executeOnVisible: true,
      executeOnOnline: true,
      ...options
    }
  }

  /**
   * 开始轮询
   * @param callback - 轮询回调函数
   */
  start(callback: () => void | Promise<void>) {
    if (this.running) {
      logger.warn('[PollingManager] 轮询已在运行中')
      return
    }

    this.callback = callback
    this.running = true

    // 立即执行一次
    this.executeCallback()

    // 启动定时器
    this.startTimer()

    // 监听页面可见性变化（仅 H5 平台）
    if (this.options.pauseWhenHidden) {
      this.setupVisibilityListener()
    }

    // 监听网络状态变化
    if (this.options.pauseWhenOffline) {
      this.setupNetworkListeners()
    }

    logger.log('[PollingManager] 轮询已启动，间隔:', this.interval, 'ms')
  }

  /**
   * 停止轮询
   */
  stop() {
    if (!this.running) {
      return
    }

    this.running = false
    this.stopTimer()
    this.removeListeners()

    logger.log('[PollingManager] 轮询已停止')
  }

  /**
   * 启动定时器
   */
  private startTimer() {
    this.stopTimer()
    
    this.timerId = setInterval(() => {
      this.executeCallback()
    }, this.interval) as unknown as number
  }

  /**
   * 停止定时器
   */
  private stopTimer() {
    if (this.timerId !== null) {
      clearInterval(this.timerId)
      this.timerId = null
    }
  }

  /**
   * 执行回调函数
   */
  private async executeCallback() {
    if (!this.callback || !this.running) {
      return
    }

    try {
      await this.callback()
    } catch (error) {
      logger.error('[PollingManager] 轮询回调执行失败:', error)
    }
  }

  /**
   * 设置页面可见性监听器（仅 H5 平台）
   */
  private setupVisibilityListener() {
    // 检查是否支持 Page Visibility API
    if (typeof document === 'undefined' || !document.addEventListener) {
      return
    }

    this.visibilityListener = () => {
      if (document.hidden) {
        // 页面不可见，暂停轮询
        logger.log('[PollingManager] 页面不可见，暂停轮询')
        this.stopTimer()
      } else {
        // 页面可见，恢复轮询
        logger.log('[PollingManager] 页面可见，恢复轮询')
        
        // 立即执行一次（如果配置允许）
        if (this.options.executeOnVisible) {
          this.executeCallback()
        }
        
        this.startTimer()
      }
    }

    document.addEventListener('visibilitychange', this.visibilityListener)
  }

  /**
   * 设置网络状态监听器
   */
  private setupNetworkListeners() {
    // uni-app 网络状态监听
    this.onlineListener = () => {
      logger.log('[PollingManager] 网络已连接，恢复轮询')
      
      // 立即执行一次（如果配置允许）
      if (this.options.executeOnOnline) {
        this.executeCallback()
      }
      
      this.startTimer()
    }

    this.offlineListener = () => {
      logger.log('[PollingManager] 网络已断开，暂停轮询')
      this.stopTimer()
    }

    // 监听网络状态变化
    uni.onNetworkStatusChange((res) => {
      if (res.isConnected) {
        this.onlineListener?.()
      } else {
        this.offlineListener?.()
      }
    })
  }

  /**
   * 移除所有监听器
   */
  private removeListeners() {
    // 移除页面可见性监听器
    if (this.visibilityListener && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', this.visibilityListener)
      this.visibilityListener = null
    }

    // uni-app 的网络监听器无法直接移除，但停止轮询后不会再触发回调
    this.onlineListener = null
    this.offlineListener = null
  }

  /**
   * 更新轮询间隔
   * @param interval - 新的轮询间隔（毫秒）
   */
  updateInterval(interval: number) {
    this.interval = interval
    this.options.interval = interval
    
    if (this.running) {
      this.startTimer()
    }
    
    logger.log('[PollingManager] 轮询间隔已更新:', interval, 'ms')
  }

  /**
   * 检查是否正在运行
   */
  isRunning(): boolean {
    return this.running
  }
}

/**
 * 创建轮询管理器实例
 * @param interval - 轮询间隔（毫秒）
 * @param options - 配置选项
 * @returns 轮询管理器实例
 */
export function createPollingManager(interval: number, options?: Partial<PollingOptions>): PollingManager {
  return new PollingManager(interval, options)
}

/**
 * 默认导出
 */
export default PollingManager
