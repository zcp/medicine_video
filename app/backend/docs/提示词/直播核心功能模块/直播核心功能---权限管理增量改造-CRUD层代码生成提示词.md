# 直播核心功能 - 权限管理增量改造 - CRUD 层代码生成提示词

## ⚠️ 使用说明（重要）

**本提示词用于改造已有代码，不是生成新代码。**

在使用本提示词之前，**必须**在 Cursor 聊天框中先 `@` 引用本提示词文档和所有需要改造的代码文件：

```
@docs/提示词/直播核心功能---权限管理增量改造-CRUD层代码生成提示词.md
@app/crud/room.py
@app/crud/session.py
@app/models/room.py
@app/models/session.py
...（其他相关文件）
```

**⚠️ 关键**：AI 需要读取现有的代码文件，才能进行增量改造。如果不引用已有代码文件，AI 无法知道现有代码的结构和内容，将无法正确执行增量改造。

---

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端工程师，专门负责实现 **数据访问层（CRUD/Repository Layer）**。  

**你的任务**：
1. **读取上下文**：用户已经在提示词的开头使用了 Cursor 的 `@` 标记引用了**已有的代码文件**（例如 `@app/crud/room.py`、`@app/models/room.py` 等）。
2. **分析现有代码**：**读取**这些 `@` 引用的代码文件内容，分析现有的CRUD方法、SQL查询逻辑等。
3. **增量改造**：在**不破坏现有查询逻辑**的前提下，为所有列表查询和详情查询方法**最小幅度地融合权限过滤**。

**⚠️ 重要**：你已经在上一版中完成了所有业务功能的 CRUD 实现（Room、Session、Tab、Message 等），现在只需要进行权限过滤的增量改造，**严禁重写或删除任何已有 CRUD 代码**。

## 2. 任务目标（权限增量范围）

本次任务 **只做权限过滤相关的最小增量改造**，严禁重写或删除任何已有 CRUD 代码：

### 2.1 核心改造原则（⚠️ 必须严格遵守）

1. **最小幅度修改原则**：
   - ✅ **只增加**权限过滤的 WHERE 条件（在 SQL 层面）
   - ✅ **只修改**方法签名（增加 `user_id`、`role` 参数，使用 Optional 类型）
   - ❌ **禁止**修改任何事务处理逻辑
   - ❌ **禁止**删除或重命名任何现有 CRUD 函数
   - ❌ **禁止**改变任何方法的返回类型和语义
   - ❌ **禁止**在内存中过滤数据（必须在 SQL 层面过滤）

2. **性能优先原则**：
   - 所有权限过滤**必须**在数据库层面通过 SQL WHERE 条件实现
   - **严禁**查出所有数据后在 Python 代码中过滤（性能陷阱）
   - 分页查询的总数计算必须应用相同的 WHERE 条件

3. **向后兼容原则**：
   - 新增的权限参数必须使用 `Optional` 类型，并提供默认值 `None`
   - 当权限参数为 `None` 时，应视为匿名用户（最严格的过滤）

### 2.2 改造范围

根据《直播核心功能设计文档 v6.1：权限体系与接口改造全案》，需要对以下 CRUD 方法进行权限过滤改造：

| 模块 | CRUD 方法 | 改造类型 | 权限策略 |
|------|----------|---------|---------|
| Room | `get_multi` | 列表查询 | Admin 看全部 / Regular 看 Public+Own / Anonymous 看 Public |
| Room | `get` | 详情查询 | 不在此层过滤（由 Service 层调用守卫函数） |
| Session | `get_multi_by_room` | 列表查询 | 继承 Room 的 is_private（不在此层过滤） |
| Session | `get` | 详情查询 | 不在此层过滤（由 Service 层调用守卫函数） |
| Message | `get_multi_by_room` | 列表查询 | 继承 Room 的 is_private（不在此层过滤） |

**⚠️ 重要说明**：
- **详情查询**（`get` 方法）不在 CRUD 层做权限过滤，由 Service 层调用权限守卫函数处理
- **列表查询**（`get_multi` 方法）必须在 CRUD 层通过 SQL WHERE 条件实现权限过滤
- **Session 和 Message** 的列表查询不在此层过滤，因为它们继承 Room 的权限，由 Service 层先检查 Room 权限后再查询

