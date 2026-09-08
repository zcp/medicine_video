# 专题功能 API 端点测试代码生成提示词

## 1. 角色定义 (Role Definition)

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` for asynchronous code and FastAPI's `AsyncClient` for integration testing. Your task is to write a robust test suite for the **Topic Aggregation Feature API Endpoints** of the `LiveCore Service`.

## 2. 任务目标 (Task Objective)

Your goal is to generate the complete code for **one test file**:

**`tests/integration/test_api_topic.py`**: This file will contain **integration tests** for the API endpoints (`app/api/v1/endpoints/topic.py`), verifying the external API contract, critical business logic flows, and database state changes.

## 3. 核心上下文信息 (Core Context Information)

### 3.1. Testing Strategy

* **For `endpoints` layer:** Focus on testing the external API contract (request/response structure) and critical business logic flows (e.g., permission denied, resource not found, data validation).
* **Verify both API responses and database state changes** to ensure end-to-end correctness.
* Test error scenarios comprehensively (404, 403, 400, 500).

### 3.2. Testing Environment Setup

* Assume a `pytest` environment is set up with `pytest-asyncio`.
* Assume a testing database is configured via `tests/conftest.py`.
* **DO NOT MODIFY** the existing `conftest.py` file. It contains working fixtures used by other tests. You may only **ADD NEW** fixtures if absolutely necessary.
* Use the existing `db_session` and `async_client` fixtures from `conftest.py`.

### 3.3. Project Structure

```
backend/live_core_service/
├── app/
│   ├── api/v1/endpoints/
│   │   └── topic.py              # <-- To be tested (15 endpoints)
│   ├── crud/
│   │   └── topic.py              # <-- Existing (CRUD operations)
│   ├── services/
│   │   └── topic_service.py      # <-- Existing (Business logic)
│   ├── models/
│   │   ├── live_core.py          # <-- Existing (LiveRoom, LiveSession, SessionStatistics)
│   │   └── topic.py              # <-- Existing (Topic, TopicCategory, TopicCategoryRoom, TopicStatus)
│   ├── schemas/
│   │   └── topic.py              # <-- Existing (Pydantic schemas)
│   ├── core/
│   │   ├── deps.py               # <-- Existing (get_current_user dependency)
│   │   └── responses.py          # <-- Existing (success_response, error_response)
│   └── exceptions.py             # <-- Existing (Custom exceptions)
└── tests/
    ├── conftest.py               # <-- DO NOT MODIFY (可以增加但不要修改现有内容)
    └── integration/
        └── test_api_topic.py     # <-- To be generated
```

### 3.4. API Endpoints to Test (15 endpoints)

**⚠️ 重要说明：多路由器架构与路由配置规范**

`app/api/v1/endpoints/topic.py` 定义了**三个独立的 APIRouter 实例**：

1. **`router`** (主路由器): `APIRouter(tags=["Topics"])`
   - 负责专题的 CRUD 操作
   - **注意**：路由器定义时**不指定 prefix**，prefix 统一在 `api.py` 中指定
   - 端点示例: `POST /api/v1/topics`, `GET /api/v1/topics/{topic_id}`

2. **`category_router`** (分类路由器): `APIRouter(tags=["Topic Categories"])`
   - 负责分类的管理和直播间关联
   - 在 `api.py` 中注册时指定 `prefix="/topic-categories"`
   - 端点示例: `PATCH /api/v1/topic-categories/{category_id}`

3. **`room_router`** (直播间关系路由器): `APIRouter(tags=["Room-Topic Relations"])`
   - 负责直播间与专题的关系查询
   - 在 `api.py` 中注册时指定 `prefix="/rooms"`
   - 端点示例: `GET /api/v1/rooms/{room_id}/topics`

**✅ 路由配置关键点（避免404错误）：**

**在 `app/api/v1/endpoints/topic.py` 中：**
```python
# ❌ 错误：在定义时指定 prefix 会导致路径重复
# router = APIRouter(prefix="/topics", tags=["Topics"])

# ✅ 正确：prefix 留空，统一在 api.py 中指定
router = APIRouter(tags=["Topics"])
category_router = APIRouter(tags=["Topic Categories"])
room_router = APIRouter(tags=["Room-Topic Relations"])

# ❌ 错误：使用 "/" 会导致路径末尾有斜杠 (/topics/)
# @router.post("/")

# ✅ 正确：使用空字符串 ""
@router.post("")
async def create_topic(...):
    pass
```

**在 `app/api/v1/api.py` 中正确注册所有三个路由器：**
```python
from app.api.v1.endpoints import topic

# 必须显式指定每个路由器的 prefix 和 tags
api_router.include_router(
    topic.router,
    prefix="/topics",
    tags=["topics"]
)

api_router.include_router(
    topic.category_router,
    prefix="/topic-categories",
    tags=["topic-categories"]
)

