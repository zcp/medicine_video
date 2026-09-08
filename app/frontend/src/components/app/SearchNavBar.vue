<template>
  <view class="search-navbar">
    <!-- 状态栏占位 -->
    <view :style="{ height: statusBarHeight + 'px' }"></view>

    <!-- 导航栏内容 - Bilibili 极简风格 -->
    <view class="navbar-content">
      <!-- 左侧返回图标 -->
      <view class="back-btn" @tap="handleBack">
        <text class="iconfont icon-arrow-left back-icon"></text>
      </view>

      <!--
        flex + 悬浮清除稳定版：
        图标｜input(flex:1) 为 flex 文档流（文字起点在图标后，不依赖 padding）；
        清除钮 absolute 悬浮右端（不占 flex 位）+ input 恒定 padding-right 预留 → 输入/显隐全程布局零变化。
      -->
      <view class="capsule-wrapper">
        <view class="app-search-field search-capsule">
          <text class="iconfont icon-search search-icon"></text>

          <input
            class="search-input"
            type="text"
            :value="keyword"
            :placeholder="placeholder"
            :focus="autoFocus"
            placeholder-class="search-placeholder"
            confirm-type="search"
            @input="handleInput"
            @confirm="handleConfirm"
            @blur="handleBlur"
          />

          <!-- 清除按钮：iconfont 叉号，absolute 悬浮（不占布局 → 显隐零布局变化） -->
          <view class="search-clear-slot">
            <ClearButton v-if="keyword" @clear="handleClear" />
          </view>
        </view>
      </view>

      <!-- 右侧搜索文字 -->
      <view v-if="showSearchButton" class="search-btn" @tap="handleSearch">
        <text class="search-text">搜索</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 搜索页面自定义导航栏（参考B站样式）
 * @description 仿 uni-app 系统导航栏，集成搜索框。
 * 示范范围：仅 search/index、search/results 引用；不改其它页搜索框与共享 ClearButton 视觉契约。
 */
import { ref } from 'vue';
import ClearButton from './ClearButton.vue';

interface Props {
  /** 搜索关键词 */
  keyword?: string;
  /** 占位文本 */
  placeholder?: string;
  /** 是否自动聚焦 */
  autoFocus?: boolean;
  /** 是否显示搜索按钮 */
  showSearchButton?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  keyword: '',
  placeholder: '搜索直播间、专家、品牌',
  autoFocus: false,
  showSearchButton: true
});

const emit = defineEmits<{
  (e: 'update:keyword', value: string): void;
  (e: 'search', keyword: string): void;
  (e: 'back'): void;
}>();

/** 状态栏高度（px） */
const statusBarHeight = ref(0);

// 获取系统信息
try {
  const sysInfo = uni.getSystemInfoSync();
  statusBarHeight.value = sysInfo.statusBarHeight || 0;
} catch (e) {
  console.error('[SearchNavBar] 获取状态栏高度失败:', e);
  statusBarHeight.value = 20; // 默认值
}

/**
 * 输入事件
 */
const handleInput = (e: any) => {
  const value = e.detail.value;
  console.log('[TRACE-NAVBAR] @input 触发, value:', value);
  emit('update:keyword', value);
};

/**
 * 确认搜索（回车）
 */
const handleConfirm = (e: any) => {
  const value = e.detail.value.trim();
  console.log('[TRACE-NAVBAR] @confirm 触发, value:', value);
  if (value) {
    emit('search', value);
  }
};

/**
 * 失去焦点
 */
const handleBlur = () => {
  console.log('[TRACE-NAVBAR] @blur 触发');
};

/**
 * 清除按钮
 */
const handleClear = () => {
  console.log('[TRACE-NAVBAR] 清除按钮点击');
  emit('update:keyword', '');
};

/**
 * 搜索按钮点击
 */
const handleSearch = () => {
  const value = props.keyword.trim();
  console.log('[TRACE-NAVBAR] 搜索按钮点击, keyword:', props.keyword, 'trimmed:', value);
  if (value) {
    emit('search', value);
  } else {
    uni.showToast({
      title: '请输入搜索关键词',
      icon: 'none',
      duration: 1500
    });
  }
};

/**
 * 返回按钮
 */
const handleBack = () => {
  emit('back');
};
</script>

<style scoped lang="scss">
/* Bilibili 极简清新风格 - 顶部搜索导航栏 */
.search-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 1000;
  background-color: #ffffff;
  border-bottom: 1rpx solid #ebebeb;
  box-sizing: border-box;
}

.navbar-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 88rpx;
  padding: 0 24rpx;
  gap: 16rpx;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0;
  background: transparent;
}

.back-icon {
  font-size: 40rpx;
  color: #333333;
  font-weight: 400;
  line-height: 1;
}

.capsule-wrapper {
  flex: 1;
  min-width: 0;
}

/* 胶囊：叠加 .app-search-field（flex 容器：白底/深灰细边/全胶囊/padding 0 24rpx 公共提供）；
   本地仅覆盖高度（导航栏档位 64rpx）与 relative（悬浮清除钮定位基准） */
.search-capsule {
  position: relative;
  height: 64rpx;
  box-sizing: border-box;
}

/* 搜索图标 - flex 项（线稿灰），文字起点由其后的 input flex:1 物理保证 */
.search-icon {
  flex-shrink: 0;
  margin-right: 12rpx;
  font-size: 32rpx;
  color: var(--search-icon);
  line-height: 1;
}

/* 输入框 - flex:1 中间区，边框/背景/outline 全清（无分隔线来源）；
   padding-right 恒定预留悬浮清除位（不随内容/叉号显隐变化 → 布局全程恒定） */
.search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  box-sizing: border-box;
  padding: 0 56rpx 0 0; /* 右侧恒定预留：悬浮叉位（30rpx 叉 + 边距），不随内容变化 */
  margin: 0 !important;
  font-size: 28rpx;
  color: #333333;
  caret-color: #0f766e;
  line-height: 64rpx;
  background: transparent !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  -webkit-appearance: none;
  appearance: none;
}

/* 清除钮悬浮槽：absolute 右端，不参与 flex → 显隐不改变 input 宽度（零布局变化） */
.search-clear-slot {
  position: absolute;
  right: 10rpx;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  z-index: 2;
}

.search-placeholder {
  color: var(--search-placeholder);
  font-size: 28rpx;
}

.search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0 12rpx;
  background: transparent;
  transition: opacity 0.2s;
}
.search-btn:active {
  opacity: 0.6;
}

.search-text {
  font-size: 30rpx;
  color: #0f766e;
  font-weight: 500;
}
</style>
