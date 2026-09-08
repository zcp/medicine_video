<!--
 * TagList - 标签管理列表页
 * @description 管理端词库：搜/筛 → 建改 → 停用可恢复；含运营与用户自建（V2 source）
 * 顶栏/行密度对标 BrandAdminList；行信息按标签前端设计 §6.1.0
 -->
<template>
  <view class="tag-list-page">
    <view class="page-header">
      <view class="toolbar-search">
        <view class="search-box">
          <input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索标签名称或英文标识"
            confirm-type="search"
            @confirm="handleSearch"
          />
          <view v-if="searchKeyword" class="search-clear" @tap="clearSearch">✕</view>
        </view>
      </view>
      <view class="toolbar-actions">
        <view class="btn-query" @tap="handleSearch">
          <text class="btn-text">查询</text>
        </view>
        <view class="btn-add" @tap="openCreateDialog">
          <text class="btn-text">新建</text>
        </view>
        <picker
          :range="statusOptions"
          range-key="label"
          :value="statusPickerIndex"
          @change="onStatusFilterChange"
        >
          <view class="filter-picker">
            <text class="filter-picker__label">{{ statusOptions[statusPickerIndex].label }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
      </view>
    </view>

    <view class="tag-list" v-if="!loading">
      <view v-if="displayData.length === 0" class="empty-state">
        <text class="empty-text">{{ emptyText }}</text>
      </view>

      <view
        v-for="item in displayData"
        :key="item.id"
        :class="['tag-item', { 'tag-item--inactive': !item.is_active }]"
      >
        <view class="item-row">
          <view class="item-main">
            <view class="name-row">
              <text class="item-name">{{ item.name }}</text>
              <text :class="['status-tag', item.is_active ? 'status-on' : 'status-off']">
                {{ item.is_active ? '启用' : '已停用' }}
              </text>
            </view>
            <view v-if="item.slug || sourceLabel(item)" class="meta-row">
              <text v-if="item.slug" class="slug-text">{{ item.slug }}</text>
              <text v-if="sourceLabel(item)" class="source-tag">{{ sourceLabel(item) }}</text>
            </view>
            <text v-if="item.description" class="desc-text">{{ item.description }}</text>
            <text class="meta-text">创建于 {{ formatDate(item.created_at) }}</text>
          </view>
          <view class="item-actions">
            <view class="action-btn btn-plain" @tap="openEditDialog(item)">
              <text>编辑</text>
            </view>
            <view
              v-if="item.is_active"
              class="action-btn btn-del"
              @tap="handleDeactivate(item)"
            >
              <text>停用</text>
            </view>
            <view v-else class="action-btn btn-enable" @tap="handleActivate(item)">
              <text>启用</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-else class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <TagFormDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="currentTag"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, deleteTag, updateTag } from '@/api/tags'
import type { Tag } from '@/types/tags'
import TagFormDialog from './TagFormDialog.vue'

type StatusFilter = 'all' | 'active' | 'inactive'

