# 用户偏好与通知模块代码生成提示词 - 第二阶段（Service层和API层）

## 1. 角色定义 (Role Definition)

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构。

## 2. 任务目标 (Task Objective)

你的任务是为**用户偏好与通知模块（User Preferences、Notifications）**生成第二阶段的代码，包括：

1. **自定义异常** (在 `app/exceptions.py` 中补充)
2. **业务逻辑层 (Service Layer)** (创建 `app/services/user_preferences_notification_service.py`)
3. **API端点层 (Endpoint Layer)** (创建 `app/api/v1/endpoints/user_preferences_notification.py`)

**模块范围**:
- **User Preferences模块**: 2个API（获取用户偏好设置、更新用户偏好设置）
- **Notifications模块**: 9个API（获取通知列表用户、获取未读通知数量、标记通知为已读、标记所有通知为已读、创建通知Admin、获取通知列表Admin、更新通知Admin、删除通知Admin、批量删除通知Admin）

## 3. 核心架构约束 (学院派关键规则)

你**必须**严格执行"学院派"架构分层：

  * **`Service` 层 (本提示词生成)**:
      * **负责**：业务逻辑（权限检查、资源验证、默认值处理、批量操作编排）。
      * **严禁**：处理事务（`db.commit/rollback`）。
      * **严禁**：抛出 `HTTPException` 或返回 `JSONResponse`。
      * **[关键] 权限模式**：**必须**遵循 `5.0` 规范，接收 `user_id: UUID` 和 `user_role: Optional[UserPreferencesNotificationUserRole]`，失败则 `raise PermissionDeniedException("权限不足...")`。
      * **[关键] 用户身份验证**：所有用户操作必须验证资源属于当前用户（如标记通知为已读时验证 `notification.user_id == user_id`）。

  * **`Endpoint` (API) 层 (本提示词生成)**:
      * **负责**：参数绑定、`Depends` 注入、调用 Service。
      * **[关键] 权限模式**：**必须**遵循 `5.0` 规范，依赖 `Depends(get_current_user)` 获取 `Dict`，**并在 API 层解析**。
      * **[关键] 异常处理**：**必须**使用 `try/except` 块捕获所有自定义异常，并将其转换为 `JSONResponse(status_code=..., content=error_response(code=...))`。
      * **[关键] 路由定义**：**必须**在 `endpoints/user_preferences_notification.py` 中定义 `APIRouter(tags=["用户偏好与通知"])` (不含 `prefix`)。`prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。

## 4. 核心上下文信息 (Dependencies)

  * `app/crud/user_preferences_notification.py`：已存在 `crud_preference`, `crud_notification` 对象。
  * `app/core/deps.py`：已存在 `get_current_user(token:...) -> Dict`。返回类型为 `Dict` (JWT Payload)。
  * `app/core/responses.py`：已存在 `success_response(data)` 和 `error_response(code, message, data)`。

## 5. 自定义异常定义

在 `app/exceptions.py` 文件中添加以下自定义异常：

```python
# --- 用户偏好与通知模块异常 (Service 层抛出) ---

class UserPreferenceNotFoundException(Exception):
    """用户偏好不存在"""
    pass

class NotificationNotFoundException(Exception):
    """通知不存在"""
    pass

class PermissionDeniedException(Exception):
    """权限不足（资源不属于当前用户）"""
    pass

class InvalidUserIdsException(Exception):
    """无效的用户ID列表"""
    def __init__(self, message: str, invalid_ids: List[UUID]):
        self.message = message
        self.invalid_ids = invalid_ids
        super().__init__(self.message)
