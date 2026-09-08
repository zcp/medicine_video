<template>
  <view class="featured-carousel">
    <view v-if="loading" class="loading-skeleton">
      <view class="skeleton-slide" />
    </view>
    <view v-else-if="slides.length === 0" class="empty-state" />
    <swiper
      :key="swiperKey"
      class="swiper"
      :current="currentSwiperIndex"
      :indicator-dots="false"
      :autoplay="innerAutoplay"
      :interval="4000"
      :duration="300"
      :circular="canLoop"
      :previous-margin="sidePeek"
      :next-margin="sidePeek"
      @change="handleSwiperChange"
      @touchstart="handleTouchStart"
      @touchend="handleTouchEnd"
    >
      <swiper-item v-for="(slide, idx) in slides" :key="slideKey(slide, idx)">
        <!-- 统一样式的焦点图：预告和专题使用相同布局 -->
        <view class="slide-item" :class="getCardClass(idx)" @tap="handleSlideTap(slide, idx)">
          <view class="slide-content">
            <ProxyImage
              v-if="slide.type === 'upcoming' ? getUpcomingCover(slide.data) : getCampaignImageUrl(slide.data)"
              class="slide-image"
              :src="slide.type === 'upcoming' ? getUpcomingCover(slide.data) : getCampaignImageUrl(slide.data)"
              :fallback="FALLBACK_BANNER_IMAGE"
              mode="aspectFill"
              @error="slide.type === 'upcoming' ? onUpcomingImageError(slide.data.id) : onCampaignImageError(slide.data.id)"
            />
            <view v-else class="slide-image slide-image-placeholder" />
            <view class="slide-overlay">
              <text class="slide-title">{{ slide.data.title }}</text>
              <!-- CTA按钮：预告显示"立即预约"，其他显示 subtitle -->
              <view v-if="slide.type === 'upcoming' || slide.data.subtitle" class="slide-cta">
                <text class="cta-text">
                  {{ slide.type === 'upcoming' ? '立即预约' : slide.data.subtitle }}
                </text>
              </view>
            </view>
          </view>
        </view>
      </swiper-item>
    </swiper>
    <!-- 自定义分页：非激活 0.25 透明度，激活为短条胶囊 -->
    <view v-if="slides.length > 1" class="custom-indicator">
      <view
        v-for="(_, idx) in slides"
        :key="idx"
        class="indicator-dot"
        :class="{ 'indicator-dot--active': currentSwiperIndex === idx }"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 焦点图轮播：支持 campaign（专题）与 upcoming（直播预告）两种 item
 * upcoming 最多 1–2 条，优先排在前面；upcoming 采用玻璃卡片布局，预约按钮 @tap.stop
 */
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getFeaturedContent } from '@/api/featured';
import { resolveMediaUrl, isValidUUID } from '@/utils/url';
import ProxyImage from '@/components/common/ProxyImage.vue';
import type { FeaturedContent } from '@/types/featured';
import type { HomepageRoomItem } from '@/types/homepage';
import { parseTitleInfo, formatHospitalDepartment } from '@/utils/titleParser';

type SlideCampaign = { type: 'campaign'; data: FeaturedContent };
type SlideUpcoming = { type: 'upcoming'; data: HomepageRoomItem };
type Slide = SlideCampaign | SlideUpcoming;

const props = withDefaults(
  defineProps<{
    /** 即将开播列表（取前 1–2 条放入轮播首位） */
    upcomingList?: HomepageRoomItem[];
  }>(),
  { upcomingList: () => [] }
);

const loading = ref(false);
const campaignBanners = ref<FeaturedContent[]>([]);
const upcomingImageErrors = ref<Set<string>>(new Set());
const campaignImageErrors = ref<Set<string>>(new Set());
const currentSwiperIndex = ref(0);
const innerAutoplay = ref(true);
let pauseTimer: ReturnType<typeof setTimeout> | null = null;

const bannerCount = computed(() => slides.value.length);
/** 微信/App circular 在单张时异常；少于 2 张关闭循环与左右露出 */
const canLoop = computed(() => bannerCount.value >= 2);
const sidePeek = computed(() => (bannerCount.value >= 2 ? '48rpx' : '0rpx'));

