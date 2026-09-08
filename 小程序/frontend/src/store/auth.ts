/**
 * 认证状态管理
 * 管理用户登录状态、Token、权限等认证相关信息
 */

import { defineStore } from 'pinia'
import type { 
  LoginRequest,
  LoginResponse,
  UserInfo,
  Permission
} from '@/types/auth'
import { STORAGE_KEYS } from '@/common/constants'
import { logout, refreshToken as refreshTokenApi, login, loginByPhone, loginByEmail, registerByPhone, oneTapLogin, oneTapLoginCloudFunction } from '@/api/auth'
import { getMyProfile } from '@/api/user'
import type {
  PhoneRegisterRequest,
  OneTapLoginRequest,
  CloudFunctionLoginRequest,
  ChannelType
} from '@/types/auth'
import { resetUserBehaviorStores } from './resetUserBehaviorStores'
import { normalizeCanStream } from '@/types/adminUser'

function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const base64Url = parts[1]

    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)

    // H5 / 部分运行时
    if (typeof atob === 'function') {
      const json = decodeURIComponent(
        Array.prototype.map
          .call(atob(padded), (c: string) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(json)
    }

    // 微信小程序 / 其他运行时
    const wxAny = (globalThis as any).wx
    const uniAny = (globalThis as any).uni
    const base64ToArrayBuffer = wxAny?.base64ToArrayBuffer || uniAny?.base64ToArrayBuffer
    if (typeof base64ToArrayBuffer === 'function' && typeof TextDecoder !== 'undefined') {
      const ab: ArrayBuffer = base64ToArrayBuffer(padded)
      const json = new TextDecoder('utf-8').decode(new Uint8Array(ab))
      return JSON.parse(json)
    }

    return null
  } catch {
    return null
  }
}

function getTokenExpireTimeMs(accessToken: string): number | null {
  const payload = decodeJwtPayload(accessToken)
  const exp = payload?.exp
  if (typeof exp === 'number' && Number.isFinite(exp)) return exp * 1000
  // 文档建议 access token 15 分钟；解析失败则使用保守默认值
  return Date.now() + 15 * 60 * 1000
}

function buildMinimalUserInfo(accessToken: string): UserInfo | null {
  const payload = decodeJwtPayload(accessToken)
  const sub = payload?.sub || payload?.user_id
  const role = payload?.role
  if (typeof sub !== 'string' || !sub) return null
  return {
    user_id: sub,
    username: payload?.username || '',
    email: payload?.email || null,
    phone: payload?.phone || null,
    nickname: payload?.nickname || null,
    avatar_url: payload?.avatar_url || null,
    role: typeof role === 'string' ? role as any : 'user',
    status: 'active',
    // V2.1：缺省或旧 Token 无字段 → true；显式 false → 禁止开播
    can_stream: normalizeCanStream(payload?.can_stream),
    created_at: payload?.created_at || new Date().toISOString()
  }
}

interface AuthState {
  // 认证状态
  isLoggedIn: boolean
  token: string | null
  refreshToken: string | null
  tokenExpireTime: number | null
  
  // 用户基本信息
  userInfo: UserInfo | null
  
  // 用户权限
  permissions: Permission[]
  
  // 加载状态
  loading: boolean
  error: Error | null
  
