<template>
  <view class="brand-header">
    <view class="app-search-field search-box">
      <text class="iconfont icon-search search-icon"></text>
      <input 
        class="search-input" 
        type="text" 
        :value="kw" 
        placeholder="搜索品牌" 
        @input="onInput" 
        aria-label="搜索品牌" 
      />
      <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
      <view class="search-clear-slot">
        <ClearButton v-if="kw" @clear="onClear" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌头部组件
 * @description 品牌搜索框
 */
import { ref } from 'vue';
import ClearButton from '@/components/app/ClearButton.vue';

const props = withDefaults(defineProps<{
  /** 初始关键词 */
  keyword?: string;
}>(), {
  keyword: ''
});

const emit = defineEmits<{
  (e: 'search', keyword: string): void;
}>();

/** 搜索关键词 */
const kw = ref(props.keyword);

/** 防抖定时器 */
let timer: ReturnType<typeof setTimeout> | null = null;

/**
 * 处理输入
 */
function onInput(e: any) {
  kw.value = e.detail.value;
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => emit('search', kw.value.trim()), 400);
}

/**
 * 清除搜索内容
 */
function onClear() {
  kw.value = '';
  if (timer) clearTimeout(timer);
  emit('search', '');
}
</script>

<style scoped lang="scss">
.brand-header {
  padding: var(--home-spacing-module) var(--home-spacing-page) var(--home-spacing-inner);
  background: var(--home-bg);
}

/* 叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；高度统一 72rpx（D2） */
.search-box {
  height: 72rpx;
  box-sizing: border-box;
}

.search-icon {
  margin-right: var(--home-spacing-inner);
  color: var(--search-icon);
  font-size: var(--home-fs-card-title);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  height: 100%;
  background: transparent;
  border: none;
  outline: none;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}
</style>
