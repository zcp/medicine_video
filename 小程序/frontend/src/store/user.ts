/**
 * 用户状态管理
 * 管理用户个人信息、偏好设置、统计数据等
 */

import { defineStore } from 'pinia'
import type {
  UserProfile,
  UpdateProfileRequest
} from '@/types/user'
import { getCurrentUser, updateProfile } from '@/api/user'
import { logger } from '@/logs/logger'

interface UserState {
  profile: UserProfile | null
  loading: boolean
  profileLoading: boolean
  error: Error | null
  lastUpdateTime: number | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    profile: null,
    loading: false,
    profileLoading: false,
    error: null,
    lastUpdateTime: null
  }),

  getters: {
    /**
     * 用户基本信息
     */
    userInfo: (state) => state.profile,
    
    nickname: (state) => state.profile?.nickname || '未设置',
    avatar: (state) => state.profile?.avatar || '',
    isProfileComplete: (state) => {
      if (!state.profile) return false
      return !!(state.profile.nickname && state.profile.avatar)
    }
  },

  actions: {
    /**
     * 获取当前用户信息
     */
    async fetchCurrentUser(): Promise<void> {
      logger.info('user', '[fetchCurrentUser] 开始获取用户信息', {
        当前状态: {
          loading: this.loading,
          是否有缓存: !!this.profile,
          上次更新: this.lastUpdateTime
        }
      })

      this.loading = true
      this.error = null

      try {
        const response = await getCurrentUser()

        logger.info('user', '[fetchCurrentUser] API响应成功', {
          响应码: response.code,
          是否有数据: !!response.data,
          数据预览: response.data ? {
            id: response.data.id,
            nickname: response.data.nickname,
            phone: response.data.phone?.substring(0, 3) + '****'
          } : null
        })

        if (response.code === 200) {
          this.profile = response.data
          this.lastUpdateTime = Date.now()
        } else {
          throw new Error(response.message || '获取用户信息失败')
        }
      } catch (error) {
        logger.error('user', '[fetchCurrentUser] 获取用户信息失败', {
          错误类型: error instanceof Error ? error.constructor.name : typeof error,
          错误信息: error instanceof Error ? error.message : String(error),
          错误详情: error
        })
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
        logger.debug('user', '[fetchCurrentUser] 完成', {
          最终状态: {
            loading: this.loading,
            hasProfile: !!this.profile,
            hasError: !!this.error
          }
        })
      }
    },

    /**
     * 更新用户档案
     */
    async updateUserProfile(data: UpdateProfileRequest): Promise<void> {
      this.profileLoading = true
      this.error = null
      
      try {
        const response = await updateProfile(data)
        if (response.code === 200) {
          // 更新本地状态
          if (this.profile) {
            Object.assign(this.profile, response.data)
          }
          this.lastUpdateTime = Date.now()
        } else {
          throw new Error(response.message || '更新档案失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.profileLoading = false
      }
    },

    /**
     * 清除用户数据
     */
    clearUserData(): void {
      this.profile = null
      this.error = null
      this.lastUpdateTime = null
    },

    /**
     * 检查是否需要刷新数据
     */
    shouldRefresh(): boolean {
      if (!this.lastUpdateTime) return true
      
      // 5分钟内不重复请求
      const CACHE_DURATION = 5 * 60 * 1000
      return Date.now() - this.lastUpdateTime > CACHE_DURATION
    }
  },

  // persist: {
  //   key: 'user-store',
  //   paths: ['profile', 'statistics', 'preferences', 'lastUpdateTime']
  // }
})
