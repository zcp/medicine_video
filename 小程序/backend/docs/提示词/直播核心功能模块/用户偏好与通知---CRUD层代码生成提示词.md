# 用户偏好与通知模块 - CRUD层代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**模块名**: user_preference_notification  
**功能模块**: 用户偏好与通知  
**目标文件**: `backend/live_core_service/app/crud/user_preference_notification.py`

---

## 1. 角色定义

你是一名精通SQLAlchemy 2.0和异步编程的资深Python后端工程师。你的任务是生成符合"学院派"架构规范的CRUD层代码。

**核心职责**:
- 只执行数据库操作
- 不处理业务逻辑
- 不调用`commit()`或`rollback()`（由Service层管理）
- SQL级权限过滤
- 防止N+1问题

---

## 2. 文件导入

```python
"""
用户偏好与通知模块 - CRUD层

职责：数据访问层，执行数据库CRUD操作
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_preference_notification import UserPreferences, Notification
from app.schemas.user_preference_notification import UserPreferencesUpdate
from app.exceptions import DatabaseOperationException

logger = logging.getLogger(__name__)
```

---

## 3. CRUD函数定义

### 3.1 User Preferences CRUD

#### 3.1.1 get_preferences - 获取用户偏好

```python
async def get_preferences(
    db: AsyncSession,
    user_id: UUID
) -> Optional[UserPreferences]:
    """
    获取用户偏好设置
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        UserPreferences对象或None（首次访问）
    """
    try:
        query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"查询用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"查询用户偏好失败: {str(e)}") from e
```

**关键说明**:
- 返回`None`表示首次访问，由Service层处理默认值
- 使用`scalar_one_or_none()`处理结果
- 不调用`commit()`

#### 3.1.2 create_or_update_preferences - 创建或更新用户偏好

```python
async def create_or_update_preferences(
    db: AsyncSession,
    user_id: UUID,
    prefs_in: UserPreferencesUpdate
) -> UserPreferences:
    """
    创建或更新用户偏好设置（Upsert）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        prefs_in: 偏好更新数据
        
    Returns:
        创建或更新后的UserPreferences对象
    """
    try:
        # 查询现有偏好
        existing = await get_preferences(db, user_id)
        
        # 获取实际提供的字段（排除未设置的字段）
        update_data = prefs_in.model_dump(exclude_unset=True)
        
        if existing:
            # 更新现有记录
            for key, value in update_data.items():
                setattr(existing, key, value)
            await db.flush()
            await db.refresh(existing)
            logger.info(f"更新用户偏好: user_id={str(user_id)[:8]}, fields={list(update_data.keys())}")
            return existing
        else:
            # 创建新记录
            import uuid
            new_prefs = UserPreferences(
                id=uuid.uuid4(),
                user_id=user_id,
                **update_data
            )
            db.add(new_prefs)
            await db.flush()
            await db.refresh(new_prefs)
            logger.info(f"创建用户偏好: user_id={str(user_id)[:8]}")
            return new_prefs
    except Exception as e:
        logger.error(f"创建或更新用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"创建或更新用户偏好失败: {str(e)}") from e
```

**关键说明**:
- 使用`model_dump(exclude_unset=True)`只获取实际提供的字段
- 区分创建和更新逻辑
- 使用`flush()`和`refresh()`刷新对象
- 不调用`commit()`（由Service层调用）

---

### 3.2 Notifications CRUD

#### 3.2.1 get_notifications - 获取通知列表（分页）

```python
async def get_notifications(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 10,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """
    获取用户通知列表（分页）
    
    Args:
        db: 数据库会话
        user_id: 要查询的用户ID
        page: 页码
        size: 每页大小
        is_read: 是否已读筛选（可选）
        notification_type: 通知类型筛选（可选）
        current_user_id: 当前用户的ID（用于权限检查）
        role: 当前用户的角色（用于权限检查）
        
    Returns:
        (通知列表, 总数)
        
    Raises:
        PermissionDeniedException: 权限不足
    """
    from app.exceptions import PermissionDeniedException
    
    try:
        # 🚨 SQL级权限过滤：普通用户只能查看自己的通知
        if role not in ['ADMIN', 'SUPERADMIN']:
            if current_user_id != user_id:
                raise PermissionDeniedException("权限不足，只能查看自己的通知")
        
        # 构建基础查询
        query = select(Notification).where(Notification.user_id == user_id)
        conditions = []
        
        # 业务筛选条件
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        if notification_type:
            conditions.append(Notification.notification_type == notification_type)
        
        # 组合所有条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 🚨 COUNT查询（防止N+1）
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # 排序和分页
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        # 执行查询
        result = await db.execute(query)
        items = list(result.scalars().all())
        
        logger.info(f"查询通知列表: user_id={str(user_id)[:8]}, page={page}, size={size}, total={total}")
        return items, total
    except PermissionDeniedException:
        raise
    except Exception as e:
        logger.error(f"查询通知列表失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"查询通知列表失败: {str(e)}") from e
```

