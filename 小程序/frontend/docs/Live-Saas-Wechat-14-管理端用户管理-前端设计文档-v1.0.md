# 管理端用户管理（Admin Users）—— 前端可落地实现文档

**项目**: Live-Saas-Wechat  
**模块编号**: 14  
**版本**: 1.0.3  
**创建日期**: 2026-07-13  
**状态**: 基线保留（网关/分页骨架）；**业务语义与操作入口以 V2.1 为准**；Admin「品牌成员管理 / 品牌商品治理」前端入口已下线  
**技术栈**: uni-app + Vue 3 + TypeScript + Pinia

> **后端设计文档**：《Live-Saas-Wechat-14-管理端用户管理-后端设计文档-v1.1》  
> **关联文档**：《Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7》、《前端API路径变更同步报告.md》、《通用规范-文件创建规范-v1.0》  
> **零偏差（V1 基线）**：users 网关、`public_id`、`size` 分页；**开播/专家/品牌勿按本文旧「改角色」方案实现**

> **修订说明（2026-07-14 → 1.0.1；2026-07-30 → 1.0.2）**  
> 身份模型、开播能力（`can_stream`）、ADMIN/SUPERADMIN 职责、运营检索、创建直播门禁、专家认领/品牌工作台等，以  
> 《[Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0](./Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md)》**为准**（以下简称 **《V2 前端》**，当前 **2.1.0**）。  
> **V2.1**：默认人人可播；管理端为「禁止开播 / 恢复开播」；用户侧仅禁止时提示「开播功能已被禁用」。  
> 本文档 **仍有效**：users 网关前缀、`public_id` 路径参数、`size` 分页、列表页骨架、§七会员/订阅 Admin（V2 不改）。  
> 下文若写「ADMIN 可改他人 role」「用角色表达主播/专家」「授予开播资格」等，**一律视为已废止**，见《V2 前端》V2.1。  
> **运营怎么点**：见下方「操作入口速查」；完整流程/错误码/测试编号见《V2 前端》§七～§十三。

---

## 🚦 操作入口速查（运营必读 · 对齐 V2）

> 本表只回答「在哪个页面点什么」。实现细节、禁止文案、错误码以《V2 前端》为准。  
> ❌ **不要**在用户管理里用「设为专家 / 设为品牌商 / 设为主播角色」代替下列入口。

| 目标 | 谁操作 | 入口（小程序） | 关键操作 | 对方入口 / 生效注意 |
|------|--------|----------------|----------|---------------------|
| **禁止 / 恢复开播** | ADMIN / SUPERADMIN | 个人中心 → **管理功能 → 用户管理** → 编辑 | 弹窗独立开关「禁止开播 / 恢复开播」（写 `can_stream`，与 role 无关；**次要紧急操作**） | 恢复成功 Toast：**请对方退出并重新登录（或刷新）后再开播**；禁止后对方会话吊销 → 401 |
| **禁用 / 恢复账号** | 同上 | 同上编辑弹窗 | 状态仅日常 `NORMAL` ↔ `BANNED`（**日常停人主路径**） | 封禁后目标用户下次请求 3001/401 → 跳登录；**不自动关房**（需另到直播管理结束房间） |
| **设为管理员 / 取消** | **仅 SUPERADMIN** | 同上编辑弹窗「平台角色」 | 改 `role`（REGULAR/ADMIN/SUPERADMIN）；二次确认 | 普通 ADMIN **看不到**角色 picker；禁止改自己；ADMIN 不可编 SUPERADMIN |
| **用户开直播** | 默认可播（V2.1）；无需运营授出 | — | — | 对方：**个人中心 → 直播管理 → 创建直播**；仅被禁止时灰显并提示「开播功能已被禁用」；**我的直播**可继续管旧房（B5） |
| **绑定「我的专家页」** | ADMIN / SUPERADMIN | 个人中心 → **管理功能 → 专家账号绑定**（亦可从用户编辑「绑定专家页」跳转并预填 ID） | 选择专家 → 填入登录用户 `public_id` → 保存；清空即解绑 | 对方：**个人中心 → 专业与品牌 → 我的专家页**；未绑定显示空态。绑专家 **≠** 改开播开关 |
| **加入品牌工作台** | ADMIN / SUPERADMIN | **前端 Admin 入口已下线**（原「管理功能 → 品牌成员管理」；无小程序治理页） | 后端仍保留 `/api/core/admin/brands/{id}/members*`；成员关系见 `brand_members` | 对方：**个人中心 → 专业与品牌 → 品牌工作台**；非成员空态。**勿**因此升 `ADMIN` |
| **治理已上架商品** | ADMIN / SUPERADMIN | **前端 Admin 入口已下线**（原「管理功能 → 品牌商品治理」；`BrandProductList` 已移除） | 后端仍保留 `/api/core/admin/brand-products*`；成员侧上架见品牌工作台 | 与成员工作台上架正交；无前端治理页 |

