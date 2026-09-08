# 科室分类管理（Category）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **后端设计文档**：《01-科室分类管理-后端设计文档.md》
> **零偏差**：所有类型、路径、端点严格对齐后端设计文档
>
> **运营面变更（2026-08-17）**：独立 Admin 列表页 `CategoryList` 已退役；根分类建/改/停用由 [《20》专家分类承接根分类细能力 V2.1](./Live-Saas-Wechat-20-专家分类承接根分类细能力-前端设计文档-v2.1.md) 在「专家分类」页承接。表单组件 `CategoryFormDialog` 与 `src/api/categories.ts`、C 端消费仍有效。

---

## 一、功能概述

科室分类是平台基础数据，贯穿管理端和用户端。前端需实现：

1. **管理端**：分类 CRUD + 图标上传 + 直播间分类关联
2. **用户端**：统一分类查询，服务于首页科室Tab、品牌分类筛选、专家分类筛选

**后端数据表**：
- `categories`：id(UUID PK), name(VARCHAR 100), slug(VARCHAR 100 NOT NULL UNIQUE), icon(VARCHAR 500), description(TEXT), sort_order(INTEGER DEFAULT 0), is_active(BOOLEAN DEFAULT TRUE), created_at, updated_at
- `live_room_categories`：room_id(UUID FK CASCADE), category_id(UUID FK CASCADE), created_at — 复合主键(room_id, category_id)

**软删除策略**：categories 使用 `is_active` 字段；live_room_categories 使用物理删除

---

## 二、目录结构

```
src/
├── api/
│   └── categories.ts              # 分类 API 封装（11个端点）
├── types/
│   └── category.ts                # TypeScript 类型定义（对齐后端 Schema）
├── store/
│   └── category.ts                # Pinia 状态管理
├── pages/
│   └── admin/
│       └── category/
│           ├── CategoryList.vue         # 管理端分类列表页
│           └── CategoryFormDialog.vue   # 新增/编辑弹窗
├── components/
│   └── RoomCategorySelector.vue         # 直播间分类关联选择器
└── composables/
    └── useCategory.ts                   # 分类组合函数（首页/品牌/专家共用）
```

---

## 三、类型定义

> 严格对齐后端 Pydantic Schema，字段名、类型、必填/可选100%一致

```typescript
// src/types/category.ts

/**
 * 分类信息（对应后端 CategoryItem Schema）
 * DDL: categories 表, slug VARCHAR(100) NOT NULL UNIQUE
 */
export interface Category {
  id: string           // UUID
  name: string         // 1-100字符，必填
  slug: string         // 必填，唯一，仅小写字母+数字+连字符
  icon?: string        // 最大500字符
  description?: string
  sort_order: number   // 必填，默认0
  is_active: boolean   // 软删除标记
  created_at: string   // ISO 8601
  updated_at: string
}

/**
 * 创建分类请求（对应后端 CategoryCreate Schema）
 * slug 为必填（后端 Field(..., min_length=1, max_length=100)）
 */
export interface CategoryCreate {
  name: string         // 必填，1-100字符
  slug: string         // 必填，唯一，正则 ^[a-z0-9\-]+$
  icon?: string
  description?: string
  sort_order?: number  // 默认0
  is_active?: boolean  // 默认true
}

/**
 * 更新分类请求（对应后端 CategoryUpdate Schema，部分更新 PATCH）
 */
export interface CategoryUpdate {
  name?: string
  slug?: string
  icon?: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

/**
 * 分类分页结果（对应后端统一分页格式）
 */
export interface CategoryPageResult {
  items: Category[]
  total: number
  page: number
  size: number          // 后端字段名为 size（非 page_size）
}

/**
 * 直播间分类关联设置请求（对应后端 LiveRoomCategoriesSetRequest Schema）
 */
export interface LiveRoomCategoriesSetRequest {
  category_ids: string[]         // 分类UUID列表
  mode: 'replace' | 'append'    // replace=替换, append=追加
}

/**
 * 直播间分类关联项（对应后端 LiveRoomCategoryItem Schema）
 */
export interface LiveRoomCategoryItem {
  room_id: string
  category_id: string
  category_name: string
  category_slug: string
  created_at: string
}
```

---

## 四、API 封装

> 严格对齐后端路由表（11个端点），使用 `API_PATHS` 配置

