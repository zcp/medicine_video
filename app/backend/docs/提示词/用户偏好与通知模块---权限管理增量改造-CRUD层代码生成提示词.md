# 用户偏好与通知模块 - 权限管理增量改造 CRUD 层代码生成提示词

**版本**: V1.0
**创建日期**: 2026-01-12
**目标**: 指导 AI 对用户偏好与通知模块的 CRUD 层进行权限管理增量改造

---

## 1. 任务概述

**目标模块**: 用户偏好与通知模块（User Preferences & Notifications Module）

**需要更新的代码文件**:
- `app/crud/user_preferences_notifications.py`

**目标**: 将现有的用户偏好与通知模块 CRUD 层代码更新，使其符合通用权限管理策略（母版 Section 5.0.5）

---

## 2. 核心权限管理策略

### 2.1. CRUD 层权限过滤职责

**核心原则**：
- **禁止内存过滤**：严禁在 Python 代码中先查询所有数据，再用 if 判断过滤（性能陷阱）。
- **SQL 层面过滤**：必须在 WHERE 条件中应用权限过滤逻辑。
- **业务与权限 AND 关系**：业务筛选条件与权限过滤条件必须用 AND 连接。
- **总数与数据查询一致**：`count(*)` 查询和实际数据查询必须使用完全相同的 WHERE 条件。

**权限过滤逻辑**：
1. **Admin 查询**（`role in ['ADMIN', 'SUPERADMIN']`）：无权限过滤，可查看所有用户的通知和偏好。
2. **Regular User 查询**（`role == 'REGULAR'`）：`WHERE user_id=current_user_id`（仅可查看自己的通知和偏好）。
3. **Anonymous 查询**（`role is None`）：`WHERE FALSE`（无权限，不可查看任何通知或偏好）。

### 2.2. CRUD 方法参数规范

**所有需要权限过滤的 CRUD 方法，都必须接收以下参数**：

```python
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,  # 当前用户的 public_id
    role: Optional[str] = None,  # 当前用户的角色（'ADMIN', 'SUPERADMIN', 'REGULAR', None）
) -> Tuple[List[Notification], int]:
    """
    分页获取通知列表（带权限过滤）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量
        is_read: 是否已读
        notification_type: 通知类型
        current_user_id: 当前用户的 public_id（权限参数）
        role: 当前用户的角色（权限参数）
    
    Returns:
        Tuple[List[Notification], int]: 通知列表和总数
    
    Raises:
        无
    """
```

**参数类型规范**：
- `current_user_id: Optional[UUID]` - 当前用户的 public_id，未登录时为 `None`
- `role: Optional[str]` - 当前用户的角色，可能值为 `'ADMIN'`、`'SUPERADMIN'`、`'REGULAR'` 或 `None`

---

## 3. 更新前检查清单

### 3.1. 文档结构检查

- [ ] 确认目标文件路径正确（`app/crud/user_preferences_notifications.py`）
- [ ] 确认模块名称正确（用户偏好与通知模块）
- [ ] 确认需要更新的 CRUD 层方法

### 3.2. 现有代码分析

- [ ] 读取 `app/crud/user_preferences_notifications.py` 现有代码
- [ ] 识别所有需要权限过滤的 CRUD 方法
- [ ] 识别现有的权限实现方式
- [ ] 检查现有的 SQL 查询语句

### 3.3. 改造范围确认

- [ ] 确认 CRUD 方法数量（10+个）
- [ ] 确认需要添加权限参数的方法数量（3个）
- [ ] 确认需要权限过滤的方法类型（分页查询、列表查询）

---

## 4. CRUD 方法改造指南

### 4.1. 需要改造的 CRUD 方法清单

**所有需要改造的 CRUD 方法**：

1. **用户偏好查询**（1个方法）：
   - `get_user_preferences` - 获取用户偏好

2. **通知查询**（4个方法）：
   - `get_notifications_paginated` - 分页获取通知列表
   - `get_notifications` - 获取通知列表
   - `get_notification` - 获取通知详情
   - `get_unread_count` - 获取未读通知数量

**不需要改造的方法**：
- `create` - 创建通知（不需要权限过滤）
- `create_bulk` - 批量创建通知（不需要权限过滤）
- `update` - 更新通知（不需要权限过滤）
- `delete` - 删除通知（不需要权限过滤）
- `delete_bulk` - 批量删除通知（不需要权限过滤）
- `create_or_update_user_preferences` - 创建或更新用户偏好（不需要权限过滤）

**总计需要改造**: 3个 CRUD 方法（用户偏好查询 + 通知查询）

### 4.2. CRUD 方法改造规范

