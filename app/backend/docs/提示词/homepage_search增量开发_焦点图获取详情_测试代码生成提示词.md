# homepage_search 增量开发 - 测试代码生成提示词（焦点图获取详情）

**版本**: 增量版  
**模块名称**: 首页与搜索模块 (homepage_search)  
**增量主题**: 焦点图获取详情接口（GET /api/v1/featured-content/admin/{content_id}）  
**测试模式**: incremental（增量测试生成模式）  
**对应设计文档**:
- 主设计文档：`docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`
- 增量设计文档：`docs/03_系统设计/首页与搜索模块增量开发设计文档-焦点图获取详情接口.md`

---

## 1. 角色定义与测试模式

执行者须在生成任何测试代码前，**按顺序**完成：读取 Section 6 全部依赖 → 提取 Model/Schema/CRUD/Service/API 签名与路由 → 再按 Section 7 生成增量测试代码。

**测试模式**：**增量测试生成模式**。为 homepage_search 模块**新增**「焦点图获取详情」相关测试，在已有测试基础上**只追加**新测试函数；**严禁修改**已存在的测试函数与 conftest 已有内容。

**最小幅度修改**：只追加新测试函数；不修改、不删除、不重命名已有测试；conftest 仅允许新增 Fixture/导入，且需做冲突检查。

---

## 2. 核心测试哲学（混合策略）

| 测试目标层级 | 强制测试风格 | 核心工具 | 测试目标 |
|-------------|-------------|----------|----------|
| API / Endpoint 层 | 实用派 (Pragmatic) | httpx.AsyncClient + db_session + async_session_factory | 验证完整链路：JSON 响应 + 真实数据库状态 |
| Service 层 | 学院派 (Academic) | mocker（Mock CRUD） | 验证业务逻辑：权限检查、数据编排、异常抛出 |
| CRUD 层 | 实用派 (Pragmatic) | db_session（真实数据库） | 验证数据库状态：创建/更新/删除后通过再次查询验证 |

本次增量：**无 CRUD 变更**；**Service 增量** 1 个方法；**API 增量** 1 个端点。

---

## 3. 核心实现规范（须完整继承）

- **3.1** 测试环境：conftest 只增不改；新增 Fixture 前必须做命名/功能冲突检查；优先在测试文件内部定义新 Fixture 避免改 conftest。
- **3.1.5** Mock：禁止 MagicMock 模拟 Model；Service 层 `db` 必须为 `AsyncMock()`；CRUD 用 `new_callable=AsyncMock`。
- **3.2** 所有用例采用 Arrange-Act-Assert 结构，并用注释分节。
- **3.3** async generator fixture（如 `db_session`、`async_client`）必须使用 `async for x in fixture:` 解包。
- **3.3.5** 事务：默认不调用 `await db.commit()`；仅唯一性/级联等例外场景可 commit。
- **3.5** 外键：禁止用随机 UUID 作外键；先创建父对象再使用其 ID。
- **3.6** 函数式测试：禁止类式测试（禁止 `class TestXXX:`）。
- **3.7** Mock 链：`db.execute.return_value` 为同步 Mock；复杂链用 `Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=[...]))))` 等。
- **3.8** 字段/函数/路由均从 Section 6 依赖文件中读取，禁止猜测。
- **3.9** Service 层：须从源码读取被测方法**完整签名**；Mock 须覆盖调用链上所有被调 CRUD（如 `get_featured_content_by_id`）。
- **3.10** SQLAlchemy：joinedload 一对多须 `.unique()`，以 CRUD 实际加载策略为准。
- **3.11** 唯一约束字段使用 Faker 或 `uuid.uuid4().hex[:8]` 等生成唯一值。
- **3.12** 使用 `unittest.mock.ANY`，禁止 `pytest.any`。

**增量数据库验证**：断言须用增量方式（如记录操作前 count/ids，操作后断言增量），不得依赖“总数”断言。

---

## 4. 测试用例规划（仅增量部分）

### 4.1 CRUD 增量

无。本次增量未修改或新增 CRUD 函数，复用现有 `get_featured_content_by_id`。

### 4.2 Service 增量

| 方法名 | 测试场景 | 预期 |
|--------|----------|------|
| `get_featured_content_detail_admin` | 管理员、存在 content | 200，data 为单条 FeaturedContentItem |
| `get_featured_content_detail_admin` | 非 ADMIN/SUPERADMIN | 抛出 PermissionDeniedException |
| `get_featured_content_detail_admin` | content_id 不存在 | 抛出 NotFoundException |

