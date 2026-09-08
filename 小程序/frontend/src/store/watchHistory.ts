/**
 * 观看历史状态管理（观众端）
 * 对齐接口：GET/DELETE /api/v1/users/me/watch-history
 */

import { defineStore } from 'pinia'
import { deleteWatchHistory, getWatchHistory } from '@/api/history'
import { getSessionDetail } from '@/api/session'
import { getRoomById } from '@/api/room'
import { logger } from '@/logs/logger'

function firstNonEmptyString(...values: any[]): string {
  for (const v of values) {
    if (typeof v === 'string' && v.trim()) return v
    if (typeof v === 'number' && Number.isFinite(v)) return String(v)
  }
  return ''
}

export interface WatchHistoryItem {
  id: string
  session_id: string
  session_title: string
  room_cover_url: string
  progress: number
  watched_at: string
  session_type?: WatchHistorySessionType
  session_status?: WatchHistorySessionStatus
}

export type WatchHistorySessionType = 'scheduled' | 'live' | 'replay'

export type WatchHistorySessionStatus = 'scheduled' | 'live' | 'replay' | 'ended' | 'playback'

interface LocalWatchHistoryItem extends WatchHistoryItem {
  session_type: WatchHistorySessionType
  session_status?: WatchHistorySessionStatus
  _local: true
}

const LOCAL_STORAGE_KEY = 'watchHistoryLocal_v1'
const TYPE_MAP_STORAGE_KEY = 'watchHistoryTypeMap_v1'

const sessionTypeCache = new Map<string, WatchHistorySessionType>()
const sessionTypeInflight = new Map<string, Promise<WatchHistorySessionType | null>>()

function coerceSessionType(v: any): WatchHistorySessionType | null {
  if (v === 'scheduled' || v === 'live' || v === 'replay') return v
  return null
}

function typeFromSessionStatus(statusRaw: any): WatchHistorySessionType {
  const s = typeof statusRaw === 'string' ? statusRaw.toLowerCase() : ''
  if (s === 'scheduled' || s === 'pending' || s === 'upcoming' || s === 'preview') return 'scheduled'
  if (s === 'ended' || s === 'replay' || s === 'playback') return 'replay'
  return 'live'
}

async function hydrateSessionType(sessionId: string): Promise<WatchHistorySessionType | null> {
  const sid = firstNonEmptyString(sessionId)
  if (!sid) return null
  if (sessionTypeCache.has(sid)) return sessionTypeCache.get(sid)!
  const inflight = sessionTypeInflight.get(sid)
  if (inflight) return inflight

  const p = (async (): Promise<WatchHistorySessionType | null> => {
    try {
      const res = await getSessionDetail(sid)
      const s: any = (res as any)?.data ?? res
      const t = typeFromSessionStatus(s?.status)
      sessionTypeCache.set(sid, t)
      return t
    } catch {
      return null
    } finally {
      sessionTypeInflight.delete(sid)
    }
  })()

  sessionTypeInflight.set(sid, p)
  return p
}

type HydratedInfo = { session_title: string; room_cover_url: string; session_status: WatchHistorySessionStatus | '' }
const hydratedCache = new Map<string, HydratedInfo>()
const hydratedInflight = new Map<string, Promise<HydratedInfo | null>>()

