# 标签管理（Tag）—— 前端设计文档（V2 增量）

**项目**: Live-Saas-Wechat  
**模块编号**: 02（前端增量）  
**版本**: V2.0  
**创建日期**: 2026-09-02  
**状态**: 📋 设计定稿（待实施）  
**技术栈**: uni-app + Vue 3 + TypeScript  
**平台**: 微信小程序  

**基于**:  
- [《02-标签管理-V2-增量设计文档》](./02-标签管理-V2-增量设计文档.md) V2.0（**本版契约真源**）  
- [《Live-Saas-Wechat-02-标签管理-前端设计文档-v1.0》](./Live-Saas-Wechat-02-标签管理-前端设计文档-v1.0.md)（Admin CRUD / 公开列表 / 搜场次基线；未标注处仍以 V1 为准）  
- [《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》](./Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0.md) §3（resolve 的 2004/2005 人话）  

> **一句话闭环**：开播者在 CreateLive 选/建 ≤5 个标签 → 保存时只提交 UUID → 离开。  
> **完成定义**：阶段 1 权限与 `0～5` 已可对后端；阶段 2「创建并使用」走 `POST /content/tags/resolve`，禁止伪造 UUID、禁止普通用户调 `/admin/tags`。  
> **采用方案（最小化、最友好）**：在现有 `CreateLive.vue` 补丁接 resolve；`api/tags` + `types/tags` + `API_PATHS` 增量补齐；Admin `TagList` 仅弱展示 `source`（已有则保持）。**不**重写 V1 全文、不新开并行选择器页。

**体验钉五问**（[AI-工作约定 §5.1](./AI-工作约定.md)）：

| # | 问 | 答 |
|---|-----|-----|
| 1 | 给谁用 | **房主/开播者**（CreateLive）；**Admin**（TagList 词表，弱展示 source） |
| 2 | 闭环/完成定义 | 选或 resolve ≤5 → replace 保存 → 离开；见上文 |
| 3 | 首屏只留 | chip 计数 + draft/联想 +「从词库选择」；不堆治理筛 |
| 4 | 空/满/无权限 | 空：占位「暂未关联」；满 5：Toast；403：无权改场次标签；resolve 2005：人话保留输入 |
| 5 | 非目标 | 见 §3.2（禁止用户调 admin、伪造 UUID、内联 tag_names 等） |
---

## 📋 目录