#### 4.2.1. 方法签名更新

**所有需要权限过滤的 CRUD 方法，都必须更新方法签名**：

```python
# 改造前（旧签名）
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """分页获取通知列表"""
    ...

# 改造后（新签名）
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """
    分页获取通知列表（带权限过滤）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量
        is_read: 是否已读
        notification_type: 通知类型
        current_user_id: 当前用户的 public_id（权限参数）
        role: 当前用户的角色（权限参数）
    
    Returns:
        Tuple[List[Notification], int]: 通知列表和总数
    
    Raises:
        无
    """
    ...
```

#### 4.2.2. 权限过滤实现

**核心实现要点**：
1. **禁止内存过滤**：必须在 SQL 的 WHERE 条件中应用权限过滤。
2. **业务与权限 AND 关系**：业务筛选条件和权限过滤条件用 AND 连接。
3. **总数与数据查询一致**：count 查询和实际数据查询使用完全相同的 WHERE 条件。
4. **根据用户身份应用不同过滤**：Admin、Regular User、Anonymous 使用不同的权限过滤逻辑。

**权限过滤逻辑实现示例**：

```python
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """
    分页获取通知列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有用户的通知
    - Regular User：仅可查看自己的通知
    - Anonymous：无权限，不可查看任何通知
    """
    
    # 1. 构建基础查询
    query = select(Notification)
    
    # 2. 构建业务筛选条件
    conditions = []
    
    if is_read is not None:
        conditions.append(Notification.is_read == is_read)
    
    if notification_type:
        conditions.append(Notification.notification_type == NotificationType(notification_type))
    
    # 3. 添加权限过滤条件（核心）
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤，可查看所有通知
        pass  # 不添加任何权限过滤条件
    elif role == 'REGULAR':
        # Regular User：仅可查看自己的通知
        conditions.append(Notification.user_id == current_user_id)
    else:
        # Anonymous：无权限，不可查看任何通知
        conditions.append(False)  # 这会导致查询返回空结果
    
    # 4. 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    # 5. 排序（按创建时间倒序）
    query = query.order_by(Notification.created_at.desc())
    
    # 6. 计算总数（使用完全相同的 WHERE 条件）
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 7. 应用分页
    query = query.offset((page - 1) * size).limit(size)
    
    # 8. 执行查询
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # 9. 返回结果
    return list(notifications), total
```

---

## 5. 具体方法改造示例

### 5.1. `get_notifications_paginated` 方法

**改造前**：
```python
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """分页获取通知列表"""
    query = select(Notification)
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    
    if notification_type:
        query = query.where(Notification.notification_type == NotificationType(notification_type))
    
    query = query.order_by(Notification.created_at.desc())
    
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return list(notifications), total
```

**改造后**：
```python
async def get_notifications_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Notification], int]:
    """
    分页获取通知列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有通知
    - Regular User：仅可查看自己的通知
    - Anonymous：无权限
    """
    query = select(Notification)
    
    # 构建业务筛选条件
    conditions = []
    
    if is_read is not None:
        conditions.append(Notification.is_read == is_read)
    
    if notification_type:
        conditions.append(Notification.notification_type == NotificationType(notification_type))
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    elif role == 'REGULAR':
        # Regular User：仅可查看自己的通知
        conditions.append(Notification.user_id == current_user_id)
    else:
        # Anonymous：无权限
        conditions.append(False)
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Notification.created_at.desc())
    
    # 计算总数（使用完全相同的 WHERE 条件）
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return list(notifications), total
```

### 5.2. `get_notifications` 方法

**改造前**：
```python
async def get_notifications(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None
) -> List[Notification]:
    """获取通知列表"""
    query = select(Notification)
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    
    if notification_type:
        query = query.where(Notification.notification_type == NotificationType(notification_type))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return list(notifications)
```

**改造后**：
```python
async def get_notifications(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> List[Notification]:
    """
    获取通知列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有通知
    - Regular User：仅可查看自己的通知
    - Anonymous：无权限
    """
    query = select(Notification)
    
    # 构建业务筛选条件
    conditions = []
    
    if is_read is not None:
        conditions.append(Notification.is_read == is_read)
    
    if notification_type:
        conditions.append(Notification.notification_type == NotificationType(notification_type))
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    elif role == 'REGULAR':
        # Regular User：仅可查看自己的通知
        conditions.append(Notification.user_id == current_user_id)
    else:
        # Anonymous：无权限
        conditions.append(False)
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return list(notifications)
```

### 5.3. `get_user_preferences` 方法

