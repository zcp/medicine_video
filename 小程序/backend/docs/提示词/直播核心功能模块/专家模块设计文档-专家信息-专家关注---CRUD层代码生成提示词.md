# 专家模块 - CRUD层代码生成提示词

**模块名称**: experts  
**功能模块名称**: 专家模块设计文档-专家信息-专家关注  
**目标文件**: `backend/live_core_service/app/crud/experts.py`  
**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和Python异步编程的资深后端开发工程师。你的任务是根据本提示词文档，生成专家模块的CRUD层代码。

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
3. **事务管理**: 使用`AsyncSession`，写操作必须包含`try/except IntegrityError/finally`块，并处理`db.commit()`和`db.rollback()`
4. **异常处理**: 捕获`IntegrityError`并转换为`DatabaseIntegrityException`
5. **日志记录**: 每个CRUD操作记录INFO日志，UUID脱敏（只记录前8位）
6. **N+1问题防范**: 使用`selectinload`或`joinedload`预加载关联数据
7. **安全异步异常处理**: 在`try`块之前提取用于日志的变量，避免在`except`块中访问可能已失效会话的ORM对象属性

---

## 3. 项目结构与上下文信息

**项目目录结构**:
```
app/
├── models/          # SQLAlchemy 模型（数据层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块模型
│   ├── live_core.py
│   ├── content_management.py
│   ├── topic.py
│   └── ...
├── schemas/         # Pydantic Schema（数据验证层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块Schema
│   └── ...
├── crud/            # CRUD 层（数据访问层）
│   ├── __init__.py
│   ├── experts.py  # 📋 待生成的专家模块CRUD
│   ├── topic.py     # 参考：专题模块CRUD（app/crud/topic.py）
│   └── ...
└── ...
```

**文件命名规范**:
- 模型文件: `experts.py`
- Schema文件: `experts.py`
- CRUD文件: `experts.py`

**导入路径规范**:
- 模型导入: `from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert`
- Schema导入: `from app.schemas.experts import ExpertCreate, ExpertUpdate, ExpertItem, ...`

**现有代码参考**:
- 专题模块CRUD: `app/crud/topic.py`（可作为代码风格和结构参考）

---

## 4. Model字段摘要（来自实际代码）

**重要提示**: 以下模型定义引用自已生成的代码：`backend/live_core_service/app/models/experts.py`

**执行者指令**: 
1. 使用 `read_file()` 工具读取 `backend/live_core_service/app/models/experts.py` 文件
2. 提取所有字段信息：字段名、类型、约束（如 unique=True, nullable=False）
3. 记录主键、外键、索引等元信息
4. 识别关系定义（relationship）

### 4.1. Expert模型

