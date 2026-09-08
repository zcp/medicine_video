# 管理端 App 页面 — 前后端对比审查与修复方案

> 项目：live-streaming-saas-v2-main / saas_app-main
> 创建日期：2026-07-28
> 版本：V1.1
> 状态：**审查完成，已实施完毕**
> 关联文档：
> - [管理端后台数据面板_AdminStats设计文档.md](./管理端后台数据面板_AdminStats设计文档.md)
> - [专家分类管理_App端接口优化设计文档.md](./专家分类管理_App端接口优化设计文档.md)
> - [直播间管理接口优化设计文档.md](./直播间管理接口优化设计文档.md)

---

## 目录

1. [审查背景与方法](#一审查背景与方法)
2. [专家分类管理模块](#二专家分类管理模块)
3. [专家管理模块](#三专家管理模块)
4. [焦点图管理模块](#四焦点图管理模块)
5. [修复方案汇总](#五修复方案汇总)
6. [收益分析](#六收益分析)
7. [风险评估](#七风险评估)
8. [实施计划](#八实施计划)

---

## 一、审查背景与方法

### 1.1 审查目的

对 App 端三个管理模块（专家分类管理、专家管理、焦点图管理）的前后端实现进行字段级逐项对比，排查：
- 前端调用了哪些后端接口、使用了哪些字段、未使用哪些字段
- 后端返回了哪些字段、前端缺少哪些类型定义
- 前后端字段名/类型/格式不一致导致的数据丢失或报错
- 接口功能冗余或缺失

### 1.2 审查范围

| 模块 | 后端文件 | 前端页面 | 前端类型 | 前端 API |
|------|---------|---------|---------|---------|
| 专家分类管理 | `endpoints/expert_departments.py`、`crud/expert_departments.py`、`schemas/expert_departments.py` | `admin/departments/index.vue` | `types/department.ts` | `api/department.ts` |
| 专家管理 | `endpoints/experts.py`（admin router）、`schemas/experts.py` | `admin/expert-list/index.vue` | `types/expert.ts` | `api/expert.ts` |
| 焦点图管理 | `endpoints/homepage_search.py`（admin router）、`schemas/homepage_search.py` | `admin/featured/index.vue`、`FeaturedCarousel.vue` | `types/featured.ts` | `api/featured.ts` |

### 1.3 审查方法

- 后端：逐端点读取 request schema 和 response 构造逻辑
- 前端：逐页面读取模板中的字段引用、脚本中的 API 调用和数据绑定
- 对比：建立字段级映射表，标记"匹配"、"缺失"、"冗余"、"类型不一致"

---

## 二、专家分类管理模块

### 2.1 后端端点清单

| # | 端点 | 作用 | 前端调用状态 |
|:--:|------|------|:--:|
| 1 | `GET /admin/expert-departments` | 分页列表，支持 is_verified/category_id/q 筛选 | ✅ 已调用 |
| 2 | `POST /admin/expert-departments` | 创建科室 | ✅ 已调用 |
| 3 | `PATCH /admin/expert-departments/{id}` | 部分更新科室（name/category_id/synonyms/is_verified 等） | ✅ 已调用 |
| 4 | `DELETE /admin/expert-departments/{id}` | 软删除科室 | ✅ 已调用 |
| 5 | `GET /admin/expert-departments/unmapped` | 未分配科室的专家列表 | ✅ 已调用 |
| 6 | `POST /admin/expert-departments/merge` | 合并科室 + 专家迁移 | ✅ 已调用 |
| 7 | `POST /admin/expert-departments/batch-verify` | 批量审核（通过/驳回） | ✅ 已调用 |
| 8 | `GET /admin/expert-departments/{id}` | 科室详情（含 expert_count） | ❌ 未调用 |
| 9 | `PATCH /admin/expert-departments/{id}/category` | 修改科室分类 + 批量同步专家 category_id | ❌ 未调用 |

### 2.2 发现的问题

#### 问题 A-1：batch-verify 响应字段不匹配（中危）

**现象**：后端返回 `{ affected: int }`（实际审核成功的数量），前端读取 `res.data?.success_count`（不存在的字段），永远为 `undefined`。Fallback 到 `ids.length`（选中的数量）。

**危害**：当选中 5 个科室批量审核，其中 2 个已审核、实际只更新了 3 个时，Toast 错误地显示"已审核 5 个科室"——用户被误导认为全部审核成功。

**涉及文件**：`departments/index.vue:587`

#### 问题 A-2：已审核科室不可选的 UX 缺口（低危）

**现象**：批量审核模式下，已审核的科室 checkbox 未被禁用，用户可勾选已审核科室并点"批量审核"。

**危害**：用户操作后无效果（后端跳过已审核的），但前端仍提示"已审核 N 个"，形成困惑。

**涉及文件**：`departments/index.vue` 列表 checkbox 区域

#### 问题 A-3：`ExpertDepartment` 类型缺少 `source` 和 `created_by`（低危）

**现象**：后端 `ExpertDepartmentItem` Schema 包含 `source`（科室来源：auto_match/csv_import/admin_api 等）和 `created_by`（创建人 UUID），但前端 `ExpertDepartment` 接口未声明这两个字段。

**危害**：不影响运行时数据获取（JSON 中字段仍存在），但 TypeScript 无法类型提示，代码重构时可能被遗漏。管理员无法看到科室的来源和创建人信息。

**涉及文件**：`types/department.ts`

#### 问题 A-4：分类编辑不自动同步专家（数据一致性风险）

**现象**：前端编辑弹窗通过通用 `PATCH /admin/expert-departments/{id}` 修改科室的 `category_id`，但该接口只改科室自身，不触发专家 `category_id` 批量同步。专用接口 `PATCH /admin/expert-departments/{id}/category` 才包含同步逻辑——但前端未调用。

**危害**：当管理员把"乳腺外科"从"普通外科"改挂到"肿瘤科"后，科室分类是新值，但下面 26 位专家的 `category_id` 仍为旧值，形成数据不一致。后续按分类筛选专家时，这些专家不会被正确命中。

**涉及文件**：`departments/index.vue:502-504`（编辑提交）、`api/department.ts`（`updateDepartmentCategory` 未调用）

### 2.3 修复方案

| 问题 | 修复 | 位置 | 工时 |
|------|------|------|:--:|
| A-1 | `res.data?.success_count` → `res.data?.affected` | `departments/index.vue:587` | 2min |
| A-2 | 已审核科室 checkbox 加 `:disabled="dept.is_verified"` | `departments/index.vue` 列表 | 2min |
| A-3 | `ExpertDepartment` 接口加 `source: string \| null`、`created_by: string \| null` | `types/department.ts` | 2min |
| A-4 | 编辑弹窗加勾选框"同步更新关联专家的分类"，勾上走 `updateDepartmentCategory`，不勾走 `updateDepartment` | `departments/index.vue` + 弹窗 UI | 0.5h |

**修复后效果**：
- A-1/A-2：批量审核 Toast 显示真实数据，不会误操作已审核科室
- A-3：管理员可查看每个科室的创建来源和创建人
- A-4：管理员修改科室分类时可选择是否同步专家，消除数据不一致风险

---

## 三、专家管理模块

### 3.1 后端端点清单

| # | 端点 | 作用 | 前端调用状态 |
|:--:|------|------|:--:|
| 1 | `GET /admin/experts` | 分页列表，支持 name/is_verified/category_id/department_id 等 8 个筛选参数 | ✅ 已调用 |
| 2 | `POST /admin/experts` | 创建专家 | ✅ 已调用 |
| 3 | `PATCH /admin/experts/{id}` | 部分更新专家 | ✅ 已调用 |
| 4 | `DELETE /admin/experts/{id}` | 软删除专家 | ✅ 已调用 |
| 5 | `POST /admin/experts/batch-import` | CSV 文件批量导入专家 | ❌ 未调用 |
| 6 | `POST /admin/experts/{id}/avatar` | 上传头像图片 | ❌ 未调用 |

### 3.2 发现的问题

#### 问题 B-1：Admin 编辑表单仅 6 字段，后端支持 15 个（中危）

**现象**：当前编辑弹窗只有 name、title、hospital、department_id、bio、avatar_url 六个字段。后端 `ExpertCreate` 支持 15 个字段。

| 缺失字段 | 含义 | 是否需要 |
|---------|------|:--:|
| `expertise_areas` | 擅长领域，列表中已渲染为标签 | **是**——列表展示了但改不了 |
| `category_id` | 主专业分类（心内科/骨科...） | **是**——分类筛选的核心维度 |
| `is_featured` | 是否首页推荐 | **是**——运营常用开关 |
| `is_verified` | 审核状态 | **是**——已有审核按钮，加开关做补充 |
| `is_active` | 启用/下架 | 可选——delete 已覆盖软删除 |
| `sort_order` | 排序权重 | 暂不需要 |
| `contact_info` | 联系方式（JSONB） | 暂不需要 |
| `user_id` | 关联平台用户 | 暂不需要 |

**危害**：管理员在 App 端无法设置专家的擅长领域（但列表能看到）、无法设置分类归属、无法控制首页推荐状态。核心管理操作需要依赖 H5 桌面端完成，App 端管理能力不完整。

**涉及文件**：`expert-list/index.vue` — formModel 定义（line 505）和表单模板

#### 问题 B-2：`category_id` 在 `Expert` 类型中缺失（低危）

**现象**：后端 `format_expert_response()` 返回了 `category_id`，但前端 `Expert` 接口未声明此字段。

**危害**：TypeScript 不认该字段，VSCode 无自动补全和类型校验。运行时字段存在、功能不受影响，但代码健壮性有缺口。

**涉及文件**：`types/expert.ts`

#### 问题 B-3：`batchImportExperts` 前后端协议不匹配（高危）

**现象**：前端 `batchImportExperts` 用 `post()` 发 JSON 请求（`application/json`），后端期望 `multipart/form-data`（`file: UploadFile = File(...)` + `skip_duplicates: bool = Form(...)`）。

**危害**：该函数完全不可用——调用即报错。批量导入专家是许多运营场景的高频需求，前端处于"看起来有但实际上不能点"的状态。

**涉及文件**：`api/expert.ts` — `batchImportExperts` 函数

**根因**：FastAPI 的 `UploadFile` 参数要求请求 Content-Type 为 `multipart/form-data`，但 UniApp 的 `post()` 发送的是 `application/json`。需要用 `uni.uploadFile()` 替换。

#### 问题 B-4：`contact_info` 在 `ExpertUpdate` 中缺失（低危）

**现象**：前端 `ExpertUpdatePayload` 含有 `contact_info` 字段，但后端 `ExpertUpdate` Schema（`schemas/expert.py:65`）中没有此字段。Pydantic 默认行为 `extra='ignore'` 静默丢弃。

**危害**：前端传了联系方式但后端不保存。由于当前 App 端未计划使用 `contact_info`，实际无影响。

**涉及文件**：`schemas/experts.py`（后端）、`types/expert.ts`（前端）

### 3.3 修复方案

| 问题 | 修复 | 位置 | 工时 |
|------|------|------|:--:|
| B-1 | 编辑表单加 expertise_areas（逗号分隔输入）、category_id（下拉选择）、is_featured（开关）、is_verified（开关） | `expert-list/index.vue` 表单模板 + formModel | 1h |
| B-2 | `Expert` 接口加 `category_id: string \| null` | `types/expert.ts` | 2min |
| B-3 | `batchImportExperts` 改为 `uni.uploadFile(filePath, name:'file', formData:{skip_duplicates})` + 平台兼容判断 | `api/expert.ts` | 0.5h |
| B-4 | 暂不处理（`contact_info` 不在 App 端使用范围内） | — | — |

**修复后效果**：
- B-1：管理员可在 App 端完整管理专家：设置擅长领域、选择分类归属、控制推荐和审核状态。编辑弹窗从 6 字段扩充为 10 字段
- B-2：消除 TypeScript 类型缺口，代码补全和校验完整
- B-3：`batchImportExperts` 从不可用变为可用，支持 CSV 文件上传导入

---

## 四、焦点图管理模块

### 4.1 后端端点清单

| # | 端点 | 作用 | 前端调用状态 |
|:--:|------|------|:--:|
| 1 | `GET /featured-content`（公开） | 返回活跃焦点图，最多 10 条 | ✅ 已调用（管理员列表和数据轮播都在用） |
| 2 | `POST /admin/featured-content` | 创建焦点图 | ✅ 已调用 |
| 3 | `PATCH /admin/featured-content/{id}` | 更新焦点图 | ✅ 已调用 |
| 4 | `DELETE /admin/featured-content/{id}` | 删除焦点图 | ✅ 已调用 |
| 5 | `GET /admin/featured-content`（管理端分页） | 分页列表，返回全部记录含已下线/过期 | ❌ 未调用 |
| 6 | `GET /admin/featured-content/{id}` | 单条详情 | ❌ 未调用 |
| 7 | `POST /admin/featured-content/{id}/image` | 上传焦点图图片 | ❌ 未调用 |

### 4.2 发现的问题

#### 问题 C-1：`cta_text` 是全前端幻觉字段（高危）

**现象**：前端从类型定义、创建表单、更新表单、列表展示到轮播组件，全程引用 `cta_text` 字段。
但后端——数据库 `featured_content` 表无此列、Pydantic Schema `FeaturedContentCreate/Update/Item` 无此字段、`_validate_target_resource` 无此逻辑。前端提交的 `cta_text` 被 Pydantic v2 的默认 `extra='ignore'` 行为静默丢弃。

**危害**：
1. 用户在表单填写 CTA 文案 → 点击保存 → 成功提示 → **数据实际未保存**
2. 轮播组件主展示逻辑 `slide.data.cta_text || slide.data.subtitle` → 因为 `cta_text` 永为空，始终 fallback 到 `subtitle`
3. 用户看到的是副标题而非自己填的 CTA 文案，但不知原因

**根因**：前端自行增加了 CTA 按钮文案功能，但后端从未规划、未评审、未实现。设计文档中焦点图功能描述不含 CTA 字段。

**涉及文件**：
- `types/featured.ts` — `FeaturedContent`/`CreatePayload`/`UpdatePayload` 均含 `cta_text`
- `api/featured.ts` — 三个 Admin 函数的参数类型间接引用
- `admin/featured/index.vue` — 表单 L111（CTA 输入框）、列表 L55（CTA 展示）、`formModel` L140
- `FeaturedCarousel.vue` — L37 `slide.data.cta_text || slide.data.subtitle`

#### 问题 C-2：`target_type: 'expert'` 前端支持、后端拒绝（高危）

**现象**：前端焦点图编辑表单的"跳转目标类型"下拉包含 `'expert'`（专家）选项。后端 `_validate_target_resource()` 只支持 `room`/`session`/`topic`/`brand`/`external` 五种，`expert` 不在其中。

**危害**：管理员选择"专家(expert)"并填写目标 ID → 提交 → 后端返回 `400 InvalidParameterException: "不支持的目标类型: expert"`。**一个可选的操作路径通向明确的报错**。

**涉及文件**：`admin/featured/index.vue:143` — `targetTypeValues` 数组

#### 问题 C-3：管理列表用公开接口，无分页、看不到已下线内容（中危）

**现象**：管理端列表页调用 `getFeaturedContent()`，它请求的是公开接口 `GET /featured-content`——只返回最多 10 条活跃项（`is_active=true` 且时间有效）。后端有管理员专用分页接口 `GET /admin/featured-content?page=&size=&q=&search_type=`，但前端未封装、未调用。

**危害**：
1. 焦点图超过 10 条时，列表截断，管理员看不到第 11 条及之后的内容
2. 已下线的焦点图（`is_active=false`）和已过期的焦点图完全不可见——管理员无法恢复、无法审计
3. 无法搜索（按 ID 或标题），只能手动翻找

**涉及文件**：`api/featured.ts`、`admin/featured/index.vue:173`

#### 问题 C-4：前端类型缺 5 个后端字段（低危）

**现象**：后端 `FeaturedContentItem` 返回 `is_active`、`start_at`、`end_at`、`created_at`、`updated_at`，前端 `FeaturedContent` 类型均未声明，表单均未提供编辑控件。

**危害**：
- 管理员无法下架焦点图（只能彻底删除）
- 无法设置定时上线/下线（活动到期后需手动删除）
- 列表不显示创建和更新时间

**涉及文件**：`types/featured.ts`、`admin/featured/index.vue`

#### 问题 C-5：图片上传仅支持 URL 输入，不支持文件上传（低危）

**现象**：编辑表单只有"图片 URL"文本输入框，无文件上传功能。后端有专用上传接口 `POST /admin/featured-content/{id}/image`（`multipart/form-data`，接收图片文件），前端未封装。

**危害**：手机端管理员需要先将图片上传到图床获取 URL，再粘贴到表单——操作链路长。不支持"从相册选图直接上传"的移动端自然体验。

**涉及文件**：`api/featured.ts`（缺封装）、`admin/featured/index.vue`（缺上传 UI）

### 4.3 修复方案

| 问题 | 修复 | 位置 | 工时 |
|------|------|------|:--:|
| C-1 | 前端删除 `cta_text` 的全部引用：类型、表单、列表、轮播组件（`cta_text \|\| subtitle` → `subtitle`） | 4 个文件，共约 -15 行 | 15min |
| C-2 | `targetTypeValues` 删除 `'expert'`，对应 labels 删除 `'专家(expert)'` | `featured/index.vue:142-143` 各减一项 | 2min |
| C-3 | 封装 `getAdminFeaturedContent({page,size,q})` 调 admin 分页接口；列表页改造为分页模式 + 加 Tab（正在展示/已下线/全部）；后端补 `?is_active=` 过滤参数 | `api/featured.ts` + `featured/index.vue` + `homepage_search_service.py` | 1h |
| C-4 | `FeaturedContent` 类型加 `is_active`/`start_at`/`end_at`/`created_at`/`updated_at`；编辑表单加上下线开关 + 日期选择器；列表卡片展示状态和时间信息 | `types/featured.ts` + `featured/index.vue` | 0.5h |
| C-5 | 封装 `uploadFeaturedImage(contentId, filePath)` 调上传接口；表单加"从相册选择"按钮，选图后调上传接口并自动填入 URL | `api/featured.ts` + `featured/index.vue` | 0.5h |

**修复后效果**：
- C-1：消除"数据写入成功但实际丢弃"的 Silent Data Loss 隐患
- C-2：移除无效选项，管理员不会遇到 400 报错
- C-3：列表支持分页翻看、按状态筛选、按关键词搜索，焦点图 >10 条后仍可管理
- C-4：管理员可下架焦点图（不用删除）、设置定时上线/下线、查看创建和更新时间
- C-5：支持从手机相册直接选图上传，图片 URL 自动填入输入框，两种方式并存

---

## 五、修复方案汇总

### 5.1 前端改动清单（16 项，约 4.5h）

| # | 优先级 | 文件 | 改动简述 | 工时 |
|:--:|:--:|------|------|:--:|
| 1 | P0 | `types/featured.ts` | 删除 `cta_text` 字段（3 个接口） | 2min |
| 2 | P0 | `api/featured.ts` | 删除 CreatePayload/UpdatePayload 中的 `cta_text` 类型引用 | 2min |
| 3 | P0 | `featured/index.vue` | 删除表单 CTA 输入框（L111）、列表 CTA 展示（L55）、formModel 中的 cta_text（L140） | 5min |
| 4 | P0 | `FeaturedCarousel.vue` | `slide.data.cta_text \|\| subtitle` → `slide.data.subtitle`（L37） | 2min |
| 5 | P0 | `featured/index.vue` | `targetTypeValues` 删除 `'expert'`，labels 删除 `'专家(expert)'`（L142-143） | 2min |
| 6 | P0 | `departments/index.vue` | batch-verify：`res.data?.success_count` → `res.data?.affected`（L587） | 2min |
| 7 | P0 | `departments/index.vue` | 已审核科室 checkbox 加 `:disabled="dept.is_verified"` | 2min |
| 8 | P1 | `types/department.ts` | `ExpertDepartment` 加 `source`/`created_by` | 2min |
| 9 | P1 | `types/expert.ts` | `Expert` 加 `category_id`（响应类型） | 2min |
| 10 | P1 | `types/featured.ts` | `FeaturedContent` 加 `is_active`/`start_at`/`end_at`/`created_at`/`updated_at` | 5min |
| 11 | P1 | `api/featured.ts` | 封装 `getAdminFeaturedContent`（admin 分页列表）+ `uploadFeaturedImage`（上传图片） | 0.5h |
| 12 | P1 | `featured/index.vue` | 改造列表为 admin 分页接口 + Tab（正在展示/已下线/全部）+ 搜索 | 1h |
| 13 | P1 | `featured/index.vue` | 编辑表单加 is_active 开关 + start_at/end_at 日期选择器 + 列表展示时间信息 | 0.5h |
| 14 | P2 | `expert-list/index.vue` | 编辑表单扩充 expertise_areas、category_id、is_featured、is_verified | 1h |
| 15 | P2 | `departments/index.vue` | 编辑弹窗加"同步更新关联专家的分类"勾选框 | 0.5h |
| 16 | P2 | `api/expert.ts` | `batchImportExperts` 改为 `uni.uploadFile` + FormData | 0.5h |

### 5.2 后端改动清单（2 项，约 1h）

| # | 优先级 | 文件 | 改动简述 | 工时 |
|:--:|:--:|------|------|:--:|
| 17 | P1 | `homepage_search.py`（endpoint） | `GET /admin/featured-content` 加 `?is_active=` Query 参数 | 0.5h |
| 18 | P1 | `homepage_search_service.py` | `get_featured_content_list_admin_paginated` 加 `is_active` 过滤逻辑 | 0.5h |

### 5.3 涉及文件总览

```
saas_app-main/src/
├── types/
│   ├── department.ts         ⚡ 修改 — 加 source/created_by
│   ├── expert.ts             ⚡ 修改 — 加 category_id
│   └── featured.ts           ⚡ 修改 — 删 cta_text、加 5 字段
├── api/
│   ├── featured.ts           ⚡ 修改 — 封装 admin 分页 + 上传
│   └── expert.ts             ⚡ 修改 — batchImport 改 uploadFile
├── pages/app/admin/
│   ├── departments/index.vue ⚡ 修改 — batch-verify 修复、checkbox disabled、同步勾选框
│   ├── expert-list/index.vue ⚡ 修改 — 表单扩充 4 字段
│   └── featured/index.vue    ⚡ 修改 — 删 cta/expert、改分页、加上下线、加图片上传
└── pages/app/tabbar/home/
    └── components/
        └── FeaturedCarousel.vue ⚡ 修改 — cta_text → subtitle

live-streaming-saas-v2-main/backend/live_core_service/app/
├── api/v1/endpoints/
│   └── homepage_search.py         ⚡ 修改 — 加 is_active 参数
└── services/
    └── homepage_search_service.py  ⚡ 修改 — 加 is_active 过滤逻辑
```

### 5.4 不涉及的文件

- 所有 H5 桌面端页面（不在 App 端范围）
- 后端 Model 层（无需新增列）
- 后端数据库迁移（无 DDL 变更）
- 后端 CRUD 层（焦点图 is_active 过滤可复用现有条件）

---

## 六、收益分析

### 6.1 消除 Silent Data Loss

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| `cta_text` | 用户填写后保存，数据静默丢弃，轮播显示副标题而非 CTA | 字段删除，轮播直接显示副标题，语义明确 |
| batch-verify | 选中已审核科室仍可点审核，Toast 显示数量不准确 | 已审核不可选中，显示真实审核数量 |

### 6.2 消除明确报错

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| `target_type: 'expert'` | 选专家后提交 → 400 报错 | 选项移除，不会触发此路径 |

### 6.3 App 端管理能力补全

| 修复 | 修复前 | 修复后 |
|------|--------|--------|
| 专家表单扩充 | 只能编辑 6 个基础字段 | 可设置擅长领域、分类归属、推荐和审核状态（10 字段） |
| 焦点图上下线 | 只能创建/删除，无法下架或定时 | 可下架、可设置上线/下线时间 |
| 焦点图分页 | 列表最多显示 10 条，超出的不可见 | 分页翻看，可筛选已下线内容 |
| 焦点图图片上传 | 需手动填 URL，无法从相册选图 | URL 输入 + 相册选图上传并存 |

### 6.4 代码质量提升

| 修复 | 修复前 | 修复后 |
|------|--------|--------|
| 类型缺口（3 处） | TypeScript 无类型提示和校验 | 完整类型覆盖 |
| `batchImportExperts` | 函数存在但调用即报错 | 函数可用 |
| 科室分类同步 | 改分类后专家数据不一致 | 可选同步，数据一致性可保障 |

---

## 七、风险评估

### 7.1 前端改动风险

| 风险 | 描述 | 概率 | 影响 | 对策 |
|------|------|:--:|:--:|------|
| 删除 `cta_text` 后轮播语义变化 | 轮播组件从 `cta \|\| subtitle` 改为仅 `subtitle`，可能影响展示效果 | 低 | 验证轮播组件在修复后的展示效果 |
| `uni.uploadFile` 跨平台兼容 | 部分小程序平台不支持文件选择，`uni.chooseFile` API 可能存在兼容性差异 | 中 | 加 `#ifdef APP-PLUS` 条件编译，不支持的平台隐藏按钮或降级为 URL 输入 |
| 专家表单字段扩充后 UI 过长 | 编辑弹窗从 6 字段扩到 10 字段，在小屏手机上可能需要滚动 | 低 | 弹窗本身已使用 `scroll-view`，无需额外处理 |
| `start_at`/`end_at` 日期选择器格式 | UniApp `<picker mode="date">` 返回的日期格式可能是 `YYYY-MM-DD`，后端期望 ISO 8601 | 低 | 提交时将日期转为 ISO 8601（`new Date(val).toISOString()`） |
| 焦点图 admin 分页接口格式切换 | 当前公开接口返回数组 `data: [...]`，admin 分页接口返回 `data: {total, page, size, items}` | 低 | 封装 `getAdminFeaturedContent` 时适配新的响应格式 |

### 7.2 后端改动风险

| 风险 | 描述 | 概率 | 影响 | 对策 |
|------|------|:--:|:--:|------|
| `is_active` 参数与现有 `q`/`search_type` 交互 | 三个参数组合时 SQL 条件拼接是否正确 | 低 | 每个参数独立 `if` 追加条件，互不影响 |
| 公开接口 `GET /featured-content` 的 `is_active` 逻辑 | 公开接口已过滤 `is_active=True`，admin 接口不应受此限制 | 无 | admin 接口不加 `is_active` 默认过滤，仅当传参时追加条件 |

### 7.3 文档核验补充的风险

| 风险 | 描述 | 概率 | 影响 | 对策 |
|------|------|:--:|:--:|------|
| 焦点图列表切换分页接口后 `res.data` 从数组变为对象 | 现有代码 `items.value = res.data`（期望数组），分页接口返回 `{total, items, page, size}`，取值路径变化 | 高 | 封装 `getAdminFeaturedContent` 时内部统一提取 `res.data.items` 作为返回值 |
| FeaturedCarousel 删 `cta_text` 后 `v-if` 条件也需同步 | L35 条件为 `slide.data.cta_text \|\| slide.data.subtitle`，删 cta_text 后忘记改条件将导致 CTA 区域显隐逻辑依赖不复存在的字段 | 中 | 同步修改为 `slide.data.subtitle` |

---

## 八、实施计划

### 8.1 总览

| 阶段 | 名称 | 工时 | 项数 | 依赖 | 上线风险 |
|:--:|------|:--:|:--:|------|:--:|
| Phase 1 | 清障型 —— 消隐患、补缺口 | 0.5h | 16 | 无 | 极低 |
| Phase 2 | 核心功能型 —— 焦点图管理升级 | 3h | 10 | Phase 1 | 低 |
| Phase 3 | 增强型 —— 专家表单 + 分类同步 | 0.8h | 5 | Phase 1 | 低 |
| **总计** | | **4.3h** | | | |

> **原方案 5.5h → 调整为 4.3h**。Phase 3 剔除 2 项：`is_verified` switch（与审核通过按钮双控点冲突）和 `batchImportExperts` 修复（无 App 端 UI 触发路径）。

---

### 8.2 Phase 1：清障型 —— 消隐患、补缺口（0.5h / 16 项全部做）

**目标**：清除已知的 Silent Data Loss 和 400 报错，补齐类型定义缺口。零风险、零后端依赖。

**判定**：前端评估"6 个必须做 + 2 个应该做。总 30min，零风险，纯删代码/加类型/改属性"——完全正确。

#### 操作清单

| # | 文件 | 操作 | 行数 | 工时 |
|:--:|------|------|:--:|:--:|
| 1 | `types/featured.ts` | 删除 `FeaturedContent`、`CreatePayload`、`UpdatePayload` 中的 `cta_text` 字段 | -4 | 2min |
| 2 | `featured/index.vue` | 删除 formModel 中的 `cta_text: ''`（L140） | -1 | 2min |
| 3 | `featured/index.vue` | 删除列表展示 `cta_text`（L55） | -1 | — |
| 4 | `featured/index.vue` | 删除表单 CTA 输入框（L109-112） | -4 | — |
| 5 | `featured/index.vue` | 删除 payload 中 `cta_text`（L227） | -1 | — |
| 6 | `FeaturedCarousel.vue` | L35 `v-if` 条件：`\|\| slide.data.cta_text` → 删除 | -1 | 2min |
| 7 | `FeaturedCarousel.vue` | L37 表达式：`slide.data.cta_text \|\| slide.data.subtitle` → `slide.data.subtitle` | -1 | — |
| 8 | `featured/index.vue` | `targetTypeValues` 删除 `'expert'`，`targetTypeLabels` 删除 `'专家(expert)'`（L142-143） | -2 | 2min |
| 9 | `departments/index.vue` | L587：`res.data?.success_count` → `res.data?.affected` | 1 | 2min |
| 10 | `departments/index.vue` | 已审核科室 checkbox 加 `:disabled="dept.is_verified"` | +1 | 2min |
| 11 | `types/department.ts` | `ExpertDepartment` 加 `source: string \| null`、`created_by: string \| null` | +2 | 2min |
| 12 | `types/expert.ts` | `Expert` 加 `category_id: string \| null` | +1 | 2min |
| 13 | `types/featured.ts` | `FeaturedContent` 加 `is_active: boolean`、`start_at: string \| null`、`end_at: string \| null`、`created_at: string`、`updated_at: string` | +5 | 2min |
| 14 | `types/featured.ts` | `FeaturedContentCreatePayload` 加 `subtitle?: string` | +1 | 2min |
| 15 | `types/featured.ts` | `FeaturedContentUpdatePayload` 加 `subtitle?: string` | +1 | — |

**风险**：极低。删除的是后端从未返回/从不接受的字段，不影响任何现有数据流。

**验证方式**：TypeScript/Hbuilder 编译通过 + departments 批量选择已审核不可勾选 + featured 下拉无 expert 选项 + 轮播 CTA 正常展示。

---

### 8.3 Phase 2：核心功能型 —— 焦点图管理升级（3h / 10 项全部做）

**目标**：焦点图从"无分页、无上下线、公开接口"升级为"分页管理、支持上下线、定时上下线、图片上传"。需要后端配合加一个参数。

**已确认**：`GET /admin/featured-content` 返回的 `FeaturedContentItem` 与公开接口字段完全一致（11 字段全量），仅多分页包装和不过滤 `is_active`。后端多返回的 `is_active`/时间字段已在 Phase 1 #13 加类型声明。

#### 操作清单

##### 后端（1h）

| # | 文件 | 操作 | 工时 |
|:--:|------|------|:--:|
| B1 | `homepage_search.py`（endpoint） | `GET /admin/featured-content` 加 `is_active: Optional[bool] = Query(None)` | 0.3h |
| B2 | `homepage_search_service.py` | `get_featured_content_list_admin_paginated` 方法签名加 `is_active` 参数，query 内加 `if is_active is not None: conditions.append(FeaturedContent.is_active == is_active)` | 0.5h |
| B3 | 重建 Docker 容器验证 | `docker-compose -f compose-app.windows.yml up -d --build live_core_service` | 0.2h |

##### 前端（2h）

| # | 文件 | 操作 | 工时 |
|:--:|------|------|:--:|
| F1 | `api/featured.ts` | 封装 `getAdminFeaturedContent(params)` — 调 `GET /admin/featured-content?page=&size=&q=&is_active=`，⚠️ **关键**：内部统一提取 `res.data.items`，外层包装为 `{items, total, page, size}` | 0.3h |
| F2 | `api/featured.ts` | 封装 `uploadFeaturedImage(contentId, filePath)` — 用 `uni.uploadFile` 调 `POST /admin/featured-content/{id}/image` | 0.2h |
| F3 | `featured/index.vue` | `loadList()` 从 `getFeaturedContent()` 改为 `getAdminFeaturedContent({page,size,is_active})`，适配分页响应格式 | 0.3h |
| F4 | `featured/index.vue` | 列表顶部加三个 Tab：正在展示 / 已下线 / 全部，切换时 `is_active` 分别传 `true`/`false`/不传，重设 page=1 重新加载 | 0.3h |
| F5 | `featured/index.vue` | 编辑表单加 `is_active` 开关（switch）、`start_at`/`end_at` 日期选择器（`picker mode="date"`），提交时 `new Date(val + 'T00:00:00').toISOString()` | 0.3h |
| F6 | `featured/index.vue` | 列表卡片展示：上线/下线状态标签、上线时间、下线时间、创建时间 | 0.2h |
| F7 | `featured/index.vue` | 图片 URL 输入框旁加"从相册选择"按钮 → `uni.chooseImage` → 调 F2 → 自动填入 URL | 0.3h |
| F8 | `featured/index.vue` | 分页触底加载更多（复用 departments 页的 `hasMore`/`loadMore` 模式） | 0.1h |

**⚠️ 最大风险点**（前端评估已指出）：

```typescript
// ❌ 错误写法（直接替换会导致 items 被赋值为整个对象）
items.value = res.data  // res.data = {total, items, page, size}

// ✅ 正确写法（F1 封装内部处理）
// api/featured.ts:
export const getAdminFeaturedContent = (params) => {
  return get('/admin/featured-content', params, { auth: true }).then(res => ({
    items: res.data.items,
    total: res.data.total,
    page: res.data.page,
    size: res.data.size,
  }))
}
// featured/index.vue:
items.value = result.items
```

**验证方式**：
- 调 admin 分页接口，返回 items 长度正确
- 切换 Tab 后列表正确过滤
- 创建焦点图设置 `start_at` 为明天 → 公开接口不可见、admin 列表可见（定时生效确认）
- 相册选图上传后 URL 自动填入输入框

---

### 8.4 Phase 3：增强型 —— 专家表单 + 分类同步（0.8h / 5 项）

**目标**：专家编辑弹窗扩充 `expertise_areas`、`category_id`、`is_featured` 三个字段，科室编辑加分类同步选项。

**剔除 2 项**（经前端评估确认）：

| 剔除项 | 剔除理由 |
|--------|---------|
| ~~专家表单加 `is_verified` switch~~ | `expert-list/index.vue:141` 已有"审核通过"按钮，加 switch 形成双控点冲突，不增值 |
| ~~`batchImportExperts` 改为 `uni.uploadFile`~~ | 手机端不适合 CSV 导入（用户已确认），修复后无 App 端 UI 触发入口，纯僵尸函数修复 |

#### 操作清单

| # | 文件 | 操作 | 工时 |
|:--:|------|------|:--:|
| E1 | `expert-list/index.vue` | `formModel` 加 `expertise_areas: ''`、`category_id: null`、`is_featured: false` | 0.1h |
| E2 | `expert-list/index.vue` | `openEditForm` 从 item 回填新增字段 | 0.1h |
| E3 | `expert-list/index.vue` | 编辑表单加：擅长领域（逗号分隔输入框）、分类（下拉选择，数据源 `getCategories()`，已有不重复请求）、首页推荐（switch） | 0.3h |
| E4 | `expert-list/index.vue` | `handleFormConfirm` payload 加新增 3 字段（trim 后 undefined 过滤） | 0.1h |
| E5 | `departments/index.vue` | 编辑弹窗表单加勾选框"同步更新关联专家的分类"（默认不勾）+ `handleFormConfirm` 编辑分支：勾选调 `updateDepartmentCategory`，不勾选调 `updateDepartment` | 0.2h |

**收益**：
- E1-E4：修复核心 UX 断裂——列表卡片已展示擅长领域标签但编辑弹窗改不了
- E5：消除科室改分类后专家数据不一致的隐患（勾上才同步，默认不勾，安全默认值）

**风险**：低。新增字段不影响现有逻辑。E2 回填时 `expertise_areas` 后端存逗号分隔字符串，列表也按逗号 split 渲染标签，回填直接赋值字符串即可。E5 创建模式不走同步逻辑（创建时还没有关联专家）。

**验证方式**：
- 编辑专家：打开弹窗 → 填擅长领域、选分类、开推荐开关 → 保存 → 刷新列表，卡片新增字段正确展示
- 科室编辑：打开弹窗 → 改分类、勾选"同步更新关联专家" → 保存 → 检查该科室下专家的 `category_id` 是否全部更新

---

### 8.5 工序依赖图

```
Phase 1（0.5h，清障）
   │
   ├─── Phase 2（3h，焦点图）─── 可并行 ─── Phase 3（0.8h，专家表单）
   │    ├── B1-B3 后端（1h）                  ├── E1-E4（0.6h）
   │    └── F1-F8 前端（2h）                  └── E5（0.2h）
   │
   └── Phase 2/3 均依赖 Phase 1（类型要在其他改动之前修好），但彼此之间无依赖，可并行实施
```

### 8.6 总工时

| 阶段 | 前端 | 后端 | 合计 |
|:--:|:--:|:--:|:--:|
| Phase 1 | 0.5h | 0h | 0.5h |
| Phase 2 | 2h | 1h | 3h |
| Phase 3 | 0.8h | 0h | 0.8h |
| **总计** | **3.3h** | **1h** | **4.3h** |

### 8.7 涉及文件总览

```
saas_app-main/src/
├── types/
│   ├── department.ts         ⚡ Phase 1 — 加 source/created_by
│   ├── expert.ts             ⚡ Phase 1 — 加 category_id
│   └── featured.ts           ⚡ Phase 1 — 删 cta_text、加 5 字段 + subtitle
├── api/
│   └── featured.ts           ⚡ Phase 2 — 封装 admin 分页 + 上传
├── pages/app/admin/
│   ├── departments/index.vue ⚡ Phase 1 — batch-verify + checkbox disabled
│   │                         ⚡ Phase 3 — 分类同步勾选框
│   ├── expert-list/index.vue ⚡ Phase 3 — 表单扩充 3 字段
│   └── featured/index.vue    ⚡ Phase 1 — 删 cta/expert
│                              ⚡ Phase 2 — 分页 + 上下线 + 上传
└── pages/app/tabbar/home/
    └── components/
        └── FeaturedCarousel.vue ⚡ Phase 1 — cta_text → subtitle

live-streaming-saas-v2-main/backend/live_core_service/app/
├── api/v1/endpoints/
│   └── homepage_search.py         ⚡ Phase 2 — 加 is_active 参数
└── services/
    └── homepage_search_service.py  ⚡ Phase 2 — 加 is_active 过滤
```

### 8.8 不做项清单

| 原方案编号 | 不做项 | 不做理由 | 决策来源 |
|-----------|--------|---------|---------|
| E3 部分 | 专家表单加 `is_verified` switch | 与 `expert-list/index.vue:141` "审核通过"按钮形成双控点冲突 | 前端评估，已确认 |
| E7/E9 | `batchImportExperts` 改为 `uni.uploadFile` + 加 UI 按钮 | 手机端不适合 CSV 批量导入（用户已确认）；修复后无 App 端 UI 触发入口，纯僵尸函数修复 | 前端评估，已确认 |

---

## 九、实施记录（2026-07-28 实施完毕）

### 9.1 Phase 1 — 清障（16 项 / 6 文件）

| # | 文件 | 改动 |
|:--:|------|------|
| P1-1~3 | `types/featured.ts` | `FeaturedContent` 删 `cta_text` + 加 `is_active`/`start_at`/`end_at`/`created_at`/`updated_at`；`CreatePayload`/`UpdatePayload` 删 `cta_text` + 加 `subtitle` |
| P1-4 | `types/department.ts` | `ExpertDepartment` 加 `source: string \| null`、`created_by: string \| null` |
| P1-5 | `types/expert.ts` | `Expert` 加 `category_id: string \| null` |
| P1-6~10 | `featured/index.vue` | 删 `formModel`、列表、表单、payload、`openEditForm`/`closeForm` 中的 `cta_text`；`targetTypeValues`/`targetTypeLabels` 删 `'expert'` / `'专家(expert)'`；删死 CSS `.feat-cta` |
| **P1-11~14** | **`FeaturedCarousel.vue`** | **L35/L37 `cta_text \|\|` → 删除；L218-219 debug 日志删 cta_text 引用；3 条 mock 数据 `cta_text` → `subtitle`** |
| P1-15 | `departments/index.vue` | `res.data?.success_count` → `res.data?.affected` |
| P1-16 | `departments/index.vue` | 两处 checkbox：`dept-check--disabled` class + 条件阻止 toggle + CSS 禁用 |

> P1-11~14 为代码核实阶段新增项（debug 日志 + mock 数据残留），原方案 15 项 → 实施 16 项。

### 9.2 Phase 2 — 焦点图管理升级（10 项 / 4 文件）

#### 后端（B1-B3 / 3 文件）

| # | 文件 | 改动 |
|:--:|------|------|
| B1 | `homepage_search.py` | `GET /admin/featured-content` 加 `is_active: Optional[bool] = Query(None)` |
| B2 | `homepage_search_service.py` | `get_featured_content_list_admin_paginated` 加 `is_active` 参数 + WHERE 条件 |
| B3 | — | Docker 重建，接口行为：`?is_active=true` 仅已上线 / `?is_active=false` 仅已下线 / 不传全部 |

#### 前端（F1-F8 / 2 文件）

| # | 文件 | 改动 |
|:--:|------|------|
| F1+F2 | `api/featured.ts` | `getAdminFeaturedContent(params)` + `uploadFeaturedImage(contentId, filePath)` 用 `uni.uploadFile` |
| F3 | `featured/index.vue` | `loadList(reset)` 改调 `getAdminFeaturedContent`，支持 `page/size` 分页 + `is_active` 筛选 |
| F4 | `featured/index.vue` | 模板加 `.tab-bar` 三 Tab（正在展示/已下线/全部），`onTabChange(key)` 切换 + reset |
| F5 | `featured/index.vue` | 编辑表单加 `is_active` switch + `start_at`/`end_at` date picker |
| F6 | `featured/index.vue` | 卡片加 `.status-tag`（已上线绿/已下线灰）+ `.feat-times` 时间行 |
| F7 | `featured/index.vue` | 图片 URL 行改为 `.form-row` flex，加"从相册选择"按钮 → `handleChooseImage()` |
| F8 | `featured/index.vue` | 加 `page/size/total/hasMore/isLoadingMore` + `loadMore()` + `.load-more` UI |

**关键设计**：
- `loadList(reset=true)`：reset 时 `page=1 + items=[]`；false 时追加
- payload 新增 `is_active`（boolean）、`start_at`/`end_at`（选填 → ISO 8601）
- `openEditForm` 回填 `is_active`/`start_at`/`end_at`，日期用 `formatDate()` 截取前 10 位
- `handleChooseImage`：`uni.chooseImage` → `uploadFeaturedImage` → 自动填入 `image_url`
- 文件从 481 行 → 716 行（+235）

### 9.3 Phase 3 — 专家表单 + 分类同步（5 项 / 2 文件）

| # | 文件 | 改动 |
|:--:|------|------|
| E1 | `expert-list/index.vue` | `formModel` 加 `expertise_areas: ''`、`category_id: null`、`is_featured: false` |
| E2 | `expert-list/index.vue` | `openEditForm`/`closeForm` 回填/重置 3 字段 |
| E3 | `expert-list/index.vue` | 表单加：擅长领域 `<input>`、分类 `<picker>`（复用 `categories.value`，参照 dept picker 模式）、首页推荐 `<switch>`；加 `formCatLabels`/`formCatName`/`onFormCatChange` 辅助函数 |
| E4 | `expert-list/index.vue` | `handleFormConfirm` payload 加 3 字段 |
| E5 | `departments/index.vue` | 导入 `updateDepartmentCategory`；新增 `syncExpertCategory` ref；表单加勾选框（仅编辑模式）；4 处重置；编辑分支：先 `updateDepartment` 再按需 `updateDepartmentCategory` |

**关键设计**（与文档方案差异）：
- 同步采用"先自身更新、后专家同步"策略，防止只同步分类却丢失科室名/同义词修改
- `syncExpertCategory` 每次打开弹窗/关闭/成功后重置为 `false`
- 分类 picker 完全复用 `categories.value`（已在 `loadFilters()` 加载），零额外 API 请求

### 9.4 实际变更统计

| 阶段 | 文件数 | 净增行 | 净删行 |
|:--|:--:|:--:|:--:|
| Phase 1 清障 | 6 | +27 | -25 |
| Phase 2 焦点图 | 2 | +285 | -50 |
| Phase 3 增强 | 2 | +58 | 0 |
| **合计** | **8** | **+370** | **-75** |

### 9.5 实施方案与文档差异说明

| 差异项 | 文档方案 | 实际实施 | 原因 |
|--------|---------|---------|------|
| P1 项数 | 15 项 | 16 项 | 代码核实时发现 FeaturedCarousel debug 日志（L218-219）+ mock 数据（L245/255/265）残留 cta_text |
| E5 同步策略 | 勾选→`updateDepartmentCategory` / 不勾选→`updateDepartment` | 始终先调 `updateDepartment`，再按需调 `updateDepartmentCategory` | 防止同步分类时丢失科室名/同义词修改 |
| F1 返回值 | 文档建议 `.then()` 包装为 `{items,total,page,size}` | 直接在 `loadList` 中读取 `res.data.items` / `res.data.total` | `get()` 返回 `ApiResponse<PaginatedResponse<T>>`，原生类型安全 |
| Phase 3 字段数 | 文档说 10 字段 | 实际 9 字段（6 原有 + 3 新增） | 剔除 `is_verified` switch 后为 9 字段 |
| Phase 2 后端 | 文档计划 3 文件 | 实际 3 文件，接口测试通过 | 无差异 |

---

**最后更新**: 2026-07-28（补充实施记录）
**总体状态**: 三阶段全部实施完毕，前端 8 文件 + 后端 3 文件，累计 +370/-75 行。
