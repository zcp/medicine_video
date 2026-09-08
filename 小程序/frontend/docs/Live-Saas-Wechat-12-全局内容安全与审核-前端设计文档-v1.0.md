# 全局内容安全与审核（Content Safety）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia  
> **平台**：微信小程序 + H5 管理端  
> **后端设计文档**：《12-全局内容安全与审核-后端设计文档》V2.3、《13-医学合规文本违禁词库-数据库规则设计文档》V1.0.2  
> **定位**：内容安全**唯一前端上游文档**；各业务 V2/V3 增量文档仅描述页面级接入，规则口径以本文档为准

---

## 一、功能概述

后端在业务 API **写库前**统一执行内容安全校验，**不新增**独立「先调安全 API、再调业务 API」的两段式主路径。前端职责极简：

| 层级 | 职责 | 说明 |
|------|------|------|
| **基础设施** | 统一识别 `2004` / `2005`，**全员**展示人话 Toast | 一处实现，各业务 + 管理端复用 |
| **接口对齐** | 头像 `POST /me/avatar`；`PATCH /me` **不含** `avatar_url` | 见 §四 |
| **管理端** | 检查项列表/编辑 + 检查记录查询 | **仅 ADMIN/SUPERADMIN**；界面文案与 UGC 同一套人话原则 |
| **业务联调** | 各 UGC 入口走 §十 自测清单 | 各增量文档自测项 |

**不在前端范围**：
- 规则引擎、词库 seed、政治/图片第三方 API（后端《12》《13》）
- **users 库** nickname/bio 规则维护（无管理端 HTTP API，不可在 live_core 管理端创建 `scene=nickname` 规则）
- warn（`2006`）对用户**无感知**——HTTP 200 正常成功，前端不弹警告

---

## 二、目录结构

```
src/
├── types/
│   └── contentSafety.ts              # 【新增】规则/日志类型（对齐后端 Schema）
├── api/
│   └── contentSafety.ts              # 【新增】管理端 4 个端点封装
├── utils/
│   ├── contentSafety.ts              # 2004/2005 + 全员文案过滤
│   └── contentSafetyDisplay.ts       # 【新增】管理端 scene/decision 等人话映射 + 技术字段写 logger
├── config/
│   └── api.ts                        # 【修改】新增 CONTENT_SAFETY 路径段
└── pages/
    └── admin/
        └── contentSafety/
            ├── ContentSafetyRuleList.vue       # 【新增】规则列表 + 筛选
            ├── ContentSafetyRuleFormDialog.vue # 【新增】创建/编辑弹窗
            └── ContentSafetyLogList.vue        # 【新增】审计日志列表
```

**业务入口（仅联调改造，见各增量文档）**：

| 场景 | 页面/组件 | 增量文档 |
|------|-----------|----------|
| nickname / bio / 头像 | `ProfileEdit.vue` | 《10-V2-内容安全-前端》 |
| 留言 | `LiveView.vue` | 《07-V2-内容安全-前端》 |
| 标题/简介/Tab | `CreateLive.vue`、`TabEditDialog.vue` | 《06-V2-内容安全-前端》 |
| 搜索词 | `subpackages/search/index.vue` | 《搜索-V3-内容安全-前端》 |

---

## 三、错误码与统一处理

### 3.0 全员用户文案原则（含管理员）

> **管理员也是用户，不是运维/技术人员。** 凡屏幕可见文案（Toast、列表、表单标签、导航标题、菜单项）均不得出现实现术语。

| 层级 | 允许展示 | 禁止展示（示例） | 技术细节去向 |
|------|----------|------------------|--------------|
| **Toast / 错误提示** | 固定人话（§3.2） | `内容违规：…命中…拦截规则`、HTTP 路径 | — |
| **UGC 页面** | 同上 | 规则、拦截、违规、scene、block | — |
| **管理端列表/表单** | 人话标签（§6） | `rule_name`、`target_field`、`match_type`、`pattern` 英文字段名、`block/warn` 原文 | — |
| **管理端检查记录页** | 时间、来源（留言/搜索…）、处理结果（未通过/已记录/已通过）、内容摘要 | `reason_message`、`matched_rule_names`、`normalized_excerpt`、原始 `scene` 枚举 | `logger.info('contentSafety', …)` |
| **开发调试** | — | — | 浏览器/小程序控制台 + 项目 `logger` |