**表名**: `experts`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 主键UUID |
| `user_id` | UUID | NULLABLE, UNIQUE | NULL | 关联平台用户公开ID |
| `name` | String(120) | NOT NULL | - | 专家姓名 |
| `title` | String(120) | NULLABLE | NULL | 职称 |
| `hospital` | String(200) | NULLABLE | NULL | 所属医院 |
| `department` | String(120) | NULLABLE | NULL | 科室 |
| `expertise_areas` | Text | NULLABLE | NULL | 擅长领域 |
| `bio` | Text | NULLABLE | NULL | 个人简介 |
| `avatar_url` | String(512) | NULLABLE | NULL | 头像URL |
| `is_featured` | Boolean | NOT NULL | False | 是否为首页推荐专家 |
| `sort_order` | Integer | NOT NULL | 0 | 排序顺序 |
| `contact_info` | JSONB | NULLABLE | NULL | 联系方式JSONB |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 创建时间 |
| `updated_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 更新时间 |

**索引**: 
- `idx_experts_is_featured` (is_featured, sort_order)
- `idx_experts_user_id` (user_id)

**关系**:
- `user_expert_subscriptions`: 一对多关系，关联`UserExpertSubscription`
- `live_session_experts`: 一对多关系，关联`LiveSessionExpert`

**唯一性约束**: `user_id` 具有唯一性约束（一个用户只能绑定一个专家档案）

---

### 4.2. UserExpertSubscription模型

**表名**: `user_expert_subscriptions`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 主键UUID |
| `user_id` | UUID | NOT NULL | - | 用户公开ID |
| `expert_id` | UUID | NOT NULL, FK | - | 专家ID（外键，CASCADE删除） |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 关注时间 |

**唯一性约束**: `UNIQUE(user_id, expert_id)` - 防止重复关注

**索引**: 
- `idx_user_expert_subscriptions_user_id` (user_id)
- `idx_user_expert_subscriptions_expert_id` (expert_id)
- `idx_user_expert_subscriptions_created_at` (created_at)

**关系**:
- `expert`: 多对一关系，关联`Expert`

---

### 4.3. LiveSessionExpert模型

**表名**: `live_session_experts`

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | uuid.uuid4() | 主键UUID |
| `session_id` | UUID | NOT NULL, FK | - | 直播场次ID（外键，CASCADE删除） |
| `expert_id` | UUID | NOT NULL, FK | - | 专家ID（外键，CASCADE删除） |
| `role` | String(50) | NOT NULL | "主讲" | 专家角色（主讲、主持、嘉宾） |
| `sort_order` | Integer | NOT NULL | 0 | 显示顺序 |
| `created_at` | TIMESTAMP(TZ) | NOT NULL | func.now() | 关联创建时间 |

**唯一性约束**: `UNIQUE(session_id, expert_id, role)` - 同一场次同一专家只能有一个角色

**索引**: 
- `idx_live_session_experts_session` (session_id)
- `idx_live_session_experts_expert` (expert_id)
- `idx_live_session_experts_role` (session_id, role)

**关系**:
- `session`: 多对一关系，关联`LiveSession`
- `expert`: 多对一关系，关联`Expert`

---

## 5. 需要生成的CRUD函数清单

### 5.1. Expert CRUD函数（7个）

#### 函数1: `create_expert`

**函数签名**:
```python
async def create_expert(
    db: AsyncSession,
    expert_data: ExpertCreate
) -> Expert
```

**功能**: 创建专家

**唯一性约束处理**:
- `Expert.user_id`具有唯一性约束
- 如果违反唯一性，数据库会抛出`IntegrityError`
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("该用户已绑定到其他专家档案")`

**执行流程**:
1. 在应用层生成UUID：`expert_id = uuid.uuid4()`
2. 创建Expert实例：`expert = Expert(id=expert_id, **expert_data.model_dump())`
3. 提前提取用于日志的变量：`expert_id_for_logging = str(expert_id)[:8]`
4. 添加到会话：`db.add(expert)`
5. Flush（不commit）：`await db.flush()` - 触发唯一性检查
6. 刷新对象：`await db.refresh(expert)` - 获取数据库生成的时间戳
7. 记录日志：`logger.info(f"创建专家成功: id={expert_id_for_logging}, name={expert.name}")`
8. 返回expert对象
9. 异常处理：
   ```python
   try:
       # ... 执行创建
   except IntegrityError as e:
       await db.rollback()
       logger.error(f"创建专家失败（唯一性冲突）: {str(e)}")
       raise DatabaseIntegrityException("该用户已绑定到其他专家档案")
   except Exception as e:
       await db.rollback()
       logger.error(f"创建专家失败: {str(e)}")
       raise
   ```

---

#### 函数2: `get_expert`

**函数签名**:
```python
async def get_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> Optional[Expert]
```

**功能**: 根据ID获取单个专家

**执行流程**:
1. 构建查询：`stmt = select(Expert).where(Expert.id == expert_id)`
2. 执行查询：`result = await db.execute(stmt)`
3. 返回结果：`result.scalar_one_or_none()`
4. 记录日志：`logger.debug(f"查询专家: expert_id={str(expert_id)[:8]}")`

---

#### 函数3: `get_expert_by_user_id`

**函数签名**:
```python
async def get_expert_by_user_id(
    db: AsyncSession,
    user_id: uuid.UUID
) -> Optional[Expert]
```

**功能**: 根据user_id获取专家（用于检查user_id是否已被绑定）

**执行流程**:
1. 构建查询：`stmt = select(Expert).where(Expert.user_id == user_id)`
2. 执行查询：`result = await db.execute(stmt)`
3. 返回结果：`result.scalar_one_or_none()`
4. 记录日志：`logger.debug(f"查询专家（按user_id）: user_id={str(user_id)[:8]}")`

---

#### 函数4: `get_featured_experts`

**函数签名**:
```python
async def get_featured_experts(
    db: AsyncSession,
    limit: int = 10
) -> List[Expert]
```

**功能**: 获取首页推荐专家列表（按sort_order排序）

