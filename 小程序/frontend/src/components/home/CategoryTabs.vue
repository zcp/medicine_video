<!--
 * CategoryTabs - 科室分类筛选器
 * @description 横向滚动科室 Tab；微信端用 inline-block，避免 flex 竖排撑满首页
 -->
<template>
  <view class="category-tabs">
    <scroll-view
      class="category-tabs__scroll"
      scroll-x
      :show-scrollbar="false"
      scroll-with-animation
    >
      <!-- 推荐 -->
      <view
        class="category-tabs__item"
        :class="{ 'is-active': activeId === RECOMMEND_ID }"
        @click="handleSelect(RECOMMEND_ID)"
      >
        <text class="item__text">推荐</text>
      </view>

      <!-- 用户固定科室 -->
      <view
        v-for="c in pinnedCategories"
        :key="c.id"
        class="category-tabs__item is-pinned"
        :class="{ 'is-active': c.id === activeId }"
        @click="handleSelect(c.id)"
      >
        <text class="item__text">{{ c.name }}</text>
      </view>

      <!-- 其他科室 -->
      <view
        v-for="category in normalCategories"
        :key="category.id"
        class="category-tabs__item"
        :class="{ 'is-active': category.id === activeId }"
        @click="handleSelect(category.id)"
      >
        <text class="item__text">{{ category.name }}</text>
      </view>
    </scroll-view>

    <view class="category-tabs__all" @click="emit('open-all')" role="button" aria-label="更多科室">
      <text class="all__icon">≡</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Category {
  id: string
  name: string
  icon?: string
}

interface Props {
  categories: Category[]
  activeId?: string | null
  pinnedIds?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  activeId: 'recommend',
  pinnedIds: () => []
})

const emit = defineEmits<{
  select: [id: string | null]
  'open-all': []
}>()

const RECOMMEND_ID = 'recommend'

const pinnedSet = computed(() => new Set((props.pinnedIds || []).filter(Boolean).slice(0, 5)))

const categoryMap = computed(() => {
  const map = new Map<string, { name: string; icon?: string }>()
  ;(props.categories || []).forEach((c) => {
    if (c?.id) map.set(String(c.id), { name: String(c.name || ''), icon: c.icon })
  })
  return map
})

const pinnedCategories = computed(() => {
  const ids = (props.pinnedIds || []).filter(Boolean).slice(0, 5)
  return ids
    .map((id) => {
      const info = categoryMap.value.get(String(id))
      return { id: String(id), name: info?.name || '未知科室', icon: info?.icon }
    })
    .filter((c) => c.id)
})

const normalCategories = computed(() => {
  return (props.categories || []).filter((c) => {
    const id = String(c?.id || '')
    if (!id) return false
    return !pinnedSet.value.has(id)
  })
})

const handleSelect = (id: string | null) => {
  emit('select', id)
}
</script>

<script lang="ts">
export default {
  name: 'CategoryTabs',
  options: {
    styleIsolation: 'shared'
  }
}
</script>

<style lang="scss" scoped>
.category-tabs {
  position: relative;
  height: 88rpx;
  overflow: hidden;
  background-color: #ffffff;
  flex-shrink: 0;
}

.category-tabs__scroll {
  height: 88rpx;
  width: 100%;
  padding-right: 88rpx;
  box-sizing: border-box;
  white-space: nowrap;
}

.category-tabs__item {
  display: inline-block;
  height: 88rpx;
  padding: 0 24rpx;
  vertical-align: middle;
  position: relative;
  box-sizing: border-box;

  &:active {
    opacity: 0.7;
  }

  .item__text {
    font-size: 28rpx;
    color: #909399;
    line-height: 88rpx;
    white-space: nowrap;
  }

  &.is-active {
    .item__text {
      color: #0f766e;
      font-weight: 600;
    }

    &::after {
      content: '';
      position: absolute;
      left: 50%;
      bottom: 0;
      transform: translateX(-50%);
      width: 48rpx;
      height: 6rpx;
      border-radius: 3rpx;
      background-color: #0f766e;
    }
  }

  &.is-pinned .item__text {
    color: #333333;
  }
}

.category-tabs__all {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 2;
  height: 88rpx;
  padding: 0 24rpx;
  background-color: #ffffff;
  display: flex;
  align-items: center;

  &::before {
    content: '';
    position: absolute;
    left: -40rpx;
    top: 0;
    width: 40rpx;
    height: 100%;
    background: linear-gradient(to right, rgba(255, 255, 255, 0), #ffffff);
    pointer-events: none;
  }

  &:active {
    opacity: 0.7;
  }

  .all__icon {
    font-size: 36rpx;
    color: #909399;
    line-height: 88rpx;
  }
}
</style>
