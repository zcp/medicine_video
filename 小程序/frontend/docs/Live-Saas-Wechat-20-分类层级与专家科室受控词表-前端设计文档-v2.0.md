# 分类层级与专家科室受控词表 —— 前端设计文档

**项目**: Live-Saas-Wechat  
**模块编号**: 20  
**版本**: V2.0  
**创建日期**: 2026-08-17  
**状态**: 📋 设计定稿（实施对齐中）  
**技术栈**: uni-app + Vue 3 + TypeScript + Pinia  
**平台**: 微信小程序  

**基于**:  
- 行为真源：`app-frontend/main`《专家分类管理页面实施文档》+《专家管理页面实施文档》+ 现码 `pages/app/admin/departments/index.vue`、`pages/app/admin/expert-list/index.vue`  
- 契约真源：《20-分类层级与专家科室受控词表-后端设计文档》V1.0（路径 / 字段 / 错误码）  
- 历史方案：[《20》前端设计文档 V1.0](./Live-Saas-Wechat-20-分类层级与专家科室受控词表-前端设计文档-v1.0.md)（保留备查，**实施以本文为准**）  
- 基线：《01》科室分类管理前端（分类 CRUD API 可复用；本版允许在专家分类管理页内嵌根分类 CRUD，与 V1.0「同页不做分类 CRUD」不同）

> **一句话闭环（专家分类）**：按分类看清词表 → 审 / 并 / 改 / 停用 → 必要时增改根分类 → 离开。  
> **一句话闭环（专家管理）**：找未分配 → 分配 `department_id` → 列表可见标准科室名。  
> **一句话闭环（C 端）**：点根分类 Tab → 后端出子孙结果 → 卡片展示真实主分类名 / 科室名。  
> **完成定义**：小程序 Admin「专家分类」交互与 main 实施清单对齐；专家页可分配未映射；房间可设主分类；C 端不硬编码假名、不前端子孙展开。  
> **入口文案**：管理功能 / 导航标题统一为 **「专家分类」**（非「专家分类管理」）。  
> **科室分类管理页**：已按 [V2.1](./Live-Saas-Wechat-20-专家分类承接根分类细能力-前端设计文档-v2.1.md) 将细能力迁入「专家分类」；独立 `CategoryList` 路由与页面已退役，`CategoryFormDialog` 保留复用。  
> **壳层与分类治理（migrate/merge/级联）**：V2.0 本文仍作词表闭环真源；对齐 main 截图的壳层与治理解封见增量 [V2.2](./Live-Saas-Wechat-20-专家分类对齐main治理台-前端设计文档-v2.2.md)。

---

## 📋 目录