api_router.include_router(
    topic.room_router,
    prefix="/rooms",
    tags=["room-topic-relations"]
)
```

**⚠️ 常见路由错误及解决方案：**

| 错误现象 | 根本原因 | 解决方案 |
|---------|---------|---------|
| 404 Not Found | 1. 路由器未在 `api.py` 中注册<br>2. prefix 重复定义导致路径错误<br>3. 路由装饰器使用 `"/"` 导致路径末尾有斜杠 | 1. 确保所有三个路由器都在 `api.py` 中注册<br>2. 路由器定义时不指定 prefix<br>3. 使用 `@router.post("")` 而非 `@router.post("/")` |
| 405 Method Not Allowed | 路由路径正确但HTTP方法未注册 | 检查路由装饰器方法（post/get/patch/delete） |

#### **专题管理 API (/topics) - 7 endpoints**

1. **POST /api/v1/topics**
   - 功能：创建专题
   - 认证：需要（get_current_user）
   - 请求体：TopicCreate
   - 成功响应：200，包含创建的专题信息
   - 错误响应：400（参数校验失败），500（数据库错误）

2. **GET /api/v1/topics**
   - 功能：获取专题列表（支持分页和筛选）
   - 认证：不需要
   - 查询参数：page, size, status, user_id
   - 成功响应：200，包含分页数据（total, page, size, items）
   - 错误响应：400（参数校验失败），500（数据库错误）

3. **GET /api/v1/topics/{topic_id}**
   - 功能：获取专题详情（层级化数据：专题→分类→直播间）
   - 认证：不需要
   - 路径参数：topic_id (UUID)
   - 成功响应：200，包含完整的专题详情（含分类和直播间）
   - 错误响应：404（专题不存在），500（数据库错误）

4. **PATCH /api/v1/topics/{topic_id}**
   - 功能：更新专题
   - 认证：需要（get_current_user）
   - 路径参数：topic_id (UUID)
   - 请求体：TopicUpdate
   - 成功响应：200，包含更新后的专题信息
   - 错误响应：404（专题不存在），403（权限不足），400（参数校验失败）

5. **DELETE /api/v1/topics/{topic_id}**
   - 功能：删除专题（级联删除分类和关联）
   - 认证：需要（get_current_user）
   - 路径参数：topic_id (UUID)
   - 成功响应：200，包含删除确认（id, status: "deleted"）
   - 错误响应：404（专题不存在），403（权限不足），500（数据库错误）

6. **POST /api/v1/topics/{topic_id}/categories**
   - 功能：创建分类
   - 认证：需要（get_current_user）
   - 路径参数：topic_id (UUID)
   - 请求体：CategoryCreate
   - 成功响应：200，包含创建的分类信息
   - 错误响应：404（专题不存在），403（权限不足），400（参数校验失败）

7. **GET /api/v1/topics/{topic_id}/categories**
   - 功能：获取分类列表（支持分页）
   - 认证：不需要
   - 路径参数：topic_id (UUID)
   - 查询参数：page, size
   - 成功响应：200，包含分页数据
   - 错误响应：404（专题不存在），500（数据库错误）

#### **分类管理 API (/topic-categories) - 6 endpoints**

8. **PATCH /api/v1/topic-categories/{category_id}**
   - 功能：更新分类
   - 认证：需要（get_current_user）
   - 路径参数：category_id (UUID)
   - 请求体：CategoryUpdate
   - 成功响应：200，包含更新后的分类信息
   - 错误响应：404（分类不存在），403（权限不足），400（参数校验失败）

9. **DELETE /api/v1/topic-categories/{category_id}**
   - 功能：删除分类（级联删除直播间关联）
   - 认证：需要（get_current_user）
   - 路径参数：category_id (UUID)
   - 成功响应：200，包含删除确认
   - 错误响应：404（分类不存在），403（权限不足），500（数据库错误）

10. **POST /api/v1/topic-categories/{category_id}/rooms**
    - 功能：批量添加直播间到分类
    - 认证：需要（get_current_user）
    - 路径参数：category_id (UUID)
    - 请求体：AddRoomsRequest (rooms: List[RoomAssociation])
    - 成功响应：200，包含添加数量（added_count）
    - 错误响应：404（分类不存在），403（权限不足），400（直播间不存在或已关联）

11. **GET /api/v1/topic-categories/{category_id}/rooms**
    - 功能：获取分类下的直播间列表（支持分页）
    - 认证：不需要
    - 路径参数：category_id (UUID)
    - 查询参数：page, size
    - 成功响应：200，包含分页数据（直播间信息+live_status）
    - 错误响应：404（分类不存在），500（数据库错误）

12. **PATCH /api/v1/topic-categories/{category_id}/rooms/sort-order**
    - 功能：批量更新直播间排序
    - 认证：需要（get_current_user）
    - 路径参数：category_id (UUID)
    - 请求体：UpdateRoomSortRequest (rooms: List[RoomAssociation])
    - 成功响应：200，包含更新数量（updated_count）
    - 错误响应：404（分类不存在），403（权限不足），500（数据库错误）

13. **DELETE /api/v1/topic-categories/{category_id}/rooms**
    - 功能：批量移除直播间
    - 认证：需要（get_current_user）
    - 路径参数：category_id (UUID)
    - 请求体：RemoveRoomsRequest (room_ids: List[UUID])
    - 成功响应：200，包含删除数量（deleted_count）
    - 错误响应：404（分类不存在），403（权限不足），500（数据库错误）

#### **直播间与专题关系 API (/rooms) - 2 endpoints**

14. **GET /api/v1/rooms/{room_id}/topics**
    - 功能：获取直播间关联的所有已发布专题
    - 认证：不需要
    - 路径参数：room_id (UUID)
    - 成功响应：200，包含专题列表（只返回status=published的专题）
    - 错误响应：404（直播间不存在），500（数据库错误）

15. **POST /api/v1/rooms/batch-status**
    - 功能：批量获取直播间状态
    - 认证：不需要
    - 请求体：BatchStatusRequest (room_ids: List[UUID], 最多100个)
    - 成功响应：200，包含状态列表（room_id, live_status, current_session_id, viewer_count）
    - 错误响应：400（参数校验失败：超过100个或直播间不存在），500（数据库错误）

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

* **`status`**:
  - **规则**: TopicStatus 枚举类型
  - **有效值**: `"draft"`, `"published"`, `"archived"`

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
  - **规则**: UUID 类型，必填字段
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

**⚠️ 重要：所有专题功能的测试必须使用 `topic_client` fixture**

```python
# ✅ 正确模板：使用 topic_client（含认证）
@pytest.mark.asyncio
async def test_api_endpoint_with_auth(topic_client):
    """测试描述：详细说明测试目的和验证点"""
    async for client, app, db in topic_client:  # ✅ 解包得到三个对象
        from app.core.deps import get_current_user
        
        # Mock 认证
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "mock_user_id",
            "username": "testuser"
        }
        
        try:
            # 1. Arrange: 准备测试数据和请求
            # 2. Act: 执行 API 请求
            # 3. Assert: 验证响应和数据库状态
            pass
        finally:
            # ✅ 清理依赖覆盖
            app.dependency_overrides.clear()

