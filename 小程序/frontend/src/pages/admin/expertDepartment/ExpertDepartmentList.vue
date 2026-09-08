<!--
 * ExpertDepartmentList - 专家分类管理（《20》前端 V2.0 + V2.1 + V2.2）
 * 一句话闭环：按 Tab/树看清词表 → 组内审改/合并 → 根分类编辑与治理 → 离开
 * 非目标：未分配专家、H5、平行 pages/app、前端子孙展开；词条硬删
 -->
<template>
  <view class="page">
    <view class="page-header">
      <view class="top-bar">
        <view class="tab-bar">
          <view
            v-for="(t, idx) in mainTabs"
            :key="t.key"
            class="tab-item"
            :class="{ 'tab-item--active': activeTabIndex === idx }"
            @tap="onTabTap(idx)"
          >
            <text class="tab-label">{{ t.label }}</text>
            <view v-if="activeTabIndex === idx" class="tab-indicator" />
          </view>
        </view>
        <view class="header-actions">
          <view v-if="!isSelectMode" class="header-btn" @tap="toggleSelectMode">
            <text>选择</text>
          </view>
          <view v-else class="header-btn" @tap="toggleSelectMode">
            <text>取消</text>
          </view>
          <view v-if="!isSelectMode" class="header-add-btn" @tap="openCreateCategory">
            <text class="add-icon">＋</text>
            <text>新增分类</text>
          </view>
        </view>
      </view>

      <view class="toolbar-search">
        <view class="search-box">
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索科室名称"
            maxlength="100"
            confirm-type="search"
            @confirm="handleSearch"
            @input="onKeywordInput"
          />
          <text v-if="keyword" class="search-clear" @tap="clearKeyword">✕</text>
        </view>
      </view>

      <view v-if="!isSelectMode" class="toolbar-secondary">
        <picker :range="activeOptions" range-key="label" :value="activePickerIndex" @change="onActiveFilterChange">
          <view class="filter-picker">
            <text class="filter-picker__label">{{ activeOptions[activePickerIndex].label }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <picker
          :range="categoryVisibilityOptions"
          range-key="label"
          :value="categoryVisibilityIndex"
          @change="onCategoryVisibilityChange"
        >
          <view class="filter-picker">
            <text class="filter-picker__label">{{
              categoryVisibilityOptions[categoryVisibilityIndex].label
            }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <view v-if="filtersDirty" class="btn-reset" @tap="handleResetFilters">
          <text class="btn-reset-text">重置</text>
        </view>
      </view>
    </view>

    <view v-if="!accessGranted" class="state-box">
      <text class="state-text">{{ accessMessage }}</text>
    </view>
    <view v-else-if="loading && !items.length && !categoryRecords.length" class="state-box">
      <view class="loading-spinner" />
      <text class="state-text">加载中...</text>
    </view>
    <view v-else-if="errorMsg && !items.length && !categoryRecords.length" class="state-box">
      <text class="state-text">{{ errorMsg }}</text>
      <view class="btn-query" @tap="fetchData(true)"><text class="btn-text">重试</text></view>
    </view>

    <view v-else class="list">
      <!-- 平铺：有搜索 -->
      <template v-if="isFlatMode">
        <view v-if="items.length === 0" class="state-box">
          <text class="state-text">无匹配科室</text>
        </view>
        <view
          v-for="item in items"
          :key="item.id"
          :class="['dept-card', { 'dept-card--inactive': !item.is_active }]"
        >
          <view
            v-if="isSelectMode"
            class="item-check"
            :class="{ disabled: item.is_verified }"
            @tap="toggleSelect(item)"
          >
            <text class="check-mark">{{ selectedIds.includes(item.id) ? '✓' : '' }}</text>
          </view>
          <view class="dept-card__body">
            <view class="dept-card__head">
              <text class="dept-card__name">{{ item.name }}</text>
              <text v-if="!item.is_verified" class="tag tag--pending">待审核</text>
              <text v-else class="tag tag--ok">已审核</text>
              <text v-if="!item.is_active" class="tag tag--off">已停用</text>
              <text v-if="item.category_name" class="tag tag--cat">{{ item.category_name }}</text>
            </view>
            <text class="dept-card__meta">{{ item.expert_count ?? 0 }} 位专家</text>
            <view v-if="!isSelectMode" class="dept-card__actions">
              <view
                v-if="!item.is_verified"
                class="action-chip action-chip--ok"
                @tap="handleVerifyOne(item)"
              >
                <text>通过</text>
              </view>
              <view class="action-chip" @tap="openEdit(item)"><text>编辑</text></view>
              <view
                v-if="item.is_active"
                class="action-chip"
                @tap="handleDeactivate(item)"
              >
                <text>停用</text>
              </view>
              <view v-else class="action-chip action-chip--ok" @tap="handleRestore(item)">
                <text>启用</text>
              </view>
              <view class="action-chip action-chip--del" @tap="handleHardDelete(item)">
                <text>删除</text>
              </view>
              <view class="action-chip" @tap="openMerge(item)"><text>合并</text></view>
            </view>
          </view>
        </view>
      </template>

      <!-- 树：无搜索，按分类分组；默认收起，点击展开后可见科室与「新增科室」 -->
      <template v-else>
        <view v-if="groupedDepartments.length === 0" class="state-box">
          <text class="state-text">{{ emptyTreeHint }}</text>
        </view>
        <view
          v-for="group in groupedDepartments"
          :key="group.categoryId"
          class="group"
          :class="{ 'group--inactive': !group.isActive }"
        >
          <view class="cat-row" @tap="toggleCat(group.categoryId)">
            <text class="cat-arrow">{{ isCatExpanded(group.categoryId) ? '▼' : '▶' }}</text>
            <text class="cat-name">{{ group.categoryName }}</text>
            <text v-if="!group.isActive" class="tag tag--off">已停用</text>
            <text class="cat-count">{{ group.items.length }} 个科室</text>
            <view
              v-if="group.categoryId !== '__none__' && !isSelectMode"
              class="cat-actions"
              @tap.stop
            >
              <view class="cat-btn" @tap="openEditCategory(group)">
                <text>编辑分类</text>
              </view>
              <view class="cat-btn" @tap="openCategoryGovern(group)">
                <text>治理</text>
              </view>
            </view>
          </view>
          <view v-if="isCatExpanded(group.categoryId)" class="group-children">
            <view
              v-for="item in group.items"
              :key="item.id"
              :class="['dept-card', { 'dept-card--inactive': !item.is_active }]"
            >
              <view
                v-if="isSelectMode"
                class="item-check"
                :class="{ disabled: item.is_verified }"
                @tap="toggleSelect(item)"
              >
                <text class="check-mark">{{ selectedIds.includes(item.id) ? '✓' : '' }}</text>
              </view>
              <view class="dept-card__body">
                <view class="dept-card__head">
                  <text class="dept-card__name">{{ item.name }}</text>
                  <text v-if="item.is_verified" class="tag tag--ok">已审核</text>
                  <text v-else class="tag tag--pending">待审核</text>
                  <text v-if="!item.is_active" class="tag tag--off">已停用</text>
                </view>
                <text class="dept-card__meta">{{ item.expert_count ?? 0 }} 位专家</text>
                <view v-if="!isSelectMode" class="dept-card__actions">
                  <view
                    v-if="!item.is_verified"
                    class="action-chip action-chip--ok"
                    @tap="handleVerifyOne(item)"
                  >
                    <text>通过</text>
                  </view>
                  <view class="action-chip" @tap="openEdit(item)"><text>编辑</text></view>
                  <view
                    v-if="item.is_active"
                    class="action-chip"
                    @tap="handleDeactivate(item)"
                  >
                    <text>停用</text>
                  </view>
                  <view v-else class="action-chip action-chip--ok" @tap="handleRestore(item)">
                    <text>启用</text>
                  </view>
                  <view class="action-chip action-chip--del" @tap="handleHardDelete(item)">
                    <text>删除</text>
                  </view>
                  <view class="action-chip" @tap="openMerge(item)"><text>合并</text></view>
                </view>
              </view>
            </view>
            <view
              v-if="!isSelectMode && group.categoryId !== '__none__' && group.isActive"
              class="add-under"
              @tap="openCreate(group.categoryId)"
            >
              <text>＋ 新增科室</text>
            </view>
            <view
              v-else-if="!isSelectMode && group.categoryId !== '__none__' && !group.isActive"
              class="add-under add-under--disabled"
              @tap="toastInactiveCategory"
            >
              <text>分类已停用，无法新增科室</text>
            </view>
          </view>
        </view>
      </template>

      <view v-if="loadingMore" class="state-box state-box--sm">
        <text class="state-text">加载更多...</text>
      </view>
      <view v-else-if="hasMore" class="load-more" @tap="loadMore">
        <text>加载更多</text>
      </view>
    </view>

    <view v-if="isSelectMode" class="select-bar">
      <view class="select-left" @tap="selectAllPending">
        <text>全选</text>
        <text class="select-count">已选 {{ selectedIds.length }}</text>
      </view>
      <view
        :class="['btn-batch', selectedIds.length ? '' : 'disabled']"
        @tap="handleBatchVerify"
      >
        <text class="btn-text">批量通过</text>
      </view>
    </view>

    <ExpertDepartmentFormDialog
      v-model:visible="formVisible"
      :mode="formMode"
      :initial-data="currentItem"
      :default-category-id="defaultCategoryId"
      :default-category-name="defaultCategoryName"
      @success="onFormSuccess"
    />

    <ExpertDepartmentMergeDialog
      v-model:visible="mergeVisible"
      :source="mergeSource"
      @success="fetchData(true)"
    />

    <!-- 改词表分类（仅启用分类） -->
    <view v-if="categoryDialogVisible" class="dialog-overlay" @tap="categoryDialogVisible = false">
      <view class="dialog" @tap.stop>
        <text class="dialog-title">改分类</text>
        <text class="dialog-sub">将同步该词条下专家的主分类</text>
        <picker
          v-if="activeCategoryOptions.length"
          :range="activeCategoryOptions"
          range-key="name"
          :value="changeCategoryPickerIndex"
          @change="onChangeCategoryPick"
        >
          <view class="picker-trigger">
            <text class="picker-value">{{ changeCategoryName || '请选择分类' }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <text v-else class="dialog-sub">暂无启用中的分类</text>
        <view class="dialog-footer">
          <view class="btn-cancel" @tap="categoryDialogVisible = false"><text>取消</text></view>
          <view class="btn-confirm" @tap="submitChangeCategory"><text>确认</text></view>
        </view>
      </view>
    </view>

    <CategoryFormDialog
      v-model:visible="catDialogVisible"
      :mode="catDialogMode"
      :initial-data="catEditing"
      @success="onCategoryFormSuccess"
    />

    <!-- 迁移分类引用 -->
    <view v-if="catMigrateVisible" class="dialog-overlay" @tap="closeCatMigrate">
      <view class="dialog dialog--wide" @tap.stop>
        <view class="dialog-head">
          <text class="dialog-title">迁移分类引用</text>
          <text class="dialog-close" @tap="closeCatMigrate">✕</text>
        </view>
        <view class="form-group">
          <text class="form-label">源分类</text>
          <view class="form-static">{{ catMigrateSourceName }}</view>
        </view>
        <view class="form-group">
          <text class="form-label">迁移到</text>
          <picker
            :range="catMigrateTargetNames"
            :value="catMigrateTargetIndex"
            @change="onCatMigrateTargetChange"
          >
            <view class="picker-trigger">
              <text :class="['picker-value', { 'picker-value--ph': !catMigrateTargetId }]">
                {{ catMigrateTargetName || '请选择目标分类' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        <view class="form-group">
          <text class="form-label">迁移范围</text>
          <picker
            :range="catMigrateScopeLabels"
            :value="catMigrateScopeIndex"
            @change="onCatMigrateScopeChange"
          >
            <view class="picker-trigger">
              <text class="picker-value">{{ catMigrateScopeLabels[catMigrateScopeIndex] }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        <view v-if="catMigrateStats" class="ref-block">
          <view class="ref-row">
            <text class="ref-label">已迁移专家</text>
            <text class="ref-value">{{ catMigrateStats.expert_count }} 位</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">已迁移科室</text>
            <text class="ref-value">{{ catMigrateStats.department_count }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">已迁移房间</text>
            <text class="ref-value">{{ catMigrateStats.room_count }} 个</text>
          </view>
        </view>
        <view class="dialog-footer">
          <view class="btn-cancel" @tap="closeCatMigrate"><text>取消</text></view>
          <view class="btn-confirm" @tap="submitCatMigrate"><text>迁移</text></view>
        </view>
      </view>
    </view>

    <!-- 合并分类（预览 → 确认） -->
    <view v-if="catMergeVisible" class="dialog-overlay" @tap="closeCatMerge">
      <view class="dialog dialog--wide" @tap.stop>
        <view class="dialog-head">
          <text class="dialog-title">{{
            catMergeStats && !catMergeStats.dry_run ? '合并分类' : '合并分类（预览）'
          }}</text>
          <text class="dialog-close" @tap="closeCatMerge">✕</text>
        </view>
        <view class="form-group">
          <text class="form-label">源分类</text>
          <view class="form-static">{{ catMergeSourceName }}</view>
        </view>
        <view class="form-group">
          <text class="form-label">合并到</text>
          <picker
            :range="catMergeTargetNames"
            :value="catMergeTargetIndex"
            @change="onCatMergeTargetChange"
          >
            <view class="picker-trigger">
              <text :class="['picker-value', { 'picker-value--ph': !catMergeTargetId }]">
                {{ catMergeTargetName || '请选择目标分类' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        <view class="form-group form-group--row">
          <text class="form-label">子分类提升为一级</text>
          <switch :checked="catMergeAttachChildren" color="#0F766E" @change="onCatMergeAttachChange" />
        </view>
        <view v-if="catMergeStats" class="ref-block">
          <text class="form-note form-note--preview">{{ catMergePreviewMessage }}</text>
          <view class="ref-row">
            <text class="ref-label">迁移专家</text>
            <text class="ref-value">{{ catMergeStats.expert_count ?? 0 }} 位</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">迁移科室</text>
            <text class="ref-value">{{ catMergeStats.department_count ?? 0 }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">房间关联</text>
            <text class="ref-value">{{ catMergeStats.room_count ?? 0 }} 个</text>
          </view>
          <view class="ref-row">
            <text class="ref-label">子分类</text>
            <text class="ref-value">{{ catMergeStats.child_count ?? 0 }} 个</text>
          </view>
        </view>
        <text v-else class="form-note form-note--hint">
          点击「预览统计」查看合并影响，确认无误后再点击「确认合并」执行。
        </text>
        <view class="dialog-footer">
          <view class="btn-cancel" @tap="closeCatMerge"><text>取消</text></view>
          <view class="btn-confirm" @tap="submitCatMerge">
            <text>{{ catMergeReadyToConfirm ? '确认合并' : '预览统计' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 删除分类：409 引用 → 级联确认 -->
    <view v-if="catDeleteVisible" class="dialog-overlay" @tap="closeCatDelete">
      <view class="dialog dialog--wide" @tap.stop>
        <view class="dialog-head">
          <text class="dialog-title">删除分类（确认级联）</text>
          <text class="dialog-close" @tap="closeCatDelete">✕</text>
        </view>
        <text class="form-note">
          「{{ catDeleteSourceName }}」存在引用，确认后将安顿引用并级联停用（可恢复语义以后端为准）。
        </text>
        <view class="ref-block">
          <view class="ref-row">
            <text class="ref-label">专家引用</text>
            <text class="ref-value">
              {{ catDeleteRefs?.expert_all ?? 0 }} 位（启用 {{ catDeleteRefs?.expert_active ?? 0 }}）
            </text>
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
            <text class="ref-value">{{ catDeleteRefs?.active_child_count ?? 0 }} 个</text>
          </view>
        </view>
        <view class="form-group">
          <text class="form-label">引用迁移目标（可选）</text>
          <picker
            :range="catDeleteTargetNames"
            :value="catDeleteTargetIndex"
            @change="onCatDeleteTargetChange"
          >
            <view class="picker-trigger">
              <text :class="['picker-value', { 'picker-value--ph': !catDeleteTargetId }]">
                {{ catDeleteTargetName || '使用兜底分类「其他」' }}
              </text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        <view class="dialog-footer">
          <view class="btn-cancel" @tap="closeCatDelete"><text>取消</text></view>
          <view class="btn-confirm btn-confirm--danger" @tap="submitCatDeleteForce">
            <text>确认级联停用</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import {
  deleteCategory,
  getAdminCategories,
  getAdminCategoryDetail,
  mergeCategories,
  migrateCategoryReferences,
  updateCategory
} from '@/api/categories'
import {
  batchVerifyExpertDepartments,
  deleteExpertDepartment,
  listExpertDepartments,
  updateExpertDepartment,
  updateExpertDepartmentCategory
} from '@/api/expertDepartments'
import type {
  Category,
  CategoryMigrateScope,
  CategoryMigrateStats,
  CategoryMergeResult,
  CategoryReferences
} from '@/types/category'
import type { ExpertDepartmentItem } from '@/types/expertDepartment'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'
import CategoryFormDialog from '@/components/admin/CategoryFormDialog.vue'
import ExpertDepartmentFormDialog from './ExpertDepartmentFormDialog.vue'
import ExpertDepartmentMergeDialog from './ExpertDepartmentMergeDialog.vue'

const authStore = useAuthStore()
const accessGranted = ref(false)
const accessMessage = ref('正在校验权限...')
const loading = ref(false)
const loadingMore = ref(false)
const errorMsg = ref('')
const keyword = ref('')
const items = ref<ExpertDepartmentItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const selectedIds = ref<string[]>([])
const isSelectMode = ref(false)
/** 未写入时默认收起，仅 expandState[id]===true 时展开 */
const expandState = ref<Record<string, boolean>>({})

const mainTabs = [
  { key: 'all', label: '全部分类' },
  { key: 'pending', label: '待审核科室' }
] as const
const activeTabIndex = ref(0)
const isPendingTab = computed(() => activeTabIndex.value === 1)

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

const activeOptions = [
  { label: '启用中', value: 'true' as const },
  { label: '已停用', value: 'false' as const },
  { label: '状态全部', value: '' as '' | 'true' | 'false' }
]
const activePickerIndex = ref(0)

const categoryVisibilityOptions = [
  { label: '分类:仅启用', value: 'active' as const },
  { label: '分类:含停用', value: 'all' as const }
]
const categoryVisibilityIndex = ref(0)

const filtersDirty = computed(
  () =>
    Boolean(keyword.value.trim()) ||
    activePickerIndex.value !== 0 ||
    categoryVisibilityIndex.value !== 0 ||
    activeTabIndex.value !== 0
)

/** 管理端分类全量（含字段） */
const categoryRecords = ref<Category[]>([])

const activeCategoryOptions = computed(() =>
  categoryRecords.value
    .filter((c) => c.is_active !== false)
    .map((c) => ({ id: c.id, name: c.name }))
)

const governTargetOptions = computed(() =>
  categoryRecords.value.filter((c) => c.is_active !== false)
)

function targetOptionsExcluding(sourceId: string) {
  if (!sourceId) return governTargetOptions.value
  return governTargetOptions.value.filter((c) => c.id !== sourceId)
}

const isFlatMode = computed(() => Boolean(keyword.value.trim()))
const hasMore = computed(() => items.value.length < total.value)
const emptyTreeHint = computed(() =>
  isPendingTab.value ? '暂无待审核科室' : '暂无分类，点击「＋ 新增分类」创建'
)

type Group = {
  categoryId: string
  categoryName: string
  sortOrder: number
  isActive: boolean
  category: Category | null
  items: ExpertDepartmentItem[]
}

const groupedDepartments = computed((): Group[] => {
  const includeInactive = categoryVisibilityOptions[categoryVisibilityIndex.value]?.value === 'all'
  const map = new Map<string, Group>()
  for (const cat of categoryRecords.value) {
    if (!includeInactive && cat.is_active === false) continue
    map.set(cat.id, {
      categoryId: cat.id,
      categoryName: cat.name,
      sortOrder: Number(cat.sort_order ?? 0) || 0,
      isActive: cat.is_active !== false,
      category: cat,
      items: []
    })
  }
  for (const dept of items.value) {
    const cid = dept.category_id || '__none__'
    if (!map.has(cid)) {
      map.set(cid, {
        categoryId: cid,
        categoryName: dept.category_name || (cid === '__none__' ? '未分类' : '未知分类'),
        sortOrder: 9999,
        isActive: true,
        category: null,
        items: []
      })
    }
    map.get(cid)!.items.push(dept)
  }
  return Array.from(map.values())
    .filter((g) => {
      if (isPendingTab.value) return g.items.length > 0
      return g.items.length > 0 || g.categoryId !== '__none__'
    })
    .sort((a, b) => a.sortOrder - b.sortOrder || a.categoryName.localeCompare(b.categoryName, 'zh'))
})

const formVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const currentItem = ref<ExpertDepartmentItem | null>(null)
const defaultCategoryId = ref('')
const defaultCategoryName = ref('')

const mergeVisible = ref(false)
const mergeSource = ref<ExpertDepartmentItem | null>(null)

const categoryDialogVisible = ref(false)
const changeCategoryItem = ref<ExpertDepartmentItem | null>(null)
const changeCategoryId = ref('')
const changeCategoryPickerIndex = computed(() => {
  const idx = activeCategoryOptions.value.findIndex((c) => c.id === changeCategoryId.value)
  return idx >= 0 ? idx : 0
})
const changeCategoryName = computed(
  () => activeCategoryOptions.value.find((c) => c.id === changeCategoryId.value)?.name || ''
)

const catDialogVisible = ref(false)
const catDialogMode = ref<'create' | 'edit'>('create')
const catEditing = ref<Category | null>(null)

/** 治理：迁移 */
const catMigrateVisible = ref(false)
const catMigrateSourceId = ref('')
const catMigrateSourceName = ref('')
const catMigrateTargetId = ref('')
const catMigrateScopeIndex = ref(0)
const catMigrateScopeLabels = ['全部', '仅专家', '仅科室', '仅房间']
const catMigrateScopeValues: CategoryMigrateScope[] = ['all', 'experts', 'departments', 'rooms']
const catMigrateStats = ref<CategoryMigrateStats | null>(null)
const catMigrateTargetOptions = computed(() => targetOptionsExcluding(catMigrateSourceId.value))
const catMigrateTargetNames = computed(() => catMigrateTargetOptions.value.map((c) => c.name))
const catMigrateTargetIndex = computed(() => {
  const idx = catMigrateTargetOptions.value.findIndex((c) => c.id === catMigrateTargetId.value)
  return idx >= 0 ? idx : 0
})
const catMigrateTargetName = computed(
  () => catMigrateTargetOptions.value.find((c) => c.id === catMigrateTargetId.value)?.name || ''
)

/** 治理：合并 */
const catMergeVisible = ref(false)
const catMergeSourceId = ref('')
const catMergeSourceName = ref('')
const catMergeTargetId = ref('')
const catMergeAttachChildren = ref(false)
const catMergeStats = ref<CategoryMergeResult | null>(null)
const catMergeTargetOptions = computed(() => targetOptionsExcluding(catMergeSourceId.value))
const catMergeTargetNames = computed(() => catMergeTargetOptions.value.map((c) => c.name))
const catMergeReadyToConfirm = computed(
  () => Boolean(catMergeStats.value?.dry_run === true)
)
const catMergePreviewMessage = computed(() => {
  const s = catMergeStats.value
  if (!s) return ''
  if (s.message?.includes('预览：')) return s.message
  return buildMergePreviewMessage(
    Number(s.expert_count ?? 0),
    Number(s.department_count ?? 0),
    Number(s.room_count ?? 0),
    Number(s.child_count ?? 0)
  )
})
const catMergeTargetIndex = computed(() => {
  const idx = catMergeTargetOptions.value.findIndex((c) => c.id === catMergeTargetId.value)
  return idx >= 0 ? idx : 0
})
const catMergeTargetName = computed(
  () => catMergeTargetOptions.value.find((c) => c.id === catMergeTargetId.value)?.name || ''
)

/** 治理：级联删除 */
const catDeleteVisible = ref(false)
const catDeleteSourceId = ref('')
const catDeleteSourceName = ref('')
const catDeleteRefs = ref<CategoryReferences | null>(null)
const catDeleteTargetId = ref('')
const catDeleteTargetOptions = computed(() => targetOptionsExcluding(catDeleteSourceId.value))
const catDeleteTargetNames = computed(() => catDeleteTargetOptions.value.map((c) => c.name))
const catDeleteTargetIndex = computed(() => {
  const idx = catDeleteTargetOptions.value.findIndex((c) => c.id === catDeleteTargetId.value)
  return idx >= 0 ? idx : 0
})
const catDeleteTargetName = computed(
  () => catDeleteTargetOptions.value.find((c) => c.id === catDeleteTargetId.value)?.name || ''
)

function extractCategoryReferences(err: any): CategoryReferences | null {
  const payload = err?.raw?.data ?? err?.data ?? err?.raw
  const body = payload?.data !== undefined && typeof payload.data === 'object' ? payload.data : payload
  const refs = body?.references ?? payload?.references
  if (!refs || typeof refs !== 'object') return null
  return {
    expert_all: Number(refs.expert_all ?? 0) || 0,
    expert_active: Number(refs.expert_active ?? 0) || 0,
    department_count: Number(refs.department_count ?? 0) || 0,
    room_count: Number(refs.room_count ?? 0) || 0,
    active_child_count: Number(refs.active_child_count ?? 0) || 0
  }
}

function isBackendMissing(err: any): boolean {
  const status = Number(err?.statusCode ?? err?.raw?.statusCode ?? 0)
  const code = Number(err?.code ?? 0)
  return status === 404 || status === 405 || code === 404 || code === 405
}

function buildMergePreviewMessage(
  expert: number,
  dept: number,
  room: number,
  child: number
): string {
  return `预览：将合并 ${expert} 位专家、${dept} 个科室、${room} 个房间关联、${child} 个子分类`
}

function normalizeCategoryMergeResult(raw: any, requestedDryRun: boolean): CategoryMergeResult {
  const src =
    raw?.data && typeof raw.data === 'object' && !Array.isArray(raw.data) ? raw.data : raw
  const nested = src?.counts || src?.migrated || src?.preview || src?.result || src
  const expert = Number(
    nested?.expert_count ?? nested?.experts ?? nested?.expert_all ?? src?.expert_count ?? 0
  )
  const dept = Number(
    nested?.department_count ?? nested?.departments ?? src?.department_count ?? 0
  )
  const room = Number(nested?.room_count ?? nested?.rooms ?? src?.room_count ?? 0)
  const child = Number(
    nested?.child_count ?? nested?.children ?? nested?.subcategory_count ?? src?.child_count ?? 0
  )
  const dryRun = nested?.dry_run !== undefined ? Boolean(nested.dry_run) : requestedDryRun
  const message =
    String(nested?.message || src?.message || '').trim() ||
    buildMergePreviewMessage(expert, dept, room, child)
  return {
    dry_run: dryRun,
    expert_count: Number.isFinite(expert) ? expert : 0,
    department_count: Number.isFinite(dept) ? dept : 0,
    room_count: Number.isFinite(room) ? room : 0,
    child_count: Number.isFinite(child) ? child : 0,
    inconsistent_expert_count: Number(nested?.inconsistent_expert_count ?? 0) || 0,
    message
  }
}

function buildLocalMergePreview(sourceId: string): CategoryMergeResult {
  const depts = items.value.filter((d) => d.category_id === sourceId)
  const expert = depts.reduce((sum, d) => sum + (Number(d.expert_count) || 0), 0)
  const dept = depts.length
  return {
    dry_run: true,
    expert_count: expert,
    department_count: dept,
    room_count: 0,
    child_count: 0,
    inconsistent_expert_count: 0,
    message: buildMergePreviewMessage(expert, dept, 0, 0)
  }
}

function ensureAdminAccess(): boolean {
  if (!authStore.isAuthenticated) {
    accessGranted.value = false
    accessMessage.value = '请先登录'
    uni.navigateTo({
      url:
        '/pages/auth/OneTapLogin?redirect=' +
        encodeURIComponent('/pages/admin/expertDepartment/ExpertDepartmentList')
    })
    return false
  }
  if (!authStore.isAdmin) {
    accessGranted.value = false
    accessMessage.value = '权限不足：仅管理员可访问'
    setTimeout(() => uni.navigateBack(), 1200)
    return false
  }
  accessGranted.value = true
  return true
}

function normalizeCategory(raw: any): Category | null {
  if (!raw?.id || !raw?.name) return null
  return {
    id: String(raw.id),
    name: String(raw.name),
    display_name: raw.display_name ? String(raw.display_name) : undefined,
    slug: String(raw.slug || ''),
    icon: raw.icon ?? undefined,
    description: raw.description ?? undefined,
    sort_order: Number(raw.sort_order ?? 0) || 0,
    is_active: raw.is_active !== false,
    parent_id: raw.parent_id ?? null,
    children: raw.children,
    is_primary: raw.is_primary,
    created_at: String(raw.created_at || ''),
    updated_at: String(raw.updated_at || '')
  }
}

async function loadCategories() {
  try {
    const res: any = await getAdminCategories({
      page: 1,
      page_size: 100,
      include_inactive: true
    })
    const list = Array.isArray(res?.items)
      ? res.items
      : Array.isArray(res?.data?.items)
        ? res.data.items
        : Array.isArray(res?.data)
          ? res.data
          : Array.isArray(res)
            ? res
            : []
    categoryRecords.value = list
      .map(normalizeCategory)
      .filter(Boolean) as Category[]
    categoryRecords.value.sort(
      (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, 'zh')
    )
  } catch {
    categoryRecords.value = []
  }
}

async function fetchData(reset = true) {
  if (!accessGranted.value) return
  if (reset) {
    page.value = 1
    loading.value = true
    errorMsg.value = ''
  } else {
    loadingMore.value = true
  }
  try {
    const activeVal = activeOptions[activePickerIndex.value]?.value
    const res = await listExpertDepartments({
      page: page.value,
      size: pageSize.value,
      q: keyword.value.trim() || undefined,
      is_active: activeVal === '' ? undefined : activeVal === 'true',
      is_verified: isPendingTab.value ? false : undefined
    })
    const next = Array.isArray(res.items) ? res.items : []
    if (reset) items.value = next
    else {
      const seen = new Set(items.value.map((x) => x.id))
      items.value = [...items.value, ...next.filter((x) => x?.id && !seen.has(x.id))]
    }
    total.value = Number(res.total) || items.value.length
    selectedIds.value = selectedIds.value.filter((id) => items.value.some((x) => x.id === id))
  } catch (e: any) {
    if (e?.code === 3003) errorMsg.value = '无管理权限'
    else errorMsg.value = getUserFacingErrorMessage(e, '加载失败')
    if (reset) items.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loadingMore.value || loading.value) return
  page.value += 1
  void fetchData(false)
}

function handleSearch() {
  void fetchData(true)
}

function onKeywordInput() {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    void fetchData(true)
  }, 300)
}

function clearKeyword() {
  keyword.value = ''
  void fetchData(true)
}

function onTabTap(idx: number) {
  if (activeTabIndex.value === idx) return
  activeTabIndex.value = idx
  isSelectMode.value = false
  selectedIds.value = []
  void fetchData(true)
}

function handleResetFilters() {
  keyword.value = ''
  activePickerIndex.value = 0
  categoryVisibilityIndex.value = 0
  activeTabIndex.value = 0
  void fetchData(true)
}

function onActiveFilterChange(e: any) {
  activePickerIndex.value = Number(e?.detail?.value) || 0
  void fetchData(true)
}

function onCategoryVisibilityChange(e: any) {
  categoryVisibilityIndex.value = Number(e?.detail?.value) || 0
}

function isCatExpanded(categoryId: string) {
  return expandState.value[categoryId] === true
}

function toggleCat(categoryId: string) {
  expandState.value = {
    ...expandState.value,
    [categoryId]: !expandState.value[categoryId]
  }
}

function toggleSelectMode() {
  isSelectMode.value = !isSelectMode.value
  if (!isSelectMode.value) selectedIds.value = []
}

function toggleSelect(item: ExpertDepartmentItem) {
  if (item.is_verified) return
  const idx = selectedIds.value.indexOf(item.id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(item.id)
}

function selectAllPending() {
  const pending = items.value.filter((x) => !x.is_verified).map((x) => x.id)
  const allSelected = pending.length > 0 && pending.every((id) => selectedIds.value.includes(id))
  selectedIds.value = allSelected ? [] : pending
}

function openCreate(categoryId: string) {
  if (!categoryId || categoryId === '__none__') {
    uni.showToast({ title: '请在分类下新增科室', icon: 'none' })
    return
  }
  formMode.value = 'create'
  currentItem.value = null
  defaultCategoryId.value = categoryId
  defaultCategoryName.value =
    categoryRecords.value.find((c) => c.id === categoryId)?.name || ''
  formVisible.value = true
}

function openEdit(item: ExpertDepartmentItem) {
  formMode.value = 'edit'
  currentItem.value = item
  defaultCategoryId.value = ''
  defaultCategoryName.value = ''
  formVisible.value = true
}

function onFormSuccess() {
  void fetchData(true)
}

function openMerge(item: ExpertDepartmentItem) {
  mergeSource.value = item
  mergeVisible.value = true
}

function openChangeCategory(item: ExpertDepartmentItem) {
  changeCategoryItem.value = item
  changeCategoryId.value = item.category_id || ''
  categoryDialogVisible.value = true
}

function onChangeCategoryPick(e: any) {
  const opt = activeCategoryOptions.value[Number(e?.detail?.value)]
  if (opt) changeCategoryId.value = opt.id
}

async function submitChangeCategory() {
  const item = changeCategoryItem.value
  if (!item?.id || !changeCategoryId.value) {
    uni.showToast({ title: '请选择分类', icon: 'none' })
    return
  }
  try {
    const res = await updateExpertDepartmentCategory(item.id, changeCategoryId.value)
    const n = Number(res?.synced_experts ?? 0)
    uni.showToast({
      title: Number.isFinite(n) ? `已改分类，同步专家 ${n} 人` : '已改分类',
      icon: 'none'
    })
    categoryDialogVisible.value = false
    await fetchData(true)
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '改分类失败'), icon: 'none' })
  }
}

async function handleVerifyOne(item: ExpertDepartmentItem) {
  try {
    const res = await batchVerifyExpertDepartments({
      department_ids: [item.id],
      verified: true
    })
    const n = Number(res?.affected ?? 1)
    uni.showToast({ title: `已通过${Number.isFinite(n) ? ` (${n})` : ''}`, icon: 'success' })
    await fetchData(true)
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '审核失败'), icon: 'none' })
  }
}

async function handleBatchVerify() {
  if (!selectedIds.value.length) return
  uni.showModal({
    title: '批量通过',
    content: `确定将选中的 ${selectedIds.value.length} 条标记为已审核？`,
    success: async (r) => {
      if (!r.confirm) return
      try {
        const res = await batchVerifyExpertDepartments({
          department_ids: selectedIds.value.slice(0, 200),
          verified: true
        })
        const n = Number(res?.affected ?? selectedIds.value.length)
        uni.showToast({
          title: `已通过 ${Number.isFinite(n) ? n : selectedIds.value.length} 条`,
          icon: 'success'
        })
        selectedIds.value = []
        isSelectMode.value = false
        await fetchData(true)
      } catch (e: any) {
        uni.showToast({ title: getUserFacingErrorMessage(e, '批量审核失败'), icon: 'none' })
      }
    }
  })
}

function handleDeactivate(item: ExpertDepartmentItem) {
  uni.showModal({
    title: '停用科室',
    content: `确定停用「${item.name}」？停用后可在状态筛「已停用」中查看并重新启用。`,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await updateExpertDepartment(item.id, { is_active: false })
        uni.showToast({ title: '已停用', icon: 'success' })
        await fetchData(true)
      } catch (e: any) {
        uni.showToast({ title: getUserFacingErrorMessage(e, '停用失败'), icon: 'none' })
      }
    }
  })
}

function handleHardDelete(item: ExpertDepartmentItem) {
  const count = item.expert_count ?? 0
  if (count > 0) {
    uni.showModal({
      title: '无法删除',
      content: `「${item.name}」仍有 ${count} 位专家关联，请先使用「合并」迁移到其他科室后再删除。`,
      showCancel: false
    })
    return
  }
  uni.showModal({
    title: '删除科室',
    content: `确定永久删除「${item.name}」？删除后不可从本页恢复（与「停用」不同，此为物理删除）。`,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await deleteExpertDepartment(item.id, { hardDelete: true })
        uni.showToast({ title: '已删除', icon: 'success' })
        await fetchData(true)
      } catch (e: any) {
        uni.showToast({ title: getUserFacingErrorMessage(e, '删除失败'), icon: 'none' })
      }
    }
  })
}

async function handleRestore(item: ExpertDepartmentItem) {
  try {
    await updateExpertDepartment(item.id, { is_active: true })
    uni.showToast({ title: '已启用', icon: 'success' })
    await fetchData(true)
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '启用失败'), icon: 'none' })
  }
}

