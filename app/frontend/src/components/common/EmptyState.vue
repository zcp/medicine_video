<template>
  <view class="empty-state">
    <image v-if="icon" :src="icon" mode="aspectFit" class="empty-icon" />
    <view v-else class="empty-icon-placeholder"><uni-icons type="mail-open" size="60" color="#c0c4cc" /></view>
    <text class="title">{{ title }}</text>
    <text v-if="description" class="desc">{{ description }}</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 空状态组件
 * @description 用于展示无数据时的空状态
 */

defineProps<{
  /** 标题 */
  title: string;
  /** 描述 */
  description?: string;
  /** 图标URL */
  icon?: string;
}>();
</script>

<style scoped lang="scss">
.empty-state {
  padding: 48rpx;
  text-align: center;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  width: 240rpx;
  height: 240rpx;
  margin-bottom: 24rpx;
  opacity: 0.8;
}

.empty-icon-placeholder {
  font-size: 120rpx;
  margin-bottom: 24rpx;
  opacity: 0.6;
}

.title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.desc {
  display: block;
  font-size: 26rpx;
  color: #999;
  margin-top: 12rpx;
}
</style>