# ✅ 不需要认证的测试（如GET列表）
@pytest.mark.asyncio
async def test_api_endpoint_no_auth(topic_client):
    """测试描述：详细说明测试目的和验证点"""
    async for client, app, db in topic_client:
        # 1. Arrange: 准备测试数据
        # 2. Act: 执行 API 请求
        # 3. Assert: 验证响应和数据库状态
        pass
```

### 5.2. ⚠️ 禁止的写法

- ❌ **禁止使用 `async_client` 和 `db_session` fixtures**（会导致认证失败）
  ```python
  # ❌ 错误示例
  async def test_wrong(async_client, db_session):
      async for client in async_client:
          async for db in db_session:
              ...
  ```

- ❌ **禁止从 `app.main` 导入 app**（会导致认证失败）
  ```python
  # ❌ 错误示例
  from app.main import app
  app.dependency_overrides[get_current_user] = ...
  ```

- ❌ **禁止忘记清理 `dependency_overrides`**（会影响其他测试）
  ```python
  # ❌ 错误示例：没有 finally 清理
  async for client, app, db in topic_client:
      app.dependency_overrides[get_current_user] = ...
      response = await client.post(...)
      # ❌ 缺少清理！
  ```

- ❌ 不得在 `async for` 外部调用数据库操作
- ❌ 不得直接使用 fixture 参数而不解包
- ❌ 不得在函数参数中添加类型提示（会导致混淆）

### 5.3. 测试模式 (AAA Pattern)

**所有测试必须遵循 Arrange-Act-Assert 模式：**

#### **1. 准备 (Arrange)**

在 Arrange 阶段，准备测试数据和必要的数据库记录：

```python
async for client, app, db in topic_client:  # ✅ 使用 topic_client
    from app.core.deps import get_current_user
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCreate
    from app.models.topic import TopicStatus
    from faker import Faker
    import uuid
    
    # Step 1: Mock 认证
    fake = Faker()
    user_id = uuid.uuid4()
    
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": str(user_id),
        "username": "testuser"
    }
    
    try:
        # Step 2: 创建依赖数据
        topic_in = TopicCreate(
            title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
            description=fake.text(max_nb_chars=100),
            banner_url=fake.image_url(),
            status="draft"
        )
        topic = await crud_topic.create(db, topic_in, user_id)
        
        # Step 3: 准备请求数据
        payload = {
            "name": f"{fake.word()}_{uuid.uuid4().hex[:4]}",
            "sort_order": 10
        }
```

#### **2. 执行 (Act)**

调用API接口：

```python
        # 执行API请求
        response = await client.post(
            f"/api/v1/topics/{topic.id}/categories",
            json=payload
        )
