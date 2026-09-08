<template>
  <view class="search-results-page">
    <!-- 自定义导航栏（参考B站样式） -->
    <SearchNavBar
      v-model:keyword="keyword"
      :auto-focus="false"
      @search="handleSearch"
      @back="handleBack"
    />
    
    <!-- 内容区（需要上边距以防止被导航栏遮挡） -->
    <view class="content-wrapper" :style="{ paddingTop: navbarHeight + 'px' }">      <!-- 搜索建议（输入时显示） -->
      <view v-if="showSuggestions && keyword.trim()" class="suggestion-list">
        <view
          v-for="(item, index) in searchStore.suggestions"
          :key="index"
          class="suggestion-item"
          @tap="handleSuggestionClick(item)"
        >
          <text class="suggestion-text">{{ item }}</text>
        </view>
        <view
          v-if="searchStore.suggestions.length === 0 && !searchStore.suggestionsLoading"
          class="suggestion-item"
          @tap="handleSearch()"
        >
          <text class="suggestion-text">搜索 "{{ keyword.trim() }}"</text>
        </view>
      </view>

      <!-- 搜索结果（默认显示） -->
      <template v-else>
        <!-- Tab切换（移除"全部"）：点击 ↔ swiper 滑动双向联动 -->
        <view class="tabs-wrapper">
          <view
            v-for="(tab, idx) in tabs"
            :key="tab.key"
            class="tab-item"
            :class="{ 'tab-item--active': activeIndex === idx }"
            @tap="handleTabTap(idx)"
          >
            <text class="tab-text">{{ tab.label }}</text>
            <view v-if="activeIndex === idx" class="tab-indicator"></view>
          </view>
        </view>

        <!-- 内容区：swiper 承载三个 Tab，左右滑动切换 -->
        <swiper
          class="results-swiper"
          :style="{ height: swiperHeight + 'px' }"
          :current="activeIndex"
          @change="handleSwiperChange"
        >
          <swiper-item v-for="tab in tabs" :key="tab.key" class="results-swiper-item">
            <scroll-view
              class="results-scroll"
              scroll-y
              @scrolltolower="handleLoadMore(tab.key)"
            >
              <!-- 加载中状态 -->
              <view v-if="searchStore.isSearching && searchStore.searchResults.length === 0" class="loading-state">
                <text class="loading-text">搜索中...</text>
              </view>

              <!-- 搜索结果 -->
              <view v-else-if="tabResults(tab.key).length > 0" class="results-list">
                <!-- 结果数量提示 -->
                <view class="results-count">
                  共找到 {{ tabResults(tab.key).length }} 个结果
                </view>

                <!-- 结果列表 -->
                <template v-for="item in tabResults(tab.key)" :key="item.id">
                  <!-- 专家：使用ExpertCard（添加容器提供padding） -->
                  <view v-if="item.type === 'expert'" class="expert-card-wrapper">
                    <ExpertCard
                      :avatar="item.cover_url || '/static/default-avatar.png'"
                      :name="item.title"
                      :title="item.metadata?.title || ''"
                      :hospital="item.metadata?.hospital || ''"
                      :specialization="toSpecialization(item.metadata?.expertise_areas)"
                      :is-following="followStore.isFollowed(item.id)"
                      @click="handleResultClick(item)"
                      @toggle-follow="handleExpertFollow(item)"
                    />
                  </view>
                  <!-- 其他类型：使用SearchResultCard -->
                  <SearchResultCard
                    v-else
                    :item="item"
                    @click="handleResultClick"
                  />
                </template>

                <!-- 加载更多提示 -->
                <view v-if="searchStore.hasMore" class="load-more-tip">
                  <text class="tip-text">{{ searchStore.isSearching ? '加载中...' : '上拉加载更多' }}</text>
                </view>

                <!-- 没有更多数据提示 -->
                <view v-else class="no-more-tip">
                  <text class="tip-text">没有更多了</text>
                </view>
              </view>

              <!-- 空状态：显示推荐内容 -->
              <view v-else class="empty-with-recommend">
                <view class="empty-state">
                  <text class="iconfont icon-search empty-icon"></text>
                  <text class="empty-text">没有找到相关结果</text>
                  <text class="empty-hint">为你推荐以下内容</text>
                </view>

                <!-- 推荐内容（根据Tab显示对应类型） -->
                <view v-if="tabRecommendations(tab.key).length > 0" class="recommend-section">
                  <view class="section-title">{{ tabRecommendTitle(tab.key) }}</view>
                  <!-- 推荐列表 -->
                  <template v-for="item in tabRecommendations(tab.key)" :key="item.id">
                    <!-- 专家：使用ExpertCard（添加容器） -->
                    <view v-if="item.type === 'expert'" class="expert-card-wrapper">
                      <ExpertCard
                        :avatar="item.cover_url || '/static/default-avatar.png'"
                        :name="item.title"
                        :title="item.metadata?.title || ''"
                        :hospital="item.metadata?.hospital || ''"
                        :specialization="toSpecialization(item.metadata?.expertise_areas)"
                        :is-following="followStore.isFollowed(item.id)"
                        @click="handleResultClick(item)"
                        @toggle-follow="handleExpertFollow(item)"
                      />
                    </view>
                    <!-- 其他类型：使用SearchResultCard -->
                    <SearchResultCard
                      v-else
                      :item="item"
                      @click="handleResultClick"
                    />
                  </template>
                </view>
              </view>
            </scroll-view>
          </swiper-item>
        </swiper>
      </template>
  </view>
