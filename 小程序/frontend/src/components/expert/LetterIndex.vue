<template>
  <view class="letter-index" aria-label="字母索引">
    <view class="letters">
      <text
        v-for="(l, i) in letters"
        :key="i"
        class="letter"
        :class="{ active: l === active }"
        @tap="pick(l)"
        :aria-label="`跳转字母：${l}`"
      >{{ l }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ letters?: string[]; active?: string }>(), {
  letters: () => Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
  active: ''
})
const emit = defineEmits<{ (e: 'pick', letter: string): void }>()
function pick(letter: string) { emit('pick', letter) }
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.letter-index {
  display: block;
  max-height: 100%;
  padding: 2px 1px;
  overflow: hidden;
}
.letters {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}
.letter {
  font-size: 11px;
  line-height: 1.1;
  color: var(--color-text-regular);
  padding: 3px 5px;
  border-radius: var(--border-radius-full);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: none;
}
.letter.active {
  color: var(--color-primary);
  font-weight: 700;
  background: var(--color-primary-soft-strong);
}
</style>
