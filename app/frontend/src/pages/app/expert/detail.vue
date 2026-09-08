<template>
  <view class="expert-detail">
    <LoadingIndicator v-if="loadingDetail && !dataLoaded" />
    <ErrorBanner v-if="error" :message="error.message" @close="clearError" />

    <view v-if="dataLoaded && detail">
      <ExpertProfile
        :avatar="detail.avatar"
        :name="detail.name"
        :title="detail.title"
        :hospital="detail.hospital ?? ''"
        :department="detail.department_name ?? ''"
        :category="detail.category_name ?? ''"
        :isFollowing="isFollowed"
        :pending="followPending"
        @toggle-follow="toggleFollow"
      />

      <!-- 专家介绍（首 section：与 Header 之间结构断点） -->
      <view class="section section--after-header">
        <text class="section-title">专家介绍</text>
        <view class="bio">
          <template v-if="detail.bio">
            <text v-for="(p, i) in bioParagraphs" :key="'p-' + i" class="bio-paragraph">{{ p }}</text>
          </template>
          <view class="bio-block" v-if="specialties.length">
            <text class="block-title">擅长领域</text>
            <view class="tags">
              <text v-for="tag in specialties" :key="tag" class="tag">{{ tag }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 相关直播 -->
      <view class="section">
        <text class="section-title">相关直播</text>
        <view class="session-list">
          <view class="session-item clickable" v-for="s in sortedSessions" :key="s.id" @tap="goLiveSession(s.id)">
            <view class="cover-wrap">
              <image class="cover" :src="s.cover" mode="aspectFill" />
              <!-- 状态标签（封面左上角，统一位置） -->
              <text class="cover-status-tag" :class="`status-${s.status}`">{{ formatStatus(s.status) }}</text>
            </view>
            <view class="right">
              <view class="session-title-row">
                <text class="session-title">{{ s.title }}</text>
              </view>
              <!-- 专家 host 块：姓名 | 角色 | 职称，第二行医院 -->
              <view class="session-host" v-if="detail && detail.name">
                <image class="host-avatar" :src="hostAvatarError ? HOST_FALLBACK_AVATAR : detail.avatar" mode="aspectFill" @error="hostAvatarError = true" />
                <view class="host-text">
                  <view class="host-line1">
                    <text class="host-name">{{ detail.name }}</text>
                    <text v-if="s.role" class="host-role"> | {{ formatRole(s.role) }}</text>
                    <text v-if="detail.title" class="host-title"> | {{ detail.title }}</text>
                  </view>
                  <view v-if="detail.hospital" class="host-line2">{{ detail.hospital }}</view>
                </view>
              </view>
            </view>
          </view>
          <view v-if="!sortedSessions.length" class="empty-state-inline">
            <EmptyState title="暂无相关直播" description="稍后再来看看吧" />
          </view>
        </view>
      </view>
    </view>

    <EmptyState v-if="!loadingDetail && !detail" title="无法加载专家信息" description="请稍后重试" />
  </view>
</template>

<script setup lang="ts">
/**
 * 专家详情页面
 * @description 展示专家详细信息、直播场次列表
 */
import { computed, ref, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import ExpertProfile from '@/components/expert/ExpertProfile.vue';
import LoadingIndicator from '@/components/common/LoadingIndicator.vue';
import ErrorBanner from '@/components/common/ErrorBanner.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import { useExpertStore, type ExpertSession } from '@/store/expert';
import { useFollowStore } from '@/store/follow';
import { useAuthStore } from '@/store/auth';
import { storeToRefs } from 'pinia';

// ========== Store ==========
const expertStore = useExpertStore();
const followStore = useFollowStore();
const authStore = useAuthStore();
const { detail, sessions, loadingDetail, error } = storeToRefs(expertStore);

// ========== 状态 ==========
const dataLoaded = ref(false);
const expertId = ref('');
// host 块头像兜底（与项目其他头像一致）
const HOST_FALLBACK_AVATAR = '/static/default-avatar.png';
// host 块头像加载失败标记（失败后改用兜底图）
const hostAvatarError = ref(false);

// ========== 计算属性 ==========

/**
 * 擅长领域
 */
const specialties = computed(() => (detail.value?.specialization ?? []) as string[]);

/**
 * 专家介绍按段落拆分（\n\n 或 \n，便于排版与可读性）
 */
const bioParagraphs = computed(() => {
  const raw = detail.value?.bio;
  if (!raw || typeof raw !== 'string') return [];
  return raw.split(/\n\n+|\n+/).map(s => s.trim()).filter(Boolean);
});

/**
 * 相关直播：统一展示，按直播中、即将开始、已结束分组排序
 */
const sortedSessions = computed(() => {
  const statusWeight: Record<ExpertSession['status'], number> = {
    live: 0,
    scheduled: 1,
    ended: 2
  };

  return [...(sessions.value || [])].sort((a, b) => {
    const statusDiff = statusWeight[a.status] - statusWeight[b.status];
    if (statusDiff !== 0) return statusDiff;

    const ta = a.scheduledAt ? Date.parse(a.scheduledAt) : 0;
    const tb = b.scheduledAt ? Date.parse(b.scheduledAt) : 0;
    return a.status === 'ended' ? tb - ta : ta - tb;
  });
});

/**
 * 是否已关注
 */
const isFollowed = computed(() => {
  return expertId.value ? followStore.isFollowed(expertId.value) : false;
});

/**
 * 关注操作中
 */
const followPending = ref(false);

/**
 * 格式化专家角色
 */
function formatRole(role?: string): string {
  if (!role) return '';
  const roleMap: Record<string, string> = {
    'host': '主持人',
    'speaker': '演讲嘉宾',
    'guest': '特邀嘉宾'
  };
  return roleMap[role] || role;
}

function formatStatus(status: ExpertSession['status']): string {
  const statusMap: Record<ExpertSession['status'], string> = {
    live: '直播中',
    scheduled: '预告',
    ended: '回放'
  };
  return statusMap[status];
}

// ========== 方法 ==========

/**
 * 跳转到直播场次
 */
function goLiveSession(sessionId: string) {
  const sid = String(sessionId || '');
  if (!sid) return;
  uni.navigateTo({ url: `/pages/app/live/LiveView?sessionId=${encodeURIComponent(sid)}` });
}

/**
 * 切换关注状态
 */
async function toggleFollow() {
  if (!expertId.value) return;
  
  // 🔴 P0：检查登录状态，未登录时轻量提示
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  
  try {
    followPending.value = true;
    
    if (isFollowed.value) {
      await followStore.unfollowExpert(expertId.value);
      uni.showToast({ title: '已取消关注', icon: 'none' });
    } else {
      await followStore.followExpert(expertId.value);
      uni.showToast({ title: '关注成功', icon: 'success' });
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    followPending.value = false;
  }
}

/**
 * 清除错误
 */
function clearError() {
  expertStore.error = null;
}

// ========== 生命周期 ==========

onLoad((options: any) => {
  const id: string | undefined = options?.id;
  console.log('[ExpertDetail] 页面加载，专家ID:', id);
  
  if (id) {
    expertId.value = id;
    
    Promise.all([
      expertStore.fetchExpertById(id),
      expertStore.fetchExpertSessions(id)
    ]).then(async () => {
      dataLoaded.value = true;
      console.log('[ExpertDetail] 数据加载完成');
      
      // ===== 🔄 检查关注状态（从服务器同步） =====
      if (authStore.isAuthenticated) {
        try {
          await followStore.checkIsFollowedFromApi(id);
          console.log('[ExpertDetail] ✅ 已同步关注状态');
        } catch (error) {
          console.error('[ExpertDetail] ❌ 检查关注状态失败:', error);
        }
      }
    }).catch((e) => {
      console.error('[ExpertDetail] 数据加载失败:', e);
    });
  }
});

onMounted(() => {
  // 🔴 P0：只有在用户已登录时才加载关注列表，避免触发登录跳转
  if (authStore.isAuthenticated) {
    followStore.loadFollowedExperts();
    console.log('✅ [专家详情] 用户已登录，加载关注列表');
  } else {
    console.log('📱 [专家详情] 用户未登录，跳过加载关注列表');
  }
});
</script>

<style lang="scss" scoped>
.expert-detail {
  min-height: 100vh;
  background: var(--home-bg);
  padding: var(--home-spacing-page) var(--home-spacing-module);
  padding-bottom: env(safe-area-inset-bottom);
  box-sizing: border-box;
}

/* 去卡片化：section 无背景/圆角/阴影，仅靠 spacing 分组（ConsumerLayout 单背景） */
.section {
  margin-top: calc(2 * var(--home-spacing-page));
  padding: 0;
}

/* Header 与正文结构断点：首 section 上间距提升 1 级，形成明显呼吸点 */
.section--after-header {
  margin-top: calc(5 * var(--home-spacing-page));
}

.section-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  padding-left: var(--home-spacing-inner);
  border-left: 5rpx solid var(--home-primary);
  display: block;
  line-height: 1.4;
}

.bio {
  margin-top: var(--home-spacing-inner);
}

/* 专家介绍段落：行高与段落间距来自节奏，secondary 色，不抢主标题 */
.bio-paragraph {
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
  line-height: 1.75;
  display: block;
  margin-top: var(--home-spacing-module);
  transition: opacity 0.2s ease;
}

.bio-paragraph:first-child {
  margin-top: 0;
}

.bio-block {
  margin-top: var(--home-spacing-module);
}

/* 擅长领域：meta title（caption/secondary）+ 下方 Tag 组件展示 */
.block-title {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.9;
  margin-bottom: var(--home-spacing-inner);
  display: block;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--home-spacing-inner);
}

/* Tag 组件：Neutral 底 + 轻边框 + Pill 圆角，与全局 tag 体系对齐 */
.tag {
  padding: var(--home-tag-padding-y) var(--home-tag-padding-x);
  min-height: var(--home-tag-height);
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  background: var(--home-tag-forecast-bg);
  color: var(--home-primary);
  border-radius: var(--home-tag-radius);
  font-size: var(--home-tag-font);
  font-weight: 500;
}

.session-list {
  margin-top: var(--home-spacing-inner);
}

.session-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: var(--home-spacing-module);
  transition: background-color 0.2s ease;
}

