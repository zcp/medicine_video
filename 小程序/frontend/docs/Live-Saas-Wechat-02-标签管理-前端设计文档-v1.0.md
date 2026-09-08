# 标签管理（Tag）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **后端设计文档**：《02-标签管理-后端设计文档.md》
> **零偏差**：所有类型、路径、端点严格对齐后端设计文档

---

## 一、功能概述

标签系统用于给直播场次打标签，支持按标签搜索场次。前端需要实现：

1. **管理端**：标签 CRUD（软删除） + 场次标签关联（物理删除）
2. **用户端**：按标签搜索场次（AND/OR 模式）

**后端数据表**：
- `tags`：id(UUID PK), name(VARCHAR 100 NOT NULL), slug(VARCHAR 100 NOT NULL UNIQUE), description(TEXT), is_active(BOOLEAN DEFAULT TRUE), created_at, updated_at
- `session_tags`：session_id(UUID FK CASCADE), tag_id(UUID FK CASCADE), created_at — 复合主键(session_id, tag_id)

**软删除策略**：tags 使用 `is_active` 字段；session_tags 使用物理删除

**API 端点清单（9个）**：

| # | 方法 | 路径 | 权限 | 说明 |
|---|------|------|------|------|
| 1 | GET | /content/tags | 公开 | 标签列表（支持搜索） |
| 2 | GET | /content/tags/{tagId} | 公开 | 标签详情 |
| 3 | POST | /admin/tags | JWT+Admin | 创建标签 |
| 4 | PATCH | /admin/tags/{tagId} | JWT+Admin | 更新标签 |
| 5 | DELETE | /admin/tags/{tagId} | JWT+Admin | 删除标签（软删除） |
| 6 | POST | /content/sessions/{sessionId}/tags | JWT+Admin | 设置场次标签 |
| 7 | GET | /content/sessions/{sessionId}/tags | 公开 | 获取场次标签 |
| 8 | DELETE | /content/sessions/{sessionId}/tags/{tagId} | JWT+Admin | 移除场次标签 |
| 9 | GET | /content/tags/search/sessions | 公开 | 按标签搜索场次 |

---

## 二、目录结构

```
src/
├── api/
│   └── tags.ts                    # 标签相关 API 封装（9个端点）
├── types/
│   └── tags.ts                    # TypeScript 类型定义（对齐后端 Schema）
├── pages/
│   ├── admin/
│   │   └── tag/
│   │       ├── TagList.vue            # 管理端标签列表页
│   │       └── TagFormDialog.vue      # 新增/编辑弹窗
│   └── user/
│       └── search/
│           └── SearchByTag.vue        # 按标签搜索页
├── components/
│   └── SessionTagSelector.vue         # 场次标签选择器组件
└── composables/
    └── useTag.ts                      # 标签相关组合函数
```

---

## 三、类型定义

> 严格对齐后端 Pydantic Schema，字段名、类型、必填/可选 100% 一致

```typescript
// src/types/tags.ts

/**
 * 标签信息（对应后端 TagItem Schema）
 * DDL: tags 表, slug VARCHAR(100) NOT NULL UNIQUE
 */
export interface Tag {
  /** 标签唯一标识（UUID） */
  id: string
  /** 标签名称（1-100字符） */
  name: string
  /** URL友好标识（必填，唯一，仅小写字母+数字+连字符） */
  slug: string
  /** 标签描述 */
  description?: string
  /** 是否启用状态（软删除标记） */
  is_active: boolean
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 最后更新时间（ISO 8601格式） */
  updated_at: string
  /** 来源（V2 可选）：admin=运营；user=用户 resolve；列表可弱标 */
  source?: 'admin' | 'user' | string
  /** 创建者 public_id（V2 可选） */
  created_by?: string | null
}

/**
 * 创建标签请求参数（对应后端 TagCreate Schema）
 * slug 为必填
 */
export interface TagCreate {
  /** 标签名称（必填，1-100字符） */
  name: string
  /** URL友好标识（必填，唯一） */
  slug: string
  /** 标签描述（可选） */
  description?: string
  /** 是否启用状态（可选，默认true） */
  is_active?: boolean
}

/**
 * 更新标签请求参数（对应后端 TagUpdate Schema，全部可选）
 */
export interface TagUpdate {
  /** 标签名称（可选） */
  name?: string
  /** URL友好标识（可选） */
  slug?: string
  /** 标签描述（可选） */
  description?: string
  /** 是否启用状态（可选） */
  is_active?: boolean
}

/**
 * 标签列表查询参数
 */
export interface TagListParams {
  /** 搜索关键词（匹配name、slug、description） */
  q?: string
  /** 搜索类型 */
  search_type?: 'name' | 'slug' | 'description'
  /** 是否包含已禁用的标签 */
  include_inactive?: boolean
}

/**
 * 场次标签关联设置请求（对应后端 SessionTagsSetRequest Schema）
 */
export interface SessionTagsSetRequest {
  /** 标签UUID列表 */
  tag_ids: string[]
  /** 关联模式：replace=替换, append=追加 */
  mode: 'replace' | 'append'
}

/**
 * 标签简要信息（对应后端 TagBriefItem Schema）
 * 用于场次标签关联响应，仅包含 id 和 name
 */
export interface TagBriefItem {
  /** 标签UUID */
  id: string
  /** 标签名称 */
  name: string
}

/**
 * 按标签搜索场次请求参数（对应后端 TagSearchParams Schema）
 */
export interface TagSearchParams {
  /** 标签UUID列表（至少1个） */
  tag_ids: string[]
  /** true=AND模式（必须匹配所有标签），false=OR模式（匹配任一标签） */
  match_all: boolean
  /** 页码，默认1 */
  page?: number
  /** 每页数量，默认20 */
  page_size?: number
}

/**
 * 搜索结果项（对应后端 SearchResultItem Schema）
 */
export interface SearchResultItem {
  /** 场次UUID */
  session_id: string
  /** 场次标题 */
  title: string
  /** 匹配到的标签名称列表 */
  matched_tags: string[]
  /** 匹配分数（匹配标签数/总搜索标签数） */
  score: number
}
```

