<template>
  <view
    class="live-card-row"
    @tap="handleTap"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    @touchcancel="onTouchEnd"
  >
    <!-- 左侧封面 -->
    <view class="card-cover">
      <ProxyImage
        v-if="coverUrl"
        class="cover-image"
        :src="resolvedCoverUrl"
        mode="aspectFill"
      />
      <!-- 封面兜底：浅灰渐变 + 居中播放三角（无封面/加载失败） -->
      <view v-else class="cover-image cover-fallback" />
      <!-- 状态角标（封面左上角） -->
      <text v-if="status" class="status-badge" :class="getStatusClass(status)">{{ getStatusText(status) }}</text>
    </view>

    <!-- 右侧信息 -->
    <view class="card-info">
      <!-- 标题（最多2行） -->
      <text class="card-title">{{ title || '直播标题' }}</text>

      <!-- UP主（专家/创建者）信息 - 后端聚合返回，无数据时不显示 -->
      <view v-if="expertName" class="card-author">
        <ProxyImage
          class="author-avatar"
          :src="expertAvatar || ''"
          :fallback="'/static/default-avatar.png'"
          mode="aspectFill"
        />
        <view class="author-info">
          <text class="author-name">
            {{ expertName }}<text v-if="expertTitle" class="author-title"> | {{ expertTitle }}</text>
          </text>
          <text v-if="expertHospital" class="author-hospital">{{ expertHospital }}</text>
        </view>
      </view>
    </view>

    <!-- 更多操作按钮（右上角） -->
    <view class="more-btn" @tap.stop="emitMore">
      <text class="more-icon">⋮</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { resolveMediaUrl } from '@/utils/url'
import ProxyImage from '@/components/common/ProxyImage.vue'

/**
 * 直播横条卡片（我的收藏/订阅/观看历史统一样式）
 * 字段由后端卡片接口聚合返回，组件只做有值才显示的空值渲染
 */

const LONG_PRESS_DURATION = 500
const MOVE_THRESHOLD = 10

const props = defineProps<{
  /** 封面URL */
  coverUrl?: string
  /** 标题 */
  title?: string
  /** 场次状态（scheduled/live/finished/ready/error 等，有值显示状态角标） */
  status?: string
  /** 专家姓名（后端聚合返回，无专家时为 null） */
  expertName?: string
  /** 专家职称 */
  expertTitle?: string
  /** 专家医院 */
  expertHospital?: string
  /** 专家头像 */
  expertAvatar?: string
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'more'): void
}>()

/** 封面URL：resolveMediaUrl 处理相对路径（后端返回 /uploads/... 需解析为完整地址） */
const resolvedCoverUrl = computed(() => {
  const url = props.coverUrl || ''
  return url ? (resolveMediaUrl(url) || url) : ''
})

// ========== 长按逻辑（500ms + 移动阈值 10rpx） ==========
const longPressTimer = ref<number | null>(null)
const touchStartPos = ref({ x: 0, y: 0 })
const isTouchMoved = ref(false)

function onTouchStart(event: any) {
  const touch = event.touches[0]
  touchStartPos.value = { x: touch.clientX, y: touch.clientY }
  isTouchMoved.value = false

  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
  }

  longPressTimer.value = setTimeout(() => {
    if (!isTouchMoved.value) {
      uni.vibrateShort({ type: 'medium' })
      emit('more')
    }
  }, LONG_PRESS_DURATION) as unknown as number
}

function onTouchMove(event: any) {
  const touch = event.touches[0]
  const deltaX = Math.abs(touch.clientX - touchStartPos.value.x)
  const deltaY = Math.abs(touch.clientY - touchStartPos.value.y)

  if (deltaX > MOVE_THRESHOLD || deltaY > MOVE_THRESHOLD) {
    isTouchMoved.value = true
    if (longPressTimer.value) {
      clearTimeout(longPressTimer.value)
      longPressTimer.value = null
    }
  }
}

function onTouchEnd() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
}

// ========== 事件 ==========
function handleTap() {
  if (longPressTimer.value) {
    return
  }
  emit('click')
}

function emitMore() {
  emit('more')
}