后端 API 响应中的 `message`、`reason_message`、`matched_rule_names` 等字段**仅用于 logger 记录**，任何角色的前端 UI **不得原样渲染**。

### 3.1 业务状态码（内容安全相关）

| code | HTTP | 含义 | 前端行为（**所有角色**） |
|------|------|------|--------------------------|
| `2005` | 422 | 内容被 block | Toast **固定人话**（§3.2）；**保留用户输入** |
| `2004` | 422 | 服务异常 / 限流 | 默认「暂时无法提交，请稍后再试」；限流等人话短 message 可透传 |
| `2006` | — | warn | **不处理**；HTTP 200 视为成功 |
| `4001` | 400/422 | 参数/业务校验 | `getUserFacingErrorMessage` 过滤后展示 |

> **4001 HTTP 说明**：后端《12》§4.2.1 对 PATCH 误传 `avatar_url` 写 `400/4001`，§5.1 对 Pydantic 写 `422/4001`；前端统一按 `code===4001` 处理，不依赖 HTTP 状态码。  
> **注意**：微信小程序 `live-player` 状态码也有 `2004`/`2005`，与 API 业务码**无关**，禁止混用本工具函数。

### 3.2 统一工具

> **全员文案原则**：见 §3.0。工具分两块：`contentSafety.ts`（错误 Toast）、`contentSafetyDisplay.ts`（管理端人话映射 + logger）。

**`src/utils/contentSafety.ts`**：`USER_*_MESSAGE`、`isTechnicalBackendMessage`、`pickUserFacingMessage`、`getUserFacingErrorMessage`、`handleContentSafetyError`

**`src/utils/contentSafetyDisplay.ts`**：`formatSceneLabel`、`formatDecisionLabel`、`formatActionLabel`、`formatBindingLabel`、`logContentSafetyAuditDetail`

完整实现见仓库对应文件。

### 3.3 业务页面接入模式

所有 UGC 提交处统一：

```typescript
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

try {
  await someWriteApi(payload)
  uni.showToast({ title: '保存成功', icon: 'success' })
} catch (e) {
  if (handleContentSafetyError(e)) return   // 2004/2005 已提示（固定/过滤后人话文案）
  uni.showToast({ title: getUserFacingErrorMessage(e, '操作失败，请稍后再试'), icon: 'none' })
}
```

**原则**：
- 提交接口设 `showError: false`，由页面决定 Toast
- block 时**不清空**用户已填内容
- **全员禁止**展示后端审计 message
- 管理端 UI 使用 §6 人话映射；技术字段仅 `logContentSafetyAuditDetail` 写 logger
- `4001` 走 `getUserFacingErrorMessage`

---

## 四、用户资料接口对齐（users 服务）

与《10-V2-内容安全-后端》§4.2.1 严格一致：

| 操作 | 方法 | 网关路径 | 请求体 | 说明 |
|------|------|----------|--------|------|
| 更新文本资料 | PATCH | `/api/users/me` | `{ nickname?, bio? }` | **禁止** `avatar_url` |
| 上传头像 | POST | `/api/users/me/avatar` | `multipart`，字段名 **`file`** | JPG / PNG / WEBP |
| 读取资料 | GET | `/api/users/me` | — | 响应含只读 `avatar_url` |

### 4.1 类型修正（`src/types/auth.ts`）

```typescript
/** PATCH /users/me — 对齐 UserUpdateSelf，不含 avatar_url */
export interface UpdateProfileRequest {
  nickname?: string   // 1-50（V2 Schema，非 V1 的 100）
  bio?: string
  // avatar_url 已移除；头像仅 POST /me/avatar
}

/** POST /me/avatar 成功响应 data */
export interface AvatarUploadResponse {
  avatar_url: string
}
```

