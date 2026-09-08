<!--
 * ExpertCard - 专家卡片组件
 * @description 展示专家信息的卡片组件
 * @author 直播SaaS团队
 -->
<template>
  <view class="expert-card" @click="handleClick">
    <image
      v-if="!avatarShowIcon"
      class="expert-card__avatar"
      :src="avatarSrc"
      mode="aspectFill"
      @error="onAvatarError"
    />
    <view v-else class="expert-card__avatar-placeholder">
      <uni-icons type="person" size="32" :color="'var(--color-text-tertiary)'" />
    </view>
    
    <!-- 专家信息 -->
    <view class="expert-card__info">
      <text class="expert-card__name">{{ name }}</text>
      <text v-if="title" class="expert-card__title">{{ title }}</text>
      <text v-if="hospital" class="expert-card__hospital">{{ hospital }}</text>
    </view>
    
    <!-- 关注按钮 -->
    <view class="expert-card__action">
      <AppButton
        size="small"
        :type="isFollowed ? 'secondary' : 'primary'"
        :text="isFollowed ? '已关注' : '+关注'"
        @click.stop="handleFollow"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppButton from './AppButton.vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

/**
 * 组件Props定义
 */
interface Props {
  /** 专家ID */
  id: string
  /** 专家姓名 */
  name: string
  /** 专家头像 */
  avatar?: string
  /** 职称 */
  title?: string
  /** 医院 */
  hospital?: string
  /** 是否已关注 */
  isFollowed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isFollowed: false
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击事件 */
  click: [id: string]
  /** 关注/取消关注事件 */
  follow: [id: string, isFollowed: boolean]
}>()

const avatarBroken = ref(false)
const avatarShowIcon = ref(false)

const avatarSrc = computed(() => resolveAvatarUrl(props.avatar, avatarBroken.value))

watch(
  () => props.avatar,
  () => {
    avatarBroken.value = false
    avatarShowIcon.value = false
  }
)

const handleClick = () => {
  emit('click', props.id)
}

function onAvatarError() {
  if (avatarShowIcon.value) return
  if (avatarBroken.value || !shouldMarkAvatarBroken(props.avatar, avatarBroken.value)) {
    avatarShowIcon.value = true
    return
  }
  avatarBroken.value = true
}

const handleFollow = () => {
  emit('follow', props.id, !props.isFollowed)
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: var(--color-bg-primary);
  border-radius: 8px;
  cursor: pointer;
  
  &__avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: var(--color-bg-tertiary);
  }
  
  &__avatar-placeholder {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: var(--color-bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  &__info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  &__name {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
  
  &__title {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
  
  &__hospital {
    font-size: 12px;
    color: var(--color-text-tertiary);
  }
  
  &__action {
    flex-shrink: 0;
  }
}
</style>