</view>
</template>

<script setup lang="ts">
/**
 * 搜索结果页面
 * @description 展示搜索结果，支持Tab切换、加载更多、无结果推荐
 */
import { ref, onMounted, watch, nextTick } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import SearchNavBar from '@/components/app/SearchNavBar.vue';
import SearchResultCard from '@/components/app/SearchResultCard.vue';
import ExpertCard from '@/components/expert/ExpertCard.vue';
import { useSearchStore } from '@/store/search';
import { useFollowStore } from '@/store/follow';
import { getHomepageRooms } from '@/api/homepage';
import { getExperts } from '@/api/expert';
import { getBrands } from '@/api/brand';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import { rpx2px, getWindowHeight } from '@/composables/usePageLayout';
import type { SearchResultItem } from '@/api/search';
import type { SearchTabType, SearchTab } from '@/types/search';
import type { HomepageRoomItem } from '@/types/homepage';
import type { Expert } from '@/types/expert';
import type { Brand } from '@/types/brand';
import { logger } from '@/utils/logger';

/** 搜索关键词 */
const keyword = ref<string>('');

/** 是否显示搜索建议 */
const showSuggestions = ref(false);

/** 标记：是否正在通过点击建议执行搜索（用于跳过 watch 中自动显示建议的逻辑） */
const isClickingSuggestion = ref(false);

/** 当前Tab（移除all） */
const currentTab = ref<SearchTabType>('room');

/** 搜索Store */
const searchStore = useSearchStore();

/** 关注Store */
const followStore = useFollowStore();

/** 导航栏高度（px，包含状态栏） */
const navbarHeight = ref(88);

// 获取系统信息
try {
  const sysInfo = uni.getSystemInfoSync();
  const statusBarHeight = sysInfo.statusBarHeight || 0;
  navbarHeight.value = statusBarHeight + 44; // 状态栏 + 导航栏高度(44px)
} catch (e) {
  console.error('[搜索结果] 获取系统信息失败:', e);
  navbarHeight.value = 88; // 默认值
}

/** 内容区 swiper 高度（px）：视口 - 导航栏 - Tab 头 */
const swiperHeight = ref(500);

/**
 * 测量 swiper 高度
 * @description Tab 头高度动态测量（padding 布局无固定高），失败时回退 88rpx
 */
function measureSwiperHeight(): void {
  nextTick(() => {
    try {
      const query = uni.createSelectorQuery();
      query.select('.tabs-wrapper').boundingClientRect(rect => {
        const r = Array.isArray(rect) ? rect[0] : rect;
        const tabsH = r?.height || rpx2px(88);
        swiperHeight.value = Math.max(0, getWindowHeight() - navbarHeight.value - tabsH);
      }).exec();
    } catch (e) {
      swiperHeight.value = Math.max(0, getWindowHeight() - navbarHeight.value - rpx2px(88));
    }
  });
}

// 建议区显示状态变化时（收起建议 → 显示 Tab），重测 swiper 高度
watch(showSuggestions, (v) => {
  if (!v) measureSwiperHeight();
});

