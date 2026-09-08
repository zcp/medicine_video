# 直播间Tab管理（Live Room Tabs）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **平台**：微信小程序
> **后端表**：`live_room_tabs`
> **后端设计文档版本**：V1.1（2026-06-08）

---

## 一、功能概述

直播间Tab是直播间详情页内的自定义内容板块。管理员可以为每个直播间配置多个Tab（如"科室介绍"、"专家团队"、"资料下载"等），每个Tab支持三种内容类型（纯文本 / 纯图片 / 图文混排）。前端需要实现：

1. **管理端**：在直播间编辑页内嵌Tab管理（CRUD + 图片上传 + 批量排序）
2. **用户端**：直播间详情页内以Tab切换形式展示（仅激活的Tab）

后端共提供 7 个 API 端点，权限分为管理员端（JWT+Admin）和公开端（Public）。

---

## 二、目录结构

```
src/
├── api/
│   ├── tabs.ts                 # Tab 管理端 API 封装（已有）
│   └── room-tabs.ts            # Tab 公开接口封装（已有）
├── types/
│   └── room.ts                 # Tab 类型定义（已有，Tab/RoomTab 接口）
├── config/
│   └── api.ts                  # API_PATHS 统一路径配置（已有）
├── pages/
│   ├── admin/
│   │   └── roomTab/
│   │       ├── RoomTabManager.vue      # 管理端Tab管理组件（嵌入直播间编辑页）
│   │       └── TabEditDialog.vue       # Tab 新增/编辑弹窗
│   └── live/
│       └── LiveView.vue                # 用户端Tab展示（已集成，消费功能性Tab）
└── components/
    └── common/
        ├── EmptyState.vue              # 空状态组件（已有）
        ├── LoadingIndicator.vue        # 加载指示器（已有）
        └── ErrorBanner.vue             # 错误提示横幅（已有）
```

---

## 三、类型定义

### 3.1 后端 DDL 对应关系（V1.1）

| 列名 | 类型 | 约束 | TypeScript 类型 |
|---|---|---|---|
| `id` | UUID | PK | `string` |
| `room_id` | UUID | FK CASCADE | `string` |
| `tab_key` | VARCHAR(64) | NOT NULL | `string` |
| `title` | VARCHAR(128) | NOT NULL | `string` |
| `content_type` | ENUM('text','image','mixed') | NOT NULL | `'text' \| 'image' \| 'mixed'` |
| `text_content` | TEXT | 可选 | `string \| null` |
| `image_url` | TEXT | 可选 | `string \| null` |
| `sort_order` | INTEGER | DEFAULT 0 | `number` |
| `is_active` | BOOLEAN | DEFAULT TRUE | `boolean` |
| `created_at` | TIMESTAMPTZ | 自动 | `string` |
| `updated_at` | TIMESTAMPTZ | 自动 | `string` |

**⚠️ 关键变更（V1.1 vs V1.0）**：
- ✅ 新增 `tab_key`：系统级标识符，前端用 `tab_key` 而非 `title` 做逻辑匹配
- ✅ 新增 `content_type`：枚举类型，决定前端渲染分支
- ✅ `content` → `text_content`：字段重命名
- ✅ `title` 长度：200 → 128
- ✅ `image_url` 类型：VARCHAR(500) → TEXT

### 3.2 类型文件

类型已定义在 `src/api/tabs.ts` 和 `src/types/room.ts` 中，**禁止重复定义**。

```typescript
// src/api/tabs.ts — 管理端类型

/**
 * Tab内容类型枚举（对应后端 live_room_tab_content_type）
 */
export type LiveRoomTabContentType = 'text' | 'image' | 'mixed'

/**
 * 直播间Tab项（对应后端 LiveRoomTabItem Schema）
 */
export interface LiveRoomTab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: LiveRoomTabContentType
  text_content?: string | null
  image_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 创建Tab请求（对应后端 LiveRoomTabCreate Schema）
 */
export interface LiveRoomTabCreate {
  tab_key: string
  title: string
  content_type: LiveRoomTabContentType
  text_content?: string
  image_url?: string
  sort_order?: number
  is_active?: boolean
}

/**
 * 更新Tab请求（对应后端 LiveRoomTabUpdate Schema）
 * 所有字段可选，部分更新
 */
export interface LiveRoomTabUpdate {
  tab_key?: string
  title?: string
  content_type?: LiveRoomTabContentType
  text_content?: string
  image_url?: string
  sort_order?: number
  is_active?: boolean
}

/**
 * 批量排序请求（对应后端 LiveRoomTabSortRequest Schema）
 */
export interface LiveRoomTabSortRequest {
  tab_ids: string[]
}
```

