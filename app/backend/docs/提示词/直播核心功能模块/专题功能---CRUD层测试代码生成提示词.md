# 专题功能 CRUD 层测试代码生成提示词

## 1. 角色定义 (Role Definition)

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` for asynchronous code and FastAPI's `TestClient` for integration testing. Your task is to write a robust test suite for the **Topic Aggregation Feature CRUD Layer** of the `LiveCore Service`.

## 2. 任务目标 (Task Objective)

Your goal is to generate the complete code for **one test file**:

**`tests/unit/test_crud_topic.py`**: This file will contain detailed **unit tests** for the data access layer (`app/crud/topic.py`), ensuring each function works correctly in isolation.

### 测试策略 (Testing Strategy)

* **For `crud` layer:** Test thoroughly. This code is stable and foundational.
* **Focus:** Test all 20 CRUD functions defined in `app/crud/topic.py`, covering:
  - Topic operations (6 functions)
  - TopicCategory operations (6 functions)
  - TopicCategoryRoom operations (7 functions)
  - Auxiliary query operations (1 function)

## 3. 核心上下文信息 (Core Context Information)

### 3.1. 测试环境设置 (Testing Environment Setup)

* Assume a `pytest` environment is set up with `pytest-asyncio`.
* Assume a testing database is configured via `tests/conftest.py`.
* **DO NOT MODIFY** the existing `conftest.py` file. It contains working fixtures used by other tests. You may only **ADD NEW** fixtures if absolutely necessary.
* Use the existing `db_session` fixture from `conftest.py`.

### 3.2. 项目结构 (Project Structure)

```
backend/live_core_service/
├── app/
│   ├── crud/
│   │   └── topic.py              # <-- To be tested (20 functions)
│   ├── models/
│   │   ├── live_core.py          # <-- Existing (LiveRoom, LiveSession, SessionStatistics)
│   │   └── topic.py              # <-- Existing (Topic, TopicCategory, TopicCategoryRoom)
│   ├── schemas/
│   │   └── topic.py              # <-- Existing (Pydantic schemas)
│   └── exceptions.py             # <-- Existing (Custom exceptions)
└── tests/
    ├── conftest.py               # <-- DO NOT MODIFY (可以增加但不要修改现有内容)
    └── unit/
        └── test_crud_topic.py    # <-- To be generated
```

### 3.3. 已存在的代码全文 (Full Text of Existing Code)

**The CRUD functions to test are defined in `app/crud/topic.py` with 20 functions:**

#### **专题 (Topic) 相关操作 (6 functions):**
1. `create(db, obj_in, user_id)` - 创建新专题
2. `get(db, topic_id)` - 根据ID获取单个专题
3. `get_with_categories(db, topic_id)` - 获取专题及其所有分类（预加载）
4. `get_multi_and_total(db, skip, limit, status, user_id)` - 分页获取专题列表
5. `update(db, db_obj, obj_in)` - 更新专题信息
6. `remove(db, db_obj)` - 删除专题

#### **分类 (TopicCategory) 相关操作 (6 functions):**
7. `create_category(db, obj_in, topic_id)` - 创建新分类
8. `get_category(db, category_id)` - 根据ID获取单个分类
9. `get_category_with_topic(db, category_id)` - 获取分类及其关联的专题
10. `get_categories_by_topic(db, topic_id, skip, limit)` - 分页获取专题下的所有分类
11. `update_category(db, db_obj, obj_in)` - 更新分类信息
12. `remove_category(db, db_obj)` - 删除分类

#### **直播间关联 (TopicCategoryRoom) 相关操作 (7 functions):**
13. `add_room_to_category(db, category_id, room_id, sort_order)` - 将直播间添加到分类
14. `batch_add_rooms(db, category_id, room_associations)` - 批量添加直播间到分类
15. `get_rooms_by_category(db, category_id, skip, limit)` - 分页获取分类下的直播间列表
16. `update_room_sort_order(db, category_id, room_sort_updates)` - 批量更新分类下直播间的排序
17. `remove_room_from_category(db, category_id, room_id)` - 移除单个直播间关联
18. `batch_remove_rooms(db, category_id, room_ids)` - 批量移除直播间关联
19. `check_room_association_exists(db, category_id, room_id)` - 检查关联是否已存在

#### **辅助查询操作 (1 function):**
20. `get_topics_by_room(db, room_id)` - 获取指定直播间关联的所有已发布专题

### 3.4. 参考代码示例 (Reference Code Samples)

**已有的测试配置文件 `tests/conftest.py` 提供以下 fixtures：**

```python
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with async_session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """提供异步HTTP客户端"""
    # ... 实现代码 ...
