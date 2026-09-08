import { STORAGE_KEYS } from '@/common/constants'
import { resolveMediaUrl } from './url'

export type MyLiveCacheItem = {
  id: string
  title: string
  summary?: string
  cover_url?: string
  status?: string
  created_at?: string
  updated_at: number
}

const MAX_CACHE_ITEMS = 50

function getCacheKey(userId?: string | null): string {
  const normalizedUserId = String(userId || '').trim() || 'anonymous'
  return `${STORAGE_KEYS.MY_LIVE_CACHE}:${normalizedUserId}`
}

function normalizeItem(raw: any): MyLiveCacheItem | null {
  const id = String(raw?.id || '').trim()
  if (!id) return null

  return {
    id,
    title: String(raw?.title || '').trim() || '未命名直播间',
    summary: typeof raw?.summary === 'string' ? raw.summary : '',
    cover_url: typeof raw?.cover_url === 'string' ? raw.cover_url : '',
    status: typeof raw?.status === 'string' ? raw.status : '',
    created_at: typeof raw?.created_at === 'string' ? raw.created_at : '',
    updated_at: Number(raw?.updated_at) > 0 ? Number(raw.updated_at) : Date.now()
  }
}

function save(userId: string | null | undefined, items: MyLiveCacheItem[]) {
  uni.setStorageSync(getCacheKey(userId), items.slice(0, MAX_CACHE_ITEMS))
}

export function readMyLiveCache(userId?: string | null): MyLiveCacheItem[] {
  try {
    const raw = uni.getStorageSync(getCacheKey(userId))
    const items = Array.isArray(raw) ? raw.map(normalizeItem).filter(Boolean) : []
    // 对缓存中的 cover_url 进行解析，确保使用正确的媒体地址
    const resolved = (items as MyLiveCacheItem[]).map(item => ({
      ...item,
      cover_url: item.cover_url ? resolveMediaUrl(item.cover_url) : item.cover_url
    }))
    return resolved.sort((a, b) => b.updated_at - a.updated_at)
  } catch {
    return []
  }
}

export function upsertMyLiveCache(userId: string | null | undefined, item: Omit<MyLiveCacheItem, 'updated_at'> & { updated_at?: number }) {
  const current = readMyLiveCache(userId)
  const existing = current.find((it) => it.id === String(item?.id || '').trim())
  const normalized = normalizeItem({
    ...existing,
    ...item,
    title: String(item?.title || existing?.title || '').trim() || '未命名直播间',
    summary: typeof item?.summary === 'string' ? item.summary : existing?.summary,
    cover_url: typeof item?.cover_url === 'string' && item.cover_url.trim() ? item.cover_url : existing?.cover_url,
    status: typeof item?.status === 'string' && item.status.trim() ? item.status : existing?.status,
    created_at: typeof item?.created_at === 'string' && item.created_at.trim() ? item.created_at : existing?.created_at,
    updated_at: Number(item?.updated_at) > 0 ? Number(item.updated_at) : Date.now()
  })
  if (!normalized) return

  const next = [normalized, ...current.filter((it) => it.id !== normalized.id)]
  save(userId, next)
}

export function removeMyLiveCache(userId: string | null | undefined, roomId: string) {
  const normalizedRoomId = String(roomId || '').trim()
  if (!normalizedRoomId) return
  const current = readMyLiveCache(userId)
  save(userId, current.filter((it) => it.id !== normalizedRoomId))
}

export function mergeMyLiveCache(userId: string | null | undefined, remoteItems: Array<Omit<MyLiveCacheItem, 'updated_at'> & { updated_at?: number }>) {
  const normalizedRemote = (Array.isArray(remoteItems) ? remoteItems : [])
    .map((item) => normalizeItem(item))
    .filter(Boolean) as MyLiveCacheItem[]

  const localItems = readMyLiveCache(userId)
  const map = new Map<string, MyLiveCacheItem>()

  normalizedRemote.forEach((item) => {
    map.set(item.id, item)
  })

  localItems.forEach((item) => {
    if (!map.has(item.id)) {
      map.set(item.id, item)
    }
  })

  const merged = Array.from(map.values()).sort((a, b) => b.updated_at - a.updated_at)
  save(userId, merged)
  return merged
}
