# 首页与搜索模块 - CRUD层代码生成提示词 (Phase1: 焦点图CRUD)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase1 - 焦点图CRUD  
**目标文件**: `backend/live_core_service/app/crud/homepage_search.py`  
**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（本文档）**: 焦点图CRUD - 基础的增删改查操作
- **Phase2（待生成）**: 首页API - 复杂的多表JOIN和业务逻辑
- **Phase3（待生成）**: 搜索API - 跨多个表的全文搜索

---

## 1. 角色定义

你是一名精通Clean Architecture和Python异步编程的资深后端开发工程师。你的任务是根据本提示词文档，生成首页与搜索模块Phase1（焦点图CRUD）的CRUD层代码。

---

## 2. 核心要求

### 2.1. CRUD层职责

CRUD层是数据访问层，**仅负责数据库操作**：
- ✅ 执行数据库查询（SELECT、INSERT、UPDATE、DELETE）
- ✅ 处理数据库事务（通过AsyncSession）
- ✅ 记录数据库操作日志（INFO级别）
- ❌ 不负责业务逻辑（由Service层处理）
- ❌ 不负责权限检查（由Service层处理）
- ❌ 不负责响应构造（由API层处理）

### 2.2. 关键原则

1. **异步编程**: 所有函数必须是`async def`
2. **类型提示**: 所有参数和返回值必须有类型提示
3. **事务管理**: 
   - 单表操作：使用单次`await db.commit()`
   - 批量操作：使用`async with db.begin()`显式事务
4. **异常处理**: 捕获`IntegrityError`并转换为业务异常
5. **日志记录**: 每个CRUD操作记录INFO日志，UUID脱敏（只记录前8位）
6. **焦点图特点**: 焦点图是公开资源，但管理员可以看到所有状态（包括未启用和未到上线时间的）

---

## 3. Model字段摘要（来自实际代码）

### 3.1. FeaturedContent模型

**文件**: `backend/live_core_service/app/models/homepage_search.py`

**表名**: `featured_content`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 焦点图ID（应用层生成） |
| `title` | String(255) | NOT NULL | - | 焦点图标题 |
| `subtitle` | String(512) | NULLABLE | NULL | 焦点图副标题 |
| `image_url` | String(512) | NOT NULL | - | 焦点图图片URL |
| `target_type` | String(50) | NULLABLE | NULL | 目标类型（room/session/topic/brand/external） |
| `target_id` | UUID | NULLABLE | NULL | 目标资源ID（应用层关联，无外键） |
| `target_url` | String(512) | NULLABLE | NULL | 外部链接（优先级高于target_id） |
| `sort_order` | Integer | NOT NULL | 0 | 排序权重（数字越小越靠前） |
| `is_active` | Boolean | NOT NULL | True | 是否启用（软删除标识） |
| `start_at` | TIMESTAMP(TZ) | NULLABLE | NULL | 上线时间（NULL表示立即上线） |
| `end_at` | TIMESTAMP(TZ) | NULLABLE | NULL | 下线时间（NULL表示永久有效） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间（自动更新） |

**索引**: 
- `idx_featured_content_active_sort` (is_active, sort_order)
- `idx_featured_content_schedule` (start_at, end_at)

**特殊说明**:
- `target_id`字段**不设置外键**（因为target_type可能指向不同的表）
- 通过应用层验证保证引用完整性

---

## 4. 需要生成的CRUD函数清单

### 4.1. Featured Content CRUD函数（6个）

#### 函数1: `get_featured_content_list`

**函数签名**:
```python
async def get_featured_content_list(
    db: AsyncSession,
    include_inactive: bool = False,
    include_scheduled: bool = False
) -> List[FeaturedContent]
```

**功能**: 获取焦点图列表（公开接口或管理员接口）

**执行流程**:
1. 构建查询：`select(FeaturedContent).order_by(FeaturedContent.sort_order)`
2. 如果`include_inactive=False`（公开接口），添加过滤：
   - `FeaturedContent.is_active == True`
   - `(FeaturedContent.start_at.is_(None) | (FeaturedContent.start_at <= func.now()))`
   - `(FeaturedContent.end_at.is_(None) | (FeaturedContent.end_at >= func.now()))`