```

**测试函数必须使用 `async for` 模式：**

```python
@pytest.mark.asyncio
async def test_example(db_session):
    """示例测试"""
    async for db in db_session:
        # 所有测试逻辑必须在 async for 块内
        # 1. Arrange: 准备测试数据
        # 2. Act: 执行被测试的函数
        # 3. Assert: 验证结果
        pass
```

## 4. 测试数据隔离 (Test Data Isolation)

### 4.1. 唯一性字段随机生成规则

为了防止测试之间因违反数据库 `UNIQUE` 约束而产生冲突，所有唯一性字段**必须**是随机生成的。

#### **实现要求：**

* **推荐使用 `faker` 库**: `pip install Faker`
* 所有生成的随机数据**必须**严格遵守 `app/schemas/topic.py` 中 Pydantic 模型的验证规则

#### **具体字段要求：**

**专题 (Topic) 相关字段：**

* **`title`**:
  - **规则**: 必须符合 `min_length=1`, `max_length=100`
  - **Faker 示例**: `f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}"`
  - **禁止**: 硬编码如 `"测试专题"`

* **`description`**:
  - **规则**: 可选字段，文本类型
  - **Faker 示例**: `fake.text(max_nb_chars=200)`

* **`banner_url`**:
  - **规则**: 可选字段，`max_length=255`
  - **Faker 示例**: `fake.image_url()`

**分类 (TopicCategory) 相关字段：**

* **`name`**:
  - **规则**: 必须符合 `min_length=1`, `max_length=50`
  - **注意**: 在同一专题下必须唯一 (unique constraint)
  - **Faker 示例**: `f"{fake.word()}_{uuid.uuid4().hex[:4]}"`

* **`sort_order`**:
  - **规则**: 整数，`ge=0`
  - **Faker 示例**: `fake.random_int(min=0, max=100)`

**直播间 (LiveRoom) 相关字段：**

* **`user_id`**:
  - **规则**: UUID 类型，必填字段 (nullable=False)
  - **示例**: `uuid.uuid4()`

* **`stream_key`**:
  - **规则**: 全局唯一 (unique constraint), 必填字段
  - **示例**: `f"key_{uuid.uuid4().hex}"`

* **`title`**:
  - **规则**: 必填字段，`max_length=100`
  - **Faker 示例**: `f"{fake.company()}_{uuid.uuid4().hex[:4]}"`

* **`description`**:
  - **规则**: 可选字段，文本类型
  - **Faker 示例**: `fake.text(max_nb_chars=50)`

#### **禁止事项：**

- ❌ 在测试的 Arrange 阶段使用硬编码的字符串（如 `'专题A'`）作为唯一性字段的值
- ❌ 重复使用相同的测试数据导致 `IntegrityError`
- ✅ 所有测试必须能独立运行且不依赖执行顺序

## 5. 测试函数生成规范

### 5.1. 必须严格遵循的测试函数模板

```python
# CRUD 测试模板（单 fixture）
@pytest.mark.asyncio
async def test_crud_operation(db_session):
    """测试描述：详细说明测试目的和验证点"""
    async for db in db_session:
        # 1. Arrange: 准备测试数据
        # 2. Act: 执行被测试的函数
        # 3. Assert: 验证结果
        pass
```

### 5.2. ⚠️ 禁止的写法

- ❌ 不得在 `async for` 外部调用数据库操作
- ❌ 不得直接使用 fixture 参数而不解包
- ❌ 不得在函数参数中添加类型提示（会导致混淆）
- ❌ 不得使用 `await db_session` 的方式

### 5.3. 测试模式 (AAA Pattern)

**所有测试必须遵循 Arrange-Act-Assert 模式：**

#### **1. 准备 (Arrange)**

在创建测试数据前，明确依赖关系：