---

## 四、API 封装

> 使用 `request.get/post/put/delete` from `@/utils/request`
> 响应类型统一为 `ApiResponse<T>` from `@/types/common`
> 路径统一使用 `API_PATHS` from `@/config/api`

```typescript
// src/api/tags.ts

/**
 * 标签管理 API
 * 以后端设计文档为准：《02-标签管理-后端设计文档.md》
 *
 * 端点清单（9个）:
 *   Tags CRUD: GET列表, GET详情, POST创建, PATCH更新, DELETE删除
 *   Session Tags: GET场次标签, POST设置场次标签, DELETE移除场次标签
 *   搜索: GET按标签搜索场次
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  Tag,
  TagCreate,
  TagUpdate,
  TagListParams,
  SessionTagsSetRequest,
  TagBriefItem,
  TagSearchParams,
  SearchResultItem
} from '@/types/tags'

// ============ Tags CRUD（公开+管理员） ============

/**
 * 获取标签列表（公开，支持搜索）
 * GET /api/v1/content/tags
 */
export const getTags = (params?: TagListParams): Promise<ApiResponse<{ items: Tag[] }>> => {
  return request.get(API_PATHS.TAGS.LIST, { data: params, showError: false })
}

/**
 * 获取单个标签详情（公开）
 * GET /api/v1/content/tags/{tagId}
 */
export const getTag = (tagId: string): Promise<ApiResponse<Tag>> => {
  return request.get(API_PATHS.TAGS.DETAIL(tagId), { showError: false })
}

/**
 * 创建标签（管理员）
 * POST /api/v1/admin/tags
 */
export const createTag = (data: TagCreate): Promise<ApiResponse<Tag>> => {
  return request.post(API_PATHS.TAGS.CREATE, data, {
    loading: true,
    loadingText: '创建中...'
  })
}

/**
 * 更新标签（管理员）
 * PATCH /api/v1/admin/tags/{tagId}
 */
export const updateTag = (tagId: string, data: TagUpdate): Promise<ApiResponse<Tag>> => {
  return request.put(API_PATHS.TAGS.UPDATE(tagId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

/**
 * 删除标签（管理员，软删除）
 * DELETE /api/v1/admin/tags/{tagId}
 */
export const deleteTag = (tagId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.TAGS.DELETE(tagId), {
    loading: true,
    loadingText: '删除中...'
  })
}

// ============ Session Tags（场次-标签关联） ============

/**
 * 获取场次的标签列表（公开）
 * GET /api/v1/content/sessions/{sessionId}/tags
 * 后端返回 TagItem[]（标签完整信息），data 为数组，不带 items 包装
 */
export const getSessionTags = (sessionId: string): Promise<ApiResponse<Tag[]>> => {
  return request.get(API_PATHS.SESSION.TAGS(sessionId), { showError: false })
}

/**
 * 设置场次标签关联（管理员）
 * POST /api/v1/content/sessions/{sessionId}/tags
 * 后端返回 SessionTagsSetResponse: { session_id, mode, tags: TagBriefItem[] }
 */
export const setSessionTags = (
  sessionId: string,
  data: SessionTagsSetRequest
): Promise<ApiResponse<{ session_id: string; mode: string; tags: TagBriefItem[] }>> => {
  return request.post(API_PATHS.SESSION.TAGS(sessionId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

/**
 * 移除场次标签关联（管理员）
 * DELETE /api/v1/content/sessions/{sessionId}/tags/{tagId}
 */
export const removeSessionTag = (sessionId: string, tagId: string): Promise<ApiResponse<null>> => {
  return request.delete(`${API_PATHS.SESSION.TAGS(sessionId)}/${tagId}`, {
    loading: true,
    loadingText: '移除中...'
  })
}

// ============ 搜索（按标签搜索场次） ============

/**
 * 按标签搜索场次（公开）
 * GET /api/v1/content/tags/search/sessions
 */
export const searchSessionsByTag = (
  params: TagSearchParams
): Promise<ApiResponse<{ total: number; page: number; size: number; items: SearchResultItem[] }>> => {
  return request.get(API_PATHS.TAGS.SEARCH_SESSIONS, {
    data: {
      tag_ids: params.tag_ids,
      match_all: params.match_all ?? false,
      page: params.page || 1,
      page_size: params.page_size || 20
    },
    showError: false
  })
}

export default {
  getTags,
  getTag,
  createTag,
  updateTag,
  deleteTag,
  getSessionTags,
  setSessionTags,
  removeSessionTag,
  searchSessionsByTag
}
```

---

## 五、config/api.ts 路径配置

> 已存在于 `src/config/api.ts`，此处记录完整路径映射关系

