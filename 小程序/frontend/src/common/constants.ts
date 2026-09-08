/**
 * 全局常量定义
 * 定义应用中使用的所有常量值，包括配置、枚举、静态数据等
 */

// ================== 应用基础常量 ==================

/**
 * 应用信息
 */
export const APP_INFO = {
  /** 应用名称 */
  NAME: '医学直播SaaS平台',
  /** 应用版本 */
  VERSION: '1.0.0',
  /** 应用描述 */
  DESCRIPTION: '专业的医学直播服务平台',
  /** 应用作者 */
  AUTHOR: '医学直播团队',
  /** 应用官网 */
  WEBSITE: 'https://medical-live.com',
  /** 应用Logo */
  LOGO: '/static/images/logo.png'
} as const

/**
 * 环境配置
 */
export const ENV_CONFIG = {
  /** 开发环境 */
  DEVELOPMENT: 'development',
  /** 测试环境 */
  TESTING: 'testing',
  /** 预发布环境 */
  STAGING: 'staging',
  /** 生产环境 */
  PRODUCTION: 'production'
} as const

/**
 * 平台类型
 */
export const PLATFORM_TYPES = {
  /** H5网页 */
  H5: 'h5',
  /** 微信小程序 */
  MP_WEIXIN: 'mp-weixin',
  /** 支付宝小程序 */
  MP_ALIPAY: 'mp-alipay',
  /** 百度小程序 */
  MP_BAIDU: 'mp-baidu',
  /** 字节跳动小程序 */
  MP_TOUTIAO: 'mp-toutiao',
  /** QQ小程序 */
  MP_QQ: 'mp-qq',
  /** uni-app */
  APP_PLUS: 'app-plus',
  /** 快应用 */
  QUICKAPP: 'quickapp'
} as const

// ================== API相关常量 ==================

/**
 * API基础配置
 */
export const API_CONFIG = {
  /** 请求超时时间（毫秒） */
  TIMEOUT: 10000,
  /** 重试次数 */
  RETRY_COUNT: 3,
  /** 重试延迟（毫秒） */
  RETRY_DELAY: 1000,
  /** 分页大小 */
  PAGE_SIZE: 20,
  /** 最大分页大小 */
  MAX_PAGE_SIZE: 100
} as const

/**
 * HTTP状态码
 */
export const HTTP_STATUS = {
  /** 成功 */
  OK: 200,
  /** 创建成功 */
  CREATED: 201,
  /** 接受请求 */
  ACCEPTED: 202,
  /** 无内容 */
  NO_CONTENT: 204,
  /** 重定向 */
  REDIRECT: 302,
  /** 未修改 */
  NOT_MODIFIED: 304,
  /** 请求错误 */
  BAD_REQUEST: 400,
  /** 未授权 */
  UNAUTHORIZED: 401,
  /** 禁止访问 */
  FORBIDDEN: 403,
  /** 未找到 */
  NOT_FOUND: 404,
  /** 方法不允许 */
  METHOD_NOT_ALLOWED: 405,
  /** 请求超时 */
  REQUEST_TIMEOUT: 408,
  /** 冲突 */
  CONFLICT: 409,
  /** 内容过大 */
  PAYLOAD_TOO_LARGE: 413,
  /** 请求过于频繁 */
  TOO_MANY_REQUESTS: 429,
  /** 服务器错误 */
  INTERNAL_SERVER_ERROR: 500,
  /** 服务不可用 */
  SERVICE_UNAVAILABLE: 503,
  /** 网关超时 */
  GATEWAY_TIMEOUT: 504
} as const

/**
 * 业务状态码
 */
export const BUSINESS_CODE = {
  /** 成功 */
  SUCCESS: 200,
  /** 失败 */
  FAIL: 400,
  /** 未授权 */
  UNAUTHORIZED: 401,
  /** 禁止访问 */
  FORBIDDEN: 403,
  /** 资源不存在 */
  NOT_FOUND: 404,
  /** 服务器错误 */
  SERVER_ERROR: 500,
  /** Token过期 */
  TOKEN_EXPIRED: 4001,
  /** 账号被禁用 */
  ACCOUNT_DISABLED: 4002,
  /** 权限不足 */
  PERMISSION_DENIED: 4003,
  /** 参数错误 */
  PARAM_ERROR: 4004,
  /** 业务逻辑错误 */
  BUSINESS_ERROR: 4005
} as const

