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
        <view
          v-if="!isSelectMode"
          class="header-btn"
          @tap="enterSelectMode"
        >
          <text>选择</text>
        </view>
        <view
          v-else
          class="header-btn header-btn--cancel"
          @tap="exitSelectMode"
        >
          <text>取消</text>
        </view>
        <view class="header-add-btn" @tap="openCreateCategory">
          <text class="add-icon">＋</text>
          <text>新增分类</text>
        </view>
      </view>
    </view>

    <view class="filter-bar">
      <view class="app-search-field filter-search">
        <text class="filter-icon iconfont icon-search"></text>
        <input class="filter-input" v-model="searchKeyword" placeholder="搜索科室名称" placeholder-class="filter-placeholder" />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="searchKeyword = ''" />
        </view>
      </view>
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
        <!-- 首次加载骨架 -->
        <view v-if="isLoading && departments.length === 0">
          <view v-for="i in 4" :key="i" class="skeleton-card">
            <view class="skeleton-line skeleton-line--long" />
            <view class="skeleton-line skeleton-line--short" />
          </view>
        </view>

        <!-- 错误态 -->
        <view v-else-if="error && departments.length === 0" class="placeholder-block">
          <text class="placeholder-icon iconfont icon-error"></text>
          <text class="placeholder-title">加载失败</text>
          <text class="placeholder-desc">{{ error }}</text>
          <view class="retry-btn" @tap="loadDepartments(true)">点击重试</view>
        </view>

        <!-- 空数据 -->
        <view v-else-if="!isLoading && departments.length === 0" class="placeholder-block">
          <text class="placeholder-icon"><uni-icons type="folder-add" size="36" /></text>
          <text class="placeholder-title">{{ emptyTitle }}</text>
          <text class="placeholder-desc">{{ emptyDesc }}</text>
        </view>

        <!-- 科室列表：搜索时平铺，无搜索时按分类分组 -->
        <template v-else>
          <!-- 树状模式：按分类分组 -->
          <template v-if="!searchKeyword">
            <view v-for="group in groupedDepartments" :key="group.categoryId">
              <view class="cat-row" @tap="toggleCat(group.categoryId)">
                <text class="cat-arrow iconfont" :class="expandState[group.categoryId] !== false ? 'icon-arrow-down' : 'icon-arrow-right'"></text>
                <text class="cat-name">{{ group.categoryName }}</text>
                <text class="cat-count">{{ group.items.length }} 个科室</text>
                <view class="cat-edit" @tap.stop="openEditCategory(group)">
                  <text>编辑分类</text>
                </view>
                <view class="cat-edit cat-edit--govern" @tap.stop="openCategoryGovern(group)">
                  <text>治理</text>
                </view>
              </view>
              <template v-if="expandState[group.categoryId] !== false">
                <view
                  v-for="dept in group.items"
                  :key="dept.id"
                  class="dept-card dept-card--child"
                >
                  <view v-if="isSelectMode" class="dept-check" :class="{ 'dept-check--on': selectedIds.has(dept.id), 'dept-check--disabled': dept.is_verified }" @tap.stop="!dept.is_verified && toggleSelect(dept.id)">
                    <text v-if="selectedIds.has(dept.id)" class="check-icon">✓</text>
                  </view>
                  <view class="dept-body">
                    <view class="dept-main">
                      <text class="dept-name">{{ dept.name }}</text>
                      <view class="dept-badge" :class="dept.is_verified ? 'badge--verified' : 'badge--pending'">
                        <text>{{ dept.is_verified ? '已审核' : '待审核' }}</text>
                      </view>
                    </view>
                    <view class="dept-meta">
                      <text class="dept-count">{{ dept.expert_count }} 位专家</text>
                    </view>
                    <view v-if="dept.synonyms && dept.synonyms.length > 0" class="dept-synonyms">
                      <text v-for="s in dept.synonyms" :key="s" class="synonym-tag">{{ s }}</text>
                    </view>
                    <view v-if="!isSelectMode" class="dept-actions">
                      <view v-if="!dept.is_verified" class="action-btn action-btn--primary" @tap.stop="handleAudit(dept)">
                        <text>审核通过</text>
                      </view>
                      <view class="action-btn" @tap.stop="openEditForm(dept)"><text>编辑</text></view>
                      <view class="action-btn action-btn--danger" @tap.stop="handleDelete(dept)"><text>删除</text></view>
                      <view v-if="activeTab === 'all'" class="action-btn" @tap.stop="openMergeModal(dept)"><text>合并</text></view>
                    </view>
                  </view>
                </view>
                <view v-if="activeTab === 'all'" class="add-dept-btn" @tap="openCreateDeptUnder(group)">
                  <text>＋ 新增科室</text>
                </view>
              </template>
            </view>
          </template>
          <!-- 搜索模式：平铺列表 -->
          <template v-else>
            <view v-for="dept in departments" :key="dept.id" class="dept-card">
              <view v-if="isSelectMode" class="dept-check" :class="{ 'dept-check--on': selectedIds.has(dept.id), 'dept-check--disabled': dept.is_verified }" @tap.stop="!dept.is_verified && toggleSelect(dept.id)">
                <text v-if="selectedIds.has(dept.id)" class="check-icon">✓</text>
              </view>
              <view class="dept-body">
                <view class="dept-main">
                  <text class="dept-name">{{ dept.name }}</text>
                  <view class="dept-badge" :class="dept.is_verified ? 'badge--verified' : 'badge--pending'">
                    <text>{{ dept.is_verified ? '已审核' : '待审核' }}</text>
                  </view>
                  <text v-if="dept.category_name" class="dept-cat-tag">{{ dept.category_name }}</text>
                </view>
                <view class="dept-meta">
                  <text class="dept-count">{{ dept.expert_count }} 位专家</text>
                </view>
                <view v-if="dept.synonyms && dept.synonyms.length > 0" class="dept-synonyms">
                  <text v-for="s in dept.synonyms" :key="s" class="synonym-tag">{{ s }}</text>
                </view>
                <view v-if="!isSelectMode" class="dept-actions">
                  <view v-if="!dept.is_verified" class="action-btn action-btn--primary" @tap.stop="handleAudit(dept)">
                    <text>审核通过</text>
                  </view>
                  <view class="action-btn" @tap.stop="openEditForm(dept)"><text>编辑</text></view>
                  <view class="action-btn action-btn--danger" @tap.stop="handleDelete(dept)"><text>删除</text></view>
                  <view v-if="activeTab === 'all'" class="action-btn" @tap.stop="openMergeModal(dept)"><text>合并</text></view>
                </view>
              </view>
            </view>
          </template>

          <view v-if="isLoadingMore" class="loading-more"><text>加载中...</text></view>
          <view v-if="!hasMore && departments.length > 0" class="no-more"><text>没有更多了</text></view>
        </template>
      </view>
    </scroll-view>
    </view>

    <view v-if="isSelectMode" class="select-bar">
      <view class="select-bar-left">
        <view class="select-all-row" @tap="selectAll">
          <view class="select-bar-check" :class="{ 'select-bar-check--on': allSelected }">
            <text v-if="allSelected" class="check-icon">✓</text>
          </view>
          <text>全选</text>
        </view>
        <text class="select-count">已选 {{ selectedIds.size }} 项</text>
      </view>
      <view
        class="batch-btn"
        :class="{ 'batch-btn--disabled': selectedIds.size === 0 }"
        @tap="handleBatchVerify"
      >
        <text>批量审核</text>
      </view>
    </view>

    <ModalDialog
      :visible="isFormVisible"
      :title="formMode === 'create' ? '新增科室' : '编辑科室'"
      :confirmText="formMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isSubmitting"
      @update:visible="isFormVisible = $event"
      @confirm="handleFormConfirm"
      @cancel="closeForm"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">科室名称</text>
          <input
            class="form-input"
            v-model="formModel.name"
            placeholder="请输入科室名称"
            placeholder-class="form-placeholder"
          />
        </view>
        <view class="form-group">
          <text class="form-label">所属分类</text>
          <wd-picker
            v-model="formCatIdx"
            :columns="formCatCols"
            title="选择所属分类"
            :z-index="3000"
            @confirm="onFormCategoryChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !formModel.category_id }">
                {{ formCategoryLabel || '请选择分类' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">同义词（选填）</text>
          <input
            class="form-input"
            v-model="synonymsInput"
            placeholder="多个同义词用逗号分隔"
            placeholder-class="form-placeholder"
          />
        </view>
        <view v-if="formMode === 'edit'" class="form-group form-group--switch">
          <text class="form-label">启用科室</text>
          <switch :checked="formModel.is_active" @change="formModel.is_active = $event.detail.value" color="#0F766E" />
        </view>
      </view>
    </ModalDialog>

    <ModalDialog
      :visible="showMergeModal"
      title="合并科室"
      confirmText="合并"
      :confirmLoading="isMerging"
      @update:visible="showMergeModal = $event"
      @confirm="handleMergeConfirm"
      @cancel="closeMergeModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">源科室</text>
          <view class="form-static">{{ mergeSourceName }}</view>
        </view>
        <view class="form-group">
          <text class="form-label">合并到</text>
          <wd-picker
            v-model="mergeTargetIdx"
            :columns="mergeTargetCols"
            title="选择目标科室"
            :z-index="3000"
            @confirm="onMergeTargetChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !mergeTargetId }">
                {{ mergeTargetName || '请选择目标科室' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-note">合并后，源科室下的专家将迁移到目标科室，源科室将被删除。</text>
        </view>
      </view>
    </ModalDialog>

    <ModalDialog
      :visible="isCatFormVisible"
      :title="catFormMode === 'create' ? '新增根分类' : '编辑根分类'"
      :confirmText="catFormMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isCatSubmitting"
      @update:visible="isCatFormVisible = $event"
      @confirm="handleCatFormConfirm"
      @cancel="closeCatForm"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">分类名称（标准名）</text>
          <input class="form-input" v-model="catFormModel.name" placeholder="如：心血管内科" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">口语名（C端展示，可选）</text>
          <input class="form-input" v-model="catFormModel.display_name" placeholder="如：心内科" placeholder-class="form-placeholder" />
        </view>
        <view v-if="catFormMode === 'edit'" class="form-group form-group--switch">
          <text class="form-label">启用分类</text>
          <switch :checked="catFormModel.is_active" @change="catFormModel.is_active = $event.detail.value" color="#0F766E" />
        </view>
      </view>
    </ModalDialog>

    <!-- 分类删除确认弹窗（409 引用清单 + force 确认级联） -->
    <ModalDialog
      :visible="catDeleteVisible"
      title="删除分类（确认级联）"
      confirmText="确认级联停用"
      :confirmLoading="catDeleteSubmitting"
      confirmColor="#dc2626"
      @update:visible="catDeleteVisible = $event"
      @confirm="handleCatDeleteForce"
      @cancel="closeCatDeleteModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-note">该分类存在引用，默认禁止停用。确认后将级联停用整棵子树并安顿引用：</text>
        </view>
        <view class="form-group">
          <view class="ref-row">
            <text class="ref-label">专家引用</text>
            <text class="ref-value">{{ catDeleteRefs?.expert_all ?? 0 }} 位（启用 {{ catDeleteRefs?.expert_active ?? 0 }}）</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">科室引用</text>
            <text class="ref-value">{{ catDeleteRefs?.department_count ?? 0 }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">直播间关联</text>
            <text class="ref-value">{{ catDeleteRefs?.room_count ?? 0 }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">启用子分类</text>
            <text class="ref-value">{{ catDeleteRefs?.active_child_count ?? 0 }} 个（将级联停用）</text>
          </view>
        </view>
        <view v-if="catDeleteWarnings.length > 0" class="form-group">
          <text v-for="(w, i) in catDeleteWarnings" :key="i" class="form-note form-note--warn">· {{ w }}</text>
        </view>
        <view class="form-group">
          <text class="form-label">引用迁移目标（可选，缺省"其他"）</text>
          <wd-picker
            v-model="catDeleteTargetIdx"
            :columns="catDeleteTargetCols"
            title="选择迁移目标分类"
            :z-index="3000"
            @confirm="onCatDeleteTargetChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !catDeleteTargetId }">
                {{ catDeleteTargetName || '使用兜底分类"其他"' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
      </view>
    </ModalDialog>

    <!-- 分类迁移弹窗 -->
    <ModalDialog
      :visible="catMigrateVisible"
      title="迁移分类引用"
      confirmText="迁移"
      :confirmLoading="catMigrateSubmitting"
      @update:visible="catMigrateVisible = $event"
      @confirm="handleCatMigrateConfirm"
      @cancel="closeCatMigrateModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">源分类</text>
          <view class="form-static">{{ catMigrateSourceName }}</view>
        </view>
        <view class="form-group">
          <text class="form-label">迁移到</text>
          <wd-picker
            v-model="catMigrateTargetIdx"
            :columns="catMigrateTargetCols"
            title="选择目标分类"
            :z-index="3000"
            @confirm="onCatMigrateTargetChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !catMigrateTargetId }">{{ catMigrateTargetName || '请选择目标分类' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">迁移范围</text>
          <wd-picker
            v-model="catMigrateScopeIndex"
            :columns="catMigrateScopeCols"
            title="选择迁移范围"
            :z-index="3000"
          >
            <view class="form-picker">{{ catMigrateScopeLabel }}<text class="picker-arrow">▼</text></view>
          </wd-picker>
        </view>
        <view v-if="catMigrateStats" class="form-group">
          <view class="ref-row">
            <text class="ref-label">已迁移专家</text>
            <text class="ref-value">{{ catMigrateStats.expert_count }} 位</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">已迁移科室</text>
            <text class="ref-value">{{ catMigrateStats.department_count }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">已迁移房间关联</text>
            <text class="ref-value">{{ catMigrateStats.room_count }} 个</text>
          </view>
        </view>
      </view>
    </ModalDialog>

    <!-- 分类合并弹窗（dry_run 两段式） -->
    <ModalDialog
      :visible="catMergeVisible"
      :title="catMergeStats && !catMergeStats.dry_run ? '合并分类' : '合并分类（预览）'"
      :confirmText="catMergeStats && !catMergeStats.dry_run ? '确认合并' : '预览统计'"
      :confirmLoading="catMergeSubmitting"
      @update:visible="catMergeVisible = $event"
      @confirm="handleCatMergeConfirm"
      @cancel="closeCatMergeModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">源分类</text>
          <view class="form-static">{{ catMergeSourceName }}</view>
        </view>
        <view class="form-group">
          <text class="form-label">合并到</text>
          <wd-picker
            v-model="catMergeTargetIdx"
            :columns="catMergeTargetCols"
            title="选择目标分类"
            :z-index="3000"
            @confirm="onCatMergeTargetChange"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !catMergeTargetId }">{{ catMergeTargetName || '请选择目标分类' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view class="form-group form-group--switch">
          <text class="form-label">子分类提升为一级</text>
          <switch :checked="catMergeAttachChildren" @change="catMergeAttachChildren = $event.detail.value" color="#0F766E" />
        </view>
        <view v-if="catMergeStats" class="form-group">
          <text class="form-note">{{ catMergeStats.message }}</text>
          <view class="ref-row">
            <text class="ref-label">迁移专家</text>
            <text class="ref-value">{{ catMergeStats.expert_count }} 位</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">迁移科室</text>
            <text class="ref-value">{{ catMergeStats.department_count }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">房间关联</text>
            <text class="ref-value">{{ catMergeStats.room_count }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">子分类</text>
            <text class="ref-value">{{ catMergeStats.child_count }} 个</text>
          </view>
          <view v-if="catMergeStats.inconsistent_expert_count > 0" class="ref-row">
            <text class="ref-label">不一致专家（将校正）</text>
            <text class="ref-value">{{ catMergeStats.inconsistent_expert_count }} 位</text>
          </view>
        </view>
        <view v-else class="form-group">
          <text class="form-note">点击"预览统计"查看合并影响，确认无误后再点击"确认合并"执行。</text>
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { getDepartments, createDepartment, updateDepartment, deleteDepartment, batchVerifyDepartments, mergeDepartments } from '@/api/department';
import { getCategories, createCategory, updateCategory, deleteCategory, migrateCategoryReferences, mergeCategories } from '@/api/category';
import type { CategoryReferences, CategoryMigrateStats, CategoryMergeResult } from '@/api/category';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import { useAdminGuard } from '@/composables/useAdminGuard';
import type { ExpertDepartment } from '@/types/department';
import type { Category } from '@/types/category';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import ClearButton from '@/components/app/ClearButton.vue';
import WdPicker from 'wot-design-uni/components/wd-picker/wd-picker.vue';

const tabs = [
  { key: 'all', label: '全部分类' },
  { key: 'pending', label: '待审核科室' },
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

const departments = ref<ExpertDepartment[]>([]);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const error = ref<string | null>(null);
const page = ref(1);
const size = 200;
const total = ref(0);
const hasMore = computed(() => page.value * size < total.value);
const loadedOnce = ref(false);
/** 请求进行中到达的刷新请求标记（本轮结束后自动补跑，替代静默丢弃） */
let pendingRefresh = false;

const searchKeyword = ref('');
const categories = ref<Category[]>([]);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const expandState = ref<Record<string, boolean>>({});
const groupedDepartments = computed(() => {
  const map = new Map<string, { categoryId: string; categoryName: string; items: ExpertDepartment[] }>();
  for (const cat of categories.value) {
    map.set(cat.id, { categoryId: cat.id, categoryName: cat.display_name || cat.name, items: [] });
  }
  for (const dept of departments.value) {
    const cid = dept.category_id;
    if (map.has(cid)) {
      map.get(cid)!.items.push(dept);
    } else {
      const key = cid || '__none__';
      if (!map.has(key)) {
        map.set(key, { categoryId: cid, categoryName: dept.category_name || '未分类', items: [] });
      }
      map.get(key)!.items.push(dept);
    }
  }
  return [...map.values()].filter(g => g.items.length > 0);
});

const isFormVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const editingDeptId = ref<string | null>(null);
const isSubmitting = ref(false);
const formModel = ref({ name: '', category_id: null as string | null, is_active: true });
const synonymsInput = ref('');

const isCatFormVisible = ref(false);
const catFormMode = ref<'create' | 'edit'>('create');
const catFormModel = ref({ id: '', name: '', display_name: '', is_active: true });
const isCatSubmitting = ref(false);

// —— P2 短枚举迁移：wd-picker 列（value=index，与原生 picker index 语义一致）+ 受控 index ——
const formCatCols = computed(() => formCategoryNames.value.map((label, i) => ({ value: i, label })));
const mergeTargetCols = computed(() => mergeTargetNames.value.map((label, i) => ({ value: i, label })));
const catDeleteTargetCols = computed(() => catDeleteTargetNames.value.map((label, i) => ({ value: i, label })));
const catMigrateTargetCols = computed(() => catMigrateTargetNames.value.map((label, i) => ({ value: i, label })));
const catMigrateScopeCols = computed(() => catMigrateScopeLabels.map((label, i) => ({ value: i, label })));
const catMergeTargetCols = computed(() => catMergeTargetNames.value.map((label, i) => ({ value: i, label })));

const formCatIdx = ref(0);
const mergeTargetIdx = ref(0);
const catDeleteTargetIdx = ref(0);
const catMigrateTargetIdx = ref(0);
const catMergeTargetIdx = ref(0);

const formCategoryNames = computed(() => categories.value.map(c => c.display_name || c.name));
const formCategoryLabel = computed(() => {
  if (!formModel.value.category_id) return '';
  const cat = categories.value.find(c => c.id === formModel.value.category_id);
  return cat ? (cat.display_name || cat.name) : '';
});

const isSelectMode = ref(false);
const selectedIds = ref(new Set<string>());
const showMergeModal = ref(false);
const mergeSourceId = ref<string | null>(null);
const mergeSourceName = ref('');
const mergeTargetId = ref<string | null>(null);
const isMerging = ref(false);

const allSelected = computed(() =>
  departments.value.length > 0 && departments.value.every(d => selectedIds.value.has(d.id))
);

const mergeTargetNames = computed(() =>
  departments.value.filter(d => d.id !== mergeSourceId.value).map(d => d.name)
);

const mergeTargetName = computed(() => {
  if (!mergeTargetId.value) return '';
  const dept = departments.value.find(d => d.id === mergeTargetId.value);
  return dept ? dept.name : '';
});

const emptyTitle = computed(() =>
  activeTab.value === 'pending' ? '没有待审核科室' : '暂无科室'
);
const emptyDesc = computed(() =>
  activeTab.value === 'pending' ? '所有科室已审核通过' : '点击右上角新增科室'
);

async function loadDepartments(refresh = false) {
  // 请求进行中到达的刷新请求：标记补跑，本轮结束后自动执行（不再静默丢弃）
  if (isLoading.value || isLoadingMore.value) {
    if (refresh) pendingRefresh = true;
    return;
  }
  if (refresh) {
    isLoading.value = true;
  } else {
    isLoadingMore.value = true;
  }
  error.value = null;

  if (refresh) {
    page.value = 1;
    // 下拉/补跑刷新不清空旧列表（stale-while-revalidate）：
    // 避免内容高度骤降导致原生 refresher 动画错乱（下拉卡死）；骨架仅首载（列表为空）时显示
  }

  const requestPage = refresh ? 1 : page.value + 1;

  try {
    const params: Record<string, any> = {
      page: requestPage,
      size,
      is_active: true,
    };
    if (activeTab.value === 'pending') {
      params.is_verified = false;
    }
    if (searchKeyword.value) {
      params.q = searchKeyword.value;
    }

    const res = await getDepartments(params, { showLoading: false, retry: 1, timeout: 8000 });
    if (res.code === 200) {
      const deptItems = res.data.items || [];
      if (refresh) {
        departments.value = deptItems;
        total.value = res.data.total;
      } else {
        const existingIds = new Set(departments.value.map(d => d.id));
        const newItems = deptItems.filter((d: any) => !existingIds.has(d.id));
        departments.value = [...departments.value, ...newItems];
        if (newItems.length < deptItems.length) {
          total.value = departments.value.length;
        } else {
          total.value = res.data.total ?? total.value;
        }
      }
      page.value = requestPage;
    }
  } catch (e: any) {
    error.value = e?.message || '加载失败，下拉重试';
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
    loadedOnce.value = true;
    // 加载期间到达的刷新请求：补跑一次（合并连续触发）
    if (pendingRefresh) {
      pendingRefresh = false;
      await loadDepartments(true);
    }
  }
}

async function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value) return;
  await loadDepartments(false);
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
    await loadDepartments(true);
  } finally {
    const elapsed = Date.now() - pullRefreshStartTime;
    if (elapsed < PULL_REFRESH_MIN_MS) {
      await new Promise(resolve => setTimeout(resolve, PULL_REFRESH_MIN_MS - elapsed));
    }
    isPullRefreshing.value = false;
  }
}

watch(searchKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadDepartments(true);
  }, 300);
});

async function loadCategories() {
  try {
    const res = await getCategories({ showLoading: false });
    if (res.code === 200) {
      categories.value = res.data || [];
    }
  } catch {
    /* silent */
  }
}

function openCreateForm(categoryId?: string | null) {
  formMode.value = 'create';
  editingDeptId.value = null;
  formModel.value = { name: '', category_id: categoryId || null, is_active: true };
  synonymsInput.value = '';
  // wd-picker 分类定位同步（无占位列，index=数组下标）
  const ci = categoryId ? categories.value.findIndex(c => c.id === categoryId) : -1;
  formCatIdx.value = ci >= 0 ? ci : 0;
  isFormVisible.value = true;
}

function openEditForm(dept: ExpertDepartment) {
  formMode.value = 'edit';
  editingDeptId.value = dept.id;
  formModel.value = { name: dept.name, category_id: dept.category_id, is_active: dept.is_active };
  synonymsInput.value = dept.synonyms?.join('，') || '';
  const ci = dept.category_id ? categories.value.findIndex(c => c.id === dept.category_id) : -1;
  formCatIdx.value = ci >= 0 ? ci : 0;
  isFormVisible.value = true;
}

function closeForm() {
  isFormVisible.value = false;
  formModel.value = { name: '', category_id: null, is_active: true };
  synonymsInput.value = '';
  formCatIdx.value = 0;
}

function onFormCategoryChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  formModel.value.category_id = categories.value[idx]?.id || null;
}

async function handleFormConfirm() {
  if (!formModel.value.name.trim()) {
    uni.showToast({ title: '请输入科室名称', icon: 'none' });
    return;
  }
  if (!formModel.value.category_id) {
    uni.showToast({ title: '请选择所属分类', icon: 'none' });
    return;
  }

  isSubmitting.value = true;
  try {
    const synonyms = synonymsInput.value
      .split(/[,，]/)
      .map(s => s.trim())
      .filter(Boolean);

    if (formMode.value === 'create') {
      await createDepartment({
        name: formModel.value.name.trim(),
        category_id: formModel.value.category_id,
        synonyms: synonyms.length > 0 ? synonyms : undefined,
      });
      uni.showToast({ title: '创建成功', icon: 'success' });
    } else {
      await updateDepartment(editingDeptId.value!, {
        name: formModel.value.name.trim(),
        category_id: formModel.value.category_id,
        synonyms,
        is_active: formModel.value.is_active,
      });
      uni.showToast({ title: '保存成功', icon: 'success' });
    }
    closeForm();
    loadDepartments(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isSubmitting.value = false;
  }
}

async function handleAudit(dept: ExpertDepartment) {
  try {
    await updateDepartment(dept.id, { is_verified: true });
    uni.showToast({ title: '审核通过', icon: 'success' });
    dept.is_verified = true;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

async function handleDelete(dept: ExpertDepartment) {
  const warn = dept.expert_count > 0
    ? `该科室下有 ${dept.expert_count} 位专家，删除后专家将变为未分类。`
    : '';

  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({
      title: '确认删除',
      content: `确定要删除「${dept.name}」吗？${warn}`,
      confirmColor: '#dc2626',
      success: r => resolve(r),
    });
  });

  if (!confirm) return;

  try {
    await deleteDepartment(dept.id);
    uni.showToast({ title: '已删除', icon: 'success' });
    departments.value = departments.value.filter(d => d.id !== dept.id);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
  }
}

function enterSelectMode() {
  isSelectMode.value = true;
  selectedIds.value = new Set();
}

function exitSelectMode() {
  isSelectMode.value = false;
  selectedIds.value = new Set();
}

function toggleSelect(deptId: string) {
  const next = new Set(selectedIds.value);
  if (next.has(deptId)) {
    next.delete(deptId);
  } else {
    next.add(deptId);
  }
  selectedIds.value = next;
}

function selectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(departments.value.map(d => d.id));
  }
}

async function handleBatchVerify() {
  if (selectedIds.value.size === 0) return;
  const ids = [...selectedIds.value];
  try {
    const res = await batchVerifyDepartments({ department_ids: ids, verified: true });
    uni.showToast({
      title: `已审核 ${res.data?.affected || ids.length} 个科室`,
      icon: 'success',
    });
    exitSelectMode();
    loadDepartments(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '批量审核失败', icon: 'none' });
  }
}

function openMergeModal(dept: ExpertDepartment) {
  mergeSourceId.value = dept.id;
  mergeSourceName.value = dept.name;
  mergeTargetId.value = null;
  mergeTargetIdx.value = 0;
  showMergeModal.value = true;
}

function closeMergeModal() {
  showMergeModal.value = false;
  mergeSourceId.value = null;
  mergeSourceName.value = '';
  mergeTargetId.value = null;
}

function onMergeTargetChange(e: any) {
  const idx = (e?.value ?? e?.detail?.value) as number;
  const targets = departments.value.filter(d => d.id !== mergeSourceId.value);
  mergeTargetId.value = targets[idx]?.id || null;
}

async function handleMergeConfirm() {
  if (!mergeTargetId.value) {
    uni.showToast({ title: '请选择目标科室', icon: 'none' });
    return;
  }
  isMerging.value = true;
  try {
    await mergeDepartments(mergeSourceId.value!, mergeTargetId.value);
    uni.showToast({ title: '合并成功', icon: 'success' });
    closeMergeModal();
    loadDepartments(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '合并失败', icon: 'none' });
  } finally {
    isMerging.value = false;
  }
}

watch(activeTab, () => {
  loadDepartments(true);
});

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) {
    loadCategories();
    loadDepartments(true);
  }
});

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
});

