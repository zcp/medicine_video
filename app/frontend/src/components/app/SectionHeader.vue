<template>
  <view class="section-header">
    <text class="section-title">{{ title }}</text>
    <view v-if="moreText" class="section-more" @tap="handleMore">
      <text class="section-more-text">{{ moreText }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 区块头（左标题 + 右侧更多）
 */
withDefaults(
  defineProps<{
    title: string;
    moreText?: string;
  }>(),
  { moreText: '查看全部 >' }
);

const emit = defineEmits<{ (e: 'more'): void }>();

function handleMore() {
  emit('more');
}
</script>

<style lang="scss" scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--home-spacing-inner) 0;
}

.section-title {
  font-size: var(--home-fs-section);
  font-weight: 700;
  color: var(--home-text1);
}

.section-more-text {
  font-size: 24rpx;
  color: var(--home-primary);
}

.section-more {
  padding: 8rpx 0;
}
</style>
