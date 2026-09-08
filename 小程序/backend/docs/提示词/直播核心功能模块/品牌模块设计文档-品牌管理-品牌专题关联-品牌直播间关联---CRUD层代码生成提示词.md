# 品牌模块 - CRUD层代码生成提示词

**模块名称**: brand  
**功能模块名称**: 品牌模块设计文档-品牌管理-品牌专题关联-品牌直播间关联  
**目标文件**: `backend/live_core_service/app/crud/brand.py`  
**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和Python异步编程的资深后端开发工程师。你的任务是根据本提示词文档，生成品牌模块的CRUD层代码。

---

## 2. 核心要求

### 2.1. CRUD层职责

CRUD层是数据访问层，**仅负责数据库操作**：
- ✅ 执行数据库查询（SELECT、INSERT、UPDATE、DELETE）
- ✅ 处理数据库事务（通过AsyncSession）
- ✅ 记录数据库操作日志（INFO级别）
- ❌ 不负责业务逻辑（由Service层处理）
- ❌ 不负责权限检查（由Service层处理）
- ❌ 不负责响应构造（由Service层处理）

### 2.2. 关键原则

1. **异步编程**: 所有函数必须是`async def`
2. **类型提示**: 所有参数和返回值必须有类型提示
3. **事务管理**: 
   - 单表操作：使用单次`await db.commit()`
   - 批量操作：使用`async with db.begin()`显式事务
4. **异常处理**: 捕获`IntegrityError`并转换为`DatabaseIntegrityException`
5. **日志记录**: 每个CRUD操作记录INFO日志，UUID脱敏（只记录前8位）
6. **N+1问题防范**: 使用`selectinload`或`joinedload`预加载关联数据
7. **品牌模块特点**: 品牌信息是公开资源，无需SQL级权限过滤

---

## 3. Model字段摘要（来自实际代码）

### 3.1. Brand模型

**表名**: `brands`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 品牌ID（应用层生成） |
| `name` | String(150) | NOT NULL, UNIQUE | - | 品牌名称 |
| `slug` | String(150) | NULLABLE | NULL | URL友好标识符 |
| `logo_url` | String(512) | NULLABLE | NULL | 品牌Logo URL |
| `description` | Text | NULLABLE | NULL | 品牌描述 |
| `website_url` | String(255) | NULLABLE | NULL | 品牌官网链接 |
| `sort_order` | Integer | NOT NULL | 0 | 排序权重 |
| `is_active` | Boolean | NOT NULL | True | 是否启用（软删除） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间 |

**索引**: `idx_brands_sort_order`, `idx_brands_is_active`, `idx_brands_active_sort`

**唯一约束**: `name`字段全局唯一

---

### 3.2. BrandTopic模型

**表名**: `brand_topics`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `brand_id` | UUID | PRIMARY KEY, FK | - | 品牌ID |
| `topic_id` | UUID | PRIMARY KEY, FK | - | 专题ID |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (brand_id, topic_id)  
**外键**: `brand_id → brands.id`, `topic_id → topics.id`  
**删除策略**: 硬删除（ON DELETE CASCADE）

---

### 3.3. BrandRoom模型

**表名**: `brand_rooms`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `brand_id` | UUID | PRIMARY KEY, FK | - | 品牌ID |
| `room_id` | UUID | PRIMARY KEY, FK | - | 直播间ID |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |

**主键**: 复合主键 (brand_id, room_id)  
**外键**: `brand_id → brands.id`, `room_id → live_rooms.id`  
**删除策略**: 硬删除（ON DELETE CASCADE）

---

## 4. 需要生成的CRUD函数清单

### 4.1. Brands CRUD函数（8个）

#### 函数1: `get_brands`

**函数签名**:
```python
async def get_brands(
    db: AsyncSession,
    limit: int = 100,
    q: Optional[str] = None
) -> List[Brand]
```

**功能**: 获取品牌列表（公开接口）

