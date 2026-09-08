/// <reference types="vite/client" />
/// <reference types="@dcloudio/types" />

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 环境变量类型定义
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_BASE_API_URL: string    // API 基础地址 (Core Service)
  readonly VITE_AUTH_API_URL: string    // API 基础地址 (Users Service)
  readonly VITE_API_PATH_PREFIX?: string // API 路径前缀，默认为空；设为空则不追加
  readonly VITE_API_TIMEOUT: string
  readonly VITE_UPLOAD_URL: string
  readonly VITE_WEBSOCKET_URL: string
  readonly VITE_MEDIA_BASE_URL: string  // 媒体资源基础地址
  readonly VITE_APP_VERSION: string
  readonly VITE_BUILD_TIME: string
  readonly VITE_USE_MOCK: string        // 是否使用 Mock
  readonly VITE_ENABLE_ANALYTICS: string
  // 微信小程序相关
  readonly VITE_WECHAT_APPID: string
  readonly VITE_WECHAT_SECRET: string
  readonly VITE_LOGIN_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 全局类型扩展
declare global {
  // uni-app 全局API类型声明已由 @dcloudio/types 提供
  // 这里只扩展自定义的全局变量

  // 微信小程序全局变量
  const App: (option: any) => void
  const Page: (option: any) => void  
  const Component: (option: any) => void
  const Behavior: (option: any) => void

  // 自定义全局变量
  interface Window {
    __UNI_PLATFORM__: string
    __wxjs_environment: string
  }

  // 项目全局配置类型
  interface AppConfig {
    version: string
    env: string
    platform: string
    apiBaseUrl: string
    uploadUrl: string
    wsUrl: string
  }

  // 微信小程序API类型补充
  namespace WechatMiniprogram {
    interface Wx {
      // 扩展微信API类型定义
      getUpdateManager(): UpdateManager
      createLivePlayerContext(livePlayerId: string): LivePlayerContext
      createVideoContext(videoId: string): VideoContext
    }

    interface UpdateManager {
      onCheckForUpdate(callback: (result: { hasUpdate: boolean }) => void): void
      onUpdateReady(callback: () => void): void
      onUpdateFailed(callback: () => void): void
      applyUpdate(): void
    }

    interface LivePlayerContext {
      play(): void
      stop(): void
      pause(): void
      resume(): void
      mute(): void
      snapshot(): void
      requestFullScreen(options?: { direction: number }): void
      exitFullScreen(): void
    }
  }

  // 系统信息类型
  interface SystemInfo {
    brand: string
    model: string
    pixelRatio: number
    screenWidth: number
    screenHeight: number
    windowWidth: number
    windowHeight: number
    statusBarHeight: number
    language: string
    version: string
    system: string
    platform: string
    fontSizeSetting: number
    SDKVersion: string
    benchmarkLevel: number
    albumAuthorized: boolean
    cameraAuthorized: boolean
    locationAuthorized: boolean
    microphoneAuthorized: boolean
    notificationAuthorized: boolean
    notificationAlertAuthorized: boolean
    notificationBadgeAuthorized: boolean
    notificationSoundAuthorized: boolean
    bluetoothEnabled: boolean
    locationEnabled: boolean
    wifiEnabled: boolean
    safeArea: {
      left: number
      right: number
      top: number
      bottom: number
      width: number
      height: number
    }
    locationReducedAccuracy: boolean
    theme: 'light' | 'dark'
    host: {
      appId: string
    }
  }
}

export {}