function toggleCat(catId: string) {
  expandState.value = { ...expandState.value, [catId]: !expandState.value[catId] };
}

function openCreateDeptUnder(group: { categoryId: string; categoryName: string }) {
  openCreateForm(group.categoryId === '__none__' ? null : group.categoryId);
}

function openCreateCategory() {
  catFormMode.value = 'create';
  catFormModel.value = { id: '', name: '', display_name: '', is_active: true };
  isCatFormVisible.value = true;
}

function openEditCategory(group: { categoryId: string; categoryName: string }) {
  catFormMode.value = 'edit';
  const cat = categories.value.find(c => c.id === group.categoryId);
  catFormModel.value = { id: group.categoryId, name: cat?.name || '', display_name: cat?.display_name || '', is_active: cat?.is_active ?? true };
  isCatFormVisible.value = true;
}

function closeCatForm() {
  isCatFormVisible.value = false;
}

async function handleCatFormConfirm() {
  if (!catFormModel.value.name.trim()) {
    uni.showToast({ title: '请输入分类名称', icon: 'none' });
    return;
  }
  isCatSubmitting.value = true;
  try {
    const payload: any = { name: catFormModel.value.name.trim(), is_active: true };
    if (catFormModel.value.display_name.trim()) {
      payload.display_name = catFormModel.value.display_name.trim();
    }
    if (catFormMode.value === 'create') {
      await createCategory(payload);
      uni.showToast({ title: '分类已创建', icon: 'success' });
    } else {
      const updatePayload: any = { name: catFormModel.value.name.trim(), is_active: catFormModel.value.is_active };
      if (catFormModel.value.display_name.trim()) {
        updatePayload.display_name = catFormModel.value.display_name.trim();
      }
      await updateCategory(catFormModel.value.id, updatePayload);
      uni.showToast({ title: '分类已更新', icon: 'success' });
    }
    closeCatForm();
    loadCategories();
    loadDepartments(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isCatSubmitting.value = false;
  }
}

// ========== 分类治理（删除/迁移/合并，阶段4） ==========

/** 治理入口：编辑分类 / 迁移引用 / 合并分类 / 删除分类 */
function openCategoryGovern(group: { categoryId: string; categoryName: string }) {
  uni.showActionSheet({
    itemList: ['编辑分类', '迁移引用', '合并分类', '删除分类'],
    success: (res) => {
      if (res.tapIndex === 0) {
        openEditCategory(group);
      } else if (res.tapIndex === 1) {
        openCatMigrateModal(group);
      } else if (res.tapIndex === 2) {
        openCatMergeModal(group);
      } else if (res.tapIndex === 3) {
        handleCatDelete(group);
      }
    },
  });
}

// ----- 删除闭环（409 引用清单 → force 确认级联） -----
const catDeleteVisible = ref(false);
const catDeleteSubmitting = ref(false);
const catDeleteRefs = ref<CategoryReferences | null>(null);
const catDeleteWarnings = ref<string[]>([]);
const catDeleteCategoryId = ref<string | null>(null);
const catDeleteTargetId = ref<string | null>(null);

const catDeleteTargetNames = computed(() => categories.value.map(c => c.display_name || c.name));
const catDeleteTargetName = computed(() => {
  if (!catDeleteTargetId.value) return '';
  const c = categories.value.find(x => x.id === catDeleteTargetId.value);
  return c ? (c.display_name || c.name) : '';
});

function onCatDeleteTargetChange(e: any) {
  catDeleteTargetId.value = categories.value[Number(e?.value ?? e?.detail?.value)]?.id || null;
}

/** 第一步：非 force 删除 → 有引用则 409 弹窗 */
async function handleCatDelete(group: { categoryId: string; categoryName: string }) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({
      title: '删除分类',
      content: `确定要停用分类「${group.categoryName}」吗？`,
      confirmColor: '#dc2626',
      success: r => resolve(r),
    });
  });
  if (!confirm) return;

  try {
    await deleteCategory(group.categoryId);
    uni.showToast({ title: '已停用', icon: 'success' });
    loadCategories();
    loadDepartments(true);
  } catch (e: any) {
    if (e?.statusCode === 409 && e?.data?.references) {
      // 有引用：展示引用清单 + force 确认
      catDeleteCategoryId.value = group.categoryId;
      catDeleteRefs.value = e.data.references;
      catDeleteWarnings.value = Array.isArray(e.data.warnings) ? e.data.warnings : [];
      catDeleteTargetId.value = null;
      catDeleteTargetIdx.value = 0;
      catDeleteVisible.value = true;
    } else {
      // 400（禁删"其他"/目标非法等）与网络错误：request 已 toast 则不重复
      if (!e?.__toasted) {
        uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
      }
    }
  }
}