```typescript
// src/config/api.ts 中已配置的标签相关路径

// 标签管理 (core服务, 路径以后端设计文档为准: /api/v1/content/tags)
TAGS: {
  LIST: '/content/tags',                                         // GET 公开
  DETAIL: (tagId: string) => `/content/tags/${tagId}`,           // GET 公开
  SEARCH_SESSIONS: '/content/tags/search/sessions',              // GET 公开
  ADMIN_LIST: '/admin/tags',                                     // 预留
  CREATE: '/admin/tags',                                         // POST JWT+Admin
  UPDATE: (tagId: string) => `/admin/tags/${tagId}`,             // PATCH JWT+Admin
  DELETE: (tagId: string) => `/admin/tags/${tagId}`              // DELETE JWT+Admin
},

// 场次标签关联（在 SESSION 模块中）
SESSION: {
  // ...
  TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,  // GET/POST
},

// 管理员场次标签（在 ADMIN 模块中，用于 DELETE）
ADMIN: {
  // ...
  SESSION_TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,
  DELETE_SESSION_TAG: (sessionId: string, tagId: string) => `/content/sessions/${sessionId}/tags/${tagId}`,
}
```

**9个端点与 API_PATHS 对应关系**：

| # | 端点 | 使用的 API_PATHS |
|---|------|-----------------|
| 1 | GET /content/tags | `API_PATHS.TAGS.LIST` |
| 2 | GET /content/tags/{tagId} | `API_PATHS.TAGS.DETAIL(tagId)` |
| 3 | POST /admin/tags | `API_PATHS.TAGS.CREATE` |
| 4 | PATCH /admin/tags/{tagId} | `API_PATHS.TAGS.UPDATE(tagId)` |
| 5 | DELETE /admin/tags/{tagId} | `API_PATHS.TAGS.DELETE(tagId)` |
| 6 | POST /content/sessions/{sessionId}/tags | `API_PATHS.SESSION.TAGS(sessionId)` |
| 7 | GET /content/sessions/{sessionId}/tags | `API_PATHS.SESSION.TAGS(sessionId)` |
| 8 | DELETE /content/sessions/{sessionId}/tags/{tagId} | `` `${API_PATHS.SESSION.TAGS(sessionId)}/${tagId}` `` |
| 9 | GET /content/tags/search/sessions | `API_PATHS.TAGS.SEARCH_SESSIONS` |

---

## 六、管理端页面实现

### 6.1 TagList.vue

> 标签管理列表页（**实现真源**：`src/pages/admin/tag/TagList.vue`；下文大段样本若冲突以源码为准）
>
> **一句话闭环**：搜/筛 → 建/改 → 停用可恢复 → 离开  
> **非目标**：按 `source` 隐藏用户词；多维运营台；普通用户入口  
> **数据范围（对齐 V2）**：`GET /content/tags?include_inactive=true`，**同时展示**运营与用户自建（不按 `source` 过滤）

#### 6.1.0 管理端列表约定（2026-09-02）

| 项 | 约定 |
|----|------|
| 顶栏 | 导航已有标题 → **页内不再重复**「标签管理」；搜索 + 状态筛 + 新增同行 |
| 行布局 | **第一行**：名称（可截断）+ 启停徽章（固定槽、统一尺寸）；**第二行**：slug（弱化/截断）+ 可选 `source` 弱标（运营/用户） |
| 启停文案 | 徽章：启用 / 已停用；主操作：**停用**（`DELETE /admin/tags/{id}` 软删）/ **启用**（`PATCH … { is_active: true }`）；禁止再用「删除」冒充软禁用 |
| 筛选 | 客户端：全部 / 启用中 / 已停用（列表已拉全量含 inactive） |
| 停用行 | `tag-item--inactive` 降透，便于扫库 |
| 操作权重 | 「编辑」主色；「停用」描边次按钮 |

