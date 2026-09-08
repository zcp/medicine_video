<template>
  <view class="room-card-grid">
    <!-- 骨架屏 -->
    <view v-if="isLoading" class="skeleton-grid">
      <view v-for="i in 4" :key="i" class="skeleton-card">
        <view class="skeleton-cover" />
        <view class="skeleton-info">
          <view class="skeleton-title" />
          <view class="skeleton-desc" />
        </view>
      </view>
    </view>

    <!-- 模块级 Tab：正在直播 / 预告 / 回放（无标题） -->
    <view v-else class="cards-wrapper">
      <view class="section">
        <view class="module-tabs">
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeIndex === 0 }"
            @tap="handleTabTap(0)"
          >
            <view class="module-tab-inner">
              <view v-if="liveCount > 0" class="tab-badge-dot" />
              <text class="module-tab-text">正在直播</text>
            </view>
            <view v-if="activeIndex === 0" class="module-tab-indicator" />
          </view>
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeIndex === 1 }"
            @tap="handleTabTap(1)"
          >
            <text class="module-tab-text">预告</text>
            <view v-if="activeIndex === 1" class="module-tab-indicator" />
          </view>
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeIndex === 2 }"
            @tap="handleTabTap(2)"
          >
            <text class="module-tab-text">回放</text>
            <view v-if="activeIndex === 2" class="module-tab-indicator" />
          </view>
        </view>

        <!-- 内容区：swiper 承载三个 Tab（自适应高度 = 当前激活 panel 高度） -->
        <swiper
          class="module-swiper"
          :style="{ height: swiperHeight + 'px' }"
          :current="activeIndex"
          @change="handleSwiperChange"
        >
          <!-- 正在直播 -->
          <swiper-item class="module-swiper-item">
            <view class="tab-panel tab-panel--live">
              <view v-if="liveList.length === 0" class="empty-section empty-live">
                <text class="empty-section-text">暂无直播</text>
                <text class="empty-hint">敬请期待更多精彩内容</text>
                <view class="empty-actions">
                  <view class="empty-btn" @tap.stop="handleTabTap(1)">
                    <text class="empty-btn-text">看预告</text>
                  </view>
                  <view class="empty-btn empty-btn-secondary" @tap.stop="handleTabTap(2)">
                    <text class="empty-btn-text">看回放</text>
                  </view>
                </view>
                <text class="empty-hint">或下拉刷新获取最新直播</text>
              </view>
              <view v-else class="grid-container grid-double">
                <view v-for="room in liveList" :key="room.id" class="card-item">
                  <RoomCard :room="room" :is-mobile="true" :show-description="false" @click="handleCardClick(room)" />
                </view>
              </view>
            </view>
          </swiper-item>

          <!-- 预告 -->
          <swiper-item class="module-swiper-item">
            <view class="tab-panel tab-panel--scheduled">
              <view v-if="scheduledList.length === 0" class="empty-section empty-live">
                <text class="empty-section-text">暂无预告</text>
                <text class="empty-hint">敬请期待更多精彩内容</text>
                <view class="empty-actions">
                  <view class="empty-btn" @tap.stop="handleTabTap(2)">
                    <text class="empty-btn-text">看回放</text>
                  </view>
                  <view class="empty-btn empty-btn-secondary" @tap.stop="handleTabTap(0)">
                    <text class="empty-btn-text">看直播</text>
                  </view>
                </view>
                <text class="empty-hint">或下拉刷新获取最新预告</text>
              </view>
              <view v-else class="grid-container grid-double">
                <view v-for="room in scheduledList" :key="room.id" class="card-item">
                  <RoomCard :room="room" :is-mobile="true" :show-description="false" @click="handleCardClick(room)" />
                </view>
              </view>
            </view>
          </swiper-item>

          <!-- 回放 -->
          <swiper-item class="module-swiper-item">
            <view class="tab-panel tab-panel--replay">
              <view v-if="replayList.length === 0" class="empty-section empty-live">
                <text class="empty-section-text">暂无回放</text>
                <text class="empty-hint">敬请期待更多精彩内容</text>
                <view class="empty-actions">
                  <view class="empty-btn" @tap.stop="handleTabTap(1)">
                    <text class="empty-btn-text">看预告</text>
                  </view>
                  <view class="empty-btn empty-btn-secondary" @tap.stop="handleTabTap(0)">
                    <text class="empty-btn-text">看直播</text>
                  </view>
                </view>
                <text class="empty-hint">或下拉刷新获取最新回放</text>
              </view>
              <view v-else class="grid-container grid-double">
                <view v-for="room in replayList" :key="room.id" class="card-item">
                  <RoomCard :room="room" :is-mobile="true" :show-description="false" @click="handleCardClick(room)" />
                </view>
              </view>
            </view>
          </swiper-item>
        </swiper>
      </view>

      <view v-if="isLoadingMore" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>
      <view v-if="!hasMore && roomList.length > 0" class="no-more">
        <text class="no-more-text">—— 已经到底了 ——</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 模块级 Tab「正在直播 / 预告 / 回放」，双栏卡片；默认优先显示正在直播，无直播则显示预告，都没有则显示回放
 */
