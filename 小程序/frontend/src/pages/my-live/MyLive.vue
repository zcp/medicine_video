<template>
  <view class="my-live-page">
    <view v-if="!isLoggedIn" class="placeholder-content">
      <text class="placeholder-icon iconfont icon-zhibo"></text>
      <text class="placeholder-title">登录后查看我的直播</text>
      <text class="placeholder-desc">创建、管理自己的直播间</text>
      <button class="primary-btn" @tap="goLogin">去登录</button>
    </view>

    <view v-else>
      <view v-if="loadNotice" class="notice">{{ loadNotice }}</view>

      <view v-if="loading" class="loading">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="rooms.length === 0" class="empty">
        <text class="empty-title">暂无直播间</text>
        <text class="empty-desc">{{ emptyDesc }}</text>
      </view>

      <view v-else class="list">
        <view v-for="item in rooms" :key="item.id" class="room" @tap="onRoomTap(item)">
          <image class="room__cover" :src="item.cover" mode="aspectFill" @error="handleCoverError(item)" />
          <view class="room__meta">
            <view class="room__top">
              <text class="room__title">{{ item.title }}</text>
              <view class="room__actions">
                <text v-if="item.source_room_id" class="badge badge--test">连接测试</text>
                <text v-else-if="item.is_private" class="badge badge--private">不公开</text>
                <text v-if="item.status" class="badge">{{ item.status }}</text>
                <button class="mini-btn" :disabled="loading" @tap.stop="openManage(item)">管理</button>
              </view>
            </view>
            <text v-if="item.summary" class="room__summary">{{ item.summary }}</text>
            <text v-if="item.created_at" class="room__time">创建：{{ formatTime(item.created_at) }}</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'
import { deleteRoom, ensureTestRoom, getMyRooms } from '@/api/room'
import { mergeMyLiveCache, readMyLiveCache, removeMyLiveCache } from '@/utils/myLiveCache'
import { resolveCoverUrl, shouldMarkCoverBroken, FALLBACK_COVER, FALLBACK_COVER_ERROR } from '@/utils/url'
import dayjs from 'dayjs'

type MyRoomListItem = {
  id: string
  title: string
  summary?: string
  cover: string
  raw_cover_url?: string
  resolved_cover_url?: string
  cover_fallback_reason?: string
  is_cover_fallback?: boolean
  status?: string
  created_at?: string
  /** 不公开房 */
  is_private?: boolean
  /** 测播间关联正式间；有值则为测播间 */
  source_room_id?: string | null
}

const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isAuthenticated)

const loading = ref(false)
const rooms = ref<MyRoomListItem[]>([])
const total = ref(0)
const loadNotice = ref('')
const emptyDesc = computed(() => loadNotice.value || '去“我的-创建直播”创建一个吧')

function getCurrentUserId(): string | null {
  return String(authStore.userInfo?.user_id || '').trim() || null
}

function normalizeStatus(status?: string): string | undefined {
  const normalized = String(status || '').trim().toLowerCase()
  if (!normalized) return undefined
  if (normalized === 'live') return '直播中'
  if (normalized === 'replay' || normalized === 'finished') return '回放'
  if (normalized === 'scheduled' || normalized === 'upcoming') return '预告'
  return String(status)
}

function resolveCoverWithDiagnostics(rawCoverUrl?: string) {
  const raw = String(rawCoverUrl || '').trim()
  const final = resolveCoverUrl(raw)

  if (final === FALLBACK_COVER) {
    return {
      final,
      raw,
      resolved: final,
      isFallback: true,
      reason: raw ? 'resolved_empty' : 'missing_cover_field'
    }
  }

  return {
    final,
    raw,
    resolved: final,
    isFallback: false,
    reason: ''
  }
}