**改造前**：
```python
async def get_user_preferences(
    db: AsyncSession,
    user_id: UUID
) -> Optional[UserPreferences]:
    """获取用户偏好"""
    query = select(UserPreferences).where(UserPreferences.user_id == user_id)
    
    result = await db.execute(query)
    user_preferences = result.scalar_one_or_none()
    
    return user_preferences
```

**改造后**：
```python
async def get_user_preferences(
    db: AsyncSession,
    current_user_id: UUID,  # ← 新增权限参数
    role: Optional[str] = None  # ← 新增权限参数
) -> Optional[UserPreferences]:
    """
    获取用户偏好（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看任何用户的偏好
    - Regular User：仅可查看自己的偏好
    - Anonymous：无权限
    """
    # 构建业务筛选条件（按 user_id 查询）
    query = select(UserPreferences)
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤，按传入的 current_user_id 查询（可能查询其他用户的偏好）
        pass  # 直接使用 current_user_id
    elif role == 'REGULAR':
        # Regular User：仅可查看自己的偏好（current_user_id 必须等于查询的 user_id）
        query = query.where(UserPreferences.user_id == current_user_id)
    else:
        # Anonymous：无权限
        query = query.where(False)
    
    result = await db.execute(query)
    user_preferences = result.scalar_one_or_none()
    
    return user_preferences
```

---

## 6. 改造后检查清单

### 6.1. 方法签名检查

- [ ] `get_notifications_paginated` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] `get_notifications` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] `get_user_preferences` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] 所有参数类型定义正确（`Optional[UUID]` 和 `Optional[str]`）

### 6.2. 权限过滤实现检查

- [ ] 所有方法都在 SQL WHERE 条件中应用权限过滤
- [ ] 所有方法都禁止内存过滤
- [ ] Admin 查询无权限过滤
- [ ] Regular User 查询使用正确的权限过滤逻辑（`user_id == current_user_id`）
- [ ] Anonymous 查询返回空结果（`WHERE FALSE`）
- [ ] 业务筛选与权限过滤使用 AND 关系

### 6.3. 总数查询一致性检查

- [ ] 所有分页查询方法的 `count(*)` 查询都使用与数据查询完全相同的 WHERE 条件
- [ ] 所有方法都使用 `.subquery()` 方法包装查询
- [ ] 所有方法都使用 `select(func.count())` 计算总数

### 6.4. 无内存过滤检查

- [ ] 没有在 Python 内存中过滤数据
- [ ] 所有过滤都在 SQL 查询中完成
- [ ] 没有使用 `if notification.user_id == current_user_id:` 这样的循环判断

### 6.5. 代码风格一致性检查

- [ ] 所有方法使用相同的权限过滤逻辑结构
- [ ] 所有方法的注释格式一致
- [ ] 所有方法的返回值结构一致
- [ ] 所有方法的代码风格一致

---

## 7. 最终检查清单

### 7.1. 完整性检查

- [ ] 所有 3个需要改造的 CRUD 方法都已更新
- [ ] 所有方法都已添加权限参数
- [ ] 所有方法都已实现权限过滤
- [ ] 所有方法都已实现总数查询一致性（如适用）

### 7.2. 一致性检查

- [ ] 所有改造都与母版 Section 5.0.5 保持一致
- [ ] 权限过滤逻辑与母版一致
- [ ] 参数名称和类型与母版一致
- [ ] SQL 查询结构一致

### 7.3. 无遗漏检查

- [ ] 没有遗漏任何需要改造的 CRUD 方法
- [ ] 没有遗漏任何权限参数
- [ ] 没有遗漏任何权限过滤逻辑
- [ ] 没有遗漏任何总数查询一致性检查

### 7.4. 无冲突检查

- [ ] 没有与现有业务逻辑冲突
- [ ] 没有改变方法的返回值结构
- [ ] 没有改变方法的参数顺序
- [ ] 所有改造都是最小幅度修改

---

## 8. 使用说明

### 8.1. Cursor 使用说明

**改造代码时必须使用 Cursor 的 `@` 标记引用**：

```python
# 正确的引用方式
@app.crud.user_preferences_notifications  # ← 使用 @app.crud.user_preferences_notifications 引用 CRUD 文件

# 改造时
from app.crud.user_preferences_notifications import (
    get_notifications_paginated,
    get_notifications,
    get_user_preferences,
    # ← 使用 @app.crud.user_preferences_notifications 引用所有需要改造的方法
)
```

### 8.2. 读取现有代码

**改造前必须读取现有代码**：
1. 使用 `@app/crud/user_preferences_notifications` 读取 `app/crud/user_preferences_notifications.py`
2. 仔细分析现有方法签名和权限实现
3. 只修改权限相关的代码，不改变业务逻辑

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