**用户侧自助入口（登录后个人中心）**:

| 区块 | 菜单 | 说明 |
|------|------|------|
| 直播管理 | 我的直播 / 创建直播 | 创建受 `canCreateRoom` 门禁 |
| 专业与品牌 | 我的专家页 / 品牌工作台 | P1/P2；与平台 role 正交 |
| 管理功能 | 用户管理、专家账号绑定… | 仅 `isAdmin` 可见；**不含**品牌成员管理 / 品牌商品治理（已下线） |

页面文件对照：《V2 前端》§七；路由已在 `pages.json` 注册。

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档专注于 **管理端用户管理（Admin Users）** 的前端实现**基线**（列表骨架 + users 网关），归属 `user_service` 网关，**不**走 `live_core_service`。

**V1 基线范围**（仍有效）:
- 管理端用户列表（分页 + 筛选骨架）
- 管理端用户 PATCH 路径与 `public_id` 约定

**已被《V2 前端》修订 / 扩展（勿按旧文实现）**:
- 编辑能力拆成：**禁止/恢复开播 `can_stream`**｜**禁用/恢复账号**｜**设为管理员（仅超管）**
- 日常隐藏 `MODERATOR`；仅超管可改 `role`
- 专家认领、品牌工作台（core 网关；Admin 成员/商品治理页已下线，入口见上表）
- **V2.1**：默认可播；开播开关为紧急操作，日常停人用封禁

**关联模块（同 `/api/users/admin/` 前缀，会员体系 · V2 不改 · 仍属后续）**:
- 会员产品管理（`/admin/membership-products`）
- 订阅管理（`/admin/subscriptions/*`）

### 2. 关键网关约定

| 维度 | 值 |
|------|-----|
| 微服务 | `user_service` |
| Nginx 网关 | `http://localhost:8080` |
| Users 网关前缀 | `/api/users` |
| Admin 网关前缀 | `/api/users/admin/` |
| 列表完整 URL | `GET http://localhost:8080/api/users/admin/users` |
| 更新完整 URL | `PATCH http://localhost:8080/api/users/admin/users/{user_uuid}` |

> ❌ **禁止路径**：`/api/core/admin/users` → 转发至 `live_core_service`，返回 **404**（当前联调 404 根因即此）。

### 3. 与现有代码的差异说明

当前仓库已有 `UserList.vue` 与 `getAdminUsers()` 骨架，但存在以下**必须修正**项（本文档以修正后为准）：

| # | 问题 | 现状 | 应改为 |
|---|------|------|--------|
| 1 | 网关归属 | `API_BASE_MAP.ADMIN` → core | 用户管理路径走 **users** 网关 |
| 2 | 角色枚举 | `user/admin/expert` | `REGULAR/MODERATOR/ADMIN/SUPERADMIN` |
| 3 | 状态枚举 | `active/disabled/deleted` | `NORMAL/BANNED/DELETED/PENDING_REVIEW/REJECTED` |
| 4 | 路径参数 | `user_id` | `public_id`（后端字段名 `user_uuid`） |
| 5 | 分页参数 | `page_size` | `size`（后端 Query 名为 `size`） |
| 6 | 邮箱/手机验证筛选 | 前端已传参 | 后端 API 层 **P1 待暴露**，联调前勿依赖 |

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《Live-Saas-Wechat-14-管理端用户管理-后端设计文档-v1.1.md》 | 📋 V1 后端骨架 | 网关、分页、会员 Admin |
| 1b | 《Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md》 | 📋 **业务语义 / 操作入口主文档** | `can_stream`、角色护栏、专家/品牌 |
| 2 | 《Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md》 | 📖 **参考文档** | JWT、request 封装、auth store |
| 3 | 《前端API路径变更同步报告.md》 | 📖 **参考文档** | 网关前缀、联调环境 |
| 4 | 《Live-Saas-Wechat-01-科室分类管理-前端设计文档-v1.0.md》 | 📖 **模板参考** | 管理端列表页结构、对接清单格式 |
---

