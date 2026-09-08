<!--
 * FeedList - Feed流容器组件
 * @description 双列瀑布流布局的容器组件
 * @author 直播SaaS团队
 -->
<template>
  <view class="feed-list">
    <!-- 双列布局 -->
    <view class="feed-list__column">
      <slot name="left" />
    </view>
    <view class="feed-list__column">
      <slot name="right" />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * @description 简单的双列布局容器，实际内容通过插槽传入
 */
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.feed-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px 16px;
  
  &__column {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
