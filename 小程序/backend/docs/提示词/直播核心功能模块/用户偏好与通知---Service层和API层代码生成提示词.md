# 用户偏好与通知模块 - Service层和API层代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**模块名**: user_preference_notification  
**功能模块**: 用户偏好与通知  
**目标文件**: 
- Service层: `backend/live_core_service/app/services/user_preference_notification_service.py`
- API层: `backend/live_core_service/app/api/v1/endpoints/user_preference_notification.py`

---

## 1. 角色定义

你是一名精通FastAPI和"学院派"架构的资深Python后端工程师。你的任务是生成Service层（业务逻辑）和API层（HTTP端点）代码。

**核心要求**:
- Service层负责业务编排、权限检查、事务管理
- API层负责HTTP请求/响应、调用Service层
- 严格遵循异常处理规范
- 使用统一响应格式

---

## 2. Service层代码

### 2.1 文件导入

```python
"""
用户偏好与通知模块 - Service层

职责：业务逻辑层，负责业务编排、权限检查、事务管理
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user_preference_notification as crud
from app.schemas.user_preference_notification import (
    UserPreferencesUpdate,
    UserPreferencesItem,
    NotificationItem,
    NotificationCreateRequest,
    NotificationBatchCreateResponse,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationListResponse,
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseOperationException,
)

logger = logging.getLogger(__name__)
```

### 2.2 Service类定义

```python
class UserPreferenceNotificationService:
    """用户偏好与通知Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
```

### 2.3 权限守卫方法

#### 2.3.1 _check_admin_permission

```python
def _check_admin_permission(self, user_role: Optional[str]) -> None:
    """
    检查管理员权限
    
    Args:
        user_role: 用户角色
        
    Raises:
        PermissionDeniedException: 非管理员用户
    """
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

#### 2.3.2 _check_user_preferences_ownership

```python
def _check_user_preferences_ownership(
    self,
    resource_owner_id: UUID,
    current_user_id: UUID,
    user_role: str
) -> None:
    """
    检查用户资源所有权
    
    Args:
        resource_owner_id: 资源所有者ID
        current_user_id: 当前用户ID
        user_role: 当前用户角色
        
    Raises:
        PermissionDeniedException: 无权操作
        NotFoundException: 资源不存在或无权访问
    """
    # 管理员：可以操作所有用户的资源
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源所有者：可以操作自己的资源
    if resource_owner_id == current_user_id:
        return
    
    # 其他用户：返回404隐藏存在性
    raise NotFoundException("Resource not found")
