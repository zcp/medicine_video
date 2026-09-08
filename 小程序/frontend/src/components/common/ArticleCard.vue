<!--
 * ArticleCard - 文章卡片组件
 * @description 展示文章/内容信息的卡片组件
 * @author 直播SaaS团队
 -->
<template>
  <view class="article-card" @click="handleClick">
    <!-- 左侧内容 -->
    <view class="article-card__content">
      <text class="article-card__title">{{ title }}</text>
      <text v-if="summary" class="article-card__summary">{{ summary }}</text>
      
      <view class="article-card__meta">
        <text v-if="author" class="meta__author">{{ author }}</text>
        <text v-if="readCount" class="meta__read">{{ formattedReadCount }}阅读</text>
        <text v-if="publishTime" class="meta__time">{{ publishTime }}</text>
      </view>
    </view>
    
    <!-- 右侧缩略图 -->
    <image
      v-if="thumbnail"
      class="article-card__thumbnail"
      :src="thumbnail"
      mode="aspectFill"
    />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 组件Props定义
 */
interface Props {
  /** 文章ID */
  id: string
  /** 文章标题 */
  title: string
  /** 文章摘要 */
  summary?: string
  /** 缩略图 */
  thumbnail?: string
  /** 作者 */
  author?: string
  /** 阅读数 */
  readCount?: number
  /** 发布时间 */
  publishTime?: string
}

const props = defineProps<Props>()

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击事件 */
  click: [id: string]
}>()

/**
 * 格式化阅读数
 */
const formattedReadCount = computed(() => {
  if (!props.readCount) return ''
  if (props.readCount >= 10000) {
    return `${(props.readCount / 10000).toFixed(1)}万`
  }
  return String(props.readCount)
})

const handleClick = () => {
  emit('click', props.id)
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.article-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background-color: var(--color-bg-primary);
  border-radius: 8px;
  cursor: pointer;
  
  &__content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  &__title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }
  
  &__summary {
    font-size: 13px;
    color: var(--color-text-secondary);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }
  
  &__meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    color: var(--color-text-tertiary);
    
    .meta__author {
      font-weight: 500;
    }
  }
  
  &__thumbnail {
    width: 100px;
    height: 80px;
    border-radius: 4px;
    flex-shrink: 0;
    background-color: var(--color-bg-secondary);
  }
}
</style>
