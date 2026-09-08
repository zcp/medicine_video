# 内容管理模块 - CRUD层代码生成提示词

**模块名称**: content_management  
**功能模块名称**: 内容管理模块设计文档-标签-分类-场次标签关联  
**目标文件**: `backend/live_core_service/app/crud/content_management.py`  
**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和Python异步编程的资深后端开发工程师。你的任务是根据本提示词文档，生成内容管理模块的CRUD层代码。

---

## 2. 核心要求

### 2.1. CRUD层职责

CRUD层是数据访问层，**仅负责数据库操作**：
- ✅ 执行数据库查询（SELECT、INSERT、UPDATE、DELETE）
- ✅ 处理数据库事务（通过AsyncSession）
- ✅ 应用SQL级权限过滤（where条件）
- ✅ 记录数据库操作日志（INFO级别）
- ❌ 不负责业务逻辑（由Service层处理）
- ❌ 不负责权限检查（由Service层处理）
- ❌ 不负责响应构造（由Service层处理）

### 2.2. 关键原则

1. **异步编程**: 所有函数必须是`async def`
2. **类型提示**: 所有参数和返回值必须有类型提示
3. **事务管理**: 使用`AsyncSession`，不手动commit（由Service层控制）
4. **异常处理**: 捕获`IntegrityError`并转换为`DatabaseIntegrityException`
5. **日志记录**: 每个CRUD操作记录INFO日志，UUID脱敏（只记录前8位）
6. **N+1问题防范**: 使用`selectinload`或`joinedload`预加载关联数据
7. **SQL级权限过滤**: 在查询时应用where条件（如`is_active=True`）

---

## 3. Model字段摘要（来自实际代码）

### 3.1. Tag模型

**表名**: `tags`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 标签ID |
| `name` | String(80) | NOT NULL, UNIQUE | - | 标签名称 |
| `slug` | String(100) | NULLABLE | NULL | URL友好标识符 |
| `description` | Text | NULLABLE | NULL | 标签描述 |
| `is_active` | Boolean | NOT NULL | True | 是否启用 |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间 |

**索引**: `idx_tags_name`, `idx_tags_is_active`

---

### 3.2. Category模型

**表名**: `categories`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 分类ID |
| `name` | String(100) | NOT NULL, UNIQUE | - | 分类名称 |
| `slug` | String(120) | NULLABLE | NULL | URL友好标识符 |
| `icon` | String(255) | NULLABLE | NULL | 图标 |
| `description` | Text | NULLABLE | NULL | 分类描述 |
| `sort_order` | Integer | NOT NULL | 0 | 排序权重 |
| `is_active` | Boolean | NOT NULL | True | 是否启用 |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间 |

**索引**: `idx_categories_sort_order`, `idx_categories_is_active`

---

### 3.3. SessionTag模型

**表名**: `session_tags`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `session_id` | UUID | PRIMARY KEY, FK | - | 场次ID |
| `tag_id` | UUID | PRIMARY KEY, FK | - | 标签ID |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (session_id, tag_id)

---

## 4. 需要生成的CRUD函数清单

### 4.1. Tags CRUD函数（4个）

#### 函数1: `get_tags`

**函数签名**:
```python
async def get_tags(
    db: AsyncSession,
    is_active: Optional[bool],
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> List[Tag]
```

**功能**: 获取标签列表

**SQL级权限过滤**:
- 如果`role not in ['ADMIN', 'SUPERADMIN']`，则自动添加`where is_active=True`（🚨 必须使用大写）
- 如果`is_active`参数不为None，则添加`where is_active=is_active`

**执行流程**:
1. 构建查询：`select(Tag).order_by(Tag.created_at.desc())`
2. 应用权限过滤（where条件）
3. 执行查询：`result = await db.execute(query)`
4. 返回结果：`result.scalars().all()`
5. 记录日志：`logger.info(f"查询标签列表，返回{len(tags)}条记录")`

---

#### 函数2: `create_tag`

