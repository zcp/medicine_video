/**
 * 通用工具函数
 * 提供项目中常用的工具函数和实用方法
 */

import { logger } from '@/logs/logger'

/**
 * 类型判断工具
 */
export const is = {
  /** 是否为字符串 */
  string: (val: unknown): val is string => typeof val === 'string',
  
  /** 是否为数字 */
  number: (val: unknown): val is number => typeof val === 'number',
  
  /** 是否为布尔值 */
  boolean: (val: unknown): val is boolean => typeof val === 'boolean',
  
  /** 是否为函数 */
  function: (val: unknown): val is Function => typeof val === 'function',
  
  /** 是否为对象 */
  object: (val: unknown): val is Record<any, any> => 
    val !== null && typeof val === 'object' && !Array.isArray(val),
  
  /** 是否为数组 */
  array: (val: unknown): val is any[] => Array.isArray(val),
  
  /** 是否为null */
  null: (val: unknown): val is null => val === null,
  
  /** 是否为undefined */
  undefined: (val: unknown): val is undefined => val === undefined,
  
  /** 是否为null或undefined */
  nullOrUndefined: (val: unknown): val is null | undefined => 
    val === null || val === undefined,
  
  /** 是否为空值 */
  empty: (val: unknown): boolean => {
    if (is.nullOrUndefined(val)) return true
    if (is.string(val)) return val.length === 0
    if (is.array(val)) return val.length === 0
    if (is.object(val)) return Object.keys(val).length === 0
    return false
  },
  
  /** 是否为Promise */
  promise: (val: unknown): val is Promise<any> => 
    is.object(val) && is.function((val as any).then),
  
  /** 是否为URL */
  url: (val: string): boolean => {
    try {
      new URL(val)
      return true
    } catch {
      return false
    }
  },
  
  /** 是否为移动设备 */
  mobile: (): boolean => {
    // #ifdef H5
    return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    // #endif
    
    // #ifdef MP-WEIXIN
    return true
    // #endif
    
    // #ifdef APP-PLUS
    return true
    // #endif
    
    return false
  },
  
  /** 是否为iOS */
  ios: (): boolean => {
    // #ifdef H5
    return /iPhone|iPad|iPod/i.test(navigator.userAgent)
    // #endif
    
    // #ifdef MP-WEIXIN
    try {
      const deviceInfo = (wx as any).getDeviceInfo?.()
      if (deviceInfo?.platform) return deviceInfo.platform === 'ios'
    } catch {
      // ignore
    }
    const systemInfo = uni.getSystemInfoSync()
    return systemInfo.platform === 'ios'
    // #endif
    
    // #ifdef APP-PLUS
    return uni.getSystemInfoSync().platform === 'ios'
    // #endif
    
    return false
  },
  
  /** 是否为Android */
  android: (): boolean => {
    // #ifdef H5
    return /Android/i.test(navigator.userAgent)
    // #endif
    
    // #ifdef MP-WEIXIN
    try {
      const deviceInfo = (wx as any).getDeviceInfo?.()
      if (deviceInfo?.platform) return deviceInfo.platform === 'android'
    } catch {
      // ignore
    }
    const systemInfo = uni.getSystemInfoSync()
    return systemInfo.platform === 'android'
    // #endif
    
    // #ifdef APP-PLUS
    return uni.getSystemInfoSync().platform === 'android'
    // #endif
    
    return false
  }
}

/**
 * 深拷贝
 * @param obj 要拷贝的对象
 * @returns 深拷贝后的对象
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as any
  }

  if (typeof obj === 'object') {
    const copy: any = {}
    Object.keys(obj).forEach(key => {
      copy[key] = deepClone((obj as any)[key])
    })
    return copy
  }

  return obj
}

/**
 * 防抖函数
 * @param func 要防抖的函数
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: number | undefined

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay) as any
  }
}

/**
 * 节流函数
 * @param func 要节流的函数
 * @param limit 时间间隔（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 生成唯一ID
 * @param prefix 前缀
 * @returns 唯一ID
 */