```typescript
// src/types/room.ts — 用户端复用类型

/**
 * Tab数据结构（对应后端 LiveRoomTabItem Schema）
 */
export interface Tab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: 'text' | 'image' | 'mixed'
  text_content?: string | null
  image_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 兼容别名：历史代码中使用 RoomTab
 */
export type RoomTab = Tab
```

---

## 四、API 封装

### 4.1 管理端 API（`src/api/tabs.ts`）

所有管理端接口需要 JWT + Admin 权限。

```typescript
// src/api/tabs.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  LiveRoomTab,
  LiveRoomTabCreate,
  LiveRoomTabUpdate,
  LiveRoomTabSortRequest
} from '@/api/tabs'

/**
 * 获取直播间的所有Tab（含禁用）
 * GET /api/v1/admin/rooms/{roomId}/tabs
 */
export const getTabs = (roomId: string): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ADMIN.ROOM_TABS(roomId), { showError: false })
}

/**
 * 创建Tab
 * POST /api/v1/admin/rooms/{roomId}/tabs
 */
export const createTab = (
  roomId: string,
  data: LiveRoomTabCreate
): Promise<ApiResponse<LiveRoomTab>> => {
  return request.post(API_PATHS.ADMIN.CREATE_TAB(roomId), data, {
    loading: true,
    loadingText: '创建中...'
  })
}

/**
 * 更新Tab（部分更新）
 * PATCH /api/v1/admin/tabs/{tabId}
 */
export const updateTab = (
  tabId: string,
  data: LiveRoomTabUpdate
): Promise<ApiResponse<LiveRoomTab>> => {
  return request.patch(API_PATHS.ADMIN.UPDATE_TAB(tabId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

/**
 * 删除Tab
 * DELETE /api/v1/admin/tabs/{tabId}
 */
export const deleteTab = (tabId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.ADMIN.DELETE_TAB(tabId), {
    loading: true,
    loadingText: '删除中...'
  })
}

/**
 * 上传Tab图片（multipart/form-data，最大 2MB，支持 jpg/png/webp）
 * POST /api/v1/admin/rooms/{roomId}/tabs/image
 */
export const uploadTabImage = (
  roomId: string,
  formData: FormData
): Promise<ApiResponse<{ image_url: string }>> => {
  return request.post(API_PATHS.ADMIN.UPLOAD_TAB_IMAGE(roomId), formData, {
    loading: true,
    loadingText: '上传中...'
  })
}

/**
 * 批量排序Tab
 * PATCH /api/v1/admin/rooms/{roomId}/tabs/sort
 */
export const sortTabs = (
  roomId: string,
  data: LiveRoomTabSortRequest
): Promise<ApiResponse<null>> => {
  return request.patch(API_PATHS.ADMIN.SORT_TABS(roomId), data, {
    loading: true,
    loadingText: '排序中...'
  })
}

/**
 * 获取直播间公开Tab列表（仅is_active=true）
 * GET /api/v1/rooms/{roomId}/tabs
 */
export const getPublicTabs = (
  roomId: string
): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { auth: false, showError: false })
}

export default {
  getTabs,
  createTab,
  updateTab,
  deleteTab,
  uploadTabImage,
  sortTabs,
  getPublicTabs
}
```

### 4.2 公开 API（`src/api/room-tabs.ts`）

```typescript
// src/api/room-tabs.ts（已有，保持不变）

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type { LiveRoomTab } from '@/api/tabs'

/**
 * 获取直播间公开Tab列表（仅is_active=true）
 * GET /api/v1/rooms/{roomId}/tabs
 */
export const getRoomTabs = (
  roomId: string
): Promise<ApiResponse<{ items: LiveRoomTab[] }>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { auth: false, showError: false })
}

export default {
  getRoomTabs
}
```

---

## 五、config/api.ts 路径配置

路径已定义在 `src/config/api.ts` 中，**禁止重复定义**。以下为完整映射：

