<!--
 * ExpertSearch - 专家搜索栏
 * @description 样式对齐首页 TopBar 搜索条
 -->
<template>
  <view class="expert-search" aria-label="专家搜索栏">
    <view class="search-box">
      <text class="search-icon iconfont icon-sousuo" aria-hidden="true"></text>
      <input
        class="input"
        type="text"
        :value="keyword"
        :placeholder="placeholder || '搜索专家'"
        @input="onInput"
        confirm-type="search"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const props = defineProps<{ placeholder?: string }>()
const emit = defineEmits<{ (e: 'search', keyword: string): void }>()

const keyword = ref('')
let timer: any = null

function onInput(e: any) {
  const val = e?.detail?.value ?? e?.target?.value ?? ''
  keyword.value = val
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => emit('search', keyword.value.trim()), 400)
}

onUnmounted(() => {
  if (timer) clearTimeout(timer)
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-search {
  background: transparent;
  padding: 0;
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

.input {
  flex: 1;
  min-width: 0;
  height: 32px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: transparent;
  line-height: 32px;
}
</style>