## 3. 项目文件组织结构

### 3.1 项目目录结构

```
backend/live_core_service/
├── app/
│   ├── crud/
│   │   ├── room.py                    # Room CRUD（需要改造get_multi和search）
│   │   ├── session.py                 # Session CRUD（不在此层过滤）
│   │   ├── tab.py                     # Tab CRUD（不在此层过滤）
│   │   └── message.py                 # Message CRUD（不在此层过滤）
│   ├── models/
│   │   ├── room.py                    # LiveRoom模型（了解is_private、user_id字段）
│   │   ├── session.py                 # LiveSession模型
│   │   ├── tab.py                     # LiveRoomTab模型
│   │   └── message.py                 # LiveRoomMessage模型
│   └── core/
│       └── exceptions.py              # 自定义异常（如果存在）
```

### 3.2 必须引用的代码文件（⚠️ 重要）

在使用本提示词时，用户**必须**通过 `@` 引用以下代码文件：

#### CRUD层文件（必须引用）
- `@app/crud/room.py` - Room CRUD（需要改造 `get_multi` 和 `search` 方法）

#### Models文件（必须引用，用于了解字段定义）
- `@app/models/room.py` - LiveRoom模型（了解 `is_private`、`user_id` 字段定义）

#### 其他相关文件（推荐引用）
- `@app/crud/session.py` - Session CRUD（用于了解现有代码结构，不在此层过滤）
- `@app/models/session.py` - LiveSession模型（可选）
- `@app/core/exceptions.py` - 自定义异常（如果存在）

**⚠️ 重要**：
- 如果某些文件不存在，可以只引用存在的文件
- AI 需要读取这些文件来了解现有代码的结构和内容
- 如果不引用这些文件，AI 无法知道现有代码，将无法正确执行增量改造

## 4. 内容来源（设计文档）

所有实现必须严格对齐以下设计文档，**不得自创权限逻辑或偏离语义**：

- **主设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`
  - 提供数据库 Schema 和字段定义
  
- **权限设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加权重设计版(非独立版).md`
  - **重点章节**：
    - § 3.1「直播间模块 (Room Domain)」—— 接口 2「获取直播间列表」的权限逻辑与 SQL 策略
    - § 4.3「Repository 层查询优化」—— SQL 权限过滤实现示例

**⚠️ 重要**：如权限设计文档与主设计文档存在歧义，以 **权限设计文档（v6.1）** 为最终口径。

## 5. 核心架构与编码约束（继承原有规范）

完全继承原有「CRUD 层代码生成提示词」中的全部规范，包括但不限于：

### 5.1 CRUD 层职责（学院派核心）

**必须遵守的规则**：

1. ✅ 只封装 **原子性数据库操作**，不做业务逻辑或权限检查（但需要在 SQL 层面应用权限过滤）
2. ✅ 所有写操作（create/update/delete）在函数内部处理事务（`commit/rollback`）
3. ✅ 所有写操作必须有 `try...except IntegrityError/Exception` 块，并在异常时 `rollback`
4. ✅ 在 `try` 之前提取日志所需变量（如 `obj_id_log` / `room_id_log`），避免在 `except` 中访问已失效对象
5. ✅ 使用 `logger.error(..., exc_info=True)` 记录数据库异常，并抛出自定义异常（`DatabaseIntegrityException` / `DatabaseOperationException`）
6. ✅ **权限过滤**：列表查询方法必须在 SQL 层面根据 `user_id` 和 `role` 构建不同的 WHERE 条件
7. ❌ 不做业务逻辑校验，不做权限判断（但需要应用权限过滤条件）

### 5.2 安全异步异常处理

继续严格执行「安全异步异常处理规范」：

```python
# ✅ 正确：在try之前提取日志变量
room_id_log = room_id
user_id_log = user_id

try:
    query = select(LiveRoom).where(...)
    result = await db.execute(query)
    return result.scalars().all()
except Exception as e:
    await db.rollback()
    logger.error(
        f"查询房间列表失败：room_id={room_id_log}, user_id={user_id_log}, error={e}",
        exc_info=True,
    )
    raise DatabaseOperationException("查询房间列表时发生错误")
```

