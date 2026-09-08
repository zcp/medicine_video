<template>
  <view class="expert-search search-bar" aria-label="专家搜索栏">
    <view class="app-search-field search-box">
      <text class="icon iconfont icon-search" aria-hidden="true"></text>
      <view class="input-wrap">
        <text v-show="!keyword" class="input-placeholder">{{ placeholder }}</text>
        <input
          class="input"
          type="text"
          :value="keyword"
          @input="onInput"
          confirm-type="search"
        />
      </view>
      <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
      <view class="search-clear-slot">
        <ClearButton v-if="keyword" @clear="onClear" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 专家搜索组件
 * @description 带防抖的搜索输入框
 */
import { ref, onUnmounted } from 'vue';
import ClearButton from '@/components/app/ClearButton.vue';

const props = withDefaults(
  defineProps<{
    /** 占位文本 */
    placeholder?: string;
  }>(),
  { placeholder: '搜索专家姓名/医院' }
);

const emit = defineEmits<{
  (e: 'search', keyword: string): void;
}>();

/** 搜索关键词 */
const keyword = ref('');

/** 防抖定时器 */
let timer: ReturnType<typeof setTimeout> | null = null;

/**
 * 处理输入事件
 */
function onInput(e: any) {
  const val = e?.detail?.value ?? e?.target?.value ?? '';
  keyword.value = val;
  
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => emit('search', keyword.value.trim()), 400);
}

/**
 * 清除搜索内容
 */
function onClear() {
  keyword.value = '';
  if (timer) clearTimeout(timer);
  emit('search', '');
}

onUnmounted(() => {
  if (timer) clearTimeout(timer);
});
</script>

<style lang="scss" scoped>
.expert-search.search-bar {
  padding: 0 0 var(--home-spacing-inner);
}

/* 叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；高度统一 72rpx（D2） */
.search-box {
  height: 72rpx;
  box-sizing: border-box;
}

.input-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
}

.input-placeholder {
  position: absolute;
  left: 0;
  top: 0;
  height: 72rpx;
  line-height: 72rpx;
  font-size: var(--home-fs-card-title);
  color: var(--search-placeholder);
  padding-left: var(--home-spacing-inner);
  pointer-events: none;
}

.input {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 72rpx;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  padding-left: var(--home-spacing-inner);
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
  background: transparent;
}

.icon {
  margin-right: var(--home-spacing-inner);
  font-size: var(--home-fs-card-title);
  color: var(--search-icon);
}
</style>
