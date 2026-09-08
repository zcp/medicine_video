<template>
  <scroll-view class="filter-tabs" scroll-x scroll-with-animation aria-label="科室筛选标签">
    <view class="tabs-container">
      <view
        v-for="(item, idx) in items"
        :key="idx"
        :id="'tab-' + idx"
        class="tab-item"
        :class="{ 'tab-item--active': idx === selectedIndex }"
        @tap="handleClick(idx, item)"
        :aria-label="`筛选科室：${item}`"
      >
        <text class="tab-text">{{ item }}</text>
        <view v-if="idx === selectedIndex" class="tab-indicator"></view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
/**
 * 筛选Tab组件
 * @description 横向滚动的筛选标签，采用首页同款样式与逻辑
 */

const props = defineProps<{
  /** 标签列表 */
  items: string[];
  /** 当前选中索引 */
  selectedIndex?: number;
}>();

const emit = defineEmits<{
  (e: 'change', index: number, item: string): void;
}>();

/**
 * 处理标签点击
 */
function handleClick(index: number, item: string) {
  emit('change', index, item);
}
</script>

<style lang="scss" scoped>
.filter-tabs {
  width: 100%;
  height: 80rpx;
  background-color: var(--home-bg);
  white-space: nowrap;
}

.tabs-container {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--home-spacing-page);
}

.tab-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 0 32rpx;
  flex-shrink: 0;
}

.tab-text {
  font-size: 28rpx;
  color: var(--home-text2);
  transition: color 0.2s ease;
}

.tab-item--active .tab-text {
  color: var(--home-primary);
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 28rpx;
  height: 6rpx;
  background-color: var(--home-primary);
  border-radius: 4rpx;
}
</style>
