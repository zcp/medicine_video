<!--
 * RoomTabManager - 直播间Tab管理组件
 * @description 嵌入直播间编辑页，管理该直播间的所有Tab
 * @requires uni-app + Vue 3 + TypeScript
 -->
<template>
  <view class="tab-manager">
    <!-- 标题栏 -->
    <view class="tab-manager__header">
      <text class="tab-manager__title">Tab 管理</text>
      <view class="tab-manager__add-btn" @tap="handleAdd">
        <text class="tab-manager__add-text">+ 新增Tab</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <LoadingIndicator v-if="loading" text="加载Tab列表..." />

    <!-- 错误状态 -->
    <ErrorBanner
      v-else-if="error"
      :message="error"
      @close="error = null"
    />

    <!-- 空状态 -->
    <EmptyState
      v-else-if="tabs.length === 0"
      title="暂无Tab"
      description="点击上方按钮新增Tab"
    />

    <!-- Tab列表 -->
    <view v-else class="tab-manager__list">
      <view
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-card"
      >
        <!-- Tab信息 -->
        <view class="tab-card__info">
          <view class="tab-card__title-row">
            <text class="tab-card__title">{{ tab.title }}</text>
            <view
              :class="['tab-card__status', tab.is_active ? 'status-active' : 'status-inactive']"
            >
              <text class="tab-card__status-text">
                {{ tab.is_active ? '启用' : '禁用' }}
              </text>
            </view>
          </view>
          <text v-if="tab.text_content" class="tab-card__content">
            {{ truncateText(tab.text_content, 60) }}
          </text>
          <image
            v-if="tab.image_url"
            class="tab-card__image"
            :src="resolveMediaUrl(tab.image_url)"
            mode="aspectFill"
            @error="handleImageError(tab)"
          />
        </view>

        <!-- 操作按钮 -->
        <view class="tab-card__actions">
          <view class="action-btn action-btn--edit" @tap="handleEdit(tab)">
            <text class="action-btn__text">编辑</text>
          </view>
          <view class="action-btn action-btn--delete" @tap="handleDelete(tab)">
            <text class="action-btn__text">删除</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 编辑弹窗 -->
    <TabEditDialog
      v-if="showEditDialog"
      :tab="editingTab"
      :room-id="roomId"
      @close="showEditDialog = false"
      @saved="handleSaved"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTabs, deleteTab } from '@/api/tabs'
import type { LiveRoomTab } from '@/api/tabs'
import { resolveMediaUrl } from '@/utils/url'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TabEditDialog from './TabEditDialog.vue'

/**
 * 组件Props
 */
const props = defineProps<{
  /** 房间ID */
  roomId: string
}>()

/** Tab列表 */
const tabs = ref<LiveRoomTab[]>([])
/** 加载状态 */
const loading = ref(false)
/** 错误信息 */
const error = ref<string | null>(null)
/** 是否显示编辑弹窗 */
const showEditDialog = ref(false)
/** 当前编辑的Tab（null表示新增） */
const editingTab = ref<LiveRoomTab | null>(null)

/**
 * 加载Tab列表
 */
async function loadTabs() {
  if (!props.roomId) return
  loading.value = true
  error.value = null
  try {
    const res = await getTabs(props.roomId)
    const items = res.data?.items ?? []
    tabs.value = items.sort((a, b) => a.sort_order - b.sort_order)
  } catch (e: any) {
    error.value = e?.message || '加载Tab列表失败'
  } finally {
    loading.value = false
  }
}

/**
 * 截断文本
 */
function truncateText(text: string, maxLen: number): string {
  if (!text) return ''
  return text.length > maxLen ? `${text.slice(0, maxLen)}...` : text
}

/**
 * 处理图片加载失败
 */
function handleImageError(tab: LiveRoomTab) {
  console.warn('[TabManager] Tab图片加载失败', { tabId: tab.id, image_url: tab.image_url })
}

/**
 * 新增Tab
 */
function handleAdd() {
  editingTab.value = null
  showEditDialog.value = true
}

/**
 * 编辑Tab
 */
function handleEdit(tab: LiveRoomTab) {
  editingTab.value = { ...tab }
  showEditDialog.value = true
}

/**
 * 删除Tab
 */
function handleDelete(tab: LiveRoomTab) {
  uni.showModal({
    title: '确认删除',
    content: `确定删除Tab「${tab.title}」吗？`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteTab(tab.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
          await loadTabs()
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

/**
 * 弹窗保存回调
 */
async function handleSaved() {
  showEditDialog.value = false
  await loadTabs()
}

onMounted(() => {
  loadTabs()
})
</script>

<style lang="scss" scoped>
.tab-manager {
  padding: 16rpx 0;
}

.tab-manager__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.tab-manager__title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tab-manager__add-btn {
  padding: 12rpx 24rpx;
  background-color: var(--color-primary);
  border-radius: 8rpx;
}

.tab-manager__add-text {
  font-size: 26rpx;
  color: #ffffff;
}

.tab-manager__list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.tab-card {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 20rpx;
  background-color: var(--color-bg-primary);
  border-radius: 12rpx;
  border: 1rpx solid var(--color-border);
}

.tab-card__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tab-card__title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.tab-card__title {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--color-text-primary);
}

.tab-card__status {
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.status-active {
  background-color: #f6ffed;
  .tab-card__status-text { color: #52c41a; }
}

.status-inactive {
  background-color: #fff7e6;
  .tab-card__status-text { color: #fa8c16; }
}

.tab-card__status-text {
  font-size: 22rpx;
}

.tab-card__content {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
  word-break: break-word;
}

.tab-card__image {
  width: 200rpx;
  height: 120rpx;
  border-radius: 8rpx;
  margin-top: 8rpx;
}

.tab-card__actions {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex-shrink: 0;
}

.action-btn {
  padding: 8rpx 16rpx;
  border-radius: 6rpx;
}

.action-btn--edit {
  background-color: #e6f7ff;
  .action-btn__text { color: #1890ff; }
}

.action-btn--delete {
  background-color: #fff2f0;
  .action-btn__text { color: #ff4d4f; }
}

.action-btn__text {
  font-size: 22rpx;
}
</style>