/** 第二步：force 确认级联（安顿引用 + 级联停用子树） */
async function handleCatDeleteForce() {
  if (!catDeleteCategoryId.value) return;
  catDeleteSubmitting.value = true;
  try {
    await deleteCategory(catDeleteCategoryId.value, {
      force: true,
      ...(catDeleteTargetId.value ? { target_category_id: catDeleteTargetId.value } : {}),
    });
    uni.showToast({ title: '已级联停用', icon: 'success' });
    closeCatDeleteModal();
    loadCategories();
    loadDepartments(true);
  } catch (e: any) {
    if (!e?.__toasted) {
      uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
    }
  } finally {
    catDeleteSubmitting.value = false;
  }
}

function closeCatDeleteModal() {
  catDeleteVisible.value = false;
  catDeleteRefs.value = null;
  catDeleteWarnings.value = [];
  catDeleteCategoryId.value = null;
  catDeleteTargetId.value = null;
}

// ----- 迁移引用 -----
const catMigrateVisible = ref(false);
const catMigrateSubmitting = ref(false);
const catMigrateSourceId = ref<string | null>(null);
const catMigrateSourceName = ref('');
const catMigrateTargetId = ref<string | null>(null);
const catMigrateStats = ref<CategoryMigrateStats | null>(null);
const catMigrateScopeIndex = ref(0);
const catMigrateScopeLabels = ['全部', '仅专家', '仅科室', '仅房间'];
const catMigrateScopeValues = ['all', 'experts', 'departments', 'rooms'] as const;
const catMigrateScopeLabel = computed(() => catMigrateScopeLabels[catMigrateScopeIndex.value] || '全部');

