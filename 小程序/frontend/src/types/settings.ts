/**
 * 设置相关类型定义
 * 包含用户设置、系统配置、应用偏好等类型定义
 */

import { Language, ThemeMode } from './common'

/**
 * 通知设置
 */
export interface NotificationSettings {
  /** 推送通知 */
  push: boolean
  /** 邮件通知 */
  email: boolean
  /** 短信通知 */
  sms: boolean
  /** 应用内通知 */
  inApp: boolean
  /** 直播开始通知 */
  liveStart: boolean
  /** 关注专家动态 */
  expertUpdate: boolean
  /** 系统消息 */
  systemMessage: boolean
  /** 营销消息 */
  marketing: boolean
}

/**
 * 隐私设置
 */
export interface PrivacySettings {
  /** 显示手机号 */
  showPhone: boolean
  /** 显示邮箱 */
  showEmail: boolean
  /** 允许关注 */
  allowFollow: boolean
  /** 允许私信 */
  allowMessage: boolean
  /** 显示在线状态 */
  showOnlineStatus: boolean
  /** 允许搜索 */
  allowSearch: boolean
  /** 观看历史可见 */
  showWatchHistory: boolean
}

/**
 * 播放设置
 */
export interface PlaybackSettings {
  /** 自动播放 */
  autoplay: boolean
  /** 画质偏好 */
  qualityPreference: 'auto' | 'low' | 'medium' | 'high'
  /** 音量 */
  volume: number
  /** 静音 */
  muted: boolean
  /** 弹幕开关 */
  danmuEnabled: boolean
  /** 弹幕透明度 */
  danmuOpacity: number
  /** 弹幕速度 */
  danmuSpeed: number
  /** 硬件加速 */
  hardwareAcceleration: boolean
}

/**
 * 用户设置
 */
export interface UserSettings {
  /** 基本设置 */
  basic: {
    language: Language
    theme: ThemeMode
    timezone: string
  }
  /** 通知设置 */
  notifications: NotificationSettings
  /** 隐私设置 */
  privacy: PrivacySettings
  /** 播放设置 */
  playback: PlaybackSettings
  /** 个性化设置 */
  personalization: {
    recommendationEnabled: boolean
    dataCollectionEnabled: boolean
    targetedAdsEnabled: boolean
  }
}

/**
 * 系统配置
 */
export interface SystemConfig {
  /** 应用配置 */
  app: {
    name: string
    version: string
    description: string
    logo: string
    supportUrl: string
    privacyPolicyUrl: string
    termsOfServiceUrl: string
  }
  /** 功能开关 */
  features: {
    registration: boolean
    guestAccess: boolean
    socialLogin: boolean
    expertVerification: boolean
    liveStreaming: boolean
    comments: boolean
    ratings: boolean
  }
  /** 限制配置 */
  limits: {
    maxUploadSize: number
    maxVideoLength: number
    maxConcurrentViewers: number
    rateLimit: {
      requests: number
      window: number
    }
  }
}

/**
 * 更新设置请求
 */
export interface UpdateSettingsRequest {
  category: 'basic' | 'notifications' | 'privacy' | 'playback' | 'personalization'
  settings: Partial<UserSettings[keyof UserSettings]>
}

/**
 * 应用设置（别名，API兼容性）
 */
export interface AppSettings extends UserSettings {}

/**
 * 主题设置
 */
export interface ThemeSettings {
  /** 主题模式 */
  mode: ThemeMode
  /** 自定义主色 */
  primaryColor?: string
  /** 自定义背景 */
  backgroundColor?: string
  /** 字体大小 */
  fontSize: 'small' | 'medium' | 'large'
  /** 紧凑模式 */
  compactMode: boolean
  /** 暗色模式跟随系统 */
  followSystem: boolean
  /** 夜间模式时间 */
  nightModeSchedule?: {
    enabled: boolean
    startTime: string
    endTime: string
  }
}

/**
 * 账号安全设置
 */
export interface SecuritySettings {
  /** 两步验证 */
  twoFactorEnabled: boolean
  /** 登录提醒 */
  loginNotification: boolean
  /** 密码强度要求 */
  passwordStrength: 'weak' | 'medium' | 'strong'
  /** 会话超时时间（分钟） */
  sessionTimeout: number
  /** 允许的登录设备数 */
  maxDevices: number
  /** 自动登出 */
  autoLogout: boolean
}

/**
 * 数据同步设置
 */
export interface SyncSettings {
  /** 云同步开关 */
  enabled: boolean
  /** 同步历史记录 */
  syncHistory: boolean
  /** 同步收藏 */
  syncFavorites: boolean
  /** 同步设置 */
  syncPreferences: boolean
  /** 自动同步 */
  autoSync: boolean
  /** 同步频率 */
  syncFrequency: 'real-time' | 'hourly' | 'daily' | 'manual'
  /** 仅WiFi同步 */
  wifiOnly: boolean
}

/**
 * 缓存设置
 */
export interface CacheSettings {
  /** 缓存开关 */
  enabled: boolean
  /** 视频缓存大小（MB） */
  videoCacheSize: number
  /** 图片缓存大小（MB） */
  imageCacheSize: number
  /** 自动清理缓存 */
  autoClean: boolean
  /** 清理间隔（天） */
  cleanInterval: number
  /** 仅WiFi缓存 */
  wifiOnlyCache: boolean
}

/**
 * 可访问性设置
 */
export interface AccessibilitySettings {
  /** 高对比度 */
  highContrast: boolean
  /** 大字体 */
  largeText: boolean
  /** 屏幕朗读支持 */
  screenReader: boolean
  /** 减少动画 */
  reduceMotion: boolean
  /** 字幕显示 */
  showCaptions: boolean
  /** 键盘导航 */
  keyboardNavigation: boolean
}

/**
 * 实验性功能设置
 */
export interface ExperimentalSettings {
  /** 实验性功能开关 */
  enabled: boolean
  /** 启用的实验功能列表 */
  enabledFeatures: string[]
  /** 测试版本检查 */
  betaUpdates: boolean
  /** 错误报告 */
  errorReporting: boolean
  /** 使用统计 */
  usageStats: boolean
}

/**
 * 扩展的用户设置
 */
export interface ExtendedUserSettings extends UserSettings {
  /** 主题设置 */
  theme: ThemeSettings
  /** 安全设置 */
  security: SecuritySettings
  /** 同步设置 */
  sync: SyncSettings
  /** 缓存设置 */
  cache: CacheSettings
  /** 可访问性设置 */
  accessibility: AccessibilitySettings
  /** 实验性功能 */
  experimental: ExperimentalSettings
}

/**
 * 设置导入导出
 */
export interface SettingsImportExport {
  /** 导出设置 */
  export: {
    includeSensitive: boolean
    format: 'json' | 'xml'
    encryption: boolean
  }
  /** 导入设置 */
  import: {
    overwriteExisting: boolean
    skipInvalid: boolean
    backupBefore: boolean
  }
}

/**
 * 设置备份
 */
export interface SettingsBackup {
  id: string
  name: string
  description?: string
  settings: Partial<ExtendedUserSettings>
  createdAt: string
  size: number
  checksum: string
}

/**
 * 设置验证规则
 */
export interface SettingsValidation {
  field: string
  rules: Array<{
    type: 'required' | 'min' | 'max' | 'pattern'
    value?: any
    message: string
  }>
}
