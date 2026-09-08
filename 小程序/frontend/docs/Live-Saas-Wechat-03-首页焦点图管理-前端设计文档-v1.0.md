# 首页焦点图管理（Featured Content）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **后端设计文档**：《03-首页焦点图管理-后端设计文档.md》
> **零偏差**：所有类型、路径、端点严格对齐后端设计文档

---

## 一、功能概述

焦点图（Featured Content）是首页顶部的轮播图，用于推广直播间、专题、品牌、外部链接等。前端需要实现：

1. **管理端**：焦点图 CRUD + 图片上传（jpg/png/webp, max 5MB）+ 跳转目标配置 + 定时上下线
2. **用户端**：首页轮播展示 + 点击跳转逻辑

**后端数据表**：
- `featured_content`：id(UUID PK), title(VARCHAR 200 NOT NULL), subtitle(VARCHAR 500), image_url(VARCHAR 500 NOT NULL), target_type(VARCHAR NOT NULL CHECK room/session/topic/brand/external), target_id(UUID), target_url(VARCHAR 1000), sort_order(INTEGER DEFAULT 0), is_active(BOOLEAN DEFAULT TRUE), start_at(TIMESTAMPTZ), end_at(TIMESTAMPTZ), created_at, updated_at

**约束**：external 类型必须有 target_url；非 external 类型必须有 target_id

**软删除策略**：featured_content 使用 `is_active` 字段

**API 端点清单（7个）**：

| # | 方法 | 路径 | 权限 | 说明 |
|---|------|------|------|------|
| 1 | GET | /featured-content | 公开 | 首页焦点图列表（仅启用+在有效期内） |
| 2 | GET | /admin/featured-content | JWT+Admin | 管理端分页列表（含未启用） |
| 3 | GET | /admin/featured-content/{contentId} | JWT+Admin | 焦点图详情 |
| 4 | POST | /admin/featured-content | JWT+Admin | 创建焦点图 |
| 5 | PATCH | /admin/featured-content/{contentId} | JWT+Admin | 部分更新焦点图 |
| 6 | DELETE | /admin/featured-content/{contentId} | JWT+Admin | 删除焦点图（软删除） |
| 7 | POST | /admin/featured-content/{contentId}/image | JWT+Admin | 上传图片（jpg/png/webp, max 5MB） |

---

## 二、目录结构

```
src/
├── api/
│   └── featuredContent.ts         # 焦点图 API 封装（7个端点）
├── types/
│   └── featuredContent.ts         # TypeScript 类型定义（对齐后端 Schema）
├── pages/
│   ├── admin/
│   │   └── featuredContent/
│   │       ├── FeaturedContentList.vue        # 管理端焦点图列表页
│   │       └── FeaturedContentFormDialog.vue  # 新增/编辑弹窗
│   └── user/
│       └── home/
│           └── BannerCarousel.vue             # 首页轮播组件
└── components/
    └── TargetSelector.vue                     # 跳转目标选择器
```

---

## 三、类型定义

> 严格对齐后端 Pydantic Schema，字段名、类型、必填/可选 100% 一致

```typescript
// src/types/featuredContent.ts

/**
 * 首页焦点图管理（Featured Content）类型定义
 * 以后端设计文档为准：featured_content 表 DDL + Pydantic Schema
 *
 * DDL: featured_content 表
 *   id UUID PK, title VARCHAR(200), subtitle VARCHAR(500), image_url VARCHAR(500),
 *   target_type VARCHAR(20) CHECK (room/session/topic/brand/external),
 *   target_id UUID, target_url VARCHAR(1000),
 *   sort_order INTEGER, is_active BOOLEAN,
 *   start_at TIMESTAMPTZ, end_at TIMESTAMPTZ,
 *   created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
 *
 * 约束: external类型必须有target_url, 非external类型必须有target_id
 */

/**
 * 焦点图跳转目标类型
 * 后端 CHECK 约束: 'room' | 'session' | 'topic' | 'brand' | 'external'
 */
export type FeaturedContentTargetType = 'room' | 'session' | 'topic' | 'brand' | 'external'

/**
 * 焦点图信息（对应后端 FeaturedContentItem Schema）
 */
export interface FeaturedContent {
  /** 焦点图唯一标识（UUID） */
  id: string
  /** 焦点图标题（最大200字符） */
  title: string
  /** 焦点图副标题（最大500字符） */
  subtitle?: string
  /** 图片URL路径 */
  image_url: string
  /** 跳转目标类型（必填） */
  target_type: FeaturedContentTargetType
  /** 目标资源ID（external类型时为null） */
  target_id: string | null
  /** 外部链接URL（仅target_type=external时使用） */
  target_url: string | null
  /** 排序权重（升序，0最前） */
  sort_order: number
  /** 是否启用状态（软删除标记） */
  is_active: boolean
  /** 展示开始时间（ISO 8601格式） */
  start_at: string | null
  /** 展示结束时间（ISO 8601格式） */
  end_at: string | null
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 最后更新时间（ISO 8601格式） */
  updated_at: string
}

/**
 * 创建焦点图请求参数（对应后端 FeaturedContentCreate Schema）
 * target_type 为必填，无 cta_text 字段
 */
export interface FeaturedContentCreate {
  /** 焦点图标题（必填） */
  title: string
  /** 焦点图副标题（可选） */
  subtitle?: string
  /** 图片URL路径（必填） */
  image_url: string
  /** 跳转目标类型（必填） */
  target_type: FeaturedContentTargetType
  /** 目标资源ID（非external时必填） */
  target_id?: string | null
  /** 外部链接URL（external时必填） */
  target_url?: string | null
  /** 排序权重（可选，默认0） */
  sort_order?: number
  /** 是否启用状态（可选，默认true） */
  is_active?: boolean
  /** 展示开始时间（可选） */
  start_at?: string | null
  /** 展示结束时间（可选） */
  end_at?: string | null
}

/**
 * 更新焦点图请求参数（对应后端 FeaturedContentUpdate Schema，PATCH 部分更新）
 * 全部字段可选
 */
export interface FeaturedContentUpdate {
  /** 焦点图标题（可选） */
  title?: string
  /** 焦点图副标题（可选） */
  subtitle?: string
  /** 图片URL路径（可选） */
  image_url?: string
  /** 跳转目标类型（可选） */
  target_type?: FeaturedContentTargetType
  /** 目标资源ID（可选） */
  target_id?: string | null
  /** 外部链接URL（可选） */
  target_url?: string | null
  /** 排序权重（可选） */
  sort_order?: number
  /** 是否启用状态（可选） */
  is_active?: boolean
  /** 展示开始时间（可选） */
  start_at?: string | null
  /** 展示结束时间（可选） */
  end_at?: string | null
}
```

