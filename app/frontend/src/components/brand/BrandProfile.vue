<template>
  <view class="brand-profile">
    <image class="banner" v-if="bannerSrc" :src="bannerSrc" mode="aspectFill" :lazy-load="true" @error="onBannerError" />
    <view class="head">
      <image class="logo" :src="logoSrc" mode="aspectFit" :alt="name" :lazy-load="true" @error="onLogoError" />
      <view class="text">
        <text class="name">{{ name }}</text>
        <text class="desc" v-if="description">{{ description }}</text>
      </view>
    </view>
    <view class="stats" v-if="stats">
      <view class="item">
        <text class="num">{{ stats.followersCount }}</text>
        <text class="label">关注</text>
      </view>
      <view class="item">
        <text class="num">{{ stats.contentCount }}</text>
        <text class="label">内容</text>
      </view>
      <view class="item">
        <text class="num">{{ stats.viewsCount }}</text>
        <text class="label">浏览</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌资料卡片组件
 * @description 展示品牌Logo、名称、描述和统计信息
 */
import { ref, computed } from 'vue';

interface Stats {
  followersCount: number;
  contentCount: number;
  viewsCount: number;
}

interface Props {
  name: string;
  logo: string;
  banner?: string;
  description?: string;
  stats?: Stats;
}

const props = defineProps<Props>();

/** 品牌默认Logo（与品牌列表页 BrandCard 兜底一致） */
const DEFAULT_LOGO = '/static/tabbar/brand.png';

/** logo 加载失败标记 */
const hasLogoError = ref(false);
/** banner 加载失败标记（失败后隐藏） */
const hasBannerError = ref(false);

/** logo 源：加载失败或为空时使用默认Logo */
const logoSrc = computed(() => (hasLogoError.value ? '' : props.logo) || DEFAULT_LOGO);

/** banner 源：加载失败后隐藏，避免空白图 */
const bannerSrc = computed(() => (hasBannerError.value ? '' : props.banner || ''));

function onLogoError() {
  hasLogoError.value = true;
}

function onBannerError() {
  hasBannerError.value = true;
}
</script>

<style scoped lang="scss">
.brand-profile {
  background: var(--home-card);
}

.banner {
  width: 100%;
  height: 240rpx;
  background: var(--home-bg);
}

.head {
  display: flex;
  gap: 24rpx;
  padding: 24rpx;
}

.logo {
  width: 112rpx;
  height: 112rpx;
  border-radius: var(--home-r-md);
  background: var(--home-bg);
  border: 1.5rpx solid var(--home-border);
}

.text {
  flex: 1;
}

.name {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--home-text1);
  display: block;
}

.desc {
  font-size: 24rpx;
  color: var(--home-text2);
  margin-top: 8rpx;
}

.stats {
  display: flex;
  gap: 36rpx;
  padding: 0 24rpx 24rpx;
}

.item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.num {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.label {
  font-size: 22rpx;
  color: var(--home-text2);
}
</style>
