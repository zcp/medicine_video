<template>
  <!-- B站风格全页式头像预览：无遮罩，纯黑背景，X 关闭，底部操作 -->
  <view v-if="visible" class="avatar-preview">
    <!-- 顶部 X 关闭按钮 -->
    <view class="avatar-preview__topbar">
      <view class="avatar-preview__close" @tap="handleClose">
        <text class="iconfont icon-close close-icon"></text>
      </view>
    </view>

    <!-- 中间图片展示区 -->
    <view class="avatar-preview__content">
      <view v-if="resolvedSrc" class="avatar-preview__frame">
        <image
          class="avatar-preview__image"
          :src="resolvedSrc"
          mode="widthFix"
          @load="handleLoad"
          @error="handleError"
        />
      </view>

      <view v-else class="avatar-preview__empty">
        <text class="avatar-preview__empty-text">{{ emptyReason }}</text>
      </view>
    </view>

    <!-- 底部操作按钮区 -->
    <view class="avatar-preview__actions">
      <button class="avatar-preview__action-btn avatar-preview__action-btn--primary" @tap="handleChangeAvatar">
        更换头像
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { resolveMediaUrl } from '@/utils/url';

interface Props {
  visible: boolean;
  src?: string | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
  (e: 'change-avatar'): void;
}>();

const fallbackFailed = ref(false);
const emptyReason = ref('暂无可预览头像');

watch(
  () => props.src,
  (newSrc, oldSrc) => {
    console.log('[AvatarPreview] 📸 src变化:', { old: oldSrc, new: newSrc });
    fallbackFailed.value = false;
    emptyReason.value = '暂无可预览头像';
  }
);

watch(
  () => props.visible,
  (newVisible) => {
    console.log('[AvatarPreview] 👁️ visible变化:', {
      visible: newVisible,
      src: props.src
    });
  }
);

const resolvedSrc = computed(() => {
  if (fallbackFailed.value) {
    console.log('[AvatarPreview] ⚠️ 之前加载失败，返回空');
    return '';
  }
  const src = props.src || '';
  if (!src) {
    console.log('[AvatarPreview] ❌ src为空');
    emptyReason.value = '头像地址为空';
    return '';
  }
  const resolved = resolveMediaUrl(src) || src;
  console.log('[AvatarPreview] 🔗 解析头像URL:', { 原始src: src, 解析后: resolved });
  return resolved;
});

function handleClose() {
  emit('update:visible', false);
}

function handleChangeAvatar() {
  emit('update:visible', false);
  emit('change-avatar');
}

function handleLoad(e: any) {
  console.log('[AvatarPreview] ✅ 图片加载成功:', e.detail);
}

function handleError(e: any) {
  console.error('[AvatarPreview] ❌ 图片加载失败:', {
    src: resolvedSrc.value,
    errMsg: e?.detail?.errMsg || '未知错误'
  });
  emptyReason.value = '图片加载失败，请检查网络';
  fallbackFailed.value = true;
}
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

// ===== B站风格全页式头像预览 =====
.avatar-preview {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  background: #000; // 纯黑背景，与B站一致
  animation: previewFadeIn $motion-normal both;
}

@keyframes previewFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

// 顶部 X 关闭按钮
.avatar-preview__topbar {
  display: flex;
  align-items: center;
  padding: calc(env(safe-area-inset-top) + 12rpx) $spacing-lg 0;
  height: calc(env(safe-area-inset-top) + 88rpx);
  box-sizing: border-box;
  flex-shrink: 0;
}

.avatar-preview__close {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity $motion-fast, transform $motion-fast;

  &:active {
    opacity: 0.6;
    transform: scale(0.92);
  }
}

.close-icon {
  font-size: 32rpx;
  color: #fff;
}

// 中间图片展示区
.avatar-preview__content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;
  overflow: hidden;
}

.avatar-preview__frame {
  width: 80vw;
  max-width: 600rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-preview__image {
  width: 100%;
  display: block;
}

.avatar-preview__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.avatar-preview__empty-text {
  color: $color-text-on-dark-secondary;
  font-size: $font-md;
}

// 底部操作按钮区
.avatar-preview__actions {
  flex-shrink: 0;
  padding: $spacing-lg $spacing-xl;
  padding-bottom: calc(env(safe-area-inset-bottom) + $spacing-xl);
  display: flex;
  gap: $spacing-md;
}

.avatar-preview__action-btn {
  flex: 1;
  height: $touch-target-min;
  border-radius: 44rpx;
  border: none;
  font-size: $font-md;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity $motion-fast, transform $motion-fast;

  &--primary {
    background: $color-primary;
    color: $color-text-white;
    box-shadow: $shadow-button-primary;

    &:active {
      opacity: 0.88;
      transform: scale(0.97);
    }
  }
}
</style>