3. 如果`include_inactive=True`（管理员接口），返回所有焦点图
4. 限制返回数量：最多10条（公开接口）或100条（管理员接口）
5. 执行查询并返回结果
6. 记录日志：`logger.info(f"查询焦点图列表，返回{len(items)}条记录")`

**SQL示例**（公开接口）:
```sql
SELECT * FROM featured_content
WHERE is_active = true
  AND (start_at IS NULL OR start_at <= NOW())
  AND (end_at IS NULL OR end_at >= NOW())
ORDER BY sort_order
LIMIT 10;
```

---

#### 函数2: `get_featured_content_by_id`

**函数签名**:
```python
async def get_featured_content_by_id(
    db: AsyncSession,
    content_id: UUID
) -> Optional[FeaturedContent]
```

**功能**: 根据ID获取焦点图

**执行流程**:
1. 构建查询：`select(FeaturedContent).where(FeaturedContent.id == content_id)`
2. 执行查询
3. 如果不存在，返回`None`
4. 记录日志：`logger.info(f"查询焦点图: {str(content_id)[:8]}")`

---

#### 函数3: `create_featured_content`

**函数签名**:
```python
async def create_featured_content(
    db: AsyncSession,
    content_data: FeaturedContentCreate
) -> FeaturedContent
```

**功能**: 创建焦点图

**执行流程**:
1. 生成UUID：`content_id = uuid.uuid4()`
2. 创建模型实例：`content = FeaturedContent(id=content_id, **content_data.model_dump())`
3. 添加到会话：`db.add(content)`
4. 提交事务：`await db.commit()`
5. 刷新对象：`await db.refresh(content)`
6. 记录日志：`logger.info(f"创建焦点图: {str(content_id)[:8]}, 标题={content.title}")`
7. 返回创建的对象

**异常处理**:
```python
try:
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    logger.error(f"创建焦点图失败: {str(e)}")
    raise DatabaseIntegrityException("创建焦点图失败")
```

---

#### 函数4: `update_featured_content`

**函数签名**:
```python
async def update_featured_content(
    db: AsyncSession,
    content_id: UUID,
    content_data: FeaturedContentUpdate
) -> Optional[FeaturedContent]
```

**功能**: 更新焦点图

**执行流程**:
1. 查询焦点图：`content = await get_featured_content_by_id(db, content_id)`
2. 如果不存在，返回`None`
3. 提取更新数据：`update_data = content_data.model_dump(exclude_unset=True)`
4. 遍历更新数据，逐个设置属性：`setattr(content, key, value)`
5. 提交事务：`await db.commit()`
6. 刷新对象：`await db.refresh(content)`
7. 记录日志：`logger.info(f"更新焦点图: {str(content_id)[:8]}, 更新字段={list(update_data.keys())}")`
8. 返回更新后的对象

**注意**: 数据库触发器会自动更新`updated_at`字段

---

#### 函数5: `delete_featured_content`

**函数签名**:
```python
async def delete_featured_content(
    db: AsyncSession,
    content_id: UUID,
    soft_delete: bool = True
) -> bool
```

**功能**: 删除焦点图（软删除或硬删除）

**执行流程**:
1. 查询焦点图：`content = await get_featured_content_by_id(db, content_id)`
2. 如果不存在，返回`False`
3. 如果`soft_delete=True`（默认）：
   - 设置`content.is_active = False`
   - 提交事务：`await db.commit()`
   - 记录日志：`logger.warning(f"软删除焦点图: {str(content_id)[:8]}")`
4. 如果`soft_delete=False`（硬删除）：
   - 删除对象：`await db.delete(content)`
   - 提交事务：`await db.commit()`
   - 记录日志：`logger.warning(f"硬删除焦点图: {str(content_id)[:8]}")`
5. 返回`True`

---

#### 函数6: `get_featured_content_count`