```

#### **3. 断言 (Assert)**

**必须验证多个维度：**

```python
        # 断言 1: 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际 {response.status_code}"
        
        # 断言 2: 验证响应JSON结构
        data = response.json()
        assert "code" in data, "响应缺少 code 字段"
        assert "message" in data, "响应缺少 message 字段"
        assert "data" in data, "响应缺少 data 字段"
        assert "timestamp" in data, "响应缺少 timestamp 字段"
        
        # 断言 3: 验证业务码
        assert data["code"] == 200, f"期望业务码200，实际 {data['code']}"
        assert data["message"] == "success"
        
        # 断言 4: 验证响应数据
        category_data = data["data"]
        assert category_data["name"] == payload["name"]
        assert category_data["sort_order"] == payload["sort_order"]
        assert "id" in category_data
        
        # 断言 5: 验证数据库状态
        from sqlalchemy import select
        from app.models.topic import TopicCategory
        
        stmt = select(TopicCategory).where(TopicCategory.name == payload["name"])
        result = await db.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        assert db_category is not None, "数据库中未找到创建的分类"
        assert db_category.topic_id == topic.id
        assert db_category.sort_order == payload["sort_order"]
    
    finally:
        # ✅ 清理依赖覆盖
        app.dependency_overrides.clear()
```

## 6. 认证和依赖注入Mock（⚠️ 关键 - 避免401错误）

### 6.1. ⚠️ 为什么会出现 401 Unauthorized 错误

**常见错误示例1（❌ 禁止使用 `app.main.app`）：**

```python
from app.main import app  # ❌ 错误！
from app.core.deps import get_current_user

async def test_example(async_client, db_session):
    async for client in async_client:
        # ❌ 这样设置不会生效！
        app.dependency_overrides[get_current_user] = lambda: {"user_id": "123"}
        # 测试会收到 401 Unauthorized 错误
```

**常见错误示例2（❌ 禁止使用 `async_client` 和 `db_session`）：**

```python
async def test_example(async_client, db_session):
    async for client in async_client:
        async for db in db_session:
            # ❌ 无法访问 app 实例，无法设置 dependency_overrides
            # 测试会收到 401 Unauthorized 错误
```

**错误根本原因：**

1. `conftest.py` 中的 `async_client` fixture 创建了一个**新的 FastAPI 应用实例**
2. 这个测试用的 app 实例与 `app.main.app` 是**两个不同的对象**
3. 修改 `app.main.app.dependency_overrides` 不会影响测试中实际使用的 app 实例
4. `async_client` fixture 只返回 client，不返回 app，测试代码无法访问 app 来设置 `dependency_overrides`

**结果：**
- 所有需要认证的端点（使用 `Depends(get_current_user)`）都会返回 **401 Unauthorized**
- 测试无法通过认证检查

### 6.2. ✅ 正确方案：创建本地 `topic_client` Fixture

**为什么需要本地 fixture？**

1. **暴露 app 实例**：`topic_client` 返回 `(client, app, db)` 元组，让测试代码能访问 app
2. **正确的 app 对象**：确保 `dependency_overrides` 设置在测试实际使用的 app 上
3. **隔离性**：不影响其他测试文件（不能修改 `conftest.py`，因为其他测试依赖它）

**在 `test_api_topic.py` 文件顶部添加本地 fixture：**

```python
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def topic_client(db_session) -> AsyncGenerator[tuple, None]:
    """
    专门为 topic 测试创建的 fixture，返回 (client, app, db) 元组
    这样可以在测试中访问 app 实例来设置 dependency_overrides
    """
    from app.api.v1.api import api_router
    from app.database import get_db
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine
    import os
    
    # 创建测试专用的 FastAPI 应用
    app = FastAPI(
        title="LiveCore Service Test - Topic",
        version="1.0.0",
        redirect_slashes=False
    )
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 设置数据库 - 使用与 conftest 相同的配置
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "live_core_test")
    TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 覆盖数据库依赖
    async def override_get_db():
        async with async_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建客户端
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        # 获取数据库会话
        async for db in db_session:
            yield (client, app, db)
            break
    
    # 清理
    await engine.dispose()
```

### 6.3. ✅ 在测试中使用本地 Fixture

**所有需要认证的测试必须使用 `topic_client` fixture：**

```python
@pytest.mark.asyncio
async def test_create_topic_success(topic_client):  # ✅ 使用 topic_client
    """测试成功创建专题"""
    async for client, app, db in topic_client:  # ✅ 解包得到 client, app, db
        from app.core.deps import get_current_user
        import uuid
        
        # ✅ 使用从 fixture 返回的 app 实例
        mock_user_id = str(uuid.uuid4())
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": mock_user_id,
            "username": "testuser"
        }
        
        try:
            # 执行测试
            response = await client.post(
                "/api/v1/topics",
                json=payload
            )
            # 断言...
        finally:
            # ✅ 清理依赖覆盖
            app.dependency_overrides.clear()