---

## 四、API 封装

> 使用 `request.get/post/patch/delete` from `@/utils/request`
> 响应类型统一为 `ApiResponse<T>` from `@/types/common`
> 路径统一使用 `API_PATHS` from `@/config/api`

```typescript
// src/api/featuredContent.ts

/**
 * 首页焦点图管理 API
 * 以后端设计文档为准：《03-首页焦点图管理-后端设计文档.md》
 *
 * 端点清单（7个）:
 *   GET /featured-content              公开列表（最多10条，is_active=true）
 *   GET /admin/featured-content        管理端分页列表（JWT+Admin）
 *   GET /admin/featured-content/{id}   管理端详情（JWT+Admin）
 *   POST /admin/featured-content       创建（JWT+Admin）
 *   PATCH /admin/featured-content/{id} 部分更新（JWT+Admin）
 *   DELETE /admin/featured-content/{id}软删除（JWT+Admin）
 *   POST /admin/featured-content/{id}/image  上传图片（JWT+Admin）
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  FeaturedContent,
  FeaturedContentCreate,
  FeaturedContentUpdate
} from '@/types/featuredContent'

// ============ 公开接口 ============

/**
 * 获取首页焦点图列表（公开，最多10条active数据）
 * GET /api/v1/featured-content
 */
export const getFeaturedContent = (params?: {
  limit?: number
}): Promise<ApiResponse<{ items: FeaturedContent[] }>> => {
  return request.get(API_PATHS.CONTENT.FEATURED_CONTENT, { data: params, auth: false })
}

// ============ 管理端接口 ============

/**
 * 管理端焦点图分页列表（含已禁用）
 * GET /api/v1/admin/featured-content
 */
export const getAdminFeaturedContent = (params?: {
  page?: number
  page_size?: number
}): Promise<ApiResponse<{ total: number; page: number; size: number; items: FeaturedContent[] }>> => {
  return request.get(API_PATHS.ADMIN.FEATURED_CONTENT, { data: params })
}

/**
 * 获取单个焦点图详情
 * GET /api/v1/admin/featured-content/{contentId}
 */
export const getFeaturedContentDetail = (contentId: string): Promise<ApiResponse<FeaturedContent>> => {
  return request.get(API_PATHS.ADMIN.UPDATE_FEATURED(contentId))
}

/**
 * 创建焦点图
 * POST /api/v1/admin/featured-content
 */
export const createFeaturedContent = (data: FeaturedContentCreate): Promise<ApiResponse<FeaturedContent>> => {
  return request.post(API_PATHS.ADMIN.CREATE_FEATURED, data, {
    loading: true,
    loadingText: '创建中...'
  })
}

/**
 * 更新焦点图（部分更新）
 * PATCH /api/v1/admin/featured-content/{contentId}
 */
export const updateFeaturedContent = (
  contentId: string,
  data: FeaturedContentUpdate
): Promise<ApiResponse<FeaturedContent>> => {
  return request.patch(API_PATHS.ADMIN.UPDATE_FEATURED(contentId), data, {
    loading: true,
    loadingText: '更新中...'
  })
}

/**
 * 删除焦点图（软删除）
 * DELETE /api/v1/admin/featured-content/{contentId}
 */
export const deleteFeaturedContent = (contentId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.ADMIN.DELETE_FEATURED(contentId), {
    loading: true,
    loadingText: '删除中...'
  })
}

/**
 * 上传焦点图图片
 * POST /api/v1/admin/featured-content/{contentId}/image
 * 限制：jpg/png/webp，最大5MB
 */
export const uploadFeaturedContentImage = (
  contentId: string,
  file: File
): Promise<ApiResponse<{ image_url: string }>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(API_PATHS.ADMIN.UPLOAD_FEATURED_IMAGE(contentId), formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    loading: true,
    loadingText: '上传中...'
  })
}

export default {
  getFeaturedContent,
  getAdminFeaturedContent,
  getFeaturedContentDetail,
  createFeaturedContent,
  updateFeaturedContent,
  deleteFeaturedContent,
  uploadFeaturedContentImage
}
```

---

## 五、config/api.ts 路径配置

> 已存在于 `src/config/api.ts`，此处记录完整路径映射关系

```typescript
// src/config/api.ts 中已配置的焦点图相关路径

// 内容管理（公开接口）
CONTENT: {
  // ...
  FEATURED_CONTENT: '/featured-content',   // GET 公开
}

// 管理员接口（焦点图管理）
ADMIN: {
  // ...
  FEATURED_CONTENT: '/admin/featured-content',                                     // GET 分页列表
  CREATE_FEATURED: '/admin/featured-content',                                      // POST 创建
  UPDATE_FEATURED: (contentId: string) => `/admin/featured-content/${contentId}`,  // GET/PATCH 详情/更新
  DELETE_FEATURED: (contentId: string) => `/admin/featured-content/${contentId}`,  // DELETE 删除
  UPLOAD_FEATURED_IMAGE: (contentId: string) => `/admin/featured-content/${contentId}/image`,  // POST 上传图片
}
```

**7个端点与 API_PATHS 对应关系**：

| # | 端点 | 使用的 API_PATHS |
|---|------|-----------------|
| 1 | GET /featured-content | `API_PATHS.CONTENT.FEATURED_CONTENT` |
| 2 | GET /admin/featured-content | `API_PATHS.ADMIN.FEATURED_CONTENT` |
| 3 | GET /admin/featured-content/{contentId} | `API_PATHS.ADMIN.UPDATE_FEATURED(contentId)` |
| 4 | POST /admin/featured-content | `API_PATHS.ADMIN.CREATE_FEATURED` |
| 5 | PATCH /admin/featured-content/{contentId} | `API_PATHS.ADMIN.UPDATE_FEATURED(contentId)` |
| 6 | DELETE /admin/featured-content/{contentId} | `API_PATHS.ADMIN.DELETE_FEATURED(contentId)` |
| 7 | POST /admin/featured-content/{contentId}/image | `API_PATHS.ADMIN.UPLOAD_FEATURED_IMAGE(contentId)` |