**函数签名**:
```python
async def create_tag(db: AsyncSession, tag_data: TagCreate) -> Tag
```

**功能**: 创建标签

**唯一性约束处理**:
- `Tag.name`具有唯一性约束
- 如果违反唯一性，数据库会抛出`IntegrityError`
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("标签名称已存在")`

**执行流程**:
1. 创建Tag实例：`tag = Tag(**tag_data.model_dump())`
2. 添加到会话：`db.add(tag)`
3. Flush（不commit）：`await db.flush()` - 触发唯一性检查
4. 刷新对象：`await db.refresh(tag)` - 获取数据库生成的时间戳
5. 记录日志：`logger.info(f"创建标签成功: id={str(tag.id)[:8]}, name={tag.name}")`
6. 返回tag对象
7. 异常处理：
   ```python
   try:
       # ... 执行创建
   except IntegrityError as e:
       await db.rollback()
       logger.error(f"创建标签失败（唯一性冲突）: {str(e)}")
       raise DatabaseIntegrityException("标签名称已存在")
   except Exception as e:
       await db.rollback()
       logger.error(f"创建标签失败（数据库错误）: {str(e)}")
       raise DatabaseOperationException("创建标签时发生数据库错误")
   ```

---

#### 函数3: `update_tag`

**函数签名**:
```python
async def update_tag(
    db: AsyncSession,
    tag_id: UUID,
    tag_data: TagUpdate
) -> Optional[Tag]
```

**功能**: 更新标签（部分更新）

**唯一性约束处理**:
- 如果更新了`name`字段，可能违反唯一性约束
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("标签名称已存在")`

**执行流程**:
1. 查询标签：`query = select(Tag).where(Tag.id == tag_id)`
2. 执行查询：`result = await db.execute(query)`
3. 获取标签：`tag = result.scalar_one_or_none()`
4. 如果tag为None，返回None（由Service层处理404）
5. 部分更新：
   ```python
   update_data = tag_data.model_dump(exclude_unset=True)
   for field, value in update_data.items():
       setattr(tag, field, value)
   ```
6. Flush：`await db.flush()`
7. 刷新对象：`await db.refresh(tag)`
8. 记录日志：`logger.info(f"更新标签成功: id={str(tag_id)[:8]}")`
9. 返回tag对象
10. 异常处理（同create_tag）

---

#### 函数4: `delete_tag`

**函数签名**:
```python
async def delete_tag(db: AsyncSession, tag_id: UUID) -> bool
```

**功能**: 删除标签（软删除，设置`is_active=False`）

**🚨 异常处理要求（强制）**：
- **必须**使用`try-except`块包裹所有数据库操作
- **必须**捕获通用`Exception`并执行`await db.rollback()`
- **必须**记录错误日志并抛出`DatabaseOperationException`

**执行流程**:
1. 进入`try`块
2. 查询标签：`query = select(Tag).where(Tag.id == tag_id)`
3. 执行查询：`result = await db.execute(query)`
4. 获取标签：`tag = result.scalar_one_or_none()`
5. 如果tag为None，返回False
6. 软删除：`tag.is_active = False`
7. Flush：`await db.flush()`
8. 记录日志：`logger.info(f"软删除标签成功: id={str(tag_id)[:8]}")`
9. 返回True
10. **异常处理**：
    ```python
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除标签失败（数据库错误）: id={str(tag_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("软删除标签时发生数据库错误")
    ```

---

### 4.2. Categories CRUD函数（6个）

#### 函数5: `get_categories`

**函数签名**:
```python
async def get_categories(
    db: AsyncSession,
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> List[Category]
```

**功能**: 获取分类列表（公开接口，按sort_order排序，只返回is_active=True）

**SQL级权限过滤**:
- **强制**过滤：`where is_active=True`（公开接口）
- 按`sort_order ASC`排序

