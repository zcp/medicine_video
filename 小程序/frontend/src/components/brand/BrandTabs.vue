<!-- 本版不接入：品牌分类 Tab（专区暂不做分类） -->
<template>
  <scroll-view class="brand-tabs" scroll-x role="tablist" aria-label="品牌分类">
    <view class="tabs-row">
      <view
        v-for="(tab, i) in items"
        :key="i"
        class="tab"
        :class="{ active: i === selectedIndex }"
        role="tab"
        :aria-selected="i===selectedIndex"
        @tap="onChange(i, tab)"
      >
        <text class="label">{{ tab }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ items?: string[]; selectedIndex?: number }>(), {
  items: () => ['全部','医疗设备','制药','耗材','软件','其他'],
  selectedIndex: 0
})
const emit = defineEmits<{ (e:'change', index:number, item:string):void }>()
function onChange(index:number, item:string){ emit('change', index, item) }
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-tabs {
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
  flex-shrink: 0;
  height: 100%;
  min-width: 96rpx;
  max-width: 320rpx;
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
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
