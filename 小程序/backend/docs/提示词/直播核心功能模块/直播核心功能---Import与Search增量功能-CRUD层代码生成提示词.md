# LiveCore Service - Import与Search增量功能 CRUD 层代码生成提示词

## 1. 角色定义

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师，专门负责实现数据访问层（CRUD Layer）。你严格遵循事务处理、异常处理、日志记录的最佳实践。

## 2. 任务目标

为 LiveCore Service 的"Import与Search增量功能"生成完整的 CRUD 层代码，包括：
1. **Import Session CRUD 函数**：复用现有 `crud_session.create()`
2. **Search CRUD 函数**：新增 `crud_room.list_with_search()`
3. **Batch Import CRUD 函数**：复用现有 `crud_room.create()` 和 `crud_session.create()`

## 3. 内容来源

基于《LiveCore Service - Import 与 Search 增量功能设计文档 (V5.0)》的技术规范。

## 4. 核心架构约束（最高优先级）

### 4.1 CRUD 层职责（学院派核心）

**必须遵守的规则**：
1. ✅ **必须**封装原子性数据库操作
2. ✅ **必须**在写操作（create, update, delete）函数内部处理事务
3. ✅ **必须**包含 `try...except IntegrityError/Exception...finally` 块
4. ✅ **必须**处理 `db.commit()` 和 `db.rollback()`
5. ✅ **必须**处理数据库错误日志（`logger.error`, `exc_info=True`）
6. ✅ **必须**在 `try` 块之前提取日志所需变量（安全异步异常处理）
7. ❌ **不做**业务逻辑或权限检查

### 4.2 安全异步异常处理规范

**关键规则**：在 `try...except` 块中记录日志时：
- ✅ **必须**在 `try` 之前提取所有日志变量（如 `obj_id_log = obj_in.get('id')`）
- ❌ **严禁**在 `except` 块中访问可能已失效的数据库会话或 ORM 对象属性

**示例**：
```python
# ✅ 正确做法
session_id_log = obj_in.get('id', uuid.uuid4())
room_id_log = obj_in.get('room_id')

try:
    db_obj = Model(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
except IntegrityError as e:
    await db.rollback()
    logger.error(f"DB错误: id={session_id_log}, room_id={room_id_log}, error={e}", exc_info=True)
    raise DatabaseIntegrityException("唯一键冲突")

# ❌ 错误做法
try:
    db_obj = Model(**obj_in)
    # ...
except IntegrityError as e:
    # 此时 db_obj 可能已失效
    logger.error(f"错误: id={db_obj.id}, error={e}")  # ❌ 危险！
```

### 4.3 事务处理模板

**标准模板**（所有写操作必须遵循）：
```python
async def create(db: AsyncSession, obj_in: dict) -> Model:
    """
    创建记录（CRUD 层 - 学院派实现）
    
    职责：
    1. 创建数据库记录
    2. 处理事务（commit/rollback）
    3. 处理数据库异常
    4. 记录错误日志
    
    不做：
    1. 业务逻辑校验（由 Service 层负责）
    2. 权限检查（由 Service 层负责）
    """
    # 提前提取日志所需变量（安全规范）
    obj_id_log = obj_in.get('id', uuid.uuid4())
    related_id_log = obj_in.get('related_id')  # 根据实际情况提取
    
    try:
        # 创建 ORM 对象
        db_obj = Model(**obj_in)
        db.add(db_obj)
        
        # 提交事务
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"创建成功：id={db_obj.id}, related_id={related_id_log}")
        return db_obj
        
    except IntegrityError as e:
        # 数据库完整性错误（如唯一键冲突）
        await db.rollback()
        logger.error(
            f"创建失败（完整性错误）：id={obj_id_log}, "
            f"related_id={related_id_log}, error={e}",
            exc_info=True
        )
        raise DatabaseIntegrityException("创建记录时发生唯一键冲突")
        
    except Exception as e:
        # 其他数据库错误
        await db.rollback()
        logger.error(
            f"创建失败（未知DB错误）：id={obj_id_log}, "
            f"related_id={related_id_log}, error={e}",
            exc_info=True
        )
        raise DatabaseOperationException(f"数据库操作失败: {e}")
```

