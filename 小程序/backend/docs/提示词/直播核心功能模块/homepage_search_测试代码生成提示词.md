# homepage_search 模块测试代码生成提示词

**模块名称**: homepage_search  
**测试模式**: incremental（增量测试模式）  
**生成日期**: 2026-01-19  
**设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`

---

## 1. 模块概述

homepage_search模块包含3个Phase：
- **Phase1**: 焦点图CRUD（Featured Content管理）
- **Phase2**: 首页API（复杂多表JOIN查询、热度计算）
- **Phase3**: 搜索API（跨4个表的全文搜索）

**核心功能**：
- 6个CRUD函数（焦点图管理）
- 13个Service方法（含业务逻辑）
- 7个API端点（5个管理员 + 2个公开）

---

## 2. 测试策略

### 2.1 测试分层

由于模块功能复杂且代码量大（~1500行），采用**重点测试策略**：

**CRUD层测试（单元测试）**：
- ✅ 测试焦点图CRUD（Phase1）- 6个函数
- ⏭️ Phase2和Phase3的CRUD暂不测试（复杂SQL查询，留待集成测试）

**Service层测试（单元测试，使用mock）**：
- ✅ 测试焦点图Service方法（Phase1）- 5个方法
- ✅ 测试Phase2的关键业务逻辑方法（热度计算、状态判断）- 4个辅助方法
- ⏭️ Phase3的Service方法暂不测试（简单逻辑，留待集成测试）

**API层测试（集成测试，真实数据库）**：
- ✅ 测试焦点图API（Phase1）- 5个端点
- ✅ 测试首页API（Phase2）- 1个端点
- ✅ 测试搜索API（Phase3）- 1个端点

### 2.2 优先级

- **P0（必测）**: Phase1焦点图CRUD + Service + API
- **P1（重要）**: Phase2首页API（集成测试）
- **P2（一般）**: Phase3搜索API（集成测试）

---

## 3. CRUD层测试生成要求

### 3.1 目标文件

- 输出路径：`tests/unit/test_crud_homepage_search.py`
- 测试对象：`app/crud/homepage_search.py`（Phase1部分）

### 3.2 需要测试的函数（Phase1 - 6个函数）

**从代码中提取的函数签名**：

```python
# 1. 获取焦点图列表
async def get_featured_content_list(
    db: AsyncSession,
    include_inactive: bool = False,
    include_scheduled: bool = False
) -> List[FeaturedContent]

# 2. 根据ID获取焦点图
async def get_featured_content_by_id(
    db: AsyncSession,
    content_id: uuid.UUID
) -> Optional[FeaturedContent]

# 3. 创建焦点图
async def create_featured_content(
    db: AsyncSession,
    content_data: FeaturedContentCreate
) -> FeaturedContent

# 4. 更新焦点图
async def update_featured_content(
    db: AsyncSession,
    content_id: uuid.UUID,
    content_data: FeaturedContentUpdate
) -> Optional[FeaturedContent]

# 5. 删除焦点图
async def delete_featured_content(
    db: AsyncSession,
    content_id: uuid.UUID,
    soft_delete: bool = True
) -> bool

# 6. 获取焦点图总数
async def get_featured_content_count(
    db: AsyncSession,
    include_inactive: bool = False
) -> int
```

### 3.3 测试用例清单

**测试函数清单**（约12个测试用例）：

```python
# 1. get_featured_content_list 测试（3个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_list_public()  # 公开接口，只返回有效焦点图
@pytest.mark.asyncio
async def test_get_featured_content_list_admin()  # 管理员接口，返回所有焦点图
@pytest.mark.asyncio
async def test_get_featured_content_list_scheduled()  # 测试定时上下线逻辑

# 2. get_featured_content_by_id 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_by_id_success()
@pytest.mark.asyncio
async def test_get_featured_content_by_id_not_found()

# 3. create_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_create_featured_content_success()
@pytest.mark.asyncio
async def test_create_featured_content_with_schedule()  # 带定时上下线

# 4. update_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_update_featured_content_success()
@pytest.mark.asyncio
async def test_update_featured_content_not_found()

# 5. delete_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_delete_featured_content_soft_delete()
@pytest.mark.asyncio
async def test_delete_featured_content_hard_delete()

# 6. get_featured_content_count 测试（1个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_count()
```

### 3.4 测试数据规范

**FeaturedContent测试数据结构**（从Model和Schema提取）：

```python
# 必需字段
- title: str (max_length=255)
- image_url: str (max_length=512)

# 可选字段
- subtitle: Optional[str] (max_length=512)
- target_type: Optional[str] (max_length=50)
- target_id: Optional[UUID]
- target_url: Optional[str] (max_length=512)
- sort_order: int (default=0, ge=0)
- is_active: bool (default=True)
- start_at: Optional[datetime]
- end_at: Optional[datetime]
```

**测试数据生成辅助函数**：

```python
def create_test_featured_content_data(**kwargs):
    """创建测试用焦点图数据"""
    unique_id = str(uuid.uuid4())[:8]
    default_data = {
        "title": f"测试焦点图_{unique_id}",
        "image_url": f"https://example.com/image_{unique_id}.jpg",
        "subtitle": f"副标题_{unique_id}",
        "target_type": "room",
        "target_url": None,
        "sort_order": 0,
        "is_active": True,
    }
    default_data.update(kwargs)
    return FeaturedContentCreate(**default_data)
