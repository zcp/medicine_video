<template>
  <view class="search-page">
    <!-- 导航栏：使用已验证可用的 SearchNavBar 组件 -->
    <SearchNavBar
      v-model:keyword="keyword"
      :auto-focus="true"
      @search="handleSearch"
      @back="handleCancel"
    />
    
    <!-- 滚动区域：padding-top 补偿 fixed 导航栏的高度 -->
    <scroll-view class="scroll-content" scroll-y :style="{ paddingTop: navbarHeight + 'px' }">
      <!-- 输入关键词时：显示搜索建议 -->
      <template v-if="keyword.trim()">
        <view class="suggestion-list">
          <view
            v-for="(item, index) in searchStore.suggestions"
            :key="index"
            class="suggestion-item"
            @tap="handleSelectKeyword(item)"
          >
            <text class="suggestion-text">{{ item }}</text>
          </view>
          <!-- 无建议时显示直接搜索入口 -->
          <view
            v-if="searchStore.suggestions.length === 0 && !searchStore.suggestionsLoading"
            class="suggestion-item"
            @tap="handleSearch(keyword)"
          >
            <text class="suggestion-text">搜索 "{{ keyword.trim() }}"</text>
          </view>
        </view>
      </template>

      <!-- 无关键词时：热门搜索 → 搜索历史 → 搜索推荐 -->
      <template v-else>
        <!-- 1. 热门搜索 —— 顶部 -->
        <HotSearches
          :items="searchStore.hotSearches"
          @select-keyword="handleSelectKeyword"
        />

        <!-- 2. 搜索历史 —— 中间区域 -->
        <SearchHistory
          v-if="searchStore.searchHistory.length > 0"
          :items="searchStore.searchHistory"
          @select-keyword="handleSelectKeyword"
          @delete-item="handleDeleteHistory"
          @clear-all="handleClearHistory"
        />

        <!-- 3. 搜索推荐（猜你想搜）—— 底部 -->
        <view v-if="searchStore.recommendations.length > 0" class="recommend-section">
          <view class="section-header">猜你想搜</view>
          <view class="recommend-tags">
            <view
              v-for="item in searchStore.recommendations"
              :key="item.keyword"
              class="recommend-tag"
              @tap="handleSelectKeyword(item.keyword)"
            >
              {{ item.keyword }}
            </view>
          </view>
        </view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 搜索前页面（Landing Page）
 * @description 展示搜索框、搜索历史、热门搜索，点击搜索后跳转到结果页
 */
import { ref, computed, onMounted, watch } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import SearchNavBar from '@/components/app/SearchNavBar.vue';
import SearchHistory from '@/components/app/SearchHistory.vue';
import HotSearches from '@/components/app/HotSearches.vue';
import { useSearchStore } from '@/store/search';
import { logger } from '@/utils/logger';

/** 搜索关键词 */
const keyword = ref<string>('');

/** 搜索Store */
const searchStore = useSearchStore();

/** 状态栏高度 */
const statusBarHeight = ref<number>(0);
/** 导航栏总高度（状态栏 + 44px内容行） */
const navbarHeight = computed(() => statusBarHeight.value + 44);

/**
 * 页面加载
 */
onLoad((options) => {
  console.log('[TRACE-INDEX] onLoad 触发, options:', JSON.stringify(options));
  // 获取系统信息
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  
  // 如果从其他页面带关键词跳转过来，直接执行搜索
  if (options?.keyword) {
    const decodedKeyword = decodeURIComponent(options.keyword as string);
    console.log('[TRACE-INDEX] onLoad 收到关键词，跳转搜索结果:', decodedKeyword);
    keyword.value = decodedKeyword;
    handleSearch(decodedKeyword);
  }
});

/**
 * 页面挂载
 */