  // 登录方式
  loginType: 'password' | 'sso' | 'phone' | 'email' | 'one_tap' | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    isLoggedIn: false,
    token: null,
    refreshToken: null,
    tokenExpireTime: null,
    userInfo: null,
    permissions: [],
    loading: false,
    error: null,
    loginType: null
  }),

  getters: {
    /**
     * 是否已认证（必须同时满足：已登录、有Token、Token未过期）
     */
    isAuthenticated(state) {
      return state.isLoggedIn && !!state.token && !this.isTokenExpired
    },

    /**
     * Token是否过期
     */
    isTokenExpired: (state) => {
      if (!state.tokenExpireTime) return true
      return Date.now() > state.tokenExpireTime
    },

    /**
     * 用户角色
     */
    userRole: (state) => state.userInfo?.role || 'user',

    /**
     * 是否为管理员（兼容大小写：admin / ADMIN / SUPERADMIN）
     */
    isAdmin: (state) => {
      const role = (state.userInfo?.role || '').toLowerCase()
      return role === 'admin' || role === 'superadmin'
    },

    /**
     * 是否为超级管理员（V2：仅超管可改 role）
     */
    isSuperAdmin: (state) => {
      return (state.userInfo?.role || '').toLowerCase() === 'superadmin'
    },

    /**
     * 是否可开播（V2.1；JWT 缺省按 true；false=禁止开播）
     */
    canStream: (state) => normalizeCanStream(state.userInfo?.can_stream),

    /**
     * 是否允许新建直播间（可开播或 ADMIN/SUPERADMIN 旁路）
     */
    canCreateRoom: (state) => {
      const role = (state.userInfo?.role || '').toLowerCase()
      if (role === 'admin' || role === 'superadmin') return true
      return normalizeCanStream(state.userInfo?.can_stream)
    },

    /**
     * 是否为专家（兼容大小写：expert / EXPERT）
     */
    isExpert: (state) => (state.userInfo?.role || '').toLowerCase() === 'expert',

    /**
     * 用户权限列表
     */
    // 注意：不要在 getters 中定义与 state 同名的字段（例如 permissions），否则会把 state 字段变成只读计算属性，
    // 在 clearAuth()/restoreAuth() 中对 this.permissions 赋值会触发运行时错误。
  },

  actions: {
    /**
     * 账号密码登录（跨平台；具体可用性以服务端实现为准）
     */
    async passwordLogin(params: LoginRequest): Promise<LoginResponse | null> {
      this.loading = true
      this.error = null
      
      try {
        const response = await login(params)
        
        if (response.code === 200 && response.data) {
          this._setAuthData(response.data, 'password')
          return response.data
        } else {
          throw new Error(response.message || '登录失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 拉取当前用户信息 GET /users/me
     */
    async fetchUserInfo(): Promise<void> {
      if (!this.token) return
      try {
        const res = await getMyProfile()
        if (res.code === 200 && res.data) {
          const data: any = res.data
          this.userInfo = {
            ...data,
            can_stream: normalizeCanStream(data?.can_stream)
          }
          uni.setStorageSync(STORAGE_KEYS.USER_INFO, this.userInfo)
        }
      } catch {
        // 保持 JWT 登录态，用户信息可后续重试
      }
    },

    /**
     * V3：手机号 ticket 登录
     */
    async loginByPhoneTicket(login_ticket: string, agreed_to_terms = false) {
      this.loading = true
      this.error = null
      try {
        const response = await loginByPhone({ login_ticket, agreed_to_terms })
        if (response.code === 200 && response.data) {
          this._setAuthData(response.data, 'phone')
          await this.fetchUserInfo()
          return response.data
        }
        throw new Error(response.message || '登录失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * V3.5：邮箱 ticket 登录（POST /auth/login/email）
     */
    async loginByEmailTicket(login_ticket: string, agreed_to_terms = false) {
      this.loading = true
      this.error = null
      try {
        const response = await loginByEmail({ login_ticket, agreed_to_terms })
        if (response.code === 200 && response.data) {
          this._setAuthData(response.data, 'email')
          await this.fetchUserInfo()
          return response.data
        }
        throw new Error(response.message || '登录失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * V3.5：按 channel 消费 login_ticket（EMAIL → login/email，SMS → login/phone）
     */
    async loginByOtpTicket(login_ticket: string, channel: ChannelType, agreed_to_terms = false) {
      if (channel === 'EMAIL') {
        return this.loginByEmailTicket(login_ticket, agreed_to_terms)
      }
      return this.loginByPhoneTicket(login_ticket, agreed_to_terms)
    },

    /**
     * V3：手机号 ticket 注册（直接登录）
     */
    async registerByPhoneTicket(data: PhoneRegisterRequest) {
      this.loading = true
      this.error = null
      try {
        const response = await registerByPhone(data)
        if (response.code === 200 && response.data) {
          const { access_token, refresh_token } = response.data
          this._setAuthData({ access_token, refresh_token, token_type: 'bearer' }, 'phone')
          await this.fetchUserInfo()
          return response.data
        }
        throw new Error(response.message || '注册失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * V3：运营商一键登录
     */
    async oneTapLoginAction(data: OneTapLoginRequest) {
      this.loading = true
      this.error = null
      try {
        const response = await oneTapLogin(data)
        if (response.code === 200 && response.data) {
          this._setAuthData(response.data, 'one_tap')
          await this.fetchUserInfo()
          return response.data
        }
        throw new Error(response.message || '一键登录失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * V3：云函数 HMAC 一键登录
     */
    async oneTapLoginViaCloudFunction(data: CloudFunctionLoginRequest) {
      this.loading = true
      this.error = null
      try {
        const response = await oneTapLoginCloudFunction(data)
        if (response.code === 200 && response.data) {
          this._setAuthData(response.data, 'one_tap')
          await this.fetchUserInfo()
          return response.data
        }
        throw new Error(response.message || '一键登录失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 刷新Token
     */
    async refreshTokenAction(): Promise<void> {
      if (!this.refreshToken) {
        throw new Error('没有可用的刷新Token')
      }

      try {
        const response = await refreshTokenApi({ refresh_token: this.refreshToken })
        
        if (response.code === 200 && response.data) {
          this.token = response.data.access_token
          this.tokenExpireTime = getTokenExpireTimeMs(this.token)
          this.userInfo = buildMinimalUserInfo(this.token)
          
          // 更新本地存储
          uni.setStorageSync(STORAGE_KEYS.ACCESS_TOKEN, this.token)
          uni.setStorageSync('tokenExpireTime', this.tokenExpireTime)
          if (this.userInfo) {
            uni.setStorageSync(STORAGE_KEYS.USER_INFO, this.userInfo)
          }
        } else {
          throw new Error(response.message || 'Token刷新失败')
        }
      } catch (error) {
        // Token刷新失败，清除认证信息
        this.clearAuth()
        throw error
      }
    },

    /**
     * 退出登录
     */
    async logout(): Promise<void> {
      this.loading = true
      
      try {
        if (this.token) {
          await logout()
        }
      } catch (error) {
        console.error('退出登录失败:', error)
      } finally {
        this.clearAuth()
        this.loading = false
      }
    },

    /**
     * 清除认证信息
     */
    clearAuth(): void {
      this.isLoggedIn = false
      this.token = null
      this.refreshToken = null
      this.tokenExpireTime = null
      this.userInfo = null
      this.permissions = []
      this.loginType = null
      this.error = null
      
      // 清除本地存储
      uni.removeStorageSync(STORAGE_KEYS.ACCESS_TOKEN)
      uni.removeStorageSync(STORAGE_KEYS.REFRESH_TOKEN)
      uni.removeStorageSync('tokenExpireTime')
      uni.removeStorageSync(STORAGE_KEYS.USER_INFO)

      // 清空收藏/订阅/历史/通知等行为 Store，避免换号露旧数据（G2）
      resetUserBehaviorStores()
    },

    /**
     * Token 本地已过期但尚未 clearAuth 时：同步清会话，避免 isAuthenticated=false 仍残留头像等 userInfo
     * @returns 是否因过期执行了清理
     */
    clearAuthIfExpired(): boolean {
      if (!this.isLoggedIn) return false
      if (!this.isTokenExpired) return false
      this.clearAuth()
      return true
    },

    /**
     * 从本地存储恢复认证状态
     * - access token 未过期 → 直接恢复
     * - access token 已过期但有 refresh token → 尝试静默刷新
     * - 都不可用 → 清除登录态
     */
    restoreAuth(): void {
      try {
        const storedToken = uni.getStorageSync(STORAGE_KEYS.ACCESS_TOKEN)
        const storedRefreshToken = uni.getStorageSync(STORAGE_KEYS.REFRESH_TOKEN)
        const storedTokenExpireTime = uni.getStorageSync('tokenExpireTime')
        const storedUserInfo = uni.getStorageSync(STORAGE_KEYS.USER_INFO)

        const hasValidToken = storedToken && storedTokenExpireTime && Date.now() < storedTokenExpireTime

        if (hasValidToken) {
          this.token = storedToken
          this.refreshToken = storedRefreshToken
          this.tokenExpireTime = storedTokenExpireTime
          this.userInfo = storedUserInfo
          this.permissions = []
          this.isLoggedIn = true
        } else if (storedRefreshToken) {
          // access token 已过期，尝试用 refresh token 静默刷新
          this.refreshToken = storedRefreshToken
          this.token = storedToken || null
          this.tokenExpireTime = storedTokenExpireTime || null
          this.userInfo = storedUserInfo || null
          this.isLoggedIn = !!storedToken
          // 异步刷新，不阻塞启动
          this.refreshTokenAction().catch(() => {
            this.clearAuth()
          })
        } else {
          this.clearAuth()
        }
      } catch (error) {
        console.error('恢复认证状态失败:', error)
        this.clearAuth()
      }
    },

    /**
     * 设置认证数据
     * @private
     */
    _setAuthData(data: LoginResponse, type: 'password' | 'sso' | 'phone' | 'email' | 'one_tap'): void {
      this.token = data.access_token
      this.refreshToken = data.refresh_token || null
      this.tokenExpireTime = getTokenExpireTimeMs(this.token)
      this.userInfo = buildMinimalUserInfo(this.token)
      this.permissions = []
      this.isLoggedIn = true
      this.loginType = type
      
      // 存储到本地
      uni.setStorageSync(STORAGE_KEYS.ACCESS_TOKEN, this.token)
      if (this.refreshToken) {
        uni.setStorageSync(STORAGE_KEYS.REFRESH_TOKEN, this.refreshToken)
      } else {
        uni.removeStorageSync(STORAGE_KEYS.REFRESH_TOKEN)
      }
      uni.setStorageSync('tokenExpireTime', this.tokenExpireTime)
      if (this.userInfo) {
        uni.setStorageSync(STORAGE_KEYS.USER_INFO, this.userInfo)
      } else {
        uni.removeStorageSync(STORAGE_KEYS.USER_INFO)
      }
    }
  },

  // persist: {
  //   key: 'auth-store',
  //   paths: ['isLoggedIn', 'token', 'refreshToken', 'tokenExpireTime', 'userInfo', 'loginType']
  // }
})