1. [背景与目标](#一背景与目标)
2. [范围定义](#二范围定义)
3. [术语与关键概念](#三术语与关键概念)
4. [与 V1.0 / main 的关系](#四与-v10--main-的关系)
5. [核心流程](#五核心流程)
6. [页面与交互设计](#六页面与交互设计)
7. [涉及文件与落点](#七涉及文件与落点)
8. [数据结构与字段约定](#八数据结构与字段约定)
9. [API 封装约定](#九api-封装约定)
10. [权限与可见性](#十权限与可见性)
11. [错误处理与兜底](#十一错误处理与兜底)
12. [实施分期](#十二实施分期)
13. [测试要点](#十三测试要点)
14. [检查清单](#十四检查清单)
15. [更新日志](#更新日志)

---

## 一、背景与目标

### 1.1 为什么做 V2.0

| 问题 | 说明 |
|------|------|
| V1.0 定位 | 词表「主体库瘦 CRUD」：筛/建/改/审/Merge/未映射同页 Tab；分类 CRUD 严格留给《01》 |
| 本仓现状 | 已按 V1.0 落地一截（`expertDepartments` API、词表列表页、专家选词表、房间主分类等），但**交互形态与 main 不一致** |
| main 真源 | 实施文档 + 现码已做成「专家分类管理」治理台：树/平铺、选择批审、按类新增、同页根分类 CRUD；未分配在**专家管理**页闭环 |
| 决策 | **产品行为以 main 为准**；工程落点仍用本仓路径 / `request` / 规范样本；**不**照搬 H5、不平行新建 `pages/app/**` |

### 1.2 目标

1. 用本文替换 V1.0 作为《20》前端**实施真源**（V1.0 文件保留）。  
2. 规定本仓如何把现有实现**同步**到 main 行为，而不是整文件拷贝 main。  
3. 保留本仓已领先能力：房间 `primary_category_id` / `primary_category_name`（main 侧基本缺失，本文要求维持）。

---

## 二、范围定义

### 2.1 做什么

| 表面 | 能力 |
|------|------|
| **专家分类**（原「专家科室」入口） | 树/平铺双模式；搜索防抖；科室 CRUD；单条/批量审核；合并；软删（停用）可恢复；**按分类下新增科室**；**同页新增/编辑根分类**；选择模式 + 底栏批量审 |
| **专家管理** | 词表选择建档（`department_id` 优先，文本自适应）；**未分配 Tab** + 行内「分配科室」 |
| **房间设分类** | 多选 + 设为主 → `primary_category_id`；卡片读 `primary_category_name` |
| **C 端** | Home/搜索传根 `category_id`；展示优先序；禁止前端子孙展开 |

### 2.2 不做什么（非目标封印）

| 永不做（本版） | 原因 |
|----------------|------|
| 平行复制 `pages/app/admin/departments` 目录结构 | 本仓路由与规范不同；行为移植即可 |
| 搬 H5 Element 三页（`DepartmentManage` 等） | 本仓是微信小程序 |
| 前端子孙 ID 展开再请求/过滤 | 发现层只信后端 |
| Phase T DROP 旧列；发明后端未实现字段（如 `is_public`） | 契约零偏差 |
| 词表页「一键建词表并绑定」复杂向导 | main 也是分配到专家页完成 |
| Topic 分类混用 | 与《20》后端一致 |
| 分类合并 / 引用迁移治理 | **V2.0 本文范围内不做**；已由 [V2.2](./Live-Saas-Wechat-20-专家分类对齐main治理台-前端设计文档-v2.2.md) 解封并规定落点（依赖后端契约） |

> **同步深度**：V2.0 = main 词表壳 + 同页根分类 CRUD（不含当时的 merge/migrate）。**V2.2** = 继续对齐 main 治理台（Tab/治理/migrate/merge/级联）；实施以 V2.2 为准，本文词表与未分配闭环仍有效。

---

## 三、术语与关键概念

| 对内 | 对运营文案 |
|------|------------|
| `categories` | **科室分类** / 根分类（Tab / 树分组标题） |
| `expert_departments` | **专家科室**（受控词表） |
| `is_verified=false` | **待审核** |
| `is_active=false` | **已停用**（软删，可筛回/启用） |
| Merge 科室 | **合并科室**（源物理删除；二次确认） |
| 树模式 | 搜索为空：按分类分组折叠 |
| 平铺模式 | 有搜索关键词：科室列表平铺 + 分类标签 |
| `primary_category_name` | 房间卡片**主分类名** |
| 未分配专家 | `department_id` 为空；在**专家管理**处理 |

三层关系（与 main 设计一致）：

```text
categories（根分类）
    ↑ FK
expert_departments（词表，本页核心）
    ↑
experts（专家；未分配在专家管理页修正）
```

---

## 四、与 V1.0 / main 的关系

### 4.1 文档关系

| 文档 | 角色 |
|------|------|
| 《20》前端 V1.0 | 历史方案；保留；**不再作为实施依据** |
| **本文 V2.0** | 本仓《20》前端实施真源 |
| main《专家分类管理页面实施文档》 | 行为对照清单（树/平铺、批审、根分类 CRUD 等） |
| main《专家管理页面实施文档》 | 未分配 Tab / 分配科室对照 |
| 《20》后端 | API / Schema / 错误码真源 |
| 《01》前端 | 分类 Admin API / 独立分类页仍可存在；本版允许词表页**内嵌**根分类增改 |

### 4.2 V1.0 → V2.0 主要变更

| 项 | V1.0 | V2.0 |
|----|------|------|
| 词表页形态 | 筛选项 + 平铺列表 + 未映射 Tab | **树/平铺**；选择模式底栏批审；未映射**迁出** |
| 根分类 | 禁止同页 CRUD | **同页新增/编辑根分类**（对齐 main） |
| 未映射 | 词表页次级 Tab | **专家管理**未分配 Tab + 分配弹窗 |
| 入口文案 | 专家科室 | **专家分类** |
| 房间主分类 | 要求补齐 | **维持本仓已实现** |
| 原则 | 最瘦 CRUD、与《01》强分离 | 行为跟 main；落点跟本仓 |

### 4.3 本仓 vs main 工程差异（必须遵守）

| 维度 | main | 本仓（本文要求） |
|------|------|------------------|
| 词表 API 文件 | `src/api/department.ts` | 继续 `src/api/expertDepartments.ts`（勿双轨同义 API） |
| 词表页路径 | `pages/app/admin/departments/index` | `pages/admin/expertDepartment/ExpertDepartmentList`（可保留目录名，**导航文案**改「专家分类管理」） |
| 专家页 | `pages/app/admin/expert-list` | `pages/admin/expert/ExpertAdminList` |
| 请求层 | main 自有 `get/post/...` | 本仓 `request` + `API_PATHS` + `baseType: 'core'` |
| UI 组件 | `ModalDialog` 等 main 组件 | 复用本仓已有 Dialog / 列表样式，**不**为对齐而引入 main 组件树 |

---

## 五、核心流程

### 5.1 待审治理（专家分类管理）

```text
进入专家分类管理
  →（可选）搜索关键字 → 平铺模式
  → 或树模式展开某分类 → 勾选待审 / 单条通过 / 进入选择模式批量通过
  → 或 Merge 到标准名 / 编辑 / 停用
  → 列表刷新 → 离开
```

### 5.2 按分类补词条

```text
树模式某分类行 →「＋ 新增科室」→ 预填 category_id → 保存
```

### 5.3 根分类维护（同页）

```text
顶栏「新增根分类」/ 分组行「编辑分类」
  → createCategory / updateCategory（《01》已有封装）
  → 刷新分类 + 词表分组
```

### 5.4 未分配专家

```text
专家管理 → Tab「未分配」→ GET unmapped
  →「分配科室」→ 选词表 → PATCH expert { department_id }
  → 刷新
```

### 5.5 专家建档

```text
选词表 department_id（推荐）或填 department 文本
  → POST/PATCH Admin 专家（前端不 UPSERT 词表）
  → 展示 department_name || department
```

### 5.6 房间主分类

```text
RoomCategorySelector 多选 →「设为主」→ POST categories + primary_category_id
  → 卡片 primary_category_name
```

---

## 六、页面与交互设计

### 6.1 入口

| 入口 | 条件 | 目标 |
|------|------|------|
| 个人中心 → 管理功能 → **专家分类** | `isAdmin` | 词表治理页 |
| 个人中心 → 管理功能 → 专家管理 | `isAdmin` | 含未分配 Tab |
| 房间运营内嵌 | 既有 Admin | `RoomCategorySelector` |

### 6.2 专家分类管理页（对齐 main 布局）

> **布局与治理解封**：以下为 V2.0 基线线框；Tab /「治理」/ 迁移·合并·级联弹窗以 [V2.2](./Live-Saas-Wechat-20-专家分类对齐main治理台-前端设计文档-v2.2.md) §六为准。

```text
┌──────────────────────────────────────────┐
│ 专家分类管理  [选择] [新增根分类]          │
├──────────────────────────────────────────┤
│ 🔍 搜索科室名称...                        │
├──────────────────────────────────────────┤
│ ▼ 某分类  N 个科室            [编辑分类]   │
│   · 科室名  待审/已审  专家数  同义词       │
│   · [通过][编辑][停用][合并]               │
│   ── [＋ 新增科室] ──                     │
├──────────────────────────────────────────┤
│ （有搜索时：平铺卡片 + 分类标签）           │
├──────────────────────────────────────────┤
│ ☐ 全选  已选 n 项           [批量通过]    │  ← 仅选择模式
└──────────────────────────────────────────┘
```

**行为要点**（对照 main 实施清单 1–15）：

1. 列表分页 / 触底加载或等价拉全再分组；`q` 建议 **300ms 防抖**。  
2. `search` 空 → 树模式（按 `category_id` 分组，可折叠）；非空 → 平铺。  
3. 选择模式：顶栏进入；底栏全选 + 批量审核；已审项不可勾。  
4. 单条审核：可走 `batch-verify` 单 id，或 `PATCH` `{ is_verified: true }`（与 main 一致即可；本仓已有 batch-verify 可统一）。  
5. 删除文案用**停用**；可恢复启用（V1.0 口径保留，优于「删除不可恢复」误导）。  
6. Merge：二次确认；文案标明源物理删除；Toast `transferred_experts`；**目标候选须可跨页**（拉 `size` 足够或可搜，修 main/本仓共有坑）。  
7. 改分类：优先专用 `PATCH .../category`，Toast `synced_experts`。  
8. **本页不再放「未映射专家」主闭环**（可保留弱入口跳转专家管理 `?tab=unmapped`，非必须）。

### 6.3 专家管理页补丁

| 项 | 要求 |
|----|------|
| Tab / 筛 | 至少支持「未分配」数据源：`GET .../unmapped` |
| 分配 | 弹窗选启用词表 → `updateExpert({ department_id })` |
| 建档/编辑 | 词表 picker + 可选自由文本；优先提交 `department_id` |
| 展示 | `department_name \|\| department` |

### 6.4 房间与 C 端（维持 + 本仓优势）

| 表面 | 要求 |
|------|------|
| `RoomCategorySelector` | 多选 + 设为主；`mode: 'replace'`；传 `primary_category_id` |
| Home Tab | 只传根 `category_id`；禁止本地展开子孙 |
| 房间卡片 | `primary_category_name`；无则空，不写死假名 |
| 搜索/专家卡 | 科室名优先序同下表 |

---

## 七、涉及文件与落点

### 7.1 目标文件树（本仓）

```text
src/config/api.ts                         # EXPERT_DEPARTMENT 九端点（已有则维持）
src/types/expertDepartment.ts             # 词表 Schema（已有则维持）
src/types/expert.ts / room.ts / category.ts
src/api/expertDepartments.ts              # 九端点封装（唯一词表 API 模块）
src/api/categories.ts                     # 根分类 CRUD + setRoomCategories(primary)
src/api/expert.ts                         # Admin 专家读写 department_id
src/pages/admin/expertDepartment/
  ├── ExpertDepartmentList.vue            # 【重做交互】树/平铺 + 批审 + 根分类入口
  ├── ExpertDepartmentFormDialog.vue      # 创建/编辑科室（可预填 category_id）
  ├── ExpertDepartmentMergeDialog.vue     # Merge；候选可跨页
  └── （UnmappedExpertsPanel 降级或删除主闭环）
src/pages/admin/expert/ExpertAdminList.vue # 【补】未分配 + 分配科室
src/components/RoomCategorySelector.vue   # 主分类（已有则保持）
src/pages/profile/Profile.vue             # 入口文案「专家分类管理」
src/pages.json                            # 导航 title 对齐
src/pages/home/Home.vue / store/expert.ts / subpackages/search/
```

### 7.2 相对现状的改造策略

| 策略 | 说明 |
|------|------|
| 最小化 | **改**现有 `ExpertDepartmentList` 交互，不新建第二路由世界 |
| 友好 | 保留已通的 API/类型/房间主分类；先对齐可感知 UX |
| 禁止 | `department.ts` 与 `expertDepartments.ts` 长期双轨 |

---

## 八、数据结构与字段约定

> 字段名与《20》后端 Pydantic **snake_case 一致**；分页参数为 **`size`**（禁止词表接口写 `page_size`）。

### 8.1 词表（维持 V1.0 Schema，零偏差）

`ExpertDepartmentItem` / `Create` / `Update` / `PageResult` / `BatchVerifyRequest` / `MergeDepartmentsRequest` / `UnmappedExpertItem` —— 以本仓 `src/types/expertDepartment.ts` 与后端为准。

### 8.2 专家增量

```text
department_id? / department_name? / category_id? / category_name?
department?          # 过渡文本；展示次选
```

### 8.3 房间设分类

```text
category_ids: string[]
mode: 'replace' | 'append'   # 管理端主路径 replace
primary_category_id?: string | null
```

### 8.4 展示优先序

| 场景 | 优先 |
|------|------|
| 专家科室文案 | `department_name` → `department` → 空 |
| 房间主分类 | `primary_category_name` →（可选）关联中 `is_primary` 名 → 空 |
| 分类口语名 | 若后端有 `display_name` 则展示优先，否则 `name`（与 main 一致时采用） |

---

## 九、API 封装约定

### 9.1 词表九端点（不变）

| # | Method | Path | 用途 |
|---|--------|------|------|
| 1 | GET | `/admin/expert-departments` | 列表：`page` `size` `is_active?` `is_verified?` `category_id?` `q?` |
| 2 | POST | `/admin/expert-departments` | 创建 |
| 3 | PATCH | `/admin/expert-departments/{id}` | 编辑 |
| 4 | DELETE | `/admin/expert-departments/{id}` | 软删（停用） |
| 5 | GET | `/admin/expert-departments/unmapped` | 未映射（专家页消费） |
| 6 | POST | `/admin/expert-departments/merge` | 合并 |
| 7 | PATCH | `/admin/expert-departments/{id}/category` | 改分类 + sync |
| 8 | POST | `/admin/expert-departments/batch-verify` | 批量审核 |
| 9 | GET | `/admin/expert-departments/{id}` | 详情（按需） |

`baseType: 'core'`。路径常量继续挂 `API_PATHS.EXPERT_DEPARTMENT`。

### 9.2 根分类（同页调用《01》已有）

| 用途 | 本仓函数（示例） | 说明 |
|------|------------------|------|
| 列表 | `getCategoryList` / `getAdminCategories` | 树分组标题 |
| 创建 | `createCategory` | 顶栏新增根分类 |
| 更新 | `updateCategory` | 分组行编辑分类 |

> 不在本文重做整套分类 Admin；仅规定词表页**允许调用**上述接口。

### 9.3 行为增强（无新路由）

| 调用 | 注意 |
|------|------|
| Admin 专家 POST/PATCH | 优先 `department_id`；仅文本时 `department`；禁止前端 UPSERT 词表 |
| 房间 categories | 可选 `primary_category_id` |
| 首页 | 根 `category_id`；勿展开 |

---

## 十、权限与可见性

| 表面 | 条件 |
|------|------|
| 专家分类管理 / 专家写 | JWT + Admin UI 门闸；接口 `3003` 人话提示 |
| 公开分类 / 首页 / 搜索 | 不为词表单独加登录 |
| 房间设分类 | 既有 Admin 房间能力 |

---

## 十一、错误处理与兜底

| code | HTTP | 提示建议 |
|------|------|----------|
| `3003` | 403 | 无管理权限 |
| `2001` | 404 | 科室不存在或已合并 |
| `4001` | 400 | 参数非法 / 分类不可用 / 不能合并到自身 |
| `3001` | 401 | 重新登录 |
| `1002` | 500 | 服务异常，稍后重试 |

兜底：列表失败可重试；Merge/批审失败不假删本地缓存；停用与 Merge 文案严格区分。

---

## 十二、实施分期

| 优先级 | 项 | 说明 |
|--------|----|------|
| **P0** | 词表页树/平铺 + 选择批审 + 按类新增 | 对齐 main 核心 UX |
| **P0** | 同页根分类新增/编辑 | 调本仓 `categories` API |
| **P0** | 专家页未分配 + 分配科室 | 对齐 main 专家实施 |
| **P0** | 入口文案「专家分类」 | Profile + pages.json；收敛「科室分类管理」双入口 |
| **P0** | Merge 候选跨页可搜 | 修共有坑 |
| **保持** | 房间主分类 + C 端优先序 + 不展开子孙 | 已有则回归即可 |
| **P1** | 展示 helper 统一 | 减少各处 `\|\|` 拷贝 |
| **不做（V2.0 本文）** | H5；平行 `pages/app` | 封印 |
| **分类 merge/migrate/级联** | 见 [V2.2](./Live-Saas-Wechat-20-专家分类对齐main治理台-前端设计文档-v2.2.md) | 已解封到增量 |

**现状说明（2026-08-17）**：P0 中「九端点 + 瘦列表 + 专家选词表 + 房间主分类」已有基础；V2.0 实施重点是**交互形态与职责迁移**，不是从零写 API。  
**现状说明（2026-08-26）**：壳层再对齐与分类治理见 V2.2。

---

## 十三、测试要点

| # | 场景 | 期望 |
|---|------|------|
| 1 | 无搜索树模式 | 按分类分组可折叠；组下可新增科室 |
| 2 | 搜索平铺 | 防抖请求；卡片含分类标签 |
| 3 | 选择模式批量通过 | 仅待审可选；`affected`/`成功数` 反馈；标签变已审 |
| 4 | 单条通过 / 停用 / 启用 | 状态与文案正确 |
| 5 | Merge | 二次确认；源消失；Toast 转移人数；目标可跨当前页 |
| 6 | 新增/编辑根分类 | 分组标题更新；不影响《01》独立页可用性 |
| 7 | 专家未分配分配科室 | 列表减少；专家详情有 `department_name` |
| 8 | 专家选词表/纯文本新建 | id 优先；文本不前端建词条 |
| 9 | 房间设主分类 | 卡片 `primary_category_name` |
| 10 | 首页根 Tab | 含子类内容（后端）；前端无本地子孙逻辑 |
| 11 | 非 Admin | 入口隐藏；直打 API → 3003 人话 |

---

## 十四、检查清单

- [ ] 文件名：`Live-Saas-Wechat-20-…-前端设计文档-v2.0.md`
- [ ] 文首声明：行为真源 = main 实施+现码；契约 =《20》后端；落点 = 本仓
- [ ] V1.0 保留且标明不再作实施依据
- [ ] 目录锚点可用
- [ ] 九端点与 `size` / `3003` 口径正确
- [ ] 非目标含：H5、平行 app 路径、前端子孙展开；分类 merge/migrate 指向 V2.2
- [ ] 房间主分类列为保持项
- [ ] 实施分期可执行；测试表覆盖树/平铺/批审/未分配/主分类

---

## 更新日志

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-08-12 | 对照《20》后端起草；瘦 CRUD + 与《01》分离 | — |
| V2.0 | 2026-08-17 | 行为对齐 main 实施/现码；同页根分类 CRUD；未分配迁专家页；保留本仓房间主分类；V1.0 留档 | — |
| V2.0 | 2026-08-26 | 文首/非目标/分期补丁：分类治理解封指向 V2.2；本文仍作词表闭环真源 | — |

---

**文档结束** ✅