---

## 六、管理端页面实现

### 6.1 FeaturedContentList.vue

> 焦点图管理列表页，包含新增、编辑、换图、删除功能
> 每个页面包含 loading/error/empty 三种状态

```vue
<!--
 * FeaturedContentList - 焦点图管理列表页
 * @description 管理端焦点图的增删改查页面
 -->
<template>
  <view class="featured-content-list-page">
    <!-- 顶部操作栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title">焦点图管理</text>
      </view>
      <view class="header-actions">
        <view class="btn-add" @click="openCreateDialog">
          <text class="btn-text">+ 新增焦点图</text>
        </view>
      </view>
    </view>

    <!-- 焦点图列表 -->
    <view class="content-list" v-if="!loading">
      <view v-if="tableData.length === 0" class="empty-state">
        <text class="empty-text">暂无焦点图数据</text>
      </view>

      <view
        v-for="item in tableData"
        :key="item.id"
        class="content-item"
      >
        <!-- 图片预览 -->
        <view class="item-image">
          <image
            v-if="item.image_url"
            :src="item.image_url"
            class="cover-image"
            mode="aspectFill"
          />
          <view v-else class="image-placeholder">
            <text class="placeholder-text">🖼️</text>
          </view>
        </view>

        <!-- 内容信息 -->
        <view class="item-info">
          <view class="item-title-row">
            <text class="item-title">{{ item.title }}</text>
            <view :class="['status-tag', item.is_active ? 'status-active' : 'status-inactive']">
              <text class="status-text">{{ item.is_active ? '启用' : '禁用' }}</text>
            </view>
          </view>

          <!-- 跳转目标 -->
          <view class="item-target">
            <view v-if="item.target_type" class="target-info">
              <view class="target-type-tag">
                <text class="target-type-text">{{ targetTypeLabel(item.target_type) }}</text>
              </view>
              <text v-if="item.target_url" class="target-url">{{ item.target_url }}</text>
              <text v-else-if="item.target_id" class="target-id">{{ item.target_id }}</text>
            </view>
            <text v-else class="target-none">纯展示</text>
          </view>

          <!-- 元信息 -->
          <view class="item-meta">
            <text class="meta-text">排序: {{ item.sort_order }}</text>
            <view v-if="item.start_at || item.end_at" class="date-range">
              <text class="meta-text">{{ item.start_at ? formatDate(item.start_at) : '不限' }} ~ {{ item.end_at ? formatDate(item.end_at) : '不限' }}</text>
            </view>
            <text v-else class="meta-text">永久有效</text>
          </view>
        </view>

        <!-- 操作按钮 -->
        <view class="item-actions">
          <view class="action-btn btn-edit" @click="openEditDialog(item)">
            <text class="btn-text">编辑</text>
          </view>
          <view class="action-btn btn-image" @click="handleUploadImage(item)">
            <text class="btn-text">换图</text>
          </view>
          <view class="action-btn btn-delete" @click="handleDelete(item)">
            <text class="btn-text">删除</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-else class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 分页 -->
    <view class="pagination-wrapper" v-if="total > 0">
      <view class="pagination">
        <view
          :class="['page-btn', currentPage <= 1 ? 'disabled' : '']"
          @click="changePage(currentPage - 1)"
        >
          <text class="page-btn-text">上一页</text>
        </view>
        <view class="page-info">
          <text class="page-text">{{ currentPage }} / {{ totalPages }}</text>
        </view>
        <view
          :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']"
          @click="changePage(currentPage + 1)"
        >
          <text class="page-btn-text">下一页</text>
        </view>
      </view>
    </view>

    <!-- 新增/编辑弹窗 -->
    <FeaturedContentFormDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="currentItem"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import {
  getAdminFeaturedContent,
  deleteFeaturedContent,
  uploadFeaturedContentImage
} from '@/api/featuredContent'
import type { FeaturedContent, FeaturedContentTargetType } from '@/types/featuredContent'
import FeaturedContentFormDialog from './FeaturedContentFormDialog.vue'

// 表格数据
const tableData = ref<FeaturedContent[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 弹窗状态
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentItem = ref<FeaturedContent | null>(null)

// 计算总页数
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 跳转类型映射
const targetTypeMap: Record<FeaturedContentTargetType, string> = {
  room: '直播间',
  session: '场次',
  topic: '专题',
  brand: '品牌',
  external: '外部链接'
}

/** 跳转类型显示文本 */
function targetTypeLabel(type: FeaturedContentTargetType): string {
  return targetTypeMap[type] || type
}

/** 格式化日期 */
function formatDate(iso: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 获取数据 */
async function fetchData() {
  loading.value = true
  try {
    logger.info('network', '加载管理端焦点图列表', {
      page: currentPage.value,
      page_size: pageSize.value
    })
    const res = await getAdminFeaturedContent({
      page: currentPage.value,
      page_size: pageSize.value
    })
    tableData.value = res.data?.items || []
    total.value = res.data?.total || 0
    logger.info('network', '管理端焦点图列表加载完成', {
      total: res.data?.total,
      page: res.data?.page,
      page_size: res.data?.size,
      count: tableData.value.length
    })
  } catch (error) {
    logger.error('system', '加载管理端焦点图列表失败', error)
    uni.showToast({ title: '加载焦点图列表失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 切换页码 */
function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

/** 打开新增弹窗 */
function openCreateDialog() {
  logger.info('user', '打开新增焦点图弹窗')
  dialogMode.value = 'create'
  currentItem.value = null
  dialogVisible.value = true
}

/** 打开编辑弹窗 */
function openEditDialog(item: FeaturedContent) {
  logger.info('user', '打开编辑焦点图弹窗', { id: item.id, title: item.title })
  dialogMode.value = 'edit'
  currentItem.value = { ...item }
  dialogVisible.value = true
}

/** 上传图片 */
function handleUploadImage(item: FeaturedContent) {
  logger.info('user', '发起焦点图图片上传', { id: item.id })
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const file = res.tempFiles[0]
      logger.info('network', '选择焦点图图片文件', {
        contentId: item.id,
        fileName: file?.name,
        fileSize: file?.size
      })
      try {
        await uploadFeaturedContentImage(item.id, file as any)
        logger.info('network', '焦点图图片上传完成', { contentId: item.id })
        uni.showToast({ title: '图片上传成功', icon: 'success' })
        fetchData()
      } catch (error) {
        logger.error('system', '焦点图图片上传失败', { contentId: item.id, error })
        uni.showToast({ title: '图片上传失败', icon: 'none' })
      }
    }
  })
}

/** 删除焦点图 */
async function handleDelete(item: FeaturedContent) {
  logger.info('user', '准备删除焦点图', { id: item.id, title: item.title })
  uni.showModal({
    title: '确认删除',
    content: `确定删除焦点图"${item.title}"吗？`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteFeaturedContent(item.id)
          logger.info('network', '焦点图删除成功', { id: item.id })
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        } catch (error) {
          logger.error('system', '焦点图删除失败', { contentId: item.id, error })
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => {
  logger.info('system', '进入焦点图管理页')
  fetchData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.featured-content-list-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.header-title {
  .title {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.btn-add {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 16px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 14px;
    color: #ffffff;
  }
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.content-item {
  display: flex;
  align-items: flex-start;
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  gap: var(--spacing-md);
}

.item-image {
  width: 120px;
  height: 68px;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  flex-shrink: 0;

  .cover-image {
    width: 100%;
    height: 100%;
  }

  .image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--color-bg-secondary);

    .placeholder-text {
      font-size: 28px;
    }
  }
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.item-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .item-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-tag {
    padding: 2px 8px;
    border-radius: var(--border-radius-sm);
    flex-shrink: 0;

    &.status-active {
      background-color: #e6f7ff;
      .status-text {
        color: #1890ff;
      }
    }

    &.status-inactive {
      background-color: #fff2f0;
      .status-text {
        color: #ff4d4f;
      }
    }
  }
}

.item-target {
  .target-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .target-type-tag {
    padding: 2px 6px;
    background-color: var(--color-bg-secondary);
    border-radius: var(--border-radius-sm);
    flex-shrink: 0;

    .target-type-text {
      font-size: 11px;
      color: var(--color-text-secondary);
    }
  }

  .target-url {
    font-size: 12px;
    color: var(--color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .target-id {
    font-size: 12px;
    color: var(--color-text-secondary);
    font-family: monospace;
  }

  .target-none {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.item-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);

  .meta-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.item-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 10px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .btn-text {
    font-size: 12px;
  }

  &.btn-edit {
    background-color: #e6f7ff;
    .btn-text {
      color: #1890ff;
    }
  }

  &.btn-image {
    background-color: #f6ffed;
    .btn-text {
      color: #52c41a;
    }
  }

  &.btn-delete {
    background-color: #fff2f0;
    .btn-text {
      color: #ff4d4f;
    }
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);

  .empty-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
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

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-lg);
}

.pagination {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .page-btn-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.page-info {
  .page-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}
</style>
```