const allData = ref<Tag[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref<StatusFilter>('all')

const statusOptions = [
  { label: '全部状态', value: 'all' as const },
  { label: '启用中', value: 'active' as const },
  { label: '已停用', value: 'inactive' as const }
]

const statusPickerIndex = computed(() =>
  Math.max(0, statusOptions.findIndex((o) => o.value === statusFilter.value))
)

const displayData = computed(() => {
  if (statusFilter.value === 'active') return allData.value.filter((t) => t.is_active)
  if (statusFilter.value === 'inactive') return allData.value.filter((t) => !t.is_active)
  return allData.value
})

const emptyText = computed(() => {
  if (searchKeyword.value || statusFilter.value !== 'all') return '未找到匹配的标签'
  return '暂无标签数据'
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentTag = ref<Tag | null>(null)

function formatDate(iso: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function sourceLabel(item: Tag): string {
  const s = (item.source || '').toLowerCase()
  if (s === 'user') return '用户'
  if (s === 'admin') return '运营'
  return ''
}

function onStatusFilterChange(e: { detail: { value: string } }) {
  const idx = Number(e.detail.value)
  const next = statusOptions[idx]?.value ?? 'all'
  statusFilter.value = next
  logger.info('user', '切换标签状态筛', { status: next })
}

async function fetchData() {
  loading.value = true
  try {
    logger.info('network', '加载管理端标签列表', {
      q: searchKeyword.value || undefined
    })
    const res = await getTags({
      q: searchKeyword.value || undefined,
      include_inactive: true
    })
    const data = res.data
    if (Array.isArray(data)) {
      allData.value = data
    } else {
      allData.value = data?.items || []
    }
    logger.info('network', '管理端标签列表加载完成', {
      count: allData.value.length
    })
  } catch (error) {
    logger.error('system', '加载管理端标签列表失败', error)
    uni.showToast({ title: '加载标签列表失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  logger.info('user', '搜索标签', { keyword: searchKeyword.value })
  fetchData()
}

function clearSearch() {
  logger.info('user', '清除标签搜索条件')
  searchKeyword.value = ''
  handleSearch()
}

function openCreateDialog() {
  logger.info('user', '打开新增标签弹窗')
  dialogMode.value = 'create'
  currentTag.value = null
  dialogVisible.value = true
}

function openEditDialog(tag: Tag) {
  logger.info('user', '打开编辑标签弹窗', { id: tag.id, name: tag.name })
  dialogMode.value = 'edit'
  currentTag.value = { ...tag }
  dialogVisible.value = true
}

/** 停用：DELETE /admin/tags/{id}（软删 is_active=false） */
function handleDeactivate(tag: Tag) {
  logger.info('user', '准备停用标签', { id: tag.id, name: tag.name })
  uni.showModal({
    title: '停用标签',
    content: `确定停用「${tag.name}」？停用后开播侧公开联想不可见，可在「已停用」中重新启用。`,
    confirmText: '停用',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteTag(tag.id)
        logger.info('network', '标签停用成功', { id: tag.id })
        uni.showToast({ title: '已停用', icon: 'success' })
        fetchData()
      } catch (error) {
        logger.error('system', '标签停用失败', { tagId: tag.id, error })
        uni.showToast({ title: '停用失败', icon: 'none' })
      }
    }
  })
}

/** 启用：PATCH /admin/tags/{id} { is_active: true } */
function handleActivate(tag: Tag) {
  logger.info('user', '准备启用标签', { id: tag.id, name: tag.name })
  uni.showModal({
    title: '启用标签',
    content: `确定重新启用「${tag.name}」？`,
    confirmText: '启用',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await updateTag(tag.id, { is_active: true })
        logger.info('network', '标签启用成功', { id: tag.id })
        uni.showToast({ title: '已启用', icon: 'success' })
        fetchData()
      } catch (error) {
        logger.error('system', '标签启用失败', { tagId: tag.id, error })
        uni.showToast({ title: '启用失败', icon: 'none' })
      }
    }
  })
}

onMounted(() => {
  logger.info('system', '进入标签管理页')
  fetchData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.tag-list-page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
  padding: var(--spacing-md);
}

.page-header {
  margin-bottom: var(--spacing-sm);
}

.toolbar-search {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.toolbar-actions {
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
  height: 32px;
  padding: 0 28px 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background: var(--color-bg-primary);
  font-size: 13px;
  box-sizing: border-box;
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.btn-query,
.btn-add {
  height: 32px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  flex-shrink: 0;

  .btn-text {
    color: #fff;
    font-size: 13px;
  }
}

.btn-query {
  background: var(--color-primary);
}

.btn-add {
  background: #52c41a;
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

.tag-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tag-item {
  padding: 10px 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);

  &--inactive {
    opacity: 0.72;
  }
}

.item-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.item-name {
  flex: 1;
  min-width: 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tag {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  line-height: 1.4;
}

.status-on {
  background: #e6f7ff;
  color: #1890ff;
}

.status-off {
  background: #f5f5f5;
  color: var(--color-text-secondary);
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.slug-text {
  min-width: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-tag {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f5f5f5;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.desc-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.item-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  flex-shrink: 0;
}

.action-btn {
  height: 28px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-sm);
  font-size: 12px;
  border: 1px solid var(--color-border);
}

.btn-plain {
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-del {
  background: transparent;
  border-color: #ffccc7;
  color: #ff4d4f;
}

.btn-enable {
  background: #f6ffed;
  border-color: #b7eb8f;
  color: #52c41a;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: var(--spacing-md);
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
}

.empty-text,
.loading-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
