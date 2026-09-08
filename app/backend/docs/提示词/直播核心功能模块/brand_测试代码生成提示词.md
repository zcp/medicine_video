# 品牌模块 - 测试代码生成提示词

**模块名称**: brand  
**功能模块名称**: 品牌模块设计文档-品牌管理-品牌专题关联-品牌直播间关联  
**测试模式**: **增量测试生成模式**  
**生成日期**: 2026-01-18  

---

## ⚠️ 增量测试模式说明

**当前状态**：
- ✅ 项目已存在测试基础设施（`tests/conftest.py`）
- ❌ 品牌模块暂无测试文件（`test_*brand*.py`）
- ✅ 使用增量测试生成模式，复用现有Fixture和测试基础设施

**已存在的测试文件**（**严禁修改**）：
- `tests/conftest.py` - 测试配置和Fixture定义
- `tests/unit/test_*.py` - 其他模块的单元测试
- `tests/integration/test_api_*.py` - 其他模块的集成测试

**需要新增的测试文件**：
- `tests/unit/test_crud_brand.py` - 品牌模块CRUD层测试（**新增**）
- `tests/unit/test_service_brand.py` - 品牌模块Service层测试（**新增**）
- `tests/integration/test_api_brand.py` - 品牌模块API层测试（**新增**）

**关键约束**：
- ❌ **严禁修改**已存在的测试文件
- ✅ **允许修改** `conftest.py`（仅限添加新内容，必须检查命名冲突）
- ✅ **必须使用增量判断方式**验证数据库操作（记录基线，验证增量）
- ✅ **必须复用现有Fixture**（如 `db_session`, `async_client`, `regular_user_id`, `admin_user_id`, `admin_user_token` 等）

---

## 1. 角色定义与测试模式 (Role Definition & Test Mode)

你是一名资深的 Python 测试架构师。你精通使用 `pytest`、`pytest-asyncio`、`httpx` 和 `pytest-mock`，并且是"混合测试策略"的专家。

**⚠️ 测试模式说明**：
- **测试模式**：**增量测试生成模式**
- **说明**：为品牌模块**新增**测试代码，在已有测试基础上增量生成。**严禁修改**已存在的测试文件。

你的任务是**主动读取** `Section 6` 中列出的所有依赖文件的完整内容（包括模型、Schema、CRUD、Service、API文件等），以及已存在的测试文件（增量模式），并**严格按照** `Section 2-5` 的"核心规则"和 `Section 7` 的"具体任务列表"，为它们生成一个**完整、健壮、可运行的 `pytest` 测试文件**。

**🚨 [最高优先级] 生成测试代码前的强制要求**：

在生成任何测试代码之前，**必须**完成以下步骤（按顺序执行，不可跳过）：

1. **第一步：读取 Model 定义（MANDATORY）**
   - **必须**使用 `read_file()` 工具读取 `Section 6` 中列出的所有 Model 文件（如 `app/models/brand.py`）
   - **必须**提取所有模型类的完整字段定义（字段名、类型、约束、默认值、注释）
   - **必须**识别所有必需字段（`nullable=False`）和可选字段（`nullable=True`）
   - **必须**识别所有唯一约束（`unique=True`）和外键关系
   - **严禁**在未读取 Model 定义的情况下生成测试代码
   - **严禁**猜测字段名、类型或约束

2. **第二步：读取 Schema 定义（MANDATORY）**
   - **必须**使用 `read_file()` 工具读取 `Section 6` 中列出的所有 Schema 文件（如 `app/schemas/brand.py`）
   - **必须**提取所有 Pydantic 模型的字段定义和验证规则

3. **第三步：读取 CRUD/Service/API 代码（MANDATORY）**
   - **必须**使用 `read_file()` 工具读取 `Section 6` 中列出的所有 CRUD、Service、API 文件
   - **必须**提取所有函数的签名（参数名、类型、返回值）

4. **第四步：读取 conftest.py（增量模式MANDATORY）**
   - **必须**使用 `read_file()` 工具读取 `tests/conftest.py` 的完整内容
   - **必须**识别所有已定义的Fixture（如 `db_session`, `async_client`, `regular_user_id`, `admin_user_id`, `admin_user_token` 等）
   - **必须**了解现有Fixture的代码风格和命名约定

5. **第五步：生成测试代码**
   - 只有在完成上述所有读取步骤后，才能开始生成测试代码
   - **必须**基于实际读取的代码生成测试，**严禁**猜测任何字段、函数或参数

**⚠️ 违反此要求的后果**：
- 如果生成的测试代码使用了 Model 中不存在的字段（如 `Brand.description` 误写为 `Brand.desc`），测试将失败
- 如果生成的测试代码缺少必需字段（如 `Brand.name`），测试将失败
- 如果生成的测试代码使用了错误的函数签名，测试将失败

**⚠️ 增量测试模式的特殊要求**：
- **严禁修改**已存在的测试函数（即使是修复错误也不行，除非用户明确要求）。
- **允许修改 `conftest.py`**（仅限添加新内容）：
  - ✅ **只增加**新的Fixture、函数、变量、导入等。
  - ❌ **严禁修改**已有的Fixture、函数、变量等。
  - ❌ **严禁删除**任何现有内容。
  - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
- **必须使用增量判断方式**验证数据库操作（记录测试前状态，只验证增量变化）。

---

## 2. 核心测试哲学 (The Hybrid Testing Strategy - MANDATORY)

你**必须**根据被测试代码的层级，严格遵循以下混合测试策略。这是最高优先级指令。

| 测试目标层级 | 强制测试风格 | 核心工具 | 测试目标 (你必须验证什么？) |
| :--- | :--- | :--- | :--- |
| **API / Endpoint 层** | **实用派 (Pragmatic)** | `httpx.AsyncClient` + `db_session` + `async_session_factory` | **验证完整链路**：HTTP 请求 → JSON 响应 → 数据库状态变化（**注意**：必须使用**新会话**查询以避免缓存陷阱）。 |
| **Service (服务) 层** | **学院派 (Academic)** | `mocker` (Mock 掉 CRUD/I/O) | **验证业务逻辑**：*隔离地*测试权限检查、数据编排、以及自定义异常（`pytest.raises`）的抛出。 |
| **CRUD (数据) 层** | **实用派 (Pragmatic)** | `db_session` (真实数据库) | **验证数据库状态**：*必须*通过 `db.refresh()` 或**再次查询**来"证明"数据已被正确创建、更新或删除。 |