```python
# 示例：测试创建分类需要先创建专题
async for db in db_session:
    # Step 1: 创建依赖数据（专题）
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCreate
    from app.models.topic import TopicStatus
    import uuid
    from faker import Faker
    
    fake = Faker()
    user_id = uuid.uuid4()
    
    topic_in = TopicCreate(
        title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
        description=fake.text(max_nb_chars=100),
        banner_url=fake.image_url(),
        status=TopicStatus.DRAFT
    )
    topic = await crud_topic.create(db, topic_in, user_id)
    
    # Step 2: 准备测试输入
    from app.schemas.topic import CategoryCreate
    
    category_in = CategoryCreate(
        name=f"{fake.word()}_{uuid.uuid4().hex[:4]}",
        sort_order=fake.random_int(min=0, max=10)
    )
```

#### **2. 执行 (Act)**

调用被测试的 CRUD 函数：

```python
    # 执行被测试的函数
    created_category = await crud_topic.create_category(
        db=db,
        obj_in=category_in,
        topic_id=topic.id
    )
```

#### **3. 断言 (Assert)**

**必须验证多个维度：**

```python
    # 断言 1: 验证返回对象不为空
    assert created_category is not None
    
    # 断言 2: 验证对象类型
    from app.models.topic import TopicCategory
    assert isinstance(created_category, TopicCategory)
    
    # 断言 3: 验证关键字段值
    assert created_category.name == category_in.name
    assert created_category.sort_order == category_in.sort_order
    assert created_category.topic_id == topic.id
    
    # 断言 4: 验证自动生成的字段
    assert created_category.id is not None
    assert created_category.created_at is not None
    assert created_category.updated_at is not None
    
    # 断言 5: 通过数据库查询验证数据持久化
    from sqlalchemy import select
    stmt = select(TopicCategory).where(TopicCategory.id == created_category.id)
    result = await db.execute(stmt)
    db_category = result.scalar_one_or_none()
    
    assert db_category is not None
    assert db_category.name == category_in.name
```

## 6. 具体测试用例规格 (Specific Test Case Specifications)

### 6.1. 专题 (Topic) 相关测试 (7 tests)

#### **Test 1: `test_create_topic_success`**

**测试目标**: 验证成功创建新专题

**步骤**:
1. **Arrange**: 
   - 生成随机 `user_id`
   - 使用 faker 创建 `TopicCreate` 对象（包含 title, description, banner_url, status）
2. **Act**: 
   - 调用 `crud_topic.create(db, obj_in, user_id)`
3. **Assert**:
   - 验证返回的 Topic 对象不为 None
   - 验证 `topic.id` 是 UUID 类型
   - 验证 `topic.user_id == user_id`
   - 验证 `topic.title == obj_in.title`
   - 验证 `topic.status == obj_in.status`
   - 验证 `created_at` 和 `updated_at` 已设置
   - **数据库验证**: 使用 `select` 语句查询数据库，确认记录存在

#### **Test 2: `test_get_topic_by_id_success`**

**测试目标**: 验证根据ID获取专题

**步骤**:
1. **Arrange**: 先创建一个专题
2. **Act**: 调用 `crud_topic.get(db, topic_id)`
3. **Assert**:
   - 验证返回的对象不为 None
   - 验证 `topic.id` 与创建时的 ID 一致
   - 验证其他字段值正确

#### **Test 3: `test_get_topic_by_id_not_found`**

**测试目标**: 验证获取不存在的专题返回 None

**步骤**:
1. **Arrange**: 生成一个随机的、不存在的 UUID
2. **Act**: 调用 `crud_topic.get(db, random_uuid)`
3. **Assert**:
   - 验证返回值为 `None`

#### **Test 4: `test_get_with_categories_success`**

**测试目标**: 验证获取专题时预加载分类列表

**步骤**:
1. **Arrange**: 
   - 创建一个专题
   - 为该专题创建 2-3 个分类
2. **Act**: 调用 `crud_topic.get_with_categories(db, topic_id)`
3. **Assert**:
   - 验证返回的 Topic 对象不为 None
   - **关键验证**: 验证 `topic.categories` 已被预加载（不为空列表）
   - 验证 `len(topic.categories) == 创建的分类数量`
   - 验证分类按 `sort_order` 排序

#### **Test 5: `test_get_multi_and_total_with_filters`**