```

---

## 4. Service层测试生成要求

### 4.1 目标文件

- 输出路径：`tests/unit/test_service_homepage_search.py`
- 测试对象：`app/services/homepage_search_service.py`

### 4.2 需要测试的方法

**Phase1 - 焦点图Service方法（5个方法）**：

```python
# 1. 获取焦点图列表（公开）
async def get_featured_content_list(self, db: AsyncSession) -> dict

# 2. 获取焦点图列表（管理员）
async def get_featured_content_list_admin(
    self, db: AsyncSession, current_user_id: UUID, role: str
) -> dict

# 3. 创建焦点图
async def create_featured_content(
    self, db: AsyncSession, content_data: FeaturedContentCreate,
    current_user_id: UUID, role: str
) -> dict

# 4. 更新焦点图
async def update_featured_content(
    self, db: AsyncSession, content_id: UUID,
    content_data: FeaturedContentUpdate,
    current_user_id: UUID, role: str
) -> dict

# 5. 删除焦点图
async def delete_featured_content(
    self, db: AsyncSession, content_id: UUID,
    current_user_id: UUID, role: str
) -> dict
```

**Phase2 - 业务逻辑辅助方法（4个方法，单元测试）**：

```python
# 1. Host选择逻辑
def _select_host(self, room_data: Dict) -> Optional[HomepageHostInfo]

# 2. 直播状态判断
def _determine_live_status(self, session_status: Optional[str]) -> LiveStatusEnum

# 3. 状态数据构造
def _build_status_data(
    self, live_status: LiveStatusEnum, room_data: Dict
) -> HomepageStatusData

# 4. 热度计算
def _calculate_heat(self, room_data: Dict) -> Optional[int]
```

### 4.3 测试用例清单

**Phase1 Service层测试**（约10个测试用例）：

```python
# 1. get_featured_content_list 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_list_success()
@pytest.mark.asyncio
async def test_get_featured_content_list_empty()

# 2. get_featured_content_list_admin 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_list_admin_success()
@pytest.mark.asyncio
async def test_get_featured_content_list_admin_permission_denied()

# 3. create_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_create_featured_content_success()
@pytest.mark.asyncio
async def test_create_featured_content_permission_denied()

# 4. update_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_update_featured_content_success()
@pytest.mark.asyncio
async def test_update_featured_content_not_found()

# 5. delete_featured_content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_delete_featured_content_success()
@pytest.mark.asyncio
async def test_delete_featured_content_permission_denied()
```

**Phase2 业务逻辑辅助方法测试**（约5个测试用例）：

```python
# 1. _select_host 测试（2个测试用例）
def test_select_host_with_expert()  # 有场次专家
def test_select_host_without_expert()  # 无场次专家，返回null

# 2. _determine_live_status 测试（1个测试用例）
def test_determine_live_status()  # 测试所有状态映射

# 3. _build_status_data 测试（1个测试用例）
def test_build_status_data()  # 测试3种状态的数据填充

# 4. _calculate_heat 测试（1个测试用例）
def test_calculate_heat()  # 测试热度计算公式
```

### 4.4 Mock策略

**Service层测试使用Academic Testing模式（全mock）**：

```python
@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db
```

**Mock CRUD调用示例**：

```python
# 在测试中mock CRUD层调用
with patch('app.services.homepage_search_service.crud') as mock_crud:
    mock_crud.get_featured_content_list.return_value = [mock_content]
    
    service = HomepageSearchService()
    result = await service.get_featured_content_list(mock_db)
    
    assert result["code"] == 200
    assert len(result["data"]) == 1
```

---

## 5. API层测试生成要求

### 5.1 目标文件

- 输出路径：`tests/integration/test_api_homepage_search.py`
- 测试对象：`app/api/v1/endpoints/homepage_search.py`

### 5.2 需要测试的端点（7个端点）

**Phase1 - 焦点图API**（5个端点）：

```python
# 1. GET /featured-content - 获取焦点图列表（公开）
# 2. GET /featured-content/admin - 获取焦点图列表（管理员）
# 3. POST /featured-content/admin - 创建焦点图（管理员）
# 4. PATCH /featured-content/admin/{id} - 更新焦点图（管理员）
# 5. DELETE /featured-content/admin/{id} - 删除焦点图（管理员）
```

**Phase2 - 首页API**（1个端点）：

```python
# 6. GET /homepage/rooms - 获取首页直播间列表（公开）
```

**Phase3 - 搜索API**（1个端点）：

```python
# 7. GET /search - 全局搜索（公开）
```

### 5.3 测试用例清单

**Phase1 API测试**（约10个测试用例）：

```python
# 1. GET /featured-content 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_api_success()
@pytest.mark.asyncio
async def test_get_featured_content_api_only_active()

