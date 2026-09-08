# 内容管理模块 - 权限管理增量改造 CRUD 层代码生成提示词

**版本**: V1.0
**创建日期**: 2026-01-12
**目标**: 指导 AI 对内容管理模块的 CRUD 层进行权限管理增量改造

---

## 1. 任务概述

**目标模块**: 内容管理模块（Content Management Module）

**需要更新的代码文件**:
- `app/crud/content_management.py`

**目标**: 将现有的内容管理模块 CRUD 层代码更新，使其符合通用权限管理策略（母版 Section 5.0.5）

---

## 2. 核心权限管理策略

### 2.1. CRUD 层权限过滤职责

**核心原则**：
- **禁止内存过滤**：严禁在 Python 代码中先查询所有数据，再用 if 判断过滤（性能陷阱）。
- **SQL 层面过滤**：必须在 WHERE 条件中应用权限过滤逻辑。
- **业务与权限 AND 关系**：业务筛选条件与权限过滤条件必须用 AND 连接。
- **总数与数据查询一致**：`count(*)` 查询和实际数据查询必须使用完全相同的 WHERE 条件。

**权限过滤逻辑（基于 `status` 字段）**：
1. **Admin 查询**（`role in ['ADMIN', 'SUPERADMIN']`）：无权限过滤，可查看所有标签、分类和关联。
2. **Regular User 查询**（`role == 'REGULAR'`）：`WHERE status='published'`（仅可查看已发布的标签、分类和关联）。
3. **Anonymous 查询**（`role is None`）：`WHERE status='published'`（仅可查看已发布的标签、分类和关联）。

### 2.2. CRUD 方法参数规范

**所有需要权限过滤的 CRUD 方法，都必须接收以下参数**：

```python
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,  # 当前用户的 public_id
    role: Optional[str] = None,  # 当前用户的角色（'ADMIN', 'SUPERADMIN', 'REGULAR', None）
) -> Tuple[List[Tag], int]:
    """
    分页获取标签列表（带权限过滤）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量
        search: 搜索关键词
        category_id: 分类ID
        current_user_id: 当前用户的 public_id（权限参数）
        role: 当前用户的角色（权限参数）
    
    Returns:
        Tuple[List[Tag], int]: 标签列表和总数
    
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

- [ ] 确认目标文件路径正确（`app/crud/content_management.py`）
- [ ] 确认模块名称正确（内容管理模块）
- [ ] 确认需要更新的 CRUD 层方法

### 3.2. 现有代码分析

- [ ] 读取 `app/crud/content_management.py` 现有代码
- [ ] 识别所有需要权限过滤的 CRUD 方法
- [ ] 识别现有的权限实现方式
- [ ] 检查现有的 SQL 查询语句

### 3.3. 改造范围确认

- [ ] 确认 CRUD 方法数量（20+个）
- [ ] 确认需要添加权限参数的方法数量（4个）
- [ ] 确认需要权限过滤的方法类型（分页查询、列表查询）

---

## 4. CRUD 方法改造指南

### 4.1. 需要改造的 CRUD 方法清单

**所有需要改造的 CRUD 方法**：

1. **标签查询**（4个方法）：
   - `get_tags_paginated` - 分页获取标签列表
   - `get_tags` - 获取标签列表
   - `get_tag_sessions` - 获取标签的场次列表
   - `get_tags_multi` - 多条件查询标签列表

2. **分类查询**（3个方法）：
   - `get_categories_paginated` - 分页获取分类列表
   - `get_categories` - 获取分类列表
   - `get_category_tags` - 获取分类的标签列表

3. **场次标签关联查询**（1个方法）：
   - `get_session_tags` - 获取场次的标签列表

**不需要改造的方法**：
- `get` - 根据ID获取单个标签/分类（不需要权限过滤，由 Service 层处理）
- `create` - 创建标签/分类（不需要权限过滤）
- `update` - 更新标签/分类（不需要权限过滤）
- `delete` - 删除标签/分类（不需要权限过滤）
- `set_session_tags` - 为场次设置标签（不需要权限过滤）

**总计需要改造**: 4个 CRUD 方法（标签查询 + 分类查询 + 场次标签关联查询）

### 4.2. CRUD 方法改造规范

#### 4.2.1. 方法签名更新

**所有需要权限过滤的 CRUD 方法，都必须更新方法签名**：

```python
# 改造前（旧签名）
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None
) -> Tuple[List[Tag], int]:
    """分页获取标签列表"""
    ...

