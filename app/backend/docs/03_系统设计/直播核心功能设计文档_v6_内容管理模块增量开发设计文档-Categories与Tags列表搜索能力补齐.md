# 内容管理模块增量开发设计文档 - Categories 与 Tags 列表搜索能力补齐

**版本**: 增量版  
**基于**: 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》  
**状态**: 增量设计（与主设计文档配套使用，冲突时以主文档为准，本文档仅描述增量）

---

## 1. 核心定位说明

### 1.1 范围与关系

本增量在**不新增表、不新增字段、不改变既有响应结构**的前提下，为内容管理模块的以下两个列表接口补齐/标准化搜索能力：

1. **Categories 列表**：`GET /api/v1/content/categories/admin` — 补齐 `q` 模糊搜索（匹配分类名称等字符串字段）及 ID 精确查询。
2. **Tags 列表**：`GET /api/v1/content/tags` — 标准化为支持 **ID 精确查询** 与 **字符串字段模糊查询**（基于设计文档显式声明的「可配置字符串搜索字段列表」，不写死为 name）。

与主设计文档关系：主文档 Section 4.2.3、4.1.1（及 6.4.1 示例）未完整约定列表的 Query 参数 `q`、`search_type` 及字符串搜索字段；本增量在主文档基础上**补漏**，与《列表筛选与搜索规范》及母版「ID 精确 + 字符串模糊」约定对齐。

**阅读顺序**：先阅读主设计文档全文（尤其 Section 1、2、3、4 及权限/业务码规范），再阅读本文档。本文档仅描述在上述基础上的增量变更，不重复主文档已有内容。

### 1.2 增量原则

- 最小幅度修改，仅影响上述两个列表接口及其对应的 CRUD、Service。
- 复用现有 Query 参数体系：**优先使用 `q`**，配合 `search_type`（`id` | `keyword` 或未传表示关键词），不新增 DSL。
- **ID 精确查询优先**于模糊查询（当 `search_type=id` 且 `q` 非空时按主键精确匹配）。
- 不新增字段；不改变既有响应结构（如 `CategoryAdminListResponse`、`TagListResponse` 的 `data` 结构不变）。

---

## 2. 依赖与参考

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|----------|----------|----------|
| 1 | 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》 | 主设计文档，本文档在其基础上补漏 | API 4.2.3、4.1.1 列表 Query 与 CRUD 条件 |
| 2 | 前端《列表筛选与搜索规范》 | 对齐 q、search_type、UUID 校验 | API 层 Query 设计、CRUD 条件逻辑 |

---

## 3. 修改点总览

| 序号 | 修改位置 | 变更内容 |
|------|----------|----------|
| 1 | 主设计文档 Section 4.2.3（GET /api/v1/admin/categories） | 请求参数增加 `q`（可选）、`search_type`（可选，`id` \| `keyword`）；本列表的字符串搜索字段（可配置字符串搜索字段列表）显式声明为 `["name"]`；执行流程增加「q/search_type 处理」与「CRUD 条件逻辑」说明。 |
| 2 | 主设计文档 Section 4.1.1（GET /api/v1/tags） | 请求参数增加 `q`（可选）、`search_type`（可选，`id` \| `keyword`）；本列表的字符串搜索字段（可配置字符串搜索字段列表）显式声明为 `["name"]`；执行流程增加「q/search_type 处理」与「CRUD 条件逻辑」说明。 |
| 3 | API（app/api/v1/endpoints/content_management.py） | `get_categories_admin`：增加 Query 参数 `q`、`search_type`；当 `search_type=id` 且 `q` 非空时对 `q` 做 UUID 校验，非法则 400。`get_tags`：增加 Query 参数 `q`、`search_type`；当 `search_type=id` 且 `q` 非空时对 `q` 做 UUID 校验，非法则 400。 |
| 4 | CRUD（app/crud/content_management.py） | `get_categories_paginated`：增加参数 `q`、`search_type`；同一套 WHERE 条件用于总数与分页列表；`search_type=id` 且 q 为合法 UUID 时 `WHERE id = :id`；否则 q 非空时对 `name` 模糊（ILIKE）；`get_tags`：增加参数 `q`、`search_type`；同上逻辑，字符串搜索字段为设计文档声明的 `["name"]`。 |
| 5 | Service（app/services/content_management_service.py） | `get_categories_paginated`：增加参数 `q`、`search_type`，下传 CRUD；`get_tags_list`：增加参数 `q`、`search_type`，下传 CRUD。 |

---

## 4. 与主文档关系及合并决策说明

| 序号 | 修改位置 | 变更类型 | 合并决策 | 简要说明 |
|------|----------|----------|----------|----------|
| 1 | 主文档 Section 4.2.3 | 补漏 | 并入主文档对应位置 | 主文档未约定 admin 分类列表的 q/search_type 及字符串搜索字段，本增量补充。 |
| 2 | 主文档 Section 4.1.1 | 补漏 | 并入主文档对应位置 | 主文档 6.4.1 示例有 q/name 模糊，但 4.1.1 未正式约定 Query 与 search_type；本增量标准化为 q+search_type+显式字符串搜索字段。 |
| 3 | API / CRUD / Service 代码 | 新增行为 | 以本文档为准 | 在既有接口上增加 Query 与条件逻辑，不改变路径与响应结构。 |

---

