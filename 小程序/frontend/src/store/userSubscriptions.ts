/**
 * 用户订阅（房间开播提醒）状态管理（观众端）
 * 对齐接口：GET/POST/DELETE /api/v1/users/me/subscriptions
 */

import { defineStore } from 'pinia'
import { getRoomById } from '@/api/room'
import { getSessionDetail } from '@/api/session'
import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { resolveMediaUrl } from '@/utils/url'

/** 内联订阅 API，避免小程序 require('api/subscriptions') 模块未注册 */
const getSubscriptionList = (params?: { page?: number; size?: number }) =>
  request.get(API_PATHS.SUBSCRIPTION.LIST, { data: params })

const unsubscribe = (roomId: string) =>
  request.delete(API_PATHS.SUBSCRIPTION.REMOVE(roomId), {
    loading: true,
    loadingText: '取消订阅中...',
    showError: false
  })

const subscribe = async (roomId: string) => {
  const payload = { target_id: String(roomId || '').trim(), target_type: 'room' as const }
  try {
    return await request.post(API_PATHS.SUBSCRIPTION.ADD, payload, {
      loading: true,
      loadingText: '订阅中...',
      showError: false
    })
  } catch (e: any) {
    const statusCode = e?.statusCode
    const msg = String(e?.message || e?.raw?.data?.message || '')
    if ((statusCode === 400 || statusCode === 409) && /已订阅|订阅已存在|资源已存在|already/i.test(msg)) {
      return {
        code: 200,
        message: 'success',
        data: {
          id: '',
          target_id: payload.target_id,
          target_type: payload.target_type,
          is_active: true,
          created_at: ''
        },
        timestamp: new Date().toISOString()
      }
    }
    throw e
  }
}

type RoomSummary = {
  title: string
  cover_url: string
}

const roomSummaryCache = new Map<string, RoomSummary>()
const roomSummaryInflight = new Map<string, Promise<RoomSummary | null>>()

const sessionRoomCache = new Map<string, string | null>()
const sessionRoomInflight = new Map<string, Promise<string | null>>()

let hasLoggedSubscriptionsShape = false
let hasLoggedSubscriptionsResolve = false

function firstNonEmptyString(...values: any[]): string {
  for (const v of values) {
    if (typeof v === 'string' && v.trim()) return v
    if (typeof v === 'number' && Number.isFinite(v)) return String(v)
  }
  return ''
}

function normalizeUserSubscriptionRoom(raw: any): UserSubscriptionRoom {
  const targetType = firstNonEmptyString(raw?.target_type, raw?.targetType).toLowerCase()
  const targetId = firstNonEmptyString(raw?.target_id, raw?.targetId)

  const room = raw?.room ?? raw?.room_info ?? raw?.roomInfo ?? null
  const roomId = firstNonEmptyString(
    raw?.room_id,
    raw?.roomId,
    // 兼容：后端返回 target_type=room
    targetType === 'room' ? targetId : '',
    raw?.room_uuid,
    raw?.roomUuid,
    raw?.roomID,
    room?.id,
    room?.room_id,
    room?.roomId,
    room?.room_uuid,
    room?.roomUuid,
    room?.uuid
  )

  const cover = firstNonEmptyString(
    raw?.room_cover_url,
    raw?.roomCoverUrl,
    raw?.cover_url,
    raw?.coverUrl,
    raw?.cover,
    raw?.room_cover,
    raw?.roomCover,
    room?.room_cover_url,
    room?.roomCoverUrl,
    room?.cover_url,
    room?.coverUrl,
    room?.cover,
    room?.room_cover,
    room?.roomCover
  )

  return {
    id: firstNonEmptyString(raw?.id, raw?.subscription_id, raw?.subscriptionId),
    session_id: targetType === 'session' ? targetId : '',
    room_id: roomId,
    room_title: firstNonEmptyString(
      raw?.room_title,
      raw?.roomTitle,
      raw?.title,
      raw?.name,
      raw?.room_name,
      raw?.roomName,
      room?.room_title,
      room?.roomTitle,
      room?.title,
      room?.name
    ),
    room_cover_url: resolveMediaUrl(cover),
    created_at: firstNonEmptyString(
      raw?.created_at,
      raw?.createdAt,
      raw?.created_time,
      raw?.createdTime,
      raw?.subscribed_at,
      raw?.subscribedAt
    )
  }
}

