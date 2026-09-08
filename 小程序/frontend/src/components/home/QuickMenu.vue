<!--
 * QuickMenu - 快捷菜单组件
 * @description 长按首页Tab弹出的快捷设置菜单
 * @author 直播SaaS团队
 -->
<template>
  <view v-if="visible" class="quick-menu" @click="handleClose">
    <view class="quick-menu__content" @click.stop>
      <view class="quick-menu__title">⚙️ 首页快捷设置</view>
      
      <view class="quick-menu__section">
        <view
          class="menu-item"
          :class="{ 'is-active': viewMode === 'double' }"
          @click="handleViewModeChange('double')"
        >
          <text class="menu-item__text">☷  双列模式</text>
          <uni-icons v-if="viewMode === 'double'" type="checkmarkempty" size="20" color="var(--color-primary)" />
        </view>
        
        <view
          class="menu-item"
          :class="{ 'is-active': viewMode === 'single' }"
          @click="handleViewModeChange('single')"
        >
          <text class="menu-item__text">≡  单列模式</text>
          <uni-icons v-if="viewMode === 'single'" type="checkmarkempty" size="20" color="var(--color-primary)" />
        </view>
      </view>
      
      <view class="quick-menu__section">
        <view class="menu-item" @click="handleRefresh">
          <text class="menu-item__text">🔄  刷新推荐</text>
        </view>
        
        <view class="menu-item" @click="handleScrollToTop">
          <text class="menu-item__text">⬆️  回到顶部</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 组件Props定义
 */
interface Props {
  /** 是否显示 */
  visible: boolean
  /** 当前视图模式 */
  viewMode: 'double' | 'single'
}

defineProps<Props>()

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 关闭菜单 */
  close: []
  /** 切换视图模式 */
  'view-mode-change': [mode: 'double' | 'single']
  /** 刷新推荐 */
  refresh: []
  /** 回到顶部 */
  'scroll-to-top': []
}>()

const handleClose = () => {
  emit('close')
}

const handleViewModeChange = (mode: 'double' | 'single') => {
  emit('view-mode-change', mode)
  emit('close')
}

const handleRefresh = () => {
  emit('refresh')
  emit('close')
}

const handleScrollToTop = () => {
  emit('scroll-to-top')
  emit('close')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.quick-menu {
  position: fixed;
  inset: 0;
  background-color: var(--color-mask);
  z-index: 999;
  display: flex;
  align-items: flex-end;
  
  &__content {
    width: 100%;
    background-color: var(--color-bg-primary);
    border-radius: 12px 12px 0 0;
    padding: 20px;
    animation: slideUp var(--duration-base) var(--ease-in-out);
  }
  
  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 16px;
  }
  
  &__section {
    margin-bottom: 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background-color: var(--color-bg-secondary);
  cursor: pointer;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &.is-active {
    background-color: var(--color-primary-soft);
  }
  
  &__text {
    font-size: 15px;
    color: var(--color-text-primary);
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>