| 端点 | HTTP 方法 | API_PATHS 调用 | 基础URL |
|---|---|---|---|
| 管理端列表（含禁用） | GET | `API_PATHS.ADMIN.ROOM_TABS(roomId)` | core |
| 创建Tab | POST | `API_PATHS.ADMIN.CREATE_TAB(roomId)` | core |
| 更新Tab | PATCH | `API_PATHS.ADMIN.UPDATE_TAB(tabId)` | core |
| 删除Tab | DELETE | `API_PATHS.ADMIN.DELETE_TAB(tabId)` | core |
| 上传图片 | POST | `API_PATHS.ADMIN.UPLOAD_TAB_IMAGE(roomId)` | core |
| 批量排序 | PATCH | `API_PATHS.ADMIN.SORT_TABS(roomId)` | core |
| 公开列表 | GET | `API_PATHS.ROOM.TABS(roomId)` | core |

对应 `src/config/api.ts` 中的路径定义：

```typescript
// ADMIN 模块
ROOM_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs`
CREATE_TAB: (roomId: string) => `/admin/rooms/${roomId}/tabs`
UPDATE_TAB: (tabId: string) => `/admin/tabs/${tabId}`
DELETE_TAB: (tabId: string) => `/admin/tabs/${tabId}`
UPLOAD_TAB_IMAGE: (roomId: string) => `/admin/rooms/${roomId}/tabs/image`
SORT_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs/sort`

// ROOM 模块
TABS: (roomId: string) => `/rooms/${roomId}/tabs`
```

---

## 六、管理端页面

### 6.1 RoomTabManager.vue — Tab 管理组件

嵌入直播间编辑页，提供 Tab 的增删改查、图片上传和排序功能。

```vue
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
        v-for="(tab, index) in tabs"
        :key="tab.id"
        class="tab-card"
      >
        <!-- 排序手柄 -->
        <view class="tab-card__sort">
          <view
            class="sort-btn"
            :class="{ 'sort-btn--disabled': index === 0 }"
            @tap="handleMoveUp(index)"
          >
            <text class="sort-btn__text">↑</text>
          </view>
          <view
            class="sort-btn"
            :class="{ 'sort-btn--disabled': index === tabs.length - 1 }"
            @tap="handleMoveDown(index)"
          >
            <text class="sort-btn__text">↓</text>
          </view>
        </view>

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
            :src="tab.image_url"
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
import { getTabs, deleteTab, sortTabs } from '@/api/tabs'
import type { LiveRoomTab, LiveRoomTabSortRequest } from '@/api/tabs'
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
 * 上移Tab
 */
async function handleMoveUp(index: number) {
  if (index <= 0) return
  const newList = [...tabs.value]
  const temp = newList[index]
  newList[index] = newList[index - 1]
  newList[index - 1] = temp
  await persistSortOrder(newList)
}

/**
 * 下移Tab
 */
async function handleMoveDown(index: number) {
  if (index >= tabs.value.length - 1) return
  const newList = [...tabs.value]
  const temp = newList[index]
  newList[index] = newList[index + 1]
  newList[index + 1] = temp
  await persistSortOrder(newList)
}

/**
 * 持久化排序（调用后端专用排序端点）
 */
async function persistSortOrder(orderedTabs: LiveRoomTab[]) {
  const data: LiveRoomTabSortRequest = {
    tab_ids: orderedTabs.map(t => t.id)
  }
  try {
    await sortTabs(props.roomId, data)
    tabs.value = orderedTabs
    uni.showToast({ title: '排序已保存', icon: 'success' })
  } catch {
    uni.showToast({ title: '排序保存失败', icon: 'none' })
    await loadTabs()
  }
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

.tab-card__sort {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex-shrink: 0;
}

.sort-btn {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-secondary);
  border-radius: 8rpx;

  &--disabled {
    opacity: 0.3;
  }
}

.sort-btn__text {
  font-size: 24rpx;
  color: var(--color-text-primary);
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
```

### 6.2 TabEditDialog.vue — Tab 新增/编辑弹窗