## 5. 具体功能实现要求

### 5.1 Import Session CRUD

**复用现有函数**：`crud_session.create(db: AsyncSession, obj_in: dict)`

**关键点**：
- 该函数已存在，无需新增代码
- Import Session 与普通创建的唯一区别是 `obj_in` 中包含 `playback_url`
- Service 层负责构建 `obj_in`，CRUD 层只负责写入

**必须验证**：现有 `crud_session.create()` 是否符合 4.3 节的事务处理模板。

---

### 5.2 Search CRUD - 新增函数

**函数签名**：
```python
async def list_with_search(
    db: AsyncSession,
    filters: dict = None,
    page: int = 1,
    size: int = 10,
    sort: Optional[str] = None
) -> dict:
```

**功能描述**：
- 支持 ID 精确匹配（`filters['id_or_title'] = ('id', uuid_value)`）
- 支持标题模糊匹配（`filters['id_or_title'] = ('title', '%keyword%')`）
- 支持可配置排序（`sort` 参数，格式为 `field:direction`，例如 `created_at:desc`）
- 分页返回：`{"total": int, "page": int, "size": int, "items": [LiveRoom]}`

**实现要求**：
1. 使用 `select(LiveRoom)` 构建基础查询
2. 根据 `filters['id_or_title']` 添加 WHERE 条件：
   - 若 `field == 'id'`：`query.where(LiveRoom.id == value)`
   - 若 `field == 'title'`：`query.where(LiveRoom.title.ilike(value))`
3. 执行两次查询：
   - `select(func.count()).select_from(query.subquery())` 获取总数
   - `query.offset((page-1)*size).limit(size)` 获取数据列表
4. 排序处理：
   - 若 `sort` 非空：解析 `field:direction`（例如 `created_at:desc`），动态构建 `order_by()` 子句
   - 若 `sort` 为空：默认按 `created_at DESC` 排序
5. 捕获异常并抛出 `DatabaseOperationException`

**参考代码框架**：
```python
async def list_with_search(
    db: AsyncSession,
    filters: dict = None,
    page: int = 1,
    size: int = 10,
    sort: Optional[str] = None
) -> dict:
    """
    搜索房间列表（CRUD 层 - 学院派实现）
    
    职责：
    1. 执行数据库查询
    2. 支持 ID 精确匹配和标题模糊匹配
    3. 支持可配置排序
    4. 分页返回
    
    不做：
    1. 业务逻辑（由 Service 层负责）
    """
    try:
        # 构建基础查询
        query = select(LiveRoom)
        
        # 添加搜索条件
        if filters and 'id_or_title' in filters:
            field, value = filters['id_or_title']
            
            if field == 'id':
                # UUID 精确匹配
                query = query.where(LiveRoom.id == value)
            elif field == 'title':
                # 标题模糊匹配
                query = query.where(LiveRoom.title.ilike(value))
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页
        query = query.offset((page - 1) * size).limit(size)
        
        # 排序处理
        if sort:
            # 解析 sort 参数（格式：field:direction）
            sort_parts = sort.split(':')
            if len(sort_parts) == 2:
                field_name, direction = sort_parts[0], sort_parts[1].upper()
                # 验证字段名（仅允许安全字段）
                if hasattr(LiveRoom, field_name) and direction in ('ASC', 'DESC'):
                    field = getattr(LiveRoom, field_name)
                    if direction == 'DESC':
                        query = query.order_by(field.desc())
                    else:
                        query = query.order_by(field.asc())
                else:
                    # 无效的排序参数，使用默认排序
                    query = query.order_by(LiveRoom.created_at.desc())
            else:
                # 无效格式，使用默认排序
                query = query.order_by(LiveRoom.created_at.desc())
        else:
            # 默认排序
            query = query.order_by(LiveRoom.created_at.desc())
        
        # 执行查询
        result = await db.execute(query)
        rooms = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": rooms
        }
        
    except Exception as e:
        logger.error(f"搜索房间失败：{e}", exc_info=True)
        raise DatabaseOperationException(f"数据库查询失败: {e}")
```

---