**关键说明**:
- SQL级权限过滤在查询开始前完成
- 使用两次查询（COUNT + SELECT）
- 按`created_at`倒序排序
- 不调用`commit()`

#### 3.2.2 get_unread_count - 获取未读通知数量

```python
async def get_unread_count(
    db: AsyncSession,
    user_id: UUID
) -> int:
    """
    获取用户的未读通知数量
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        未读通知数量
    """
    try:
        query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False  # noqa: E712
            )
        )
        count = await db.scalar(query)
        return count or 0
    except Exception as e:
        logger.error(f"查询未读通知数量失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"查询未读通知数量失败: {str(e)}") from e
```

#### 3.2.3 mark_as_read - 标记通知为已读

```python
async def mark_as_read(
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID
) -> Optional[Notification]:
    """
    标记通知为已读
    
    Args:
        db: 数据库会话
        notification_id: 通知ID
        user_id: 用户ID（用于权限检查）
        
    Returns:
        更新后的Notification对象或None（不存在或权限不足）
    """
    try:
        # 查询通知（含权限检查）
        query = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            return None
        
        # 幂等性：如果已读，直接返回
        if notification.is_read:
            return notification
        
        # 更新状态
        notification.is_read = True
        await db.flush()
        await db.refresh(notification)
        logger.info(f"标记通知为已读: notification_id={str(notification_id)[:8]}, user_id={str(user_id)[:8]}")
        return notification
    except Exception as e:
        logger.error(f"标记通知为已读失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"标记通知为已读失败: {str(e)}") from e
```

**关键说明**:
- 权限检查在SQL查询中完成
- 幂等性处理（已读直接返回）
- 不调用`commit()`

#### 3.2.4 mark_all_as_read - 标记所有通知为已读

```python
async def mark_all_as_read(
    db: AsyncSession,
    user_id: UUID
) -> int:
    """
    标记用户的所有未读通知为已读
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        更新的通知数量
    """
    try:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False  # noqa: E712
                )
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        updated_count = result.rowcount
        logger.info(f"标记所有通知为已读: user_id={str(user_id)[:8]}, count={updated_count}")
        return updated_count
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: user_id={str(user_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"标记所有通知为已读失败: {str(e)}") from e
```

#### 3.2.5 create_notification - 创建单条通知

```python
async def create_notification(
    db: AsyncSession,
    notification: Dict[str, Any]
) -> Notification:
    """
    创建单条通知
    
    Args:
        db: 数据库会话
        notification: 通知数据字典
        
    Returns:
        创建的Notification对象
    """
    try:
        import uuid
        new_notification = Notification(
            id=uuid.uuid4(),
            **notification
        )
        db.add(new_notification)
        await db.flush()
        await db.refresh(new_notification)
        return new_notification
    except Exception as e:
        logger.error(f"创建通知失败: error={str(e)}")
        raise DatabaseOperationException(f"创建通知失败: {str(e)}") from e
```

#### 3.2.6 bulk_create_notifications - 批量创建通知

```python
async def bulk_create_notifications(
    db: AsyncSession,
    notifications_list: List[Dict[str, Any]]
) -> int:
    """
    批量创建通知
    
    Args:
        db: 数据库会话
        notifications_list: 通知数据列表
        
    Returns:
        创建的通知数量
    """
    try:
        import uuid
        # 为每条通知生成UUID
        for notification in notifications_list:
            if 'id' not in notification:
                notification['id'] = uuid.uuid4()
        
        # 批量插入
        await db.execute(
            Notification.__table__.insert(),
            notifications_list
        )
        count = len(notifications_list)
        logger.info(f"批量创建通知: count={count}")
        return count
    except Exception as e:
        logger.error(f"批量创建通知失败: error={str(e)}")
        raise DatabaseOperationException(f"批量创建通知失败: {str(e)}") from e
```

**关键说明**:
- 使用`__table__.insert()`批量插入
- 为每条通知生成UUID
- 不调用`commit()`

#### 3.2.7 get_notifications_admin - 管理员获取通知列表

```python
async def get_notifications_admin(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    user_id: Optional[UUID] = None,
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None
) -> Tuple[List[Notification], int]:
    """
    管理员获取通知列表（分页，支持多条件筛选）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页大小
        user_id: 用户ID筛选（可选）
        notification_type: 通知类型筛选（可选）
        is_read: 是否已读筛选（可选）
        
    Returns:
        (通知列表, 总数)
    """
    try:
        # 构建基础查询
        query = select(Notification)
        conditions = []
        
        # 筛选条件
        if user_id:
            conditions.append(Notification.user_id == user_id)
        if notification_type:
            conditions.append(Notification.notification_type == notification_type)
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        
        # 组合所有条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # COUNT查询
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # 排序和分页
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        # 执行查询
        result = await db.execute(query)
        items = list(result.scalars().all())
        
        logger.info(f"管理员查询通知列表: page={page}, size={size}, total={total}")
        return items, total
    except Exception as e:
        logger.error(f"管理员查询通知列表失败: error={str(e)}")
        raise DatabaseOperationException(f"管理员查询通知列表失败: {str(e)}") from e
```

