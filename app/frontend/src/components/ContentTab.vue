<template>
  <view class="content-tab">
    <!-- 纯文字 -->
    <view v-if="tab.content_type === 'text'" class="text-content">
      <text v-if="tab.text_content">{{ tab.text_content }}</text>
      <text v-else class="empty-hint">暂无内容</text>
    </view>
    
    <!-- 纯图片 -->
    <image 
      v-else-if="tab.content_type === 'image'" 
      :src="resolveMediaUrl(tab.image_url)" 
      @error="handleImageError"
      mode="widthFix"
      lazy-load
      class="image-content"
    />
    
    <!-- 图文混合 -->
    <view v-else-if="tab.content_type === 'mixed'" class="mixed-content">
      <view v-if="tab.text_content" class="text-part">
        <text>{{ tab.text_content }}</text>
      </view>
      <image 
        v-if="tab.image_url" 
        :src="resolveMediaUrl(tab.image_url)" 
        @error="handleImageError"
        mode="widthFix"
        lazy-load
        class="image-part"
      />
      <text v-if="!tab.text_content && !tab.image_url" class="empty-hint">暂无内容</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { resolveMediaUrl } from '@/utils/url'
import type { Tab } from '@/types/tab'

interface Props {
  tab: Tab
}

defineProps<Props>()

// 图片加载失败处理
const handleImageError = (e: any) => {
  e.target.src = '/static/default-image.png'
}
</script>

<style scoped>
.content-tab {
  width: 100%;
}

/* 文字内容 */
.text-content {
  padding: 32rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
}

/* 图片内容 */
.image-content {
  width: 100%;
  max-height: 800rpx;
}

/* 图文混合 */
.mixed-content {
  padding: 32rpx;
}

.text-part {
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
  margin-bottom: 24rpx;
}

.image-part {
  width: 100%;
  max-height: 800rpx;
  border-radius: 8rpx;
}

/* 空内容提示 */
.empty-hint {
  display: block;
  padding: 32rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}
</style>
