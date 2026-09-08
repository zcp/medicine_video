<template>
  <view class="experts-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="experts.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无专家信息</text>
    </view>
    
    <!-- 专家列表（复用专家列表页 ExpertCard，样式与列表页一致） -->
    <view v-else class="experts-list">
      <view v-for="expert in experts" :key="expert.id" class="expert-item">
        <ExpertCard
          :avatar="avatarOf(expert)"
          :name="expert.name"
          :title="expert.title || ''"
          :hospital="expert.hospital || ''"
          :specialization="specializationOf(expert)"
          :stats="{ followers: 0, sessions: 0 }"
          :is-following="followStore.isFollowed(expert.id)"
          @click="goToExpertDetail(expert.id)"
          @toggle-follow="toggleFollow(expert)"
        />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ExpertCard from '@/components/expert/ExpertCard.vue'
import { useFollowStore } from '@/store/follow'
import { useAuthStore } from '@/store/auth'
import { resolveMediaUrl } from '@/utils/url'
import type { Expert } from '@/types/expert'

interface Props {
  experts: Expert[]  // 接收专家数据，不再自己请求API
}

defineProps<Props>()
const loading = ref(false)  // 不需要loading状态，因为数据由父组件传入

const followStore = useFollowStore()
const authStore = useAuthStore()

/** 头像：与专家列表页 store 映射一致（resolveMediaUrl + 默认头像兜底） */
const avatarOf = (expert: Expert): string => {
  return resolveMediaUrl(expert.avatar_url) || '/static/default-avatar.png'
}

/** 擅长领域：逗号拆分为数组（与专家列表页/搜索页映射一致） */
const specializationOf = (expert: Expert): string[] => {
  return (expert.expertise_areas || '')
    .split(',')
    .map((s: string) => s.trim())
    .filter((s: string) => !!s)
}

// 跳转到专家详情
const goToExpertDetail = (expertId: string) => {
  uni.navigateTo({
    url: `/pages/app/expert/detail?id=${expertId}`
  })
}

// 切换关注状态（与专家列表页逻辑一致：followStore 统一维护关注状态）
const toggleFollow = async (expert: Expert) => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }

  try {
    if (followStore.isFollowed(expert.id)) {
      await followStore.unfollowExpert(expert.id)
      uni.showToast({ title: '已取消关注', icon: 'none' })
    } else {
      await followStore.followExpert(expert.id)
      uni.showToast({ title: '关注成功', icon: 'success' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '操作失败', icon: 'none' })
  }
}

// 已登录时加载关注列表（followStore 内部有缓存，重复调用无副作用）
onMounted(() => {
  if (authStore.isAuthenticated) {
    followStore.loadFollowedExperts()
  }
})
</script>

<style scoped>
.experts-tab {
  width: 100%;
  min-height: 400rpx;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

/* 行式列表：左右间距对齐专家列表页（--home-spacing-page），灰底直接展示 */
.experts-list {
  padding: 0 var(--home-spacing-page);
}
</style>
