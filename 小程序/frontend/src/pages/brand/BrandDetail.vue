<template>
  <view class="brand-detail">
    <LoadingIndicator v-if="loading" />
    <ErrorBanner v-if="error && !unavailable" :message="error.message" @close="error=null" />
    <template v-if="!loading && brand && !unavailable">
      <BrandProfile
        :name="brand.name"
        :logo="brand.logo_url"
        :description="brand.description ?? undefined"
      />

      <view class="info-card" v-if="brand.website_url">
        <view class="website-block">
          <text class="website-label">官网</text>
          <text class="website-url">{{ brand.website_url }}</text>
          <view class="website-actions">
            <view class="website-btn" @tap="copyWebsite">
              <text>复制</text>
            </view>
            <view class="website-btn website-btn--primary" @tap="openWebsite">
              <text>打开</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section" v-if="brandRoomsLoaded">
        <text class="section-title">关联直播间</text>
        <view class="room-list" v-if="brandRooms.length">
          <view class="room-item" v-for="r in brandRooms" :key="r.room_id" @tap="openRoom(r.room_id)">
            <image
              class="cover"
              :src="roomCoverSrc(r.room_id, r.cover_url)"
              mode="aspectFill"
              @error="onRoomCoverError(r.room_id, r.cover_url)"
            />
            <view class="right">
              <text class="title">{{ r.title }}</text>
              <text class="meta" v-if="r.description">{{ r.description }}</text>
              <text class="meta" v-else>—</text>
            </view>
          </view>
        </view>
        <EmptyState
          v-else
          title="暂无关联直播间"
          :description="roomsEmptyDesc"
        />
      </view>
    </template>
    <EmptyState
      v-if="!loading && (!brand || unavailable)"
      title="品牌不存在或已下架"
      description="该品牌不可用，请返回上一页"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BrandProfile from '@/components/brand/BrandProfile.vue'
import { getAdminBrandRooms, getBrandContent } from '@/api/brands'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'
import type { BrandContentData, BrandItem, BrandRoomItem } from '@/types/brands'
import { logger } from '@/logs/logger'
import { diffObjectKeys } from '@/utils/contractCheck'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
const brand = ref<BrandItem | null>(null)
const loading = ref(false)
const error = ref<Error | null>(null)
/** 16-D5：未启用 / 2001 视同不存在，不展示挂靠 */
const unavailable = ref(false)

const brandRooms = ref<Array<{ room_id: string; title: string; description: string; cover_url: string }>>([])
const brokenRoomCoverIds = ref<Record<string, true>>({})
const brandRoomsLoaded = ref(false)
/** none=公开无数据；admin_ok=管理员拉到；admin_denied=非管理员且无公开数据 */
const roomsSource = ref<'none' | 'content' | 'admin_ok' | 'admin_denied'>('none')

const roomsEmptyDesc = computed(() => {
  if (roomsSource.value === 'admin_denied') {
    return '当前账号无法查看品牌关联直播间（需公开接口或管理员权限）。'
  }
  return '该品牌暂未关联任何直播间'
})

function markUnavailable() {
  unavailable.value = true
  brand.value = null
  brandRooms.value = []
  brandRoomsLoaded.value = false
  error.value = null
}

function mapBrandRooms(items: BrandRoomItem[] | any[]) {
  return items
    .map((it: any) => {
      const roomId = String(it?.room_id || it?.id || '').trim()
      if (!roomId) return null
      return {
        room_id: roomId,
        title: String(it?.room_title || it?.title || '').trim() || '未命名直播间',
        description: String(it?.description || it?.summary || '').trim(),
        cover_url: String(it?.cover_url || '').trim()
      }
    })
    .filter((x): x is { room_id: string; title: string; description: string; cover_url: string } => !!x)
}

function roomCoverSrc(roomId: string, raw?: string | null): string {
  const id = String(roomId || '').trim()
  return resolveCoverUrl(raw, id ? !!brokenRoomCoverIds.value[id] : false)
}

function onRoomCoverError(roomId: string, raw?: string | null) {
  const id = String(roomId || '').trim()
  if (!id || brokenRoomCoverIds.value[id]) return
  if (!shouldMarkCoverBroken(raw, !!brokenRoomCoverIds.value[id])) return
  brokenRoomCoverIds.value = { ...brokenRoomCoverIds.value, [id]: true }
}

async function loadBrandRooms(brandId: string, contentRooms?: any[]) {
  brandRoomsLoaded.value = false
  brandRooms.value = []
  roomsSource.value = 'none'

  // 优先用内容接口里可能带的关联房间（公开）
  if (Array.isArray(contentRooms) && contentRooms.length) {
    brandRooms.value = mapBrandRooms(contentRooms)
    roomsSource.value = 'content'
    brandRoomsLoaded.value = true
    return
  }

  // 无公开 rooms 契约时：仅管理员尝试 Admin 接口；普通用户不静默调 Admin（避免假「暂无」）
  if (!authStore.isAdmin) {
    roomsSource.value = 'admin_denied'
    brandRooms.value = []
    brandRoomsLoaded.value = true
    return
  }

  try {
    const resp: any = await getAdminBrandRooms(brandId, { page: 1, size: 50 })
    const raw = resp?.data
    const items: BrandRoomItem[] = Array.isArray(raw?.items)
      ? raw.items
      : (Array.isArray(raw) ? raw : [])
    brandRooms.value = mapBrandRooms(items)
    roomsSource.value = 'admin_ok'
  } catch (e: any) {
    logger.warn('api', 'BrandDetail loadBrandRooms failed', {
      brand_id: brandId,
      statusCode: Number(e?.statusCode || e?.status || 0),
      message: e?.message || e?.errMsg || null
    })
    brandRooms.value = []
    roomsSource.value = 'admin_ok'
  } finally {
    brandRoomsLoaded.value = true
  }
}