import { ref, computed, watch, nextTick, getCurrentInstance } from 'vue';
import RoomCard from '@/components/shared/RoomCard.vue';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import type { HomepageRoomItem } from '@/types/homepage';

/** 模块级 Tab：正在直播 | 预告 | 回放 */
type ContentTab = 'live' | 'scheduled' | 'replay';

/** 模块级 Tab 索引映射：0=正在直播 | 1=预告 | 2=回放 */
const TAB_KEYS: ContentTab[] = ['live', 'scheduled', 'replay'];

const activeContentTab = ref<ContentTab>('live');

/** Props 定义 */
const props = withDefaults(
  defineProps<{
    roomList: HomepageRoomItem[];
    isLoading: boolean;
    isLoadingMore: boolean;
    hasMore: boolean;
  }>(),
  {
    roomList: () => [],
    isLoading: false,
    isLoadingMore: false,
    hasMore: true,
  }
);

/** 
 * 根据 live_status 动态分类直播间
 * 每个直播间只会出现在一个Tab下，确保无重复
 * 注意：live_status 会随时间变化（预告→正在直播→回放），computed 会自动响应更新
 */
const liveList = computed(() => props.roomList.filter(r => r.live_status === 'live'));
const scheduledList = computed(() => props.roomList.filter(r => r.live_status === 'scheduled'));
const replayList = computed(() => props.roomList.filter(r => r.live_status === 'replay'));
const liveCount = computed(() => liveList.value.length);

/** 
 * 默认 Tab 规则：智能选择有内容的Tab
 * 优先级：正在直播 > 预告 > 回放
 * 当数据更新时（如下拉刷新、加载更多、状态变化），会自动重新评估
 */
const hasAppliedDefaultTab = ref(false);

// 监听数据加载状态，首次加载完成后应用默认Tab规则
watch(
  () => props.isLoading,
  (loading) => {
    if (loading || hasAppliedDefaultTab.value) return;
    hasAppliedDefaultTab.value = true;
    if (liveList.value.length > 0) {
      setActiveTab('live');
    } else if (scheduledList.value.length > 0) {
      setActiveTab('scheduled');
    } else {
      setActiveTab('replay');
    }
    scheduleMeasure();
  },
  { immediate: true }
);

// 监听数据变化，当roomList变化时（如从其他页面返回、数据刷新），重新评估Tab状态
watch(
  () => props.roomList.length,
  () => {
    // 如果当前Tab没有数据，自动切换到有数据的Tab
    if (activeContentTab.value === 'live' && liveList.value.length === 0) {
      // 正在直播Tab无数据，切换到预告或回放
      if (scheduledList.value.length > 0) {
        setActiveTab('scheduled');
      } else if (replayList.value.length > 0) {
        setActiveTab('replay');
      }
    } else if (activeContentTab.value === 'scheduled' && scheduledList.value.length === 0) {
      // 预告Tab无数据，切换到正在直播或回放
      if (liveList.value.length > 0) {
        setActiveTab('live');
      } else if (replayList.value.length > 0) {
        setActiveTab('replay');
      }
    } else if (activeContentTab.value === 'replay' && replayList.value.length === 0) {
      // 回放Tab无数据，切换到正在直播或预告
      if (liveList.value.length > 0) {
        setActiveTab('live');
      } else if (scheduledList.value.length > 0) {
        setActiveTab('scheduled');
      }
    }
    // 数据变化后重测当前 panel 高度（内容增删可能改变高度）
    scheduleMeasure();
  }
);

