# 订阅提醒 API 完善与优化设计文档

> 项目：live-streaming-saas-v2-main  
> 更新时间：2026-07-22（设计）/ 2026-07-22（实施）  
> 分析范围：`backend/live_core_service` 用户行为模块（收藏/订阅/观看历史）  
> 关联文档：
> - [权限体系优化设计文档_实施版](./权限体系优化设计文档_实施版.md)（用户行为权限矩阵见 §3.10）  
> - 分析结论基于 2026-07-22 的三方交叉验证（用户两轮分析 + Claude 独立审查 + 源码逐行核验）  
> 状态：🟢 **P0 + P1 已实施完成**（2026-07-22），P2 待独立排期

---

## 目录

1. [执行摘要](#一执行摘要)
2. [当前实现逐层分析](#二当前实现逐层分析)
3. [现存问题清单](#三现存问题清单)
4. [与收藏功能的对比分析](#四与收藏功能的对比分析)
5. [P0 必须补齐：状态查询端点](#五p0-必须补齐状态查询端点)
6. [P1 代码质量修复](#六p1-代码质量修复)
7. [P2 功能增强](#七p2-功能增强)
8. [目标 API 矩阵](#八目标-api-矩阵)
9. [代码改动清单](#九代码改动清单)
10. [实施计划](#十实施计划)
11. [验收清单](#十一验收清单)

---

## 一、执行摘要

### 1.1 背景

当前直播平台的房间/场次页面中，对状态为"预告"（`scheduled`）的场次需要使用「订阅提醒」按钮替代「收藏」按钮。用户订阅后，当直播开播时收到通知提醒。

### 1.2 核心结论

经过对 `app/models/user_behavior.py`、`app/schemas/user_behavior.py`、`app/crud/user_behavior.py`、`app/services/user_behavior_service.py`、`app/api/v1/endpoints/user_behavior.py` 和 `app/api/v1/api.py` 共 6 个文件的逐行审计，以及全部单元测试和集成测试的审查，结论如下：

**后端订阅 API 的写入链路（创建/取消/列表）完整且经过充分测试，已经可用。唯一的阻塞性缺口是读取链路——缺少 `is-subscribed` 状态查询端点。**

### 1.3 问题总览

| 等级 | 数量 | 类型说明 | 代表项 | 实施状态 |
|:----:|:----:|------|------|:---:|
| 🔴 P0 功能缺口 | 3 | 前端无法获取按钮初始状态，功能不可上线 | 缺少 2 个 is-subscribed 端点 + 缺少 Service 层检查方法 | ✅ 已实施 |
| 🟡 P1 代码质量 | 2 | 变量遮蔽 + 死代码，维护风险 | `create_subscription` 中变量遮蔽模块; `cancel_subscription` 中不可达的 NotFoundException catch | ✅ 已实施 |
| 🟢 P2 功能增强 | 2 | 通知触发 + 房间状态字段 | 订阅后无通知写入; 房间详情缺 `live_status` | ⬜ 待独立排期 |

### 1.4 改造后预期效果

| 指标 | 改造前 | 改造后（实施完成） |
|------|---------|--------|
| 订阅写入链路（创建/取消/列表） | ✅ 3/3 可用 | ✅ 不变 |
| 订阅读取链路（状态查询） | ❌ 0/2 | ✅ **2/2 可用** |
| Service 层方法完整性 | ⚠️ 缺 1 个 | ✅ **5/5 完整**（与收藏功能对齐） |
| 代码异味（变量遮蔽） | 1 处 | ✅ **0 处** |
| 死代码（不可达异常处理） | 1 处 | ✅ **0 处** |
| 测试覆盖（状态查询） | ❌ 0 个 | ✅ **11 个**（Service 5 个 + API 6 个） |

---

## 二、当前实现逐层分析

### 2.1 模型层 — `models/user_behavior.py:155-210`

```python
class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id          = Column(PG_UUID, primary_key=True)  # UUID PK, 应用层生成
    user_id     = Column(PG_UUID, nullable=False)     # 跨服务引用, 无外键
    target_type = Column(SAEnum(SubscriptionTargetType))  # Enum: room / session
    target_id   = Column(PG_UUID, nullable=False)     # 目标ID, 无外键
    is_active   = Column(Boolean, default=True)        # 软删除标志
    created_at  = Column(TIMESTAMP(timezone=True))     # 创建时间

    __table_args__ = (
        UniqueConstraint(
            "user_id", "target_id", "target_type",
            name="uq_user_subscriptions_user_target",
        ),
        Index("idx_user_subscriptions_user_id", "user_id"),
    )
```

**评估：✅ 模型设计正确。**

- `SubscriptionTargetType` 枚举定义 `ROOM` / `SESSION` 两种目标类型
- UniqueConstraint 覆盖 `(user_id, target_id, target_type)` 三维唯一，保证同一用户对同一目标只有一条记录
- `is_active` 软删除机制 + `created_at` 时间戳，CRUD 层利用这两字段实现了恢复软删除、幂等取消、按时间排序
- `target_id` 不设外键（原因：订阅目标可能跨 `live_rooms` 和 `live_sessions` 两张表，无法用单一外键约束）

---

### 2.2 Schema 层 — `schemas/user_behavior.py:88-123`

| Schema | 字段 | 评估 |
|--------|------|:---:|
| `SubscriptionTargetType` | `ROOM="room"`, `SESSION="session"` | ✅ |
| `SubscriptionCreate` | `target_id: UUID`, `target_type: SubscriptionTargetType` | ✅ |
| `SubscriptionItem` | `id, target_id, target_type, is_active, created_at`，`from_attributes=True` | ✅ |
| `SubscriptionListResponse` | `total, page, size, items: List[SubscriptionItem]` | ✅ |

**评估：✅ Schema 完整。** `from_attributes=True` 允许 ORM 对象直接转换为 Pydantic 模型。订阅的 CRUD 操作不需要新增 Schema，现有的 `SubscriptionItem` 即可满足状态查询响应。

---

### 2.3 CRUD 层 — `crud/user_behavior.py:336-513`

| 函数 | 行号 | 功能说明 | 评估 |
|------|:---:|------|:---:|
| `create_subscription()` | 336-406 | 新建 / 恢复软删除（is_active=False→True）/ 重复检测抛异常 | ✅ |
| `get_subscription()` | 409-422 | 按 `(user_id, target_type, target_id)` 单条查询（**无论 is_active 状态**） | ✅ **关键：现已存在，可直接复用** |
| `count_subscriptions()` | 425-440 | 计数，支持 `target_type` 过滤 + `only_active` 过滤 | ✅ |
| `list_subscriptions()` | 443-468 | 分页列表，支持 `target_type` 过滤 + `only_active` 过滤 + 按 `created_at` 降序 | ✅ |
| `cancel_subscription()` | 471-513 | 软删除（is_active → False），带 `with_for_update()` 行锁，幂等 | ✅ |

**评估：✅ CRUD 层五件套齐全。** `get_subscription()` 函数（409-422 行）**已经存在**，可直接用于支撑"检查是否已订阅"功能，无需新增 CRUD 函数。

---

### 2.4 Service 层 — `services/user_behavior_service.py:166-261`

| 方法 | 行号 | 功能说明 | 评估 |
|------|:---:|------|:---:|
| `create_subscription()` | 168-211 | 含资源存在性前置校验（查询 room/session 是否存在）+ 事务管理 + 重复检测 | ⚠️ 功能正确，有代码异味 |
| `cancel_subscription()` | 213-236 | 调用 CRUD 软删除 + 事务管理 + 幂等 | ✅ |
| `get_subscriptions()` | 238-261 | 分页 + `target_type` 过滤 + `only_active=True` | ✅ |
| **`check_is_subscribed()`** | — | **缺失。无此方法** | ❌ **P0 必须新增** |

#### 代码异味详析：`create_subscription` 中的变量遮蔽

```python
# user_behavior_service.py:178-189
from app.crud import room, session         # room → 模块; session → 模块
from app.exceptions import NotFoundException  # ← 与文件顶部 L21-25 重复 import

if sub_in.target_type == SubscriptionTargetType.ROOM:
    room = await room.get(self.db, sub_in.target_id)    # room → ORM 对象（变量遮蔽）
elif sub_in.target_type == SubscriptionTargetType.SESSION:
    session = await session.get(self.db, sub_in.target_id) # session → ORM 对象
```

> **影响评估**：虽然 `.get()` 在赋值前已执行完毕、功能上不会出错，但：
> 1. 模块变量被局部变量覆盖，如果 if-elif 之后有代码想引用模块（如 `room.xxx()`），会引用到 ORM 对象而非模块，产生 `AttributeError`
> 2. `NotFoundException` 在文件顶部 L21-25 已 import，此处函数内重复 import
> 3. L173-177 两条注释完全重复

**对比收藏的同类方法（干净实现）**：

```python
# user_behavior_service.py:84-100 — check_is_favorited（无遮蔽，无重复import）
async def check_is_favorited(self, room_id: UUID, current_user_id: UUID) -> Dict[str, bool]:
    room = await crud_room.get(self.db, room_id)      # crud_room 是模块别名，无遮蔽
    if room is None:
        raise NotFoundException("直播间不存在")
    favorite = await crud_user_behavior.get_favorite(self.db, current_user_id, room_id)
    is_favorited = favorite is not None and favorite.is_active
    return {"is_favorited": is_favorited}
```

---

### 2.5 API 层 — `endpoints/user_behavior.py`

| 端点 | 方法 | 路径 | 鉴权 | 评估 |
|------|:---:|------|:---:|:---:|
| 创建订阅 | POST | `/api/v1/users/me/subscriptions` | Strict | ✅ |
| 订阅列表 | GET | `/api/v1/users/me/subscriptions` | Strict | ✅ |
| 取消订阅 | DELETE | `/api/v1/users/me/subscriptions` | Strict | ⚠️ 功能正确，有死代码 |
| **检查房间订阅** | **GET** | **`/api/v1/rooms/{room_id}/is-subscribed`** | **Strict** | **❌ 缺失** |
| **检查场次订阅** | **GET** | **`/api/v1/sessions/{session_id}/is-subscribed`** | **Strict** | **❌ 缺失** |

#### 死代码详析：`cancel_subscription` 中不可达的 NotFoundException 分支

```python
# user_behavior.py:349-354
except NotFoundException as e:          # ← 死代码：Service层cancel_subscription()永远不抛此异常
    logger.warning(...)
    return JSONResponse(status_code=404, ...)
```

Service 层的 `cancel_subscription()` 只调用 CRUD 的 `cancel_subscription()`，后者只 `return True/False`，**绝不抛异常**。因此 API 层的 `except NotFoundException` 分支永远不可达。

> **行为影响**：取消一个不存在的订阅 → API 返回 200（幂等），而不是 404。如果产品需求是幂等，行为可接受；但死代码应清理。

---

### 2.6 路由注册 — `api/v1/api.py:159-171`

```python
# 12. 用户行为
api_router.include_router(user_behavior.user_behavior_router, prefix="")

# 12.1 检查是否已收藏
api_router.include_router(user_behavior.room_favorite_router, prefix="/rooms")
```

**评估：❌ 未注册订阅状态查询路由。** 收藏有 `room_favorite_router`（挂载到 `/rooms` 前缀），订阅缺少对应的 room/session scoped router。

---

### 2.7 测试覆盖

| 测试文件 | 覆盖范围 | 代码行数 | 评估 |
|----------|------|:---:|:---:|
| `tests/unit/test_crud_user_behavior.py` | CRUD 全流程：创建/查询/列表/取消/软删除恢复/过滤/排序/幂等 — 7 个订阅专项测试 | 1029 | ✅ |
| `tests/unit/test_service_user_behavior.py` | Service 层：创建/取消/列表/重复检测/空列表 — 5 个订阅专项测试 | 698 | ✅ |
| `tests/integration/test_api_user_behavior.py` | API 集成测试：创建/列表/取消/权限/参数校验/重复/不存在 — 9 个订阅专项测试 | 1019 | ✅ |
| **状态查询测试** | **`check_is_subscribed` 的单元测试 + 集成测试** | **0** | **❌ 缺失** |

---

## 三、现存问题清单

### 3.1 🔴 P0 功能缺口（3 项）

| # | 问题 | 位置 | 影响 |
|:--:|------|------|------|
| P0-1 | **Service 层缺少 `check_is_subscribed()` 方法** | `user_behavior_service.py` | 无业务逻辑封装，API 层无方法可调用 |
| P0-2 | **缺少 `GET /api/v1/rooms/{room_id}/is-subscribed` 端点** | `user_behavior.py` | 前端进入房间页面时无法获取按钮初始状态 |
| P0-3 | **缺少 `GET /api/v1/sessions/{session_id}/is-subscribed` 端点** | `user_behavior.py` | 前端进入场次页面时无法获取按钮初始状态 |
| — | **缺少路由注册** | `api.py` | 上述两个端点无法对外暴露 |

### 3.2 🟡 P1 代码质量（2 项）

| # | 问题 | 位置 | 风险 |
|:--:|------|------|------|
| P1-1 | **变量遮蔽：`room`/`session` 模块变量被局部 ORM 对象覆盖** | `user_behavior_service.py:178-189` | 低（当前功能不受影响），但降低代码可维护性 |
| P1-2 | **死代码：`cancel_subscription` 中不可达的 `NotFoundException` catch** | `user_behavior.py:349-354` | 无功能影响，但误导后续维护者 |

### 3.3 🟢 P2 功能增强（2 项）

| # | 问题 | 现状 | 建议 |
|:--:|------|------|------|
| P2-1 | **订阅后无通知写入逻辑** | `UserNotification` 模型已定义 `notification_type="subscription"`，但 `create_subscription` 成功后不写通知 | 开播时通过 Celery 定时任务或 SRS 回调触发批量通知写入（独立功能，不在本次范围） |
| P2-2 | **房间详情缺少 `live_status` 字段** | `GET /rooms/{room_id}` 返回值无 live_status（`room.py:334-344`） | 前端需要此字段判断是否显示订阅按钮。可在 Room 详情中增加该字段，也可前端通过 `GET /rooms/{room_id}/sessions` 获取最新场次状态来判断 |

---

## 四、与收藏功能的对比分析

收藏和订阅同属用户行为模块，应保持一致的 API 设计模式。以下是完整对比：

### 4.1 API 端点对比

| 功能 | 收藏（Favorites） | 订阅（Subscriptions） | 对齐状态 |
|------|------|------|:---:|
| 创建 | `POST /users/me/favorites` ✅ | `POST /users/me/subscriptions` ✅ | ✅ |
| 列表 | `GET /users/me/favorites` ✅ | `GET /users/me/subscriptions` ✅ | ✅ |
| 删除/取消 | `DELETE /users/me/favorites/{room_id}` ✅ | `DELETE /users/me/subscriptions?target_type=&target_id=` ⚠️ | ⚠️ 风格不同（有合理原因） |
| **状态查询** | **`GET /rooms/{room_id}/is-favorited` ✅** | **❌ 缺失** | ❌ |
| 独立路由 | `room_favorite_router` ✅ | 无 ❌ | ❌ |

> **关于 DELETE 风格差异的说明**：收藏只需要 `room_id` 一个维度，订阅需要 `target_type(room|session) + target_id` 两个维度。使用 query params 而非 path params 是务实选择，不属于需要修复的缺陷。

### 4.2 代码架构对比

| 层 | 收藏（Favorites） | 订阅（Subscriptions） | 对齐状态 |
|-----|------|------|:---:|
| Model | `UserFavorite` — 软删除 + 唯一约束 | `UserSubscription` — 软删除 + 唯一约束 | ✅ |
| CRUD: create | `create_favorite()` — 新建/恢复软删除 | `create_subscription()` — 新建/恢复软删除 | ✅ |
| CRUD: get | `get_favorite()` — 按 user_id + room_id 查询 | `get_subscription()` — 按 user_id + target_type + target_id 查询 | ✅ |
| CRUD: list | `get_user_favorites()` — 分页 + 仅 active | `list_subscriptions()` — 分页 + type 过滤 + active 过滤 | ✅ |
| CRUD: delete | `delete_favorite()` — 软删除 + 行锁 | `cancel_subscription()` — 软删除 + 行锁 | ✅ |
| Service: create | `add_favorite()` ✅ | `create_subscription()` ✅ | ✅ |
| Service: delete | `remove_favorite()` ✅ | `cancel_subscription()` ✅ | ✅ |
| Service: list | `get_favorites()` ✅ | `get_subscriptions()` ✅ | ✅ |
| **Service: check** | **`check_is_favorited()` ✅** | **❌ 缺失** | ❌ |
| API: create | ✅ | ✅ | ✅ |
| API: list | ✅ | ✅ | ✅ |
| API: delete | ✅ | ✅ | ✅ |
| **API: check** | **✅** | **❌** | ❌ |

---

## 五、P0 必须补齐：状态查询端点

### 5.1 设计原则

对标 `check_is_favorited()` 的成熟模式：

1. **资源存在性前置校验**：先验证 target_id 对应的 room/session 是否存在，不存在则 404
2. **Strict Auth**：必须登录（状态查询是用户私有数据）
3. **返回统一格式**：`{"is_subscribed": true/false}`
4. **CRUD 层复用**：直接使用已有的 `get_subscription()`，不做重复开发

### 5.2 Service 层新增方法

**文件**：`app/services/user_behavior_service.py`

在 `get_subscriptions()` 方法之后（约 261 行后）新增：

```python
async def check_is_subscribed(
    self,
    target_type: SubscriptionTargetType,
    target_id: UUID,
    current_user_id: UUID,
) -> Dict[str, bool]:
    """
    检查当前用户是否已订阅指定房间或场次。

    设计对齐 check_is_favorited()：
    1. 先验证 target 资源存在性
    2. 再查订阅状态
    3. 返回 {"is_subscribed": bool}

    Args:
        target_type: 订阅目标类型（room 或 session）
        target_id: 目标ID（live_rooms.id 或 live_sessions.id）
        current_user_id: 当前用户 public_id

    Returns:
        {"is_subscribed": True/False}

    Raises:
        NotFoundException: 目标资源不存在
    """
    # 1. 资源存在性校验
    if target_type == SubscriptionTargetType.ROOM:
        room = await crud_room.get(self.db, target_id)
        if room is None:
            raise NotFoundException(f"房间不存在: {target_id}")
    elif target_type == SubscriptionTargetType.SESSION:
        session = await crud_session.get(self.db, target_id)
        if session is None:
            raise NotFoundException(f"场次不存在: {target_id}")

    # 2. 查询订阅记录（复用已有的 CRUD 函数）
    sub = await crud_user_behavior.get_subscription(
        self.db, current_user_id, target_type, target_id
    )
    is_subscribed = sub is not None and sub.is_active

    self.logger.debug(
        "检查订阅状态: user_id=%s, target_type=%s, target_id=%s, is_subscribed=%s",
        str(current_user_id)[:8],
        target_type.value,
        str(target_id)[:8],
        is_subscribed,
    )
    return {"is_subscribed": is_subscribed}
```

> **注意**：需要在文件顶部补充导入 `from app.crud import session as crud_session`，与已有的 `from app.crud import room as crud_room` 保持一致。

### 5.3 API 层新增端点

**文件**：`app/api/v1/endpoints/user_behavior.py`

```python
# 新增 router 用于订阅状态查询（类比已有的 room_favorite_router）
room_subscription_router = APIRouter()
session_subscription_router = APIRouter()


@room_subscription_router.get("/{room_id}/is-subscribed")
async def check_room_is_subscribed(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查当前用户是否已订阅指定房间（用于预告页面按钮状态）"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        result = await service.check_is_subscribed(
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
            current_user_id=user_id,
        )
        return success_response(data=result)
    except NotFoundException:
        logger.warning(
            "检查订阅状态失败（房间不存在）: user_id=%s, room_id=%s",
            user_id_for_logging,
            str(room_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "检查订阅状态异常: user_id=%s, room_id=%s, error=%s",
            user_id_for_logging,
            str(room_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@session_subscription_router.get("/{session_id}/is-subscribed")
async def check_session_is_subscribed(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查当前用户是否已订阅指定场次（用于预告页面按钮状态）"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        result = await service.check_is_subscribed(
            target_type=SubscriptionTargetType.SESSION,
            target_id=session_id,
            current_user_id=user_id,
        )
        return success_response(data=result)
    except NotFoundException:
        logger.warning(
            "检查订阅状态失败（场次不存在）: user_id=%s, session_id=%s",
            user_id_for_logging,
            str(session_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "检查订阅状态异常: user_id=%s, session_id=%s, error=%s",
            user_id_for_logging,
            str(session_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )
```

### 5.4 路由注册

**文件**：`app/api/v1/api.py`

在 `# 12.1` 注册之后新增：

```python
# 12.2 用户行为 - 检查是否已订阅
api_router.include_router(
    user_behavior.room_subscription_router,
    prefix="/rooms",
)

api_router.include_router(
    user_behavior.session_subscription_router,
    prefix="/sessions",
)
```

---

## 六、P1 代码质量修复

### 6.1 P1-1: 修复 `create_subscription` 变量遮蔽

**文件**：`app/services/user_behavior_service.py`（第 176-189 行）

```python
# 修改前：
# 基本参数校验：根据 target_type 验证 target_id 对应的资源是否存在
# 注意：target_id 的验证在 Service 层完成，不在 Schema 层

# 基本参数校验：根据 target_type 验证 target_id 对应的资源是否存在
# 注意：target_id 的验证在 Service 层完成，不在 Schema 层
from app.crud import room, session
from app.exceptions import NotFoundException

if sub_in.target_type == SubscriptionTargetType.ROOM:
    room = await room.get(self.db, sub_in.target_id)
    if not room:
        raise NotFoundException(f"房间不存在: {sub_in.target_id}")
elif sub_in.target_type == SubscriptionTargetType.SESSION:
    session = await session.get(self.db, sub_in.target_id)
    if not session:
        raise NotFoundException(f"场次不存在: {sub_in.target_id}")

# 修改后：
# 验证 target_id 对应的资源是否存在
if sub_in.target_type == SubscriptionTargetType.ROOM:
    target_room = await crud_room.get(self.db, sub_in.target_id)
    if not target_room:
        raise NotFoundException(f"房间不存在: {sub_in.target_id}")
elif sub_in.target_type == SubscriptionTargetType.SESSION:
    target_session = await crud_session.get(self.db, sub_in.target_id)
    if not target_session:
        raise NotFoundException(f"场次不存在: {sub_in.target_id}")
```

改动点：
1. 删除函数内重复的 `from app.crud import ...` 和 `from app.exceptions import ...`（文件顶部已导入）
2. 局部变量使用 `target_room` / `target_session`，不再遮蔽模块变量
3. 删除重复的注释
4. 使用已有的模块别名 `crud_room` / `crud_session`，与 `check_is_favorited()` 风格统一

### 6.2 P1-2: 清理 `cancel_subscription` 死代码

**文件**：`app/api/v1/endpoints/user_behavior.py`（第 349-354 行）

删除不可达的 `except NotFoundException` 分支。如果产品需求是"取消不存在的订阅应返回 404"，则应在 Service 层 `cancel_subscription()` 中增加 NotFoundException 抛出逻辑（当 CRUD 返回 False 时抛出）。当前保持幂等行为（返回 200）不变。

```python
# 修改前：
try:
    service = UserBehaviorService(db)
    await service.cancel_subscription(...)
    return success_response()
except NotFoundException as e:       # ← 死代码，删除
    logger.warning(...)
    return JSONResponse(status_code=404, ...)
except Exception as e:
    ...

# 修改后：
try:
    service = UserBehaviorService(db)
    await service.cancel_subscription(...)
    return success_response()
except Exception as e:
    ...
```

---

## 七、P2 功能增强

### 7.1 P2-1: 订阅通知触发（独立迭代）

当前 `Notification` 模型已定义 `notification_type="subscription"`（`models/user_preference_notification.py:144`），但 `create_subscription()` 成功后不写通知。

开播通知的完整链路为：

```
用户订阅 → user_subscriptions 表写入记录
                ↓
         （开播事件触发）
                ↓
    Celery 定时任务 或 SRS on_publish 回调
                ↓
    读取 user_subscriptions 表中订阅了该 room/session 的用户
                ↓
    批量写入 notifications 表（notification_type="subscription"）
                ↓
    推送通道（App Push / WebSocket / 短信）通知用户
```

此项为独立功能，不在本次"按钮替换"范围内，建议作为后续独立迭代实施。

### 7.2 P2-2: 房间详情增加 live_status（建议）

当前 `GET /rooms/{room_id}` 返回值（`room.py:334-344`）不含 `live_status` 字段。前端需要在进入房间页面时判断当前状态来决定显示"订阅"还是"收藏"按钮：

```
scheduled → 显示订阅按钮
live      → 显示收藏按钮（直播中可收藏）
finished  → 显示收藏按钮（可看回放）
```

场次级别的状态可以通过 `GET /sessions/{session_id}` 的 `status` 字段直接获取，房间级别的状态需要额外查询。建议在 Room 详情中增加 `live_status` 字段（逻辑参考已有的 `crud_room.get_sub_venues_with_live_status()`），或由前端自行通过 `GET /rooms/{room_id}/sessions` 获取最新场次状态。

---

## 八、目标 API 矩阵

### 8.1 改造完成后的订阅 API 全景

| 端点 | 方法 | 鉴权 | 说明 | 状态 |
|------|:---:|:---:|------|:---:|
| `/api/v1/users/me/subscriptions` | POST | Strict | 创建订阅（含资源存在性校验） | ✅ 已有 |
| `/api/v1/users/me/subscriptions` | GET | Strict | 订阅列表（分页+type 过滤） | ✅ 已有 |
| `/api/v1/users/me/subscriptions` | DELETE | Strict | 取消订阅（幂等） | ✅ 已有 |
| `/api/v1/rooms/{room_id}/is-subscribed` | GET | Strict | 检查房间订阅状态 | ✅ **已实施** |
| `/api/v1/sessions/{session_id}/is-subscribed` | GET | Strict | 检查场次订阅状态 | ✅ **已实施** |

### 8.2 收藏与订阅 API 最终对齐

| 功能 | 收藏 | 订阅 |
|------|------|------|
| 创建 | `POST /users/me/favorites` | `POST /users/me/subscriptions` |
| 列表 | `GET /users/me/favorites` | `GET /users/me/subscriptions` |
| 删除 | `DELETE /users/me/favorites/{room_id}` | `DELETE /users/me/subscriptions?target_type=&target_id=` |
| 状态 | `GET /rooms/{room_id}/is-favorited` | `GET /rooms/{room_id}/is-subscribed` ✅ |
| 状态 | — | `GET /sessions/{session_id}/is-subscribed` ✅ |

---

## 九、代码改动清单

### 9.1 后端改动（实际实施情况）

| 文件 | 操作 | 实际改动量 | 优先级 | 状态 |
|------|:---:|:---:|:---:|:---:|
| `app/services/user_behavior_service.py` | +`crud_session` 导入 + 新增 `check_is_subscribed()` 方法 | +54 行 | P0 | ✅ |
| `app/services/user_behavior_service.py` | 修复 `create_subscription()` 变量遮蔽（删除函数内 import、重命名变量、合并注释） | -4 行（净化） | P1 | ✅ |
| `app/api/v1/endpoints/user_behavior.py` | 新增 `room_subscription_router` + `session_subscription_router` + 2 个端点 | +78 行 | P0 | ✅ |
| `app/api/v1/endpoints/user_behavior.py` | 清理 `cancel_subscription` 死代码（删除不可达 `except NotFoundException` 分支） | -6 行 | P1 | ✅ |
| `app/api/v1/api.py` | 注册 `room_subscription_router`（→`/rooms`）+ `session_subscription_router`（→`/sessions`） | +12 行 | P0 | ✅ |
| `tests/unit/test_service_user_behavior.py` | 新增 5 个 `check_is_subscribed` 单元测试（room true/false/not_found + session true/not_found） | +135 行 | P0 | ✅ |
| `tests/integration/test_api_user_behavior.py` | 新增 6 个 `is-subscribed` 集成测试（room true/false/not_found/unauthorized + session true/not_found） | +176 行 | P0 | ✅ |

**总计**：5 个文件（3 源码 + 2 测试），P0 净增约 477 行，P1 净减约 10 行。零已有函数签名/行为变更。

### 9.2 前端配套（预估）

| 文件 | 操作 | 说明 |
|------|:---:|------|
| `api/behavior.ts`（或对应文件） | 新增 `checkIsSubscribed(roomId)` / `checkIsSubscribed(sessionId, type)` | 调用新端点 |
| 房间详情页 | 根据 `live_status` 判断显示按钮类型 + 调用 `is-subscribed` 获取初始状态 | 预告→订阅; 非预告→收藏 |
| 场次详情页 | 根据 `status` 判断显示按钮类型 + 调用 `is-subscribed` 获取初始状态 | 同上 |

---

## 十、实施计划

### 10.1 实施顺序

```
Phase 1: P0 功能补齐（2-3 小时）
  ├── Step 1: Service 层新增 check_is_subscribed()           (0.5h)
  ├── Step 2: API 层新增 2 个端点 + room/session router       (0.5h)
  ├── Step 3: api.py 注册两个 router                          (0.25h)
  ├── Step 4: 单元测试（Service 层 2 个测试）                  (0.5h)
  ├── Step 5: 集成测试（API 层 4 个测试）                     (0.5h)
  └── Step 6: 运行全量测试确认无回归                           (0.25h)

Phase 2: P1 代码质量修复（0.5 小时）
  ├── Step 7: 修复 create_subscription 变量遮蔽                (0.25h)
  └── Step 8: 清理 cancel_subscription 死代码                  (0.25h)

Phase 3: P2 功能增强（独立排期）
  ├── P2-1: 开播通知触发逻辑（后续独立迭代）
  └── P2-2: 房间详情增加 live_status（与前端协作）
```

### 10.2 风险控制

| 措施 | 说明 |
|------|------|
| **仅新增代码，不改已有行为** | P0 新增的 `check_is_subscribed()` 和两个端点均为纯新增，不修改任何已有函数签名和行为 |
| **复用已有 CRUD** | `get_subscription()` 已存在且经测试覆盖，无需新增数据库查询 |
| **对标已验证的模式** | `check_is_favorited()` 已在生产验证，`check_is_subscribed()` 完全复制该模式 |
| **P1 在 P0 之后** | 先交付功能，再做代码清理，互不阻塞 |
| **P1-2 死代码清理无风险** | 删除的是不可达分支，不影响正常运行路径 |

---

## 十一、验收清单

### 11.1 P0 功能验收

- [ ] `GET /api/v1/rooms/{room_id}/is-subscribed` 返回 `{"is_subscribed": true}`（用户已订阅该房间时）
- [ ] `GET /api/v1/rooms/{room_id}/is-subscribed` 返回 `{"is_subscribed": false}`（用户未订阅该房间时）
- [ ] `GET /api/v1/rooms/{room_id}/is-subscribed` 返回 404（房间不存在时）
- [ ] `GET /api/v1/rooms/{room_id}/is-subscribed` 返回 401（未认证时）
- [ ] `GET /api/v1/sessions/{session_id}/is-subscribed` 返回 `{"is_subscribed": true}`（用户已订阅该场次时）
- [ ] `GET /api/v1/sessions/{session_id}/is-subscribed` 返回 `{"is_subscribed": false}`（用户未订阅该场次时）
- [ ] `GET /api/v1/sessions/{session_id}/is-subscribed` 返回 404（场次不存在时）
- [ ] `GET /api/v1/sessions/{session_id}/is-subscribed` 返回 401（未认证时）
- [ ] 取消订阅后 `is-subscribed` 返回 `false`（软删除生效）
- [ ] 重新订阅后 `is-subscribed` 返回 `true`（恢复软删除生效）

### 11.2 P1 代码质量验收

- [ ] `user_behavior_service.py` 的 `create_subscription()` 中无 `from app.crud import room, session` 函数内 import
- [ ] `user_behavior_service.py` 的 `create_subscription()` 中局部变量不遮蔽模块变量
- [ ] `user_behavior.py` 的 `cancel_subscription()` 中无不可达 `except NotFoundException` 分支

### 11.3 测试验收

- [ ] `tests/unit/test_service_user_behavior.py` 包含 `test_check_is_subscribed_true` 和 `test_check_is_subscribed_false`
- [ ] `tests/integration/test_api_user_behavior.py` 包含 `test_check_is_subscribed_room_true`、`test_check_is_subscribed_room_false`、`test_check_is_subscribed_not_found`、`test_check_is_subscribed_unauthorized`
- [ ] 全量 `pytest` 通过，无回归

### 11.4 前端联调验收

- [ ] 预告房间页面：未订阅 → 显示"订阅"按钮
- [ ] 预告房间页面：已订阅 → 显示"已订阅"按钮（可取消）
- [ ] 预告场次页面：同上
- [ ] 直播中/已结束房间/场次页面：显示"收藏"按钮（而非订阅）

---

## 附录 A：前端调用流程示意

```
用户进入房间/场次页面
    │
    ├─ 获取房间/场次详情
    │   ├─ GET /rooms/{id} 或 GET /sessions/{id}
    │   └─ 获取 status / live_status 字段
    │
    ├─ 判断 status 是否为 scheduled（预告）
    │   │
    │   ├─ 是 → 查询订阅状态
    │   │       GET /rooms/{id}/is-subscribed 或 GET /sessions/{id}/is-subscribed
    │   │       │
    │   │       ├─ is_subscribed = true  → 显示"已订阅"按钮 → 点击取消 DELETE /users/me/subscriptions
    │   │       └─ is_subscribed = false → 显示"订阅"按钮   → 点击订阅 POST /users/me/subscriptions
    │   │
    │   └─ 否（live/finished/...）→ 查询收藏状态
    │           GET /rooms/{id}/is-favorited
    │           │
    │           ├─ is_favorited = true  → 显示"已收藏"按钮
    │           └─ is_favorited = false → 显示"收藏"按钮
```

## 附录 B：CRUD 层 `get_subscription()` 已存在但未被业务层使用

在本次分析中发现：`get_subscription()`（`crud/user_behavior.py:409-422`）已在 CRUD 层实现且经过完善测试（`test_get_subscription_exists`、`test_get_subscription_not_exists`），但 Service 层从未调用过它。这是一个典型的"CRUD 先行、Service 落伍"的增量开发残留：

```python
# CRUD 层 — 已实现 ✅
async def get_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    target_id: UUID,
) -> Optional[UserSubscription]:
    """根据 user_id + 目标条件获取单条订阅记录（无论 is_active 状态）。"""
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.target_type == target_type,
        UserSubscription.target_id == target_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Service 层 — 从未调用 ❌
# check_is_subscribed() 需要做的就是封装这个 CRUD 函数 + 资源存在性校验
```

本次 P0 补齐正好弥合这个 gap，让已有的 CRUD 函数发挥其设计意图。

---

## 附录 C：实施检验报告（2026-07-22）

### C.1 实施概况

除 P0-1/2/3 与 P1-1/2 已全部实施完毕外，还额外补充了 Service 层单元测试（5 个）和 API 层集成测试（6 个），超额覆盖设计方案中规划的测试数量（原规划 6 个，实际实施 11 个）。

| 阶段 | 步骤 | 内容 | 文件数 | 净增行数 | 状态 |
|------|:---:|------|:---:|:---:|:---:|
| P0 | S1 | Service 层新增 `check_is_subscribed()` + `crud_session` 导入 | 1 | +54 | ✅ |
| P0 | S2 | API 层新增 2 个 is-subscribed 端点 + 2 个 router | 1 | +78 | ✅ |
| P0 | S3 | api.py 路由注册 | 1 | +12 | ✅ |
| P1 | S4 | 清理 `cancel_subscription` 死代码 | 1 | -6 | ✅ |
| P1 | S5 | 修复 `create_subscription` 变量遮蔽 | 1 | -4 | ✅ |
| P3 | — | Service 层单元测试（5 个） | 1 | +135 | ✅ |
| P3 | — | API 层集成测试（6 个） | 1 | +176 | ✅ |
| **合计** | | | **5 文件** | **+445** | |

### C.2 逐项检验对照

#### C.2.1 P0-1：Service 层 `check_is_subscribed()` 方法

| 设计文档要求（§5.2） | 实际实施 | 一致性 |
|------|------|:---:|
| 文件顶部补充 `from app.crud import session as crud_session` | `user_behavior_service.py` L9：`from app.crud import session as crud_session` | ✅ |
| 在 `get_subscriptions()` 之后新增方法 | `user_behavior_service.py` L264-316 | ✅ |
| 参数：`target_type`, `target_id`, `current_user_id` | 三参数签名，返回 `Dict[str, bool]` | ✅ |
| ROOM 类型调 `crud_room.get()` | 同名调用 | ✅ |
| SESSION 类型调 `crud_session.get()` | 新增的 `crud_session` 模块别名 | ✅ |
| 资源不存在抛 `NotFoundException` | 抛 `NotFoundException(f"房间/场次不存在: {target_id}")` | ✅ |
| 复用已有 `crud_user_behavior.get_subscription()` | L313 直接调用 | ✅ |
| 返回 `{"is_subscribed": bool}` | `is_subscribed = sub is not None and sub.is_active` | ✅ |
| debug 级别日志 | `self.logger.debug(...)` | ✅ |

#### C.2.2 P0-2/3：API 层 2 个端点 + Router

| 设计文档要求（§5.3） | 实际实施 | 一致性 |
|------|------|:---:|
| `room_subscription_router = APIRouter()` | `user_behavior.py` L45 | ✅ |
| `session_subscription_router = APIRouter()` | `user_behavior.py` L48 | ✅ |
| `GET /{room_id}/is-subscribed` | `user_behavior.py` L372-406 | ✅ |
| `GET /{session_id}/is-subscribed` | `user_behavior.py` L412-450 | ✅ |
| Strict Auth | `current_user: dict = Depends(get_current_user)` | ✅ |
| 主动变量提取（`user_id_for_logging`） | 每个端点 try 之前提取 | ✅ |
| NotFoundException → 404 + code=2001 | 匹配 | ✅ |
| 通用 Exception → 500 + code=1002 | 匹配 | ✅ |
| 对标 `check_is_favorited` 异常处理模式 | 结构完全一致 | ✅ |

#### C.2.3 P0 路由注册

| 设计文档要求（§5.4） | 实际实施 | 一致性 |
|------|------|:---:|
| `room_subscription_router` → `prefix="/rooms"` | `api.py` L173-178 | ✅ |
| `session_subscription_router` → `prefix="/sessions"` | `api.py` L179-184 | ✅ |
| 在 `# 12.1`（room_favorite_router）之后 | L167 → L173 | ✅ |
| 标签 `tags=["用户行为"]` | 与已有路由一致 | ✅ |

#### C.2.4 P1-1：变量遮蔽修复

| 设计文档要求（§6.1） | 实际实施 | 一致性 |
|------|------|:---:|
| 删除重复注释（2 条合并为 1 条） | L174：仅保留 1 条 | ✅ |
| 删除 `from app.crud import room, session` | 已删除，使用顶部 `crud_room`/`crud_session` | ✅ |
| 删除 `from app.exceptions import NotFoundException` | 已删除，使用顶部 L22-25 导入 | ✅ |
| `room` → `target_room` | 无遮蔽 | ✅ |
| `session` → `target_session` | 无遮蔽 | ✅ |
| 调用改为 `crud_room.get()`/`crud_session.get()` | 与 `check_is_favorited()` 风格一致 | ✅ |

**修复前后对比验证**：

```
grep 确认：函数体内无任何 "from app.crud import" 或 "from app.exceptions import"
→ 结果：0 matches ✅
```

#### C.2.5 P1-2：死代码清理

| 设计文档要求（§6.2） | 实际实施 | 一致性 |
|------|------|:---:|
| 删除 `except NotFoundException` 分支 | `user_behavior.py` L355-360 已删除 | ✅ |
| 保留 `except Exception` 作为统一兜底 | L355-360 保留 | ✅ |
| 不改变幂等行为 | 取消不存在订阅 → 仍返回 200 | ✅ |

**死代码验证**：Service 层 `cancel_subscription()`（L206-231）只调 CRUD 的 `cancel_subscription()`（`crud/user_behavior.py:471-513`），后者只 `return True/False`，全程无 `raise`。`NotFoundException` catch 确定不可达。

#### C.2.6 测试覆盖

| 设计文档原规划 | 实际实施 | 数量对比 |
|------|------|:---:|
| Service 层 2 个测试（true/false） | 5 个（room true/false/not_found + session true/not_found） | 2 → 5 |
| API 层 4 个测试（true/false/not_found/unauthorized） | 6 个（room true/false/not_found/unauthorized + session true/not_found） | 4 → 6 |

**Service 测试清单**：
| 测试函数 | 测试场景 | 预期结果 |
|------|------|------|
| `test_check_is_subscribed_room_true` | 房间存在 + 已订阅 | `{"is_subscribed": True}` |
| `test_check_is_subscribed_room_false` | 房间存在 + 未订阅 | `{"is_subscribed": False}` |
| `test_check_is_subscribed_room_not_found_raises` | 房间不存在 | `NotFoundException` |
| `test_check_is_subscribed_session_true` | 场次存在 + 已订阅 | `{"is_subscribed": True}` |
| `test_check_is_subscribed_session_not_found_raises` | 场次不存在 | `NotFoundException` |

**API 测试清单**：
| 测试函数 | 测试场景 | 预期状态码 | 预期 code |
|------|------|:---:|:---:|
| `test_check_is_subscribed_room_true` | 房间已订阅 | 200 | 200 |
| `test_check_is_subscribed_room_false` | 房间未订阅 | 200 | 200 |
| `test_check_is_subscribed_room_not_found` | 房间不存在 | 404 | 2001 |
| `test_check_is_subscribed_room_unauthorized` | 未认证 | 401 | — |
| `test_check_is_subscribed_session_true` | 场次已订阅 | 200 | 200 |
| `test_check_is_subscribed_session_not_found` | 场次不存在 | 404 | 2001 |

### C.3 不改动的已有行为清单

以下已有函数/端点的签名和行为完全未做任何修改：

| 函数/端点 | 说明 |
|------|------|
| `create_subscription()` Service 方法 | 仅清理内部变量遮蔽，外部行为不变 |
| `cancel_subscription()` Service 方法 | 未修改 |
| `get_subscriptions()` Service 方法 | 未修改 |
| `POST /users/me/subscriptions` | 未修改 |
| `GET /users/me/subscriptions` | 未修改 |
| `DELETE /users/me/subscriptions` | 仅删除不可达的 catch 分支，外部行为不变（仍幂等返回 200） |
| 所有收藏相关端点 | 未修改 |
| 所有观看历史相关端点 | 未修改 |
| `api.py` 已有路由注册 | 未修改（仅在已有注册之后追加新路由） |

### C.4 未实施项（P2 独立排期）

| 项目 | 设计文档章节 | 状态 | 说明 |
|------|:---:|:---:|------|
| P2-1：订阅通知触发 | §7.1 | ⬜ 独立迭代 | 需 Celery 定时任务 + 批量通知写入 + 推送通道 |
| P2-2：房间详情增加 `live_status` | §7.2 | ⬜ 与前端协作 | 前端当前可通过 `GET /rooms/{room_id}/sessions` 获取场次状态 |

### C.5 前端接入接口完整协议

后端共实现 **5 个订阅相关接口**，其中 3 个已有（创建/列表/取消）、2 个本次新增（状态查询）。

---

#### 接口 1：创建订阅

```
POST /api/v1/users/me/subscriptions
```

**请求头**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Authorization` | string | ✅ | `Bearer <jwt_token>` |
| `Content-Type` | string | ✅ | `application/json` |

**请求体（JSON）**：
| 字段 | 类型 | 必填 | 说明 | 有效值 |
|------|------|:---:|------|------|
| `target_type` | string | ✅ | 订阅目标类型 | `"room"` 或 `"session"` |
| `target_id` | UUID | ✅ | 目标资源ID | 对应 `live_rooms.id` 或 `live_sessions.id` |

**请求示例**：
```json
{
  "target_type": "room",
  "target_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应（200 成功）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "target_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_type": "room",
    "is_active": true,
    "created_at": "2026-07-22T10:30:00.123456+00:00"
  }
}
```

**响应字段说明**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | UUID | 订阅记录唯一标识 |
| `data.target_id` | UUID | 被订阅的目标ID（房间或场次） |
| `data.target_type` | string | 目标类型（`"room"` 或 `"session"`） |
| `data.is_active` | bool | 订阅状态：`true`=有效，`false`=已取消（软删除恢复后仍为 `true`） |
| `data.created_at` | datetime | 订阅创建时间（ISO 8601 格式） |

**错误响应**：
| HTTP 状态码 | `code` | `message` | 触发条件 |
|:---:|:---:|------|------|
| 400 | 4001 | `"订阅已存在"` | 用户已订阅该目标 |
| 404 | 2001 | `"资源不存在"` | `target_id` 对应的房间/场次不存在 |
| 401 | — | — | 未携带 Token 或 Token 无效 |
| 422 | — | — | 缺少必填字段或字段类型错误 |
| 500 | 1002 | `"内部服务器错误"` | 数据库异常等 |

---

#### 接口 2：获取订阅列表

```
GET /api/v1/users/me/subscriptions
```

**请求头**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Authorization` | string | ✅ | `Bearer <jwt_token>` |

**Query 参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:---:|:---:|------|
| `target_type` | string | ❌ | 无（返回全部类型） | 按目标类型筛选：`"room"` 或 `"session"` |
| `page` | int | ❌ | 1 | 页码（最小 1） |
| `size` | int | ❌ | 10 | 每页条数（最小 1，最大 100） |

**请求示例**：
```
GET /api/v1/users/me/subscriptions?target_type=room&page=1&size=10
```

**响应（200 成功）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "target_id": "550e8400-e29b-41d4-a716-446655440000",
        "target_type": "room",
        "is_active": true,
        "created_at": "2026-07-22T10:30:00.123456+00:00"
      }
    ]
  }
}
```

**响应字段说明**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `data.total` | int | 符合条件的订阅总数 |
| `data.page` | int | 当前页码 |
| `data.size` | int | 每页条数 |
| `data.items` | array | 订阅记录数组（按 `created_at` 降序） |
| `data.items[].id` | UUID | 订阅记录ID |
| `data.items[].target_id` | UUID | 被订阅的资源ID |
| `data.items[].target_type` | string | `"room"` 或 `"session"` |
| `data.items[].is_active` | bool | 订阅状态（列表中始终为 `true`，已取消的不返回） |
| `data.items[].created_at` | datetime | 创建时间（ISO 8601） |

**此接口仅返回 `is_active=true` 的订阅**，已取消的不在列表中。

---

#### 接口 3：取消订阅

```
DELETE /api/v1/users/me/subscriptions
```

**请求头**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Authorization` | string | ✅ | `Bearer <jwt_token>` |

**Query 参数**：
| 参数 | 类型 | 必填 | 说明 | 有效值 |
|------|------|:---:|------|------|
| `target_type` | string | ✅ | 订阅目标类型 | `"room"` 或 `"session"` |
| `target_id` | UUID | ✅ | 目标资源ID | UUID 格式 |

**请求示例**：
```
DELETE /api/v1/users/me/subscriptions?target_type=room&target_id=550e8400-e29b-41d4-a716-446655440000
```

**响应（200 成功）**：
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

**幂等行为**：重复取消同一个订阅也返回 200（不会报错）。

**错误响应**：
| HTTP 状态码 | `code` | `message` | 触发条件 |
|:---:|:---:|------|------|
| 401 | — | — | 未携带 Token 或 Token 无效 |
| 422 | — | — | 缺少必填参数或字段类型错误 |
| 500 | 1002 | `"内部服务器错误"` | 数据库异常等 |

---

#### 🆕 接口 4：检查房间订阅状态

```
GET /api/v1/rooms/{room_id}/is-subscribed
```

**请求头**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Authorization` | string | ✅ | `Bearer <jwt_token>` |

**路径参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `room_id` | UUID | ✅ | 房间ID（`live_rooms.id`） |

**请求示例**：
```
GET /api/v1/rooms/550e8400-e29b-41d4-a716-446655440000/is-subscribed
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**响应（200，已订阅）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_subscribed": true
  }
}
```

**响应（200，未订阅）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_subscribed": false
  }
}
```

**响应字段说明**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `data.is_subscribed` | bool | `true`=当前用户已订阅此房间，`false`=未订阅 |

**错误响应**：
| HTTP 状态码 | `code` | `message` | 触发条件 |
|:---:|:---:|------|------|
| 404 | 2001 | `"资源不存在"` | 房间不存在 |
| 401 | — | — | 未携带 Token 或 Token 无效 |
| 422 | — | — | `room_id` 不是有效 UUID |
| 500 | 1002 | `"内部服务器错误"` | 数据库异常等 |

---

#### 🆕 接口 5：检查场次订阅状态

```
GET /api/v1/sessions/{session_id}/is-subscribed
```

**请求头**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Authorization` | string | ✅ | `Bearer <jwt_token>` |

**路径参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `session_id` | UUID | ✅ | 场次ID（`live_sessions.id`） |

**请求示例**：
```
GET /api/v1/sessions/660e8400-e29b-41d4-a716-446655440001/is-subscribed
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**响应（200，已订阅）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_subscribed": true
  }
}
```

**响应（200，未订阅）**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_subscribed": false
  }
}
```

**响应字段说明**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `data.is_subscribed` | bool | `true`=当前用户已订阅此场次，`false`=未订阅 |

**错误响应**：
| HTTP 状态码 | `code` | `message` | 触发条件 |
|:---:|:---:|------|------|
| 404 | 2001 | `"资源不存在"` | 场次不存在 |
| 401 | — | — | 未携带 Token 或 Token 无效 |
| 422 | — | — | `session_id` 不是有效 UUID |
| 500 | 1002 | `"内部服务器错误"` | 数据库异常等 |

---

### C.6 前端接入完整指南

#### C.6.1 订阅相关枚举定义（前端 TypeScript 参考）

```typescript
/** 订阅目标类型 */
type SubscriptionTargetType = 'room' | 'session';

/** 创建订阅请求体 */
interface SubscriptionCreateRequest {
  target_type: SubscriptionTargetType;
  target_id: string;  // UUID
}

/** 订阅记录 */
interface SubscriptionItem {
  id: string;           // UUID
  target_id: string;    // UUID
  target_type: SubscriptionTargetType;
  is_active: boolean;
  created_at: string;   // ISO 8601
}

/** 订阅列表响应 data 部分 */
interface SubscriptionListData {
  total: number;
  page: number;
  size: number;
  items: SubscriptionItem[];
}

/** is-subscribed 响应 data 部分 */
interface IsSubscribedData {
  is_subscribed: boolean;
}

/** 统一响应外层 */
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}
```

#### C.6.2 前端 API 函数签名（参考实现）

```typescript
// ─── 创建订阅 ───
// POST /api/v1/users/me/subscriptions
async function createSubscription(
  targetType: 'room' | 'session',
  targetId: string
): Promise<ApiResponse<SubscriptionItem>>

// ─── 获取订阅列表 ───
// GET /api/v1/users/me/subscriptions
async function getSubscriptions(params?: {
  target_type?: 'room' | 'session';
  page?: number;
  size?: number;
}): Promise<ApiResponse<SubscriptionListData>>

// ─── 取消订阅 ───
// DELETE /api/v1/users/me/subscriptions
async function cancelSubscription(
  targetType: 'room' | 'session',
  targetId: string
): Promise<ApiResponse<null>>

// ─── 检查房间订阅状态（新增） ───
// GET /api/v1/rooms/{room_id}/is-subscribed
async function checkRoomIsSubscribed(
  roomId: string
): Promise<ApiResponse<IsSubscribedData>>

// ─── 检查场次订阅状态（新增） ───
// GET /api/v1/sessions/{session_id}/is-subscribed
async function checkSessionIsSubscribed(
  sessionId: string
): Promise<ApiResponse<IsSubscribedData>>
```

#### C.6.3 页面按钮决策与交互完整流程

```
用户进入房间/场次详情页
│
├─ 第一步：获取资源状态判断展示哪个按钮
│   │
│   ├─ 场景 A：场次页面（如 /sessions/{session_id}）
│   │   GET /api/v1/sessions/{session_id}
│   │   → 从响应中读取 response.data.status 字段
│   │
│   └─ 场景 B：房间页面（如 /rooms/{room_id}）
│       GET /api/v1/rooms/{room_id}/sessions?size=1
│       → 从响应中读取 response.data.items[0].status
│       （取最近一场 session 的 status 作为房间当前状态）
│
├─ 第二步：根据 status 决定按钮类型
│   │
│   ├─ status === "scheduled"（预告）→ 显示【订阅】按钮
│   │
│   └─ status !== "scheduled"（live / finished / ready / processing）
│       → 显示【收藏】按钮（走已有的收藏 API 流程）
│
├─ 第三步（仅 scheduled 预告状态）：查询订阅初始状态
│   │
│   ├─ 场次预告：GET /api/v1/sessions/{session_id}/is-subscribed
│   └─ 房间预告：GET /api/v1/rooms/{room_id}/is-subscribed
│   │
│   ├─ data.is_subscribed === true  → 按钮显示"已订阅"（可点击取消）
│   └─ data.is_subscribed === false → 按钮显示"订阅"（可点击订阅）
│
└─ 第四步：按钮点击交互
    │
    ├─ 当前状态"订阅" → 点击
    │   POST /api/v1/users/me/subscriptions
    │   Body: { target_type: "room"|"session", target_id: "<id>" }
    │   → 成功后按钮切换为"已订阅"
    │
    └─ 当前状态"已订阅" → 点击
        DELETE /api/v1/users/me/subscriptions?target_type=room|session&target_id=<id>
        → 成功后按钮切换为"订阅"
```

#### C.6.4 边界情况处理建议

| 场景 | 建议处理 |
|------|---------|
| `is-subscribed` 接口返回 404 | 房间/场次不存在，跳转错误页或返回上一页 |
| `is-subscribed` 接口返回 401 | Token 失效，跳转登录页 |
| `is-subscribed` 接口返回 500 | 网络/服务异常，降级为不展示订阅按钮（展示收藏按钮） |
| 创建订阅返回 400 "订阅已存在" | 按钮状态已过期（其他端已订阅），直接刷新按钮为"已订阅" |
| 创建订阅返回 404 | 目标资源已删除，刷新页面或提示用户 |
| 取消订阅的幂等特性 | 取消后无需关心返回值，直接切换按钮为"订阅" |
| 用户快速反复点击 | 按钮点击后立即 disabled，等待接口返回后再恢复 |

#### C.6.5 接口调用时序汇总

| 页面 | API 调用顺序 | 说明 |
|------|------|------|
| **场次详情页** | ① `GET /sessions/{id}` 获取状态<br>② 若 status=scheduled → `GET /sessions/{id}/is-subscribed` | 两个接口可并行调用 |
| **房间详情页** | ① `GET /rooms/{id}` / `GET /rooms/{id}/sessions?size=1` 获取状态<br>② 若 status=scheduled → `GET /rooms/{id}/is-subscribed` | 同样可并行 |

> 注：`is-subscribed` 调用不依赖于详情接口的数据（只需要 ID），因此两个请求可以并行发出，再根据详情接口返回的 `status` 来决定是否使用 `is-subscribed` 的结果。

---

> **文档维护说明：** 本文档基于 2026-07-22 的三方交叉验证分析（用户两轮逐层分析 + Claude 独立代码审查 + 源码逐行核验）生成。P0 + P1 已于同日实施完成，附录 C 记录逐项检验结果。P2 两项为独立功能增强，待后续排期。