```

### 2.4 User Preferences Service方法

#### 2.4.1 get_preferences

```python
async def get_preferences(
    self,
    user_id: UUID,
    role: str
) -> UserPreferencesItem:
    """
    获取用户偏好设置
    
    Args:
        user_id: 用户ID
        role: 用户角色
        
    Returns:
        UserPreferencesItem对象
        
    Raises:
        NotFoundException: 用户不存在
    """
    try:
        prefs = await crud.get_preferences(self.db, user_id)
        
        if not prefs:
            # 首次访问，返回默认偏好
            import uuid
            from app.models.user_preference_notification import UserPreferences
            prefs = UserPreferences(
                id=uuid.uuid4(),
                user_id=user_id
            )
            # 不保存到数据库，只返回默认值
        
        return UserPreferencesItem.model_validate(prefs)
    except Exception as e:
        self.logger.error(f"获取用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise
```

**关键说明**:
- 首次访问返回默认值对象（不存入数据库）
- 使用`model_validate()`转换ORM对象

#### 2.4.2 update_preferences

```python
async def update_preferences(
    self,
    user_id: UUID,
    prefs_update: UserPreferencesUpdate,
    role: str
) -> UserPreferencesItem:
    """
    更新用户偏好设置
    
    Args:
        user_id: 用户ID
        prefs_update: 偏好更新数据
        role: 用户角色
        
    Returns:
        更新后的UserPreferencesItem对象
        
    Raises:
        InvalidParameterException: 参数错误
    """
    try:
        # 创建或更新偏好
        prefs = await crud.create_or_update_preferences(
            self.db,
            user_id,
            prefs_update
        )
        
        # 提交事务
        await self.db.commit()
        await self.db.refresh(prefs)
        
        self.logger.info(f"更新用户偏好成功: user_id={str(user_id)[:8]}")
        return UserPreferencesItem.model_validate(prefs)
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"更新用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise
```

**关键说明**:
- Service层调用`commit()`和`rollback()`
- 异常时回滚事务

### 2.5 Notifications Service方法

#### 2.5.1 get_notifications_list

```python
async def get_notifications_list(
    self,
    user_id: UUID,
    page: int,
    size: int,
    is_read: Optional[bool],
    notification_type: Optional[str],
    role: str
) -> NotificationListResponse:
    """
    获取用户通知列表
    
    Args:
        user_id: 用户ID
        page: 页码
        size: 每页大小
        is_read: 是否已读筛选
        notification_type: 通知类型筛选
        role: 用户角色
        
    Returns:
        NotificationListResponse对象
    """
    try:
        items, total = await crud.get_notifications(
            self.db,
            user_id=user_id,
            page=page,
            size=size,
            is_read=is_read,
            notification_type=notification_type,
            current_user_id=user_id,
            role=role
        )
        
        # 转换为Schema
        notification_items = [NotificationItem.model_validate(item) for item in items]
        
        return NotificationListResponse(
            items=notification_items,
            total=total,
            page=page,
            size=size,
            has_more=(page * size) < total
        )
    except Exception as e:
        self.logger.error(f"获取通知列表失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.2 get_unread_count

```python
async def get_unread_count(self, user_id: UUID) -> Dict[str, int]:
    """
    获取未读通知数量
    
    Args:
        user_id: 用户ID
        
    Returns:
        {"unread_count": int}
    """
    try:
        count = await crud.get_unread_count(self.db, user_id)
        return {"unread_count": count}
    except Exception as e:
        self.logger.error(f"获取未读数量失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.3 mark_notification_as_read

```python
async def mark_notification_as_read(
    self,
    notification_id: UUID,
    user_id: UUID,
    role: str
) -> None:
    """
    标记通知为已读
    
    Args:
        notification_id: 通知ID
        user_id: 用户ID
        role: 用户角色
        
    Raises:
        NotFoundException: 通知不存在或不属于当前用户
    """
    try:
        notification = await crud.mark_as_read(self.db, notification_id, user_id)
        
        if not notification:
            raise NotFoundException("通知不存在或不属于当前用户")
        
        await self.db.commit()
        self.logger.info(f"标记通知为已读: notification_id={str(notification_id)[:8]}")
    except NotFoundException:
        raise
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"标记通知为已读失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.4 mark_all_notifications_as_read

```python
async def mark_all_notifications_as_read(self, user_id: UUID) -> Dict[str, int]:
    """
    标记所有通知为已读
    
    Args:
        user_id: 用户ID
        
    Returns:
        {"updated_count": int}
    """
    try:
        count = await crud.mark_all_as_read(self.db, user_id)
        await self.db.commit()
        self.logger.info(f"标记所有通知为已读: user_id={str(user_id)[:8]}, count={count}")
        return {"updated_count": count}
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"标记所有通知为已读失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.5 create_notifications_batch

```python
async def create_notifications_batch(
    self,
    user_ids: List[UUID],
    notification_data: NotificationCreateRequest,
    admin_role: str
) -> NotificationBatchCreateResponse:
    """
    批量创建通知（管理员）
    
    Args:
        user_ids: 用户ID列表（空列表表示全部用户）
        notification_data: 通知数据
        admin_role: 管理员角色
        
    Returns:
        NotificationBatchCreateResponse对象
        
    Raises:
        PermissionDeniedException: 非管理员
        InvalidParameterException: 参数错误
    """
    # 权限检查
    self._check_admin_permission(admin_role)
    
    try:
        # 处理user_ids
        if not user_ids:
            # 空列表表示全部用户，需要查询所有用户ID
            from app.models.user_core import User
            from sqlalchemy import select
            query = select(User.public_id)
            result = await self.db.execute(query)
            user_ids = [row[0] for row in result.all()]
            
            if not user_ids:
                raise InvalidParameterException("没有可通知的用户")
        
        # 构建通知列表
        notifications_list = [
            {
                "user_id": uid,
                "title": notification_data.title,
                "content": notification_data.content,
                "notification_type": notification_data.notification_type,
                "related_id": notification_data.related_id,
                "related_type": notification_data.related_type,
            }
            for uid in user_ids
        ]
        
        # 批量创建
        count = await crud.bulk_create_notifications(self.db, notifications_list)
        await self.db.commit()
        
        self.logger.info(f"批量创建通知: count={count}")
        return NotificationBatchCreateResponse(
            total_created=count,
            user_ids=user_ids
        )
    except PermissionDeniedException:
        raise
    except InvalidParameterException:
        raise
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"批量创建通知失败: error={str(e)}")
        raise
```

**关键说明**:
- 空`user_ids`表示全部用户，需查询所有用户ID
- 批量创建优化性能

#### 2.5.6 get_notifications_list_admin

```python
async def get_notifications_list_admin(
    self,
    page: int,
    size: int,
    user_id_filter: Optional[UUID],
    notification_type: Optional[str],
    is_read: Optional[bool],
    admin_role: str
) -> NotificationListResponse:
    """
    管理员获取通知列表
    
    Args:
        page: 页码
        size: 每页大小
        user_id_filter: 用户ID筛选
        notification_type: 通知类型筛选
        is_read: 是否已读筛选
        admin_role: 管理员角色
        
    Returns:
        NotificationListResponse对象
        
    Raises:
        PermissionDeniedException: 非管理员
    """
    # 权限检查
    self._check_admin_permission(admin_role)
    
    try:
        items, total = await crud.get_notifications_admin(
            self.db,
            page=page,
            size=size,
            user_id=user_id_filter,
            notification_type=notification_type,
            is_read=is_read
        )
        
        notification_items = [NotificationItem.model_validate(item) for item in items]
        
        return NotificationListResponse(
            items=notification_items,
            total=total,
            page=page,
            size=size,
            has_more=(page * size) < total
        )
    except PermissionDeniedException:
        raise
    except Exception as e:
        self.logger.error(f"管理员获取通知列表失败: error={str(e)}")
        raise
```

#### 2.5.7 update_notification

```python
async def update_notification(
    self,
    notification_id: UUID,
    update_data: NotificationUpdateRequest,
    admin_role: str
) -> NotificationItem:
    """
    更新通知（管理员）
    
    Args:
        notification_id: 通知ID
        update_data: 更新数据
        admin_role: 管理员角色
        
    Returns:
        NotificationItem对象
        
    Raises:
        PermissionDeniedException: 非管理员
        NotFoundException: 通知不存在
    """
    # 权限检查
    self._check_admin_permission(admin_role)
    
    try:
        update_dict = update_data.model_dump(exclude_unset=True)
        notification = await crud.update_notification(
            self.db,
            notification_id,
            update_dict
        )
        
        if not notification:
            raise NotFoundException("通知不存在")
        
        await self.db.commit()
        await self.db.refresh(notification)
        
        self.logger.info(f"更新通知: notification_id={str(notification_id)[:8]}")
        return NotificationItem.model_validate(notification)
    except PermissionDeniedException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"更新通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.8 delete_notification

```python
async def delete_notification(
    self,
    notification_id: UUID,
    admin_role: str
) -> None:
    """
    删除通知（管理员）
    
    Args:
        notification_id: 通知ID
        admin_role: 管理员角色
        
    Raises:
        PermissionDeniedException: 非管理员
        NotFoundException: 通知不存在
    """
    # 权限检查
    self._check_admin_permission(admin_role)
    
    try:
        deleted = await crud.delete_notification(self.db, notification_id)
        
        if not deleted:
            raise NotFoundException("通知不存在")
        
        await self.db.commit()
        self.logger.info(f"删除通知: notification_id={str(notification_id)[:8]}")
    except PermissionDeniedException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"删除通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise
```

#### 2.5.9 batch_delete_notifications

```python
async def batch_delete_notifications(
    self,
    delete_request: NotificationBatchDeleteRequest,
    admin_role: str
) -> Dict[str, int]:
    """
    批量删除通知（管理员）
    
    Args:
        delete_request: 删除请求
        admin_role: 管理员角色
        
    Returns:
        {"deleted_count": int}
        
    Raises:
        PermissionDeniedException: 非管理员
    """
    # 权限检查
    self._check_admin_permission(admin_role)
    
    try:
        count = await crud.batch_delete_notifications(
            self.db,
            notification_ids=delete_request.notification_ids,
            delete_before=delete_request.delete_before,
            notification_type=delete_request.notification_type,
            is_read=delete_request.is_read
        )
        
        await self.db.commit()
        self.logger.info(f"批量删除通知: count={count}")
        return {"deleted_count": count}
    except PermissionDeniedException:
        raise
    except Exception as e:
        await self.db.rollback()
        self.logger.error(f"批量删除通知失败: error={str(e)}")
        raise
```

---

## 3. API层代码

### 3.1 文件导入

```python
"""
用户偏好与通知模块 - API层

职责：HTTP端点层，处理请求/响应，调用Service层
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.schemas.user_preference_notification import (
    UserPreferencesUpdate,
    NotificationCreateRequest,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
)
from app.services.user_preference_notification_service import UserPreferenceNotificationService
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Preferences & Notifications"])
```

### 3.2 User Preferences API端点

#### 3.2.1 GET /users/me/preferences

```python
@router.get("/users/me/preferences")
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户偏好设置"""
    # 🚨 必须在try之前提取user_id
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_preferences(user_id, role)
        logger.info(f"获取用户偏好成功: user_id={user_id_for_logging}")
        return success_response(data=result)
    except NotFoundException as e:
        logger.warning(f"获取用户偏好失败（资源不存在）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取用户偏好失败（系统错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.2.2 PATCH /users/me/preferences

```python
@router.patch("/users/me/preferences")
async def update_user_preferences(
    prefs_update: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户偏好设置"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.update_preferences(user_id, prefs_update, role)
        logger.info(f"更新用户偏好成功: user_id={user_id_for_logging}")
        return success_response(data=result)
    except InvalidParameterException as e:
        logger.warning(f"更新用户偏好失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新用户偏好失败（系统错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

### 3.3 Notifications API端点（用户）

#### 3.3.1 GET /users/me/notifications

```python
@router.get("/users/me/notifications")
async def get_user_notifications(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_notifications_list(
            user_id, page, size, is_read, notification_type, role
        )
        logger.info(f"获取通知列表成功: user_id={user_id_for_logging}, page={page}, size={size}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取通知列表失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.3.2 GET /users/me/notifications/unread-count

```python
@router.get("/users/me/notifications/unread-count")
async def get_unread_notifications_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未读通知数量"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_unread_count(user_id)
        logger.info(f"获取未读数量成功: user_id={user_id_for_logging}, count={result['unread_count']}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取未读数量失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.3.3 POST /users/me/notifications/{notification_id}/read

```python
@router.post("/users/me/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID = Path(..., description="通知ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记通知为已读"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        await service.mark_notification_as_read(notification_id, user_id, role)
        logger.info(f"标记通知为已读成功: notification_id={str(notification_id)[:8]}")
        return success_response(data=None)
    except NotFoundException as e:
        logger.warning(f"标记通知为已读失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"标记通知为已读失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.3.4 POST /users/me/notifications/read-all

```python
@router.post("/users/me/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记所有通知为已读"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.mark_all_notifications_as_read(user_id)
        logger.info(f"标记所有通知为已读成功: user_id={user_id_for_logging}, count={result['updated_count']}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

### 3.4 Notifications API端点（管理员）

#### 3.4.1 POST /admin/notifications

```python
@router.post("/admin/notifications")
async def create_notifications_batch(
    notification_data: NotificationCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.create_notifications_batch(
            notification_data.user_ids,
            notification_data,
            role
        )
        logger.info(f"批量创建通知成功: admin={user_id_for_logging}, count={result.total_created}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"批量创建通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"批量创建通知失败（参数错误）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"批量创建通知失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.4.2 GET /admin/notifications

```python
@router.get("/admin/notifications")
async def get_notifications_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    user_id: Optional[UUID] = Query(None, description="用户ID筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_notifications_list_admin(
            page, size, user_id, notification_type, is_read, role
        )
        logger.info(f"管理员获取通知列表成功: admin={user_id_for_logging}, page={page}, size={size}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"管理员获取通知列表失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except Exception as e:
        logger.error(f"管理员获取通知列表失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.4.3 PATCH /admin/notifications/{notification_id}

```python
@router.patch("/admin/notifications/{notification_id}")
async def update_notification(
    notification_id: UUID = Path(..., description="通知ID"),
    update_data: NotificationUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.update_notification(notification_id, update_data, role)
        logger.info(f"更新通知成功: admin={user_id_for_logging}, notification_id={str(notification_id)[:8]}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"更新通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"更新通知失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"更新通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.4.4 DELETE /admin/notifications/{notification_id}

```python
@router.delete("/admin/notifications/{notification_id}")
async def delete_notification(
    notification_id: UUID = Path(..., description="通知ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        await service.delete_notification(notification_id, role)
        logger.info(f"删除通知成功: admin={user_id_for_logging}, notification_id={str(notification_id)[:8]}")
        return success_response(data=None)
    except PermissionDeniedException as e:
        logger.warning(f"删除通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"删除通知失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"删除通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.4.5 POST /admin/notifications/batch-delete

```python
@router.post("/admin/notifications/batch-delete")
async def batch_delete_notifications(
    delete_request: NotificationBatchDeleteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.batch_delete_notifications(delete_request, role)
        logger.info(f"批量删除通知成功: admin={user_id_for_logging}, count={result['deleted_count']}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"批量删除通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except Exception as e:
        logger.error(f"批量删除通知失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

## 4. 验证清单

### 4.1 Service层检查
- [ ] 所有方法都有权限检查
- [ ] 使用`_check_admin_permission()`检查管理员权限
- [ ] 事务管理正确（`commit()`/`rollback()`）
- [ ] 批量操作有验证逻辑
- [ ] 角色字符串使用大写

### 4.2 API层检查
- [ ] 所有端点都使用完整的异常处理模板
- [ ] 使用`JSONResponse`和`error_response()`
- [ ] `user_id`在`try`之前提取
- [ ] 记录日志（UUID只取前8位）
- [ ] `APIRouter`不指定`prefix`

### 4.3 API-Service对应关系检查
- [ ] 每个API端点都有对应的Service方法

---

**生成指令**: 请严格按照本文档要求生成Service层和API层代码。