onLoad(async (query: any) => {
  const id = String(query?.id || '')
  logger.info('ui', 'BrandDetail enter', { id })
  if (!id) {
    markUnavailable()
    return
  }
  loading.value = true
  unavailable.value = false
  const startedAt = Date.now()
  try {
    logger.debug('api', 'BrandDetail getBrandContent start', { brand_id: id })
    const resp = await getBrandContent(id)
    if (resp.code === 200 && resp.data) {
      const data: BrandContentData = resp.data

      const dataDiff = diffObjectKeys(data, ['brand_info', 'associated_topics'], ['brand_info', 'associated_topics'])
      if (!dataDiff.ok) {
        logger.warn('api', 'BrandDetail content.data contract mismatch', { brand_id: id, ...dataDiff })
      }

      const brandInfoDiff = diffObjectKeys(
        data.brand_info,
        ['id', 'name', 'slug', 'logo_url', 'description', 'website_url', 'sort_order', 'is_active', 'created_at', 'updated_at'],
        ['id', 'name']
      )
      if (!brandInfoDiff.ok) {
        logger.warn('api', 'BrandDetail brand_info contract mismatch', { brand_id: id, ...brandInfoDiff })
      }

      // 16-D5：漏网 is_active=false 按不可用处理
      if (data.brand_info?.is_active === false) {
        logger.info('api', 'BrandDetail brand inactive (soft-deleted)', { brand_id: id })
        markUnavailable()
        return
      }

      brand.value = data.brand_info

      const contentRooms =
        (data as any)?.associated_rooms ||
        (data as any)?.rooms ||
        (data as any)?.brand_rooms ||
        []
      await loadBrandRooms(id, contentRooms)

      logger.info('api', 'BrandDetail getBrandContent success', {
        brand_id: id,
        name: brand.value?.name,
        roomsCount: brandRooms.value.length,
        roomsSource: roomsSource.value,
        hasLogoUrl: !!brand.value?.logo_url,
        durationMs: Date.now() - startedAt
      })
    } else if (resp.code === 2001) {
      logger.info('api', 'BrandDetail not found or inactive', {
        brand_id: id,
        code: resp.code,
        durationMs: Date.now() - startedAt
      })
      markUnavailable()
    } else {
      logger.warn('api', 'BrandDetail getBrandContent non-200 or empty data', {
        brand_id: id,
        code: resp.code,
        message: resp.message,
        hasData: !!resp.data,
        durationMs: Date.now() - startedAt
      })
      error.value = new Error('加载失败，请稍后再试')
      brand.value = null
    }
  } catch (e: any) {
    const code = Number(e?.code ?? e?.data?.code ?? 0)
    logger.error('api', 'BrandDetail getBrandContent failed', {
      brand_id: id,
      message: e?.message,
      statusCode: e?.statusCode,
      code,
      durationMs: Date.now() - startedAt
    })
    if (code === 2001 || Number(e?.statusCode) === 404) {
      markUnavailable()
    } else {
      error.value = new Error('加载失败，请稍后再试')
      brand.value = null
    }
  } finally {
    loading.value = false
  }
})

function openRoom(roomId: string) {
  const rid = String(roomId || '')
  if (!rid) return
  uni.navigateTo({ url: `/pages/live/LiveView?roomId=${encodeURIComponent(rid)}` })
}

function copyWebsite() {
  const text = String(brand.value?.website_url || '').trim()
  if (!text) return
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title: '已复制官网链接', icon: 'success' })
  })
}

function openWebsite() {
  const url = String(brand.value?.website_url || '').trim()
  if (!url) return
  // #ifdef H5
  try {
    window.open(url, '_blank')
    return
  } catch {
    // fall through
  }
  // #endif
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: '链接已复制，请在浏览器打开', icon: 'none' })
  })
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-detail {
  min-height: 100vh;
  background: var(--color-background);
  padding-bottom: var(--spacing-md);
}

.info-card {
  margin: 0;
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.website-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.website-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.website-url {
  font-size: 13px;
  color: var(--color-text-primary);
  word-break: break-all;
  line-height: 1.5;
}

.website-actions {
  display: flex;
  gap: 10px;
}

.website-btn {
  height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary, var(--color-background));
}

.website-btn--primary {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: transparent;
}

.section {
  margin: 0;
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.room-list {
  margin-top: var(--spacing-sm);
}

.room-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.room-item:last-child {
  border-bottom: none;
}

.cover {
  width: 120rpx;
  height: 90rpx;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
}

.right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 13px;
  color: var(--color-text-primary);
}

.meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  display: block;
}
</style>
