<template>
  <view class="search-page">
    <view class="top-bar">
      <view class="top-bar__back" role="button" aria-label="返回" @tap="goBack">
        <uni-icons type="left" size="20" :color="'var(--color-text-primary)'" />
      </view>

      <!-- 样式对齐首页 TopBar 搜索条：同高、同圆角、同占位文案 -->
      <view class="search-pill">
        <text class="search-pill__icon iconfont icon-sousuo"></text>
        <input
          v-model="keyword"
          class="search-pill__input"
          placeholder="搜索直播、专家、科室"
          placeholder-class="search-pill__placeholder"
          confirm-type="search"
          :focus="inputFocused"
          @confirm="onSubmit"
        />
        <view
          v-if="keywordNormalized"
          class="search-pill__clear"
          role="button"
          aria-label="清空"
          @tap="clearKeyword"
        >
          <uni-icons type="closeempty" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
      </view>

      <!-- 与返回同宽占位，左右对称，搜索条视觉居中（对齐首页头像/消息） -->
      <view class="top-bar__side-spacer" aria-hidden="true" />
    </view>

    <view v-if="showAssistPanel" class="assist-panel">
      <view v-if="keywordNormalized" class="assist-group">
        <view class="assist-group__header">
          <text class="assist-group__title">搜索建议</text>
          <text v-if="suggestionsLoading" class="assist-group__meta">加载中...</text>
        </view>

        <view v-if="suggestions.length > 0" class="assist-chips">
          <view
            v-for="item in suggestions"
            :key="item"
            class="assist-chip assist-chip--suggestion"
            role="button"
            @tap="applyKeyword(item)"
          >
            <text class="assist-chip__text">{{ item }}</text>
          </view>
        </view>

        <EmptyState
          v-else-if="!suggestionsLoading"
          title="暂无搜索建议"
          description="换个更具体的关键词试试"
        />
      </view>

      <view v-else class="assist-stack">
        <view class="assist-group">
          <view class="assist-group__header">
            <text class="assist-group__title">搜索历史</text>
            <text
              v-if="historyItems.length > 0"
              class="assist-group__action"
              role="button"
              @tap="clearHistory"
            >
              清空
            </text>
          </view>

          <view v-if="historyItems.length > 0" class="history-list">
            <view v-for="item in historyItems" :key="item.id" class="history-row">
              <view class="history-row__content" role="button" @tap="applyKeyword(item.keyword)">
                <text class="history-row__keyword">{{ item.keyword }}</text>
                <text class="history-row__meta">
                  {{ item.search_count > 1 ? `搜索 ${item.search_count} 次` : '最近搜索' }}
                  <text v-if="formatHistoryTime(item.last_searched_at)" class="history-row__dot">·</text>
                  <text v-if="formatHistoryTime(item.last_searched_at)">
                    {{ formatHistoryTime(item.last_searched_at) }}
                  </text>
                </text>
              </view>
              <view class="history-row__delete" role="button" aria-label="删除历史" @tap="deleteHistory(item)">
                <uni-icons type="trash" size="16" :color="'var(--color-text-tertiary)'" />
              </view>
            </view>
          </view>

          <EmptyState
            v-else
            :title="historyLoading ? '加载历史中...' : '暂无搜索历史'"
            :description="isLoggedIn ? '搜索后会自动记录到云端历史' : '登录后可同步云端搜索历史'"
          />
        </view>

        <view class="assist-group">
          <view class="assist-group__header">
            <text class="assist-group__title">热门搜索</text>
            <text v-if="hotLoading" class="assist-group__meta">加载中...</text>
          </view>

          <view v-if="hotKeywords.length > 0" class="assist-chips">
            <view
              v-for="item in hotKeywords"
              :key="item.keyword"
              class="assist-chip assist-chip--hot"
              role="button"
              @tap="applyKeyword(item.keyword)"
            >
              <text class="assist-chip__text">{{ item.keyword }}</text>
              <text class="assist-chip__count">{{ item.search_count }}</text>
            </view>
          </view>

          <EmptyState
            v-else
            :title="hotLoading ? '加载热门搜索中...' : '暂无热门搜索'"
            description="系统会根据最近搜索自动更新"
          />
        </view>
      </view>

    </view>

    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading && (!loaded || showResults)" fullscreen text="搜索中..." />

    <view v-if="showResults" class="content">
      <scroll-view class="result-tabs" scroll-x role="tablist" aria-label="搜索结果分类">
        <view class="tabs-row">
          <view
            v-for="(t, i) in tabs"
            :key="t.type"
            class="tab"
            :class="{ active: i === activeTabIndex }"
            role="tab"
            :aria-selected="i === activeTabIndex"
            @tap="onChangeTab(i)"
          >
            <text class="label">{{ t.label }}</text>
          </view>
        </view>
      </scroll-view>

      <EmptyState v-if="totalAll === 0" title="暂无结果" description="换个关键词试试" />

      <EmptyState
        v-else-if="activeItems.length === 0"
        :title="`暂无${activeTabName}结果`"
        description="换个关键词试试"
      />

      <view v-else class="list">
        <view
          v-for="it in activeItems"
          :key="`${it.type}_${it.id}`"
          class="row"
          :class="{
            'row--room': it.type === 'room',
            'row--expert': it.type === 'expert',
            'row--brand': it.type === 'brand'
          }"
          role="button"
          @tap="openItem(it)"
        >
          <!-- 直播间：与首页 LiveCard 同字段，横排 -->
          <template v-if="it.type === 'room'">
            <view class="room-cover">
              <image class="cover" :src="itemCoverSrc(it)" mode="aspectFill" @error="onItemCoverError(it)" />
              <view v-if="it.categoryName" class="room-cover__badge">
                <text class="room-cover__badge-text">{{ it.categoryName }}</text>
              </view>
            </view>
            <view class="meta">
              <text class="title title--2line">{{ it.title || '未命名' }}</text>
              <view class="host-row">
                <image
                  class="host-avatar"
                  :src="roomHostAvatarSrc(it)"
                  mode="aspectFill"
                  @error="onRoomHostAvatarError(it)"
                />
                <view class="host-meta">
                  <text class="host-name">{{ it.hostName || '主讲专家' }}</text>
                  <text v-if="it.hostHospital" class="host-hospital">{{ it.hostHospital }}</text>
                </view>
              </view>
            </view>
          </template>

          <!-- 专家：与专家列表 ExpertCard 同字段，横排（无关注按钮） -->
          <template v-else-if="it.type === 'expert'">
            <image
              class="expert-avatar"
              :src="itemCoverSrc(it)"
              mode="aspectFill"
              @error="onItemCoverError(it)"
            />
            <view class="meta">
              <view class="expert-name-row">
                <text class="expert-name">{{ it.title || '未命名' }}</text>
                <text v-if="it.expertJobTitle" class="expert-job">{{ it.expertJobTitle }}</text>
              </view>
              <text v-if="it.expertDepartment" class="expert-dept">{{ it.expertDepartment }}</text>
              <text v-if="it.expertSpecialty" class="expert-specialty">擅长：{{ it.expertSpecialty }}</text>
            </view>
          </template>

          <!-- 品牌：与品牌页 BrandCard 同字段，横排 -->
          <template v-else-if="it.type === 'brand'">
            <view class="brand-logo-wrap">
              <image
                class="brand-logo"
                :src="itemCoverSrc(it)"
                mode="aspectFit"
                @error="onItemCoverError(it)"
              />
            </view>
            <view class="meta">
              <text class="brand-name">{{ it.title || '未命名' }}</text>
              <text v-if="it.brandDescription" class="brand-desc">{{ it.brandDescription }}</text>
            </view>
          </template>
        </view>

        <view v-if="activeLoadingMore" class="more">加载更多...</view>
        <view v-else-if="loaded && !activeHasMore" class="more">没有更多了</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store'