**执行流程**:
1. 构建查询：`stmt = select(Expert).where(Expert.is_featured == True).order_by(Expert.sort_order.asc(), Expert.created_at.desc())`
2. 应用限制：`stmt = stmt.limit(limit)`
3. 执行查询：`result = await db.execute(stmt)`
4. 返回结果：`result.scalars().all()`
5. 记录日志：`logger.info(f"查询推荐专家列表，返回{len(experts)}条记录")`

---

#### 函数5: `get_experts_multi_and_total`

**函数签名**:
```python
async def get_experts_multi_and_total(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None
) -> Tuple[List[Expert], int]
```

**功能**: 分页获取专家列表，支持筛选和排序

**执行流程**:
1. 构建基础查询：`stmt = select(Expert)`
2. 应用筛选条件：
   - 如果`name`不为None，添加`where(Expert.name.ilike(f'%{name}%'))`
   - 如果`is_featured`不为None，添加`where(Expert.is_featured == is_featured)`
   - 如果`hospital`不为None，添加`where(Expert.hospital.ilike(f'%{hospital}%'))`
3. 执行COUNT查询获取总数：`count_stmt = select(func.count()).select_from(stmt.subquery())`
4. 解析`sort`参数（默认`sort_order:asc,created_at:desc`）并应用排序
5. 应用分页：`stmt = stmt.offset(skip).limit(limit)`
6. 执行查询获取数据列表
7. 返回结果：`(result.scalars().all(), total)`
8. 记录日志：`logger.info(f"查询专家列表，返回{len(experts)}条记录，总数={total}")`

---

#### 函数6: `update_expert`

**函数签名**:
```python
async def update_expert(
    db: AsyncSession,
    expert_id: uuid.UUID,
    expert_data: ExpertUpdate
) -> Optional[Expert]
```

**功能**: 更新专家（部分更新）

**唯一性约束处理**:
- 如果更新了`user_id`字段，可能违反唯一性约束
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("该用户已绑定到其他专家档案")`

**执行流程**:
1. 查询专家：`stmt = select(Expert).where(Expert.id == expert_id)`
2. 执行查询：`result = await db.execute(stmt)`
3. 获取专家：`expert = result.scalar_one_or_none()`
4. 如果expert为None，返回None（由Service层处理404）
5. 提前提取用于日志的变量：`expert_id_for_logging = str(expert_id)[:8]`
6. 部分更新：
   ```python
   update_data = expert_data.model_dump(exclude_unset=True)
   for field, value in update_data.items():
       setattr(expert, field, value)
   ```
7. Flush：`await db.flush()`
8. 刷新对象：`await db.refresh(expert)`
9. 记录日志：`logger.info(f"更新专家成功: id={expert_id_for_logging}")`
10. 返回expert对象
11. 异常处理（同create_expert）

---

#### 函数7: `delete_expert`

**函数签名**:
```python
async def delete_expert(
    db: AsyncSession,
    expert_id: uuid.UUID
) -> bool
```

**功能**: 删除专家（软删除：设置is_featured=False）

**执行流程**:
1. 查询专家：`stmt = select(Expert).where(Expert.id == expert_id)`
2. 执行查询：`result = await db.execute(stmt)`
3. 获取专家：`expert = result.scalar_one_or_none()`
4. 如果expert为None，返回False（由Service层处理404）
5. 提前提取用于日志的变量：`expert_id_for_logging = str(expert_id)[:8]`
6. 软删除：`expert.is_featured = False`
7. Flush：`await db.flush()`
8. 刷新对象：`await db.refresh(expert)`
9. 记录日志：`logger.warning(f"删除专家（软删除）: id={expert_id_for_logging}")`
10. 返回True
11. 异常处理：
    ```python
    try:
        # ... 执行删除
    except Exception as e:
        await db.rollback()
        logger.error(f"删除专家失败: {str(e)}")
        raise
    ```

---

### 5.2. UserExpertSubscription CRUD函数（5个）

#### 函数8: `create_subscription`

**函数签名**:
```python
async def create_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> UserExpertSubscription
```

**功能**: 创建用户关注专家记录

**唯一性约束处理**:
- `UNIQUE(user_id, expert_id)`约束
- 如果违反唯一性，数据库会抛出`IntegrityError`
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("您已关注该专家")`

