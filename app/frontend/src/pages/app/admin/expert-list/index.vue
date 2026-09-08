<template>
  <view class="admin-page consumer-layout">
    <view class="top-bar">
      <view class="tab-bar">
        <view
          v-for="(t, idx) in tabs"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text class="tab-label">{{ t.label }}</text>
          <view v-if="activeIndex === idx" class="tab-indicator" />
        </view>
      </view>
      <view class="header-actions">
        <view class="header-btn" @tap="handleImport">
          <text>导入</text>
        </view>
        <view class="header-btn header-btn--primary" @tap="openCreateForm">
          <text>＋ 新增</text>
        </view>
      </view>
    </view>

    <view v-if="activeTab !== 'unmapped'" class="filter-bar">
      <view class="app-search-field filter-search">
        <text class="filter-icon iconfont icon-search"></text>
        <input
          class="filter-input"
          v-model="searchKeyword"
          placeholder="搜索专家姓名"
          placeholder-class="filter-placeholder"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="searchKeyword = ''" />
        </view>
      </view>
      <wd-picker
        v-model="filterCategoryIdx"
        :columns="filterCategoryCols"
        title="选择分类"
        :z-index="3000"
        @confirm="onCategoryChange"
      >
        <view class="filter-tag">{{ selectedCategoryLabel }}</view>
      </wd-picker>
      <wd-picker
        v-model="filterDeptIdx"
        :columns="filterDeptCols"
        title="选择科室"
        :z-index="3000"
        @confirm="onDeptChange"
      >
        <view class="filter-tag">{{ selectedDeptLabel }}</view>
      </wd-picker>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换，仅激活 Tab 渲染内容避免串扰） -->
    <view
      v-for="(t, idx) in tabs"
      :key="t.key"
      class="admin-panel"
      v-show="activeIndex === idx"
    >
    <scroll-view
      class="list-scroll"
      scroll-y
      @scrolltolower="loadMore"
      :refresher-enabled="true"
      :refresher-triggered="isPullRefreshing"
      @refresherrefresh="onRefresh"
      :lower-threshold="150"
    >
      <view class="list-inner">
        <view v-if="(isLoading || isRefreshing) && experts.length === 0">
          <view v-for="i in 4" :key="i" class="skeleton-card">
            <view class="skeleton-avatar" />
            <view class="skeleton-body">
              <view class="skeleton-line skeleton-line--long" />
              <view class="skeleton-line skeleton-line--short" />
            </view>
          </view>
        </view>

        <view v-else-if="error && experts.length === 0" class="placeholder-block">
          <text class="placeholder-icon iconfont icon-error"></text>
          <text class="placeholder-title">加载失败</text>
          <text class="placeholder-desc">{{ error }}</text>
          <view class="retry-btn" @tap="loadExperts(true)">点击重试</view>
        </view>

        <view v-else-if="!isLoading && !isRefreshing && experts.length === 0" class="placeholder-block">
          <text class="placeholder-icon iconfont icon-my"></text>
          <text class="placeholder-title">{{ emptyTitle }}</text>
          <text class="placeholder-desc">{{ emptyDesc }}</text>
        </view>

        <template v-else>
          <view
            v-for="item in experts"
            :key="item.id"
            class="expert-card"
          >
            <ProxyImage
              class="expert-avatar"
              :src="resolveMediaUrl(item.avatar_url || '')"
              :fallback="DEFAULT_AVATAR"
              mode="aspectFill"
              lazy-load
            />
            <view class="expert-info">
              <view class="expert-name-row">
                <text class="expert-name">{{ item.name }}</text>
                <view v-if="getIsFeatured(item)" class="expert-badge badge--featured">
                  <text>推荐</text>
                </view>
              </view>
              <text
                v-if="item.title || item.hospital"
                class="expert-subtitle"
              >{{ [item.title, item.hospital].filter(Boolean).join(' · ') }}</text>
              <view v-if="getDepartmentName(item) || getCategoryName(item) || getExpertiseAreas(item)" class="expert-meta-row">
                <text v-if="getDepartmentName(item)" class="expert-dept">{{ getDepartmentName(item) }}</text>
                <text v-else-if="getCategoryName(item)" class="expert-category">分类：{{ getCategoryName(item) }}</text>
                <text
                  v-if="getExpertiseAreas(item)"
                  class="expert-tags"
                >{{ (getExpertiseAreas(item) || '').split(/[,，;；]/).filter(Boolean).map(s => s.trim()).slice(0, 4).join(' · ') }}</text>
              </view>
            </view>
            <view class="expert-actions">
              <view
                v-if="activeTab === 'unmapped'"
                class="action-btn action-btn--primary"
                @tap.stop="openAssignModal(item)"
              >
                <text>分配科室</text>
              </view>
              <view class="action-btn" @tap.stop="openEditForm(item)">
                <text>编辑</text>
              </view>
              <view class="action-btn action-btn--danger" @tap.stop="handleDelete(item)">
                <text>删除</text>
              </view>
            </view>
          </view>

          <view v-if="isLoading" class="loading-more">
            <text>加载中...</text>
          </view>
          <view v-if="!hasMore && experts.length > 0" class="no-more">
            <text>没有更多了</text>
          </view>
        </template>
      </view>
    </scroll-view>
    </view>

    <ModalDialog
      :visible="isFormVisible"
      :title="formMode === 'create' ? '新增专家' : '编辑专家'"
      :confirmText="formMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isSubmitting"
      @update:visible="isFormVisible = $event"
      @confirm="handleFormConfirm"
      @cancel="closeForm"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">姓名</text>
          <input class="form-input" v-model="formModel.name" placeholder="请输入专家姓名" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">职称</text>
          <input class="form-input" v-model="formModel.title" placeholder="如：主任医师" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">医院</text>
          <input class="form-input" v-model="formModel.hospital" placeholder="如：北京协和医院" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">所属科室</text>
          <wd-picker
            v-model="formDeptIdx"
            :columns="formDeptCols"
            title="选择所属科室"
            :z-index="3000"
            @confirm="onFormDeptChange"
          >
            <view class="form-picker">
              <text>{{ formDeptName }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">简介</text>
          <textarea class="form-textarea" v-model="formModel.bio" placeholder="专家简介（选填）" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">擅长领域</text>
          <input class="form-input" v-model="formModel.expertise_areas" placeholder="多个领域用逗号分隔，如：心血管疾病, 介入治疗" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">所属分类</text>
          <wd-picker
            v-model="formCatIdx"
            :columns="formCatCols"
            title="选择所属分类"
            :z-index="3000"
            @confirm="onFormCatChange"
          >
            <view class="form-picker">
              <text>{{ formCatName }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group form-group--switch">
          <text class="form-label">首页推荐</text>
          <switch :checked="formModel.is_featured" @change="formModel.is_featured = $event.detail.value" color="#0F766E" />
        </view>
        <view class="form-group">
          <text class="form-label">头像URL</text>
          <input class="form-input" v-model="formModel.avatar_url" placeholder="请输入头像图片URL" placeholder-class="form-placeholder" />
        </view>
        <view v-if="formMode === 'edit'" class="form-group form-group--switch">
          <text class="form-label">启用专家</text>
          <switch :checked="formModel.is_active" @change="formModel.is_active = $event.detail.value" color="#0F766E" />
        </view>
      </view>
    </ModalDialog>

    <ModalDialog
      :visible="showAssignModal"
      title="分配科室"
      confirmText="确定"
      :confirmLoading="isAssigning"
      @update:visible="showAssignModal = $event"
      @confirm="handleAssignConfirm"
      @cancel="closeAssignModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">所属分类</text>
          <wd-picker
            v-model="assignCatIdx"
            :columns="assignCatCols"
            title="选择所属分类"
            :z-index="3000"
            @confirm="onAssignCatChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !assignCategoryId }">
                {{ assignCatName || '请选择分类' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">选择科室</text>
          <wd-picker
            v-model="assignDeptIdx"
            :columns="assignDeptCols"
            title="选择科室"
            :z-index="3000"
            @confirm="onAssignDeptChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !assignDeptId }">
                {{ assignDeptName || '请选择科室' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-note">分配后该专家将从"未分配"列表中移除。</text>
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { getAdminExperts, createExpert, updateExpert, deleteExpert } from '@/api/expert';
import { getUnmappedExperts, getDepartments } from '@/api/department';
import { getCategories } from '@/api/category';
import { resolveMediaUrl } from '@/utils/url';
import { DEFAULT_AVATAR } from '@/constants/assets';
import ProxyImage from '@/components/common/ProxyImage.vue';
import WdPicker from 'wot-design-uni/components/wd-picker/wd-picker.vue';
import { useAdminGuard } from '@/composables/useAdminGuard';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import type { Expert } from '@/types/expert';
import type { UnmappedExpert } from '@/types/department';
import type { Category } from '@/types/category';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import ClearButton from '@/components/app/ClearButton.vue';

const tabs = [
  { key: 'all', label: '全部专家' },
  { key: 'inactive', label: '已下架' },
  { key: 'unmapped', label: '未分配科室' },
];
const activeTab = ref('all');

/**
 * Tab 索引 ↔ 业务联动：设置 activeTab（watch(activeTab) 会自动触发重新加载）
 */
function onTabActivated(idx: number): void {
  const t = tabs[idx];
  if (!t) return;
  if (activeTab.value === t.key) return;
  activeTab.value = t.key;
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabs.length,
  onTabActivated,
  0
);

const experts = ref<(Expert | UnmappedExpert)[]>([]);
const isLoading = ref(false);
const isRefreshing = ref(false);
const error = ref<string | null>(null);
const page = ref(1);
const size = 20;
const total = ref(0);
const hasMore = computed(() => page.value * size < total.value);
const loadedOnce = ref(false);
/** 刷新结果合并：请求进行中又来了刷新请求时标记一次，本轮结束后自动补跑 */
let pendingRefresh = false;
/** loadMore 失败冷却（ms）：后端持续报错时避免触底即重发请求链 */
const LOAD_MORE_FAIL_COOLDOWN = 3000;
let lastLoadMoreFailTime = 0;

const searchKeyword = ref('');
const selectedCategoryId = ref<string | null>(null);
const selectedDepartmentId = ref<string | null>(null);
const categories = ref<Category[]>([]);
const deptOptions = ref<{ id: string; name: string; category_id: string; is_active: boolean }[]>([]);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const categoryLabels = computed(() => ['全部分类', ...categories.value.map(c => c.display_name || c.name)]);
const selectedCategoryLabel = computed(() => {
  if (!selectedCategoryId.value) return '全部分类';
  const cat = categories.value.find(c => c.id === selectedCategoryId.value);
  return cat ? (cat.display_name || cat.name) : '全部分类';
});
const deptLabels = computed(() => ['全部科室', ...deptOptions.value.map(d => d.name)]);
const selectedDeptLabel = computed(() => {
  if (!selectedDepartmentId.value) return '全部科室';
  const d = deptOptions.value.find(d => d.id === selectedDepartmentId.value);
  return d ? d.name : '全部科室';
});

// —— P2 短枚举迁移：wd-picker 列（value=index，与原生 picker index 语义一致）+ 受控 index ——
const filterCategoryCols = computed(() => categoryLabels.value.map((label, i) => ({ value: i, label })));
const filterDeptCols = computed(() => deptLabels.value.map((label, i) => ({ value: i, label })));
const formDeptCols = computed(() => formDeptLabels.value.map((label, i) => ({ value: i, label })));
const formCatCols = computed(() => formCatLabels.value.map((label, i) => ({ value: i, label })));
const assignCatCols = computed(() => assignCatLabels.value.map((label, i) => ({ value: i, label })));
const assignDeptCols = computed(() => assignDeptLabels.value.map((label, i) => ({ value: i, label })));

const filterCategoryIdx = ref(0);
const filterDeptIdx = ref(0);
const formDeptIdx = ref(0);
const formCatIdx = ref(0);
const assignCatIdx = ref(0);
const assignDeptIdx = ref(0);

const isFormVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const editingExpertId = ref<string | null>(null);
const isSubmitting = ref(false);
const formModel = ref({
  name: '',
  title: '',
  hospital: '',
  department_id: null as string | null,
  bio: '',
  avatar_url: '',
  expertise_areas: '',
  category_id: null as string | null,
  is_featured: false,
  is_active: true,
});

const showAssignModal = ref(false);
const assignExpertId = ref<string | null>(null);
const assignCategoryId = ref<string | null>(null);
const assignDeptId = ref<string | null>(null);
const isAssigning = ref(false);

const expandedExpertId = ref<string | null>(null);

const activeDeptOptions = computed(() =>
  deptOptions.value.filter(d => d.is_active)
);

const assignAvailableDepts = computed(() => {
  if (!assignCategoryId.value) return activeDeptOptions.value;
  return activeDeptOptions.value.filter(d => d.category_id === assignCategoryId.value);
});

const assignCatLabels = computed(() => ['不修改分类', ...categories.value.map(c => c.display_name || c.name)]);
const assignCatName = computed(() => {
  if (!assignCategoryId.value) return '不修改分类';
  const c = categories.value.find(c => c.id === assignCategoryId.value);
  return c ? (c.display_name || c.name) : '不修改分类';
});

const assignDeptLabels = computed(() => assignAvailableDepts.value.map(d => d.name));
const assignDeptName = computed(() => {
  if (!assignDeptId.value) return '';
  const d = assignAvailableDepts.value.find(d => d.id === assignDeptId.value);
  return d ? d.name : '';
});

const emptyTitle = computed(() => {
  if (activeTab.value === 'unmapped') return '所有专家已分配科室';
  if (activeTab.value === 'inactive') return '暂无已下架专家';
  return '暂无专家';
});
const emptyDesc = computed(() => {
  if (activeTab.value === 'unmapped') return '没有未分配科室的专家';
  if (activeTab.value === 'inactive') return '下架的专家将在此处显示，可编辑恢复';
  return '点击右上角新增专家';
});

function getDepartmentName(item: Expert | UnmappedExpert) {
  if ('department_name' in item) return (item as Expert).department_name;
  return null;
}

function getCategoryName(item: Expert | UnmappedExpert) {
  return item.category_name || null;
}

function getIsFeatured(item: Expert | UnmappedExpert) {
  if ('is_featured' in item) return (item as Expert).is_featured;
  return false;
}

function getBio(item: Expert | UnmappedExpert) {
  if ('bio' in item) return (item as Expert).bio;
  return null;
}

function getExpertiseAreas(item: Expert | UnmappedExpert) {
  const v = item.expertise_areas;
  // 未分配专家（UnmappedExpert）的 expertise_areas 为数组——归一化为字符串，
  // 否则模板 .split() 对数组调用会抛 TypeError 导致整页白屏（空数组同为 truthy 必触发）
  if (Array.isArray(v)) return v.filter(Boolean).join('，') || null;
  return v || null;
}

async function loadExperts(refresh = false) {
  if (!refresh) {
    await loadMore();
    return;
  }
  // 串行队列：上一轮请求未完成时，标记待补跑并返回（本轮结束后自动补跑一次）。
  // 不再使用 800ms 冷却直接丢弃——Tab 切换/筛选等关键刷新在冷却窗口内会被吞掉（停在旧 Tab 数据），
  // 高频重复触发（onShow/watch 双发、快速连点）由 pendingRefresh 合并为一次补跑，效果等同且不丢请求。
  if (isLoading.value || isRefreshing.value) {
    pendingRefresh = true;
    return;
  }

  isRefreshing.value = true;
  error.value = null;
  page.value = 1;
  experts.value = [];

  try {
    const params: Record<string, any> = { page: page.value, size };

    let res: any;
    if (activeTab.value === 'unmapped') {
      res = await getUnmappedExperts(params, { showLoading: false });
    } else {
      // 已下架 Tab 查询 is_active=false，其余查询启用专家
      params.is_active = activeTab.value === 'inactive' ? false : true;
      if (searchKeyword.value) {
        params.name = searchKeyword.value;
      }
      if (selectedCategoryId.value) {
        params.category_id = selectedCategoryId.value;
      }
      if (selectedDepartmentId.value) {
        params.department_id = selectedDepartmentId.value;
      }
      res = await getAdminExperts(params, { showLoading: false });
    }

    if (res.code === 200) {
      experts.value = res.data.items || [];
      total.value = res.data.total || 0;
    }
  } catch (e: any) {
    error.value = e?.message || '加载失败，下拉重试';
  } finally {
    isRefreshing.value = false;
    loadedOnce.value = true;
    // 期间有新请求到达则自动补跑一次（合并 watch/onShow/筛选连续触发的刷新）
    if (pendingRefresh) {
      pendingRefresh = false;
      await loadExperts(true);
    }
  }
}

async function loadMore() {
  // 空列表（首屏/失败态/空态）时跳过，避免 scroll-view 滚动到底部自激触发无限循环
  if (experts.value.length === 0) return;
  if (!hasMore.value) return;
  // 已有进行中的刷新/加载，直接合并
  if (isLoading.value || isRefreshing.value) return;
  // 失败冷却：后端持续报错时避免触底即重发（3 秒内不重复请求）
  if (Date.now() - lastLoadMoreFailTime < LOAD_MORE_FAIL_COOLDOWN) return;

  isLoading.value = true;
  error.value = null;

  const currentPage = page.value;
  try {
    const params: Record<string, any> = { page: currentPage + 1, size };

    let res: any;
    if (activeTab.value === 'unmapped') {
      res = await getUnmappedExperts(params, { showLoading: false });
    } else {
      params.is_active = activeTab.value === 'inactive' ? false : true;
      if (searchKeyword.value) params.name = searchKeyword.value;
      if (selectedCategoryId.value) params.category_id = selectedCategoryId.value;
      if (selectedDepartmentId.value) params.department_id = selectedDepartmentId.value;
      res = await getAdminExperts(params, { showLoading: false });
    }

    if (res.code === 200) {
      const items = res.data.items || [];
      // 去重追加：防止后端分页不稳定导致的数据重复
      const existingIds = new Set(experts.value.map(e => e.id));
      const newItems = items.filter((item: any) => !existingIds.has(item.id));
      experts.value = [...experts.value, ...newItems];
      // 空页判定为到底；非空页无论是否混入重复数据都继续翻页，
      // 避免重复页导致 page 停滞、每次下拉都请求同一页而无法加载新数据
      if (items.length === 0) {
        total.value = experts.value.length;
      } else {
        total.value = Math.max(total.value, res.data.total || 0);
        page.value = currentPage + 1;
      }
    } else {
      lastLoadMoreFailTime = Date.now();
    }
  } catch (e: any) {
    error.value = e?.message || '加载失败，下拉重试';
    lastLoadMoreFailTime = Date.now();
  } finally {
    isLoading.value = false;
  }
}

/** 下拉刷新最小展示时长（ms）：请求过快时保证指示器可感知 */
const PULL_REFRESH_MIN_MS = 400;
const isPullRefreshing = ref(false);
let pullRefreshStartTime = 0;

async function onRefresh() {
  if (isPullRefreshing.value) return;
  isPullRefreshing.value = true;
  pullRefreshStartTime = Date.now();
  try {
    await loadExperts(true);
  } finally {
    const elapsed = Date.now() - pullRefreshStartTime;
    if (elapsed < PULL_REFRESH_MIN_MS) {
      await new Promise(resolve => setTimeout(resolve, PULL_REFRESH_MIN_MS - elapsed));
    }
    isPullRefreshing.value = false;
  }
}

function onCategoryChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  selectedCategoryId.value = idx === 0 ? null : categories.value[idx - 1]?.id || null;
  loadExperts(true);
}

function onDeptChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  selectedDepartmentId.value = idx === 0 ? null : deptOptions.value[idx - 1]?.id || null;
  loadExperts(true);
}

watch(searchKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadExperts(true);
  }, 300);
});

async function loadFilters() {
  try {
    const [catRes, deptRes] = await Promise.allSettled([
      getCategories({ showLoading: false }),
      getDepartments({ page: 1, size: 200 }, { showLoading: false }),
    ]);
    if (catRes.status === 'fulfilled' && catRes.value.code === 200) {
      categories.value = catRes.value.data || [];
    }
    if (deptRes.status === 'fulfilled' && deptRes.value.code === 200) {
      deptOptions.value = (deptRes.value.data as any).items || [];
    }
  } catch {
    /* silent */
  }
}

function openCreateForm() {
  formMode.value = 'create';
  editingExpertId.value = null;
  formModel.value = { name: '', title: '', hospital: '', department_id: null, bio: '', avatar_url: '', expertise_areas: '', category_id: null, is_featured: false, is_active: true };
  formCatIdx.value = 0;
  formDeptIdx.value = 0;
  isFormVisible.value = true;
}

function openEditForm(item: Expert | UnmappedExpert) {
  formMode.value = 'edit';
  editingExpertId.value = item.id;
  formModel.value = {
    name: item.name,
    title: (item as any).title || '',
    hospital: (item as any).hospital || '',
    department_id: getDepartmentName(item) ? (item as Expert).department_id : null,
    bio: 'bio' in item ? (item as Expert).bio || '' : '',
    avatar_url: item.avatar_url || '',
    expertise_areas: (item as any).expertise_areas || '',
    category_id: (item as any).category_id || null,
    is_featured: 'is_featured' in item ? (item as Expert).is_featured : false,
    is_active: 'is_active' in item ? (item as Expert).is_active : true,
  };
  // wd-picker 回填定位（分类/科室，'不指定' 占 idx0）
  const catIdx = formModel.value.category_id
    ? categories.value.findIndex(c => c.id === formModel.value.category_id)
    : -1;
  formCatIdx.value = catIdx >= 0 ? catIdx + 1 : 0;
  const deptIdx = formModel.value.department_id
    ? availableFormDepts.value.findIndex(d => d.id === formModel.value.department_id)
    : -1;
  formDeptIdx.value = deptIdx >= 0 ? deptIdx + 1 : 0;
  isFormVisible.value = true;
}

function closeForm() {
  isFormVisible.value = false;
  formModel.value = { name: '', title: '', hospital: '', department_id: null, bio: '', avatar_url: '', expertise_areas: '', category_id: null, is_featured: false, is_active: true };
  formCatIdx.value = 0;
  formDeptIdx.value = 0;
}

const availableFormDepts = computed(() => {
  if (!formModel.value.category_id) return activeDeptOptions.value;
  return activeDeptOptions.value.filter(d => d.category_id === formModel.value.category_id);
});

function onFormDeptChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  if (idx === 0) {
    formModel.value.department_id = null;
  } else {
    const dept = availableFormDepts.value[idx - 1];
    formModel.value.department_id = dept?.id || null;
    if (dept?.category_id) {
      formModel.value.category_id = dept.category_id;
      // 分类被科室联动同步：wd-picker 分类定位同步到对应行（'不指定分类' 占 idx0）
      const catIdx = categories.value.findIndex(c => c.id === dept.category_id);
      formCatIdx.value = catIdx >= 0 ? catIdx + 1 : 0;
    }
  }
}

