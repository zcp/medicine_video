<template>
  <view class="authority-strip">
    <view class="strip-header">
      <text class="strip-title">精选专家</text>
    </view>
    <scroll-view class="expert-scroll" scroll-x :show-scrollbar="false">
      <view class="expert-list">
        <view
          v-for="expert in expertList"
          :key="expert.id"
          class="expert-card"
          @tap="handleExpertClick(expert)"
        >
          <!-- 头部：头像 + 姓名 + 职称|科室 -->
          <view class="expert-head">
            <ProxyAvatarImage
              :src="expert.avatar_url || ''"
              shape="circle"
              size="72rpx"
              class="expert-avatar"
            />
            <!-- 右侧信息区 -->
            <view class="expert-info">
              <text class="expert-name">{{ expert.name }}</text>
              <text v-if="metaTextOf(expert)" class="expert-meta">{{ metaTextOf(expert) }}</text>
            </view>
          </view>
          <!-- 擅长领域：头部块下方整行展示，从头像底缘附近起、横贯全宽 -->
          <text v-if="skillsOf(expert)" class="expert-skills">{{ skillsOf(expert) }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 精选专家横滑模块（与 TabBar「专家」入口区分：本周精选）
 * 展示认证专家卡片，增强医疗权威感
 */
import { ref, onMounted } from 'vue';
import { getFeaturedExperts } from '@/api/expert';
import type { Expert } from '@/types/expert';
import ProxyAvatarImage from '@/components/common/ProxyAvatarImage.vue';

const emit = defineEmits<{ (e: 'expertClick', expert: Expert): void }>();

/** 从 API 拉取的完整专家池 */
const allExperts = ref<Expert[]>([]);
/** 当前展示的 6 位专家（每次 shuffle 随机取） */
const expertList = ref<Expert[]>([]);

const DISPLAY_COUNT = 6;

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pickRandom(): void {
  expertList.value = shuffle(allExperts.value).slice(0, DISPLAY_COUNT);
}

/**
 * 职称取第一个（按常见分隔符拆分），多个职称只显示首个
 */
const firstTitleOf = (expert: Expert): string => {
  if (!expert.title) return '';
  const first = expert.title
    .split(/[，,、;；/|｜]/)
    .map(s => s.trim())
    .filter(Boolean)[0];
  return first || '';
};

/**
 * 科室：优先标准科室名称（受控词表），无则回退自由文本科室首段
 */
const deptOf = (expert: Expert): string => {
  const name = expert.department_name?.trim();
  if (name) return name;
  const legacy = (expert.department || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  return legacy[0] || '';
};

/**
 * 职称（首个）| 科室：单行并排，小字号压入一行，超宽时尾部省略
 */
const metaTextOf = (expert: Expert): string => {
  const title = firstTitleOf(expert);
  const dept = deptOf(expert);
  if (title && dept) return `${title} | ${dept}`;
  return title || dept || '';
};

/**
 * 擅长领域：逗号拆分为顿号文案（与专家列表页/搜索页解析一致）
 */
const skillsOf = (expert: Expert): string => {
  const areas = (expert.expertise_areas || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  return areas.length ? `擅长：${areas.join('、')}` : '';
};

onMounted(async () => {
  try {
    const res = await getFeaturedExperts({ limit: 30 });
    if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
      allExperts.value = res.data;
      pickRandom();
    }
  } catch (e) {
    console.error('[AuthorityStrip] 加载推荐专家失败:', e);
  }
});

/** 供父组件下拉刷新时调用，重新随机挑选 */
function refresh(): void {
  if (allExperts.value.length > 0) pickRandom();
}

function handleExpertClick(expert: Expert): void {
  emit('expertClick', expert);
  uni.navigateTo({ url: `/pages/app/expert/detail?id=${expert.id}` });
}

defineExpose({ refresh });
</script>

<style lang="scss" scoped>
.authority-strip {
  padding: 0 16rpx;
  margin-bottom: 0;
}

.strip-header {
  display: flex;
  align-items: center;
  padding: 0 0 12rpx;
}

.strip-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
}

.expert-scroll {
  width: 100%;
  white-space: nowrap;
}

.expert-list {
  display: inline-flex;
  gap: 16rpx;
  padding-bottom: 4rpx;
}

.expert-card {
  display: flex;
  flex-direction: column;
  width: 330rpx;
  padding: 12rpx 16rpx;
  gap: 10rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg); /* 圆角统一来自 token 体系 */
  border: 1px solid var(--home-border-light);
  box-shadow: none; /* 小卡片无阴影：去油腻，轻边框即够 */
  transition: border-color 0.2s ease;

  &:active {
    border-color: var(--home-border);
  }
}

.expert-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  width: 100%;
  min-width: 0;
}

.expert-avatar {
  flex-shrink: 0;
}

.expert-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.expert-name {
  font-size: 26rpx;
  font-weight: 600;
  line-height: 1.4;
  color: var(--home-text1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expert-meta {
  font-size: 20rpx;
  color: var(--home-text2);
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expert-skills {
  width: 100%;
  font-size: 20rpx;
  color: var(--home-text2);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}
</style>
