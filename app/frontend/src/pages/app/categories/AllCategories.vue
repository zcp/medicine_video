<template>
  <view class="all-categories-page">
    <!-- 搜索框 (参照品牌/专家搜索UI，叠加共享B站风格容器) -->
    <view class="search-container">
      <view class="app-search-field search-box">
        <text class="iconfont icon-search search-icon"></text>
        <input 
          class="search-input"
          type="text"
          v-model="searchKeyword"
          placeholder="搜索科室名称"
          placeholder-class="search-placeholder"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="searchKeyword = ''" />
        </view>
      </view>
    </view>

    <!-- 我的关注科室 (优化为网格标签) -->
    <view v-if="starredCategories.length > 0" class="section card-section">
      <view class="section-header">
        <view class="title-group">
          <text class="main-title">我的关注</text>
          <text v-if="isEditMode" class="sub-title">点击移除</text>
        </view>
        <view class="section-actions">
          <text v-if="starredCategories.length >= 5" class="limit-badge">已满</text>
          <text class="action" @tap="toggleEditMode">
            {{ isEditMode ? '完成' : '编辑' }}
          </text>
        </view>
      </view>

      <view class="tags-grid">
        <view 
          v-for="category in starredCategories" 
          :key="category.id"
          class="tag-item is-active"
          :class="{ 'is-shaking': isEditMode }"
        >
          <text class="tag-text">{{ category.display_name || category.name }}</text>
          <!-- 编辑模式下显示右上角的删除小按钮 -->
          <view v-if="isEditMode" class="remove-badge" @tap="handleRemoveStar(category.id)">
            <text class="iconfont icon-close"></text>
          </view>
        </view>
      </view>
    </view>

    <!-- 全部科室 (优化为清爽列表) -->
    <view class="section card-section">
      <view class="section-header">
        <view class="title-group">
          <text class="main-title">全部科室</text>
          <text class="sub-title">可点击添加最多5个科室固定显示在首页前排</text>
        </view>
      </view>

      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>

      <view v-else-if="filteredCategories.length === 0" class="empty-state">
        <text>{{ searchKeyword ? '未找到相关科室' : '暂无科室数据' }}</text>
      </view>

      <view v-else class="tags-grid">
        <view 
          v-for="category in filteredCategories" 
          :key="category.id"
          class="tag-item"
          :class="{ 'is-disabled': isStarDisabled(category.id) }"
          @tap="handleToggleStar(category.id)"
        >
          <text class="add-icon">+</text>
          <text class="tag-text">{{ category.display_name || category.name }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { getCategories } from '@/api/category';
import type { Category } from '@/types/category';
import ClearButton from '@/components/app/ClearButton.vue';

// ===== 状态 =====
const loading = ref(false);
const isEditMode = ref(false);
const searchKeyword = ref('');
const allCategories = ref<Category[]>([]);
const starredIds = ref<string[]>([]);

// ===== 计算属性 =====
const starredCategories = computed(() => {
  return allCategories.value.filter(c => starredIds.value.includes(c.id));
});

const filteredCategories = computed(() => {
  let categories = allCategories.value.filter(c => !starredIds.value.includes(c.id));
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    categories = categories.filter(c => 
      (c.display_name || c.name).toLowerCase().includes(keyword) ||
      c.name.toLowerCase().includes(keyword) ||
      c.slug?.toLowerCase().includes(keyword)
    );
  }
  
  return categories;
});

// ===== 方法 =====
const loadCategories = async () => {
  loading.value = true;
  try {
    const res = await getCategories();
    allCategories.value = res.data || [];
  } catch (error) {
    console.error('[分类加载失败]', error);
    uni.showToast({ title: '分类加载失败，使用本地数据', icon: 'none' });
    
    // 使用Mock数据（对齐后端种子数据）
    allCategories.value = [
      { id: '1', name: '普通外科', slug: 'general-surgery', description: '', sort_order: 1, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '2', name: '神经外科', slug: 'neurosurgery', description: '', sort_order: 2, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '3', name: '心内科', slug: 'cardiology', description: '', sort_order: 3, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '4', name: '骨科', slug: 'orthopedics', description: '', sort_order: 4, is_active: true, created_at: '', updated_at: '', icon: null },
      { id: '5', name: '妇产科', slug: 'obstetrics-gynecology', description: '', sort_order: 6, is_active: true, created_at: '', updated_at: '', icon: null },
    ];
  } finally {
    loading.value = false;
  }
};

