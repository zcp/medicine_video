import { defineStore } from 'pinia'
import type { ExpertInfoItem, ExpertSessionBriefItem } from '@/api/expert'
import { followExpert, unfollowExpert, getExpertDetail, getAdminExpertList, getExpertList, getMyFollowedExperts, getSessionExperts, getExpertSessions } from '@/api/expert'
import { DEFAULT_CONFIG } from '@/common/constants'
import { log } from '@/logs/logger'
import { resolveMediaUrl } from '@/utils/url'
import { resolveAvatarUrl } from '@/utils/url'
import { useAuthStore } from '@/store/auth'

export interface Expert {
  id: string
  name: string
  avatar: string
  title: string
  department: string
  bio?: string
  specialization?: string[]
  stats: { followers: number; sessions: number; views: number }
}

export interface ExpertSession {
  id: string
  roomId?: string
  title: string
  cover: string
  status: 'scheduled' | 'live' | 'ended'
  scheduledAt?: string
  viewers?: number
}

/** 后端 LiveSessionStatus → 详情页分组状态 */
function normalizeExpertSessionStatus(raw: unknown): ExpertSession['status'] {
  const s = String(raw || '').toLowerCase()
  if (s === 'live') return 'live'
  if (s === 'scheduled') return 'scheduled'
  // finished / ready / processing / error / ended → 历史（含回放）
  return 'ended'
}

interface Pagination { page: number; pageSize: number; total: number; hasMore: boolean }