```

## 6. Service层实现规范

### 6.1 User Preferences Service方法

#### `get_preferences(
    self,
    db: AsyncSession,
    user_id: UUID
) -> UserPreference`

**业务逻辑**:
1. **查询偏好**: 调用 `crud_preference.get_preference_by_user_id(db, user_id)`
2. **默认值处理**: 如果不存在（首次访问），返回默认偏好设置（创建默认 `UserPreference` 对象）
3. 返回用户偏好对象

**默认偏好设置**:
```python
default_preference = UserPreference(
    id=uuid.uuid4(),
    user_id=user_id,
    theme_mode="auto",
    homepage_view_mode="double",
    cellular_warning_enabled=True,
    auto_reduce_quality=True,
    auto_play_on_wifi=False
)
```

#### `update_preferences(
    self,
    db: AsyncSession,
    user_id: UUID,
    preference_update: UserPreferencesUpdate
) -> UserPreference`

**业务逻辑**:
1. **upsert操作**: 调用 `crud_preference.upsert_preference(db, user_id, preference_update)`
2. 返回更新后的用户偏好对象

### 6.2 Notifications Service方法

#### `get_notifications(
    self,
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 10,
    is_read: Optional[bool] = None,
    sort: str = "created_at:desc"
) -> Tuple[List[Notification], int]`

**业务逻辑**:
1. 计算 `skip = (page - 1) * size`
2. 调用 `crud_notification.get_notifications_by_user_id_paginated(db, user_id, skip, size, is_read, sort)`
3. 返回通知列表和总数

#### `get_unread_count(
    self,
    db: AsyncSession,
    user_id: UUID
) -> int`

**业务逻辑**:
1. 调用 `crud_notification.get_unread_count_by_user_id(db, user_id)`
2. 返回未读数量

#### `mark_notification_as_read(
    self,
    db: AsyncSession,
    user_id: UUID,
    notification_id: UUID
) -> None`

**业务逻辑**:
1. **查询通知**: 调用 `crud_notification.get_notification_by_id(db, notification_id)`
2. **存在性检查**: 如果不存在，抛出 `NotificationNotFoundException`
3. **用户身份验证**: 验证 `notification.user_id == user_id`，如果不匹配抛出 `PermissionDeniedException`
4. **幂等性检查**: 如果 `notification.is_read == True`，直接返回（幂等性）
5. **标记已读**: 调用 `crud_notification.mark_notification_as_read(db, notification)`

#### `mark_all_notifications_as_read(
    self,
    db: AsyncSession,
    user_id: UUID
) -> int`

**业务逻辑**:
1. 调用 `crud_notification.mark_all_notifications_as_read(db, user_id)`
2. 返回更新的记录数

#### `create_notifications(
    self,
    db: AsyncSession,
    notification_in: NotificationCreateRequest,
    user_id: UUID,
    user_role: UserPreferencesNotificationUserRole
) -> Tuple[int, List[UUID]]`

**业务逻辑**:
1. **权限检查**: 检查 `user_role` 是否为 `ADMIN` 或 `SUPERADMIN`，否则抛出 `PermissionDeniedException`
2. **用户ID处理**:
   - 如果 `notification_in.user_ids` 为空数组，查询所有用户ID（调用User Service或查询users表）
   - 如果 `notification_in.user_ids` 不为空，验证所有用户ID是否存在
3. **批量验证**: 如果部分用户ID不存在，抛出 `InvalidUserIdsException`（包含无效ID列表）
4. **批量创建**: 为每个用户创建一条通知记录，调用 `crud_notification.batch_create_notifications(db, notifications_data)`
5. 返回 `(创建数量, 用户ID列表)`

#### `get_notifications_paginated(
    self,
    db: AsyncSession,
    user_id: Optional[UUID],
    user_role: UserPreferencesNotificationUserRole,
    page: int = 1,
    size: int = 10,
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    sort: str = "created_at:desc"
) -> Tuple[List[Notification], int]`

**业务逻辑**:
1. **权限检查**: 检查管理员权限
2. 计算 `skip = (page - 1) * size`
3. 调用 `crud_notification.get_notifications_paginated(db, skip, limit, user_id, notification_type, is_read, sort)`
4. 返回通知列表和总数

#### `update_notification(
    self,
    db: AsyncSession,
    notification_id: UUID,
    notification_update: Dict,
    user_id: UUID,
    user_role: UserPreferencesNotificationUserRole
) -> Notification`

**业务逻辑**:
1. **权限检查**: 检查管理员权限
2. **查询通知**: 调用 `crud_notification.get_notification_by_id(db, notification_id)`
3. **存在性检查**: 如果不存在，抛出 `NotificationNotFoundException`
4. **字段限制**: 只允许更新 `title` 和 `content`（在Service层验证）
5. 调用 `crud_notification.update_notification(db, notification, notification_update)`
6. 返回更新后的通知对象

#### `delete_notification(
    self,
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID,
    user_role: UserPreferencesNotificationUserRole
) -> None`

**业务逻辑**:
1. **权限检查**: 检查管理员权限
2. **查询通知**: 调用 `crud_notification.get_notification_by_id(db, notification_id)`
3. **存在性检查**: 如果不存在，抛出 `NotificationNotFoundException`
4. **硬删除**: 调用 `crud_notification.delete_notification(db, notification)`

#### `batch_delete_notifications(
    self,
    db: AsyncSession,
    delete_request: NotificationBatchDeleteRequest,
    user_id: UUID,
    user_role: UserPreferencesNotificationUserRole
) -> int`

**业务逻辑**:
1. **权限检查**: 检查管理员权限
2. **参数验证**: 验证至少提供 `notification_ids` 或 `delete_before` 之一（已在Schema层验证）
3. **批量删除**: 调用 `crud_notification.batch_delete_notifications(db, notification_ids, delete_before, notification_type, is_read)`
4. 返回删除的记录数

## 7. API层实现规范

### 7.1 User Preferences API端点

#### `GET /api/v1/users/me/preferences`

**路由定义**: `@router.get("/users/me/preferences")`

**认证**: 强制认证（`Depends(get_current_user)`）

**实现要点**:
1. 解析JWT Token，提取 `user_id`（在 `try` 块之前）
2. 调用 `service.get_preferences(db, user_id)`
3. 返回用户偏好信息（如果不存在，返回默认偏好）

#### `PATCH /api/v1/users/me/preferences`

**路由定义**: `@router.patch("/users/me/preferences")`

**认证**: 强制认证

**请求体**: `UserPreferencesUpdate`

**实现要点**:
1. 解析JWT Token和请求体
2. 调用 `service.update_preferences(db, user_id, preference_update)`
3. 捕获 `ValidationError` → 返回 `4001` 错误
4. 返回更新后的用户偏好信息

### 7.2 Notifications API端点

#### `GET /api/v1/users/me/notifications`

**路由定义**: `@router.get("/users/me/notifications")`

**认证**: 强制认证

**请求参数**: `page`, `size`, `is_read`, `sort`

**实现要点**:
1. 解析JWT Token和查询参数
2. 调用 `service.get_notifications(db, user_id, page, size, is_read, sort)`
3. 构建分页响应并返回

#### `GET /api/v1/users/me/notifications/unread-count`

**路由定义**: `@router.get("/users/me/notifications/unread-count")`

**认证**: 强制认证

**实现要点**:
1. 解析JWT Token
2. 调用 `service.get_unread_count(db, user_id)`
3. 返回未读数量

#### `POST /api/v1/users/me/notifications/{notification_id}/read`

**路由定义**: `@router.post("/users/me/notifications/{notification_id}/read")`

**认证**: 强制认证

**实现要点**:
1. 解析JWT Token和路径参数 `notification_id`
2. 调用 `service.mark_notification_as_read(db, user_id, notification_id)`
3. 捕获 `NotificationNotFoundException` → 返回 `2001` 错误
4. 捕获 `PermissionDeniedException` → 返回 `3002` 错误

#### `POST /api/v1/users/me/notifications/read-all`

**路由定义**: `@router.post("/users/me/notifications/read-all")`

**认证**: 强制认证

**实现要点**:
1. 解析JWT Token
2. 调用 `service.mark_all_notifications_as_read(db, user_id)`
3. 返回更新数量

#### `POST /api/v1/admin/notifications`

**路由定义**: `@router.post("/admin/notifications")`

**认证**: 强制认证（管理员）

**请求体**: `NotificationCreateRequest`

**实现要点**:
1. 解析JWT Token和请求体
2. 调用 `service.create_notifications(...)`
3. 捕获 `InvalidUserIdsException` → 返回 `4001` 错误（包含无效ID列表）
4. 捕获 `PermissionDeniedException` → 返回 `3002` 错误
5. 返回批量创建结果（创建数量、用户ID列表）

#### `GET /api/v1/admin/notifications`

**路由定义**: `@router.get("/admin/notifications")`

**认证**: 强制认证（管理员）

**请求参数**: `page`, `size`, `user_id`, `notification_type`, `is_read`, `sort`

**实现要点**:
1. 解析JWT Token和查询参数
2. 调用 `service.get_notifications_paginated(...)`
3. 构建分页响应并返回

#### `PATCH /api/v1/admin/notifications/{notification_id}`

**路由定义**: `@router.patch("/admin/notifications/{notification_id}")`

**认证**: 强制认证（管理员）

**请求体**: `NotificationUpdateRequest`

**实现要点**:
1. 解析JWT Token、路径参数和请求体
2. 调用 `service.update_notification(...)`
3. 捕获 `NotificationNotFoundException` → 返回 `2001` 错误
4. 捕获 `PermissionDeniedException` → 返回 `3002` 错误

#### `DELETE /api/v1/admin/notifications/{notification_id}`

**路由定义**: `@router.delete("/admin/notifications/{notification_id}")`

**认证**: 强制认证（管理员）

**实现要点**:
1. 解析JWT Token和路径参数
2. 调用 `service.delete_notification(...)`
3. 捕获 `NotificationNotFoundException` → 返回 `2001` 错误
4. 捕获 `PermissionDeniedException` → 返回 `3002` 错误

#### `POST /api/v1/admin/notifications/batch-delete`

**路由定义**: `@router.post("/admin/notifications/batch-delete")`

**认证**: 强制认证（管理员）

**请求体**: `NotificationBatchDeleteRequest`

**实现要点**:
1. 解析JWT Token和请求体
2. 调用 `service.batch_delete_notifications(...)`
3. 捕获 `ValidationError` → 返回 `4001` 错误（必须提供 `notification_ids` 或 `delete_before`）
4. 捕获 `PermissionDeniedException` → 返回 `3002` 错误
5. 返回删除数量

## 8. 错误码映射

- `UserPreferenceNotFoundException` → `2001` 资源不存在（但在获取偏好时返回默认值，不抛出此异常）
- `NotificationNotFoundException` → `2001` 资源不存在
- `PermissionDeniedException` → `3002` 权限不足
- `InvalidUserIdsException` → `4001` 参数校验失败
- `ValidationException` → `4001` 参数校验失败

## 9. 关键注意事项

### 9.1 默认值处理

- **用户偏好**: 首次访问时自动返回默认偏好设置，不创建记录（在获取时返回默认值，在更新时创建记录）
- **更新时创建**: 如果用户偏好不存在，更新操作会自动创建记录（upsert）

### 9.2 批量操作

- **批量创建通知**: 支持指定用户ID列表或发送给所有用户（`user_ids` 为空数组）
- **批量删除通知**: 支持按ID列表删除或按条件删除（`delete_before`）
- **批量操作优化**: 使用 `bulk_insert_mappings()` 提升性能

### 9.3 用户身份验证

- 所有用户操作必须验证资源属于当前用户
- 如果 `resource.user_id != user_id`，抛出 `PermissionDeniedException`

### 9.4 JSONB字段处理

- `pinned_categories`: 存储为JSONB数组，最多5个
- `extra`: 存储为JSONB对象，可扩展
- 数据库自动处理JSONB的序列化和反序列化

### 9.5 幂等性设计

- 标记通知为已读：如果已为已读，直接返回成功（幂等性）
- 避免重复操作导致的错误

### 9.6 字段限制

- 更新通知时，只允许更新 `title` 和 `content`
- 不允许更新 `user_id`、`notification_type`、`related_id`、`related_type`、`is_read` 等字段

## 10. 完整代码模板

### 10.1 Service层示例

```python
"""
用户偏好与通知模块的 Service 层 (学院派)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict
from uuid import UUID
import logging
import uuid

from app.crud import user_preferences_notification as crud_user_preferences_notification
from app.schemas.user_preferences_notification import (
    UserPreferencesUpdate, NotificationCreateRequest, NotificationBatchDeleteRequest
)
from app.models.user_preferences_notification import UserPreference, Notification
from app.exceptions import (
    NotificationNotFoundException, PermissionDeniedException,
    InvalidUserIdsException
)

logger = logging.getLogger(__name__)

class UserPreferencesNotificationService:
    """用户偏好与通知Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud_preference = crud_user_preferences_notification.crud_preference
        self.crud_notification = crud_user_preferences_notification.crud_notification
    
    async def get_preferences(
        self,
        user_id: UUID
    ) -> UserPreference:
        """
        获取用户偏好设置（如果不存在返回默认值）
        
        Args:
            user_id: 用户公开ID
        
        Returns:
            用户偏好对象（如果不存在返回默认偏好）
        """
        # 查询用户偏好
        preference = await self.crud_preference.get_preference_by_user_id(
            self.db, user_id
        )
        
        # 如果不存在，返回默认偏好设置（不创建记录）
        if preference is None:
            default_preference = UserPreference(
                id=uuid.uuid4(),
                user_id=user_id,
                theme_mode="auto",
                homepage_view_mode="double",
                cellular_warning_enabled=True,
                auto_reduce_quality=True,
                auto_play_on_wifi=False,
                pinned_categories=None,
                extra=None
            )
            logger.debug(f"返回默认用户偏好: user_id={user_id}")
            return default_preference
        
        return preference
    
    async def update_preferences(
        self,
        user_id: UUID,
        preference_update: UserPreferencesUpdate
    ) -> UserPreference:
        """
        更新用户偏好设置（upsert）
        
        Args:
            user_id: 用户公开ID
            preference_update: 偏好更新数据
        
        Returns:
            更新后的用户偏好对象
        """
        # Upsert操作：如果不存在则创建，存在则更新
        preference = await self.crud_preference.upsert_preference(
            self.db, user_id, preference_update
        )
        
        logger.info(f"用户偏好更新成功: user_id={user_id}, preference_id={preference.id}")
        return preference
