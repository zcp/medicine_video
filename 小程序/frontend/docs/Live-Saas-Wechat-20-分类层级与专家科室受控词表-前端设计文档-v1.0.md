# 分类层级与专家科室受控词表 —— 前端可落地实现文档

**项目**: Live-Saas-Wechat  
**模块编号**: 20  
**版本**: V1.0  
**创建日期**: 2026-08-12  
**状态**: 📦 历史方案（保留备查）；**实施请改以 [V2.0](./Live-Saas-Wechat-20-分类层级与专家科室受控词表-前端设计文档-v2.0.md) 为准**  
**技术栈**: uni-app + Vue 3 + TypeScript + Pinia  
**平台**: 微信小程序

> **已被取代（实施）**：自 2026-08-17 起，本仓《20》前端实施真源为 **V2.0**（行为对齐 `app-frontend/main` 实施文档与现码）。本文全文保留，不作删除。  
> **后端设计文档**：《20-分类层级与专家科室受控词表-后端设计文档》V1.0（代码归集稿；契约真源）  
> **基线前端文档**：[《01-科室分类管理-前端设计文档-v1.0》](./Live-Saas-Wechat-01-科室分类管理-前端设计文档-v1.0.md)（`categories` CRUD / 房间多对多选择器骨架）  
> **关联**：《01》后端 V1/V2（`parent_id` 树）；《17》Admin 房间运营（复用「设科室」入口）；现网 `CategoryTabs` / `Home` / `ExpertAdminList` / `RoomCategorySelector` / `search`  
> **零偏差**：类型字段名（snake_case）、路径、分页 `size`、错误码、权威字段口径严格对齐《20》后端；**不**发明后端未实现的接口/字段  
> **原则**：最简单 / 最友好 / 最小化——能补丁不重写；能复用《01》不复制第二套分类 CRUD；发现层子孙展开**只信后端**

> **一句话闭环（Admin）**：找待审/未映射 → 审核 / 改分类 / Merge → 离开。  
> **一句话闭环（C 端）**：点根分类 Tab → 列表按后端子孙出结果 → 卡片展示真实主分类名/科室名。  
> **完成定义**：Admin 用现有 9 个词表端点可治理待审；专家建档可绑词表；房间可指定主分类；首页/搜索**不再**硬编码假分类名。

---

## ⚠️ 重要声明

- 本文是《20》后端的**前端增量设计**，**不替代**《01》分类 CRUD 专篇。  
- 【新增】Admin **专家科室词表**治理页（挂载 9 个 `/admin/expert-departments*`）。  
- 【修改】专家 Admin 建档：科室从「用分类名冒充 `department` 文本」改为**优先选词表**（仍可填文本，走后端自适应 resolve）。  
- 【修改】`RoomCategorySelector` / 设分类请求：补 `primary_category_id`；展示优先 `primary_category_name`。  
- 【维持】首页 Tab 只传根 `category_id`；**禁止**前端本地展开子孙再滤。  
- 【禁止】前端自动写入 `categories`；Phase T DROP 旧列；`categories.is_public`（后端未实现）。

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【新增·P0】 | Admin 词表列表 + 待审筛 + 批量审核 + 改分类 + Merge + 软删 + unmapped |
| 【新增·契约】 | `src/api/expertDepartments.ts` + `src/types/expertDepartment.ts` + `API_PATHS` 常量 |
| 【修改·专家】 | `ExpertAdminList`：科室选择器对接词表；读写 `department_id` / `department_name`（过渡仍兼容 `department`） |
| 【修改·房间】 | `LiveRoomCategoriesSetRequest` + 选择器：支持主分类；卡片读 `primary_category_name` |
| 【修改·展示】 | 专家卡/搜索/详情：展示优先 `department_name` → 回退 `department` |
| 【维持·分类树】 | 《01》`CategoryList` / 公开分类列表；树查询复用 V2 `tree` / `parent_id`，本文不重做 CRUD |
| 【不做】 | Phase T DROP；前端再滤子孙；第二套分类 Admin；Topic 分类混用；独立 C 端「科室百科」页 |

---

## 📌 核心定位说明

### 1. 本文档的定位

