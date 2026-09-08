/**
 * 日志系统配置
 * 微信小程序环境下的日志系统完整配置
 */

import type {
  LogLevel,
  LogCategory,
  ConsoleAppenderConfig,
  StorageAppenderConfig,
  NetworkAppenderConfig
} from './logTypes'

/**
 * 日志系统主配置接口
 */
export interface LogConfig {
  /** 全局日志级别 */
  level: LogLevel
  /** 是否启用日志 */
  enabled: boolean
  /** 开发模式 */
  development: boolean
  /** 应用版本 */
  appVersion?: string
  /** 分类配置 */
  categories: LogCategoryConfig[]
  /** 控制台输出器配置 */
  console: ConsoleAppenderConfig
  /** 存储输出器配置 */
  storage: StorageAppenderConfig
  /** 网络输出器配置 */
  network: NetworkAppenderConfig
  /** 性能监控配置 */
  performance: PerformanceConfig
  /** 错误监控配置 */
  errorTracking: ErrorTrackingConfig
  /** 用户行为追踪配置 */
  userTracking: UserTrackingConfig
}

/**
 * 分类配置接口
 */
export interface LogCategoryConfig {
  /** 分类名称 */
  category: LogCategory
  /** 分类级别 */
  level: LogLevel
  /** 是否启用 */
  enabled: boolean
  /** 输出器列表 */
  appenders: string[]
  /** 是否采样 */
  sampling?: {
    rate: number // 采样率 0-1
    maxPerSecond: number // 每秒最大条数
  }
}

/**
 * 性能监控配置
 */
export interface PerformanceConfig {
  /** 是否启用 */
  enabled: boolean
  /** 页面加载时间监控 */
  pageLoad: boolean
  /** API响应时间监控 */
  apiResponse: boolean
  /** 内存使用监控 */
  memoryUsage: boolean
  /** FPS监控 */
  fps: boolean
  /** 采样率 */
  samplingRate: number
}

/**
 * 错误追踪配置
 */
export interface ErrorTrackingConfig {
  /** 是否启用 */
  enabled: boolean
  /** 自动捕获未处理的错误 */
  captureUnhandled: boolean
  /** 自动捕获Promise拒绝 */
  captureRejections: boolean
  /** 是否收集堆栈信息 */
  collectStackTrace: boolean
  /** 错误上报阈值 */
  reportThreshold: number
  /** 忽略的错误模式 */
  ignorePatterns: string[]
}

/**
 * 用户行为追踪配置
 */
export interface UserTrackingConfig {
  /** 是否启用 */
  enabled: boolean
  /** 页面访问追踪 */
  pageView: boolean
  /** 按钮点击追踪 */
  buttonClick: boolean
  /** 表单提交追踪 */
  formSubmit: boolean
  /** 滚动行为追踪 */
  scroll: boolean
  /** 采样率 */
  samplingRate: number
}

/**
 * 默认配置
 */