function openCreateCategory() {
  catDialogMode.value = 'create'
  catEditing.value = null
  catDialogVisible.value = true
}

async function openEditCategory(group: Group) {
  if (group.categoryId === '__none__') return
  let cat = group.category || categoryRecords.value.find((c) => c.id === group.categoryId) || null
  if (!cat || !cat.slug) {
    try {
      const detail: any = await getAdminCategoryDetail(group.categoryId)
      const raw = detail?.data ?? detail
      cat = normalizeCategory(raw)
    } catch (e: any) {
      uni.showToast({ title: getUserFacingErrorMessage(e, '加载分类失败'), icon: 'none' })
      return
    }
  }
  if (!cat) {
    uni.showToast({ title: '分类不存在', icon: 'none' })
    return
  }
  catDialogMode.value = 'edit'
  catEditing.value = cat
  catDialogVisible.value = true
}

async function onCategoryFormSuccess() {
  await loadCategories()
  await fetchData(true)
}

function handleDeactivateCategory(group: Group) {
  if (group.categoryId === '__none__') return
  const count = group.items.length
  const tip =
    count > 0
      ? `「${group.categoryName}」下仍有 ${count} 个科室词条。停用后 C 端默认不可见；词条仍在，请勿再往此分类新建。`
      : `确定停用分类「${group.categoryName}」？停用后 C 端默认不可见，可在「分类:含停用」中启用。`
  uni.showModal({
    title: '停用分类',
    content: tip,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await deleteCategory(group.categoryId)
        uni.showToast({ title: '分类已停用', icon: 'success' })
        categoryVisibilityIndex.value = 1
        await loadCategories()
        await fetchData(true)
      } catch (e: any) {
        const refs = extractCategoryReferences(e)
        if (Number(e?.statusCode) === 409 && refs) {
          catDeleteSourceId.value = group.categoryId
          catDeleteSourceName.value = group.categoryName
          catDeleteRefs.value = refs
          catDeleteTargetId.value = ''
          catDeleteVisible.value = true
          return
        }
        uni.showToast({ title: getUserFacingErrorMessage(e, '停用分类失败'), icon: 'none' })
      }
    }
  })
}

