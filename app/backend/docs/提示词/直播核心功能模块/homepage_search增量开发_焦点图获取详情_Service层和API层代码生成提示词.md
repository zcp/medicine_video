# homepage_search 增量开发 - Service 层和 API 层代码生成提示词（焦点图获取详情）

**版本**: 增量版  
**模块名称**: 首页与搜索模块 (homepage_search)  
**增量主题**: 焦点图获取详情接口（GET /api/v1/featured-content/admin/{content_id}）  
**对应设计文档**:
- 主设计文档：`docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`
- 增量设计文档：`docs/03_系统设计/首页与搜索模块增量开发设计文档-焦点图获取详情接口.md`

---

## 1. 角色定义

在既有 homepage_search Service/API 提示词基础上，按本增量提示词**仅新增**下列方法与端点；不修改既有方法或端点。

---

## 2. Schema 变更摘要

无。复用主文档 Section 3.1 的 `FeaturedContentItem`。

---

## 3. 需要新增的 Service 方法

| 方法名 | 签名 | 功能 | 执行流程 | 异常 |
|--------|------|------|----------|------|
| `get_featured_content_detail_admin` | `async def get_featured_content_detail_admin(self, db: AsyncSession, content_id: uuid.UUID, current_user_id: uuid.UUID, role: str) -> dict` | 管理员获取单条焦点图详情；用于详情页。 | 1. `_check_admin_permission(role)`；2. `content = await crud.get_featured_content_by_id(db, content_id)`；3. 若 `content is None` 则 `raise NotFoundException("焦点图不存在: {content_id}")`；4. `content_item = FeaturedContentItem.model_validate(content).model_dump(mode='json')`；5. 返回与同文件其他 Admin 方法一致的 dict：`{"code": 200, "message": "success", "data": content_item, "timestamp": ...}`（或调用 `success_response(data=content_item)` 若项目统一使用）。 | PermissionDeniedException（非 ADMIN/SUPERADMIN）；NotFoundException（焦点图不存在）。 |

---

## 4. 需要新增的 API 端点

| 方法 | 路径 | 描述 | 认证 | 参数 | 响应 | 错误码 |
|------|------|------|------|------|------|--------|
| GET | `/admin/{content_id}` | 获取焦点图详情（Admin） | `Depends(get_current_user)` | Path `content_id`: UUID | 200，body 为统一格式，`data` 为单条 FeaturedContentItem | 401 未认证；403 业务码 3002；404 业务码 2001；500 业务码 5001 |

**实现要点**:
- 在 `app/api/v1/endpoints/homepage_search.py` 的 `router`（prefix `/featured-content`）上新增端点，即路径为 `GET /admin/{content_id}`，完整 URL 为 `GET /api/v1/featured-content/admin/{content_id}`。
- 在 try 块之前提取 `user_id`、`role`（`.upper()`），与同文件 `update_featured_content_endpoint`、`delete_featured_content_endpoint` 一致。
- 调用 `service.get_featured_content_detail_admin(db, content_id, user_id, role)`。
- 成功：`return JSONResponse(status_code=200, content=result)`。
- 异常映射：PermissionDeniedException → 403、error_response(code=3002)；NotFoundException → 404、error_response(code=2001)；Exception → 500、error_response(code=5001)。

---

## 5. 质量标准

与既有 Service/API 提示词在「权限在 Service 层、双轨鉴权、响应标准化、日志脱敏、安全异步异常处理」等方面要求一致。不改变未被列出的方法或端点的签名与行为。