// H5 端窗口尺寸变化时重测
if (typeof window !== 'undefined' && window.addEventListener) {
  window.addEventListener('resize', measureSwiperHeight);
}

/** 推荐直播间 */
const recommendRooms = ref<SearchResultItem[]>([]);

/** 推荐专家 */
const recommendExperts = ref<SearchResultItem[]>([]);

/** 推荐品牌 */
const recommendBrands = ref<SearchResultItem[]>([]);

/** Tab配置（移除"全部"） */
const tabs: SearchTab[] = [
  { key: 'room', label: '直播间', apiType: 'room' },
  { key: 'expert', label: '专家', apiType: 'expert' },
  { key: 'brand', label: '品牌', apiType: 'brand' }
];

/**
 * Tab 索引 ↔ 业务逻辑联动
 * @description 点击 Tab 头 / 滑动 swiper 均会触发；设置 currentTab 并重新搜索（与原有"点击即重搜"行为一致）
 */
function onTabActivated(idx: number): void | Promise<void> {
  const tab = tabs[idx];
  if (!tab) return;
  currentTab.value = tab.key;

  // 如果有搜索关键词，重新搜索（带类型筛选）
  if (keyword.value && keyword.value.trim()) {
    return performSearch(keyword.value, 'swiper');
  }
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap, handleSwiperChange } = useSwiperTabs(
  tabs.length,
  onTabActivated,
  0
);

/**
 * 获取指定 Tab 的过滤结果
 * @description 每个 swiper-item 内按 tab.key 独立取该类型结果
 * 用 Map 缓存避免模板多次调用时重复 filter（数据源变化时失效）
 * @param tabKey Tab 类型
 */
const tabResultsCache = new Map<SearchTabType, SearchResultItem[]>();
watch(
  () => searchStore.searchResults,
  () => tabResultsCache.clear(),
  { flush: 'sync' }
);
function tabResults(tabKey: SearchTabType): SearchResultItem[] {
  const cached = tabResultsCache.get(tabKey);
  if (cached) return cached;

  const filtered = searchStore.searchResults.filter(item => item.type === tabKey);

  // 添加调试日志：查看原始数据
  if (filtered.length > 0 && tabKey === 'expert') {
    console.log('[搜索结果] 专家原始数据:', JSON.stringify(filtered[0], null, 2));
  }

  // 直接返回后端结果，不做标题解析/占位降级（后端返回真实 metadata，无数据时组件空值不渲染）
  tabResultsCache.set(tabKey, filtered);
  return filtered;
}

/**
 * 获取指定 Tab 的推荐内容
 * @param tabKey Tab 类型
 */
function tabRecommendations(tabKey: SearchTabType): SearchResultItem[] {
  if (tabKey === 'room') {
    return recommendRooms.value;
  } else if (tabKey === 'expert') {
    return recommendExperts.value;
  } else if (tabKey === 'brand') {
    return recommendBrands.value;
  }
  return [];
}

/**
 * 获取指定 Tab 的推荐标题
 * @param tabKey Tab 类型
 */
function tabRecommendTitle(tabKey: SearchTabType): string {
  if (tabKey === 'room') return '推荐直播间';
  if (tabKey === 'expert') return '推荐专家';
  if (tabKey === 'brand') return '推荐品牌';
  return '推荐内容';
}

/**
 * 页面加载
 * @description 从搜索首页跳转过来时，直接显示搜索结果，不显示建议列表
 */
onLoad(async (options) => {
  console.log('[TRACE-RESULTS] onLoad 触发, options:', JSON.stringify(options));
  if (options?.keyword) {
    const decodedKeyword = decodeURIComponent(options.keyword as string);
    console.log('[TRACE-RESULTS] onLoad 收到关键词:', decodedKeyword);
    // 阻止 watch 将 showSuggestions 设为 true，确保直接展示搜索结果
    isClickingSuggestion.value = true;
    showSuggestions.value = false;
    keyword.value = decodedKeyword;
    isClickingSuggestion.value = false;
    console.log('[TRACE-RESULTS] onLoad 状态: showSuggestions=', showSuggestions.value, 'keyword=', keyword.value);
    
    // 执行搜索
    await performSearch(decodedKeyword, 'onLoad');
  } else {
    console.log('[TRACE-RESULTS] onLoad 无关键词参数，显示建议列表');
  }
});