async function handleActivateCategory(group: Group) {
  if (group.categoryId === '__none__') return
  try {
    await updateCategory(group.categoryId, { is_active: true })
    uni.showToast({ title: '分类已启用', icon: 'success' })
    await loadCategories()
    await fetchData(true)
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '启用分类失败'), icon: 'none' })
  }
}

function openCategoryGovern(group: Group) {
  if (group.categoryId === '__none__') return
  const itemList = ['迁移引用', '合并分类']
  if (group.isActive) itemList.push('删除分类')
  else itemList.push('启用分类')
  uni.showActionSheet({
    itemList,
    success: (res) => {
      const i = res.tapIndex
      if (i === 0) openCatMigrate(group)
      else if (i === 1) openCatMerge(group)
      else if (i === 2) {
        if (group.isActive) void handleCatDelete(group)
        else void handleActivateCategory(group)
      }
    }
  })
}

function openCatMigrate(group: Group) {
  catMigrateSourceId.value = group.categoryId
  catMigrateSourceName.value = group.categoryName
  catMigrateTargetId.value = ''
  catMigrateScopeIndex.value = 0
  catMigrateStats.value = null
  catMigrateVisible.value = true
}

function closeCatMigrate() {
  catMigrateVisible.value = false
  catMigrateStats.value = null
}