const formDeptLabels = computed(() => ['不指定科室', ...availableFormDepts.value.map(d => d.name)]);
const formDeptName = computed(() => {
  if (!formModel.value.department_id) return '不指定科室';
  const d = availableFormDepts.value.find(d => d.id === formModel.value.department_id);
  return d ? d.name : '不指定科室';
});

function onFormCatChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  formModel.value.category_id = idx === 0 ? null : categories.value[idx - 1]?.id || null;
  formModel.value.department_id = null;
  formDeptIdx.value = 0;
}

const formCatLabels = computed(() => ['不指定分类', ...categories.value.map(c => c.display_name || c.name)]);
const formCatName = computed(() => {
  if (!formModel.value.category_id) return '不指定分类';
  const c = categories.value.find(c => c.id === formModel.value.category_id);
  return c ? (c.display_name || c.name) : '不指定分类';
});

async function handleFormConfirm() {
  if (!formModel.value.name.trim()) {
    uni.showToast({ title: '请输入专家姓名', icon: 'none' });
    return;
  }

  // 一致性校验（后端 4.1：分类必须与所属科室一致，否则 400）
  const deptId = formModel.value.department_id;
  const catId = formModel.value.category_id;
  if (deptId && catId) {
    const dept = activeDeptOptions.value.find(d => d.id === deptId);
    if (dept?.category_id && dept.category_id !== catId) {
      uni.showToast({ title: '分类与所属科室不一致，请调整', icon: 'none' });
      return;
    }
  }

  isSubmitting.value = true;
  try {
    const payload: Record<string, any> = {
      name: formModel.value.name.trim(),
      title: formModel.value.title.trim() || undefined,
      hospital: formModel.value.hospital.trim() || undefined,
      department_id: formModel.value.department_id || undefined,
      bio: formModel.value.bio.trim() || undefined,
      avatar_url: formModel.value.avatar_url.trim() || undefined,
      expertise_areas: formModel.value.expertise_areas.trim() || undefined,
      category_id: formModel.value.category_id || undefined,
      is_featured: formModel.value.is_featured,
      is_active: formModel.value.is_active,
      is_verified: true,
    };

    if (formMode.value === 'create') {
      await createExpert(payload as any);
      uni.showToast({ title: '创建成功', icon: 'success' });
    } else {
      await updateExpert(editingExpertId.value!, payload as any);
      uni.showToast({ title: '保存成功', icon: 'success' });
    }
    closeForm();
    loadExperts(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isSubmitting.value = false;
  }
}

async function handleDelete(item: Expert | UnmappedExpert) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({
      title: '确认删除',
      content: `确定要删除专家「${item.name}」吗？`,
      confirmColor: '#dc2626',
      success: r => resolve(r),
    });
  });

  if (!confirm) return;

  try {
    await deleteExpert(item.id);
    uni.showToast({ title: '已删除', icon: 'success' });
    experts.value = experts.value.filter(e => e.id !== item.id);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
  }
}