```

### 6.4. 测试用户权限场景

```python
@pytest.mark.asyncio
async def test_update_topic_permission_denied(topic_client):
    """测试无权限更新专题"""
    async for client, app, db in topic_client:
        from app.core.deps import get_current_user
        import uuid
        
        # 创建专题（所有者：user_A）
        user_a_id = uuid.uuid4()
        topic = await create_test_topic(db, user_a_id)
        
        # 尝试用user_B修改（应该失败）
        user_b_id = uuid.uuid4()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": str(user_b_id),
            "username": "userB"
        }
        
        try:
            response = await client.patch(
                f"/api/v1/topics/{topic.id}",
                json={"title": "New Title"}
            )
            
            # 断言返回403
            assert response.status_code == 403
            data = response.json()
            assert data["code"] == 2003  # 权限不足的业务码
        finally:
            app.dependency_overrides.clear()
```

## 7. API 端点测试用例规格

### 7.1. 专题管理API测试 (7 tests)

#### **Test 1: `test_create_topic_success`**

```python
@pytest.mark.asyncio
async def test_create_topic_success(topic_client):  # ✅ 使用 topic_client
    """
    测试成功创建专题
    
    验证点:
    1. HTTP状态码为200
    2. 响应包含正确的JSON结构（code, message, data, timestamp）
    3. 业务码为200
    4. 返回的专题数据包含所有必要字段
    5. 数据库中成功插入记录
    6. 默认状态为draft
    """
    async for client, app, db in topic_client:  # ✅ 解包三个对象
        # Arrange
        from faker import Faker
        import uuid
        from app.core.deps import get_current_user
        
        fake = Faker()
        mock_user_id = str(uuid.uuid4())
        
        # Mock认证
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": mock_user_id,
            "username": "testuser"
        }
        
        payload = {
            "title": f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
            "description": fake.text(max_nb_chars=100),
            "banner_url": fake.image_url(),
            "status": "draft"
        }
        
        try:
            # Act
            response = await client.post(
                "/api/v1/topics",
                json=payload
            )
            
            # Assert - API Response
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "success"
            assert "data" in data
            assert data["data"]["title"] == payload["title"]
            assert data["data"]["status"] == "draft"
            assert "id" in data["data"]
            
            # Assert - Database State
            from sqlalchemy import select
            from app.models.topic import Topic
            
            stmt = select(Topic).where(Topic.title == payload["title"])
            result = await db.execute(stmt)
            db_topic = result.scalar_one_or_none()
            
            assert db_topic is not None
            assert db_topic.title == payload["title"]
            assert db_topic.user_id == uuid.UUID(mock_user_id)
            assert db_topic.status.value == "draft"
            
        finally:
            # ✅ 清理依赖覆盖
            app.dependency_overrides.clear()
