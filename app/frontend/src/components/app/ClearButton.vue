<template>
  <view
    class="clear-button"
    :style="buttonStyle"
    @tap.stop="handleTap"
    aria-label="清除"
  >
    <text class="clear-button__icon iconfont icon-close"></text>
  </view>
</template>

<script setup lang="ts">
/**
 * 清除按钮（B站风格：iconfont 叉号，无圆形底）
 * @description 直接用 iconfont 叉号字形（icon-close，同码点 \e620），不额外包裹圆形区域；
 * 热区默认 64rpx 防误触
 */
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  /** 热区尺寸（rpx），默认 64 */
  size?: number;
}>(), {
  size: 64
});

const emit = defineEmits<{
  (e: 'clear'): void;
}>();

const buttonStyle = computed(() => ({
  width: `${props.size}rpx`,
  height: `${props.size}rpx`
}));

function handleTap() {
  emit('clear');
}
</script>

<style lang="scss" scoped>
.clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.clear-button__icon {
  font-size: 30rpx;
  color: var(--search-clear-icon);
  line-height: 1;
}
</style>
