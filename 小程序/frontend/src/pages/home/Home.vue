<template>
  <view class="home-page">
    <view class="home-page__top">
      <!-- tab 保活时 sticky TopBar 可能渗入其他页；非前台卸载以切断叠层 -->
      <TopBar
        v-if="homeForeground"
        :unread-count="unreadCount"
        :avatar-url="authStore.isAuthenticated ? authStore.userInfo?.avatar_url : null"
        @search="handleSearch"
        @message="handleMessage"
        @avatar="handleAvatar"
      />

      <CategoryTabs
        :categories="categories"
        :active-id="activeCategory"
        :pinned-ids="preferencesStore.pinnedCategoryIds"
        @select="handleCategorySelect"
        @open-all="handleOpenAllCategories"
      />
    </view>

    <Banner3D :banners="banners" @click="handleBannerClick" />

    <FeaturedExperts
      :experts="featuredExperts"
      :following-map="featuredFollowMap"
      :follow-pending-id="featuredFollowPendingId"
      @open-detail="handleFeaturedExpertClick"
      @toggle-follow="handleFeaturedExpertToggleFollow"
    />

    <!-- flow：横滑/点击切 Tab；列表随页面撑高，可滑到底 -->
    <StickyTabPager
      class="home-pager"
      :tabs="statusPagerTabs"
      :current="statusSwiperIndex"
      flow
      @change="handleStatusPagerChange"
    >
      <template #pane>
        <view class="home-page__content">
          <LoadingIndicator v-if="loading && displayRooms.length === 0" text="加载中..." />

          <view v-else-if="displayRooms.length > 0" class="room-grid">
            <view class="room-grid__column">
              <LiveCard
                v-for="room in leftColumnRooms"
                :key="room.id"
                v-bind="room"
                @click="handleRoomClick(room)"
              />
            </view>
            <view class="room-grid__column">
              <LiveCard
                v-for="room in rightColumnRooms"
                :key="room.id"
                v-bind="room"
                @click="handleRoomClick(room)"
              />
            </view>
          </view>

          <view v-else class="empty-state">
            <text class="iconfont icon-shipin empty-state__icon"></text>
            <text class="empty-state__text">{{ emptyTextByStatus(statusFilter) }}</text>
          </view>

          <view v-if="!loading && hasMore && rooms.length > 0" class="load-more">
            <text class="load-more__text">加载更多...</text>
          </view>

          <view v-if="!hasMore && rooms.length > 0" class="no-more">
            <text class="no-more__text">没有更多了</text>
          </view>
        </view>
      </template>
    </StickyTabPager>

    <QuickMenu
      :visible="showQuickMenu"
      :view-mode="viewMode"
      @close="showQuickMenu = false"
      @view-mode-change="handleViewModeChange"
      @refresh="handleRefresh"
      @scroll-to-top="handleScrollToTop"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow, onHide, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { logger } from '@/logs/logger'
import { normalizeImageUrl, resolveMediaUrl } from '@/utils/url'
import { setCustomTabBarSelected } from '@/utils/tabbar'
import { useAuthStore } from '@/store/auth'
import { useRoomStore } from '@/store/room'
import { usePreferencesStore } from '@/store/preferences'
import { getHomepageRooms } from '@/api/room'
import { followExpert, unfollowExpert, getExpertDetail, getFeaturedExperts, getMyFollowedExperts } from '@/api/expert'
import { getFeaturedContent } from '@/api/featuredContent'
import { getUnreadNotificationCount } from '@/api/notifications'
import { getCategoryList } from '@/api/categories'
import TopBar from '@/components/home/TopBar.vue'
import CategoryTabs from '@/components/home/CategoryTabs.vue'
import Banner3D from '@/components/home/Banner3D.vue'
import FeaturedExperts, { type FeaturedExpertCard } from '@/components/home/FeaturedExperts.vue'
import LiveCard from '@/components/common/LiveCard.vue'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import QuickMenu from '@/components/home/QuickMenu.vue'
import StickyTabPager, { type StickyTabItem } from '@/components/common/StickyTabPager.vue'
import { DEFAULT_CONFIG } from '@/common/constants'