// ================== 存储相关常量 ==================

/**
 * 存储键名
 */
export const STORAGE_KEYS = {
  /** 访问令牌 */
  ACCESS_TOKEN: 'access_token',
  /** 刷新令牌 */
  REFRESH_TOKEN: 'refresh_token',
  /** 用户信息 */
  USER_INFO: 'user_info',
  /** 用户设置 */
  USER_SETTINGS: 'user_settings',
  /** 主题模式 */
  THEME_MODE: 'theme_mode',
  /** 语言设置 */
  LANGUAGE: 'language',
  /** 搜索历史 */
  SEARCH_HISTORY: 'search_history',
  /** 浏览历史 */
  BROWSE_HISTORY: 'browse_history',
  /** 收藏列表 */
  FAVORITES: 'favorites',
  MY_LIVE_CACHE: 'my_live_cache',
  /** 本地缓存版本 */
  CACHE_VERSION: 'cache_version',
  /** 应用配置缓存 */
  APP_CONFIG_CACHE: 'app_config_cache',
  /** 用户权限缓存 */
  USER_PERMISSIONS: 'user_permissions'
} as const

/**
 * 缓存过期时间（毫秒）
 */
export const CACHE_EXPIRES = {
  /** 1分钟 */
  MINUTE: 60 * 1000,
  /** 5分钟 */
  MINUTE_5: 5 * 60 * 1000,
  /** 15分钟 */
  MINUTE_15: 15 * 60 * 1000,
  /** 30分钟 */
  MINUTE_30: 30 * 60 * 1000,
  /** 1小时 */
  HOUR: 60 * 60 * 1000,
  /** 6小时 */
  HOUR_6: 6 * 60 * 60 * 1000,
  /** 12小时 */
  HOUR_12: 12 * 60 * 60 * 1000,
  /** 1天 */
  DAY: 24 * 60 * 60 * 1000,
  /** 7天 */
  WEEK: 7 * 24 * 60 * 60 * 1000,
  /** 30天 */
  MONTH: 30 * 24 * 60 * 60 * 1000
} as const

// ================== 用户相关常量 ==================

/**
 * 用户角色
 */
export const USER_ROLES = {
  /** 超级管理员 */
  SUPER_ADMIN: 'super_admin',
  /** 平台管理员 */
  PLATFORM_ADMIN: 'platform_admin',
  /** 机构管理员 */
  ORG_ADMIN: 'org_admin',
  /** 专家医生 */
  EXPERT_DOCTOR: 'expert_doctor',
  /** 普通医生 */
  DOCTOR: 'doctor',
  /** 护士 */
  NURSE: 'nurse',
  /** 医学生 */
  MEDICAL_STUDENT: 'medical_student',
  /** 普通用户 */
  USER: 'user'
} as const

/**
 * 用户状态
 */
export const USER_STATUS = {
  /** 正常 */
  ACTIVE: 'active',
  /** 未激活 */
  INACTIVE: 'inactive',
  /** 已禁用 */
  DISABLED: 'disabled',
  /** 已删除 */
  DELETED: 'deleted'
} as const

/**
 * 认证类型
 */
export const AUTH_TYPES = {
  /** 手机号登录 */
  PHONE: 'phone',
  /** 邮箱登录 */
  EMAIL: 'email',
  /** 用户名登录 */
  USERNAME: 'username',
  /** 微信登录 */
  WECHAT: 'wechat',
  /** 第三方登录 */
  THIRD_PARTY: 'third_party'
} as const

// ================== 直播相关常量 ==================

/**
 * 直播间状态
 */
export const LIVE_ROOM_STATUS = {
  /** 未开始 */
  NOT_STARTED: 'not_started',
  /** 直播中 */
  LIVE: 'live',
  /** 暂停 */
  PAUSED: 'paused',
  /** 已结束 */
  ENDED: 'ended',
  /** 回放 */
  REPLAY: 'replay'
} as const