**执行流程**:
1. 构建查询：`select(Category).where(Category.is_active == True).order_by(Category.sort_order.asc())`
2. 执行查询：`result = await db.execute(query)`
3. 返回结果：`result.scalars().all()`
4. 记录日志：`logger.info(f"查询分类列表（公开），返回{len(categories)}条记录")`

---

#### 函数6: `get_categories_paginated`

**函数签名**:
```python
async def get_categories_paginated(
    db: AsyncSession,
    page: int,
    size: int,
    is_active: Optional[bool],
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> Tuple[List[Category], int]
```

**功能**: 获取分类列表（管理员接口，分页，支持按is_active过滤）

**SQL级权限过滤**:
- 如果`is_active`参数不为None，则添加`where is_active=is_active`
- 如果`role not in ['ADMIN', 'SUPERADMIN']`，则**强制**添加`where is_active=True`（防御性编程，🚨 必须使用大写）

**分页逻辑**:
- offset: `(page - 1) * size`
- limit: `size`

**执行流程**:
1. 构建查询：`select(Category).order_by(Category.sort_order.asc())`
2. 应用权限过滤（where条件）
3. 执行总数查询：`count_query = select(func.count()).select_from(query.subquery())`
4. 执行分页查询：`query.offset((page - 1) * size).limit(size)`
5. 返回：`(categories, total)`
6. 记录日志：`logger.info(f"查询分类列表（Admin），page={page}, size={size}, total={total}")`

---

#### 函数7: `create_category`

**函数签名**:
```python
async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category
```

**功能**: 创建分类

**唯一性约束处理**: 同`create_tag`

**执行流程**: 同`create_tag`（替换Tag为Category）

---

#### 函数8: `update_category`

**函数签名**:
```python
async def update_category(
    db: AsyncSession,
    category_id: UUID,
    category_data: CategoryUpdate
) -> Optional[Category]
```

**功能**: 更新分类

**唯一性约束处理**: 同`update_tag`

**执行流程**: 同`update_tag`（替换Tag为Category，tag_id为category_id）

---

#### 函数9: `delete_category`

**函数签名**:
```python
async def delete_category(db: AsyncSession, category_id: UUID) -> bool
```

**功能**: 删除分类（软删除，设置`is_active=False`）

**🚨 异常处理要求（强制）**：
- **必须**使用`try-except`块包裹所有数据库操作
- **必须**捕获通用`Exception`并执行`await db.rollback()`
- **必须**记录错误日志并抛出`DatabaseOperationException`

**执行流程**:
1. 进入`try`块
2. 查询分类：`query = select(Category).where(Category.id == category_id)`
3. 执行查询：`result = await db.execute(query)`
4. 获取分类：`category = result.scalar_one_or_none()`
5. 如果category为None，返回False
6. 软删除：`category.is_active = False`
7. Flush：`await db.flush()`
8. 记录日志：`logger.info(f"软删除分类成功: id={str(category_id)[:8]}")`
9. 返回True
10. **异常处理**：
    ```python
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除分类失败（数据库错误）: id={str(category_id)[:8]}, error={str(e)}")
        raise DatabaseOperationException("软删除分类时发生数据库错误")
    ```

---

#### 函数10: `get_category_by_id`

**函数签名**:
```python
async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Optional[Category]
```

**功能**: 根据ID获取分类（用于更新和删除时的验证）

**执行流程**:
1. 查询分类：`query = select(Category).where(Category.id == category_id)`
2. 执行查询：`result = await db.execute(query)`
3. 返回：`result.scalar_one_or_none()`
4. 记录日志：`logger.info(f"根据ID查询分类: id={str(category_id)[:8]}")`

---

### 4.3. Session_Tags CRUD函数（4个）

#### 函数11: `set_session_tags`

**函数签名**:
```python
async def set_session_tags(
    db: AsyncSession,
    session_id: UUID,
    tag_ids: List[UUID],
    mode: str
) -> List[Tag]
```

**功能**: 为场次设置标签

**模式处理**:
- `mode="replace"`: 先删除所有现有关联，再创建新关联
- `mode="append"`: 只追加新关联（如已存在则忽略）