# 改造后（新签名）
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Tag], int]:
    """
    分页获取标签列表（带权限过滤）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页数量
        search: 搜索关键词
        category_id: 分类ID
        current_user_id: 当前用户的 public_id（权限参数）
        role: 当前用户的角色（权限参数）
    
    Returns:
        Tuple[List[Tag], int]: 标签列表和总数
    
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
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Tag], int]:
    """
    分页获取标签列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有标签（包括草稿和归档）
    - Regular User：仅可查看已发布的标签
    - Anonymous：仅可查看已发布的标签
    """
    
    # 1. 构建基础查询
    query = select(Tag)
    
    # 2. 构建业务筛选条件
    conditions = []
    
    if search:
        conditions.append(Tag.name.ilike(f"%{search}%"))
    
    if category_id:
        conditions.append(Tag.category_id == category_id)
    
    # 3. 添加权限过滤条件（核心）
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤，可查看所有标签
        pass  # 不添加任何权限过滤条件
    else:
        # Regular User 或 Anonymous：仅可查看已发布的标签
        conditions.append(Tag.status == 'published')
    
    # 4. 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    # 5. 排序（按创建时间倒序）
    query = query.order_by(Tag.created_at.desc())
    
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
    tags = result.scalars().all()
    
    # 9. 返回结果
    return list(tags), total
```

---

## 5. 具体方法改造示例

### 5.1. `get_tags_paginated` 方法

**改造前**：
```python
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None
) -> Tuple[List[Tag], int]:
    """分页获取标签列表"""
    query = select(Tag)
    
    if search:
        query = query.where(Tag.name.ilike(f"%{search}%"))
    
    if category_id:
        query = query.where(Tag.category_id == category_id)
    
    query = query.order_by(Tag.created_at.desc())
    
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return list(tags), total
```

**改造后**：
```python
async def get_tags_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Tag], int]:
    """
    分页获取标签列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有标签
    - Regular User：仅可查看已发布的标签
    - Anonymous：仅可查看已发布的标签
    """
    query = select(Tag)
    
    # 构建业务筛选条件
    conditions = []
    
    if search:
        conditions.append(Tag.name.ilike(f"%{search}%"))
    
    if category_id:
        conditions.append(Tag.category_id == category_id)
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    else:
        # Regular User 或 Anonymous：仅可查看已发布的标签
        conditions.append(Tag.status == 'published')
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Tag.created_at.desc())
    
    # 计算总数（使用完全相同的 WHERE 条件）
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return list(tags), total
```

### 5.2. `get_categories_paginated` 方法

**改造前**：
```python
async def get_categories_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None
) -> Tuple[List[Category], int]:
    """分页获取分类列表"""
    query = select(Category)
    
    if search:
        query = query.where(Category.name.ilike(f"%{search}%"))
    
    query = query.order_by(Category.created_at.desc())
    
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return list(categories), total
```

**改造后**：
```python
async def get_categories_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Category], int]:
    """
    分页获取分类列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有分类
    - Regular User：仅可查看已发布的分类
    - Anonymous：仅可查看已发布的分类
    """
    query = select(Category)
    
    # 构建业务筛选条件
    conditions = []
    
    if search:
        conditions.append(Category.name.ilike(f"%{search}%"))
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    else:
        # Regular User 或 Anonymous：仅可查看已发布的分类
        conditions.append(Category.status == 'published')
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Category.created_at.desc())
    
    # 计算总数（使用完全相同的 WHERE 条件）
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return list(categories), total
```

### 5.3. `get_tag_sessions` 方法

**改造前**：
```python
async def get_tag_sessions(
    db: AsyncSession,
    tag_id: UUID,
    page: int = 1,
    size: int = 20
) -> Tuple[List[Session], int]:
    """获取标签的场次列表"""
    query = select(Session).join(
        SessionTag,
        Session.id == SessionTag.session_id
    )
    
    query = query.where(SessionTag.tag_id == tag_id)
    query = query.order_by(Session.created_at.desc())
    
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return list(sessions), total
```

**改造后**：
```python
async def get_tag_sessions(
    db: AsyncSession,
    tag_id: UUID,
    page: int = 1,
    size: int = 20,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[Session], int]:
    """
    获取标签的场次列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有场次
    - Regular User：仅可查看已发布的场次
    - Anonymous：仅可查看已发布的场次
    """
    query = select(Session).join(
        SessionTag,
        Session.id == SessionTag.session_id
    )
    
    # 构建业务筛选条件
    conditions = [SessionTag.tag_id == tag_id]
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    else:
        # Regular User 或 Anonymous：仅可查看已发布的场次
        conditions.append(Session.status == 'published')
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Session.created_at.desc())
    
    # 计算总数（使用完全相同的 WHERE 条件）
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return list(sessions), total
```

### 5.4. `get_session_tags` 方法

**改造前**：
```python
async def get_session_tags(
    db: AsyncSession,
    session_id: UUID
) -> List[Tag]:
    """获取场次的标签列表"""
    query = select(Tag).join(
        SessionTag,
        Tag.id == SessionTag.tag_id
    )
    
    query = query.where(SessionTag.session_id == session_id)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return list(tags)
```

**改造后**：
```python
async def get_session_tags(
    db: AsyncSession,
    session_id: UUID,
    # ← 新增权限参数
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> List[Tag]:
    """
    获取场次的标签列表（带权限过滤）
    
    权限过滤逻辑：
    - Admin：无过滤，可查看所有标签
    - Regular User：仅可查看已发布的标签
    - Anonymous：仅可查看已发布的标签
    """
    query = select(Tag).join(
        SessionTag,
        Tag.id == SessionTag.tag_id
    )
    
    # 构建业务筛选条件
    conditions = [SessionTag.session_id == session_id]
    
    # ← 新增：添加权限过滤条件
    if role in ['ADMIN', 'SUPERADMIN']:
        # Admin：无权限过滤
        pass
    else:
        # Regular User 或 Anonymous：仅可查看已发布的标签
        conditions.append(Tag.status == 'published')
    
    # 应用所有条件（业务 AND 权限）
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return list(tags)
```

---

## 6. 改造后检查清单

### 6.1. 方法签名检查

- [ ] `get_tags_paginated` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] `get_categories_paginated` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] `get_tag_sessions` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] `get_session_tags` 方法已添加 `current_user_id` 和 `role` 参数
- [ ] 所有参数类型定义正确（`Optional[UUID]` 和 `Optional[str]`）

### 6.2. 权限过滤实现检查

- [ ] 所有方法都在 SQL WHERE 条件中应用权限过滤
- [ ] 所有方法都禁止内存过滤
- [ ] Admin 查询无权限过滤
- [ ] Regular User 查询使用正确的权限过滤逻辑（`status == 'published'`）
- [ ] Anonymous 查询使用正确的权限过滤逻辑（`status == 'published'`）
- [ ] 业务筛选与权限过滤使用 AND 关系

### 6.3. 总数查询一致性检查

- [ ] 所有分页查询方法的 `count(*)` 查询都使用与数据查询完全相同的 WHERE 条件
- [ ] 所有方法都使用 `.subquery()` 方法包装查询
- [ ] 所有方法都使用 `select(func.count())` 计算总数

### 6.4. 无内存过滤检查

- [ ] 没有在 Python 内存中过滤数据
- [ ] 所有过滤都在 SQL 查询中完成
- [ ] 没有使用 `if tag.status == 'published':` 这样的循环判断

### 6.5. 代码风格一致性检查

- [ ] 所有方法使用相同的权限过滤逻辑结构
- [ ] 所有方法的注释格式一致
- [ ] 所有方法的返回值结构一致
- [ ] 所有方法的代码风格一致

---

## 7. 最终检查清单

### 7.1. 完整性检查

- [ ] 所有 4个需要改造的 CRUD 方法都已更新
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
@app.crud.content_management  # ← 使用 @app.crud.content_management 引用 CRUD 文件

# 改造时
from app.crud.content_management import (
    get_tags_paginated,
    get_categories_paginated,
    get_tag_sessions,
    get_session_tags,
    # ← 使用 @app.crud.content_management 引用所有需要改造的方法
)
```

### 8.2. 读取现有代码

**改造前必须读取现有代码**：
1. 使用 `@app/crud/content_management` 读取 `app/crud/content_management.py`
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