1. [重要声明](#一重要声明)
2. [背景与目标](#二背景与目标)
3. [范围定义](#三范围定义)
4. [术语与关键概念](#四术语与关键概念)
5. [与 V1 前端 / 后端 V2 的关系](#五与-v1-前端--后端-v2-的关系)
6. [核心流程](#六核心流程)
7. [页面与交互设计](#七页面与交互设计)
8. [涉及文件与落点](#八涉及文件与落点)
9. [API 封装约定](#九api-封装约定)
10. [数据结构与字段约定](#十数据结构与字段约定)
11. [权限与可见性](#十一权限与可见性)
12. [错误处理与兜底](#十二错误处理与兜底)
13. [现码差集（实施前对照）](#十三现码差集实施前对照)
14. [实施分期](#十四实施分期)
15. [测试要点](#十五测试要点)
16. [检查清单](#十六检查清单)
17. [更新日志](#更新日志)

---

## 一、重要声明

- **本文档是对前端 V1.0 的增量扩展，不是替代或覆盖**
- **V1 中 Admin CRUD、公开 `GET /content/tags`、按标签搜场次等未标注内容保持不变**
- **变更已标【新增】【修改】【保持】【禁止】**；未标注处以 V1 前端 + 后端 V1 为准
- **零偏差**：字段名、路径、method、必填/可选、长度、枚举、响应 `data` 形状严格对齐 [后端 V2](./02-标签管理-V2-增量设计文档.md) §2 / §3 / §7；禁止发明字段或本地伪造 UUID
- **后端状态**（据 V2 文首）：阶段 1 ✅、阶段 2 ✅（含 `tag_name` 内容安全 + bind 拒 inactive）；本仓待办为前端对接

---

## 二、背景与目标

### 2.1 问题

| 现状 | 后果 |
|------|------|
| 后端已允许**房主或 Admin**绑场次标签，且 `tag_ids` **0～5** | 前端须按房主 Token 提交；一次最多 5；`replace` + `[]` 可清空 |
| 后端已提供 `POST /content/tags/resolve` | CreateLive 未匹配词库时仍只能「请从词库选择」，自建卡死 |
| `TagItem` 可选返回 `source` / `created_by` | Admin 列表可弱标来源；公开联想语义不变 |

### 2.2 目标

1. **阶段 1 对齐**：CreateLive 提交 `{ tag_ids: UUID[], mode: 'replace' }`，长度 0～5；权限依赖后端（房主/Admin）。  
2. **阶段 2 对齐**：未命中词库 →「创建并使用」→ `resolve(name)` → 用返回 `id` 进 chip → 再绑场次。  
3. **内容安全**：仅 resolve 写路径接 2005/2004 人话；Admin CRUD 本期不强制前端预检。  
4. **工程约束**：增量改现有文件；不平行造第二套标签域。

### 2.3 业务价值

- 开播自助打标，提升发现质量。  
- 词库可补全，避免「只能选已有」。  
- 自建与 Admin CRUD 分离，控制权限面。

---

## 三、范围定义

### 3.1 做什么

| 类型 | 项 | 依据 |
|------|-----|------|
| 【修改】 | CreateLive：chip ≤5；`replace` 提交；未匹配 → resolve 后使用 | V2 §3.1 / §3.4 / §3.6 |
| 【新增】 | `API_PATHS.TAGS.RESOLVE` + `resolveTag()` | V2 §3.4 |
| 【新增】 | 类型 `TagResolveRequest` / `TagResolveData` | V2 §2.2 |
| 【修改】 | `Tag` 可选 `source` / `created_by`（读侧弱展示） | V2 §2.3 |
| 【修改】 | `removeSessionTag` 注释/权限口径：房主或 Admin（与 set 对齐） | V2 §3.2 |
| 【保持】 | Admin `TagList` / `TagFormDialog` 走 `/admin/tags` | V2 §3.5 |
| 【保持】 | `GET /content/tags?q=` 联想 | V2 §3.3 |
| 【保持】 | 按标签搜场次等 V1 能力 | V1 前端 |

### 3.2 不做什么（非目标封印）

| 永不做（本版） | 原因 |
|----------------|------|
| 普通用户调 `POST/PATCH/DELETE /admin/tags` | V2 决策 3 / §3.6 禁止 |
| 绑标签 Body 内联 `tag_names` | V2 决策 3：MVP 不做 |
| 本地伪造 / 临时 UUID 当 `tag_ids` | 契约只收真实 UUID |
| 模糊合并同义词、软删名自动复活 | V2 决策 5 |
| 发现层按标签推荐算法 | 超出增量 |
| 重写 Admin 列表为运营大台（多维筛选 source/created_by 必做） | V2 仅 DDL 索引；本版 Admin 弱标即可，强筛另开需求 |
| 前端预校验违禁词代替后端 | 与《12》一致：写库前后端统一检 |
| 新建独立 `SessionTagSelector` 页替代 CreateLive 内联（若现码已内联） | 最小化；可后续抽取，非本版必做 |

### 3.3 完成定义（防填洞）

| 角色 | 几步内算完成 |
|------|----------------|
| 开播者 | 输入/联想/词库选 →（可选）创建并使用 → 保存场次带 ≤5 UUID → 离开 |
| Admin | 仍按 V1 管词表；列表可见 `source` 弱标（有则显示） |
| 本页永不做 | 用户改名/硬删全局标签；同义词治理；推荐算法 |

---

## 四、术语与关键概念

| 术语 | 含义 |
|------|------|
| resolve | `POST /content/tags/resolve`：按名精确匹配或创建；返回 `id` + `created` |
| chip | CreateLive 已选标签展示单元；对应一个真实 `tag_id` |
| 房主 | `live_rooms.user_id == 当前用户`；可写该房下场次标签 |
| source | `admin` = 运营创建；`user` = resolve 创建 |
| replace / append | 设标签 mode；开播主路径固定 **`replace`**（幂等覆盖） |
| SESSION_TAGS_MAX | 常量 **5**（与后端 `SESSION_TAGS_MAX` 一致） |

---

## 五、与 V1 前端 / 后端 V2 的关系

| 文档 | 本版用法 |
|------|----------|
| 前端 V1.0 | Admin CRUD、公开读、搜场次、目录骨架；冲突时**写路径以本 V2 为准** |
| 后端 V2 | Endpoint / Schema / 错误码 / 流程真源 |
| 《12》前端 | resolve 失败时 `handleContentSafetyError` |

**冲突裁决**：

1. 绑/删标签权限与 `tag_ids` 长度 → **后端 V2**  
2. resolve 安全 HTTP → **后端 V2 §3.4（422 + 2005/2004）**；文案 → 《12》§3  
3. 与**已上线代码**不一致 → 实施时标偏差并按本设计改代码，不得 silently 改契约含义  

---

## 六、核心流程

### 6.1 开播打标（阶段 1+2 串联）

对齐后端 V2 §4.2：

```
1. GET /content/tags?q=…（或全量词库缓存）联想 / 词库选择
2. 用户确认新词 → POST /content/tags/resolve { name }
3. 本地 chip 收集 UUID（≤5）；可删 chip
4. 场次已存在后 → POST /content/sessions/{session_id}/tags
      Body: { tag_ids: [...], mode: "replace" }
   （新建场次：先创建 session，再 set；与现 CreateLive 保存顺序一致即可）
```

### 6.2 resolve 成功分支

| `data.created` | UI |
|----------------|-----|
| `true` | 静默加入 chip（可选短 Toast「已创建并使用」）；把 `{ id, name }` 合并进本地 `tagOptions` |
| `false` | 静默加入 chip（复用已有）；合并本地选项 |

### 6.3 清空标签

`selectedTagIds = []` → 保存时 `POST …/tags` + `{ tag_ids: [], mode: "replace" }`（合法，对齐 V2 §2.1 / §3.1）。

---

## 七、页面与交互设计

### 7.1 CreateLive（主落点）

**入口**：创建/编辑直播页标签区（现有 chip + draft + 词库弹层）。

| 交互 | 行为 | 约束 |
|------|------|------|
| 计数 | 展示「已选 N/5」 | N ≤ 5 |
| draft 确认（`#`/空格/添加） | 精确名命中本地词库 → 直接加 chip | 不调用 resolve |
| draft 未命中 | 【阶段 2】弹出确认：「创建并使用「xxx」？」→ 是则 `resolveTag` | 否：保持原提示或仅清空该 token |
| 联想点击 | 加已有 id | 同阶段 1 |
| 词库选择器 | 多选 toggle；达 5 禁止再加并 Toast | 同阶段 1 |
| 移除 chip | 从 `selectedTagIds` 删除 | 本地操作 |
| 保存 | 仅提交真实 UUID 列表 + `mode: 'replace'` | 禁止提交 name |

**前端本地校验（提交前，弱于契约不可）**：

| 项 | 规则 |
|----|------|
| 数量 | `tag_ids.length` ∈ [0, 5] |
| 去重 | 提交前 `unique`；重复不传 |
| name（仅 resolve） | `trim` 后 1～80；禁空；前端可拦 `<>'";`（与 V2 validator 一致），最终以后端为准 |
| Admin name | 仍按 V1 Admin 表单（可达 100）；**与 resolve 80 上限不同，勿混用** |

**文案（建议）**：

| 场景 | 文案 |
|------|------|
| 已满 5 | 「最多选择 5 个标签」 |
| 未匹配且未开阶段 2 | 「未在词库：…，请从词库选择」（现码可保留至阶段 2 上线） |
| 确认自建 | 「词库中没有「{name}」，创建并使用？」 |
| 软删名占用（400/4001） | 「该标签不可用，请换一个名称」 |
| 非房主 403 | 「无权修改该场次标签」 |

### 7.2 Admin TagList（弱增量）

| 项 | 约定 |
|----|------|
| CRUD | 仍 `/admin/tags`；不改为 resolve |
| `source` | 有值则弱标「运营 / 用户自建」；无字段则不显示 |
| `created_by` | 本版不强制展示 UUID；治理筛选项封印 |
| 停用 | 仍软删 `is_active`；与 V1 一致；**不停毁文案** |

### 7.3 其他页

| 页 | 本版 |
|----|------|
| 按标签搜场次 | 【保持】V1 |
| LiveView 等只读展示场次标签 | 【保持】读 `GET …/sessions/{id}/tags`；不写 resolve |

---

## 八、涉及文件与落点

```
src/config/api.ts                 # 【新增】TAGS.RESOLVE
src/types/tags.ts                 # 【新增】TagResolve*；【确认】Tag.source/created_by；【注释】SessionTagsSet 0～5
src/api/tags.ts                   # 【新增】resolveTag；【修改】set/remove 注释口径
src/pages/live/CreateLive.vue     # 【修改】未匹配 → resolve；错误处理；MAX=5（已有则保持）
src/pages/admin/tag/TagList.vue   # 【保持/微调】source 弱标（已有则不再扩）
```

**可选（非必须）**：若后续抽取，再新增 `components/SessionTagSelector.vue`；本版以 CreateLive 内联为准。

**禁止新增**：第二套 `api/tagUser.ts`、假 UUID 工具、用户侧 Admin 创建封装。

---

## 九、API 封装约定

> 使用 `request` from `@/utils/request`；`ApiResponse<T>`；路径进 `API_PATHS`。  
> 网关前缀由现有 core baseURL 处理；下表 path **不含** `/api/v1` 时与现仓 `API_PATHS` 风格一致。

### 9.1 路径表（本版相关）

| # | 变更 | Method | Path（相对 core） | 权限 | 说明 |
|---|------|--------|-------------------|------|------|
| A | 【修改行为】 | POST | `/content/sessions/{sessionId}/tags` | JWT 房主或 Admin | Body: `SessionTagsSetRequest` |
| B | 【修改行为】 | DELETE | `/content/sessions/{sessionId}/tags/{tagId}` | JWT 房主或 Admin | 单条移除 |
| C | 【保持】 | GET | `/content/tags` | 公开（Admin 可带 `include_inactive`） | Query: `q?` `search_type?` `include_inactive?` |
| D | 【新增】 | POST | `/content/tags/resolve` | JWT（MVP：已登录） | Body: `{ name }` |
| E | 【保持】 | POST/PATCH/DELETE | `/admin/tags…` | Admin | V1 CRUD |

### 9.2 【新增】resolve 封装（摘录）

```typescript
// src/config/api.ts — TAGS 内
RESOLVE: '/content/tags/resolve'

// src/api/tags.ts
/** POST /content/tags/resolve — 解析或创建（用户侧）；禁止用 admin CREATE 代替 */
export const resolveTag = (
  data: TagResolveRequest
): Promise<ApiResponse<TagResolveData>> => {
  return request.post(API_PATHS.TAGS.RESOLVE, data, {
    loading: true,
    loadingText: '处理中...',
    showError: false // 由页面接内容安全人话
  })
}
```

**请求字段（必要摘录）**：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `name` | string | 是 | 1～80；服务端 strip；禁 `<>'";` |

**成功 `data`（必要摘录）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 标签 id |
| `name` | string | 规范化后的名称 |
| `created` | boolean | `true`=本次新建；`false`=命中已有 |
| `source` | string \| null/omit | 可选；`admin` \| `user` |

### 9.3 【修改】设场次标签（摘录）

```typescript
export const setSessionTags = (
  sessionId: string,
  data: SessionTagsSetRequest
): Promise<ApiResponse<{ session_id: string; tags: Array<{ tag_id: string; tag_name: string; tag_slug: string }> }>> => {
  return request.post(API_PATHS.SESSION.TAGS(sessionId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}
```

**请求字段（必要摘录）**：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `tag_ids` | string[] | 是 | **0～5**；元素 UUID；列表内不重复；`[]` + replace = 清空 |
| `mode` | `'replace' \| 'append'` | 是 | CreateLive 固定 `'replace'` |

**响应**：沿用现网/V1 形状（`session_id` + `tags` 简要列表）；本版不改解析字段名。

### 9.4 公开列表（联想）

| Query | 必填 | 说明 |
|-------|------|------|
| `q` | 否 | 关键词 |
| `search_type` | 否 | `name` \| `slug` \| `description` |
| `include_inactive` | 否 | 仅 Admin；开播侧**不要**传 true |

`data` 兼容：`{ items }` / 分页包 / `TagItem[]`（与现 `getTags` 一致）。

---

## 十、数据结构与字段约定

### 10.1 【新增】Resolve 类型

```typescript
/** 对齐后端 TagResolveRequest */
export interface TagResolveRequest {
  name: string
}

/** 对齐后端 TagResolveData */
export interface TagResolveData {
  id: string
  name: string
  created: boolean
  source?: string | null
}
```

### 10.2 【修改】Tag 溯源（可选读字段）

```typescript
export interface Tag {
  id: string
  name: string
  slug: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
  /** V2 可选 */
  source?: 'admin' | 'user' | string
  created_by?: string | null
}
```

- 写 Admin `TagCreate` / `TagUpdate`：**不**要求前端传 `source`/`created_by`（后端自填）。  
- 禁止把 `source` 塞进 resolve Body。

### 10.3 SessionTagsSetRequest

```typescript
export interface SessionTagsSetRequest {
  tag_ids: string[]  // 0～5
  mode: 'replace' | 'append'
}
```

前端常量：`export const SESSION_TAGS_MAX = 5`（`types/tags.ts` 或 CreateLive 内一处即可，避免魔法数分叉）。

---

## 十一、权限与可见性

| 操作 | 前端条件 | 后端最终裁决 |
|------|----------|--------------|
| resolve | 已登录（JWT） | MVP 已登录即可；后期可能收紧 |
| set/remove 场次标签 | 编辑自己的直播/场次；Admin 工具另议 | 房主或 Admin，否则 403/3003 |
| Admin CRUD | `isAdmin` 路由守卫 | Admin/SuperAdmin |
| 公开 GET tags / 场次 tags | 可未登录 | 非 Admin 仅 active |

前端**不得**用隐藏按钮代替权限；403 须可读提示。

---

## 十二、错误处理与兜底

### 12.1 码表（本版消费）

对齐后端 V2 §3.4 / §7 + 《12》前端：

| code | HTTP（典型） | 场景 | 前端 |
|------|--------------|------|------|
| 2005 | 422 | resolve 内容安全 block | `handleContentSafetyError`；保留 draft/name |
| 2004 | 422 | 内容安全服务异常 | 同上 |
| 4001 | 400 | 超 5、软删名占用、参数非法 | Toast 人话；超 5 应本地先拦 |
| 3003 | 403 | 非房主写标签 | 「无权修改该场次标签」 |
| 3001 | 401 | 未登录 | 走现有登录引导 |
| 2001 | 404 | 场次/标签不存在 | 通用失败文案 |
| 1002 | 500 | 内部错误 | 「请稍后再试」 |

> 说明：V2 §7 表将「安全拦截」亦列在 4001 下；**resolve 安全以 §3.4 的 422/2005·2004 为准**。页面用 `handleContentSafetyError` 优先识别 2005/2004。

### 12.2 CreateLive 伪代码

```typescript
import { resolveTag, setSessionTags } from '@/api/tags'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

async function createAndUseTag(rawName: string) {
  const name = rawName.trim()
  if (!name || name.length > 80) {
    uni.showToast({ title: '标签名称不合法', icon: 'none' })
    return
  }
  try {
    const res = await resolveTag({ name })
    const data = res.data
    if (!data?.id) throw new Error('empty resolve')
    // 合并 tagOptions + tryAddTagId(data.id)
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({
      title: getUserFacingErrorMessage(e, '无法使用该标签'),
      icon: 'none'
    })
  }
}
```

设标签失败同理：`handleContentSafetyError` 一般不命中（bind 侧主要是 4001 inactive）；按 `getUserFacingErrorMessage` 兜底。

### 12.3 inactive 标签

后端 bind **拒绝** `is_active=false`。前端：

- 开播词库只拉默认公开列表（不含 inactive）。  
- 若编辑回填出现已停用标签：展示但保存前可提示用户更换；或以保存错误文案为准（不发明解绑专用 API）。

---

## 十三、现码差集（实施前对照）

> 只读快照（2026-09-02）；实施时再核对，以本文 + 后端 V2 为准。

| 项 | 文档要求 | 现码倾向 | 实施动作 |
|----|----------|----------|----------|
| `POST …/tags/resolve` | 必需 | `api/tags` / `API_PATHS` **缺** | 【新增】 |
| `TagResolve*` 类型 | 必需 | **缺** | 【新增】 |
| CreateLive ≤5 + replace | 必需 | **已有** `MAX_SESSION_TAGS=5` + replace | 【保持】 |
| 未匹配自建 | resolve | Toast「请从词库选择」 | 【改】确认 → resolve |
| `Tag.source` / `created_by` | 可选读 | types **已有**；TagList **已弱标** | 【保持】 |
| set 权限注释 | 房主或 Admin | 注释仍偏 Admin/待放宽 | 【改注释】 |
| 用户调 admin 创建 | 禁止 | CreateLive 未调 admin | 【保持禁止】 |

---

## 十四、实施分期

| 阶段 | 前端工作 | 依赖 | 验收 |
|------|----------|------|------|
| F1 | 核对 CreateLive 0～5、`replace`、房主 Token 保存；403/超限文案 | 后端阶段 1 ✅ | 房主绑 2 标签成功；空列表清空；第 6 个本地拦截 |
| F2 | `RESOLVE` + `resolveTag` + 类型；CreateLive「创建并使用」+ 内容安全 | 后端阶段 2 ✅ | 新名 `created=true`；同名复用；违禁 2005 人话 |
| F3 | Admin source 弱标回归；删注释误导 | 无 | 列表可见运营/用户自建（有字段时） |

建议：**F1 冒烟通过后立即 F2**（后端均已落地）。

---

## 十五、测试要点

### 15.1 阶段 1（F1）

- [ ] 房主保存 1～5 个标签 → 200；再次进入回显一致  
- [ ] 清空全部芯片后保存 → 场次无标签  
- [ ] 选第 6 个 → 本地 Toast，不发 >5 请求  
- [ ] 非房主账号若能进编辑 → 403 人话（若产品无入口则跳过）  

### 15.2 阶段 2（F2）

- [ ] 输入新名 → 确认 → resolve → chip 为返回 id → 保存后关联正确  
- [ ] 再 resolve 同名 → `created=false`，同一 id  
- [ ] 违禁名 → 2005 固定人话，输入可改  
- [ ] 软删占用名 → 不可用提示，不进 chip  
- [ ] Network：无 `/admin/tags` 由开播者触发  

### 15.3 回归

- [ ] Admin 创建/停用/恢复标签  
- [ ] `GET /content/tags?q=` 联想仍可用  
- [ ] 按标签搜场次（若已上线）不受影响  

---

## 十六、检查清单

- [ ] 文首元信息、目录、更新日志齐全  
- [ ] 契约字段已摘录（resolve / set tags），无发明字段  
- [ ] 非目标封印含「禁止 admin 创建 / 禁止伪造 UUID / 禁止 tag_names 内联」  
- [ ] 内容安全指向《12》§3，不重复造文案表  
- [ ] 落点文件可指导编码（config / types / api / CreateLive）  
- [ ] 与前端 V1 关系为增量，未宣称替代全文  

---

## 更新日志

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V2.0 | 2026-09-02 | 初稿：对齐后端 V2 阶段 1+2；CreateLive resolve 闭环；零偏差 API/类型/错误码；现码差集与分期 | Composer |
| V2.0 | 2026-09-02 | 文首补体验钉五问表，对齐 AI-工作约定 §5.1 | Composer |

---

**文档结束**
