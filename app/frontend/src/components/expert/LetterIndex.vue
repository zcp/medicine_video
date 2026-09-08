<template>
  <view class="letter-index" aria-label="字母索引">
    <view class="letters">
      <text
        v-for="(l, i) in letters"
        :key="i"
        class="letter"
        :class="{ active: l === active }"
        @tap="pick(l)"
        :aria-label="`跳转字母：${l}`"
      >{{ l }}</text>
    </view>
    
    <!-- 浮动提示框 -->
    <view v-if="showHint" class="letter-hint">
      {{ hintLetter }}
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 字母索引组件
 * @description 右侧A-Z字母快速索引，支持浮动提示
 */
import { ref } from 'vue';

const props = withDefaults(defineProps<{
  /** 字母列表 */
  letters?: string[];
  /** 当前激活的字母 */
  active?: string;
}>(), {
  letters: () => Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
  active: ''
});

const emit = defineEmits<{
  (e: 'pick', letter: string): void;
}>();

// 浮动提示状态
const showHint = ref(false);
const hintLetter = ref('');
let hintTimer: any = null;

/**
 * 选择字母
 */
function pick(letter: string) {
  // 显示浮动提示
  showHint.value = true;
  hintLetter.value = letter;
  
  // 触发事件
  emit('pick', letter);
  
  // 触觉反馈（微信小程序）
  if (uni.vibrateShort) {
    uni.vibrateShort({ type: 'light' });
  }
  
  // 500ms后隐藏提示
  clearTimeout(hintTimer);
  hintTimer = setTimeout(() => {
    showHint.value = false;
  }, 500);
}
</script>

<style lang="scss" scoped>
.letter-index {
  position: fixed;
  right: var(--expert-index-inset, 8rpx);
  top: 200rpx;
  bottom: 120rpx;
  display: flex;
  align-items: center;
  z-index: 100;
  pointer-events: none; /* 让背景区域不拦截触摸事件 */
}

.letters {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  height: 100%;
  pointer-events: auto; /* 恢复字母的触摸事件 */
}

/* 默认更弱：opacity 0.45 + Neutral-500；滑动/选中时仅当前字母主色 */
.letter {
  font-size: 22rpx;
  color: var(--home-text2, #666);
  opacity: 0.45;
  padding: 4rpx 8rpx;
  min-height: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: color 0.2s ease, opacity 0.2s ease, transform 0.15s ease;
  user-select: none;
}

.letter.active {
  color: var(--home-primary, #00b96b);
  font-weight: 600;
  opacity: 1;
  transform: scale(1.15);
}

.letter:active {
  opacity: 1;
  color: var(--home-primary, #00b96b);
  transform: scale(1.1);
}

/* 浮动提示框（参考iOS通讯录） */
.letter-hint {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 120rpx;
  height: 120rpx;
  background: rgba(0, 0, 0, 0.75);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 68rpx;
  font-weight: 600;
  color: #ffffff;
  z-index: 9999;
  pointer-events: none;
  animation: hintFadeIn 0.15s ease-out;
}

@keyframes hintFadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}
</style>
