# 专家模块增量开发设计文档 - is_active 与批量导入与关注状态

**版本**: 增量版  
**基于**: 《直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md》  
**状态**: 增量设计（与主设计文档配套使用，冲突时以主文档为准，本文档仅描述增量）

---

## 核心定位说明

本文档描述专家模块的**增量变更**，与主设计文档配套使用，不改变主设计文档既有章节编号与主体内容。增量范围包括：

1. **专家启用状态 is_active**：软删除统一改为「设置 is_active = false」，is_featured 仅表示「是否首页推荐」。
2. **专家信息批量导入（CSV）**：支持通过上传 CSV 批量创建专家，错误隔离、可选去重、结果统计。
3. **检查是否已关注（增强）**：check_is_followed 先校验专家存在且 is_active=true，再查询关注关系；专家不存在或已下架时返回 404。

**增量原则**：最小修改、与主设计文档零冲突、所有修改点显式列出。

**阅读顺序**：先阅读主设计文档全文（尤其 Section 1 设计要点与约定、Section 2.1 experts 表、Section 3 Pydantic Schemas、Section 4 API 接口设计、权限与业务码规范），再阅读本文档。本文档仅描述在上述基础上的增量变更，不重复主文档已有内容。

---

## 依赖与参考

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|----------|----------|----------|
| 1 | 《直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md》 | 主设计文档 | 结构、规范、DDL、Schema、API、执行流程、权限 |
| 2 | 《专家模块设计文档-专家信息-专家关注---CRUD层代码生成提示词.md》 | CRUD 代码生成基准 | 函数清单格式、执行流程与异常约定 |
| 3 | 《专家模块设计文档-专家信息-专家关注---Service层和API层代码生成提示词.md》 | Service/API 代码生成基准 | 权限守卫、方法/端点清单格式 |
| 4 | 《媒体下载服务功能代码生成指令v4-已修正---batch_import_csv功能增量开发提示词.md》 | 批量导入参考 | CSV 格式、错误隔离、去重、结果统计、API 形态 |

---

## 修改点总览

| 序号 | 修改位置 | 变更内容 |
|------|----------|----------|
| 1 | 主设计文档 Section 1.3 软删除策略 | 将「专家软删除：设置 is_featured=false」改为「专家软删除：设置 is_active=false」；注明 is_featured 仅表示首页推荐。 |
| 2 | 主设计文档 Section 2.1 experts 表 | 新增列 is_active BOOLEAN NOT NULL DEFAULT true，注释与索引；迁移说明。 |
| 3 | 主设计文档 Section 3.x Pydantic Schemas | ExpertCreate、ExpertUpdate、ExpertItem 等与专家对象相关的 Schema 增加 is_active（创建默认 True，更新可选，响应必含）；新增批量导入请求/响应 Schema（Section 3.3）。 |
| 4 | 主设计文档 Section 4.x API | 各专家相关 API 的请求/响应示例增加 is_active；新增 Section 4.1.9 批量导入接口；明确 Section 4.2.4 check_is_followed 执行流程（先可见性再订阅）。 |
| 5 | Model（app/models/experts.py） | Expert 模型新增 is_active 字段。 |
| 6 | CRUD（app/crud/experts.py） | create_expert、get_featured_experts、get_experts_multi_and_total、update_expert、delete_expert 的变更；get_expert、get_expert_by_user_id 约定不按 is_active 过滤；批量导入去重复用 get_experts_multi_and_total。**关注列表查询以既有 CRUD 提示词与实现为准，使用 get_user_subscriptions（主文档 Section 1 示例中的函数名已更新为 get_user_subscriptions）**。 |
| 7 | Service（app/services/expert_service.py） | _check_expert_visibility、get_experts_list、get_followed_experts、check_is_followed、set_session_experts 的变更；新增 batch_import_experts_from_csv（保留）；新增 batch_import_experts_from_csv_optimized（单事务+savepoint，API 调用此实现）；get_expert_detail、get_expert_sessions、follow_expert 可见性随守卫变更。 |
| 8 | API（app/api/v1/endpoints/experts.py） | 所有返回专家对象的响应增加 is_active；Admin GET /experts 增加 is_active Query；新增 POST /experts/batch-import（Admin）；check_is_followed 行为随 Service 变更。 |

---

## 数据库变更

### experts 表增量 DDL

```sql
-- 新增列（在现有 experts 表上）
ALTER TABLE experts
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

COMMENT ON COLUMN experts.is_active IS '是否启用（false 表示软删除/下架）';

-- 索引（可选，用于 Admin 列表按 is_active 筛选）
CREATE INDEX idx_experts_is_active ON experts(is_active);
```

**迁移说明**：使用 Alembic 生成 revision，仅包含上述 ADD COLUMN 与 CREATE INDEX；已有数据 is_active 默认为 true。

---

## Schema 变更

### 与专家对象相关的 Schema 增加 is_active