## 6. 权限过滤 SQL 策略（核心实现）

### 6.1 Room 列表查询权限过滤

根据权限设计文档 § 3.1，Room 列表查询的权限策略为：

| 用户身份 | SQL WHERE 条件 | 说明 |
|---------|---------------|------|
| **Admin** | 无过滤 | `SELECT * FROM live_rooms ...` |
| **Regular User** | `is_private=false OR user_id={user_id}` | `SELECT * FROM live_rooms WHERE is_private=false OR user_id={user_id}` |
| **Anonymous** | `is_private=false` | `SELECT * FROM live_rooms WHERE is_private=false` |

**⚠️ 性能关键**：必须在 Repository 层通过 SQL 过滤，禁止查出所有数据在内存过滤。

### 6.2 实现模式

#### 模式 A：Room 列表查询（带权限过滤）

**改造前**：
```python
async def get_multi(
    self,
    db: AsyncSession,
    page: int,
    size: int
) -> Tuple[List[LiveRoom], int]:
    """获取房间列表"""
    # 构建基础查询
    stmt = select(LiveRoom)
    
    # 计算总数
    count_stmt = select(func.count()).select_from(LiveRoom)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # 应用分页和排序
    stmt = stmt.order_by(LiveRoom.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    # 执行查询
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    
    return list(rooms), total
```

#### 6.1.1.a `get_multi_for_owner` - 房间列表查询（仅返回指定 Owner 的房间，可选）

**用途说明**：
- 为了支持管理后台 RoomList 中“Regular 只管理自己的房间”的视图，可以在 `app/crud/room.py` 中额外提供一个按 `user_id` 精确过滤的辅助方法，例如：

```python
async def get_multi_for_owner(
    db: AsyncSession,
    page: int,
    size: int,
    owner_id: UUID,
) -> Tuple[List[LiveRoom], int]:
    stmt = select(LiveRoom).where(LiveRoom.user_id == owner_id)
    # 计算总数、排序、分页的逻辑与 get_multi 保持一致
    ...
```

- 该方法仅用于 Service 层在“管理视图（owner_only 模式）”下调用，不改变 `get_multi` 的既有行为；
- 如果现有项目采用的是模块级函数（如 `async def get_multi_and_total(...)`），可将上述方法名和参数列表调整为与项目风格一致（例如 `get_multi_and_total_by_owner(db, skip, limit, owner_id)`）。

**改造后**（最小幅度修改）：
```python
async def get_multi(
    self,
    db: AsyncSession,
    page: int,
    size: int,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None       # ← 新增：权限参数
) -> Tuple[List[LiveRoom], int]:
    """获取房间列表（带权限过滤）"""
    # 构建基础查询
    stmt = select(LiveRoom)
    
    # ← 新增：根据用户身份应用不同的WHERE条件（在分页之前）
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有
        pass
    elif user_id:
        # 普通用户：Public OR Own
        stmt = stmt.where(
            or_(
                LiveRoom.is_private == False,
                LiveRoom.user_id == user_id
            )
        )
    else:
        # 匿名用户：Only Public
        stmt = stmt.where(LiveRoom.is_private == False)
    
    # ← 计算总数（需要应用相同的WHERE条件）
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # ← 应用分页和排序（保持不变）
    stmt = stmt.order_by(LiveRoom.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    # ← 执行查询（保持不变）
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    
    return list(rooms), total
```

**⚠️ 关键点**：
1. WHERE 条件必须在分页之前应用
2. 总数计算必须使用相同的 WHERE 条件（通过 `stmt.subquery()` 复用）
3. 管理员判断使用 `role in ['ADMIN', 'SUPERADMIN']`（MVP 阶段 MODERATOR 等同于 REGULAR）

#### 模式 B：Room 搜索查询（带权限过滤）

