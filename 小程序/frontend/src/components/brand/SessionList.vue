<!-- 本版未挂页面：品牌相关场次列表（可后续接入详情） -->
<template>
  <view class="session-list">
    <view class="header">相关直播</view>
    <view v-for="s in sessions" :key="s.id" class="row" @tap="open(s.id)">
      <view class="col">
        <text class="title">{{ s.title }}</text>
        <text class="meta">{{ s.schedule_time || s.start_time }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const props = defineProps<{ sessions: Array<any> }>()
const emit = defineEmits<{ (e:'open', id:string):void }>()
function open(id:string){ emit('open', id) }
</script>

<style scoped lang="scss">
@import '@/common/uni.scss';

.session-list {
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
  padding: 10px var(--spacing-lg);
  box-shadow: none;
  border-top: 1px solid var(--color-border);
}
.col { flex:1; }
.title { font-size:13px; color: var(--color-text-primary); }
.meta { font-size:11px; color: var(--color-text-tertiary); margin-top:4px; }
</style>