async function hydrateSessionInfo(sessionId: string): Promise<HydratedInfo | null> {
  const sid = firstNonEmptyString(sessionId)
  if (!sid) return null
  if (hydratedCache.has(sid)) return hydratedCache.get(sid)!
  const inflight = hydratedInflight.get(sid)
  if (inflight) return inflight

  const p = (async (): Promise<HydratedInfo | null> => {
    try {
      const sRes = await getSessionDetail(sid)
      const s: any = (sRes as any)?.data ?? sRes
      const roomId = firstNonEmptyString(s?.room_id, s?.roomId, s?.room?.id, s?.room_info?.id)

      let room: any = null
      if (roomId) {
        try {
          const rRes = await getRoomById(roomId)
          room = (rRes as any)?.data ?? rRes
        } catch {
          room = null
        }
      }

      const title = firstNonEmptyString(
        s?.title,
        s?.name,
        room?.title,
        room?.name,
        room?.room_title,
        room?.roomTitle
      )
      const cover = firstNonEmptyString(
        room?.cover_url,
        room?.coverUrl,
        room?.cover,
        room?.cover_image,
        s?.cover_url,
        s?.coverUrl,
        s?.cover
      )

      const info: HydratedInfo = {
        session_title: title,
        room_cover_url: cover,
        session_status: firstNonEmptyString(s?.status, s?.live_status, s?.session_status) as WatchHistorySessionStatus | ''
      }
      hydratedCache.set(sid, info)
      return info
    } catch {
      return null
    } finally {
      hydratedInflight.delete(sid)
    }
  })()

  hydratedInflight.set(sid, p)
  return p
}

function normalizeWatchHistoryItem(raw: any): WatchHistoryItem {
  const obj: any = raw && typeof raw === 'object' ? raw : {}
  const sessionInfo = obj.session_info ?? obj.sessionInfo ?? null
  const session = obj.session ?? sessionInfo ?? null
  const roomInfo = obj.room_info ?? obj.roomInfo ?? session?.room_info ?? session?.roomInfo ?? null
  const room = obj.room ?? roomInfo ?? session?.room ?? null

  const id = firstNonEmptyString(obj.id)
  const sessionId = firstNonEmptyString(
    obj.session_id,
    obj.sessionId,
    obj.session?.id,
    obj.session?.session_id,
    obj.session?.sessionId,
    sessionInfo?.id,
    sessionInfo?.session_id,
    sessionInfo?.sessionId
  )

  const sessionTitle = firstNonEmptyString(
    obj.session_title,
    obj.sessionTitle,
    obj.session?.title,
    obj.session?.name,
    session?.title,
    session?.name,
    sessionInfo?.title,
    sessionInfo?.name,
    obj.title,
    obj.room_title,
    obj.roomTitle,
    obj.room?.title,
    obj.room?.name,
    room?.title,
    room?.name,
    roomInfo?.title,
    roomInfo?.name,
    roomInfo?.room_title,
    roomInfo?.roomTitle
  )

  const roomCoverUrl = firstNonEmptyString(
    obj.room_cover_url,
    obj.roomCoverUrl,
    obj.room?.cover_url,
    obj.room?.coverUrl,
    obj.room?.cover,
    obj.room?.cover_image,
    room?.cover_url,
    room?.coverUrl,
    room?.cover,
    room?.cover_image,
    roomInfo?.cover_url,
    roomInfo?.coverUrl,
    roomInfo?.cover,
    roomInfo?.cover_image,
    roomInfo?.room_cover_url,
    roomInfo?.roomCoverUrl,
    session?.cover_url,
    session?.coverUrl,
    session?.cover,
    sessionInfo?.cover_url,
    sessionInfo?.coverUrl,
    sessionInfo?.cover,
    obj.cover_url,
    obj.coverUrl,
    obj.cover,
    obj.thumbnail
  )

  const progressRaw = obj.progress ?? obj.last_position ?? obj.lastPosition ?? 0
  const progress = Number(progressRaw) || 0

  const sessionType = coerceSessionType(
    obj.session_type ?? obj.sessionType ?? session?.session_type ?? session?.sessionType
  ) || typeFromSessionStatus(obj.session_status ?? obj.sessionStatus ?? session?.status ?? session?.live_status ?? obj.status)

  const sessionStatus = firstNonEmptyString(
    obj.session_status,
    obj.sessionStatus,
    session?.status,
    session?.live_status,
    obj.status
  ) as WatchHistorySessionStatus | ''

  const watchedAt = firstNonEmptyString(
    obj.watched_at,
    obj.watchedAt,
    obj.updated_at,
    obj.updatedAt,
    obj.created_at,
    obj.createdAt,
    obj.last_watched_at,
    obj.lastWatchedAt
  )

  return {
    id,
    session_id: sessionId,
    session_title: sessionTitle,
    room_cover_url: roomCoverUrl,
    progress,
    watched_at: watchedAt,
    session_type: sessionType,
    session_status: sessionStatus || undefined
  }
}