function onCatMigrateTargetChange(e: any) {
  const opt = catMigrateTargetOptions.value[Number(e?.detail?.value)]
  catMigrateTargetId.value = opt?.id || ''
}

function onCatMigrateScopeChange(e: any) {
  catMigrateScopeIndex.value = Number(e?.detail?.value) || 0
}

async function submitCatMigrate() {
  if (!catMigrateSourceId.value || !catMigrateTargetId.value) {
    uni.showToast({ title: '请选择目标分类', icon: 'none' })
    return
  }
  if (catMigrateTargetId.value === catMigrateSourceId.value) {
    uni.showToast({ title: '目标不能与源相同', icon: 'none' })
    return
  }
  try {
    const res = await migrateCategoryReferences(catMigrateSourceId.value, {
      target_category_id: catMigrateTargetId.value,
      scope: catMigrateScopeValues[catMigrateScopeIndex.value] || 'all'
    })
    catMigrateStats.value = res.migrated
    uni.showToast({
      title: `已迁移 专家${res.migrated?.expert_count ?? 0}/科室${res.migrated?.department_count ?? 0}/房间${res.migrated?.room_count ?? 0}`,
      icon: 'none'
    })
    await loadCategories()
    await fetchData(true)
  } catch (e: any) {
    if (isBackendMissing(e)) {
      uni.showToast({ title: '后端尚未开通迁移接口', icon: 'none' })
      return
    }
    uni.showToast({ title: getUserFacingErrorMessage(e, '迁移失败'), icon: 'none' })
  }
}