---

## 3. 核心实现规范 (Core Implementation Requirements - MANDATORY)

### 3.1. 测试环境配置 (`conftest.py`)

**⚠️ 增量测试模式特殊约束**：
- **允许修改 `conftest.py`**（仅限添加新内容）：可以添加新的Fixture、函数或变量，但**必须严格遵守以下规则**：
  - ✅ **只增加新的内容**：只能添加新的Fixture、函数、变量、导入等。
  - ❌ **严禁修改已有的内容**：不能修改、删除或重命名现有的Fixture、函数、变量等。
  - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
  - ✅ **保持代码风格一致**：新增的内容必须遵循现有代码的格式、命名约定和代码风格。

### 3.2. [关键] Fixture使用规范 (MANDATORY - V6.1 新增)

**🚨（关键）Async Generator Fixture 解包问题**

在测试函数中，**必须**使用 `async for` 解包 async generator fixture，不能直接使用 fixture 参数。

**问题场景**：
```python
# ❌ 错误：直接使用 async generator fixture
@pytest.mark.asyncio
async def test_create_brand(db_session):
    brand = Brand(name="测试品牌")
    db_session.add(brand)  # AttributeError: 'async_generator' object has no attribute 'add'
```

**正确做法**：
```python
# ✅ 正确：使用 async for 解包
@pytest.mark.asyncio
async def test_create_brand(db_session):
    async for db in db_session:  # ← 必须使用 async for 解包
        brand = Brand(name="测试品牌")
        db.add(brand)
        await db.flush()
        break  # ← 必须 break，否则会继续迭代
```

**强制要求**：
- **所有CRUD层测试**：**必须**使用 `async for db in db_session:` 解包 `db_session` fixture
- **所有API层测试**：**必须**使用 `async for client in async_client:` 解包 `async_client` fixture
- **严禁**直接使用 fixture 参数（如 `db_session.add(...)` 或 `async_client.post(...)`）

### 3.3. [关键] 测试事务管理与数据隔离规范 (MANDATORY)

**🚨 核心原则**：测试函数**严禁**调用 `await db.commit()`，依赖 fixture 的自动 `rollback()` 做测试隔离。

**禁止行为**：
- ❌ **严禁**在测试函数中调用 `await db.commit()`（3种场景除外）
- ❌ **严禁**手动调用 `await db.rollback()`（fixture会自动rollback）

**唯一可以使用commit的场景**：

1. **测试唯一性约束冲突**：
```python
# ✅ 正确：测试唯一性约束需要commit第一条数据
async def test_create_brand_duplicate_name(db_session):
    async for db in db_session:
        # 第一条数据：commit以触发约束
        brand1 = await crud.create_brand(db, BrandCreate(name="品牌A"))
        await db.commit()  # ✅ 必须commit，否则唯一性约束不生效
        
        # 第二条数据：期望违反唯一性约束
        with pytest.raises(DatabaseIntegrityException):
            brand2 = await crud.create_brand(db, BrandCreate(name="品牌A"))
            await db.commit()  # ✅ 这里commit会触发IntegrityError
        break
```

2. **测试级联删除或外键约束**：
```python
# ✅ 正确：测试级联删除需要commit父记录
async def test_cascade_delete(db_session):
    async for db in db_session:
        brand = await crud.create_brand(db, brand_data)
        await db.commit()  # ✅ commit父记录
        
        # 测试级联删除
        await crud.delete_brand(db, brand.id, hard_delete=True)
        break
```

3. **辅助函数内部**：
```python
# ✅ 辅助函数可以commit（但要谨慎使用）
async def create_test_brand(db: AsyncSession, **kwargs) -> Brand:
    """创建测试品牌的辅助函数"""
    brand = await crud.create_brand(db, BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}", **kwargs))
    await db.commit()  # ✅ 辅助函数可以commit
    await db.refresh(brand)
    return brand
```

### 3.4. [关键] 数据唯一性约束规范 (MANDATORY)

**🚨 核心原则**：唯一字段（如 `Brand.name`）**必须**使用UUID或Faker生成唯一值，**严禁**硬编码。

**禁止行为**：
- ❌ **严禁**硬编码唯一字段值（如 `name="测试品牌"`）
- ❌ **严禁**在多处使用相同的唯一值

**正确做法**：
```python
# ✅ 正确：使用UUID或Faker生成唯一值
from faker import Faker
import uuid

fake = Faker()

# 方式1：使用Faker
brand_name = f"品牌_{fake.company()}_{uuid.uuid4().hex[:8]}"

# 方式2：使用纯UUID
brand_name = f"品牌_{uuid.uuid4().hex[:12]}"
```

### 3.5. [关键] 外键依赖规范 (MANDATORY)

**🚨 核心原则**：创建有外键约束的对象时，**必须**先创建被引用的对象。

**禁止行为**：
- ❌ **严禁**直接使用 `uuid.uuid4()` 作为外键值（如 `topic_id=uuid.uuid4()`）
- ❌ **严禁**假设外键值已经存在于数据库中

**正确做法**：
```python
# ✅ 正确：先创建被引用的对象（Topic），再创建关联对象（BrandTopic）
async def test_create_brand_topic(db_session):
    async for db in db_session:
        # 1. 先创建Topic（被引用对象）
        from app.crud import topic as crud_topic
        from app.schemas.topic import TopicCreate
        topic = await crud_topic.create(db, TopicCreate(
            title=f"专题_{uuid.uuid4().hex[:8]}",
            status="published"
        ))
        await db.flush()  # flush以获取生成的ID
        
        # 2. 再创建Brand（被引用对象）
        brand = await crud.create_brand(db, BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}"))
        await db.flush()
        
        # 3. 最后创建关联对象（BrandTopic）
        brand_topic = await crud.batch_add_brand_topics(db, brand.id, [topic.id])
        break
```