// 三个 panel 内容数量变化时（渲染后）重测高度
watch(
  () => [liveList.value.length, scheduledList.value.length, replayList.value.length],
  () => scheduleMeasure()
);

/** 组件实例（用于组件作用域选择器查询，适配首页整页滚动） */
const instance = getCurrentInstance();

/** 使用滑动 Tab（点击 ↔ swiper 双向联动）；activeIndex 为唯一数据源 */
const { activeIndex, handleTabTap, handleSwiperChange, setActive, waitForSwiperSettle } = useSwiperTabs(
  TAB_KEYS.length,
  onTabActivated,
  0
);

/**
 * 通过 Tab 标识切换（供智能默认/自动切换逻辑复用，保持 activeIndex 同步）
 * @param key 目标 Tab 标识
 */
function setActiveTab(key: ContentTab): void {
  const idx = TAB_KEYS.indexOf(key);
  if (idx >= 0) setActive(idx);
}

/**
 * Tab 激活回调（点击/滑动共用）：同步业务状态 + 等 swiper 动画结束后重测高度
 * @description 立即测高会在 swiper 动画期间量到旧 panel 高度导致整页跳动；
 * 先等动画结束（waitForSwiperSettle）再测当前激活 panel，抑制跳动（R8）
 * @param idx 索引（0=正在直播 | 1=预告 | 2=回放）
 */
function onTabActivated(idx: number): void {
  const key = TAB_KEYS[idx];
  if (!key) return;
  activeContentTab.value = key;
  void waitForSwiperSettle(300).then(() => {
    scheduleMeasure();
  });
}

/** swiper 自适应高度（px）：测量当前激活 panel 的实际高度 */
const swiperHeight = ref(300);
/** 测量防抖标记 */
let measureTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * 测量当前激活 panel 高度并写入 swiper
 * @description 方案 B：swiper 在整页滚动流内，必须显式高度 = 当前 panel 内容高度
 * 只测激活 panel（tab-panel--{key}），避免非激活 swiper-item 干扰
 */
function measurePanelHeight(): void {
  if (!instance) return;
  const key = TAB_KEYS[activeIndex.value] || 'live';
  nextTick(() => {
    try {
      const query = uni.createSelectorQuery().in(instance);
      query.select(`.tab-panel--${key}`).boundingClientRect(rect => {
        const r = Array.isArray(rect) ? rect[0] : rect;
        if (r && r.height) {
          swiperHeight.value = Math.ceil(r.height);
        }
      }).exec();
    } catch (e) {
      // 测量失败保持原高度
    }
  });
}

/**
 * 安排测量（防抖：连续切换/数据变化只测一次）
 */
function scheduleMeasure(): void {
  if (measureTimer) clearTimeout(measureTimer);
  measureTimer = setTimeout(measurePanelHeight, 50);
}

/** Emits 定义 */
const emit = defineEmits<{
  (e: 'cardClick', room: HomepageRoomItem): void;
}>();

/**
 * 卡片点击处理
 * @param room - 直播间数据
 */
function handleCardClick(room: HomepageRoomItem): void {
  emit('cardClick', room);
}
</script>

<style lang="scss" scoped>
.room-card-grid {
  padding: 0 16rpx;
  /* flex 纵向布局：配合外层 min-height 撑满，内容不足一屏时 no-more 贴容器底（tabbar 正上方） */
  display: flex;
  flex-direction: column;
}

// 骨架屏
.skeleton-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.skeleton-card {
  width: calc(50% - 6rpx);
  background-color: var(--home-card);
  border-radius: var(--home-r-lg);
  overflow: hidden;
  box-shadow: var(--home-shadow-card);
}