```vue
<!--
 * TabEditDialog - Tab新增/编辑弹窗
 * @description 支持新增和编辑Tab，所有Tab均支持图文内容
 -->
<template>
  <view class="dialog-overlay" @click="handleClose">
    <view class="dialog" @click.stop>
      <view class="dialog__header">
        <text class="dialog__title">{{ isEdit ? '编辑Tab' : '新增Tab' }}</text>
        <view class="dialog__close" @click="handleClose">
          <text class="dialog__close-text">✕</text>
        </view>
      </view>

      <view class="dialog__body">
        <!-- tab_key -->
        <view class="field">
          <text class="field__label"><text class="required">*</text>Tab标识</text>
          <input
            class="field__input"
            :class="{ 'field__input--disabled': isEdit }"
            v-model="form.tab_key"
            :disabled="isEdit"
            placeholder="如 intro、agenda、speakers"
            maxlength="64"
          />
          <text class="field__hint">{{ isEdit ? '创建后不可修改' : '用于区分Tab的唯一标识，如 intro（不可含空格）' }}</text>
        </view>

        <!-- 标题 -->
        <view class="field">
          <text class="field__label"><text class="required">*</text>标题</text>
          <input
            class="field__input"
            v-model="form.title"
            placeholder="请输入Tab标题"
            maxlength="128"
          />
          <text class="field__count">{{ form.title.length }}/128</text>
        </view>

        <!-- 文字内容 -->
        <view class="field">
          <text class="field__label">文字内容</text>
          <textarea
            class="field__textarea"
            v-model="form.text_content"
            placeholder="请输入文本内容"
            :maxlength="50000"
          />
        </view>

        <!-- 配图 -->
        <view class="field">
          <text class="field__label">配图</text>
          <view class="field__image-area">
            <image
              v-if="imagePreviewUrl"
              class="field__image"
              :src="imagePreviewUrl"
              mode="aspectFill"
            />
            <view v-else class="field__image-placeholder">
              <text class="field__image-placeholder-text">未上传图片</text>
            </view>
          </view>
          <view class="field__image-actions">
            <view class="ghost-btn" @click="handlePickImage">
              <text class="ghost-btn__text">选择图片</text>
            </view>
            <view v-if="form.image_url" class="ghost-btn ghost-btn--danger" @click="handleClearImage">
              <text class="ghost-btn__text">删除图片</text>
            </view>
          </view>
          <text class="field__hint">支持 jpg/png/webp，最大 2MB</text>
        </view>

        <!-- 排序 -->
        <view class="field">
          <text class="field__label">排序权重</text>
          <input
            class="field__input"
            v-model.number="form.sort_order"
            type="number"
            placeholder="0"
          />
          <text class="field__hint">数值越小越靠前</text>
        </view>

        <!-- 启用状态 -->
        <view class="field field--switch">
          <text class="field__label">启用</text>
          <view
            :class="['switch', form.is_active ? 'switch--on' : 'switch--off']"
            @click="form.is_active = !form.is_active"
          >
            <view class="switch__thumb" />
          </view>
        </view>
      </view>

      <view class="dialog__footer">
        <view class="ghost-btn" @click="handleClose">
          <text class="ghost-btn__text">取消</text>
        </view>
        <view class="primary-btn" :class="{ 'primary-btn--disabled': saving }" @click="handleSave">
          <text class="primary-btn__text">{{ saving ? '保存中...' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { createTab, updateTab, uploadTabImage } from '@/api/tabs'
import type { LiveRoomTab, LiveRoomTabContentType, LiveRoomTabCreate, LiveRoomTabUpdate } from '@/api/tabs'

/**
 * 组件Props
 */
const props = defineProps<{
  /** 编辑的Tab（null表示新增） */
  tab: LiveRoomTab | null
  /** 房间ID */
  roomId: string
}>()

/**
 * 组件Emits
 */
const emit = defineEmits<{
  close: []
  saved: []
}>()

/** 是否编辑模式 */
const isEdit = computed(() => !!props.tab)

/** 表单数据 */
const form = ref({
  tab_key: '',
  title: '',
  content_type: 'mixed' as LiveRoomTabContentType,
  text_content: '',
  image_url: '',
  sort_order: 0,
  is_active: true
})

/** 图片预览URL */
const imagePreviewUrl = computed(() => form.value.image_url || '')

/** 保存中 */
const saving = ref(false)

/**
 * 初始化表单
 */
onMounted(() => {
  if (props.tab) {
    form.value = {
      tab_key: props.tab.tab_key || '',
      title: props.tab.title || '',
      content_type: 'mixed',
      text_content: props.tab.text_content || '',
      image_url: props.tab.image_url || '',
      sort_order: props.tab.sort_order ?? 0,
      is_active: props.tab.is_active !== false
    }
  }
})

/**
 * 选择图片并上传
 */
async function handlePickImage() {
  try {
    const res = await new Promise<UniApp.ChooseImageSuccessCallbackResult>((resolve, reject) => {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: resolve,
        fail: reject
      })
    })

    const filePath = res.tempFilePaths[0]
    if (!filePath) return

    // 校验文件大小（2MB）
    const fileInfo = await new Promise<UniApp.GetFileInfoSuccessCallbackResult>((resolve, reject) => {
      uni.getFileInfo({
        filePath,
        success: resolve,
        fail: reject
      })
    })
    if (fileInfo.size > 2 * 1024 * 1024) {
      uni.showToast({ title: '图片不能超过2MB', icon: 'none' })
      return
    }

    // 上传到后端
    saving.value = true
    const uploadRes = await uploadTabImage(props.roomId, filePath)
    const imageUrl = uploadRes.data?.image_url
    if (imageUrl) {
      form.value.image_url = imageUrl
      uni.showToast({ title: '图片上传成功', icon: 'success' })
    }
  } catch {
    uni.showToast({ title: '图片上传失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

/**
 * 清除图片
 */
function handleClearImage() {
  form.value.image_url = ''
}

/**
 * 关闭弹窗
 */
function handleClose() {
  emit('close')
}

/**
 * 保存
 */
async function handleSave() {
  // 校验
  const tabKey = form.value.tab_key.trim()
  const title = form.value.title.trim()
  if (!tabKey) {
    uni.showToast({ title: '请输入Tab标识', icon: 'none' })
    return
  }
  if (/\s/.test(tabKey)) {
    uni.showToast({ title: 'Tab标识不可包含空格', icon: 'none' })
    return
  }
  if (!title) {
    uni.showToast({ title: '请输入Tab标题', icon: 'none' })
    return
  }

  saving.value = true
  try {
    if (isEdit.value && props.tab) {
      // 更新（部分更新，只发有值的字段）
      const data: LiveRoomTabUpdate = {
        tab_key: tabKey,
        title,
        content_type: 'mixed',
        text_content: form.value.text_content || undefined,
        image_url: form.value.image_url || undefined,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active
      }
      await updateTab(props.tab.id, data)
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      // 创建
      const data: LiveRoomTabCreate = {
        tab_key: tabKey,
        title,
        content_type: 'mixed',
        text_content: form.value.text_content || undefined,
        image_url: form.value.image_url || undefined,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active
      }
      await createTab(props.roomId, data)
      uni.showToast({ title: '创建成功', icon: 'success' })
    }
    emit('saved')
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 32rpx;
}

.dialog {
  width: 100%;
  max-height: 80vh;
  background-color: var(--color-bg-primary);
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid var(--color-border);
}

.dialog__title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog__close {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog__close-text {
  font-size: 32rpx;
  color: var(--color-text-secondary);
}

.dialog__body {
  flex: 1;
  overflow-y: auto;
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.field--switch {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.field__label {
  font-size: 26rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.required {
  color: #ff4d4f;
  margin-right: 4rpx;
}

.field__input {
  height: 72rpx;
  padding: 0 20rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
  font-size: 28rpx;
  background-color: var(--color-bg-secondary);
}

.field__textarea {
  min-height: 200rpx;
  padding: 16rpx 20rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
  font-size: 28rpx;
  background-color: var(--color-bg-secondary);
}

.field__count {
  font-size: 22rpx;
  color: var(--color-text-tertiary);
  text-align: right;
}

.field__hint {
  font-size: 22rpx;
  color: var(--color-text-tertiary);
}

.field__image-area {
  width: 300rpx;
  height: 180rpx;
  border-radius: 8rpx;
  overflow: hidden;
}

.field__image {
  width: 100%;
  height: 100%;
}

.field__image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-secondary);
  border: 1rpx dashed var(--color-border);
}

.field__image-placeholder-text {
  font-size: 24rpx;
  color: var(--color-text-tertiary);
}

.field__image-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 8rpx;
}

.ghost-btn {
  padding: 12rpx 24rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
}

.ghost-btn--danger {
  border-color: #ff4d4f;
  .ghost-btn__text { color: #ff4d4f; }
}

.ghost-btn__text {
  font-size: 24rpx;
  color: var(--color-text-primary);
}

.switch {
  width: 88rpx;
  height: 48rpx;
  border-radius: 24rpx;
  position: relative;
  transition: background-color 0.2s;
}

.switch--on {
  background-color: var(--color-primary);
  .switch__thumb { transform: translateX(40rpx); }
}

.switch--off {
  background-color: var(--color-border);
}

.switch__thumb {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background-color: #ffffff;
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  transition: transform 0.2s;
}

.dialog__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16rpx;
  padding: 20rpx 32rpx;
  border-top: 1rpx solid var(--color-border);
}

.primary-btn {
  padding: 16rpx 32rpx;
  background-color: var(--color-primary);
  border-radius: 8rpx;

  &--disabled {
    opacity: 0.5;
  }
}

.primary-btn__text {
  font-size: 28rpx;
  color: #ffffff;
}
</style>
```

