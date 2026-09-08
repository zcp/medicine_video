<template>
  <view class="followed-experts-page consumer-layout">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="app-search-field search-input">
        <text class="iconfont icon-search"></text>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索我的关注"
          @input="handleSearch"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="handleClearSearch" />
        </view>
      </view>
    </view>

    <!-- 分组Tab -->
    <view class="tabs-container">
      <view class="tabs">
        <view
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text class="tab-label">{{ tab.label }}</text>
          <text v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</text>
        </view>
      </view>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换） -->
    <view
      v-for="(tab, idx) in tabs"
      :key="tab.key"
      class="follows-panel"
      v-show="activeIndex === idx"
    >
        <scroll-view
          class="experts-list"
          scroll-y
          :refresher-enabled="true"
          :refresher-triggered="refreshing"
          @refresherrefresh="onRefresh"
        >
          <!-- 骨架屏加载状态 -->
          <view v-if="loading && filteredListByTab(tab.key).length === 0" class="skeleton-list">
            <view v-for="i in 5" :key="i" class="skeleton-card">
              <view class="skeleton-avatar"></view>
              <view class="skeleton-info">
                <view class="skeleton-line skeleton-name"></view>
                <view class="skeleton-line skeleton-hospital"></view>
              </view>
              <view class="skeleton-btn"></view>
            </view>
          </view>

          <!-- 专家列表 -->
          <view v-else>
            <view
              v-for="item in filteredListByTab(tab.key)"
              :key="item.expert_id"
              class="expert-card"
              :class="{ 'is-live': item.live_status?.is_live }"
              @tap="handleCardClick(item)"
            >
              <!-- 直播中标识 -->
              <view v-if="item.live_status?.is_live" class="live-indicator">
                <view class="live-dot"></view>
              </view>

              <image
                v-if="!failedAvatarIds.has(item.expert_id)"
                class="expert-avatar"
                :src="getAvatarUrl(item.avatar_url)"
                mode="aspectFill"
                @error="(e) => handleAvatarError(item, e)"
              />
              <view v-else class="expert-avatar avatar-placeholder" />

              <view class="expert-info">
                <view class="name-row">
                  <text class="expert-name">{{ item.name }}</text>
                  <text v-if="item.title" class="expert-title">{{ item.title }}</text>
                </view>

                <view class="hospital-row">
                  <text v-if="item.hospital" class="hospital-name">{{ item.hospital }}</text>
                  <text v-if="item.hospital && (item.department_name ?? item.department)" class="separator">·</text>
                  <text v-if="item.department_name ?? item.department" class="department-name">{{ item.department_name ?? item.department }}</text>
                </view>

                <view v-if="item.live_status?.is_live" class="live-status">
                  <text class="live-badge">
                    <text class="live-pulse">●</text>
                    直播中
                  </text>
                  <text class="live-title">{{ item.live_status.title }}</text>
                </view>
              </view>

              <view class="action-btn" @tap.stop="handleUnfollow(item)">
                <text class="btn-text">已关注</text>
              </view>
            </view>

            <!-- 空状态 -->
            <view v-if="filteredListByTab(tab.key).length === 0" class="empty-state">
              <text class="iconfont icon-heart empty-icon"></text>
              <text class="empty-title">{{ emptyTitleByTab(tab.key) }}</text>
              <text class="empty-desc">{{ emptyDescByTab(tab.key) }}</text>
              <view v-if="tab.key === 'all'" class="empty-action" @tap="handleGoDiscover">
                <text class="action-text">去发现专家</text>
              </view>
            </view>
          </view>
        </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { requireAuth } from '@/utils/auth';
import { useFollowStore } from '@/store/follow';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import type { FollowedExpertItem } from '@/types/expertFollow';
import { DEFAULT_AVATAR } from '@/constants/assets';
import ClearButton from '@/components/app/ClearButton.vue';

const followStore = useFollowStore();
const { followedList, loading } = storeToRefs(followStore);