// ========== 状态角标 ==========
// 展示收敛为三态（与首页 RoomCard 对齐）：预告 / 直播中 / 回放
// 后端字段为原始枚举，此处仅做展示映射；error 保留独立以提示异常
function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'scheduled': '预告',
    'live': '直播中',
    'finished': '回放',
    'processing': '回放',
    'ready': '回放',
    'ended': '回放',
    'archived': '回放',
    'replay': '回放',
    'error': '异常'
  }
  return statusMap[status] || status
}

function getStatusClass(status: string): string {
  const classMap: Record<string, string> = {
    'scheduled': 'status-scheduled',
    'live': 'status-live',
    'finished': 'status-replay',
    'processing': 'status-replay',
    'ready': 'status-replay',
    'ended': 'status-replay',
    'archived': 'status-replay',
    'replay': 'status-replay',
    'error': 'status-error'
  }
  return classMap[status] || 'status-replay'
}
</script>

<style lang="scss" scoped>
// ===== 错落淡入动画（与收藏/订阅/历史原视觉一致） =====
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.live-card-row {
  position: relative;
  display: flex;
  align-items: center;
  padding: var(--home-spacing-card, 20rpx);
  background-color: var(--home-card);
  border-radius: var(--home-r-lg);
  margin-bottom: var(--home-spacing-card, 20rpx);
  box-shadow: var(--home-shadow-card);

  // 错落淡入
  opacity: 0;
  transform: translateY(20rpx);
  animation: fadeInUp 0.4s ease-out forwards;
  @for $i from 1 through 20 {
    &:nth-child(#{$i}) {
      animation-delay: #{$i * 0.04}s;
    }
  }

  &:active {
    opacity: 0.9;
    transform: scale(0.98);
    transition: all 0.1s ease;
  }

  .card-cover {
    position: relative;
    width: 240rpx;
    height: 150rpx;
    flex-shrink: 0;
    border-radius: var(--home-r-md);
    overflow: hidden;
    background-color: var(--home-bg);

    .cover-image {
      width: 100%;
      height: 100%;
    }

    /* 封面兜底：浅灰渐变 + 居中灰色播放三角（统一全站） */
    .cover-fallback {
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, #F0F2F5 0%, #E4E8EE 100%);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .cover-fallback::after {
      content: '';
      border-left: 16rpx solid rgba(148, 157, 170, 0.5);
      border-top: 10rpx solid transparent;
      border-bottom: 10rpx solid transparent;
    }

    .status-badge {
      position: absolute;
      top: 8rpx;
      left: 8rpx;
      padding: 2rpx 12rpx;
      border-radius: 4rpx;
      font-size: 20rpx;
      line-height: 1.5;
      z-index: 2;

      &.status-scheduled {
        background: var(--home-primary);
        color: #fff;
      }

      &.status-live {
        background: rgba(220, 38, 38, 0.9);
        color: #fff;
      }

      &.status-ended,
      &.status-replay,
      &.status-finished,
      &.status-processing,
      &.status-ready,
      &.status-archived {
        background: rgba(0, 0, 0, 0.6);
        color: #fff;
      }

      &.status-error {
        background: rgba(0, 0, 0, 0.45);
        color: #fff;
      }
    }
  }

  .card-info {
    flex: 1;
    margin-left: 20rpx;
    margin-right: 60rpx;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-width: 0;

    .card-title {
      font-size: var(--home-fs-card-title, 28rpx);
      color: var(--home-text1);
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
      line-height: 1.4;
      margin-bottom: 12rpx;
      word-break: break-all;
      max-width: 100%;
    }

    .card-author {
      display: flex;
      align-items: center;
      margin-top: auto;

      .author-avatar {
        width: 48rpx;
        height: 48rpx;
        border-radius: 50%;
        background-color: var(--home-bg);
        margin-right: 12rpx;
        flex-shrink: 0;
      }

      .author-info {
        flex: 1;
        overflow: hidden;

        .author-name {
          display: block;
          font-size: var(--home-fs-meta, 24rpx);
          color: var(--home-text1);
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-bottom: 4rpx;
        }

        .author-title {
          color: var(--home-text2);
          font-weight: 400;
        }

        .author-hospital {
          display: block;
          font-size: 22rpx;
          color: var(--home-text2);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .more-btn {
    position: absolute;
    top: 16rpx;
    right: 16rpx;
    width: 48rpx;
    height: 48rpx;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    z-index: 3;

    .more-icon {
      font-size: 32rpx;
      color: var(--home-text2);
      line-height: 1;
    }
  }
}
</style>
