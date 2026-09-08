<!--
 * RoomCategorySelector - 直播间分类关联选择器
 * @description 用于管理直播间与科室分类的关联关系
 * @author 直播SaaS团队
 -->
<template>
  <view class="room-category-selector">
    <view class="selector-header">
      <text class="header-title">所属科室</text>
      <view class="header-tag">
        <text class="tag-text">最多 50 个</text>
      </view>
    </view>

    <!-- 分类选择器 -->
    <view class="selector-body">
      <view class="select-trigger" @click="showPicker = true">
        <view v-if="selectedIds.length > 0" class="selected-preview">
          <view
            v-for="catId in selectedIds.slice(0, 3)"
            :key="catId"
            class="preview-tag"
          >
            <text class="preview-tag-text">{{ getCategoryName(catId) }}</text>
          </view>
          <view v-if="selectedIds.length > 3" class="preview-more">
            <text class="more-text">+{{ selectedIds.length - 3 }}</text>
          </view>
        </view>
        <text v-else class="placeholder-text">选择科室</text>
        <view class="select-arrow">
          <text class="arrow-icon">▼</text>
        </view>
      </view>
    </view>

    <!-- 已选科室标签 -->
    <view class="selected-tags" v-if="selectedIds.length > 0">
      <view
        v-for="catId in selectedIds"
        :key="catId"
        class="tag-item"
      >
        <text class="tag-name">{{ getCategoryName(catId) }}</text>
        <view
          v-if="primaryCategoryId === catId"
          class="tag-primary"
        >
          <text class="primary-text">主</text>
        </view>
        <view
          v-else
          class="tag-set-primary"
          @click="setPrimaryCategory(catId)"
        >
          <text class="set-primary-text">设为主</text>
        </view>
        <view class="tag-close" @click="removeCategory(catId)">
          <text class="close-icon">✕</text>
        </view>
      </view>
      <text class="primary-hint">未指定主分类时，保存默认以第一项为主</text>
    </view>

    <!-- 分类选择弹窗 -->
    <view class="picker-overlay" v-if="showPicker" @click="handleOverlayClick">
      <view class="picker-container" @click="handlePickerClick">
        <view class="picker-header">
          <text class="picker-title">选择科室</text>
          <view class="picker-close" @click="showPicker = false">
            <text class="close-icon">✕</text>
          </view>
        </view>
        <view class="picker-body">
          <view v-if="loading" class="picker-loading">
            <view class="loading-spinner"></view>
            <text class="loading-text">加载中...</text>
          </view>
          <view v-else class="picker-list">
            <view
              v-for="cat in allCategories"
              :key="cat.id"
              :class="['picker-item', { 'is-selected': isSelected(cat.id) }]"
              @click="toggleCategory(cat.id)"
            >
              <view class="item-icon" v-if="cat.icon">
                <image :src="cat.icon" class="icon-image" mode="aspectFill" />
              </view>
              <view class="item-icon" v-else>
                <text class="icon-placeholder">🏷️</text>
              </view>
              <text class="item-name">{{ cat.name }}</text>
              <view v-if="isSelected(cat.id)" class="item-check">
                <text class="check-icon">✓</text>
              </view>
            </view>
          </view>
        </view>
        <view class="picker-footer">
          <view class="picker-btn" @click="showPicker = false">
            <text class="btn-text">完成</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import categoryApi from '@/api/categories'
import type { Category } from '@/types/category'

const props = defineProps<{
  roomId: string
}>()

const allCategories = ref<Category[]>([])
const selectedIds = ref<string[]>([])
const primaryCategoryId = ref<string>('')
const loading = ref(false)
const showPicker = ref(false)

/** 小程序 named/default 导出互操作兜底 */
function resolveCategoryApi() {
  const mod: any = categoryApi
  const root = typeof mod?.getAllCategories === 'function' ? mod : mod?.default
  const getAllCategories = root?.getAllCategories || root?.getCategoryList
  const getRoomCategories = root?.getRoomCategories
  const setRoomCategories = root?.setRoomCategories
  const removeRoomCategory = root?.removeRoomCategory
  if (
    typeof getAllCategories !== 'function' ||
    typeof getRoomCategories !== 'function' ||
    typeof setRoomCategories !== 'function' ||
    typeof removeRoomCategory !== 'function'
  ) {
    throw new Error('科室接口暂不可用')
  }
  return { getAllCategories, getRoomCategories, setRoomCategories, removeRoomCategory }
}