**测试目标**: 验证分页获取专题列表，支持状态和用户ID筛选

**步骤**:
1. **Arrange**: 
   - 创建多个专题（至少5个）
   - 使用不同的 `user_id` 和 `status` 值
   - 例如: 2个使用 `TopicStatus.PUBLISHED`, 3个使用 `TopicStatus.DRAFT`；属于不同用户
2. **Act**: 
   - 调用 `crud_topic.get_multi_and_total(db, skip=0, limit=10, status=TopicStatus.PUBLISHED, user_id=specific_user_id)`
3. **Assert**:
   - 验证返回的 tuple 格式: `(topics_list, total_count)`
   - 验证筛选后的列表长度正确
   - 验证所有返回的专题的 `status == TopicStatus.PUBLISHED`
   - 验证所有返回的专题的 `user_id == specific_user_id`
   - 验证 `total_count` 数值正确

#### **Test 6: `test_update_topic_success`**

**测试目标**: 验证更新专题信息

**步骤**:
1. **Arrange**: 
   - 创建一个专题
   - 准备 `TopicUpdate` 对象，更新 title 和 status
2. **Act**: 
   - 调用 `crud_topic.update(db, db_obj=topic, obj_in=update_data)`
3. **Assert**:
   - 验证返回的对象不为 None
   - 验证 `topic.title` 已更新为新值
   - 验证 `topic.status` 已更新
   - **数据库验证**: 重新查询数据库，确认更新已持久化
   - 验证 `updated_at` 时间戳已更新

#### **Test 7: `test_remove_topic_success`**

**测试目标**: 验证删除专题及级联删除

**步骤**:
1. **Arrange**: 
   - 创建一个专题
   - 为该专题创建 1-2 个分类
   - 记录 `topic_id` 和 `category_ids`
2. **Act**: 
   - 调用 `crud_topic.remove(db, db_obj=topic)`
3. **Assert**:
   - **数据库验证 1**: 查询 Topic 表，确认专题已删除（返回 None）
   - **数据库验证 2**: 查询 TopicCategory 表，确认关联的分类也已被级联删除

### 6.2. 分类 (TopicCategory) 相关测试 (7 tests)

#### **Test 8: `test_create_category_success`**

**测试目标**: 验证成功创建分类

**步骤**:
1. **Arrange**: 
   - 先创建一个专题
   - 使用 faker 创建 `CategoryCreate` 对象
2. **Act**: 
   - 调用 `crud_topic.create_category(db, obj_in, topic_id)`
3. **Assert**:
   - 验证返回的 TopicCategory 对象不为 None
   - 验证 `category.topic_id == topic.id`
   - 验证 `category.name` 和 `category.sort_order` 正确
   - **数据库验证**: 查询确认记录存在

#### **Test 9: `test_create_category_duplicate_name_fails`**

**测试目标**: 验证在同一专题下创建重名分类失败

**步骤**:
1. **Arrange**: 
   - 创建一个专题
   - 创建第一个分类（name = "分类A"）
   - 准备第二个 `CategoryCreate` 对象，使用相同的 name
2. **Act & Assert**: 
   - 调用 `crud_topic.create_category()`
   - **预期抛出 `IntegrityError`** (因为违反 unique constraint)
   - 使用 `pytest.raises(IntegrityError)` 捕获异常

#### **Test 10: `test_get_category_by_id_success`**

**测试目标**: 验证根据ID获取分类

**步骤**:
1. **Arrange**: 先创建专题和分类
2. **Act**: 调用 `crud_topic.get_category(db, category_id)`
3. **Assert**:
   - 验证返回的对象不为 None
   - 验证 `category.id` 正确

#### **Test 11: `test_get_category_with_topic_success`**

**测试目标**: 验证获取分类时预加载专题对象

**步骤**:
1. **Arrange**: 创建专题和分类
2. **Act**: 调用 `crud_topic.get_category_with_topic(db, category_id)`
3. **Assert**:
   - 验证返回的 category 不为 None
   - **关键验证**: 验证 `category.topic` 已被预加载（不为 None）
   - 验证 `category.topic.id == topic.id`

#### **Test 12: `test_get_categories_by_topic_pagination`**

**测试目标**: 验证分页获取专题下的分类列表