function clearPauseTimer() {
  if (pauseTimer) {
    clearTimeout(pauseTimer);
    pauseTimer = null;
  }
}

function handleTouchStart() {
  innerAutoplay.value = false;
  clearPauseTimer();
}

function handleTouchEnd() {
  if (bannerCount.value < 2) return;
  clearPauseTimer();
  pauseTimer = setTimeout(() => {
    innerAutoplay.value = true;
  }, 8000);
}

/** 3D 卡片四态：中间放大、两侧缩小变暗、远端隐藏 */
function getCardClass(idx: number): string {
  const len = bannerCount.value;
  if (len <= 1) return 'is-center';
  const diff = (idx - currentSwiperIndex.value + len) % len;
  if (diff === 0) return 'is-center';
  if (diff === 1) return 'is-right';
  if (diff === len - 1) return 'is-left';
  return 'is-hidden';
}

/** 点击侧边卡片先切中，点击中卡才触发业务跳转 */
function handleSlideTap(slide: Slide, idx: number): void {
  if (idx !== currentSwiperIndex.value) {
    currentSwiperIndex.value = idx;
    return;
  }
  if (slide.type === 'upcoming') handleUpcomingSlideClick(slide.data);
  else handleCampaignClick(slide.data);
}

const FALLBACK_BANNER_IMAGE = 'data:image/svg+xml;utf8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%221200%22 height%3D%22675%22 viewBox%3D%220 0 1200 675%22%3E%3Crect width%3D%221200%22 height%3D%22675%22 fill%3D%22%23E5E7EB%22%2F%3E%3Ctext x%3D%22600%22 y%3D%22337%22 text-anchor%3D%22middle%22 fill%3D%22%239CA3AF%22 font-size%3D%2224%22%3E%E6%9A%82%E6%97%A0%E5%9B%BE%E7%89%87%3C%2Ftext%3E%3C%2Fsvg%3E';

const slides = computed<Slide[]>(() => {
  const up = (props.upcomingList || []).slice(0, 2).map((r) => ({ type: 'upcoming' as const, data: r }));
  const camp = campaignBanners.value.map((c) => ({ type: 'campaign' as const, data: c }));
  return [...up, ...camp];
});

/**
 * swiper key：当 slides 内容变化时强制重建 swiper，避免 uni-app Android 端
 * SWIPER-ITEM.remove 时 getBoundingClientRect 取到 null 节点的问题
 */
const swiperKey = computed(() =>
  slides.value.map((s, i) => slideKey(s, i)).join('|') || 'empty'
);

function slideKey(slide: Slide, idx: number): string {
  return slide.type === 'upcoming' ? `up-${slide.data.id}` : `c-${slide.data.id}-${idx}`;
}

/** 预告封面：后端返回的 cover_url，用 resolveMediaUrl 转成可访问地址，解析不到则用原值 */
function getUpcomingCover(room: HomepageRoomItem): string {
  const raw = room.cover_url;
  if (!raw) return '';
  const resolved = resolveMediaUrl(raw);
  return resolved || raw;
}

function onUpcomingImageError(_id: string): void {
  // 可在此将当前项 src 切到 fallback，模板已用 getUpcomingCover，fallback 在 getUpcomingCover 中
  // 若需单次错误后换图，可维护 upcomingImageErrors 并在 getUpcomingCover 里判断
}

function handleUpcomingSlideClick(room: HomepageRoomItem): void {
  uni.navigateTo({ url: `/pages/app/live/LiveView?roomId=${room.id}` });
}

/** 专题图：后端返回的 image_url，用 resolveMediaUrl 转成可访问地址，解析不到则用原值 */
function getCampaignImageUrl(item: FeaturedContent): string {
  const raw = item.image_url;
  if (!raw) return FALLBACK_BANNER_IMAGE;
  const resolved = resolveMediaUrl(raw);
  return resolved || raw || FALLBACK_BANNER_IMAGE;
}

