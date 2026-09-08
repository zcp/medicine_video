# 专家模块增量开发 - Service 层和 API 层代码生成提示词

**模块名称**: experts  
**功能模块名称**: 专家模块增量（is_active、批量导入、check_is_followed 增强）  
**目标文件**: `backend/live_core_service/app/services/expert_service.py`、`backend/live_core_service/app/api/v1/endpoints/experts.py`  
**配套文档**: 与现有《专家模块设计文档-专家信息-专家关注---Service层和API层代码生成提示词.md》配套使用；先阅读现有提示词（角色、职责、权限守卫、Schema 摘要），再按本增量提示词仅修改或新增下列内容。

---

## 1. 角色定义

在既有专家 Service/API 提示词基础上，按本增量提示词修改/新增下列方法与端点。角色与职责与现有 Service/API 提示词一致（Service 层业务逻辑与权限检查，API 层请求解析与响应）。

---

## 2. Schema 变更摘要

### 2.1 专家相关 Schema 增加 is_active

- **ExpertCreate**：增加 `is_active: Optional[bool] = True`（创建时默认 True）。
- **ExpertUpdate**：增加 `is_active: Optional[bool] = None`（可选更新）。
- **ExpertItem**：增加 `is_active: bool`（响应必含）。
- **FeaturedExpertItem**：若需在推荐列表中返回启用状态可增加 `is_active: bool`；否则仅依赖 CRUD 查询条件过滤。
- **FollowedExpertItem**：若「我的关注」需展示已下架专家则增加 `is_active: bool`；否则由 Service 层过滤。

### 2.2 批量导入相关 Schema（新增）

- **BatchImportExpertsResult**（或等效命名）：包含 total、success、failed、skipped、created_expert_ids、failed_rows、skipped_rows、processing_time，与《媒体下载服务 batch_import_csv》参考文档结构对齐。
- **failed_rows**：每项含 row（行号）、行数据摘要、error。
- **skipped_rows**：每项含 row、行数据摘要、reason。

---

## 3. 权限守卫与可见性

### 3.1 _check_expert_visibility（修改）

**实现要点（修改后）**：
- 若 expert 为 None，抛出 NotFoundException("专家不存在")。
- 可见性判断：**仅依据 expert.is_active**；当 `expert.is_active == False` 且 `role not in ['ADMIN', 'SUPERADMIN']` 时，记录警告日志并抛出 NotFoundException("专家不存在")（404 伪装）。
- **删除**所有「is_featured 表示已删除」的逻辑与注释；不再使用 is_featured 判断可见性。

### 3.2 仅调用 _check_expert_visibility 的 Service 方法（无方法体变更）

以下方法可见性逻辑随 _check_expert_visibility 变更，**无需修改方法体**，仅在增量提示词中注明：
- **get_expert_detail**：调用 get_expert + _check_expert_visibility，守卫改为 is_active 后自动生效。
- **get_expert_sessions**：同上。
- **follow_expert**：调用 get_expert + _check_expert_visibility 后再创建关注，守卫改为 is_active 后自动生效。

---

## 4. 需要修改的 Service 方法清单

### 4.1 get_experts_list

**函数签名（变更）**：
```python
async def get_experts_list(
    self,
    page: int = 1,
    size: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    current_user_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None
) -> Dict[str, Any]
```

**功能**: 获取专家列表（Admin 分页）（变更：增加 is_active 参数并传给 CRUD）

**权限/鉴权**: 不变，_check_admin_permission(role)

**执行流程（仅写变更步骤）**:
- 调用 CRUD 时增加参数：`experts, total = await crud.get_experts_multi_and_total(self.db, skip, size, name, is_featured, is_active, hospital, sort)`（即增加 is_active 参数）。

---

### 4.2 get_followed_experts

**功能**: 获取关注列表（变更：约定是否过滤 is_active=False 的专家）

**执行流程（仅写变更步骤）**:
- 若约定「我的关注」只展示启用专家：在构造列表时过滤掉 `sub.expert.is_active == False`（或由 CRUD get_user_subscriptions 增加过滤参数）；若展示已下架专家，则 FollowedExpertItem 需含 is_active 字段。

---

### 4.3 check_is_followed

**功能**: 检查是否已关注专家（变更：先 get_expert + _check_expert_visibility，再 get_subscription；专家不存在或已下架时抛出 NotFoundException；响应 key 保持 is_followed）

**权限/鉴权**: 不变，_check_write_permission(current_user_id, current_user_id, role)

**执行流程（仅写变更步骤）**:
1. 权限检查：`self._check_write_permission(current_user_id, current_user_id, role)`
2. **新增**：`expert = await crud.get_expert(self.db, expert_id)`；`self._check_expert_visibility(expert, current_user_id, role)`（专家不存在或 is_active=False 且非 Admin 则抛出 NotFoundException）
3. 调用 CRUD：`subscription = await crud.get_subscription(self.db, current_user_id, expert_id)`
4. 返回：`return {"is_followed": subscription is not None}`（响应 key 保持 is_followed）

---

### 4.4 set_session_experts

