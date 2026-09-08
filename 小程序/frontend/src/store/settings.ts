/**
 * 设置状态管理
 * 管理系统设置、用户偏好设置、主题设置等
 */

import { defineStore } from 'pinia'
import type { 
  UserSettings,
  UpdateUserSettingsRequest,
  SystemConfig,
  NotificationSettings,
  PrivacySettings,
  PlaybackSettings
} from '@/types/settings'
import type { Language, ThemeMode } from '@/types/common'
import { 
  getUserSettings,
  updateUserSettings,
  getSystemConfig
} from '@/api/settings'

interface SettingsState {
  // 用户设置
  userSettings: UserSettings | null
  
  // 系统配置
  systemConfig: SystemConfig | null
  
  // 加载状态
  loading: boolean
  systemLoading: boolean
  
  // 错误状态
  error: Error | null
  
  // 临时设置（未保存）
  tempSettings: Partial<UserSettings> | null
}

export const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => ({
    userSettings: null,
    systemConfig: null,
    loading: false,
    systemLoading: false,
    error: null,
    tempSettings: null
  }),

  getters: {
    /**
     * 当前主题模式
     */
    themeMode: (state) => state.userSettings?.basic?.theme || 'light',
    
    /**
     * 当前语言
     */
    language: (state) => state.userSettings?.basic?.language || 'zh-CN',
    
    /**
     * 通知设置
     */
    notificationSettings: (state) => state.userSettings?.notifications,
    
    /**
     * 隐私设置
     */
    privacySettings: (state) => state.userSettings?.privacy,
    
    /**
     * 播放设置
     */
    playbackSettings: (state) => state.userSettings?.playback,
    
    /**
     * 是否开启推送通知
     */
    pushEnabled: (state) => state.userSettings?.notifications?.push || false,
    
    /**
     * 是否开启夜间模式
     */
    isDarkMode: (state) => {
      if (state.userSettings?.basic?.theme === 'auto') {
        // 根据系统时间判断
        const hour = new Date().getHours()
        return hour < 7 || hour >= 19
      }
      return state.userSettings?.basic?.theme === 'dark'
    },
    
    /**
     * 播放器音量
     */
    volume: (state) => state.userSettings?.playback?.volume || 80,
    
    /**
     * 是否自动播放
     */
    autoPlay: (state) => state.userSettings?.playback?.autoplay || false
  },

  actions: {
    /**
     * 获取用户设置
     */
    async fetchUserSettings(): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await getUserSettings()
        if (response.code === 200) {
          this.userSettings = response.data
        } else {
          throw new Error(response.message || '获取用户设置失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新用户设置
     */
    async updateSettings(settings: Partial<UserSettings>): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await updateUserSettings(settings)
        if (response.code === 200) {
          // 更新本地设置
          if (this.userSettings) {
            Object.assign(this.userSettings, settings)
          } else {
            this.userSettings = settings as UserSettings
          }
          
          // 清除临时设置
          this.tempSettings = null
          
          // 应用设置变更
          this._applySettingsChange(settings)
        } else {
          throw new Error(response.message || '更新设置失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取系统配置
     */
    async fetchSystemConfig(): Promise<void> {
      this.systemLoading = true
      
      try {
        const response = await getSystemConfig()
        if (response.code === 200) {
          this.systemConfig = response.data
        } else {
          throw new Error(response.message || '获取系统配置失败')
        }
      } catch (error) {
        console.error('获取系统配置失败:', error)
      } finally {
        this.systemLoading = false
      }
    },

    /**
     * 更新主题设置
     */
    async updateTheme(theme: ThemeMode): Promise<void> {
      const settings: Partial<UserSettings> = {
        basic: {
          ...this.userSettings?.basic,
          theme
        }
      }
      
      await this.updateSettings(settings)
    },

    /**
     * 更新语言设置
     */
    async updateLanguage(language: Language): Promise<void> {
      const settings: Partial<UserSettings> = {
        basic: {
          ...this.userSettings?.basic,
          language
        }
      }
      
      await this.updateSettings(settings)
    },

    /**
     * 更新通知设置
     */
    async updateNotificationSettings(notifications: Partial<NotificationSettings>): Promise<void> {
      const settings: Partial<UserSettings> = {
        notifications: {
          ...this.userSettings?.notifications,
          ...notifications
        }
      }
      
      await this.updateSettings(settings)
    },

    /**
     * 更新隐私设置
     */
    async updatePrivacySettings(privacy: Partial<PrivacySettings>): Promise<void> {
      const settings: Partial<UserSettings> = {
        privacy: {
          ...this.userSettings?.privacy,
          ...privacy
        }
      }
      
      await this.updateSettings(settings)
    },

    /**
     * 更新播放设置
     */
    async updatePlaybackSettings(playback: Partial<PlaybackSettings>): Promise<void> {
      const settings: Partial<UserSettings> = {
        playback: {
          ...this.userSettings?.playback,
          ...playback
        }
      }
      
      await this.updateSettings(settings)
    },

    /**
     * 临时修改设置（未保存）
     */
    setTempSettings(settings: Partial<UserSettings>): void {
      this.tempSettings = {
        ...this.tempSettings,
        ...settings
      }
    },

    /**
     * 应用临时设置
     */
    async applyTempSettings(): Promise<void> {
      if (this.tempSettings) {
        await this.updateSettings(this.tempSettings)
      }
    },

    /**
     * 取消临时设置
     */
    cancelTempSettings(): void {
      this.tempSettings = null
    },

    /**
     * 重置为默认设置
     */
    async resetToDefault(): Promise<void> {
      const defaultSettings: UserSettings = {
        basic: {
          language: 'zh-CN',
          theme: 'light',
          timezone: 'Asia/Shanghai'
        },
        notifications: {
          push: true,
          email: false,
          sms: false,
          inApp: true,
          liveStart: true,
          expertUpdate: true,
          systemMessage: true,
          marketing: false
        },
        privacy: {
          showPhone: false,
          showEmail: false,
          allowFollow: true,
          allowMessage: true,
          showOnlineStatus: true,
          allowSearch: true,
          showWatchHistory: false
        },
        playback: {
          autoplay: false,
          qualityPreference: 'auto',
          volume: 80,
          muted: false,
          danmuEnabled: true,
          danmuOpacity: 0.8,
          danmuSpeed: 1,
          hardwareAcceleration: true
        },
        personalization: {
          recommendationEnabled: true,
          dataCollectionEnabled: true,
          targetedAdsEnabled: false
        }
      }
      
      await this.updateSettings(defaultSettings)
    },

    /**
     * 应用设置变更
     * @private
     */
    _applySettingsChange(settings: Partial<UserSettings>): void {
      // 应用主题变更
      if (settings.basic?.theme) {
        const theme = this.isDarkMode ? 'dark' : 'light'
        uni.setStorageSync('theme', theme)
        
        // 触发主题变更事件
        uni.$emit && uni.$emit('themeChange', theme)
      }
      
      // 应用语言变更
      if (settings.basic?.language) {
        uni.setStorageSync('language', settings.basic.language)
        
        // 触发语言变更事件
        uni.$emit && uni.$emit('languageChange', settings.basic.language)
      }
    }
  },

  // persist: {
  //   key: 'settings-store',
  //   paths: ['userSettings', 'systemConfig']
  // }
})
