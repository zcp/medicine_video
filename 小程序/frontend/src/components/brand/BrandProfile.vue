<template>
  <view class="brand-profile">
    <image
      v-if="showBanner"
      class="banner"
      :src="bannerSrc"
      mode="aspectFill"
      :lazy-load="true"
      @error="onBannerError"
    />
    <view class="head">
      <view class="logo-wrap">
        <image
          class="logo"
          :src="logoSrc"
          mode="aspectFill"
          :alt="name"
          :lazy-load="true"
          @error="onLogoError"
        />
      </view>
      <view class="text">
        <text class="name">{{ name }}</text>
        <text class="desc" v-if="description">{{ description }}</text>
      </view>
    </view>
    <view class="stats" v-if="stats">
      <view class="item"><text class="num">{{ stats.followersCount }}</text><text class="label">关注</text></view>
      <view class="item"><text class="num">{{ stats.contentCount }}</text><text class="label">内容</text></view>
      <view class="item"><text class="num">{{ stats.viewsCount }}</text><text class="label">浏览</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { resolveBannerUrl, resolveBrandLogoUrl, shouldMarkBannerBroken, shouldMarkBrandLogoBroken } from '@/utils/url'

const props = defineProps<{
  name: string
  logo?: string | null
  banner?: string | null
  description?: string
  stats?: { followersCount: number; contentCount: number; viewsCount: number }
}>()

const logoBroken = ref(false)
const bannerBroken = ref(false)

const showBanner = computed(() => !!String(props.banner || '').trim() || bannerBroken.value)

const logoSrc = computed(() => resolveBrandLogoUrl(props.logo, logoBroken.value))
const bannerSrc = computed(() => resolveBannerUrl(props.banner, bannerBroken.value))

function onLogoError() {
  if (!shouldMarkBrandLogoBroken(props.logo, logoBroken.value)) return
  logoBroken.value = true
}

function onBannerError() {
  if (!shouldMarkBannerBroken(props.banner, bannerBroken.value)) return
  bannerBroken.value = true
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-profile {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.banner { width:100%; height:140px; background: var(--color-bg-tertiary); }
.head {
  display:flex;
  gap:14px;
  padding:16px var(--spacing-lg);
  align-items: flex-start;
}
.logo-wrap {
  width: 80px;
  height: 80px;
  border-radius: var(--border-radius-base);
  background: var(--color-bg-tertiary);
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid var(--color-border);
}
.logo { width: 100%; height: 100%; display: block; }
.text { flex:1; min-width: 0; }
.name {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
  color: var(--color-text-primary);
}
.desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-regular);
  margin-top: 8px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
}
.stats { display:flex; gap:18px; padding: 0 var(--spacing-lg) 14px; }
.item { display:flex; flex-direction:column; align-items:center; }
.num { font-size:14px; font-weight:600; color: var(--color-text-primary); }
.label { font-size:11px; color: var(--color-text-tertiary); }
</style>
