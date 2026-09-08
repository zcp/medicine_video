# 用户偏好与通知模块 - 权限管理增量改造 Service 与 API 层代码生成提示词

**版本**: V1.0
**创建日期**: 2026-01-12
**目标**: 指导 AI 对用户偏好与通知模块的 Service 和 API 层进行权限管理增量改造

---

## 1. 任务概述

**目标模块**: 用户偏好与通知模块（User Preferences & Notifications Module）

**需要更新的代码文件**:
- `app/services/user_preferences_notifications_service.py`
- `app/api/v1/endpoints/user_preferences_notifications.py`

**目标**: 将现有的用户偏好与通知模块 Service 和 API 层代码更新，使其符合通用权限管理策略（母版 Section 5.0.5）

---

## 2. 核心权限管理策略

### 2.1. 三层权限职责分工

**API 层 (Endpoint)**：负责 Authentication（认证）
- 使用 `get_current_user` 或 `get_current_user_optional` 获取用户信息
- 从 JWT Payload 中提取 `user_id` (UUID) 和 `role` (str)
- 将用户身份传递给 Service 层
- **不做权限判断**，不直接拒绝请求

**Service 层**：全权负责 Authorization（鉴权）
- 接收 `user_id: UUID` 和 `user_role: str` 参数
- 调用权限守卫函数（如 `_check_user_preferences_ownership`、`_check_write_permission`）
- 根据权限检查结果决定是否允许访问
- 对于需要权限过滤的列表查询，将 `current_user_id` 和 `role` 传递给 CRUD 层

**CRUD 层**：负责在 SQL 层面应用权限过滤
- 接收 `current_user_id: Optional[UUID]` 和 `role: Optional[str]` 参数
- 在 WHERE 条件中应用权限过滤逻辑
- Admin 查询：无过滤
- Regular User 查询：`WHERE user_id=current_user_id`
- Anonymous 查询：`WHERE FALSE`（无权限）
- 业务筛选与权限过滤：AND 关系

### 2.2. 双轨鉴权模式

| 模式 | 行为 | 适用场景 | API 层依赖 |
|-------|------|---------|-------------|
| **Strict Auth**（强制鉴权） | 无 Token → 401<br>Token 无效 → 401 | 所有写操作（创建、修改、删除） | `get_current_user` |
| **Optional Auth**（可选鉴权） | 无 Token → None<br>Token 无效 → 401 | 所有读操作（列表、详情） | `get_current_user_optional` |

**关键原则**：
1. **严禁降级为匿名**：Token 无效时必须报 401，不能返回 `None` 降级为匿名用户。否则已登录用户在 Token 过期时会莫名其妙看不到自己的私有资源，导致前端状态错乱。
2. **职责清晰**：API 层只负责解析"你是谁"（User vs Anonymous），Service 层负责判定"你能看吗/你能改吗"。

### 2.3. 权限守卫函数（Service 层专用）

**类型 1：资源可见性检查**

```python
def _check_user_preferences_ownership(
    self,
    user_preferences: UserPreferences,
    user_id: UUID,
    user_role: str
) -> None:
    """
    用户偏好所有权校验
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 上帝视角通过
        2. Owner（user_preferences.user_id == user_id）→ 通过
        3. 其他情况 → 403（权限不足）
    
    Raises:
        PermissionDeniedException(403): 权限不足
    """
    # 管理员：上帝视角通过
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源创建者：通过
    if user_preferences.user_id == user_id:
        return
    
    # 其他用户：拒绝
    raise PermissionDeniedException(
        "您没有权限访问其他用户的偏好设置"
    )
```

**类型 2：写权限检查**

```python
def _check_write_permission(
    self,
    resource: Any,
    user_id: UUID,
    user_role: str
) -> None:
    """
    通用的写操作权限校验（修改、删除）
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过
        2. Owner（resource.user_id == user_id）→ 通过
        3. 其他情况 → 403（已登录但无权）
    
    Raises:
        PermissionDeniedException(403): 权限不足
    """
    # 管理员：上帝视角通过
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源创建者：通过
    if resource.user_id == user_id:
        return
    
    # 其他用户：拒绝
    raise PermissionDeniedException(
        "You don't have permission to modify this resource"
    )
```

**类型 3：管理员权限检查**