- **ExpertCreate**：增加 `is_active: Optional[bool] = True`（创建时默认 True）。
- **ExpertUpdate**：增加 `is_active: Optional[bool] = None`（可选更新）。
- **ExpertItem**：增加 `is_active: bool`（响应必含）。
- **FeaturedExpertItem**：若首页推荐列表需展示启用状态，可增加 `is_active: bool`；否则仅依赖 get_featured_experts 查询条件过滤。
- **FollowedExpertItem**：若「我的关注」需展示已下架专家则增加 `is_active: bool`；否则由 Service 层过滤。

### 批量导入相关 Schema（新增）

- **BatchImportExpertsResult**（或等效命名）：包含 total、success、failed、skipped、created_expert_ids、failed_rows、skipped_rows、processing_time，与《媒体下载服务 batch_import_csv》参考文档结构对齐。
- **failed_rows / skipped_rows**：每项含 row（行号）、行数据摘要、error/reason。

---

## API 变更

### 已有端点请求/响应变更

- **所有返回专家对象的响应**：data 或 data.items 中每个专家对象增加 `is_active` 字段（与主文档统一响应结构一致）。
- **Admin GET /api/v1/admin/experts**：增加 Query 参数 `is_active: Optional[bool] = None`，传给 Service 的 get_experts_list。

### 新增端点

- **POST /api/v1/admin/experts/batch-import**
  - 描述：上传 CSV 批量创建专家。
  - 认证：Strict Auth；权限：Admin（Service 内 _check_admin_permission，非 Admin 返回 403，业务码 3003）。
  - Content-Type：multipart/form-data。
  - 请求参数：file（必填）、skip_duplicates（可选，默认 false）。
  - 响应：201 全成功 / 207 部分成功 / 400 格式错误或全部失败 / 413 文件过大；data 结构同 BatchImportExpertsResult。
  - 文件校验：扩展名 .csv、最大文件大小（如 10MB）、最大行数（如 1000）、UTF-8 编码；违反时 400/413，与参考文档一致。

### check_is_followed 执行流程与错误码变更

- **GET /api/v1/experts/{expert_id}/is-followed**：不新增路径。
- 执行流程：先 get_expert + _check_expert_visibility（专家不存在或 is_active=false 且非 Admin 则 404），再 get_subscription；响应 key 保持 **is_followed**。
- 错误码：404 专家不存在或已下架（与专家详情一致）；200 返回 `{"is_followed": true/false}`。

---

## 执行流程与错误处理

### 批量导入

1. API 层：校验文件（扩展名、大小、非空、编码）；提取 current_user、role；调用 Service **batch_import_experts_from_csv_optimized**（优化实现：单事务 + 每行 savepoint，一次 commit，与 batch_import_experts_from_csv 返回结构一致）。
2. Service 层：_check_admin_permission(role)；解析 CSV（UTF-8、表头校验）；逐行处理：校验必填列（至少 name）、可选列与 ExpertCreate 对齐；若 skip_duplicates=true，调用 get_experts_multi_and_total(..., name=, hospital=, limit=1) 判断是否存在，存在则记录到 skipped_rows 并 continue；否则在 savepoint 内构造 ExpertCreate（缺省 is_active 视为 true）、调用 create_expert，成功则记录 id 并统计；单行异常回滚该行 savepoint、记录到 failed_rows 并 continue；循环结束后一次 commit；返回与 BatchImportExpertsResult 一致的结构。
3. 错误隔离：单行失败不中断整体；全部失败或表头/文件级错误返回 400；文件过大返回 413。
4. **API 层实现要求**：须遵守变量提取与安全异步异常处理（在 try 前提取 user_id、file 名等用于日志的变量；except 中仅用已提取变量记录日志）；日志脱敏遵循主文档 Section 1.4.3（如 UUID 前 8 位）。与主文档及《生成指令》批量导入专项一致。

### check_is_followed（增强后）

1. Service 层：_check_user_resource_permission(user_id, user_id, role)；get_expert(db, expert_id)；_check_expert_visibility(expert, user_id, user_role)（与主文档 Section 1 参数命名一致；专家不存在或 is_active=False 且非 Admin 则抛出 NotFoundException）；get_subscription(db, user_id, expert_id)；返回 {"is_followed": subscription is not None}。

---

## 测试建议

- **is_active**：创建/更新/删除专家后断言 is_active 值；get_featured_experts 不包含 is_active=False；Admin 列表按 is_active 筛选；非 Admin 访问已下架专家详情/check_is_followed 返回 404；set_session_experts 传入 is_active=False 的专家返回 400。
- **批量导入**：合法 CSV 全成功 201；部分行失败 207、failed_rows 正确；skip_duplicates 跳过已存在；文件过大 413；非 CSV/缺列 400；未认证 401、非 Admin 403。
- **关注状态**：check_is_followed 对已下架专家（非 Admin）返回 404；响应 key 为 is_followed。

---

**文档结束。本文档为主设计文档的补充，须与主设计文档配套使用；冲突时以主文档为准，本文档仅描述增量。功能增强的完整设计详见主文档 Section 1.3、Section 2.1、Section 3.x、Section 4.x。**