**包含能力（P0）**:
- **词表治理（Admin）**：分页列表（`is_verified` / `is_active` / `category_id` / `q`）→ 创建 / 编辑 / 软删 / 详情 → 批量审核 → Merge → 改分类同步 → 未映射专家列表
- **专家绑定（Admin）**：创建/编辑时选 `department_id` 或填科室文本（后端 resolve）；展示 `department_name` / `category_name`
- **房间主分类（Admin）**：设多对多时传 `primary_category_id`；列表/卡片展示 `primary_category_name`
- **发现层消费（C 端）**：Tab/搜索继续传 `category_id`；信任后端子孙 + JOIN 词表名

**不包含（非目标封印）**:
- 替代或重写《01》分类 CRUD / 图标上传
- 前端实现「子孙展开」或二次过滤 `is_private`（私密口径见《18》）
- 运行时向 `categories` 插入未知科室（后端也不做）
- Phase T：DROP `experts.department` / `live_rooms.category_id`
- 词表与 Topic 分类混用

### 2. 权威字段（前端必守，对齐后端 §1.1）

| 对象 | 前端读写优先 | 过渡兼容 | 禁止 |
|------|--------------|----------|------|
| 专家科室名 | `department_id` + 展示 `department_name` | 仍可读/可传 `department` 文本 | 用 `categories.name` 冒充科室终态 |
| 专家主分类 | 展示 `category_id` / `category_name`（由词表同步，一般不手改） | 可空 | 前端自己推导写库规则 |
| 直播间分类 | 多对多 + `primary_category_id`；展示 `primary_category_name` | 可读旧 `category_id` 单列 | 把单列当筛选权威 |
| 全局分类树 | `categories`（公开树 / Admin CRUD 仍走《01》） | — | 与词表 CRUD 混在同一表单强耦 |

### 3. 关键网关约定

| 维度 | 值 |
|------|-----|
| 微服务 | `live_core_service` |
| Core 网关前缀 | `/api/core` |
| 词表 Admin | `/api/core/admin/expert-departments*` |
| 分类公开/Admin | 既有 `/api/core/content/categories`、`/api/core/admin/categories*`（《01》） |
| 房间分类 | 既有 `/api/core/admin/rooms/{id}/categories`（body 增强） |
| 权限拒绝 | HTTP 403 / 业务码 **`3003`**（以后端代码为准，非模板偶发 `3002`） |

> ✅ 与科室/专家/房间 Admin 一致走 **core**。  
> ❌ 勿写成 `/api/users/admin/expert-departments`。

### 4. 与现网前端的差异 / 缺口

| # | 现状 | 本包应补 |
|---|------|----------|
| 1 | 无 `expert-departments` API / 类型 / 常量 | 新增封装 + `API_PATHS` |
| 2 | 个人中心管理功能无「专家科室」入口 | `Profile.vue` + `pages.json` |
| 3 | `ExpertAdminList` 用**分类名**写入 `department` 文本 | 改为词表选择器；可选文本走自适应 |
| 4 | `LiveRoomCategoriesSetRequest` 无 `primary_category_id` | 类型 + 选择器补主分类 |
| 5 | `Category` 类型无 `parent_id` / 树节点 | 按《01》V2 增量补字段（消费树时）；**不**新造分类 CRUD |
| 6 | 房间/首页卡片可能缺 `primary_category_name` 展示 | 优先读后端字段，禁硬编码假名 |
| 7 | 搜索已部分兼容 `department_name` | 维持优先序；补齐专家 Admin/卡片一致 |
| 8 | Home Tab 已传根 `category_id` | **维持**；禁止前端再展开子孙 |

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《20-分类层级与专家科室受控词表-后端设计文档》 | 📋 **契约主文档** | 9 Admin API、字段、错误码、权威源 |
| 2 | 《01-科室分类管理-前端设计文档》 | 📋 **基线复用** | 分类 CRUD、RoomCategorySelector 骨架 |
| 3 | 《01》后端 V1 / V2 | 📖 树语义 | `parent_id`、tree/children |
| 4 | 《17》管理端直播间内容运营 MVP 前端 | 📖 入口复用 | Admin 房编辑内「设科室」 |
| 5 | 《通用规范-文件创建规范-v1.0》 | 📋 命名/目录 | 新增 api/types/pages |
| 6 | 《通用数据列表展示规范》《前端分页实现规范》 | 📖 列表页 | Admin 词表列表 |
| 7 | 《编辑页面数据与校验规范》 | 📖 表单 | 创建/编辑/Merge 弹窗 |

