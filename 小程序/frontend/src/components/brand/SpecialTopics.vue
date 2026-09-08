<!-- 本版不接入：专区专题推荐（专题能力整版暂缓） -->
<template>
  <view class="special-topics">
    <view class="header">专题推荐</view>
    <view class="list">
      <view class="topic" v-for="t in topics" :key="t.id" @tap="onOpen(t.id)">
        <image class="cover" :src="getTopicCover(t)" mode="aspectFill" :lazy-load="true" @error="handleImageError(t.id)" />
        <view class="title">{{ t.title }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { logger } from '@/logs/logger'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'

const props = defineProps<{ topics: Array<{ id:string; title:string; cover_url?:string; banner_url?:string }> }>()
const emit = defineEmits<{ (e:'open', id:string):void }>()

const brokenIds = ref<Record<string, true>>({})

function getTopicCover(t: { id: string; cover_url?: string; banner_url?: string }) {
  const raw = t?.cover_url || t?.banner_url || ''
  return resolveCoverUrl(raw, t?.id ? !!brokenIds.value[t.id] : false)
}

function handleImageError(id: string) {
  if (brokenIds.value[id]) return
  const topic = props.topics.find(item => item.id === id)
  const raw = topic?.cover_url || topic?.banner_url || ''
  if (!shouldMarkCoverBroken(raw, !!brokenIds.value[id])) return
  logger.warn('system', 'special_topic_image_load_failed', {
    component: 'SpecialTopics',
    imageSlot: 'special-topic-cover',
    topicId: id,
    topicTitle: topic?.title || '',
    rawImageUrl: raw
  })
  brokenIds.value = { ...brokenIds.value, [id]: true }
}

function onOpen(id:string){ emit('open', id) }
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.special-topics {
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
.list { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 0 var(--spacing-lg) 12px; }
.topic {
  background: var(--color-surface);
  border-radius: 0;
  overflow: hidden;
  box-shadow: none;
  border: 1px solid var(--color-border);
}
.cover { width: 100%; height: 90px; background: var(--color-bg-tertiary); }
.title { font-size: 12px; padding: 6px 8px; color: var(--color-text-primary); }
</style>