**外键关联用例的自检清单**：
- [ ] 已经在上下文中列出了本模块涉及的外键关系（谁引用谁）
- [ ] 对每个外键字段，测试 Arrange 中都显式创建了父对象，并使用其 `id` 作为外键
- [ ] 没有出现"只创建关联表记录（如 `brand_topics`）但完全没有创建对应父表记录"的用例

### 3.6. [关键] 增量测试模式规范 (MANDATORY for Incremental Test Mode)

**🚨 关键原则**：在增量测试模式下，数据库中可能已经包含数据，因此**必须使用增量判断方式**验证数据库操作。

**✅ 正确的增量验证模式**：
```python
@pytest.mark.asyncio
async def test_create_brand_success(db_session):
    """测试创建品牌（增量验证）"""
    async for db in db_session:
        # ===== Arrange (准备) =====
        # [关键] 记录测试前的记录数量（基线）
        from sqlalchemy import select, func
        from app.models.brand import Brand
        
        count_stmt = select(func.count(Brand.id))
        result = await db.execute(count_stmt)
        initial_count = result.scalar()
        
        # 准备测试数据
        brand_data = BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}")
        
        # ===== Act (执行) =====
        brand = await crud.create_brand(db, brand_data)
        await db.flush()
        
        # ===== Assert (断言) =====
        # [关键] 验证增量：记录数应该增加1
        final_count_stmt = select(func.count(Brand.id))
        final_result = await db.execute(final_count_stmt)
        final_count = final_result.scalar()
        
        assert final_count == initial_count + 1, f"记录数应该增加1，但实际增加了{final_count - initial_count}"
        assert brand.name == brand_data.name
        assert brand.id is not None
        break
```

**❌ 错误的验证方式（禁止在增量模式下使用）**：
```python
# ❌ 错误：基于固定总数判断
brands = await crud.get_brands(db, limit=100)
assert len(brands) == 5  # 禁止！数据库中可能已经有其他数据

# ✅ 正确：基于增量判断
initial_count = await get_count_before_test(db)
brands = await crud.get_brands(db, limit=100)
assert len(brands) >= initial_count  # 只验证数量增加了（或保持不变）
assert new_brand.id in [b.id for b in brands]  # 验证新创建的数据存在
```

### 3.7. [关键] Mock 对象配置规范 (MANDATORY)

**🚨 核心原则**：Service 层测试中的 `db` 参数**必须是 `AsyncMock()` 对象。

**问题场景**：
```python
# ❌ 错误：使用同步 Mock
db = Mock()  # 同步 Mock
await db.execute(...)  # TypeError: object Mock can't be used in 'await' expression
```

**正确做法**：
```python
# ✅ 正确：使用 AsyncMock
from unittest.mock import AsyncMock, Mock

db = AsyncMock()  # 异步 Mock，支持 await

# execute的return_value应该是同步Mock（因为已被await）
mock_scalars = Mock()  # 同步Mock，不是AsyncMock
mock_scalars.all.return_value = [mock_brand1, mock_brand2]

mock_result = Mock()  # 同步Mock，不是AsyncMock
mock_result.scalars.return_value = mock_scalars

db.execute.return_value = mock_result  # 配置execute返回同步Mock对象
```

**关键要点**：
- 所有 Service 层测试必须使用 `db = AsyncMock()`，不能是 `db = Mock()`
- 所有 Mock 配置必须使用直接赋值 `db.execute.return_value = ...`
- 对于复杂调用链，需要配置完整的 Mock 链（如 `.scalars().all()`）

### 3.8. [关键] 函数式测试规范 (MANDATORY)

**🚨 核心原则**：**必须**使用函数式测试，所有测试函数必须直接定义在模块级别。

**禁止行为**：
- ❌ **严禁**使用类式测试（`class TestBrandCrud:`）

**正确做法**：
```python
# ✅ 正确：函数式测试
@pytest.mark.asyncio
async def test_create_brand_success(db_session):
    async for db in db_session:
        # 测试代码
        pass
```

---

## 4. 具体实现规范 (Specific Implementation Requirements)

### 4.1. 实用派测试 (Pragmatic: CRUD & API)

#### A. CRUD层测试规范

**验证数据库状态**：
- **必须**通过 `db.refresh()` 或**再次查询**来"证明"数据已被正确创建、更新或删除
- **必须**使用增量判断方式验证数据库操作（记录基线，验证增量）

**示例**：
```python
@pytest.mark.asyncio
async def test_create_brand_success(db_session):
    async for db in db_session:
        # Arrange: 记录基线
        count_stmt = select(func.count(Brand.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # Act
        brand_data = BrandCreate(name=f"品牌_{uuid.uuid4().hex[:8]}")
        brand = await crud.create_brand(db, brand_data)
        await db.flush()
        
        # Assert: 验证增量
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count + 1
        
        # Assert: 验证对象属性
        await db.refresh(brand)
        assert brand.name == brand_data.name
        break
```

#### B. API层测试规范

**验证完整链路**：
- **必须**同时验证API响应（状态码、业务码、数据）和数据库状态变化
- **必须**使用**新会话**查询以避免身份映射缓存陷阱

**示例**：
```python
@pytest.mark.asyncio
async def test_create_brand_api_success(async_client, admin_user_token):
    async for client in async_client:
        # Arrange
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        brand_data = {"name": f"品牌_{uuid.uuid4().hex[:8]}"}
        
        # Act
        response = await client.post("/api/v1/admin/brands", json=brand_data, headers=headers)
        
        # Assert: 验证HTTP响应
        assert response.status_code == 200
        assert response.json()["code"] == 200
        brand_id = response.json()["data"]["id"]
        
        # Assert: 验证数据库状态（使用新会话）
        from app.database import async_session_factory
        async with async_session_factory() as new_db:
            from sqlalchemy import select
            from app.models.brand import Brand
            stmt = select(Brand).where(Brand.id == brand_id)
            result = await new_db.execute(stmt)
            db_brand = result.scalar_one_or_none()
            assert db_brand.name == brand_data["name"]
        break
```