```

#### **Test 2: `test_get_topic_list_with_pagination`**
- 创建5个专题
- 请求第1页，每页2条
- 验证返回正确的分页数据

#### **Test 3: `test_get_topic_list_with_filters`**
- 创建多个专题（不同status和user_id）
- 使用status筛选
- 验证只返回匹配的专题

#### **Test 4: `test_get_topic_detail_success`**
- 创建专题、分类、直播间
- 获取专题详情
- 验证返回层级化数据结构

#### **Test 5: `test_get_topic_detail_not_found`**
- 使用不存在的topic_id
- 验证返回404和正确的错误码

#### **Test 6: `test_update_topic_success`**
- 创建专题
- 使用所有者更新
- 验证更新成功且数据库持久化

#### **Test 7: `test_update_topic_permission_denied`**
- 创建专题（user_A）
- 使用不同用户（user_B）尝试更新
- 验证返回403

#### **Test 8: `test_delete_topic_success`**
- 创建专题和分类
- 删除专题
- 验证专题和分类都被删除（级联）

#### **Test 9: `test_delete_topic_permission_denied`**
- 创建专题（user_A）
- 使用不同用户（user_B）尝试删除
- 验证返回403

#### **Test 10: `test_create_category_success`**
- 创建专题
- 创建分类
- 验证分类创建成功

#### **Test 11: `test_create_category_topic_not_found`**
- 使用不存在的topic_id创建分类
- 验证返回404

#### **Test 12: `test_get_category_list_with_pagination`**
- 创建专题和5个分类
- 请求分页数据
- 验证按sort_order排序

### 7.2. 分类管理API测试 (6 tests)

#### **Test 13: `test_update_category_success`**
#### **Test 14: `test_update_category_permission_denied`**
#### **Test 15: `test_delete_category_success`**
#### **Test 16: `test_add_rooms_to_category_success`**
#### **Test 17: `test_add_rooms_already_associated`**
#### **Test 18: `test_add_rooms_not_found`**
#### **Test 19: `test_get_rooms_in_category_success`**
#### **Test 20: `test_update_room_sort_order_success`**
#### **Test 21: `test_remove_rooms_from_category_success`**

### 7.3. 直播间与专题关系API测试 (2 tests)

#### **Test 22: `test_get_topics_by_room_success`**
- 创建3个专题（2个published，1个draft）
- 将直播间关联到所有专题
- 验证只返回2个published专题

#### **Test 23: `test_batch_get_room_status_success`**
- 创建3个直播间
- 批量查询状态
- 验证返回正确的状态信息

#### **Test 24: `test_batch_get_room_status_exceeds_limit`**
- 请求超过100个直播间
- 验证返回400错误

## 8. 辅助函数 (Helper Functions)

### 8.1. 创建测试专题

```python
async def create_test_topic(
    db: AsyncSession,
    user_id: uuid.UUID = None,
    status: str = "draft"
) -> Topic:
    """创建测试专题的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import TopicCreate
    from faker import Faker
    
    if user_id is None:
        user_id = uuid.uuid4()
    
    fake = Faker()
    topic_in = TopicCreate(
        title=f"{fake.catch_phrase()}_{uuid.uuid4().hex[:6]}",
        description=fake.text(max_nb_chars=100),
        banner_url=fake.image_url(),
        status=status
    )
    
    return await crud_topic.create(db, topic_in, user_id)
```

### 8.2. 创建测试分类

```python
async def create_test_category(
    db: AsyncSession,
    topic_id: uuid.UUID,
    sort_order: int = 0
) -> TopicCategory:
    """创建测试分类的辅助函数"""
    from app.crud import topic as crud_topic
    from app.schemas.topic import CategoryCreate
    from faker import Faker
    
    fake = Faker()
    category_in = CategoryCreate(
        name=f"{fake.word()}_{uuid.uuid4().hex[:4]}",
        sort_order=sort_order
    )
    
    return await crud_topic.create_category(db, category_in, topic_id)
```

### 8.3. 创建测试直播间

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

### 8.4. Mock认证辅助函数

```python
def create_mock_current_user(user_id: str = None):
    """创建Mock的当前用户（用于依赖注入覆盖）"""
    import uuid
    
    def mock_user():
        return {
            "user_id": user_id or str(uuid.uuid4()),
            "username": "testuser"
        }
    return mock_user
```

## 9. 代码质量要求

### 9.1. 导入语句规范

```python
"""
LiveCore Service - Topic API Integration Tests

