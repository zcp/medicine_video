<template>
  <scroll-view class="brand-tabs" scroll-x scroll-with-animation role="tablist" aria-label="品牌分类">
    <view class="tabs-container">
      <view 
        v-for="(tab, i) in items" 
        :key="i"
        :id="'tab-' + i" 
        class="tab-item" 
        :class="{ 'tab-item--active': i === selectedIndex }" 
        role="tab" 
        :aria-selected="i === selectedIndex" 
        @tap="onChange(i, tab)"
      >
        <text class="tab-text">{{ tab }}</text>
        <view v-if="i === selectedIndex" class="tab-indicator"></view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
/**
 * 品牌Tab组件
 * @description 品牌分类筛选标签，采用首页同款样式与逻辑
 */

const props = withDefaults(defineProps<{
  /** 标签列表 */
  items?: string[];
  /** 当前选中索引 */
  selectedIndex?: number;
}>(), {
  items: () => ['全部', '医疗设备', '制药', '耗材', '软件', '其他'],
  selectedIndex: 0
});

const emit = defineEmits<{
  (e: 'change', index: number, item: string): void;
}>();

/**
 * 处理Tab切换
 */
function onChange(index: number, item: string) {
  emit('change', index, item);
}
</script>

<style scoped lang="scss">
.brand-tabs {
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