/**
 * 直播类型
 */
export const LIVE_TYPES = {
  /** 实时直播 */
  REAL_TIME: 'real_time',
  /** 点播 */
  VOD: 'vod',
  /** 录播 */
  RECORDED: 'recorded'
} as const

/**
 * 直播权限
 */
export const LIVE_PERMISSIONS = {
  /** 公开 */
  PUBLIC: 'public',
  /** 需要登录 */
  LOGIN_REQUIRED: 'login_required',
  /** 需要付费 */
  PAID: 'paid',
  /** 仅限会员 */
  VIP_ONLY: 'vip_only',
  /** 私有 */
  PRIVATE: 'private'
} as const

/**
 * 直播质量
 */
export const LIVE_QUALITY = {
  /** 流畅 */
  SMOOTH: 'smooth',
  /** 标清 */
  SD: 'sd',
  /** 高清 */
  HD: 'hd',
  /** 超清 */
  FHD: 'fhd',
  /** 4K */
  UHD: 'uhd'
} as const

// ================== 专家相关常量 ==================

/**
 * 专家认证状态
 */
export const EXPERT_STATUS = {
  /** 未认证 */
  UNVERIFIED: 'unverified',
  /** 认证中 */
  VERIFYING: 'verifying',
  /** 已认证 */
  VERIFIED: 'verified',
  /** 认证失败 */
  REJECTED: 'rejected'
} as const

/**
 * 专业职称
 */
export const PROFESSIONAL_TITLES = {
  /** 住院医师 */
  RESIDENT: 'resident',
  /** 主治医师 */
  ATTENDING: 'attending',
  /** 副主任医师 */
  ASSOCIATE_CHIEF: 'associate_chief',
  /** 主任医师 */
  CHIEF: 'chief',
  /** 教授 */
  PROFESSOR: 'professor',
  /** 院士 */
  ACADEMICIAN: 'academician'
} as const

/**
 * 医学科室
 */
export const MEDICAL_DEPARTMENTS = {
  /** 内科 */
  INTERNAL_MEDICINE: 'internal_medicine',
  /** 外科 */
  SURGERY: 'surgery',
  /** 儿科 */
  PEDIATRICS: 'pediatrics',
  /** 妇产科 */
  OBSTETRICS_GYNECOLOGY: 'obstetrics_gynecology',
  /** 神经科 */
  NEUROLOGY: 'neurology',
  /** 心血管科 */
  CARDIOLOGY: 'cardiology',
  /** 呼吸科 */
  RESPIRATORY: 'respiratory',
  /** 消化科 */
  GASTROENTEROLOGY: 'gastroenterology',
  /** 内分泌科 */
  ENDOCRINOLOGY: 'endocrinology',
  /** 肿瘤科 */
  ONCOLOGY: 'oncology',
  /** 急诊科 */
  EMERGENCY: 'emergency',
  /** 重症医学科 */
  ICU: 'icu'
} as const

// ================== 订单支付常量 ==================

/**
 * 订单状态
 */
export const ORDER_STATUS = {
  /** 待支付 */
  PENDING: 'pending',
  /** 已支付 */
  PAID: 'paid',
  /** 已取消 */
  CANCELLED: 'cancelled',
  /** 已退款 */
  REFUNDED: 'refunded',
  /** 退款中 */
  REFUNDING: 'refunding'
} as const

/**
 * 支付方式
 */
export const PAYMENT_METHODS = {
  /** 微信支付 */
  WECHAT_PAY: 'wechat_pay',
  /** 支付宝 */
  ALIPAY: 'alipay',
  /** 银行卡 */
  BANK_CARD: 'bank_card',
  /** 余额支付 */
  BALANCE: 'balance',
  /** 积分支付 */
  POINTS: 'points'
} as const

// ================== 消息通知常量 ==================

/**
 * 消息类型
 */
export const MESSAGE_TYPES = {
  /** 系统消息 */
  SYSTEM: 'system',
  /** 直播通知 */
  LIVE_NOTICE: 'live_notice',
  /** 课程提醒 */
  COURSE_REMINDER: 'course_reminder',
  /** 关注通知 */
  FOLLOW_NOTICE: 'follow_notice',
  /** 评论回复 */
  COMMENT_REPLY: 'comment_reply',
  /** 私信 */
  PRIVATE_MESSAGE: 'private_message'
} as const