function openAssignModal(item: Expert | UnmappedExpert) {
  assignExpertId.value = item.id;
  assignCategoryId.value = item.category_id || null;
  assignDeptId.value = null;
  // wd-picker 分类定位同步（'不修改分类' 占 idx0）；科室重置 0
  const catIdx = assignCategoryId.value
    ? categories.value.findIndex(c => c.id === assignCategoryId.value)
    : -1;
  assignCatIdx.value = catIdx >= 0 ? catIdx + 1 : 0;
  assignDeptIdx.value = 0;
  showAssignModal.value = true;
}

function closeAssignModal() {
  showAssignModal.value = false;
  assignExpertId.value = null;
  assignCategoryId.value = null;
  assignDeptId.value = null;
}

function onAssignCatChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  assignCategoryId.value = idx === 0 ? null : categories.value[idx - 1]?.id || null;
  assignDeptId.value = null;
  assignDeptIdx.value = 0;
}

function onAssignDeptChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  const dept = assignAvailableDepts.value[idx];
  assignDeptId.value = dept?.id || null;
  // 对齐主表单联动：选科室后同步分类，防止后端 4.1 校验不一致 400
  if (dept?.category_id) {
    assignCategoryId.value = dept.category_id;
    // 分类被科室联动同步：wd-picker 分类定位同步（'不修改分类' 占 idx0）
    const catIdx = categories.value.findIndex(c => c.id === dept.category_id);
    assignCatIdx.value = catIdx >= 0 ? catIdx + 1 : 0;
  }
}