function openCatMerge(group: Group) {
  catMergeSourceId.value = group.categoryId
  catMergeSourceName.value = group.categoryName
  catMergeTargetId.value = ''
  catMergeAttachChildren.value = false
  catMergeStats.value = null
  catMergeVisible.value = true
}

function closeCatMerge() {
  catMergeVisible.value = false
  catMergeStats.value = null
}

function onCatMergeTargetChange(e: any) {
  const opt = catMergeTargetOptions.value[Number(e?.detail?.value)]
  catMergeTargetId.value = opt?.id || ''
  catMergeStats.value = null
}

function onCatMergeAttachChange(e: any) {
  catMergeAttachChildren.value = Boolean(e?.detail?.value)
  catMergeStats.value = null
}

async function submitCatMerge() {
  if (!catMergeSourceId.value || !catMergeTargetId.value) {
    uni.showToast({ title: '请选择目标分类', icon: 'none' })
    return
  }
  if (catMergeTargetId.value === catMergeSourceId.value) {
    uni.showToast({ title: '目标不能与源相同', icon: 'none' })
    return
  }
  const dryRun = !catMergeReadyToConfirm.value
  try {
    const res = await mergeCategories({
      source_id: catMergeSourceId.value,
      target_id: catMergeTargetId.value,
      attach_children: catMergeAttachChildren.value,
      dry_run: dryRun
    })
    catMergeStats.value = normalizeCategoryMergeResult(res, dryRun)
    if (dryRun) {
      const local = buildLocalMergePreview(catMergeSourceId.value)
      if (
        local.department_count > 0 &&
        !catMergeStats.value.department_count &&
        !catMergeStats.value.expert_count
      ) {
        catMergeStats.value = local
      } else {
        catMergeStats.value = { ...catMergeStats.value, dry_run: true }
      }
      uni.showToast({ title: '预览完成', icon: 'none' })
      return
    }
    uni.showToast({ title: '合并完成', icon: 'success' })
    closeCatMerge()
    await loadCategories()
    await fetchData(true)
  } catch (e: any) {
    if (dryRun) {
      catMergeStats.value = buildLocalMergePreview(catMergeSourceId.value)
      uni.showToast({
        title: isBackendMissing(e)
          ? '后端未开通合并接口，已本地预览'
          : '预览失败，已按当前列表估算',
        icon: 'none'
      })
      return
    }
    if (isBackendMissing(e)) {
      uni.showToast({ title: '后端尚未开通合并接口', icon: 'none' })
      return
    }
    uni.showToast({ title: getUserFacingErrorMessage(e, '合并失败'), icon: 'none' })
  }
}

