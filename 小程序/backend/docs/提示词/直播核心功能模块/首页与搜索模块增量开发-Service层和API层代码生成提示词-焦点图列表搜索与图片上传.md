# 首页与搜索模块增量开发 - Service 层和 API 层代码生成提示词（焦点图列表搜索与图片上传）

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块（焦点图管理）  
**增量主题**: 焦点图列表搜索（q/search_type）与图片上传  
**目标文件**:  
- `backend/live_core_service/app/services/homepage_search_service.py`  
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`  

**基准提示词**: 《首页与搜索模块设计文档-焦点图-首页API-搜索API---Service层和API层代码生成提示词-Phase1-焦点图.md》

---

## 1. 角色定义

在既有首页与搜索模块 Phase1 焦点图 Service/API 提示词基础上，按本增量提示词**仅修改或新增**下列方法与端点，不重写未变更方法/端点。权限守卫、双轨鉴权、响应标准化、日志脱敏、异常转换与基准提示词一致。

---

## 2. Schema 变更摘要

无。图片上传后更新焦点图使用现有 `FeaturedContentUpdate(image_url=...)`，不新增 Schema。

---

## 3. 需要修改的 Service 方法清单

### 3.1 修改：`get_featured_content_list_admin_paginated`

**函数签名（修改后）**:

```python
async def get_featured_content_list_admin_paginated(
    self,
    db: AsyncSession,
    page: int,
    size: int,
    current_user_id: uuid.UUID,
    role: str,
    q: Optional[str] = None,
    search_type: Optional[str] = None
) -> dict:
```

**功能**: 获取焦点图列表（管理员，分页）。返回统一分页格式 `data: { total, page, size, items }`；支持按 `q`、`search_type` 过滤（与前端《列表筛选与搜索规范》对齐）。

**执行流程（变更步骤）**:

1. 权限检查：`self._check_admin_permission(role)`（不变）。
2. 调用 CRUD：`items, total = await crud.get_featured_content_list_paginated(db, page=page, size=size, q=q, search_type=search_type)`（**新增传入 q、search_type**）。
3. 序列化与返回：与现有一致，`content_items = [FeaturedContentItem.model_validate(item).model_dump(mode='json') for item in items]`，返回 `{ "code": 200, "message": "success", "data": { "total", "page", "size", "items" }, "timestamp" }`。
4. 日志：可保留现有或增加 q、search_type 的简要记录。

---

## 4. 需要新增的 Service 方法

### 4.1 新增：`upload_featured_content_image`

**函数签名**:

```python
async def upload_featured_content_image(
    self,
    db: AsyncSession,
    content_id: uuid.UUID,
    file: UploadFile,
    current_user_id: uuid.UUID,
    role: str
) -> str:
```

**功能**: 为指定焦点图上传图片；校验焦点图存在、调用 FileHandler 保存、更新该焦点图 `image_url`，返回可访问的图片 URL（或相对路径）。

**执行流程**:

1. 权限检查：`self._check_admin_permission(role)`。
2. 校验焦点图存在：`content = await crud.get_featured_content_by_id(db, content_id)`；若 `not content` 则 `raise NotFoundException("焦点图不存在")`（或类似文案）。
3. 调用 FileHandler：`image_url = await FileHandler.save_featured_content_image(file, content_id)`。若 FileHandler 抛 `HTTPException`，可在 Service 内捕获并转为 `InvalidParameterException`，或由 API 层统一捕获。
4. 更新焦点图：`update_data = FeaturedContentUpdate(image_url=image_url)`；`await crud.update_featured_content(db, content_id, update_data)`。
5. 记录日志（如 content_id 前 8 位、管理员前 8 位）。
6. `return image_url`。

**导入**: `from app.schemas.homepage_search import FeaturedContentUpdate`（已有则略）；`from fastapi import UploadFile` 或 `TYPE_CHECKING` 下导入用于类型注解。

---

## 5. 需要修改的 API 端点

### 5.1 修改：GET `/featured-content`（管理员分页列表）

**路径与装饰器**: 保持 `@featured_content_admin_router.get("/featured-content", ...)`。

**变更内容**:

1. **新增 Query 参数**：  
   `q: Optional[str] = Query(None, description="关键词（标题/副标题模糊 或 当 search_type=id 时为焦点图 ID")`  
   `search_type: Optional[str] = Query(None, description="搜索类型：id=按ID精确，name 或不传=按标题/副标题模糊")`
2. **ID 校验**：在调用 Service 前，若 `search_type == "id"` 且 `q` 非空，则 `try: UUID(q)`；`except ValueError:` 返回 `JSONResponse(status_code=400, content=error_response(code=4001, message="无效的焦点图ID格式，请确保为合法 UUID"))`。需在文件头 `from uuid import UUID`（若已有则不改）。
3. **调用 Service**：`result = await service.get_featured_content_list_admin_paginated(db, page, size, user_id, role, q=q, search_type=search_type)`。
4. 其余异常处理与现有一致（PermissionDeniedException → 403/3002；Exception → 500/5001）。

---

## 6. 需要新增的 API 端点

### 6.1 新增：POST `/featured-content/{content_id}/image`

**路径**: 挂在 `featured_content_admin_router` 下，即 `POST /featured-content/{content_id}/image`（与现有 admin 前缀一致，完整路径为 `/api/v1/admin/featured-content/{content_id}/image`）。

**参数**:  
- Path：`content_id: UUID`  
- Body：`file: UploadFile = File(..., description="焦点图图片文件")`  
- Depends：`current_user: dict = Depends(get_current_user)`，`db: AsyncSession = Depends(get_db)`

**逻辑**:

1. 提取 `user_id`、`role`（与列表端点一致，`role` 须 `.upper()`）。
2. 进入 try 块，实例化 `HomepageSearchService()`，调用 `image_url = await service.upload_featured_content_image(db, content_id, file, user_id, role)`。
3. 成功返回：`JSONResponse(status_code=200, content=success_response(data={"content_id": str(content_id), "image_url": image_url}, message="图片上传成功"))`。
4. 异常映射：`PermissionDeniedException` → 403，`error_response(code=3002, ...)`；`NotFoundException` → 404，`error_response(code=2001, message="焦点图不存在")`；`InvalidParameterException` 或 `HTTPException`（文件校验）→ 400，`error_response(code=4001, message=str(e)` 或 `e.detail)`；`Exception` → 500，`error_response(code=5001, ...)` 或 `1002`（与同文件一致）。

**导入**: `from fastapi import File, UploadFile`；`from app.core.response import success_response`（若尚未导入）。

---

## 7. FileHandler 层变更（需同步实现）

本次增量需在 **`backend/live_core_service/app/core/file_handler.py`** 中新增两个方法，风格与 `generate_expert_avatar_path`、`save_expert_avatar` 一致，供 Service 层 `upload_featured_content_image` 调用。生成 Service/API 代码时请同步实现或确保已有实现。

### 7.1 新增：`generate_featured_content_image_path`

**签名**: `def generate_featured_content_image_path(content_id: uuid.UUID, extension: str) -> Tuple[str, str]`  
**功能**: 生成焦点图图片存储路径。目录 `featured-content/{content_id}`（相对 `ROOM_MEDIA_ROOT_PATH`），文件名 `image_{timestamp}.{extension}`；返回 `(fs_path, url_path)`，`url_path` 形如 `/media/featured-content/{content_id}/image_{timestamp}.{ext}`。写盘前 `os.makedirs(fs_dir, exist_ok=True)`。

### 7.2 新增：`save_featured_content_image`

**签名**: `async def save_featured_content_image(file: UploadFile, content_id: uuid.UUID) -> str`  
**功能**: 校验图片（`validate_image_file`）、取扩展名、调用 `generate_featured_content_image_path`、读内容校验 `UPLOAD_MAX_SIZE`、写入 `fs_path`、返回 `url_path`。异常：`HTTPException` 直接 raise，其他可记录日志后 `raise HTTPException(500, detail="文件保存失败")`。

---

## 8. 质量标准

与既有 Service/API 提示词在「权限在 Service 层、双轨鉴权、响应标准化、日志脱敏、安全异步异常处理、try 块前提取 user_id/role」等方面要求一致。不改变未被列出的方法或端点的签名与行为。
