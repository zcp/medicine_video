/**
 * 用户收藏（房间）状态管理（观众端）
 * 对齐接口：GET/POST/DELETE /api/v1/users/me/favorites
 */

import { defineStore } from 'pinia'
import { getRoomById } from '@/api/room'
import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { logger } from '@/logs/logger'

/** 内联收藏 API，避免小程序 require('api/favorites') 模块未注册 */
const addFavorite = (roomId: string) =>
  request.post(API_PATHS.FAVORITE.ADD, { room_id: roomId }, { loading: true, loadingText: '收藏中...' })

const getFavoriteList = (params?: { page?: number; size?: number }) =>
  request.get(API_PATHS.FAVORITE.LIST, { data: params })

const removeFavorite = (roomId: string) =>
  request.delete(API_PATHS.FAVORITE.REMOVE(roomId), { loading: true, loadingText: '取消收藏中...' })

type RoomSummary = {
  title: string
  cover_url: string
}

const roomSummaryCache = new Map<string, RoomSummary>()
const roomSummaryInflight = new Map<string, Promise<RoomSummary | null>>()

let hasLoggedFavoritesShape = false
const favoriteStatusInflight = new Map<string, Promise<boolean>>()

function firstNonEmptyString(...values: any[]): string {
  for (const v of values) {
    if (typeof v === 'string' && v.trim()) return v
    if (typeof v === 'number' && Number.isFinite(v)) return String(v)
  }
  return ''
}

function normalizeUserFavoriteRoom(raw: any): UserFavoriteRoom {
  const roomInfo = raw?.room_info ?? raw?.roomInfo ?? raw?.room_detail ?? raw?.roomDetail ?? null
  const room = raw?.room ?? roomInfo ?? raw?.live_room ?? raw?.liveRoom ?? null
  const roomId = firstNonEmptyString(
    raw?.room_id,
    raw?.roomId,
    room?.id,
    room?.room_id,
    room?.roomId,
    roomInfo?.id,
    roomInfo?.room_id,
    roomInfo?.roomId
  )

  return {
    id: firstNonEmptyString(raw?.id, raw?.favorite_id, raw?.favoriteId, roomId),
    room_id: roomId,
    room_title: firstNonEmptyString(
      raw?.room_title,
      raw?.roomTitle,
      raw?.title,
      raw?.name,
      raw?.room_name,
      raw?.roomName,
      raw?.subject,
      raw?.topic,
      room?.room_title,
      room?.roomTitle,
      room?.title,
      room?.name,
      room?.subject,
      room?.topic,
      roomInfo?.room_title,
      roomInfo?.roomTitle,
      roomInfo?.title,
      roomInfo?.name,
      roomInfo?.subject,
      roomInfo?.topic
    ),
    room_cover_url: firstNonEmptyString(
      raw?.room_cover_url,
      raw?.roomCoverUrl,
      raw?.cover_url,
      raw?.coverUrl,
      raw?.cover,
      raw?.thumbnail,
      raw?.thumb,
      room?.room_cover_url,
      room?.roomCoverUrl,
      room?.cover_url,
      room?.coverUrl,
      room?.cover,
      room?.cover_image,
      room?.coverImage,
      room?.thumbnail,
      roomInfo?.room_cover_url,
      roomInfo?.roomCoverUrl,
      roomInfo?.cover_url,
      roomInfo?.coverUrl,
      roomInfo?.cover,
      roomInfo?.cover_image,
      roomInfo?.coverImage,
      roomInfo?.thumbnail
    ),
    created_at: firstNonEmptyString(
      raw?.created_at,
      raw?.createdAt,
      raw?.created_time,
      raw?.createdTime,
      raw?.favorited_at,
      raw?.favoritedAt,
      raw?.updated_at,
      raw?.updatedAt
    )
  }
}

function normalizeRoomSummaryFromRoomDetail(raw: any): RoomSummary | null {
  if (!raw || typeof raw !== 'object') return null

  // 兼容：部分后端会用 { room: {...} } 包裹
  const root = (raw?.room ?? raw?.room_info ?? raw?.roomInfo ?? raw?.detail ?? raw) as any

  const title = firstNonEmptyString(
    root?.title,
    root?.room_title,
    root?.roomTitle,
    root?.name,
    root?.subject,
    root?.topic
  )

  const cover_url = firstNonEmptyString(
    root?.cover_url,
    root?.coverUrl,
    root?.room_cover_url,
    root?.roomCoverUrl,
    root?.cover,
    root?.cover_image,
    root?.coverImage,
    root?.coverImageUrl,
    root?.thumbnail
  )

  if (!title && !cover_url) return null
  return { title, cover_url }
}