### 4.2. 学院派测试 (Academic: Service & I/O)

**验证业务逻辑**：
- **必须**使用 `mocker` Mock 掉 CRUD/I/O
- **必须**使用 `pytest.raises` 验证自定义异常

**🚨 [关键] Service层响应结构检查清单（brand模块特定）**：

**⚠️ 必须读取Service层代码**：在生成测试代码前，**必须**使用 `read_file()` 读取 `app/services/brand_service.py`，确认每个方法的 `data` 字段类型。

**brand模块Service层响应结构类型（必须基于实际代码确认）**：

1. **单个对象返回**（如 `get_brand_by_id`, `create_brand`, `update_brand`）：
   - `data` 字段类型：**`BrandItem` 对象**（Pydantic模型）
   - **访问方式**：使用**属性访问**（`result["data"].id`，**不是** `result["data"]["id"]`）

2. **对象列表返回**（如 `get_brands_list`）：
   - `data` 字段类型：**`List[BrandItem]`**（Pydantic模型列表）
   - **访问方式**：使用**列表索引 + 属性访问**（`result["data"][0].name`，**不是** `result["data"][0]["name"]`）

3. **嵌套结构返回**（如 `get_brand_content`）：
   - `data` 字段类型：**字典**（`{"brand_info": BrandItem, "associated_topics": [...]}`）
   - **访问方式**：使用**混合访问**（`result["data"]["brand_info"].id`，先字典访问，再属性访问）

**正确示例**：
```python
@pytest.mark.asyncio
async def test_create_brand_service_success(mocker):
    # Arrange
    from unittest.mock import AsyncMock, Mock
    from app.services.brand_service import BrandService
    
    db = AsyncMock()
    mock_brand = Mock(id=uuid.uuid4(), name="测试品牌")
    
    # Mock CRUD调用
    mock_create = mocker.patch("app.crud.brand.create_brand", new_callable=AsyncMock, return_value=mock_brand)
    
    service = BrandService()
    brand_data = BrandCreate(name="测试品牌")
    
    # Act
    result = await service.create_brand(db, brand_data, user_id=uuid.uuid4(), role="ADMIN")
    
    # Assert
    assert result["code"] == 200
    # ✅ 正确：data 是 BrandItem 对象，使用属性访问
    assert result["data"].id == mock_brand.id  # 不是 result["data"]["id"]
    mock_create.assert_called_once()
```

```python
@pytest.mark.asyncio
async def test_get_brands_list_success(mocker):
    # Arrange
    mock_brand1 = Mock(name="品牌1")
    mock_brand2 = Mock(name="品牌2")
    
    mock_get_brands = mocker.patch("app.crud.brand.get_brands", new_callable=AsyncMock, return_value=[mock_brand1, mock_brand2])
    
    service = BrandService()
    
    # Act
    result = await service.get_brands_list(db, limit=100, q=None, current_user_id=None, role=None)
    
    # Assert
    assert result["code"] == 200
    assert len(result["data"]) == 2
    # ✅ 正确：data 是 List[BrandItem]，使用列表索引 + 属性访问
    assert result["data"][0].name == "品牌1"  # 不是 result["data"][0]["name"]
    mock_get_brands.assert_called_once_with(db, 100, None)
```

```python
@pytest.mark.asyncio
async def test_get_brand_content_success(mocker):
    # Arrange
    mock_brand = Mock(id=brand_id)
    mock_topic1 = Mock(title="专题1")
    mock_topic2 = Mock(title="专题2")
    
    mock_get_brand_with_topics = mocker.patch("app.crud.brand.get_brand_with_topics", new_callable=AsyncMock, return_value=(mock_brand, [mock_topic1, mock_topic2]))
    
    service = BrandService()
    
    # Act
    result = await service.get_brand_content(db, brand_id, current_user_id=None, role=None)
    
    # Assert
    assert result["code"] == 200
    # ✅ 正确：data 是字典结构，使用混合访问（先字典访问，再属性访问）
    assert result["data"]["brand_info"].id == brand_id  # 不是 result["data"]["brand_info"]["id"]
    assert len(result["data"]["associated_topics"]) == 2
    mock_get_brand_with_topics.assert_called_once_with(db, brand_id)
```

**❌ 错误示例（常见错误）**：
```python
# ❌ 错误：使用字典访问访问 Pydantic 对象
result = await service.create_brand(...)
assert result["data"]["id"] == brand_id  # TypeError: 'BrandItem' object is not subscriptable

# ❌ 错误：使用属性访问访问字典
result = await service.get_brand_content(...)
assert result["data"].id == brand_id  # AttributeError: 'dict' object has no attribute 'id'

# ❌ 错误：使用字典访问访问 Pydantic 对象列表
result = await service.get_brands_list(...)
assert result["data"][0]["name"] == "品牌1"  # TypeError: 'BrandItem' object is not subscriptable
```

**关键检查点**：
- [ ] 已读取 `app/services/brand_service.py`，确认每个方法的 `data` 字段类型
- [ ] 已区分 `data` 是 Pydantic 对象还是字典结构
- [ ] 已根据类型选择正确的访问方式（属性访问 vs 字典访问 vs 混合访问）
- [ ] 已考虑 ID 类型转换（`uuid.UUID` vs `str`）

---

## 5. 工程与风格规范 (Engineering & Style Norms)

- **函数式测试**：所有测试函数必须直接定义在模块级别（**严禁**使用类式测试）
- **命名规范**：测试函数名使用 `test_<function_name>_<scenario>` 格式（如 `test_create_brand_success`）
- **唯一字段生成**：使用 `uuid.uuid4()` 或 `Faker` 生成唯一值
- **外键依赖**：必须先创建被引用的对象，再创建引用对象
- **增量验证**：必须使用增量判断方式验证数据库操作

