<!--
 * MyExpert - 已按《14-V2》V2.2 产品裁剪下线
 * 专家认领 /experts/me* 后端已删除；专家资料改由 Admin 维护
 -->
<template>
  <view class="my-expert-page">
    <view class="state-box">
      <text class="state-title">功能已下线</text>
      <text class="state-text">专家认领与自编辑已取消。专家资料请联系运营在管理端维护；公开专家页仍可正常浏览与关注。</text>
      <view class="btn-primary" @tap="goBack">
        <text class="btn-text">返回</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/profile/Profile' })
    }
  })
}
</script>

<style scoped>
.my-expert-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
}
.state-box {
  margin-top: 120rpx;
  padding: 48rpx 36rpx;
  background: #fff;
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}
.state-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #1a1a1a;
}
.state-text {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
  text-align: center;
}
.btn-primary {
  margin-top: 16rpx;
  padding: 20rpx 56rpx;
  background: #2f6bff;
  border-radius: 999rpx;
}
.btn-text {
  color: #fff;
  font-size: 28rpx;
}
</style>