export const DEFAULT_LOG_CONFIG: LogConfig = {
  // 全局配置
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  enabled: true,
  development: process.env.NODE_ENV === 'development',

  // 分类配置
  categories: [
    {
      category: 'system',
      level: 'info',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'user',
      level: 'info', 
      enabled: true,
      appenders: ['storage', 'network'],
      sampling: {
        rate: 0.1, // 10%采样
        maxPerSecond: 10
      }
    },
    {
      category: 'api',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'performance',
      level: 'info',
      enabled: true,
      appenders: ['storage', 'network'],
      sampling: {
        rate: 0.05, // 5%采样
        maxPerSecond: 5
      }
    },
    {
      category: 'error',
      level: 'error',
      enabled: true,
      appenders: ['console', 'storage', 'network']
    },
    {
      category: 'business',
      level: 'info',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'ui',
      level: 'debug',
      enabled: process.env.NODE_ENV === 'development',
      appenders: ['console']
    },
    {
      category: 'network',
      level: 'info',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'storage',
      level: 'debug',
      enabled: process.env.NODE_ENV === 'development',
      appenders: ['console']
    },
    {
      category: 'live',
      level: 'info',
      enabled: true,
      appenders: ['console', 'storage', 'network']
    }
  ],

  // 控制台输出器配置
  console: {
    colorEnabled: true,
    showTimestamp: true,
    showLevel: true,
    showCategory: true,
    timestampFormat: 'HH:mm:ss.SSS'
  },

  // 存储输出器配置
  storage: {
    keyPrefix: 'live_saas_log',
    maxSize: 1000, // 最多存储1000条日志
    compress: false, // 微信小程序环境暂不压缩
    expireTime: 7 * 24 * 60 * 60 * 1000 // 7天过期
  },

  // 网络输出器配置
  network: {
    uploadUrl: '/api/v1/logs/upload',
    batchSize: 50,
    uploadInterval: 30 * 1000, // 30秒上传一次
    retryCount: 3,
    headers: {
      'Content-Type': 'application/json'
    }
  },

  // 性能监控配置
  performance: {
    enabled: true,
    pageLoad: true,
    apiResponse: true,
    memoryUsage: process.env.NODE_ENV === 'development',
    fps: false, // 微信小程序不支持
    samplingRate: 0.1 // 10%采样
  },

  // 错误追踪配置
  errorTracking: {
    enabled: true,
    captureUnhandled: true,
    captureRejections: true,
    collectStackTrace: true,
    reportThreshold: 1, // 所有错误都上报
    ignorePatterns: [
      'Script error',
      'Non-Error promise rejection captured'
    ]
  },

  // 用户行为追踪配置
  userTracking: {
    enabled: true,
    pageView: true,
    buttonClick: true,
    formSubmit: true,
    scroll: false, // 微信小程序中谨慎使用
    samplingRate: 0.2 // 20%采样
  }
}

/**
 * 生产环境配置
 */
export const PRODUCTION_LOG_CONFIG: Partial<LogConfig> = {
  level: 'warn',
  categories: [
    {
      category: 'system',
      level: 'warn',
      enabled: true,
      appenders: ['storage', 'network']
    },
    {
      category: 'user',
      level: 'info',
      enabled: true,
      appenders: ['network'],
      sampling: {
        rate: 0.05, // 5%采样
        maxPerSecond: 5
      }
    },
    {
      category: 'api',
      level: 'warn',
      enabled: true,
      appenders: ['storage', 'network']
    },
    {
      category: 'performance',
      level: 'info',
      enabled: true,
      appenders: ['network'],
      sampling: {
        rate: 0.02, // 2%采样
        maxPerSecond: 2
      }
    },
    {
      category: 'error',
      level: 'error',
      enabled: true,
      appenders: ['storage', 'network']
    },
    {
      category: 'business',
      level: 'warn',
      enabled: true,
      appenders: ['network']
    },
    {
      category: 'ui',
      level: 'error',
      enabled: false,
      appenders: []
    },
    {
      category: 'network',
      level: 'error',
      enabled: true,
      appenders: ['storage', 'network']
    },
    {
      category: 'storage',
      level: 'error',
      enabled: true,
      appenders: ['network']
    },
    {
      category: 'live',
      level: 'info',
      enabled: true,
      appenders: ['storage', 'network']
    }
  ],
  console: {
    colorEnabled: false,
    showTimestamp: false,
    showLevel: true,
    showCategory: true,
    timestampFormat: 'YYYY-MM-DD HH:mm:ss'
  }
}

/**
 * 开发环境配置
 */
