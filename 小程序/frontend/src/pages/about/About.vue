<template>
  <view class="about-page">
    <view class="card">
      <text class="title">关于我们</text>
      <text class="desc">此页面为占位页，可后续补充版本信息与联系方式。</text>

      <view class="row">
        <text class="label">应用名称</text>
        <text class="value">医学直播平台</text>
      </view>
      <view class="row">
        <text class="label">版本</text>
        <text class="value">v0.1.0</text>
      </view>

      <button class="btn" @tap="goBack">返回</button>
    </view>
  </view>
</template>

<script setup lang="ts">
function goBack() {
  uni.navigateBack()
}
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.about-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
  box-sizing: border-box;
}

.card {
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-lg) var(--spacing-lg);
  box-shadow: none;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.desc {
  display: block;
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.row:last-of-type {
  border-bottom: none;
}

.label {
  color: var(--color-text-primary);
  font-size: 14px;
}

.value {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.btn {
  width: 100%;
  margin-top: 14px;
  height: 44px;
  line-height: 44px;
  border-radius: var(--border-radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  transition: var(--transition-base);
}

.btn:active {
  opacity: 0.92;
}
</style>
