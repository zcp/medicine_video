<!-- 本版不接入：品牌专题列表（专题能力整版暂缓） -->
<template>
  <view class="topic-list">
    <view class="header">专题列表</view>
    <view v-for="t in topics" :key="t.id" class="row" @tap="open(t.id)">
      <image class="thumb" :src="getTopicCover(t)" mode="aspectFill" :lazy-load="true" @error="handleImageError(t.id)" />
      <view class="col">
        <text class="title">{{ t.title }}</text>
        <text class="meta" v-if="t.status">{{ t.status }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { logger } from '@/logs/logger'
import type { TopicBriefItem } from '@/types/brands'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'

const props = defineProps<{ topics: TopicBriefItem[] }>()
const emit = defineEmits<{ (e:'open', id:string):void }>()

const brokenIds = ref<Record<string, true>>({})

function getTopicCover(t: TopicBriefItem) {
  return resolveCoverUrl(t?.banner_url || '', t?.id ? !!brokenIds.value[t.id] : false)
}

function handleImageError(id: string) {
  if (brokenIds.value[id]) return
  const topic = props.topics.find(item => item.id === id)
  const raw = topic?.banner_url || ''
  if (!shouldMarkCoverBroken(raw, !!brokenIds.value[id])) return
  logger.warn('system', 'topic_image_load_failed', {
    component: 'TopicList',
    imageSlot: 'topic-thumb',
    topicId: id,
    topicTitle: topic?.title || '',
    rawImageUrl: raw
  })
  brokenIds.value = { ...brokenIds.value, [id]: true }
}

function open(id:string){ emit('open', id) }
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.topic-list {
  padding: 0;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
.header {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  padding: 12px var(--spacing-lg) 8px;
  color: var(--color-text-primary);
}
.row {
  display: flex;
  gap: 10px;
  background: var(--color-surface);
  border-radius: 0;
  overflow: hidden;
  margin: 0;
  box-shadow: none;
  border-top: 1px solid var(--color-border);
}
.thumb { width:90px; height:70px; background: var(--color-bg-tertiary); }
.col { flex:1; padding: 10px var(--spacing-lg) 10px 0; }
.title { font-size:13px; color: var(--color-text-primary); }
.meta { font-size:11px; color: var(--color-text-tertiary); margin-top:4px; }
</style>
