<template>
  <view class="home-page">
    <!-- 顶部搜索栏（固定） -->
    <SearchBar :status-bar-height="statusBarHeight" class="fixed-search" />
    <!-- 搜索与 Tabs 间 16rpx 间距 -->
    <view class="header-gap" :style="{ top: `${searchBarHeight}px`, height: `${gapPx}px` }" />
    <!-- 分类筛选器（固定在搜索栏下方） -->
    <view 
      class="sticky-categories"
      :style="{ top: `${searchBarHeight + gapPx}px` }"
    >
      <CategoryTabs 
        ref="categoryTabsRef"
        :active-id="activeCategoryId"
        @change="handleCategoryChange"
      />
    </view>

    <!-- 自定义 TabBar -->
    <CustomTabBar :current="0" />

    <!-- 登录引导横幅（仅未登录时显示，可关闭） -->
    <LoginGuideBanner />

    <!-- 主内容区 -->
    <scroll-view
      :style="{ top: `${headerHeight}px` }"
      class="main-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handlePullDownRefresh"
      @scrolltolower="handleScrollToLower"
    >
      <!-- 焦点图轮播（含专题 + 即将开播 1–2 条） -->
      <!-- 内容区 flex 撑满：数据加载完成后"已经到底了"贴底显示在 tabbar 正上方 -->
      <view class="content-fill" :style="{ minHeight: contentFillHeight }">
        <FeaturedCarousel ref="featuredCarouselRef" :upcoming-list="upcomingListForBanner" />

        <!-- 权威专家/专题推荐轻量模块 -->
        <AuthorityStrip ref="authorityStripRef" />

        <!-- 热门回放卡片 -->
        <RoomCardGrid 
          class="grid-fill"
          :room-list="roomList"
          :is-loading="isLoading"
          :is-loading-more="isLoadingMore"
          :has-more="hasMore"
          @card-click="handleRoomClick"
        />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 首页
 * @description 医学直播平台移动端首页，包含搜索、分类、焦点图、直播卡片
 * 升级说明：使用真实首页API（getHomepageRooms）
 */
