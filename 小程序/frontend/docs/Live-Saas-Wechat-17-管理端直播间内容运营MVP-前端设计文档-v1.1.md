# 管理端直播间内容运营 MVP（Admin Room Content Ops）—— 前端可落地实现文档

**项目**: Live-Saas-Wechat  
**模块编号**: 17  
**版本**: V1.1  
**创建日期**: 2026-07-24  
**修订日期**: 2026-08-08  
**状态**: ✅ 列表/编辑已落地；文案与《18》管理端口径对齐  
**技术栈**: uni-app + Vue 3 + TypeScript + Pinia  
**平台**: 微信小程序

> **后端设计文档**：《17-管理端管播MVP-后端设计文档.md》V1.1（契约）；`is_private` 产品文案与发现层语义以《18-私密测播不公开通道-增量设计文档》V1.1.1 为准  
> **姊妹前端文档**：[《18-私密测播不公开通道-前端设计文档-v1.0》](./Live-Saas-Wechat-18-私密测播不公开通道-前端设计文档-v1.0.md)（小程序测试连接；本文只管 Admin）  
> **关联文档**：《01-科室分类管理》《06-直播间Tab管理》《07-直播间留言》《06-直播间标题与简介-内容安全》《14-管理端用户管理》《通用规范-文件创建规范-v1.0》  
> **零偏差**：类型 / 路径 / 分页字段 `size` / 网关前缀严格对齐后端；写操作**不**新造 Admin 专用写接口

> **原则**：最简单 / 最友好 / 最快落地。P0 =「管理员找得到任意直播间 + 改得了内容」；**不做**强制结束/暂停/踢流等播控（开播未通，见附录 A）。  
> **一句话闭环**：找房 → 改内容 → 离开（不堆播控、不堆测播专页）。

---

## 🚦 操作入口速查（运营必读）

| 目标 | 谁操作 | 入口（小程序） | 关键操作 | 说明 |
|------|--------|----------------|----------|------|
| **找任意直播间** | ADMIN / SUPERADMIN | 个人中心 → **管理功能 → 直播间运营** | 标题搜索 / 房主 UUID / **不公开**筛选 | 走 `GET /admin/rooms`（含 `is_private=true`） |
| **改标题 / 简介 / 不公开** | 同上 | 列表 → **编辑内容** | 弹窗保存 → `PATCH /rooms/{id}` | Admin 可改**他人**房；开关文案用「不公开」 |
| **换封面** | 同上 | 编辑弹窗「换封面」 | `POST /rooms/{id}/cover` | 复用现网 upload |
| **管 Tab** | 同上 | 列表项「Tab」或编辑页入口 | 进入既有 `RoomTabManager` | 复用 06 模块 |
| **设科室** | 同上 | 编辑页「科室」 | `RoomCategorySelector` / 既有 Admin 分类关联 API | 复用 01 |
| **绑品牌** | 同上 | 编辑页「品牌」 | `setAdminRoomBrands` | 复用现网 |
| **清留言 / 管留言** | 同上 | 列表快捷入口 或 **留言管理** | `DELETE .../messages` / 既有留言页 | 复用 07；可带 `room_id` 预填 |
| **删房** | 同上 | 编辑页「删除直播间」 | 二次确认 → `DELETE /rooms/{id}` | 慎用；级联见 16-D4 |
| ❌ 强制结束 / 暂停 / 下架回放 | — | **无入口** | — | P1，附录 A；P0 禁止做按钮 |

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档专注于 **管理端对他人直播间内容的运营能力** 的前端落地：

**包含能力（P0）**:
- **全站房间列表**：标题模糊搜、按房主筛、**含不公开房**、展示 `owner_user_id`；可筛 `is_private`
- **内容编辑**：标题 / 简介 / **不公开**（字段仍为 `is_private`）/ 封面 —— 复用现网房间写接口
- **子资源快捷入口**：Tab / 科室 / 品牌 / 留言 / 删房 —— 复用既有页面与 API
- **权限 UI**：仅 `isAdmin` 可见入口；列表遇 `3003` 友好提示

**不包含（P0 / 非目标封印）**:
- 强制结束直播、暂停、踢流、下架回放、取消预告专用包（播控整包后置，见附录 A）
- 新造 `PATCH /admin/rooms/{id}` 或第二套写路径
- 列表 / 编辑弹窗展示或请求 `stream_key`（后端 Admin 列表亦不返回；推流密钥只走房主侧）
- 场次三态列表 / 播控台
- 小程序「测试连接」主路径（见《18》前端设计；Admin 不另做测播专页）