const catMigrateTargetNames = computed(() => categories.value.map(c => c.display_name || c.name));
const catMigrateTargetName = computed(() => {
  if (!catMigrateTargetId.value) return '';
  const c = categories.value.find(x => x.id === catMigrateTargetId.value);
  return c ? (c.display_name || c.name) : '';
});

function onCatMigrateTargetChange(e: any) {
  catMigrateTargetId.value = categories.value[Number(e?.value ?? e?.detail?.value)]?.id || null;
}

function openCatMigrateModal(group: { categoryId: string; categoryName: string }) {
  catMigrateSourceId.value = group.categoryId;
  catMigrateSourceName.value = group.categoryName;
  catMigrateTargetId.value = null;
  catMigrateTargetIdx.value = 0;
  catMigrateStats.value = null;
  catMigrateScopeIndex.value = 0;
  catMigrateVisible.value = true;
}

function closeCatMigrateModal() {
  catMigrateVisible.value = false;
  catMigrateSourceId.value = null;
  catMigrateSourceName.value = '';
  catMigrateTargetId.value = null;
  catMigrateStats.value = null;
}

async function handleCatMigrateConfirm() {
  if (!catMigrateSourceId.value) return;
  if (!catMigrateTargetId.value) {
    uni.showToast({ title: '请选择目标分类', icon: 'none' });
    return;
  }
  catMigrateSubmitting.value = true;
  try {
    const res = await migrateCategoryReferences(catMigrateSourceId.value, {
      target_category_id: catMigrateTargetId.value,
      scope: catMigrateScopeValues[catMigrateScopeIndex.value],
    });
    catMigrateStats.value = res.data?.migrated || null;
    uni.showToast({ title: '迁移成功', icon: 'success' });
    loadDepartments(true);
    setTimeout(() => closeCatMigrateModal(), 800);
  } catch (e: any) {
    if (!e?.__toasted) {
      uni.showToast({ title: e?.message || '迁移失败', icon: 'none' });
    }
  } finally {
    catMigrateSubmitting.value = false;
  }
}