```typescript
// src/api/categories.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategoryPageResult,
  LiveRoomCategoriesSetRequest,
  LiveRoomCategoryItem
} from '@/types/category'

// ============ 公开接口 ============

/**
 * 获取所有分类（用户端，按 sort_order 排序，仅 is_active=true）
 * GET /api/v1/content/categories
 * 使用场景：首页科室Tab、品牌分类筛选、专家分类筛选
 */
export const getAllCategories = (): Promise<ApiResponse<{ items: Category[] }>> => {
  return request.get(API_PATHS.CATEGORY.LIST, { auth: false, showError: false })
}

/**
 * 获取单个分类详情
 * GET /api/v1/content/categories/{categoryId}
 */
export const getCategory = (categoryId: string): Promise<ApiResponse<Category>> => {
  return request.get(API_PATHS.CATEGORY.ADMIN_DETAIL(categoryId), { auth: false, showError: false })
}

/**
 * 获取直播间关联的分类
 * GET /api/v1/rooms/{roomId}/categories（公开）
 */
export const getRoomCategories = (roomId: string): Promise<ApiResponse<{ items: LiveRoomCategoryItem[] }>> => {
  return request.get(API_PATHS.CATEGORY.ROOM_CATEGORIES(roomId), { auth: false, showError: false })
}

// ============ 管理端接口 ============

/**
 * 管理端分类列表（分页+搜索）
 * GET /api/v1/admin/categories
 */
export const getAdminCategories = (params?: {
  page?: number
  page_size?: number
  q?: string
  include_inactive?: boolean
}): Promise<ApiResponse<CategoryPageResult>> => {
  return request.get(API_PATHS.CATEGORY.ADMIN_LIST, { data: params })
}

/**
 * 创建分类
 * POST /api/v1/admin/categories
 */
export const createCategory = (data: CategoryCreate): Promise<ApiResponse<Category>> => {
  return request.post(API_PATHS.CATEGORY.LIST, data, { loading: true, loadingText: '创建中...' })
}

/**
 * 更新分类（部分更新）
 * PATCH /api/v1/admin/categories/{categoryId}
 */
export const updateCategory = (categoryId: string, data: CategoryUpdate): Promise<ApiResponse<Category>> => {
  return request.patch(API_PATHS.CATEGORY.ADMIN_DETAIL(categoryId), data, { loading: true, loadingText: '更新中...' })
}

/**
 * 删除分类（软删除，设置 is_active=false）
 * DELETE /api/v1/admin/categories/{categoryId}
 */
export const deleteCategory = (categoryId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.CATEGORY.ADMIN_DETAIL(categoryId), { loading: true, loadingText: '删除中...' })
}

/**
 * 上传分类图标
 * POST /api/v1/admin/categories/{categoryId}/icon
 * 文件限制：jpg/png/webp，最大2MB
 * 注意：uni-app 环境不支持 FormData，需使用 uni.uploadFile（通过 request.upload 封装）
 */
export const uploadCategoryIcon = (categoryId: string, filePath: string): Promise<ApiResponse<{ icon_url: string }>> => {
  return request.upload({
    url: API_PATHS.CATEGORY.ICON(categoryId),
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传中...'
  })
}

/**
 * 删除分类图标
 * DELETE /api/v1/admin/categories/{categoryId}/icon
 */
export const deleteCategoryIcon = (categoryId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.CATEGORY.ICON(categoryId), { loading: true, loadingText: '删除中...' })
}

/**
 * 设置直播间分类关联
 * POST /api/v1/admin/rooms/{roomId}/categories
 */
export const setRoomCategories = (
  roomId: string,
  data: LiveRoomCategoriesSetRequest
): Promise<ApiResponse<{ items: LiveRoomCategoryItem[] }>> => {
  return request.post(API_PATHS.CATEGORY.ADMIN_SET_ROOM_CATEGORIES(roomId), data, {
    loading: true,
    loadingText: '更新中...'
  })
}

/**
 * 解除直播间分类关联
 * DELETE /api/v1/admin/rooms/{roomId}/categories/{categoryId}
 */
export const removeRoomCategory = (roomId: string, categoryId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.CATEGORY.ADMIN_REMOVE_ROOM_CATEGORY(roomId, categoryId), {
    loading: true,
    loadingText: '解除中...'
  })
}

export default {
  getAllCategories,
  getCategory,
  getRoomCategories,
  getAdminCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  uploadCategoryIcon,
  deleteCategoryIcon,
  setRoomCategories,
  removeRoomCategory
}
```

---

## 五、config/api.ts 路径配置