```python
def _check_admin_permission(
    self,
    user_role: str
) -> None:
    """
    管理员权限校验（用于批量操作）
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过
        2. 其他情况 → 403（权限不足）
    
    Raises:
        PermissionDeniedException(403): 权限不足
    """
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException(
            "需要管理员权限"
        )
```

---

## 3. 更新前检查清单

### 3.1. 文档结构检查

- [ ] 确认目标文件路径正确
- [ ] 确认模块名称正确（用户偏好与通知模块）
- [ ] 确认需要更新的代码文件（Service 和 API 层）

### 3.2. 现有代码分析

- [ ] 读取 `app/services/user_preferences_notifications_service.py` 现有代码
- [ ] 读取 `app/api/v1/endpoints/user_preferences_notifications.py` 现有代码
- [ ] 识别所有需要权限改造的 Service 方法
- [ ] 识别所有需要权限改造的 API 端点
- [ ] 检查现有的权限实现方式

### 3.3. 改造范围确认

- [ ] 确认 Service 方法数量（10个）
- [ ] 确认 API 端点数量（10个）
- [ ] 确认需要添加的权限参数（user_id, user_role）
- [ ] 确认需要实现的权限守卫函数

---

## 4. Service 层改造指南

### 4.1. 需要改造的 Service 方法清单

**所有需要改造的 Service 方法**：

1. **用户偏好管理**（2个方法）：
   - `get_user_preferences` - 获取用户偏好
   - `update_user_preferences` - 更新用户偏好

2. **通知管理**（8个方法）：
   - `create_notifications` - 创建通知（单个）
   - `create_bulk_notifications` - 批量创建通知
   - `get_notifications_paginated` - 获取通知列表（分页）
   - `get_notifications` - 获取通知列表（列表）
   - `get_notification` - 获取通知详情
   - `mark_notification_as_read` - 标记通知为已读
   - `batch_mark_notifications_as_read` - 批量标记通知为已读
   - `get_unread_count` - 获取未读通知数量

3. **通知删除**（3个方法）：
   - `delete_notification` - 删除通知
   - `batch_delete_notifications` - 批量删除通知

**总计**: 10个 Service 方法

### 4.2. Service 方法改造规范

#### 4.2.1. 方法签名更新

**所有需要权限检查的 Service 方法，都必须更新方法签名**：

```python
# 改造前（旧签名）
async def get_user_preferences(
    self,
    user_id: uuid.UUID,
    db: AsyncSession
) -> UserPreferencesItem:
    """获取用户偏好"""
    ...

# 改造后（新签名）
async def get_user_preferences(
    self,
    current_user_id: uuid.UUID,  # ← 当前用户的 user_id
    user_role: str,  # ← 当前用户的角色
    db: AsyncSession
) -> UserPreferencesItem:
    """获取用户偏好（带权限检查）"""
    ...
```

**改造规则**：
1. **用户偏好方法**：
   - `get_user_preferences`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `update_user_preferences`: 添加 `current_user_id` 和 `user_role` 参数（必选）

2. **通知管理方法**：
   - `create_notifications`: 添加 `current_user_id` 和 `user_role` 参数（必选，仅管理员）
   - `create_bulk_notifications`: 添加 `current_user_id` 和 `user_role` 参数（必选，仅管理员）
   - `get_notifications_paginated`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `get_notifications`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `get_notification`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `mark_notification_as_read`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `batch_mark_notifications_as_read`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `get_unread_count`: 添加 `current_user_id` 和 `user_role` 参数（必选）

3. **通知删除方法**：
   - `delete_notification`: 添加 `current_user_id` 和 `user_role` 参数（必选）
   - `batch_delete_notifications`: 添加 `current_user_id` 和 `user_role` 参数（必选）

#### 4.2.2. 权限守卫函数实现

**在 UserPreferencesNotificationsService 类中实现以下权限守卫函数**：

```python
class UserPreferencesNotificationsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _check_user_preferences_ownership(
        self,
        user_preferences: UserPreferences,
        current_user_id: UUID,
        user_role: str
    ) -> None:
        """
        用户偏好所有权校验
        """
        # 管理员：上帝视角通过
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        if user_preferences.user_id == current_user_id:
            return
        
        # 其他用户：拒绝
        raise PermissionDeniedException(
            "您没有权限访问其他用户的偏好设置"
        )
    
    def _check_write_permission(
        self,
        resource: Any,
        current_user_id: UUID,
        user_role: str
    ) -> None:
        """
        通用的写操作权限校验
        """
        # 管理员：上帝视角通过
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        if resource.user_id == current_user_id:
            return
        
        # 其他用户：拒绝
        raise PermissionDeniedException(
            "You don't have permission to modify this resource"
        )
    
    def _check_admin_permission(
        self,
        user_role: str
    ) -> None:
        """
        管理员权限校验（用于批量操作）
        """
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException(
                "需要管理员权限"
            )
```