This module contains integration tests for all API endpoints
in the topic aggregation feature.
"""

import uuid
import pytest
import json  # ✅ 用于 DELETE 请求的 body 序列化
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from httpx import AsyncClient  # ✅ 用于创建本地 fixture
from fastapi import FastAPI  # ✅ 用于创建本地 fixture

# 项目内导入
# ⚠️ 不要导入 app.main.app！
from app.core.deps import get_current_user
from app.crud import topic as crud_topic
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession
from app.schemas.topic import (
    TopicCreate, TopicUpdate,
    CategoryCreate, CategoryUpdate,
    RoomAssociation
)

# 初始化 Faker
fake = Faker()
```

### 9.2. 测试组织结构

使用 pytest 的类来组织相关测试：

```python
class TestTopicManagementAPI:
    """专题管理API测试"""
    
    @pytest.mark.asyncio
    async def test_create_topic_success(self, topic_client):  # ✅ 使用 topic_client
        """测试创建专题成功"""
        async for client, app, db in topic_client:
            # 测试逻辑...
            pass


class TestCategoryManagementAPI:
    """分类管理API测试"""
    
    @pytest.mark.asyncio
    async def test_update_category_success(self, topic_client):  # ✅ 使用 topic_client
        """测试更新分类成功"""
        async for client, app, db in topic_client:
            # 测试逻辑...
            pass


class TestRoomTopicRelationAPI:
    """直播间与专题关系API测试"""
    
    @pytest.mark.asyncio
    async def test_get_topics_by_room(self, topic_client):  # ✅ 使用 topic_client
        """测试获取直播间关联专题"""
        async for client, app, db in topic_client:
            # 测试逻辑...
            pass
```

### 9.3. 文档字符串规范

每个测试函数必须包含详细的文档字符串：

```python
@pytest.mark.asyncio
async def test_create_topic_success(self, topic_client):  # ✅ 使用 topic_client
    """
    测试成功创建专题
    
    验证点:
    1. HTTP状态码为200
    2. 响应包含正确的JSON结构（code, message, data, timestamp）
    3. 业务码为200
    4. 返回的专题数据包含所有必要字段
    5. 数据库中成功插入记录
    6. 默认状态为draft
    """
    async for client, app, db in topic_client:
        # 测试逻辑 ...
        pass
```

### 9.4. 断言消息规范

所有断言必须包含清晰的错误消息：

```python
assert response.status_code == 200, \
    f"期望HTTP状态码200，实际 {response.status_code}"
assert data["code"] == 200, \
    f"期望业务码200，实际 {data['code']}"
assert "data" in data, \
    "响应JSON中缺少 data 字段"
```

### 9.5. 清理依赖覆盖

确保在每个测试后清理依赖覆盖：

```python
async for client, app, db in topic_client:  # ✅ 使用 topic_client
    # 设置Mock
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "mock_id",
        "username": "testuser"
    }
    
    try:
        # 执行测试
        response = await client.post(...)
        # 断言
        assert ...
    finally:
        # ✅ 清理依赖覆盖
        app.dependency_overrides.clear()
```

## 10. 错误场景测试（重要）

### 10.1. 资源不存在 (404)

```python
@pytest.mark.asyncio
async def test_get_topic_not_found(topic_client):  # ✅ 使用 topic_client
    """测试获取不存在的专题"""
    async for client, app, db in topic_client:
        # 使用随机UUID
        random_id = uuid.uuid4()
        
        response = await client.get(f"/api/v1/topics/{random_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 2001  # 资源不存在的业务码
        assert "data" in data
        assert data["data"]["resource"] == "Topic"
```

### 10.2. 权限不足 (403)

```python
@pytest.mark.asyncio
async def test_update_topic_permission_denied(topic_client):  # ✅ 使用 topic_client
    """测试无权限更新专题"""
    async for client, app, db in topic_client:
        from app.core.deps import get_current_user
        
        # 创建专题（所有者：user_A）
        user_a_id = uuid.uuid4()
        topic = await create_test_topic(db, user_a_id)
        
        # 使用不同用户（user_B）尝试更新
        user_b_id = uuid.uuid4()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": str(user_b_id),
            "username": "userB"
        }
        
        try:
            response = await client.patch(
                f"/api/v1/topics/{topic.id}",
                json={"title": "New Title"}
            )
            
            assert response.status_code == 403
            data = response.json()
            assert data["code"] == 2003  # 权限不足的业务码
        finally:
            app.dependency_overrides.clear()
```

### 10.3. 参数校验失败 (400)

```python
@pytest.mark.asyncio
async def test_create_topic_invalid_data(topic_client):  # ✅ 使用 topic_client
    """测试使用无效数据创建专题"""
    async for client, app, db in topic_client:
        from app.core.deps import get_current_user
        
        # Mock认证
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": str(uuid.uuid4()),
            "username": "testuser"
        }
        
        try:
            # 缺少必填字段title
            payload = {
                "description": "Test",
                "status": "draft"
            }
            
            response = await client.post("/api/v1/topics", json=payload)
            
            assert response.status_code == 422  # FastAPI的验证错误
        finally:
            app.dependency_overrides.clear()
```

## 11. 最终交付 (Final Deliverable)

Please generate the complete, runnable Python code for the following file, placed in clearly marked code blocks:

**`tests/integration/test_api_topic.py`**

**代码应包含**:
- 完整的模块文档字符串
- 所有必要的导入语句（包括 `json`, `AsyncClient`, `FastAPI`, `AsyncGenerator`）
- **✅ 1 个本地 fixture: `topic_client`** (返回 `(client, app, db)` 元组)
- 3 个辅助函数（create_test_topic, create_test_category, create_test_room）
- ⚠️ **不需要** `create_mock_current_user` 辅助函数（直接使用 lambda）
- 至少 24 个测试函数，覆盖所有 15 个API端点
- 每个端点至少包含：成功场景 + 1-2个错误场景
- 使用 pytest 类组织相关测试
- **✅ 所有测试函数都使用 `topic_client` fixture**（不使用 `async_client` 和 `db_session`）
- 每个测试函数都严格遵循 `async for client, app, db in topic_client:` 模式
- 详细的函数文档字符串
- 适当的断言消息
- 所有测试数据使用 faker 生成，确保唯一性
- **✅ 正确处理认证Mock和清理**（使用 try-finally 块）

**代码格式要求**:
- 使用 4 个空格缩进
- 每个测试函数之间空 2 行
- 导入语句按标准库、第三方库、项目内导入分组
- 确保所有测试可以独立运行且不依赖执行顺序
- 每个测试后清理依赖覆盖

---

## 12. ⚠️ 关键错误总结与避免指南

在生成测试代码时，务必避免以下两类常见错误：

### 12.1. 路由配置错误（导致404 Not Found）

**错误表现：**
- 测试发送请求后收到 `404 Not Found` 错误
- 即使端点代码正确，路由也无法匹配

**根本原因与解决方案：**

| 问题 | 错误写法 | 正确写法 | 说明 |
|------|---------|---------|------|
| **1. 路由器未注册** | `api.py` 中只注册了 `topic.router`，忘记 `category_router` 和 `room_router` | 在 `api.py` 中注册全部三个路由器 | 多路由器架构必须全部注册 |
| **2. prefix 重复定义** | `router = APIRouter(prefix="/topics")`<br>+<br>`api_router.include_router(router, prefix="/topics")` | 路由器定义时不指定 prefix，统一在 `api.py` 的 `include_router` 中指定 | 避免路径叠加成 `/api/v1/topics/topics` |
| **3. 路由路径末尾斜杠** | `@router.post("/")`<br>导致路径为 `/api/v1/topics/` | `@router.post("")`<br>路径为 `/api/v1/topics` | 使用空字符串避免末尾斜杠 |

**正确的路由配置模式：**

```python
# endpoints/topic.py
router = APIRouter(tags=["Topics"])  # 不指定 prefix
category_router = APIRouter(tags=["Topic Categories"])
room_router = APIRouter(tags=["Room-Topic Relations"])

@router.post("")  # 使用空字符串，不是 "/"
async def create_topic(...):
    pass

# api.py
api_router.include_router(topic.router, prefix="/topics", tags=["topics"])
api_router.include_router(topic.category_router, prefix="/topic-categories", tags=["topic-categories"])
api_router.include_router(topic.room_router, prefix="/rooms", tags=["room-topic-relations"])
```

### 12.2. JWT认证失败（导致401 Unauthorized）

**错误表现：**
- 所有需要认证的测试都返回 `401 Unauthorized`
- 即使设置了 `dependency_overrides`，认证仍然失败

**根本原因：**
- `conftest.py` 的 `async_client` fixture 创建了新的 FastAPI app 实例
- 测试中对 `app.main.app` 或无法访问的 app 实例设置 `dependency_overrides` 不生效

**错误写法（❌）：**

```python
# 错误1：使用 app.main.app
from app.main import app
async def test_xxx(async_client, db_session):
    app.dependency_overrides[get_current_user] = ...  # 不会生效

# 错误2：无法访问 app
async def test_xxx(async_client, db_session):
    async for client in async_client:
        # 无法访问 app 实例来设置 dependency_overrides
```

**正确写法（✅）：**

```python
# 创建本地 fixture
@pytest.fixture
async def topic_client(db_session) -> AsyncGenerator[tuple, None]:
    from app.api.v1.api import api_router
    app = FastAPI(...)  # 创建测试专用 app
    app.include_router(api_router, prefix="/api/v1")
    # ... 数据库配置 ...
    async with AsyncClient(app=app, base_url="...") as client:
        async for db in db_session:
            yield (client, app, db)  # 返回三元组
            break

# 在测试中使用
async def test_xxx(topic_client):
    async for client, app, db in topic_client:  # 解包得到 app
        app.dependency_overrides[get_current_user] = lambda: {"user_id": "..."}
        try:
            # 执行测试
            pass
        finally:
            app.dependency_overrides.clear()  # 必须清理
```

**关键点：**
1. **创建本地 fixture** 返回 `(client, app, db)` 元组
2. **在测试中解包** `async for client, app, db in topic_client:`
3. **使用解包的 app** 设置 `dependency_overrides`
4. **使用 try-finally** 确保清理 `dependency_overrides`

---

## 附录：快速检查清单

生成代码后，请确认以下内容：

### API测试覆盖率
- [ ] 15 个 API 端点全部有对应测试
- [ ] 每个端点至少有 2-3 个测试用例（成功、失败、边界）
- [ ] 所有需要认证的端点都使用了Mock认证
- [ ] 所有错误场景都有测试（404, 403, 400）

### 代码规范
- [ ] 所有测试使用 `@pytest.mark.asyncio` 装饰器
- [ ] **✅ 所有测试使用 `topic_client` fixture**（不使用 `async_client` 和 `db_session`）
- [ ] **✅ 所有测试使用 `async for client, app, db in topic_client:` 模式**
- [ ] **✅ 不从 `app.main` 导入 app**
- [ ] 所有唯一性字段使用 faker 或 uuid 生成随机值
- [ ] 所有测试包含详细的文档字符串
- [ ] 所有断言包含清晰的错误消息
- [ ] **✅ 所有测试后使用 try-finally 清理 `app.dependency_overrides`**

### API测试验证
- [ ] 所有API测试验证HTTP状态码
- [ ] 所有API测试验证响应JSON结构（code, message, data, timestamp）
- [ ] 所有API测试验证业务错误码
- [ ] 所有API测试同时验证数据库状态变化

### 权限测试
- [ ] 所有需要认证的端点都测试了权限场景
- [ ] 测试了所有者可以操作，非所有者不能操作的场景
- [ ] 权限不足场景验证返回403和正确的业务码

### 数据验证
- [ ] 所有创建操作都验证数据库中记录存在
- [ ] 所有更新操作都重新查询数据库验证持久化
- [ ] 所有删除操作都验证记录已被删除
- [ ] 所有级联删除操作都验证子记录也被删除

---

**现在，请开始生成测试代码！**