**执行流程**:

**replace模式**:
1. 删除现有关联：
   ```python
   delete_query = delete(SessionTag).where(SessionTag.session_id == session_id)
   await db.execute(delete_query)
   await db.flush()
   ```
2. 创建新关联：
   ```python
   for tag_id in tag_ids:
       session_tag = SessionTag(session_id=session_id, tag_id=tag_id)
       db.add(session_tag)
   await db.flush()
   ```
3. 查询标签列表（用于返回）：
   ```python
   query = select(Tag).where(Tag.id.in_(tag_ids))
   result = await db.execute(query)
   tags = result.scalars().all()
   ```
4. 记录日志：`logger.info(f"为场次设置标签（replace）: session_id={str(session_id)[:8]}, tag_count={len(tag_ids)}")`
5. 返回tags

**append模式**:
1. 查询现有关联：
   ```python
   query = select(SessionTag.tag_id).where(SessionTag.session_id == session_id)
   result = await db.execute(query)
   existing_tag_ids = set(result.scalars().all())
   ```
2. 过滤新标签（排除已存在的）：
   ```python
   new_tag_ids = [tag_id for tag_id in tag_ids if tag_id not in existing_tag_ids]
   ```
3. 创建新关联（同replace模式步骤2）
4. 查询所有标签列表（包括已存在的）：
   ```python
   all_tag_ids = list(existing_tag_ids) + new_tag_ids
   query = select(Tag).where(Tag.id.in_(all_tag_ids))
   result = await db.execute(query)
   tags = result.scalars().all()
   ```
5. 记录日志：`logger.info(f"为场次追加标签（append）: session_id={str(session_id)[:8]}, new_tag_count={len(new_tag_ids)}")`
6. 返回tags

---

#### 函数12: `get_tags_by_session_id`

**函数签名**:
```python
async def get_tags_by_session_id(db: AsyncSession, session_id: UUID) -> List[Tag]
```

**功能**: 根据场次ID获取标签列表

**SQL级权限过滤**:
- **强制**过滤：`where Tag.is_active=True`（只返回启用的标签）

**执行流程**:
1. 构建JOIN查询：
   ```python
   query = (
       select(Tag)
       .join(SessionTag, Tag.id == SessionTag.tag_id)
       .where(SessionTag.session_id == session_id)
       .where(Tag.is_active == True)
       .order_by(Tag.name.asc())
   )
   ```
2. 执行查询：`result = await db.execute(query)`
3. 返回：`result.scalars().all()`
4. 记录日志：`logger.info(f"查询场次标签: session_id={str(session_id)[:8]}, tag_count={len(tags)}")`

---

#### 函数13: `get_sessions_by_tags`

**函数签名**:
```python
async def get_sessions_by_tags(
    db: AsyncSession,
    tag_ids: List[UUID],
    match_all: bool
) -> List[UUID]
```

**功能**: 根据标签查询场次ID列表

**匹配模式**:
- `match_all=True`: AND逻辑（场次必须包含所有指定标签）
- `match_all=False`: OR逻辑（场次包含任一指定标签即可）

**执行流程**:

**OR逻辑（match_all=False）**:
1. 构建查询：
   ```python
   query = (
       select(SessionTag.session_id)
       .where(SessionTag.tag_id.in_(tag_ids))
       .distinct()
   )
   ```
2. 执行查询：`result = await db.execute(query)`
3. 返回：`result.scalars().all()`

**AND逻辑（match_all=True）**:
1. 使用GROUP BY和HAVING：
   ```python
   query = (
       select(SessionTag.session_id)
       .where(SessionTag.tag_id.in_(tag_ids))
       .group_by(SessionTag.session_id)
       .having(func.count(SessionTag.tag_id) == len(tag_ids))
   )
   ```
2. 执行查询：`result = await db.execute(query)`
3. 返回：`result.scalars().all()`