# 2. GET /featured-content/admin 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_featured_content_admin_api_success()
@pytest.mark.asyncio
async def test_get_featured_content_admin_api_permission_denied()

# 3. POST /featured-content/admin 测试（2个测试用例）
@pytest.mark.asyncio
async def test_create_featured_content_api_success()
@pytest.mark.asyncio
async def test_create_featured_content_api_validation_error()

# 4. PATCH /featured-content/admin/{id} 测试（2个测试用例）
@pytest.mark.asyncio
async def test_update_featured_content_api_success()
@pytest.mark.asyncio
async def test_update_featured_content_api_not_found()

# 5. DELETE /featured-content/admin/{id} 测试（2个测试用例）
@pytest.mark.asyncio
async def test_delete_featured_content_api_success()
@pytest.mark.asyncio
async def test_delete_featured_content_api_not_found()
```

**Phase2 API测试**（约2个测试用例）：

```python
# 6. GET /homepage/rooms 测试（2个测试用例）
@pytest.mark.asyncio
async def test_get_homepage_rooms_api_success()
@pytest.mark.asyncio
async def test_get_homepage_rooms_api_with_pagination()
```

**Phase3 API测试**（约2个测试用例）：

```python
# 7. GET /search 测试（2个测试用例）
@pytest.mark.asyncio
async def test_search_api_success()
@pytest.mark.asyncio
async def test_search_api_validation_error()  # 关键词少于2个字符
```

### 5.4 API测试模式

**使用Pragmatic Testing模式（真实数据库）**：

```python
@pytest.fixture
async def test_client():
    """创建测试客户端"""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def admin_auth_headers():
    """创建管理员认证headers"""
    return {
        "Authorization": "Bearer mock_admin_token"
    }
```

---

## 6. 测试数据准备

### 6.1 测试数据依赖

由于homepage_search模块依赖多个表，需要准备测试数据：

**Phase1测试依赖**：
- ✅ 只需`featured_content`表（自身表）

**Phase2测试依赖**：
- `live_rooms` - 直播间
- `live_sessions` - 场次
- `live_session_experts` - 场次专家关联
- `experts` - 专家
- `session_statistics` - 统计数据

**Phase3测试依赖**：
- `live_rooms` - 直播间
- `experts` - 专家
- `topics` - 专题
- `brands` - 品牌

### 6.2 测试数据创建策略

**简化策略**（减少测试复杂度）：

1. **Phase1测试**：直接创建`featured_content`记录
2. **Phase2测试**：使用数据库现有数据或创建最小化测试数据
3. **Phase3测试**：使用数据库现有数据或创建最小化测试数据

---

## 7. 特殊注意事项

### 7.1 增量测试模式

由于是增量测试模式，需要注意：
- ✅ 不修改现有测试（如果有）
- ✅ 只添加新测试用例
- ✅ 使用独立的测试数据（UUID后缀）

### 7.2 异步测试规范

```python
# ✅ 正确：使用 async for 展开 async_generator fixture
@pytest.mark.asyncio
async def test_example(db_session):
    async for db in db_session:
        result = await some_async_function(db)
        assert result is not None

# ❌ 错误：直接使用 async_generator fixture
@pytest.mark.asyncio
async def test_example(db_session):
    result = await some_async_function(db_session)  # 会报错
```

### 7.3 字段名提取要求

**严禁猜测字段名，必须从Model提取**：

```python
# ✅ 正确：从FeaturedContent Model提取的字段名
assert content.title == "测试焦点图"
assert content.subtitle == "副标题"
assert content.image_url == "https://example.com/image.jpg"
assert content.sort_order == 0
assert content.is_active == True

# ❌ 错误：猜测的字段名（Model中不存在）
assert content.name == "测试焦点图"  # 错误：Model中字段名是 title，不是 name
assert content.cta_text == "副标题"  # 错误：Model中字段名是 subtitle，不是 cta_text
```

---

## 8. 测试代码生成检查清单

生成测试代码时，必须确保：

- [ ] 所有字段名都从Model文件提取（不猜测）
- [ ] 所有函数签名都从CRUD/Service/API文件提取（不猜测）
- [ ] 所有API端点路径都从API文件提取（不猜测）
- [ ] 测试数据使用UUID后缀确保唯一性
- [ ] 异步测试使用`async for db in db_session:`模式
- [ ] Service层测试使用mock（Academic模式）
- [ ] API层测试使用真实数据库（Pragmatic模式）
- [ ] 所有测试用例都有清晰的docstring
- [ ] 测试覆盖了成功和失败场景

---

## 9. 预期测试数量总结

- **CRUD层测试**: 约12个测试用例
- **Service层测试**: 约15个测试用例（Phase1 10个 + Phase2 5个）
- **API层测试**: 约14个测试用例（Phase1 10个 + Phase2 2个 + Phase3 2个）
- **总计**: 约41个测试用例

---

**生成时间**: 2026-01-19  
**版本**: V1.0  
**状态**: ✅ 准备就绪，可开始生成测试代码