import {
  clearSearchHistory as clearRemoteSearchHistory,
  deleteSearchHistoryItem as deleteRemoteSearchHistoryItem,
  getHotKeywords,
  getSearchHistory,
  getSearchSuggestions,
  globalSearch,
  type HotKeywordItem,
  type SearchHistoryItem
} from '@/api/search'
import { getHomepageRooms, getRoomById } from '@/api/room'
import { getExpertDetail, searchExperts } from '@/api/expert'
import { getBrandList } from '@/api/brands'
import { STORAGE_KEYS } from '@/common/constants'
import {
  normalizeImageUrl,
  resolveAvatarUrl,
  resolveBrandLogoUrl,
  resolveCoverUrl,
  shouldMarkAvatarBroken,
  shouldMarkBrandLogoBroken,
  shouldMarkCoverBroken
} from '@/utils/url'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

type SearchResultType = 'room' | 'expert' | 'brand'

type ResultChipTone = 'status-live' | 'status-scheduled' | 'status-replay' | 'category' | 'neutral'

type ResultChip = {
  label: string
  tone?: ResultChipTone
}

type SearchItem = {
  type: SearchResultType
  id: string
  title: string
  coverUrl: string | null
  snippet: string | null
  chips: ResultChip[]
  /** 直播间：与首页 LiveCard 一致 */
  hostName?: string | null
  hostAvatarUrl?: string | null
  hostHospital?: string | null
  /** 封面右上角科室角标（category.name） */
  categoryName?: string | null
  /** 专家：与 ExpertCard 一致 */
  expertJobTitle?: string | null
  expertDepartment?: string | null
  expertSpecialty?: string | null
  /** 品牌：与 BrandCard 一致 */
  brandDescription?: string | null
}

type DisplayHistoryItem = SearchHistoryItem & {
  local?: boolean
}

const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isAuthenticated)

const SEARCH_HISTORY_KEY = STORAGE_KEYS.SEARCH_HISTORY
const localHistory = ref<string[]>([])
const historyItems = ref<DisplayHistoryItem[]>([])
const hotKeywords = ref<HotKeywordItem[]>([])
const suggestions = ref<string[]>([])

const keyword = ref('')
const searchedKeyword = ref('')
/** 进入页后自动聚焦，贴近首页点搜索进入的体验 */
const inputFocused = ref(false)

const loading = ref(false)
const loaded = ref(false)
const error = ref<string | null>(null)
const hotLoading = ref(false)
const historyLoading = ref(false)
const suggestionsLoading = ref(false)
const size = 20
const brokenImageKeys = ref<Record<string, true>>({})

type TabType = SearchResultType
const TAB_TYPES: TabType[] = ['room', 'expert', 'brand']

type TabState = {
  items: SearchItem[]
  page: number
  total: number
  loadingMore: boolean
}

const tabState = reactive<Record<TabType, TabState>>({
  room: { items: [], page: 1, total: 0, loadingMore: false },
  expert: { items: [], page: 1, total: 0, loadingMore: false },
  brand: { items: [], page: 1, total: 0, loadingMore: false }
})

const activeTabIndex = ref(0)
const activeType = computed<TabType>(() => TAB_TYPES[activeTabIndex.value] ?? 'room')
const activeItems = computed(() => tabState[activeType.value].items)
const activeLoadingMore = computed(() => tabState[activeType.value].loadingMore)
const activeHasMore = computed(() => {
  const st = tabState[activeType.value]
  return st.page * size < st.total
})

const totalAll = computed(() => TAB_TYPES.reduce((sum, t) => sum + Number(tabState[t].total || 0), 0))

const tabs = computed(() =>
  TAB_TYPES.map((t) => ({
    type: t,
    label: `${typeLabel(t)}(${Number(tabState[t].total || 0)})`
  }))
)

const activeTabName = computed(() => typeLabel(activeType.value))
const keywordNormalized = computed(() => normalizeKeyword(keyword.value))
const showResults = computed(
  () => loaded.value && !!searchedKeyword.value && keywordNormalized.value === searchedKeyword.value
)
const showAssistPanel = computed(() => !showResults.value)

let suggestionTimer: ReturnType<typeof setTimeout> | null = null