import { ref, onMounted, computed, nextTick } from 'vue';
import { onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app';
import type { HomepageRoomItem } from '@/types/homepage';
import { getHomepageRooms } from '@/api/homepage';
import { useAuthStore } from '@/store/auth';
import { APP_LOGIN_PATH, APP_HOME_PATH } from '@/constants/routes';
import { isValidUUID } from '@/utils/url';

// 页面组件
import SearchBar from './components/SearchBar.vue';
import CategoryTabs from './components/CategoryTabs.vue';
import FeaturedCarousel from './components/FeaturedCarousel.vue';
import AuthorityStrip from './components/AuthorityStrip.vue';
import RoomCardGrid from './components/RoomCardGrid.vue';
import CustomTabBar from '@/components/app/CustomTabBar.vue';
import LoginGuideBanner from '@/components/app/LoginGuideBanner.vue';

// ========== Store ==========
const authStore = useAuthStore();

/** 状态栏高度 */
const statusBarHeight = ref(0);
/** AuthorityStrip 组件实例引用 */
const authorityStripRef = ref<InstanceType<typeof AuthorityStrip> | null>(null);
/** FeaturedCarousel 组件实例引用 */
const featuredCarouselRef = ref<InstanceType<typeof FeaturedCarousel> | null>(null);
/** CategoryTabs 组件实例引用 */
const categoryTabsRef = ref<InstanceType<typeof CategoryTabs> | null>(null);
/** 搜索栏总高度 */
const searchBarHeight = computed(() => statusBarHeight.value + 44);
/** 搜索与 Tabs 间距（8rpx 转 px） */
const gapPx = ref(4);
/** 分类tabs高度（动态测量，默认40px） */
const tabsHeight = ref(40);
/** 顶部固定区总高度：搜索栏 + 间距 + 分类tabs */
const headerHeight = computed(() => searchBarHeight.value + gapPx.value + tabsHeight.value);

/**
 * 内容区最小高度（px 字符串）：撑满到 tabbar 正上方（112rpx + safe-area）
 * 内容不足一屏时"已经到底了"贴底显示；内容超一屏时由内容自然撑开，提示跟随内容流末尾
 */
const contentFillHeight = computed(() => {
  const w = uni.getSystemInfoSync().windowWidth || 375;
  const tabbarPx = Math.round((112 * w) / 750);
  return `calc(100vh - ${headerHeight.value}px - ${tabbarPx}px - env(safe-area-inset-bottom))`;
});

/** 每页数据条数（性能优化：首页建议10-15条） */
const PAGE_SIZE = 15;

/** 首次加载时额外获取的数据量，确保包含各种状态的直播间 */
const INITIAL_EXTRA_SIZE = 85;

// ========== 页面状态 ==========
/** 是否加载中 */
const isLoading = ref(true);
/** 是否刷新中 */
const isRefreshing = ref(false);
/** 是否加载更多中 */
const isLoadingMore = ref(false);
/** 是否有更多数据 */
const hasMore = ref(true);
/** 当前页码 */
const currentPage = ref(1);
/** 当前选中分类ID（null表示推荐Tab） */
const activeCategoryId = ref<string | null>(null);

// ========== 数据状态 ==========
/** 直播列表 */
const roomList = ref<HomepageRoomItem[]>([]);
/** 总数 */
const totalCount = ref(0);

/** 预告列表（即将开播，已移入 Banner 轮播） */
const scheduledList = computed(() => roomList.value.filter(r => r.live_status === 'scheduled'));
/** 轮播用即将开播（最多 2 条） */
const upcomingListForBanner = computed(() => scheduledList.value.slice(0, 2));
/** 回放列表（仅回放状态，不包含正在直播） */
const replayList = computed(() => roomList.value.filter(r => r.live_status === 'replay'));

/**
 * 加载直播间列表
 * @param append - 是否追加模式（分页加载）
 */
async function loadRooms(append = false): Promise<void> {
  const loading = append ? 'isLoadingMore' : 'isLoading';
  (loading === 'isLoadingMore' ? isLoadingMore : isLoading).value = true;
  
  try {
    // 首次加载时，增加数据量以确保包含各种状态的直播间
    const loadSize = append ? PAGE_SIZE : (PAGE_SIZE + INITIAL_EXTRA_SIZE);
    
    const res = await getHomepageRooms({
      page: currentPage.value,
      size: loadSize,
      sort: 'heat:desc',
      // 推荐Tab（id=null）不传category_id参数；非UUID格式不传（防止Mock数值ID导致422）
      category_id: isValidUUID(activeCategoryId.value) ? activeCategoryId.value : undefined
    });
    
    if (append) {
      // 追加模式（上拉加载更多）
      roomList.value.push(...res.data.items);
    } else {
      // 覆盖模式（首次加载或筛选）
      roomList.value = res.data.items;
    }

    totalCount.value = res.data.total;
    hasMore.value = roomList.value.length < totalCount.value;
    
    console.log('[Home] ✅ 直播间列表加载完成，当前数量:', roomList.value.length, '/ 总数:', totalCount.value);
    
    // 统计各状态数量（用于调试）
    const statusCount = {
      live: roomList.value.filter(r => r.live_status === 'live').length,
      scheduled: roomList.value.filter(r => r.live_status === 'scheduled').length,
      replay: roomList.value.filter(r => r.live_status === 'replay').length
    };
    console.log('[Home] 📊 状态分布:', statusCount);
    
    // 检查封面URL
    if (roomList.value.length > 0) {
      const firstRoom = roomList.value[0];
      console.log('[Home] 🖼️ 第一个房间封面信息:', {
        id: firstRoom.id,
        title: firstRoom.title,
        cover_url: firstRoom.cover_url,
        has_cover: !!firstRoom.cover_url
      });
    }
  } catch (error) {
    console.error('[Home] 直播间列表加载失败', error);
    uni.showToast({ title: '加载直播间列表失败', icon: 'none' });
  } finally {
    (loading === 'isLoadingMore' ? isLoadingMore : isLoading).value = false;
  }
}

/**
 * 加载页面数据
 */
async function loadPageData(): Promise<void> {
  currentPage.value = 1;
  await loadRooms(false);
}

/**
 * 分类切换处理
 * @param categoryId - 分类ID（null表示推荐Tab）
 */
async function handleCategoryChange(categoryId: string | null): Promise<void> {
  console.log('[Home] 🔄 切换分类:', categoryId === null ? '推荐' : categoryId);
  activeCategoryId.value = categoryId;
  currentPage.value = 1;
  await loadRooms(false);
}

/**
 * 下拉刷新处理
 */
async function handlePullDownRefresh(): Promise<void> {
  isRefreshing.value = true;
  currentPage.value = 1;

  try {
    await loadRooms(false);
    await featuredCarouselRef.value?.refresh();
    authorityStripRef.value?.refresh();
    uni.showToast({ title: '刷新成功', icon: 'success' });
  } catch {
    uni.showToast({ title: '刷新失败', icon: 'none' });
  } finally {
    isRefreshing.value = false;
  }
}

/**
 * 上拉加载更多（触底）
 */
async function handleScrollToLower(): Promise<void> {
  if (isLoadingMore.value || !hasMore.value) return;

  currentPage.value += 1;
  await loadRooms(true);
}

/**
 * 直播卡片点击处理
 * @param room - 直播间数据
 */
function handleRoomClick(room: HomepageRoomItem): void {
  // 所有状态统一跳转到LiveView页面，由LiveView根据roomId自动处理
  uni.navigateTo({
    url: `/pages/app/live/LiveView?roomId=${room.id}`
  });
}

// ========== 生命周期 ==========
onMounted(async () => {
  // 初始化认证状态（等待完成以确保状态正确）
  await authStore.initializeAuth();
  
  // 🔴 P0：每次App启动，未登录时显示模态弹窗（可选择立即登录/稍后再说）
  if (!authStore.isAuthenticated) {
    uni.showModal({
      title: '登录提示',
      content: '登录后可享受收藏、点赞、订阅等完整功能',
      confirmText: '立即登录',
      cancelText: '稍后再说',
      success: (res) => {
        if (res.confirm) {
          uni.setStorageSync('loginRedirectPath', APP_HOME_PATH);
          uni.navigateTo({ url: APP_LOGIN_PATH });
        }
      }
    });
  }
  
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  const w = systemInfo.windowWidth || 375;
  gapPx.value = Math.max(2, Math.round((8 * w) / 750));
  
  // 动态测量分类tabs高度，确保滚动区域偏移正确
  nextTick(() => {
    try {
      const query = uni.createSelectorQuery();
      query.select('.sticky-categories').boundingClientRect(rect => {
        // 处理可能的数组返回值
        const actualRect = Array.isArray(rect) ? rect[0] : rect;
        if (actualRect && actualRect.height) {
          // 使用实际测量的px高度
          tabsHeight.value = Math.ceil(actualRect.height);
          console.log('[Home] 测量分类tabs高度:', tabsHeight.value, 'px');
        }
      }).exec();
    } catch (e) {
      // 测量失败时使用默认高度（80rpx ≈ 40px）
      tabsHeight.value = 40;
      console.warn('[Home] 分类tabs高度测量失败，使用默认值:', tabsHeight.value);
    }
  });

  loadPageData();
});

/** 页面显示时刷新分类Tab（用户可能在全部科室页修改了星标科室） */
onShow(() => {
  categoryTabsRef.value?.refresh();
});

// uni-app 下拉刷新生命周期（备用）
onPullDownRefresh(() => {
  handlePullDownRefresh().finally(() => {
    uni.stopPullDownRefresh();
  });
});

// uni-app 触底生命周期（备用）
onReachBottom(() => {
  handleScrollToLower();
});
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  background-color: var(--home-bg);
  position: relative;
}

.fixed-search {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
}

.header-gap {
  position: fixed;
  left: 0;
  right: 0;
  z-index: 998;
  /* 与页面背景一致：去油腻，避免搜索栏与分类栏之间出现第二条硬分割线 */
  background-color: var(--home-bg);
}

.sticky-categories {
  position: fixed;
  left: 0;
  right: 0;
  z-index: 998;
  /* 分隔由分类栏自身的极浅 border 承担，此处不再叠加 */
  background-color: var(--home-bg);
}

.main-content {
  position: fixed;
  left: 0;
  right: 0;
  /* 精确跟随 tabbar 高度：112rpx 内容区 + safe-area，消除盲区 */
  bottom: calc(112rpx + env(safe-area-inset-bottom));
  overflow: hidden;
  z-index: 1;
}

/* 内容区 flex 纵向布局：min-height 由 JS 计算撑满到 tabbar 上方 */
.content-fill {
  display: flex;
  flex-direction: column;
}

/* RoomCardGrid 根节点占满剩余高度（配合其内部 no-more 贴底） */
.grid-fill {
  flex: 1;
}

</style>