// ----- 合并分类（dry_run 两段式） -----
const catMergeVisible = ref(false);
const catMergeSubmitting = ref(false);
const catMergeSourceId = ref<string | null>(null);
const catMergeSourceName = ref('');
const catMergeTargetId = ref<string | null>(null);
const catMergeAttachChildren = ref(false);
const catMergeStats = ref<CategoryMergeResult | null>(null);

const catMergeTargetNames = computed(() => categories.value.map(c => c.display_name || c.name));
const catMergeTargetName = computed(() => {
  if (!catMergeTargetId.value) return '';
  const c = categories.value.find(x => x.id === catMergeTargetId.value);
  return c ? (c.display_name || c.name) : '';
});

function onCatMergeTargetChange(e: any) {
  catMergeTargetId.value = categories.value[Number(e?.value ?? e?.detail?.value)]?.id || null;
  catMergeStats.value = null;
}

function openCatMergeModal(group: { categoryId: string; categoryName: string }) {
  catMergeSourceId.value = group.categoryId;
  catMergeSourceName.value = group.categoryName;
  catMergeTargetId.value = null;
  catMergeTargetIdx.value = 0;
  catMergeAttachChildren.value = false;
  catMergeStats.value = null;
  catMergeVisible.value = true;
}

function closeCatMergeModal() {
  catMergeVisible.value = false;
  catMergeSourceId.value = null;
  catMergeSourceName.value = '';
  catMergeTargetId.value = null;
  catMergeStats.value = null;
}