async function getRoomSummary(roomId: string): Promise<RoomSummary | null> {
  const rid = (roomId || '').trim()
  if (!rid) return null
  const cached = roomSummaryCache.get(rid)
  if (cached) return cached

  const inflight = roomSummaryInflight.get(rid)
  if (inflight) return inflight

  const p = (async () => {
    try {
      const res = await getRoomById(rid)
      if (res.code !== 200 || !res.data) return null
      const normalized = normalizeRoomSummaryFromRoomDetail(res.data)
      if (!normalized) return null
      roomSummaryCache.set(rid, normalized)
      return normalized
    } catch {
      return null
    } finally {
      roomSummaryInflight.delete(rid)
    }
  })()

  roomSummaryInflight.set(rid, p)
  return p
}

export interface UserFavoriteRoom {
  id: string
  room_id: string
  room_title: string
  room_cover_url: string
  created_at: string
}

interface UserFavoritesState {
  items: UserFavoriteRoom[]
  favoriteStatus: Record<string, boolean | undefined>
  pendingRoomIds: Set<string>
  page: number
  size: number
  total: number
  loading: boolean
  loadingMore: boolean
  error: string | null
}

export const useUserFavoritesStore = defineStore('userFavorites', {
  state: (): UserFavoritesState => ({
    items: [],
    favoriteStatus: {},
    pendingRoomIds: new Set(),
    page: 1,
    size: 20,
    total: 0,
    loading: false,
    loadingMore: false,
    error: null
  }),

  getters: {
    hasMore: (state) => state.items.length < state.total
  },

  actions: {
    /** 登出时清空列表与状态缓存（含模块级 inflight） */
    resetForLogout() {
      this.items = []
      this.favoriteStatus = {}
      this.pendingRoomIds = new Set()
      this.page = 1
      this.size = 20
      this.total = 0
      this.loading = false
      this.loadingMore = false
      this.error = null
      roomSummaryCache.clear()
      roomSummaryInflight.clear()
      favoriteStatusInflight.clear()
    },

    async hydrateMissingRoomInfo(roomIds?: string[]) {
      const ids = (roomIds && roomIds.length ? roomIds : this.items.map(i => i.room_id))
        .map(v => String(v || '').trim())
        .filter(Boolean)

      const uniqueIds = Array.from(new Set(ids))
      const needHydrate = uniqueIds.filter((rid) => {
        const has = this.items.some(it => it.room_id === rid && (!it.room_title || !it.room_cover_url))
        return has && !roomSummaryCache.has(rid)
      })
      if (needHydrate.length === 0) return

      const summaries = await Promise.all(needHydrate.map(getRoomSummary))
      const hasAny = summaries.some(Boolean)
      if (!hasAny) return

      this.items = this.items.map((it) => {
        const summary = roomSummaryCache.get(it.room_id)
        if (!summary) return it
        if (it.room_title && it.room_cover_url) return it
        return {
          ...it,
          room_title: it.room_title || summary.title,
          room_cover_url: it.room_cover_url || summary.cover_url
        }
      })
    },

    async fetch(params?: { page?: number; size?: number }, append: boolean = false) {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
      }
      this.error = null

      try {
        const nextPage = params?.page ?? (append ? this.page + 1 : 1)
        const pageSize = params?.size ?? this.size

        const res = await getFavoriteList({ page: nextPage, size: pageSize })
        if (res.code !== 200 || !res.data) throw new Error(res.message || '获取收藏失败')

        this.page = res.data.page
        this.size = res.data.size
        this.total = res.data.total
        const rawItems = (res.data.items || []) as any[]
        const normalized = rawItems.map(normalizeUserFavoriteRoom)
        if (append) {
          this.items = this.items.concat(normalized)
        } else {
          // 刷新时：如果后端列表不返回标题/封面，保留旧值避免全量兜底闪烁
          const prevByRoomId = new Map(this.items.map(it => [it.room_id, it]))
          this.items = normalized.map((it) => {
            const prev = prevByRoomId.get(it.room_id)
            if (!prev) return it
            return {
              ...it,
              room_title: it.room_title || prev.room_title,
              room_cover_url: it.room_cover_url || prev.room_cover_url
            }
          })
        }

        normalized.forEach((it) => {
          if (it.room_id) this.favoriteStatus[it.room_id] = true
        })

        // 开发态排查：若收藏列表缺标题/封面，打印一次原始字段结构
        if (process.env.NODE_ENV === 'development' && !hasLoggedFavoritesShape) {
          const firstMissingIndex = normalized.findIndex(it => !it.room_title || !it.room_cover_url)
          if (firstMissingIndex >= 0) {
            const sampleRaw = rawItems[firstMissingIndex]
            const sampleNorm = normalized[firstMissingIndex]
            hasLoggedFavoritesShape = true
            try {
              // eslint-disable-next-line no-console
              console.log('🧩 [favorites] sample raw item keys:', Object.keys(sampleRaw || {}))
              // eslint-disable-next-line no-console
              console.log('🧩 [favorites] sample raw item:', sampleRaw)
              // eslint-disable-next-line no-console
              console.log('🧩 [favorites] normalized item:', sampleNorm)

              logger.info('system', 'favorites sample item (missing title/cover)', {
                rawKeys: Object.keys(sampleRaw || {}),
                raw: sampleRaw,
                normalized: sampleNorm
              })
            } catch {
              // ignore
            }
          }
        }

        // 兜底：若收藏列表未返回房间标题/封面，则按 room_id 再拉一次房间详情补齐
        // 不影响主流程；失败则静默忽略
        void this.hydrateMissingRoomInfo(normalized.map(i => i.room_id))
      } catch (e: any) {
        this.error = e?.message || '获取收藏失败'
        throw e
      } finally {
        this.loading = false
        this.loadingMore = false
      }
    },

    async refresh() {
      await this.fetch({ page: 1, size: this.size }, false)
    },

    async loadMore() {
      if (this.loading || this.loadingMore || !this.hasMore) return
      await this.fetch(undefined, true)
    },

    async checkStatus(roomId: string): Promise<boolean> {
      const rid = String(roomId || '').trim()
      if (!rid) return false

      const cached = this.favoriteStatus[rid]
      if (typeof cached === 'boolean') return cached

      const inflight = favoriteStatusInflight.get(rid)
      if (inflight) return inflight

      const p = (async () => {
        try {
          // 后端无独立检查接口，从已加载的收藏列表中推断
          const next = this.items.some((item: any) => item.room_id === rid)
          this.favoriteStatus[rid] = next
          return next
        } catch {
          return false
        } finally {
          favoriteStatusInflight.delete(rid)
        }
      })()

      favoriteStatusInflight.set(rid, p)
      return p
    },

    async remove(roomId: string) {
      const rid = String(roomId || '').trim()
      if (!rid) return
      if (this.pendingRoomIds.has(rid)) return
      this.pendingRoomIds.add(rid)
      try {
        const res = await removeFavorite(rid)
        if (res.code !== 200) throw new Error(res.message || '取消收藏失败')
        this.favoriteStatus[rid] = false
        this.items = this.items.filter(i => i.room_id !== rid)
        this.total = Math.max(0, this.total - 1)
      } finally {
        this.pendingRoomIds.delete(rid)
      }
    },

    async add(roomId: string) {
      const rid = String(roomId || '').trim()
      if (!rid) return
      if (this.pendingRoomIds.has(rid)) return
      this.pendingRoomIds.add(rid)
      try {
        const res = await addFavorite(rid)
        if (res.code !== 200) throw new Error(res.message || '收藏失败')
        this.favoriteStatus[rid] = true
      } catch (e: any) {
        const statusCode = e?.statusCode
        const msg = String(e?.message || '')
        // 后端若用 HTTP 400 表示“已收藏”，按幂等语义视为成功
        if (statusCode === 400 && /已收藏|资源已存在|already/i.test(msg)) {
          this.favoriteStatus[rid] = true
          return
        }
        throw e
      } finally {
        this.pendingRoomIds.delete(rid)
      }
      // 不强行插入到列表顶部，避免和分页/排序冲突；需要时由 refresh() 拉新数据
    }
  }
})