#### 4.2.3. 方法内部权限检查实现

**用户偏好方法的权限检查示例**：

```python
async def get_user_preferences(
    self,
    current_user_id: uuid.UUID,
    user_role: str,
    db: AsyncSession
) -> UserPreferencesItem:
    """获取用户偏好（仅当前用户或管理员）"""
    
    # 调用 CRUD 获取用户偏好
    user_preferences = await crud_user_preferences.get_by_user_id(
        db=db,
        user_id=current_user_id
    )
    
    # 检查用户偏好是否存在
    if not user_preferences:
        raise UserPreferenceNotFoundException("User preferences not found")
    
    # 调用权限守卫函数（管理员可查看所有用户偏好）
    self._check_user_preferences_ownership(
        user_preferences=user_preferences,
        current_user_id=current_user_id,
        user_role=user_role
    )
    
    # 返回结果
    return user_preferences
```

**通知创建方法的权限检查示例**：

```python
async def create_bulk_notifications(
    self,
    current_user_id: uuid.UUID,
    user_role: str,
    notifications_data: List[NotificationCreate],
    db: AsyncSession
) -> List[NotificationItem]:
    """批量创建通知（仅管理员）"""
    
    # 权限检查：仅管理员可批量创建通知
    self._check_admin_permission(user_role=user_role)
    
    # 调用 CRUD 批量创建通知
    notifications = await crud_notification.create_bulk(
        db=db,
        objects_in=notifications_data
    )
    
    # 返回结果
    return notifications
```

**通知列表查询方法的权限检查示例**：

```python
async def get_notifications_paginated(
    self,
    current_user_id: uuid.UUID,
    user_role: str,
    page: int,
    size: int,
    is_read: Optional[bool] = None,
    db: AsyncSession
) -> Tuple[List[NotificationItem], int]:
    """获取通知列表（分页）"""
    
    # 调用 CRUD 获取通知列表（带权限过滤）
    notifications, total = await crud_notification.get_notifications_paginated(
        db=db,
        current_user_id=current_user_id,
        role=user_role,
        page=page,
        size=size,
        is_read=is_read
    )
    
    # 返回结果
    return notifications, total
```

---

## 5. API 层改造指南

### 5.1. 需要改造的 API 端点清单

**所有需要改造的 API 端点**：

1. **用户偏好管理**（2个端点）：
   - `GET /api/v1/user-preferences` - 获取用户偏好
   - `PUT /api/v1/user-preferences` - 更新用户偏好

2. **通知管理**（8个端点）：
   - `POST /api/v1/notifications` - 创建通知
   - `POST /api/v1/notifications/bulk` - 批量创建通知
   - `GET /api/v1/notifications` - 获取通知列表（分页）
   - `GET /api/v1/notifications/{notification_id}` - 获取通知详情
   - `POST /api/v1/notifications/{notification_id}/mark-read` - 标记通知为已读
   - `POST /api/v1/notifications/bulk/mark-read` - 批量标记通知为已读
   - `GET /api/v1/notifications/unread-count` - 获取未读通知数量

3. **通知删除**（2个端点）：
   - `DELETE /api/v1/notifications/{notification_id}` - 删除通知
   - `DELETE /api/v1/notifications/bulk` - 批量删除通知

**总计**: 10个 API 端点

### 5.2. API 端点改造规范

#### 5.2.1. 端点认证方式更新

**所有需要改造的 API 端点，都必须更新认证方式**：

