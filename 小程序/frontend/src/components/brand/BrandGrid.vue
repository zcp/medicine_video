<!--
 * BrandGrid - 品牌双列网格
 * @description 品牌专区列表：一排两个，字段沿用 BrandCard
 -->
<template>
  <view class="brand-grid" aria-label="品牌列表">
    <view class="card-grid">
      <view v-for="b in brands" :key="b.id" class="card-wrapper ui-trans">
        <BrandCard
          :id="b.id"
          :name="b.name"
          :logo_url="b.logo_url"
          :description="b.description"
          :sort_order="b.sort_order"
          :is_active="b.is_active"
          @click="onClick"
        />
      </view>
    </view>
    <view class="load-more" v-if="hasMore && !loading">上拉加载更多</view>
  </view>
</template>

<script setup lang="ts">
import BrandCard from './BrandCard.vue'
const props = defineProps<{ brands: any[]; loading: boolean; hasMore: boolean }>()
const emit = defineEmits<{ (e: 'select', id: string): void }>()
function onClick(id: string) {
  emit('select', id)
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-grid {
  padding: 12px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.card-wrapper {
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  overflow: hidden;
}

.card-wrapper:active {
  opacity: 0.92;
}

.load-more {
  text-align: center;
  color: var(--color-text-tertiary);
  padding: 12px;
  font-size: 12px;
}

.ui-trans {
  transition: opacity 160ms ease;
}
</style>