export const useExpertStore = defineStore('expert', {
  state: () => ({
    list: [] as Expert[],
    detail: null as Expert | null,
    sessions: [] as ExpertSession[],
    loadingList: false,
    loadingDetail: false,
    loadingSessions: false,
    error: null as null | { message: string },
    pagination: { page: 1, pageSize: 10, total: 0, hasMore: true } as Pagination,
    keyword: '',
    specialty: '',
    /** 根分类筛选（《20》专家按 category_id） */
    categoryId: '',
    followingMap: {} as Record<string, boolean>,
    followPending: false,
    followPendingId: null as string | null
  }),
  actions: {
    async refreshMyFollowedExperts() {
      this.error = null
      try {
        const res = await getMyFollowedExperts()
        if (res.code !== 200) return
        const list = Array.isArray(res.data) ? res.data : []
        const map: Record<string, boolean> = {}
        list.forEach((it) => {
          if (it?.expert_id) map[String(it.expert_id)] = true
        })
        this.followingMap = map
        log.info('business', 'refreshMyFollowedExperts:success', { count: list.length })
      } catch {
        // 静默失败：未登录/后端未实现时不阻断
      }
    },
    async fetchExperts(params?: {
      page?: number
      pageSize?: number
      keyword?: string
      specialty?: string
      categoryId?: string
    }) {
      this.loadingList = true
      this.error = null
      try {
        const page = Math.max(1, Number(params?.page ?? 1))
        const pageSize = Math.max(1, Number(params?.pageSize ?? this.pagination.pageSize))
        const finalKeyword = (params?.keyword ?? this.keyword).trim()
        const finalSpecialty = (params?.specialty ?? this.specialty).trim()
        const finalCategoryId = String(params?.categoryId ?? this.categoryId ?? '').trim()

        const authStore = useAuthStore()

        log.info('business', '[fetchExperts] 开始', {
          page, pageSize, finalKeyword, finalSpecialty, finalCategoryId,
          isAdmin: authStore.isAdmin,
          isAuthenticated: authStore.isAuthenticated,
          storeKeyword: this.keyword,
          storeSpecialty: this.specialty,
          storeCategoryId: this.categoryId
        })

        if (authStore.isAdmin) {
          log.info('business', '[fetchExperts] 走 Admin 路径')
          const adminApiParams: any = { page, size: pageSize }
          if (finalKeyword) adminApiParams.name = finalKeyword
          if (finalCategoryId) adminApiParams.category_id = finalCategoryId
          const res = await getAdminExpertList(adminApiParams)
          log.info('business', '[fetchExperts] Admin 原始响应结构', {
            code: res?.code,
            dataType: typeof res?.data,
            dataIsArray: Array.isArray(res?.data),
            hasItems: !!(res?.data as any)?.items,
            total: (res?.data as any)?.total,
            rawItemsCount: Array.isArray((res?.data as any)?.items) ? (res?.data as any).items.length : 'N/A',
            rawDataKeys: res?.data && typeof res?.data === 'object' ? Object.keys(res.data) : []
          })
          const raw = res.data as any
          const items: any[] = raw?.items ?? []
          const total = Number(raw?.total ?? 0)
          log.info('business', '[fetchExperts] Admin items 提取', { itemsCount: items.length, total, firstItem: items[0] ? JSON.stringify(items[0]).slice(0, 400) : 'null' })
          if (!raw || !Array.isArray(items)) {
            log.error('business', '[fetchExperts] Admin 数据异常', { raw, items })
            throw new Error(res.message || '获取专家失败')
          }

          const mappedPage: Expert[] = items.map((x: any, idx: number) => {
            const expert: Expert = {
              id: String(x.id ?? ''),
              name: String(x.name ?? ''),
              avatar: resolveAvatarUrl(x.avatar_url),
              title: x.title || '',
              department: [x.hospital, x.department_name || x.department].filter(Boolean).join('｜'),
              bio: x.bio,
              specialization: (x.expertise_areas || '')
                .split(',')
                .map((s: string) => s.trim())
                .filter((s: string) => !!s),
              stats: { followers: 0, sessions: 0, views: 0 }
            }
            if (idx === 0) log.info('business', '[fetchExperts] Admin 首条映射结果', JSON.stringify(expert).slice(0, 500))
            return expert
          })

          const base = page === 1 ? [] : (this.list || [])
          const mergedMap = new Map<string, Expert>()
          base.forEach((e) => {
            if (e?.id) mergedMap.set(String(e.id), e)
          })
          mappedPage.forEach((e) => {
            if (e?.id) mergedMap.set(String(e.id), e)
          })
          let merged = Array.from(mergedMap.values())
          log.info('business', '[fetchExperts] Admin 合并前', { baseCount: base.length, mappedCount: mappedPage.length, mergedCount: merged.length })
          // 有 category_id 时以后端筛选为准；仅无 specialty 文本时才本地兜底
          if (finalSpecialty && !finalCategoryId) {
            const beforeFilter = merged.length
            merged = merged.filter((it) => it.department?.includes(finalSpecialty))
            log.info('business', '[fetchExperts] Admin 科室筛选', { specialty: finalSpecialty, before: beforeFilter, after: merged.length })
          }
          // 保持分页追加顺序，避免按姓名重排导致上下滑内容跳动
          this.list = merged

          const effectiveTotal = Number.isFinite(total) && total > 0 ? total : merged.length
          const hasMore = effectiveTotal > 0 ? page * pageSize < effectiveTotal : mappedPage.length >= pageSize
          this.pagination = { page, pageSize, total: effectiveTotal, hasMore }
          log.info('business', '[fetchExperts] Admin 最终结果', {
            listCount: this.list.length,
            total: effectiveTotal,
            hasMore,
            pagination: this.pagination,
            firstId: this.list[0]?.id,
            firstItemSample: this.list[0] ? JSON.stringify(this.list[0]).slice(0, 200) : 'null'
          })
          return
        }

        log.info('business', '[fetchExperts] 走 Public 路径')
        const apiParams: any = { page, size: pageSize }
        if (finalKeyword) apiParams.keyword = finalKeyword
        if (finalCategoryId) apiParams.category_id = finalCategoryId
        const res = await getExpertList(apiParams)
        log.info('business', '[fetchExperts] Public 原始响应结构', {
          code: res?.code,
          message: res?.message,
          dataType: typeof res?.data,
          dataIsArray: Array.isArray(res?.data),
          hasItems: !!(res?.data as any)?.items,
          total: (res?.data as any)?.total,
          rawItemsCount: Array.isArray((res?.data as any)?.items) ? (res?.data as any).items.length : (Array.isArray(res?.data) ? res.data.length : 'N/A'),
          rawDataKeys: res?.data && typeof res?.data === 'object' && !Array.isArray(res?.data) ? Object.keys(res.data) : [],
          rawPreview: JSON.stringify(res?.data)?.slice(0, 600)
        })
        const raw = res.data as any
        const items: any[] = raw?.items ?? (Array.isArray(raw) ? raw : [])
        const total = Number(raw?.total ?? items.length)
        log.info('business', '[fetchExperts] Public items 提取', { itemsCount: items.length, total, firstItem: items[0] ? JSON.stringify(items[0]).slice(0, 400) : 'null' })
        if (!Array.isArray(items)) {
          log.error('business', '[fetchExperts] Public items 不是数组', { raw, typeofRaw: typeof raw, items })
          throw new Error(res.message || '获取专家失败')
        }

        const mapped: Expert[] = items.map((x: any, idx: number) => {
          const expert: Expert = {
            id: String(x.id ?? ''),
            name: String(x.name ?? ''),
            avatar: resolveAvatarUrl(x.avatar_url),
            title: x.title || '',
            department: [x.hospital, x.department_name || x.department].filter(Boolean).join('｜'),
            bio: x.bio,
            specialization: (x.expertise_areas || '')
              .split(',')
              .map((s: string) => s.trim())
              .filter((s: string) => !!s),
            stats: { followers: 0, sessions: 0, views: 0 }
          }
          if (idx === 0) log.info('business', '[fetchExperts] Public 首条映射结果', JSON.stringify(expert).slice(0, 500))
          return expert
        })

        log.info('business', '[fetchExperts] Public 过滤前', { mappedCount: mapped.length, keyword: finalKeyword, specialty: finalSpecialty, categoryId: finalCategoryId })
        const filtered = mapped.filter((item, idx) => {
          const matchKeyword = finalKeyword ? (item.name.includes(finalKeyword) || item.department.includes(finalKeyword)) : true
          // category_id 已交后端；specialty 仅作无分类时的本地兜底
          const matchSpecialty =
            finalCategoryId || !finalSpecialty ? true : item.department.includes(finalSpecialty)
          const keep = matchKeyword && matchSpecialty
          if (!keep) {
            log.debug('business', '[fetchExperts] Public 过滤掉', { idx, id: item.id, name: item.name, department: item.department, matchKeyword, matchSpecialty })
          }
          return keep
        })
        log.info('business', '[fetchExperts] Public 过滤后', { before: mapped.length, after: filtered.length, droppedCount: mapped.length - filtered.length })

        // 与 Admin 路径一致：分页追加合并，避免加载更多时整表被替换
        const base = page === 1 ? [] : (this.list || [])
        const mergedMap = new Map<string, Expert>()
        base.forEach((e) => {
          if (e?.id) mergedMap.set(String(e.id), e)
        })
        filtered.forEach((e) => {
          if (e?.id) mergedMap.set(String(e.id), e)
        })
        // 保持服务端分页顺序：先旧页再新页，不再按姓名重排打乱分页
        const merged = Array.from(mergedMap.values())
        this.list = merged
        const effectiveTotal = Number.isFinite(total) && total > 0 ? total : merged.length
        const hasMore = effectiveTotal > 0 ? page * pageSize < effectiveTotal : mapped.length >= pageSize
        this.pagination = { page, pageSize, total: effectiveTotal, hasMore }
        log.info('business', '[fetchExperts] Public 最终结果', {
          listCount: this.list.length,
          total: effectiveTotal,
          hasMore,
          pagination: this.pagination,
          firstId: this.list[0]?.id,
          firstItemSample: this.list[0] ? JSON.stringify(this.list[0]).slice(0, 200) : 'null'
        })
      } catch (e: any) {
        log.error('business', '[fetchExperts] 异常', { message: e?.message, statusCode: e?.statusCode, stack: e?.stack?.slice?.(0, 300) })
        this.error = { message: e?.message || '加载专家列表失败' }
      } finally {
        this.loadingList = false
        log.info('business', '[fetchExperts] 完成', { listLength: this.list.length, hasError: !!this.error })
      }
    },
    async fetchExpertById(id: string) {
      this.loadingDetail = true
      this.error = null
      try {
        log.info('business', 'fetchExpertById:start', { id })
        // 《16》P44：已下架专家对 C 端 404，用友好文案而非「接口不存在」
        const res = await getExpertDetail(id, { showError: false })
        if (res.code !== 200 || !res.data) throw new Error(res.message || '获取专家详情失败')
        const info: ExpertInfoItem = res.data
        const dept = [info.hospital, info.department_name || info.department].filter(Boolean).join('｜')
        const specialization = (info.expertise_areas || '')
          .split(',')
          .map((s: string) => s.trim())
          .filter((s: string) => !!s)
        this.detail = {
          id: info.id,
          name: info.name,
          avatar: resolveAvatarUrl(info.avatar_url),
          title: info.title || '',
          department: dept,
          bio: info.bio,
          specialization,
          stats: { followers: 0, sessions: 0, views: 0 }
        }
        log.info('business', 'fetchExpertById:success', { id })
      } catch (e: any) {
        const statusCode = Number(e?.statusCode)
        const bizCode = Number(e?.code)
        const inactive =
          statusCode === 404 ||
          bizCode === 2001 ||
          String(e?.message || '').includes('资源不存在')
        this.error = { message: inactive ? '专家已下架' : e?.message || '加载专家详情失败' }
        this.detail = null
        this.sessions = []
        log.error('business', 'fetchExpertById:error', e)
      } finally {
        this.loadingDetail = false
      }
    },
    async fetchExpertSessions(id: string, _params?: { page?: number; pageSize?: number }) {
      this.loadingSessions = true
      this.error = null
      try {
        log.info('business', 'fetchExpertSessions:start', { id, params: _params })
        const res = await getExpertSessions(id, { page: 1, size: _params?.pageSize ?? 50 })
        if (res.code !== 200) throw new Error(res.message || '获取专家直播失败')
        const raw = res.data as any
        const items: ExpertSessionBriefItem[] = raw?.sessions?.items ?? []
        this.sessions = items.map((it) => {
          const raw = it as ExpertSessionBriefItem & Record<string, any>
          const roomId =
            (typeof raw.room_id === 'string' && raw.room_id.trim()) ||
            (typeof raw.roomId === 'string' && raw.roomId.trim()) ||
            (typeof raw.room?.id === 'string' && raw.room.id.trim()) ||
            (typeof raw.room_info?.id === 'string' && raw.room_info.id.trim()) ||
            undefined
          return {
            id: it.id,
            roomId: roomId || undefined,
            title: it.room_title,
            cover: resolveMediaUrl(it.cover_url) || DEFAULT_CONFIG.DEFAULT_COVER,
            status: normalizeExpertSessionStatus(it.status),
            scheduledAt: it.start_time,
            viewers: undefined
          }
        })
        log.info('business', 'fetchExpertSessions:success', { id, sessions: items.length })
      } catch (e: any) {
        this.error = { message: e?.message || '加载专家直播失败' }
        this.sessions = []
        log.error('business', 'fetchExpertSessions:error', e)
      } finally {
        this.loadingSessions = false
      }
    },
    async checkFollow(id: string) {
      this.error = null
      try {
        // 后端无独立“是否关注”检查接口，从已关注列表推断状态
        const res = await getMyFollowedExperts()
        if (res.code === 200 && Array.isArray(res.data)) {
          const followedIds = new Set(
            res.data
              .map((e: any) => String(e?.expert_id || e?.id || '').trim())
              .filter(Boolean)
          )
          // 一次拉取同步所有已关注，供直播间专家列表等复用
          for (const fid of followedIds) {
            this.followingMap[fid] = true
          }
          const isFollowing = followedIds.has(id)
          this.followingMap[id] = isFollowing
          log.info('business', 'checkFollow', { id, is_following: isFollowing })
        }
      } catch (e: any) {
        // 静默失败，不影响页面加载
        log.warn('business', 'checkFollow:failed', { id })
      }
    },
    async follow(id: string) {
      if (!id) return
      this.followPending = true
      this.followPendingId = id
      this.error = null
      try {
        log.info('business', 'follow:start', { id })
        const res = await followExpert(id)
        if (res.code !== 200) throw new Error(res.message || '关注失败')
        this.followingMap[id] = true
        // 提升详情页显示的粉丝数（若存在）
        if (this.detail?.id === id) {
          this.detail.stats.followers += 1
        }
        log.info('business', 'follow:success', { id })
      } catch (e: any) {
        const statusCode = e?.statusCode
        const msg = String(e?.message || '')
        // 幂等：后端若提示已关注，视为成功
        if (statusCode === 400 && /已关注|already/i.test(msg)) {
          this.followingMap[id] = true
          log.info('business', 'follow:idempotent', { id })
          return
        }
        this.error = { message: e?.message || '关注失败' }
        log.error('business', 'follow:error', e)
        throw e
      } finally {
        this.followPending = false
        if (this.followPendingId === id) this.followPendingId = null
      }
    },
    async unfollow(id: string) {
      if (!id) return
      this.followPending = true
      this.followPendingId = id
      this.error = null
      try {
        log.info('business', 'unfollow:start', { id })
        const res = await unfollowExpert(id)
        if (res.code !== 200) throw new Error(res.message || '取消关注失败')
        this.followingMap[id] = false
        if (this.detail?.id === id) {
          this.detail.stats.followers = Math.max(0, this.detail.stats.followers - 1)
        }
        log.info('business', 'unfollow:success', { id })
      } catch (e: any) {
        const statusCode = e?.statusCode
        const msg = String(e?.message || '')
        // 幂等：后端若提示未关注，视为成功
        if (statusCode === 400 && /未关注|not/i.test(msg)) {
          this.followingMap[id] = false
          log.info('business', 'unfollow:idempotent', { id })
          return
        }
        this.error = { message: e?.message || '取消关注失败' }
        log.error('business', 'unfollow:error', e)
        throw e
      } finally {
        this.followPending = false
        if (this.followPendingId === id) this.followPendingId = null
      }
    },
    async toggleFollow(id: string) {
      if (!id) return
      if (this.followPendingId === id) return
      if (this.followingMap[id]) {
        await this.unfollow(id)
      } else {
        await this.follow(id)
      }
    },
    reset() {
      this.list = []
      this.detail = null
      this.sessions = []
      this.pagination = { page: 1, pageSize: 10, total: 0, hasMore: true }
      this.error = null
      this.keyword = ''
      this.specialty = ''
      this.categoryId = ''
      this.followingMap = {}
      this.followPending = false
      this.followPendingId = null
    }
  },
  persist: {
    paths: ['keyword', 'specialty', 'categoryId']
  }
})
