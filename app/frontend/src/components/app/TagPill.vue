<template>
  <view class="tag-pill" :class="[`tag-pill--${type}`]">
    <text class="tag-pill-text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 统一标签（预告/回放/直播中）
 * @description 圆角 r-md，字体 22–24rpx，轻背景
 */
withDefaults(
  defineProps<{
    text: string;
    type?: 'scheduled' | 'live' | 'replay';
  }>(),
  { type: 'scheduled' }
);
</script>

<style lang="scss" scoped>
.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 12rpx;
  border-radius: var(--home-r-md);
  font-size: 22rpx;
  font-weight: 500;
}

.tag-pill-text {
  font-size: 22rpx;
}

.tag-pill--scheduled {
  background-color: rgba(15, 118, 110, 0.12);
  color: var(--home-primary);
}

.tag-pill--live {
  background-color: rgba(220, 53, 69, 0.12);
  color: #dc3545;
}

.tag-pill--replay {
  background-color: rgba(107, 114, 128, 0.12);
  color: var(--home-text2);
}
</style>