```python
# 改造前（旧方式）
@router.post("/bulk")
async def create_bulk_notifications(
    notifications_data: List[NotificationCreate],
    current_user: User = Depends(get_current_user)  # ← 直接获取 User 模型
    db: AsyncSession = Depends(get_db)
) -> List[NotificationItem]:
    """批量创建通知（旧方式）"""
    ...

# 改造后（新方式）
@router.post("/bulk")
async def create_bulk_notifications(
    notifications_data: List[NotificationCreate],
    current_user: Dict = Depends(get_current_user),  # ← 使用 JWT Payload Dict
    db: AsyncSession = Depends(get_db)
) -> List[NotificationItem]:
    """批量创建通知（新方式 - 带权限检查）"""
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))  # ← 从 user_id 字段获取用户ID（UUID字符串）
    user_role = current_user.get("role", "REGULAR").upper()  # ← 直接使用字符串
    
    # 调用 Service 层（传递 current_user_id 和 user_role）
    notifications = await user_preferences_notifications_service.create_bulk_notifications(
        db=db,
        current_user_id=user_id,
        user_role=user_role,
        notifications_data=notifications_data
    )
    
    return success_response(data=notifications)
```

#### 5.2.2. 双轨鉴权模式应用

**Strict Auth 模式**（写操作）：

```python
# 写操作必须使用 Strict Auth
@router.post("/bulk")
async def create_bulk_notifications(
    notifications_data: List[NotificationCreate],
    current_user: Dict = Depends(get_current_user),  # ← Strict Auth
    db: AsyncSession = Depends(get_db)
) -> List[NotificationItem]:
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))
    user_role = current_user.get("role", "REGULAR").upper()
    
    # 调用 Service 层
    notifications = await user_preferences_notifications_service.create_bulk_notifications(
        db=db,
        current_user_id=user_id,
        user_role=user_role,
        notifications_data=notifications_data
    )
    
    return success_response(data=notifications)
```

**Optional Auth 模式**（读操作）：

```python
# 读操作必须使用 Optional Auth
@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← Optional Auth
    db: AsyncSession = Depends(get_db)
) -> NotificationItem:
    # 解析用户身份
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    user_role = current_user.get("role", "REGULAR").upper() if current_user else None
    
    # 调用 Service 层（传递 current_user_id 和 user_role）
    notification = await user_preferences_notifications_service.get_notification(
        db=db,
        current_user_id=user_id,
        user_role=user_role,
        notification_id=uuid.UUID(notification_id)
    )
    
    return success_response(data=notification)
```

#### 5.2.3. 异常处理更新

**所有 API 端点都必须更新异常处理**：

```python
from fastapi import HTTPException
from app.core.security import (
    UserPreferenceNotFoundException,
    NotificationNotFoundException,
    PermissionDeniedException
)
from app.utils.response import success_response, error_response

@router.post("/bulk")
async def create_bulk_notifications(
    notifications_data: List[NotificationCreate],
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationItem]:
    """批量创建通知"""
    
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))
    user_role = current_user.get("role", "REGULAR").upper()
    
    try:
        # 调用 Service 层
        notifications = await user_preferences_notifications_service.create_bulk_notifications(
            db=db,
            current_user_id=user_id,
            user_role=user_role,
            notifications_data=notifications_data
        )
        
        return success_response(data=notifications)
    
    except PermissionDeniedException as e:
        # 捕获 403 异常（权限不足）
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3003,
                message=e.message or "Permission denied"
            )
        )
    
    except Exception as e:
        # 捕获其他异常
        logger.error(f"批量创建通知失败: {type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=5000,
                message="Internal server error"
            )
        )
```

---

## 6. 改造后检查清单

### 6.1. Service 层改造后检查

**方法签名检查**：
- [ ] 所有 Service 方法都添加了 `current_user_id: uuid.UUID` 和 `user_role: str` 参数（必选）
- [ ] 参数类型定义正确（UUID 和 str）

**权限守卫函数检查**：
- [ ] `_check_user_preferences_ownership` 函数已实现
- [ ] `_check_write_permission` 函数已实现
- [ ] `_check_admin_permission` 函数已实现
- [ ] 权限守卫函数逻辑正确（管理员上帝视角、所有者通过、其他拒绝）
- [ ] 权限守卫函数调用位置正确（在调用 CRUD 之前）

**权限检查实现检查**：
- [ ] 用户偏好方法都调用了所有权检查
- [ ] 通知创建方法都调用了管理员权限检查
- [ ] 通知查询方法都传递了权限参数给 CRUD 层
- [ ] 通知删除方法都调用了写权限检查
- [ ] 权限检查失败时抛出正确的异常（403）

**CRUD 层参数传递检查**：
- [ ] 需要权限过滤的列表查询方法都传递了 `current_user_id` 和 `role` 给 CRUD 层
- [ ] 参数名称和类型与 CRUD 层定义一致

### 6.2. API 层改造后检查