/** 两段式：未预览 → dry_run 预览；已预览 → 确认合并 */
async function handleCatMergeConfirm() {
  if (!catMergeSourceId.value) return;
  if (!catMergeTargetId.value) {
    uni.showToast({ title: '请选择目标分类', icon: 'none' });
    return;
  }
  if (catMergeStats.value && !catMergeStats.value.dry_run) return; // 已执行，防重复

  catMergeSubmitting.value = true;
  try {
    const isPreview = !catMergeStats.value; // 无预览数据 → 先预览
    const res = await mergeCategories({
      source_id: catMergeSourceId.value,
      target_id: catMergeTargetId.value,
      attach_children: catMergeAttachChildren.value,
      dry_run: isPreview,
    });
    if (isPreview) {
      catMergeStats.value = res.data;
      uni.showToast({ title: '预览完成，请确认', icon: 'none' });
    } else {
      catMergeStats.value = res.data;
      uni.showToast({ title: '合并成功', icon: 'success' });
      loadCategories();
      loadDepartments(true);
      setTimeout(() => closeCatMergeModal(), 800);
    }
  } catch (e: any) {
    if (!e?.__toasted) {
      uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
    }
  } finally {
    catMergeSubmitting.value = false;
  }
}
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
  gap: 4rpx;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.header-btn {
  padding: 8rpx 20rpx;
  border: 1rpx solid var(--home-border);
  border-radius: var(--home-r-pill);
  transition: all var(--transition-base);
  font-size: 24rpx;
  color: var(--home-text1);
}