**函数签名**:
```python
async def get_featured_content_count(
    db: AsyncSession,
    include_inactive: bool = False
) -> int
```

**功能**: 获取焦点图总数（用于管理员统计）

**执行流程**:
1. 构建查询：`select(func.count()).select_from(FeaturedContent)`
2. 如果`include_inactive=False`，添加过滤：`where(FeaturedContent.is_active == True)`
3. 执行查询并返回结果
4. 记录日志：`logger.info(f"查询焦点图总数: {count}")`

---

## 5. 导入语句要求

```python
"""
首页与搜索模块的CRUD层 (Phase1: 焦点图CRUD)

本模块负责焦点图的数据库操作。
"""
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.homepage_search import FeaturedContent
from app.schemas.homepage_search import FeaturedContentCreate, FeaturedContentUpdate
from app.core.exceptions import DatabaseIntegrityException
from app.core.logging import get_logger

logger = get_logger(__name__)
```

---

## 6. 代码组织要求

### 6.1. 文件结构

```python
# 1. 模块文档字符串
# 2. 导入语句
# 3. Logger初始化
# 4. Featured Content CRUD函数（按功能分组）
#    - 查询函数（get_featured_content_list, get_featured_content_by_id, get_featured_content_count）
#    - 创建函数（create_featured_content）
#    - 更新函数（update_featured_content）
#    - 删除函数（delete_featured_content）
```

### 6.2. 函数命名规范

- 查询单个：`get_<resource>_by_<field>`
- 查询列表：`get_<resource>_list` 或 `get_<resources>`
- 创建：`create_<resource>`
- 更新：`update_<resource>`
- 删除：`delete_<resource>`
- 统计：`get_<resource>_count`

### 6.3. 日志规范

- **INFO级别**: 正常的CRUD操作
- **WARNING级别**: 删除操作
- **ERROR级别**: 数据库异常
- **UUID脱敏**: 只记录前8位（`str(uuid)[:8]`）
- **日志格式**: `操作类型: UUID前8位, 关键字段=值`

---

## 7. 异常处理规范

### 7.1. IntegrityError处理

```python
try:
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    logger.error(f"数据库完整性错误: {str(e)}")
    # 根据错误类型抛出不同的业务异常
    if "unique constraint" in str(e).lower():
        raise DatabaseIntegrityException("记录已存在")
    else:
        raise DatabaseIntegrityException("数据库操作失败")
```

### 7.2. 异常类型

- `DatabaseIntegrityException`: 数据库完整性错误（唯一约束、外键约束等）
- 不在CRUD层抛出业务异常（如`NotFoundException`），由Service层处理

---

## 8. 测试验证要点

生成代码后，请确保：

1. ✅ 所有函数都有完整的类型提示
2. ✅ 所有函数都是异步函数（`async def`）
3. ✅ 所有数据库操作都有事务管理（`commit`/`rollback`）
4. ✅ 所有CRUD操作都有日志记录
5. ✅ UUID在日志中脱敏（只记录前8位）
6. ✅ 异常处理完整（`IntegrityError`）
7. ✅ 查询使用了正确的过滤条件（is_active、时间范围）
8. ✅ 排序使用了`sort_order`字段
9. ✅ 代码遵循PEP 8规范
10. ✅ 导入语句完整且正确

---

## 9. Phase1完成标准

Phase1（焦点图CRUD）完成后，应该能够：

1. ✅ 创建焦点图（管理员功能）
2. ✅ 更新焦点图（管理员功能）
3. ✅ 删除焦点图（软删除，管理员功能）
4. ✅ 获取焦点图列表（公开接口，带时间范围过滤）
5. ✅ 获取焦点图列表（管理员接口，显示所有状态）
6. ✅ 获取焦点图详情
7. ✅ 统计焦点图总数

**下一步**: Phase2将实现首页API的复杂查询逻辑（多表JOIN、热度计算等）

---

**版本历史**:
- V1.0 (2026-01-18): Phase1 - 焦点图CRUD初始版本
