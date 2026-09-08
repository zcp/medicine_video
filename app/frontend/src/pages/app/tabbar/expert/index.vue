<template>
  <view class="expert-page consumer-layout">
    <!-- 顶部：Search + Tabs 轻导航（spacing 分组，无硬分割） -->
    <view class="expert-header">
      <ExpertSearch @search="handleSearch" />
      <view class="filter-row">
        <FilterTabs :items="deptTabs" :selectedIndex="selectedIndex" @change="handleFilter" />
      </view>
    </view>

    <!-- 加载状态 -->
    <LoadingIndicator v-if="loadingList && !dataLoaded" />
    
    <!-- 错误提示 -->
    <ErrorBanner v-if="error" :message="error.message" @close="clearError" />

    <!-- 专家列表 -->
    <scroll-view 
      scroll-y 
      class="list" 
      v-if="dataLoaded" 
      :lower-threshold="120"
      @scrolltolower="loadMoreData"
    >
      <view v-for="e in list" :key="e.id">
        <ExpertCard
          :avatar="e.avatar"
          :name="e.name"
          :title="e.title"
          :hospital="e.hospital ?? ''"
          :specialization="e.specialization"
          :stats="e.stats"
          :isFollowing="isFollowed(e.id)"
          @click="goDetail(e.id)"
          @toggle-follow="toggleFollow(e.id)"
        />
      </view>
      <view class="load-more" v-if="pagination.hasMore && !loadingList">上拉加载更多</view>
      <view class="no-more" v-else-if="!pagination.hasMore && list.length > 0">已经到底啦~</view>
    </scroll-view>

    <!-- 空状态 -->
    <EmptyState 
      v-if="!loadingList && dataLoaded && list.length === 0" 
      title="暂无专家" 
      description="稍后再试或更换筛选条件" 
    />

    <!-- 自定义 TabBar -->
    <CustomTabBar :current="2" />
  </view>
</template>

<script setup lang="ts">
/**
 * 专家列表页面
 * @description 展示专家列表，支持搜索、科室筛选、字母索引
 */