### 2. 关键网关约定

| 维度 | 值 |
|------|-----|
| 微服务 | `live_core_service` |
| Nginx 网关 | `http://localhost:8080` |
| Core 网关前缀 | `/api/core` |
| **新增**列表完整 URL | `GET http://localhost:8080/api/core/admin/rooms` |
| 详情 / 改 / 删 | `GET/PATCH/DELETE /api/core/rooms/{id}` |
| 封面 | `POST /api/core/rooms/{id}/cover` |
| Tab / 科室 / 品牌 / 留言 | 既有 `/api/core/admin/rooms/{id}/...` |

> ✅ 本包走 **core** 网关（与科室/Tab/留言 Admin 一致）。  
> ❌ 勿写成 `/api/users/admin/rooms`（users 服务无此路由）。

### 3. 与现网前端的差异 / 缺口

| # | 现状 | 本包应补 |
|---|------|----------|
| 1 | 无 `GET /admin/rooms` 封装 | 新增 `getAdminRooms` |
| 2 | 个人中心管理功能无「直播间运营」入口 | `Profile.vue` + `pages.json` 注册 |
| 3 | Admin 改他人房需先知道 roomId（无运营列表） | 新增 `AdminRoomList.vue` |
| 4 | `CreateLive` / `MyLive` 偏房主视角 | **不**强改 CreateLive；运营走专用列表 + 轻量编辑弹窗 |
| 5 | Tab/科室/留言等 Admin 能力已有 | 列表提供跳转/嵌入，**禁止复制第二套 CRUD** |

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《17-管理端管播MVP-后端设计文档》V1.1 | 📋 **契约主文档** | 新列表 Schema、复用写清单、错误码 |
| 1b | 《18-私密测播不公开通道》后端 + 前端设计 | 📖 **文案/语义** | `is_private`=不公开；Admin 仍可见可筛；测播不进本文 |
| 2 | 《01-科室分类管理-前端设计文档》 | 📖 复用 | 科室关联选择器、Admin 列表页骨架 |
| 3 | 《06-直播间Tab管理-前端设计文档》 | 📖 复用 | `RoomTabManager` / `TabEditDialog` |
| 4 | 《07-直播间留言-前端设计文档》 | 📖 复用 | 留言列表 / 清空留言 |
| 5 | 《06-直播间标题与简介-内容安全-前端设计文档-v2.1》 | 📖 错误态 | PATCH 标题/简介 `2004/2005` 人话 |
| 6 | 《14-管理端用户管理-前端设计文档》 | 📖 模板参考 | Admin 入口、权限 UI、对接清单格式 |
| 7 | 《16-D1》 | 📋 约束 | 封禁≠关播；可管孤儿房 |
| 8 | 《测试账号信息.md》 | 📖 联调 | `superadmin` Token |

---

## 一、功能概述

管理端直播间内容运营为运营/管理员提供「全站找房 + 改展示内容」能力。开播链路未通时即可验收。

**前端需实现（P0）**:

1. **直播间运营列表页**：分页、标题 `q`、房主 `owner_user_id`、不公开筛选；加载 / 空 / 错误态  
2. **内容编辑弹窗**：标题、简介、是否不公开、换封面；保存走 `updateRoom` / `uploadRoomCover`  
3. **子模块入口**：跳转/打开既有 Tab 管理、科室选择、品牌绑定、留言管理、删房（二次确认）  
4. **权限门禁**：非 Admin 不可见菜单；进页后若 `3003` 展示无权限  
5. **内容安全**：标题/简介提交失败按《06 内容安全前端》人话 Toast，停留弹窗  

**后端**:
- **0** 张新表  
- **1** 个新 API：`GET /admin/rooms`  
- **N** 个复用 API（见 §九）

**软删除 / 删房**:
- 删房走现网 `DELETE /rooms/{id}`（物理/级联以后端 D4 为准）；前端仅二次确认，不假装「下架」

---

## 二、目录结构