## 一、功能概述

管理端用户管理为运营/管理员提供全量用户检索与状态管控能力。

**前端需实现（V1 基线 + V2 已落地）**:

1. **用户列表页**：分页展示、多条件筛选（含手机/昵称/`can_stream`）、加载/空/错误态  
2. **用户编辑弹窗**：禁止/恢复开播 + 禁用/恢复账号；**仅超管**可改平台角色（二次确认）  
3. **权限感知 UI**：不可编自己；ADMIN 不可编辑 SUPERADMIN；角色 picker 仅 SUPERADMIN  
4. **网关正确路由**：所有 Admin Users 请求经 `/api/users/admin/*`  
5. **跨模块入口**：专家页认领、品牌工作台——操作入口见文首「操作入口速查」，契约见《V2 前端》（Admin 品牌成员/商品治理页已下线）

**后端数据表**（users 服务侧；专家/品牌在 core）:
- `users`：列表 + PATCH `role` / `status` / `can_stream`（以《后端 V2》为准）
- 专家绑定、品牌成员：走 core，**不要**用 users.role 表达

**软删除策略**:
- 用户注销/禁用通过 `status`（如 `BANNED`、`DELETED`），管理端不物理删除行

---

## 二、目录结构

```
src/
├── api/
│   └── user.ts                          # 已有；追加/修正 Admin Users 函数
├── types/
│   └── adminUser.ts                     # 【新增】管理端用户类型（对齐 UserResponse）
├── config/
│   └── api.ts                           # 修正 ADMIN 用户路径的 baseURL 映射
├── utils/
│   └── request.ts                       # shouldUseUsersGateway 已含 /admin/users
├── store/
│   └── auth.ts                          # 读取当前登录角色，驱动编辑权限 UI
├── pages/
│   └── admin/
│       └── user/
│           └── UserList.vue             # 管理端用户列表 + 编辑弹窗
└── pages.json                           # 路由已注册
```

---

## 三、类型定义

> 严格对齐后端 `UserResponse`、`UserUpdate`、`UserFilterParams` Schema  
> 建议独立文件，避免与 C 端 `UserInfo`（`/me` 响应）混用旧枚举

```typescript
// src/types/adminUser.ts

/** 用户角色 — 对齐后端 user_role 枚举 */
export type AdminUserRole = 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN'

/** 用户状态 — 对齐后端 entity_status 枚举 */
export type AdminEntityStatus =
  | 'NORMAL'
  | 'BANNED'
  | 'DELETED'
  | 'PENDING_REVIEW'
  | 'REJECTED'

/**
 * 管理端用户响应（对应后端 UserResponse）
 * PATCH/GET 列表 items 均使用此结构
 */
export interface AdminUserResponse {
  id: number                    // 内部 BigInt ID，仅展示/debug，不作路径参数
  public_id: string             // UUID — PATCH 路径参数 user_uuid 使用此字段
  username: string
  nickname: string
  email: string | null
  phone_number: string | null
  avatar_url: string | null
  bio: string | null
  role: AdminUserRole
  status: AdminEntityStatus
  is_email_verified: boolean
  is_phone_verified: boolean
  last_login_at: string | null
  last_login_ip: string | null
  social_provider: string | null
  social_id: string | null
  created_at: string
  updated_at: string
}

/**
 * 管理端 PATCH 更新（对应后端 UserUpdate，全部 Optional）
 */
export interface AdminUserUpdatePayload {
  role?: AdminUserRole
  status?: AdminEntityStatus
  nickname?: string
}

/**
 * 管理端列表 Query（对应后端 UserFilterParams + 分页）
 * 注意：is_email_verified / is_phone_verified 后端 CRUD 已支持，API Query P1 待暴露
 */
export interface AdminUserListQuery {
  page?: number                 // 默认 1，≥1
  size?: number                 // 默认 10，1~100；前端建议 20
  sort?: string                 // 预留，当前后端固定 created_at:desc
  username?: string             // 模糊匹配 ILIKE
  email?: string                // 精确匹配
  role?: AdminUserRole
  status?: AdminEntityStatus
  is_email_verified?: boolean   // P1 待后端 API 暴露
  is_phone_verified?: boolean   // P1 待后端 API 暴露
}

/**
 * 管理端分页结果（对应后端统一分页格式）
 */
export interface AdminUserPageResult {
  total: number
  page: number
  size: number
  items: AdminUserResponse[]
}
```