function getCategoryName(id: string): string {
  return allCategories.value.find(c => c.id === id)?.name || id
}

function isSelected(id: string): boolean {
  return selectedIds.value.includes(id)
}

function summarizeCategory(category: Category) {
  return {
    id: category.id,
    name: category.name,
    slug: category.slug,
    is_active: category.is_active,
    sort_order: category.sort_order
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    logger.info('network', '加载直播间科室', { roomId: props.roomId })
    const api = resolveCategoryApi()
    const [all, selected] = await Promise.all([
      api.getAllCategories(),
      api.getRoomCategories(props.roomId)
    ])
    const allList = Array.isArray(all) ? all : []
    const selectedList = Array.isArray(selected) ? selected : []
    allCategories.value = allList
    selectedIds.value = selectedList.map((c: Category) => c.id).filter(Boolean)
    const primaryHit = selectedList.find((c: Category) => c.is_primary === true)
    primaryCategoryId.value = primaryHit?.id
      || (selectedIds.value.length ? selectedIds.value[0] : '')
    logger.info('network', '直播间科室加载完成', {
      roomId: props.roomId,
      allCount: allList.length,
      selectedCount: selectedIds.value.length,
      primaryCategoryId: primaryCategoryId.value,
      selectedSample: selectedList.slice(0, 5).map(summarizeCategory)
    })
  } catch (error: any) {
    logger.error('system', '加载直播间科室失败', {
      roomId: props.roomId,
      message: error?.message || String(error),
      name: error?.name
    })
    uni.showToast({ title: '暂时无法加载科室，请稍后重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 点击遮罩层关闭选择器 */
function handleOverlayClick() {
  showPicker.value = false
}

/** 点击选择器内容区域，阻止冒泡 */
function handlePickerClick(event: Event) {
  event.stopPropagation()
}

// 切换分类选择状态
async function toggleCategory(catId: string) {
  const index = selectedIds.value.indexOf(catId)
  let newIds: string[]
  let nextPrimary = primaryCategoryId.value

  if (index > -1) {
    // 移除
    newIds = selectedIds.value.filter(id => id !== catId)
    if (nextPrimary === catId) {
      nextPrimary = newIds[0] || ''
    }
  } else {
    // 添加
    if (selectedIds.value.length >= 50) {
      uni.showToast({ title: '最多选择 50 个科室', icon: 'none' })
      return
    }
    newIds = [...selectedIds.value, catId]
    if (!nextPrimary) nextPrimary = catId
  }

  logger.info('user', '切换直播间科室', {
    roomId: props.roomId,
    categoryId: catId,
    action: index > -1 ? 'remove' : 'add',
    beforeCount: selectedIds.value.length,
    afterCount: newIds.length,
    primaryCategoryId: nextPrimary
  })

  try {
    const api = resolveCategoryApi()
    await api.setRoomCategories(props.roomId, {
      category_ids: newIds,
      mode: 'replace',
      primary_category_id: nextPrimary || undefined
    })
    selectedIds.value = newIds
    primaryCategoryId.value = nextPrimary
    logger.info('network', '直播间科室更新成功', {
      roomId: props.roomId,
      categoryIds: newIds,
      primaryCategoryId: nextPrimary
    })
    uni.showToast({ title: '科室已更新', icon: 'success' })
  } catch (error: any) {
    logger.error('system', '更新直播间科室失败', {
      roomId: props.roomId,
      categoryId: catId,
      nextIds: newIds,
      message: error?.message || String(error)
    })
    uni.showToast({ title: '保存失败，请稍后重试', icon: 'none' })
    loadData() // 回滚
  }
}

async function setPrimaryCategory(categoryId: string) {
  if (!selectedIds.value.includes(categoryId) || primaryCategoryId.value === categoryId) return
  const prev = primaryCategoryId.value
  primaryCategoryId.value = categoryId
  try {
    const api = resolveCategoryApi()
    await api.setRoomCategories(props.roomId, {
      category_ids: selectedIds.value,
      mode: 'replace',
      primary_category_id: categoryId
    })
    uni.showToast({ title: '已设为主分类', icon: 'success' })
  } catch (error: any) {
    primaryCategoryId.value = prev
    logger.error('system', '设置主分类失败', {
      roomId: props.roomId,
      categoryId,
      message: error?.message || String(error)
    })
    uni.showToast({ title: '设置失败，请稍后重试', icon: 'none' })
  }
}

// 移除单个分类
async function removeCategory(categoryId: string) {
  logger.info('user', '移除直播间科室', {
    roomId: props.roomId,
    categoryId
  })
  const newIds = selectedIds.value.filter(id => id !== categoryId)
  const nextPrimary =
    primaryCategoryId.value === categoryId ? (newIds[0] || '') : primaryCategoryId.value
  try {
    const api = resolveCategoryApi()
    // 走 replace 一次性同步主分类，避免 DELETE 后主分类悬空
    await api.setRoomCategories(props.roomId, {
      category_ids: newIds,
      mode: 'replace',
      primary_category_id: nextPrimary || undefined
    })
    selectedIds.value = newIds
    primaryCategoryId.value = nextPrimary
    logger.info('network', '直播间科室移除成功', {
      roomId: props.roomId,
      categoryId,
      remainingIds: selectedIds.value,
      primaryCategoryId: nextPrimary
    })
    uni.showToast({ title: '已移除', icon: 'success' })
  } catch (error: any) {
    logger.error('system', '移除直播间科室失败', {
      roomId: props.roomId,
      categoryId,
      message: error?.message || String(error)
    })
    uni.showToast({ title: '移除失败，请稍后重试', icon: 'none' })
  }
}

onMounted(() => {
  logger.info('system', '进入直播间科室选择', { roomId: props.roomId })
  loadData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.room-category-selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.selector-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .header-title {
    font-size: 16px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .header-tag {
    padding: 2px 8px;
    background-color: var(--color-bg-secondary);
    border-radius: var(--border-radius-sm);

    .tag-text {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
  }
}

.selector-body {
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 40px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
  cursor: pointer;

  &:active {
    border-color: var(--color-primary);
  }
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.preview-tag {
  padding: 4px 8px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);

  .preview-tag-text {
    font-size: 12px;
    color: var(--color-text-primary);
  }
}

.preview-more {
  .more-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.placeholder-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.select-arrow {
  .arrow-icon {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);

  .tag-name {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  .tag-primary {
    padding: 0 4px;
    border-radius: 2px;
    background-color: var(--color-primary);

    .primary-text {
      font-size: 11px;
      color: #ffffff;
    }
  }

  .tag-set-primary {
    padding: 0 4px;

    .set-primary-text {
      font-size: 11px;
      color: var(--color-primary);
    }
  }

  .tag-close {
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    .close-icon {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
  }
}

.primary-hint {
  width: 100%;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.picker-container {
  width: 90%;
  max-width: 500px;
  max-height: 70vh;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);

  .picker-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .picker-close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    .close-icon {
      font-size: 18px;
      color: var(--color-text-secondary);
    }
  }
}

.picker-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.picker-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: var(--spacing-md);

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.picker-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.picker-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  &:active {
    background-color: var(--color-bg-secondary);
  }

  &.is-selected {
    background-color: #e6f7ff;
  }
}

.item-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  flex-shrink: 0;

  .icon-image {
    width: 100%;
    height: 100%;
  }

  .icon-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }
}

.item-name {
  flex: 1;
  font-size: 14px;
  color: var(--color-text-primary);
}

.item-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;

  .check-icon {
    font-size: 16px;
    color: var(--color-primary);
    font-weight: 600;
  }
}

.picker-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.picker-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 16px;
    color: #ffffff;
    font-weight: 500;
  }
}
</style>