function mapRoomItem(it: any): MyRoomListItem {
  const coverUrl = String(it?.cover_url || it?.coverUrl || it?.cover || '')
  const roomId = String(it?.id || '')
  const coverInfo = resolveCoverWithDiagnostics(coverUrl)

  if (coverInfo.isFallback) {
    logger.warn('system', 'my_live_cover_fallback_applied', {
      page: 'my_live',
      roomId: roomId || null,
      reason: coverInfo.reason || 'unknown',
      rawCoverUrl: coverInfo.raw || null,
      resolvedCoverUrl: coverInfo.resolved || null,
      finalCoverUrl: coverInfo.final,
      emptyCover: !coverInfo.raw
    })
  }

  return {
    id: roomId,
    title: String(it?.title || '') || '未命名直播间',
    summary: typeof it?.summary === 'string' ? it.summary : '',
    cover: coverInfo.final,
    raw_cover_url: coverInfo.raw,
    resolved_cover_url: coverInfo.resolved,
    cover_fallback_reason: coverInfo.reason || undefined,
    is_cover_fallback: coverInfo.isFallback,
    status: normalizeStatus(it?.status),
    created_at: typeof it?.created_at === 'string' ? it.created_at : undefined,
    is_private: Boolean(it?.is_private),
    source_room_id: it?.source_room_id ? String(it.source_room_id) : null
  }
}

function handleCoverError(item: MyRoomListItem) {
  if (!item) return
  const raw = item.raw_cover_url || ''
  if (!shouldMarkCoverBroken(raw, item.cover === FALLBACK_COVER_ERROR)) return
  if (item.cover !== FALLBACK_COVER_ERROR) {
    item.cover = FALLBACK_COVER_ERROR
    item.is_cover_fallback = true
    item.cover_fallback_reason = item.cover_fallback_reason || 'cover_image_load_error'
  }

  logger.warn('system', 'my_live_cover_load_failed', {
    page: 'my_live',
    roomId: item?.id || null,
    title: item?.title || null,
    imageSrc: item?.cover || null,
    rawCoverUrl: item?.raw_cover_url || null,
    resolvedCoverUrl: item?.resolved_cover_url || null,
    isFallback: !!item?.is_cover_fallback,
    fallbackReason: item?.cover_fallback_reason || null
  })
}

