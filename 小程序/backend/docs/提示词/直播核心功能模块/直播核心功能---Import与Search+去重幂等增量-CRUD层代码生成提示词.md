# LiveCore Service - Import 与 Search + 批量导入 V6 去重幂等增量 - CRUD 层代码生成提示词

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端工程师，专门负责实现 **数据访问层（CRUD Layer）**。  
你已经在上一版中为「Import 与 Search 增量功能」实现了基础 CRUD 代码，现在需要在**不破坏现有逻辑**的前提下，为 **V6 去重幂等增量**补充少量 CRUD 能力。

## 2. 任务目标（V6 增量范围）

本次任务 **只做 V6 去重幂等相关的最小增量**，不要重写或删除任何已有 CRUD 代码：

1. 在 `app/crud/room.py` 中新增：
   - `get_by_external_id(db: AsyncSession, user_id: UUID, external_room_id: str) -> Optional[LiveRoom]`
2. 在 `app/crud/session.py` 中新增：
   - `get_by_room_and_playback_hash(db: AsyncSession, room_id: UUID, playback_url_hash: str) -> Optional[LiveSession]`
3. 确认已有的 `crud_session.create()` / `crud_room.create()` 在接收新字段时**保持向后兼容**：
   - `LiveSession` 新增可选字段：`playback_url_hash`
   - `LiveRoom` 新增可选字段：`external_room_id`（通常在 Service 层赋值后 `commit/refresh`）

> 重要：  
> - **禁止**删除、重命名或改变任何已有 CRUD 函数的返回类型和语义；  
> - **禁止**在本次增量中修改数据库 Schema（Schema 已由迁移脚本根据设计文档完成）；  
> - 只允许 **新增函数** 或在 `create()` 中**无侵入地透传新字段**。

## 3. 内容来源（设计文档）

所有实现必须严格对齐以下设计文档，**不得自创字段或偏离语义**：

- `docs/03_系统设计/直播核心功能设计文档v6-Import与Search+批量导入幂等版.md`
  - 重点章节：
    - 2.2「V6 去重补丁的 DB 增量（external_room_id / playback_url_hash）」  
    - 2.3「ORM 模型增量」  
    - 7「CRUD 扩展（去重相关）」  

如设计文档与本提示词存在歧义，以 **设计文档 V6** 为最终口径。

## 4. 核心架构与编码约束（继承上一版）

完全继承原有「Import 与 Search 增量功能-CRUD 层代码生成提示词」中的全部规范，包括但不限于：

### 4.1 CRUD 层职责（学院派核心）

**必须遵守的规则**：

1. ✅ 只封装 **原子性数据库操作**，不做业务逻辑或权限检查；  
2. ✅ 所有写操作（create/update/delete）在函数内部处理事务（`commit/rollback`）；  
3. ✅ 所有写操作必须有 `try...except IntegrityError/Exception` 块，并在异常时 `rollback`；  
4. ✅ 在 `try` 之前提取日志所需变量（如 `obj_id_log` / `room_id_log`），避免在 `except` 中访问已失效对象；  
5. ✅ 使用 `logger.error(..., exc_info=True)` 记录数据库异常，并抛出自定义异常（`DatabaseIntegrityException` / `DatabaseOperationException`）；  
6. ❌ 不做业务逻辑校验，不做权限判断。

### 4.2 安全异步异常处理

继续严格执行上一版的「安全异步异常处理规范」：

```python
# ✅ 正确
session_id_log = obj_in.get("id", uuid.uuid4())
room_id_log = obj_in.get("room_id")

try:
    db_obj = LiveSession(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
except IntegrityError as e:
    await db.rollback()
    logger.error(
        f"创建会话失败（完整性错误）：session_id={session_id_log}, room_id={room_id_log}, error={e}",
        exc_info=True,
    )
    raise DatabaseIntegrityException("创建会话时发生唯一键冲突")
```

## 5. V6 去重幂等相关的 DB 口径（只读，不修改）

> 注意：Schema 已通过迁移脚本完成，CRUD 层 **只需按照字段语义读写**。

设计文档 V6 中的 DB 增量为：

- `live_rooms.external_room_id VARCHAR(64) NULL`  
  - 部分唯一索引：`uq_live_rooms_user_external_room(user_id, external_room_id) WHERE external_room_id IS NOT NULL`
- `live_sessions.playback_url_hash VARCHAR(128) NULL`  
  - 部分唯一索引：`uq_live_sessions_room_playback_hash(room_id, playback_url_hash) WHERE playback_url_hash IS NOT NULL`

ORM 模型增量示意：