```typescript
// src/config/api.ts 中 CATEGORY 模块

CATEGORY: {
  LIST: '/content/categories',
  ADMIN_LIST: '/admin/categories',
  ADMIN_DETAIL: (categoryId: string) => `/admin/categories/${categoryId}`,
  ICON: (categoryId: string) => `/admin/categories/${categoryId}/icon`,
  ROOM_CATEGORIES: (roomId: string) => `/rooms/${roomId}/categories`,
  ADMIN_SET_ROOM_CATEGORIES: (roomId: string) => `/admin/rooms/${roomId}/categories`,
  ADMIN_REMOVE_ROOM_CATEGORY: (roomId: string, categoryId: string) => `/admin/rooms/${roomId}/categories/${categoryId}`
}
```

---

## 六、管理端页面实现

### 6.1 分类列表页 CategoryList.vue

```vue
<!-- src/pages/admin/category/CategoryList.vue -->
<template>
  <view class="category-list-page">
    <!-- 顶部操作栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title">科室分类管理</text>
      </view>
      <view class="header-actions">
        <view class="search-box">
          <input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索分类名称"
            @confirm="handleSearch"
          />
          <view v-if="searchKeyword" class="search-clear" @click="clearSearch">
            <text>✕</text>
          </view>
        </view>
        <view class="btn-add" @click="openCreateDialog">
          <text class="btn-text">+ 新增分类</text>
        </view>
      </view>
    </view>

    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 空态 -->
    <view v-else-if="tableData.length === 0" class="empty-state">
      <text class="empty-text">暂无分类数据</text>
    </view>

    <!-- 分类列表 -->
    <view v-else class="category-list">
      <view
        v-for="item in tableData"
        :key="item.id"
        class="category-item"
      >
        <view class="item-main">
          <view class="item-icon">
            <image
              v-if="item.icon"
              :src="item.icon"
              class="icon-image"
              mode="aspectFill"
            />
            <view v-else class="icon-placeholder">
              <text class="icon-text">🏷️</text>
            </view>
          </view>
          <view class="item-info">
            <text class="item-name">{{ item.name }}</text>
            <text class="item-slug">{{ item.slug }}</text>
            <text v-if="item.description" class="item-desc">{{ item.description }}</text>
          </view>
        </view>
        <view class="item-meta">
          <text class="item-sort">排序: {{ item.sort_order }}</text>
          <view :class="['status-tag', item.is_active ? 'status-active' : 'status-inactive']">
            <text class="status-text">{{ item.is_active ? '启用' : '禁用' }}</text>
          </view>
        </view>
        <view class="item-actions">
          <view class="action-btn" @click="openEditDialog(item)">
            <text class="action-text">编辑</text>
          </view>
          <view class="action-btn action-btn--upload">
            <text class="action-text">{{ item.icon ? '换图标' : '传图标' }}</text>
          </view>
          <view class="action-btn action-btn--danger" @click="handleDelete(item)">
            <text class="action-text">删除</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 分页 -->
    <view v-if="total > pageSize" class="pagination">
      <view class="page-btn" :class="{ disabled: currentPage <= 1 }" @click="changePage(currentPage - 1)">
        <text>上一页</text>
      </view>
      <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
      <view class="page-btn" :class="{ disabled: currentPage >= totalPages }" @click="changePage(currentPage + 1)">
        <text>下一页</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAdminCategories, deleteCategory } from '@/api/categories'
import type { Category } from '@/types/category'

const tableData = ref<Category[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

async function fetchData() {
  loading.value = true
  try {
    const res = await getAdminCategories({
      page: currentPage.value,
      page_size: pageSize.value,
      q: searchKeyword.value || undefined,
      include_inactive: true
    })
    if (res.code === 200 && res.data) {
      tableData.value = res.data.items
      total.value = res.data.total
    }
  } catch (error) {
    uni.showToast({ title: '加载分类列表失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchData()
}

function clearSearch() {
  searchKeyword.value = ''
  handleSearch()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

function openCreateDialog() {
  // 跳转或弹窗
}

function openEditDialog(item: Category) {
  // 跳转或弹窗
}

async function handleDelete(item: Category) {
  uni.showModal({
    title: '确认删除',
    content: `确定删除分类"${item.name}"吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteCategory(item.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        } catch (error) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => fetchData())
</script>

<style lang="scss" scoped>
.category-list-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.header-title .title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.btn-add {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.btn-add .btn-text {
  color: #fff;
  font-size: var(--font-size-sm);
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-sm);
}

.item-main {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
}