```
src/
├── api/
│   └── room.ts                              # 【追加】getAdminRooms；写接口已有 updateRoom/uploadRoomCover/deleteRoom
├── types/
│   └── adminRoom.ts                         # 【新增】Admin 房间列表类型（对齐 AdminRoomListItem）
├── config/
│   └── api.ts                               # 【追加】ADMIN.ROOMS / ROOM 段已有 DETAIL/UPDATE/COVER
├── pages/
│   ├── admin/
│   │   └── room/
│   │       ├── AdminRoomList.vue            # 【新增】全站房间运营列表
│   │       └── AdminRoomEditDialog.vue      # 【新增】标题/简介/不公开/封面编辑弹窗
│   ├── profile/
│   │   └── Profile.vue                      # 【修改】管理功能增加「直播间运营」入口
│   └── admin/
│       ├── roomTab/RoomTabManager.vue       # 【复用】可从列表带 roomId 打开
│       ├── roomMessage/RoomMessageList.vue  # 【复用】可选预填 room 筛选
│       └── category/… + RoomCategorySelector # 【复用】
└── pages.json                               # 【追加】AdminRoomList 路由
```

> Tab / 科室 / 留言 **不**在本包新建 CRUD 页；仅接入口。

---

## 三、类型定义

> 严格对齐后端 `AdminRoomQueryParams`、`AdminRoomListItem`；字段名、类型 100% 一致。  
> **禁止**与 C 端偏展示的 `Room`（camelCase 历史类型）混用为本列表模型。

```typescript
// src/types/adminRoom.ts

/**
 * 管理端全站房间列表 Query（对应后端 AdminRoomQueryParams）
 */
export interface AdminRoomQueryParams {
  /** 标题模糊搜索，最大 100 字符 */
  q?: string
  /** 房主 public_id（UUID） */
  owner_user_id?: string
  /** 不公开筛选；省略 = 全部（含不公开）；字段名仍为 is_private */
  is_private?: boolean
  page?: number
  /** 后端字段名为 size，非 page_size；1–100 */
  size?: number
}

/**
 * 管理端房间列表项（对应后端 AdminRoomListItem）
 * ⚠️ 不含 stream_key（禁止前端补请求或展示）
 */
export interface AdminRoomListItem {
  id: string
  title: string
  description?: string | null
  cover_url?: string | null
  /** 房主 public_id — 运营定位主播的关键字段 */
  owner_user_id: string
  /** true = 不公开（unlisted）；UI 文案勿写「私密」作主标签 */
  is_private: boolean
  parent_room_id?: string | null
  created_at: string
  updated_at: string
}

/**
 * 管理端房间分页结果（统一分页）
 */
export interface AdminRoomPageResult {
  items: AdminRoomListItem[]
  total: number
  page: number
  size: number
}

/**
 * 运营编辑弹窗本地表单（提交时映射到既有 UpdateRoomRequest）
 * 字段以现网 PATCH LiveRoomUpdate 为准；此处仅列 P0 常用项
 */
export interface AdminRoomEditForm {
  title: string
  description: string
  is_private: boolean
  cover_url?: string | null
}
```

### 3.1 展示映射

| 字段 | 列表展示 | 说明 |
|------|----------|------|
| `title` | 主标题 | 过长截断 |
| `owner_user_id` | 副文案「房主：{uuid 前 8}…」+ 可复制 | **必显**，否则运营无法定位 |
| `is_private` | 标签「不公开 / 公开」 | 与《18》产品语言一致；筛选同文案 |
| `cover_url` | 缩略图；空则占位 | HTTPS 策略同现网封面 |
| `updated_at` | 相对或本地时间 | 列表按此后端排序 |
| `description` | 列表可一行摘要；完整在编辑弹窗 | |

---

## 四、API 封装

> 新接口仅 1 个；写操作全部复用 `src/api/room.ts` 既有函数。

```typescript
// src/api/room.ts —— 追加部分

import type { AdminRoomQueryParams, AdminRoomPageResult } from '@/types/adminRoom'

/**
 * 管理端全站房间列表（含不公开；与 C 端发现层过滤无关）
 * GET /api/v1/admin/rooms → 网关 /api/core/admin/rooms
 * 认证：JWT + ADMIN/SUPERADMIN（非 Admin → 3003）
 */
export const getAdminRooms = (
  params?: AdminRoomQueryParams
): Promise<ApiResponse<AdminRoomPageResult>> => {
  const clean: Record<string, string | number | boolean> = {}
  if (params?.q) clean.q = params.q
  if (params?.owner_user_id) clean.owner_user_id = params.owner_user_id
  if (params?.is_private !== undefined) clean.is_private = params.is_private
  if (params?.page !== undefined) clean.page = params.page
  if (params?.size !== undefined) clean.size = params.size
  return request.get(API_PATHS.ADMIN.ROOMS, { data: clean, showError: false })
}
```