**步骤**:
1. **Arrange**: 
   - 创建一个专题
   - 创建 5 个分类，设置不同的 `sort_order` (0, 10, 20, 30, 40)
2. **Act**: 
   - 调用 `crud_topic.get_categories_by_topic(db, topic_id, skip=0, limit=3)`
3. **Assert**:
   - 验证返回的 tuple: `(categories_list, total_count)`
   - 验证 `len(categories_list) == 3`
   - 验证 `total_count == 5`
   - **关键验证**: 验证返回的分类按 `sort_order ASC` 排序

#### **Test 13: `test_update_category_success`**

**测试目标**: 验证更新分类信息

**步骤**:
1. **Arrange**: 
   - 创建专题和分类
   - 准备 `CategoryUpdate` 对象，更新 name 和 sort_order
2. **Act**: 
   - 调用 `crud_topic.update_category(db, db_obj=category, obj_in=update_data)`
3. **Assert**:
   - 验证 `category.name` 已更新
   - 验证 `category.sort_order` 已更新
   - **数据库验证**: 重新查询确认持久化

#### **Test 14: `test_remove_category_success`**

**测试目标**: 验证删除分类及级联删除

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建一个直播间，并添加到该分类
   - 记录 `category_id` 和 `association_id`
2. **Act**: 
   - 调用 `crud_topic.remove_category(db, db_obj=category)`
3. **Assert**:
   - **数据库验证 1**: 查询 TopicCategory 表，确认分类已删除
   - **数据库验证 2**: 查询 TopicCategoryRoom 表，确认关联记录也被级联删除

### 6.3. 直播间关联 (TopicCategoryRoom) 相关测试 (9 tests)

#### **Test 15: `test_add_room_to_category_success`**

**测试目标**: 验证成功添加直播间到分类

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建一个 LiveRoom
2. **Act**: 
   - 调用 `crud_topic.add_room_to_category(db, category_id, room_id, sort_order=10)`
3. **Assert**:
   - 验证返回的 TopicCategoryRoom 对象不为 None
   - 验证 `association.category_id == category.id`
   - 验证 `association.room_id == room.id`
   - 验证 `association.sort_order == 10`
   - **数据库验证**: 查询确认关联记录存在

#### **Test 16: `test_add_room_duplicate_fails`**

**测试目标**: 验证重复添加同一直播间到同一分类失败

**步骤**:
1. **Arrange**: 
   - 创建专题、分类、直播间
   - 第一次添加直播间到分类
2. **Act & Assert**: 
   - 尝试第二次添加相同的直播间
   - **预期抛出 `IntegrityError`**（违反 unique constraint: uq_category_room）

#### **Test 17: `test_batch_add_rooms_success`**

**测试目标**: 验证批量添加多个直播间

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建 3 个 LiveRoom
   - 准备 `List[RoomAssociation]`，包含 3 个直播间的信息
2. **Act**: 
   - 调用 `crud_topic.batch_add_rooms(db, category_id, room_associations)`
3. **Assert**:
   - 验证返回的列表长度为 3
   - 验证每个 association 的字段值正确
   - **数据库验证**: 查询 TopicCategoryRoom 表，确认 3 条记录都已插入

#### **Test 18: `test_get_rooms_by_category_pagination`**

**测试目标**: 验证分页获取分类下的直播间列表

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建 5 个直播间并添加到分类，设置不同的 sort_order
2. **Act**: 
   - 调用 `crud_topic.get_rooms_by_category(db, category_id, skip=0, limit=3)`
3. **Assert**:
   - 验证返回的 tuple: `(rooms_list, total_count)`
   - 验证 `len(rooms_list) == 3`
   - 验证 `total_count == 5`
   - 验证每个返回的字典包含: `room_id`, `title`, `cover_url`, `sort_order` 等字段
   - **关键验证**: 验证返回的直播间按 `sort_order ASC` 排序

#### **Test 19: `test_update_room_sort_order_success`**

**测试目标**: 验证批量更新直播间排序

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 添加 3 个直播间，初始 sort_order 为 [10, 20, 30]
   - 准备更新数据: `[{"room_id": room1_id, "sort_order": 100}, {"room_id": room2_id, "sort_order": 200}]`
2. **Act**: 
   - 调用 `crud_topic.update_room_sort_order(db, category_id, room_sort_updates)`