.session-item:last-of-type {
  border-bottom: none;
}

.session-item.clickable {
  cursor: pointer;
}

.session-item.clickable:active {
  background-color: rgba(0, 0, 0, 0.02);
}

.cover {
  width: 240rpx;
  height: 135rpx;
  border-radius: var(--home-r-md);
  background: var(--home-bg);
  flex-shrink: 0;
}

.right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.session-title-row {
  display: flex;
  align-items: flex-start;
  gap: var(--home-spacing-inner);
}

.session-title {
  flex: 1;
  min-width: 0;
  font-size: 30rpx;
  color: var(--home-text1);
}

/* 封面容器：状态标签定位锚点 */
.cover-wrap {
  position: relative;
  flex-shrink: 0;
}

/* 状态标签（封面左上角，统一位置） */
.cover-status-tag {
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

.cover-status-tag.status-live {
  background: rgba(220, 38, 38, 0.9);
}

.cover-status-tag.status-scheduled {
  background: var(--home-primary);
}

.cover-status-tag.status-ended {
  background: rgba(0, 0, 0, 0.6);
}

.cover-status-tag.status-replay {
  background: rgba(0, 0, 0, 0.6);
}

.cover-status-tag.status-error {
  background: rgba(0, 0, 0, 0.45);
}

/* 专家 host 块：场次主展示人 = 专家本人 */
.session-host {
  margin-top: 8rpx;
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  min-width: 0;
}

.host-avatar {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--home-bg);
  margin-top: 2rpx;
}