const refreshing = ref(false);
const searchKeyword = ref('');
const failedAvatarIds = ref<Set<string>>(new Set());

// Tab配置
const tabs = computed(() => {
  const liveCount = followedList.value.filter(item => item.live_status?.is_live).length;
  const allCount = followedList.value.length;

  return [
    { key: 'live', label: '正在直播', count: liveCount },
    { key: 'all', label: '全部关注', count: allCount }
  ] as const;
});

/**
 * 获取指定 Tab 的过滤列表（按 Tab 过滤 + 搜索关键词过滤）
 * @param tabKey live=正在直播 / all=全部关注
 */
function filteredListByTab(tabKey: 'live' | 'all'): FollowedExpertItem[] {
  let list = followedList.value;

  // 按Tab过滤
  if (tabKey === 'live') {
    list = list.filter(item => item.live_status?.is_live);
  }

  // 按搜索关键词过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    list = list.filter(item =>
      item.name.toLowerCase().includes(keyword) ||
      item.hospital?.toLowerCase().includes(keyword) ||
      (item.department_name ?? item.department)?.toLowerCase().includes(keyword)
    );
  }

  return list;
}

/**
 * 获取指定 Tab 的空状态标题
 * @param tabKey live=正在直播 / all=全部关注
 */
function emptyTitleByTab(tabKey: 'live' | 'all'): string {
  if (searchKeyword.value) {
    return '未找到相关专家';
  }
  if (tabKey === 'live') {
    return '暂无直播中的专家';
  }
  return '暂无关注';
}

/**
 * 获取指定 Tab 的空状态描述
 * @param tabKey live=正在直播 / all=全部关注
 */
function emptyDescByTab(tabKey: 'live' | 'all'): string {
  if (searchKeyword.value) {
    return '试试其他关键词';
  }
  if (tabKey === 'live') {
    return '关注的专家暂未开播';
  }
  return '快去关注你喜欢的专家吧';
}

/**
 * Tab 索引变化：更新本地筛选（仅本地过滤，不重新请求）
 */
function onTabActivated(): void {
  // 列表按 tab.key 在模板内过滤，无需额外逻辑
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabs.value.length,
  onTabActivated,
  0
);

onMounted(async () => {
  if (!requireAuth()) {
    return;
  }

  await loadExperts(false);
});

onShow(async () => {
  if (!requireAuth()) {
    return;
  }

  await loadExperts(true);
});

async function loadExperts(force: boolean) {
  try {
    await followStore.loadFollowedExperts(force);
    // 刷新列表后重置头像失败标记，给新数据一次重试机会
    failedAvatarIds.value.clear();
  } catch (error) {
    console.error('加载关注列表失败:', error);
    uni.showToast({ title: '加载失败', icon: 'none' });
  } finally {
    refreshing.value = false;
  }
}

/**
 * 获取头像URL（带降级）
 */
function getAvatarUrl(url: string | null | undefined): string {
  return url || DEFAULT_AVATAR;
}

/**
 * 头像加载失败处理
 */
function handleAvatarError(item: FollowedExpertItem, e?: any) {
  console.warn('[FollowsPage] 头像加载失败，使用默认头像');
  failedAvatarIds.value.add(item.expert_id);
  item.avatar_url = '';
  if (e?.target) {
    e.target.src = '';
  }
}

function onRefresh() {
  refreshing.value = true;
  loadExperts(true);
}

function handleSearch() {
  // 搜索逻辑由 filteredListByTab 计算属性处理
}

/**
 * 清除搜索关键词（接线：过滤由计算属性实时驱动，清空即恢复全量列表）
 */
function handleClearSearch() {
  searchKeyword.value = '';
}

/**
 * 点击专家卡片
 * - 如果正在直播：跳转到直播页面
 * - 否则：跳转到专家详情页
 */