function normalizeRoomSummaryFromRoomDetail(raw: any): RoomSummary | null {
  if (!raw || typeof raw !== 'object') return null
  const root = (raw?.room ?? raw?.room_info ?? raw?.roomInfo ?? raw?.detail ?? raw) as any

  const title = firstNonEmptyString(
    root?.title,
    root?.room_title,
    root?.roomTitle,
    root?.name,
    root?.room_name,
    root?.roomName
  )

  const cover = firstNonEmptyString(
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

  const cover_url = resolveMediaUrl(cover)
  if (!title && !cover_url) return null
  return { title, cover_url }
}

async function getRoomSummary(roomId: string): Promise<RoomSummary | null> {
  const rid = String(roomId || '').trim()
  if (!rid) return null
  const cached = roomSummaryCache.get(rid)
  if (cached) return cached

  const inflight = roomSummaryInflight.get(rid)
  if (inflight) return inflight

  const p = (async () => {
    try {
      const res: any = await getRoomById(rid, { showError: false })
      if (res?.code !== 200 || !res?.data) return null
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

export interface UserSubscriptionRoom {
  id: string
  session_id: string
  room_id: string
  room_title: string
  room_cover_url: string
  created_at: string
}

interface UserSubscriptionsState {
  items: UserSubscriptionRoom[]
  page: number
  size: number
  total: number
  loading: boolean
  loadingMore: boolean
  error: string | null
  subscriptionStatus: Record<string, boolean | undefined>
}

export const useUserSubscriptionsStore = defineStore('userSubscriptions', {
  state: (): UserSubscriptionsState => ({
    items: [],
    page: 1,
    size: 20,
    total: 0,
    loading: false,
    loadingMore: false,
    error: null,
    subscriptionStatus: {}
  }),

  getters: {
    hasMore: (state) => state.items.length < state.total
  },

  actions: {
    /** 登出时清空订阅列表与状态缓存 */
    resetForLogout() {
      this.items = []
      this.page = 1
      this.size = 20
      this.total = 0
      this.loading = false
      this.loadingMore = false
      this.error = null
      this.subscriptionStatus = {}
      roomSummaryCache.clear()
      roomSummaryInflight.clear()
      sessionRoomCache.clear()
      sessionRoomInflight.clear()
    },

    async hydrateMissingRoomIds() {
      const currentItems = this.items as UserSubscriptionRoom[]
      const needSessionIds = currentItems
        .filter(it => !it.room_id && it.session_id)
        .map(it => it.session_id)
        .map(v => String(v || '').trim())
        .filter(Boolean)

      const uniqueSessionIds = Array.from(new Set(needSessionIds))
      if (uniqueSessionIds.length === 0) return

      const concurrency = 4
      for (let i = 0; i < uniqueSessionIds.length; i += concurrency) {
        const batch = uniqueSessionIds.slice(i, i + concurrency)
        await Promise.all(
          batch.map(async (sid) => {
            if (sessionRoomCache.has(sid)) return
            const inflight = sessionRoomInflight.get(sid)
            if (inflight) {
              await inflight
              return
            }

            const p = (async () => {
              try {
                const res: any = await getSessionDetail(sid, { showError: false })
                const s: any = res?.data ?? res
                const roomId = firstNonEmptyString(
                  s?.room_id,
                  s?.roomId,
                  s?.room_uuid,
                  s?.roomUuid,
                  s?.room?.id,
                  s?.room?.room_id,
                  s?.room?.roomId,
                  s?.room?.room_uuid,
                  s?.room?.roomUuid,
                  s?.room_info?.id,
                  s?.roomInfo?.id,
                  s?.roomInfo?.room_id,
                  s?.roomInfo?.roomId,
                  s?.roomInfo?.room_uuid,
                  s?.roomInfo?.roomUuid
                )
                if (roomId) {
                  sessionRoomCache.set(sid, roomId)

                  if (process.env.NODE_ENV === 'development' && !hasLoggedSubscriptionsResolve) {
                    hasLoggedSubscriptionsResolve = true
                    try {
                      // eslint-disable-next-line no-console
                      console.log('✅ [subscriptions] resolved session->room', { sessionId: sid, roomId })
                    } catch {
                      // ignore
                    }
                  }

                  // 若 session detail 已包含可用 title/cover，先提前写入 roomSummaryCache（减少兜底时间）
                  const title = firstNonEmptyString(
                    s?.room_title,
                    s?.roomTitle,
                    s?.title,
                    s?.name,
                    s?.room?.title,
                    s?.room?.room_title,
                    s?.room_info?.title,
                    s?.roomInfo?.title
                  )
                  const cover = firstNonEmptyString(
                    s?.room_cover_url,
                    s?.roomCoverUrl,
                    s?.cover_url,
                    s?.coverUrl,
                    s?.cover,
                    s?.room?.cover_url,
                    s?.room?.room_cover_url,
                    s?.room_info?.cover_url,
                    s?.roomInfo?.cover_url
                  )
                  const cover_url = resolveMediaUrl(cover)
                  if ((title || cover_url) && !roomSummaryCache.has(roomId)) {
                    roomSummaryCache.set(roomId, { title, cover_url })
                  }
                }
                if (!roomId) {
                  // 成功拿到 session 但解析不到 roomId：做负缓存避免重复请求刷屏
                  sessionRoomCache.set(sid, null)
                }
                return roomId || null
              } catch (e: any) {
                const statusCode = e?.statusCode

                // 订阅里可能存在“已删除/不可见”的 session，404 属于预期；做负缓存避免反复请求
                if (statusCode === 404) {
                  // 兼容：后端偶发把 roomId 填进 target_id，但 target_type 仍标为 session
                  try {
                    const roomRes: any = await getRoomById(sid, { showError: false })
                    if (roomRes?.code === 200 && roomRes?.data) {
                      sessionRoomCache.set(sid, sid)
                      const normalized = normalizeRoomSummaryFromRoomDetail(roomRes.data)
                      if (normalized && !roomSummaryCache.has(sid)) {
                        roomSummaryCache.set(sid, normalized)
                      }
                      return sid
                    }
                  } catch {
                    // ignore
                  }

                  sessionRoomCache.set(sid, null)
                  return null
                }

                return null
              } finally {
                sessionRoomInflight.delete(sid)
              }
            })()

            sessionRoomInflight.set(sid, p)
            await p
          })
        )
      }

      // 将 session->room 映射回填到列表项
      this.items = (this.items as UserSubscriptionRoom[]).map((it) => {
        if (it.room_id) return it
        if (!it.session_id) return it
        const rid = sessionRoomCache.get(it.session_id)
        if (!rid) return it
        return { ...it, room_id: rid }
      })
    },

    async hydrateMissingRoomInfo(roomIds?: string[]) {
      // 订阅接口可能返回 target_type=session，需先把 session_id 换算成 room_id
      await this.hydrateMissingRoomIds()

      const ids = (roomIds && roomIds.length ? roomIds : (this.items as UserSubscriptionRoom[]).map(i => i.room_id))
        .map(v => String(v || '').trim())
        .filter(Boolean)

      const uniqueIds = Array.from(new Set(ids))
      if (uniqueIds.length === 0) return

      const applyCachedSummaryToItems = () => {
        this.items = (this.items as UserSubscriptionRoom[]).map((it) => {
          const summary = roomSummaryCache.get(it.room_id)
          if (!summary) return it
          if (it.room_title && it.room_cover_url) return it
          return {
            ...it,
            room_title: it.room_title || summary.title,
            room_cover_url: it.room_cover_url || summary.cover_url
          }
        })
      }

      // 关键：即使缓存里已经有 summary，也需要把缓存同步回 items（否则“刷新后丢标题/封面”）
      applyCachedSummaryToItems()

      const needHydrate = uniqueIds.filter((rid) => {
        const hasMissing = (this.items as UserSubscriptionRoom[]).some(
          (it) => it.room_id === rid && (!it.room_title || !it.room_cover_url)
        )
        return hasMissing && !roomSummaryCache.has(rid)
      })

      if (needHydrate.length > 0) {
        await Promise.all(needHydrate.map(getRoomSummary))
        applyCachedSummaryToItems()
      }
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

        const res = await getSubscriptionList({ page: nextPage, size: pageSize })
        if (res.code !== 200 || !res.data) throw new Error(res.message || '获取订阅失败')

        const data: any = res.data as any
        const rawItems: any[] =
          (Array.isArray(data?.items) && data.items) ||
          (Array.isArray(data?.list) && data.list) ||
          (Array.isArray(data?.records) && data.records) ||
          (Array.isArray(data?.data) && data.data) ||
          []

        this.page = Number(data?.page ?? data?.page_num ?? data?.pageNum ?? nextPage ?? 1)
        this.size = Number(data?.size ?? data?.page_size ?? data?.pageSize ?? pageSize)
        this.total = Number(data?.total ?? data?.count ?? data?.total_count ?? rawItems.length)

        const normalized: UserSubscriptionRoom[] = rawItems.map(normalizeUserSubscriptionRoom)

        if (append) {
          this.items = (this.items as UserSubscriptionRoom[]).concat(normalized)
        } else {
          // 刷新时：如果后端列表不返回标题/封面，保留旧值避免全量兜底闪烁
          const prevItems = this.items as UserSubscriptionRoom[]
          const prevByRoomId = new Map(prevItems.filter(it => it.room_id).map(it => [it.room_id, it]))
          const prevBySessionId = new Map(prevItems.filter(it => it.session_id).map(it => [it.session_id, it]))
          const prevById = new Map(prevItems.filter(it => it.id).map(it => [it.id, it]))

          this.items = normalized.map((it) => {
            const prev =
              (it.room_id ? prevByRoomId.get(it.room_id) : undefined) ||
              (it.session_id ? prevBySessionId.get(it.session_id) : undefined) ||
              (it.id ? prevById.get(it.id) : undefined)
            if (!prev) return it
            return {
              ...it,
              room_title: it.room_title || prev.room_title,
              room_cover_url: it.room_cover_url || prev.room_cover_url
            }
          })
        }

        for (const item of this.items as UserSubscriptionRoom[]) {
          if (item.room_id) {
            this.subscriptionStatus[item.room_id] = true
          }
        }

        // 开发态排查：若订阅列表缺标题/封面，打印一次原始字段结构
        if (process.env.NODE_ENV === 'development' && !hasLoggedSubscriptionsShape) {
          const firstMissingIndex = normalized.findIndex(it => !it.room_title || !it.room_cover_url)
          if (firstMissingIndex >= 0) {
            const sampleRaw = rawItems[firstMissingIndex]
            const sampleNorm = normalized[firstMissingIndex]
            hasLoggedSubscriptionsShape = true
            try {
              // eslint-disable-next-line no-console
              console.log('🧩 [subscriptions] sample raw item keys:', Object.keys(sampleRaw || {}))
              // eslint-disable-next-line no-console
              console.log('🧩 [subscriptions] sample raw item:', sampleRaw)
              // eslint-disable-next-line no-console
              console.log('🧩 [subscriptions] normalized item:', sampleNorm)
            } catch {
              // ignore
            }
          }
        }

        // 兜底：若订阅列表未返回房间标题/封面，或返回的是 session 订阅，则补齐 room_id/title/cover（后台执行）
        void this.hydrateMissingRoomInfo()
      } catch (e: any) {
        this.error = e?.message || '获取订阅失败'
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

    async remove(roomId: string) {
      const rid = String(roomId || '').trim()
      if (!rid) throw new Error('房间ID缺失')

      const res = await unsubscribe(rid)
      if (res.code !== 200) throw new Error(res.message || '取消订阅失败')

      this.items = this.items.filter(i => i.room_id !== rid)
      this.subscriptionStatus[rid] = false
      this.total = Math.max(0, this.total - 1)
    },

    async add(roomId: string) {
      const rid = String(roomId || '').trim()
      if (!rid) throw new Error('房间ID缺失')

      try {
        const res = await subscribe(rid)
        if (res.code !== 200) throw new Error(res.message || '订阅失败')
        this.subscriptionStatus[rid] = true
      } catch (e: any) {
        const statusCode = e?.statusCode
        const msg = String(e?.message || e?.raw?.data?.message || '')
        // 后端若用 HTTP 400/409 表示“已订阅”，按幂等语义视为成功
        if ((statusCode === 400 || statusCode === 409) && /已订阅|订阅已存在|资源已存在|already/i.test(msg)) {
          this.subscriptionStatus[rid] = true
          return
        }

        throw e
      }
    }
  }
})