export function generateId(prefix: string = 'id'): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substr(2, 9)
  return `${prefix}_${timestamp}_${random}`
}

/**
 * 生成UUID
 * @returns UUID字符串
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * 随机字符串
 * @param length 长度
 * @param chars 字符集
 * @returns 随机字符串
 */
export function randomString(
  length: number = 8, 
  chars: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
): string {
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @param decimals 小数位数
 * @returns 格式化后的文件大小
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化数字
 * @param num 数字
 * @param decimals 小数位数
 * @returns 格式化后的数字
 */
export function formatNumber(num: number, decimals: number = 0): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(decimals) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K'
  } else {
    return num.toString()
  }
}

/**
 * 手机号脱敏
 * @param phone 手机号
 * @returns 脱敏后的手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 邮箱脱敏
 * @param email 邮箱
 * @returns 脱敏后的邮箱
 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email
  const [username, domain] = email.split('@')
  const maskedUsername = username.length > 3 
    ? username.slice(0, 2) + '***' + username.slice(-1)
    : username.slice(0, 1) + '***'
  return `${maskedUsername}@${domain}`
}

/**
 * 身份证脱敏
 * @param idCard 身份证号
 * @returns 脱敏后的身份证号
 */
export function maskIdCard(idCard: string): string {
  if (!idCard || idCard.length !== 18) return idCard
  return idCard.replace(/(\d{6})\d{8}(\d{4})/, '$1********$2')
}

/**
 * 树形数据扁平化
 * @param tree 树形数据
 * @param childrenKey 子节点字段名
 * @returns 扁平化数据
 */
export function flattenTree<T extends Record<string, any>>(
  tree: T[], 
  childrenKey: string = 'children'
): T[] {
  const result: T[] = []
  
  function traverse(nodes: T[]) {
    nodes.forEach(node => {
      const { [childrenKey]: children, ...rest } = node
      result.push(rest as T)
      
      if (children && Array.isArray(children)) {
        traverse(children)
      }
    })
  }
  
  traverse(tree)
  return result
}

/**
 * 扁平数据转树形
 * @param list 扁平数据
 * @param idKey ID字段名
 * @param parentKey 父ID字段名
 * @param childrenKey 子节点字段名
 * @returns 树形数据
 */
export function listToTree<T extends Record<string, any>>(
  list: T[],
  idKey: string = 'id',
  parentKey: string = 'parentId',
  childrenKey: string = 'children'
): T[] {
  const map = new Map<any, T>()
  const roots: T[] = []

  // 创建节点映射
  list.forEach(item => {
    map.set(item[idKey], { ...item, [childrenKey]: [] })
  })

  // 构建树形结构
  list.forEach(item => {
    const node = map.get(item[idKey])!
    const parentId = item[parentKey]
    
    if (parentId && map.has(parentId)) {
      const parent = map.get(parentId)! as any
      if (!parent[childrenKey]) {
        parent[childrenKey] = []
      }
      parent[childrenKey].push(node)
    } else {
      roots.push(node)
    }
  })

  return roots
}

/**
 * 对象数组按字段分组
 * @param list 对象数组
 * @param key 分组字段
 * @returns 分组结果
 */
export function groupBy<T extends Record<string, any>>(
  list: T[], 
  key: keyof T
): Record<string, T[]> {
  return list.reduce((groups, item) => {
    const value = item[key]
    const groupKey = String(value)
    
    if (!groups[groupKey]) {
      groups[groupKey] = []
    }
    
    groups[groupKey].push(item)
    return groups
  }, {} as Record<string, T[]>)
}

/**
 * 数组去重
 * @param arr 数组
 * @param key 对象数组时的去重字段
 * @returns 去重后的数组
 */
export function unique<T>(arr: T[], key?: keyof T): T[] {
  if (!key) {
    return [...new Set(arr)]
  }
  
  const seen = new Set()
  return arr.filter(item => {
    const value = item[key]
    if (seen.has(value)) {
      return false
    }
    seen.add(value)
    return true
  })
}

/**
 * 安全的JSON解析
 * @param str JSON字符串
 * @param defaultValue 解析失败时的默认值
 * @returns 解析结果
 */