async function handleAssignConfirm() {
  if (!assignDeptId.value) {
    uni.showToast({ title: '请选择科室', icon: 'none' });
    return;
  }
  isAssigning.value = true;
  try {
    const payload: Record<string, any> = { department_id: assignDeptId.value };
    if (assignCategoryId.value) {
      payload.category_id = assignCategoryId.value;
    }
    await updateExpert(assignExpertId.value!, payload);
    uni.showToast({ title: '分配成功', icon: 'success' });
    closeAssignModal();
    experts.value = experts.value.filter(e => e.id !== assignExpertId.value);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isAssigning.value = false;
  }
}

function handleImport() {
  uni.showToast({ title: '批量导入功能开发中', icon: 'none' });
}

watch(activeTab, () => {
  loadExperts(true);
});

onLoad((options?: any) => {
  // 直链指定 tab 时直接写入（watch 的 immediate 会在同帧晚于 onLoad 触发，
  // 由 pendingRefresh 合并，不会产生双请求）
  const tab = options?.tab;
  if (tab && tabs.some(t => t.key === tab) && activeTab.value !== tab) {
    activeTab.value = tab as string;
  }
});

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) {
    loadFilters();
    loadExperts(true);
  }
});

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = null;
});
</script>

<style lang="scss" scoped>
.admin-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: var(--home-bg);
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx var(--home-spacing-page);
  border-bottom: 1rpx solid var(--home-divider);
}

