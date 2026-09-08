<template>
  <view class="webview-container">
    <web-view :src="url" @message="handleMessage" @error="handleError" />
  </view>
</template>

<script setup lang="ts">
/**
 * 内嵌网页页面
 * @description 用于在 App 内嵌入外部网页
 */
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

/** 网页 URL */
const url = ref('');

/**
 * 页面加载，接收路由参数
 */
onLoad((options) => {
  if (options?.url) {
    url.value = decodeURIComponent(options.url);
  }
  if (options?.title) {
    uni.setNavigationBarTitle({
      title: decodeURIComponent(options.title)
    });
  }
});

/**
 * 处理 web-view 消息
 */
const handleMessage = (e: any) => {
  console.log('[WebView] 收到消息:', e.detail);
};

/**
 * 处理加载错误
 */
const handleError = (e: any) => {
  console.error('[WebView] 加载失败:', e);
  uni.showToast({
    title: '页面加载失败',
    icon: 'none'
  });
};
</script>

<style lang="scss" scoped>
.webview-container {
  width: 100%;
  height: 100vh;
}
</style>