**执行流程**:
1. 在应用层生成UUID：`subscription_id = uuid.uuid4()`
2. 创建UserExpertSubscription实例：`subscription = UserExpertSubscription(id=subscription_id, user_id=user_id, expert_id=expert_id)`
3. 提前提取用于日志的变量：`user_id_for_logging = str(user_id)[:8]`, `expert_id_for_logging = str(expert_id)[:8]`
4. 添加到会话：`db.add(subscription)`
5. Flush（不commit）：`await db.flush()` - 触发唯一性检查
6. 刷新对象：`await db.refresh(subscription)`
7. 记录日志：`logger.info(f"创建关注记录成功: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}")`
8. 返回subscription对象
9. 异常处理：
   ```python
   try:
       # ... 执行创建
   except IntegrityError as e:
       await db.rollback()
       logger.error(f"创建关注记录失败（唯一性冲突）: {str(e)}")
       raise DatabaseIntegrityException("您已关注该专家")
   except Exception as e:
       await db.rollback()
       logger.error(f"创建关注记录失败: {str(e)}")
       raise
   ```

---

#### 函数9: `get_subscription`

**函数签名**:
```python
async def get_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> Optional[UserExpertSubscription]
```

**功能**: 查询用户是否已关注专家

**执行流程**:
1. 构建查询：`stmt = select(UserExpertSubscription).where(and_(UserExpertSubscription.user_id == user_id, UserExpertSubscription.expert_id == expert_id))`
2. 执行查询：`result = await db.execute(stmt)`
3. 返回结果：`result.scalar_one_or_none()`
4. 记录日志：`logger.debug(f"查询关注记录: user_id={str(user_id)[:8]}, expert_id={str(expert_id)[:8]}")`

---

#### 函数10: `get_user_subscriptions`

**函数签名**:
```python
async def get_user_subscriptions(
    db: AsyncSession,
    user_id: uuid.UUID
) -> List[UserExpertSubscription]
```

**功能**: 获取用户关注的所有专家列表（预加载专家信息）

**执行流程**:
1. 构建查询：`stmt = select(UserExpertSubscription).where(UserExpertSubscription.user_id == user_id).order_by(UserExpertSubscription.created_at.desc())`
2. 预加载专家信息：`stmt = stmt.options(selectinload(UserExpertSubscription.expert))`
3. 执行查询：`result = await db.execute(stmt)`
4. 返回结果：`result.scalars().all()`
5. 记录日志：`logger.info(f"查询用户关注列表: user_id={str(user_id)[:8]}, 返回{len(subscriptions)}条记录")`

---

#### 函数11: `delete_subscription`

**函数签名**:
```python
async def delete_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_id: uuid.UUID
) -> bool
```

**功能**: 删除用户关注记录（硬删除）

**执行流程**:
1. 查询关注记录：`stmt = select(UserExpertSubscription).where(and_(UserExpertSubscription.user_id == user_id, UserExpertSubscription.expert_id == expert_id))`
2. 执行查询：`result = await db.execute(stmt)`
3. 获取记录：`subscription = result.scalar_one_or_none()`
4. 如果subscription为None，返回False（由Service层处理404）
5. 提前提取用于日志的变量：`user_id_for_logging = str(user_id)[:8]`, `expert_id_for_logging = str(expert_id)[:8]`
6. 删除记录：`await db.delete(subscription)`
7. Flush：`await db.flush()`
8. 记录日志：`logger.info(f"删除关注记录成功: user_id={user_id_for_logging}, expert_id={expert_id_for_logging}")`
9. 返回True
10. 异常处理：
    ```python
    try:
        # ... 执行删除
    except Exception as e:
        await db.rollback()
        logger.error(f"删除关注记录失败: {str(e)}")
        raise
    ```

---

#### 函数12: `get_subscriptions_by_expert_ids`

**函数签名**:
```python
async def get_subscriptions_by_expert_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
    expert_ids: List[uuid.UUID]
) -> List[UserExpertSubscription]
```

**功能**: 批量查询用户是否关注了指定的专家列表

**执行流程**:
1. 构建查询：`stmt = select(UserExpertSubscription).where(and_(UserExpertSubscription.user_id == user_id, UserExpertSubscription.expert_id.in_(expert_ids)))`
2. 执行查询：`result = await db.execute(stmt)`
3. 返回结果：`result.scalars().all()`
4. 记录日志：`logger.debug(f"批量查询关注记录: user_id={str(user_id)[:8]}, expert_ids数量={len(expert_ids)}")`