export function safeJsonParse<T = any>(str: string, defaultValue: T): T {
  try {
    return JSON.parse(str)
  } catch (error) {
    logger.warn('system', 'JSON parse failed', { str, error })
    return defaultValue
  }
}

/**
 * 安全的JSON字符串化
 * @param obj 对象
 * @param defaultValue 字符串化失败时的默认值
 * @returns JSON字符串
 */
export function safeJsonStringify(obj: any, defaultValue: string = '{}'): string {
  try {
    return JSON.stringify(obj)
  } catch (error) {
    logger.warn('system', 'JSON stringify failed', { obj, error })
    return defaultValue
  }
}

/**
 * URL参数解析
 * @param url URL字符串
 * @returns 参数对象
 */
export function parseUrlParams(url: string): Record<string, string> {
  const params: Record<string, string> = {}
  const urlObj = new URL(url)
  
  urlObj.searchParams.forEach((value, key) => {
    params[key] = value
  })
  
  return params
}

/**
 * 构建URL参数
 * @param params 参数对象
 * @returns URL参数字符串
 */
export function buildUrlParams(params: Record<string, any>): string {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      searchParams.append(key, String(value))
    }
  })
  
  return searchParams.toString()
}

/**
 * 复制到剪贴板
 * @param text 要复制的文本
 * @returns 是否成功
 */
export function copyToClipboard(text: string): Promise<boolean> {
  return new Promise((resolve) => {
    uni.setClipboardData({
      data: text,
      success: () => {
        uni.showToast({
          title: '复制成功',
          icon: 'success'
        })
        resolve(true)
      },
      fail: () => {
        uni.showToast({
          title: '复制失败',
          icon: 'none'
        })
        resolve(false)
      }
    })
  })
}

/**
 * 预览图片
 * @param urls 图片URL数组
 * @param current 当前显示的图片索引或URL
 */
export function previewImages(urls: string[], current: number | string = 0): void {
  const currentUrl = typeof current === 'number' ? urls[current] : current
  
  uni.previewImage({
    urls,
    current: currentUrl,
    fail: (error) => {
      logger.error('ui', 'Preview image failed', { urls, current, error })
      uni.showToast({
        title: '图片预览失败',
        icon: 'none'
      })
    }
  })
}

/**
 * 获取系统信息
 * @returns 系统信息
 */
export function getSystemInfo(): Promise<UniApp.GetSystemInfoResult> {
  return new Promise((resolve, reject) => {
    uni.getSystemInfo({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 页面跳转
 * @param url 页面路径
 * @param type 跳转类型
 */
export function navigateTo(
  url: string, 
  type: 'navigateTo' | 'redirectTo' | 'reLaunch' | 'switchTab' = 'navigateTo'
): void {
  const options = {
    url,
    fail: (error: any) => {
      logger.error('ui', 'Navigate failed', { url, type, error })
      uni.showToast({
        title: '页面跳转失败',
        icon: 'none'
      })
    }
  }

  switch (type) {
    case 'navigateTo':
      uni.navigateTo(options)
      break
    case 'redirectTo':
      uni.redirectTo(options)
      break
    case 'reLaunch':
      uni.reLaunch(options)
      break
    case 'switchTab':
      uni.switchTab(options)
      break
  }
}

/**
 * 返回上一页
 * @param delta 返回层数
 */
export function navigateBack(delta: number = 1): void {
  uni.navigateBack({
    delta,
    fail: (error) => {
      logger.error('ui', 'Navigate back failed', { delta, error })
    }
  })
}

// 导出所有工具函数
export default {
  is,
  deepClone,
  debounce,
  throttle,
  generateId,
  generateUUID,
  randomString,
  formatFileSize,
  formatNumber,
  maskPhone,
  maskEmail,
  maskIdCard,
  flattenTree,
  listToTree,
  groupBy,
  unique,
  safeJsonParse,
  safeJsonStringify,
  parseUrlParams,
  buildUrlParams,
  copyToClipboard,
  previewImages,
  getSystemInfo,
  navigateTo,
  navigateBack
}
