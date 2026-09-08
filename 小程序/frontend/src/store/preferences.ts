/**
 * 用户偏好（首页个性化）
 * - 科室星标 pinned_categories
 * - 首页视图模式 homepage_view_mode
 */

import { defineStore } from 'pinia'
import { request } from '@/utils/request'
import type { HomepageViewMode, UserPreferencesV2, UpdateUserPreferencesRequest } from '@/types/userPreferences'
import { useAuthStore } from '@/store/auth'
import { API_PATHS } from '@/config/api'

const LOCAL_STORAGE_KEY = 'local_user_preferences_v2'

interface PreferencesState {
  pinnedCategoryIds: string[]
  homepageViewMode: HomepageViewMode

  loading: boolean
  saving: boolean
  error: string | null

  lastLoadedAt: number | null
}

function coercePinnedCategories(input: any): string[] {
  const arr = Array.isArray(input) ? input : []
  return arr
    .map(v => String(v || ''))
    .filter(Boolean)
    .slice(0, 5)
}

export const usePreferencesStore = defineStore('preferences', {
  state: (): PreferencesState => ({
    pinnedCategoryIds: [],
    homepageViewMode: 'double',

    loading: false,
    saving: false,
    error: null,

    lastLoadedAt: null
  }),

  actions: {
    async apiGetUserPreferences() {
      return request({
        url: API_PATHS.USER_PREFERENCES.GET,
        method: 'GET'
      })
    },

    async apiUpdateUserPreferences(patch: UpdateUserPreferencesRequest) {
      return request({
        url: API_PATHS.USER_PREFERENCES.UPDATE,
        method: 'PATCH',
        data: patch,
        loading: true,
        loadingText: '保存中...'
      })
    },

    restoreLocal() {
      try {
        const raw = uni.getStorageSync(LOCAL_STORAGE_KEY)
        if (!raw) return
        const data = typeof raw === 'string' ? JSON.parse(raw) : raw
        this.pinnedCategoryIds = coercePinnedCategories(data?.pinned_categories)
        this.homepageViewMode = data?.homepage_view_mode === 'single' ? 'single' : 'double'
      } catch {
        // ignore
      }
    },

    cacheLocal(patch: Partial<UpdateUserPreferencesRequest>) {
      try {
        const existingRaw = uni.getStorageSync(LOCAL_STORAGE_KEY)
        const existing = existingRaw ? (typeof existingRaw === 'string' ? JSON.parse(existingRaw) : existingRaw) : {}
        const next = { ...existing, ...patch }
        uni.setStorageSync(LOCAL_STORAGE_KEY, JSON.stringify(next))
      } catch {
        // ignore
      }
    },

    /**
     * 尝试从服务端加载偏好；未登录时仅恢复本地缓存。
     */
    async fetchPreferences(options?: { force?: boolean }) {
      const force = !!options?.force
      if (!force && this.lastLoadedAt && Date.now() - this.lastLoadedAt < 60_000) {
        return
      }

      const auth = useAuthStore()
      if (!auth.isAuthenticated) {
        this.restoreLocal()
        this.lastLoadedAt = Date.now()
        return
      }

      this.loading = true
      this.error = null

      try {
        const resp = await this.apiGetUserPreferences()
        const pref: UserPreferencesV2 | null = (resp as any)?.data ?? null
        if (!pref) throw new Error('偏好数据为空')

        this.pinnedCategoryIds = coercePinnedCategories((pref as any).pinned_categories)
        this.homepageViewMode = (pref as any).homepage_view_mode === 'single' ? 'single' : 'double'

        this.cacheLocal({
          pinned_categories: this.pinnedCategoryIds,
          homepage_view_mode: this.homepageViewMode
        })

        this.lastLoadedAt = Date.now()
      } catch (e: any) {
        this.error = String(e?.message || '加载偏好失败')
        this.restoreLocal()
      } finally {
        this.loading = false
      }
    },

    /**
     * 仅更新本地/内存中的 pinned（点星即时生效用；真正落库走 savePinnedCategories）
     */
    setPinnedCategoriesLocal(ids: string[]) {
      const nextIds = coercePinnedCategories(ids)
      this.pinnedCategoryIds = nextIds
      this.cacheLocal({ pinned_categories: nextIds })
    },

    /**
     * 保存 pinned_categories（登录用户同步到服务端；未登录仅本地缓存）
     */
    async savePinnedCategories(ids: string[], options?: { silent?: boolean }) {
      const silent = !!options?.silent
      const nextIds = coercePinnedCategories(ids)
      if (nextIds.length > 5) {
        if (!silent) uni.showToast({ title: '最多固定5个科室', icon: 'none' })
        return
      }

      this.pinnedCategoryIds = nextIds
      this.cacheLocal({ pinned_categories: nextIds })

      const auth = useAuthStore()
      if (!auth.isAuthenticated) {
        if (!silent) uni.showToast({ title: '已保存（本地）', icon: 'success' })
        this.lastLoadedAt = Date.now()
        return
      }

      this.saving = true
      this.error = null
      try {
        const resp = await this.apiUpdateUserPreferences({ pinned_categories: nextIds })
        const pref: any = (resp as any)?.data
        if (pref?.pinned_categories) {
          this.pinnedCategoryIds = coercePinnedCategories(pref.pinned_categories)
          this.cacheLocal({ pinned_categories: this.pinnedCategoryIds })
        }
        if (!silent) uni.showToast({ title: '已保存', icon: 'success' })
        this.lastLoadedAt = Date.now()
      } catch (e: any) {
        this.error = String(e?.message || '保存失败')
        if (!silent) uni.showToast({ title: '保存失败', icon: 'none' })
        throw e
      } finally {
        this.saving = false
      }
    },

    async saveHomepageViewMode(mode: HomepageViewMode) {
      this.homepageViewMode = mode === 'single' ? 'single' : 'double'
      this.cacheLocal({ homepage_view_mode: this.homepageViewMode })

      const auth = useAuthStore()
      if (!auth.isAuthenticated) return

      this.saving = true
      try {
        await this.apiUpdateUserPreferences({ homepage_view_mode: this.homepageViewMode })
      } finally {
        this.saving = false
      }
    }
  },

  persist: {
    paths: ['pinnedCategoryIds', 'homepageViewMode']
  }
})
