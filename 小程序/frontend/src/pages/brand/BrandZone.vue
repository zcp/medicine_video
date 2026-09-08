<template>
  <view class="brand-zone theme-soft">
    <view class="page-shell panel main-panel">
      <view class="hero">
        <view class="hero-actions">
          <BrandHeader class="search-box" :keyword="keyword" @search="onSearch" @focus="onSearchFocus" @blur="onSearchBlur" />
        </view>

        <view v-if="showSearchAssist" class="search-assist">
          <view v-if="featuredSearchRecommendations.length > 0" class="assist-strip">
            <view
              v-for="item in featuredSearchRecommendations"
              :key="`featured_${item}`"
              class="assist-chip assist-chip--recommend assist-chip--featured"
              role="button"
              @tap="applySearchTerm(item)"
            >
              <text class="assist-chip__text">{{ item }}</text>
            </view>
          </view>

          <view v-if="history.length > 0" class="assist-group">
            <view class="assist-group__header">
              <text class="assist-group__title">搜索历史</text>
              <text class="assist-group__action" role="button" @tap="clearSearchHistory">清空</text>
            </view>
            <view class="assist-group__chips">
              <view v-for="item in history" :key="`history_${item}`" class="assist-chip" role="button" @tap="applySearchTerm(item)">
                <text class="assist-chip__text">{{ item }}</text>
              </view>
            </view>
          </view>

          <view v-if="history.length > 0 && hotSearches.length > 0" class="assist-divider" />

          <view v-if="hotSearches.length > 0" class="assist-group">
            <view class="assist-group__header">
              <text class="assist-group__title">热门搜索</text>
            </view>
            <view class="assist-group__chips">
              <view v-for="item in hotSearches" :key="`hot_${item}`" class="assist-chip assist-chip--hot" role="button" @tap="applySearchTerm(item)">
                <text class="assist-chip__text">{{ item }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="list-shell">
        <view v-if="!loading && brands.length === 0" class="empty-state">
          <text class="empty-state__title">{{ emptyStateTitle }}</text>
          <text class="empty-state__desc">{{ emptyStateDesc }}</text>
        </view>
        <scroll-view v-else scroll-y class="scroll" @scrolltolower="onReachBottom">
          <BrandGrid :brands="brands" :loading="loading" :hasMore="hasMore" @select="openDetail" />
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BrandHeader from '@/components/brand/BrandHeader.vue'
import BrandGrid from '@/components/brand/BrandGrid.vue'
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { getBrandList } from '@/api/brands'
import { logger } from '@/logs/logger'
import { setCustomTabBarSelected } from '@/utils/tabbar'
import type { BrandItem } from '@/types/brands'

const keyword = ref('')
const allBrands = ref<BrandItem[]>([])
const pageSize = ref(12)
const visibleCount = ref(pageSize.value)
const loading = ref(false)
const loadError = ref('')
const SEARCH_HISTORY_KEY = 'brand_search_history_v1'
const MAX_HISTORY_COUNT = 12
const history = ref<string[]>([])
const searchAssistVisible = ref(false)
const hasMore = computed(() => visibleCount.value < filtered.value.length)
const showSearchAssist = computed(() => searchAssistVisible.value || !!normalizeSearchTerm(keyword.value))

const emptyStateTitle = computed(() => {
  if (loadError.value) return '品牌加载失败'
  if (String(keyword.value || '').trim()) return '未找到匹配品牌'
  return '当前没有可展示的品牌'
})

const emptyStateDesc = computed(() => {
  if (loadError.value) return loadError.value
  if (String(keyword.value || '').trim()) return '请检查搜索关键词，或下拉刷新重试。'
  return '公开品牌接口返回为空，通常表示后端当前没有可用品牌数据。'
})

onShow(() => {
  setCustomTabBarSelected(1)
})

/** 品牌页不做分类：直接展示全部启用品牌；搜索时按关键词过滤 */
const filtered = computed(() => {
  const activeOnly = (allBrands.value || []).filter((b) => b.is_active !== false)
  const q = normalizeSearchTerm(keyword.value).toLowerCase()
  if (!q) return activeOnly
  return activeOnly.filter((b) => String(b?.name || '').toLowerCase().includes(q))
})

const brands = computed(() => filtered.value.slice(0, visibleCount.value))

const hotSearches = computed(() => {
  return collectBrandNames(allBrands.value, true).slice(0, 8)
})

const searchRecommendations = computed(() => {
  const current = normalizeSearchTerm(keyword.value).toLowerCase()
  const historySet = new Set(history.value.map((item) => normalizeSearchTerm(item).toLowerCase()))
  const names = collectBrandNames(allBrands.value, false)

  if (current) {
    return names
      .filter((item) => item.toLowerCase().includes(current) && item.toLowerCase() !== current)
      .slice(0, 8)
  }

  return names.filter((item) => !historySet.has(item.toLowerCase())).slice(0, 8)
})

const featuredSearchRecommendations = computed(() => searchRecommendations.value.slice(0, 3))

function normalizeSearchTerm(value: string) {
  return String(value || '').trim()
}

function collectBrandNames(source: BrandItem[], sortByOrder: boolean) {
  const sorted = [...(source || [])].filter((item) => !!item?.name)

  if (sortByOrder) {
    sorted.sort((a, b) => {
      const orderA = typeof a?.sort_order === 'number' ? a.sort_order : Number(a?.sort_order ?? 0)
      const orderB = typeof b?.sort_order === 'number' ? b.sort_order : Number(b?.sort_order ?? 0)
      if (orderA !== orderB) return orderA - orderB
      return String(a?.name || '').localeCompare(String(b?.name || ''), 'zh')
    })
  }

  const seen = new Set<string>()
  const names: string[] = []
  sorted.forEach((item) => {
    const name = normalizeSearchTerm(String(item?.name || ''))
    if (!name || seen.has(name)) return
    seen.add(name)
    names.push(name)
  })

  return names
}

function restoreSearchHistory() {
  try {
    const raw = uni.getStorageSync(SEARCH_HISTORY_KEY)
    if (!raw) {
      history.value = []
      return
    }

    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    if (!Array.isArray(parsed)) {
      history.value = []
      return
    }

    history.value = parsed
      .map((item) => normalizeSearchTerm(String(item || '')))
      .filter(Boolean)
      .slice(0, MAX_HISTORY_COUNT)
  } catch {
    history.value = []
  }
}

function persistSearchHistory() {
  try {
    uni.setStorageSync(SEARCH_HISTORY_KEY, JSON.stringify(history.value.slice(0, MAX_HISTORY_COUNT)))
  } catch {
    // ignore storage write failures
  }
}

function saveSearchHistory(term: string) {
  const value = normalizeSearchTerm(term)
  if (!value) return

  const next = [value, ...history.value.filter((item) => item !== value)].slice(0, MAX_HISTORY_COUNT)
  history.value = next
  persistSearchHistory()
}

function clearSearchHistory() {
  history.value = []
  persistSearchHistory()
}

function normalizeBrandItem(raw: any): BrandItem {
  const id = raw?.id ?? raw?.brand_id ?? raw?.brandId ?? ''
  const name = raw?.name ?? raw?.brand_name ?? raw?.brandName ?? raw?.title ?? ''
  const logoUrl = raw?.logo_url ?? raw?.logoUrl ?? raw?.logo ?? null
  const websiteUrl = raw?.website_url ?? raw?.websiteUrl ?? null
  const createdAt = raw?.created_at ?? raw?.createdAt ?? ''
  const updatedAt = raw?.updated_at ?? raw?.updatedAt ?? ''
  // 未回传 is_active 时默认启用（信任服务端已过滤）；显式 false 才丢弃
  const rawActive = raw?.is_active ?? raw?.isActive ?? raw?.active
  const is_active = rawActive === undefined || rawActive === null ? true : Boolean(rawActive)
  return {
    id: String(id),
    name: String(name),
    slug: raw?.slug ?? null,
    logo_url: logoUrl,
    description: raw?.description ?? null,
    website_url: websiteUrl,
    sort_order: typeof raw?.sort_order === 'number'
      ? raw.sort_order
      : (typeof raw?.sortOrder === 'number' ? raw.sortOrder : Number(raw?.sort_order ?? raw?.sortOrder ?? 0)),
    is_active,
    created_at: String(createdAt),
    updated_at: String(updatedAt)
  }
}

onLoad(async () => {
  restoreSearchHistory()
  visibleCount.value = pageSize.value
  await loadBrands()
})

onPullDownRefresh(async () => {
  visibleCount.value = pageSize.value
  await loadBrands()
  uni.stopPullDownRefresh()
})

function onSearch(kw: string) {
  const nextKeyword = normalizeSearchTerm(kw)
  keyword.value = nextKeyword
  searchAssistVisible.value = true
  visibleCount.value = pageSize.value
  if (nextKeyword) {
    saveSearchHistory(nextKeyword)
  }
  void loadBrands()
}

function onSearchFocus() {
  searchAssistVisible.value = true
}

function onSearchBlur() {
  window.setTimeout(() => {
    searchAssistVisible.value = !!normalizeSearchTerm(keyword.value)
  }, 120)
}

function applySearchTerm(term: string) {
  onSearch(term)
}

function onReachBottom(){
  if (loading.value) return
  if (!hasMore.value) return
  visibleCount.value = Math.min(visibleCount.value + pageSize.value, filtered.value.length)
}

function openDetail(id: string){
  uni.navigateTo({ url: `/pages/brand/BrandDetail?id=${id}` })
}

async function loadBrands(){
  const startedAt = Date.now()
  loadError.value = ''
  logger.debug('api', 'BrandZone loadBrands start', {
    q: keyword.value || undefined,
    limit: 500
  })
  try {
    loading.value = true
    const resp = await getBrandList({ q: keyword.value || undefined, limit: 500 })
    if (resp.code === 200 && resp.data) {
      const raw = resp.data as any
      const list = Array.isArray(raw)
        ? raw
        : (Array.isArray(raw?.items) ? raw.items : (Array.isArray(raw?.list) ? raw.list : (Array.isArray(raw?.data) ? raw.data : [])))

      const sampleRaw = list[0]
      logger.debug('api', 'BrandZone loadBrands response shape', {
        rawType: Array.isArray(raw) ? 'array' : typeof raw,
        listCount: Array.isArray(list) ? list.length : -1,
        sampleKeys: sampleRaw && typeof sampleRaw === 'object' ? Object.keys(sampleRaw).slice(0, 12) : [],
        durationMs: Date.now() - startedAt
      })

      const normalizedAll = list.map(normalizeBrandItem)
      const dropped = normalizedAll.filter((item: BrandItem) => !item.id || !item.name)
      // 16-D5：公开专区仅保留启用品牌
      const normalized = normalizedAll.filter(
        (item: BrandItem) => !!item.id && !!item.name && item.is_active !== false
      )

      allBrands.value = normalized
      logger.info('api', 'BrandZone loadBrands success', {
        count: normalized.length,
        rawCount: Array.isArray(list) ? list.length : 0,
        droppedCount: dropped.length,
        durationMs: Date.now() - startedAt
      })

      if (dropped.length > 0) {
        logger.warn('api', 'BrandZone loadBrands dropped invalid items', {
          droppedCount: dropped.length,
          droppedSample: dropped.slice(0, 3).map((item: BrandItem) => ({ id: item.id, name: item.name })),
          rawSample: list.slice(0, 3).map((item: any) => ({
            id: item?.id,
            brand_id: item?.brand_id,
            brandId: item?.brandId,
            name: item?.name,
            brand_name: item?.brand_name,
            brandName: item?.brandName
          })),
          durationMs: Date.now() - startedAt
        })
      }

      if (normalized.length === 0) {
        logger.warn('api', 'BrandZone loadBrands empty result', {
          q: keyword.value || undefined,
          limit: 500,
          durationMs: Date.now() - startedAt
        })
      }
    } else {
      allBrands.value = []
      loadError.value = `接口返回异常：${resp.message || '无有效数据'}`
      logger.warn('api', 'BrandZone loadBrands non-200 or non-array data', {
        code: resp.code,
        message: resp.message,
        hasData: !!resp.data,
        durationMs: Date.now() - startedAt
      })
    }
  } catch (e: any) {
    loadError.value = e?.message || `品牌接口请求失败${e?.statusCode ? `（HTTP ${e.statusCode}）` : ''}`
    logger.error('api', 'BrandZone loadBrands failed', {
      message: e?.message,
      statusCode: e?.statusCode,
      durationMs: Date.now() - startedAt
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-zone {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
  display: flex;
  flex-direction: column;
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
}

.panel {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.main-panel {
  padding: 0;
}

.hero {
  background: var(--color-surface);
  padding: var(--spacing-base) var(--spacing-lg) var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.tab-bar {
  width: 100%;
}

.tab-bar-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  white-space: nowrap;
}

.search-assist {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0 4px;
  border: none;
  border-radius: 0;
  background: transparent;
}

.assist-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assist-divider {
  height: 1px;
  width: 100%;
  background: var(--color-border);
}

.assist-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assist-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.assist-group__title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.assist-group__action {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.assist-group__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assist-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-height: 28px;
  padding: 0 12px;
  border-radius: var(--border-radius-base);
  background: var(--color-bg-secondary, var(--color-background));
  border: 1px solid var(--color-border);
}

.assist-chip--hot,
.assist-chip--recommend,
.assist-chip--featured {
  background: var(--color-bg-secondary, var(--color-background));
  border-color: var(--color-border);
}

.assist-chip__text {
  font-size: 12px;
  line-height: 1;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-shell {
  padding: 0;
  background: var(--color-background);
  border-bottom: none;
  flex: 1;
  overflow: hidden;
}

.scroll {
  height: 100%;
  padding-bottom: calc(100rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
}

.empty-state {
  text-align: center;
  padding: 56px 24px;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.empty-state__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-state__desc {
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  max-width: 520px;
}

.brand-zone :deep(.brand-tabs) {
  background: var(--color-surface);
}

@media (max-width: 767px) {
  .brand-zone { padding: 0; }
  .hero { padding: var(--spacing-base) var(--spacing-lg) var(--spacing-sm); }
  .hero-actions { flex-direction: column; gap: 10px; }
  .tab-bar, .search-box { width: 100%; }
  .scroll { max-height: none; }
}
</style>