---

## 七、用户端页面/组件

用户端 Tab 展示已集成在 `src/pages/live/LiveView.vue` 中。以下为关键对接逻辑说明。

### 7.1 数据来源

用户端 Tab 数据来源有两条路径（优先级从高到低）：

1. **房间详情接口** `GET /api/v1/rooms/{roomId}` 响应中的 `data.tabs` 数组
2. **公开Tab接口** `GET /api/v1/rooms/{roomId}/tabs`（仅 `is_active=true`）

### 7.2 Tab 渲染规则

```typescript
// LiveView.vue 中的核心逻辑

// 1. 加载Tab列表
const roomFunctionalTabs = ref<RoomFunctionalTab[]>([])

// 2. 过滤 + 排序
const baseTabs = effectiveTabs
  .filter(t => t.is_active !== false)          // 仅显示启用的Tab
  .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))  // 按 sort_order 升序

// 3. Tab 匹配：使用 tab_key 而非 title 做逻辑判断
// - 系统级Tab（intro / agenda / 留言等）通过 tab_key === 'intro' 匹配
// - 自定义Tab通过 tab_key 或 id 做唯一标识

// 4. Tab 内容渲染：根据 content_type 分支
// - content_type === 'text'：渲染 text_content 纯文本
// - content_type === 'image'：渲染 image_url 纯图片
// - content_type === 'mixed'：渲染 text_content + image_url 图文混排
// - 三者都没有：显示"暂无内容"
```

