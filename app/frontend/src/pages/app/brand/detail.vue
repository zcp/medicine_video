<template>
  <view class="brand-detail">
    <LoadingIndicator v-if="loading" />
    <ErrorBanner v-if="error" :message="error.message" @close="error = null" />
    
    <template v-if="!loading && brand">
      <BrandProfile 
        :name="brand.name" 
        :logo="brandLogo" 
        :description="brand.description ?? undefined" 
      />

      <view class="intro-card">
        <view class="intro-row">
          <text class="intro-k">入驻时间</text>
          <text class="intro-v">{{ formatTime(brand.created_at) }}</text>
        </view>
        <view class="intro-row" v-if="joinedDays !== null">
          <text class="intro-k">入驻时长</text>
          <text class="intro-v">{{ joinedDays }} 天</text>
        </view>
        <view class="intro-row" v-if="brand.website_url">
          <text class="intro-k">官网</text>
          <text class="intro-v link" @tap="copy(brand.website_url)">{{ brand.website_url }}</text>
        </view>
        <view class="intro-row">
          <text class="intro-k">关联直播间</text>
          <text class="intro-v">{{ roomsCount }} 个</text>
        </view>
      </view>

      <view class="section" v-if="brandRoomsLoaded">
        <text class="section-title">关联直播间</text>
        <view class="room-list" v-if="brandRooms.length">
          <view class="room-item" v-for="r in brandRooms" :key="r.room_id" @tap="openRoom(r.room_id)">
            <view class="cover-wrap">
              <image
                v-if="r.cover_url"
                class="cover"
                :src="resolveMediaUrl(r.cover_url) || r.cover_url"
                mode="aspectFill"
              />
              <!-- 封面兜底：浅灰渐变 + 居中播放三角（统一全站） -->
              <view v-else class="cover cover-fallback" />
              <!-- 状态标签（封面左上角，统一位置） -->
              <text v-if="r.live_status" class="cover-status-tag" :class="`status-${r.live_status}`">{{ formatStatus(r.live_status) }}</text>
            </view>
            <view class="right">
              <text class="title">{{ r.title }}</text>
              <!-- 专家 host 块：姓名 | 职称，第二行医院（与专家详情卡片一致） -->
              <view class="session-host" v-if="r.expert_name">
                <ProxyImage
                  class="host-avatar"
                  :src="r.expert_avatar || ''"
                  :fallback="'/static/default-avatar.png'"
                  mode="aspectFill"
                />
                <view class="host-text">
                  <view class="host-line1">
                    <text class="host-name">{{ r.expert_name }}</text>
                    <text v-if="r.expert_title" class="host-title"> | {{ r.expert_title }}</text>
                  </view>
                  <view v-if="r.expert_hospital" class="host-line2">{{ r.expert_hospital }}</view>
                </view>
              </view>
            </view>
          </view>
        </view>
        <EmptyState v-else title="暂无关联直播间" description="该品牌暂未关联任何直播间" />
        <view class="hint" v-if="brandRoomsError">{{ brandRoomsError }}</view>
      </view>
    </template>
    
    <EmptyState v-if="!loading && !brand" title="品牌不存在" description="稍后再试或返回上一页" />
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌详情页面
 * @description 展示品牌详细信息、关联直播间
 */
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import LoadingIndicator from '@/components/common/LoadingIndicator.vue';
import ErrorBanner from '@/components/common/ErrorBanner.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import BrandProfile from '@/components/brand/BrandProfile.vue';
import { getBrandContent, getBrandRooms, type BrandRoomCardItem } from '@/api/brand';
import { resolveMediaUrl } from '@/utils/url';
import ProxyImage from '@/components/common/ProxyImage.vue';

