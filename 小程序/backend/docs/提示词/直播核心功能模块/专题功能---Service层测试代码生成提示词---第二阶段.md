# 专题功能 Service 层测试代码生成提示词（第二阶段）

## 1. 角色定义 (Role Definition)

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` for asynchronous code and `unittest.mock` for mocking dependencies. Your task is to write a robust test suite for the **Topic Aggregation Feature Service Layer** of the `LiveCore Service`.

## 2. 任务目标 (Task Objective)

Your goal is to generate the complete code for **one test file**:

**`tests/unit/test_service_topic.py`**: This file will contain detailed **unit tests** for the service layer (`app/services/topic_service.py`), ensuring each business logic method works correctly in complete isolation with all dependencies mocked.

## 3. 核心上下文信息 (Core Context Information)

### 3.1. Testing Strategy

* The `TopicService` must be tested in **complete isolation**.
* All of its external dependencies, specifically all functions within the **`app.crud.topic` module, must be "mocked"**. These tests must not make any real database calls.
* Focus on testing business logic, permission checks, and exception handling.

**⚠️ 关键概念：CRUD 模块导入与 Mock 路径**

Service 层在 `app/services/topic_service.py` 中使用以下方式导入 CRUD 模块：
```python
from app.crud import topic as crud_topic  # 使用别名 crud_topic
```

在 Service 层代码中，所有 CRUD 调用都使用别名：
```python
topic = await crud_topic.create(self.db, obj_in, user_id)  # ✅ 使用 crud_topic
category = await crud_topic.get_category_with_topic(self.db, category_id)  # ✅ 使用 crud_topic
```

**但在测试中 Mock 时，必须使用原始模块路径：**
```python
mocker.patch("app.crud.topic.create", ...)  # ✅ Mock 原始路径
mocker.patch("app.crud.topic.get_category_with_topic", ...)  # ✅ Mock 原始路径
```

**禁止的错误写法：**
```python
# ❌ 错误：使用别名路径（模块不存在）
mocker.patch("app.crud_topic.create", ...)

# ❌ 错误：Mock Service 内部引用
mocker.patch("app.services.topic_service.crud_topic.create", ...)
```

### 3.2. Project and Code Context

* **Test File to Create:** `tests/unit/test_service_topic.py`
* **No `conftest.py` Changes Needed:** These tests will not use database fixtures because all dependencies will be mocked.
* **Key Files for Context:**
    * `app/services/topic_service.py` (The class to be tested - 16 methods)
    * `app/crud/topic.py` (The module whose functions will be mocked - 20 functions)
    * `app/exceptions.py` (Contains the custom exceptions that will be asserted)
    * `app/models/topic.py` and `app/schemas/topic.py` (For creating mock data objects)

### 3.3. Project Structure

```
backend/live_core_service/
├── app/
│   ├── api/v1/endpoints/
│   │   └── topic.py              # <-- Existing code context
│   ├── crud/
│   │   └── topic.py              # <-- Existing code (to be mocked)
│   ├── services/
│   │   └── topic_service.py      # <-- To be tested (16 methods)
│   ├── models/
│   │   ├── live_core.py          # <-- Existing (LiveRoom, LiveSession)
│   │   └── topic.py              # <-- Existing (Topic, TopicCategory, TopicCategoryRoom, TopicStatus)
│   ├── schemas/
│   │   └── topic.py              # <-- Existing (Pydantic schemas)
│   └── exceptions.py             # <-- Existing (Custom exceptions)
└── tests/
    ├── conftest.py               # <-- Existing (no changes needed)
    └── unit/
        └── test_service_topic.py # <-- To be generated