### 3.1 枚举中文映射

```typescript
// 可在 UserList.vue 或 constants 中维护
export const ADMIN_USER_ROLE_LABEL: Record<AdminUserRole, string> = {
  REGULAR: '普通用户',
  MODERATOR: '版主',
  ADMIN: '管理员',
  SUPERADMIN: '超级管理员'
}

export const ADMIN_USER_STATUS_LABEL: Record<AdminEntityStatus, string> = {
  NORMAL: '正常',
  BANNED: '已禁用',
  DELETED: '已注销',
  PENDING_REVIEW: '待审核',
  REJECTED: '已拒绝'
}
```

---

## 四、API 封装

> 严格对齐后端路由表（2 个核心端点）  
> 使用 `API_PATHS.ADMIN_USER`（见第五节），经 users 网关拼接

```typescript
// src/api/user.ts — Admin Users 段（追加或替换现有 getAdminUsers / adminUpdateUser）

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  AdminUserListQuery,
  AdminUserPageResult,
  AdminUserResponse,
  AdminUserUpdatePayload
} from '@/types/adminUser'

/**
 * 管理端用户列表（分页 + 筛选）
 * 网关: GET /api/users/admin/users
 * 服务内: GET /api/v1/admin/users
 * JWT + ADMIN/SUPERADMIN
 */
export const getAdminUsers = (
  params?: AdminUserListQuery
): Promise<ApiResponse<AdminUserPageResult>> => {
  return request.get(API_PATHS.ADMIN_USER.USERS, { data: params })
}

/**
 * 管理员更新用户（角色/状态）
 * 网关: PATCH /api/users/admin/users/{user_uuid}
 * 服务内: PATCH /api/v1/admin/users/{user_uuid}
 * 路径参数为 public_id（非内部 id）
 */
export const adminUpdateUser = (
  userUuid: string,
  data: AdminUserUpdatePayload
): Promise<ApiResponse<AdminUserResponse>> => {
  return request.patch(API_PATHS.ADMIN_USER.USER_DETAIL(userUuid), data, {
    loading: true,
    loadingText: '保存中...'
  })
}
```

### 4.1 Query 参数传递规范

- 使用 `request.get(url, { data: params })`，由 `request.ts` 的 `cleanQueryParams` 过滤 `undefined/null`
- **禁止**传 `page_size`，后端只认 `size`
- 空字符串筛选项不要传给后端

---

## 五、config/api.ts 路径配置

### 5.1 RAW 路径（相对路径）

```typescript
// src/config/api.ts — 新增独立段，与 core 侧 ADMIN 分离

ADMIN_USER: {
  USERS: '/admin/users',
  USER_DETAIL: (userUuid: string) => `/admin/users/${userUuid}`
}
```

### 5.2 网关 Base URL 映射（关键修正）

```typescript
// API_BASE_MAP 中新增（或修正原 ADMIN 用户项）

ADMIN_USER: { baseType: 'users', baseURL: USERS_API_BASE_URL }

// 默认:
// USERS_API_BASE_URL = 'http://localhost:8080/api/users'
// 最终列表 URL = http://localhost:8080/api/users/admin/users
```

> **说明**：原 `ADMIN.USERS` 挂在 `core` 下会导致 `http://localhost:8080/api/core/admin/users` → 404。  
> 用户管理必须从 `ADMIN` 段拆出至 `ADMIN_USER`，或单独为 `/admin/users` 指定 users baseURL。

### 5.3 request.ts 网关选择

`shouldUseUsersGateway()` 已包含 `/admin/users` 前缀判断：