### 6.2 FeaturedContentFormDialog.vue

> 焦点图新增/编辑弹窗，含图片上传、跳转目标选择、定时上下线

```vue
<!--
 * FeaturedContentFormDialog - 焦点图新增/编辑弹窗
 * @description 管理端焦点图的新增和编辑表单弹窗
 -->
<template>
  <view class="dialog-overlay" v-if="visible" @click.self="handleClose">
    <view class="dialog-container">
      <!-- 弹窗头部 -->
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新增焦点图' : '编辑焦点图' }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- 表单内容 -->
      <scroll-view class="dialog-body" scroll-y>
        <view class="form">
          <!-- 标题 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">标题</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.title"
                class="form-input"
                placeholder="焦点图标题（1-200字符）"
                maxlength="200"
              />
            </view>
            <view v-if="errors.title" class="form-error">
              <text class="error-text">{{ errors.title }}</text>
            </view>
          </view>

          <!-- 副标题 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">副标题</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.subtitle"
                class="form-input"
                placeholder="副标题（可选，最大500字符）"
                maxlength="500"
              />
            </view>
          </view>

          <!-- 焦点图图片 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">焦点图图片</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <view class="image-upload-area">
                <image
                  v-if="formData.image_url"
                  :src="formData.image_url"
                  class="preview-image"
                  mode="aspectFill"
                />
                <view v-else class="upload-placeholder" @click="handleChooseImage">
                  <text class="placeholder-icon">+</text>
                  <text class="placeholder-text">点击上传图片</text>
                  <text class="placeholder-hint">建议尺寸 750×320，支持 jpg/png/webp</text>
                </view>
                <view v-if="formData.image_url" class="image-actions">
                  <view class="btn-rechoose" @click="handleChooseImage">
                    <text class="btn-text">更换图片</text>
                  </view>
                </view>
              </view>
            </view>
            <view v-if="errors.image_url" class="form-error">
              <text class="error-text">{{ errors.image_url }}</text>
            </view>
          </view>

          <!-- 跳转类型 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">跳转类型</text>
            </view>
            <view class="form-control">
              <picker
                :value="targetTypeIndex"
                :range="targetTypeOptions"
                range-key="label"
                @change="handleTargetTypeChange"
              >
                <view class="picker-display">
                  <text class="picker-text">
                    {{ targetTypeIndex >= 0 ? targetTypeOptions[targetTypeIndex].label : '不跳转（纯展示）' }}
                  </text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
          </view>

          <!-- 外部链接 -->
          <view class="form-item" v-if="formData.target_type === 'external'">
            <view class="form-label">
              <text class="label-text">外部链接</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.target_url"
                class="form-input"
                placeholder="https://example.com"
              />
            </view>
            <view v-if="errors.target_url" class="form-error">
              <text class="error-text">{{ errors.target_url }}</text>
            </view>
          </view>

          <!-- 内部资源选择 -->
          <view class="form-item" v-if="formData.target_type && formData.target_type !== 'external'">
            <view class="form-label">
              <text class="label-text">关联资源</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <TargetSelector
                :target-type="formData.target_type"
                :model-value="formData.target_id"
                @update:model-value="formData.target_id = $event"
              />
            </view>
            <view v-if="errors.target_id" class="form-error">
              <text class="error-text">{{ errors.target_id }}</text>
            </view>
          </view>

          <!-- 排序值 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">排序值</text>
            </view>
            <view class="form-control">
              <input
                v-model.number="formData.sort_order"
                class="form-input"
                type="number"
                placeholder="0"
              />
            </view>
            <view class="form-hint">
              <text class="hint-text">数值越小越靠前</text>
            </view>
          </view>

          <!-- 启用状态 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">启用状态</text>
            </view>
            <view class="form-control">
              <switch
                :checked="formData.is_active"
                @change="formData.is_active = $event.detail.value"
                color="var(--color-primary)"
              />
            </view>
          </view>

          <!-- 上线时间 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">上线时间</text>
            </view>
            <view class="form-control">
              <picker
                mode="date"
                :value="startDateStr"
                @change="handleStartDateChange"
              >
                <view class="picker-display">
                  <text class="picker-text">{{ startDateStr || '选择上线时间（可选）' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
          </view>

          <!-- 下线时间 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">下线时间</text>
            </view>
            <view class="form-control">
              <picker
                mode="date"
                :value="endDateStr"
                :start="startDateStr"
                @change="handleEndDateChange"
              >
                <view class="picker-display">
                  <text class="picker-text">{{ endDateStr || '选择下线时间（可选）' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
            <view class="form-hint">
              <text class="hint-text">须晚于上线时间</text>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- 弹窗底部 -->
      <view class="dialog-footer">
        <view class="btn-cancel" @click="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view class="btn-confirm" :class="{ 'is-loading': submitting }" @click="handleSubmit">
          <text class="btn-text">{{ submitting ? '提交中...' : (mode === 'create' ? '创建' : '保存') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { logger } from '@/logs/logger'
import { createFeaturedContent, updateFeaturedContent } from '@/api/featuredContent'
import type { FeaturedContent, FeaturedContentTargetType } from '@/types/featuredContent'
import TargetSelector from '@/components/TargetSelector.vue'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData: FeaturedContent | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)

const formData = reactive({
  title: '',
  subtitle: '',
  image_url: '',
  target_type: '' as FeaturedContentTargetType | '',
  target_id: '',
  target_url: '',
  sort_order: 0,
  is_active: true,
  start_at: '',
  end_at: ''
})

const errors = reactive({
  title: '',
  image_url: '',
  target_url: '',
  target_id: ''
})

// 跳转类型选项
const targetTypeOptions = [
  { label: '直播间', value: 'room' },
  { label: '场次', value: 'session' },
  { label: '专题', value: 'topic' },
  { label: '品牌', value: 'brand' },
  { label: '外部链接', value: 'external' }
]

const targetTypeIndex = computed(() => {
  if (!formData.target_type) return -1
  return targetTypeOptions.findIndex(opt => opt.value === formData.target_type)
})

// 日期格式化（用于 picker 显示）
const startDateStr = computed(() => {
  return formData.start_at ? formData.start_at.slice(0, 10) : ''
})

const endDateStr = computed(() => {
  return formData.end_at ? formData.end_at.slice(0, 10) : ''
})

/** 监听初始数据，用于编辑模式填充表单 */
watch(
  () => props.initialData,
  (data) => {
    if (data && props.mode === 'edit') {
      formData.title = data.title || ''
      formData.subtitle = data.subtitle || ''
      formData.image_url = data.image_url || ''
      formData.target_type = data.target_type || ''
      formData.target_id = data.target_id || ''
      formData.target_url = data.target_url || ''
      formData.sort_order = data.sort_order || 0
      formData.is_active = data.is_active
      formData.start_at = data.start_at || ''
      formData.end_at = data.end_at || ''
      logger.info('system', '焦点图弹窗加载编辑数据', {
        mode: props.mode,
        id: data.id,
        title: data.title
      })
    }
  },
  { immediate: true }
)

/** 监听visible变化，重置表单 */
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      resetForm()
    }
  }
)

/** 重置表单 */
function resetForm() {
  formData.title = ''
  formData.subtitle = ''
  formData.image_url = ''
  formData.target_type = ''
  formData.target_id = ''
  formData.target_url = ''
  formData.sort_order = 0
  formData.is_active = true
  formData.start_at = ''
  formData.end_at = ''
  errors.title = ''
  errors.image_url = ''
  errors.target_url = ''
  errors.target_id = ''
}

/** 关闭弹窗 */
function handleClose() {
  emit('update:visible', false)
}

/** 选择图片（本地预览） */
function handleChooseImage() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const file = res.tempFiles[0]
      // 本地预览
      formData.image_url = file.path
      errors.image_url = ''
      logger.info('user', '选择焦点图图片', { path: file.path })
    }
  })
}

/** 跳转类型变更 */
function handleTargetTypeChange(e: any) {
  const index = e.detail.value
  formData.target_type = targetTypeOptions[index].value as FeaturedContentTargetType
  formData.target_id = ''
  formData.target_url = ''
}

/** 上线时间变更 */
function handleStartDateChange(e: any) {
  const dateStr = e.detail.value
  formData.start_at = dateStr ? `${dateStr}T00:00:00` : ''
}

/** 下线时间变更 */
function handleEndDateChange(e: any) {
  const dateStr = e.detail.value
  formData.end_at = dateStr ? `${dateStr}T23:59:59` : ''
}

/** 验证表单 */
function validateForm(): boolean {
  let isValid = true
  errors.title = ''
  errors.image_url = ''
  errors.target_url = ''
  errors.target_id = ''

  // 标题验证
  if (!formData.title.trim()) {
    errors.title = '请输入标题'
    isValid = false
  } else if (formData.title.length > 200) {
    errors.title = '长度不超过200个字符'
    isValid = false
  }

  // 图片验证
  if (!formData.image_url) {
    errors.image_url = '请上传焦点图图片'
    isValid = false
  }

  // 外部链接验证（external 类型时 target_url 必填）
  if (formData.target_type === 'external') {
    if (!formData.target_url.trim()) {
      errors.target_url = '请输入外部链接'
      isValid = false
    } else if (!/^https?:\/\/.+/.test(formData.target_url)) {
      errors.target_url = '请输入有效的URL（以http://或https://开头）'
      isValid = false
    }
  }

  // 内部资源ID验证（非 external 类型时 target_id 必填）
  if (formData.target_type && formData.target_type !== 'external' && !formData.target_id.trim()) {
    errors.target_id = '请选择关联资源'
    isValid = false
  }

  return isValid
}

/** 提交 */
async function handleSubmit() {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true
  try {
    const payload: any = {
      title: formData.title.trim(),
      subtitle: formData.subtitle.trim() || undefined,
      image_url: formData.image_url,
      sort_order: formData.sort_order,
      is_active: formData.is_active,
      start_at: formData.start_at || null,
      end_at: formData.end_at || null
    }

    // 跳转目标
    if (formData.target_type) {
      payload.target_type = formData.target_type
      if (formData.target_type === 'external') {
        payload.target_url = formData.target_url.trim()
      } else {
        payload.target_id = formData.target_id.trim()
      }
    }

    logger.info('network', '提交焦点图表单', {
      mode: props.mode,
      title: payload.title
    })

    if (props.mode === 'create') {
      await createFeaturedContent(payload)
      uni.showToast({ title: '焦点图创建成功', icon: 'success' })
    } else {
      await updateFeaturedContent(props.initialData!.id, payload)
      uni.showToast({ title: '焦点图更新成功', icon: 'success' })
    }

    emit('update:visible', false)
    emit('success')
  } catch (error) {
    logger.error('system', props.mode === 'create' ? '创建焦点图失败' : '更新焦点图失败', error)
    uni.showToast({
      title: props.mode === 'create' ? '创建失败' : '更新失败',
      icon: 'none'
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
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

.dialog-container {
  width: 90%;
  max-width: 520px;
  max-height: 85vh;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);

  .dialog-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .dialog-close {
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

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  max-height: 60vh;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;

  .label-text {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .label-required {
    font-size: 14px;
    color: #ff4d4f;
  }
}

.form-control {
  width: 100%;
}

.form-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  background-color: var(--color-bg-primary);
  box-sizing: border-box;

  &:focus {
    border-color: var(--color-primary);
  }
}

.form-error {
  .error-text {
    font-size: 12px;
    color: #ff4d4f;
  }
}

.form-hint {
  .hint-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

// 图片上传区域
.image-upload-area {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.preview-image {
  width: 280px;
  height: 120px;
  border-radius: var(--border-radius-sm);
}

.upload-placeholder {
  width: 280px;
  height: 120px;
  border: 1px dashed var(--color-border);
  border-radius: var(--border-radius-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;

  .placeholder-icon {
    font-size: 28px;
    color: var(--color-text-secondary);
  }

  .placeholder-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }

  .placeholder-hint {
    font-size: 11px;
    color: var(--color-text-secondary);
    opacity: 0.7;
  }
}

.image-actions {
  .btn-rechoose {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 28px;
    padding: 0 12px;
    background-color: var(--color-primary);
    border-radius: var(--border-radius-sm);
    cursor: pointer;

    .btn-text {
      font-size: 12px;
      color: #ffffff;
    }
  }
}

// Picker 样式
.picker-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);

  .picker-text {
    font-size: 14px;
    color: var(--color-text-primary);
  }

  .picker-arrow {
    font-size: 10px;
    color: var(--color-text-secondary);
  }
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.btn-cancel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 20px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 14px;
    color: var(--color-text-primary);
  }
}

.btn-confirm {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 20px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 14px;
    color: #ffffff;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>
```