3. **Assert**:
   - 验证返回的更新记录数 `== 2`
   - **数据库验证**: 查询 TopicCategoryRoom 表，确认对应记录的 sort_order 已更新为新值

#### **Test 20: `test_remove_room_from_category_success`**

**测试目标**: 验证移除单个直播间关联

**步骤**:
1. **Arrange**: 
   - 创建专题、分类、直播间
   - 添加直播间到分类
2. **Act**: 
   - 调用 `crud_topic.remove_room_from_category(db, category_id, room_id)`
3. **Assert**:
   - 验证返回值为 `True`（删除成功）
   - **数据库验证**: 查询 TopicCategoryRoom 表，确认关联记录已删除（返回 None）

#### **Test 21: `test_remove_room_not_exists_returns_false`**

**测试目标**: 验证移除不存在的关联返回 False

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建一个直播间但**不添加**到分类
2. **Act**: 
   - 调用 `crud_topic.remove_room_from_category(db, category_id, room_id)`
3. **Assert**:
   - 验证返回值为 `False`

#### **Test 22: `test_batch_remove_rooms_success`**

**测试目标**: 验证批量移除直播间关联

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 添加 5 个直播间到分类
   - 选择其中 3 个直播间的 ID
2. **Act**: 
   - 调用 `crud_topic.batch_remove_rooms(db, category_id, [room1_id, room2_id, room3_id])`
3. **Assert**:
   - 验证返回的删除记录数 `== 3`
   - **数据库验证**: 查询 TopicCategoryRoom 表，确认 3 条记录已删除，剩余 2 条

#### **Test 23: `test_check_room_association_exists`**

**测试目标**: 验证检查关联是否存在

**步骤**:
1. **Arrange**: 
   - 创建专题、分类
   - 创建两个直播间：room1 添加到分类，room2 不添加
2. **Act & Assert**: 
   - 调用 `crud_topic.check_room_association_exists(db, category_id, room1_id)`
   - 验证返回 `True`
   - 调用 `crud_topic.check_room_association_exists(db, category_id, room2_id)`
   - 验证返回 `False`

### 6.4. 辅助查询操作测试 (1 test)

#### **Test 24: `test_get_topics_by_room_success`**

**测试目标**: 验证获取直播间关联的所有已发布专题

**步骤**:
1. **Arrange**: 
   - 创建 3 个专题：2 个使用 `TopicStatus.PUBLISHED`，1 个使用 `TopicStatus.DRAFT`
   - 为每个专题创建分类
   - 创建一个直播间
   - 将该直播间添加到所有 3 个分类
2. **Act**: 
   - 调用 `crud_topic.get_topics_by_room(db, room_id)`
3. **Assert**:
   - 验证返回的列表长度为 `2`（只包含 PUBLISHED 状态的专题）
   - 验证每个字典包含: `topic_id`, `topic_title`, `topic_status`, `category_id`, `category_name`
   - 验证所有返回的 `topic_status` 值为 `"published"` 字符串（因为函数返回的是字典，status 被转换为字符串）

## 7. 辅助函数 (Helper Functions)

### 7.1. 创建测试专题

```python
async def create_test_topic(db: AsyncSession, user_id: uuid.UUID = None) -> Topic:
    """创建测试专题的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCreate
    from app.models.topic import TopicStatus
    from faker import Faker
    
    if user_id is None:
        user_id = uuid.uuid4()
    
    fake = Faker()
    topic_in = TopicCreate(
        title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
        description=fake.text(max_nb_chars=100),
        banner_url=fake.image_url(),
        status=TopicStatus.DRAFT
    )
    
    return await crud_topic.create(db, topic_in, user_id)
```

### 7.2. 创建测试分类

```python
async def create_test_category(db: AsyncSession, topic_id: uuid.UUID) -> TopicCategory:
    """创建测试分类的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import CategoryCreate
    from faker import Faker
    
    fake = Faker()
    category_in = CategoryCreate(
        name=f"{fake.word()}_{uuid.uuid4().hex[:4]}",
        sort_order=fake.random_int(min=0, max=10)
    )
    
    return await crud_topic.create_category(db, category_in, topic_id)
```

### 7.3. 创建测试直播间