```typescript
// src/utils/request.ts
p.startsWith('/admin/users')  // → users 网关
```

当 `API_PATHS` 传入**相对路径** `/admin/users` 时，`resolveBaseURL` 会正确选择 users 网关。  
若 `API_PATHS` 已被预处理为含 `/api/core/` 的绝对 URL，则网关选择失效——**务必保证 ADMIN_USER 使用 users baseURL 转换**。

---

## 六、管理端页面实现

### 6.1 用户列表页 UserList.vue

**路由**: `pages/admin/user/UserList`（`pages.json` 已注册，`navigationBarTitleText: 用户管理`）

**页面结构**:

| 区域 | 内容 |
|------|------|
| 页头 | 标题「用户管理」 |
| 筛选栏 | 用户名（模糊）、邮箱（精确）、角色 picker、状态 picker |
| 列表 | 头像、昵称/用户名、角色 tag、邮箱、注册时间、状态 tag、编辑按钮 |
| 分页 | 上一页 / 页码 / 下一页（`total`、`page`、`size`） |
| 编辑弹窗 | 角色 picker、状态 picker、取消/保存 |

**交互流程**:

```
onMounted → fetchData()
  → getAdminUsers({ page, size, ...filters })
  → 渲染 items

筛选变更 → currentPage=1 → fetchData()

点击编辑 → openEditPopup(user)
  → 根据当前登录角色过滤可编辑选项
  → 预填 user.role / user.status

保存 → adminUpdateUser(user.public_id, { role, status })
  → 成功 toast → 关闭弹窗 → fetchData()
```

### 6.2 权限感知 UI（对齐后端权限矩阵）

| 当前登录角色 | 目标用户 | 前端行为 |
|-------------|---------|---------|
| ADMIN | REGULAR / MODERATOR / ADMIN | 允许编辑 |
| ADMIN | SUPERADMIN | **隐藏/禁用编辑按钮**；若强行请求 → 403 |
| ADMIN | 角色选项 | 不可选 SUPERADMIN |
| SUPERADMIN | 任意用户 | 允许编辑，含 SUPERADMIN |

```typescript
// 示例：编辑角色选项
function getEditableRoleOptions(currentRole: AdminUserRole): AdminUserRole[] {
  const all: AdminUserRole[] = ['REGULAR', 'MODERATOR', 'ADMIN', 'SUPERADMIN']
  if (currentRole === 'SUPERADMIN') return all
  // ADMIN 登录时不可将他人设为 SUPERADMIN
  return all.filter(r => r !== 'SUPERADMIN')
}

function canEditUser(target: AdminUserResponse, operatorRole: AdminUserRole): boolean {
  if (operatorRole === 'SUPERADMIN') return true
  return target.role !== 'SUPERADMIN'
}
```

### 6.3 列表项主键

- `:key="user.public_id"`（**禁止**使用 `user_id`，管理端响应无此字段）
- PATCH 路径参数：`adminUpdateUser(user.public_id, payload)`

### 6.4 状态展示建议

| status | Tag 样式 | 说明 |
|--------|---------|------|
| NORMAL | 绿色 | 正常 |
| BANNED | 红色 | 已禁用 |
| DELETED | 灰色 | 已注销 |
| PENDING_REVIEW | 橙色 | 待审核 |
| REJECTED | 灰色 | 已拒绝 |

### 6.5 核心脚本片段（对齐后端）