4. 记录日志：`logger.info(f"根据标签查询场次: tag_count={len(tag_ids)}, match_all={match_all}, session_count={len(session_ids)}")`

---

#### 函数14: `remove_session_tag`

**函数签名**:
```python
async def remove_session_tag(
    db: AsyncSession,
    session_id: UUID,
    tag_id: UUID
) -> bool
```

**功能**: 删除场次与标签的关联（硬删除）

**执行流程**:
1. 构建DELETE语句：
   ```python
   delete_query = delete(SessionTag).where(
       SessionTag.session_id == session_id,
       SessionTag.tag_id == tag_id
   )
   ```
2. 执行删除：`result = await db.execute(delete_query)`
3. Flush：`await db.flush()`
4. 检查是否删除了记录：`deleted_count = result.rowcount`
5. 记录日志：`logger.info(f"删除场次标签关联: session_id={str(session_id)[:8]}, tag_id={str(tag_id)[:8]}, deleted={deleted_count > 0}")`
6. 返回：`deleted_count > 0`

---

## 5. 导入清单

**必需导入**:
```python
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.content_management import Tag, Category, SessionTag
from app.schemas.content_management import TagCreate, TagUpdate, CategoryCreate, CategoryUpdate
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)
```

---

## 6. 文件结构模板

```python
"""
内容管理模块的CRUD层
负责Tags、Categories、Session_Tags的数据访问
"""
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.content_management import Tag, Category, SessionTag
from app.schemas.content_management import TagCreate, TagUpdate, CategoryCreate, CategoryUpdate
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)


# ============================================================================
# Tags CRUD Functions
# ============================================================================

async def get_tags(...) -> List[Tag]:
    """获取标签列表"""
    # 实现...


async def create_tag(...) -> Tag:
    """创建标签"""
    # 实现...


# ... 其他函数


# ============================================================================
# Categories CRUD Functions
# ============================================================================

# ... 实现


# ============================================================================
# Session_Tags CRUD Functions
# ============================================================================

# ... 实现
```

---

## 7. 关键约束和注意事项

1. **唯一性约束处理**: Tag.name和Category.name具有唯一性约束，必须捕获IntegrityError
2. **软删除 vs 硬删除**: Tag和Category使用软删除（is_active=False），SessionTag使用硬删除
3. **SQL级权限过滤**: 在查询时应用where条件，不在Service层过滤
4. **UUID脱敏**: 日志中UUID只记录前8位
5. **异步操作**: 所有数据库操作使用async/await
6. **不手动commit**: 由Service层控制事务提交
7. **分页查询**: 使用offset/limit，返回(items, total)
8. **JOIN查询**: 使用SQLAlchemy的join语法，不使用原生SQL

### 7.1. 🚨 [强制要求] 异常处理（最高优先级）

**所有写操作（create, update, remove）必须包含完整的异常处理**：

1. **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException`，并执行`await db.rollback()`
2. **必须**捕获通用`Exception`，执行`await db.rollback()`并记录错误日志
3. **必须**在try块中包含所有数据库操作

**完整示例**：
```python
async def create_tag(db: AsyncSession, tag_data: TagCreate) -> Tag:
    """创建标签"""
    try:
        # 创建Tag实例
        tag = Tag(**tag_data.model_dump())
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
        logger.info(f"创建标签成功: id={str(tag.id)[:8]}, name={tag.name}")
        return tag
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建标签失败（唯一性冲突）: {str(e)}")
        raise DatabaseIntegrityException("标签名称已存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建标签失败（数据库错误）: {str(e)}")
        raise DatabaseOperationException("创建标签时发生数据库错误")
```

### 7.2. 🚨 [强制要求] N+1问题防治

**对于需要加载关系的查询，必须使用`selectinload`或`joinedload`预加载关系**：

1. **一对多关系**：使用`joinedload`时，**必须**在`.scalars()`后调用`.unique()`去重
2. **多对一关系**：使用`joinedload`时，**不需要**`.unique()`
3. **任意关系**：使用`selectinload`时，**不需要**`.unique()`

**示例**：
```python
# 一对多关系（需要.unique()）
stmt = select(Tag).options(
    joinedload(Tag.session_tags)
).where(Tag.is_active == True)
result = await db.execute(stmt)
tags = result.scalars().unique().all()  # ← 必须使用.unique()