.tab-bar {
  display: flex;
  gap: 0;
}

.tab-item {
  position: relative;
  padding: 16rpx 12rpx;
  flex-shrink: 0;
  transition: color var(--transition-base);
}

.tab-label {
  font-size: 28rpx;
  color: var(--home-text2);
}

.tab-item--active .tab-label {
  color: var(--home-primary);
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 32rpx;
  height: 4rpx;
  background-color: var(--home-primary);
  border-radius: 2rpx;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx var(--home-spacing-page);
  background: var(--home-bg);
}

.filter-search {
  /* 叠加共享容器 .app-search-field：白底+1rpx细边+胶囊；高度 64rpx（管理端档，D6） */
  height: 64rpx;
  box-sizing: border-box;
}

.filter-icon {
  font-size: 26rpx;
  margin-right: 12rpx;
  color: var(--search-icon);
  flex-shrink: 0;
  line-height: 1;
}

.filter-input {
  flex: 1;
  height: 100%;
  font-size: 26rpx;
  color: var(--home-text1);
  background: transparent;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.filter-placeholder {
  color: var(--search-placeholder);
}

.filter-tag {
  height: 64rpx;
  line-height: 64rpx;
  padding: 0 20rpx;
  background: var(--home-card);
  border-radius: var(--home-r-pill); /* D4：与输入框同步胶囊 */
  border: 1rpx solid var(--search-border);
  font-size: 24rpx;
  color: var(--home-text1);
  white-space: nowrap;
  transition: border-color var(--transition-base);
}

/* 内容区 Tab 面板：flex 撑满剩余高度（根容器 100vh + flex column） */
.admin-panel { flex: 1; min-height: 0; overflow: hidden; }

.list-scroll { height: 100%; overflow-y: auto; -webkit-overflow-scrolling: touch; }

.list-inner {
  padding: 0 var(--home-spacing-page);
}

.expert-card {
  display: flex;
  align-items: flex-start;
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  border: 1rpx solid var(--home-divider);
  transition: box-shadow var(--transition-base);
}

.expert-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  margin-right: 20rpx;
}