/**
 * 页面挂载
 */
onMounted(() => {
  logger.info('[SearchResults] 页面已加载');
  loadAllRecommendations();
  followStore.loadFollowedExperts().catch(error => {
    logger.error('[SearchResults] 加载关注列表失败:', error);
  });

  // 测量 swiper 高度（Tab 头渲染后）
  measureSwiperHeight();
});

/**
 * 监听输入变化，输入时显示建议（点击建议项时不触发）
 * ⚠️ 使用 flush: 'sync' 确保守卫 isClickingSuggestion 在 keyword 变更的同一时刻生效，
 * 否则 Vue 3 默认 flush:'pre' 会延迟到 microtask 才执行回调，此时守卫已被复位。
 */
watch(keyword, (newVal, oldVal) => {
  console.log('[TRACE-RESULTS] watch(keyword) 触发:', {
    newVal: newVal ? `"${newVal}"` : '(空)',
    oldVal: oldVal ? `"${oldVal}"` : '(空)',
    isClickingSuggestion: isClickingSuggestion.value,
    showSuggestions: showSuggestions.value
  });
  if (isClickingSuggestion.value) {
    console.log('[TRACE-RESULTS] watch 被 isClickingSuggestion 守卫拦截，跳过');
    return;
  }
  if (newVal && newVal.trim()) {
    console.log('[TRACE-RESULTS] watch 设置 showSuggestions=true');
    showSuggestions.value = true;
    searchStore.fetchSuggestions(newVal);
    searchStore.loadRecommendations(newVal.trim());
  } else {
    console.log('[TRACE-RESULTS] watch 设置 showSuggestions=false');
    showSuggestions.value = false;
  }
}, { flush: 'sync' });

/**
 * 点击建议词 → 搜索
 */
const handleSuggestionClick = (suggestionKeyword: string) => {
  console.log('[TRACE-RESULTS] handleSuggestionClick 被调用:', suggestionKeyword);
  // 先关建议+设守卫，再改 keyword，防止 watch 重新打开建议
  showSuggestions.value = false;
  isClickingSuggestion.value = true;
  keyword.value = suggestionKeyword;
  isClickingSuggestion.value = false;
  console.log('[TRACE-RESULTS] handleSuggestionClick 调用 performSearch');
  performSearch(suggestionKeyword, 'handleSuggestionClick');
};

/**
 * 搜索按钮 / 键盘确认
 */
const handleSearch = (searchKeyword?: string) => {
  console.log('[TRACE-RESULTS] handleSearch 被调用, 参数类型:', typeof searchKeyword, '参数值:', searchKeyword);
  const raw = typeof searchKeyword === 'string' ? searchKeyword : keyword.value;
  const kw = (raw || '').trim();
  console.log('[TRACE-RESULTS] handleSearch 解析后关键词:', kw);
  if (!kw || kw.length < 2) {
    console.log('[TRACE-RESULTS] handleSearch 校验失败，关键词过短');
    uni.showToast({ title: '请输入至少2个字符', icon: 'none', duration: 2000 });
    return;
  }
  // 先关建议+设守卫，再改 keyword，防止 watch 重新打开建议
  showSuggestions.value = false;
  isClickingSuggestion.value = true;
  keyword.value = kw;
  isClickingSuggestion.value = false;
  console.log('[TRACE-RESULTS] handleSearch 调用 performSearch');
  performSearch(kw, 'handleSearch');
};

/**
 * 执行搜索
 * @param searchKeyword 搜索关键词
 * @param caller 调用来源（用于调试）
 */
const performSearch = async (searchKeyword: string, caller: string = 'unknown') => {
  console.log(`[TRACE-RESULTS] performSearch 被调用, caller=${caller}, keyword="${searchKeyword}", currentTab=${currentTab.value}`);
  try {
    // 默认搜索当前Tab类型
    const tab = tabs.find(t => t.key === currentTab.value);
    await searchStore.performSearch(searchKeyword, tab?.apiType);
    logger.info(`[SearchResults] 搜索完成: "${searchKeyword}", 结果数: ${searchStore.totalResults}`);
  } catch (error) {
    logger.error('[SearchResults] 搜索失败:', error);
  }
};

/**
 * 获取直播间专家信息（三级降级策略）
 * @description 采用和首页相同的策略
 */
