<template>
  <view class="my-live-page">
    <template v-if="authStore.isAuthenticated">
      <!-- 已登录：跳转到直播管理首页（通过 onShow 触发） -->
      <PlaceholderPage 
        title="正在加载直播管理..."
        description="即将跳转至直播管理页面"
        icon="video"
      />
    </template>
    <template v-else>
      <PlaceholderPage 
        title="创建直播" 
        description="登录后可创建和管理直播"
        icon="video"
      >
        <button class="login-btn" @click="handleGoLogin">立即登录</button>
      </PlaceholderPage>
    </template>
    <CustomTabBar :current="-1" />
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app';
import PlaceholderPage from '@/components/app/PlaceholderPage.vue';
import CustomTabBar from '@/components/app/CustomTabBar.vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

onShow(() => {
  if (authStore.isAuthenticated) {
    // 管理员无 owner 房：改道全站房间，避免落入"我的直播"空态引导创建
    if (authStore.isAdmin) {
      uni.redirectTo({ url: '/pages/app/live-manage/list?mode=admin' });
      return;
    }
    // V15 修复：跳转到真实的直播管理列表页（原实现跳回首页导致入口失效）
    uni.redirectTo({ url: '/pages/app/live-manage/list' });
  }
});

function handleGoLogin(): void {
  uni.setStorageSync('loginRedirectPath', '/pages/app/tabbar/my-live/index');
  uni.navigateTo({ url: '/pages/app/auth/login' });
}
</script>

<style scoped>
.my-live-page {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: 100rpx;
}
</style>