const loadStarredIds = () => {
  try {
    const stored = uni.getStorageSync('starred_category_ids');
    starredIds.value = stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('[读取星标失败]', error);
    starredIds.value = [];
  }
};

const saveStarredIds = () => {
  try {
    uni.setStorageSync('starred_category_ids', JSON.stringify(starredIds.value));
  } catch (error) {
    console.error('[保存星标失败]', error);
  }
};

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value;
};

const isStarred = (id: string): boolean => {
  return starredIds.value.includes(id);
};

const isStarDisabled = (id: string): boolean => {
  return !isStarred(id) && starredIds.value.length >= 5;
};

const handleToggleStar = (id: string) => {
  if (isStarred(id)) {
    // 取消星标
    starredIds.value = starredIds.value.filter(sid => sid !== id);
    uni.showToast({ title: '已取消固定', icon: 'none' });
  } else {
    // 添加星标
    if (starredIds.value.length >= 5) {
      uni.showToast({ title: '最多固定5个科室', icon: 'none' });
      return;
    }
    starredIds.value.push(id);
    uni.showToast({ title: '已固定到首页', icon: 'none' });
  }
  
  saveStarredIds();
};

const handleRemoveStar = (id: string) => {
  starredIds.value = starredIds.value.filter(sid => sid !== id);
  saveStarredIds();
  uni.showToast({ title: '已取消固定', icon: 'none' });
};

onMounted(() => {
  loadStarredIds();
  loadCategories();
});
</script>

<style lang="scss" scoped>
.all-categories-page {
  min-height: 100vh;
  background: #f4f6f8; /* 更柔和的底色 */
  padding-bottom: 40rpx;
}

.action {
  font-size: 28rpx;
  color: #0F766E; /* 统一为主色 */
  padding: 8rpx 16rpx;
}

/* --- 参照品牌页面的搜索UI --- */
.search-container {
  padding: 16rpx 24rpx;
  background: #fff;
}

/* 搜索框：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊，高度 72rpx 公共默认）
   图标/占位/输入样式局部保留，颜色走 --search-* token */

.search-icon {
  font-size: 32rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.search-input {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
  color: #333;
  caret-color: #0F766E;
  background: transparent;
  outline: none;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.search-placeholder {
  color: var(--search-placeholder);
}

/* --- 新版现代化样式 --- */

.card-section {
  background: #ffffff;
  margin: 20rpx 24rpx;
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04); /* PRO-MAX: 使用极轻柔的体系阴影 Level1 */
}

/* 标题组优化 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section-actions {
  display: flex;
  align-items: center;
}

.title-group {
  display: flex;
  align-items: baseline;
}
.main-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #1a1a1a;
}
.sub-title {
  font-size: 24rpx;
  color: #999;
  margin-left: 16rpx;
}
.limit-badge {
  font-size: 20rpx;
  color: #ff4d4f;
  background: #fff2f0;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

/* 胶囊网格布局 */
.tags-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24rpx; /* PRO-MAX: 放大间距让元素更呼吸 */
  margin-top: 24rpx;
}
.tag-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #333;
  padding: 0 32rpx;
  min-height: 68rpx; /* PRO-MAX: 保障更好的点击热区高度 */
  border-radius: 34rpx;
  font-size: 26rpx;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); /* PRO-MAX: 丝滑过渡曲线 */
  box-sizing: border-box;
}
.tag-item:active {
  transform: scale(0.92);
}
.tag-item.is-active {
  background: rgba(15, 118, 110, 0.06); /* PRO-MAX: 色彩清洗，对齐主色 #0F766E */
  color: #0F766E; 
  border: 1px solid rgba(15, 118, 110, 0.15);
}
.tag-item.is-disabled {
  opacity: 0.5;
}
.add-icon {
  margin-right: 8rpx;
  font-size: 28rpx;
  font-weight: 500;
  line-height: 1;
}

/* 编辑模式下抖动动画（可选） */
.is-shaking {
  animation: shake 0.3s infinite ease-in-out alternate;
}
@keyframes shake {
  0% { transform: rotate(-1deg); }
  100% { transform: rotate(1deg); }
}

/* 编辑模式下的小红叉 */
.remove-badge {
  position: absolute;
  top: -12rpx;
  right: -12rpx;
  width: 36rpx;
  height: 36rpx;
  background: #ff4d4f;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid #fff;
  box-shadow: 0 2rpx 8rpx rgba(255, 77, 79, 0.3);
  z-index: 2;
}
.icon-close {
  font-size: 20rpx;
  line-height: 1;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80rpx 0;
  font-size: 28rpx;
  color: #999;
}
</style>