**认证方式检查**：
- [ ] 所有端点都使用了 `Depends(get_current_user)` 或 `Depends(get_current_user_optional)`
- [ ] 没有使用 `Depends(require_admin)` 这类直接抛出 HTTPException 的依赖

**用户身份解析检查**：
- [ ] 所有端点都正确解析了 `user_id`（使用 `uuid.UUID(current_user.get("user_id"))`）
- [ ] 所有端点都正确解析了 `user_role`（使用 `current_user.get("role", "REGULAR").upper()`）
- [ ] Optional Auth 端点都正确处理了 `current_user` 为 `None` 的情况

**Service 层调用检查**：
- [ ] 所有端点都将 `current_user_id` 和 `user_role` 传递给 Service 层
- [ ] Service 层参数名称与类型一致（UUID, str）

**异常处理检查**：
- [ ] 所有端点都捕获了 `UserPreferenceNotFoundException` 并返回 404
- [ ] 所有端点都捕获了 `NotificationNotFoundException` 并返回 404
- [ ] 所有端点都捕获了 `PermissionDeniedException` 并返回 403
- [ ] 所有端点都捕获了通用异常并返回 500
- [ ] 错误响应使用了 `error_response()` 函数
- [ ] 成功响应使用了 `success_response()` 函数

**响应格式检查**：
- [ ] 所有成功响应都包含 `success_response(data=...)`
- [ ] 所有错误响应都包含 `JSONResponse(status_code=..., content=error_response(...))`

---

## 7. 最终检查清单

### 7.1. 通用检查

- [ ] 所有 10个 Service 方法都已更新
- [ ] 所有 10个 API 端点都已更新
- [ ] 权限守卫函数已实现（3个函数）
- [ ] 所有权限检查都已实现

### 7.2. 一致性检查

- [ ] 所有改造都与母版 Section 5.0.5 保持一致
- [ ] 权限守卫函数逻辑与母版一致
- [ ] 用户身份解析方式与母版一致
- [ ] 双轨鉴权模式应用正确
- [ ] 字符串比较方式一致（`if user_role not in ['ADMIN', 'SUPERADMIN']:`）

### 7.3. 无遗漏检查

- [ ] 没有遗漏任何 Service 方法
- [ ] 没有遗漏任何 API 端点
- [ ] 没有遗漏任何权限检查
- [ ] 没有遗漏任何异常处理

### 7.4. 无冲突检查

- [ ] 没有与现有业务逻辑冲突
- [ ] 没有改变方法的返回值结构
- [ ] 没有引入新的依赖
- [ ] 所有改造都是最小幅度修改

---

## 8. 使用说明

### 8.1. Cursor 使用说明

**改造代码时必须使用 Cursor 的 `@` 标记引用**：

```python
# 正确的引用方式
@app.crud.user_preferences_notifications  # ← 使用 @app.crud.user_preferences_notifications 引用 CRUD 文件
from app.services.user_preferences_notifications_service import UserPreferencesNotificationsService  # ← 使用 @app.services.user_preferences_notifications_service 引用 Service 文件

# 改造 Service 层时
from app.crud.user_preferences_notifications import (
    get_user_preferences,
    create_bulk_notifications,
    get_notifications_paginated,
    # ← 使用 @app.crud.user_preferences_notifications 引用所有需要用到的 CRUD 函数
)

# 改造 API 层时
from app.services.user_preferences_notifications_service import UserPreferencesNotificationsService  # ← 使用 @app.services.user_preferences_notifications_service 引用 Service 文件
```

### 8.2. 读取现有代码

**改造前必须读取现有代码**：
1. 使用 `@app/services/user_preferences_notifications_service` 读取 `app/services/user_preferences_notifications_service.py`
2. 使用 `@app/api/v1/endpoints/user_preferences_notifications` 读取 `app/api/v1/endpoints/user_preferences_notifications.py`
3. 仔细分析现有方法签名和权限实现
4. 只修改权限相关的代码，不改变业务逻辑

### 8.3. 最小幅度修改原则

**改造时必须遵守的原则**：
1. 只添加或修改权限相关的代码
2. 不修改任何业务逻辑执行流程
3. 不删除或重命名任何现有方法
4. 不改变任何方法的返回值结构
5. 保持代码风格和结构一致

---

**文档版本**: V1.0
**创建日期**: 2026-01-12
**状态**: 准备就绪
