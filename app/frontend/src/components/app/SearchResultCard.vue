<template>
  <view class="search-result-card" @tap="handleClick">
    <!-- 左侧封面 -->
    <view class="card-cover">
      <image
        v-if="coverUrl"
        class="cover-image"
        :src="coverUrl"
        mode="aspectFill"
        @error="handleImageError"
      />
      <!-- 封面兜底：浅灰渐变 + 居中播放三角（兜底图加载异常时的最后防线） -->
      <view v-else class="cover-fallback" />

      <!-- 状态标签（仅直播间） -->
      <text v-if="type === 'room' && statusLabel" class="status-badge" :class="statusClass">{{ statusLabel }}</text>
    </view>

    <!-- 右侧信息 -->
    <view class="card-info">
      <!-- 标题（最多2行） -->
      <text class="card-title">{{ title }}</text>

      <!-- 副标题/描述 -->
      <text v-if="subtitle" class="card-subtitle">{{ subtitle }}</text>

      <!-- 元信息 -->
      <view class="card-meta">
        <!-- 直播间：显示专家头像+信息（专家/创建者/兜底用户均显示头像） -->
        <view v-if="type === 'room' && metaText" class="expert-info">
          <ProxyImage
            class="expert-avatar"
            :src="expertAvatar"
            :fallback="DEFAULT_AVATAR"
            mode="aspectFill"
          />
          <text class="meta-text">{{ metaText }}</text>
        </view>
        <!-- 其他类型：纯文本 -->
        <text v-else-if="metaText" class="meta-text">{{ metaText }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 搜索结果卡片组件（细横条样式）
 * @description 统一的搜索结果卡片，支持直播间、专家、品牌
 */
import { computed, ref } from 'vue';
import { resolveMediaUrl } from '@/utils/url';
import ProxyImage from '@/components/common/ProxyImage.vue';
import { DEFAULT_AVATAR } from '@/constants/assets';
import type { SearchResultItem } from '@/api/search';

interface Props {
  /** 搜索结果项 */
  item: SearchResultItem;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'click', item: SearchResultItem): void;
}>();

/** 资源类型 */
const type = computed(() => props.item.type);

/** 标题 */
const title = computed(() => props.item.title);

/** 副标题（优先 subtitle；品牌类型兜底读取后端 summary=description） */
const subtitle = computed(() =>
  props.item.subtitle ?? (props.item.type === 'brand' ? props.item.summary : '')
);

/** 封面图加载失败标记（失败后切换为对应类型的兜底图） */
const hasImgError = ref(false);

/** 封面URL（无封面或加载失败时按类型返回兜底图） */
const coverUrl = computed(() => {
  if (hasImgError.value) {
    // 默认封面
    if (type.value === 'expert') return '/static/default-avatar.png';
    if (type.value === 'brand') return '/static/tabbar/brand.png';
    return '/static/default-cover.png';
  }
  const url = props.item.cover_url;
  if (!url) {
    // 默认封面
    if (type.value === 'expert') return '/static/default-avatar.png';
    if (type.value === 'brand') return '/static/tabbar/brand.png';
    return '/static/default-cover.png';
  }
  return resolveMediaUrl(url) || url;
});

/** 直播状态 */
const status = computed(() => props.item.metadata?.status);

/** 状态标签文本（值域与后端场次枚举对齐，三态收敛与 LiveCardRow 一致） */
const statusLabel = computed(() => {
  if (type.value !== 'room') return '';

  const st = status.value;
  if (st === 'live') return '直播中';
  if (st === 'scheduled') return '预告';
  if (st === 'finished' || st === 'ended' || st === 'ready' || st === 'processing' || st === 'archived' || st === 'replay') return '回放';
  if (st === 'error') return '异常';
  return '';
});

/** 状态标签 class（对齐后端枚举：回放相关状态统一 status-replay） */
const statusClass = computed(() => {
  const st = status.value;
  if (st === 'live') return 'status-live';
  if (st === 'scheduled') return 'status-scheduled';
  if (st === 'error') return 'status-error';
  return 'status-replay';
});

/** 专家/创建者头像（后端聚合返回，无头像时用兜底图） */
const expertAvatar = computed(() => {
  const url = props.item.metadata?.expert_avatar;
  return url ? (resolveMediaUrl(url) || url) : '';
});

/** 元信息文本（直播间：专家姓名 | 职称 | 医院；创建者/兜底用户同样拼接） */
const metaText = computed(() => {
  if (type.value === 'room') {
    // 直播间：显示专家姓名 + 职称 + 医院
    const expertName = props.item.metadata?.expert_name;
    const expertTitle = props.item.metadata?.expert_title;
    const expertHospital = props.item.metadata?.expert_hospital;

    const parts: string[] = [];

    if (expertName) {
      // 有姓名，拼接 姓名 | 职称 | 医院
      parts.push(expertName);
      if (expertTitle) parts.push(expertTitle);
      if (expertHospital) parts.push(expertHospital);
    } else {
      // 无姓名，显示职称+医院
      if (expertTitle) parts.push(expertTitle);
      if (expertHospital) parts.push(expertHospital);
    }

    return parts.join(' | ');
  } else if (type.value === 'expert') {
    // 专家：显示职称·医院
    const title = props.item.metadata?.title;
    const hospital = props.item.metadata?.hospital;
    if (title && hospital) return `${title} · ${hospital}`;
    if (title) return title;
    if (hospital) return hospital;
    return '';
  } else if (type.value === 'brand') {
    // 品牌：显示副标题或无元信息
    return '';
  }
  return '';
});

/**
 * 图片加载失败处理（切换为对应类型的兜底图）
 */
const handleImageError = () => {
  console.warn('[SearchResultCard] 图片加载失败:', props.item.cover_url);
  hasImgError.value = true;
};

/**
 * 点击事件
 */
const handleClick = () => {
  emit('click', props.item);
};
</script>

<style scoped lang="scss">
.search-result-card {
  display: flex;
  padding: 24rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #F0F0F0;
  gap: 24rpx;
}

.card-cover {
  position: relative;
  width: 240rpx;
  height: 135rpx;
  flex-shrink: 0;
  border-radius: 12rpx;
  overflow: hidden;
  background: #F5F5F5;
}

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
  color: #fff;
  z-index: 2;
}

.status-live {
  background: rgba(220, 38, 38, 0.9);
}

.status-scheduled {
  background: var(--home-primary);
}

.status-replay {
  background: rgba(0, 0, 0, 0.6);
}

.status-error {
  background: rgba(0, 0, 0, 0.45);
}

.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.card-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}

.card-subtitle {
  font-size: 24rpx;
  color: #999;
  line-height: 1.4;
  margin-top: 8rpx;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expert-info {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.expert-avatar {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #f5f5f5;
  flex-shrink: 0;
}

.card-meta {
  margin-top: 8rpx;
}

.meta-text {
  font-size: 24rpx;
  color: #666;
  line-height: 1.4;
}
</style>