### 4.2 API 修正（`src/api/user.ts`）

```typescript
export const uploadAvatar = (filePath: string): Promise<ApiResponse<AvatarUploadResponse>> => {
  return request.upload({
    url: API_PATHS.USER.AVATAR,
    filePath,
    name: 'file',          // 对齐后端 multipart 字段名（非 avatar）
    loading: true,
    loadingText: '上传中...'
  })
}
```

### 4.3 ProfileEdit 流程

1. 选图（`chooseImage` / `chooseMedia`，建议 `sizeType: ['compressed']`）→ `POST /me/avatar`（`file`，JPG/PNG/WEBP）→ 成功后更新本地展示 + `authStore`
2. 点保存 → **仅** `PATCH /me` 提交 `{ nickname, bio? }`，**不**带 `avatar_url`
3. PATCH 若误传 `avatar_url` → `4001`（HTTP 400 或 422），Toast 后端 message

---

## 五、管理端 API 与类型

### 5.1 路径配置（`src/config/api.ts`）

```typescript
CONTENT_SAFETY: {
  RULES: '/admin/content-safety/rules',
  RULE: (ruleId: string) => `/admin/content-safety/rules/${ruleId}`,
  LOGS: '/admin/content-safety/logs'
}
```

网关前缀：`/api/core`（与《12》§1.7 一致）。**无 DELETE**；停用规则设 `enabled=false`。

### 5.2 类型（`src/types/contentSafety.ts`）

> **Schema 版本说明**：《13》§1.2 收窄了 `ContentSafetyRuleUpdate` 可 PATCH 字段，**以《13》为准**，覆盖《12》§2.2 中仍含 `rule_name` / `target_field` / `match_type` 的旧版宽 Schema。

```typescript
/** live_core 管理端可维护的场景（不含 nickname，nickname 规则在 users 库 seed，无管理端 API） */
export type AdminContentScene =
  | 'message'
  | 'room_title'
  | 'room_description'
  | 'room_tab'
  | 'search_query'

/** 全量 scene 枚举（日志筛选/展示用；nickname 仅出现在 users 库日志，不会出现在本管理端规则列表） */
export type ContentScene = AdminContentScene | 'nickname'

export type ContentSafetyAction = 'block' | 'warn' | 'allow'
export type BindingLevel = 'statutory' | 'platform'

export interface ContentSafetyRule {
  id: string
  rule_name: string
  scene: ContentScene
  target_field: string
  match_type: string
  pattern: string
  action: ContentSafetyAction
  severity: 'low' | 'medium' | 'high' | 'critical'
  priority: number
  enabled: boolean
  remark?: string
  binding_level: BindingLevel      // 《13》
  rule_category: string            // 《13》
  regulation_ref?: string          // 《13》
  created_by?: string
  created_at: string
  updated_at: string
}

export interface ContentSafetyRuleCreate {
  rule_name: string
  scene: AdminContentScene         // 禁止 nickname
  target_field: string
  match_type: string
  pattern: string
  action?: ContentSafetyAction
  severity?: ContentSafetyRule['severity']
  priority?: number
  enabled?: boolean
  remark?: string
  binding_level?: BindingLevel     // 默认 platform
  rule_category?: string
  regulation_ref?: string
}

/** PATCH 仅允许更新以下字段（《13》§1.2；不可改 binding_level / rule_category / scene / target_field / match_type） */
export interface ContentSafetyRuleUpdate {
  pattern?: string
  action?: ContentSafetyAction
  severity?: ContentSafetyRule['severity']
  priority?: number
  enabled?: boolean
  remark?: string
}

/** 日志查询参数（对齐《12》§2.3 ContentSafetyLogQueryParams） */
export interface ContentSafetyLogQueryParams {
  scene?: string
  resource_type?: string
  user_id?: string
  decision?: 'allow' | 'warn' | 'block'
  start_time?: string              // ISO 8601
  end_time?: string
  page?: number
  page_size?: number               // 默认 20，最大 100
  rule_category?: string           // P1，《13》§6
}

/** 日志项（对齐《12》§2.3 ContentSafetyLogItem） */
export interface ContentSafetyLog {
  id: string
  scene: string
  resource_type: string
  resource_id?: string
  target_field: string
  user_id?: string
  input_excerpt?: string
  normalized_excerpt?: string
  decision: 'allow' | 'warn' | 'block'
  matched_rule_ids?: string[] | null
  matched_rule_names?: string[]
  reason_code?: string
  reason_message?: string
  client_ip?: string
  created_at: string
}
```