---

## 6. [动态生成] 核心上下文与被测试代码 (Context & Code to Test)

**⚠️ 关键规则（MUST READ）**：
- **本节列出依赖文件清单，生成测试代码时必须主动读取这些文件的完整内容**
- **必须根据实际代码的字段、方法、约束来生成测试，而不是猜测**

### 6.1 依赖文件清单

**⚠️ 必须读取的文件（CRITICAL）**：
- `app/models/brand.py` - Brand、BrandTopic、BrandRoom模型定义
- `app/schemas/brand.py` - BrandCreate、BrandUpdate、BrandItem等Schema定义
- `app/crud/brand.py` - 14个CRUD函数定义
- `app/services/brand_service.py` - 14个Service方法定义
- `app/api/v1/endpoints/brand.py` - 13个API端点定义
- `tests/conftest.py` - **必须读取**（增量模式），了解现有Fixture定义
- `app/models/topic.py` - Topic模型（外键依赖）
- `app/models/live_core.py` - LiveRoom模型（外键依赖）

### 6.2 关键模型字段摘要（必须从实际代码读取完整定义）

**Brand模型（`app/models/brand.py`）**：
- `id: UUID` - 主键（应用层生成）
- `name: str` - 品牌名称（**唯一约束**：`unique=True`）
- `slug: Optional[str]` - URL友好标识符
- `logo_url: Optional[str]` - Logo图片URL
- `description: Optional[Text]` - 品牌描述
- `website_url: Optional[str]` - 官网链接
- `sort_order: int` - 排序权重（默认0）
- `is_active: bool` - 软删除标识（默认True）
- `created_at: datetime` - 创建时间
- `updated_at: datetime` - 更新时间

**BrandTopic模型（关联表）**：
- `brand_id: UUID` - 外键（引用 `brands.id`）
- `topic_id: UUID` - 外键（引用 `topics.id`）
- 复合主键：`(brand_id, topic_id)`

**BrandRoom模型（关联表）**：
- `brand_id: UUID` - 外键（引用 `brands.id`）
- `room_id: UUID` - 外键（引用 `live_rooms.id`）
- 复合主键：`(brand_id, room_id)`

### 6.3 关键CRUD函数签名摘要（必须从实际代码读取完整定义）

**Brands CRUD（8个函数）**：
1. `async def get_brands(db, limit=100, q=None) -> List[Brand]`
2. `async def get_brand_with_topics(db, brand_id) -> Tuple[Optional[Brand], List[Topic]]`
3. `async def create_brand(db, brand_in: BrandCreate) -> Brand`
4. `async def get_brands_paginated(db, page, size, name=None, is_active=None) -> Tuple[List[Brand], int]`
5. `async def get_brand_by_id(db, brand_id) -> Optional[Brand]`
6. `async def update_brand(db, brand_id, brand_in: BrandUpdate) -> Brand`
7. `async def delete_brand(db, brand_id, hard_delete=False) -> Brand`
8. `async def check_brand_references(db, brand_id) -> Tuple[int, int]`

**Brand_Topics CRUD（3个函数）**：
9. `async def batch_add_brand_topics(db, brand_id, topic_ids: List[UUID]) -> int`
10. `async def delete_brand_topic(db, brand_id, topic_id) -> bool`
11. `async def get_brand_topics_paginated(db, brand_id, page, size) -> Tuple[List[dict], int]`

**Brand_Rooms CRUD（3个函数）**：
12. `async def bind_room_brands(db, room_id, brand_ids: List[UUID]) -> List[UUID]`
13. `async def get_room_brands(db, room_id) -> List[Brand]`
14. `async def get_room_brands_for_tab(db, room_id) -> List[Brand]`

### 6.4 关键Service方法签名摘要（必须从实际代码读取完整定义）

**Brands Service（7个方法）**：
1. `async def get_brands_list(self, db, limit, q, current_user_id, role) -> dict`
2. `async def get_brand_content(self, db, brand_id, current_user_id, role) -> dict`
3. `async def create_brand(self, db, brand_in, current_user_id, role) -> dict`
4. `async def get_brands_paginated(self, db, page, size, sort, name, is_active, current_user_id, role) -> dict`
5. `async def get_brand_by_id(self, db, brand_id, current_user_id, role) -> dict`
6. `async def update_brand(self, db, brand_id, brand_in, current_user_id, role) -> dict`
7. `async def delete_brand(self, db, brand_id, hard_delete, current_user_id, role) -> dict`

**Brand_Topics Service（3个方法）**：
8. `async def batch_add_brand_topics(self, db, brand_id, topic_ids, current_user_id, role) -> dict`
9. `async def delete_brand_topic(self, db, brand_id, topic_id, current_user_id, role) -> dict`
10. `async def get_brand_topics_paginated(self, db, brand_id, page, size, current_user_id, role) -> dict`

**Brand_Rooms Service（3个方法）**：
11. `async def bind_room_brands(self, db, room_id, brand_ids, current_user_id, role) -> dict`
12. `async def get_room_brands_admin(self, db, room_id, current_user_id, role) -> dict`
13. `async def get_room_brands_for_tab(self, db, room_id, include_topic_brands, topic_id, current_user_id, role) -> dict`

**权限守卫函数（1个）**：
14. `def _check_admin_permission(self, user_role: str) -> None`

### 6.5 关键API端点摘要（必须从实际代码读取完整定义）

**Brands API（7个端点）**：
1. `GET /brands` - 获取品牌列表（Public + Optional Auth）
2. `GET /brands/{brand_id}/content` - 获取品牌详情及关联专题（Public + Optional Auth）
3. `POST /admin/brands` - 创建品牌（Strict Auth + Admin）
4. `GET /admin/brands` - 管理员分页获取品牌列表（Strict Auth + Admin）
5. `GET /admin/brands/{brand_id}` - 获取单个品牌（Strict Auth + Admin）
6. `PATCH /admin/brands/{brand_id}` - 更新品牌（Strict Auth + Admin）
7. `DELETE /admin/brands/{brand_id}` - 删除品牌（Strict Auth + Admin/SuperAdmin）