.host-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.host-line1 {
  font-size: 26rpx;
  color: var(--home-text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.host-name {
  color: var(--home-text1);
  font-weight: 500;
}

.host-role {
  color: var(--home-primary);
}

.host-title {
  color: var(--home-text3, #999);
}

.host-line2 {
  font-size: 24rpx;
  color: var(--home-text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 历史直播空状态：上移、高度收敛、图标略缩、文案弱化（secondary/tertiary） */
.empty-state-inline {
  padding: 0 0 var(--home-spacing-inner);
}

.empty-state-inline :deep(.empty-state) {
  padding: var(--home-spacing-inner) var(--home-spacing-inner);
  padding-top: var(--home-spacing-inner);
  background: transparent;
}

.empty-state-inline :deep(.empty-icon-placeholder),
.empty-state-inline :deep(.empty-icon) {
  width: 56rpx;
  height: 56rpx;
  font-size: 36rpx;
  margin-bottom: 6rpx;
  opacity: 0.4;
}

/* uni-icons 内联 font-size（60px）优先于普通选择器，需 !important 覆盖，
   使图标字号与 56rpx 容器匹配，避免图标溢出后与下方文字重叠 */
.empty-state-inline :deep(.empty-icon-placeholder .uni-icons) {
  font-size: 36rpx !important;
  line-height: 1;
}

.empty-state-inline :deep(.title) {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.85;
}

.empty-state-inline :deep(.desc) {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  opacity: 0.7;
  margin-top: 4rpx;
}
</style>