function onCampaignImageError(id: string): void {
  const banner = campaignBanners.value.find(b => b.id === id);
  if (banner) {
    campaignImageErrors.value.add(id);
  }
  console.error('[焦点图] 图片加载失败:', {
    id,
    title: banner?.title,
    original_url: banner?.image_url,
    resolved_url: banner ? getCampaignImageUrl(banner) : null,
    fallback_url: FALLBACK_BANNER_IMAGE
  });
}

const isUrlSafe = (url: string): boolean => {
  if (!url) return false;
  const dangerous = ['javascript:', 'data:', 'vbscript:', 'file:', 'blob:'];
  const lower = url.toLowerCase().trim();
  return !dangerous.some((p) => lower.startsWith(p));
};

function handleCampaignClick(banner: FeaturedContent): void {
  if (!banner.target_type) return;
  try {
    if (banner.target_type === 'session' && isValidUUID(banner.target_id)) {
      uni.navigateTo({ url: `/pages/app/live/LiveView?sessionId=${banner.target_id}` });
      return;
    }
    if (banner.target_type === 'room' && isValidUUID(banner.target_id)) {
      uni.navigateTo({ url: `/pages/app/live/LiveView?roomId=${banner.target_id}` });
      return;
    }
    if (banner.target_type === 'topic' && isValidUUID(banner.target_id)) {
      // #ifdef H5
      uni.navigateTo({ url: `/pages/h5/topic/TopicDisplay?topic_id=${banner.target_id}` });
      // #endif
      // #ifndef H5
      // App/小程序暂未实现专题展示页，忽略跳转
      console.warn('[焦点图] App端暂不支持 topic 类型跳转，忽略:', banner.target_id);
      // #endif
      return;
    }
    if (banner.target_type === 'brand' && isValidUUID(banner.target_id)) {
      uni.navigateTo({ url: `/pages/app/brand/detail?id=${encodeURIComponent(banner.target_id)}` });
      return;
    }
    if (banner.target_type === 'external' && banner.target_url && isUrlSafe(banner.target_url)) {
      if (banner.target_url.startsWith('http')) {
        uni.navigateTo({ url: `/pages/shared/webview/index?url=${encodeURIComponent(banner.target_url)}` });
      } else if (banner.target_url.startsWith('/')) {
        uni.navigateTo({ url: banner.target_url });
      }
    }
  } catch (e) {
    console.error('[焦点图] 跳转异常', e);
    uni.showToast({ title: '跳转失败', icon: 'none' });
  }
}

function handleSwiperChange(e: { detail: { current: number } }): void {
  currentSwiperIndex.value = e.detail.current;
}

async function loadBanners(): Promise<void> {
  loading.value = true;
  try {
    // 👇 添加时间戳防止缓存
    const timestamp = Date.now();
    console.log(`[焦点图] 开始加载数据，时间戳: ${timestamp}`);
    
    const res = await getFeaturedContent();
    const dataArray = res.data || [];
    
    // 👇 调试日志
    console.log('[焦点图] API返回数据:', {
      count: dataArray.length,
      timestamp: new Date().toLocaleTimeString(),
      data: dataArray
    });
    
    if (dataArray.length > 0) {
      // 保留后端返回的原始 image_url，展示时再通过 getCampaignImageUrl 解析
      campaignBanners.value = dataArray;
      
      // 👇 检查URL解析和 CTA 显示
      console.log('[焦点图] 数据处理结果:', 
        campaignBanners.value.map(b => ({
          title: b.title,
          subtitle: b.subtitle,
          has_subtitle: !!b.subtitle,
          original_url: b.image_url,
          resolved_url: getCampaignImageUrl(b)
        }))
      );
    } else {
      console.warn('[焦点图] API返回空数据，使用Mock');
      campaignBanners.value = getDefaultCampaigns();
    }
  } catch (e) {
    console.error('[焦点图] API调用失败:', e);
    campaignBanners.value = getDefaultCampaigns();
  } finally {
    loading.value = false;
  }
}

function getDefaultCampaigns(): FeaturedContent[] {
  return [
    {
      id: 'banner-local-fallback',
      title: '',
      image_url: FALLBACK_BANNER_IMAGE,
      target_type: null,
      target_id: null,
      target_url: null,
      sort_order: 0
    }
  ];
}