async function handleCatDelete(group: Group) {
  const { confirm } = await new Promise<{ confirm: boolean }>((resolve) => {
    uni.showModal({
      title: '删除分类',
      content: `确定删除「${group.categoryName}」？若存在引用将提示级联安顿。`,
      confirmColor: '#ff4d4f',
      success: (r) => resolve({ confirm: Boolean(r.confirm) }),
      fail: () => resolve({ confirm: false })
    })
  })
  if (!confirm) return
  try {
    await deleteCategory(group.categoryId, {}, { showError: false })
    uni.showToast({ title: '分类已停用', icon: 'success' })
    categoryVisibilityIndex.value = 1
    await loadCategories()
    await fetchData(true)
  } catch (e: any) {
    const refs = extractCategoryReferences(e)
    if (Number(e?.statusCode) === 409 && refs) {
      catDeleteSourceId.value = group.categoryId
      catDeleteSourceName.value = group.categoryName
      catDeleteRefs.value = refs
      catDeleteTargetId.value = ''
      catDeleteVisible.value = true
      return
    }
    if (isBackendMissing(e)) {
      // 旧后端无 force：回退软删确认
      handleDeactivateCategory(group)
      return
    }
    uni.showToast({ title: getUserFacingErrorMessage(e, '删除分类失败'), icon: 'none' })
  }
}

