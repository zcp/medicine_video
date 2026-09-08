<template>
  <view class="brand-grid" aria-label="品牌网格">
    <!-- 加载骨架屏 -->
    <view class="grid" v-if="loading && brands.length === 0">
      <view class="skeleton-card" v-for="i in 6" :key="'s-' + i">
        <view class="skeleton-logo" />
        <view class="skeleton-line skeleton-line--short" />
        <view class="skeleton-line skeleton-line--long" />
      </view>
    </view>

    <!-- 品牌卡片网格 -->
    <view class="grid" v-else-if="brands.length > 0">
      <BrandCard
        v-for="b in brands"
        :key="b.id"
        :id="b.id"
        :name="b.name"
        :logo_url="b.logo_url"
        :description="b.description"
        :is_active="b.is_active"
        @click="onClick"
      />
    </view>

    <!-- 空状态 -->
    <view class="empty" v-if="!loading && brands.length === 0">暂无品牌</view>

    <!-- 加载更多提示 -->
    <view class="load-more" v-if="loading && brands.length > 0">加载中...</view>
    <view class="no-more" v-else-if="!hasMore && brands.length > 0 && !loading">已经到底啦~</view>
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌网格组件
 * @description 2列网格展示品牌卡片，含骨架屏加载态
 */
import BrandCard from './BrandCard.vue';

defineProps<{
  /** 品牌列表 */
  brands: any[];
  /** 是否加载中 */
  loading: boolean;
  /** 是否有更多 */
  hasMore: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', id: string): void;
}>();

/**
 * 处理品牌点击
 */
function onClick(id: string) {
  emit('select', id);
}
</script>

<style scoped lang="scss">
.brand-grid {
  padding: var(--home-spacing-inner) 0;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--home-spacing-module);
  padding: 0 var(--home-spacing-page);
}

/* ---------- 骨架屏 ---------- */
.skeleton-card {
  padding: var(--home-spacing-module);
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.skeleton-logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: var(--home-r-md);
  background: var(--home-border);
  animation: shimmer 1.5s infinite;
}

.skeleton-line {
  height: 24rpx;
  border-radius: 6rpx;
  background: var(--home-border);
  animation: shimmer 1.5s infinite;
}

.skeleton-line--short {
  width: 60%;
}

.skeleton-line--long {
  width: 85%;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ---------- 状态提示 ---------- */
.load-more,
.no-more {
  text-align: center;
  color: var(--home-text2);
  padding: var(--home-spacing-module);
  font-size: var(--home-fs-meta, 24rpx);
}

.empty {
  text-align: center;
  color: var(--home-text2);
  padding: 80rpx 40rpx;
  font-size: var(--home-fs-card-title, 28rpx);
}
</style>