**改造前**：
```python
async def search(
    self,
    db: AsyncSession,
    q: str,
    page: int,
    size: int
) -> Tuple[List[LiveRoom], int]:
    """搜索房间"""
    stmt = select(LiveRoom).where(
        or_(
            LiveRoom.title.ilike(f"%{q}%"),
            LiveRoom.description.ilike(f"%{q}%")
        )
    )
    # ... 分页和总数计算
```

**改造后**（最小幅度修改）：
```python
async def search(
    self,
    db: AsyncSession,
    q: str,
    page: int,
    size: int,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None       # ← 新增：权限参数
) -> Tuple[List[LiveRoom], int]:
    """搜索房间（带权限过滤）"""
    # 构建搜索条件
    search_conditions = or_(
        LiveRoom.title.ilike(f"%{q}%"),
        LiveRoom.description.ilike(f"%{q}%")
    )
    
    # ← 新增：根据用户身份应用权限过滤（与搜索条件组合）
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：只应用搜索条件
        stmt = select(LiveRoom).where(search_conditions)
    elif user_id:
        # 普通用户：搜索条件 AND (Public OR Own)
        stmt = select(LiveRoom).where(
            and_(
                search_conditions,
                or_(
                    LiveRoom.is_private == False,
                    LiveRoom.user_id == user_id
                )
            )
        )
    else:
        # 匿名用户：搜索条件 AND Public
        stmt = select(LiveRoom).where(
            and_(
                search_conditions,
                LiveRoom.is_private == False
            )
        )
    
    # ... 分页和总数计算（保持不变）
```

#### 模式 C：详情查询（不在此层过滤）

**⚠️ 重要**：详情查询方法（如 `get`）**不在 CRUD 层做权限过滤**，由 Service 层调用权限守卫函数处理。

**保持不变**：
```python
async def get(
    self,
    db: AsyncSession,
    id: UUID
) -> Optional[LiveRoom]:
    """获取房间详情（不在此层做权限过滤）"""
    stmt = select(LiveRoom).where(LiveRoom.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

**原因**：
- 详情查询需要返回 404 来隐藏 Private 资源的存在性
- 这个逻辑应该在 Service 层的 `_check_room_visibility` 守卫函数中处理
- CRUD 层只负责根据 ID 查询，不做权限判断

## 7. 具体 CRUD 方法改造清单

### 7.1 Room CRUD（`app/crud/room.py`）

#### 6.1.1 `get_multi` - 房间列表查询

**改造要求**：
- 增加 `user_id: Optional[UUID] = None` 和 `role: Optional[str] = None` 参数
- 在 SQL 查询中根据权限构建 WHERE 条件
- 总数计算必须应用相同的 WHERE 条件

**实现要点**：
```python
from sqlalchemy import select, or_, and_, func
from typing import Optional, List, Tuple
from uuid import UUID