## 5. 数据库变更

无。不新增表、不新增字段。

---

## 6. Schema 变更

无。请求体与响应 Schema 不变；仅增加列表接口的 **Query 参数**（见下文 API 变更）。

---

## 7. API 变更

### 7.1 已有端点请求变更（Query 参数）

#### 7.1.1 GET /api/v1/content/categories/admin（管理员分类列表）

- **现有 Query**：`page`、`size`、`is_active`（主文档 4.2.3 及当前实现已支持）。
- **本次增加 Query**：
  - `q`（optional, string）：关键词或主键 ID。与 `search_type` 配合使用。
  - `search_type`（optional, string）：`id` \| `keyword`。未传或非 `id` 时视为关键词模糊。
- **语义**：
  - 当 `search_type=id` 且 `q` 非空：按主键精确匹配；**API 层须校验 `q` 为合法 UUID**，非法则返回 400（code 4001）。
  - 当 `search_type` 非 `id`（或未传）且 `q` 非空：对**本列表的字符串搜索字段**做模糊匹配（ILIKE）。本接口的**字符串搜索字段（可配置字符串搜索字段列表）**在设计文档中显式声明为 **`["name"]`**（分类名称）；实现时从设计约定或配置读取该列表（如常量 `CATEGORY_LIST_SEARCH_FIELDS`），不在多处写死 `name`；后续若主文档扩展可增加 slug 等。
  - `q` 为空时：不施加关键词/ID 条件。
- **优先级**：ID 精确优先；与现有 `page`、`size`、`is_active` 组合为 AND 关系。响应结构不变（仍为 `CategoryAdminListResponse`：`total`、`page`、`size`、`items`）。

#### 7.1.2 GET /api/v1/content/tags（标签列表）

- **现有 Query**：无（当前实现无 Query 参数）。
- **本次增加 Query**：
  - `q`（optional, string）：关键词或主键 ID。
  - `search_type`（optional, string）：`id` \| `keyword`。未传或非 `id` 时视为关键词模糊。
- **语义**：
  - 当 `search_type=id` 且 `q` 非空：按主键精确匹配；API 层须校验 `q` 为合法 UUID，非法则 400。
  - 当 `search_type` 非 `id`（或未传）且 `q` 非空：对**本列表的字符串搜索字段**做模糊匹配。本接口的**字符串搜索字段（可配置字符串搜索字段列表 / searchableTextFields）**在设计文档中显式声明为 **`["name"]`**（标签名称）；实现时从设计约定或配置读取该列表（如常量 `TAGS_LIST_SEARCH_FIELDS`），不在多处写死 `name`；后续若主文档扩展可增加 slug 等。
  - `q` 为空时：不施加关键词/ID 条件。
- **优先级**：ID 精确优先；与现有权限过滤（is_active）组合为 AND。响应结构不变（仍为 `TagListResponse`）。

---

## 8. 执行流程与错误处理

### 8.1 GET /api/v1/content/categories/admin（增强后）

1. JWT 验证与管理员权限检查（与主文档一致）。
2. **新增**：若请求带有 `q` 且 `search_type=id`，校验 `q` 为合法 UUID；非法则返回 400，code 4001。
3. 参数校验：page、size、is_active（与主文档一致）。
4. 调用 Service：`get_categories_paginated(db, page, size, is_active, current_user_id, role, q=q, search_type=search_type)`。
5. Service 将 `q`、`search_type` 下传 CRUD；CRUD 构建同一套 WHERE 条件（含 q/search_type 分支）用于 COUNT 与分页列表查询。
6. 构建分页响应（total、page、size、items），返回 200。错误码与主文档一致（2001、3003、4001 等）。

### 8.2 GET /api/v1/content/tags（增强后）

1. JWT 可选验证（get_current_user_optional），提取 current_user_id、role。
2. **新增**：若请求带有 `q` 且 `search_type=id`，校验 `q` 为合法 UUID；非法则返回 400，code 4001。
3. 调用 Service：`get_tags_list(db, current_user_id, role, q=q, search_type=search_type)`。
4. Service 将 `q`、`search_type` 下传 CRUD；CRUD 构建 WHERE 条件（权限过滤 + q/search_type 分支），用于列表查询。
5. 构建 TagListResponse，返回 200。错误码与主文档一致。

---

## 9. 测试建议

- **Categories admin 列表**：1）无 q：行为与现有一致（分页、is_active）；2）q=合法 UUID + search_type=id：返回至多一条，id 匹配；3）q=关键词 + search_type=keyword 或未传：对 name 模糊，分页与 total 一致；4）q=非法字符串 + search_type=id：返回 400。
- **Tags 列表**：1）无 q：行为与现有一致；2）q=合法 UUID + search_type=id：返回至多一条；3）q=关键词：对 name 模糊；4）q=非法 UUID + search_type=id：返回 400。
- 回归：确认 GET /api/v1/content/categories、GET /api/v1/content/sessions/{id}/tags、直播间分类等接口行为未变。

---

## 10. 文档结束语

本文档为主设计文档的补充，须与主设计文档配套使用；冲突时以主文档为准，本文档仅描述增量。功能增强的完整设计详见主文档 Section 4.2.3、4.1.1 及 6.4；本增量仅在上述两处列表接口上增加 q/search_type 及可配置字符串搜索字段的约定与实现要求。