```vue
<!--
 * TagList - 标签管理列表页
 * @description 管理端标签的增删改查页面（样本；以 src 为准）
 -->
<template>
  <view class="tag-list-page">
    <!-- 顶部操作栏：搜索 + 状态筛 + 新增（无页内大标题） -->
    <view class="page-header">
      <view class="header-actions">
        <view class="search-box">
          <input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索标签名称或英文标识"
            @confirm="handleSearch"
          />
          <view v-if="searchKeyword" class="search-clear" @click="clearSearch">
            <text class="clear-icon">✕</text>
          </view>
        </view>
        <view class="btn-add" @click="openCreateDialog">
          <text class="btn-text">+ 新增</text>
        </view>
      </view>
    </view>

    <!-- 标签列表 -->
    <view class="tag-list" v-if="!loading">
      <view v-if="tableData.length === 0" class="empty-state">
        <text class="empty-text">{{ searchKeyword ? '未找到匹配的标签' : '暂无标签数据' }}</text>
      </view>

      <view
        v-for="item in tableData"
        :key="item.id"
        class="tag-item"
      >
        <view class="item-main">
          <view class="item-info">
            <view class="item-name-row">
              <text class="item-name">{{ item.name }}</text>
              <view v-if="item.slug" class="item-slug">
                <text class="slug-text">{{ item.slug }}</text>
              </view>
              <view :class="['status-tag', item.is_active ? 'status-active' : 'status-inactive']">
                <text class="status-text">{{ item.is_active ? '启用' : '禁用' }}</text>
              </view>
            </view>
            <view v-if="item.description" class="item-desc">
              <text class="desc-text">{{ item.description }}</text>
            </view>
            <view class="item-meta">
              <text class="meta-text">创建于 {{ formatDate(item.created_at) }}</text>
            </view>
          </view>
        </view>
        <view class="item-actions">
          <view class="action-btn btn-edit" @click="openEditDialog(item)">
            <text class="btn-text">编辑</text>
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

    <!-- 新增/编辑弹窗 -->
    <TagFormDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="currentTag"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, deleteTag } from '@/api/tags'
import type { Tag } from '@/types/tags'
import TagFormDialog from './TagFormDialog.vue'

// 表格数据
const tableData = ref<Tag[]>([])
const loading = ref(false)
const searchKeyword = ref('')

// 弹窗状态
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentTag = ref<Tag | null>(null)

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
    logger.info('network', '加载管理端标签列表', {
      q: searchKeyword.value || undefined
    })
    const res = await getTags({
      q: searchKeyword.value || undefined,
      include_inactive: true
    })
    tableData.value = res.data?.items || []
    logger.info('network', '管理端标签列表加载完成', {
      count: tableData.value.length
    })
  } catch (error) {
    logger.error('system', '加载管理端标签列表失败', error)
    uni.showToast({ title: '加载标签列表失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 搜索 */
function handleSearch() {
  logger.info('user', '搜索标签', { keyword: searchKeyword.value })
  fetchData()
}

/** 清除搜索 */
function clearSearch() {
  logger.info('user', '清除标签搜索条件')
  searchKeyword.value = ''
  handleSearch()
}

/** 打开新增弹窗 */
function openCreateDialog() {
  logger.info('user', '打开新增标签弹窗')
  dialogMode.value = 'create'
  currentTag.value = null
  dialogVisible.value = true
}

/** 打开编辑弹窗 */
function openEditDialog(tag: Tag) {
  logger.info('user', '打开编辑标签弹窗', { id: tag.id, name: tag.name })
  dialogMode.value = 'edit'
  currentTag.value = { ...tag }
  dialogVisible.value = true
}

/** 删除标签 */
async function handleDelete(tag: Tag) {
  logger.info('user', '准备删除标签', { id: tag.id, name: tag.name })
  uni.showModal({
    title: '确认删除',
    content: `确定删除标签"${tag.name}"吗？此操作将禁用该标签。`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteTag(tag.id)
          logger.info('network', '标签删除成功', { id: tag.id })
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        } catch (error) {
          logger.error('system', '标签删除失败', { tagId: tag.id, error })
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
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

.search-box {
  position: relative;
  flex: 1;
  max-width: 300px;

  .search-input {
    width: 100%;
    height: 36px;
    padding: 0 32px 0 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-base);
    font-size: 14px;
    background-color: var(--color-bg-primary);
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

    .clear-icon {
      font-size: 14px;
      color: var(--color-text-secondary);
    }
  }
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

.tag-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.item-main {
  display: flex;
  align-items: center;
  flex: 1;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .item-name {
    font-size: 16px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .item-slug {
    padding: 2px 6px;
    background-color: var(--color-bg-secondary);
    border-radius: var(--border-radius-sm);

    .slug-text {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
  }

  .status-tag {
    padding: 2px 8px;
    border-radius: var(--border-radius-sm);

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

.item-desc {
  .desc-text {
    font-size: 13px;
    color: var(--color-text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.item-meta {
  .meta-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.item-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-left: var(--spacing-md);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .btn-text {
    font-size: 13px;
  }

  &.btn-edit {
    background-color: #e6f7ff;
    .btn-text {
      color: #1890ff;
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
</style>
```

### 6.2 TagFormDialog.vue

> 标签新增/编辑弹窗，表单验证、提交、重置

