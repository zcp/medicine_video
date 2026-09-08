/**
 * 应用基础常量
 * 零阶段：仅定义日志和安全相关常量
 * 阶段一：添加API、分页等业务常量
 */

// ===== 应用信息 =====
export const APP_NAME = '直播SaaS平台'
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0'

// ===== 日志相关 =====
export const LOG_STORAGE_KEY = 'app_logs'
export const MAX_LOG_ENTRIES = 1000
export const LOG_BATCH_SIZE = parseInt(import.meta.env.VITE_LOG_BATCH_SIZE || '20')
export const LOG_REPORT_INTERVAL = parseInt(import.meta.env.VITE_LOG_INTERVAL || '60000')

// ===== 安全相关 =====
export const SENSITIVE_FIELD_KEYS = [
  'password',
  'token',
  'accessToken',
  'refreshToken',
  'phone',
  'mobile',
  'idCard',
  'idcard',
  'email',
  'patientName',
  'medicalRecord'
]

export const PHONE_REGEX = /^1[3-9]\d{9}$/
export const ID_CARD_REGEX = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/
export const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