**已有、本包直接复用（勿重复封装）**:

| 能力 | 现有函数 | 路径 |
|------|----------|------|
| 详情回填 | `getRoomById(id)` | `GET /rooms/{id}` |
| 改标题/简介/不公开等 | `updateRoom(id, data)` | `PATCH /rooms/{id}` |
| 换封面 | `uploadRoomCover(id, filePath)` | `POST /rooms/{id}/cover` |
| 删房 | `deleteRoom(id)` | `DELETE /rooms/{id}` |
| 绑品牌 | `setAdminRoomBrands(id, brandIds)` | `POST /admin/rooms/{id}/brands` |
| Tab CRUD | `src/api/tabs.ts` | `/admin/rooms/{id}/tabs*` |
| 科室 | `setRoomCategories` / `removeRoomCategory` | `/admin/rooms/{id}/categories*` |
| 清空留言 | `clearRoomMessages`（roomMessage API） | `DELETE /admin/rooms/{id}/messages` |

### 4.1 Query 参数传递规范

- 分页参数名必须为 **`size`**，禁止 `page_size`  
- 空字符串的 `q` / `owner_user_id` **不要**传给后端（省略字段）  
- `is_private` 仅在用户选择「仅不公开 / 仅公开」时传 `true`/`false`；选「全部」时省略  

---

## 五、config/api.ts 路径配置

```typescript
// src/config/api.ts —— ADMIN 段追加

ADMIN: {
  // ...既有 BIND_ROOM_BRAND / ROOM_TABS 等...

  /** 管理端全站房间列表（17 P0 新增） */
  ROOMS: '/admin/rooms',
},

// ROOM 段已有，确认保留：
ROOM: {
  LIST: '/rooms',
  DETAIL: (roomId: string) => `/rooms/${roomId}`,
  UPDATE: (roomId: string) => `/rooms/${roomId}`,
  DELETE: (roomId: string) => `/rooms/${roomId}`,
  COVER: (roomId: string) => `/rooms/${roomId}/cover`,
  // ...
}
```

> `API_BASE_MAP.ADMIN` / `ROOM` 均为 `core` —— 无需像用户管理那样改 users 网关。

---

## 六、管理端页面实现

### 6.1 列表页 `AdminRoomList.vue`

**路径**: `src/pages/admin/room/AdminRoomList.vue`  
**风格**: 对齐 `UserList` / `CategoryList` / `TagList`（页头筛选 + 卡片列表 + 分页）

**UI 结构**:

1. **页头**：标题「直播间运营」+ 副标题「查找全站房间并修正标题/封面/Tab 等」+ 刷新  
2. **筛选行**：
   - 标题搜索 `q`（confirm / 查询按钮）  
   - 房主 UUID 输入 `owner_user_id`  
   - 可见性 picker：全部可见性 / 仅公开 / 仅不公开  
   - 查询 / 重置  
3. **列表项**（每卡）:
   - 封面缩略图  
   - 标题、不公开/公开标签  
   - 房主 ID（点击复制）  
   - `updated_at`  
   - 操作：`编辑内容` | `Tab` | `留言` | 更多（删房放编辑弹窗内，避免误触）  
4. **态**：无权限 / 加载 / 错误重试 / 空「暂无房间」 / 分页  

**核心脚本约定**:

```typescript
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getAdminRooms } from '@/api/room'
import type { AdminRoomListItem } from '@/types/adminRoom'
import { resolveMediaUrl } from '@/utils/url' // 若项目已有封面 HTTPS 工具则复用

const authStore = useAuthStore()
const accessGranted = computed(() => authStore.isAdmin)

const filters = ref({
  q: '',
  owner_user_id: '',
  privacy: 'all' as 'all' | 'public' | 'private'
})
const page = ref(1)
const size = ref(20)
const total = ref(0)
const list = ref<AdminRoomListItem[]>([])
const loading = ref(false)
const errorMsg = ref('')

async function fetchData() {
  if (!accessGranted.value) {
    errorMsg.value = '需要管理员权限'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const params: Record<string, any> = { page: page.value, size: size.value }
    if (filters.value.q.trim()) params.q = filters.value.q.trim()
    if (filters.value.owner_user_id.trim()) {
      params.owner_user_id = filters.value.owner_user_id.trim()
    }
    if (filters.value.privacy === 'private') params.is_private = true
    if (filters.value.privacy === 'public') params.is_private = false

    const res = await getAdminRooms(params)
    if (res.code === 200 && res.data) {
      list.value = res.data.items || []
      total.value = res.data.total || 0
    } else if (res.code === 3003) {
      errorMsg.value = '需要管理员权限'
    } else if (res.code === 3001) {
      // request 层通常已跳登录；此处兜底
      errorMsg.value = '请先登录'
    } else {
      errorMsg.value = res.message || '加载失败'
    }
  } catch (e: any) {
    errorMsg.value = e?.message || '网络异常，请重试'
  } finally {
    loading.value = false
  }
}

function openEdit(item: AdminRoomListItem) {
  // 打开 AdminRoomEditDialog，传入 item.id；弹窗内再 getRoomById 回填
}

function openTabs(item: AdminRoomListItem) {
  // 方案 A（推荐最快）：navigateTo 带 roomId 的 Tab 管理页（若现网为嵌入组件，则开独立壳页或复用 CreateLive 的 Tab 区仅读 roomId）
  // 方案 B：本页内嵌 RoomTabManager，v-if 显示
  uni.navigateTo({
    url: `/pages/admin/roomTab/RoomTabManagerShell?roomId=${item.id}` // 若无壳页，见 §7.1
  })
}

function openMessages(item: AdminRoomListItem) {
  uni.navigateTo({
    url: `/pages/admin/roomMessage/RoomMessageList?roomId=${item.id}`
  })
}

function copyOwnerId(id: string) {
  uni.setClipboardData({ data: id })
}
```

**鉴权**:
- `onShow`：若未登录 → 跳登录；若已登录非 Admin → 展示无权限空态（与 UserList 一致）  
- **不要**依赖「能打开 CreateLive」代替本列表  

### 6.2 编辑弹窗 `AdminRoomEditDialog.vue`

**职责（P0 最小）**: 改标题、简介、不公开、封面；提供子模块入口与删房。

**打开流程**:

```
列表点击「编辑内容」
  → 传 roomId
  → GET /rooms/{id} 回填（Admin 可读不公开房）
  → 用户改表单（开关文案：不公开 / 公开）
  → PATCH /rooms/{id}（字段仍传 is_private）
  → 可选 POST cover
  → Toast 成功 → emit success → 列表刷新
```

> 开关旁可用一句弱说明：「不公开：不进首页广场；持链接仍可看」（对齐《18》，勿写成「仅房主可看」）。

**表单校验（前端）**:
- `title` 必填、长度按现网 CreateLive / 后端约束（建议与 CreateLive 一致，避免前后端分歧）  
- `description` 可选  
- **不做**前端敏感词预检；拦截交给内容安全后端  

**提交错误处理**（对齐《06 内容安全前端》）:

```typescript
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'
import { updateRoom, uploadRoomCover, getRoomById, deleteRoom } from '@/api/room'

async function handleSave() {
  try {
    const res = await updateRoom(roomId.value, {
      title: form.title.trim(),
      description: form.description,
      // is_private：若现网 UpdateRoomRequest 已支持则带上；否则以后端 LiveRoomUpdate 为准补类型
      ...(typeof form.is_private === 'boolean' ? { is_private: form.is_private } as any : {})
    })
    if (res.code !== 200) {
      if (handleContentSafetyError(res)) return
      uni.showToast({ title: getUserFacingErrorMessage(res, '保存失败'), icon: 'none' })
      return
    }
    uni.showToast({ title: '已保存', icon: 'success' })
    emit('success')
    visible.value = false
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'), icon: 'none' })
  }
}
```

**删房**:
- 按钮文案：「删除直播间」  
- `uni.showModal`：明确「将删除该房间及相关内容，不可恢复」  
- 成功后关闭弹窗并刷新列表  
- **不要**在 P0 做成「强制下播」文案  

**封面**:
- 选图 → `uploadRoomCover` → 用返回 `cover_url` 更新预览  
- 失败 Toast；不清空已有封面  

### 6.3 个人中心入口 `Profile.vue`

在「管理功能」卡片中增加一项（建议放在「留言管理」附近）:

```vue
<view class="menu-item" @tap="handleAdminMenu('admin-rooms')">
  <text class="label">直播间运营</text>
  <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
</view>
```

```typescript
case 'admin-rooms':
  uni.navigateTo({ url: '/pages/admin/room/AdminRoomList' })
  break
```

### 6.4 路由 `pages.json`

```json
{
  "path": "pages/admin/room/AdminRoomList",
  "style": {
    "navigationBarTitleText": "直播间运营",
    "navigationBarBackgroundColor": "#ffffff"
  }
}
```

> `AdminRoomEditDialog` 作为列表页子组件即可，**无需**独立路由。

---

## 七、子模块复用与操作流

### 7.1 建议操作流（对齐后端 §3.2.3）

```
1. Admin 登录（superadmin）
2. 个人中心 → 直播间运营
3. GET /admin/rooms?q=关键字  → 选中房间
4. 编辑内容 → GET /rooms/{id} 回填
5. PATCH /rooms/{id}          → 改标题/简介/不公开（is_private）
6. POST /rooms/{id}/cover     → 换封面
7. 按需：Tab / 科室 / 品牌 / 清留言 / 删房
```

> **完成定义**：运营在 3 步内完成「搜到房 → 改完标题/封面等 → 回到列表」即算本页闭环完成。

### 7.2 Tab 管理接入

| 方案 | 做法 | 选用 |
|------|------|------|
| A | 新增极薄壳页 `RoomTabManagerShell.vue`，`onLoad` 读 `roomId`，内嵌既有 `RoomTabManager` | **推荐**（若现网 Manager 仅组件、无独立路由） |
| B | 列表内 `v-if` 全屏层嵌入 `RoomTabManager` | 亦可，少一路由 |
| C | 跳转 `CreateLive?roomId=` 并滚到 Tab 区 | **不推荐**（CreateLive 过重且偏房主创建流） |

实现时 **只传 `roomId`**，CRUD 仍走 `src/api/tabs.ts`。

### 7.3 科室 / 品牌

- 科室：在编辑弹窗内嵌 `RoomCategorySelector`，保存走既有 Admin `setRoomCategories`  
- 品牌：复用 `setAdminRoomBrands`；选择器可参考 `CreateLive` 品牌多选逻辑（复制交互、不复制房主门禁）  

### 7.4 留言

- 快捷：「留言」→ `RoomMessageList?roomId=`  
- 若列表页暂不支持 query 预填：P0 可先进入留言管理由运营手工筛；预填作为 P0.1 小改  
- 「清空该房留言」：编辑弹窗危险操作区，二次确认后调清空 API  

### 7.5 与 `GET /rooms` 的关系（前端）

| | 通用 `getRooms` | 本包 `getAdminRooms` |
|--|-----------------|----------------------|
| 用途 | C 端/首页等 | **仅**运营后台列表 |
| 字段 | 无稳定 `owner_user_id` | **含** owner 等运营字段 |
| 前端入口 | 禁止用管理功能菜单调用 | 仅 AdminRoomList |

---

## 八、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 新增类型 | `src/types/adminRoom.ts` | 按第三节 |
| 2 | 追加列表 API | `src/api/room.ts` | `getAdminRooms`；写接口复用 |
| 3 | 配置路径 | `src/config/api.ts` | `ADMIN.ROOMS` |
| 4 | 列表页 | `src/pages/admin/room/AdminRoomList.vue` | 筛选 + 分页 + 入口 |
| 5 | 编辑弹窗 | `src/pages/admin/room/AdminRoomEditDialog.vue` | PATCH + 封面 + 删房 |
| 6 | Tab 壳页（如需） | `src/pages/admin/roomTab/RoomTabManagerShell.vue` | 仅当 Manager 无路由时 |
| 7 | 个人中心入口 | `src/pages/profile/Profile.vue` | 「直播间运营」 |
| 8 | 注册路由 | `src/pages.json` | AdminRoomList |
| 9 | 留言预填（可选） | `RoomMessageList.vue` | 读 `roomId` query |
| 10 | 联调自测 | — | 见第十节；重点改**他人**房 |

---

## 九、API 链路总结

### 9.1 路由表（本包相关）