```vue
<!--
 * TagFormDialog - 标签新增/编辑弹窗
 * @description 管理端标签的新增和编辑表单弹窗
 -->
<template>
  <view class="dialog-overlay" v-if="visible" @click.self="handleClose">
    <view class="dialog-container">
      <!-- 弹窗头部 -->
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新增标签' : '编辑标签' }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- 表单内容 -->
      <scroll-view class="dialog-body" scroll-y>
        <view class="form">
          <!-- 标签名称 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">标签名称</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.name"
                class="form-input"
                placeholder="请输入标签名称（1-100字符）"
                maxlength="100"
              />
            </view>
            <view v-if="errors.name" class="form-error">
              <text class="error-text">{{ errors.name }}</text>
            </view>
          </view>

          <!-- Slug -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">Slug</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.slug"
                class="form-input"
                placeholder="URL友好标识（必填，如 my-tag）"
                maxlength="100"
              />
            </view>
            <view class="form-hint">
              <text class="hint-text">仅允许小写字母、数字和连字符</text>
            </view>
            <view v-if="errors.slug" class="form-error">
              <text class="error-text">{{ errors.slug }}</text>
            </view>
          </view>

          <!-- 描述 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">描述</text>
            </view>
            <view class="form-control">
              <textarea
                v-model="formData.description"
                class="form-textarea"
                placeholder="标签描述（可选）"
                maxlength="500"
              />
            </view>
            <view v-if="errors.description" class="form-error">
              <text class="error-text">{{ errors.description }}</text>
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
import { ref, reactive, watch } from 'vue'
import { logger } from '@/logs/logger'
import { createTag, updateTag } from '@/api/tags'
import type { Tag } from '@/types/tags'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData: Tag | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)

const formData = reactive({
  name: '',
  slug: '',
  description: '',
  is_active: true
})

const errors = reactive({
  name: '',
  slug: '',
  description: ''
})

/** 监听初始数据，用于编辑模式填充表单 */
watch(
  () => props.initialData,
  (data) => {
    if (data && props.mode === 'edit') {
      formData.name = data.name
      formData.slug = data.slug || ''
      formData.description = data.description || ''
      formData.is_active = data.is_active
      logger.info('system', '标签弹窗加载编辑数据', {
        mode: props.mode,
        tag: { id: data.id, name: data.name, slug: data.slug }
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
  formData.name = ''
  formData.slug = ''
  formData.description = ''
  formData.is_active = true
  errors.name = ''
  errors.slug = ''
  errors.description = ''
}

/** 关闭弹窗 */
function handleClose() {
  emit('update:visible', false)
}

/** 验证表单 */
function validateForm(): boolean {
  let isValid = true
  errors.name = ''
  errors.slug = ''
  errors.description = ''

  // 名称验证
  if (!formData.name.trim()) {
    errors.name = '请输入标签名称'
    isValid = false
  } else if (formData.name.length < 1 || formData.name.length > 100) {
    errors.name = '长度在1-100个字符'
    isValid = false
  }

  // Slug验证（必填）
  if (!formData.slug.trim()) {
    errors.slug = '请输入Slug'
    isValid = false
  } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
    errors.slug = '只能包含小写字母、数字和连字符'
    isValid = false
  } else if (formData.slug.length > 100) {
    errors.slug = '长度不超过100个字符'
    isValid = false
  }

  // 描述验证
  if (formData.description && formData.description.length > 500) {
    errors.description = '长度不超过500个字符'
    isValid = false
  }

  if (!isValid) {
    logger.warn('system', '标签表单校验失败', {
      mode: props.mode,
      errors: { name: errors.name, slug: errors.slug, description: errors.description }
    })
  }

  return isValid
}

/** 提交 */
async function handleSubmit() {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true
  try {
    const payload = {
      name: formData.name.trim(),
      slug: formData.slug.trim(),
      description: formData.description.trim() || undefined,
      is_active: formData.is_active
    }

    logger.info('network', '提交标签表单', { mode: props.mode, payload })

    if (props.mode === 'create') {
      await createTag(payload)
      uni.showToast({ title: '标签创建成功', icon: 'success' })
    } else {
      await updateTag(props.initialData!.id, payload)
      uni.showToast({ title: '标签更新成功', icon: 'success' })
    }

    emit('update:visible', false)
    emit('success')
  } catch (error) {
    logger.error('system', props.mode === 'create' ? '创建标签失败' : '更新标签失败', error)
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
  max-height: 80vh;
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

.form-textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px 12px;
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

### 7.1 SessionTagSelector.vue

> 场次标签选择器组件，嵌入场次编辑页使用

```vue
<!--
 * SessionTagSelector - 场次标签选择器
 * @description 嵌入场次编辑页，管理场次的标签关联
 -->