type HomepageRoomBrief = {
  id: string
  live_status?: string
  summary?: string | null
  host?: Record<string, unknown> | null
  status_data?: Record<string, unknown> | null
  category?: { name?: string } | null
  heat?: number | null
}

let homepageRoomCache: Map<string, HomepageRoomBrief> | null = null
let homepageRoomCacheAt = 0
const HOMEPAGE_ROOM_CACHE_TTL_MS = 5 * 60 * 1000
/** 与首页一致：按专家 ID 补全主播头像 */
const expertAvatarCache = new Map<string, string>()

function normalizeKeyword(v: string) {
  return String(v || '').trim().replace(/\s+/g, ' ')
}

function formatHistoryTime(value: string) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

function stripHtmlTags(input: string) {
  return String(input || '').replace(/<[^>]+>/g, '')
}

function decodeHtmlEntities(input: string) {
  return String(input || '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
}

function toSnippet(highlight?: string | null, summary?: string | null) {
  const raw = highlight || summary || ''
  const s = decodeHtmlEntities(stripHtmlTags(raw)).trim()
  return s ? s : null
}

function typeLabel(t: SearchResultType) {
  switch (t) {
    case 'room':
      return '直播间'
    case 'expert':
      return '专家'
    case 'brand':
      return '品牌'
    default:
      return '内容'
  }
}

function pickString(...values: unknown[]): string | null {
  for (const value of values) {
    if (value == null) continue
    const text = String(value).trim()
    if (text) return text
  }
  return null
}

async function getHomepageRoomLookup() {
  const now = Date.now()
  if (homepageRoomCache && now - homepageRoomCacheAt < HOMEPAGE_ROOM_CACHE_TTL_MS) {
    return homepageRoomCache
  }

  const lookup = new Map<string, HomepageRoomBrief>()
  try {
    for (let pageNo = 1; pageNo <= 3; pageNo += 1) {
      const resp = await getHomepageRooms({ page: pageNo, size: 50 })
      const items = Array.isArray(resp?.data?.items) ? resp.data.items : []
      if (!items.length) break

      items.forEach((item: any) => {
        const id = String(item?.id || '')
        if (!id) return
        lookup.set(id, {
          id,
          live_status: item?.live_status,
          summary: item?.summary ?? null,
          host: item?.host ?? null,
          status_data: item?.status_data ?? null,
          category: item?.category ?? null,
          heat: item?.heat ?? null
        })
      })

      if (items.length < 50) break
    }
  } catch {
    // 补全失败不影响搜索结果展示
  }

  homepageRoomCache = lookup
  homepageRoomCacheAt = now
  return lookup
}

/** 合并 host：搜索常返回空壳 host，不能用 ?? 挡住 homepage 里带头像的完整 host */
function mergeRoomHost(primary: any, fallback: any) {
  const a = primary && typeof primary === 'object' ? primary : null
  const b = fallback && typeof fallback === 'object' ? fallback : null
  if (!a && !b) return null
  if (!a) return b
  if (!b) return a

  const avatar = pickString(
    a.avatar_url,
    a.avatarUrl,
    a.avatar,
    a.avatarURL,
    b.avatar_url,
    b.avatarUrl,
    b.avatar,
    b.avatarURL
  )
  const expertId = a.expert_id ?? a.expertId ?? b.expert_id ?? b.expertId ?? null

  return {
    ...b,
    ...a,
    name: pickString(a.name, b.name),
    hospital: pickString(a.hospital, b.hospital),
    title: pickString(a.title, b.title),
    expert_id: expertId,
    expertId,
    avatar_url: avatar,
    avatarUrl: avatar,
    avatar
  }
}

function mergeRoomCategory(primary: any, fallback: any) {
  const a = primary && typeof primary === 'object' ? primary : null
  const b = fallback && typeof fallback === 'object' ? fallback : null
  if (!a && !b) return null
  const name = pickString(a?.name, b?.name)
  if (!name && !a && !b) return null
  return {
    ...(b || {}),
    ...(a || {}),
    name: name || (a as any)?.name || (b as any)?.name || null,
    id: a?.id ?? b?.id ?? null
  }
}

async function enrichRoomSearchItems(items: any[]) {
  if (!Array.isArray(items) || items.length === 0) return items

  const lookup = await getHomepageRoomLookup()
  return items.map((item) => {
    const extra = lookup.get(String(item?.id || ''))
    if (!extra) return item

    return {
      ...item,
      summary: item?.summary ?? extra.summary ?? null,
      live_status: item?.live_status ?? extra.live_status ?? item?.metadata?.live_status,
      host: mergeRoomHost(item?.host, extra.host),
      status_data: item?.status_data ?? extra.status_data ?? null,
      category: mergeRoomCategory(item?.category, extra.category),
      heat: item?.heat ?? extra.heat ?? null,
      metadata: {
        ...(item?.metadata && typeof item.metadata === 'object' ? item.metadata : {}),
        live_status:
          item?.metadata?.live_status ??
          extra.live_status ??
          item?.live_status ??
          null,
        viewer_count:
          item?.metadata?.viewer_count ??
          extra.status_data?.viewer_count ??
          null
      }
    }
  })
}

function pickHostAvatar(host: any): string | null {
  if (!host || typeof host !== 'object') return null
  return pickString(host.avatar_url, host.avatarUrl, host.avatar, host.avatarURL)
}

function pickExpertId(item: any): string {
  const host = item?.host && typeof item.host === 'object' ? item.host : null
  return String(
    host?.expert_id ?? host?.expertId ?? item?.featured_expert_id ?? item?.featuredExpertId ?? ''
  ).trim()
}

/** 与首页一致：有 expert_id 但无头像时，拉专家详情补全 */
async function hydrateRoomHostAvatars(items: any[]) {
  if (!Array.isArray(items) || items.length === 0) return items

  const toHydrate = items
    .filter((item) => !!pickExpertId(item) && !pickHostAvatar(item?.host))
    .slice(0, 8)

  await Promise.all(
    toHydrate.map(async (item) => {
      const host = item?.host && typeof item.host === 'object' ? item.host : {}
      const expertId = pickExpertId(item)
      if (!expertId) return

      const cached = expertAvatarCache.get(expertId)
      if (cached) {
        item.host = mergeRoomHost(
          { ...host, expert_id: expertId, avatar_url: cached, avatarUrl: cached },
          host
        )
        return
      }

      try {
        // 《16》P44：已下架专家详情 404，补头像静默失败即可
        const resp = await getExpertDetail(expertId, { showError: false, quiet: true })
        const payload = (resp as any)?.data ?? resp
        const url = normalizeImageUrl(payload?.avatar_url || payload?.avatarUrl || payload?.avatar)
        if (!url) return
        expertAvatarCache.set(expertId, url)
        item.host = mergeRoomHost(
          { ...host, expert_id: expertId, avatar_url: url, avatarUrl: url },
          host
        )
      } catch {
        // 补全失败不阻断列表
      }
    })
  )

  return items
}

/**
 * 仍无头像时：按房间详情拉库内 host（搜索/首页缓存都没有的情况）
 * 最小友好：最多补 5 条，避免列表打爆详情接口
 */
/** 专家列表缺头像时按详情补全（与直播间补数同思路） */
async function hydrateExpertAvatars(items: any[]) {
  if (!Array.isArray(items) || items.length === 0) return items

  const need = items
    .filter((item) => {
      const id = String(item?.id || '').trim()
      const avatar = pickString(item?.avatar_url, item?.avatarUrl, item?.avatar, item?.cover_url)
      return !!id && !avatar
    })
    .slice(0, 8)

  await Promise.all(
    need.map(async (item) => {
      const expertId = String(item?.id || '').trim()
      if (!expertId) return

      const cached = expertAvatarCache.get(expertId)
      if (cached) {
        item.avatar_url = cached
        item.avatarUrl = cached
        return
      }

      try {
        const resp = await getExpertDetail(expertId, { showError: false, quiet: true })
        const payload = (resp as any)?.data ?? resp
        const url = normalizeImageUrl(payload?.avatar_url || payload?.avatarUrl || payload?.avatar)
        if (!url) return
        expertAvatarCache.set(expertId, url)
        item.avatar_url = url
        item.avatarUrl = url
        // 顺带补职称/医院等列表字段（仅空时写入）
        if (!pickString(item?.title) && pickString(payload?.title)) item.title = payload.title
        if (!pickString(item?.hospital) && pickString(payload?.hospital)) item.hospital = payload.hospital
        if (!pickString(item?.department) && pickString(payload?.department)) item.department = payload.department
        if (!item?.expertise_areas && payload?.expertise_areas) item.expertise_areas = payload.expertise_areas
      } catch {
        // ignore
      }
    })
  )

  return items
}

async function hydrateMissingHostsFromRoomDetail(items: any[]) {
  if (!Array.isArray(items) || items.length === 0) return items

  const need = items
    .filter((item) => {
      const id = String(item?.id || '').trim()
      return !!id && !pickHostAvatar(item?.host)
    })
    .slice(0, 5)

  await Promise.all(
    need.map(async (item) => {
      const roomId = String(item.id || '').trim()
      if (!roomId) return
      try {
        const resp = await getRoomById(roomId)
        const room: any = (resp as any)?.data ?? resp
        if (!room) return

        const detailHost =
          room.host ||
          room.hostDetail ||
          (room.featured_expert
            ? {
                name: room.featured_expert.name,
                avatar_url: room.featured_expert.avatar_url ?? room.featured_expert.avatar,
                hospital: room.featured_expert.hospital,
                expert_id: room.featured_expert.id ?? room.featured_expert_id
              }
            : null)

        item.host = mergeRoomHost(item.host, detailHost)
        item.category = mergeRoomCategory(item.category, room.category)
        if (!item.featured_expert_id && room.featured_expert_id) {
          item.featured_expert_id = room.featured_expert_id
        }
      } catch {
        // ignore
      }
    })
  )

  return items
}

function dedupeChips(chips: ResultChip[]) {
  const seen = new Set<string>()
  return chips.filter((chip) => {
    const key = chip.label.toLowerCase()
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

/** 直播间卡片不再用 chips 堆字段；结构化展示见 mapRoomFields */
function buildRoomChips(_x: any): ResultChip[] {
  return []
}

/** 与首页 LiveCard 同字段：host + category，仅真实接口数据 */
function mapRoomFields(x: any): Pick<SearchItem, 'hostName' | 'hostAvatarUrl' | 'hostHospital' | 'categoryName'> {
  const host = x?.host && typeof x.host === 'object' ? x.host : null

  return {
    hostName: pickString(host?.name, x?.expert_name, x?.host_name),
    hostAvatarUrl: pickString(
      host?.avatar_url,
      host?.avatarUrl,
      host?.avatar,
      host?.avatarURL,
      x?.host_avatar,
      x?.expert_avatar
    ),
    hostHospital: pickString(host?.hospital, x?.hospital),
    categoryName: pickString(
      x?.primary_category_name,
      x?.category?.name,
      x?.category_name,
      Array.isArray(x?.categories) ? x.categories[0]?.name : null
    )
  }
}

function buildExpertChips(x: any): ResultChip[] {
  const chips: ResultChip[] = []
  const metadata = x?.metadata && typeof x.metadata === 'object' ? x.metadata : {}
  const expertName = pickString(x?.name, x?.expert_name)

  const jobTitle = pickString(
    metadata?.title,
    x?.professional_title,
    x?.position,
    expertName ? x?.title : null
  )
  if (jobTitle && jobTitle !== expertName) chips.push({ label: jobTitle, tone: 'neutral' })

  const hospital = pickString(metadata?.hospital, x?.hospital, x?.institution, x?.organization)
  if (hospital) chips.push({ label: hospital, tone: 'neutral' })

  const department = pickString(x?.department_name, x?.department, x?.dept_name)
  if (department) chips.push({ label: department, tone: 'category' })

  const expertise = pickString(x?.expertise_areas)
  if (expertise) {
    chips.push({ label: expertise.length > 12 ? `${expertise.slice(0, 12)}…` : expertise, tone: 'neutral' })
  }

  return dedupeChips(chips).slice(0, 4)
}

function buildBrandChips(x: any): ResultChip[] {
  const description = pickString(x?.description)
  if (!description) return []
  return [{ label: description.length > 16 ? `${description.slice(0, 16)}…` : description, tone: 'neutral' }]
}

function buildResultChips(x: any, type: SearchResultType): ResultChip[] {
  switch (type) {
    case 'room':
      return buildRoomChips(x)
    case 'expert':
      return buildExpertChips(x)
    case 'brand':
      return buildBrandChips(x)
    default:
      return []
  }
}

function resetTabData() {
  TAB_TYPES.forEach((t) => {
    tabState[t].items = []
    tabState[t].page = 1
    tabState[t].total = 0
    tabState[t].loadingMore = false
  })
  brokenImageKeys.value = {}
}

function itemImageKey(it: SearchItem): string {
  return `${it.type}_${it.id}`
}

function roomHostAvatarKey(it: SearchItem): string {
  return `room_host_${it.id}`
}

function itemCoverSrc(it: SearchItem): string {
  const broken = !!brokenImageKeys.value[itemImageKey(it)]
  const raw = it.coverUrl
  if (it.type === 'expert') return resolveAvatarUrl(raw, broken)
  if (it.type === 'brand') return resolveBrandLogoUrl(raw, broken)
  return resolveCoverUrl(raw, broken)
}

function roomHostAvatarSrc(it: SearchItem): string {
  return resolveAvatarUrl(it.hostAvatarUrl, !!brokenImageKeys.value[roomHostAvatarKey(it)])
}

function onItemCoverError(it: SearchItem) {
  const key = itemImageKey(it)
  if (brokenImageKeys.value[key]) return
  const raw = it.coverUrl
  const broken = !!brokenImageKeys.value[key]
  const shouldMark =
    it.type === 'expert'
      ? shouldMarkAvatarBroken(raw, broken)
      : it.type === 'brand'
        ? shouldMarkBrandLogoBroken(raw, broken)
        : shouldMarkCoverBroken(raw, broken)
  if (!shouldMark) return
  brokenImageKeys.value = { ...brokenImageKeys.value, [key]: true }
}

function onRoomHostAvatarError(it: SearchItem) {
  const key = roomHostAvatarKey(it)
  if (brokenImageKeys.value[key]) return
  if (!shouldMarkAvatarBroken(it.hostAvatarUrl, false)) return
  brokenImageKeys.value = { ...brokenImageKeys.value, [key]: true }
}

function pickRawImage(x: any, type: SearchResultType): string | null {
  if (type === 'expert') {
    return pickString(
      x?.avatar_url,
      x?.avatarUrl,
      x?.avatar,
      x?.cover_url,
      x?.coverUrl,
      x?.image,
      x?.image_url
    )
  }
  if (type === 'brand') {
    return pickString(
      x?.logo_url,
      x?.logoUrl,
      x?.logo,
      x?.cover_url,
      x?.coverUrl,
      x?.image,
      x?.image_url
    )
  }
  return pickString(x?.cover, x?.cover_url, x?.coverUrl, x?.image, x?.image_url, x?.imageUrl)
}

function parseExpertiseAreas(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.map((s) => String(s || '').trim()).filter(Boolean)
  }
  if (typeof raw === 'string' && raw.trim()) {
    return raw
      .split(/[,，、]/)
      .map((s) => s.trim())
      .filter(Boolean)
  }
  return []
}

/** 与专家列表 ExpertCard 同字段映射（name / 职称 / 医院｜科室 / 擅长） */
function mapExpertFields(x: any): Pick<SearchItem, 'title' | 'coverUrl' | 'expertJobTitle' | 'expertDepartment' | 'expertSpecialty'> {
  const metadata = x?.metadata && typeof x.metadata === 'object' ? x.metadata : {}
  // 列表接口：name=人名，title=职称；全量搜索可能只有 title 展示名
  const nameOnly = pickString(x?.name, x?.expert_name) || pickString(x?.title) || '未命名'
  let job = pickString(x?.professional_title, metadata?.title)
  const rawTitle = pickString(x?.title)
  if (!job && rawTitle && rawTitle !== nameOnly && pickString(x?.name, x?.expert_name)) {
    job = rawTitle
  }

  const hospital = pickString(x?.hospital, metadata?.hospital, x?.institution)
  const department = pickString(x?.department_name, x?.department, metadata?.department)
  const deptLine = [hospital, department].filter(Boolean).join('｜') || null

  const specialties = parseExpertiseAreas(x?.expertise_areas ?? x?.specialization ?? metadata?.expertise_areas)
  const joined = specialties.join('、')
  const specialtyText = joined
    ? joined.length > 36
      ? `${joined.slice(0, 36)}…`
      : joined
    : null

  return {
    title: nameOnly,
    coverUrl: pickRawImage(x, 'expert'),
    expertJobTitle: job,
    expertDepartment: deptLine,
    expertSpecialty: specialtyText
  }
}

/** 与品牌页 BrandCard 同字段映射 */
function mapBrandFields(x: any): Pick<SearchItem, 'title' | 'coverUrl' | 'brandDescription'> {
  return {
    title: pickString(x?.name, x?.brand_name, x?.title) || '未命名',
    coverUrl: pickRawImage(x, 'brand'),
    brandDescription: pickString(x?.description, x?.summary)
  }
}

function mapToSearchItem(x: any, fallbackType: SearchResultType, _q?: string): SearchItem {
  const resolvedType = String(x?.type || fallbackType || '') as SearchResultType

  if (resolvedType === 'room') {
    const coverUrl = pickRawImage(x, 'room')
    const name = String(x?.name || x?.title || '')
    const room = mapRoomFields(x)
    return {
      type: 'room',
      id: String(x?.id || ''),
      title: name || '未命名',
      coverUrl,
      snippet: null,
      chips: [],
      hostName: room.hostName,
      hostAvatarUrl: room.hostAvatarUrl,
      hostHospital: room.hostHospital,
      categoryName: room.categoryName
    }
  }

  if (resolvedType === 'expert') {
    const expert = mapExpertFields(x)
    return {
      type: 'expert',
      id: String(x?.id || ''),
      title: expert.title || '未命名',
      coverUrl: expert.coverUrl,
      snippet: null,
      chips: [],
      expertJobTitle: expert.expertJobTitle,
      expertDepartment: expert.expertDepartment,
      expertSpecialty: expert.expertSpecialty
    }
  }

  if (resolvedType === 'brand') {
    const brand = mapBrandFields(x)
    return {
      type: 'brand',
      id: String(x?.id || ''),
      title: brand.title || '未命名',
      coverUrl: brand.coverUrl,
      snippet: null,
      chips: [],
      brandDescription: brand.brandDescription
    }
  }

  return {
    type: resolvedType,
    id: String(x?.id || ''),
    title: String(x?.name || x?.title || '未命名'),
    coverUrl: pickRawImage(x, resolvedType),
    snippet: null,
    chips: []
  }
}

function toLocalHistoryItems(items: string[]): DisplayHistoryItem[] {
  return items.map((item) => ({
    id: `local:${encodeURIComponent(item)}`,
    keyword: item,
    search_count: 1,
    last_searched_at: '',
    local: true
  }))
}

function restoreLocalHistory() {
  try {
    const raw = uni.getStorageSync(SEARCH_HISTORY_KEY)
    if (!raw) {
      localHistory.value = []
      return
    }

    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    if (Array.isArray(parsed)) {
      localHistory.value = parsed.map((x) => normalizeKeyword(String(x || ''))).filter(Boolean).slice(0, 12)
    } else {
      localHistory.value = []
    }
  } catch {
    localHistory.value = []
  }
}

function persistLocalHistory() {
  try {
    uni.setStorageSync(SEARCH_HISTORY_KEY, JSON.stringify(localHistory.value.slice(0, 12)))
  } catch {
    // ignore storage write failures
  }
}

function saveLocalHistory(q: string) {
  const v = normalizeKeyword(q)
  if (v.length < 2) return
  localHistory.value = [v, ...localHistory.value.filter((x) => x !== v)].slice(0, 12)
  persistLocalHistory()
}

function clearLocalHistory() {
  localHistory.value = []
  persistLocalHistory()
}

function removeLocalHistoryItem(keywordValue: string) {
  localHistory.value = localHistory.value.filter((x) => x !== keywordValue)
  persistLocalHistory()
}

function clearKeyword() {
  keyword.value = ''
  suggestions.value = []
}

function goBack() {
  try {
    uni.navigateBack({ delta: 1 })
  } catch {
    // ignore
  }
}

function scheduleSuggestionFetch() {
  if (suggestionTimer) clearTimeout(suggestionTimer)

  const q = keywordNormalized.value
  error.value = null

  if (!q) {
    suggestions.value = []
    suggestionsLoading.value = false
    return
  }

  suggestionsLoading.value = true
  suggestionTimer = setTimeout(() => {
    void loadSuggestions(q)
  }, 300)
}

async function loadSuggestions(q: string) {
  const keywordValue = normalizeKeyword(q)
  if (!keywordValue) {
    suggestions.value = []
    suggestionsLoading.value = false
    return
  }

  try {
    const resp = await getSearchSuggestions({ keyword: keywordValue, limit: 8 })
    suggestions.value = resp.code === 200 && Array.isArray(resp.data)
      ? resp.data.map((item) => normalizeKeyword(item?.keyword)).filter(Boolean)
      : []
  } catch (e) {
    if (handleContentSafetyError(e, { showToast: false })) {
      suggestions.value = []
      return
    }
    suggestions.value = []
  } finally {
    suggestionsLoading.value = false
  }
}

async function loadHotKeywords() {
  hotLoading.value = true
  try {
    const resp = await getHotKeywords({ limit: 8, days: 7 })
    hotKeywords.value = resp.code === 200 && Array.isArray(resp.data) ? resp.data : []
  } catch {
    hotKeywords.value = []
  } finally {
    hotLoading.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    if (isLoggedIn.value) {
      const resp = await getSearchHistory({ limit: 12 })
      if (resp.code === 200 && Array.isArray(resp.data) && resp.data.length > 0) {
        historyItems.value = resp.data.map((item) => ({ ...item, local: false }))
        return
      }
    }

    historyItems.value = toLocalHistoryItems(localHistory.value)
  } catch {
    historyItems.value = toLocalHistoryItems(localHistory.value)
  } finally {
    historyLoading.value = false
  }
}

async function refreshAssistData() {
  restoreLocalHistory()
  await Promise.allSettled([loadHotKeywords(), loadHistory()])
  if (keywordNormalized.value) {
    await loadSuggestions(keywordNormalized.value)
  }
}

function applyKeyword(value: string) {
  const next = normalizeKeyword(value)
  if (!next) return
  keyword.value = next
  void runSearch(true)
}

async function clearHistory() {
  try {
    if (isLoggedIn.value) {
      await clearRemoteSearchHistory()
    }
  } catch {
    // ignore remote clear failures and fall back to local state
  } finally {
    clearLocalHistory()
    historyItems.value = []
  }
}

async function deleteHistory(item: DisplayHistoryItem) {
  if (!item?.id) return

  if (item.local || !isLoggedIn.value) {
    removeLocalHistoryItem(item.keyword)
    historyItems.value = historyItems.value.filter((entry) => entry.id !== item.id)
    return
  }

  try {
    const resp = await deleteRemoteSearchHistoryItem(item.id)
    if (resp.code === 200) {
      await loadHistory()
      return
    }
  } catch {
    // fall through to local refresh below
  }

  await loadHistory()
}

function openItem(it: SearchItem) {
  if (!it?.id) return
  switch (it.type) {
    case 'room':
      uni.navigateTo({ url: `/pages/live/LiveView?roomId=${encodeURIComponent(it.id)}` })
      return
    case 'expert':
      uni.navigateTo({ url: `/pages/expert/ExpertDetail?id=${encodeURIComponent(it.id)}` })
      return
    case 'brand':
      uni.navigateTo({ url: `/pages/brand/BrandDetail?id=${encodeURIComponent(it.id)}` })
      return
    default:
      return
  }
}

function onChangeTab(index: number) {
  activeTabIndex.value = index
}

function normalizeSearchResp(resp: any, page: number) {
  const raw = resp?.data
  const list = raw?.items ?? (Array.isArray(raw) ? raw : [])
  const t = raw?.total ?? list.length
  const p = raw?.page ?? page
  return {
    total: Number(t || 0),
    page: Number(p || page),
    // 返回原始条目数组，后续由 fetchTabPage 传入 type 和 q 进行映射
    items: Array.isArray(list) ? list : []
  }
}

async function fetchTabPage(opts: {
  q: string
  type: TabType
  page: number
  append: boolean
  showGlobalError?: boolean
}) {
  const { q, type, page, append, showGlobalError } = opts

  if (append) tabState[type].loadingMore = true
  try {
    let resp: any
    if (type === 'room') {
      resp = await globalSearch(q, { type: 'room', page, size })
    } else if (type === 'expert') {
      resp = await searchExperts({ q, page, size })
    } else {
      resp = await getBrandList({ q, page, size })
    }

    if (resp.code !== 200 || !resp.data) {
      throw new Error(resp.message || '搜索失败')
    }

    // --- image debug: 打印搜索响应中缺少头像/图片的专家或品牌条目，便于在调试器中查看 ---
    try {
      const raw = resp.data
      const rawList = raw?.items ?? (Array.isArray(raw) ? raw : [])
      if (type === 'expert' || type === 'brand') {
        const missing = (Array.isArray(rawList) ? rawList : []).filter((i) => {
          return !(i && (i.avatar || i.image || i.logo || i.avatar_url || i.cover_url))
        })
        if (missing.length) {
          console.warn('[ImageLog] 搜索响应缺少头像条目', { type, q, count: missing.length })
          missing.slice(0, 50).forEach((it) => {
            console.log('[ImageLog] 缺失项', { id: it?.id, name: it?.name || it?.title || it?.nick, avatar: it?.avatar || it?.image || it?.logo || it?.avatar_url || it?.cover_url })
          })
        } else {
          console.log('[ImageLog] 搜索响应所有条目有头像', { type, q, count: Array.isArray(rawList) ? rawList.length : 0 })
        }
      }
    } catch (e) {
      // ignore logging errors
    }

    const normalized = normalizeSearchResp(resp, page)
    tabState[type].total = normalized.total
    tabState[type].page = normalized.page

    let sourceItems = normalized.items
    if (type === 'room') {
      sourceItems = await enrichRoomSearchItems(sourceItems)
      sourceItems = await hydrateRoomHostAvatars(sourceItems)
      // 仍缺头像：用房间详情补库内 host，再试一次专家头像
      sourceItems = await hydrateMissingHostsFromRoomDetail(sourceItems)
      sourceItems = await hydrateRoomHostAvatars(sourceItems)
    }
    if (type === 'expert') {
      sourceItems = await hydrateExpertAvatars(sourceItems)
    }
    // 与 BrandZone 同口径：显式 is_active=false 丢弃（F8）
    if (type === 'brand') {
      sourceItems = sourceItems.filter((b: any) => {
        const rawActive = b?.is_active ?? b?.isActive ?? b?.active
        return rawActive !== false
      })
    }

    const mappedItems = sourceItems.map((item) => {
      const mi = mapToSearchItem(item, type, q)
      return {
        ...mi,
        type: mi.type || type
      }
    })

    if (append) tabState[type].items.push(...mappedItems)
    else tabState[type].items = mappedItems
  } catch (e: any) {
    if (showGlobalError) error.value = getUserFacingErrorMessage(e, '搜索失败，请稍后再试')
  } finally {
    tabState[type].loadingMore = false
  }
}

async function runSearch(refresh = true) {
  const q = keywordNormalized.value
  if (q.length < 2) {
    uni.showToast({ title: '请输入至少2个字符', icon: 'none' })
    return
  }

  if (loading.value) return
  if (!refresh && tabState[activeType.value].loadingMore) return

  loading.value = true
  error.value = null

  try {
    // Step 1: 门禁 — 对齐后端 search_query 校验
    const gate = await globalSearch(q, { page: 1, size: 1 })
    if (gate.code !== 200) {
      throw Object.assign(new Error(gate.message || '搜索失败'), { code: gate.code })
    }

    // Step 2: 仅通过后更新状态与历史
    if (refresh) {
      searchedKeyword.value = q
      suggestions.value = []
      resetTabData()
      activeTabIndex.value = 0
      saveLocalHistory(q)
    }

    // Step 3: 并行拉各 Tab 结果（/rooms 等无 search_query 校验）
    if (refresh) {
      loaded.value = false
      await Promise.allSettled(
        TAB_TYPES.map((t) => fetchTabPage({ q, type: t, page: 1, append: false, showGlobalError: false }))
      )
    } else {
      const t = activeType.value
      const nextPage = tabState[t].page + 1
      await fetchTabPage({ q, type: t, page: nextPage, append: true, showGlobalError: false })
    }
    loaded.value = true
  } catch (e) {
    if (handleContentSafetyError(e)) {
      loaded.value = false
      resetTabData()
      return
    }
    loaded.value = true
    error.value = getUserFacingErrorMessage(e, '搜索失败，请稍后再试')
    uni.showToast({ title: error.value, icon: 'none' })
  } finally {
    loading.value = false
  }
}

function onSubmit() {
  void runSearch(true)
}

watch(keyword, () => {
  scheduleSuggestionFetch()
})

onLoad(async (options: Record<string, any>) => {
  authStore.restoreAuth()
  await refreshAssistData()

  const q = normalizeKeyword(options?.q)
  if (q) {
    keyword.value = q
    await runSearch(true)
  } else {
    // 无预填词时自动聚焦输入（与首页点搜索进入一致）
    setTimeout(() => {
      inputFocused.value = true
    }, 80)
  }
})

onShow(() => {
  authStore.restoreAuth()
  void refreshAssistData()
})

onPullDownRefresh(async () => {
  if (showResults.value) {
    await runSearch(true)
  } else {
    await refreshAssistData()
  }
  uni.stopPullDownRefresh()
})

onReachBottom(async () => {
  if (!showResults.value) return
  if (!loaded.value) return
  if (!activeHasMore.value) return
  if (activeLoadingMore.value) return
  await runSearch(false)
})

onUnmounted(() => {
  if (suggestionTimer) clearTimeout(suggestionTimer)
})
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.search-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0 0 var(--spacing-md);
  box-sizing: border-box;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 16px;
  box-sizing: border-box;
  /* 与首页 TopBar 一致：白底上衬灰搜索条，才能看出框的大小 */
  background-color: var(--color-bg-primary);
}

.top-bar__back,
.top-bar__side-spacer {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
}

.top-bar__back {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 与首页 TopBar.__search 同规格 */
.search-pill {
  flex: 1;
  min-width: 0;
  height: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  background-color: var(--color-bg-secondary);
  border: none;
  border-radius: 16px;
  box-sizing: border-box;
}

.search-pill__icon {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1;
  color: var(--color-text-tertiary);
}

.search-pill__input {
  flex: 1;
  min-width: 0;
  height: 32px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: transparent;
  line-height: 32px;
}

.search-pill__placeholder {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.search-pill__clear {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assist-panel {
  margin-top: var(--spacing-md);
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.assist-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.assist-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assist-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.assist-group__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.assist-group__meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.assist-group__action {
  font-size: 12px;
  color: var(--color-primary);
}

.assist-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.assist-chip {
  max-width: 100%;
  min-width: 0;
  padding: 12rpx 22rpx;
  border-radius: var(--border-radius-full);
  border: 1px solid var(--color-border-light);
  background: var(--color-bg-secondary);
  display: inline-flex;
  align-items: center;
  gap: 10rpx;
}

.assist-chip__text {
  font-size: 13px;
  color: var(--color-text-primary);
}

.assist-chip__count {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: 16rpx 0;
  border-bottom: 1px solid var(--color-border);
}

.history-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.history-row:first-child {
  padding-top: 0;
}

.history-row__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.history-row__keyword {
  font-size: 14px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-row__meta {
  font-size: 11px;
  color: var(--color-text-tertiary);
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
}

.history-row__dot {
  color: var(--color-text-tertiary);
}

.history-row__delete {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.content {
  margin-top: var(--spacing-md);
  padding: 0 16px;
  box-sizing: border-box;
}

.result-tabs {
  background: transparent;
  height: 72rpx;
  box-sizing: border-box;
  margin-bottom: var(--spacing-sm);
}

.tabs-row {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--spacing-lg);
  box-sizing: border-box;
  white-space: nowrap;
}

.tab {
  box-sizing: border-box;
  height: 100%;
  padding: 0 var(--spacing-base);
  margin-right: var(--spacing-base);
  background: transparent;
  border: none;
  border-radius: 0;
  font-size: 13px;
  transition: color var(--duration-base) var(--ease-in-out),
    transform var(--duration-fast) var(--ease-in-out);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;

  &:active {
    transform: scale(0.98);
  }
}

.tab.active {
  .label {
    color: var(--color-primary);
    font-weight: 600;
  }

  &::after {
    content: '';
    position: absolute;
    left: 50%;
    bottom: 8rpx;
    transform: translateX(-50%);
    width: 40rpx;
    height: 6rpx;
    border-radius: var(--border-radius-full);
    background-color: var(--color-primary);
  }
}

.label {
  height: 100%;
  display: flex;
  align-items: center;
  line-height: 1;
  color: var(--color-text-secondary);
}

.list {
  background: var(--color-surface);
  border-top: none;
  border-bottom: none;
  margin-left: calc(var(--spacing-md) * -1);
  margin-right: calc(var(--spacing-md) * -1);
}

.row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: transparent;
}

.row:last-child {
  border-bottom: none;
}

.cover {
  width: 96px;
  height: 64px;
  border-radius: var(--border-radius-base);
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
  margin-top: 2px;
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title--2line {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  min-height: calc(15px * 1.4 * 2);
}

.room-cover {
  position: relative;
  flex-shrink: 0;
  width: 112px;
  height: 84px;
}

.row--room .cover {
  width: 112px;
  height: 84px;
  margin-top: 0;
  display: block;
}

.room-cover__badge {
  position: absolute;
  top: 6px;
  right: 6px;
  max-width: calc(100% - 12px);
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.45);
  box-sizing: border-box;
}

.room-cover__badge-text {
  font-size: 10px;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.host-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.host-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
  border: 1px solid var(--color-border);
}

.host-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.host-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.host-hospital {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 专家：对齐 ExpertCard 横排信息 */
.expert-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
  margin-top: 0;
}

.expert-name-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
}

.expert-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-job {
  font-size: 12px;
  color: var(--color-text-secondary);
  max-width: 38%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-dept {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-specialty {
  font-size: 12px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 品牌：对齐 BrandCard 字段，横排 */
.brand-logo-wrap {
  width: 64px;
  height: 64px;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-logo {
  width: 100%;
  height: 100%;
  display: block;
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  word-break: break-word;
  line-height: 1.4;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.result-chip {
  max-width: 100%;
  padding: 2px 8px;
  border-radius: var(--border-radius-full);
  font-size: 10px;
  line-height: 1.4;
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
  display: inline-flex;
  align-items: center;
}

.result-chip__text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 10px;
  line-height: 1.4;
  color: inherit;
}

.result-chip--category {
  color: var(--color-primary);
  background: rgba(15, 118, 110, 0.06);
  border-color: rgba(15, 118, 110, 0.18);
}

.result-chip--status-live {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.18);
}

.result-chip--status-scheduled {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.18);
}

.result-chip--status-replay {
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-light);
}

.sub {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  flex-shrink: 0;
}

.more {
  text-align: center;
  padding: 12px 0;
  color: var(--color-text-tertiary);
  font-size: 12px;
}
</style>
