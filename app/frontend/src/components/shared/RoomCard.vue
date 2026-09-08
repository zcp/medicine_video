<template>
  <view 
    class="room-card"
    :class="{ 'card-pressing': isPressing }"
    @touchstart="isPressing = true" 
    @touchend="isPressing = false"
    @touchcancel="isPressing = false"  
    @click="handleClick"
  >
    <!-- 封面图区域 -->
    <view class="cover-wrapper" :class="{ 'cover-placeholder': isScheduled && !hasCover }">
      <image 
        v-if="hasCover"
        :src="resolveMediaUrl(room.cover_url) || room.cover_url || defaultCover" 
        class="cover-image"
        mode="aspectFill"
        lazy-load
      />
      <view v-else class="cover-image cover-fallback" />

      <!-- 封面底部：仅预告显示开播时间（直播/回放无任何统计） -->
      <view v-if="getCoverRightStat()" class="cover-stats">
        <view class="stat-right">
          <text class="stat-text">{{ getCoverRightStat() }}</text>
        </view>
      </view>
    </view>

    <!-- 直播间信息区域 -->
    <view class="room-info">
      <view class="room-title">{{ room.title }}</view>

      <!-- 主讲人信息（所有状态都显示） -->
      <view v-if="hostInfo" class="host-info">
        <ProxyImage
          v-if="hasRealAvatar"
          class="host-avatar" 
          :src="getHostAvatar(hostInfo)" 
          :fallback="DEFAULT_AVATAR"
          mode="aspectFill"
        />
        <image v-else class="host-avatar" src="/static/default-avatar.png" mode="aspectFill" />
        <view class="host-text">
          <view class="host-line1">
            <text class="host-name">{{ hostInfo.name }}</text>
            <text v-if="hostInfo.title" class="host-title"> | {{ hostInfo.title }}</text>
          </view>
          <view v-if="hostInfo.hospital" class="host-line2">
            {{ hostInfo.hospital }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { resolveMediaUrl } from '@/utils/url';
import ProxyImage from '@/components/common/ProxyImage.vue';
import type { HomepageRoomItem, HomepageHost } from '@/types/homepage';
import { DEFAULT_AVATAR } from '@/constants/assets';

/**
 * 直播卡片组件（首页专用版）
 * @description 用于展示首页直播间信息，参考Bilibili移动端视频卡片设计
 */
const props = defineProps<{
  /** 直播间数据（首页专用类型） */
  room: HomepageRoomItem;
}>();

const emit = defineEmits<{
  (e: 'click'): void;
}>();

/** 默认封面（医疗风格占位，避免破坏专业感） */
const defaultCover = '/static/med/cover_placeholder.png';

/** 卡片点击态 */
const isPressing = ref(false);

/** 是否有封面图（预告无图时用渐变占位，以后端返回为准） */
const hasCover = computed(() => !!props.room.cover_url);

/** 是否为预告 */
const isScheduled = computed(() => props.room.live_status === 'scheduled');

/** 是否有真实头像（无则隐藏头像或显示认证 icon） */
const hasRealAvatar = computed(() => {
  const h = props.room.host as any;
  return !!(h && (h.avatar_url || h.avatar));
});

/**
 * 格式化预告时间
 * @example "2026-01-28T10:00:00Z" → "明天 10:00" 或 "01-28 10:00"
 */
const formatScheduledTime = (isoString: string): string => {
  const date = new Date(isoString);
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const dayDiff = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  const timeStr = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  
  if (dayDiff === 0) return `今天 ${timeStr} 开播`;
  if (dayDiff === 1) return `明天 ${timeStr} 开播`;
  if (dayDiff === -1) return `昨天 ${timeStr}`;
  
  return `${date.getMonth() + 1}-${date.getDate()} ${timeStr} 开播`;
};

/**
 * 获取主讲人信息（由后端聚合返回：有专家=第一专家，无专家=创建者，前端不猜测不造假）
 */
const hostInfo = computed<HomepageHost | null>(() => {
  if (props.room.host && props.room.host.name) {
    return props.room.host;
  }
  return null;
});

/**
 * 获取主讲人头像
 */
const getHostAvatar = (host: HomepageHost | null): string => {
  if (!host) return DEFAULT_AVATAR;
  return resolveMediaUrl(host.avatar_url || host.avatar) || DEFAULT_AVATAR;
};

/**
 * 获取封面底部统计信息
 * @description 仅预告显示开播时间；直播/回放无任何统计（需求：不显示观看数/播放量/时长）
 * 后端未提供开播时间时返回空（不渲染），不伪造
 */
const getCoverRightStat = (): string => {
  // 预告：显示开始时间（简短格式）
  if (props.room.live_status === 'scheduled') {
    const startTime = props.room.status_data?.start_time;
    if (startTime) {
      return formatScheduledTime(startTime);
    }
    return '';
  }

  return '';
};

/**
 * 卡片点击事件处理
 */
const handleClick = () => {
  emit('click');
};
</script>

<style scoped lang="scss">
/* 直播卡片（与首页/登录统一设计语言） */
.room-card {
  display: flex;
  flex: 1;
  flex-direction: column;
  background-color: var(--home-card);
  border-radius: var(--home-r-lg);
  overflow: hidden;
  border: 1px solid var(--home-border-light);
  box-shadow: var(--home-shadow-card);
  
  &.card-pressing {
    opacity: 0.9;
  }
}

.cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 52%;
  overflow: hidden;
}

.cover-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--home-border);
}

/* 封面兜底：浅灰渐变 + 居中灰色播放三角（统一全站） */
.cover-fallback {
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

.cover-wrapper.cover-placeholder .cover-stats {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.35), transparent);
}

/* 封面底部统计（仅预告开播时间使用） */
.cover-stats {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10rpx 12rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, rgba(0, 0, 0, 0.3) 50%, transparent 100%);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  z-index: 2;

  .stat-right {
    display: flex;
    align-items: center;
    gap: 6rpx;
    padding: 6rpx 12rpx;
    background: rgba(0, 0, 0, 0.45);
    border-radius: var(--home-r-pill);
  }

  .stat-text {
    font-size: var(--home-tag-font);
    color: #ffffff;
    font-weight: 500;
    text-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.8);
    line-height: 1;
  }
}

/* 信息区域：标题更突出、meta 更克制，间距 6rpx */
.room-info {
  padding: 10rpx 12rpx;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.room-title {
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-text1);
  line-height: 1.35;
  min-height: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}

.host-info {
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  min-height: 44rpx;
}

.host-avatar {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background-color: var(--home-border);
}

.host-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.host-line1 {
  font-size: 24rpx;
  color: var(--home-text2);
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  
  .host-name {
    color: var(--home-text1);
    font-weight: 500;
  }
  
  .host-title {
    color: var(--home-text2);
  }
}

.host-line2 {
  font-size: 22rpx;
  color: var(--home-text2);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
