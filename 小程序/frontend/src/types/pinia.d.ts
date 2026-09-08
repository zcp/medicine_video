/**
 * Pinia相关类型声明
 */

import 'pinia'

declare module 'pinia' {
  export interface DefineStoreOptionsBase<S, Store> {
    /**
     * 持久化配置
     */
    persist?: {
      key?: string
      paths?: (keyof S)[]
      storage?: {
        getItem: (key: string) => string | null
        setItem: (key: string, value: string) => void
        removeItem: (key: string) => void
      }
    }
  }
}
