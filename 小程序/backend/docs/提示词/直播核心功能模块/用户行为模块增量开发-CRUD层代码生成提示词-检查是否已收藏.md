# 用户行为模块增量开发 - CRUD 层代码生成提示词（检查是否已收藏）

**模块名称**: user_behavior  
**功能模块名称**: 用户行为模块  
**增量主题**: 检查当前用户是否已收藏指定直播间（GET /api/v1/rooms/{room_id}/is-favorited）  
**目标文件**: `backend/live_core_service/app/crud/user_behavior.py`  

**定位**：与既有《用户行为模块设计文档-收藏-观看历史-订阅提醒---CRUD层代码生成提示词.md》配套使用；按本增量提示词**仅约定**下列内容，无需新增或修改 CRUD 函数。

---

## 1. 角色定义

在既有用户行为模块 CRUD 提示词基础上，按本增量提示词**约定**「检查是否已收藏」所用数据访问方式。不新增 CRUD 函数，不修改已有函数签名与行为。

---

## 2. Model 字段变更摘要

无。仍使用 `UserFavorite` 表与既有字段（`user_id`, `room_id`, `is_active` 等）。

---

## 3. 需要约定的 CRUD 使用方式（无代码变更）

**检查是否已收藏**（对应 API GET /api/v1/rooms/{room_id}/is-favorited）：

- **不新增** CRUD 函数。
- **复用** 已有 `get_favorite(db, user_id, room_id) -> Optional[UserFavorite]`（见 `app/crud/user_behavior.py`）。
- Service 层根据返回值判断：`is_favorited = (favorite is not None and favorite.is_active)`。即查询语义为「user_id + room_id + is_active=true」的存在性，由现有 `get_favorite` 取回记录后在业务层根据 `is_active` 判断。

---

## 4. 质量标准

与既有 CRUD 提示词在异步、类型提示、事务（不在此层 commit/rollback）、日志脱敏、安全异步异常处理等方面要求一致。不改变未被列出的 CRUD 函数的签名与行为。