---

## 一、功能概述

### 1.1 产品语言

| 对内实现 | 对运营/用户文案 |
|----------|-----------------|
| `categories` | **科室分类**（一级 Tab / 树结构） |
| `expert_departments` | **专家科室**（受控词表；可待审） |
| `is_verified=false` | **待审核** |
| `is_active=false` | **已停用**（软删，可列表筛回） |
| Merge | **合并科室**（源物理删除；须二次确认） |
| `primary_category_name` | 房间卡片上的**主分类名** |

### 1.2 闭环与非目标（防填洞）

| 页/面 | 一句话闭环 | 完成定义 | 永不做 |
|-------|------------|----------|--------|
| 词表 Admin | 找待审 → 审/并/改类 → 离开 | 待审可清空到可运营水位 | 播控、内容安全规则、Topic |
| 专家 Admin | 选词表科室 → 保存 → 列表可见名 | 新建专家带 `department_id` 或可自适应 | 在专家页做完整词表 CRUD |
| 房间设分类 | 多选 + 指定主 → 保存 | 卡片出真实主分类名 | 前端算子孙、写单列权威 |
| 首页 Tab | 点根类 → 看列表 | 结果含子类下内容（后端保证） | 前端展开 ID 再请求多次 |

---

## 二、涉及文件

```
src/config/api.ts                              # 【追加】EXPERT_DEPARTMENT / ADMIN 路径
src/types/expertDepartment.ts                  # 【新增】词表 Schema 对齐
src/types/category.ts                          # 【补丁】parent_id?；LiveRoomCategoriesSetRequest.primary_category_id?
src/types/expert.ts / 邻近 Admin 类型          # 【补丁】department_id / department_name / category_*
src/types/room.ts                              # 【补丁】primary_category_name?
src/api/expertDepartments.ts                   # 【新增】9 个 Admin 端点
src/api/categories.ts                          # 【补丁】setRoomCategories 透传 primary_category_id；树查询若缺则补
src/api/expert.ts（Admin 创建/更新）             # 【补丁】可传 department_id；展示字段映射
src/pages/admin/expertDepartment/
  ├── ExpertDepartmentList.vue                 # 【新增】列表 + 筛 + 批量审
  ├── ExpertDepartmentFormDialog.vue           # 【新增】创建/编辑
  ├── ExpertDepartmentMergeDialog.vue          # 【新增】Merge 二次确认
  └── UnmappedExpertsPanel.vue                 # 【新增或同页 Tab】未映射专家
src/pages/admin/expert/ExpertAdminList.vue     # 【修改】科室选择器
src/components/RoomCategorySelector.vue        # 【修改】主分类
src/components/expert/* / search               # 【按需补丁】展示优先序
src/pages/profile/Profile.vue                  # 【修改】管理入口
src/pages.json                                 # 【修改】注册词表页
```

**现网缺口速查**：

| 落点 | 现状 | P0 |
|------|------|-----|
| 词表 API | 无 | 新增 |
| 词表 Admin 页 | 无 | 新增（主体库瘦 CRUD + 待审） |
| `ExpertAdminList` 科室 | 分类名 → `department` 文本 | 改为词表；文本可选 |
| `RoomCategorySelector` | 多选无主分类 | 补主分类 + body 字段 |
| `Category` / 分页 | 缺 `parent_id`；代码偶发 `page_size` | 契约用 `size`；树字段对齐 V2 |
| Home Tab | 已传根 `category_id` | 维持，勿前端再滤 |

---

## 三、类型定义（零偏差对齐后端）

> 字段名与后端 Pydantic **一致（snake_case）**；网关路径用 `/api/core` 前缀由 `request` + `API_PATHS` 处理。