type WatchHistoryDebugRow = {
  session_id: string
  id: string
  session_type: string
  session_status: string
  watched_at: string
  source: 'local' | 'server' | 'merged'
}

function buildDebugRows(items: WatchHistoryItem[], source: WatchHistoryDebugRow['source'], limit: number = 30): WatchHistoryDebugRow[] {
  return items
    .filter(it => !!firstNonEmptyString(it?.session_id))
    .slice(0, limit)
    .map(it => ({
      session_id: firstNonEmptyString(it.session_id),
      id: firstNonEmptyString(it.id),
      session_type: firstNonEmptyString(it.session_type) || 'unknown',
      session_status: firstNonEmptyString(it.session_status) || 'unknown',
      watched_at: firstNonEmptyString(it.watched_at),
      source
    }))
}

function findCrossTypeConflicts(rows: WatchHistoryDebugRow[]) {
  const map: Record<string, { types: string[]; sources: string[]; ids: string[] }> = {}

  for (const row of rows) {
    if (!map[row.session_id]) {
      map[row.session_id] = { types: [], sources: [], ids: [] }
    }
    const entry = map[row.session_id]
    if (!entry.types.includes(row.session_type)) entry.types.push(row.session_type)
    if (!entry.sources.includes(row.source)) entry.sources.push(row.source)
    if (row.id && !entry.ids.includes(row.id)) entry.ids.push(row.id)
  }

  return Object.entries(map)
    .filter(([, v]) => v.types.length > 1)
    .map(([session_id, v]) => ({
      session_id,
      types: v.types,
      sources: v.sources,
      ids: v.ids
    }))
}

interface WatchHistoryState {
  items: WatchHistoryItem[]
  localItems: LocalWatchHistoryItem[]
  localRestored: boolean
  typeMap: Record<string, WatchHistorySessionType>
  typeMapRestored: boolean
  page: number
  size: number
  total: number
  sessionType: WatchHistorySessionType
  loading: boolean
  loadingMore: boolean
  error: string | null
}

