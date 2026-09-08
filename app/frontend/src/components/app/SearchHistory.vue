<template>
  <view class="search-history">
    <!-- 标题栏 -->
    <view class="history-header">
      <view class="header-left">
        <text class="iconfont icon-history header-icon"></text>
        <text class="header-title">搜索历史</text>
      </view>
      <view class="clear-btn" @tap="handleClearAll">
        <text class="iconfont icon-trash clear-icon"></text>
      </view>
    </view>
    
    <!-- 历史记录列表 -->
    <view v-if="items.length > 0" class="history-list">
      <view
        v-for="(item, index) in items"
        :key="index"
        class="history-tag"
        @tap="handleSelect(item.keyword)"
      >
        <text class="tag-text">{{ item.keyword }}</text>
        <view class="delete-btn" @tap.stop="handleDelete(item.keyword)">
          <text class="iconfont icon-close delete-icon"></text>
        </view>
      </view>
    </view>
    
    <!-- 空状态 -->
    <view v-else class="empty-state">
      <text class="empty-text">暂无搜索历史</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 搜索历史组件
 * @description 展示搜索历史记录，支持点击选择、删除单条、清空全部
 */
import type { SearchHistoryItem } from '@/types/search';

interface Props {
  /** 搜索历史列表 */
  items: SearchHistoryItem[];
}

defineProps<Props>();

const emit = defineEmits<{
  /** 选择关键词事件 */
  (e: 'select-keyword', keyword: string): void;
  /** 删除单条记录事件 */
  (e: 'delete-item', keyword: string): void;
  /** 清空全部记录事件 */
  (e: 'clear-all'): void;
}>();

/**
 * 选择关键词
 */
const handleSelect = (keyword: string) => {
  emit('select-keyword', keyword);
};

/**
 * 删除单条记录
 */
const handleDelete = (keyword: string) => {
  emit('delete-item', keyword);
};

/**
 * 清空全部记录
 */
const handleClearAll = () => {
  uni.showModal({
    title: '提示',
    content: '确定要清空搜索历史吗？',
    success: (res) => {
      if (res.confirm) {
        emit('clear-all');
      }
    }
  });
};
</script>

<style scoped lang="scss">
.search-history {
  padding: 32rpx;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-icon {
  font-size: 32rpx;
  color: #999;
  margin-right: 8rpx;
}

.header-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.clear-btn {
  display: flex;
  align-items: center;
  padding: 8rpx;
}

.clear-icon {
  font-size: 36rpx;
  color: #999;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.history-tag {
  display: inline-flex;
  align-items: center;
  padding: 12rpx 24rpx;
  background: #F6F6F6;
  border-radius: 12rpx;
  gap: 8rpx;
  max-width: 100%;
}

.tag-text {
  font-size: 24rpx;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400rpx;
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.delete-icon {
  font-size: 20rpx;
  color: #999;
}

.empty-state {
  padding: 80rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}
</style>
