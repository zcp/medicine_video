<template>
  <view class="brand-card" @tap="onClick" role="button" :aria-label="`打开品牌：${name}`">
    <image class="logo" :src="logoSrc" mode="aspectFit" :lazy-load="true" @error="onImgError" />
    <view class="info">
      <text class="name">{{ name }}</text>
      <text class="desc" v-if="description">{{ description }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌卡片组件
 * @description 网格中的品牌卡片，展示Logo、名称、简介，点击进入品牌详情
 */
import { ref, computed } from 'vue';
import { resolveMediaUrl } from '@/utils/url';

const props = defineProps<{
  /** 品牌ID */
  id: string;
  /** 品牌名称 */
  name: string;
  /** Logo URL */
  logo_url?: string | null;
  /** 品牌描述 */
  description?: string;
  /** 是否激活 */
  is_active?: boolean;
}>();

const emit = defineEmits<{
  (e: 'click', id: string): void;
}>();

/** 默认Logo */
const fallbackLogo = '/static/tabbar/brand.png';

/** 图片加载是否失败 */
const hasImgError = ref(false);

/** Logo源地址 */
const logoSrc = computed(() => {
  if (hasImgError.value) return fallbackLogo;
  const resolved = resolveMediaUrl(props.logo_url);
  return resolved || fallbackLogo;
});

/**
 * 处理点击
 */
function onClick() {
  emit('click', props.id);
}

/**
 * 处理图片加载失败
 */
function onImgError() {
  if (!hasImgError.value) {
    console.warn('[BrandCard] 图片加载失败:', props.logo_url);
  }
  hasImgError.value = true;
}
</script>

<style scoped lang="scss">
.brand-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--home-spacing-module);
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  box-shadow: var(--home-shadow-card);
  text-align: center;
  transition: transform 0.15s ease;
}

.brand-card:active {
  transform: scale(0.97);
}

.logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: var(--home-r-md);
  background: var(--home-bg);
  flex-shrink: 0;
  margin-bottom: 16rpx;
}

.info {
  width: 100%;
  min-width: 0;
}

.name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--home-text1);
  display: block;
}

.desc {
  font-size: 22rpx;
  color: var(--home-text2);
  margin-top: 8rpx;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
