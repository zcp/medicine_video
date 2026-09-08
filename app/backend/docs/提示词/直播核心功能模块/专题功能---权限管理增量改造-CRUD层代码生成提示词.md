# 专题功能 - 权限管理增量改造 - CRUD 层代码生成提示词

## ⚠️ 使用说明（重要）

**本提示词用于改造已有代码，不是生成新代码。**

在使用本提示词之前，**必须**在 Cursor 聊天框中先 `@` 引用本提示词文档和所有需要改造的代码文件：

```
@docs/提示词/专题功能---权限管理增量改造-CRUD层代码生成提示词.md
@app/crud/topic.py
@app/models/topic.py
@app/core/exceptions.py
...（其他相关文件）
```

**⚠️ 关键**：AI 需要读取现有的代码文件，才能进行增量改造。如果不引用已有代码文件，AI 无法知道现有代码的结构和内容，将无法正确执行增量改造。

---

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端工程师，专门负责实现 **数据访问层（CRUD/Repository Layer）**。  

**你的任务**：
1. **读取上下文**：用户已经在提示词的开头使用了 Cursor 的 `@` 标记引用了**已有的代码文件**（例如 `@app/crud/topic.py`、`@app/models/topic.py` 等）。
2. **分析现有代码**：**读取**这些 `@` 引用的代码文件内容，分析现有的CRUD方法、SQL查询逻辑等。
3. **增量改造**：在**不破坏现有查询逻辑**的前提下，为所有列表查询方法**最小幅度地融合权限过滤**。

**⚠️ 重要**：你已经在上一版中完成了所有专题功能的 CRUD 实现（Topic、TopicCategory、TopicCategoryRoom 等），现在只需要进行权限过滤的增量改造，**严禁重写或删除任何已有 CRUD 代码**。

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

4. **专题功能特殊说明**：
   - 专题功能使用 `status` 字段（ENUM: draft/published/archived）而非 `is_private` 字段
   - **权限映射关系**：
     - `status = 'published'` ↔ `is_private = false`（公开，支持匿名访问）
     - `status = 'draft'` 或 `status = 'archived'` ↔ `is_private = true`（私有，仅Owner/Admin可访问）

### 2.2 改造范围

根据《直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md》，需要对以下 CRUD 方法进行权限过滤改造：

| 模块 | CRUD 方法 | 改造类型 | 权限策略 |
|------|----------|---------|---------|
| Topic | `get_multi` | 列表查询 | Admin 看全部 / Regular 看 Published+Own / Anonymous 看 Published |
| Topic | `get_topics_by_room` | 列表查询 | Admin 看全部 / Regular 看 Published+Own / Anonymous 看 Published |
| Topic | `get` | 详情查询 | 不在此层过滤（由 Service 层调用守卫函数） |
| TopicCategory | `get_multi` | 列表查询 | 继承 Topic 的 status（不在此层过滤） |
| TopicCategory | `get` | 详情查询 | 不在此层过滤（由 Service 层调用守卫函数） |
| TopicCategoryRoom | `get_multi` | 列表查询 | 双重权限过滤（Topic status + Room is_private） |
| TopicCategoryRoom | `get` | 详情查询 | 不在此层过滤（由 Service 层调用守卫函数） |

**⚠️ 重要说明**：
- **详情查询**（`get` 方法）不在 CRUD 层做权限过滤，由 Service 层调用权限守卫函数处理
- **列表查询**（`get_multi` 方法）必须在 CRUD 层通过 SQL WHERE 条件实现权限过滤
- **`get_topics_by_room` 方法**：需要权限增补改造，根据用户身份应用不同的权限过滤（与 `get_multi` 相同的权限策略）
- **TopicCategory** 的列表查询不在此层过滤，因为它们继承 Topic 的权限，由 Service 层先检查 Topic 权限后再查询
- **TopicCategoryRoom** 的列表查询需要双重权限过滤（专题权限 + 直播间权限）

## 3. 项目文件组织结构

### 3.1 项目目录结构