/**
 * 消息状态
 */
export const MESSAGE_STATUS = {
  /** 未读 */
  UNREAD: 'unread',
  /** 已读 */
  READ: 'read',
  /** 已删除 */
  DELETED: 'deleted'
} as const

// ================== 文件相关常量 ==================

/**
 * 文件类型
 */
export const FILE_TYPES = {
  /** 图片 */
  IMAGE: 'image',
  /** 视频 */
  VIDEO: 'video',
  /** 音频 */
  AUDIO: 'audio',
  /** 文档 */
  DOCUMENT: 'document',
  /** 压缩包 */
  ARCHIVE: 'archive'
} as const

/**
 * 图片格式
 */
export const IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'] as const

/**
 * 视频格式
 */
export const VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'] as const

/**
 * 文件大小限制（字节）
 */
export const FILE_SIZE_LIMITS = {
  /** 头像图片：2MB */
  AVATAR: 2 * 1024 * 1024,
  /** 普通图片：5MB */
  IMAGE: 5 * 1024 * 1024,
  /** 视频：100MB */
  VIDEO: 100 * 1024 * 1024,
  /** 音频：20MB */
  AUDIO: 20 * 1024 * 1024,
  /** 文档：10MB */
  DOCUMENT: 10 * 1024 * 1024
} as const

// ================== 正则表达式常量 ==================

/**
 * 常用正则表达式
 */
export const REGEX_PATTERNS = {
  /** 手机号 */
  PHONE: /^1[3-9]\d{9}$/,
  /** 邮箱 */
  EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  /** 身份证号 */
  ID_CARD: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
  /** 中文姓名 */
  CHINESE_NAME: /^[\u4e00-\u9fa5·]{2,20}$/,
  /** 用户名 */
  USERNAME: /^[a-zA-Z0-9_]{3,16}$/,
  /** 强密码 */
  STRONG_PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  /** URL */
  URL: /^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/,
  /** IP地址 */
  IP: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  /** 银行卡号 */
  BANK_CARD: /^[1-9]\d{12,19}$/,
  /** 微信号 */
  WECHAT_ID: /^[a-zA-Z][-_a-zA-Z0-9]{5,19}$/
} as const

// ================== 时间相关常量 ==================

/**
 * 时间格式
 */
export const TIME_FORMATS = {
  /** 日期时间 */
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  /** 日期 */
  DATE: 'YYYY-MM-DD',
  /** 时间 */
  TIME: 'HH:mm:ss',
  /** 简短时间 */
  TIME_SHORT: 'HH:mm',
  /** 中文日期时间 */
  DATETIME_CN: 'YYYY年M月D日 HH:mm',
  /** 中文日期 */
  DATE_CN: 'YYYY年M月D日',
  /** ISO格式 */
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ'
} as const

/**
 * 时区
 */
export const TIMEZONES = {
  /** 北京时间 */
  BEIJING: 'Asia/Shanghai',
  /** UTC时间 */
  UTC: 'UTC'
} as const

// ================== 错误信息常量 ==================

/**
 * 错误信息
 */
export const ERROR_MESSAGES = {
  /** 网络错误 */
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  /** 请求超时 */
  REQUEST_TIMEOUT: '请求超时，请稍后重试',
  /** 服务器错误 */
  SERVER_ERROR: '服务器繁忙，请稍后重试',
  /** 参数错误 */
  PARAM_ERROR: '参数错误',
  /** 未登录 */
  NOT_LOGIN: '请先登录',
  /** 无权限 */
  NO_PERMISSION: '暂无权限访问',
  /** Token过期 */
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  /** 账号被禁用 */
  ACCOUNT_DISABLED: '账号已被禁用',
  /** 验证码错误 */
  CAPTCHA_ERROR: '验证码错误',
  /** 验证码过期 */
  CAPTCHA_EXPIRED: '验证码已过期',
  /** 用户不存在 */
  USER_NOT_EXIST: '用户不存在',
  /** 密码错误 */
  PASSWORD_ERROR: '密码错误',
  /** 文件上传失败 */
  UPLOAD_FAILED: '文件上传失败',
  /** 文件格式不支持 */
  FILE_FORMAT_ERROR: '文件格式不支持',
  /** 文件大小超限 */
  FILE_SIZE_ERROR: '文件大小超过限制'
} as const