---

## 七、用户端组件/页面

### 7.1 BannerCarousel.vue

> 首页轮播组件，展示启用且在有效期内的焦点图

```vue
<!--
 * BannerCarousel - 首页轮播组件
 * @description 展示启用且在有效期内的焦点图，支持点击跳转
 -->
<template>
  <view class="banner-carousel">
    <!-- 加载状态 -->
    <view v-if="loading" class="banner-skeleton">
      <view class="skeleton-block"></view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="banners.length === 0" class="banner-empty">
      <!-- 无焦点图时不展示任何内容 -->
    </view>

    <!-- 轮播展示 -->
    <view v-else class="banner-wrapper">
      <swiper
        class="banner-swiper"
        :autoplay="true"
        :interval="4000"
        :duration="500"
        :circular="true"
        indicator-dots
        indicator-color="rgba(255,255,255,0.4)"
        indicator-active-color="#ffffff"
      >
        <swiper-item
          v-for="banner in banners"
          :key="banner.id"
          @click="handleClick(banner)"
        >
          <view class="banner-item">
            <image
              :src="banner.image_url"
              :alt="banner.title"
              class="banner-image"
              mode="aspectFill"
            />
            <view class="banner-overlay" v-if="banner.title">
              <text class="banner-title">{{ banner.title }}</text>
              <text v-if="banner.subtitle" class="banner-subtitle">{{ banner.subtitle }}</text>
            </view>
          </view>
        </swiper-item>
      </swiper>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getFeaturedContent } from '@/api/featuredContent'
import type { FeaturedContent } from '@/types/featuredContent'

const banners = ref<FeaturedContent[]>([])
const loading = ref(false)

/** 加载焦点图数据 */
async function loadBanners() {
  loading.value = true
  try {
    logger.info('network', '加载首页焦点图')
    const res = await getFeaturedContent()
    banners.value = res.data?.items || []
    logger.info('network', '首页焦点图加载完成', { count: banners.value.length })
  } catch (error) {
    logger.error('system', '加载焦点图失败', error)
  } finally {
    loading.value = false
  }
}

/** 处理点击跳转 */
function handleClick(banner: FeaturedContent) {
  logger.info('user', '点击焦点图', {
    id: banner.id,
    target_type: banner.target_type,
    target_id: banner.target_id,
    target_url: banner.target_url
  })

  // 外部链接
  if (banner.target_type === 'external' && banner.target_url) {
    // #ifdef H5
    window.open(banner.target_url, '_blank')
    // #endif
    // #ifndef H5
    uni.setClipboardData({
      data: banner.target_url,
      success: () => {
        uni.showToast({ title: '链接已复制', icon: 'success' })
      }
    })
    // #endif
    return
  }

  // 内部跳转
  if (banner.target_id && banner.target_type) {
    const routeMap: Record<string, string> = {
      room: `/pages/user/room/detail?id=${banner.target_id}`,
      session: `/pages/user/session/detail?id=${banner.target_id}`,
      topic: `/pages/user/topic/detail?id=${banner.target_id}`,
      brand: `/pages/user/brand/detail?id=${banner.target_id}`
    }
    const path = routeMap[banner.target_type]
    if (path) {
      uni.navigateTo({ url: path })
    }
  }
}

onMounted(() => {
  loadBanners()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.banner-carousel {
  width: 100%;
  margin-bottom: var(--spacing-md);
}

.banner-wrapper {
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.banner-swiper {
  width: 100%;
  height: 320rpx;
}

.banner-item {
  position: relative;
  width: 100%;
  height: 100%;
}

.banner-image {
  width: 100%;
  height: 100%;
}

.banner-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 24rpx;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));

  .banner-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #ffffff;
    display: block;
  }

  .banner-subtitle {
    font-size: 22rpx;
    color: rgba(255, 255, 255, 0.85);
    margin-top: 4rpx;
    display: block;
  }
}

.banner-skeleton {
  width: 100%;
  height: 320rpx;
  border-radius: var(--border-radius-lg);
  overflow: hidden;

  .skeleton-block {
    width: 100%;
    height: 100%;
    background-color: var(--color-bg-secondary);
    animation: pulse 1.5s infinite;
  }
}

.banner-empty {
  display: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

### 7.2 TargetSelector.vue

> 跳转目标选择器组件，根据 target_type 搜索对应资源

```vue
<!--
 * TargetSelector - 跳转目标选择器
 * @description 根据 target_type 搜索并选择关联资源
 -->
