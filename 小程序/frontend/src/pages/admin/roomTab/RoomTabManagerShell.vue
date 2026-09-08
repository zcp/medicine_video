<!--
 * RoomTabManagerShell - Tab 管理独立壳页
 * 供管理端直播间运营列表带 roomId 跳转复用 RoomTabManager
 -->
<template>
  <view class="tab-shell-page">
    <view v-if="!roomId" class="empty-state">
      <text class="empty-text">缺少直播间 ID</text>
    </view>
    <RoomTabManager v-else :room-id="roomId" />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import RoomTabManager from './RoomTabManager.vue'

const authStore = useAuthStore()
const roomId = ref('')

onLoad((query) => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({
        url:
          '/pages/auth/OneTapLogin?redirect=' +
          encodeURIComponent('/pages/admin/roomTab/RoomTabManagerShell')
      })
    }, 300)
    return
  }
  if (!authStore.isAdmin) {
    uni.showToast({ title: '暂无访问权限', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1200)
    return
  }
  roomId.value = String(query?.roomId || query?.room_id || '').trim()
  if (!roomId.value) {
    uni.showToast({ title: '缺少直播间 ID', icon: 'none' })
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.tab-shell-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
  box-sizing: border-box;
}

.empty-state {
  padding: 48px 16px;
  text-align: center;

  .empty-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}
</style>
