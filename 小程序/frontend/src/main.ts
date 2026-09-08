import './bootstrap-console'

import { createSSRApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate'
import { setupMock } from './mock'

function toConsoleText(value: unknown): string {
  if (value == null) return String(value)
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (value instanceof Error) return `${value.name}: ${value.message}`
  try {
    return JSON.stringify(value)
  } catch {
    return Object.prototype.toString.call(value)
  }
}

// 初始化 Mock API（开发环境）
if (process.env.NODE_ENV === 'development') {
  setupMock()
}

export function createApp() {
  const app = createSSRApp(App)

  // 必须在 pinia / 页面挂载前注册，避免 Vue 默认 console.warn(...args) 打出 [] [object Object]
  app.config.errorHandler = (error, _instance, info) => {
    console.error('全局错误:', toConsoleText(error), String(info || ''))
    if (process.env.NODE_ENV === 'production') {
      reportError(error instanceof Error ? error : new Error(toConsoleText(error)), String(info || ''))
    }
  }

  app.config.warnHandler = (msg, instance, trace) => {
    if (process.env.NODE_ENV !== 'development') return
    const name =
      (instance as any)?.$options?.name ||
      (instance as any)?.type?.name ||
      (instance as any)?.type?.__name ||
      ''
    const text = [String(msg || ''), name ? `组件=${name}` : '', typeof trace === 'string' ? trace : '']
      .map((s) => s.trim())
      .filter(Boolean)
      .join(' | ')
    if (text) console.warn('Vue警告:', text)
  }

  const pinia = createPinia()

  pinia.use(
    createPersistedState({
      storage: {
        getItem: (key: string) => {
          try {
            return uni.getStorageSync(key)
          } catch (error) {
            console.error('获取存储失败:', toConsoleText(error))
            return null
          }
        },
        setItem: (key: string, value: string) => {
          try {
            uni.setStorageSync(key, value)
          } catch (error) {
            console.error('设置存储失败:', toConsoleText(error))
          }
        },
        removeItem: (key: string) => {
          try {
            uni.removeStorageSync(key)
          } catch (error) {
            console.error('删除存储失败:', toConsoleText(error))
          }
        }
      }
    })
  )

  app.use(pinia)

  app.config.globalProperties.$config = {
    version: '1.0.0',
    env: process.env.NODE_ENV,
    platform: process.env.UNI_PLATFORM
  }

  return {
    app,
    Pinia: pinia
  }
}

function reportError(error: Error, info: string) {
  const errorInfo = {
    message: error.message,
    stack: error.stack,
    info,
    timestamp: new Date().toISOString(),
    platform: process.env.UNI_PLATFORM,
    version: '1.0.0'
  }
  console.log('错误上报:', toConsoleText(errorInfo))
}
