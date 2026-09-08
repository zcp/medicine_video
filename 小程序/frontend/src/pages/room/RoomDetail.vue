<template>
  <view class="room-detail-page">
    <view class="placeholder-content">
      <uni-icons type="spinner-cycle" size="40" color="var(--color-primary)" />
      <text class="placeholder-title">正在进入直播间…</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 房间详情 — 历史路由占位；真实编排在 LiveView（对照《18》G1）
 * 保留 pages.json 注册，避免旧链接 404；进入后 redirect 到 LiveView。
 */
import { onLoad } from '@dcloudio/uni-app'

onLoad((query?: Record<string, string | undefined>) => {
  const id = String(query?.id || query?.roomId || query?.room_id || '').trim()
  if (id) {
    uni.redirectTo({
      url: `/pages/live/LiveView?roomId=${encodeURIComponent(id)}`,
      fail: () => {
        uni.reLaunch({ url: `/pages/live/LiveView?roomId=${encodeURIComponent(id)}` })
      }
    })
    return
  }
  uni.showToast({ title: '缺少房间 ID', icon: 'none' })
  setTimeout(() => {
    uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/Home' }) })
  }, 400)
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.room-detail-page {
  min-height: 100vh;
  background-color: var(--color-background);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  text-align: center;
}

.placeholder-title {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin-top: 16px;
}
</style>