### 7.3 Tab 切换与留言集成

留言区作为特殊 Tab 始终注入到 Tab 列表末尾（`tab_key` 固定为 `message`，`title` 固定为 `留言`），与其他功能性 Tab 统一管理。

---

## 八、行动清单

### 8.1 类型定义修改（src/api/tabs.ts）

- [ ] **A1** 新增 `LiveRoomTabContentType` 类型：`export type LiveRoomTabContentType = 'text' | 'image' | 'mixed'`
- [ ] **A2** `LiveRoomTab` 接口新增字段：`tab_key: string`、`content_type: LiveRoomTabContentType`、`text_content?: string | null`；移除 `content` 字段
- [ ] **A3** `LiveRoomTabCreate` 接口新增必填字段：`tab_key: string`、`content_type: LiveRoomTabContentType`；新增可选字段：`text_content?: string`、`image_url?: string`；移除 `content` 字段
- [ ] **A4** `LiveRoomTabUpdate` 接口新增可选字段：`tab_key?: string`、`content_type?: LiveRoomTabContentType`、`text_content?: string`；移除 `content` 字段

### 8.2 类型定义修改（src/types/room.ts）

- [ ] **A5** `Tab` 接口新增字段：`tab_key: string`、`content_type: 'text' | 'image' | 'mixed'`、`text_content?: string | null`；移除 `content` 字段
- [ ] **A6** `RoomTab` 别名保持不变（自动跟随 `Tab`）

### 8.3 管理端页面修改（src/pages/admin/roomTab/RoomTabManager.vue）

- [ ] **A7** Tab 卡片模板：去掉 `tab_key` 标签和 `content_type` 标签，只保留标题 + 启用/禁用状态
- [ ] **A8** Tab 卡片模板：`tab.content` → `tab.text_content`（文本截断展示）
- [ ] **A9** 移除 `contentTypeLabel()` 辅助函数和 `LiveRoomTabContentType` import

### 8.4 管理端弹窗修改（src/pages/admin/roomTab/TabEditDialog.vue）

- [ ] **A10** 表单新增 `tab_key` 输入框（必填，maxlength=64，校验不含空格）
- [ ] **A11** 去掉 `content_type` 单选组，`content_type` 固定为 `'mixed'`
- [ ] **A12** `text_content` textarea 和图片上传区域始终显示（不再根据 content_type 条件显示）
- [ ] **A13** 标题 maxlength 从 200 改为 128
- [ ] **A14** 文字区域标签改为"文字内容"，图片区域标签改为"配图"
- [ ] **A15** 表单初始化：读取 `tab.tab_key`、`tab.text_content`，`content_type` 固定为 `'mixed'`
- [ ] **A16** 保存逻辑：`content_type` 固定传 `'mixed'`
- [ ] **A17** 校验逻辑：`tab_key` 必填且不含空格