---

### 5.3. LiveSessionExpert CRUD函数（3个）

#### 函数13: `get_session_experts`

**函数签名**:
```python
async def get_session_experts(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: Optional[str] = None
) -> List[LiveSessionExpert]
```

**功能**: 获取场次的专家列表（支持按角色筛选）

**执行流程**:
1. 构建查询：`stmt = select(LiveSessionExpert).where(LiveSessionExpert.session_id == session_id)`
2. 如果`role`不为None，添加筛选：`stmt = stmt.where(LiveSessionExpert.role == role)`
3. 应用排序：`stmt = stmt.order_by(LiveSessionExpert.sort_order.desc(), LiveSessionExpert.created_at.desc())`
4. 预加载专家信息：`stmt = stmt.options(selectinload(LiveSessionExpert.expert))`
5. 执行查询：`result = await db.execute(stmt)`
6. 返回结果：`result.scalars().all()`
7. 记录日志：`logger.info(f"查询场次专家列表: session_id={str(session_id)[:8]}, 返回{len(session_experts)}条记录")`

---

#### 函数14: `get_expert_sessions`

**函数签名**:
```python
async def get_expert_sessions(
    db: AsyncSession,
    expert_id: uuid.UUID,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[LiveSessionExpert], int]
```

**功能**: 获取专家参与的所有场次（分页，支持按角色筛选）

**执行流程**:
1. 构建基础查询：`stmt = select(LiveSessionExpert).where(LiveSessionExpert.expert_id == expert_id)`
2. 如果`role`不为None，添加筛选：`stmt = stmt.where(LiveSessionExpert.role == role)`
3. 预加载场次信息：`stmt = stmt.options(selectinload(LiveSessionExpert.session))`
4. 执行COUNT查询获取总数：`count_stmt = select(func.count()).select_from(stmt.subquery())`
5. 应用排序：`stmt = stmt.order_by(LiveSessionExpert.sort_order.desc(), LiveSessionExpert.created_at.desc())`
6. 应用分页：`stmt = stmt.offset(skip).limit(limit)`
7. 执行查询获取数据列表
8. 返回结果：`(result.scalars().all(), total)`
9. 记录日志：`logger.info(f"查询专家场次列表: expert_id={str(expert_id)[:8]}, 返回{len(session_experts)}条记录，总数={total}")`

---

#### 函数15: `set_session_experts`

**函数签名**:
```python
async def set_session_experts(
    db: AsyncSession,
    session_id: uuid.UUID,
    expert_data_list: List[Dict[str, Any]]  # 格式: [{"expert_id": UUID, "role": str, "sort_order": int}, ...]
) -> List[LiveSessionExpert]
```

**功能**: 为场次设置专家列表（先删除旧记录，再创建新记录）

**唯一性约束处理**:
- `UNIQUE(session_id, expert_id, role)`约束
- 如果违反唯一性，数据库会抛出`IntegrityError`
- **必须**捕获`IntegrityError`，转换为`DatabaseIntegrityException("场次专家关联已存在")`

**执行流程**:
1. 提前提取用于日志的变量：`session_id_for_logging = str(session_id)[:8]`
2. 删除旧记录：
   ```python
   delete_stmt = delete(LiveSessionExpert).where(LiveSessionExpert.session_id == session_id)
   await db.execute(delete_stmt)
   ```
3. 创建新记录：
   ```python
   new_session_experts = []
   for expert_data in expert_data_list:
       session_expert_id = uuid.uuid4()
       session_expert = LiveSessionExpert(
           id=session_expert_id,
           session_id=session_id,
           expert_id=expert_data["expert_id"],
           role=expert_data["role"],
           sort_order=expert_data.get("sort_order", 0)
       )
       db.add(session_expert)
       new_session_experts.append(session_expert)
   ```
4. Flush（不commit）：`await db.flush()` - 触发唯一性检查
5. 刷新对象：`await db.refresh(session_expert)` for each session_expert
6. 记录日志：`logger.info(f"设置场次专家列表成功: session_id={session_id_for_logging}, 专家数量={len(new_session_experts)}")`
7. 返回new_session_experts列表
8. 异常处理：
   ```python
   try:
       # ... 执行设置
   except IntegrityError as e:
       await db.rollback()
       logger.error(f"设置场次专家列表失败（唯一性冲突）: {str(e)}")
       raise DatabaseIntegrityException("场次专家关联已存在")
   except Exception as e:
       await db.rollback()
       logger.error(f"设置场次专家列表失败: {str(e)}")
       raise
   ```