import { ref, onMounted } from 'vue';
import { onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app';
import ExpertSearch from '@/components/expert/ExpertSearch.vue';
import FilterTabs from '@/components/expert/FilterTabs.vue';
import ExpertCard from '@/components/expert/ExpertCard.vue';
import LoadingIndicator from '@/components/common/LoadingIndicator.vue';
import ErrorBanner from '@/components/common/ErrorBanner.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import CustomTabBar from '@/components/app/CustomTabBar.vue';
import { useExpertStore } from '@/store/expert';
import { useFollowStore } from '@/store/follow';
import { useAuthStore } from '@/store/auth';
import { storeToRefs } from 'pinia';
import { getCategories } from '@/api/category';

// ========== Store ==========
const expertStore = useExpertStore();
const followStore = useFollowStore();
const authStore = useAuthStore();
const { list, loadingList, error, pagination } = storeToRefs(expertStore);

// ========== 状态 ==========

/** 科室筛选Tab（动态从后端分类API获取，失败时使用Mock兜底） */
const deptTabs = ref<string[]>([]);

/** 科室名称 → 分类ID 映射（用于传 category_id 给后端） */
const categoryNameToId = ref<Map<string, string>>(new Map());

/** 数据是否已加载 */
const dataLoaded = ref(false);

/** 当前选中的筛选索引 */
const selectedIndex = ref(0);

/** 防止 loadData 并发调用（快速切Tab时竞态保护） */
const isDataLoading = ref(false);

// ========== 方法 ==========

/**
 * 跳转到专家详情
 */
function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/app/expert/detail?id=${id}` });
}

/**
 * 加载数据（带并发保护，防止快速切Tab竞态）
 */
async function loadData(refresh = false) {
  if (isDataLoading.value) return;
  isDataLoading.value = true;
  try {
    const nextPage = refresh ? 1 : (pagination.value.page || 1);
    await expertStore.fetchExperts({ page: nextPage, pageSize: pagination.value.pageSize });
    dataLoaded.value = true;
  } finally {
    isDataLoading.value = false;
  }
}

async function loadMoreData() {
  if (isDataLoading.value || loadingList.value || !pagination.value.hasMore) return;
  isDataLoading.value = true;
  try {
    await expertStore.fetchExperts({
      page: pagination.value.page + 1,
      pageSize: pagination.value.pageSize
    });
  } finally {
    isDataLoading.value = false;
  }
}

/**
 * 处理搜索
 * 搜索行为统一进入“全部”范围，避免在当前分类 Tab 下展示跨分类搜索结果造成误解。
 */
async function handleSearch(keyword: string) {
  expertStore.keyword = keyword.trim();
  selectedIndex.value = 0;
  expertStore.specialty = '';
  expertStore.currentCategoryId = null;
  await loadData(true);
}

/**
 * 处理筛选
 */
function handleFilter(index: number, item: string) {
  selectedIndex.value = index;
  if (item === '全部') {
    expertStore.specialty = '';
    expertStore.currentCategoryId = null;
  } else {
    // specialty 始终设为分类名（前端降级筛选用）
    expertStore.specialty = item;
    // currentCategoryId 作为后端增强参数（新API就绪后生效）
    const catId = categoryNameToId.value.get(item) || '';
    expertStore.currentCategoryId = catId || null;
  }
  loadData(true);
}

/**
 * 检查是否已关注
 */
function isFollowed(expertId: string): boolean {
  return followStore.isFollowed(expertId);
}

/**
 * 切换关注状态
 */
async function toggleFollow(expertId: string) {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  try {
    if (isFollowed(expertId)) {
      await followStore.unfollowExpert(expertId);
      uni.showToast({ title: '已取消关注', icon: 'none' });
    } else {
      await followStore.followExpert(expertId);
      uni.showToast({ title: '关注成功', icon: 'success' });
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

/**
 * 清除错误
 */
function clearError() {
  expertStore.error = null;
}

/**
 * 加载科室Tab数据
 * 优先从后端 GET /categories 获取，失败时使用 Mock 兜底
 */
async function loadDeptTabs() {
  try {
    const res = await getCategories();
    const categories = res.data || [];
    const map = new Map<string, string>();
    const names: string[] = ['全部'];
    for (const c of categories) {
      if (c.is_active) {
        const displayName = c.display_name || c.name;
        names.push(displayName);
        // 双 key 防御：口语名与标准名均映射同一 id，避免筛选时失配
        map.set(displayName, c.id);
        map.set(c.name, c.id);
      }
    }
    deptTabs.value = names;
    categoryNameToId.value = map;
  } catch (error) {
    console.error('[科室Tab加载失败]', error);
    uni.showToast({ title: '科室加载失败，使用缓存数据', icon: 'none', duration: 2000 });
    // Mock 兜底（对齐后端种子数据）
    deptTabs.value = ['全部', '普通外科', '神经外科', '心内科', '骨科', '妇产科', '儿科', '消化科'];
  }
}

// ========== 生命周期 ==========

onMounted(() => {
  loadDeptTabs();
  loadData(true);
  
  // 🔴 P0：只有在用户已登录时才加载关注列表，避免触发登录跳转
  if (authStore.isAuthenticated) {
    followStore.loadFollowedExperts();
    console.log('✅ [专家页] 用户已登录，加载关注列表');
  } else {
    console.log('📱 [专家页] 用户未登录，跳过加载关注列表');
  }
});

onPullDownRefresh(async () => {
  await loadData(true);
  uni.stopPullDownRefresh();
});

onReachBottom(loadMoreData);
</script>

<style lang="scss" scoped>
.expert-page.consumer-layout {
  min-height: 100vh;
  background-color: var(--home-bg);
}

.expert-header {
  padding: var(--home-spacing-module) var(--home-spacing-page) var(--home-spacing-inner);
}

.filter-row {
  display: flex;
  align-items: center;
}

.filter-row :deep(.filter-tabs) {
  flex: 1;
  min-width: 0;
}

.list {
  height: calc(100vh - 280rpx - env(safe-area-inset-bottom));
  padding-left: var(--home-spacing-page);
  padding-right: var(--home-spacing-page);
}

.load-more,
.no-more {
  text-align: center;
  padding: var(--home-spacing-module);
  color: var(--home-text2);
  font-size: var(--home-fs-meta);
}

</style>
