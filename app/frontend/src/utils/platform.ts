/**
 * 平台检测与工具模块
 * 提供统一的平台判断API和平台特定功能
 * 支持 H5、App（Android/iOS）、微信小程序
 */

/**
 * 平台类型枚举
 */
export enum PlatformType {
  H5 = 'h5',
  APP = 'app',
  MP_WEIXIN = 'mp-weixin',
  MP_ALIPAY = 'mp-alipay',
  UNKNOWN = 'unknown'
}

/**
 * 判断是否为H5环境
 * @returns {boolean}
 * @example
 * if (isH5()) {
 *   // H5特有逻辑
 * }
 */
export const isH5 = (): boolean => {
  // #ifdef H5
  return true
  // #endif
  return false
}

/**
 * 判断是否为App环境
 * @returns {boolean}
 * @example
 * if (isApp()) {
 *   // App特有逻辑
 * }
 */
export const isApp = (): boolean => {
  // #ifdef APP-PLUS
  return true
  // #endif
  return false
}

/**
 * 判断是否为Android App
 * @returns {boolean}
 */
export const isAndroid = (): boolean => {
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync()
  return systemInfo.platform === 'android'
  // #endif
  return false
}

/**
 * 判断是否为iOS App
 * @returns {boolean}
 */
export const isIOS = (): boolean => {
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync()
  return systemInfo.platform === 'ios'
  // #endif
  return false
}

/**
 * 判断是否为微信小程序环境
 * @returns {boolean}
 */
export const isMiniProgram = (): boolean => {
  // #ifdef MP-WEIXIN
  return true
  // #endif
  return false
}

/**
 * 判断是否为支付宝小程序环境
 * @returns {boolean}
 */
export const isAlipayMiniProgram = (): boolean => {
  // #ifdef MP-ALIPAY
  return true
  // #endif
  return false
}

/**
 * 获取当前平台类型
 * @returns {PlatformType}
 * @example
 * const platform = getPlatform()
 * if (platform === PlatformType.H5) {
 *   // H5逻辑
 * }
 */
export const getPlatform = (): PlatformType => {
  // #ifdef H5
  return PlatformType.H5
  // #endif
  
  // #ifdef APP-PLUS
  return PlatformType.APP
  // #endif
  
  // #ifdef MP-WEIXIN
  return PlatformType.MP_WEIXIN
  // #endif
  
  // #ifdef MP-ALIPAY
  return PlatformType.MP_ALIPAY
  // #endif
  
  return PlatformType.UNKNOWN
}

/**
 * 获取平台显示名称
 * @returns {string}
 */
export const getPlatformName = (): string => {
  const platform = getPlatform()
  const names: Record<PlatformType, string> = {
    [PlatformType.H5]: 'H5网页',
    [PlatformType.APP]: 'App',
    [PlatformType.MP_WEIXIN]: '微信小程序',
    [PlatformType.MP_ALIPAY]: '支付宝小程序',
    [PlatformType.UNKNOWN]: '未知平台'
  }
  return names[platform]
}

/**
 * 平台配置接口
 */
export interface PlatformConfig {
  /** 视频播放器类型 */
  playerType: 'hls.js' | 'native' | 'mp'
  /** 图片上传方式 */
  uploadMethod: 'xhr' | 'chooseImage' | 'mp-upload'
  /** 是否支持原生能力 */
  hasNativeCapability: boolean
  /** 是否支持文件下载 */
  canDownload: boolean
  /** 最大并发请求数 */
  maxConcurrentRequests: number
}

/**
 * 获取平台配置
 * @returns {PlatformConfig}
 * @example
 * const config = getPlatformConfig()
 * if (config.playerType === 'hls.js') {
 *   // 使用 hls.js
 * }
 */
export const getPlatformConfig = (): PlatformConfig => {
  const platform = getPlatform()
  
  const configs: Record<PlatformType, PlatformConfig> = {
    [PlatformType.H5]: {
      playerType: 'hls.js',
      uploadMethod: 'xhr',
      hasNativeCapability: false,
      canDownload: true,
      maxConcurrentRequests: 6
    },
    [PlatformType.APP]: {
      playerType: 'native',
      uploadMethod: 'chooseImage',
      hasNativeCapability: true,
      canDownload: true,
      maxConcurrentRequests: 10
    },
    [PlatformType.MP_WEIXIN]: {
      playerType: 'mp',
      uploadMethod: 'mp-upload',
      hasNativeCapability: false,
      canDownload: false,
      maxConcurrentRequests: 5
    },
    [PlatformType.MP_ALIPAY]: {
      playerType: 'mp',
      uploadMethod: 'mp-upload',
      hasNativeCapability: false,
      canDownload: false,
      maxConcurrentRequests: 5
    },
    [PlatformType.UNKNOWN]: {
      playerType: 'native',
      uploadMethod: 'chooseImage',
      hasNativeCapability: false,
      canDownload: false,
      maxConcurrentRequests: 3
    }
  }
  
  return configs[platform]
}

