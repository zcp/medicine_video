<template>
  <view class="room-tabs-page">
    <view v-if="!roomId" class="empty-state">
      <text class="empty-text">缺少直播间 ID</text>
    </view>
    <view v-else-if="!accessGranted" class="empty-state">
      <text class="empty-text">{{ accessMessage }}</text>
    </view>
    <scroll-view v-else class="content-scroll" scroll-y>
      <TabManager :room-id="roomId" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import TabManager from '@/components/app/TabManager.vue';
import { useAuthStore } from '@/store/auth';
import { getMyRooms } from '@/api/room';

const roomId = ref('');
const accessGranted = ref(false);
const accessMessage = ref('');

onLoad((options?: any) => {
  roomId.value = String(options?.roomId || options?.room_id || '').trim();
});

onShow(async () => {
  const authStore = useAuthStore();
  // 管理员：直接放行（不用 useAdminGuard——其非管理员分支自带 toast+返回副作用）
  if (authStore.isAuthenticated && authStore.isAdmin) {
    accessGranted.value = true;
    return;
  }
  // 未登录：跳登录
  if (!authStore.isAuthenticated) {
    accessMessage.value = '请先登录';
    uni.navigateTo({ url: '/pages/app/auth/login' });
    return;
  }
  // 非管理员：房主可管理自己房间的 Tab（后端 admin_tab_router 支持 owner，融合方案 F1b）
  try {
    const res = await getMyRooms({ page: 1, size: 100 });
    const myIds = (res?.data?.items || []).map((r: any) => r.id);
    if (myIds.includes(roomId.value)) {
      accessGranted.value = true;
    } else {
      accessMessage.value = '仅房主或管理员可管理该直播间 Tab';
    }
  } catch {
    accessMessage.value = '权限校验失败，请稍后重试';
  }
});
</script>

<style lang="scss" scoped>
.room-tabs-page {
  min-height: 100vh;
  background: var(--home-bg);
  padding: 24rpx;
  box-sizing: border-box;
}

.content-scroll {
  height: calc(100vh - 48rpx);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
  color: var(--home-tabbar-inactive);

  .empty-text {
    font-size: 26rpx;
  }
}
</style>
