# 内容管理模块增量开发 - CRUD 层代码生成提示词（Categories 与 Tags 列表搜索能力补齐）

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories与Tags列表搜索能力补齐.md》  
**定位**：在既有内容管理 CRUD（app/crud/content_management.py）基础上，按本增量提示词**仅修改**下列两个函数，增加 `q`、`search_type` 参数及 WHERE 条件逻辑；不新增函数、不修改其他函数。

**使用前**：须先使用《增量开发设计文档与主设计文档一致性检查提示词母版》对上述增量设计文档与主设计文档（合并版）通过一致性检查后，再使用本提示词生成或修改代码。

---

## 角色定义

在既有内容管理 CRUD 实现基础上，按本增量提示词**修改** `get_categories_paginated` 与 `get_tags` 两个函数，增加列表搜索能力（ID 精确 + 字符串字段模糊）；不重写未变更函数。

---

## Model 字段变更摘要

无。不新增字段。引用既有 Model：

- **Category**（app/models/content_management.py）：id (UUID)、name、slug、sort_order、icon、description、is_active、created_at、updated_at 等。
- **Tag**（app/models/content_management.py）：id (UUID)、name、slug、is_active、created_at、updated_at 等。

本列表的**字符串搜索字段（可配置字符串搜索字段列表）**由设计文档显式声明：Categories 为 `["name"]`，Tags 为 `["name"]`。实现时从设计约定或模块常量读取（如 `CATEGORY_LIST_SEARCH_FIELDS`、`TAGS_LIST_SEARCH_FIELDS`），**禁止在函数内多处写死 `name`**。

---

## 需要修改的 CRUD 函数清单

### 1. get_categories_paginated

- **当前签名**（从 app/crud/content_management.py 读取）：  
  `async def get_categories_paginated(db, page, size, is_active, current_user_id, role) -> Tuple[List[Category], int]`
- **修改后签名**：  
  `async def get_categories_paginated(db, page, size, is_active, current_user_id, role, q: Optional[str] = None, search_type: Optional[str] = None) -> Tuple[List[Category], int]`
- **功能**：在现有「分页 + is_active + 权限过滤」基础上，增加 **ID 精确查询** 与 **字符串字段模糊查询**。
- **执行流程（仅写变更步骤）**：
  1. 在构建 `conditions` 时，**新增**对 `q`、`search_type` 的处理：
     - 若 `search_type == 'id'` 且 `q` 非空且为合法 UUID：追加 `Category.id == uuid_value`（需在函数内将 `q` 转为 UUID 后比较；若调用方已校验则可直接使用）。
     - 否则若 `q` 非空：对**本列表的字符串搜索字段**做模糊匹配。设计文档声明为 `["name"]`，即 `Category.name.ilike(f'%{q}%')`（或使用参数化避免注入）。若使用常量 `CATEGORY_LIST_SEARCH_FIELDS`，则对该列表中的字段做 OR 或首列模糊（与设计/现有项目风格一致）。
     - `q` 为空则不施加上述条件。
  2. **同一套 WHERE 条件**（含现有 is_active、role 过滤 + 上述 q/search_type 条件）用于**总数查询**与**分页列表查询**；不得仅对分页列表施加 q 条件。
  3. 总数查询与分页查询的 `conditions` 一致；offset/limit 仅应用于分页查询。
- **异常/日志**：无新增异常；若 `search_type=id` 且 `q` 非法 UUID，由 **API 层** 校验并返回 400，CRUD 层可不重复校验（若 Service 已下传合法 UUID 或 None）。

---

### 2. get_tags

- **当前签名**（从 app/crud/content_management.py 读取）：  
  `async def get_tags(db, is_active, current_user_id, role) -> List[Tag]`
- **修改后签名**：  
  `async def get_tags(db, is_active, current_user_id, role, q: Optional[str] = None, search_type: Optional[str] = None) -> List[Tag]`
- **功能**：在现有「权限过滤 is_active」基础上，增加 **ID 精确查询** 与 **字符串字段模糊查询**。
- **执行流程（仅写变更步骤）**：
  1. 在构建 `conditions` 时，**新增**对 `q`、`search_type` 的处理：
     - 若 `search_type == 'id'` 且 `q` 非空且为合法 UUID：追加 `Tag.id == uuid_value`。
     - 否则若 `q` 非空：对**本列表的字符串搜索字段**做模糊匹配。设计文档声明为 `["name"]`，即 `Tag.name.ilike(f'%{q}%')`（或参数化）；实现时从设计约定/常量 `TAGS_LIST_SEARCH_FIELDS` 读取，不写死 `name`。
     - `q` 为空则不施加上述条件。
  2. 同一套 WHERE 条件用于列表查询（get_tags 无分页，仅单次列表查询）。
- **异常/日志**：无新增异常；UUID 校验在 API 层完成。

---

## 需要约定的 CRUD（无代码变更）

- 字符串搜索字段列表（可配置字符串搜索字段列表 / searchableTextFields）以设计文档为准：Categories 列表为 `["name"]`，Tags 列表为 `["name"]`。代码中建议使用模块级常量（如 `CATEGORY_LIST_SEARCH_FIELDS = ["name"]`、`TAGS_LIST_SEARCH_FIELDS = ["name"]`）以便后续主文档扩展（如增加 slug）时只改一处。

---

## 列表分页（仅 get_categories_paginated）

- 总数与列表必须使用**相同** WHERE 条件；先 count 再 offset/limit；不改变返回形式 `(list, total)`。

---

## 质量标准

与既有 content_management CRUD 一致：异步 AsyncSession、类型提示、IntegrityError 转换、日志脱敏、**角色比较使用大写 `['ADMIN', 'SUPERADMIN']`**。不改变未被列出的函数。

**文档结束**
