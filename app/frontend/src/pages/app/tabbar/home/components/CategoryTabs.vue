<template>
  <view class="category-tabs-wrapper">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-skeleton">
      <view class="skeleton-tab" v-for="i in 5" :key="i" />
    </view>
    
    <!-- 分类Tab栏：分为可滚动区域和固定菜单按钮 -->
    <view v-else class="category-tabs-container">
      <!-- 左侧可滚动的分类标签区域 -->
      <scroll-view 
        class="category-tabs"
        scroll-x
        :scroll-with-animation="true"
      >
        <view class="tabs-container">
          <view 
            v-for="category in displayCategories" 
            :key="category.id || 'recommend'"
            class="tab-item"
            :class="{ 'tab-item--active': activeId === category.id }"
            @tap="handleTabClick(category.id)"
          >
            <image v-if="category.icon" :src="resolveMediaUrl(category.icon)" class="tab-icon" mode="aspectFit" />
            <text class="tab-text">{{ category.display_name || category.name }}</text>
            <view v-if="activeId === category.id" class="tab-indicator" />
          </view>
        </view>
      </scroll-view>
      
      <!-- 右侧固定的菜单按钮 -->
      <view class="menu-button" @tap="handleMenuClick">
        <text class="menu-icon">≡</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 分类筛选器组件
 * @description 吸顶横向滚动的分类选项卡，支持分类切换
 * 设计参考：移动端设计文档V1.3
 */
import { ref, watch, onMounted } from 'vue';
import { getCategories } from '@/api/category';
import { resolveMediaUrl } from '@/utils/url';
import type { Category } from '@/types/category';

/** Props 定义 */
const props = withDefaults(defineProps<{
  /** 当前选中的分类ID */
  activeId: string | null;
}>(), {
  activeId: null,
});

/** Emits 定义 */
const emit = defineEmits<{
  /** 分类切换事件 */
  (e: 'change', categoryId: string | null): void;
}>();

/** 所有分类列表 */
const allCategories = ref<Category[]>([]);

/** 显示在Tab栏的分类（推荐+星标+热门） */
const displayCategories = ref<Array<Category & { id: string | null }>>([]);

/** 加载状态 */
const loading = ref(false);

/** 数据源是否为 Mock（加载失败降级后为 true，用于 onShow 时重新拉取真实数据） */
const isMockData = ref(false);

/**
 * @description 从已加载的 allCategories 和 localStorage 星标数据重新构建，不发起 API 请求
 */
const buildDisplayCategories = () => {
  if (allCategories.value.length === 0) return;

  // 1. "推荐" Tab（固定第一位，id为null）
  const recommendTab = {
    id: null as any,
    name: '推荐',
    slug: 'recommended',
    icon: null,
    description: '多科室热门推荐',
    sort_order: -1,
    is_active: true,
    created_at: '',
    updated_at: ''
  };

  // 2. 用户星标的科室（从本地存储获取，最多5个）— 固定在推荐之后
  const starredIds = getStarredCategoryIds();
  const starredCategories = allCategories.value
    .filter(c => starredIds.includes(c.id))
    .slice(0, 5);

  // 3. 其余科室（非星标），接在星标科室后面
  const remainingCategories = allCategories.value
    .filter(c => !starredIds.includes(c.id));

  // 组合：推荐 + 星标科室 + 其余全部科室（全部显示，超出由横向滚动承载）
  displayCategories.value = [
    recommendTab as any,
    ...starredCategories,
    ...remainingCategories
  ];

  console.log('[分类Tab重建] 星标科室:', starredIds, '显示数:', displayCategories.value.length);
};

/**
 * 加载分类列表（完整流程：API请求 + 构建显示列表）
 * 失败自动重试（最多 MAX_RETRY 次），重试耗尽后才降级 Mock 数据
 */
const MAX_RETRY = 2;
const RETRY_DELAY = 800;

/** 防重入：并发调用 loadCategories 时复用同一个进行中的请求 */
let loadPromise: Promise<void> | null = null;

const loadCategories = (): Promise<void> => {
  if (loadPromise) return loadPromise;
  loadPromise = runLoadCategories().finally(() => {
    loadPromise = null;
  });
  return loadPromise;
};