export const useWatchHistoryStore = defineStore('watchHistory', {
  state: (): WatchHistoryState => ({
    items: [],
    localItems: [],
    localRestored: false,
    typeMap: {},
    typeMapRestored: false,
    page: 1,
    size: 20,
    total: 0,
    sessionType: 'live',
    loading: false,
    loadingMore: false,
    error: null
  }),

  getters: {
    hasMore: (state) => state.items.length < state.total
  },

  actions: {
    /** 登出时清空服务端列表态与本机观看缓存，避免换号串数据 */
    resetForLogout() {
      this.items = []
      this.localItems = []
      this.localRestored = false
      this.typeMap = {}
      this.typeMapRestored = false
      this.page = 1
      this.size = 20
      this.total = 0
      this.sessionType = 'live'
      this.loading = false
      this.loadingMore = false
      this.error = null
      sessionTypeCache.clear()
      sessionTypeInflight.clear()
      hydratedCache.clear()
      hydratedInflight.clear()
      try {
        uni.removeStorageSync(LOCAL_STORAGE_KEY)
        uni.removeStorageSync(TYPE_MAP_STORAGE_KEY)
      } catch {
        // ignore
      }
    },

    restoreTypeMapOnce() {
      if (this.typeMapRestored) return
      this.typeMapRestored = true
      try {
        const raw = uni.getStorageSync(TYPE_MAP_STORAGE_KEY)
        if (!raw) return
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
        if (!parsed || typeof parsed !== 'object') return
        const next: Record<string, WatchHistorySessionType> = {}
        for (const [k, v] of Object.entries(parsed)) {
          const sid = firstNonEmptyString(k)
          const t = coerceSessionType(v)
          if (!sid || !t) continue
          next[sid] = t
        }
        this.typeMap = next
      } catch {
        // ignore
      }
    },

    persistTypeMap() {
      try {
        uni.setStorageSync(TYPE_MAP_STORAGE_KEY, JSON.stringify(this.typeMap))
      } catch {
        // ignore
      }
    },

    syncTypeMapFromLocalItems(limit: number = 0) {
      this.restoreLocalOnce()
      let changed = false
      const items = limit > 0 ? this.localItems.slice(0, limit) : this.localItems

      for (const it of items) {
        const sid = firstNonEmptyString(it?.session_id)
        const t = coerceSessionType(it?.session_type)
        if (!sid || !t) continue
        if (this.typeMap[sid] !== t) {
          this.typeMap[sid] = t
          changed = true
        }
      }

      if (changed) this.persistTypeMap()
    },

    async hydrateTypeMapFromItems(items: WatchHistoryItem[], limit: number = 6) {
      this.restoreTypeMapOnce()
      this.syncTypeMapFromLocalItems()
      const missing = items
        .map(it => firstNonEmptyString(it?.session_id))
        .filter(Boolean)
        .filter(sid => !this.typeMap[sid])
        .slice(0, limit)

      if (missing.length === 0) return

      let changed = false
      await Promise.all(
        missing.map(async (sid) => {
          const t = await hydrateSessionType(sid)
          if (!t) return
          if (this.typeMap[sid] !== t) {
            this.typeMap[sid] = t
            changed = true
          }
        })
      )

      if (changed) this.persistTypeMap()
    },

    async reconcileTypeMapFromItems(items: WatchHistoryItem[], limit: number = 6) {
      // 纠正已存在但可能错误的映射（例如：回放被错误归到 live）
      this.restoreTypeMapOnce()
      this.syncTypeMapFromLocalItems()
      const sids: string[] = []
      for (const it of items) {
        const sid = firstNonEmptyString(it?.session_id)
        if (!sid) continue
        if (sids.includes(sid)) continue
        sids.push(sid)
        if (sids.length >= limit) break
      }

      if (sids.length === 0) return

      let changed = false
      await Promise.all(
        sids.map(async (sid) => {
          const t = await hydrateSessionType(sid)
          if (!t) return
          if (this.typeMap[sid] !== t) {
            this.typeMap[sid] = t
            changed = true
          }
        })
      )

      if (changed) this.persistTypeMap()
    },

    async hydrateMissingInfo(limit: number = 6) {
      const candidates = this.items
        .filter(i => i?.session_id && (!i.session_title || !i.room_cover_url || !i.session_status))
        .slice(0, limit)

      if (candidates.length === 0) return

      this.restoreLocalOnce()

      await Promise.all(
        candidates.map(async (it) => {
          const sid = firstNonEmptyString(it.session_id)
          if (!sid) return
          const hydrated = await hydrateSessionInfo(sid)
          if (!hydrated) return

          const title = hydrated.session_title
          const cover = hydrated.room_cover_url
          const sessionStatus = hydrated.session_status
          if (!title && !cover && !sessionStatus) return

          // 更新展示列表
          const idx = this.items.findIndex(x => x.session_id === sid)
          if (idx >= 0) {
            const prev = this.items[idx]
            this.items[idx] = {
              ...prev,
              session_title: prev.session_title || title,
              room_cover_url: prev.room_cover_url || cover,
              session_status: prev.session_status || sessionStatus || undefined,
              session_type: prev.session_type || (sessionStatus ? typeFromSessionStatus(sessionStatus) : undefined)
            }
          }

          // 同步更新本地缓存（若存在）
          const lidx = this.localItems.findIndex(x => x.session_id === sid)
          if (lidx >= 0) {
            const prev = this.localItems[lidx]
            this.localItems[lidx] = {
              ...prev,
              session_title: prev.session_title || title,
              room_cover_url: prev.room_cover_url || cover,
              session_status: prev.session_status || sessionStatus || undefined,
              session_type: prev.session_type || (sessionStatus ? typeFromSessionStatus(sessionStatus) : prev.session_type)
            }
          }
        })
      )

      this.persistLocal()
    },

    restoreLocalOnce() {
      if (this.localRestored) return
      this.localRestored = true
      try {
        const raw = uni.getStorageSync(LOCAL_STORAGE_KEY)
        if (!raw) return
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
        if (!Array.isArray(parsed)) return
        const normalized: LocalWatchHistoryItem[] = []
        for (const it of parsed) {
          const obj: any = it && typeof it === 'object' ? it : null
          if (!obj) continue
          const sessionType = coerceSessionType(obj.session_type) || 'live'
          const base = normalizeWatchHistoryItem(obj)
          if (!base.session_id) continue
          normalized.push({
            ...base,
            id: base.id || `local_${base.session_id}`,
            session_type: sessionType,
            session_status: base.session_status,
            _local: true
          })
        }
        // 最新优先
        normalized.sort((a, b) => (b.watched_at || '').localeCompare(a.watched_at || ''))
        this.localItems = normalized
      } catch {
        // ignore
      }
    },

    persistLocal() {
      try {
        uni.setStorageSync(LOCAL_STORAGE_KEY, JSON.stringify(this.localItems.slice(0, 200)))
      } catch {
        // ignore
      }
    },

    upsertLocalRecord(payload: {
      session_id: string
      session_title: string
      room_cover_url: string
      progress: number
      watched_at: string
      session_type: WatchHistorySessionType
    }) {
      this.restoreLocalOnce()

      const sessionId = firstNonEmptyString(payload.session_id)
      if (!sessionId) return

      const next: LocalWatchHistoryItem = {
        id: `local_${sessionId}`,
        session_id: sessionId,
        session_title: payload.session_title || '未命名场次',
        room_cover_url: payload.room_cover_url || '',
        progress: Number(payload.progress) || 0,
        watched_at: payload.watched_at || new Date().toISOString(),
        session_type: payload.session_type,
        _local: true
      }

      const idx = this.localItems.findIndex(i => i.session_id === sessionId)
      if (idx >= 0) {
        const prev = this.localItems[idx]
        this.localItems.splice(idx, 1)
        this.localItems.unshift({
          ...prev,
          ...next,
          session_title: next.session_title || prev.session_title,
          room_cover_url: next.room_cover_url || prev.room_cover_url
        })
      } else {
        this.localItems.unshift(next)
      }

      this.persistLocal()
    },

    async migrateLocalIfEnded(limit: number = 10) {
      this.restoreLocalOnce()
      const candidates = this.localItems.filter(i => i.session_type === 'live' && i.session_id).slice(0, limit)
      if (candidates.length === 0) return

      let changed = false
      for (const it of candidates) {
        try {
          const res = await getSessionDetail(it.session_id)
          const s: any = (res as any)?.data ?? res
          const status = typeof s?.status === 'string' ? s.status.toLowerCase() : ''
          if (status === 'ended' || status === 'replay' || status === 'playback') {
            const idx = this.localItems.findIndex(x => x.session_id === it.session_id)
            if (idx >= 0 && this.localItems[idx].session_type !== 'replay') {
              this.localItems[idx] = { ...this.localItems[idx], session_type: 'replay' }
              changed = true
            }
          }
        } catch {
          // ignore
        }
      }

      if (changed) {
        this.persistLocal()
        this.syncTypeMapFromLocalItems(limit)
      }
    },

    getLocalViewItems(): WatchHistoryItem[] {
      this.restoreLocalOnce()
      this.restoreTypeMapOnce()
      const filtered = this.localItems.filter(i => i.session_type === this.sessionType)
      // 保持倒序（新到旧）
      return filtered
        .slice()
        .sort((a, b) => (b.watched_at || '').localeCompare(a.watched_at || ''))
        .map(({ _local, ...rest }) => rest)
    },

    removeLocal(historyId: string) {
      this.restoreLocalOnce()
      const id = firstNonEmptyString(historyId)
      if (!id) return

      let removedSessionId = ''
      if (id.startsWith('local_')) {
        removedSessionId = id.replace(/^local_/, '')
        this.localItems = this.localItems.filter(i => i.session_id !== removedSessionId)
      } else {
        const idx = this.localItems.findIndex(i => i.id === id)
        if (idx >= 0) {
          removedSessionId = this.localItems[idx].session_id
          this.localItems.splice(idx, 1)
        }
      }

      if (removedSessionId) {
        this.items = this.items.filter(i => i.session_id !== removedSessionId)
      } else {
        this.items = this.items.filter(i => i.id !== id)
      }

      this.total = Math.max(0, this.total - 1)
      this.persistLocal()
    },

    async fetch(params?: { page?: number; size?: number }, append: boolean = false) {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
      }
      this.error = null

      this.restoreLocalOnce()
      this.restoreTypeMapOnce()
      this.syncTypeMapFromLocalItems()

      // 进入“直播中”列表时，先把已结束的本地 live 迁移到 replay，避免误显示
      if (!append && this.sessionType === 'live') {
        try {
          await this.migrateLocalIfEnded(8)
        } catch {
          // ignore
        }
      }

      const nextPage = params?.page ?? (append ? this.page + 1 : 1)
      const pageSize = params?.size ?? this.size

      try {
        const res = await getWatchHistory({ page: nextPage, size: pageSize, sessionType: this.sessionType })
        if (res.code !== 200 || !res.data) throw new Error(res.message || '获取观看历史失败')

        this.page = res.data.page
        this.size = res.data.size
        this.total = res.data.total
        const normalizedAll: WatchHistoryItem[] = Array.isArray(res.data.items)
          ? res.data.items.map(normalizeWatchHistoryItem)
          : []

        const serverRows = buildDebugRows(normalizedAll, 'server')
        logger.info('system', 'watch_history_server_items_snapshot', {
          sessionType: this.sessionType,
          page: nextPage,
          size: pageSize,
          totalFromServer: res.data.total,
          count: normalizedAll.length,
          rows: serverRows
        })

        // 先用场次详情补齐一部分“类型映射”，用于客户端分组（后端可能不支持 sessionType 过滤）
        await this.hydrateTypeMapFromItems(normalizedAll, 6)

        // 对当前页做一次强校准：修正“回放落在直播中”等历史错误映射
        // 只校准少量，避免过多请求
        await this.reconcileTypeMapFromItems(normalizedAll, this.sessionType === 'live' ? 8 : 4)

        // 再次用本地记录兜底，确保同一个 session 的本地显式类型优先于详情推断
        this.syncTypeMapFromLocalItems()

        // 客户端按 typeMap 过滤：避免“预告/直播/回放多个tab展示同一场”
        // 优先级：known(typeMap/local) > explicit(server)；只有 unknown 才采用 explicit
        let typeMapChanged = false
        const normalized = normalizedAll.filter((it) => {
          const sid = firstNonEmptyString(it?.session_id)
          if (!sid) return false

          const known = this.typeMap[sid]
          if (known) {
            const explicitType = coerceSessionType(it?.session_type)
            if (explicitType && explicitType !== known) {
              logger.warn('system', 'watch_history_type_mismatch_keep_known', {
                session_id: sid,
                sessionType: this.sessionType,
                known,
                explicit: explicitType,
                itemId: firstNonEmptyString(it?.id) || null
              })
            }
            return known === this.sessionType
          }

          const explicit = coerceSessionType(it?.session_type)
          if (explicit) {
            if (this.typeMap[sid] !== explicit) {
              this.typeMap[sid] = explicit
              typeMapChanged = true
            }
            return explicit === this.sessionType
          }

          return false
        })
        if (typeMapChanged) {
          this.persistTypeMap()
        }

        const local = !append ? this.getLocalViewItems() : []
        if (!append) {
          logger.info('system', 'watch_history_local_items_snapshot', {
            sessionType: this.sessionType,
            count: local.length,
            rows: buildDebugRows(local, 'local')
          })
        }
        const localSessionIds = new Set(local.map(i => i.session_id))
        const merged = !append
          ? local.concat(normalized.filter(i => i.session_id && !localSessionIds.has(i.session_id)))
          : this.items.concat(normalized.filter(i => i.session_id && !this.items.some(x => x.session_id === i.session_id)))

        const mergedRows = buildDebugRows(merged, 'merged')
        const conflicts = findCrossTypeConflicts([
          ...serverRows,
          ...(append ? [] : buildDebugRows(local, 'local')),
          ...mergedRows
        ])
        logger.info('system', 'watch_history_merged_items_snapshot', {
          sessionType: this.sessionType,
          append,
          count: merged.length,
          rows: mergedRows,
          conflictCount: conflicts.length
        })
        if (conflicts.length > 0) {
          logger.warn('system', 'watch_history_cross_type_conflict_detected', {
            sessionType: this.sessionType,
            conflictCount: conflicts.length,
            conflicts
          })
        }

        // 若后端返回空列表（常见：后端未真正写入 watch-history），回退展示本地记录
        if (!append && normalized.length === 0) {
          if (local.length > 0) {
            this.page = 1
            this.size = pageSize
            this.total = local.length
            this.items = local
          } else {
            this.items = []
            this.total = 0
          }
        } else {
          // 对当前 tab 的“展示总数”用 merged 长度更靠谱（后端 total 很可能是不分类型的）
          this.items = merged
          if (!append) {
            this.page = 1
            this.size = pageSize
            this.total = merged.length
          } else {
            this.total = Math.max(this.total, this.items.length)
          }
        }

        // 补齐缺失的标题/封面（后端可能只给 session_id 等最小字段）
        await this.hydrateMissingInfo(6)
      } catch (e: any) {
        const statusCode = e?.statusCode
        logger.error('system', 'watch_history_fetch_failed', {
          sessionType: this.sessionType,
          append,
          page: nextPage,
          size: pageSize,
          statusCode: statusCode ?? null,
          message: e?.message || 'unknown_error'
        })
        // 后端未实现/未路由到：用本地历史兜底，不打断页面
        if (statusCode === 404) {
          if (this.sessionType === 'live') {
            // 尝试把已结束的直播迁移到回放
            await this.migrateLocalIfEnded(8)
          }
          const local = this.getLocalViewItems()
          this.page = 1
          this.size = pageSize
          this.total = local.length
          this.items = append ? this.items.concat(local) : local
          this.error = null
          await this.hydrateMissingInfo(6)
          return
        }

        this.error = e?.message || '获取观看历史失败'
        throw e
      } finally {
        this.loading = false
        this.loadingMore = false
      }
    },

    async setSessionType(type: WatchHistorySessionType) {
      if (this.sessionType === type) return
      this.sessionType = type
      await this.fetch({ page: 1, size: this.size }, false)
    },

    async refresh() {
      await this.fetch({ page: 1, size: this.size }, false)
    },

    async loadMore() {
      if (this.loading || this.loadingMore || !this.hasMore) return
      await this.fetch(undefined, true)
    },

    async remove(historyId: string) {
      const id = firstNonEmptyString(historyId)
      if (!id) return

      // 本地记录：不打后端
      if (id.startsWith('local_') || this.localItems.some(i => i.id === id)) {
        this.removeLocal(id)
        return
      }

      const res = await deleteWatchHistory(id)
      if (res.code !== 200) throw new Error(res.message || '删除历史失败')
      this.items = this.items.filter(i => i.id !== id)
      this.total = Math.max(0, this.total - 1)
    }
  }
})
