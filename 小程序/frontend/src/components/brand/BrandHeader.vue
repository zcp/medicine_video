<!--
 * BrandHeader - 品牌搜索栏
 * @description 样式对齐首页 TopBar 搜索条
 -->
<template>
  <view class="brand-header" aria-label="品牌搜索栏">
    <view class="search-box">
      <text class="search-icon iconfont icon-sousuo" aria-hidden="true"></text>
      <input
        class="search"
        type="text"
        :value="keyword"
        placeholder="搜索品牌"
        aria-label="搜索品牌"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        confirm-type="search"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
const props = withDefaults(defineProps<{ keyword?: string }>(), { keyword: '' })
const emit = defineEmits<{
  (e: 'search', keyword: string): void
  (e: 'focus'): void
  (e: 'blur'): void
}>()
const kw = ref(props.keyword)
watch(
  () => props.keyword,
  (v) => {
    kw.value = v || ''
  }
)
let timer: any = null
function onInput(e: any) {
  kw.value = e.detail.value
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', kw.value.trim()), 400)
}

function onFocus() {
  emit('focus')
}

function onBlur() {
  emit('blur')
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.brand-header {
  padding: 0;
  background: transparent;
  width: 100%;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 12px;
  background-color: var(--color-bg-secondary);
  border-radius: 16px;
  box-sizing: border-box;
}

.search-icon {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1;
  color: var(--color-text-tertiary);
}

.search {
  flex: 1;
  min-width: 0;
  height: 32px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: transparent;
  line-height: 32px;
}
</style>
