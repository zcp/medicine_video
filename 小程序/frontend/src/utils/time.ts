/**
 * 时间格式化工具
 * 基于dayjs的时间处理工具函数，支持格式化、相对时间、时区等功能
 */

import dayjs, { Dayjs } from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import 'dayjs/locale/zh-cn'

// 扩展dayjs插件
dayjs.extend(relativeTime)
dayjs.extend(timezone)
dayjs.extend(utc)
dayjs.extend(customParseFormat)
dayjs.locale('zh-cn')

/**
 * 时间输入类型
 */
export type TimeInput = string | number | Date | Dayjs

/**
 * 常用时间格式
 */
export const TIME_FORMATS = {
  /** 标准日期时间 2024-01-01 12:30:00 */
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  /** 日期 2024-01-01 */
  DATE: 'YYYY-MM-DD',
  /** 时间 12:30:00 */
  TIME: 'HH:mm:ss',
  /** 简短时间 12:30 */
  TIME_SHORT: 'HH:mm',
  /** 中文日期时间 2024年1月1日 12:30 */
  DATETIME_CN: 'YYYY年M月D日 HH:mm',
  /** 中文日期 2024年1月1日 */
  DATE_CN: 'YYYY年M月D日',
  /** ISO标准 2024-01-01T12:30:00.000Z */
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
  /** 月日 01-01 */
  MONTH_DAY: 'MM-DD',
  /** 年月 2024-01 */
  YEAR_MONTH: 'YYYY-MM'
}

/**
 * 时区枚举
 */
export const TIMEZONES = {
  /** 北京时间 */
  BEIJING: 'Asia/Shanghai',
  /** UTC时间 */
  UTC: 'UTC',
  /** 纽约时间 */
  NEW_YORK: 'America/New_York',
  /** 伦敦时间 */
  LONDON: 'Europe/London',
  /** 东京时间 */
  TOKYO: 'Asia/Tokyo'
}

/**
 * 获取当前时间
 */
export function now(): Dayjs {
  return dayjs()
}

/**
 * 格式化时间
 * @param time 时间输入
 * @param format 格式化字符串
 * @returns 格式化后的时间字符串
 */
export function formatTime(time?: TimeInput, format: string = TIME_FORMATS.DATETIME): string {
  return dayjs(time).format(format)
}

/**
 * 格式化为标准日期时间
 * @param time 时间输入
 * @returns YYYY-MM-DD HH:mm:ss 格式的字符串
 */
export function formatDateTime(time?: TimeInput): string {
  return formatTime(time, TIME_FORMATS.DATETIME)
}

/**
 * 格式化为日期
 * @param time 时间输入
 * @returns YYYY-MM-DD 格式的字符串
 */
export function formatDate(time?: TimeInput): string {
  return formatTime(time, TIME_FORMATS.DATE)
}

/**
 * 格式化为时间
 * @param time 时间输入
 * @param short 是否使用短格式
 * @returns HH:mm:ss 或 HH:mm 格式的字符串
 */
export function formatTimeOnly(time?: TimeInput, short: boolean = false): string {
  return formatTime(time, short ? TIME_FORMATS.TIME_SHORT : TIME_FORMATS.TIME)
}

/**
 * 格式化为中文日期时间
 * @param time 时间输入
 * @returns 2024年1月1日 12:30 格式的字符串
 */
export function formatDateTimeCN(time?: TimeInput): string {
  return formatTime(time, TIME_FORMATS.DATETIME_CN)
}

/**
 * 格式化为中文日期
 * @param time 时间输入
 * @returns 2024年1月1日 格式的字符串
 */
export function formatDateCN(time?: TimeInput): string {
  return formatTime(time, TIME_FORMATS.DATE_CN)
}

/**
 * 获取相对时间
 * @param time 时间输入
 * @param base 基准时间，默认为当前时间
 * @returns 相对时间字符串，如 "2小时前"
 */
export function getRelativeTime(time: TimeInput, base?: TimeInput): string {
  const target = dayjs(time)
  const baseTime = base ? dayjs(base) : dayjs()
  return target.from(baseTime)
}

/**
 * 获取友好的时间显示
 * @param time 时间输入
 * @returns 友好的时间字符串
 */
export function getFriendlyTime(time: TimeInput): string {
  const target = dayjs(time)
  const now = dayjs()
  const diffDays = now.diff(target, 'day')

  if (diffDays === 0) {
    // 今天
    const diffHours = now.diff(target, 'hour')
    if (diffHours === 0) {
      const diffMinutes = now.diff(target, 'minute')
      if (diffMinutes === 0) {
        return '刚刚'
      } else if (diffMinutes < 60) {
        return `${diffMinutes}分钟前`
      }
    }
    return target.format('今天 HH:mm')
  } else if (diffDays === 1) {
    // 昨天
    return target.format('昨天 HH:mm')
  } else if (diffDays === 2) {
    // 前天
    return target.format('前天 HH:mm')
  } else if (diffDays < 7) {
    // 一周内
    return target.format('dddd HH:mm')
  } else if (target.year() === now.year()) {
    // 同年
    return target.format('M月D日 HH:mm')
  } else {
    // 不同年
    return target.format('YYYY年M月D日')
  }
}