```typescript
// src/types/expertDepartment.ts

/** 对应 ExpertDepartmentItem */
export interface ExpertDepartmentItem {
  id: string
  name: string
  category_id: string
  category_name?: string | null
  synonyms: string[]
  is_active: boolean
  is_verified: boolean
  source?: string | null
  created_by?: string | null
  expert_count: number
  created_at: string
  updated_at: string
}

export interface ExpertDepartmentCreate {
  name: string                 // 1..120
  category_id: string
  synonyms?: string[]
  is_verified?: boolean        // 默认 false
  source?: string              // 默认 "admin_api"
}

export interface ExpertDepartmentUpdate {
  name?: string
  category_id?: string
  synonyms?: string[]
  is_active?: boolean
  is_verified?: boolean
}

export interface ExpertDepartmentPageResult {
  items: ExpertDepartmentItem[]
  total: number
  page: number
  size: number                 // 禁止写成 page_size
}

export interface BatchVerifyRequest {
  department_ids: string[]     // 1..200
  verified?: boolean           // 默认 true
}

export interface MergeDepartmentsRequest {
  source_id: string
  target_id: string
}

/** unmapped 列表单项（后端 §3.1.5） */
export interface UnmappedExpertItem {
  id: string
  name: string
  title?: string | null
  hospital?: string | null
  avatar_url?: string | null
  category_id?: string | null
  category_name?: string | null
  expertise_areas?: unknown
  is_active: boolean
  department?: string | null   // 过渡文本
}
```

**专家响应增量**（写入既有专家类型，勿另造冲突模型）：

```typescript
// 在 Admin/列表映射层对齐后端 ExpertItem 增量
department_id?: string | null
department_name?: string | null
category_id?: string | null
category_name?: string | null
department?: string | null     // 过渡；展示优先 department_name
```

**房间设分类**（补丁既有类型，对齐后端 §2.3）：

```typescript
export interface LiveRoomCategoriesSetRequest {
  category_ids: string[]
  mode: 'replace' | 'append'
  primary_category_id?: string | null  // 不传则后端默认列表首个
}
```

**分类树消费**（补丁，不替代《01》全量 Schema）：

```typescript
// Category 增量（V2）
parent_id?: string | null
children?: Category[]          // tree=true 时
```

**展示优先序（前端映射唯一约定）**：

| 场景 | 优先 |
|------|------|
| 专家科室文案 | `department_name` → `department` → 空 |
| 房间主分类文案 | `primary_category_name` →（可选）关联列表中 `is_primary` 项名 → 空 |
| 搜索专家 | 维持现网 `pickString(department, department_name, …)`，建议调整为 **name 优先** |

---

## 四、API 封装

### 4.1 路径常量（建议）

```typescript
// src/config/api.ts 追加
EXPERT_DEPARTMENT: {
  ADMIN_LIST: '/admin/expert-departments',
  ADMIN_CREATE: '/admin/expert-departments',
  ADMIN_DETAIL: (id: string) => `/admin/expert-departments/${id}`,
  ADMIN_UPDATE: (id: string) => `/admin/expert-departments/${id}`,
  ADMIN_DELETE: (id: string) => `/admin/expert-departments/${id}`,
  ADMIN_UNMAPPED: '/admin/expert-departments/unmapped',
  ADMIN_MERGE: '/admin/expert-departments/merge',
  ADMIN_CATEGORY: (id: string) => `/admin/expert-departments/${id}/category`,
  ADMIN_BATCH_VERIFY: '/admin/expert-departments/batch-verify'
}
```

> `baseType: 'core'`。静态路径 `unmapped` / `merge` / `batch-verify` 的封装顺序无所谓；**后端**已保证 `unmapped` 声明在 `{id}` 详情前。

### 4.2 九端点一览（对齐后端最终路由表）

| # | Method | Path | 前端用途 |
|---|--------|------|----------|
| 1 | GET | `/admin/expert-departments` | 列表；Query: `page` `size` `is_active?` `is_verified?` `category_id?` `q?` |
| 2 | POST | `/admin/expert-departments` | 创建 |
| 3 | PATCH | `/admin/expert-departments/{id}` | 编辑；含 `category_id` 时后端 sync 专家 |
| 4 | DELETE | `/admin/expert-departments/{id}` | 软删（`is_active=false`） |
| 5 | GET | `/admin/expert-departments/unmapped` | 未映射专家 |
| 6 | POST | `/admin/expert-departments/merge` | 合并（源**物理删除**） |
| 7 | PATCH | `/admin/expert-departments/{id}/category` | 专用改分类 + sync |
| 8 | POST | `/admin/expert-departments/batch-verify` | 批量审核 |
| 9 | GET | `/admin/expert-departments/{id}` | 详情（含 `expert_count`） |

