# 内容管理模块增量开发 - Service 层和 API 层代码生成提示词（Categories 与 Tags 列表搜索能力补齐）

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories与Tags列表搜索能力补齐.md》  
**定位**：在既有内容管理 Service（app/services/content_management_service.py）与 API（app/api/v1/endpoints/content_management.py）基础上，按本增量提示词**仅修改**与 Categories 管理员列表、Tags 列表相关的方法与端点，增加 `q`、`search_type` 的接收、传递及 API 层 UUID 校验；不新增端点、不改变既有响应结构。

**使用前**：须先使用《增量开发设计文档与主设计文档一致性检查提示词母版》对上述增量设计文档与主设计文档（合并版）通过一致性检查后，再使用本提示词生成或修改代码。

---

## 角色定义

在既有内容管理 Service/API 基础上，按本增量提示词**修改** `get_categories_admin` 端点、`get_tags` 端点及对应的 Service 方法 `get_categories_paginated`、`get_tags_list`，增加列表搜索能力（ID 精确 + 字符串字段模糊）；不修改未列出的方法或端点。

---

## Schema 变更摘要

无。不新增 Schema；仅增加列表接口的 **Query 参数**（见下文），响应结构（如 `CategoryAdminListResponse`、`TagListResponse`）不变。

---

## 需要修改的 Service 方法清单

### 1. get_categories_paginated

- **当前签名**（从 app/services/content_management_service.py 读取）：  
  `async def get_categories_paginated(self, db, page, size, is_active, current_user_id, role) -> CategoryAdminListResponse`
- **修改后签名**：  
  `async def get_categories_paginated(self, db, page, size, is_active, current_user_id, role, q: Optional[str] = None, search_type: Optional[str] = None) -> CategoryAdminListResponse`
- **功能**：在现有分页、is_active、权限检查基础上，将 `q`、`search_type` 下传 CRUD。
- **执行流程（仅写变更步骤）**：  
  调用 CRUD 时增加参数：`await crud_content_management.get_categories_paginated(db, page, size, is_active, current_user_id, role, q=q, search_type=search_type)`。  
  不改变响应构造（仍为 total、page、size、items）。

---

### 2. get_tags_list

- **当前签名**（从 app/services/content_management_service.py 读取）：  
  `async def get_tags_list(self, db, current_user_id, role) -> TagListResponse`
- **修改后签名**：  
  `async def get_tags_list(self, db, current_user_id, role, q: Optional[str] = None, search_type: Optional[str] = None) -> TagListResponse`
- **功能**：在现有 is_active、权限逻辑基础上，将 `q`、`search_type` 下传 CRUD。
- **执行流程（仅写变更步骤）**：  
  确定 `is_active` 后，调用 CRUD 时增加参数：`await crud_content_management.get_tags(db, is_active, current_user_id, role, q=q, search_type=search_type)`。  
  不改变响应构造。

---

## 需要修改的 API 端点

### 1. GET /categories/admin（管理员分类列表）

- **路由**：挂载于 prefix="/content"，完整路径为 GET /api/v1/content/categories/admin。
- **现有 Query**：page、size、is_active。
- **本次增加 Query**：  
  - `q`（optional, str）：关键词或主键 ID。  
  - `search_type`（optional, str）：`id` | `keyword`。未传或非 `id` 时视为关键词模糊。
- **变更步骤**：  
  1. 在端点中增加 `q: Optional[str] = Query(None)`、`search_type: Optional[str] = Query(None)`。  
  2. **若 `search_type == 'id'` 且 `q` 非空**：校验 `q` 为合法 UUID（如 `uuid.UUID(q)` 捕获 ValueError）；非法则 `return JSONResponse(status_code=400, content=error_response(code=4001, message="无效的ID格式"))`。  
  3. 调用 Service 时传入：`await service.get_categories_paginated(db, page, size, is_active, current_user_id, role, q=q, search_type=search_type)`。  
  4. 响应结构不变（CategoryAdminListResponse）。

---

### 2. GET /tags（标签列表）

- **路由**：完整路径为 GET /api/v1/content/tags。
- **现有 Query**：无。
- **本次增加 Query**：  
  - `q`（optional, str）：关键词或主键 ID。  
  - `search_type`（optional, str）：`id` | `keyword`。未传或非 `id` 时视为关键词模糊。
- **变更步骤**：  
  1. 在端点中增加 `q: Optional[str] = Query(None)`、`search_type: Optional[str] = Query(None)`。  
  2. **若 `search_type == 'id'` 且 `q` 非空**：校验 `q` 为合法 UUID；非法则返回 400，code 4001。  
  3. 调用 Service 时传入：`await service.get_tags_list(db, current_user_id, role, q=q, search_type=search_type)`。  
  4. 响应结构不变（TagListResponse）。

---

## 列表搜索（本增量核心）

- **Query 参数**：统一使用 `q`、`search_type`（复用现有 query 参数体系，不新增 DSL）。
- **ID 精确优先**：当 `search_type=id` 且 `q` 非空时，API 层须先校验 UUID，再下传；CRUD 层按主键精确匹配。
- **字符串模糊**：当 `search_type` 非 `id`（或未传）且 `q` 非空时，对设计文档声明的**可配置字符串搜索字段列表**做模糊匹配；Categories 与 Tags 本接口均为 `["name"]`，实现时从设计约定或常量读取，不写死 `name`。

---

## 质量标准

与既有内容管理 Service/API 一致：权限在 Service 层、双轨鉴权、响应 success_response/error_response、日志脱敏、**try 块前提取 user_id/role**、异常转换为 JSONResponse。不改变未列出的方法或端点。

**文档结束**