/**
 * 检查是否为今天
 * @param time 时间输入
 * @returns 是否为今天
 */
export function isToday(time: TimeInput): boolean {
  return dayjs(time).isSame(dayjs(), 'day')
}

/**
 * 检查是否为昨天
 * @param time 时间输入
 * @returns 是否为昨天
 */
export function isYesterday(time: TimeInput): boolean {
  return dayjs(time).isSame(dayjs().subtract(1, 'day'), 'day')
}

/**
 * 检查是否为本周
 * @param time 时间输入
 * @returns 是否为本周
 */
export function isThisWeek(time: TimeInput): boolean {
  return dayjs(time).isSame(dayjs(), 'week')
}

/**
 * 检查是否为本月
 * @param time 时间输入
 * @returns 是否为本月
 */
export function isThisMonth(time: TimeInput): boolean {
  return dayjs(time).isSame(dayjs(), 'month')
}

/**
 * 检查是否为本年
 * @param time 时间输入
 * @returns 是否为本年
 */
export function isThisYear(time: TimeInput): boolean {
  return dayjs(time).isSame(dayjs(), 'year')
}

/**
 * 获取时间差
 * @param start 开始时间
 * @param end 结束时间
 * @param unit 单位
 * @returns 时间差
 */
export function getTimeDiff(
  start: TimeInput, 
  end: TimeInput, 
  unit: 'millisecond' | 'second' | 'minute' | 'hour' | 'day' = 'millisecond'
): number {
  return dayjs(end).diff(dayjs(start), unit)
}

/**
 * 格式化时长
 * @param duration 时长（秒）
 * @returns 格式化后的时长字符串
 */
export function formatDuration(duration: number): string {
  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = duration % 60

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  } else {
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }
}

/**
 * 格式化文件大小时长
 * @param seconds 秒数
 * @returns 友好的时长显示
 */
export function formatFriendlyDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

/**
 * 获取时间范围
 * @param type 时间范围类型
 * @returns 开始和结束时间
 */
export function getTimeRange(type: 'today' | 'yesterday' | 'week' | 'month' | 'year'): {
  start: Dayjs
  end: Dayjs
} {
  const now = dayjs()

  switch (type) {
    case 'today':
      return {
        start: now.startOf('day'),
        end: now.endOf('day')
      }
    case 'yesterday':
      const yesterday = now.subtract(1, 'day')
      return {
        start: yesterday.startOf('day'),
        end: yesterday.endOf('day')
      }
    case 'week':
      return {
        start: now.startOf('week'),
        end: now.endOf('week')
      }
    case 'month':
      return {
        start: now.startOf('month'),
        end: now.endOf('month')
      }
    case 'year':
      return {
        start: now.startOf('year'),
        end: now.endOf('year')
      }
  }
}

/**
 * 时区转换
 * @param time 时间输入
 * @param targetTimezone 目标时区
 * @param sourceTimezone 源时区
 * @returns 转换后的时间
 */
export function convertTimezone(
  time: TimeInput, 
  targetTimezone: string = TIMEZONES.BEIJING,
  sourceTimezone?: string
): Dayjs {
  let target = dayjs(time)
  
  if (sourceTimezone) {
    target = target.tz(sourceTimezone)
  }
  
  return target.tz(targetTimezone)
}

/**
 * 获取UTC时间戳
 * @param time 时间输入
 * @returns UTC时间戳（毫秒）
 */
export function getUTCTimestamp(time?: TimeInput): number {
  return dayjs(time).utc().valueOf()
}

/**
 * 从UTC时间戳创建本地时间
 * @param timestamp UTC时间戳（毫秒）
 * @returns 本地时间
 */
export function fromUTCTimestamp(timestamp: number): Dayjs {
  return dayjs.utc(timestamp).local()
}

/**
 * 验证时间字符串格式
 * @param timeString 时间字符串
 * @param format 期望的格式
 * @returns 是否有效
 */
export function isValidTimeString(timeString: string, format?: string): boolean {
  return dayjs(timeString, format, true).isValid()
}

/**
 * 获取当前时区
 * @returns 时区字符串
 */
export function getCurrentTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/**
 * sleep函数
 * @param ms 毫秒数
 * @returns Promise
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 导出dayjs实例，供直接使用
export { dayjs }
export default {
  now,
  formatTime,
  formatDateTime,
  formatDate,
  formatTimeOnly,
  formatDateTimeCN,
  formatDateCN,
  getRelativeTime,
  getFriendlyTime,
  isToday,
  isYesterday,
  isThisWeek,
  isThisMonth,
  isThisYear,
  getTimeDiff,
  formatDuration,
  formatFriendlyDuration,
  getTimeRange,
  convertTimezone,
  getUTCTimestamp,
  fromUTCTimestamp,
  isValidTimeString,
  getCurrentTimezone,
  sleep
}