/**
 * 获取直播间专家信息
 * @description 使用首页后端返回的 host（_select_host 已做无专家创建者兜底），
 * 不做标题解析/占位降级；host 缺失时返回 null，卡片空值不渲染
 */
const getExpertInfo = (room: HomepageRoomItem) => {
  if (room.host?.name) {
    return {
      name: room.host.name,
      title: room.host.title,
      hospital: room.host.hospital,
      avatar: room.host.avatar_url || room.host.avatar || undefined
    };
  }
  return null;
};

const toSpecialization = (raw?: string): string[] =>
  (raw || '')
    .split(',')
    .map((s: string) => s.trim())
    .filter((s: string) => !!s);

/**
 * 加载所有推荐内容（直播间、专家、品牌）
 */
const loadAllRecommendations = async () => {
  try {
    // 加载推荐直播间（8条）
    const roomsRes = await getHomepageRooms({ page: 1, size: 8, sort: 'heat:desc' });
    if (roomsRes.code === 200 && roomsRes.data) {
      recommendRooms.value = roomsRes.data.items.map((room: HomepageRoomItem) => {
        const expertInfo = getExpertInfo(room);
        return {
          id: room.id,
          type: 'room' as const,
          title: room.title,
          cover_url: room.cover_url || undefined,
          match_score: 0,
          metadata: {
            status: mapHomepageStatusToSearchStatus(room.live_status),
            start_time: room.status_data?.start_time || undefined,
            expert_name: expertInfo?.name,
            expert_avatar: expertInfo?.avatar,
            expert_title: expertInfo?.title || undefined,
            expert_hospital: expertInfo?.hospital || undefined
          }
        };
      });
    }
    
    // 加载推荐专家（8条）
    const expertsRes = await getExperts({ page: 1, size: 8 });
    if (expertsRes.code === 200 && expertsRes.data) {
      recommendExperts.value = expertsRes.data.items.map((expert: Expert) => ({
        id: expert.id,
        type: 'expert' as const,
        title: expert.name,
        subtitle: expert.bio || undefined,
        cover_url: expert.avatar_url || undefined,
        match_score: 0,
        metadata: {
          title: expert.title || undefined,
          hospital: expert.hospital || undefined,
          expertise_areas: expert.expertise_areas || undefined
        }
      }));
    }
    
    // 加载推荐品牌（8条）
    const brandsRes = await getBrands({ page: 1, size: 8 });
    if (brandsRes.code === 200 && brandsRes.data) {
      recommendBrands.value = brandsRes.data.items.map((brand: Brand) => ({
        id: brand.id,
        type: 'brand' as const,
        title: brand.name,
        subtitle: brand.description || undefined,
        cover_url: brand.logo_url || undefined,
        match_score: 0,
        metadata: {}
      }));
    }
    
    logger.info('[SearchResults] 推荐内容加载完成');
  } catch (error) {
    logger.error('[SearchResults] 加载推荐内容失败:', error);
  }
};

/**
 * 映射首页状态到搜索状态
 * @description 值域与 SearchResultItem.metadata.status 类型一致（scheduled/live/finished/ended）
 */
const mapHomepageStatusToSearchStatus = (status: string): 'scheduled' | 'live' | 'finished' | 'ended' => {
  if (status === 'live') return 'live';
  if (status === 'scheduled') return 'scheduled';
  if (status === 'replay') return 'finished';
  return 'ended';
};

/**
 * 加载更多
 * @param tabKey 当前触发的 Tab（swiper 每个 item 内独立触底）
 */
const handleLoadMore = async (tabKey: SearchTabType = currentTab.value) => {
  if (searchStore.isSearching || !searchStore.hasMore) {
    return;
  }

  const tab = tabs.find(t => t.key === tabKey);
  try {
    await searchStore.loadMore(tab?.apiType);
    logger.info('[SearchResults] 加载更多完成');
  } catch (error) {
    logger.error('[SearchResults] 加载更多失败:', error);
  }
};

/**
 * 搜索结果点击
 * @description 统一跳转逻辑，与首页保持一致：
 * - 直播间：使用 /pages/app/live/LiveView?roomId=xxx（驼峰命名）
 * - 专家详情：使用 /pages/app/expert/detail?id=xxx
 * - 品牌详情：使用 /pages/app/brand/detail?id=xxx
 */