async function runLoadCategories(retry = 0): Promise<void> {
  loading.value = true;
  try {
    const res = await getCategories();
    allCategories.value = res.data;
    isMockData.value = false;

    console.log('[分类加载成功]', allCategories.value);

    buildDisplayCategories();
  } catch (error) {
    console.error('[分类加载失败]', error);

    // 失败自动重试，避免偶发超时导致永久停留在 Mock 数据
    if (retry < MAX_RETRY) {
      console.log(`[分类加载] 请求失败，${RETRY_DELAY}ms 后重试 (${retry + 1}/${MAX_RETRY})`);
      await new Promise<void>(resolve => setTimeout(resolve, RETRY_DELAY));
      await runLoadCategories(retry + 1);
      return;
    }

    // 重试耗尽，使用Mock数据作为后备（对齐后端种子数据15个分类）
    console.log('[使用Mock分类数据]');
    isMockData.value = true;
    uni.showToast({ title: '分类加载失败，使用本地数据', icon: 'none', duration: 2000 });
    allCategories.value = [
      { id: '1', name: '普通外科', slug: 'general-surgery', description: '', sort_order: 1, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '2', name: '神经外科', slug: 'neurosurgery', description: '', sort_order: 2, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '3', name: '心内科', slug: 'cardiology', description: '', sort_order: 3, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '4', name: '骨科', slug: 'orthopedics', description: '', sort_order: 4, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '5', name: '妇产科', slug: 'obstetrics-gynecology', description: '', sort_order: 6, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '6', name: '儿科', slug: 'pediatrics', description: '', sort_order: 7, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '7', name: '眼科', slug: 'ophthalmology', description: '', sort_order: 8, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '8', name: '消化科', slug: 'gastroenterology', description: '', sort_order: 10, is_active: true, created_at: '', updated_at: '', icon: null },
    ];

    // 构建显示分类（使用Mock数据）
    displayCategories.value = [
      {
        id: null as any,
        name: '推荐',
        slug: 'recommended',
        icon: null,
        description: '多科室热门推荐',
        sort_order: -1,
        is_active: true,
        created_at: '',
        updated_at: ''
      },
      ...allCategories.value.slice(0, 6) // 显示前6个分类
    ];
  } finally {
    loading.value = false;
  }
}

/**
 * 获取用户星标的科室ID列表（从本地存储）
 */
const getStarredCategoryIds = (): string[] => {
  try {
    const stored = uni.getStorageSync('starred_category_ids');
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('[读取星标科室失败]', error);
    return [];
  }
};

/**
 * Tab 点击处理
 * @param categoryId - 分类ID（null表示推荐Tab）
 */
function handleTabClick(categoryId: string | null): void {
  if (categoryId !== props.activeId) {
    emit('change', categoryId);
  }
}

/**
 * 全部科室菜单点击
 */
function handleMenuClick(): void {
  uni.navigateTo({
    url: '/pages/app/categories/AllCategories'
  });
}

/** 页面挂载时加载分类 */
onMounted(() => {
  loadCategories();
});

/** 暴露刷新方法供父组件调用（用户从全部科室页返回时使用）
 * 数据源为 Mock（此前加载失败）时重新请求真实分类，否则仅重建显示列表
 */
defineExpose({
  refresh: async () => {
    if (isMockData.value || allCategories.value.length === 0) {
      await loadCategories();
    } else {
      buildDisplayCategories();
    }
  }
});
</script>

<style lang="scss" scoped>
.category-tabs-wrapper {
  width: 100%;
  background-color: var(--home-bg);
  /* 极浅分隔线（去油腻：低对比，若隐若现） */
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.06);
}

.loading-skeleton {
  display: flex;
  align-items: center;
  height: 80rpx;
  padding: 0 16rpx;
  gap: 16rpx;
  
  .skeleton-tab {
    width: 100rpx;
    height: 40rpx;
    background-color: var(--home-border);
    border-radius: var(--home-r-md);
    animation: pulse 1.5s infinite;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 新增：分类Tab容器，使用flex布局分离滚动区和固定按钮 */
.category-tabs-container {
  display: flex;
  align-items: center;
  height: 80rpx;
  background-color: var(--home-bg);
}

/* 左侧可滚动区域 */
.category-tabs {
  flex: 1;
  height: 100%;
  white-space: nowrap;
  overflow: hidden;
}

.tabs-container {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--home-spacing-page);
}

.tab-item {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 0 24rpx;
  flex-shrink: 0;
}

.tab-text {
  font-size: 28rpx;
  color: var(--home-text2);
  transition: color 0.2s ease;
}

.tab-icon {
  width: 32rpx;
  height: 32rpx;
  margin-right: 6rpx;
  flex-shrink: 0;
}

/* 触控反馈：整个 Tab 行可点，active 态统一 180–220ms */
.tab-item:active {
  .tab-text {
    opacity: 0.7;
  }
}

.tab-item--active {
  .tab-text {
    color: var(--home-primary);
    font-weight: 600;
  }
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 28rpx;
  height: 4rpx;
  background-color: var(--home-primary);
  border-radius: 2rpx;
}

.menu-button {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 100%;
  border-left: 1rpx solid rgba(17, 24, 39, 0.06);
  background-color: var(--home-bg);
  transition: background-color 0.2s ease;

  .menu-icon {
    font-size: 32rpx;
    font-weight: 600;
    color: var(--home-text2);
    transition: color 0.2s ease;
  }

  /* 触控反馈：180–220ms */
  &:active {
    .menu-icon {
      color: var(--home-primary);
    }
  }
}
</style>