<template>
  <view class="session-tag-selector">
    <view class="selector-header">
      <text class="selector-title">场次标签</text>
      <text class="selector-hint">可选1-50个标签</text>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="selector-loading">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 标签搜索输入 -->
    <view v-else class="selector-body">
      <view class="search-row">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="输入关键词搜索标签"
          @confirm="handleSearch"
        />
      </view>

      <!-- 搜索结果/全部标签 -->
      <scroll-view class="tag-scroll" scroll-y>
        <view v-if="availableTags.length === 0" class="empty-tags">
          <text class="empty-text">暂无可选标签</text>
        </view>
        <view class="tag-grid">
          <view
            v-for="tag in availableTags"
            :key="tag.id"
            :class="['tag-chip', selectedIds.includes(tag.id) ? 'tag-selected' : '']"
            @click="toggleTag(tag.id)"
          >
            <text class="chip-text">{{ tag.name }}</text>
            <text v-if="selectedIds.includes(tag.id)" class="chip-check">✓</text>
          </view>
        </view>
      </scroll-view>

      <!-- 已选标签展示 -->
      <view v-if="selectedIds.length > 0" class="selected-section">
        <view class="selected-header">
          <text class="selected-title">已选标签（{{ selectedIds.length }}）</text>
          <view class="btn-clear" @click="clearAll">
            <text class="clear-text">清空</text>
          </view>
        </view>
        <view class="selected-tags">
          <view
            v-for="tagId in selectedIds"
            :key="tagId"
            class="selected-chip"
          >
            <text class="chip-text">{{ getTagName(tagId) }}</text>
            <view class="chip-remove" @click="removeTag(tagId)">
              <text class="remove-icon">✕</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 保存按钮 -->
      <view class="save-row">
        <view
          class="btn-save"
          :class="{ 'is-loading': saving }"
          @click="handleSave"
        >
          <text class="btn-text">{{ saving ? '保存中...' : '保存标签' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, getSessionTags, setSessionTags } from '@/api/tags'
import type { Tag, TagBriefItem } from '@/types/tags'

const props = defineProps<{
  /** 场次ID */
  sessionId: string
}>()

const emit = defineEmits<{
  success: []
}>()

const loading = ref(false)
const saving = ref(false)
const searchKeyword = ref('')
const availableTags = ref<Tag[]>([])
const selectedIds = ref<string[]>([])
let allTags: Tag[] = []

/** 根据ID获取标签名称 */
function getTagName(id: string): string {
  return allTags.find(t => t.id === id)?.name || id
}

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    logger.info('network', '加载场次标签数据', { sessionId: props.sessionId })
    const [allRes, selectedRes] = await Promise.all([
      getTags({ include_inactive: false }),
      getSessionTags(props.sessionId)
    ])
    allTags = allRes.data?.items || []
    availableTags.value = [...allTags]
    // 后端返回 TagItem[]，直接是标签数组，id 字段为标签UUID
    selectedIds.value = (selectedRes.data || []).map(item => item.id)
    logger.info('network', '场次标签数据加载完成', {
      allCount: allTags.length,
      selectedCount: selectedIds.value.length
    })
  } catch (error) {
    logger.error('system', '加载场次标签数据失败', error)
    uni.showToast({ title: '加载标签数据失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 搜索标签 */
function handleSearch() {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    availableTags.value = [...allTags]
    return
  }
  availableTags.value = allTags.filter(tag =>
    tag.name.toLowerCase().includes(keyword) ||
    tag.slug.toLowerCase().includes(keyword)
  )
}

/** 切换标签选中状态 */
function toggleTag(tagId: string) {
  const index = selectedIds.value.indexOf(tagId)
  if (index >= 0) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(tagId)
  }
}

/** 移除单个标签 */
function removeTag(tagId: string) {
  selectedIds.value = selectedIds.value.filter(id => id !== tagId)
}

/** 清空所有选中 */
function clearAll() {
  selectedIds.value = []
}

/** 保存标签关联 */
async function handleSave() {
  if (saving.value) return
  saving.value = true
  try {
    logger.info('network', '保存场次标签', {
      sessionId: props.sessionId,
      tagIds: selectedIds.value
    })
    await setSessionTags(props.sessionId, {
      tag_ids: selectedIds.value,
      mode: 'replace'
    })
    uni.showToast({ title: '标签保存成功', icon: 'success' })
    emit('success')
  } catch (error) {
    logger.error('system', '保存场次标签失败', error)
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.session-tag-selector {
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  padding: var(--spacing-md);
}

.selector-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);

  .selector-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .selector-hint {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.selector-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  gap: var(--spacing-sm);

  .loading-spinner {
    width: 24px;
    height: 24px;
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

.search-row {
  margin-bottom: var(--spacing-md);

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

.tag-scroll {
  max-height: 200px;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .chip-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  .chip-check {
    font-size: 12px;
    color: var(--color-primary);
  }

  &.tag-selected {
    background-color: #e6f7ff;
    border: 1px solid var(--color-primary);

    .chip-text {
      color: var(--color-primary);
    }
  }
}

.empty-tags {
  padding: 20px 0;
  text-align: center;

  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.selected-section {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.selected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);

  .selected-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .btn-clear {
    cursor: pointer;

    .clear-text {
      font-size: 12px;
      color: var(--color-primary);
    }
  }
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.selected-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #e6f7ff;
  border-radius: var(--border-radius-sm);

  .chip-text {
    font-size: 12px;
    color: var(--color-primary);
  }

  .chip-remove {
    cursor: pointer;

    .remove-icon {
      font-size: 12px;
      color: var(--color-primary);
      opacity: 0.7;
    }
  }
}

.save-row {
  margin-top: var(--spacing-md);
}

.btn-save {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

### 7.2 SearchByTag.vue

> 用户端按标签搜索场次页面，支持 AND/OR 匹配模式

```vue
<!--
 * SearchByTag - 按标签搜索场次页面
 * @description 用户端选择标签后搜索匹配的场次
 -->
<template>
  <view class="search-by-tag-page">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">按标签搜索</text>
    </view>

    <!-- 已选标签展示 -->
    <view v-if="selectedIds.length > 0" class="selected-bar">
      <view class="selected-tags">
        <view
          v-for="tagId in selectedIds"
          :key="tagId"
          class="selected-chip"
        >
          <text class="chip-text">{{ getTagName(tagId) }}</text>
          <view class="chip-remove" @click="removeSelectedTag(tagId)">
            <text class="remove-icon">✕</text>
          </view>
        </view>
      </view>
      <view class="btn-clear-all" @click="clearAllTags">
        <text class="clear-text">清空</text>
      </view>
    </view>

    <!-- 标签选择区 -->
    <view class="tag-selector">
      <view class="selector-header">
        <text class="selector-title">选择标签</text>
      </view>
      <view class="search-box">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索标签"
          @confirm="handleTagSearch"
        />
      </view>

      <!-- 标签列表 -->
      <view v-if="tagLoading" class="tag-loading">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载标签...</text>
      </view>
      <scroll-view v-else class="tag-scroll" scroll-y>
        <view v-if="availableTags.length === 0" class="empty-tags">
          <text class="empty-text">暂无可选标签</text>
        </view>
        <view class="tag-grid">
          <view
            v-for="tag in availableTags"
            :key="tag.id"
            :class="['tag-chip', selectedIds.includes(tag.id) ? 'tag-selected' : '']"
            @click="toggleTag(tag.id)"
          >
            <text class="chip-text">{{ tag.name }}</text>
            <text v-if="selectedIds.includes(tag.id)" class="chip-check">✓</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 匹配模式选择（多个标签时显示） -->
    <view v-if="selectedIds.length > 1" class="match-mode">
      <view class="mode-header">
        <text class="mode-title">匹配模式</text>
      </view>
      <view class="mode-options">
        <view
          :class="['mode-option', matchAll ? 'mode-active' : '']"
          @click="matchAll = true"
        >
          <text class="mode-text">同时包含所有标签（AND）</text>
        </view>
        <view
          :class="['mode-option', !matchAll ? 'mode-active' : '']"
          @click="matchAll = false"
        >
          <text class="mode-text">包含任一标签（OR）</text>
        </view>
      </view>
    </view>

    <!-- 搜索按钮 -->
    <view class="search-action">
      <view
        class="btn-search"
        :class="{ 'is-disabled': selectedIds.length === 0, 'is-loading': searching }"
        @click="handleSearch"
      >
        <text class="btn-text">{{ searching ? '搜索中...' : '搜索场次' }}</text>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="search-results">
      <view class="results-header" v-if="hasSearched">
        <text class="results-title">搜索结果（{{ results.length }}）</text>
      </view>

      <!-- 搜索中 -->
      <view v-if="searching" class="loading-state">
        <view class="loading-spinner"></view>
        <text class="loading-text">搜索中...</text>
      </view>

      <!-- 空结果 -->
      <view v-else-if="hasSearched && results.length === 0" class="empty-state">
        <text class="empty-text">未找到匹配的场次</text>
      </view>

      <!-- 结果列表 -->
      <view v-else class="results-list">
        <view
          v-for="item in results"
          :key="item.session_id"
          class="result-item"
          @click="navigateToSession(item.session_id)"
        >
          <view class="result-info">
            <text class="result-title">{{ item.title }}</text>
            <view class="result-tags">
              <text
                v-for="tagName in item.matched_tags"
                :key="tagName"
                class="result-tag"
              >{{ tagName }}</text>
            </view>
            <view class="result-meta">
              <text class="meta-text">匹配度: {{ Math.round(item.score * 100) }}%</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, searchSessionsByTag } from '@/api/tags'
import type { Tag, SearchResultItem } from '@/types/tags'

const searchKeyword = ref('')
const tagLoading = ref(false)
const searching = ref(false)
const hasSearched = ref(false)
const matchAll = ref(true)
const availableTags = ref<Tag[]>([])
const selectedIds = ref<string[]>([])
const results = ref<SearchResultItem[]>([])
let allTags: Tag[] = []

/** 根据ID获取标签名称 */
function getTagName(id: string): string {
  return allTags.find(t => t.id === id)?.name || id
}

/** 加载标签列表 */
async function loadTags() {
  tagLoading.value = true
  try {
    const res = await getTags({ include_inactive: false })
    allTags = res.data?.items || []
    availableTags.value = [...allTags]
    logger.info('network', '标签列表加载完成', { count: allTags.length })
  } catch (error) {
    logger.error('system', '加载标签列表失败', error)
    uni.showToast({ title: '加载标签失败', icon: 'none' })
  } finally {
    tagLoading.value = false
  }
}

/** 搜索标签 */
function handleTagSearch() {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    availableTags.value = [...allTags]
    return
  }
  availableTags.value = allTags.filter(tag =>
    tag.name.toLowerCase().includes(keyword) ||
    tag.slug.toLowerCase().includes(keyword)
  )
}

/** 切换标签选中 */
function toggleTag(tagId: string) {
  const index = selectedIds.value.indexOf(tagId)
  if (index >= 0) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(tagId)
  }
}

/** 移除已选标签 */
function removeSelectedTag(tagId: string) {
  selectedIds.value = selectedIds.value.filter(id => id !== tagId)
}

/** 清空所有选中 */
function clearAllTags() {
  selectedIds.value = []
  results.value = []
  hasSearched.value = false
}

/** 执行搜索 */
async function handleSearch() {
  if (selectedIds.value.length === 0 || searching.value) return

  searching.value = true
  hasSearched.value = true
  try {
    logger.info('network', '按标签搜索场次', {
      tagIds: selectedIds.value,
      matchAll: matchAll.value
    })
    const res = await searchSessionsByTag({
      tag_ids: selectedIds.value,
      match_all: matchAll.value,
      page: 1,
      page_size: 50
    })
    results.value = res.data?.items || []
    logger.info('network', '标签搜索完成', { count: results.value.length })
  } catch (error) {
    logger.error('system', '标签搜索失败', error)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    searching.value = false
  }
}

/** 跳转到场次详情 */
function navigateToSession(sessionId: string) {
  uni.navigateTo({
    url: `/pages/user/session/detail?id=${sessionId}`
  })
}

onMounted(() => {
  logger.info('system', '进入按标签搜索页')
  loadTags()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.search-by-tag-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.selected-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  flex: 1;
}

.selected-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: #e6f7ff;
  border-radius: var(--border-radius-sm);

  .chip-text {
    font-size: 13px;
    color: var(--color-primary);
  }

  .chip-remove {
    cursor: pointer;

    .remove-icon {
      font-size: 12px;
      color: var(--color-primary);
      opacity: 0.7;
    }
  }
}

.btn-clear-all {
  flex-shrink: 0;
  cursor: pointer;

  .clear-text {
    font-size: 13px;
    color: var(--color-primary);
  }
}

.tag-selector {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.selector-header {
  margin-bottom: var(--spacing-md);

  .selector-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
}

.search-box {
  margin-bottom: var(--spacing-md);

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

.tag-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
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

.tag-scroll {
  max-height: 240px;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .chip-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  .chip-check {
    font-size: 12px;
    color: var(--color-primary);
  }

  &.tag-selected {
    background-color: #e6f7ff;
    border: 1px solid var(--color-primary);

    .chip-text {
      color: var(--color-primary);
    }
  }
}

.empty-tags {
  padding: 20px 0;
  text-align: center;

  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.match-mode {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.mode-header {
  margin-bottom: var(--spacing-md);

  .mode-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
}

.mode-options {
  display: flex;
  gap: var(--spacing-md);
}

.mode-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .mode-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }

  &.mode-active {
    background-color: #e6f7ff;
    border: 1px solid var(--color-primary);

    .mode-text {
      color: var(--color-primary);
      font-weight: 500;
    }
  }
}

.search-action {
  margin-bottom: var(--spacing-lg);
}

.btn-search {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 15px;
    color: #ffffff;
    font-weight: 500;
  }

  &.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.search-results {
  .results-header {
    margin-bottom: var(--spacing-md);

    .results-title {
      font-size: 15px;
      font-weight: 500;
      color: var(--color-text-primary);
    }
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
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

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);

  .empty-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-item {
  display: flex;
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  cursor: pointer;

  &:active {
    opacity: 0.8;
  }
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;

  .result-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
}

.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;

  .result-tag {
    padding: 2px 8px;
    background-color: #e6f7ff;
    border-radius: var(--border-radius-sm);
    font-size: 12px;
    color: var(--color-primary);
  }
}

.result-meta {
  .meta-text {
    font-size: 12px;
    color: var(--color-text-secondary);
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
| 1 | 创建 `src/types/tags.ts` | 按第三节定义类型，字段与后端 DDL/Pydantic 100% 对齐 |
| 2 | 创建 `src/api/tags.ts` | 按第四节封装 9 个 API，使用 `API_PATHS` + `request` |
| 3 | 确认 `src/config/api.ts` 路径配置 | TAGS、SESSION.TAGS、ADMIN.SESSION_TAGS 已配置 |
| 4 | 实现 `src/pages/admin/tag/TagList.vue` | 管理端标签列表页，含搜索/新增/编辑/删除 |
| 5 | 实现 `src/pages/admin/tag/TagFormDialog.vue` | 新增/编辑弹窗，slug 必填 |
| 6 | 实现 `src/components/SessionTagSelector.vue` | 场次标签选择器，嵌入场次编辑页 |
| 7 | 实现 `src/pages/user/search/SearchByTag.vue` | 用户端按标签搜索页，AND/OR 模式 |
| 8 | 在 `pages.json` 添加路由 | `/pages/admin/tag/list`、`/pages/user/search/by-tag` |
| 9 | 在管理端 TabBar/菜单添加入口 | 标签管理菜单项 |
| 10 | 在场次编辑页引入 `SessionTagSelector` | 传入 `sessionId` prop |

---

## 九、API 链路总结

### 9.1 标签 CRUD 链路

```
管理端标签列表页
  ├─ fetchData() ──→ getTags({ include_inactive: true })（须带 Admin JWT）
  │                    ──→ GET /content/tags?q=&include_inactive=true
  │                    ──→ 客户端按 全部/启用中/已停用 筛选展示
  │
  ├─ openCreateDialog() → TagFormDialog → POST /admin/tags
  ├─ openEditDialog() → TagFormDialog → PATCH /admin/tags/{tagId}
  ├─ handleDeactivate() → deleteTag(tagId) ──→ DELETE /admin/tags/{tagId}（软停用）
  └─ handleActivate() → updateTag(tagId, { is_active: true }) ──→ PATCH /admin/tags/{tagId}
```

### 9.2 场次标签关联链路

```
SessionTagSelector 组件
  ├─ loadData()
  │    ├─ getTags({ include_inactive: false })
  │    │    ──→ GET /content/tags
  │    │    ──→ ApiResponse<{ items: Tag[] }>
  │    │
  │    └─ getSessionTags(sessionId)
  │         ──→ request.get(API_PATHS.SESSION.TAGS(sessionId))
  │         ──→ GET /content/sessions/{sessionId}/tags
  │         ──→ ApiResponse<Tag[]>
  │
  └─ handleSave() → setSessionTags(sessionId, { tag_ids, mode })
                       ──→ request.post(API_PATHS.SESSION.TAGS(sessionId), data)
                       ──→ POST /content/sessions/{sessionId}/tags
                       ──→ ApiResponse<null>
```

### 9.3 按标签搜索链路

```
SearchByTag 页面
  ├─ loadTags() ──→ getTags({ include_inactive: false })
  │                  ──→ GET /content/tags
  │
  └─ handleSearch() → searchSessionsByTag({ tag_ids, match_all, page, page_size })
                        ──→ request.get(API_PATHS.TAGS.SEARCH_SESSIONS, { data: params })
                        ──→ GET /content/tags/search/sessions?tag_ids=...&match_all=...
                        ──→ ApiResponse<{ total, page, size, items: SearchResultItem[] }>
```

### 9.4 端点-类型-页面 对照表

| 端点 | 方法 | 请求类型 | 响应类型 | 调用页面/组件 |
|------|------|----------|----------|--------------|
| /content/tags | GET | TagListParams | { items: Tag[] } | TagList, SessionTagSelector, SearchByTag |
| /content/tags/{tagId} | GET | - | Tag | 预留详情页 |
| /admin/tags | POST | TagCreate | Tag | TagFormDialog |
| /admin/tags/{tagId} | PATCH | TagUpdate | Tag | TagFormDialog；TagList 启用 |
| /admin/tags/{tagId} | DELETE | - | null | TagList 停用（软删） |
| /content/sessions/{sessionId}/tags | GET | - | Tag[] | SessionTagSelector |
| /content/sessions/{sessionId}/tags | POST | SessionTagsSetRequest | - | SessionTagSelector |
| /content/sessions/{sessionId}/tags/{tagId} | DELETE | - | null | 预留 |
| /content/tags/search/sessions | GET | TagSearchParams | { total, page, size, items: SearchResultItem[] } | SearchByTag |

---

## 十、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | （原） | 初版：类型 / API / TagList·Form·选择器·搜场次可落地样本 |
| v1.0.1 | 2026-09-02 | TagList：启停对齐布局、停用/启用语义、状态筛、停用降透、source 弱标、去页内重标题；`Tag` 增可选 `source`/`created_by`（对齐 V2）；§6.1 / §9.1 与 `src` 对齐 |