function handleCardClick(item: FollowedExpertItem) {
  // 优先跳转到直播页面（如果正在直播）
  if (item.live_status?.is_live && item.live_status.room_id) {
    uni.navigateTo({
      url: `/pages/app/live/LiveView?roomId=${item.live_status.room_id}`
    });
    return;
  }

  // 跳转到专家详情页
  uni.navigateTo({
    url: `/pages/app/expert/detail?id=${item.expert_id}`
  });
}

function handleGoDiscover() {
  uni.switchTab({
    url: '/pages/app/tabbar/expert/index'
  });
}

async function handleUnfollow(item: FollowedExpertItem) {
  uni.showModal({
    title: '提示',
    content: `确定要取消关注 ${item.name} 吗？`,
    success: async (res) => {
      if (!res.confirm) return;

      try {
        await followStore.unfollowExpert(item.expert_id);
        uni.showToast({ title: '已取消关注', icon: 'success' });
      } catch (error) {
        console.error('取消关注失败:', error);
        uni.showToast({ title: '操作失败', icon: 'none' });
      }
    }
  });
}
</script>

<style lang="scss" scoped>
/* ============================================================
   色彩清洗说明：
   - #667eea / #764ba2（遗留蓝紫色）→ var(--home-primary)
   - #f5f5f5 / #ffffff（硬编码）→ var(--home-bg) / var(--home-card)
   - #333333 / #666666 / #999999 → 对应文字层级 token
   - border #f0f0f0 → rgba(17,24,39,0.04) 若隐若现
   - 动效 0.3s → 0.2s（200ms 统一规范）
   - 取关按钮热区 ~24px → min-height: 88rpx (≥44px)
   - 取关按钮激活态：灰色背景 → 品牌主色描边（ListItemAction 规范）
   ============================================================ */

.followed-experts-page {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: var(--home-bg);  /* tokens: was #f5f5f5 */
}

/* 搜索栏 */
.search-bar {
  background-color: var(--home-card);  /* tokens: was #ffffff */
  padding: var(--home-spacing-page) calc(var(--home-spacing-page) * 2);

  /* 叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊） */
  .search-input {
    .iconfont {
      font-size: 32rpx;
      color: var(--search-icon);
      margin-right: var(--home-spacing-inner);
    }

    input {
      flex: 1;
      font-size: var(--home-fs-card-title);  /* tokens: was 28rpx */
      color: var(--home-text1);  /* tokens: was #333333 */
      padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
    }
  }
}

/* Tab 切换 */
.tabs-container {
  background-color: var(--home-card);  /* tokens: was #ffffff */
  padding: 0 calc(var(--home-spacing-page) * 2);
  /* 若隐若现分割线：约 4% 对比度，远低于原 #f0f0f0 */
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.04);
}

.tabs {
  display: flex;
  gap: calc(var(--home-spacing-page) * 3);  /* 48rpx */
}

.tab-item {
  position: relative;
  padding: calc(var(--home-spacing-inner) * 2) 0;  /* 24rpx */
  display: flex;
  align-items: center;
  gap: 8rpx;
  cursor: pointer;

  .tab-label {
    font-size: var(--home-fs-tab);  /* tokens: was 28rpx */
    color: var(--home-text2);  /* tokens: was #666666 */
    transition: color 0.2s ease;  /* 200ms 统一 */
  }

  .tab-badge {
    min-width: 32rpx;
    height: 32rpx;
    line-height: 32rpx;
    padding: 0 8rpx;
    border-radius: var(--home-r-pill);  /* tokens */
    background-color: var(--home-bg);  /* tokens: was #f0f0f0 */
    color: var(--home-tabbar-inactive);  /* tokens: was #999999 */
    font-size: var(--home-fs-meta);  /* tokens: was 20rpx */
    text-align: center;
    transition: background-color 0.2s ease, color 0.2s ease;  /* 200ms 统一 */
  }

  &.active {
    .tab-label {
      color: var(--home-primary);  /* 色彩清洗：was #667eea */
      font-weight: 500;
    }

    .tab-badge {
      background-color: var(--home-primary);  /* 色彩清洗：was #667eea */
      color: var(--home-card);
    }

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 40rpx;
      height: 4rpx;
      background-color: var(--home-primary);  /* 色彩清洗：was #667eea */
      border-radius: 2rpx;
    }
  }
}