| # | 方法 | 服务内路径 | 网关路径 | 认证 | 前端函数 | 性质 |
|---|------|-----------|---------|------|---------|------|
| 1 | GET | `/api/v1/admin/rooms` | `/api/core/admin/rooms` | JWT+Admin（`verify_admin_role`） | `getAdminRooms` | **新增** |
| 2 | GET | `/api/v1/rooms/{id}` | `/api/core/rooms/{id}` | JWT（Admin 可读不公开房） | `getRoomById` | 复用 |
| 3 | PATCH | `/api/v1/rooms/{id}` | `/api/core/rooms/{id}` | Admin\|owner | `updateRoom` | 复用 |
| 4 | POST | `/api/v1/rooms/{id}/cover` | `/api/core/rooms/{id}/cover` | Admin\|owner | `uploadRoomCover` | 复用 |
| 5 | DELETE | `/api/v1/rooms/{id}` | `/api/core/rooms/{id}` | Admin\|owner | `deleteRoom` | 复用 |
| 6 | * | `/api/v1/admin/rooms/{id}/tabs*` 等 | `/api/core/admin/rooms/{id}/...` | 见子模块 | tabs/categories/brands/messages | 复用 |

### 9.2 错误码映射

| 错误码 | HTTP | 场景 | 前端处理 |
|--------|------|------|----------|
| `200` | 200 | 成功 | 刷新列表 / 关弹窗 |
| `2001` | — | 房间不存在 | Toast「直播间不存在或已删除」 |
| `2004` / `2005` | — | 内容安全等 | `handleContentSafetyError` 人话；停留编辑 |
| `3001` | 401 | Token 无效 | 跳转登录 |
| `3003` | 403 | **新列表**非管理员 | 页内「需要管理员权限」 |
| `3002` | 403 | **复用写**非 Admin 且非 owner | Toast「权限不足」（Admin 正常不应出现；作回归） |
| `4001` | 422 | Query/Body 非法 | 展示后端 message |
| `1002` | 500 | DB | 「服务异常，请稍后重试」 |

> 注意：新列表统一 **`3003`**；写接口保持现网 **`3002`**。前端勿混用提示文案。

### 9.3 端点-页面对照

| 页面/组件 | 调用 |
|-----------|------|
| `AdminRoomList` | `getAdminRooms` |
| `AdminRoomEditDialog` | `getRoomById` / `updateRoom` / `uploadRoomCover` / `deleteRoom` |
| `RoomTabManager` | `tabs.ts` |
| `RoomCategorySelector` | `categories.ts` Admin 关联 |
| 品牌保存 | `setAdminRoomBrands` |
| `RoomMessageList` / 清空 | `roomMessage.ts` |

---

## 十、联调与自测清单

### 10.1 环境

| 项目 | 值 |
|------|-----|
| Nginx 网关 | `http://localhost:8080` |
| Core 前缀 | `/api/core` |
| 测试账号 | 《测试账号信息.md》`superadmin` |
| 前置数据 | 普通用户 A 已有房间 R（`owner_user_id=A`） |

### 10.2 功能测试（对齐后端 §10，前端视角）

| # | 场景 | 预期 |
|---|------|------|
| T1 | 非 Admin 个人中心 | 无「直播间运营」菜单 |
| T2 | Admin 进入列表 | 200，含他人房 + 不公开房 |
| T2b | 筛「仅不公开」 | 仅 `is_private=true`；标签文案为「不公开」 |
| T3 | 无 Token 调列表（抓包） | 401 / 3001 |
| T4 | REGULAR Token 调列表 | 403 / 3003；页内无权限 |
| T5 | `q=标题关键字` | 模糊命中 |
| T6 | `owner_user_id=A` | 仅 A 的房间 |
| T7 | 列表项含 `owner_user_id`、`updated_at` | 字段展示齐全 |
| T8 | 响应无 `stream_key` | 不渲染、不请求该字段 |
| T9 | Admin 编辑**他人**房标题并保存 | 200，列表/详情标题已变 |
| T10 | Admin 改他人房简介 | 200 |
| T11 | Admin 换他人房封面 | 200，预览更新 |
| T12 | Admin 改他人房 Tab | 200（复用 06） |
| T13 | Admin 设他人房科室 | 200（复用 01） |
| T14 | Admin 清空他人房留言 | 200（复用 07） |
| T15 | 敏感词标题 | 内容安全拦截，人话 Toast，不关弹窗 |
| T16 | 非 owner 的 REGULAR 强行 PATCH 他人房 | 403 / 3002（回归） |
| T17 | 删房二次确认后删除 | 列表不再出现该房 |