# 多对一关系（不需要.unique()）
stmt = select(SessionTag).options(
    joinedload(SessionTag.tag)
).where(SessionTag.session_id == session_id)
result = await db.execute(stmt)
session_tags = result.scalars().all()  # ← 不需要.unique()
```

### 7.3. 🚨 [强制要求] 分页模式

**分页查询必须通过两次查询实现**：

1. **总数查询**：`select(func.count()).select_from(query.subquery())`
2. **数据列表查询**：`query.offset((page - 1) * size).limit(size)`

**示例**：
```python
async def get_categories_paginated(...) -> Tuple[List[Category], int]:
    # 构建基础查询
    query = select(Category).order_by(Category.sort_order.asc())
    
    # 应用权限过滤
    if role not in ['ADMIN', 'SUPERADMIN']:
        query = query.where(Category.is_active == True)
    
    # 执行总数查询
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 执行分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return (list(categories), total)
```

### 7.4. 🚨 [强制要求] SQL级权限过滤中的角色检查

**必须使用大写进行角色检查**：

- **必须**使用：`if role not in ['ADMIN', 'SUPERADMIN']:`
- **禁止**使用：`if role not in ['admin', 'superadmin']:` ❌
- **原因**：API层已经调用`.upper()`转换role为大写，CRUD层必须使用大写进行比较

**示例**：
```python
# ✅ 正确
if role not in ['ADMIN', 'SUPERADMIN']:
    conditions.append(Category.is_active == True)

# ❌ 错误
if role not in ['admin', 'superadmin']:  # ❌ 使用小写
    conditions.append(Category.is_active == True)
```

### 7.5. 🚨 [强制要求] 数据库初始化脚本更新（必须执行）

**生成模型代码后，必须同时更新数据库初始化脚本**：

**需要更新的模型类**：
- `Tag`
- `Category`
- `SessionTag`

**更新 `app/models/__init__.py`**（如果使用 `init_db.py`）：

**操作步骤**：
1. 检查文件末尾是否已有 `from .content_management import ...` 导入
2. 如果不存在，在文件末尾追加（保持空行和注释格式）：
```python
# 内容管理模块模型（新增）
from .content_management import Tag, Category, SessionTag
```
3. **不要修改**文件中的任何现有导入语句

**或更新 `app/scripts/create_tables.py`**（如果使用显式导入方式）：

**操作步骤**：
1. 在 `init_db()` 函数中找到现有的模型导入区域
2. 检查是否已有 `from ..models.content_management import ...` 导入
3. 如果不存在，在现有导入语句之后追加：
```python
        # 导入内容管理模块模型（新增）
        from ..models.content_management import Tag, Category, SessionTag
```
4. **保持相同的缩进级别**（与现有导入一致）
5. **不要修改**函数中的任何现有的导入语句或代码

**验证方法**：
运行数据库初始化脚本后，检查日志输出，确认新表出现在创建列表中。

---

## 8. 执行指引

### 8.1. 生成要求

1. **按顺序生成**: 先Tags，再Categories，最后Session_Tags
2. **添加docstring**: 每个函数添加详细的docstring
3. **类型提示**: 所有参数和返回值必须有类型提示
4. **异常处理**: 捕获IntegrityError并转换为DatabaseIntegrityException
5. **日志记录**: 每个函数记录INFO日志

### 8.2. 验证要求

生成代码后，请验证：
- ✅ 所有14个函数都已生成
- ✅ 所有函数签名与本文档一致
- ✅ 所有SQL级权限过滤逻辑正确
- ✅ 所有唯一性约束处理正确
- ✅ 所有日志记录包含UUID脱敏

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本，基于模块特定母版生成