```
backend/live_core_service/
├── app/
│   ├── crud/
│   │   └── topic.py                    # Topic CRUD（需要改造get_multi）
│   ├── models/
│   │   └── topic.py                    # Topic模型（了解status、user_id字段）
│   └── core/
│       └── exceptions.py                # 自定义异常（如果存在）
```

### 3.2 必须引用的代码文件（⚠️ 重要）

在使用本提示词时，用户**必须**通过 `@` 引用以下代码文件：

#### CRUD层文件（必须引用）
- `@app/crud/topic.py` - Topic CRUD（需要改造 `get_multi` 方法）

#### Models文件（必须引用，用于了解字段定义）
- `@app/models/topic.py` - Topic模型（了解 `status`、`user_id` 字段定义）

#### 其他相关文件（推荐引用）
- `@app/core/exceptions.py` - 自定义异常（如果存在）

**⚠️ 重要**：
- 如果某些文件不存在，可以只引用存在的文件
- AI 需要读取这些文件来了解现有代码的结构和内容
- 如果不引用这些文件，AI 无法知道现有代码，将无法正确执行增量改造

## 4. 内容来源（设计文档）

所有实现必须严格对齐以下设计文档，**不得自创权限逻辑或偏离语义**：

- **主设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`
  - 提供数据库 Schema 和字段定义
  
- **专题功能设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md`
  - 提供专题功能的业务逻辑定义

- **权限设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md`
  - **重点章节**：
    - § 1「核心设计原则」—— 5条核心原则
    - § 3.1「专题管理模块」—— 接口 3「获取专题列表」的权限逻辑与 SQL 策略
    - § 4.3「Repository 层查询优化」—— SQL 权限过滤实现示例
    - § 10.3「CRUD方法覆盖验证」—— 14个CRUD方法的权限过滤策略

**⚠️ 重要**：如权限设计文档与主设计文档存在歧义，以 **权限设计文档（v6.1 Topic Permission Edition）** 为最终口径。

## 5. 核心架构与编码约束（继承原有规范）

完全继承原有「CRUD 层代码生成提示词」中的全部规范，包括但不限于：

### 5.1 CRUD 层职责（学院派核心）

**必须遵守的规则**：

1. ✅ 只封装 **原子性数据库操作**，不做业务逻辑或权限检查（但需要在 SQL 层面应用权限过滤）
2. ✅ 所有写操作（create/update/delete）在函数内部处理事务（`commit/rollback`）
3. ✅ 所有写操作必须有 `try...except IntegrityError/Exception` 块，并在异常时 `rollback`
4. ✅ 在 `try` 之前提取日志所需变量（如 `obj_id_log` / `topic_id_log`），避免在 `except` 中访问已失效对象
5. ✅ 使用 `logger.error(..., exc_info=True)` 记录数据库异常，并抛出自定义异常（`DatabaseIntegrityException` / `DatabaseOperationException`）
6. ✅ **权限过滤**：列表查询方法必须在 SQL 层面根据 `user_id` 和 `role` 构建不同的 WHERE 条件
7. ❌ 不做业务逻辑校验，不做权限判断（但需要应用权限过滤条件）

### 5.2 安全异步异常处理

继续严格执行「安全异步异常处理规范」：

```python
# ✅ 正确：在try之前提取日志变量
topic_id_log = topic_id
user_id_log = user_id

try:
    query = select(Topic).where(...)
    result = await db.execute(query)
    return result.scalars().all()
except Exception as e:
    await db.rollback()
    logger.error(
        f"查询专题列表失败：topic_id={topic_id_log}, user_id={user_id_log}, error={e}",
        exc_info=True,
    )
    raise DatabaseOperationException("查询专题列表时发生错误")
