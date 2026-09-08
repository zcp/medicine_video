<template>
  <view
    class="pill-btn"
    :class="[`pill-btn--${type}`]"
    @tap="handleTap"
  >
    <text class="pill-btn-text"><slot /></text>
  </view>
</template>

<script setup lang="ts">
/**
 * 胶囊按钮（与登录页同款）
 * @description primary / outline / ghost，高度 88rpx，圆角 r-pill
 */
const props = withDefaults(
  defineProps<{
    type?: 'primary' | 'outline' | 'ghost';
  }>(),
  { type: 'primary' }
);

const emit = defineEmits<{ (e: 'click'): void }>();

function handleTap() {
  emit('click');
}
</script>

<style lang="scss" scoped>
.pill-btn {
  height: 88rpx;
  border-radius: var(--home-r-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s, transform 0.2s;

  &:active {
    transform: translateY(1rpx);
  }
}

.pill-btn-text {
  font-size: 28rpx;
  font-weight: 500;
}

.pill-btn--primary {
  background-color: var(--home-primary);
  color: #fff;
  box-shadow: 0 2px 6px rgba(15, 118, 110, 0.08);

  .pill-btn-text {
    color: #fff;
  }
}

.pill-btn--outline {
  background-color: transparent;
  border: 2rpx solid var(--home-primary);

  .pill-btn-text {
    color: var(--home-primary);
  }
}

.pill-btn--ghost {
  background-color: transparent;

  .pill-btn-text {
    color: var(--home-text2);
  }
}
</style>
