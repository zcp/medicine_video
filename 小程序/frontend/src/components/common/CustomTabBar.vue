<template>
  <view class="custom-tabbar" :class="{ 'safe-area-bottom': true }">
    <view 
      v-for="(item, index) in tabList" 
      :key="index"
      class="tab-item"
      :class="{ active: currentIndex === index }"
      @click="switchTab(index)"
    >
      <view class="tab-icon">
        <uni-icons 
          :type="currentIndex === index ? item.selectedIcon : item.icon" 
          :size="22" 
          :color="currentIndex === index ? selectedColor : color"
        />
      </view>
      <text 
        class="tab-text" 
        :style="{ color: currentIndex === index ? selectedColor : color }"
      >
        {{ item.text }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { watch } from 'vue'

interface TabItem {
  pagePath: string
  text: string
  icon: string
  selectedIcon: string
}

const props = defineProps<{
  current?: number
}>()

const emit = defineEmits<{
  change: [index: number]
}>()

// TabBar配置
/** 与 pages.json tabBar.list / custom-tab-bar 一致：无「我的直播」 */
const tabList: TabItem[] = [
  {
    pagePath: 'pages/home/Home',
    text: '首页',
    icon: 'home',
    selectedIcon: 'home-filled'
  },
  {
    pagePath: 'pages/brand/BrandZone',
    text: '品牌',
    icon: 'shop',
    selectedIcon: 'shop-filled'
  },
  {
    pagePath: 'pages/expert/ExpertList',
    text: '专家',
    icon: 'person',
    selectedIcon: 'person-filled'
  },
  {
    pagePath: 'pages/profile/Profile',
    text: '我的',
    icon: 'contact',
    selectedIcon: 'contact-filled'
  }
]

// 颜色配置
const color = 'var(--color-text-secondary)'
const selectedColor = 'var(--color-primary)'

// 当前选中索引
const currentIndex = ref(props.current || 0)

// 切换Tab
const switchTab = (index: number) => {
  if (currentIndex.value === index) return
  
  currentIndex.value = index
  emit('change', index)
  
  // 跳转页面
  const targetPage = tabList[index].pagePath
  uni.switchTab({
    url: `/${targetPage}`
  })
}

// 监听props变化
watch(() => props.current, (newVal) => {
  if (newVal !== undefined) {
    currentIndex.value = newVal
  }
})
</script>

<style lang="scss" scoped>
.custom-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  display: flex;
  z-index: 1000;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5px 0;
  transition: all 0.2s ease;
  
  &.active {
    .tab-icon {
      transform: scale(1.1);
    }
  }
}

.tab-icon {
  margin-bottom: 2px;
  transition: transform 0.2s ease;
}

.tab-text {
  font-size: 10px;
  line-height: 1;
  transition: color 0.2s ease;
}

// 安全区域适配
.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