```

### 10.2 API层示例

```python
"""
用户偏好与通知模块的 API 端点层 (学院派)
"""
from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict
from uuid import UUID
import logging

from app.core.deps import get_db, get_current_user
from app.core.responses import success_response, error_response
from app.services.user_preferences_notification_service import UserPreferencesNotificationService
from app.schemas.user_preferences_notification import (
    UserPreferencesUpdate, UserPreferencesItem,
    NotificationItem, NotificationCreateRequest
)
from app.exceptions import (
    NotificationNotFoundException, PermissionDeniedException,
    InvalidUserIdsException
)
from pydantic import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["用户偏好与通知"])

@router.get("/users/me/preferences")
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    获取用户偏好设置（首次访问返回默认值）
    """
    # 解析用户身份（在try块之前）
    try:
        user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    except (ValueError, TypeError) as e:
        logger.warning(f"JWT解析失败: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3001, message="未认证")
        )
    
    try:
        service = UserPreferencesNotificationService(db)
        preference = await service.get_preferences(user_id=user_id)
        
        # 序列化为UserPreferencesItem
        preference_item = UserPreferencesItem.model_validate(preference)
        
        return success_response(data=preference_item)
        
    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统错误")
        )
```

## 11. 路由注册

在 `app/api/v1/api.py` 文件中注册路由：

```python
from app.api.v1.endpoints import user_preferences_notification

api_router.include_router(
    user_preferences_notification.router,
    prefix="/api/v1",
    tags=["用户偏好与通知"]
)
```

**注意**：`prefix` 在 `include_router` 中指定，不在 `APIRouter` 定义时指定。

## 12. 文件结构

生成的文件应为：

```
app/
  services/
    user_preferences_notification_service.py  # Service层
  api/
    v1/
      endpoints/
        user_preferences_notification.py  # API端点层
  exceptions.py  # 补充自定义异常（如果文件已存在，则添加异常定义）
```

## 13. 完整API清单

**User Preferences模块（2个）**:
1. `GET /api/v1/users/me/preferences` - 获取用户偏好设置（首次访问返回默认值）
2. `PATCH /api/v1/users/me/preferences` - 更新用户偏好设置（upsert）

**Notifications模块（9个）**:
3. `GET /api/v1/users/me/notifications` - 获取通知列表（用户）
4. `GET /api/v1/users/me/notifications/unread-count` - 获取未读通知数量
5. `POST /api/v1/users/me/notifications/{notification_id}/read` - 标记通知为已读
6. `POST /api/v1/users/me/notifications/read-all` - 标记所有通知为已读
7. `POST /api/v1/admin/notifications` - 创建通知（Admin，支持批量创建）
8. `GET /api/v1/admin/notifications` - 获取通知列表（Admin，分页）
9. `PATCH /api/v1/admin/notifications/{notification_id}` - 更新通知（Admin）
10. `DELETE /api/v1/admin/notifications/{notification_id}` - 删除通知（Admin）
11. `POST /api/v1/admin/notifications/batch-delete` - 批量删除通知（Admin）

## 14. 测试建议

### 14.1 单元测试

- 测试Service层的业务逻辑（默认值处理、upsert操作、批量操作、用户身份验证等）
- 测试CRUD层的数据访问逻辑

### 14.2 集成测试

- 测试所有11个API端点的完整流程
- 测试权限控制（用户接口、Admin接口）
- 测试默认值处理（首次访问返回默认偏好）
- 测试upsert操作（更新时自动创建）
- 测试批量操作（批量创建通知、批量删除通知）
- 测试用户身份验证（用户只能访问自己的偏好和通知）
- 测试幂等性（标记已读操作）