const handleResultClick = (item: SearchResultItem) => {
  // 添加调试日志
  console.log('[搜索结果] 点击项目:', {
    type: item.type,
    id: item.id,
    title: item.title
  });
  
  if (item.type === 'room') {
    // 直播间：使用 app 版本的 LiveView，参数名为 roomId（驼峰）
    // 与首页跳转逻辑保持一致
    const url = `/pages/app/live/LiveView?roomId=${item.id}`;
    console.log('[搜索结果] 跳转直播间:', url);
    uni.navigateTo({ url });
  } else if (item.type === 'expert') {
    // 专家：使用 id 参数（expert/detail.vue 期望的参数名）
    const url = `/pages/app/expert/detail?id=${item.id}`;
    console.log('[搜索结果] 跳转专家详情:', url);
    uni.navigateTo({ url });
  } else if (item.type === 'brand') {
    // 品牌：使用 id 参数（brand/detail.vue 期望的参数名）
    const url = `/pages/app/brand/detail?id=${item.id}`;
    console.log('[搜索结果] 跳转品牌详情:', url);
    uni.navigateTo({ url });
  }
};

/**
 * 专家关注切换
 */
const handleExpertFollow = async (item: SearchResultItem) => {
  try {
    const expertId = item.id;
    const isCurrentlyFollowed = followStore.isFollowed(expertId);
    
    if (isCurrentlyFollowed) {
      // 取消关注
      await followStore.unfollowExpert(expertId);
      uni.showToast({
        title: '已取消关注',
        icon: 'success',
        duration: 1500
      });
      logger.info(`[SearchResults] 取消关注专家: ${item.title}`);
    } else {
      // 关注
      await followStore.followExpert(expertId);
      uni.showToast({
        title: '关注成功',
        icon: 'success',
        duration: 1500
      });
      logger.info(`[SearchResults] 关注专家: ${item.title}`);
    }
  } catch (error: any) {
    logger.error('[SearchResults] 关注操作失败:', error);
    uni.showToast({
      title: error.message || '操作失败，请重试',
      icon: 'none',
      duration: 2000
    });
  }
};
/**
 * 返回按钮
 */
const handleBack = () => {
  uni.navigateBack({
    fail: () => {
      // 如果返回失败，跳转到搜索首页
      uni.redirectTo({
        url: '/pages/app/search/index'
      });
    }
  });
};
</script>

<style scoped lang="scss">
.search-results-page {
  min-height: 100vh;
  background: #F5F5F5;
}

.content-wrapper {
  min-height: 100vh;
}

.tabs-wrapper {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #EBEBEB;
}

.tab-item {
  position: relative;
  padding: 24rpx 32rpx;
  cursor: pointer;
}

.tab-text {
  font-size: 28rpx;
  color: #666;
  transition: color 0.2s;
}

.tab-item--active .tab-text {
  color: #1677FF;
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #1677FF;
  border-radius: 2rpx;
}

/* 内容区 swiper：定高由 JS 计算（视口 - 导航栏 - Tab头） */
.results-swiper {
  width: 100%;
}

.results-swiper-item {
  height: 100%;
}

/* 每个 Tab 独立的垂直滚动区 */
.results-scroll {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.results-list {
  background: #fff;
}

.results-count {
  padding: 16rpx 32rpx;
  font-size: 24rpx;
  color: #999;
}

.load-more-tip,
.no-more-tip {
  padding: 32rpx 0;
  text-align: center;
}

.tip-text {
  font-size: 24rpx;
  color: #999;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-with-recommend {
  padding: 32rpx 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0 40rpx;
}

.empty-icon {
  font-size: 120rpx;
  color: #D9D9D9;
  margin-bottom: 32rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #999;
  margin-bottom: 16rpx;
}

.empty-hint {
  font-size: 28rpx;
  color: #BFBFBF;
}

.recommend-section {
  margin-top: 32rpx;
  background: #fff;
}

.section-title {
  padding: 16rpx 32rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.expert-card-wrapper {
  padding: 0 32rpx;
  background: #fff;
}

.suggestion-list {
  background: #fff;
  min-height: 100vh;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #f5f5f5;

  &:active {
    background: #f5f5f5;
  }
}

.suggestion-text {
  font-size: 28rpx;
  color: #333;
}
</style>