**执行流程**:
1. 构建查询：`select(Brand).where(Brand.is_active == True).order_by(Brand.sort_order)`
2. 如果提供`q`参数，添加模糊搜索：`Brand.name.ilike(f'%{q}%')`
3. 应用limit（默认100，最大500）
4. 执行查询并返回结果
5. 记录日志：`logger.info(f"查询品牌列表，返回{len(brands)}条记录")`

---

#### 函数2: `get_brand_with_topics`

**函数签名**:
```python
async def get_brand_with_topics(
    db: AsyncSession,
    brand_id: UUID
) -> Tuple[Optional[Brand], List[Topic]]
```

**功能**: 获取品牌及其关联的专题列表

**N+1问题防治**:
```python
stmt = select(Brand).options(
    selectinload(Brand.topics).selectinload(BrandTopic.topic)
).where(Brand.id == brand_id, Brand.is_active == True)
```

**执行流程**:
1. 使用selectinload预加载关联的专题
2. 过滤：仅返回is_active=True的品牌和status='published'的专题
3. 如果品牌不存在或is_active=False，返回(None, [])
4. 返回：(品牌对象, 关联的专题列表)
5. 记录日志

---

#### 函数3: `create_brand`

**函数签名**:
```python
async def create_brand(
    db: AsyncSession,
    brand_in: BrandCreate
) -> Brand
```

**功能**: 创建品牌