### 5.3 Batch Import CRUD

**复用现有函数**：
- `crud_room.create(db: AsyncSession, obj_in: dict)`
- `crud_session.create(db: AsyncSession, obj_in: dict)`

**关键点**：
- Batch Import 的 Service 层会逐行调用这两个函数
- CRUD 层无需新增代码
- 每次调用都会执行独立的事务（行级事务隔离）
- 批量导入在 **Service 层** 会先把原始 CSV/Excel 的表头做标准化与别名映射（例如：`标题 → room_title`，`播放url（以及历史表头“播放url1”）→ playback_url`，`封面图片 → cover_url`），CRUD 层只需要面向统一的逻辑字段（`room_title`、`playback_url` 等），无需感知中文表头

**必须验证**：
1. 现有 `crud_room.create()` 是否支持传入 `stream_key`
2. 现有 `crud_session.create()` 是否支持传入 `playback_url`
3. 两个函数是否都符合 4.3 节的事务处理模板

---

## 6. 自定义异常类定义

**必需的异常类**（在 `app/core/exceptions.py` 中定义）：

```python
class DatabaseIntegrityException(Exception):
    """数据库完整性错误（如唯一键冲突）"""
    def __init__(self, message: str = "数据库完整性冲突"):
        self.message = message
        super().__init__(self.message)

class DatabaseOperationException(Exception):
    """数据库操作错误"""
    def __init__(self, message: str = "数据库操作失败"):
        self.message = message
        super().__init__(self.message)
```

---

## 7. 日志记录规范

**CRUD 层日志规则**：
- ✅ 使用 `logger.info()` 记录成功操作（简要信息）
- ✅ 使用 `logger.error()` 记录数据库异常（**必须**包含 `exc_info=True`）
- ✅ 日志内容必须包含关键 ID（已提前提取到局部变量）
- ❌ 禁止在 `except` 块中访问 ORM 对象属性

**示例**：
```python
# ✅ 正确
logger.error(
    f"创建会话失败（完整性错误）：session_id={session_id_log}, "
    f"room_id={room_id_log}, error={e}",
    exc_info=True
)

# ❌ 错误
logger.error(f"创建会话失败：session_id={db_session.id}, error={e}")  # 危险！
```

---

## 8. 导入依赖清单

**必需的导入**：
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models import LiveRoom, LiveSession
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)
```

---

## 9. 交付清单

请生成以下 CRUD 层代码：

### 9.1 必须新增的代码
- [ ] `app/crud/crud_room.py`：新增 `list_with_search()` 函数

### 9.2 必须验证的现有代码
- [ ] `app/crud/crud_session.py`：验证 `create()` 函数是否符合 4.3 节模板
- [ ] `app/crud/crud_room.py`：验证 `create()` 函数是否符合 4.3 节模板

### 9.3 必须新增的异常类
- [ ] `app/core/exceptions.py`：确保包含 `DatabaseIntegrityException` 和 `DatabaseOperationException`

---

## 10. 代码质量检查清单

在生成代码后，请自查以下项：
- [ ] 所有写操作都包含完整的 `try...except IntegrityError/Exception` 块
- [ ] 所有写操作都处理了 `db.commit()` 和 `db.rollback()`
- [ ] 所有日志变量都在 `try` 之前提取
- [ ] 所有 `logger.error()` 都包含 `exc_info=True`
- [ ] 没有任何业务逻辑或权限检查代码
- [ ] 所有自定义异常都正确抛出（`raise DatabaseIntegrityException(...)`）
- [ ] 分页查询使用了两次查询（count + list）
- [ ] 搜索查询正确使用了 `ilike()` 和 `where()` 条件

---

## 11. 注意事项

1. **不要创建新的 ORM 模型**：所有模型（`LiveRoom`, `LiveSession`）已存在
2. **不要修改数据库 Schema**：本次增量功能不需要任何数据库变更
3. **严格遵循模板**：所有事务处理必须使用 4.3 节的标准模板
4. **保持幂等性**：CRUD 函数应设计为可重复调用而不产生副作用（事务保证）

---

**请根据以上所有要求，生成完整的 CRUD 层代码。**