### 8.5 用户端页面修改（src/pages/live/LiveView.vue）

- [ ] **A20** `RoomFunctionalTab` 类型扩展：确认包含 `tab_key`、`content_type`、`text_content` 字段
- [ ] **A21** Tab 匹配逻辑：`currentTabKey` 匹配从 `tab.title` 改为 `tab.tab_key`
- [ ] **A22** 系统级 Tab 常量：从 title 匹配改为 tab_key 匹配（如 `ROOM_INTRO_TAB_TITLE = '简介'` → `ROOM_INTRO_TAB_KEY = 'intro'`）
- [ ] **A23** Tab 内容渲染：根据 `content_type` 分支渲染（text → text_content，image → image_url，mixed → 两者都渲染）
- [ ] **A24** 字段回退兼容：`loadRoomFunctionalTabs` 中保留 `text_content` 回退到 `content`/`textContent` 的兼容逻辑

### 8.6 API 封装与路径配置

- [ ] **A25** `src/api/tabs.ts` 中的函数签名无需修改（类型自动跟随接口变更）
- [ ] **A26** `src/api/room-tabs.ts` 无需修改（复用 `LiveRoomTab` 类型）
- [ ] **A27** `src/config/api.ts` 路径无需修改（7 个端点路径不变）

---

## 九、自测清单

### 9.1 类型编译检查

- [ ] **T1** `npm run type-check` 通过，无 TypeScript 编译错误
- [ ] **T2** `LiveRoomTab`、`LiveRoomTabCreate`、`LiveRoomTabUpdate`、`Tab` 四个接口均包含 `tab_key`、`content_type`、`text_content` 字段
- [ ] **T3** 以上接口均不包含已废弃的 `content` 字段
- [ ] **T4** `LiveRoomTabContentType` 类型为 `'text' | 'image' | 'mixed'`

### 9.2 管理端 — RoomTabManager

- [ ] **T5** Tab 卡片不显示 `tab_key` 和 `content_type` 标签，只显示标题 + 启用/禁用状态
- [ ] **T6** Tab 卡片文本截断使用 `text_content` 字段（非 `content`）
- [ ] **T7** 排序（上移/下移）功能正常，调用 `PATCH /admin/rooms/{roomId}/tabs/sort`
- [ ] **T8** 删除功能正常，弹出确认弹窗后调用 `DELETE /admin/tabs/{tabId}`

### 9.3 管理端 — TabEditDialog

- [ ] **T9** 新增模式：表单包含 `tab_key`、`title`、`text_content`、`image_url`、`sort_order`、`is_active` 共 6 个可见字段（`content_type` 固定为 `'mixed'`，不显示选择器）
- [ ] **T10** `tab_key` 输入框校验：为空时提示"请输入Tab标识"，含空格时提示"Tab标识不可包含空格"
- [ ] **T11** 编辑弹窗中 `text_content` textarea 和图片上传区域始终同时显示（无条件判断）
- [ ] **T12** 文字区域标签显示为"文字内容"，图片区域标签显示为"配图"
- [ ] **T13** 标题输入框 maxlength 为 128，计数器显示 `x/128`
- [ ] **T14** 编辑模式：表单正确回填 `tab_key`、`text_content`、`image_url` 等字段
- [ ] **T15** 创建请求体 `content_type` 固定为 `'mixed'`（POST `/admin/rooms/{roomId}/tabs`）
- [ ] **T16** 更新请求体 `content_type` 固定为 `'mixed'`（PATCH `/admin/tabs/{tabId}`）
- [ ] **T17** 图片上传：选择 >2MB 图片时提示"图片不能超过2MB"
- [ ] **T18** 图片上传成功后 `image_url` 字段回填到表单

### 9.4 用户端 — LiveView