.skeleton-cover {
  width: 100%;
  padding-top: 52%;
  background: linear-gradient(90deg, var(--home-border) 25%, var(--home-bg) 50%, var(--home-border) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-info {
  padding: 10rpx 12rpx;
}

.skeleton-title {
  height: 28rpx;
  background-color: var(--home-border);
  border-radius: var(--home-r-md);
  margin-bottom: 12rpx;
}

.skeleton-desc {
  height: 20rpx;
  width: 60%;
  background-color: var(--home-border);
  border-radius: var(--home-r-md);
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

// 分区与网格
.cards-wrapper {
  min-height: 400rpx;
  /* 撑满父容器（flex:1），配合 no-more 的 margin-top:auto 实现贴底 */
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section {
  margin-bottom: 32rpx;
}

.section:last-of-type {
  margin-bottom: 0;
}

/* 模块级标题风格：选中 30rpx/600 未选 28rpx/500，#0F766E/#7A869A，下划线 36×4rpx 距文字 6~8rpx，与精选专家清晰分割 */
.module-tabs {
  display: flex;
  align-items: center;
  gap: 32rpx;
  margin-top: 8rpx;
  margin-bottom: 12rpx;
}

.module-tab {
  position: relative;
  padding: 10rpx 0;
  min-height: 44rpx;
  display: flex;
  align-items: center;
  transition: opacity 0.2s ease;

  /* 触控反馈：180–220ms */
  &:active {
    opacity: 0.7;
  }
}

.module-tab-inner {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.tab-badge-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--color-danger);
  box-shadow: 0 2rpx 4rpx rgba(239, 68, 68, 0.3);
  flex-shrink: 0;
}

.module-tab-text {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--home-tabbar-inactive); /* 未选中：中性弱化 */
  line-height: 1.3;
  transition: color 0.2s ease, font-size 0.2s ease;
}

.module-tab--active .module-tab-text {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-primary); /* 选中：品牌主色 */
}

.module-tab-indicator {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 6rpx;
  height: 4rpx;
  width: 36rpx;
  margin: 0 auto;
  background: var(--home-primary);
  border-radius: 4rpx;
  transition: background-color 0.2s ease;
}

/* 内容区 swiper：自适应高度（JS 测当前激活 panel 高度写入 style） */
.module-swiper {
  width: 100%;
}

.module-swiper-item {
  height: 100%;
}

.tab-panel {
  min-height: 120rpx;
}

.grid-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.card-item {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.grid-replay .card-item,
.grid-double .card-item {
  width: calc(50% - 6rpx);
}

.empty-section {
  padding: 32rpx 0;
}

.empty-section-text {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

.empty-live {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-actions {
  margin-top: 24rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.empty-hint {
  font-size: 22rpx;
  color: var(--home-text2);
  margin-top: 16rpx;
}

// 空状态（保留以兼容）
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0;
}

.empty-icon {
  font-size: 100rpx;
  color: var(--home-text2);
}

.empty-text {
  margin-top: 24rpx;
  font-size: 28rpx;
  color: var(--home-text2);
  margin-bottom: 32rpx;
}

.empty-btn {
  padding: 16rpx 48rpx;
  background-color: var(--home-primary);
  border-radius: var(--home-r-pill);
  box-shadow: var(--home-shadow-card);
  transition: opacity 0.2s ease;

  &:active {
    opacity: 0.85;
  }
}

.empty-btn-secondary {
  background-color: transparent;
  border: 2rpx solid var(--home-primary);
  box-shadow: none;

  &:active {
    background-color: var(--home-badge-featured-bg);
  }
}

.empty-btn-text {
  font-size: 28rpx;
  color: #ffffff;
  font-weight: 500;
}

.empty-btn-secondary .empty-btn-text {
  color: var(--home-primary);
}

// 加载更多
.loading-more {
  display: flex;
  justify-content: center;
  padding: 32rpx 0;
}

.loading-text {
  font-size: 24rpx;
  color: var(--home-text2);
}

.no-more {
  display: flex;
  justify-content: center;
  padding: 32rpx 0;
  /* 内容不足一屏时贴容器底部（tabbar 正上方）；内容超一屏时自然跟随内容流末尾 */
  margin-top: auto;
}

.no-more-text {
  font-size: 24rpx;
  color: var(--home-text2);
}

/* 小屏双栏改单列 */
@media (max-width: 360px) {
  .grid-replay .card-item,
  .grid-double .card-item {
    width: 100%;
  }
}
</style>