```

### 3.4. TopicService 方法列表 (16 methods to test)

**专题管理方法 (5 methods):**
1. `create_topic(obj_in, user_id)` - 创建专题
2. `get_topic_list(page, size, status, user_id)` - 获取专题列表
3. `get_topic_detail(topic_id)` - 获取专题详情（层级化）
4. `update_topic(topic_id, user_id, obj_in)` - 更新专题（含权限检查）
5. `delete_topic(topic_id, user_id)` - 删除专题（含权限检查）

**分类管理方法 (5 methods):**
6. `create_category(topic_id, user_id, obj_in)` - 创建分类（含权限检查）
7. `get_category_list(topic_id, page, size)` - 获取分类列表
8. `update_category(category_id, user_id, obj_in)` - 更新分类（含权限检查）
9. `delete_category(category_id, user_id)` - 删除分类（含权限检查）

**直播间关联方法 (4 methods):**
10. `add_rooms_to_category(category_id, user_id, room_associations)` - 批量添加直播间（含权限和存在性检查）
11. `get_rooms_in_category(category_id, page, size)` - 获取分类下的直播间列表
12. `update_room_sort_order(category_id, user_id, room_sort_updates)` - 更新排序（含权限检查）
13. `remove_rooms_from_category(category_id, user_id, room_ids)` - 移除直播间（含权限检查）

**辅助查询方法 (2 methods):**
14. `get_topics_by_room(room_id)` - 获取直播间关联的专题
15. `batch_get_room_status(room_ids)` - 批量获取直播间状态

### 3.5. 自定义异常 (Custom Exceptions)

```python
# From app/exceptions.py
class TopicNotFoundException(Exception):
    """专题不存在"""
    pass

class CategoryNotFoundException(Exception):
    """分类不存在"""
    pass