### 5.3 API 封装（`src/api/contentSafety.ts`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `CONTENT_SAFETY.RULES` | Query: `scene?`, `page`, `page_size` |
| POST | `CONTENT_SAFETY.RULES` | 创建 **platform** 规则；`scene` 限 `AdminContentScene` |
| PATCH | `CONTENT_SAFETY.RULE(ruleId)` | 更新；statutory 约束见 §5.4 |
| GET | `CONTENT_SAFETY.LOGS` | Query: `ContentSafetyLogQueryParams` 全字段 |

认证：JWT + `role` 为 **`ADMIN` / `SUPERADMIN`**（与《12》§1.5 `_require_admin` 一致）。非管理员 → `403` / `code=3002`。

### 5.4 管理端 UI 约束（《13》§1.2）

| 规则类型 | 前端禁用/提示 |
|----------|---------------|
| `binding_level=statutory` | 禁用「停用」开关（`enabled=false` → 4001）；`action` 固定 **block**，不可改 warn |
| `rule_category=political_sensitive` | **整段 pattern 只读**，提示「政治敏感词请走第三方 API，禁止管理端改词表」 |
| statutory **且非** political_sensitive | **允许** PATCH `pattern`（法务流程）；UI 加「法定词库，修改需法务确认」警示 |
| `binding_level=platform` | 可编辑 pattern / action（含 warn）/ enabled |
| 创建规则 | 默认 `binding_level=platform`；`scene` / `target_field` / `match_type` / `binding_level` / `rule_category` **创建后不可 PATCH** |
| 停用规则 | 无 DELETE；platform 规则通过 `enabled=false` 停用 |

规则列表增加列：`rule_category`、`binding_level`（法定/平台标签）、`regulation_ref`（tooltip）、`enabled`。

---

## 六、管理端页面设计（人话 UI）

> 管理员与普通用户使用**同一套**文案原则。下列「检查项 / 检查记录」替代「规则 / 审计日志」等术语。

### 6.1 导航与菜单

| 原术语 | 用户可见文案 |
|--------|--------------|
| 内容安全规则 | **内容检查设置** |
| 内容安全日志 / 审计日志 | **内容检查记录** |
| 新建规则 | **新建检查项** |

`Profile.vue` 管理菜单、`pages.json` `navigationBarTitleText` 均用上表文案。

### 6.2 检查项列表 `ContentSafetyRuleList.vue`

**列表展示（人话）**：

| 列 | 展示 |
|----|------|
| 名称 | `remark` 优先；否则「{场景}检查项」 |
| 适用范围 | `formatSceneLabel(scene)` |
| 处理方式 | `formatActionLabel(action)` |
| 状态 | 启用 / 停用 |
| 类型 | 系统预设（statutory）/ 可调整（platform） |

**禁止在列表展示**：原始 `rule_name`、`target_field`、`match_type`、`rule_category` 枚举、`regulation_ref` 原文。

**错误 Toast**：`getUserFacingErrorMessage(e, '加载失败，请稍后再试')`

### 6.3 检查项编辑弹窗 `ContentSafetyRuleFormDialog.vue`

| 表单标签（人话） | 说明 |
|------------------|------|
| 名称 | 对应 `rule_name` |
| 适用范围 | 场景下拉（留言/直播标题…） |
| 关键词或表达式 | 对应 `pattern`；提示「多个词用英文逗号分隔」 |
| 处理方式 | 不允许发布 / 允许发布但记录 |
| 系统预设项不可关闭 | 替代「法定规则不可停用」 |