**唯一性约束处理**:
- `Brand.name`具有唯一性约束
- 如果违反唯一性，数据库会抛出`IntegrityError`
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("品牌名称已存在")`

**执行流程**:
```python
try:
    brand = Brand(
        id=uuid.uuid4(),  # 🚨 应用层生成UUID
        name=brand_in.name,
        slug=brand_in.slug,
        logo_url=brand_in.logo_url,
        description=brand_in.description,
        website_url=brand_in.website_url,
        sort_order=brand_in.sort_order or 0,
        is_active=brand_in.is_active if brand_in.is_active is not None else True
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    logger.info(f"创建品牌成功: id={str(brand.id)[:8]}, name={brand.name}")
    return brand
except IntegrityError as e:
    await db.rollback()
    if "uq_brands_name" in str(e) or "unique constraint" in str(e).lower():
        raise DatabaseIntegrityException("品牌名称已存在")
    raise
except Exception as e:
    await db.rollback()
    logger.error(f"创建品牌失败: {type(e).__name__}")
    raise
```

---

#### 函数4: `get_brands_paginated`

**函数签名**:
```python
async def get_brands_paginated(
    db: AsyncSession,
    page: int,
    size: int,
    name: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[List[Brand], int]
```

**功能**: 获取品牌列表（管理员接口，分页）

**分页模式（两次查询）**:
```python
# 第一次查询：获取总数
count_stmt = select(func.count()).select_from(Brand)
if name:
    count_stmt = count_stmt.where(Brand.name.ilike(f'%{name}%'))
if is_active is not None:
    count_stmt = count_stmt.where(Brand.is_active == is_active)
total = await db.scalar(count_stmt)

# 第二次查询：获取当前页数据
stmt = select(Brand).order_by(Brand.sort_order)
if name:
    stmt = stmt.where(Brand.name.ilike(f'%{name}%'))
if is_active is not None:
    stmt = stmt.where(Brand.is_active == is_active)
stmt = stmt.offset((page - 1) * size).limit(size)
result = await db.execute(stmt)
brands = list(result.scalars().all())

return brands, total
```

---

#### 函数5: `get_brand_by_id`

**函数签名**:
```python
async def get_brand_by_id(
    db: AsyncSession,
    brand_id: UUID
) -> Optional[Brand]
```

**功能**: 根据ID获取品牌

**执行流程**:
1. 查询：`select(Brand).where(Brand.id == brand_id)`
2. 执行查询：`result = await db.execute(stmt)`
3. 返回：`result.scalar_one_or_none()`
4. 记录日志

---

#### 函数6: `update_brand`

**函数签名**:
```python
async def update_brand(
    db: AsyncSession,
    brand_id: UUID,
    brand_in: BrandUpdate
) -> Brand
```

**功能**: 更新品牌信息

**唯一性约束处理**:
- 如果更新`name`字段，可能违反唯一性约束
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("品牌名称已存在")`

**执行流程**:
```python
try:
    # 1. 查询品牌
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise NotFoundException("品牌不存在")
    
    # 2. 更新字段（部分更新）
    update_data = brand_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    
    # 3. 提交事务
    await db.commit()
    await db.refresh(brand)
    logger.info(f"更新品牌成功: id={str(brand.id)[:8]}")
    return brand
except IntegrityError as e:
    await db.rollback()
    if "uq_brands_name" in str(e) or "unique constraint" in str(e).lower():
        raise DatabaseIntegrityException("品牌名称已存在")
    raise
except Exception as e:
    await db.rollback()
    logger.error(f"更新品牌失败: {type(e).__name__}")
    raise
```

---

#### 函数7: `delete_brand`

**函数签名**:
```python
async def delete_brand(
    db: AsyncSession,
    brand_id: UUID,
    hard_delete: bool = False
) -> Brand
```

**功能**: 删除品牌

**软删除 vs 硬删除**:
- 软删除：设置`is_active=False`
- 硬删除：直接DELETE（需检查引用关系，由Service层处理）

**执行流程**:
```python
try:
    # 1. 查询品牌
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise NotFoundException("品牌不存在")
    
    # 2. 执行删除
    if hard_delete:
        await db.delete(brand)
        logger.warning(f"硬删除品牌: id={str(brand.id)[:8]}, name={brand.name}")
    else:
        brand.is_active = False
        logger.info(f"软删除品牌: id={str(brand.id)[:8]}, name={brand.name}")
    
    # 3. 提交事务
    await db.commit()
    await db.refresh(brand) if not hard_delete else None
    return brand
except Exception as e:
    await db.rollback()
    logger.error(f"删除品牌失败: {type(e).__name__}")
    raise
```

---

#### 函数8: `check_brand_references`

**函数签名**:
```python
async def check_brand_references(
    db: AsyncSession,
    brand_id: UUID
) -> Tuple[int, int]
```

**功能**: 检查品牌被引用的情况

**返回**: (专题引用数, 直播间引用数)

**执行流程**:
```python
# 1. 查询专题引用数
topic_count_stmt = select(func.count()).select_from(BrandTopic).where(
    BrandTopic.brand_id == brand_id
)
topic_count = await db.scalar(topic_count_stmt)

# 2. 查询直播间引用数
room_count_stmt = select(func.count()).select_from(BrandRoom).where(
    BrandRoom.brand_id == brand_id
)
room_count = await db.scalar(room_count_stmt)

logger.info(f"品牌引用检查: id={str(brand_id)[:8]}, 专题:{topic_count}, 直播间:{room_count}")
return topic_count, room_count
```

---

### 4.2. Brand_Topics CRUD函数（3个）

#### 函数9: `batch_add_brand_topics`

**函数签名**:
```python
async def batch_add_brand_topics(
    db: AsyncSession,
    brand_id: UUID,
    topic_ids: List[UUID]
) -> int
```

**功能**: 批量添加品牌-专题关联

**幂等性保证**: 使用`INSERT ... ON CONFLICT DO NOTHING`

**执行流程**:
```python
try:
    added_count = 0
    for topic_id in topic_ids:
        # 使用insert().on_conflict_do_nothing()保证幂等性
        stmt = insert(BrandTopic).values(
            brand_id=brand_id,
            topic_id=topic_id
        ).on_conflict_do_nothing(
            index_elements=['brand_id', 'topic_id']
        )
        result = await db.execute(stmt)
        if result.rowcount > 0:
            added_count += 1
    
    await db.commit()
    logger.info(f"批量添加品牌专题关联: brand_id={str(brand_id)[:8]}, 新增{added_count}条")
    return added_count
except Exception as e:
    await db.rollback()
    logger.error(f"批量添加品牌专题关联失败: {type(e).__name__}")
    raise
```

---

#### 函数10: `delete_brand_topic`

**函数签名**:
```python
async def delete_brand_topic(
    db: AsyncSession,
    brand_id: UUID,
    topic_id: UUID
) -> bool
```

**功能**: 删除单个品牌-专题关联（硬删除）

**执行流程**:
```python
try:
    stmt = delete(BrandTopic).where(
        BrandTopic.brand_id == brand_id,
        BrandTopic.topic_id == topic_id
    )
    result = await db.execute(stmt)
    await db.commit()
    
    success = result.rowcount > 0
    if success:
        logger.info(f"删除品牌专题关联: brand_id={str(brand_id)[:8]}, topic_id={str(topic_id)[:8]}")
    else:
        logger.warning(f"品牌专题关联不存在: brand_id={str(brand_id)[:8]}, topic_id={str(topic_id)[:8]}")
    
    return success
except Exception as e:
    await db.rollback()
    logger.error(f"删除品牌专题关联失败: {type(e).__name__}")
    raise
```

---

#### 函数11: `get_brand_topics_paginated`

**函数签名**:
```python
async def get_brand_topics_paginated(
    db: AsyncSession,
    brand_id: UUID,
    page: int,
    size: int
) -> Tuple[List[dict], int]
```

**功能**: 获取品牌关联的专题列表（管理员接口，分页）

**N+1问题防治**: 使用JOIN查询

**执行流程**:
```python
# 第一次查询：获取总数
count_stmt = select(func.count()).select_from(BrandTopic).where(
    BrandTopic.brand_id == brand_id
)
total = await db.scalar(count_stmt)

# 第二次查询：获取当前页数据（联表查询）
stmt = (
    select(
        Topic.id.label('topic_id'),
        Topic.title.label('topic_title'),
        Topic.status.label('topic_status'),
        BrandTopic.created_at.label('associated_at')
    )
    .select_from(BrandTopic)
    .join(Topic, BrandTopic.topic_id == Topic.id)
    .where(BrandTopic.brand_id == brand_id)
    .order_by(BrandTopic.created_at.desc())
    .offset((page - 1) * size)
    .limit(size)
)

result = await db.execute(stmt)
topics = [dict(row._mapping) for row in result]

logger.info(f"查询品牌关联专题: brand_id={str(brand_id)[:8]}, 返回{len(topics)}条")
return topics, total
```

---

### 4.3. Brand_Rooms CRUD函数（3个）

#### 函数12: `bind_room_brands`

**函数签名**:
```python
async def bind_room_brands(
    db: AsyncSession,
    room_id: UUID,
    brand_ids: List[UUID]
) -> List[UUID]
```

**功能**: 为直播间绑定品牌（全量替换策略）

**事务处理**: 使用`async with db.begin()`显式事务

**执行流程**:
```python
try:
    async with db.begin():  # 显式事务
        # 1. 删除该直播间的所有旧关联
        delete_stmt = delete(BrandRoom).where(BrandRoom.room_id == room_id)
        await db.execute(delete_stmt)
        
        # 2. 批量插入新关联
        if brand_ids:
            new_relations = [
                BrandRoom(brand_id=bid, room_id=room_id)
                for bid in brand_ids
            ]
            db.add_all(new_relations)
        
        # async with 块退出时自动commit
    
    logger.info(f"绑定直播间品牌: room_id={str(room_id)[:8]}, 品牌数:{len(brand_ids)}")
    return brand_ids
except Exception as e:
    await db.rollback()
    logger.error(f"绑定直播间品牌失败: {type(e).__name__}")
    raise
```

---

#### 函数13: `get_room_brands`

**函数签名**:
```python
async def get_room_brands(
    db: AsyncSession,
    room_id: UUID
) -> List[Brand]
```

**功能**: 获取直播间绑定的品牌列表

**N+1问题防治**: 使用JOIN查询

**执行流程**:
```python
stmt = (
    select(Brand)
    .select_from(BrandRoom)
    .join(Brand, BrandRoom.brand_id == Brand.id)
    .where(
        BrandRoom.room_id == room_id,
        Brand.is_active == True
    )
    .order_by(Brand.sort_order)
)

result = await db.execute(stmt)
brands = list(result.scalars().all())

logger.info(f"查询直播间品牌: room_id={str(room_id)[:8]}, 返回{len(brands)}条")
return brands
```

---

#### 函数14: `get_room_brands_for_tab`

**函数签名**:
```python
async def get_room_brands_for_tab(
    db: AsyncSession,
    room_id: UUID
) -> List[Brand]
```

**功能**: 获取直播间品牌Tab内容（公开接口）

**说明**: 与`get_room_brands`实现相同，但命名明确用于前端展示

**执行流程**: 与`get_room_brands`相同

---

## 5. 关键实现规范

### 5.1. 异常处理规范

**强制模板**:
```python
try:
    # 数据库操作
    ...
    await db.commit()
    return result
except IntegrityError as e:
    await db.rollback()
    # 识别具体的约束违反类型
    if "unique constraint" in str(e).lower():
        raise DatabaseIntegrityException("资源已存在")
    elif "foreign key constraint" in str(e).lower():
        raise DatabaseIntegrityException("关联的资源不存在")
    raise
except Exception as e:
    await db.rollback()
    logger.error(f"操作失败: {type(e).__name__}")
    raise
```

### 5.2. N+1问题防治

**使用selectinload预加载**:
```python
from sqlalchemy.orm import selectinload

stmt = select(Brand).options(
    selectinload(Brand.topics)
).where(Brand.id == brand_id)
```

### 5.3. 分页模式（两次查询）

**强制模式**:
```python
# 第一次查询：COUNT
count_stmt = select(func.count()).select_from(Brand).where(...)
total = await db.scalar(count_stmt)

# 第二次查询：数据
stmt = select(Brand).where(...).offset(...).limit(...)
result = await db.execute(stmt)
brands = list(result.scalars().all())

return brands, total
```

### 5.4. 事务处理

**单表操作**:
```python
db.add(brand)
await db.commit()
await db.refresh(brand)
```

**批量操作（显式事务）**:
```python
async with db.begin():
    # 多个操作
    await db.execute(delete_stmt)
    db.add_all(new_items)
    # 自动commit
```

### 5.5. 日志记录

**UUID脱敏**:
```python
logger.info(f"创建品牌: id={str(brand_id)[:8]}, name={brand.name}")
```

---

## 6. 导入语句

```python
import uuid
import logging
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, func, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.brand import Brand, BrandTopic, BrandRoom
from app.schemas.brand import BrandCreate, BrandUpdate
from app.core.exceptions import (
    NotFoundException,
    DatabaseIntegrityException
)

logger = logging.getLogger(__name__)
```

---

## 7. 增量开发模式

**🚨 重要**：如果`backend/live_core_service/app/crud/brand.py`文件已存在：
1. **检测现有代码**：读取文件内容，识别已实现的函数
2. **仅生成缺失部分**：只生成文件中不存在的函数
3. **最小化修改**：不修改已有函数的实现
4. **追加模式**：将新函数追加到文件末尾

如果文件不存在，则生成完整的CRUD层代码文件。

---

## 8. 交付物

请生成完整的`backend/live_core_service/app/crud/brand.py`文件，包含：
1. 完整的导入语句
2. logger初始化
3. 上述14个CRUD函数的完整实现
4. 每个函数包含完整的异常处理和日志记录
5. 遵循所有架构规范（异常处理、N+1防治、分页、事务处理）

**代码风格**:
- 使用4空格缩进
- 函数之间空2行
- 注释使用中文
- 类型提示完整

---

**生成完成时间**: 2026-01-18T12:45:00Z