type StatusFilter = 'scheduled' | 'live' | 'replay'

// Store
const authStore = useAuthStore()
const roomStore = useRoomStore()
const preferencesStore = usePreferencesStore()

// 状态
const homeForeground = ref(true)
const loading = ref(false)
const refreshing = ref(false)
const rooms = ref<any[]>([])
const page = ref(1)
// 遵循后端文档：GET /api/v1/homepage/rooms 默认 size=10（最大100）
const pageSize = 10
const hasMore = ref(true)
const unreadCount = ref(0)
const activeCategory = ref<'recommend' | string>('recommend')
const STATUS_EMPTY: Record<StatusFilter, string> = {
  live: '暂无直播',
  scheduled: '暂无预告',
  replay: '暂无回放'
}
const statusPagerTabs: StickyTabItem[] = [
  { id: 'live', label: '直播', badge: 'live-dot' },
  { id: 'scheduled', label: '预告' },
  { id: 'replay', label: '回放' }
]
const statusFilter = ref<StatusFilter>('live')
const statusSwiperIndex = ref(0)

const emptyTextByStatus = (id: StatusFilter) => STATUS_EMPTY[id] || '暂无内容'
const viewMode = computed(() => preferencesStore.homepageViewMode)
const showQuickMenu = ref(false)
const featuredExperts = ref<FeaturedExpertCard[]>([])
const featuredFollowMap = ref<Record<string, boolean>>({})
const featuredFollowPendingId = ref<string | null>(null)

// 首页主播头像补全缓存（避免重复请求）
const expertAvatarCache = new Map<string, string>()

// 分类数据（从API获取）
const categories = ref<Array<{ id: string; name: string; icon?: string }>>([])

/**
 * 加载科室分类数据
 */
const loadCategories = async () => {
  try {
    const resp = await getCategoryList()
    const data = (resp as any)?.data ?? resp
    const items = Array.isArray(data) ? data : []

    categories.value = items
      .filter((c: any) => c?.is_active !== false)
      .sort((a: any, b: any) => (a?.sort_order ?? 0) - (b?.sort_order ?? 0))
      .map((c: any) => ({
        id: String(c.id),
        name: String(c.name || ''),
        icon: c.icon || ''
      }))

    logger.info('system', '首页科室分类加载成功', { count: categories.value.length })
  } catch (error) {
    categories.value = []
    logger.error('system', '加载科室分类失败', { error })
  }
}

type HomeBanner = {
  id: string
  image_url: string
  title?: string
  link?: string
  target_type?: string  // room/session/brand/external；历史 topic/expert 不响应
  target_id?: string    // 关联资源ID
  source?: 'local_fallback' | 'backend'
}

function summarizeFeaturedContentItem(item: any) {
  return {
    id: item?.id != null ? String(item.id) : '',
    title: item?.title ? String(item.title) : '',
    image_url: item?.image_url ? String(item.image_url) : '',
    target_url: item?.target_url ? String(item.target_url) : '',
    sort_order: item?.sort_order ?? null,
    type: item?.type ? String(item.type) : '',
    status: item?.status ? String(item.status) : '',
    is_active: item?.is_active,
    created_at: item?.created_at ? String(item.created_at) : ''
  }
}

function summarizeHomeBanner(banner: HomeBanner) {
  return {
    id: banner?.id ? String(banner.id) : '',
    title: banner?.title ? String(banner.title) : '',
    image_url: banner?.image_url ? String(banner.image_url) : '',
    target_type: banner?.target_type || '',
    target_id: banner?.target_id || '',
    link: banner?.link ? String(banner.link) : '',
    source: banner?.source || 'unknown'
  }
}

// 轮播图（接口不可用/空列表时用单张焦点图兜底）
const banners = ref<HomeBanner[]>([
  {
    id: 'banner_fallback',
    image_url: DEFAULT_CONFIG.DEFAULT_BANNER,
    title: '',
    link: '',
    source: 'local_fallback'
  }
])