onMounted(async () => {
  // 加载搜索历史
  await searchStore.loadSearchHistory();
  // 加载热门搜索词（从后端API）
  searchStore.loadHotKeywords();
  // 加载搜索推荐
  searchStore.loadRecommendations();
  logger.info('[SearchLanding] 页面已加载');
});

/** 监听输入变化，实时获取搜索建议 + 推荐 */
watch(keyword, (newVal) => {
  searchStore.fetchSuggestions(newVal);
  // 有输入时也获取相关推荐（更广的 ILIKE 匹配）
  if (newVal && newVal.trim()) {
    searchStore.loadRecommendations(newVal.trim());
  }
});

/**
 * 页面显示时恢复状态（从搜索结果页返回时触发）
 * B站行为：返回后点击搜索框 → 重新显示联想菜单
 */
onShow(() => {
  console.log('[TRACE-INDEX] onShow 触发, keyword:', keyword.value);
  if (keyword.value.trim()) {
    // 关键词还在：重新拉取建议列表
    searchStore.fetchSuggestions(keyword.value);
  } else {
    // 关键词已清空：刷新热门搜索
    searchStore.loadHotKeywords();
  }
});

/**
 * 执行搜索
 * @param searchKeyword 搜索关键词
 */
const handleSearch = (searchKeyword: string) => {
  console.log('[TRACE-INDEX] handleSearch 被调用:', searchKeyword);
  const trimmedKeyword = searchKeyword.trim();
  
  // 关键词长度校验
  if (!trimmedKeyword) {
    uni.showToast({
      title: '请输入搜索关键词',
      icon: 'none',
      duration: 2000
    });
    return;
  }
  
  if (trimmedKeyword.length < 2) {
    uni.showToast({
      title: '搜索关键词至少2个字符',
      icon: 'none',
      duration: 2000
    });
    return;
  }
  
  // 跳转到搜索结果页
  const url = `/pages/app/search/results?keyword=${encodeURIComponent(trimmedKeyword)}`;
  console.log('[TRACE-INDEX] navigateTo 跳转:', url);
  uni.navigateTo({
    url
  });
  
  logger.info(`[SearchLanding] 搜索: "${trimmedKeyword}"`);
};

/**
 * 选择关键词（历史记录或热门搜索）
 * @param selectedKeyword 选中的关键词
 */
const handleSelectKeyword = (selectedKeyword: string) => {
  console.log('[TRACE-INDEX] handleSelectKeyword 被调用:', selectedKeyword);
  // 直接跳转搜索结果，不设 keyword 避免触发联想视图闪烁
  handleSearch(selectedKeyword);
};

/**
 * 删除单条搜索历史
 * @param deletedKeyword 要删除的关键词
 */
const handleDeleteHistory = async (deletedKeyword: string) => {
  await searchStore.deleteHistory(deletedKeyword);
  logger.info(`[SearchLanding] 删除历史: "${deletedKeyword}"`);
};

/**
 * 清空搜索历史
 */
const handleClearHistory = async () => {
  await searchStore.clearHistory();
  logger.info('[SearchLanding] 已清空搜索历史');
};

/**
 * 搜索按钮 / 键盘确认（均通过 handleSearch）
 */
const handleSearchConfirm = () => {
  handleSearch(keyword.value);
};

/**
 * 取消搜索（返回上一页）
 */
const handleCancel = () => {
  uni.navigateBack({
    delta: 1
  });
};
</script>

<style scoped lang="scss">
.search-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
}

.scroll-content {
  flex: 1;
  overflow-y: auto;
}

.suggestion-list {
  padding: 12px 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #f5f5f5;

  &:active {
    background: #f5f5f5;
  }
}

.suggestion-text {
  font-size: 15px;
  color: #333;
}

.recommend-section {
  padding: 16px 20px 0;
}

.section-header {
  font-size: 12px;
  color: #999;
  margin-bottom: 12px;
}

.recommend-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.recommend-tag {
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 12px;
  color: #333;
}
</style>