```python
class LiveRoom(Base):
    __tablename__ = "live_rooms"
    ...
    external_room_id = Column(String(64), nullable=True, comment="外部直播间ID（如第三方平台直播间ID）")
    __table_args__ = (
        Index("idx_live_rooms_user_id", "user_id"),
        Index(
            "uq_live_rooms_user_external_room",
            "user_id",
            "external_room_id",
            unique=True,
            postgresql_where=text("external_room_id IS NOT NULL"),
        ),
    )


class LiveSession(Base):
    __tablename__ = "live_sessions"
    ...
    playback_url = Column(String(1024), nullable=True)
    playback_url_hash = Column(String(128), nullable=True, comment="playback_url 规范化后的哈希值")
    __table_args__ = (
        Index(
            "uq_live_sessions_room_playback_hash",
            "room_id",
            "playback_url_hash",
            unique=True,
            postgresql_where=text("playback_url_hash IS NOT NULL"),
        ),
    )
```

## 6. 具体 CRUD 增量实现要求

### 6.1 Room CRUD：按 external_room_id 查找房间

**文件**：`app/crud/room.py`  
**新增函数签名**：

```python
async def get_by_external_id(
    db: AsyncSession,
    user_id: uuid.UUID,
    external_room_id: str,
) -> Optional[LiveRoom]:
    ...
```

**实现要求**：

1. 使用 `select(LiveRoom)` + `where` 构建查询：

```python
query = (
    select(LiveRoom)
    .where(
        LiveRoom.user_id == user_id,
        LiveRoom.external_room_id == external_room_id,
    )
)
result = await db.execute(query)
return result.scalar_one_or_none()
```

2. 这是一个 **只读查询**：
   - 不需要事务处理；  
   - 使用简单的 `try/except Exception` 捕获并抛出 `DatabaseOperationException` 即可（可选）。  
3. 不做权限校验，不做业务逻辑，只根据 `(user_id, external_room_id)` 返回房间或 `None`。

### 6.2 Session CRUD：按 (room_id, playback_url_hash) 查找会话

**文件**：`app/crud/session.py`  
**新增函数签名**：

```python
async def get_by_room_and_playback_hash(
    db: AsyncSession,
    room_id: uuid.UUID,
    playback_url_hash: str,
) -> Optional[LiveSession]:
    ...
```

**实现要求**：

1. 使用 `select(LiveSession)` + `where` 构建查询：

```python
query = select(LiveSession).where(
    LiveSession.room_id == room_id,
    LiveSession.playback_url_hash == playback_url_hash,
)
result = await db.execute(query)
return result.scalar_one_or_none()
```

2. 同样是 **只读查询**：  
   - 不需要显式事务；  
   - 可选地用 `try/except Exception` 包裹并抛出 `DatabaseOperationException`。

### 6.3 现有 create() 的兼容性要求

#### 6.3.1 `crud_session.create()`

**目标**：保持原有行为不变，同时支持写入 `playback_url_hash` 字段。

- 若 `obj_in` 中包含 `playback_url_hash`，则正常构造 `LiveSession(**obj_in)` 并写库；  
- 若不包含，则行为与 V5 完全相同；  
- 事务与异常处理逻辑沿用原有「学院派模板」，**不做任何破坏性修改**。

#### 6.3.2 `crud_room.create()`

**目标**：保持原有房间创建逻辑不变：

- 默认 `external_room_id` 可以不在 `obj_in` 中传入；  
- 若未来 Service 层在创建时直接传入 `external_room_id`，也应被 ORM 正常接收；  
- 常见场景是：先用 `crud_room.create()` 创建房间，再在 Service 中手动设置 `room.external_room_id` 并 `commit/refresh`，CRUD 层无需为此增加额外 API。

## 7. 自定义异常与日志规范（延续）

沿用已有异常类：

```python
class DatabaseIntegrityException(Exception): ...
class DatabaseOperationException(Exception): ...
```

**要求**：

- 所有写操作中捕获 `IntegrityError` 时抛出 `DatabaseIntegrityException`；  
- 其他数据库异常抛出 `DatabaseOperationException`；  
- 日志必须包含关键 ID（如房间 ID / 会话 ID / user_id 等）。

## 8. 导入依赖清单

在新增或修改的 CRUD 文件中，你可能需要如下导入（按实际情况增减）：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Optional
import logging
import uuid

from app.models import LiveRoom, LiveSession
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)
```

## 9. 代码质量检查清单（V6 增量）

在生成或修改代码后，请自检：

- [ ] 只新增了 `get_by_external_id` 与 `get_by_room_and_playback_hash`，**未删除或重命名**任何旧函数；  
- [ ] `crud_session.create` / `crud_room.create` 的事务、异常、日志逻辑仍符合上一版模板；  
- [ ] 所有新增函数都不包含业务逻辑或权限判断；  
- [ ] 所有数据库异常都按规范转换为 `DatabaseOperationException`（如你选择添加 try/except）；  
- [ ] 查询语义与 V6 设计文档中对 `(user_id, external_room_id)` 与 `(room_id, playback_url_hash)` 的定义完全一致。

---

**请根据本提示词，在现有 CRUD 代码基础上，以“补丁式新增”的方式实现 V6 去重幂等相关的 CRUD 能力。**


