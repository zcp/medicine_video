<template>
  <view class="empty-state">
    <image v-if="icon" :src="icon" mode="aspectFit" class="empty-icon" />
    <text class="title">{{ title }}</text>
    <text v-if="description" class="desc">{{ description }}</text>
  </view>
</template>

<script setup lang="ts">
defineProps<{ title: string; description?: string; icon?: string }>()
</script>

<style scoped lang="scss">
.empty-state {
  padding: var(--spacing-xl);
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-icon {
  width: 120px;
  height: 120px;
  margin-bottom: var(--spacing-base);
  opacity: 0.8;
}

.title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.desc {
  display: block;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-top: 6px;
}
</style>