// ========== 类型定义 ==========
interface BrandItem {
  id: string;
  name: string;
  slug?: string;
  logo_url?: string;
  description?: string;
  website_url?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ========== 状态 ==========
const brand = ref<BrandItem | null>(null);
const loading = ref(false);
const error = ref<Error | null>(null);
const brandLogo = ref<string>('');
const brandRooms = ref<BrandRoomCardItem[]>([]);
const brandRoomsLoaded = ref(false);
const brandRoomsError = ref<string>('');
const roomsTotal = ref(0);

// ========== 计算属性 ==========

/**
 * 入驻天数
 */
const joinedDays = computed(() => {
  const createdAt = brand.value?.created_at;
  const ts = createdAt ? Date.parse(createdAt) : NaN;
  if (!Number.isFinite(ts)) return null;
  const days = Math.floor((Date.now() - ts) / (24 * 60 * 60 * 1000));
  return days >= 0 ? days : null;
});

/**
 * 直播间数量（后端分页 total，加载失败时为 0）
 */
const roomsCount = computed(() => roomsTotal.value);

// ========== 方法 ==========

/**
 * 打开直播间
 */
function openRoom(roomId: string) {
  const rid = String(roomId || '');
  if (!rid) return;
  uni.navigateTo({ url: `/pages/app/live/LiveView?roomId=${encodeURIComponent(rid)}` });
}

/**
 * 加载品牌关联直播间（公开接口）
 * @description GET /brands/{brand_id}/rooms，字段由后端聚合（状态/专家/创建者）
 */
async function loadBrandRooms(brandId: string) {
  try {
    const res = await getBrandRooms(brandId, { page: 1, size: 50 });
    if (res.code === 200 && res.data) {
      brandRooms.value = res.data.items || [];
      roomsTotal.value = res.data.total ?? brandRooms.value.length;
    } else {
      brandRoomsError.value = res.message || '加载关联直播间失败';
    }
  } catch (e: any) {
    console.error('[BrandDetail] 加载关联直播间失败:', e);
    brandRoomsError.value = e?.message || '加载关联直播间失败';
  } finally {
    brandRoomsLoaded.value = true;
  }
}

/**
 * 格式化直播状态（三态收敛，与全局卡片一致）
 */
function formatStatus(status: string): string {
  if (status === 'live') return '直播中';
  if (status === 'scheduled') return '预告';
  return '回放';
}

/**
 * 复制文本
 */
function copy(text: string) {
  if (!text) return;
  uni.setClipboardData({ data: text });
}

/**
 * 格式化时间
 */
function formatTime(input?: string | null) {
  const v = String(input || '').trim();
  if (!v) return '';
  // 2025-10-23T12:05:00Z -> 2025-10-23 12:05:00
  return v.replace('T', ' ').replace('Z', '').slice(0, 19);
}

// ========== 生命周期 ==========

onLoad(async (query: any) => {
  const id = String(query?.id || '');
  console.log('[BrandDetail] 页面加载，品牌ID:', id);
  
  if (!id) {
    error.value = new Error('品牌不存在');
    return;
  }
  
  loading.value = true;
  const startedAt = Date.now();
  
  try {
    console.log('[BrandDetail] 开始获取品牌内容');
    const resp = await getBrandContent(id);
    
    if (resp.code === 200 && resp.data) {
      const data: any = resp.data;
      
      brand.value = data.brand_info;
      brandLogo.value = resolveMediaUrl(brand.value?.logo_url) || '/static/tabbar/brand.png';

      // 关联直播间：调用公开接口 GET /brands/{brand_id}/rooms（聚合状态/专家/创建者字段）
      await loadBrandRooms(id);

      console.log('[BrandDetail] 品牌内容加载成功:', {
        name: brand.value?.name,
        roomsCount: brandRooms.value.length,
        durationMs: Date.now() - startedAt
      });
    } else {
      console.warn('[BrandDetail] 品牌内容返回异常:', resp);
      error.value = new Error(resp.message || '获取品牌内容失败');
    }
  } catch (e: any) {
    console.error('[BrandDetail] 品牌内容加载失败:', e);
    error.value = e instanceof Error ? e : new Error(String(e?.message || e || '请求失败'));
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped lang="scss">
.brand-detail {
  min-height: 100vh;
  background: var(--home-bg);
}

.intro-card {
  margin: 20rpx 24rpx 8rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  padding: 20rpx 24rpx;
  box-shadow: var(--home-shadow-card);
}

.intro-row {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 16rpx 0;
  & + & {
    border-top: 1rpx solid rgba(17, 24, 39, 0.06);
  }
}

.intro-k {
  font-size: 24rpx;
  color: var(--home-text2);
  min-width: 144rpx;
}

.intro-v {
  font-size: 24rpx;
  color: var(--home-text1);
  flex: 1;
  text-align: right;
  word-break: break-all;
}

.link {
  color: var(--home-primary);
}

.section {
  margin: 20rpx 24rpx 8rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  padding: 20rpx 24rpx;
  box-shadow: var(--home-shadow-card);
}

.section-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  padding-left: var(--home-spacing-inner);
  border-left: 5rpx solid var(--home-primary);
  margin-bottom: 8rpx;
}

.room-list {
  margin-top: 16rpx;
}

.room-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.06);
  display: flex;
  align-items: center;
  gap: 20rpx;
}

/* 封面容器：状态标签定位锚点 */
.cover-wrap {
  position: relative;
  flex-shrink: 0;
}

.cover {
  width: 240rpx;
  height: 135rpx;
  border-radius: var(--home-r-md);
  background: var(--home-bg);
  flex-shrink: 0;
  display: block;
}

/* 封面兜底：浅灰渐变 + 居中灰色播放三角（统一全站） */
.cover-fallback {
  background: linear-gradient(135deg, #F0F2F5 0%, #E4E8EE 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-fallback::after {
  content: '';
  border-left: 16rpx solid rgba(148, 157, 170, 0.5);
  border-top: 10rpx solid transparent;
  border-bottom: 10rpx solid transparent;
}

/* 状态标签（封面左上角，统一位置） */
.cover-status-tag {
  position: absolute;
  top: 8rpx;
  left: 8rpx;
  padding: 2rpx 12rpx;
  border-radius: 4rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: #fff;
  z-index: 2;
}

.cover-status-tag.status-live {
  background: rgba(220, 38, 38, 0.9);
}

.cover-status-tag.status-scheduled {
  background: var(--home-primary);
}

.cover-status-tag.status-replay,
.cover-status-tag.status-finished,
.cover-status-tag.status-ended,
.cover-status-tag.status-ready,
.cover-status-tag.status-processing {
  background: rgba(0, 0, 0, 0.6);
}

.right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.title {
  font-size: 30rpx;
  color: var(--home-text1);
}

/* 专家 host 块（与专家详情卡片一致）：姓名 | 职称，第二行医院 */
.session-host {
  margin-top: 8rpx;
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  min-width: 0;
}

.host-avatar {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--home-bg);
  margin-top: 2rpx;
}

.host-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.host-line1 {
  font-size: 26rpx;
  color: var(--home-text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.host-name {
  color: var(--home-text1);
  font-weight: 500;
}

.host-title {
  color: var(--home-text3, #999);
}

.host-line2 {
  font-size: 24rpx;
  color: var(--home-text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hint {
  margin-top: 16rpx;
  font-size: 24rpx;
  color: var(--home-text2);
}
</style>