**Brand_Topics API（3个端点）**：
8. `POST /admin/brands/{brand_id}/topics` - 批量关联专题到品牌（Strict Auth + Admin）
9. `DELETE /admin/brands/{brand_id}/topics/{topic_id}` - 解除品牌-专题关联（Strict Auth + Admin）
10. `GET /admin/brands/{brand_id}/topics` - 获取品牌关联专题列表（Strict Auth + Admin）

**Brand_Rooms API（3个端点）**：
11. `POST /admin/rooms/{room_id}/brands` - 绑定直播间品牌（Strict Auth + Admin）
12. `GET /admin/rooms/{room_id}/brands` - 获取直播间绑定的品牌（Strict Auth + Admin）
13. `GET /rooms/{room_id}/brands` - 获取直播间品牌Tab内容（Public + Optional Auth）

### 6.6 conftest.py关键Fixture摘要（必须从实际代码读取完整定义）

**数据库相关Fixture**：
- `db_session` - 提供数据库会话（async generator，必须使用 `async for db in db_session:` 解包）
- `async_session_factory` - 提供创建新会话的能力（用于API层测试验证数据库状态）

**HTTP客户端Fixture**：
- `async_client` - 提供异步HTTP客户端（async generator，必须使用 `async for client in async_client:` 解包）

**用户认证Fixture**：
- `regular_user_id` - 普通用户ID（UUID）
- `admin_user_id` - 管理员用户ID（UUID）
- `admin_user_token` - 管理员JWT Token（字符串）

---

## 7. [动态生成] 具体测试任务列表 (Specific Test Tasks)

**⚠️ 增量测试模式说明**：
- **已存在的测试文件**：`tests/conftest.py` 及其他模块的测试文件（**严禁修改**）
- **需要新增的测试文件**：
  - `tests/unit/test_crud_brand.py` - **新增**
  - `tests/unit/test_service_brand.py` - **新增**
  - `tests/integration/test_api_brand.py` - **新增**
- **必须复用现有Fixture**：`db_session`, `async_client`, `regular_user_id`, `admin_user_id`, `admin_user_token` 等

### A. 针对 `app/crud/brand.py` (实用派 CRUD 测试)

**⚠️ 必须读取完整文件内容，提取所有函数签名**

**Brands CRUD函数（8个）**：

1. **`async def get_brands(db, limit, q=None)`**：
   - `test_get_brands_success`: 创建多个品牌（is_active=True），调用 `get_brands()`，断言返回的品牌列表正确（**增量验证**）
   - `test_get_brands_with_search`: 创建多个品牌，调用 `get_brands(q="关键词")`，断言只返回匹配的品牌
   - `test_get_brands_limit`: 创建多个品牌，调用 `get_brands(limit=5)`，断言返回数量不超过5

2. **`async def get_brand_with_topics(db, brand_id)`**：
   - `test_get_brand_with_topics_success`: 创建品牌和专题，建立关联，调用 `get_brand_with_topics()`，断言返回品牌和专题列表
   - `test_get_brand_with_topics_not_found`: 调用 `get_brand_with_topics()` 传入不存在的brand_id，断言返回 `(None, [])`

3. **`async def create_brand(db, brand_in)`**：
   - `test_create_brand_success`: 调用 `create_brand()`，使用 `db.refresh()` 验证数据库中的对象（**增量验证**）
   - `test_create_brand_duplicate_name`: 创建同名品牌，断言抛出 `DatabaseIntegrityException`（**需要commit第一条数据**）

4. **`async def get_brands_paginated(db, page, size, name, is_active)`**：
   - `test_get_brands_paginated_success`: 创建多个品牌，调用 `get_brands_paginated()`，断言分页结果正确（**增量验证**）
   - `test_get_brands_paginated_with_filters`: 创建多个品牌（不同is_active），调用 `get_brands_paginated(is_active=True)`，断言只返回激活品牌

5. **`async def get_brand_by_id(db, brand_id)`**：
   - `test_get_brand_by_id_success`: 创建品牌，调用 `get_brand_by_id()`，断言返回的品牌正确
   - `test_get_brand_by_id_not_found`: 调用 `get_brand_by_id()` 传入不存在的brand_id，断言返回 `None`

6. **`async def update_brand(db, brand_id, brand_in)`**：
   - `test_update_brand_success`: 创建品牌，调用 `update_brand()`，使用 `db.refresh()` 验证更新后的对象
   - `test_update_brand_duplicate_name`: 创建两个品牌，更新第二个品牌为第一个的名称，断言抛出 `DatabaseIntegrityException`

7. **`async def delete_brand(db, brand_id, hard_delete=False)`**：
   - `test_delete_brand_soft_delete`: 创建品牌，调用 `delete_brand(hard_delete=False)`，验证 `is_active=False`（**增量验证**）
   - `test_delete_brand_hard_delete`: 创建品牌，调用 `delete_brand(hard_delete=True)`，验证品牌从数据库删除（**增量验证**，**需要commit父记录**）

8. **`async def check_brand_references(db, brand_id)`**：
   - `test_check_brand_references_no_refs`: 创建品牌（无关联），调用 `check_brand_references()`，断言返回 `(0, 0)`
   - `test_check_brand_references_with_topics`: 创建品牌和专题，建立关联，调用 `check_brand_references()`，断言返回正确的引用数
   - `test_check_brand_references_with_rooms`: 创建品牌和直播间，建立关联，调用 `check_brand_references()`，断言返回正确的引用数

**Brand_Topics CRUD函数（3个）**：

9. **`async def batch_add_brand_topics(db, brand_id, topic_ids)`**：
   - `test_batch_add_brand_topics_success`: **先创建**Brand和Topic（外键依赖），调用 `batch_add_brand_topics()`，验证关联创建（**增量验证**）
   - `test_batch_add_brand_topics_empty_list`: 调用 `batch_add_brand_topics(brand_id, [])`，断言返回0