.expert-info {
  flex: 1;
  min-width: 0;
}

.expert-category {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: var(--home-text2);
}

.expert-classification {
  margin-top: 4rpx;
}

.placeholder-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}

.placeholder-icon {
  font-size: 72rpx;
  margin-bottom: 24rpx;
}

.placeholder-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
  margin-bottom: 12rpx;
}

.placeholder-desc {
  font-size: 24rpx;
  color: var(--home-text2);
}

.retry-btn {
  margin-top: 24rpx;
  padding: 16rpx 48rpx;
  background: var(--home-primary);
  color: #fff;
  border-radius: 8rpx;
  font-size: 26rpx;
}

.skeleton-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: 12rpx;
}

.skeleton-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: var(--home-divider);
  flex-shrink: 0;
  margin-right: 20rpx;
}

.skeleton-body {
  flex: 1;
}

.skeleton-line {
  height: 20rpx;
  background: var(--home-divider);
  border-radius: 4rpx;
  margin-bottom: 12rpx;
}

.skeleton-line--long {
  width: 50%;
}

.skeleton-line--short {
  width: 35%;
  margin-bottom: 0;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: var(--home-text2);
}

.expert-actions {
  display: flex;
  gap: 12rpx;
  margin-top: 14rpx;
  padding-top: 14rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}

