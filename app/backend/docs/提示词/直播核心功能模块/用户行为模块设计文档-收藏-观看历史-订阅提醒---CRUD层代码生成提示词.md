# 用户行为模块 - CRUD层代码生成提示词

**模块名称**: user_behavior  
**功能模块名称**: 用户行为模块设计文档-收藏-观看历史-订阅提醒  
**目标文件**: `backend/live_core_service/app/crud/user_behavior.py`  
**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通 Clean Architecture 和 Python 异步编程的资深后端开发工程师。你的任务是根据本提示词文档，生成**用户行为模块**的 CRUD 层代码。

**🚨 [强制要求] 异常处理（最高优先级）**：
- **所有写操作**（create, update, remove, batch_add）**必须**包含完整的 `try/except IntegrityError/finally` 块，并处理 `db.rollback()`（见母版 `crud_service_endpoint代码生成提示词母版.md` 第1222行）
- **UPDATE + INSERT 操作**（如 `record_watch_history`）**必须**有异常处理
- 详细要求见本文档第5节"日志与错误处理规范"

---

## 2. CRUD 层职责与原则

### 2.1 职责

CRUD 层是数据访问层，**仅负责数据库操作**：

- ✅ 执行数据库查询（SELECT、INSERT、UPDATE、DELETE）  
- ✅ 使用 `AsyncSession` 访问数据库（异步）  
- ✅ 应用 SQL 级过滤条件（如 `is_active=True`、按 `user_id` 过滤当前用户数据）  
- ✅ 记录关键操作日志（INFO 级），对 UUID 做前 8 位脱敏  
- ❌ 不包含业务流程控制（由 Service 层实现）  
- ❌ 不做权限判断（由 Service 层实现）  
- ❌ 不构造 HTTP 响应（由 API/Service 层实现）  

### 2.2 异步与事务管理

- 所有公开的 CRUD 函数必须是 `async def`，第一个参数为 `db: AsyncSession`。  
- CRUD 层**不主动调用 `commit()` / `rollback()`**：  
  - 只使用 `add()` / `flush()` / 查询；  
  - 由 Service 层统一控制事务提交与回滚。  
- 对 `IntegrityError` 等数据库异常，CRUD 层需要捕获并转换为 `DatabaseIntegrityException`，不直接返回裸 SQL 错误。
- **🚨 [强制要求] 异常处理**：所有写操作**必须**包含完整的异常处理（详见第5节"日志与错误处理规范"）。  

---

## 3. Model 字段摘要（来自实际代码）

> **请在生成代码前使用 `read_file()` 读取 `app/models/user_behavior.py`，确保所有字段、约束、索引与设计文档一致。下面为关键字段摘要，具体以实际代码为准。**

### 3.1 UserFavorite 模型

**表名**: `user_favorites`

| 字段名      | 类型           | 约束                                | 默认值       | 说明                                      |
|-------------|----------------|-------------------------------------|--------------|-------------------------------------------|
| `id`        | UUID (PK)      | PRIMARY KEY                         | uuid.uuid4() | 收藏记录ID                                |
| `user_id`   | UUID           | NOT NULL                            | -            | 用户公开ID（users.public_id）             |
| `room_id`   | UUID (FK)      | NOT NULL, FK→live_rooms(id)        | -            | 直播间ID                                  |
| `is_active` | Boolean        | NOT NULL                            | True         | 是否有效：true=已收藏，false=已取消       |
| `created_at`| TIMESTAMP(TZ)  | NOT NULL                            | now()        | 创建时间                                  |

约束/索引：

- `UNIQUE (user_id, room_id)` (`uq_user_favorites_user_room`)  
- 索引：`idx_user_favorites_user_id`, `idx_user_favorites_room_id`, `idx_user_favorites_user_active`  

### 3.2 WatchHistory 模型

**表名**: `watch_history`

| 字段名       | 类型           | 约束                             | 默认值       | 说明                                  |
|--------------|----------------|----------------------------------|--------------|---------------------------------------|
| `id`         | UUID (PK)      | PRIMARY KEY                      | uuid.uuid4() | 观看记录ID                            |
| `user_id`    | UUID           | NOT NULL                         | -            | 用户公开ID                            |
| `session_id` | UUID (FK)      | NOT NULL, FK→live_sessions(id)   | -            | 直播场次ID                            |
| `progress`   | Integer        | NULLABLE                         | NULL         | 观看进度（秒）                        |
| `watched_at` | TIMESTAMP(TZ)  | NOT NULL                         | now()        | 观看时间                              |
| `is_latest`  | Boolean        | NOT NULL                         | True         | 是否为该用户该场次的最新记录          |

索引：

- `idx_watch_history_user_session (user_id, session_id)`  
- `idx_watch_history_is_latest (user_id, is_latest)`  

### 3.3 UserSubscription 模型

**表名**: `user_subscriptions`

| 字段名        | 类型                         | 约束                          | 默认值       | 说明                          |
|---------------|------------------------------|-------------------------------|--------------|-------------------------------|
| `id`          | UUID (PK)                    | PRIMARY KEY                   | uuid.uuid4() | 订阅记录ID                    |
| `user_id`     | UUID                         | NOT NULL                      | -            | 用户公开ID                    |
| `target_type` | Enum(SubscriptionTargetType) | NOT NULL                      | -            | 订阅目标类型：room 或 session |
| `room_id`     | UUID (FK)                    | NULLABLE, FK→live_rooms(id)   | NULL         | 订阅房间ID                    |
| `session_id`  | UUID (FK)                    | NULLABLE, FK→live_sessions(id)| NULL         | 订阅场次ID                    |
| `is_active`   | Boolean                      | NOT NULL                      | True         | 是否仍然订阅                  |
| `created_at`  | TIMESTAMP(TZ)                | NOT NULL                      | now()        | 创建时间                      |