### 10.3 UI 测试

| # | 场景 | 预期 |
|---|------|------|
| U1 | 空列表 | 空态文案 |
| U2 | 网络错误 | 错误态 + 重试 |
| U3 | 分页边界 | 首页不可上、末页不可下 |
| U4 | 复制房主 ID | 剪贴板成功 Toast |
| U5 | 无强制结束/暂停按钮 | P0 界面不出现播控文案 |

### 10.4 明确跳过（P0）

| 项 | 说明 |
|----|------|
| force-end / 暂停 / 踢流 | 后端附录 A；前端不做入口 |
| 真实推流开播关播 | 依赖开播链路 |

---

## 十一、明确不做与 P1 后置

| 优先级 | 项 | 说明 |
|--------|-----|------|
| ❌ P0 | 播控按钮与 `force-end` 等 API | 见后端附录 A |
| ❌ P0 | `PATCH /admin/rooms/{id}` 双写路径 | 一律 `PATCH /rooms/{id}` |
| ❌ P0 | 列表展示推流密钥 | 后端不返回；前端不展示、不补调含密钥接口 |
| ❌ P0 | 重做 CreateLive 为 Admin 专用 | 轻量编辑弹窗即可 |
| ❌ P0 | Admin 测播 / 测试连接专页 | 主播侧见《18》；运营找房改内容即可 |
| ❌ P0 | 用「私密」作主 UI 文案 | 统一「不公开」；字段名 `is_private` 不变 |
| P1 | 场次三态 Admin 列表 + 强制结束 / 下架回放 | 开播通后另开 `17-P1` 前端增量文档 |
| P0.1 | 留言页 `roomId` query 预填 | 体验增强，非验收阻塞 |
| P0.1 | 从用户管理「跳转并预填 owner_user_id」 | 可选深链：`AdminRoomList?owner_user_id=` |

---

## 十二、文件创建与实现注意

1. **分页**: Query / 响应均为 `size`，与《前端分页实现规范》一致  
2. **封面 URL**: 走现网 HTTPS / `resolveMediaUrl`（或项目等价工具），避免小程序 http 图裂  
3. **showError**: 列表与保存建议 `showError: false`，由页面统一人话处理（尤其内容安全）  
4. **命名**: 页面目录 `admin/room/`，避免与 C 端 `live/`、`my-live/` 混淆  
5. **文案**: 菜单用「直播间运营」；可见性用「不公开 / 公开」；勿用「管播台 / 强制下播」等易误解为播控的 P0 文案  
6. **与《18》分工**: 本文 = Admin 找房改内容；测播双通道 / `test-room` / LiveView 弱提示见《18》前端设计  

### 12.1 现网落地对照（2026-08-08）

| 能力 | 建议文件 | 状态 |
|------|----------|------|
| Admin 列表 + `is_private` 筛 | `AdminRoomList.vue` | ✅ 文案已用「不公开」 |
| 编辑开关 | `AdminRoomEditDialog.vue` | ✅ 「不公开直播间」 |
| 不展示 `stream_key` | 列表/弹窗 | ✅ 勿新增 |
| 复用写 API | `updateRoom` 等 | ✅ |
| 播控入口 | — | ❌ P0 不做 |

---

## 附录 A（P1）— 播控前端占位（非本阶段）

> 与后端附录 A 同步，**本阶段不实现、不注册路由、不做菜单**。

| 能力 | 未来前端入口设想 | 依赖 |
|------|------------------|------|
| 全站场次三态列表 | 「场次运营」页 + bucket Tab | `GET /admin/sessions` |
| 强制结束 | 列表操作「强制结束」+ 强确认 | `POST .../force-end` + 开播链路 |
| 下架回放 | 「下架回放」 | `hide-replay` |
| 取消预告 | 复用删场次 | 禁止删 live |

开播链路就绪后另开增量前端文档，从本附录升级为正文。

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-07-24 | 初始版本：对齐《17-管理端管播MVP-后端设计文档》V1.1；P0=Admin 全站房间列表 + 复用改内容；播控后置 | — |
| V1.1 | 2026-08-08 | 对齐《18》管理端口径：UI「不公开」替「私密」；钉死不泄露 `stream_key`、复用写 API、非目标不含播控/测播专页；互链《18》前端设计；增现网落地对照 | — |

---

**文档结束** ✅