**禁止**：标签中出现 `pattern`、`block`、`warn`、`scene`、`API` 等英文/实现词。

**保存失败**：`getUserFacingErrorMessage`；statutory 不可停用等人话为「系统预设项不可关闭」。

### 6.4 检查记录 `ContentSafetyLogList.vue`

**列表展示（人话）**：

| 列 | 展示 |
|----|------|
| 时间 | `created_at` |
| 来源 | `formatSceneLabel(scene)` |
| 处理结果 | `formatDecisionLabel(decision)` → 未通过 / 已记录 / 已通过 |
| 内容摘要 | `input_excerpt` |

**禁止上屏**：`reason_message`、`matched_rule_names`、`normalized_excerpt`、原始 `scene`/`decision` 枚举、IP（可选 P1）。

**加载后**：对每条记录调用 `logContentSafetyAuditDetail(item)` 将完整技术字段写入 `logger`，供开发排查。

### 6.5 pages.json

```json
{ "navigationBarTitleText": "内容检查设置" }
{ "navigationBarTitleText": "内容检查记录" }
```

---

## 七、各业务入口索引

| scene | 前端入口 | 触发 API | 增量文档 |
|-------|----------|----------|----------|
| nickname / bio | ProfileEdit | PATCH `/users/me` | 《10-V2-内容安全-前端》 |
| avatar（图片审核） | ProfileEdit | POST `/users/me/avatar` | 同上 |
| message | LiveView 留言区 | POST `/core/rooms/{id}/messages` | 《07-V2-内容安全-前端》 |
| room_title / room_description | CreateLive | 房间创建/更新 | 《06-V2-内容安全-前端》 |
| room_tab | TabEditDialog / CreateLive 简介 Tab | Tab CRUD | 《06-V2-内容安全-前端》 |
| search_query | 搜索页 | **`GET /core/search`**、`/search/suggestions` | 《搜索-V3-内容安全-前端》 |

> **搜索注意**：`GET /rooms?q=` **不在** search_query 校验范围；搜索页须以 `globalSearch` 为门禁，见搜索增量文档。

---

## 八、行动清单

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | 新增 `contentSafety.ts` 工具 | `utils/contentSafety.ts` | 2004/2005 统一 Toast |
| 2 | 修正 `UpdateProfileRequest`、upload `name=file` | `types/auth.ts`, `api/user.ts` | PATCH 不含 avatar_url |
| 3 | ProfileEdit 拆分头像/文本保存 | `ProfileEdit.vue` | §九 #1–6 |
| 4 | 搜索页 `globalSearch` 门禁改造 | `subpackages/search/index.vue` | §九 #10–11 |
| 5 | 留言/创建直播接入 `handleContentSafetyError` | `LiveView.vue`, `CreateLive.vue` 等 | §九 #7–9 |
| 6 | 管理端 API + 3 页面 | `api/contentSafety.ts`, `pages/admin/contentSafety/*` | §九 #13–16 |
| 7 | `AdminContentScene` 类型，创建表单禁 nickname | `types/contentSafety.ts` | 管理端不可建 nickname 规则 |
| 8 | Log 类型/Query 对齐《12》§2.3 | `types/contentSafety.ts` | 含 normalized_excerpt 等 |
| 9 | statutory 非 political 规则 pattern 可编辑 + 警示文案 | `ContentSafetyRuleFormDialog.vue` | §九 #15 |
| 10 | `API_PATHS.CONTENT_SAFETY` | `config/api.ts` | 路径走 core 网关 |
| 11 | 全链路自测 | — | §九 全部勾选 |

---

## 九、联调自测清单（《12》§7.5 前端版）