function closeCatDelete() {
  catDeleteVisible.value = false
  catDeleteRefs.value = null
}

function onCatDeleteTargetChange(e: any) {
  const opt = catDeleteTargetOptions.value[Number(e?.detail?.value)]
  catDeleteTargetId.value = opt?.id || ''
}

async function submitCatDeleteForce() {
  if (!catDeleteSourceId.value) return
  try {
    await deleteCategory(catDeleteSourceId.value, {
      force: true,
      ...(catDeleteTargetId.value ? { target_category_id: catDeleteTargetId.value } : {})
    })
    uni.showToast({ title: '已级联停用', icon: 'success' })
    closeCatDelete()
    categoryVisibilityIndex.value = 1
    await loadCategories()
    await fetchData(true)
  } catch (e: any) {
    if (isBackendMissing(e)) {
      uni.showToast({ title: '后端尚未开通级联删除', icon: 'none' })
      return
    }
    uni.showToast({ title: getUserFacingErrorMessage(e, '级联停用失败'), icon: 'none' })
  }
}

function toastInactiveCategory() {
  uni.showToast({ title: '请先启用分类', icon: 'none' })
}

onMounted(() => {
  if (ensureAdminAccess()) {
    void loadCategories()
    void fetchData(true)
  }
})

onUnmounted(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})

