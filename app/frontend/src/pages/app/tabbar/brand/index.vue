<template>
  <view class="brand-page home-layout">
    <!-- 顶部固定搜索栏 -->
    <view class="brand-header-sticky">
      <BrandHeader @search="onSearch" />
    </view>

    <!-- 品牌网格 -->
    <scroll-view scroll-y class="scroll" @scrolltolower="onReachBottom">
      <BrandGrid :brands="brands" :loading="loading" :hasMore="hasMore" @select="openDetail" />
    </scroll-view>

    <!-- 自定义 TabBar -->
    <CustomTabBar :current="1" />
  </view>
</template>

<script setup lang="ts">
/**
 * 品牌专区页面
 * @description 展示品牌列表，支持拼音搜索，点击进入品牌详情查看关联直播间
 */
import { ref, computed, onMounted } from 'vue';
import { onPullDownRefresh } from '@dcloudio/uni-app';
import BrandHeader from '@/components/brand/BrandHeader.vue';
import BrandGrid from '@/components/brand/BrandGrid.vue';
import CustomTabBar from '@/components/app/CustomTabBar.vue';
import { getBrands } from '@/api/brand';
import { searchByPinyin } from '@/utils/pinyin';

// ========== 状态 ==========

/** 搜索关键词 */
const keyword = ref('');

/** 所有品牌数据 */
const allBrands = ref<any[]>([]);

/** 加载状态 */
const loading = ref(false);

/** 是否有更多（当前全量加载，后续可扩展真分页） */
const hasMore = computed(() => false);

// ========== 计算属性 ==========

/**
 * 筛选后的品牌列表（支持拼音搜索）
 */
const filtered = computed(() => {
  let result = allBrands.value;

  // 按搜索关键词筛选（支持拼音）
  if (keyword.value.trim()) {
    result = searchByPinyin(result, keyword.value, (brand) => String(brand?.name || ''));
  }

  return result;
});

/**
 * 当前显示的品牌列表
 */
const brands = computed(() => filtered.value);

// ========== 方法 ==========

/**
 * 加载品牌数据
 */
async function loadBrands() {
  console.log('[BrandZone] 开始加载品牌列表');

  try {
    loading.value = true;

    const resp = await getBrands({
      page: 1,
      size: 500
    } as any);

    if (resp.code === 200 && resp.data) {
      const items = resp.data.items || resp.data;
      allBrands.value = Array.isArray(items) ? items : [];
      console.log('[BrandZone] 品牌列表加载成功:', allBrands.value.length);
    } else {
      allBrands.value = [];
      console.warn('[BrandZone] 品牌列表返回异常:', resp);
    }
  } catch (e: any) {
    console.error('[BrandZone] 加载品牌列表失败:', e);
    allBrands.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 处理搜索（实时搜索，通过 computed 筛选）
 */
function onSearch(kw: string) {
  keyword.value = kw;
}

/**
 * 处理触底加载（预留分页扩展）
 */
function onReachBottom() {
  // 当前为全量加载，预留分页逻辑
}

/**
 * 打开品牌详情
 */
function openDetail(id: string) {
  uni.navigateTo({ url: `/pages/app/brand/detail?id=${id}` });
}

// ========== 生命周期 ==========

onMounted(() => {
  loadBrands();
});

onPullDownRefresh(async () => {
  await loadBrands();
  uni.stopPullDownRefresh();
});
</script>

<style scoped lang="scss">
.brand-page.home-layout {
  min-height: 100vh;
  background: var(--home-bg);
}

.scroll {
  height: calc(100vh - 232rpx - env(safe-area-inset-bottom));
}

.brand-header-sticky {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--home-bg);
}
</style>