const normalizeFeaturedExpertAvatar = (item: any): string | null => {
  const raw =
    item?.avatar_url ??
    item?.avatarUrl ??
    item?.avatar ??
    item?.avatar_path ??
    item?.head_img ??
    item?.headImg ??
    null
  // 仅保留解析后可展示的地址；空/空白/无效串归一为 null，交给组件走人物占位
  const resolved = resolveMediaUrl(typeof raw === 'string' || typeof raw === 'number' ? String(raw) : '')
  return resolved || null
}

const normalizeFeaturedExperts = (value: any): FeaturedExpertCard[] => {
  const list = Array.isArray(value)
    ? value
    : Array.isArray(value?.items)
      ? value.items
      : []

  return list
    .map((item: any) => ({
      id: String(item?.id ?? item?.expert_id ?? ''),
      name: String(item?.name ?? item?.expert_name ?? '未命名专家'),
      avatarUrl: normalizeFeaturedExpertAvatar(item),
      title: item?.title ?? item?.position ?? item?.professional_title ?? null,
      hospital: item?.hospital ?? item?.institution ?? item?.organization ?? null,
      department: item?.department_name ?? item?.department ?? item?.dept_name ?? null,
      liveStatus: (() => {
        const raw = String(item?.live_status?.status ?? item?.liveStatus ?? item?.live_status ?? '').toLowerCase()
        if (raw === 'live' || item?.live_status?.is_live === true) return 'live'
        if (raw === 'scheduled') return 'scheduled'
        if (raw === 'replay') return 'replay'
        return null
      })()
    }))
    .filter((item: FeaturedExpertCard) => !!item.id)
}

/**
 * 加载未读通知数量（登录后才会请求）
 * 使用独立端点 unread-count
 */
const loadUnreadCount = async () => {
  if (!authStore.isAuthenticated) {
    unreadCount.value = 0
    return
  }

  try {
    const resp = await getUnreadNotificationCount()
    const unread = Number((resp as any)?.data?.unread_count)
    if (Number.isFinite(unread)) {
      unreadCount.value = unread
    }
  } catch (error) {
    // 安静失败，不影响首页渲染
    return
  }
}

/**
 * 加载焦点图（Featured Content）
 */
const loadFeaturedBanners = async () => {
  try {
    logger.info('network', '开始加载首页焦点图', {
      hasFallback: banners.value.length > 0,
      fallbackCount: banners.value.length
    })

    const response = await getFeaturedContent()
    // 文档约定：data 为 { items: FeaturedContent[] }；兼容历史上直接返回数组
    const responseData = ((response as any)?.data ?? response) as any
    const items = Array.isArray(responseData)
      ? responseData
      : Array.isArray(responseData?.items)
        ? responseData.items
        : []

    logger.info('network', '首页焦点图接口返回', {
      responseKeys: response && typeof response === 'object' ? Object.keys(response as Record<string, any>) : [],
      code: (response as any)?.code ?? null,
      message: (response as any)?.message ?? '',
      dataType: Array.isArray(responseData) ? 'array' : typeof responseData,
      dataKeys: responseData && typeof responseData === 'object' && !Array.isArray(responseData)
        ? Object.keys(responseData)
        : [],
      dataCount: items.length,
      dataSample: items.slice(0, 3).map(summarizeFeaturedContentItem)
    })

    // 严格按后端文档：接口只返回有效/启用的焦点图；客户端不应依赖 is_active 字段。
    const activeItems = items
      .sort((a: any, b: any) => Number(a?.sort_order ?? 0) - Number(b?.sort_order ?? 0))
      .slice(0, 10)

    logger.info('network', '首页焦点图规范化完成', {
      sourceCount: items.length,
      activeCount: activeItems.length,
      activeItems: activeItems.map((item: any) => ({
        ...summarizeFeaturedContentItem(item),
        resolved_image_url: resolveMediaUrl(item?.image_url) || String(item?.image_url || '')
      }))
    })

    if (activeItems.length === 0) {
      logger.warn('network', '首页焦点图为空，继续使用本地兜底', {
        responseKeys: response && typeof response === 'object' ? Object.keys(response as Record<string, any>) : [],
        dataCount: items.length,
        dataSample: items.slice(0, 3).map(summarizeFeaturedContentItem)
      })
      return
    }

    banners.value = activeItems.map((b: any) => ({
      id: String(b.id),
      image_url: resolveMediaUrl(b.image_url) || String(b.image_url || ''),
      title: b.title ? String(b.title) : undefined,
      link: b.target_url ? String(b.target_url) : undefined,
      target_type: b.target_type ? String(b.target_type) : undefined,
      target_id: b.target_id ? String(b.target_id) : undefined,
      source: 'backend'
    }))

    logger.info('network', '首页焦点图更新完成', {
      bannerCount: banners.value.length,
      banners: banners.value.map(summarizeHomeBanner)
    })
  } catch (error) {
    // 接口不可用时保持本地兜底，不打断首页渲染
    logger.warn('system', '加载焦点图失败，使用本地兜底', {
      error,
      fallbackCount: banners.value.length,
      fallbackBanners: banners.value.map(summarizeHomeBanner)
    })
  }
}