10. **`async def delete_brand_topic(db, brand_id, topic_id)`**：
    - `test_delete_brand_topic_success`: **先创建**Brand、Topic和BrandTopic关联，调用 `delete_brand_topic()`，验证关联删除（**增量验证**）
    - `test_delete_brand_topic_not_found`: 调用 `delete_brand_topic()` 传入不存在的关联，断言返回 `False`

11. **`async def get_brand_topics_paginated(db, brand_id, page, size)`**：
    - `test_get_brand_topics_paginated_success`: **先创建**Brand和多个Topic，建立关联，调用 `get_brand_topics_paginated()`，断言分页结果正确（**增量验证**）

**Brand_Rooms CRUD函数（3个）**：

12. **`async def bind_room_brands(db, room_id, brand_ids)`**：
    - `test_bind_room_brands_success`: **先创建**LiveRoom和Brand（外键依赖），调用 `bind_room_brands()`，验证关联创建（**增量验证**，**全量替换策略**）
    - `test_bind_room_brands_replace`: **先创建**LiveRoom和Brand，建立旧关联，调用 `bind_room_brands()` 传入新brand_ids，验证旧关联被删除，新关联被创建

13. **`async def get_room_brands(db, room_id)`**：
    - `test_get_room_brands_success`: **先创建**LiveRoom和Brand，建立关联，调用 `get_room_brands()`，断言返回品牌列表

14. **`async def get_room_brands_for_tab(db, room_id)`**：
    - `test_get_room_brands_for_tab_success`: **先创建**LiveRoom和Brand，建立关联，调用 `get_room_brands_for_tab()`，断言返回品牌列表

### B. 针对 `app/services/brand_service.py` (学院派 Service 测试)

**⚠️ 必须读取完整文件内容，提取所有方法签名。必须Mock CRUD层调用。**

**Brands Service方法（7个）**：

1. **`async def get_brands_list(self, db, limit, q, current_user_id, role)`**：
   - `test_get_brands_list_success`: Mock `crud.get_brands()`，调用Service方法，断言返回标准响应格式

2. **`async def get_brand_content(self, db, brand_id, current_user_id, role)`**：
   - `test_get_brand_content_success`: Mock `crud.get_brand_with_topics()`，调用Service方法，断言返回标准响应格式
   - `test_get_brand_content_not_found`: Mock `crud.get_brand_with_topics()` 返回 `(None, [])`，断言抛出 `NotFoundException`

3. **`async def create_brand(self, db, brand_in, current_user_id, role)`**：
   - `test_create_brand_success`: Mock `crud.create_brand()`，调用Service方法，断言返回标准响应格式
   - `test_create_brand_permission_denied`: 调用Service方法（role="REGULAR"），断言抛出 `PermissionDeniedException`（**验证权限守卫**）
   - `test_create_brand_conflict`: Mock `crud.create_brand()` 抛出 `DatabaseIntegrityException`，断言Service转换为 `ConflictException`

4. **`async def get_brands_paginated(self, db, page, size, sort, name, is_active, current_user_id, role)`**：
   - `test_get_brands_paginated_success`: Mock `crud.get_brands_paginated()`，调用Service方法，断言返回标准响应格式
   - `test_get_brands_paginated_permission_denied`: 调用Service方法（role="REGULAR"），断言抛出 `PermissionDeniedException`

5. **`async def get_brand_by_id(self, db, brand_id, current_user_id, role)`**：
   - `test_get_brand_by_id_success`: Mock `crud.get_brand_by_id()`，调用Service方法，断言返回标准响应格式
   - `test_get_brand_by_id_not_found`: Mock `crud.get_brand_by_id()` 返回 `None`，断言抛出 `NotFoundException`

6. **`async def update_brand(self, db, brand_id, brand_in, current_user_id, role)`**：
   - `test_update_brand_success`: Mock `crud.update_brand()`，调用Service方法，断言返回标准响应格式
   - `test_update_brand_permission_denied`: 调用Service方法（role="REGULAR"），断言抛出 `PermissionDeniedException`

7. **`async def delete_brand(self, db, brand_id, hard_delete, current_user_id, role)`**：
   - `test_delete_brand_soft_delete_success`: Mock `crud.delete_brand()` 和 `crud.check_brand_references()`，调用Service方法（hard_delete=False），断言返回标准响应格式
   - `test_delete_brand_hard_delete_superadmin`: 调用Service方法（hard_delete=True, role="SUPERADMIN"），断言成功
   - `test_delete_brand_hard_delete_regular`: 调用Service方法（hard_delete=True, role="REGULAR"），断言抛出 `PermissionDeniedException`
   - `test_delete_brand_hard_delete_with_refs`: Mock `crud.check_brand_references()` 返回 `(1, 0)`，断言抛出 `ConflictException`

**Brand_Topics Service方法（3个）**：

8. **`async def batch_add_brand_topics(self, db, brand_id, topic_ids, current_user_id, role)`**：
   - `test_batch_add_brand_topics_success`: Mock `crud.get_brand_by_id()` 和 `crud.batch_add_brand_topics()`，调用Service方法，断言返回标准响应格式
   - `test_batch_add_brand_topics_permission_denied`: 调用Service方法（role="REGULAR"），断言抛出 `PermissionDeniedException`
   - `test_batch_add_brand_topics_invalid_topic_ids`: Mock验证topic_ids不存在，断言抛出 `InvalidParameterException`

9. **`async def delete_brand_topic(self, db, brand_id, topic_id, current_user_id, role)`**：
   - `test_delete_brand_topic_success`: Mock `crud.delete_brand_topic()` 返回 `True`，调用Service方法，断言返回标准响应格式
   - `test_delete_brand_topic_not_found`: Mock `crud.delete_brand_topic()` 返回 `False`，断言抛出 `NotFoundException`