```python
async def create_test_room(db: AsyncSession) -> LiveRoom:
    """创建测试直播间的辅助函数"""
    from app.models.live_core import LiveRoom
    from faker import Faker
    import uuid
    
    fake = Faker()
    room = LiveRoom(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"{fake.company()}_{uuid.uuid4().hex[:4]}",
        description=fake.text(max_nb_chars=50),
        stream_key=f"key_{uuid.uuid4().hex}",
        is_private=False,
        record_by_default=True
    )
    
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room
```

## 8. 代码质量要求

### 8.1. 导入语句规范

```python
"""
LiveCore Service - Topic CRUD Unit Tests

This module contains unit tests for all CRUD operations in app/crud/topic.py.
"""

import uuid
import pytest
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from faker import Faker

# 项目内导入
from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom
from app.schemas.topic import (
    TopicCreate, TopicUpdate,
    CategoryCreate, CategoryUpdate,
    RoomAssociation
)

# 初始化 Faker
fake = Faker()
```

### 8.2. 文档字符串规范

每个测试函数必须包含详细的文档字符串：

```python
@pytest.mark.asyncio
async def test_create_topic_success(db_session):
    """
    测试成功创建新专题
    
    验证点:
    1. 返回的 Topic 对象不为 None
    2. 自动生成的 UUID 有效
    3. user_id 正确关联
    4. 所有字段值与输入一致
    5. created_at 和 updated_at 时间戳已设置
    6. 数据库中成功插入记录
    """
    async for db in db_session:
        # 测试逻辑 ...
```

### 8.3. 断言消息规范

所有断言必须包含清晰的错误消息：

```python
assert created_topic is not None, "创建专题失败，返回了 None"
assert created_topic.title == topic_in.title, f"专题标题不匹配: 期望 {topic_in.title}, 实际 {created_topic.title}"
assert isinstance(created_topic.id, uuid.UUID), f"专题 ID 类型错误: {type(created_topic.id)}"
```

## 9. 最终交付 (Final Deliverable)

Please generate the complete, runnable Python code for the following file, placed in a clearly marked code block:

**`tests/unit/test_crud_topic.py`**

**代码应包含**:
- 完整的模块文档字符串
- 所有必要的导入语句
- 3 个辅助函数（create_test_topic, create_test_category, create_test_room）
- 上述列出的 24 个测试函数
- 每个测试函数都严格遵循 `async for` 模式
- 完整的类型注解（仅在辅助函数中使用）
- 详细的函数文档字符串
- 适当的断言消息
- 所有测试数据使用 faker 生成，确保唯一性

**代码格式要求**:
- 使用 4 个空格缩进
- 每个测试函数之间空 2 行
- 导入语句按标准库、第三方库、项目内导入分组
- 所有测试函数按照上述编号顺序排列
- 确保所有测试可以独立运行且不依赖执行顺序

---

## 附录：快速检查清单

生成代码后，请确认以下内容：

### 测试覆盖率
- [ ] 20 个 CRUD 函数全部有对应测试
- [ ] 包含成功路径测试
- [ ] 包含失败路径测试（如重复插入、不存在的记录）
- [ ] 包含边界条件测试（如空列表、分页边界）

### 代码规范
- [ ] 所有测试使用 `@pytest.mark.asyncio` 装饰器
- [ ] 所有测试使用 `async for db in db_session:` 模式
- [ ] 所有唯一性字段使用 faker 或 uuid 生成随机值
- [ ] 所有测试包含详细的文档字符串
- [ ] 所有断言包含清晰的错误消息

### 数据库验证
- [ ] 所有创建操作都验证数据库中记录存在
- [ ] 所有更新操作都重新查询数据库验证持久化
- [ ] 所有删除操作都验证记录已被删除
- [ ] 所有级联删除操作都验证子记录也被删除

### 预加载验证
- [ ] `get_with_categories` 验证 categories 关系已加载
- [ ] `get_category_with_topic` 验证 topic 关系已加载
- [ ] `get_rooms_by_category` 验证返回的数据包含 room 详情

### 排序验证
- [ ] 分类列表按 `sort_order ASC` 排序
- [ ] 直播间列表按 `sort_order ASC` 排序
- [ ] 专题列表按 `created_at DESC` 排序

---

**现在，请开始生成测试代码！**