/**
 * 动态导入平台组件
 * @param {string} componentName - 组件名称（不含后缀）
 * @returns {Promise<any>} 组件模块
 * @example
 * // 自动根据平台加载对应组件
 * const VideoPlayer = await importPlatformComponent('VideoPlayer')
 * // H5: components/h5/VideoPlayerH5.vue
 * // App: components/app/VideoPlayerApp.vue
 */
export const importPlatformComponent = async (componentName: string): Promise<any> => {
  const platform = getPlatform()
  
  try {
    let component: any
    
    switch (platform) {
      case PlatformType.H5:
        component = await import(`@/components/h5/${componentName}H5.vue`)
        break
      case PlatformType.APP:
        component = await import(`@/components/app/${componentName}App.vue`)
        break
      case PlatformType.MP_WEIXIN:
      case PlatformType.MP_ALIPAY:
        component = await import(`@/components/mp/${componentName}MP.vue`)
        break
      default:
        // 回退到通用组件
        component = await import(`@/components/shared/${componentName}.vue`)
    }
    
    return component.default || component
  } catch (error) {
    console.warn(`[Platform] 未找到平台组件 ${componentName}，尝试加载通用组件`)
    
    try {
      const fallback = await import(`@/components/shared/${componentName}.vue`)
      return fallback.default || fallback
    } catch (fallbackError) {
      console.error(`[Platform] 组件 ${componentName} 加载失败`, fallbackError)
      throw new Error(`组件 ${componentName} 不存在`)
    }
  }
}

/**
 * 执行平台特定函数
 * @param {Object} handlers - 平台处理器映射
 * @returns {any} 执行结果
 * @example
 * const result = runPlatformSpecific({
 *   h5: () => { console.log('H5'); return 'h5-result' },
 *   app: () => { console.log('App'); return 'app-result' },
 *   default: () => { console.log('其他'); return 'default-result' }
 * })
 */
export const runPlatformSpecific = <T = any>(handlers: {
  h5?: () => T
  app?: () => T
  mp?: () => T
  default?: () => T
}): T | undefined => {
  const platform = getPlatform()
  
  if (platform === PlatformType.H5 && handlers.h5) {
    return handlers.h5()
  } else if (platform === PlatformType.APP && handlers.app) {
    return handlers.app()
  } else if ((platform === PlatformType.MP_WEIXIN || platform === PlatformType.MP_ALIPAY) && handlers.mp) {
    return handlers.mp()
  } else if (handlers.default) {
    return handlers.default()
  }
  
  return undefined
}

/**
 * 获取平台特定路径
 * @param {string} basePath - 基础路径
 * @returns {string} 平台路径
 * @example
 * const path = getPlatformPath('/assets/icon.png')
 * // H5: /h5/assets/icon.png
 * // App: /app/assets/icon.png
 */
export const getPlatformPath = (basePath: string): string => {
  const platform = getPlatform()
  
  if (platform === PlatformType.UNKNOWN) {
    return basePath
  }
  
  const prefix = `/${platform}`
  return basePath.startsWith('/') ? prefix + basePath : prefix + '/' + basePath
}

/**
 * 检查平台能力
 * @param {string} capability - 能力名称
 * @returns {boolean} 是否支持
 * @example
 * if (hasCapability('download')) {
 *   // 支持下载
 * }
 */
export const hasCapability = (capability: 'download' | 'upload' | 'camera' | 'location' | 'share'): boolean => {
  const platform = getPlatform()
  
  const capabilities: Record<PlatformType, Record<string, boolean>> = {
    [PlatformType.H5]: {
      download: true,
      upload: true,
      camera: true,
      location: true,
      share: false
    },
    [PlatformType.APP]: {
      download: true,
      upload: true,
      camera: true,
      location: true,
      share: true
    },
    [PlatformType.MP_WEIXIN]: {
      download: false,
      upload: true,
      camera: true,
      location: true,
      share: true
    },
    [PlatformType.MP_ALIPAY]: {
      download: false,
      upload: true,
      camera: true,
      location: true,
      share: true
    },
    [PlatformType.UNKNOWN]: {
      download: false,
      upload: false,
      camera: false,
      location: false,
      share: false
    }
  }
  
  return capabilities[platform][capability] || false
}

/**
 * 平台工具导出对象（方便统一引用）
 */
export default {
  // 类型
  PlatformType,
  
  // 判断函数
  isH5,
  isApp,
  isAndroid,
  isIOS,
  isMiniProgram,
  isAlipayMiniProgram,
  
  // 获取函数
  getPlatform,
  getPlatformName,
  getPlatformConfig,
  getPlatformPath,
  
  // 工具函数
  importPlatformComponent,
  runPlatformSpecific,
  hasCapability
}