onMounted(() => {
  // 👇 检查环境变量配置
  console.log('[焦点图] 环境变量配置:', {
    MEDIA_BASE: import.meta.env.VITE_MEDIA_BASE_URL,
    BASE_API: import.meta.env.VITE_BASE_API_URL,
    NODE_ENV: import.meta.env.MODE
  });
  
  loadBanners();
});

/** 供父组件下拉刷新等场景调用：重新拉取焦点图（加载中时跳过，避免并发重复请求） */
async function refresh(): Promise<void> {
  if (loading.value) return;
  await loadBanners();
}

defineExpose({ refresh });

onUnmounted(() => {
  clearPauseTimer();
});
</script>

<style lang="scss" scoped>
.featured-carousel {
  width: 100%;
  height: 360rpx;
  margin-bottom: 10rpx; /* 与精选专家间距略压缩，提升首屏密度 */
  padding: 0 8rpx;
  box-sizing: border-box;
  position: relative;
}

.loading-skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--home-border) 0%, var(--home-bg) 100%);
  border-radius: var(--home-r-lg);
  border: 1px solid var(--home-border-light);
  animation: pulse 1.5s infinite;
  .skeleton-slide {
    width: 100%;
    height: 100%;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.empty-state {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--home-border) 0%, var(--home-bg) 100%);
  border-radius: var(--home-r-lg);
  border: 1px solid var(--home-border-light);
}

.swiper {
  width: 100%;
  height: 100%;
}

.slide-item {
  width: 100%;
  height: 100%;
  padding: 0 2rpx;
  box-sizing: border-box;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    filter 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &.is-center {
    transform: scale(1);
    opacity: 1;
    filter: brightness(1);
    z-index: 10;
  }

  &.is-left {
    /* 向中心平移：扩大左侧卡可视内容，避免仅露窄边 */
    transform: translateX(40rpx) scale(0.85);
    opacity: 0.65;
    filter: brightness(0.82);
    z-index: 5;
  }

  &.is-right {
    /* 向中心平移：扩大右侧卡可视内容，避免仅露窄边 */
    transform: translateX(-40rpx) scale(0.85);
    opacity: 0.65;
    filter: brightness(0.82);
    z-index: 5;
  }

  &.is-hidden {
    opacity: 0;
    transform: scale(0.8);
    z-index: 0;
  }
}

.slide-content {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: var(--home-r-lg);
  border: 1px solid var(--home-border-light);
  box-shadow: none; /* 图片卡片无需阴影：去油腻，靠图片本身与圆角建立层级 */
}

.slide-image {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--home-border) 0%, var(--home-bg) 100%);
  border-radius: var(--home-r-lg);
}

.slide-image-placeholder {
  background: linear-gradient(135deg, var(--home-border) 0%, var(--home-border-light) 100%);
}

.slide-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 24rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0));
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  border-radius: 0 0 16rpx 16rpx;
}

.slide-title {
  font-size: var(--home-fs-banner);
  font-weight: 600;
  color: #fff;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.slide-cta {
  align-self: flex-start;
  padding: 14rpx 32rpx;
  background: rgba(15, 118, 110, 0.10);
  border: 2rpx solid var(--home-primary);
  border-radius: var(--home-r-pill);
  transition: background-color 0.2s ease, border-color 0.2s ease;

  .cta-text {
    font-size: 26rpx;
    color: #ffffff;
    font-weight: 600;
    text-shadow: 0 1rpx 4rpx rgba(15, 118, 110, 0.6);
  }

  &:active {
    background: rgba(15, 118, 110, 0.2);
  }
}

/* 自定义分页：叠在轮播底部，非激活 0.25，激活短条胶囊 */
.custom-indicator {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 20rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12rpx;
  z-index: 4;
}

.indicator-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 6rpx;
  background: rgba(255, 255, 255, 0.25);
  transition: all 0.2s ease;
  border: 1rpx solid rgba(0, 0, 0, 0.1);
}

.indicator-dot--active {
  width: 32rpx;
  height: 12rpx;
  border-radius: 6rpx;
  background: #fff;
}
</style>