async def get_multi(
    self,
    db: AsyncSession,
    page: int,
    size: int,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[LiveRoom], int]:
    """获取房间列表（带权限过滤）"""
    stmt = select(LiveRoom)
    
    # 权限过滤
    if role in ['ADMIN', 'SUPERADMIN']:
        pass  # 管理员看全部
    elif user_id:
        stmt = stmt.where(
            or_(
                LiveRoom.is_private == False,
                LiveRoom.user_id == user_id
            )
        )
    else:
        stmt = stmt.where(LiveRoom.is_private == False)
    
    # 总数计算（应用相同WHERE条件）
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # 分页和排序
    stmt = stmt.order_by(LiveRoom.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    
    return list(rooms), total
```

#### 6.1.2 `search` - 房间搜索查询

**改造要求**：
- 增加 `user_id: Optional[UUID] = None` 和 `role: Optional[str] = None` 参数
- 将搜索条件与权限过滤条件组合（使用 `and_`）

**实现要点**：
```python
async def search(
    self,
    db: AsyncSession,
    q: str,
    page: int,
    size: int,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[LiveRoom], int]:
    """搜索房间（带权限过滤）"""
    # 搜索条件
    search_conditions = or_(
        LiveRoom.title.ilike(f"%{q}%"),
        LiveRoom.description.ilike(f"%{q}%")
    )
    
    # 权限过滤 + 搜索条件
    if role in ['ADMIN', 'SUPERADMIN']:
        stmt = select(LiveRoom).where(search_conditions)
    elif user_id:
        stmt = select(LiveRoom).where(
            and_(
                search_conditions,
                or_(
                    LiveRoom.is_private == False,
                    LiveRoom.user_id == user_id
                )
            )
        )
    else:
        stmt = select(LiveRoom).where(
            and_(
                search_conditions,
                LiveRoom.is_private == False
            )
        )
    
    # ... 总数计算和分页（同上）
```

#### 6.1.3 `get` - 房间详情查询

**⚠️ 保持不变**：详情查询不在 CRUD 层做权限过滤，由 Service 层处理。

### 7.2 Session CRUD（`app/crud/session.py`）

**⚠️ 重要说明**：Session 的列表查询不在此层做权限过滤，因为它们继承 Room 的权限。Service 层会先检查 Room 权限，然后再查询 Session 列表。

**保持不变**：
```python
async def get_multi_by_room(
    self,
    db: AsyncSession,
    room_id: UUID,
    page: int,
    size: int
) -> Tuple[List[LiveSession], int]:
    """获取房间的场次列表（不在此层做权限过滤）"""
    # Service层会先检查Room权限，再调用此方法
    stmt = select(LiveSession).where(LiveSession.room_id == room_id)
    # ... 分页和总数计算
```

### 7.3 Message CRUD（`app/crud/message.py`）

**⚠️ 重要说明**：Message 的列表查询不在此层做权限过滤，因为它们继承 Room 的权限。Service 层会先检查 Room 权限，然后再查询 Message 列表。

**保持不变**：
```python
async def get_multi_by_room(
    self,
    db: AsyncSession,
    room_id: UUID,
    page: int,
    size: int
) -> Tuple[List[LiveRoomMessage], int]:
    """获取房间的留言列表（不在此层做权限过滤）"""
    # Service层会先检查Room权限，再调用此方法
    stmt = select(LiveRoomMessage).where(
        LiveRoomMessage.room_id == room_id,
        LiveRoomMessage.is_deleted == False
    )
    # ... 分页和总数计算
```

## 8. 导入依赖清单

在修改的 CRUD 文件中，你可能需要如下导入（按实际情况增减）：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from app.models import LiveRoom, LiveSession, LiveRoomMessage
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)
```

## 9. 代码质量检查清单（权限增量）

在生成或修改代码后，请自检：

### 8.1 最小幅度修改检查

- [ ] 只增加了权限参数（`user_id`、`role`），**未删除或重命名**任何旧函数
- [ ] 只修改了 SQL WHERE 条件，**未修改**事务处理、异常处理、日志记录逻辑
- [ ] 所有新增参数都使用了 `Optional` 类型，并提供了默认值 `None`
- [ ] 详情查询方法（`get`）**未做权限过滤**（由 Service 层处理）

### 9.2 权限过滤逻辑检查

- [ ] Admin 角色：无 WHERE 条件（看全部）
- [ ] Regular 用户：`is_private=false OR user_id={user_id}`
- [ ] Anonymous 用户：`is_private=false`
- [ ] 搜索查询：搜索条件与权限过滤条件正确组合（使用 `and_`）

### 9.3 性能检查

- [ ] 所有权限过滤都在 SQL 层面实现（通过 WHERE 条件）
- [ ] **未在内存中过滤数据**（严禁查出所有数据后过滤）
- [ ] 总数计算应用了相同的 WHERE 条件（通过 `stmt.subquery()` 复用）
- [ ] WHERE 条件在分页之前应用

### 9.4 代码一致性检查

- [ ] 使用 `is_private` 布尔字段（而非 `visibility` 枚举）
- [ ] 使用 `user_id` 字段（存储 `public_id`）
- [ ] 管理员判断使用 `role in ['ADMIN', 'SUPERADMIN']`
- [ ] 所有异常处理和日志记录风格与现有代码保持一致

## 10. 实施步骤建议

1. **第一步：改造 Room CRUD**
   - 修改 `get_multi` 方法，增加权限参数和 SQL 过滤
   - 修改 `search` 方法，增加权限参数和 SQL 过滤
   - 确认 `get` 方法保持不变（详情查询不在此层过滤）

2. **第二步：确认其他 CRUD**
   - 确认 Session CRUD 的列表查询方法保持不变（继承 Room 权限）
   - 确认 Message CRUD 的列表查询方法保持不变（继承 Room 权限）

3. **第三步：测试验证**
   - Admin 查询 → 返回所有房间
   - Regular 用户查询 → 只返回 Public 房间 + 自己的房间
   - Anonymous 查询 → 只返回 Public 房间
   - 搜索查询 → 搜索结果也应用权限过滤

---

## 11. 覆盖完整性检查（⚠️ 必须验证）

在使用本提示词进行代码改造前，请确认以下覆盖完整性：

### 11.1 CRUD方法覆盖检查

根据权限设计文档和Service与API层提示词，CRUD层需要改造的方法：

| CRUD方法 | 设计文档要求 | 提示词文档覆盖 | 状态 |
|---------|------------|--------------|------|
| Room CRUD `get_multi` | 需要SQL权限过滤（§3.1接口2） | ✅ 覆盖（§7.1.1） | ✅ 完全覆盖 |
| Room CRUD `search` | 需要SQL权限过滤（§3.1接口9） | ✅ 覆盖（§7.1.2） | ✅ 完全覆盖 |
| Room CRUD `get` | 不在此层过滤（由Service层处理） | ✅ 已说明（§2.2） | ✅ 正确说明 |
| Session CRUD `get_multi_by_room` | 不在此层过滤（继承Room权限） | ✅ 已说明（§7.2） | ✅ 正确说明 |
| Session CRUD `get` | 不在此层过滤（由Service层处理） | ✅ 已说明（§2.2） | ✅ 正确说明 |
| Message CRUD `get_multi_by_room` | 不在此层过滤（继承Room权限） | ✅ 已说明（§7.3） | ✅ 正确说明 |
| Message CRUD `get` | 不在此层过滤（由Service层处理） | ✅ 已说明（§2.2） | ✅ 正确说明 |

**详细说明**：

#### 需要改造的方法（2个）
1. ✅ **Room CRUD `get_multi`** - 房间列表查询（§7.1.1）
   - 对应接口：`GET /api/v1/rooms`（接口2）
   - 需要SQL权限过滤：Admin看全部 / Regular看Public+Own / Anonymous看Public

2. ✅ **Room CRUD `search`** - 房间搜索查询（§7.1.2）
   - 对应接口：`GET /api/v1/rooms/search`（接口9）
   - 需要SQL权限过滤：与 `get_multi` 相同的权限策略

#### 不在此层过滤的方法（已明确说明）
- ✅ **Room CRUD `get`** - 房间详情查询（§2.2）
  - 原因：详情查询需要返回404来隐藏Private资源的存在性，由Service层的 `_check_room_visibility` 守卫函数处理

- ✅ **Session CRUD `get_multi_by_room`** - 场次列表查询（§7.2）
  - 原因：Session继承Room的权限，由Service层先检查Room权限后再查询

- ✅ **Message CRUD `get_multi_by_room`** - 留言列表查询（§7.3）
  - 原因：Message继承Room的权限，由Service层先检查Room权限后再查询

**结论**：✅ **100%覆盖所有需要改造的CRUD方法，其他方法已明确说明不在此层过滤**

---

## 12. 交付物（最终输出）

根据本提示词，在**已引用的现有代码**基础上，以最小幅度修改的方式完成权限过滤改造。

### 12.1 输出要求

1. **修改现有CRUD文件**：
   - 直接修改用户通过 `@` 引用的 `app/crud/room.py` 文件
   - 为 `get_multi` 和 `search` 方法增加权限参数
   - 在 SQL 查询中应用权限过滤条件
   - 保持现有查询逻辑和分页逻辑不变

2. **不删除任何内容**：
   - 严禁删除或重命名任何现有CRUD方法
   - 严禁删除任何现有查询逻辑

---

**请根据本提示词，在已引用的现有代码基础上，以最小幅度修改的方式完成权限过滤改造。**