- [ ] **T21** Tab 列表从后端获取后，按 `sort_order` 升序排列
- [ ] **T22** Tab 匹配使用 `tab_key` 而非 `title`（修改 `currentTabKey` 赋值逻辑）
- [ ] **T23** `content_type === 'text'` 的 Tab：正确渲染 `text_content` 纯文本
- [ ] **T24** `content_type === 'image'` 的 Tab：正确渲染 `image_url` 纯图片
- [ ] **T25** `content_type === 'mixed'` 的 Tab：正确渲染 `text_content` + `image_url` 图文混排
- [ ] **T26** 留言 Tab 始终注入在列表末尾（`tab_key === 'message'`）
- [ ] **T27** 仅 `is_active === true` 的 Tab 在用户端显示

### 9.5 API 链路验证

- [ ] **T28** `GET /api/v1/admin/rooms/{roomId}/tabs` 返回的 Tab 对象包含 `tab_key`、`content_type`、`text_content` 字段
- [ ] **T29** `POST /api/v1/admin/rooms/{roomId}/tabs` 请求体包含 `tab_key`、`content_type`、`text_content`
- [ ] **T30** `PATCH /api/v1/admin/tabs/{tabId}` 请求体支持 `tab_key`、`content_type`、`text_content` 部分更新
- [ ] **T31** `GET /api/v1/rooms/{roomId}/tabs` 返回的 Tab 对象包含 `tab_key`、`content_type`、`text_content` 字段
- [ ] **T32** `PATCH /api/v1/admin/rooms/{roomId}/tabs/sort` 排序后重新加载列表，顺序正确

### 9.6 边界与异常

- [ ] **T33** `tab_key` 重复时后端返回 400/409 错误，前端正确提示
- [ ] **T34** `text_content` 超长时后端返回 422 错误，前端正确提示
- [ ] **T35** 空 Tab 列表时显示 EmptyState 组件
- [ ] **T36** 网络请求失败时显示 ErrorBanner 组件
- [ ] **T37** 图片加载失败时 console.warn 输出日志，不阻断页面

---

## 十、API 链路总结

```
管理端（JWT+Admin）:
┌──────────────────────────────────────────────────────────────────────┐
│  GET    /admin/rooms/{roomId}/tabs          → API_PATHS.ADMIN.ROOM_TABS(roomId)
│  POST   /admin/rooms/{roomId}/tabs          → API_PATHS.ADMIN.CREATE_TAB(roomId)
│  PATCH  /admin/tabs/{tabId}                 → API_PATHS.ADMIN.UPDATE_TAB(tabId)
│  DELETE /admin/tabs/{tabId}                 → API_PATHS.ADMIN.DELETE_TAB(tabId)
│  POST   /admin/rooms/{roomId}/tabs/image    → API_PATHS.ADMIN.UPLOAD_TAB_IMAGE(roomId)
│  PATCH  /admin/rooms/{roomId}/tabs/sort     → API_PATHS.ADMIN.SORT_TABS(roomId)
└──────────────────────────────────────────────────────────────────────┘

用户端（Public）:
┌──────────────────────────────────────────────────────────────────────┐
│  GET    /rooms/{roomId}/tabs                → API_PATHS.ROOM.TABS(roomId)
└──────────────────────────────────────────────────────────────────────┘

前端消费方:
┌──────────────────────────────────────────────────────────────────────┐
│  src/api/tabs.ts         → 管理端 API 封装（getTabs/createTab/updateTab/...）
│  src/api/room-tabs.ts    → 公开 API 封装（getRoomTabs）
│  src/pages/live/LiveView.vue → 用户端 Tab 展示（消费 room.tabs 或公开接口）
│  src/pages/admin/roomTab/    → 管理端 Tab CRUD 页面
└──────────────────────────────────────────────────────────────────────┘
```

---

## 十一、后端对接确认清单

| # | 确认项 | 状态 | 说明 |
|---|---|---|---|
| 1 | `tab_key` 是否全局唯一或仅房间内唯一 | ⬜ 待确认 | 影响前端重复校验逻辑 |
| 2 | `content_type` 枚举值是否固定为 `text/image/mixed` | ✅ 已确认 | 后端 DDL 定义 `live_room_tab_content_type` |
| 3 | `text_content` 最大长度 | ⬜ 待确认 | 后端 Schema 未标注 max_length |
| 4 | `image_url` 返回的是相对路径还是完整 URL | ✅ 已确认 | 返回相对路径 `/uploads/tabs/uuid.ext` |
| 5 | 图片上传支持的格式 | ✅ 已确认 | jpg, png, webp，最大 2MB |
| 6 | 删除行为 | ✅ 已确认 | 软删除（`is_active = false`） |

---

**文档结束** ✅