.header-btn--cancel {
  color: var(--home-primary);
  border-color: var(--home-primary);
}

.header-add-btn {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx 20rpx;
  background: var(--home-primary);
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #fff;
}

.add-icon {
  font-size: 26rpx;
  font-weight: 300;
}

.tab-item {
  position: relative;
  padding: 20rpx 28rpx;
  flex-shrink: 0;
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
  gap: 16rpx;
  padding: 16rpx var(--home-spacing-page);
  background: var(--home-bg);
}

.filter-search {
  /* 叠加共享容器 .app-search-field：白底+1rpx细边+胶囊；高度 64rpx（管理端档，D6） */
  flex: 1;
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

.filter-picker {
  flex-shrink: 0;
}

.filter-picker-trigger {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 64rpx;
  padding: 0 20rpx;
  background: var(--home-card);
  border-radius: 10rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}

.filter-picker-text {
  font-size: 26rpx;
  color: var(--home-text1);
  max-width: 160rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow {
  font-size: 20rpx;
  color: var(--home-text2);
}

.tab-content {
  padding: 0 var(--home-spacing-page);
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

/* 内容区 Tab 面板：flex 撑满剩余高度（根容器 100vh + flex column） */
.admin-panel { flex: 1; min-height: 0; overflow: hidden; }

.list-scroll { height: 100%; overflow-y: auto; -webkit-overflow-scrolling: touch; }

.list-inner {
  padding: 0 var(--home-spacing-page);
}

.dept-card {
  display: flex;
  align-items: flex-start;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: 12rpx;
  border: 1rpx solid var(--home-divider);
}

.cat-row {
  display: flex;
  align-items: center;
  padding: 20rpx 16rpx;
  margin-bottom: 8rpx;
  background: var(--home-card);
  border-radius: 10rpx;
  border: 1rpx solid var(--home-divider);
}

.cat-arrow {
  font-size: 22rpx;
  color: var(--home-text2);
  margin-right: 10rpx;
  width: 28rpx;
}

.cat-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.cat-count {
  margin-left: 12rpx;
  font-size: 22rpx;
  color: var(--home-text2);
}

.cat-edit {
  margin-left: auto;
  padding: 4rpx 16rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.12);
  border-radius: 6rpx;
  font-size: 22rpx;
  color: var(--home-text2);
}

.add-dept-btn {
  text-align: center;
  padding: 16rpx;
  margin-bottom: 16rpx;
  border: 2rpx dashed var(--home-divider);
  border-radius: 10rpx;
  font-size: 26rpx;
  color: var(--home-primary);
}

.dept-main {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 10rpx;
}

.dept-name {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.dept-badge {
  padding: 2rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  line-height: 1.5;
  flex-shrink: 0;
}

.badge--verified {
  background: var(--home-badge-verified-bg);
  color: var(--home-badge-verified-text);
}

.badge--pending {
  background: var(--home-badge-pending-bg);
  color: var(--home-badge-pending-text);
}

.dept-meta {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.dept-category {
  font-size: 24rpx;
  color: var(--home-text2);
}

.dept-cat-tag {
  margin-left: auto;
  padding: 2rpx 14rpx;
  background: rgba(15, 118, 110, 0.06);
  border-radius: 6rpx;
  font-size: 22rpx;
  color: var(--home-primary);
  white-space: nowrap;
  flex-shrink: 0;
}

.dept-count {
  font-size: 24rpx;
  color: var(--home-text2);
}

.dept-synonyms {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 10rpx;
}

.synonym-tag {
  padding: 2rpx 12rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 6rpx;
  font-size: 20rpx;
  color: var(--home-text2);
}

.dept-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 14rpx;
  padding-top: 14rpx;
  border-top: 1rpx solid var(--home-divider);
}

.action-btn {
  padding: 8rpx 24rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
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
  margin-bottom: 28rpx;
}

.form-label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-text1);
  margin-bottom: 12rpx;
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

.skeleton-card {
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: 12rpx;
}

.skeleton-line {
  height: 20rpx;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 4rpx;
  margin-bottom: 12rpx;
}

.skeleton-line--long {
  width: 60%;
}

.skeleton-line--short {
  width: 40%;
  margin-bottom: 0;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: var(--home-text2);
}

.dept-check {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  margin-top: 6rpx;
  flex-shrink: 0;
}

.dept-check--on {
  background: var(--home-primary);
  border-color: var(--home-primary);
}

.dept-check--disabled {
  opacity: 0.35;
  pointer-events: none;
}

.check-icon {
  font-size: 24rpx;
  color: #fff;
  font-weight: 700;
}

.dept-body {
  flex: 1;
  min-width: 0;
}

.select-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx var(--home-spacing-page);
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: var(--home-card);
  border-top: 1rpx solid rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.select-bar-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.select-all-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 26rpx;
  color: var(--home-text1);
}

.select-bar-check {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.select-bar-check--on {
  background: var(--home-primary);
  border-color: var(--home-primary);
}

.select-count {
  font-size: 24rpx;
  color: var(--home-text2);
}

.batch-btn {
  padding: 14rpx 32rpx;
  background: var(--home-primary);
  border-radius: 10rpx;
  font-size: 26rpx;
  color: #fff;
}

.batch-btn--disabled {
  opacity: 0.4;
}

.form-static {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
  color: var(--home-text2);
}

.form-note {
  font-size: 22rpx;
  color: var(--home-text2);
  line-height: 1.6;
}
.form-note--warn {
  color: #b45309;
  display: block;
  margin-bottom: 4rpx;
}

/* 分类治理：引用统计行 */
.ref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.04);
}
.ref-row:last-child {
  border-bottom: none;
}
.ref-label {
  font-size: 26rpx;
  color: #666;
}
.ref-value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

/* 分类治理入口（与"编辑分类"区分） */
.cat-edit--govern {
  margin-left: 12rpx;
  color: #0F766E;
}
</style>