export const DEVELOPMENT_LOG_CONFIG: Partial<LogConfig> = {
  level: 'debug',
  // 开发环境禁用网络日志上传
  categories: [
    {
      category: 'system',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage'] // 移除 network
    },
    {
      category: 'user',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage'] // 移除 network
    },
    {
      category: 'api',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'performance',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage'] // 移除 network
    },
    {
      category: 'error',
      level: 'error',
      enabled: true,
      appenders: ['console', 'storage'] // 移除 network，开发环境不上传错误
    },
    {
      category: 'business',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'ui',
      level: 'debug',
      enabled: true,
      appenders: ['console'] // UI日志只输出到控制台
    },
    {
      category: 'network',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage']
    },
    {
      category: 'storage',
      level: 'debug',
      enabled: true,
      appenders: ['console']
    },
    {
      category: 'live',
      level: 'debug',
      enabled: true,
      appenders: ['console', 'storage'] // 移除 network
    }
  ],
  // 开发环境禁用网络上传器
  network: {
    uploadUrl: '', // 空字符串表示禁用网络上传
    batchSize: 50,
    uploadInterval: 30 * 1000,
    retryCount: 0, // 开发环境不重试
    headers: {
      'Content-Type': 'application/json'
    }
  },
  performance: {
    enabled: true,
    pageLoad: true,
    apiResponse: true,
    memoryUsage: true,
    fps: false,
    samplingRate: 1.0 // 100%采样
  },
  userTracking: {
    enabled: true,
    pageView: true,
    buttonClick: true,
    formSubmit: true,
    scroll: true,
    samplingRate: 1.0 // 100%采样
  }
}

/**
 * 获取当前环境配置
 */
export function getLogConfig(): LogConfig {
  const baseConfig = { ...DEFAULT_LOG_CONFIG }
  
  if (process.env.NODE_ENV === 'production') {
    return mergeConfig(baseConfig, PRODUCTION_LOG_CONFIG)
  } else {
    return mergeConfig(baseConfig, DEVELOPMENT_LOG_CONFIG)
  }
}

/**
 * 合并配置
 */
function mergeConfig(base: LogConfig, override: Partial<LogConfig>): LogConfig {
  const merged = { ...base } as any
  
  Object.keys(override).forEach(key => {
    const value = override[key as keyof LogConfig]
    if (value !== undefined) {
      if (typeof value === 'object' && !Array.isArray(value)) {
        merged[key] = {
          ...(merged[key] || {}),
          ...value
        }
      } else {
        merged[key] = value
      }
    }
  })
  
  return merged as LogConfig
}

/**
 * 配置验证
 */
export function validateConfig(config: LogConfig): string[] {
  const errors: string[] = []
  
  // 验证级别
  const validLevels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'fatal']
  if (!validLevels.includes(config.level)) {
    errors.push(`Invalid log level: ${config.level}`)
  }
  
  // 验证分类配置
  config.categories.forEach((category, index) => {
    if (!validLevels.includes(category.level)) {
      errors.push(`Invalid level in category[${index}]: ${category.level}`)
    }
    
    if (category.sampling) {
      if (category.sampling.rate < 0 || category.sampling.rate > 1) {
        errors.push(`Invalid sampling rate in category[${index}]: ${category.sampling.rate}`)
      }
      if (category.sampling.maxPerSecond <= 0) {
        errors.push(`Invalid maxPerSecond in category[${index}]: ${category.sampling.maxPerSecond}`)
      }
    }
  })
  
  // 验证存储配置
  if (config.storage.maxSize <= 0) {
    errors.push(`Invalid storage maxSize: ${config.storage.maxSize}`)
  }
  
  if (config.storage.expireTime <= 0) {
    errors.push(`Invalid storage expireTime: ${config.storage.expireTime}`)
  }
  
  // 验证网络配置
  if (config.network.batchSize <= 0) {
    errors.push(`Invalid network batchSize: ${config.network.batchSize}`)
  }
  
  if (config.network.uploadInterval <= 0) {
    errors.push(`Invalid network uploadInterval: ${config.network.uploadInterval}`)
  }
  
  return errors
}
