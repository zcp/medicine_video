# 用户行为模块增量开发 - Service 层和 API 层代码生成提示词（检查是否已收藏）

**模块名称**: user_behavior  
**功能模块名称**: 用户行为模块  
**增量主题**: 检查当前用户是否已收藏指定直播间（GET /api/v1/rooms/{room_id}/is-favorited）  
**目标文件**:  
- `backend/live_core_service/app/services/user_behavior_service.py`  
- `backend/live_core_service/app/api/v1/endpoints/user_behavior.py`  
- `backend/live_core_service/app/api/v1/api.py`（挂载路由）

**定位**：与既有《用户行为模块设计文档-收藏-观看历史-订阅提醒---Service层和API层代码生成提示词.md》配套使用；按本增量提示词**仅新增**下列方法与端点。

---

## 1. 角色定义

在既有用户行为模块 Service/API 提示词基础上，按本增量提示词**新增**「检查是否已收藏」的 Service 方法与 API 端点。形态对齐专家模块 `GET /api/v1/experts/{expert_id}/is-followed`。

---

## 2. Schema 变更摘要

无需新增 Schema。响应为 `{"is_favorited": true|false}`，由 API 层直接构造或使用简单 dict。

---

## 3. 需要新增的 Service 方法

### check_is_favorited

- **签名**：`async def check_is_favorited(self, room_id: UUID, current_user_id: UUID) -> Dict[str, bool]`
- **功能**：检查当前用户是否已收藏指定直播间；若直播间不存在则抛出 `NotFoundException`。
- **鉴权**：调用方（API）已做 Strict Auth，本方法仅做业务校验（直播间存在性）。
- **执行流程**：
  1. 调用 room CRUD 校验直播间存在：`crud_room.get(self.db, room_id)`（或等价方法）；若为 `None` 则 `raise NotFoundException("直播间不存在")`。
  2. 调用 `crud_user_behavior.get_favorite(self.db, current_user_id, room_id)`。
  3. `is_favorited = (favorite is not None and favorite.is_active)`。
  4. 记录 DEBUG 日志：user_id、room_id 前 8 位脱敏，is_favorited 值（遵循主文档 1.4.3）。
  5. 返回 `{"is_favorited": is_favorited}`。
- **异常**：`NotFoundException`（直播间不存在），由 API 层转换为 404、code 2001。

---

## 4. 需要新增的 API 端点

### GET /api/v1/rooms/{room_id}/is-favorited

- **路径**：`GET /{room_id}/is-favorited`，挂载于 **prefix `/rooms`**，故完整路径为 `/api/v1/rooms/{room_id}/is-favorited`。
- **认证**：Strict Auth，`Depends(get_current_user)`。
- **路径参数**：`room_id: UUID`（无效 UUID 时由 FastAPI 返回 422，或显式捕获返回 400/4001）。
- **成功响应**：`200 OK`，`success_response(data={"is_favorited": True|False})`。
- **错误**：
  - 直播间不存在：捕获 `NotFoundException`，返回 404，`error_response(code=2001, message="资源不存在")`，日志 WARNING。
  - 未认证：由依赖返回 401。
  - 其他异常：500，code 1002，日志 ERROR。
- **实现位置**：在 `user_behavior.py` 中新增独立 router（如 `room_favorite_router`），在该 router 上注册本端点；在 `api.py` 中 `include_router(room_favorite_router, prefix="/rooms", tags=["用户行为"])`，确保路径为 `/api/v1/rooms/{room_id}/is-favorited`。

---

## 5. 质量标准

与既有 Service/API 提示词在「权限在 Service 层、Strict Auth、响应标准化（success_response/error_response）、日志脱敏、安全异步异常处理」等方面要求一致。不改变未被列出的方法或端点的签名与行为。