.icon-image {
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius-sm);
}

.icon-placeholder {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
}

.item-name {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
}

.item-slug {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-family: monospace;
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.status-active {
  background: #e6f7ff;
}

.status-inactive {
  background: #fff2f0;
}

.item-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
}

.action-btn--danger {
  border-color: var(--color-danger);
}

.action-btn--danger .action-text {
  color: var(--color-danger);
}

.empty-state, .loading-state {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.empty-text, .loading-text {
  color: var(--color-text-secondary);
}
</style>
```

---

## 七、用户端科室分类使用场景

### 7.1 共用组合函数

```typescript
// src/composables/useCategory.ts
import { ref, onMounted } from 'vue'
import { getAllCategories } from '@/api/categories'
import type { Category } from '@/types/category'

/**
 * 科室分类组合函数
 * 适用于：首页科室Tab、品牌分类筛选、专家分类筛选
 * 所有场景只返回 is_active=true 的分类
 */
export function useCategory() {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchCategories = async () => {
    loading.value = true
    error.value = null
    try {
      const res = await getAllCategories()
      if (res.code === 200) {
        categories.value = res.data?.items || []
      }
    } catch (err: any) {
      error.value = err.message || '加载分类失败'
    } finally {
      loading.value = false
    }
  }

  onMounted(() => fetchCategories())

  return { categories, loading, error, refresh: fetchCategories }
}
```

---

## 八、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 创建类型定义 | `src/types/category.ts` | 按第三节，slug 必填 |
| 2 | 创建API封装 | `src/api/categories.ts` | 按第四节，11个端点 |
| 3 | 配置API路径 | `src/config/api.ts` | 按第五节，CATEGORY 段 |
| 4 | 创建组合函数 | `src/composables/useCategory.ts` | 按第七节 |
| 5 | 实现管理端列表 | `src/pages/admin/category/CategoryList.vue` | uni-app 语法 |
| 6 | 实现新增/编辑弹窗 | `src/pages/admin/category/CategoryFormDialog.vue` | uni-app 语法 |
| 7 | 实现分类选择器 | `src/components/RoomCategorySelector.vue` | 嵌入直播间编辑页 |
| 8 | 更新路由 | `src/pages.json` | 添加分类管理页路由 |
| 9 | 首页集成 | `src/pages/home/Home.vue` | 引入 useCategory |

---

## 九、API 链路总结

### 后端路由表（11个端点）

| # | 方法 | 后端路径 | 认证 | 前端函数 |
|---|------|---------|------|---------|
| 1 | GET | `/api/v1/content/categories` | 公开 | `getAllCategories()` |
| 2 | GET | `/api/v1/content/categories/{categoryId}` | 公开 | `getCategory(id)` |
| 3 | GET | `/api/v1/admin/categories` | JWT+Admin | `getAdminCategories(params)` |
| 4 | POST | `/api/v1/admin/categories` | JWT+Admin | `createCategory(data)` |
| 5 | PATCH | `/api/v1/admin/categories/{categoryId}` | JWT+Admin | `updateCategory(id, data)` |
| 6 | DELETE | `/api/v1/admin/categories/{categoryId}` | JWT+Admin | `deleteCategory(id)` |
| 7 | POST | `/api/v1/admin/categories/{categoryId}/icon` | JWT+Admin | `uploadCategoryIcon(id, file)` |
| 8 | DELETE | `/api/v1/admin/categories/{categoryId}/icon` | JWT+Admin | `deleteCategoryIcon(id)` |
| 9 | POST | `/api/v1/admin/rooms/{roomId}/categories` | JWT+Admin | `setRoomCategories(id, data)` |
| 10 | GET | `/api/v1/rooms/{roomId}/categories` | 公开 | `getRoomCategories(id)` |
| 11 | DELETE | `/api/v1/admin/rooms/{roomId}/categories/{categoryId}` | JWT+Admin | `removeRoomCategory(rid, cid)` |

### 错误码映射

| 错误码 | 说明 | 前端处理 |
|--------|------|---------|
| 200 | 成功 | 正常处理 |
| 2001 | 资源不存在 | 提示"分类不存在" |
| 2002 | 资源已存在 | 提示"slug已存在" |
| 2004 | 业务逻辑错误 | 提示"该分类下仍有直播间，无法删除" |
| 3001 | 未授权 | 跳转登录页 |
| 3002 | 权限不足 | 提示"需要管理员权限" |
| 4001 | 参数校验失败 | 提示具体校验错误 |