**功能**: 为场次设置专家列表（变更：在「专家是否存在」校验后增加「专家须 is_active=True」，否则 InvalidParameterException）

**执行流程（仅写变更步骤）**:
- 在 for item in normalized 循环中，获取 expert 后增加判断：若 `expert.is_active == False`，抛出 `InvalidParameterException("仅允许启用状态的专家关联场次", code=4001)`（或等效文案）。

---

## 5. 需要新增的 Service 方法

### 5.1 batch_import_experts_from_csv

**函数签名**：
```python
async def batch_import_experts_from_csv(
    self,
    file_content: bytes,
    skip_duplicates: bool = False,
    role: Optional[str] = None
) -> Dict[str, Any]
```

**功能**: 从 CSV 文件批量创建专家；错误隔离、可选去重、结果统计，与《媒体下载服务 batch_import_csv》风格一致。

**权限/鉴权**: Service 层内调用 `_check_admin_permission(role)`，非 Admin 返回 403（业务码 3003）；遵循主设计文档「Service 层全权负责 Authorization」的架构原则。

**返回值结构**: 与 BatchImportExpertsResult 对齐，包含 total、success、failed、skipped、created_expert_ids、failed_rows、skipped_rows、processing_time。

**执行流程**:
1. **权限检查**：调用 `self._check_admin_permission(role)`，非 Admin 抛出 PermissionDeniedException（业务码 3003）。
2. 解码文件（UTF-8），使用 csv.DictReader 解析；校验表头至少含 name；可选列与 ExpertCreate 对齐（title、hospital、department、expertise_areas、bio、avatar_url、is_featured、sort_order、is_active），缺省 is_active 视为 True。
3. 逐行处理：每行 try-except，单行异常记录到 failed_rows 并 continue；校验必填（至少 name）；若 skip_duplicates=True，调用 `get_experts_multi_and_total(self.db, skip=0, limit=1, name=..., hospital=...)` 判断是否存在，存在则记录到 skipped_rows 并 continue；否则构造 ExpertCreate（缺省 is_active=True），调用 `create_expert(self.db, expert_data)`；成功则累计 success 并收集 created_expert_ids（如最多前 100 个）。
4. 统计 total、success、failed、skipped、processing_time；返回字典。

**异常**: 表头缺必需列、文件编码错误、超过最大行数等抛出 ValueError；数据库异常按既有规范处理。

---

## 6. 需要修改的 API 端点

### 6.1 所有返回专家对象的端点

**变更**: 响应 data 中每个专家对象增加 is_active 字段。若使用 format_expert_response，则在该函数中增加 `"is_active": expert.is_active`（或从 Schema 序列化时已含 is_active）。

涉及端点（与现有实现一致）：GET 推荐专家、GET 专家详情、GET 专家场次列表（expert_info）、POST 创建专家、GET Admin 专家列表、PATCH 更新专家、GET 关注列表、GET 场次专家列表等凡返回专家对象的响应。

### 6.2 Admin GET /experts

**路径**: GET /api/v1/admin/experts（与现有路由一致：experts_admin_router 注册在 prefix="/admin"，路径为 "/experts"）

**变更**: 增加 Query 参数 `is_active: Optional[bool] = Query(default=None, description="按启用状态筛选")`，传给 Service 的 get_experts_list。

---

## 7. 需要新增的 API 端点

### 7.1 POST /api/v1/admin/experts/batch-import

**路径**: 在 experts_admin_router 上注册 `@experts_admin_router.post("/experts/batch-import")`，完整路径为 `/api/v1/admin/experts/batch-import`（与现有 Admin 专家路由一致）。

**描述**: 上传 CSV 批量创建专家。

**认证**: `Depends(get_current_user)`；Service 内调用 `_check_admin_permission(role)`，非 Admin 返回 403，业务码 3003（与主设计一致）。

**请求**: multipart/form-data；参数 file（必填，CSV）、skip_duplicates（可选，默认 False）。

**文件校验**（在解析 CSV 前执行，与参考文档一致）：扩展名 .csv；最大文件大小（如 10MB）；最大行数（如 1000）；UTF-8 编码；空文件拒绝。违反时返回 400/413，并在 data 中提供必要信息（如 missing_columns、file_size、max_size）。

**响应**: 201 全成功；207 部分成功（data 含 total/success/failed/skipped/created_expert_ids/failed_rows/skipped_rows/processing_time）；400 格式错误或全部失败；413 文件过大；403 非 Admin（业务码 3003）。

**实现要求**: API 层须遵守变量提取与安全异步异常处理（在 try 前提取 user_id_for_logging、file_name_for_logging 等；except 中仅使用提取变量记录日志）；日志脱敏（UUID 前 8 位）。

---

## 8. 质量标准

与现有 Service/API 提示词在「权限在 Service 层、双轨鉴权、响应标准化、日志脱敏、安全异步异常处理」等方面要求一致。不改变未被列出的方法或端点的签名与行为。与既有 Service/API 提示词在命名、结构、格式上保持完全一致，无冲突。

---

**文档结束。**
