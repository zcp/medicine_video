<template>
  <!-- 本版：精选品牌横滑；不做专题入口 -->
  <view v-if="brands.length" class="featured-brands">
    <view class="header">
      <text class="title">精选品牌</text>
    </view>
    <scroll-view scroll-x class="carousel" show-scrollbar="false" aria-label="精选品牌横向列表">
      <view class="row">
        <BrandCard
          v-for="b in brands"
          :key="b.id"
          :id="b.id"
          :name="b.name"
          :logo_url="b.logo_url"
          :description="b.description || undefined"
          :is_active="b.is_active"
          compact
          @click="select"
        />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import BrandCard from './BrandCard.vue'
import type { BrandItem } from '@/types/brands'

defineProps<{ brands: BrandItem[] }>()
const emit = defineEmits<{ (e: 'select', id: string): void }>()
function select(id: string) {
  emit('select', id)
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.featured-brands {
  padding: 4px 0 8px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-lg);
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.carousel {
  white-space: nowrap;
}

.row {
  display: flex;
  gap: 10px;
  padding: 8px var(--spacing-lg) 4px;
}
</style>