```typescript
// src/pages/admin/user/UserList.vue — script 关键逻辑

import { ref, reactive, computed, onMounted } from 'vue'
import { getAdminUsers, adminUpdateUser } from '@/api/user'
import { useAuthStore } from '@/store/auth'
import type { AdminUserResponse, AdminUserRole, AdminEntityStatus } from '@/types/adminUser'
import { ADMIN_USER_ROLE_LABEL, ADMIN_USER_STATUS_LABEL } from '@/types/adminUser'

const authStore = useAuthStore()
const operatorRole = computed(() => authStore.userInfo?.role as AdminUserRole | undefined)

const users = ref<AdminUserResponse[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  username: '',
  email: '',
  role: '' as AdminUserRole | '',
  status: '' as AdminEntityStatus | ''
})

async function fetchData() {
  loading.value = true
  errorMsg.value = null
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (filters.username) params.username = filters.username
    if (filters.email) params.email = filters.email
    if (filters.role) params.role = filters.role
    if (filters.status) params.status = filters.status

    const res = await getAdminUsers(params)
    if (res.code === 200 && res.data) {
      users.value = res.data.items
      total.value = res.data.total
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载用户列表失败'
  } finally {
    loading.value = false
  }
}

async function handleUpdateUser() {
  try {
    await adminUpdateUser(editingUserUuid.value, {
      role: editForm.role,
      status: editForm.status
    })
    uni.showToast({ title: '更新成功', icon: 'success' })
    closeEditPopup()
    fetchData()
  } catch (err: any) {
    uni.showToast({ title: err.message || '更新失败', icon: 'none' })
  }
}

onMounted(() => fetchData())
```

### 6.6 页面入口与鉴权

- 仅 **ADMIN / SUPERADMIN** 可访问用户管理；普通用户进入应拦截并返回  
- 可在页面 `onShow` 检查 `authStore.isAdmin`  
- 401 / 会话吊销（3001）由 `request.ts` 统一跳转登录页  
- **完整运营入口表**（禁止/恢复开播、专家、品牌工作台）见文首「操作入口速查」；勿在本页用 role 代替 `can_stream` / 品牌成员

---

## 七、关联模块（后续迭代，本期不实现 UI）

同 `/api/users/admin/` 前缀，后端已实现，前端可预留 API 封装：

| 模块 | 网关路径 | 方法 | 说明 |
|------|---------|------|------|
| 会员产品列表 | `/api/users/admin/membership-products` | GET | 分页列表 |
| 创建会员产品 | `/api/users/admin/membership-products` | POST | — |
| 产品详情/更新/删除 | `/api/users/admin/membership-products/{code}` | GET/PATCH/DELETE | — |
| 用户订阅列表 | `/api/users/admin/subscriptions/by-user/{uuid}` | GET | — |
| 手动创建订阅 | `/api/users/admin/subscriptions/by-user/{uuid}` | POST | — |
| 更新订阅 | `/api/users/admin/subscriptions/{uuid}` | PATCH | — |

---

## 八、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 新增管理端用户类型 | `src/types/adminUser.ts` | 按第三节，枚举与后端一致 |
| 2 | 修正 API 封装 | `src/api/user.ts` | Query 用 `size`；PATCH 用 `public_id` |
| 3 | 修正路径配置 | `src/config/api.ts` | 新增 `ADMIN_USER` 段，baseURL 指向 users |
| 4 | 确认网关路由 | `src/utils/request.ts` | `/admin/users` → users 网关 |
| 5 | 重构用户列表页 | `src/pages/admin/user/UserList.vue` | 枚举、主键、权限 UI |
| 6 | 对齐 auth 角色枚举 | `src/types/auth.ts` / `src/store/auth.ts` | ADMIN/SUPERADMIN 判定 |
| 7 | 路由 | `src/pages.json` | 已注册，无需变更 |
| 8 | 联调验证 | — | 见第十节测试清单 |

---

## 九、API 链路总结

### 9.1 后端路由表（Admin Users 核心）

| # | 方法 | 服务内路径 | 网关路径 | 认证 | 前端函数 |
|---|------|-----------|---------|------|---------|
| 1 | GET | `/api/v1/admin/users` | `/api/users/admin/users` | JWT+Admin | `getAdminUsers(params)` |
| 2 | PATCH | `/api/v1/admin/users/{user_uuid}` | `/api/users/admin/users/{user_uuid}` | JWT+Admin | `adminUpdateUser(uuid, data)` |

### 9.2 错误码映射

| 错误码 | HTTP | 说明 | 前端处理 |
|--------|------|------|---------|
| 200 | 200 | 成功 | 正常处理 |
| 2004 | 404 | 用户不存在 | 提示「用户不存在或已被删除」 |
| 3001 | 401 | Token 无效 | `request.ts` 跳转登录 |
| 3002 | 403 | 权限不足 / ADMIN 越权 SUPERADMIN | 提示「权限不足，无法操作该用户」 |
| 4001 | 422 | 参数校验失败 | 展示后端 message |
| 1002 | 500 | 数据库错误 | 提示「服务异常，请稍后重试」 |