.action-btn {
  padding: 8rpx 20rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: var(--home-text1);
  background: rgba(0, 0, 0, 0.04);
}

.action-btn--primary {
  color: var(--home-action-primary-text);
  background: var(--home-action-primary-bg);
}

.action-btn--danger {
  color: var(--home-action-danger-text);
  background: var(--home-action-danger-bg);
}

.form {
  padding: 8rpx 0;
}

.form-group {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-text1);
  margin-bottom: 10rpx;
}

.form-input {
  width: 100%;
  height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  height: 120rpx;
  padding: 16rpx 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
  box-sizing: border-box;
}

.form-placeholder {
  color: var(--home-text2);
}

.form-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
}

.picker-arrow {
  font-size: 20rpx;
  color: var(--home-text2);
}

.form-note {
  font-size: 22rpx;
  color: var(--home-text2);
  line-height: 1.6;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.header-btn {
  padding: 6rpx 10rpx;
  border: 1rpx solid var(--home-border);
  border-radius: var(--home-r-pill);
  font-size: 22rpx;
  color: var(--home-text1);
  min-height: 48rpx;
  line-height: 48rpx;
  transition: all var(--transition-base);
}

.header-btn--primary {
  color: #fff;
  background: var(--home-primary);
  border-color: var(--home-primary);
}

.expert-name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 6rpx;
}

