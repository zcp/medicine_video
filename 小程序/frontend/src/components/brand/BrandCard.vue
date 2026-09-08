<template>
  <view class="brand-card" :class="{ compact }" @tap="onClick" role="button" :aria-label="`打开品牌：${name}`">
    <view class="logo-wrap">
      <image class="logo" :src="logoSrc" mode="aspectFit" :lazy-load="true" @error="onImgError" />
    </view>
    <view class="info">
      <text class="name">{{ name }}</text>
      <text class="desc" v-if="description">{{ description }}</text>
      <view v-if="is_active === false" class="meta">
        <text class="stat">已禁用</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { resolveBrandLogoUrl, shouldMarkBrandLogoBroken } from '@/utils/url'
import { logger } from '@/logs/logger'
const props = withDefaults(defineProps<{
  id: string
  name: string
  logo_url?: string | null
  description?: string
  sort_order?: number
  is_active?: boolean
  compact?: boolean
}>(), { compact: false })
const emit = defineEmits<{ (e: 'click', id: string): void }>()
const logoBroken = ref(false)
const logoSrc = computed(() => resolveBrandLogoUrl(props.logo_url, logoBroken.value))
function onClick() { emit('click', props.id) }
function onImgError() {
  if (!shouldMarkBrandLogoBroken(props.logo_url, logoBroken.value)) return
  logger.warn('ui', 'BrandCard image load failed, fallback to local', {
    id: props.id,
    name: props.name,
    logo_url: props.logo_url
  })
  logoBroken.value = true
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  padding: 14px 12px 12px;
  margin: 0;
  background: var(--color-surface);
  border: none;
  border-radius: var(--border-radius-base);
  box-shadow: none;
  box-sizing: border-box;
}

.logo-wrap {
  width: 104px;
  height: 104px;
  margin: 0 auto;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo {
  width: 100%;
  height: 100%;
  display: block;
}

.info {
  margin-top: 10px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.desc {
  font-size: 12px;
  color: var(--color-text-regular);
  margin-top: 4px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  width: 100%;
}

.meta {
  display: flex;
  gap: 10px;
  margin-top: 6px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
}

.stat {
  font-size: 12px;
  color: var(--color-text-regular);
}

.brand-card.compact {
  padding: 12px 10px 10px;
  width: 220px;
}

.brand-card.compact .logo-wrap {
  width: 80px;
  height: 80px;
}

.brand-card.compact .name {
  font-size: 13px;
}

.brand-card.compact .desc {
  display: none;
}
</style>