### 9.3 404 排查速查

| 请求 URL | 结果 | 原因 |
|---------|------|------|
| `GET /api/users/admin/users` | 401/200 | ✅ 正确路径 |
| `GET /api/core/admin/users` | 404 | ❌ 错误网关（core 无此路由） |
| `GET /api/v1/admin/users`（直连 8002） | 401/200 | ✅ 服务内路径 |

---

## 十、联调与测试清单

### 10.1 环境

| 项目 | 值 |
|------|-----|
| Nginx 网关 | `http://localhost:8080` |
| user_service 直连 | `http://localhost:8002` |
| Users 网关前缀 | `/api/users` |
| 测试账号 | 见《测试账号信息.md》 |

### 10.2 功能测试

| # | 场景 | 预期 |
|---|------|------|
| T1 | ADMIN 登录进入用户管理页 | 200，列表正常展示 |
| T2 | REGULAR 用户访问 | 403 或拦截 |
| T3 | 按 `username` 模糊搜索 | 返回匹配用户 |
| T4 | 按 `role=MODERATOR` 筛选 | ~~日常路径~~ → V2 **隐藏** MODERATOR；勿作主测。改测 REGULAR/ADMIN |
| T5 | 按 `status=BANNED` 筛选 | 仅 BANNED |
| T6 | ADMIN 禁用普通用户 | PATCH 200，列表刷新 |
| T7 | ADMIN 编辑 SUPERADMIN | 前端禁用；强行请求 403 |
| T8 | PATCH 不存在 UUID | 404, code=2004 |
| T9 | 错误路径 `/api/core/admin/users` | 404（回归：确认已修复网关配置） |
| T10+ | 开播开关 / 专家 / 品牌 | **以《V2 前端》§十三 T1–T13 为准**（本表不重复） |

### 10.3 UI 测试

| # | 场景 | 预期 |
|---|------|------|
| U1 | 列表空数据 | 展示空态 |
| U2 | 网络错误 | 展示错误态 + 重试 |
| U3 | 分页 | 上一页/下一页边界正确 |
| U4 | 编辑成功 | Toast + 弹窗关闭 + 列表刷新 |
| U5 | SUPERADMIN 角色选项 | 仅 SUPERADMIN 登录可见 |

---

## 十一、后续待办与文档分工

| 优先级 | 项 | 说明 |
|--------|-----|------|
| — | 禁止/恢复开播 / 角色护栏 / 创建直播门禁 | ✅ 已由《V2 前端》P0 落地（V2.1 默认可播）；入口见文首速查 |
| — | 专家认领、品牌工作台 | ✅ 已由《V2 前端》P1/P2 落地；入口见文首速查 |
| — | Admin 品牌成员管理 / 品牌商品治理页 | **前端已下线**（`BrandMemberManager` / `BrandProductList` 已移除）；后端 members / admin-products API 契约仍见《权威 V2》 |
| P1（会员） | API 暴露 `is_email_verified` / `is_phone_verified` 筛选 | 用户列表可选增强；V2 未做 |
| P1（会员） | 启用 `sort` Query | 列表排序控件 |
| P2（会员） | 单用户 GET 详情 | 可增加详情抽屉 |
| P2（会员） | 会员产品 / 订阅管理 UI | 见 §七；**仍属本文后续**，《V2 前端》明确不改 |

**阅读建议**: 实现/联调用户管理骨架 → 本文；实现开播/专家/品牌或查「点哪里」→ 《V2 前端》+ 文首操作入口速查。

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-07-13 | 初始版本：对齐《Live-Saas-Wechat-14-管理端用户管理-后端设计文档-v1.1》 | — |
| V1.0.1 | 2026-07-14 | 增补「操作入口速查」（授开播、专家绑定、品牌成员/工作台/商品治理）；标废止条款；§一/§十一与 V2 分工对齐 | — |
| V1.0.3 | 2026-08-01 | 下线 Admin「品牌商品管理 / 品牌成员管理」前端入口：操作入口速查与 Profile 管理功能菜单标已下线；保留品牌工作台与后端契约指向 | — |

---

**文档结束** ✅