---

## 6. SQL级权限过滤规范（最高优先级）

**🚨 [强制要求] SQL级权限过滤中的角色检查（最高优先级）**：

* **必须**使用大写进行角色检查：`if role not in ['ADMIN', 'SUPERADMIN']:`
* **禁止**使用小写：`if role not in ['admin', 'superadmin']:`  ❌
* **原因**：API层已经调用`.upper()`转换role为大写，CRUD层必须使用大写进行比较

**❌ 错误示例（禁止使用）**：
```python
# CRUD层错误
if role not in ['admin', 'superadmin']:  # ❌ 使用小写
    conditions.append(Expert.is_featured == True)
```

**✅ 正确示例（必须使用）**：
```python
# CRUD层正确
if role not in ['ADMIN', 'SUPERADMIN']:  # ✅ 使用大写
    conditions.append(Expert.is_featured == True)
```

**🚨 强制检查清单（每个CRUD函数必须验证）**：
- [ ] 是否使用大写`['ADMIN', 'SUPERADMIN']`进行角色检查？
- [ ] 是否避免了小写`['admin', 'superadmin']`？
- [ ] 是否与API层传递的大写role保持一致？

**注意**：如果CRUD函数需要接收`role`参数进行权限过滤，**必须**在函数签名中明确说明`role`参数的类型和格式要求。

---

## 7. 数据库初始化脚本更新要求

**⚠️ 关键：数据库表创建前提**

当你生成新的 SQLAlchemy 模型代码（如 `app/models/experts.py`）时，**必须同时**更新数据库初始化脚本，否则新表不会被创建。

**检查方式**: 检查 `app/models/__init__.py` 文件，确认是否已包含以下导入：

```python
# 专家模块模型（新增）
from .experts import Expert, UserExpertSubscription, LiveSessionExpert
```

**如果已包含**: 无需修改，继续生成CRUD代码。

**如果未包含**: 必须在生成CRUD代码时，同时更新 `app/models/__init__.py`：

**操作指令**（最小幅度修改要求）:
- **必须**识别新生成的所有模型类名称：`Expert`, `UserExpertSubscription`, `LiveSessionExpert`
- **必须**先检查文件末尾是否已有相同的导入语句（避免重复添加）
- **必须**在文件末尾追加新导入（保持空行和注释格式一致）
- **必须**添加注释说明这是新增模块
- **严禁**修改、删除或重新排序任何现有导入语句
- **严禁**修改文件中的任何其他代码

---

## 8. 代码生成要求

### 7.1. 文件头部

```python
"""
专家模块 CRUD 层

本模块封装所有与 Expert、UserExpertSubscription、LiveSessionExpert 模型相关的数据库操作。
提供纯粹的数据访问接口，不包含任何业务逻辑验证。

所有函数遵循以下规范：
- 使用 async/await 异步编程
- UUID 在应用层生成
- 使用 selectinload/joinedload 避免 N+1 查询
- 遵循安全异步异常处理原则（提前提取变量）
- 记录适当的日志
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any

# 第三方库导入
from sqlalchemy import select, delete, and_, or_, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert
from app.schemas.experts import ExpertCreate, ExpertUpdate
from app.exceptions import DatabaseIntegrityException

# 配置日志
logger = logging.getLogger(__name__)
```

### 7.2. 函数实现要求

1. **所有函数必须有完整的类型提示**
2. **所有函数必须有文档字符串**（说明参数、返回值、异常）
3. **写操作必须包含完整的异常处理**（try/except IntegrityError/finally）
4. **所有日志记录必须使用UUID脱敏**（只记录前8位）
5. **所有查询必须使用索引字段**（如`user_id`, `expert_id`, `session_id`）
6. **所有关系查询必须使用预加载**（selectinload或joinedload）

### 7.3. 参考代码风格

参考 `app/crud/topic.py` 的代码风格和结构，确保生成的代码风格一致。

---

## 9. 最终交付

生成完整的 `app/crud/experts.py` 文件，包含以上所有15个CRUD函数。

**文件路径**: `backend/live_core_service/app/crud/experts.py`

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**状态**: 准备就绪