<template>
  <view class="target-selector">
    <!-- 搜索输入 -->
    <view class="search-row">
      <input
        v-model="searchKeyword"
        class="search-input"
        :placeholder="placeholder"
        @confirm="handleSearch"
      />
    </view>

    <!-- 加载状态 -->
    <view v-if="searchLoading" class="selector-loading">
      <view class="loading-spinner"></view>
      <text class="loading-text">搜索中...</text>
    </view>

    <!-- 搜索结果 -->
    <scroll-view v-else class="results-scroll" scroll-y>
      <view v-if="options.length === 0" class="empty-results">
        <text class="empty-text">{{ searchKeyword ? '未找到匹配结果' : '输入关键词搜索' }}</text>
      </view>
      <view
        v-for="item in options"
        :key="item.id"
        :class="['result-item', selectedId === item.id ? 'result-selected' : '']"
        @click="handleSelect(item.id)"
      >
        <view class="result-info">
          <text class="result-name">{{ item.name }}</text>
          <text class="result-id">{{ item.id.slice(0, 8) }}...</text>
        </view>
        <text v-if="selectedId === item.id" class="result-check">✓</text>
      </view>
    </scroll-view>

    <!-- 已选资源展示 -->
    <view v-if="selectedId && selectedName" class="selected-display">
      <text class="selected-label">已选：</text>
      <text class="selected-name">{{ selectedName }}</text>
      <view class="btn-clear" @click="handleClear">
        <text class="clear-icon">✕</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { request } from '@/utils/request'
