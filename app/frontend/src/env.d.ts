/// <reference types="vite/client" />
/// <reference types="@dcloudio/types" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 环境变量类型声明
interface ImportMetaEnv {
  // 日志系统环境变量
  readonly VITE_LOG_ENABLED: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_LOG_CONSOLE: string
  readonly VITE_LOG_REPORT_ENABLED: string
  readonly VITE_LOG_API_URL: string
  readonly VITE_LOG_BATCH_SIZE: string
  readonly VITE_LOG_INTERVAL: string
  
  // 应用基础环境变量
  readonly VITE_APP_VERSION: string
  readonly VITE_BASE_API_URL: string
  readonly VITE_AUTH_API_URL: string
  readonly VITE_LOGIN_URL: string
  readonly VITE_FRONTEND_USER_URL: string
  readonly VITE_APP_BASE_PATH: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 