/* 内容区 Tab 面板：flex 撑满剩余高度（根容器 100vh + flex column） */
.follows-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 列表滚动容器（每个 swiper-item 内独立滚动） */
.experts-list {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* 骨架屏 */
.skeleton-list {
  background-color: var(--home-card);  /* tokens */
}

.skeleton-card {
  display: flex;
  align-items: center;
  padding: calc(var(--home-spacing-inner) * 2) calc(var(--home-spacing-page) * 2);
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.04);  /* 若隐若现 */
}

.skeleton-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: linear-gradient(
    90deg,
    var(--home-bg) 25%,
    rgba(229, 231, 235, 0.5) 50%,
    var(--home-bg) 75%
  );  /* tokens 推衍 */
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  margin-right: calc(var(--home-spacing-inner) * 2);
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--home-spacing-page);
}

.skeleton-line {
  height: 28rpx;
  border-radius: var(--home-r-md);  /* tokens */
  background: linear-gradient(
    90deg,
    var(--home-bg) 25%,
    rgba(229, 231, 235, 0.5) 50%,
    var(--home-bg) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-name { width: 200rpx; }
.skeleton-hospital { width: 300rpx; }

.skeleton-btn {
  width: 120rpx;
  height: 56rpx;
  border-radius: var(--home-r-pill);  /* tokens */
  background: linear-gradient(
    90deg,
    var(--home-bg) 25%,
    rgba(229, 231, 235, 0.5) 50%,
    var(--home-bg) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 专家列表项——去卡片化：通栏背景 + 极低对比分割线 + 留白分组 */
.expert-card {
  position: relative;
  display: flex;
  align-items: center;
  background-color: var(--home-card);  /* tokens: was #ffffff */
  padding: calc(var(--home-spacing-inner) * 2) calc(var(--home-spacing-page) * 2);
  /* 若隐若现分割线（~4% 对比）- 去卡片化替代厚边框盒 */
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.04);
  transition: background-color 0.2s ease;  /* 200ms 统一 */
  min-height: 120rpx;  /* 保证整行点击体验 */

  &.is-live {
    /* 色彩清洗：去除红色渐变，改为极轻品牌色点缀（3% opacity） */
    background: linear-gradient(
      90deg,
      rgba(15, 118, 110, 0.03) 0%,
      var(--home-card) 100%
    );
  }

  &:active {
    background-color: var(--home-bg);  /* tokens: was #f9f9f9 */
  }
}

/* 直播指示点（保留功能性红色语义色）*/
.live-indicator {
  position: absolute;
  top: calc(var(--home-spacing-inner) * 2);
  left: 8rpx;
  width: 16rpx;
  height: 16rpx;

  .live-dot {
    width: 100%;
    height: 100%;
    background-color: var(--color-danger);  /* tokens: 语义功能色 */
    border-radius: 50%;
    animation: live-pulse 2s infinite;
  }
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(1.2); }
}

/* Avatar：对齐 tokens（圆角/背景/间距）*/
.expert-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;  /* Avatar 圆形 */
  margin-right: calc(var(--home-spacing-inner) * 2);  /* 24rpx */
  flex-shrink: 0;
  background-color: var(--home-bg);  /* tokens: was #f0f0f0 */
}

.avatar-placeholder {
  background: linear-gradient(180deg, #eff2f6 0%, #e6ebf2 100%);
}

/* 专家信息区 */
.expert-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;  /* 防文字溢出 */
}

.name-row {
  display: flex;
  align-items: center;
  gap: var(--home-spacing-inner);

  .expert-name {
    font-size: var(--home-fs-card-title);  /* tokens: was 30rpx */
    font-weight: 500;
    color: var(--home-text1);  /* tokens: was #333333 */
  }

  .expert-title {
    font-size: var(--home-fs-meta);  /* tokens: was 24rpx */
    color: var(--home-text2);  /* tokens: was #666666 */
  }
}

.hospital-row {
  display: flex;
  align-items: center;
  gap: 8rpx;

  .hospital-name,
  .department-name {
    font-size: var(--home-fs-meta);  /* tokens: was 24rpx */
    color: var(--home-tabbar-inactive);  /* tokens: was #999999 */
  }

  .separator {
    font-size: var(--home-fs-meta);
    color: var(--home-border);  /* tokens: was #cccccc */
  }
}

/* 直播状态行 */
.live-status {
  display: flex;
  align-items: center;
  gap: var(--home-spacing-inner);

  .live-badge {
    display: flex;
    align-items: center;
    gap: 6rpx;
    padding: 4rpx var(--home-spacing-inner);
    border-radius: var(--home-r-md);  /* tokens */
    font-size: var(--home-fs-meta); /* tokens */
    color: var(--home-card);
    background-color: var(--color-danger);  /* tokens: 功能性语义色 */

    .live-pulse {
      display: inline-block;
      animation: pulse-text 1.5s infinite;
    }
  }

  .live-title {
    font-size: var(--home-fs-meta);
    color: var(--home-text2);  /* tokens */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

@keyframes pulse-text {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.6; }
}

/* ============================================================
   ListItemAction：取关/已关注按钮
   规范：激活态（已关注）使用品牌主色描边，热区 >= 88rpx（44px）
   色彩清洗：was background #e5e5e5 / text #999999（灰色无归属）
   ============================================================ */
.action-btn {
  flex-shrink: 0;
  min-width: 120rpx;
  min-height: 88rpx;  /* 热区修复：was ~48rpx (~24px)，现在 ≥ 44px */
  padding: 0 var(--home-spacing-module);
  border-radius: var(--home-r-pill);  /* tokens: was 24rpx */
  /* 激活态（已关注）：品牌主色描边，克制不抢夺主信息 */
  border: 1.5rpx solid var(--home-primary);
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s ease;  /* 200ms 统一 */

  .btn-text {
    font-size: var(--home-fs-meta);  /* tokens: was 24rpx */
    color: var(--home-primary);  /* 色彩清洗：was #999999，现对齐品牌主色 */
    font-weight: 500;
  }

  &:active {
    opacity: 0.7;
  }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx calc(var(--home-spacing-page) * 4);

  .empty-icon {
    font-size: 120rpx;
    color: var(--home-border);  /* tokens: was #cccccc */
    margin-bottom: calc(var(--home-spacing-page) * 2);
  }

  .empty-title {
    font-size: var(--home-fs-section);  /* tokens: was 32rpx */
    color: var(--home-text2);  /* tokens: was #666666 */
    margin-bottom: var(--home-spacing-page);
  }

  .empty-desc {
    font-size: var(--home-fs-card-title);  /* tokens: was 28rpx */
    color: var(--home-tabbar-inactive);  /* tokens: was #999999 */
    margin-bottom: calc(var(--home-spacing-page) * 3);
    text-align: center;
  }

  /* PrimaryButton（Pill）：色彩清洗核心 - was 蓝紫渐变 #667eea/#764ba2 */
  .empty-action {
    padding: var(--home-spacing-module) calc(var(--home-spacing-page) * 3);
    border-radius: var(--home-r-pill);  /* tokens */
    background: var(--home-primary);  /* 色彩清洗：was linear-gradient(#667eea, #764ba2) */
    box-shadow: var(--home-fab-shadow);  /* tokens: was rgba(102,126,234,0.3) */
    transition: opacity 0.2s ease, transform 0.2s ease;  /* 200ms 统一 */

    .action-text {
      font-size: var(--home-fs-card-title);  /* tokens: was 28rpx */
      color: var(--home-card);
      font-weight: 500;
    }

    &:active {
      opacity: 0.85;
      transform: scale(0.97);
    }
  }
}
</style>