### 4.3 API 增量

| 端点 | 场景 | HTTP | 业务码 |
|------|------|------|--------|
| GET /api/v1/featured-content/admin/{content_id} | 管理员、有效 content_id | 200 | - |
| 同上 | 无 Token | 401 | - |
| 同上 | REGULAR Token | 403 | 3002 |
| 同上 | 不存在的 content_id | 404 | 2001 |

---

## 5. Mock 与测试数据策略

- **Service 层**：`patch('app.services.homepage_search_service.crud')`，`crud.get_featured_content_by_id = AsyncMock(return_value=...)`；权限测试不 Mock 权限，传 REGULAR 触发 PermissionDeniedException；不存在测试 `return_value=None`。
- **API 层**：使用真实数据库与现有 `admin_user_token`、`regular_user_token`；先通过 POST 创建焦点图取得 `content_id`，再请求 GET 详情；不存在用例使用 `uuid.uuid4()` 作为不存在的 ID。
- **角色**：从 conftest 读取，如 `admin_user_role` 为 `"ADMIN"`，禁止臆造角色名。

---

## 6. 依赖文件清单（生成前必须全部读取）

**核心代码**：
- `backend/live_core_service/app/models/homepage_search.py`
- `backend/live_core_service/app/schemas/homepage_search.py`
- `backend/live_core_service/app/crud/homepage_search.py`
- `backend/live_core_service/app/services/homepage_search_service.py`
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`

**测试与配置**：
- `backend/live_core_service/tests/conftest.py`
- `backend/live_core_service/tests/unit/test_service_homepage_search.py`
- `backend/live_core_service/tests/integration/test_api_homepage_search.py`

---

## 7. 具体任务列表（按顺序生成并追加）

### CRUD 层

无。不新增 CRUD 测试。

### Service 层（追加到 `tests/unit/test_service_homepage_search.py`）

1. **test_get_featured_content_detail_admin_success**  
   管理员角色，Mock `crud.get_featured_content_by_id` 返回单条焦点图对象；调用 `get_featured_content_detail_admin`；断言 `result["code"] == 200`，`result["data"]` 为单条且含 id/title/image_url 等字段。

2. **test_get_featured_content_detail_admin_permission_denied**  
   传入 `role="REGULAR"`；调用 `get_featured_content_detail_admin`；断言 `pytest.raises(PermissionDeniedException)`。

3. **test_get_featured_content_detail_admin_not_found**  
   Mock `crud.get_featured_content_by_id` 返回 `None`；调用 `get_featured_content_detail_admin`；断言 `pytest.raises(NotFoundException)`。

### API 层（追加到 `tests/integration/test_api_homepage_search.py`）

4. **test_get_featured_content_detail_admin_api_success**  
   使用 `async_client`、`admin_user_token`；先 POST 创建一条焦点图，取 `content_id`；GET `/api/v1/featured-content/admin/{content_id}`；断言 200，`data` 为单条且含 id、title、image_url 等。

5. **test_get_featured_content_detail_admin_api_unauthorized**  
   无 Authorization header；GET `/api/v1/featured-content/admin/{有效UUID}`；断言 401。

6. **test_get_featured_content_detail_admin_api_permission_denied**  
   使用 `regular_user_token`；GET `/api/v1/featured-content/admin/{有效UUID}`（可先创建一条取 id）；断言 403，业务码 3002。

7. **test_get_featured_content_detail_admin_api_not_found**  
   使用 `admin_user_token`；GET `/api/v1/featured-content/admin/{不存在的UUID}`；断言 404，业务码 2001。

---

## 8. 质量标准与自检清单

- [ ] 4 步执行顺序已遵守（读 Model → Schema → CRUD/Service/API → 再生成）
- [ ] 仅追加新测试函数，未修改/删除已有测试与 conftest 已有内容
- [ ] Service 层被测方法签名与源码一致（`get_featured_content_detail_admin(self, db, content_id, current_user_id, role)`）
- [ ] Service 层 Mock 覆盖 `crud.get_featured_content_by_id`；`db` 为 `AsyncMock()`
- [ ] API 层使用 `async for client in async_client:` 及现有 token fixture
- [ ] 角色从 conftest 读取（ADMIN/REGULAR），未臆造
- [ ] 权限顺序与设计一致：401 → 403 → 404
- [ ] 使用 `unittest.mock.ANY`，未使用 `pytest.any`；未使用类式测试

---

**文档结束。执行者须先读取 Section 6 全部依赖，再按 Section 7 逐项追加增量测试代码。**