```

## 6. 权限过滤 SQL 策略（核心实现）

### 6.1 Topic 列表查询权限过滤

根据权限设计文档 § 3.1，Topic 列表查询的权限策略为：

| 用户身份 | SQL WHERE 条件 | 说明 |
|---------|---------------|------|
| **Admin** | 无过滤 | `SELECT * FROM topics ...` |
| **Regular User** | `status='published' OR (status IN ('draft', 'archived') AND user_id={user_id})` | `SELECT * FROM topics WHERE status='published' OR (status IN ('draft', 'archived') AND user_id={user_id})` |
| **Anonymous** | `status='published'` | `SELECT * FROM topics WHERE status='published'` |

**⚠️ 性能关键**：必须在 Repository 层通过 SQL 过滤，禁止查出所有数据在内存过滤。

**⚠️ 专题功能特殊说明**：
- 专题功能使用 `status` 字段（ENUM: draft/published/archived）而非 `is_private` 字段
- `status = 'published'` 对应公开状态（`is_private = false`）
- `status = 'draft'` 或 `status = 'archived'` 对应私有状态（`is_private = true`）

### 6.2 实现模式

#### 模式 A：Topic 列表查询（带权限过滤）

**改造前**：
```python
async def get_multi(
    self,
    session: AsyncSession,
    page: int,
    size: int,
    status: Optional[str] = None
) -> Tuple[List[Topic], int]:
    """获取专题列表"""
    # 构建基础查询
    stmt = select(Topic)
    
    # 状态筛选
    if status:
        stmt = stmt.where(Topic.status == status)
    
    # 计算总数
    count_stmt = select(func.count()).select_from(Topic)
    if status:
        count_stmt = count_stmt.where(Topic.status == status)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()
    
    # 应用分页和排序
    stmt = stmt.order_by(Topic.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    # 执行查询
    result = await session.execute(stmt)
    topics = result.scalars().all()
    
    return list(topics), total
```

**改造后**（最小幅度修改）：
```python
async def get_multi(
    self,
    session: AsyncSession,
    user_id: Optional[UUID],  # ← 新增：当前用户的public_id（匿名时为None）
    role: Optional[str],      # ← 新增：当前用户的角色（匿名时为None）
    page: int,
    size: int,
    status: Optional[str] = None
) -> Tuple[List[Topic], int]:
    """获取专题列表（带权限过滤）"""
    # 构建基础查询
    stmt = select(Topic)
    
    # ⚠️ 核心修改：根据用户身份应用不同的WHERE条件（权限过滤）
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有
        if status:
            stmt = stmt.where(Topic.status == status)
    elif user_id:
        # 普通用户：Published OR (Draft/Archived AND Own)
        if status:
            if status == 'published':
                stmt = stmt.where(Topic.status == 'published')
            else:
                # draft或archived：必须是自己的
                stmt = stmt.where(
                    and_(
                        Topic.status == status,
                        Topic.user_id == user_id
                    )
                )
        else:
            # 无状态筛选：Published OR (Draft/Archived AND Own)
            stmt = stmt.where(
                or_(
                    Topic.status == 'published',
                    and_(
                        Topic.status.in_(['draft', 'archived']),
                        Topic.user_id == user_id
                    )
                )
            )
    else:
        # 匿名用户：Only Published
        stmt = stmt.where(Topic.status == 'published')
        if status and status != 'published':
            # 匿名用户请求非published状态，返回空结果
            stmt = stmt.where(False)
    
    # 计算总数（必须应用相同的WHERE条件）
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()
    
    # 应用分页和排序
    stmt = stmt.order_by(Topic.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    
    # 执行查询
    result = await session.execute(stmt)
    topics = result.scalars().all()
    
    return list(topics), total
```

**⚠️ 关键修改点**：
1. ✅ **只增加**了 `user_id` 和 `role` 两个 Optional 参数
2. ✅ **只修改**了 WHERE 条件的构建逻辑（增加了权限过滤）
3. ✅ **保持了**原有的分页、排序、状态筛选逻辑
4. ✅ **保持了**原有的返回类型和语义

### 6.3 TopicCategoryRoom 列表查询（双重权限过滤）

**⚠️ 特殊场景**：`TopicCategoryRoom.get_multi` 需要同时考虑专题权限和直播间权限。

根据权限设计文档 § 5.2，双重权限过滤的实现策略：

1. **专题可见性**：专题必须是 `published`，或用户是专题 Owner/Admin
2. **直播间可见性**：直播间必须是 `is_private=false`，或用户是直播间 Owner/Admin

**实现模式**（需要在 Service 层先检查专题权限，然后在 CRUD 层应用直播间权限过滤）：

```python
# 在 Service 层先检查专题权限
topic = await self.crud.topic.get(session, topic_id)
self._check_topic_visibility(topic, user_id, role)

# 然后在 CRUD 层查询时应用直播间权限过滤
rooms = await self.crud.category_room.get_multi(
    session=session,
    category_id=category_id,
    user_id=user_id,  # ← 用于直播间权限过滤
    role=role,        # ← 用于直播间权限过滤
    page=page,
    size=size
)
```

**⚠️ 注意**：`TopicCategoryRoom.get_multi` 的权限过滤逻辑与 `Room.get_multi` 相同（基于 `is_private` 字段），但需要先由 Service 层检查专题权限。

### 6.4 Topic.get_topics_by_room 方法权限过滤

**⚠️ 重要**：`get_topics_by_room` 方法在原始设计中只返回 `status='published'` 的专题（硬编码），权限增补时需要根据用户身份应用动态权限过滤。

**原始实现**（硬编码）：
```python
async def get_topics_by_room(
    db: AsyncSession,
    room_id: uuid.UUID
) -> List[Dict[str, Any]]:
    # 硬编码：只返回 published 状态的专题
    stmt = select(...).where(
        and_(
            TopicCategoryRoom.room_id == room_id,
            Topic.status == TopicStatus.PUBLISHED  # ← 硬编码
        )
    )
```

**权限增补后**（动态过滤）：
```python
async def get_topics_by_room(
    db: AsyncSession,
    room_id: uuid.UUID,
    user_id: Optional[UUID],  # ← 新增：当前用户的public_id（匿名时为None）
    role: Optional[str]        # ← 新增：当前用户的角色（匿名时为None）
) -> List[Dict[str, Any]]:
    """获取指定直播间关联的专题（带权限过滤）"""
    # 构建基础查询（三表JOIN）
    stmt = select(
        Topic.id.label('topic_id'),
        Topic.title.label('topic_title'),
        Topic.status.label('topic_status'),
        TopicCategory.id.label('category_id'),
        TopicCategory.name.label('category_name')
    ).select_from(TopicCategoryRoom).join(
        TopicCategory, TopicCategoryRoom.category_id == TopicCategory.id
    ).join(
        Topic, TopicCategory.topic_id == Topic.id
    ).where(
        TopicCategoryRoom.room_id == room_id
    )
    
    # ⚠️ 核心修改：根据用户身份应用不同的WHERE条件（权限过滤）
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有状态的专题
        pass
    elif user_id:
        # 普通用户：Published OR (Draft/Archived AND Own)
        stmt = stmt.where(
            or_(
                Topic.status == TopicStatus.PUBLISHED,
                and_(
                    Topic.status.in_([TopicStatus.DRAFT, TopicStatus.ARCHIVED]),
                    Topic.user_id == user_id
                )
            )
        )
    else:
        # 匿名用户：Only Published
        stmt = stmt.where(Topic.status == TopicStatus.PUBLISHED)
    
    # 排序和返回
    stmt = stmt.order_by(Topic.created_at.desc())
    result = await db.execute(stmt)
    rows = result.all()
    
    # 转换为字典列表
    topics = [
        {
            "topic_id": str(row.topic_id),
            "topic_title": row.topic_title,
            "topic_status": row.topic_status,
            "category_id": str(row.category_id),
            "category_name": row.category_name
        }
        for row in rows
    ]
    
    return topics
```

**⚠️ 关键修改点**：
1. ✅ **只增加**了 `user_id` 和 `role` 两个 Optional 参数
2. ✅ **只修改**了 WHERE 条件的构建逻辑（将硬编码的 `status='published'` 改为动态权限过滤）
3. ✅ **保持了**原有的三表JOIN查询逻辑
4. ✅ **保持了**原有的返回类型和数据结构

## 7. 完整改造清单

### 7.1 Topic CRUD 方法改造

| CRUD 方法 | 改造类型 | 权限参数 | 权限过滤策略 | 状态 |
|----------|---------|---------|------------|------|
| `get_multi` | ✅ 需要改造 | `user_id: Optional[UUID]`, `role: Optional[str]` | Admin看全部 / Regular看Published+Own / Anonymous看Published | ✅ 必须改造 |
| `get_topics_by_room` | ✅ 需要改造 | `user_id: Optional[UUID]`, `role: Optional[str]` | Admin看全部 / Regular看Published+Own / Anonymous看Published | ✅ 必须改造 |
| `get` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `create` | ❌ 不改造 | - | 无需权限过滤 | ✅ 无需改造 |
| `update` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `delete` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |

### 7.2 TopicCategory CRUD 方法改造

| CRUD 方法 | 改造类型 | 权限参数 | 权限过滤策略 | 状态 |
|----------|---------|---------|------------|------|
| `get_multi` | ❌ 不改造 | - | 继承Topic权限，由Service层检查 | ✅ 无需改造 |
| `get` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `create` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `update` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `delete` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |

### 7.3 TopicCategoryRoom CRUD 方法改造

| CRUD 方法 | 改造类型 | 权限参数 | 权限过滤策略 | 状态 |
|----------|---------|---------|------------|------|
| `get_multi` | ⚠️ 特殊改造 | `user_id: Optional[UUID]`, `role: Optional[str]` | 双重权限过滤（Topic+Room） | ⚠️ 需要改造 |
| `get` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `create` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `update` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |
| `delete` | ❌ 不改造 | - | 由Service层调用守卫函数 | ✅ 无需改造 |

**⚠️ 重要**：
- 需要在 CRUD 层进行权限过滤改造的方法：
  - `Topic.get_multi` ✅
  - `Topic.get_topics_by_room` ✅（用于 `get_room_topics` Service方法）
  - `TopicCategoryRoom.get_multi` ✅
- 其他方法（`get`、`create`、`update`、`delete`）的权限检查由 Service 层处理

## 8. 编码规范（继承母版）

完全遵循 `docs/提示词/自动化后端代码生成/crud_service_endpoint代码生成提示词母版.md` 中定义的所有编码规范，包括但不限于：

- **学院派架构原则**
- **事务处理规范**
- **异常处理规范**
- **日志记录规范**
- **安全异步异常处理规范**
- **响应处理规范**
- **配置规范**

## 9. 实施检查清单

在完成改造后，请逐一检查：

- [ ] **1. 方法签名**：`get_multi` 方法是否增加了 `user_id: Optional[UUID]` 和 `role: Optional[str]` 参数？
- [ ] **2. SQL过滤**：权限过滤是否在 SQL 层面通过 WHERE 条件实现？
- [ ] **3. 性能优化**：是否避免了在内存中过滤数据？
- [ ] **4. 总数计算**：分页查询的总数计算是否应用了相同的 WHERE 条件？
- [ ] **5. 向后兼容**：新增参数是否使用了 Optional 类型和默认值 `None`？
- [ ] **6. 字段映射**：是否使用了 `status` 字段而非 `is_private` 字段？
- [ ] **7. 权限逻辑**：Admin/Regular/Anonymous 的权限过滤逻辑是否正确？
- [ ] **8. 代码完整性**：是否保留了所有原有的业务逻辑（分页、排序、状态筛选等）？

## 10. 参考实现示例

完整的实现示例请参考权限设计文档：
- § 4.3「Repository 层查询优化」—— `TopicCRUD.get_multi` 完整实现

---

**文档版本**：v1.0  
**最后更新**：2025-01-XX  
**依赖文档**：
- 《直播核心功能设计文档_v6_深度融合最终版.md》
- 《直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md》
- 《直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md》
