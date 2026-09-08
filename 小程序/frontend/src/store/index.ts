/**
 * Pinia状态管理入口文件
 * 统一导出所有store模块，提供类型安全的状态管理
 */

import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate'

// 创建Pinia实例
const pinia = createPinia()

// 配置持久化插件
pinia.use(createPersistedState({
  // 默认使用uni.setStorageSync进行持久化
  storage: {
    getItem: (key: string) => {
      try {
        return uni.getStorageSync(key)
      } catch (error) {
        console.error('Pinia persist getItem error:', error)
        return null
      }
    },
    setItem: (key: string, value: string) => {
      try {
        uni.setStorageSync(key, value)
      } catch (error) {
        console.error('Pinia persist setItem error:', error)
      }
    }
  }
}))

export default pinia

// 先导入所有store模块到当前作用域
import { useAuthStore } from './auth'
import { useUserStore } from './user'
import { useSettingsStore } from './settings'
import { useUIStore } from './ui'
import { useRoomStore } from './room'
import { useSessionStore } from './session'
import { useTagsStore } from './tags'
import { useBrandsStore } from './brands'
import { useFavoritesStore } from './favorites'
import { useNotificationsStore } from './notifications'
import { useUserFavoritesStore } from './userFavorites'
import { useUserSubscriptionsStore } from './userSubscriptions'
import { useWatchHistoryStore } from './watchHistory'
import { useExpertStore } from './expert'
import { usePreferencesStore } from './preferences'

// Store类型定义
export interface RootState {
  auth: ReturnType<typeof useAuthStore>
  user: ReturnType<typeof useUserStore>
  settings: ReturnType<typeof useSettingsStore>
  ui: ReturnType<typeof useUIStore>
  room: ReturnType<typeof useRoomStore>
  session: ReturnType<typeof useSessionStore>
  tags: ReturnType<typeof useTagsStore>
  brands: ReturnType<typeof useBrandsStore>
  favorites: ReturnType<typeof useFavoritesStore>
  notifications: ReturnType<typeof useNotificationsStore>
  userFavorites: ReturnType<typeof useUserFavoritesStore>
  userSubscriptions: ReturnType<typeof useUserSubscriptionsStore>
  watchHistory: ReturnType<typeof useWatchHistoryStore>
  expert: ReturnType<typeof useExpertStore>
  preferences: ReturnType<typeof usePreferencesStore>
}

// 然后重新导出所有store模块
export {
  useAuthStore,
  useUserStore,
  useSettingsStore,
  useUIStore,
  useRoomStore,
  useSessionStore,
  useTagsStore,
  useBrandsStore,
  useFavoritesStore,
  useNotificationsStore,
  useUserFavoritesStore,
  useUserSubscriptionsStore,
  useWatchHistoryStore,
  useExpertStore,
  usePreferencesStore
}
