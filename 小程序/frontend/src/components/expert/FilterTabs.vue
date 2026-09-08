<template>
  <scroll-view class="filter-tabs" scroll-x aria-label="科室筛选标签">
    <view class="tabs-row">
      <view
        v-for="(item, idx) in items"
        :key="idx"
        class="tab"
        :class="{ active: idx === selectedIndex }"
        @tap="handleClick(idx, item)"
        :aria-label="`筛选科室：${item}`"
      >
        <text class="label">{{ item }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
const props = defineProps<{ items: string[]; selectedIndex?: number }>()
const emit = defineEmits<{ (e: 'change', index: number, item: string): void }>()

function handleClick(index: number, item: string) {
  emit('change', index, item)
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.filter-tabs {
  background: transparent;
  height: 72rpx;
  box-sizing: border-box;
}

.tabs-row {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--spacing-lg);
  box-sizing: border-box;
  white-space: nowrap;
}

.tab {
  box-sizing: border-box;
  height: 100%;
  padding: 0 var(--spacing-base);
  margin-right: var(--spacing-base);
  background: transparent;
  border: none;
  border-radius: 0;
  font-size: 13px;
  transition: color var(--duration-base) var(--ease-in-out),
    transform var(--duration-fast) var(--ease-in-out);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;

  &:active {
    transform: scale(0.98);
  }
}
.tab.active {
  .label {
    color: var(--color-primary);
    font-weight: 600;
  }

  &::after {
    content: '';
    position: absolute;
    left: 50%;
    bottom: 8rpx;
    transform: translateX(-50%);
    width: 40rpx;
    height: 6rpx;
    border-radius: var(--border-radius-full);
    background-color: var(--color-primary);
  }
}

.label {
  height: 100%;
  display: flex;
  align-items: center;
  line-height: 1;
  color: var(--color-text-secondary);
}
</style>
