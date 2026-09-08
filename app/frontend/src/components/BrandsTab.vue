<template>
  <view class="brands-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="brands.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无品牌信息</text>
    </view>
    
    <!-- 品牌列表（复用搜索结果页 SearchResultCard，样式与搜索页品牌一致） -->
    <view v-else class="brands-list">
      <SearchResultCard
        v-for="brand in brands"
        :key="brand.id"
        :item="toSearchItem(brand)"
        @click="goToBrandDetail"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getRoomBrands } from '@/api/brand'
import SearchResultCard from '@/components/app/SearchResultCard.vue'
import type { SearchResultItem } from '@/api/search'
import type { Brand } from '@/types/brand'

interface Props {
  roomId: string
}

const props = defineProps<Props>()

const brands = ref<Brand[]>([])
const loading = ref(true)

// 缓存策略（5分钟）
const CACHE_DURATION = 5 * 60 * 1000
const brandsCache = ref<{
  data: Brand[];
  timestamp: number;
} | null>(null)

/** 品牌 → 搜索结果项映射（与搜索结果页推荐品牌映射一致） */
const toSearchItem = (brand: Brand): SearchResultItem => ({
  id: brand.id,
  type: 'brand',
  title: brand.name,
  subtitle: brand.description || undefined,
  cover_url: brand.logo_url || undefined,
  match_score: 0,
  metadata: {}
})

onMounted(async () => {
  await loadBrands()
})

// 加载品牌列表
const loadBrands = async () => {
  // 检查缓存
  if (brandsCache.value) {
    const now = Date.now()
    if (now - brandsCache.value.timestamp < CACHE_DURATION) {
      brands.value = brandsCache.value.data
      loading.value = false
      return
    }
  }
  
  try {
    const response = await getRoomBrands(props.roomId)
    // 适配后端响应格式：data可能嵌套在data.data中
    const brandsData = (response as any).data?.data || (response as any).data || []
    
    console.log('[BrandsTab] API响应:', response)
    console.log('[BrandsTab] 品牌数据:', brandsData)
    
    brands.value = brandsData
    
    // 更新缓存
    brandsCache.value = {
      data: brandsData,
      timestamp: Date.now()
    }
  } catch (error: any) {
    console.error('获取品牌列表失败:', error)
    uni.showToast({
      title: error.message || '获取品牌列表失败',
      icon: 'none',
      duration: 2000
    })
  } finally {
    loading.value = false
  }
}

// 跳转到品牌详情页
const goToBrandDetail = (item: SearchResultItem) => {
  uni.navigateTo({
    url: `/pages/app/brand/detail?id=${item.id}`
  })
}
</script>

<style scoped>
.brands-tab {
  width: 100%;
  min-height: 400rpx;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

/* 白色列表容器：对齐搜索结果页 .results-list 展示 */
.brands-list {
  background: #fff;
}
</style>