约束/索引：

- `UNIQUE (user_id, target_type, room_id, session_id)` (`uq_user_subscriptions_user_target`)  
- 索引：`idx_user_subscriptions_user_id`  

---

## 4. 需要实现的 CRUD 函数

以下函数签名为建议，你可以根据实际需要微调，但**函数职责和语义必须保持**。

### 4.1 收藏相关 (UserFavorite)

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.user_behavior import UserFavorite
from app.exceptions import DatabaseIntegrityException


async def create_favorite(db: AsyncSession, user_id: UUID, room_id: UUID) -> UserFavorite:
    """
    创建用户收藏记录。
    - 如果已存在同一 user_id + room_id 的记录，且 is_active=False，则可以恢复为 True。
    - 如果存在 is_active=True 的记录，抛出 DatabaseIntegrityException。
    """
    ...


async def get_favorite(db: AsyncSession, user_id: UUID, room_id: UUID) -> Optional[UserFavorite]:
    """
    根据 user_id 和 room_id 获取单条收藏记录（无论 is_active 状态）。
    """
    ...


async def get_user_favorites(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
) -> List[UserFavorite]:
    """
    获取指定用户的收藏列表（仅返回 is_active=True 的记录）。
    按 created_at 降序排序，限制最大条数。
    """
    ...


async def delete_favorite(db: AsyncSession, user_id: UUID, room_id: UUID) -> bool:
    """
    取消收藏：
    - 如果存在 is_active=True 的记录，则将其 is_active 置为 False。
    - 如果不存在记录，返回 False。
    - 不执行 commit，由 Service 层负责提交事务。
    """
    ...
```

### 4.2 观看历史相关 (WatchHistory)

```python
from app.models.user_behavior import WatchHistory


async def record_watch_history(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    progress: Optional[int] = None,
) -> WatchHistory:
    """
    记录或更新观看历史：
    - 查找当前 user_id + session_id 的最新记录 (is_latest=True)。
    - 如果存在，则将原记录 is_latest=False，并插入一条新记录 is_latest=True。
    - 如果不存在，直接插入新记录 is_latest=True。
    """
    ...


async def list_watch_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
) -> List[WatchHistory]:
    """
    获取用户的观看历史（只返回 is_latest=True 的记录），按 watched_at 降序。
    """
    ...
```

### 4.3 订阅提醒相关 (UserSubscription)

```python
from app.models.user_behavior import UserSubscription, SubscriptionTargetType


async def create_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    room_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> UserSubscription:
    """
    创建订阅记录。
    - 按 (user_id, target_type, room_id, session_id) 保证唯一。
    - 如果存在 is_active=False 的相同记录，可以置为 True 并复用。
    - 如果已存在 is_active=True 的记录，抛出 DatabaseIntegrityException。
    """
    ...


async def get_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    room_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> Optional[UserSubscription]:
    """
    根据 user_id + target 条件获取单条订阅记录（无论 is_active 状态）。
    """
    ...


async def list_subscriptions(
    db: AsyncSession,
    user_id: UUID,
    target_type: Optional[SubscriptionTargetType] = None,
    only_active: bool = True,
) -> List[UserSubscription]:
    """
    获取用户的订阅列表。
    - 可选按 target_type 过滤；
    - 默认只返回 is_active=True 的记录。
    """
    ...


async def cancel_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    room_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> bool:
    """
    取消订阅：
    - 查找匹配的订阅记录，将 is_active 置为 False。
    - 如果未找到匹配记录，返回 False。
    """
    ...
```

---

## 5. 日志与错误处理规范

- 使用 `logging.getLogger(__name__)` 获取模块级 logger；  
- 记录关键操作时对 `user_id` / `room_id` / `session_id` / 订阅 ID 等 UUID 只记录前 8 位：  

```python
logger.info(
    "创建收藏成功: user_id=%s, room_id=%s, favorite_id=%s",
    str(user_id)[:8],
    str(room_id)[:8],
    str(favorite.id)[:8],
)
```

- **🚨 [强制要求] 异常处理（最高优先级）**：
  - **所有写操作**（create, update, remove, batch_add）**必须**包含完整的 `try/except IntegrityError/finally` 块，并处理 `db.rollback()`（见母版 `crud_service_endpoint代码生成提示词母版.md` 第1222行）
  - **UPDATE + INSERT 操作**（如 `record_watch_history`）**必须**有异常处理，因为可能遇到外键约束、数据库连接错误等
  - **捕获 `IntegrityError`** 时，构造 `DatabaseIntegrityException`，错误消息中说明冲突原因（例如："收藏已存在"、"订阅已存在"），并执行 `await db.rollback()`
  - **捕获通用 `Exception`** 时，执行 `await db.rollback()` 并记录错误日志
  - **示例**（适用于所有写操作）：
    ```python
    try:
        # 数据库操作（如 db.add(), await db.flush()）
        await db.flush()
        await db.refresh(new_obj)
        logger.info("操作成功: ...")
        return new_obj
    except IntegrityError as e:
        await db.rollback()
        logger.error("操作失败（唯一性约束）: ...")
        raise DatabaseIntegrityException("资源已存在") from e
    except Exception as e:
        await db.rollback()
        logger.error("操作失败（数据库错误）: ...")
        raise DatabaseOperationException("数据库操作失败") from e
    ```  

---

## 6. 代码风格与结构

- 所有 CRUD 函数集中在 `app/crud/user_behavior.py` 中；  
- 避免在 CRUD 层执行复杂业务逻辑（例如权限判断、组合多个表的业务规则），这些放在 Service 层；  
- 严格使用类型注解、文档字符串，便于后续自动生成测试用例。*** End Patch***}"/>