### 4.3 行为增强（无新路由，只改调用方）

| 调用 | 前端注意 |
|------|----------|
| `POST/PATCH` Admin 专家 | 优先传 `department_id`；仅文本时传 `department`，**不要**前端本地 UPSERT 词表 |
| `POST .../rooms/{id}/categories` | body 增加可选 `primary_category_id` |
| 首页 `getHomepageRooms({ category_id })` | 继续传根 ID；勿前端展开 |
| 搜索 | 继续传 `category_id`；展示用词表名优先 |

### 4.4 错误码（UI 人话）

| code | HTTP | 前端提示建议 |
|------|------|--------------|
| `200` | 200 | — |
| `3003` | 403 | 无管理权限 |
| `2001` | 404 | 科室不存在或已合并 |
| `4001` | 400 | 参数非法 / 分类不存在或已禁用 / 不能合并到自身 |
| `1002` | 500 | 服务异常，稍后重试 |
| `3001` | 401 | 重新登录 |

---

## 五、管理端页面设计（词表）

> 对齐 Agent `frontend`「管理端表面」+ 主体库瘦 CRUD：搜/筛 → 建/改 → 停用 → 可恢复；Merge 单独高风险确认。

### 5.1 入口

- 个人中心 → **管理功能 → 专家科室**  
- 仅 `ADMIN` / `SUPERADMIN` 可见（与现网 `isAdmin` 一致）

### 5.2 列表顶栏（一行优先）

| 控件 | 绑定 |
|------|------|
| 搜索 | `q`（≤100） |
| 状态 | `is_verified`：全部 / 待审 / 已审 |
| 启用 | `is_active`：全部 / 启用 / 停用 |
| 分类 | `category_id`（一级/树选择，复用分类列表） |
| 操作 | 查询 / 重置 / 新建 / 批量通过（待审多选） |

### 5.3 行展示

- 主信息：`name` + 标签：`待审核` / `已停用`（关键态靠标签，不只靠灰字）  
- 次要：`category_name` · `expert_count` · `source`  
- 行侧操作：详情/编辑 · 改分类 · 合并 · 停用 ·（待审）通过  

### 5.4 Merge（高风险）

1. 选源、选目标（`source_id ≠ target_id`）  
2. 文案明确：**合并后源科室将删除且不可从本页恢复**；同义词并入目标（≤20，后端截断）  
3. 成功 Toast 展示 `transferred_experts`  
4. 刷新列表；勿在前端「假删」缓存残留源 ID

### 5.5 改分类

- 优先走专用 `PATCH .../category`（返回 `synced_experts` 便于 Toast）  
- 通用 `PATCH` 带 `category_id` 亦可；二选一，**页面只保留一条主路径**（推荐专用）

### 5.6 未映射专家

- 同页次级 Tab 或折叠区：`GET .../unmapped`  
- 展示过渡 `department` 文本，引导运营去专家编辑绑定词表（跳转 `ExpertAdminList` 带 id，若现网无带参则仅提示）  
- **本页不**做「一键建词表并绑定」的复杂向导（最小化；真有需求另开）

### 5.7 软删文案

- DELETE = **停用**（`is_active=false`），可筛「停用」查看；勿写「不可恢复」  
- Merge 源删除才是物理删，文案与软删分开

---

## 六、专家 Admin 科室选择（补丁）

**现状问题**：用 `categories` 名称写入 `department`，与词表权威冲突。

**最小改法**：

1. 打开表单时拉词表列表（`is_active=true`，可 `q` 本地/服务端搜，`size` 适中）。  
2. 选择后写入 `department_id`，展示名用词表 `name`；提交优先 `department_id`。  
3. 若运营输入自由文本：只传 `department`，**不**前端创建词条（后端自适应 `is_verified=false`）。  
4. 列表/详情展示：`department_name || department`。  
5. **不要**再把「分类名」当作科室唯一来源；分类仅作词表的 `category_id` 映射维。

---

## 七、房间主分类（补丁）

**最小改法**（`RoomCategorySelector`）：

1. 多选逻辑维持。  
2. 已选中增加「设为主分类」（单选）；提交 `primary_category_id`。  
3. 未指定时可不传，后端默认 `category_ids[0]`（replace）—— UI 可弱提示「未指定则第一项为主」。  
4. `mode` 维持 `replace`（管理端主路径）；`append` 非 P0 可不暴露。  
5. Admin 房间运营（《17》）继续嵌入本选择器，禁止复制第二套。