10. **`async def get_brand_topics_paginated(self, db, brand_id, page, size, current_user_id, role)`**：
    - `test_get_brand_topics_paginated_success`: Mock `crud.get_brand_by_id()` 和 `crud.get_brand_topics_paginated()`，调用Service方法，断言返回标准响应格式

**Brand_Rooms Service方法（3个）**：

11. **`async def bind_room_brands(self, db, room_id, brand_ids, current_user_id, role)`**：
    - `test_bind_room_brands_success`: Mock `crud.bind_room_brands()`，调用Service方法，断言返回标准响应格式
    - `test_bind_room_brands_invalid_brand_ids`: Mock验证brand_ids不存在或已禁用，断言抛出 `InvalidParameterException`

12. **`async def get_room_brands_admin(self, db, room_id, current_user_id, role)`**：
    - `test_get_room_brands_admin_success`: Mock `crud.get_room_brands()`，调用Service方法，断言返回标准响应格式

13. **`async def get_room_brands_for_tab(self, db, room_id, include_topic_brands, topic_id, current_user_id, role)`**：
    - `test_get_room_brands_for_tab_success`: Mock `crud.get_room_brands_for_tab()`，调用Service方法，断言返回标准响应格式
    - `test_get_room_brands_for_tab_with_topic_brands`: 调用Service方法（include_topic_brands=True），断言返回结构化数据

### C. 针对 `app/api/v1/endpoints/brand.py` (实用派 API 测试)

**⚠️ 必须读取完整文件内容，提取所有端点路径、方法、依赖注入。必须同时验证API响应和数据库状态。**

**Brands API（7个端点）**：

1. **`GET /brands`** - 获取品牌列表（Public + Optional Auth）：
   - `test_get_brands_api_success`: 调用API（无认证），断言返回品牌列表
   - `test_get_brands_api_with_auth`: 调用API（带认证），断言返回品牌列表
   - `test_get_brands_api_with_search`: 调用API（q="关键词"），断言只返回匹配的品牌

2. **`GET /brands/{brand_id}/content`** - 获取品牌详情及关联专题：
   - `test_get_brand_content_api_success`: **先创建**Brand和Topic，建立关联，调用API，断言返回品牌详情和专题列表（**验证数据库状态**）

3. **`POST /admin/brands`** - 创建品牌（Strict Auth + Admin）：
   - `test_create_brand_api_success`: 调用API（admin_user_token），断言HTTP 200和数据库状态（**验证数据库状态**）
   - `test_create_brand_api_permission_denied`: 调用API（无认证），断言HTTP 401
   - `test_create_brand_api_duplicate_name`: 创建同名品牌，断言HTTP 409

4. **`GET /admin/brands`** - 管理员分页获取品牌列表：
   - `test_get_brands_admin_api_success`: 调用API（admin_user_token），断言分页结果

5. **`GET /admin/brands/{brand_id}`** - 获取单个品牌：
   - `test_get_brand_admin_api_success`: **先创建**Brand，调用API，断言返回品牌详情

6. **`PATCH /admin/brands/{brand_id}`** - 更新品牌：
   - `test_update_brand_api_success`: **先创建**Brand，调用API更新，断言HTTP 200和数据库状态（**验证数据库状态**）

7. **`DELETE /admin/brands/{brand_id}`** - 删除品牌：
   - `test_delete_brand_api_soft_delete`: **先创建**Brand，调用API（hard_delete=False），断言HTTP 200和 `is_active=False`（**验证数据库状态**）
   - `test_delete_brand_api_hard_delete`: **先创建**Brand（无关联），调用API（hard_delete=True, SUPERADMIN），断言HTTP 200和数据库删除（**验证数据库状态**）
   - `test_delete_brand_api_with_refs`: **先创建**Brand和Topic，建立关联，调用API（hard_delete=True），断言HTTP 409

**Brand_Topics API（3个端点）**：

8. **`POST /admin/brands/{brand_id}/topics`** - 批量关联专题到品牌：
   - `test_bind_brand_topics_api_success`: **先创建**Brand和Topic（外键依赖），调用API，断言HTTP 200和数据库状态（**验证数据库状态**）

9. **`DELETE /admin/brands/{brand_id}/topics/{topic_id}`** - 解除品牌-专题关联：
   - `test_unbind_brand_topic_api_success`: **先创建**Brand、Topic和BrandTopic关联，调用API，断言HTTP 200和数据库状态（**验证数据库状态**）

10. **`GET /admin/brands/{brand_id}/topics`** - 获取品牌关联专题列表：
    - `test_get_brand_topics_api_success`: **先创建**Brand和多个Topic，建立关联，调用API，断言分页结果

**Brand_Rooms API（3个端点）**：

11. **`POST /admin/rooms/{room_id}/brands`** - 绑定直播间品牌：
    - `test_bind_room_brands_api_success`: **先创建**LiveRoom和Brand（外键依赖），调用API，断言HTTP 200和数据库状态（**验证数据库状态**，**全量替换策略**）

12. **`GET /admin/rooms/{room_id}/brands`** - 获取直播间绑定的品牌：
    - `test_get_room_brands_admin_api_success`: **先创建**LiveRoom和Brand，建立关联，调用API，断言返回品牌列表

13. **`GET /rooms/{room_id}/brands`** - 获取直播间品牌Tab内容：
    - `test_get_room_brands_public_api_success`: **先创建**LiveRoom和Brand，建立关联，调用API（Public），断言返回品牌列表
    - `test_get_room_brands_public_api_with_topic_brands`: 调用API（include_topic_brands=True, topic_id=...），断言返回结构化数据

---

## 8. 其他规范 (Additional Norms)

- **Arrange-Act-Assert模式**：所有测试用例必须遵循此结构，使用注释清晰分开三个阶段
- **错误处理**：必须验证异常场景（NotFoundException、PermissionDeniedException等）
- **数据隔离**：依赖fixture的自动rollback机制，测试之间互不影响
- **代码风格**：遵循PEP 8，使用类型提示，添加必要的文档字符串

---

**生成日期**: 2026-01-18  
**文档版本**: V1.0
