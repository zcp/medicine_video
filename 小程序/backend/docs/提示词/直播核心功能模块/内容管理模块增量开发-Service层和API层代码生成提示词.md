# 内容管理模块增量开发 - Service 层和 API 层代码生成提示词

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-直播间与分类多对多.md》  
**定位**：在既有内容管理 Service/API 基础上，按本增量提示词新增与 live_room_categories 相关的方法与端点。

---

## 角色定义

在既有内容管理 Service（app/services/content_management_service.py）与 API（app/api/v1/endpoints/content_management.py）基础上，按本增量提示词**新增**房间-分类相关方法与端点，不修改既有 Tags/Categories/Session_Tags 的方法与端点。

---

## Schema 变更摘要

- **LiveRoomCategoriesSetRequest**：category_ids: List[UUID]（min_length=1, max_length=50），mode: Literal["replace","append"]；category_ids 唯一性校验。
- **LiveRoomCategoriesSetResponse**：data 含 room_id、mode、categories: List[CategoryItem]。
- **LiveRoomCategoriesListResponse**：code、message、data: List[CategoryItem]、timestamp（与主文档统一响应一致）。

---

## 需要新增的 Service 方法清单

### 1. get_live_room_categories_list(db, room_id, current_user_id, role) -> LiveRoomCategoriesListResponse

- **功能**：获取某直播间的分类列表（公开）；若房间不存在返回 2001。
- **权限**：Optional Auth；不按角色过滤分类列表（仅返回 is_active=true 的分类，在 CRUD 层实现）。
- **执行流程**：1）校验房间存在（调用 crud_room.get_room 或等价）；2）若不存在 raise NotFoundException；3）调用 crud_content_management.get_categories_by_room_id(db, room_id)；4）构建 LiveRoomCategoriesListResponse 返回。
- **异常**：NotFoundException -> 2001。

### 2. set_live_room_categories(db, room_id, body, current_user_id, role) -> LiveRoomCategoriesSetResponse

- **功能**：批量设置某直播间的分类（Admin）。
- **权限**：_check_admin_permission(role)；房间不存在 2001；category_ids 中无效或未启用 4001。
- **执行流程**：1）_check_admin_permission；2）校验房间存在；3）校验 body.category_ids 均在 categories 且 is_active=true（批量查 categories）；4）调用 crud set_live_room_categories(db, room_id, body.category_ids, body.mode)；5）用 get_categories_by_room_id 取当前列表，构建 LiveRoomCategoriesSetResponse。
- **异常**：NotFoundException、InvalidParameterException、PermissionDeniedException。

### 3. delete_live_room_category(db, room_id, category_id, current_user_id, role) -> 删除确认

- **功能**：删除某直播间的单个分类关联（Admin）。
- **权限**：_check_admin_permission(role)；关联不存在 2001。
- **执行流程**：1）_check_admin_permission；2）调用 crud delete_live_room_category(db, room_id, category_id)；3）若返回 False 则 raise NotFoundException；4）返回统一成功响应。
- **异常**：NotFoundException、PermissionDeniedException。

---

## 需要新增的 API 端点

### 1. GET /{room_id}/categories（公开）

- **路由**：挂载于 prefix="/rooms"，故完整路径为 GET /api/v1/rooms/{room_id}/categories。
- **依赖**：get_db, get_current_user_optional。
- **响应**：LiveRoomCategoriesListResponse；房间不存在 2001。
- **实现**：调用 service.get_live_room_categories_list(db, room_id, current_user_id, role)。

### 2. POST /{room_id}/categories（Admin）

- **路由**：挂载于 prefix="/admin/rooms"，故完整路径为 POST /api/v1/admin/rooms/{room_id}/categories。
- **依赖**：get_db, get_current_user。
- **请求体**：LiveRoomCategoriesSetRequest。
- **响应**：LiveRoomCategoriesSetResponse；2001/4001/3003。
- **实现**：调用 service.set_live_room_categories(db, room_id, body, current_user_id, role)。

### 3. DELETE /{room_id}/categories/{category_id}（Admin）

- **路由**：挂载于 prefix="/admin/rooms"，故完整路径为 DELETE /api/v1/admin/rooms/{room_id}/categories/{category_id}。
- **依赖**：get_db, get_current_user。
- **响应**：200 + 删除确认；2001/3003。
- **实现**：调用 service.delete_live_room_category(db, room_id, category_id, current_user_id, role)。

---

## 路由注册说明

- 在 app/api/v1/endpoints/content_management.py 中新增两个 APIRouter：live_room_categories_router（GET）、live_room_categories_admin_router（POST、DELETE）。
- 在 app/api/v1/api.py 中：include_router(content_management.live_room_categories_router, prefix="/rooms")；include_router(content_management.live_room_categories_admin_router, prefix="/admin/rooms")。

---

## 质量标准

与既有内容管理 Service/API 一致：权限在 Service 层、双轨鉴权、响应 success_response/error_response、日志脱敏、不改变未列出的方法或端点。

**文档结束**