#### 3.2.8 update_notification - 更新通知

```python
async def update_notification(
    db: AsyncSession,
    notification_id: UUID,
    update_data: Dict[str, Any]
) -> Optional[Notification]:
    """
    更新通知（仅title和content）
    
    Args:
        db: 数据库会话
        notification_id: 通知ID
        update_data: 更新数据
        
    Returns:
        更新后的Notification对象或None
    """
    try:
        # 查询通知
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            return None
        
        # 更新字段
        for key, value in update_data.items():
            if key in ['title', 'content']:  # 只允许更新这两个字段
                setattr(notification, key, value)
        
        await db.flush()
        await db.refresh(notification)
        logger.info(f"更新通知: notification_id={str(notification_id)[:8]}")
        return notification
    except Exception as e:
        logger.error(f"更新通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"更新通知失败: {str(e)}") from e
```

#### 3.2.9 delete_notification - 删除单条通知

```python
async def delete_notification(
    db: AsyncSession,
    notification_id: UUID
) -> bool:
    """
    删除单条通知
    
    Args:
        db: 数据库会话
        notification_id: 通知ID
        
    Returns:
        是否成功删除
    """
    try:
        stmt = delete(Notification).where(Notification.id == notification_id)
        result = await db.execute(stmt)
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"删除通知: notification_id={str(notification_id)[:8]}")
        return deleted
    except Exception as e:
        logger.error(f"删除通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException(f"删除通知失败: {str(e)}") from e
```

#### 3.2.10 batch_delete_notifications - 批量删除通知

```python
async def batch_delete_notifications(
    db: AsyncSession,
    notification_ids: Optional[List[UUID]] = None,
    delete_before: Optional[datetime] = None,
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None
) -> int:
    """
    批量删除通知
    
    Args:
        db: 数据库会话
        notification_ids: 通知ID列表（可选）
        delete_before: 删除此日期之前的通知（可选）
        notification_type: 通知类型筛选（可选）
        is_read: 是否已读筛选（可选）
        
    Returns:
        删除的通知数量
    """
    try:
        conditions = []
        
        # 按ID列表删除
        if notification_ids:
            conditions.append(Notification.id.in_(notification_ids))
        
        # 按时间删除
        if delete_before:
            conditions.append(Notification.created_at < delete_before)
        
        # 其他筛选条件
        if notification_type:
            conditions.append(Notification.notification_type == notification_type)
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        
        if not conditions:
            return 0
        
        # 构建删除语句
        stmt = delete(Notification).where(and_(*conditions))
        result = await db.execute(stmt)
        deleted_count = result.rowcount
        logger.info(f"批量删除通知: count={deleted_count}")
        return deleted_count
    except Exception as e:
        logger.error(f"批量删除通知失败: error={str(e)}")
        raise DatabaseOperationException(f"批量删除通知失败: {str(e)}") from e
```

---

## 4. 代码生成要求

### 4.1 通用要求

1. **异步函数**: 所有函数使用`async def`
2. **类型注解**: 完整的参数和返回值类型注解
3. **异常处理**: 捕获异常并抛出`DatabaseOperationException`
4. **日志记录**: 关键操作记录INFO日志，错误记录ERROR日志
5. **UUID脱敏**: 日志中UUID只记录前8位

### 4.2 权限过滤

- 普通用户只能查看/操作自己的数据
- 在SQL查询中添加`user_id`条件
- 管理员接口不做SQL级权限过滤（由Service层检查）

### 4.3 性能优化

- 分页查询使用两次查询（COUNT + SELECT）
- 批量操作使用`bulk_insert_mappings()`或`__table__.insert()`
- 避免N+1问题

### 4.4 事务管理

- CRUD层不调用`commit()`或`rollback()`
- 使用`flush()`和`refresh()`刷新对象

---

## 5. 验证清单

生成代码后，请验证：

- [ ] 所有函数都使用`async def`
- [ ] 所有函数都有完整的docstring
- [ ] 分页使用两次查询
- [ ] SQL级权限过滤正确
- [ ] 不调用`commit()`或`rollback()`
- [ ] 异常处理完整
- [ ] 日志记录正确（UUID脱敏）
- [ ] 批量操作优化性能
- [ ] 代码通过linter检查

---

**生成指令**: 请严格按照本文档要求生成CRUD层代码。