---

## 八、C 端消费（维持为主）

| 表面 | 行为 |
|------|------|
| `CategoryTabs` / `Home` | 选中根分类 → `getHomepageRooms({ category_id })`；**禁止**前端拼子孙 ID |
| 房间卡片 | 展示 `primary_category_name`；无则空，不写死「综合」等假名 |
| 专家列表/详情/搜索 | 科室文案按展示优先序；分类筛传 `category_id` 交给后端 |
| 星标 `pinned_categories` | 仍针对象 `categories` id，与词表无关 |

---

## 九、权限与可见性

| 表面 | 可见条件 |
|------|----------|
| 词表 Admin / 专家 Admin 写 | JWT + Admin UI 门闸；接口 3003 友好提示 |
| 公开分类树 / 首页 / 搜索 | 无需为词表单独加登录 |
| 房间设分类 | 既有 Admin 房间能力 |

---

## 十、核心流程

### 10.1 待审治理

```
进入专家科室 → 筛 is_verified=false → 勾选 → batch-verify
或 单条通过 / 改分类 / Merge 到标准名 → 列表刷新
```

### 10.2 专家建档

```
选词表 department_id（推荐）或填 department 文本
→ POST/PATCH Admin 专家
→ 后端 resolve / UPSERT 待审（若新名）
→ 列表显示 department_name
```

### 10.3 设房间分类

```
多选 categories → 指定 primary → POST admin rooms categories
→ 卡片读 primary_category_name
```

---

## 十一、测试要点

| # | 场景 | 期望 |
|---|------|------|
| 1 | 待审列表 + 批量通过 | `affected` 增加；标签变已审 |
| 2 | Merge 跨分类 | 专家数转入目标；源消失；Toast 人数 |
| 3 | 改词表分类 | Toast `synced_experts`；专家详情分类名更新 |
| 4 | 软删 | 行「已停用」；可筛回；非物理消失 |
| 5 | 专家选词表新建 | 响应含 `department_id` / `department_name` |
| 6 | 专家填新文本 | 不中断；词表出现待审（后端）；前端不报错即可 |
| 7 | 房间设主分类 | 卡片 `primary_category_name` 正确 |
| 8 | 首页根 Tab | 含子类内容（后端）；前端无本地子孙逻辑 |
| 9 | 非 Admin | 入口隐藏；直打 API → 3003 人话 |
| 10 | 与《01》回归 | 分类 CRUD / 旧选择器嵌入房运营仍可用 |

---

## 十二、实施分期（前端）

| 优先级 | 项 | 说明 |
|--------|----|------|
| **P0** | 词表 API + Admin 列表闭环 | 审 / 改类 / Merge / 软删 / unmapped |
| **P0** | 专家 Admin 科室选择器补丁 | `department_id` 优先 |
| **P0** | 房间主分类 + 卡片字段 | `primary_category_id` / `primary_category_name` |
| **P1** | 展示优先序统一 | 搜索/专家卡/详情同一 helper |
| **P1** | 分类类型 `parent_id` / tree 消费 | 词表表单选分类更好用 |
| **P2** | 专家页「一键处理未映射」 | 非本版；另开需求 |
| **不做** | Phase T 删字段、前端子孙展开、第二套分类 CRUD | 封印 |

---

## 十三、检查清单

- [ ] 命名：`Live-Saas-Wechat-20-…-前端设计文档-v1.0.md`  
- [ ] 九端点路径/方法/字段与《20》后端最终路由表一致  
- [ ] 分页字段为 `size`；权限码按 `3003`  
- [ ] 不替代《01》；不写后端未实现字段（`is_public`、DROP 列）  
- [ ] Admin 列表符合瘦 CRUD + 非目标封印  
- [ ] C 端不前端展开子孙  
- [ ] 更新日志已填  

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-08-12 | 对照《20》后端 V1.0 零偏差起草；最小友好增量（词表 Admin + 专家/房间补丁 + C 端维持） | — |
| V1.0 | 2026-08-17 | 文首标明实施改以 V2.0 为准；本文保留备查 | — |

---

**文档结束** ✅
