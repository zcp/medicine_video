<template>
  <view class="expert-list-item" @tap="$emit('click')">
    <view class="left">
      <image 
        class="avatar" 
        :src="avatarSrc" 
        mode="aspectFill"
        lazy-load
        @error="handleAvatarError"
      />
    </view>
    <view class="content">
      <view class="name-row">
        <view class="name-block">
          <text class="name">{{ name }}</text>
          <text class="title">{{ formattedTitle }}</text>
        </view>
      </view>
      <text v-if="hospital" class="hospital">{{ hospital }}</text>
      <view v-if="specializationText" class="specialization">
        <text class="spec-label">擅长：</text>
        <text class="spec-text">{{ specializationText }}</text>
      </view>
      <view v-else-if="stats" class="stats">
        <text class="stat">粉丝 {{ stats?.followers ?? 0 }}</text>
        <text class="dot">·</text>
        <text class="stat">直播 {{ stats?.sessions ?? 0 }}</text>
      </view>
    </view>
    <view class="action-col">
      <view
        class="follow-button"
        :class="{ followed: isFollowing, disabled: pending }"
        role="button"
        :aria-label="isFollowing ? '已关注' : '关注'"
        :aria-pressed="isFollowing"
        @tap.stop="onToggle"
      >
        <text class="follow-text">{{ isFollowing ? '已关注' : '关注' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 专家卡片组件
 * @description 展示专家头像、姓名、职称、科室、统计信息和关注按钮
 */
import { ref, watch, computed, onMounted } from 'vue';
import { loadImageWithProxy } from '@/utils/imageProxy';

interface Stats {
  followers: number;
  sessions: number;
}

interface Props {
  /** 头像URL */
  avatar: string;
  /** 专家姓名 */
  name: string;
  /** 职称（原始，组件内格式化为 职称 | 博导） */
  title: string;
  /** 所在医院 */
  hospital?: string;
  /** 擅长领域（优先展示，替代粉丝/直播/观看） */
  specialization?: string[];
  /** 统计信息 */
  stats?: Stats;
  /** 是否已关注 */
  isFollowing?: boolean;
  /** 是否正在处理 */
  pending?: boolean;
}

const props = defineProps<Props>();

/** 职称简洁：逗号改竖线，博士生导师→博导 */
const formattedTitle = computed(() => {
  if (!props.title) return '';
  return props.title
    .replace(/，/g, ' | ')
    .replace(/,/g, ' | ')
    .replace(/博士生导师/g, '博导')
    .replace(/硕士生导师/g, '硕导')
    .trim();
});

/** 擅长领域展示文案 */
const specializationText = computed(() => {
  const arr = props.specialization;
  if (!arr?.length) return '';
  return arr.join('、');
});

const emit = defineEmits<{
  (e: 'click'): void;
  (e: 'toggle-follow'): void;
}>();

// 默认头像（使用data URI避免文件不存在问题）
const DEFAULT_AVATAR = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1zaXplPSIxNCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+5rOo5YyI5aS06LGhPC90ZXh0Pjwvc3ZnPg==';

// 当前显示的头像URL（初始化为默认头像，避免直接加载外部URL触发防盗链错误）
const avatarSrc = ref(DEFAULT_AVATAR);

// 是否正在加载代理图片
const isLoadingProxy = ref(false);

/**
 * 加载头像（支持外部URL代理）
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
        console.info('[ExpertCard] ✅ 头像代理成功');
        console.info('[ExpertCard] 完整路径:', proxyUrl);
        
        // 🔥 测试：检查文件是否真实存在
        // @ts-ignore
        if (typeof plus !== 'undefined' && plus.io) {
          try {
            // @ts-ignore
            const realPath = proxyUrl.replace('file://', '');
            // @ts-ignore
            plus.io.resolveLocalFileSystemURL(realPath, (entry) => {
              console.info('[ExpertCard] ✅ 文件确认存在:', entry.fullPath);
            }, (e) => {
              console.error('[ExpertCard] ❌ 文件不存在或无法访问:', e.message);
            });
          } catch (e) {
            console.error('[ExpertCard] 文件检查异常:', e);
          }
        }
        
        avatarSrc.value = proxyUrl;
        console.info('[ExpertCard] avatarSrc已更新为:', proxyUrl.substring(0, 80));
      } else {
        // 代理加载失败，保持默认头像
        console.warn('[ExpertCard] 头像代理加载失败，返回null');
      }
    } catch (e) {
      console.error('[ExpertCard] 头像代理加载异常:', e);
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
function handleAvatarError(e: any) {
  const currentSrc = avatarSrc.value;
  console.error('[ExpertCard] ❌ Image组件加载失败');
  console.error('[ExpertCard] 失败的src:', currentSrc);
  console.error('[ExpertCard] 错误详情:', JSON.stringify(e?.detail || e));
  
  // 避免重复设置导致循环
  if (currentSrc !== DEFAULT_AVATAR) {
    console.warn('[ExpertCard] 回退到默认头像');
    avatarSrc.value = DEFAULT_AVATAR;
  } else {
    console.error('[ExpertCard] 默认头像也加载失败，可能是data URI问题');
  }
}

function onToggle() {
  emit('toggle-follow');
}
</script>

<style lang="scss" scoped>
.expert-list-item {
  position: relative;
  display: grid;
  grid-template-columns: 96rpx 1fr var(--expert-action-col-width);
  column-gap: var(--home-spacing-module);
  align-items: start;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.04);
  min-height: 88rpx;
  box-sizing: border-box;
}

.left {
  grid-column: 1;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: var(--home-bg);
  flex-shrink: 0;
}

.content {
  grid-column: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.name-row {
  display: flex;
  align-items: baseline;
  gap: var(--home-spacing-inner);
}

.name-block {
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: var(--home-spacing-inner);
}

.name {
  font-size: var(--home-fs-section);
  font-weight: 600;
  line-height: var(--expert-name-lineheight);
  color: var(--home-text1);
}

.title {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

.hospital {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.85;
  margin-top: 4rpx;
  display: block;
}

.specialization {
  display: flex;
  align-items: flex-start;
  margin-top: 6rpx;
}

.spec-label {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.9;
  flex-shrink: 0;
}

.spec-text {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.9;
  line-height: 1.35;
}

.stats {
  display: flex;
  align-items: center;
  margin-top: 6rpx;
}

.stat {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

.dot {
  margin: 0 6rpx;
  color: var(--home-text2);
  opacity: 0.5;
}

/* Action Column：固定栏位，文字按钮对齐 name-row 视觉中心 */
.action-col {
  grid-column: 3;
  width: var(--expert-action-col-width);
  display: flex;
  justify-content: flex-end;
  margin-top: calc((var(--expert-name-lineheight) - 52rpx) / 2);
}

.follow-button {
  min-width: 104rpx;
  height: 52rpx;
  padding: 0 16rpx;
  box-sizing: border-box;
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
