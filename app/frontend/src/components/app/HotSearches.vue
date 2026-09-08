<template>
  <view class="hot-searches">
    <!-- 标题行 -->
    <view class="section-header">
      <text class="section-title">热门搜索</text>
    </view>

    <!-- 两列列表 -->
    <view class="hot-list">
      <view
        v-for="(item, index) in items"
        :key="index"
        class="hot-item"
        @tap="handleSelect(item.keyword)"
      >
        <text class="rank-num" :class="{ 'rank-top3': index < 3 }">{{ index + 1 }}</text>
        <text class="item-text">{{ item.keyword }}</text>
        <view v-if="item.isNew" class="new-badge">新</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 热门搜索组件
 * @description 展示热门搜索关键词列表，支持点击选择
 */
import type { HotSearchItem } from '@/types/search';

interface Props {
  /** 热门搜索列表 */
  items: HotSearchItem[];
}

defineProps<Props>();

const emit = defineEmits<{
  /** 选择关键词事件 */
  (e: 'select-keyword', keyword: string): void;
}>();

/**
 * 选择关键词
 */
const handleSelect = (keyword: string) => {
  emit('select-keyword', keyword);
};
</script>

<style scoped lang="scss">
.hot-searches {
  padding: 0 32rpx 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  padding: 32rpx 0 16rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

/* 两列 flex 布局 */
.hot-list {
  display: flex;
  flex-wrap: wrap;
}

.hot-item {
  width: 50%;
  display: flex;
  align-items: center;
  padding: 22rpx 24rpx 22rpx 0;
  gap: 16rpx;
  box-sizing: border-box;
}

/* 排名数字 */
.rank-num {
  flex-shrink: 0;
  width: 36rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #C0C4CC;
  text-align: center;
  line-height: 1;
}

.rank-top3 {
  color: #F56C6C;
}

.item-text {
  flex: 1;
  font-size: 26rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.new-badge {
  flex-shrink: 0;
  padding: 2rpx 8rpx;
  background: var(--home-primary, #0F766E);
  color: #fff;
  font-size: 20rpx;
  border-radius: 4rpx;
  line-height: 1.4;
}
</style>
