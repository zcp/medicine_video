<template>
  <view class="app-card" :style="cardStyle">
    <slot />
  </view>
</template>

<script setup lang="ts">
/**
 * 统一卡片容器
 * @description 白底、圆角、轻阴影，与登录页/首页设计语言一致
 */
const props = withDefaults(
  defineProps<{
    padding?: string;
    radius?: string;
  }>(),
  { padding: '16rpx', radius: '16rpx' }
);

const cardStyle = { padding: props.padding, borderRadius: props.radius };
</script>

<style lang="scss" scoped>
.app-card {
  background-color: var(--home-card);
  border-radius: 16rpx;
  box-shadow: var(--home-shadow-card);
  box-sizing: border-box;
}
</style>