// ================== 成功信息常量 ==================

/**
 * 成功信息
 */
export const SUCCESS_MESSAGES = {
  /** 操作成功 */
  OPERATION_SUCCESS: '操作成功',
  /** 保存成功 */
  SAVE_SUCCESS: '保存成功',
  /** 删除成功 */
  DELETE_SUCCESS: '删除成功',
  /** 更新成功 */
  UPDATE_SUCCESS: '更新成功',
  /** 创建成功 */
  CREATE_SUCCESS: '创建成功',
  /** 登录成功 */
  LOGIN_SUCCESS: '登录成功',
  /** 注册成功 */
  REGISTER_SUCCESS: '注册成功',
  /** 发送成功 */
  SEND_SUCCESS: '发送成功',
  /** 复制成功 */
  COPY_SUCCESS: '复制成功',
  /** 收藏成功 */
  FAVORITE_SUCCESS: '收藏成功',
  /** 关注成功 */
  FOLLOW_SUCCESS: '关注成功'
} as const

// ================== 默认配置常量 ==================

/**
 * 默认配置
 */
export const DEFAULT_CONFIG = {
  /**
   * 默认头像（用户 / 留言作者 / 专家头像空值或加载失败）
   * 专用占位图：中性人像剪影，非 Mock 专家素材
   */
  DEFAULT_AVATAR: '/static/images/fallbacks/avatar-default.svg',
  /**
   * 缺省封面（无封面 URL）：浅灰简约「暂无封面」
   */
  DEFAULT_COVER: '/static/images/fallbacks/cover-default.jpg',
  /**
   * 封面加载失败（@error）：浅灰简约「加载失败」
   */
  COVER_LOAD_ERROR: '/static/images/fallbacks/cover-error.jpg',
  /**
   * 缺省品牌 Logo（无 logo URL）
   */
  DEFAULT_BRAND_LOGO: '/static/images/fallbacks/brand-logo-default.jpg',
  /**
   * 品牌 Logo 加载失败（@error）
   */
  BRAND_LOGO_LOAD_ERROR: '/static/images/fallbacks/brand-logo-error.jpg',
  /**
   * 首页焦点图 / Banner 缺省与加载失败（统一一张）
   */
  DEFAULT_BANNER: '/static/images/fallbacks/banner-default.jpg',
  /** 默认分页大小 */
  PAGE_SIZE: API_CONFIG.PAGE_SIZE,
  /** 默认主题 */
  DEFAULT_THEME: 'light',
  /** 默认语言 */
  DEFAULT_LANGUAGE: 'zh-CN',
  /** 默认时区 */
  DEFAULT_TIMEZONE: TIMEZONES.BEIJING
} as const

// ================== 导出所有常量 ==================

export default {
  APP_INFO,
  ENV_CONFIG,
  PLATFORM_TYPES,
  API_CONFIG,
  HTTP_STATUS,
  BUSINESS_CODE,
  STORAGE_KEYS,
  CACHE_EXPIRES,
  USER_ROLES,
  USER_STATUS,
  AUTH_TYPES,
  LIVE_ROOM_STATUS,
  LIVE_TYPES,
  LIVE_PERMISSIONS,
  LIVE_QUALITY,
  EXPERT_STATUS,
  PROFESSIONAL_TITLES,
  MEDICAL_DEPARTMENTS,
  ORDER_STATUS,
  PAYMENT_METHODS,
  MESSAGE_TYPES,
  MESSAGE_STATUS,
  FILE_TYPES,
  IMAGE_FORMATS,
  VIDEO_FORMATS,
  FILE_SIZE_LIMITS,
  REGEX_PATTERNS,
  TIME_FORMATS,
  TIMEZONES,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  DEFAULT_CONFIG
} as const