.expert-name {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.expert-badge {
  padding: 2rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  line-height: 1.5;
  flex-shrink: 0;
}

.badge--featured {
  background: var(--home-badge-featured-bg);
  color: var(--home-badge-featured-text);
}

.expert-subtitle {
  display: block;
  font-size: 24rpx;
  color: var(--home-text2);
  line-height: 1.4;
}

.expert-meta-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 4rpx;
  overflow: hidden;
}

.expert-dept {
  font-size: 22rpx;
  color: var(--home-primary);
  flex-shrink: 0;
}

.expert-category {
  font-size: 22rpx;
  color: var(--home-text2);
  flex-shrink: 0;
}

.expert-tags {
  font-size: 22rpx;
  color: var(--home-text2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10rpx;
  flex-shrink: 0;
  margin-left: 16rpx;
  padding-top: 14rpx;
  border-top: 1rpx solid var(--home-divider);
}

.action-btn {
  padding: 8rpx 0;
  width: 136rpx;
  text-align: center;
  border-radius: var(--home-r-pill);
  font-size: 22rpx;
  color: var(--home-text1);
  background: var(--home-action-secondary-bg);
  white-space: nowrap;
  min-height: 48rpx;
  line-height: 48rpx;
  transition: all var(--transition-base);
}

.action-btn--primary {
  color: var(--home-action-primary-text);
  background: var(--home-action-primary-bg);
}

.action-btn--danger {
  color: var(--home-action-danger-text);
  background: var(--home-action-danger-bg);
}
</style>