function goLogin() {
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent('/pages/my-live/MyLive')}` })
}

function openRoom(roomId: string) {
  uni.navigateTo({ url: `/pages/live/LiveView?roomId=${encodeURIComponent(roomId)}` })
}

/** 小程序：避免 @tap="openRoom(item.id)" 把 UUID 误当成事件方法名 */
function onRoomTap(item: MyRoomListItem) {
  if (!item?.id) return
  openRoom(item.id)
}

function formatTime(iso: string): string {
  const d = dayjs(iso)
  if (!d.isValid()) return iso
  return d.format('YYYY-MM-DD HH:mm')
}

function openManage(item: MyRoomListItem) {
  if (!item?.id) return
  // 测播间：预览/编辑；正式间：测试连接（暂不涉及推流）
  const isTestRoom = Boolean(item.source_room_id)
  const itemList = isTestRoom
    ? ['打开预览', '编辑直播间', '删除直播间']
    : ['编辑直播间', '测试连接', '删除直播间']
  uni.showActionSheet({
    itemList,
    success: async (res) => {
      const action = itemList[res.tapIndex]
      if (action === '编辑直播间') {
        uni.navigateTo({
          url: `/pages/live/CreateLive?mode=edit&roomId=${encodeURIComponent(String(item.id))}`
        })
      } else if (action === '测试连接') {
        await handleTestConnection(item)
      } else if (action === '打开预览') {
        openRoom(item.id)
      } else if (action === '删除直播间') {
        await confirmDelete(item.id)
      }
    }
  })
}

/**
 * 测试连接：确保测播间后打开预览（房间信息模式；推流能力后续再接）
 */
async function handleTestConnection(item: MyRoomListItem) {
  if (!item?.id || item.source_room_id) return
  try {
    loading.value = true
    const resp: any = await ensureTestRoom(item.id, { title_suffix: '连接测试' })
    if (resp?.code === 3001) {
      goLogin()
      return
    }
    if (resp?.code === 403 || resp?.code === 3002 || resp?.code === 3003) {
      uni.showToast({ title: '无权限', icon: 'none' })
      return
    }
    if (resp?.code !== 200 || !resp?.data?.test_room?.id) {
      uni.showToast({ title: resp?.message || '无法准备测试连接', icon: 'none' })
      return
    }
    const testRoomId = String(resp.data.test_room.id)
    const created = Boolean(resp.data.created)
    uni.showToast({
      title: created ? '已准备测试连接' : '已打开上次测试连接',
      icon: 'none'
    })
    setTimeout(() => {
      uni.navigateTo({
        url: `/pages/live/LiveView?roomId=${encodeURIComponent(testRoomId)}`
      })
    }, 350)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '网络异常，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function confirmDelete(roomId: string) {
  if (!roomId) return
  uni.showModal({
    title: '确认删除直播间？',
    content: '删除后无法恢复',
    confirmText: '删除',
    success: async (res) => {
      if (!res.confirm) return
      try {
        loading.value = true
        const resp: any = await deleteRoom(roomId)
        if (resp?.code !== 200) {
          throw new Error(resp?.message || '删除失败')
        }
        removeMyLiveCache(getCurrentUserId(), roomId)
        uni.showToast({ title: '已删除', icon: 'success' })
        rooms.value = rooms.value.filter((r) => r.id !== roomId)
        total.value = Math.max(0, total.value - 1)
      } catch (e: any) {
        uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
      } finally {
        loading.value = false
      }
    }
  })
}

async function reload() {
  if (!isLoggedIn.value) return
  loading.value = true
  loadNotice.value = ''
  try {
    const res: any = await getMyRooms(undefined, 1, 20)
    const data = res?.data
    const items = Array.isArray(data?.items) ? data.items : []

    const merged = mergeMyLiveCache(getCurrentUserId(), items)
    rooms.value = merged.map(mapRoomItem)
    total.value = Number(data?.total || rooms.value.length || 0)
  } catch (e: any) {
    // 远端接口失败时，回退到本地缓存，避免清缓存后数据彻底丢失
    const cachedItems = readMyLiveCache(getCurrentUserId())
    if (cachedItems.length > 0) {
      loadNotice.value = '正在展示本地缓存的直播间（网络暂不可用）'
      rooms.value = cachedItems.map(mapRoomItem)
      total.value = cachedItems.length
      logger.warn('system', 'my_live_api_failed_fallback_to_cache', {
        page: 'my_live',
        errorMessage: e?.message || null,
        cachedCount: cachedItems.length
      })
    } else {
      uni.showToast({ title: e?.message || '加载失败', icon: 'none' })
      rooms.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

onShow(() => {
  // 管理员不使用「我的直播」入口
  if (authStore.isAdmin) {
    uni.showToast({ title: '管理员无我的直播', icon: 'none' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/profile/Profile' })
    }, 300)
    return
  }
  if (isLoggedIn.value) reload()
})

onPullDownRefresh(async () => {
  try {
    if (isLoggedIn.value) await reload()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.my-live-page {
  min-height: 100vh;
  background-color: var(--color-background);
}

.placeholder-icon {
  font-size: 64px;
  line-height: 1;
  color: var(--color-primary);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  text-align: center;
}

.placeholder-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 16px 0 8px;
}

.placeholder-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.loading,
.empty {
  padding: 18px var(--spacing-lg);
}

.notice {
  padding: 12px var(--spacing-lg) 0;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.loading-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.empty-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-desc {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.list {
  padding: 8px var(--spacing-lg) 18px;
}

.room {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.room:last-child {
  border-bottom: none;
}

.room__cover {
  width: 120px;
  height: 72px;
  border-radius: var(--border-radius-md);
  background: var(--color-bg-secondary);
}

.room__meta {
  flex: 1;
  min-width: 0;
}

.room__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.room__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.room__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--border-radius-full);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
}

.badge--private {
  border-color: rgba(21, 148, 136, 0.35);
  color: #0f766e;
  background: rgba(21, 148, 136, 0.08);
}

.badge--test {
  border-color: rgba(180, 120, 40, 0.35);
  color: #a16207;
  background: rgba(234, 179, 8, 0.12);
}

.mini-btn {
  height: 28px;
  line-height: 28px;
  font-size: 12px;
  padding: 0 10px;
  border-radius: var(--border-radius-full);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.mini-btn:active {
  opacity: 0.85;
}

.room__summary {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room__time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.primary-btn {
  width: 220px;
  height: 44px;
  line-height: 44px;
  margin-top: 18px;
  border-radius: var(--border-radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 14px;
  font-weight: 600;
}

.ghost-btn {
  height: 32px;
  line-height: 32px;
  padding: 0 12px;
  font-size: 12px;
  border-radius: var(--border-radius-full);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}
</style>

