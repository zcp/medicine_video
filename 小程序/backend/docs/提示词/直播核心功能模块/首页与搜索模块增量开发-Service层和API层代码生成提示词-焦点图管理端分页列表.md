# 首页与搜索模块增量开发 - Service 层和 API 层代码生成提示词（焦点图管理端分页列表）

**模块名称**: 首页与搜索模块  
**增量主题**: 焦点图管理端分页列表接口  
**目标文件**:
- `backend/live_core_service/app/services/homepage_search_service.py`
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`
- `backend/live_core_service/app/api/v1/api.py`

**基于**: 《首页与搜索模块增量开发设计文档-焦点图管理端分页列表接口.md》  
**配套**: 与《首页与搜索模块设计文档-焦点图-首页API-搜索API---Service层和API层代码生成提示词-Phase1-焦点图.md》同构使用，仅新增下列方法与端点。

---

## 1. 角色定义

在既有首页与搜索模块 Phase1 Service/API 提示词基础上，按本增量提示词**仅新增**下列方法与端点；不修改已有方法/端点签名与行为。

---

## 2. Schema 变更摘要

无。复用 `FeaturedContentItem`（主文档 Section 3.1）。

---

## 3. 权限守卫与可见性

无变更。沿用既有 `_check_admin_permission(role)`（Phase1 已定义）。

---

## 4. 需要新增的 Service 方法

### 4.1 方法：`get_featured_content_list_admin_paginated`

**方法签名**:

```python
async def get_featured_content_list_admin_paginated(
    self,
    db: AsyncSession,
    page: int,
    size: int,
    current_user_id: uuid.UUID,
    role: str
) -> dict
```

**功能**: 获取焦点图列表（管理员，分页）。返回主文档统一分页格式 `{"code": 200, "message": "success", "data": {"total": int, "page": int, "size": int, "items": [...]}, "timestamp": str}`。

**权限/鉴权**: 入口调用 `self._check_admin_permission(role)`，非 ADMIN/SUPERADMIN 抛出 `PermissionDeniedException`。

**执行流程**:

1. 调用 `_check_admin_permission(role)`。
2. 调用 `crud.get_featured_content_list_paginated(db, page=page, size=size)`，得到 `(items, total)`。
3. 序列化：`content_items = [FeaturedContentItem.model_validate(item).model_dump(mode='json') for item in items]`。
4. 记录日志：`logger.info(f"查询焦点图列表（管理员分页），page={page}, size={size}, total={total}, 管理员={str(current_user_id)[:8]}")`。
5. 返回：
   ```python
   return {
       "code": 200,
       "message": "success",
       "data": {
           "total": total,
           "page": page,
           "size": size,
           "items": content_items
       },
       "timestamp": datetime.utcnow().isoformat()
   }
   ```

**异常**: `PermissionDeniedException` 由调用方（API 层）捕获并返回 403。

---

## 5. 需要新增的 API 端点

### 5.1 端点：`GET /api/v1/admin/featured-content`（分页列表）

**路径**: 需通过**独立路由器**暴露为 `GET /api/v1/admin/featured-content`。即在 `homepage_search.py` 中新增 `featured_content_admin_router = APIRouter()`，在该 router 上注册 `GET /featured-content`，在 `api.py` 中 `include_router(featured_content_admin_router, prefix="/admin")`，使完整路径为 `/api/v1` + `/admin` + `/featured-content`。

**请求**: Query 参数 `page`（默认 1）、`size`（默认 10，建议上限 100）。  
**认证**: `Depends(get_current_user)`（Strict Auth）。  
**响应**: 200 时 body 为 Service 返回的完整结构（含 `data.total`、`data.page`、`data.size`、`data.items`）。  
**错误**: 403（PermissionDeniedException）、401（未认证）、500（服务器错误）；与 Phase1 一致使用 `error_response(code=3002, message=...)` 等。

**实现要点**:

- 在 try 块前从 `current_user` 提取 `user_id`、`role`，`role = (current_user.get("role") or "REGULAR").upper()`。
- 调用 `service.get_featured_content_list_admin_paginated(db, page, size, user_id, role)`。
- 使用 `JSONResponse(status_code=200, content=result)` 返回。
- 捕获 `PermissionDeniedException` 返回 403。

---

## 6. 质量标准

与既有 Phase1 Service/API 提示词在「权限在 Service 层、双轨鉴权、响应标准化、日志脱敏」等方面要求一致。未列出的方法或端点不得修改。