const loadFeaturedFollowMap = async () => {
  if (!authStore.isAuthenticated) {
    featuredFollowMap.value = {}
    return
  }

  try {
    const resp = await getMyFollowedExperts()
    const list = Array.isArray((resp as any)?.data) ? (resp as any).data : []
    const map: Record<string, boolean> = {}
    list.forEach((item: any) => {
      const expertId = String(item?.expert_id ?? item?.id ?? '')
      if (expertId) map[expertId] = true
    })
    featuredFollowMap.value = map
  } catch (error) {
    featuredFollowMap.value = {}
  }
}

const loadFeaturedExperts = async () => {
  try {
    const response = await getFeaturedExperts(6)
    const payload = (response as any)?.data ?? response
    featuredExperts.value = normalizeFeaturedExperts(payload)
    await loadFeaturedFollowMap()
  } catch (error) {
    featuredExperts.value = []
    featuredFollowMap.value = {}
    logger.warn('system', '加载精选专家失败', { error })
  }
}

const displayRooms = computed(() =>
  rooms.value.filter((r) => r?.liveStatus === statusFilter.value)
)
const leftColumnRooms = computed(() =>
  displayRooms.value.filter((_, index) => index % 2 === 0)
)
const rightColumnRooms = computed(() =>
  displayRooms.value.filter((_, index) => index % 2 === 1)
)

const handleStatusPagerChange = (idx: number) => {
  const tab = statusPagerTabs[idx]
  if (!tab) return
  statusSwiperIndex.value = idx
  statusFilter.value = tab.id as StatusFilter
}

/** 当前 Tab 无数据时，落到第一个有房间的状态（避免一进来空白） */
const ensureVisibleStatusTab = () => {
  if (displayRooms.value.length > 0) return
  const order: StatusFilter[] = ['live', 'scheduled', 'replay']
  const hit = order.find((id) => rooms.value.some((r) => r?.liveStatus === id))
  if (!hit) return
  const idx = statusPagerTabs.findIndex((t) => t.id === hit)
  if (idx < 0) return
  statusSwiperIndex.value = idx
  statusFilter.value = hit
}

/**
 * 加载直播间列表
 */
