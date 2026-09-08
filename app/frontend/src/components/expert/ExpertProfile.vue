<template>
  <view class="expert-profile">
    <view class="header">
      <image 
        class="avatar" 
        :src="avatarSrc" 
        mode="aspectFill"
        @error="handleAvatarError"
      />
      <view class="info">
        <view class="name-row">
          <text class="name">{{ name }}</text>
          <text v-if="formattedTitle" class="title-text">{{ formattedTitle }}</text>
        </view>
        <view v-if="hospital" class="meta-line">{{ hospital }}</view>
        <view v-if="categoryDeptParts.length" class="meta-line">{{ categoryDeptParts.join(' | ') }}</view>
      </view>
      <view
        class="follow-button"
        :class="{ followed: isFollowing, disabled: pending }"
        role="button"
        :aria-label="isFollowing ? '已关注' : '关注'"
        :aria-pressed="isFollowing"
        @tap="onToggle"
      >
        <text class="follow-text">{{ isFollowing ? '已关注' : '关注' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 专家资料卡片组件
 * @description 展示专家头像、姓名、职称、科室和统计信息；关注为 Star 图标（与列表页一致）
 */
import { ref, watch, computed, onMounted } from 'vue';
import { loadImageWithProxy } from '@/utils/imageProxy';

interface Props {
  avatar: string;
  name: string;
  /** 职称（原始，组件内格式化为 职称 | 博导） */
  title: string;
  /** 所在医院（选填，与职称同排展示：职称 | 医院） */
  hospital?: string;
  department: string;
  category?: string;
  isFollowing?: boolean;
  pending?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  hospital: '',
  isFollowing: false,
  pending: false
});

/** 职称简洁：逗号改竖线，博士生导师→博导（与 ExpertCard 一致） */
const formattedTitle = computed(() => {
  if (!props.title) return '';
  return props.title
    .replace(/，/g, ' | ')
    .replace(/,/g, ' | ')
    .replace(/博士生导师/g, '博导')
    .replace(/硕士生导师/g, '硕导')
    .trim();
});

/** 分类 | 科室 组合：缺省字段自动跳过 */
const categoryDeptParts = computed(() => {
  const parts: string[] = [];
  if (props.category) parts.push(props.category);
  if (props.department) parts.push(props.department);
  return parts;
});

const emit = defineEmits<{
  (e: 'toggle-follow'): void;
}>();

// 默认头像（使用data URI避免文件不存在问题）
const DEFAULT_AVATAR = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1zaXplPSIxNCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+5rOo5YyI5aS06LGhPC90ZXh0Pjwvc3ZnPg==';

// 当前显示的头像URL
const avatarSrc = ref(DEFAULT_AVATAR);
// 是否正在代理加载头像
const isLoadingProxy = ref(false);

/**
 * 🔥 使用图片代理加载头像（与 ExpertCard 一致）
 */
async function loadAvatar(url: string) {
  if (!url) {
    avatarSrc.value = DEFAULT_AVATAR;
    return;
  }

  // 检查是否为外部URL（需要代理）
  const isExternal = /^https?:\/\//i.test(url);
  
  if (isExternal) {
    // 外部URL：先显示默认头像，然后代理加载
    avatarSrc.value = DEFAULT_AVATAR;
    isLoadingProxy.value = true;
    
    try {
      const proxyUrl = await loadImageWithProxy(url);
      if (proxyUrl) {
        avatarSrc.value = proxyUrl;
      } else {
        // 代理加载失败，保持默认头像
        console.warn('[ExpertProfile] 头像代理加载失败');
      }
    } catch (e) {
      console.error('[ExpertProfile] 头像代理加载异常:', e);
    } finally {
      isLoadingProxy.value = false;
    }
  } else {
    // 本地URL：直接使用
    avatarSrc.value = url;
  }
}

// 组件挂载时加载头像
onMounted(() => {
  loadAvatar(props.avatar);
});

// 监听avatar prop变化
watch(() => props.avatar, (newAvatar) => {
  loadAvatar(newAvatar);
});

/**
 * 头像加载失败处理
 */
function handleAvatarError() {
  console.warn('[ExpertProfile] 头像加载失败，使用默认头像');
  avatarSrc.value = DEFAULT_AVATAR;
}

/**
 * 切换关注状态
 */
function onToggle() {
  if (!props.pending) {
    emit('toggle-follow');
  }
}
</script>

<style lang="scss" scoped>
/* 去卡片化：无独立背景，融入 ConsumerLayout 单背景 */
.expert-profile {
  background: transparent;
  padding: var(--home-spacing-module) 0;
}

.header {
  display: flex;
  align-items: flex-start;
}

.avatar {
  width: 144rpx;
  height: 144rpx;
  border-radius: 50%;
  background: var(--home-bg);
  border: 1.5rpx solid var(--home-border);
  flex-shrink: 0;
}

.info {
  flex: 1;
  min-width: 0;
  margin: 0 var(--home-spacing-module);
}

.name-row {
  display: flex;
  align-items: baseline;
  gap: var(--home-spacing-inner);
  line-height: var(--expert-name-lineheight);
  min-height: var(--expert-name-lineheight);
  flex-wrap: wrap;
}

.name {
  font-size: var(--home-fs-banner);
  font-weight: 600;
  color: var(--home-text1);
}

/* 职称：与名字同行，次字号次级色，形成层级 */
.title-text {
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

/* 医院 / 分类|科室 信息行 */
.meta-line {
  margin-top: 6rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  display: block;
}

/* 文字关注按钮，与列表页保持一致，避免和直播收藏星标产生语义冲突 */
.follow-button {
  min-width: 104rpx;
  height: 52rpx;
  padding: 0 16rpx;
  box-sizing: border-box;
  margin-top: calc((var(--expert-name-lineheight) - 52rpx) / 2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
  background: var(--home-primary);
  border: 1rpx solid var(--home-primary);
  color: #fff;
  transition: transform 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}

.follow-button.followed {
  background: transparent;
  border-color: var(--home-border);
  color: var(--home-text2);
}

.follow-button.disabled {
  opacity: 0.5;
}

.follow-button:active {
  transform: scale(0.96);
}

.follow-text {
  font-size: var(--home-fs-meta);
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
}

.follow-button:focus-visible {
  outline: 2rpx solid var(--home-primary);
  outline-offset: 4rpx;
}
</style>