| # | 入口 | 测试输入 | 预期 UI 行为 | 验证 |
|---|------|----------|--------------|------|
| 1 | ProfileEdit 昵称 | `张医生` | 保存成功 | [ ] |
| 2 | ProfileEdit 昵称 | `http://a.com` | Toast「暂无法发布，请修改内容后再试」，表单保留；**不出现**规则名/违规等词 | [ ] |
| 3 | ProfileEdit 昵称 | `13800138000` | 同上 2005 | [ ] |
| 4 | ProfileEdit bio | 「根治」等医学违禁词 | 2005 Toast | [ ] |
| 5 | ProfileEdit 头像 | 正常 JPG/PNG 图 POST /me/avatar | 头像即时更新 | [ ] |
| 6 | ProfileEdit 头像 | stub reject 违规图 | 2005，头像不变 | [ ] |
| 7 | LiveView 留言 | `加V领取` | 2005，输入框保留 | [ ] |
| 8 | CreateLive 标题 | 含手机号 | 2005，表单保留 | [ ] |
| 9 | TabEditDialog 正文 | 含外链 | 2005 | [ ] |
| 10 | 搜索 | `www.xxx.com` | 2005；**无**结果 Tab；**无**本地/服务端历史；关键词保留 | [ ] |
| 11 | 搜索 | `心血管` | 正常结果（先过 `/search` 再拉 `/rooms` 等） | [ ] |
| 12 | 任意入口 | 后端模拟 2004 | Toast「暂时无法提交，请稍后再试」（**无**「内容安全/校验」等词） | [ ] |
| 13 | 管理端检查设置 | 打开列表 | 标题「内容检查设置」；列表**无** rule_name/英文字段名 | [ ] |
| 14 | 管理端检查设置 | 系统预设项点停用 | Toast「系统预设项不可关闭」等人话 | [ ] |
| 15 | 管理端检查记录 | 打开列表 | **无** reason_message / 命中规则；控制台 logger 有完整技术字段 | [ ] |
| 16 | 管理端检查记录 | 筛选「未通过」 | 标签为人话，非 block | [ ] |
| 17 | 管理端 | 新建检查项 scene 下拉 | **无** nickname | [ ] |
| 18 | 留言 warn | 命中 warn 词 | HTTP 200，留言成功，用户无感知 | [ ] |

**典型测试词（与后端 seed 对齐）**：

| 类型 | 示例 |
|------|------|
| 外链 | `http://abc.com`、`www.xxx.com` |
| 联系方式 | `13800138000` |
| 广告引流 | `加V`、`私聊返利` |
| 敏感词/医学 | `根治`、`100%有效`、`台独`（本地兜底） |

---

## 十、全员人话改造 — 代码改动清单（按步骤执行）

| 步骤 | 文件 | 改动要点 | 状态 |
|------|------|----------|------|
| **1** | `docs/12`～`07/06/10/搜索` 前端设计文档 | §3.0 全员原则；§6 管理端人话 UI | 文档 |
| **2** | `src/utils/contentSafetyDisplay.ts` | scene/decision/action 人话映射；`logContentSafetyAuditDetail` | 代码 |
| **3** | `src/pages/admin/contentSafety/ContentSafetyRuleList.vue` | 标题/列表/Toast 人话；隐藏技术列 | 代码 |
| **4** | `src/pages/admin/contentSafety/ContentSafetyRuleFormDialog.vue` | 表单标签/Toast 人话 | 代码 |
| **5** | `src/pages/admin/contentSafety/ContentSafetyLogList.vue` | 仅展示人话列；技术字段写 logger | 代码 |
| **6** | `src/pages/profile/Profile.vue` | 管理菜单文案 | 代码 |
| **7** | `src/pages.json` | 导航栏标题 | 代码 |
| **8** | UGC 页（已完成） | `LiveView` / `ProfileEdit` / `CreateLive` / `TabEditDialog` / `search` | 代码 |
| **9** | `test/roomMessage.contentSafety.test.ts` + 新增 display 测试 | 人话映射 + 过滤 | 自测 |

---

## 十一、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.2 | 2026-07-09 | **全员人话**：管理员同用户；技术字段仅 logger；§6 管理端 UI 重写；§10 改动清单 |
| V1.1 | 2026-07-09 | Toast 固定人话，禁止透传后端审计 message |
| V1.0 | 2026-07-04 | 初版 |

---

**文档结束** ✅