const loadRooms = async (isRefresh = false) => {
  if (loading.value) return
  
  try {
    loading.value = true
    
    if (isRefresh) {
      page.value = 1
      rooms.value = []
    }
    
    const response = await getHomepageRooms({
      page: page.value,
      size: pageSize,
      category_id: activeCategory.value !== 'recommend' ? activeCategory.value : undefined,
      sort: 'created_at:desc' // 按创建时间排序（参考核心设计文档房间列表）
    })
    
    // 调试：打印完整响应
    console.log('🔍 API响应数据:', response)
    
    // 响应拦截器已经提取了data字段，所以response直接就是分页数据 {total, page, size, items}
    // 或者可能是 {code: 200, data: {total, page, size, items}} 格式
    const paginatedData = (response as any).data || response
    const items = paginatedData.items || []
    const total = paginatedData.total || 0
    const pageNum = paginatedData.page || 1
    const size = paginatedData.size || 10
    
    console.log('📦 解析后的数据:', { items, total, itemsLength: items.length, pageNum, size })
    
    if (items.length === 0) {
      // 空页：可能是无数据，也可能是翻页到末尾
      hasMore.value = false
      logger.warn('user', '房间列表为空', { response, paginatedData, page: page.value })
      return
    }
    
    // 首页列表接口：GET /api/v1/homepage/rooms（包含 live_status/host/status_data/heat 等字段）
    const newRooms = items.map((item: any) => ({
      id: item.id,
      title: item.title,
      // 关键修复：不在这里预处理 URL，保存原始值
      // 原因：如果在缓存层处理，错误的 URL 会被持久化；组件层再处理时会进一步恶化
      // 正确做法：保存原始 /media/... 路径，让 LiveCard 组件在使用前解析
      coverUrl: item.cover_url || null,
      rawCoverUrl: item.cover_url || null,
      summary: item.summary || null,
      category: item.primary_category_name
        ? { name: item.primary_category_name }
        : item.category || null,
      liveStatus: (() => {
        const s = String((item as any)?.live_status || '').toLowerCase()
        if (s === 'live') return 'live' as const
        if (s === 'scheduled') return 'scheduled' as const
        if (s === 'replay') return 'replay' as const
        return 'replay' as const
      })(),
      host: item.host
        ? {
            expertId: item.host.expert_id ?? null,
            name: item.host.name,
            avatarUrl:
              item.host.avatar_url ??
              item.host.avatarUrl ??
              item.host.avatar ??
              item.host.avatarURL ??
              null,
            title: item.host.title ?? null,
            hospital: item.host.hospital ?? null
          }
        : null,
      viewerCount: (item.status_data?.viewer_count ?? null) as number | null,
      likeCount: ((item.status_data?.play_count ?? item.heat ?? null) as number | null),
      heat: (item.heat ?? null) as number | null
    }))
    
    console.log('✅ 映射后的房间数据:', newRooms)
    
    if (isRefresh) {
      rooms.value = newRooms
      ensureVisibleStatusTab()
    } else {
      rooms.value.push(...newRooms)
    }

    // 尝试补全首页缺失的主播头像：仅在 host.expertId 存在且 avatarUrl 缺失时
    const toHydrate = (isRefresh ? rooms.value : newRooms)
      .filter((r: any) => r?.host?.expertId && !r?.host?.avatarUrl)
      .slice(0, 8)

    await Promise.all(
      toHydrate.map(async (r: any) => {
        const expertId = String(r.host.expertId)
        const cached = expertAvatarCache.get(expertId)
        if (cached) {
          r.host.avatarUrl = cached
          return
        }
        try {
          // 《16》P44：已下架专家详情 404，补头像静默失败即可
          const resp = await getExpertDetail(expertId, { showError: false, quiet: true })
          const payload = (resp as any)?.data ?? resp
          const url = normalizeImageUrl(payload?.avatar_url || payload?.avatarUrl || payload?.avatar)
          if (url) {
            expertAvatarCache.set(expertId, url)
            r.host.avatarUrl = url
          }
        } catch {
          return
        }
      })
    )
    
    hasMore.value = rooms.value.length < total
    
    logger.info('user', '加载直播间列表成功', {
      page: page.value,
      count: newRooms.length,
      total: total,
      roomsLength: rooms.value.length
    })
  } catch (error) {
    console.error('❌ 加载房间列表异常:', error)
    logger.error('system', '加载直播间列表失败', { error })
    uni.showToast({ title: '加载失败，请重试', icon: 'none' })
    // 调试：显示错误详情
    if (process.env.NODE_ENV === 'development') {
      console.error('错误详情:', error)
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

/**
 * 加载更多
 */
const handleLoadMore = () => {
  if (!loading.value && hasMore.value) {
    page.value++
    loadRooms()
  }
}

/**
 * 选择科室
 */
const handleCategorySelect = (categoryId: string | null) => {
  const next = String(categoryId || 'recommend')
  logger.info('user', '切换首页科室分类', {
    from: activeCategory.value,
    to: next === 'recommend' ? 'recommend' : next,
    label: next === 'recommend' ? '推荐' : next
  })
  activeCategory.value = next === 'recommend' ? 'recommend' : next
  loadRooms(true)
}

const handleOpenAllCategories = () => {
  logger.info('user', '打开全部分类页')
  uni.navigateTo({ url: '/pages/home/AllCategories' })
}

onMounted(async () => {
  logger.info('system', '首页加载')
  await preferencesStore.fetchPreferences({ force: true })
  await Promise.all([
    loadCategories(),
    loadUnreadCount(),
    loadFeaturedBanners(),
    loadFeaturedExperts(),
    loadRooms(true)
  ])
})

onShow(() => {
  homeForeground.value = true
  setCustomTabBarSelected(0)
  authStore.clearAuthIfExpired()
  // 非 force：60s 内沿用刚保存的本地星标，避免返回瞬间被旧服务端数据冲掉
  preferencesStore.fetchPreferences()
  loadUnreadCount()
  loadFeaturedFollowMap()
  loadFeaturedBanners()
})

onHide(() => {
  homeForeground.value = false
})

onReachBottom(() => {
  handleLoadMore()
})

onPullDownRefresh(async () => {
  await handleRefresh()
  uni.stopPullDownRefresh()
})

/**
 * 刷新
 */
const handleRefresh = async () => {
  logger.info('user', '刷新首页分类与直播间数据', {
    activeCategory: activeCategory.value,
    statusFilter: statusFilter.value
  })
  refreshing.value = true
  await Promise.all([
    preferencesStore.fetchPreferences({ force: true }),
    loadCategories(),
    loadRooms(true),
    loadFeaturedExperts(),
    loadUnreadCount()
  ])
  refreshing.value = false
}

/**
 * 点击直播间
 */
const handleRoomClick = (room: any) => {
  logger.info('user', '点击直播间', { 
    roomId: room.id, 
    liveStatus: room.liveStatus 
  })
  
  // 将房间数据存储到 store，用于跨页面传递
  roomStore.setSelectedRoomFromHome(room)
  
  // 统一跳转到LiveView，传入roomId，让LiveView自动查找对应的sessionId
  // 根据你之前说的流程：通过roomId查房间详情获取current_session_id，如果没有则查场次列表取最新场次
  uni.navigateTo({
    url: `/pages/live/LiveView?roomId=${room.id}`,
    fail: (err) => {
      logger.error('system', '跳转直播观看页面失败', { error: err, roomId: room.id })
      uni.showToast({
        title: '跳转失败，请稍后重试',
        icon: 'none'
      })
    }
  })
}

/**
 * 点击搜索
 */
const handleSearch = () => {
  logger.info('user', '点击搜索')
  uni.navigateTo({
    url: '/subpackages/search/index'
  })
}

const goLogin = (redirectUrl: string) => {
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

/**
 * 点击左上角头像 → 个人中心（未登录走登录）
 */
const handleAvatar = () => {
  logger.info('user', '点击首页头像')
  const redirect = '/pages/profile/Profile'
  if (!authStore.isAuthenticated) {
    goLogin(redirect)
    return
  }
  uni.switchTab({
    url: redirect,
    fail: () => {
      uni.navigateTo({ url: redirect })
    }
  })
}

/**
 * 点击消息
 */
const handleMessage = () => {
  logger.info('user', '点击消息')

  const redirect = '/pages/profile/Notifications'
  if (!authStore.isAuthenticated) {
    goLogin(redirect)
    return
  }

  uni.navigateTo({ url: redirect })
}

/**
 * 点击轮播图
 */
const handleBannerClick = (banner: any) => {
  logger.info('user', '点击轮播图', {
    bannerId: banner?.id ? String(banner.id) : '',
    bannerTitle: banner?.title ? String(banner.title) : '',
    target_type: banner?.target_type || '',
    target_id: banner?.target_id || '',
    link: banner?.link || '',
    bannerSource: banner?.source || 'unknown'
  })

  // 历史废弃类型：不跳转
  if (banner.target_type === 'topic' || banner.target_type === 'expert') {
    logger.info('user', '焦点图废弃跳转类型，忽略点击', { target_type: banner.target_type })
    return
  }

  // 外部链接
  if (banner.target_type === 'external' && banner.link) {
    // 小程序不支持 window.open，复制链接到剪贴板
    uni.setClipboardData({
      data: banner.link,
      success: () => {
        uni.showToast({ title: '链接已复制到剪贴板', icon: 'success' })
      }
    })
    return
  }

  // 内部跳转
  if (banner.target_id && banner.target_type) {
    const routeMap: Record<string, string> = {
      room: `/pages/live/LiveView?roomId=${banner.target_id}`,
      session: `/pages/live/LiveView?sessionId=${banner.target_id}`,
      brand: `/pages/brand/BrandDetail?id=${banner.target_id}`
    }
    const path = routeMap[banner.target_type]
    if (path) {
      uni.navigateTo({
        url: path,
        fail: (err) => {
          logger.error('system', '焦点图跳转失败', { error: err, path })
          uni.showToast({ title: '页面跳转失败', icon: 'none' })
        }
      })
      return
    }
  }

  // 无跳转目标，仅展示
  logger.info('user', '焦点图无跳转目标，纯展示')
}

const handleFeaturedExpertClick = (expert: FeaturedExpertCard) => {
  if (!expert?.id) return
  uni.navigateTo({
    url: `/pages/expert/ExpertDetail?id=${encodeURIComponent(expert.id)}`
  })
}

const handleFeaturedExpertToggleFollow = async (expert: FeaturedExpertCard) => {
  if (!expert?.id || featuredFollowPendingId.value) return

  if (!authStore.isAuthenticated) {
    goLogin('/pages/home/Home')
    return
  }

  const wasFollowing = !!featuredFollowMap.value[expert.id]
  featuredFollowPendingId.value = expert.id

  try {
    if (wasFollowing) {
      const resp: any = await unfollowExpert(expert.id)
      if (resp?.code !== 200) throw new Error(resp?.message || '取消关注失败')
      featuredFollowMap.value = {
        ...featuredFollowMap.value,
        [expert.id]: false
      }
      uni.showToast({ title: '已取消关注', icon: 'none' })
      return
    }

    const resp: any = await followExpert(expert.id)
    if (resp?.code !== 200) throw new Error(resp?.message || '关注失败')
    featuredFollowMap.value = {
      ...featuredFollowMap.value,
      [expert.id]: true
    }
    uni.showToast({ title: '关注成功', icon: 'success' })
  } catch (error: any) {
    uni.showToast({ title: error?.message || '操作失败', icon: 'none' })
  } finally {
    featuredFollowPendingId.value = null
  }
}

/**
 * 切换视图模式
 */
const handleViewModeChange = (mode: 'double' | 'single') => {
  logger.info('user', '切换首页展示模式', { from: preferencesStore.homepageViewMode, to: mode })
  preferencesStore.saveHomepageViewMode(mode)
  uni.showToast({
    title: mode === 'double' ? '已切换到双列模式' : '已切换到单列模式',
    icon: 'success'
  })
}

/**
 * 回到顶部
 */
const handleScrollToTop = () => {
  uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.home-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  width: 100%;
  box-sizing: border-box;
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));

  &__top {
    background-color: var(--color-bg-primary);
  }

  &__content {
    width: 100%;
    box-sizing: border-box;
    padding-bottom: 24rpx;
  }
}

.home-pager {
  width: 100%;
  background: var(--color-bg-primary);
}

/* 与直播间一致：状态 Tab 吸顶；内容仍走页面滚动，不锁死 swiper 高度 */
.home-pager :deep(.stp-tabs) {
  position: sticky;
  top: 0;
  z-index: 20;
}

.room-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;  /* 设计文档规范：8-12px（紧凑） */
  padding: 10px 12px;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  
  &__column {
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 0; /* 防止子元素溢出 */
    width: 100%;
    box-sizing: border-box;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;

  &__icon {
    font-size: 64px;
    color: var(--color-text-tertiary);
  }
  
  &__text {
    margin-top: 16px;
    font-size: 14px;
    color: var(--color-text-tertiary);
  }
}

.load-more {
  padding: 20px;
  text-align: center;
  
  &__text {
    font-size: 14px;
    color: var(--color-text-tertiary);
  }
}

.no-more {
  padding: 20px;
  text-align: center;
  
  &__text {
    font-size: 12px;
    color: var(--color-text-tertiary);
  }
}
</style>

