<template>
  <view class="topic-list">
    <view class="header">专题列表</view>
    <view v-for="t in topics" :key="t.id" class="row" @tap="open(t.id)">
      <image class="thumb" :src="t.banner_url" mode="aspectFill" :lazy-load="true" />
      <view class="col">
        <text class="title">{{ t.title }}</text>
        <text class="meta" v-if="t.status">{{ t.status }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 专题列表组件
 * @description 展示品牌关联的专题列表
 */
interface TopicBriefItem {
  id: string;
  title: string;
  banner_url?: string;
  status?: string;
}

interface Props {
  topics: TopicBriefItem[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'open', id: string): void;
}>();

/**
 * 打开专题详情
 */
function open(id: string) {
  emit('open', id);
}
</script>

<style scoped lang="scss">
.topic-list {
  padding: 16rpx 24rpx;
}

.header {
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.row {
  display: flex;
  gap: 20rpx;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
}

.thumb {
  width: 180rpx;
  height: 140rpx;
  background: #f0f0f0;
}

.col {
  flex: 1;
  padding: 16rpx;
}

.title {
  font-size: 26rpx;
  color: #333;
}

.meta {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
}
</style>