import type { FeaturedContentTargetType } from '@/types/featuredContent'

const props = defineProps<{
  targetType: FeaturedContentTargetType
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const searchKeyword = ref('')
const searchLoading = ref(false)
const selectedId = ref(props.modelValue)
const selectedName = ref('')
const options = ref<{ id: string; name: string }[]>([])

// 占位文本
const placeholder = computed(() => {
  const map: Record<string, string> = {
    room: '搜索直播间名称',
    session: '搜索场次标题',
    topic: '搜索专题名称',
    brand: '搜索品牌名称'
  }
  return map[props.targetType] || '搜索'
})

// API 路径映射
const apiMap: Record<string, string> = {
  room: '/rooms',
  session: '/sessions',
  topic: '/topics',
  brand: '/brands'
}

/** 搜索资源 */
async function handleSearch() {
  const baseApi = apiMap[props.targetType]
  if (!baseApi) return

  searchLoading.value = true
  try {
    logger.info('network', '搜索跳转目标资源', {
      targetType: props.targetType,
      keyword: searchKeyword.value
    })
    const res = await request.get(baseApi, {
      data: { q: searchKeyword.value || undefined, page: 1, page_size: 20 },
      showError: false
    })
    const items = res.data?.items || res.data || []
    options.value = items.map((item: any) => ({
      id: item.id,
      name: item.name || item.title || item.id
    }))
  } catch (error) {
    logger.error('system', '搜索跳转目标失败', error)
    options.value = []
  } finally {
    searchLoading.value = false
  }
}

/** 选择资源 */
function handleSelect(id: string) {
  selectedId.value = id
  const item = options.value.find(opt => opt.id === id)
  selectedName.value = item?.name || id
  emit('update:modelValue', id)
}

/** 清除选择 */
function handleClear() {
  selectedId.value = ''
  selectedName.value = ''
  emit('update:modelValue', '')
}

/** 监听外部值变化 */
watch(
  () => props.modelValue,
  (val) => {
    selectedId.value = val
    if (!val) {
      selectedName.value = ''
    }
  }
)

/** 监听 target_type 变化，重置选择 */
watch(
  () => props.targetType,
  () => {
    selectedId.value = ''
    selectedName.value = ''
    options.value = []
    searchKeyword.value = ''
    emit('update:modelValue', '')
    handleSearch()
  }
)

onMounted(() => {
  // 如果有初始值，尝试搜索一次以获取名称
  if (props.modelValue) {
    handleSearch()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.target-selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.search-row {
  .search-input {
    width: 100%;
    height: 36px;
    padding: 0 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-base);
    font-size: 14px;
    background-color: var(--color-bg-secondary);
    box-sizing: border-box;
  }
}

.selector-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
  gap: var(--spacing-sm);

  .loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.results-scroll {
  max-height: 200px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
}

.empty-results {
  padding: 20px 0;
  text-align: center;

  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: var(--color-bg-secondary);
  }

  &.result-selected {
    background-color: #e6f7ff;
  }
}

.result-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
  min-width: 0;

  .result-name {
    font-size: 14px;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .result-id {
    font-size: 11px;
    color: var(--color-text-secondary);
    font-family: monospace;
    flex-shrink: 0;
  }
}

.result-check {
  font-size: 14px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.selected-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 8px 12px;
  background-color: #e6f7ff;
  border-radius: var(--border-radius-sm);

  .selected-label {
    font-size: 13px;
    color: var(--color-text-secondary);
    flex-shrink: 0;
  }

  .selected-name {
    font-size: 13px;
    color: var(--color-primary);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .btn-clear {
    cursor: pointer;
    flex-shrink: 0;

    .clear-icon {
      font-size: 14px;
      color: var(--color-text-secondary);
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

---

## 八、对接清单

| # | 任务 | 说明 |
|---|------|------|
| 1 | 创建 `src/types/featuredContent.ts` | 按第三节定义类型，字段与后端 DDL/Pydantic 100% 对齐 |
| 2 | 创建 `src/api/featuredContent.ts` | 按第四节封装 7 个 API，使用 `API_PATHS` + `request` |
| 3 | 确认 `src/config/api.ts` 路径配置 | CONTENT.FEATURED_CONTENT、ADMIN.FEATURED_CONTENT 等已配置 |
| 4 | 实现 `src/pages/admin/featuredContent/FeaturedContentList.vue` | 管理端列表页，含新增/编辑/换图/删除/分页 |
| 5 | 实现 `src/pages/admin/featuredContent/FeaturedContentFormDialog.vue` | 新增/编辑弹窗，含图片上传、目标选择、定时上下线 |
| 6 | 实现 `src/components/TargetSelector.vue` | 跳转目标选择器，按 room/session/topic/brand 搜索 |
| 7 | 实现 `src/pages/user/home/BannerCarousel.vue` | 首页轮播组件，支持点击跳转 |
| 8 | 在 `pages.json` 添加路由 | `/pages/admin/featuredContent/list` |
| 9 | 在管理端 TabBar/菜单添加入口 | 焦点图管理菜单项 |
| 10 | 在首页引入 `BannerCarousel` | 放在页面顶部 |

---

## 九、API 链路总结

### 9.1 焦点图 CRUD 链路

```
管理端焦点图列表页
  ├─ fetchData() ──→ getAdminFeaturedContent({ page, page_size })
  │                    ──→ request.get(API_PATHS.ADMIN.FEATURED_CONTENT, { data: params })
  │                    ──→ GET /admin/featured-content?page=1&page_size=20
  │                    ──→ ApiResponse<{ total, page, size, items: FeaturedContent[] }>
  │
  ├─ openCreateDialog() → FeaturedContentFormDialog
  │    └─ handleSubmit() → createFeaturedContent(payload)
  │                         ──→ request.post(API_PATHS.ADMIN.CREATE_FEATURED, data)
  │                         ──→ POST /admin/featured-content
  │                         ──→ ApiResponse<FeaturedContent>
  │
  ├─ openEditDialog() → FeaturedContentFormDialog
  │    └─ handleSubmit() → updateFeaturedContent(contentId, payload)
  │                         ──→ request.patch(API_PATHS.ADMIN.UPDATE_FEATURED(contentId), data)
  │                         ──→ PATCH /admin/featured-content/{contentId}
  │                         ──→ ApiResponse<FeaturedContent>
  │
  ├─ handleUploadImage() → uploadFeaturedContentImage(contentId, file)
  │                          ──→ request.post(API_PATHS.ADMIN.UPLOAD_FEATURED_IMAGE(contentId), formData)
  │                          ──→ POST /admin/featured-content/{contentId}/image
  │                          ──→ ApiResponse<{ image_url: string }>
  │
  └─ handleDelete() → deleteFeaturedContent(contentId)
                        ──→ request.delete(API_PATHS.ADMIN.DELETE_FEATURED(contentId))
                        ──→ DELETE /admin/featured-content/{contentId}
                        ──→ ApiResponse<null>
```

### 9.2 用户端轮播链路

```
BannerCarousel 组件
  └─ loadBanners() ──→ getFeaturedContent({ limit })
                        ──→ request.get(API_PATHS.CONTENT.FEATURED_CONTENT, { data: params, auth: false })
                        ──→ GET /featured-content
                        ──→ ApiResponse<{ items: FeaturedContent[] }>

点击跳转逻辑：
  ├─ external 类型 → window.open(target_url) 或复制链接
  ├─ room 类型    → /pages/user/room/detail?id={target_id}
  ├─ session 类型 → /pages/user/session/detail?id={target_id}
  ├─ topic 类型   → /pages/user/topic/detail?id={target_id}
  └─ brand 类型   → /pages/user/brand/detail?id={target_id}
```

### 9.3 端点-类型-页面 对照表

| 端点 | 方法 | 请求类型 | 响应类型 | 调用页面/组件 |
|------|------|----------|----------|--------------|
| /featured-content | GET | { limit? } | { items: FeaturedContent[] } | BannerCarousel |
| /admin/featured-content | GET | { page?, page_size? } | { total, page, size, items: FeaturedContent[] } | FeaturedContentList |
| /admin/featured-content/{id} | GET | - | FeaturedContent | 预留详情页 |
| /admin/featured-content | POST | FeaturedContentCreate | FeaturedContent | FeaturedContentFormDialog |
| /admin/featured-content/{id} | PATCH | FeaturedContentUpdate | FeaturedContent | FeaturedContentFormDialog |
| /admin/featured-content/{id} | DELETE | - | null | FeaturedContentList |
| /admin/featured-content/{id}/image | POST | FormData(file) | { image_url: string } | FeaturedContentList |

### 9.4 后端约束对照

| 约束 | 前端实现 |
|------|----------|
| target_type 必填 | `FeaturedContentCreate.target_type` 为必填字段 |
| external 类型 target_url NOT NULL | 表单验证：target_type=external 时 target_url 必填 |
| 非 external 类型 target_id NOT NULL | 表单验证：非 external 时 target_id 必填 |
| CHECK (room/session/topic/brand/external) | `FeaturedContentTargetType` 联合类型限制 |
| 图片上传 jpg/png/webp max 5MB | uni.chooseImage + 后端校验 |