onPullDownRefresh(async () => {
  try {
    if (ensureAdminAccess()) {
      await loadCategories()
      await fetchData(true)
    }
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
  padding: var(--spacing-md);
  padding-bottom: 80px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: var(--spacing-sm);
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
}

.tab-bar {
  display: flex;
  align-items: stretch;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.tab-item {
  position: relative;
  padding: 4px 0 8px;
}

.tab-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.tab-item--active .tab-label {
  color: var(--color-text-primary);
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: #0f766e;
  border-radius: 1px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-btn {
  padding: 4px 6px;
  font-size: 13px;
  color: var(--color-text-primary);
}

.header-add-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 30px;
  padding: 0 10px;
  background: #0f766e;
  color: #fff;
  border-radius: var(--border-radius-base);
  font-size: 13px;
}

.add-icon {
  font-size: 14px;
  line-height: 1;
}

.toolbar-search {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.toolbar-secondary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 0;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 32px 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background: var(--color-bg-primary);
  font-size: 13px;
  box-sizing: border-box;
}

.search-clear {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: var(--color-text-tertiary);
  padding: 4px;
}

.btn-query,
.btn-add,
.btn-batch {
  height: 32px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  flex-shrink: 0;
}

.btn-query {
  background: var(--color-primary);
}

.btn-add {
  background: #52c41a;
}

.btn-batch {
  background: var(--color-primary);
}

.btn-batch.disabled {
  opacity: 0.45;
}

.btn-text {
  color: #fff;
  font-size: 13px;
}

.filter-picker {
  height: 32px;
  max-width: 110px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  flex-shrink: 0;
  overflow: hidden;
}

.filter-picker__label {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow {
  font-size: 10px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
  flex-shrink: 0;
}

.btn-reset {
  height: 32px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.btn-reset-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.link-jump {
  font-size: 12px;
  color: var(--color-primary);
}

.state-box {
  padding: 40px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.state-box--sm {
  padding: 16px;
}

.state-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.group {
  margin-bottom: 10px;
}

.cat-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
}

.cat-arrow {
  font-size: 10px;
  color: var(--color-text-tertiary);
  width: 12px;
  flex-shrink: 0;
}

.cat-name {
  flex: 1;
  min-width: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-count {
  font-size: 12px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  white-space: nowrap;
}

.cat-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  margin-left: auto;
}

.cat-btn {
  height: 28px;
  min-width: 62px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg-primary);
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  box-sizing: border-box;
}

.group--inactive {
  opacity: 0.72;
}

.group-children {
  padding: 8px 0 4px;
}

.dept-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  padding: 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.dept-card--inactive {
  opacity: 0.72;
}

.dept-card__body {
  flex: 1;
  min-width: 0;
}

.dept-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.dept-card__name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dept-card__meta {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}

.dept-card__actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  margin-top: 10px;
  width: 100%;
}

.action-chip {
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: #f5f5f5;
  font-size: 12px;
  color: var(--color-text-primary);
  white-space: nowrap;
  box-sizing: border-box;
}

.action-chip text {
  white-space: nowrap;
}

.action-chip--del {
  color: #cf1322;
}

.action-chip--ok {
  color: #389e0d;
  background: #f6ffed;
}

.add-under {
  margin: 4px 0 8px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #0f766e;
  border-radius: var(--border-radius-base);
  color: #0f766e;
  font-size: 13px;
}

.add-under--disabled {
  color: var(--color-text-tertiary);
  border-color: var(--color-border);
  border-style: solid;
}

.item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
}

.item--child {
  margin-left: 8px;
}

.item--inactive {
  opacity: 0.65;
}

.item-check {
  width: 22px;
  height: 22px;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.item-check.disabled {
  opacity: 0.35;
}

.check-mark {
  font-size: 12px;
  color: var(--color-primary);
}

.item-main {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.item-bullet {
  font-size: 15px;
  color: var(--color-text-tertiary);
  line-height: 1;
}

.meta--inline {
  display: inline;
  margin-left: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
}

.tag--pending {
  background: #fff7e6;
  color: #d48806;
}

.tag--ok {
  background: #f6ffed;
  color: #389e0d;
}

.tag--off {
  background: #f5f5f5;
  color: #8c8c8c;
}

.tag--cat {
  background: #e6f4ff;
  color: #1677ff;
}

.meta,
.synonyms {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

.synonym-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.syn-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
}

.item-actions {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px;
  flex-shrink: 0;
  max-width: 58%;
}

.action-btn {
  min-width: 44px;
  height: 24px;
  padding: 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 11px;
}

.btn-plain {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn-ok {
  background: #f6ffed;
  color: #389e0d;
}

.btn-del {
  background: #fff1f0;
  color: #cf1322;
}

.btn-risk {
  background: transparent;
  color: #cf1322;
  border: 1px solid #ffccc7;
}

.load-more {
  text-align: center;
  padding: 12px;
  color: var(--color-primary);
  font-size: 13px;
}

.select-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  background: var(--color-bg-primary);
  border-top: 1px solid var(--color-border);
  z-index: 50;
}

.select-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--color-text-primary);
}

.select-count {
  color: var(--color-text-tertiary);
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
}

.dialog {
  width: 100%;
  max-width: 400px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 16px;
}

.dialog-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.dialog-sub {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 12px;
}

.field {
  margin-bottom: 12px;
}

.label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  box-sizing: border-box;
  font-size: 14px;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
}

.picker-value {
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-base);
}

.btn-cancel {
  background: var(--color-bg-secondary);
}

.btn-confirm {
  background: var(--color-primary);
  color: #fff;
}

.btn-confirm--danger {
  background: #dc2626;
}

.dialog--wide {
  max-width: 420px;
  max-height: 85vh;
  overflow-y: auto;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.dialog-close {
  font-size: 18px;
  color: var(--color-text-tertiary);
  padding: 4px;
  line-height: 1;
}

.form-group {
  margin-bottom: 12px;
}

.form-group--row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.form-group--row .form-label {
  margin-bottom: 0;
}

.form-static {
  min-height: 36px;
  padding: 8px 10px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  color: var(--color-text-primary);
}

.form-note {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.form-note--hint {
  margin-top: 4px;
  margin-bottom: 12px;
}

.form-note--preview {
  margin-bottom: 10px;
}

.picker-value--ph {
  color: var(--color-text-tertiary);
}

.ref-block {
  margin: 8px 0 12px;
  padding: 10px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.ref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
}

.ref-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.ref-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
}
</style>