class TopicPermissionDeniedException(Exception):
    """权限不足"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class RoomAlreadyAssociatedException(Exception):
    """直播间已关联"""
    def __init__(self, room_id: str, category_id: str):
        self.room_id = room_id
        self.category_id = category_id
        super().__init__(f"Room {room_id} already associated with category {category_id}")

class RoomNotFoundException(Exception):
    """直播间不存在"""
    pass
```

## 4. Mock 策略和规范

### 4.1. General Setup

* Import `pytest`, `uuid`, `unittest.mock.AsyncMock`, and `unittest.mock.patch`
* Import the necessary classes: `TopicService`, `schemas`, `models`, and custom exceptions
* All test functions must be `async def` and marked with `@pytest.mark.asyncio`
* Each test function should use `mocker` fixture from `pytest-mock` or `unittest.mock.patch`

### 4.2. Mock Target Pattern

**⚠️ 关键原则：始终 Mock 原始模块路径**

Service 层使用以下方式导入 CRUD 模块：
```python
from app.crud import topic as crud_topic  # Service 层的导入方式
```

在 Service 层代码中调用：
```python
topic = await crud_topic.create(self.db, obj_in, user_id)  # 使用别名 crud_topic
```

**但在测试中 Mock 时，必须使用原始模块路径：**

```python
# ✅ 正确：Mock CRUD 模块的原始路径
mocker.patch("app.crud.topic.create", return_value=mock_topic)
mocker.patch("app.crud.topic.get", return_value=mock_topic)
mocker.patch("app.crud.topic.get_with_categories", return_value=mock_topic)

# ❌ 错误示例 1：使用别名路径（不存在的模块）
# mocker.patch("app.crud_topic.create")  # ModuleNotFoundError!

# ❌ 错误示例 2：Mock Service 内部的引用
# mocker.patch("app.services.topic_service.crud_topic.create")  # 不推荐

# ❌ 错误示例 3：Mock Service 类的方法
# mocker.patch("app.services.topic_service.TopicService.create_topic")  # 错误!
```

**原理说明**：
- Python 的 `unittest.mock.patch` 需要使用**模块的原始导入路径**
- 别名（如 `crud_topic`）只在 Service 文件的命名空间中有效
- Mock 的是模块本身，而不是模块的引用或别名

### 4.3. AsyncMock 使用规范

```python
from unittest.mock import AsyncMock

# 对于异步函数，必须使用 AsyncMock
mock_crud_get = AsyncMock(return_value=mock_topic)
mocker.patch("app.crud.topic.get", side_effect=mock_crud_get)

# 或者使用 new_callable 参数
mocker.patch("app.crud.topic.get", return_value=mock_topic, new_callable=AsyncMock)
```

### 4.4. Mock 数据对象创建

```python
from app.models.topic import Topic, TopicCategory, TopicStatus
import uuid
from datetime import datetime

def create_mock_topic(
    user_id: uuid.UUID = None,
    status: TopicStatus = TopicStatus.DRAFT
) -> Topic:
    """创建Mock的Topic对象"""
    if user_id is None:
        user_id = uuid.uuid4()
    
    mock_topic = Topic(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Test Topic",
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=status
    )
    # 模拟数据库字段
    mock_topic.created_at = datetime.now()
    mock_topic.updated_at = datetime.now()
    
    return mock_topic
```

## 5. 测试用例规格

### 5.1. 专题管理方法测试

#### **Test 1: `test_create_topic_success`**

```python
@pytest.mark.asyncio
async def test_create_topic_success(mocker):
    """
    测试成功创建专题
    
    验证点:
    1. 调用 crud_topic.create 一次（Service 层调用）
    2. 返回创建的 Topic 对象
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.schemas.topic import TopicCreate
    from app.models.topic import Topic, TopicStatus
    import uuid
    
    mock_db = mocker.Mock()
    user_id = uuid.uuid4()
    
    topic_in = TopicCreate(
        title="Test Topic",
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=TopicStatus.DRAFT
    )
    
    mock_topic = Topic(
        id=uuid.uuid4(),
        user_id=user_id,
        title=topic_in.title,
        description=topic_in.description,
        banner_url=topic_in.banner_url,
        status=topic_in.status
    )
    
    # Mock CRUD 函数 crud_topic.create
    # 注意：mock 时使用原始模块路径 "app.crud.topic.create"
    mock_create = mocker.patch(
        "app.crud.topic.create",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    # Act
    service = TopicService(mock_db)
    result = await service.create_topic(topic_in, user_id)
    
    # Assert
    mock_create.assert_called_once_with(mock_db, topic_in, user_id)
    assert result == mock_topic
    assert result.title == topic_in.title
```

#### **Test 2: `test_update_topic_success`**
- **Mock**: `crud_topic.get()` 返回 mock_topic（Mock路径: `"app.crud.topic.get"`）
- **Mock**: `crud_topic.update()` 返回 updated_mock_topic（Mock路径: `"app.crud.topic.update"`）
- **验证**: update被调用，权限检查通过

#### **Test 3: `test_update_topic_not_found`**
- **Mock**: `crud_topic.get()` 返回 None（Mock路径: `"app.crud.topic.get"`）
- **验证**: 抛出 `TopicNotFoundException`

#### **Test 4: `test_update_topic_permission_denied`**
- **Mock**: `crud_topic.get()` 返回 mock_topic（不同user_id）（Mock路径: `"app.crud.topic.get"`）
- **验证**: 抛出 `TopicPermissionDeniedException`

#### **Test 5: `test_delete_topic_success`**
- **Mock**: `crud_topic.get_with_categories()` 返回 mock_topic（Mock路径: `"app.crud.topic.get_with_categories"`）
- **Mock**: `crud_topic.remove()` （Mock路径: `"app.crud.topic.remove"`）
- **验证**: 权限检查通过，remove被调用

#### **Test 6: `test_delete_topic_permission_denied`**
- **Mock**: `crud_topic.get_with_categories()` 返回 mock_topic（不同user_id）（Mock路径: `"app.crud.topic.get_with_categories"`）
- **验证**: 抛出 `TopicPermissionDeniedException`

#### **Test 7: `test_get_topic_list_success`**
- **Mock**: `crud_topic.get_multi_and_total()` 返回 ([mock_topic1, mock_topic2], 2)（Mock路径: `"app.crud.topic.get_multi_and_total"`）
- **验证**: 返回的列表和总数正确

#### **Test 8: `test_get_topic_detail_success`**
- **Mock**: `crud_topic.get_with_categories()` 返回 mock_topic（含categories）（Mock路径: `"app.crud.topic.get_with_categories"`）
- **Mock**: `crud_topic.get_rooms_by_category()` 返回房间列表（Mock路径: `"app.crud.topic.get_rooms_by_category"`）
- **验证**: 返回层级化的专题详情字典

#### **Test 9: `test_get_topic_detail_not_found`**
- **Mock**: `crud_topic.get_with_categories()` 返回 None（Mock路径: `"app.crud.topic.get_with_categories"`）
- **验证**: 抛出 `TopicNotFoundException`

### 5.2. 分类管理方法测试

#### **Test 10: `test_create_category_success`**
- **Mock**: `crud_topic.get()` 返回 mock_topic（Mock路径: `"app.crud.topic.get"`）
- **Mock**: `crud_topic.create_category()` 返回 mock_category（Mock路径: `"app.crud.topic.create_category"`）
- **验证**: 权限检查通过，category被创建

#### **Test 11: `test_create_category_topic_not_found`**
- **Mock**: `crud_topic.get()` 返回 None（Mock路径: `"app.crud.topic.get"`）
- **验证**: 抛出 `TopicNotFoundException`

#### **Test 12: `test_create_category_permission_denied`**
- **Mock**: `crud_topic.get()` 返回 mock_topic（不同user_id）（Mock路径: `"app.crud.topic.get"`）
- **验证**: 抛出 `TopicPermissionDeniedException`

#### **Test 13: `test_update_category_success`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: `crud_topic.update_category()` 返回 updated_category（Mock路径: `"app.crud.topic.update_category"`）
- **验证**: 权限检查通过，update被调用

#### **Test 14: `test_update_category_not_found`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 None（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **验证**: 抛出 `CategoryNotFoundException`

#### **Test 15: `test_update_category_permission_denied`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（topic的user_id不匹配）（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **验证**: 抛出 `TopicPermissionDeniedException`

#### **Test 16: `test_delete_category_success`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: `crud_topic.remove_category()`（Mock路径: `"app.crud.topic.remove_category"`）
- **验证**: 权限检查通过，remove被调用

#### **Test 17: `test_get_category_list_success`**
- **Mock**: `crud_topic.get()` 返回 mock_topic（Mock路径: `"app.crud.topic.get"`）
- **Mock**: `crud_topic.get_categories_by_topic()` 返回 ([category1, category2], 2)（Mock路径: `"app.crud.topic.get_categories_by_topic"`）
- **验证**: 返回的列表和总数正确

#### **Test 18: `test_get_category_list_topic_not_found`**
- **Mock**: `crud_topic.get()` 返回 None（Mock路径: `"app.crud.topic.get"`）
- **验证**: 抛出 `TopicNotFoundException`

### 5.3. 直播间关联方法测试

#### **Test 19: `test_add_rooms_to_category_success`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: db.execute 返回存在的room_ids
- **Mock**: `crud_topic.check_room_association_exists()` 返回 False（Mock路径: `"app.crud.topic.check_room_association_exists"`）
- **Mock**: `crud_topic.batch_add_rooms()` 返回关联列表（Mock路径: `"app.crud.topic.batch_add_rooms"`）
- **验证**: 所有检查通过，batch_add_rooms被调用

#### **Test 20: `test_add_rooms_to_category_permission_denied`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（user_id不匹配）（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **验证**: 抛出 `TopicPermissionDeniedException`

#### **Test 21: `test_add_rooms_to_category_room_not_found`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: db.execute 返回部分room_ids（有缺失）
- **验证**: 抛出 `RoomNotFoundException`

#### **Test 22: `test_add_rooms_to_category_already_associated`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: db.execute 返回存在的room_ids
- **Mock**: `crud_topic.check_room_association_exists()` 返回 True（Mock路径: `"app.crud.topic.check_room_association_exists"`）
- **验证**: 抛出 `RoomAlreadyAssociatedException`

#### **Test 23: `test_get_rooms_in_category_success`**
- **Mock**: `crud_topic.get_category()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category"`）
- **Mock**: `crud_topic.get_rooms_by_category()` 返回房间列表（Mock路径: `"app.crud.topic.get_rooms_by_category"`）
- **Mock**: db.execute 返回最新的LiveSession状态
- **验证**: 返回包含live_status的房间列表

#### **Test 24: `test_update_room_sort_order_success`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: `crud_topic.update_room_sort_order()` 返回更新数量（Mock路径: `"app.crud.topic.update_room_sort_order"`）
- **验证**: 权限检查通过，update被调用

#### **Test 25: `test_remove_rooms_from_category_success`**
- **Mock**: `crud_topic.get_category_with_topic()` 返回 mock_category（Mock路径: `"app.crud.topic.get_category_with_topic"`）
- **Mock**: `crud_topic.batch_remove_rooms()` 返回删除数量（Mock路径: `"app.crud.topic.batch_remove_rooms"`）
- **验证**: 权限检查通过，remove被调用

### 5.4. 辅助查询方法测试

#### **Test 26: `test_get_topics_by_room_success`**
- **Mock**: db.execute 返回存在的LiveRoom
- **Mock**: `crud_topic.get_topics_by_room()` 返回专题列表（Mock路径: `"app.crud.topic.get_topics_by_room"`）
- **验证**: 返回专题列表

#### **Test 27: `test_get_topics_by_room_not_found`**
- **Mock**: db.execute 返回 None（直播间不存在）
- **验证**: 抛出 `RoomNotFoundException`

#### **Test 28: `test_batch_get_room_status_success`**
- **Mock**: db.execute 返回存在的LiveRoom列表
- **Mock**: db.execute 返回最新的LiveSession
- **Mock**: db.execute 返回SessionStatistics
- **验证**: 返回包含状态信息的列表

#### **Test 29: `test_batch_get_room_status_exceeds_limit`**
- **Arrange**: room_ids列表超过100个
- **验证**: 抛出 `ValueError`

#### **Test 30: `test_batch_get_room_status_some_not_found`**
- **Mock**: db.execute 返回部分LiveRoom（有缺失）
- **验证**: 抛出 `RoomNotFoundException`

## 6. 测试函数模板

### 6.1. 基础测试模板

```python
@pytest.mark.asyncio
async def test_method_name_scenario(mocker):
    """
    测试描述
    
    验证点:
    1. 验证点1
    2. 验证点2
    3. 验证点3
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.models.topic import Topic
    import uuid
    
    mock_db = mocker.Mock()
    
    # 创建Mock数据
    mock_topic = Topic(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test Topic",
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=TopicStatus.DRAFT
    )
    
    # Mock CRUD 函数（Service层调用 crud_topic.function_name()）
    # 测试中 Mock 原始模块路径 "app.crud.topic.function_name"
    mock_crud_function = mocker.patch(
        "app.crud.topic.function_name",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    # Act
    service = TopicService(mock_db)
    result = await service.method_name(parameters)
    
    # Assert
    mock_crud_function.assert_called_once_with(expected_parameters)
    assert result == expected_result
```

### 6.2. 异常测试模板

```python
@pytest.mark.asyncio
async def test_method_name_raises_exception(mocker):
    """
    测试在特定条件下抛出异常
    
    验证点:
    1. 正确抛出自定义异常
    2. CRUD 函数被正确调用
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.exceptions import TopicNotFoundException
    import uuid
    
    mock_db = mocker.Mock()
    topic_id = uuid.uuid4()
    
    # Mock CRUD 函数返回 None（触发异常）
    # Service层调用 crud_topic.get()，测试中 Mock "app.crud.topic.get"
    mocker.patch(
        "app.crud.topic.get",
        new_callable=AsyncMock,
        return_value=None
    )
    
    # Act & Assert
    service = TopicService(mock_db)
    with pytest.raises(TopicNotFoundException):
        await service.method_name(topic_id)
```

### 6.3. 权限检查测试模板

```python
@pytest.mark.asyncio
async def test_method_permission_denied(mocker):
    """
    测试权限不足场景
    
    验证点:
    1. 正确检测用户权限
    2. 抛出 TopicPermissionDeniedException
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.models.topic import Topic
    from app.exceptions import TopicPermissionDeniedException
    import uuid
    
    mock_db = mocker.Mock()
    owner_user_id = uuid.uuid4()
    different_user_id = uuid.uuid4()
    
    mock_topic = Topic(
        id=uuid.uuid4(),
        user_id=owner_user_id,  # 所有者ID
        title="Test Topic",
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=TopicStatus.DRAFT
    )
    
    # Mock CRUD 函数（Service层调用 crud_topic.get()）
    # 测试中 Mock 原始模块路径 "app.crud.topic.get"
    mocker.patch(
        "app.crud.topic.get",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    # Act & Assert
    service = TopicService(mock_db)
    with pytest.raises(TopicPermissionDeniedException):
        await service.method_name(
            topic_id=mock_topic.id,
            user_id=different_user_id,  # 不同的用户ID
            obj_in=update_data
        )
```

## 7. 辅助函数 (Helper Functions)

### 7.1. Mock对象创建辅助函数

```python
import uuid
from datetime import datetime
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus

def create_mock_topic(
    topic_id: uuid.UUID = None,
    user_id: uuid.UUID = None,
    status: TopicStatus = TopicStatus.DRAFT,
    title: str = "Test Topic"
) -> Topic:
    """创建Mock的Topic对象"""
    if topic_id is None:
        topic_id = uuid.uuid4()
    if user_id is None:
        user_id = uuid.uuid4()
    
    mock_topic = Topic(
        id=topic_id,
        user_id=user_id,
        title=title,
        description="Test Description",
        banner_url="https://example.com/banner.jpg",
        status=status
    )
    mock_topic.created_at = datetime.now()
    mock_topic.updated_at = datetime.now()
    
    return mock_topic


def create_mock_category(
    category_id: uuid.UUID = None,
    topic_id: uuid.UUID = None,
    name: str = "Test Category",
    sort_order: int = 0
) -> TopicCategory:
    """创建Mock的TopicCategory对象"""
    if category_id is None:
        category_id = uuid.uuid4()
    if topic_id is None:
        topic_id = uuid.uuid4()
    
    mock_category = TopicCategory(
        id=category_id,
        topic_id=topic_id,
        name=name,
        sort_order=sort_order
    )
    mock_category.created_at = datetime.now()
    mock_category.updated_at = datetime.now()
    
    return mock_category


def create_mock_category_with_topic(
    category_id: uuid.UUID = None,
    topic_user_id: uuid.UUID = None
) -> TopicCategory:
    """创建Mock的TopicCategory对象（包含topic属性，用于权限检查）"""
    if category_id is None:
        category_id = uuid.uuid4()
    if topic_user_id is None:
        topic_user_id = uuid.uuid4()
    
    mock_topic = create_mock_topic(user_id=topic_user_id)
    mock_category = create_mock_category(category_id=category_id, topic_id=mock_topic.id)
    
    # 设置关联关系
    mock_category.topic = mock_topic
    
    return mock_category
```

## 8. 代码质量要求

### 8.1. 导入语句规范

```python
"""
LiveCore Service - Topic Service Unit Tests

This module contains unit tests for the TopicService business logic layer,
using mocks to isolate dependencies.
"""

import uuid
import pytest
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# 项目内导入
from app.services.topic_service import TopicService
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from app.schemas.topic import (
    TopicCreate, TopicUpdate,
    CategoryCreate, CategoryUpdate,
    RoomAssociation
)
from app.exceptions import (
    TopicNotFoundException,
    CategoryNotFoundException,
    TopicPermissionDeniedException,
    RoomAlreadyAssociatedException,
    RoomNotFoundException
)
```

### 8.2. 测试组织结构

使用 pytest 的类来组织相关测试：

```python
class TestTopicManagement:
    """专题管理相关测试"""
    
    @pytest.mark.asyncio
    async def test_create_topic_success(self, mocker):
        """测试创建专题成功"""
        pass
    
    @pytest.mark.asyncio
    async def test_update_topic_success(self, mocker):
        """测试更新专题成功"""
        pass


class TestCategoryManagement:
    """分类管理相关测试"""
    
    @pytest.mark.asyncio
    async def test_create_category_success(self, mocker):
        """测试创建分类成功"""
        pass


class TestRoomAssociation:
    """直播间关联相关测试"""
    
    @pytest.mark.asyncio
    async def test_add_rooms_success(self, mocker):
        """测试添加直播间成功"""
        pass
```

### 8.3. Mock验证规范

```python
# ✅ 正确：使用 assert_called_once_with 验证参数
mock_create.assert_called_once_with(mock_db, topic_in, user_id)

# ✅ 正确：使用 assert_called 验证被调用
mock_update.assert_called()

# ✅ 正确：使用 assert_not_called 验证未被调用
mock_remove.assert_not_called()

# ✅ 正确：验证调用次数
assert mock_get.call_count == 2
```

## 9. 最终交付 (Final Deliverable)

Please generate the complete, runnable Python code for the following file, placed in clearly marked code blocks:

**`tests/unit/test_service_topic.py`**

**代码应包含**:
- 完整的模块文档字符串
- 所有必要的导入语句
- 3 个辅助函数（create_mock_topic, create_mock_category, create_mock_category_with_topic）
- 至少 30 个测试函数，覆盖 TopicService 的所有 16 个方法
- 每个方法至少包含：成功场景、资源不存在场景、权限不足场景（如适用）
- 使用 pytest 类组织相关测试
- 详细的函数文档字符串
- 适当的 Mock 验证

**代码格式要求**:
- 使用 4 个空格缩进
- 每个测试函数之间空 2 行
- 导入语句按标准库、第三方库、项目内导入分组
- 所有测试使用 `@pytest.mark.asyncio` 装饰器
- 确保所有测试可以独立运行

---

## 附录：快速检查清单

生成代码后，请确认以下内容：

### 测试覆盖率
- [ ] 16 个 Service 方法全部有对应测试
- [ ] 每个方法至少有 2-3 个测试用例（成功、失败、边界）
- [ ] 所有权限检查逻辑都有测试
- [ ] 所有自定义异常都有测试

### Mock 规范
- [ ] 所有 CRUD 函数都被正确 Mock
- [ ] 异步函数使用 AsyncMock
- [ ] 使用正确的 Mock 目标路径（`app.crud.topic.function_name`）
- [ ] Mock 验证使用 `assert_called_once_with` 等方法

### 代码规范
- [ ] 所有测试使用 `@pytest.mark.asyncio` 装饰器
- [ ] 测试函数不使用类型提示
- [ ] 所有测试包含详细的文档字符串
- [ ] 使用 pytest 类组织相关测试

### 业务逻辑验证
- [ ] 所有权限检查逻辑都被测试
- [ ] 所有资源存在性检查都被测试
- [ ] 所有数据验证逻辑都被测试
- [ ] 所有异常场景都被测试

---

**现在，请开始生成测试代码！**

