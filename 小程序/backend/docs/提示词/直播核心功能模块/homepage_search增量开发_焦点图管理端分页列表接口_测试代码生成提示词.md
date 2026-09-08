# homepage_search 增量开发 - 测试代码生成提示词（焦点图管理端分页列表）

**版本**: 增量版  
**模块名称**: 首页与搜索模块 (homepage_search)  
**测试模式**: **incremental（增量测试生成模式）**  
**增量主题**: 管理端焦点图分页列表接口（GET /api/v1/admin/featured-content）  
**对应设计文档**:
- 主设计文档：`docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`
- 增量设计文档：`docs/03_系统设计/首页与搜索模块增量开发设计文档-焦点图管理端分页列表接口.md`

---

## 1. 角色定义与测试模式

你是一名资深的 Python 测试架构师，精通 pytest、pytest-asyncio、httpx，并熟悉本项目的测试基建（conftest.py）与《测试代码生成提示词母版》中的测试哲学与规范。

- **测试模式**: 增量测试生成模式（incremental）
- **本次增量范围**: 仅针对「管理端焦点图分页列表」：CRUD `get_featured_content_list_paginated`、Service `get_featured_content_list_admin_paginated`、API `GET /api/v1/admin/featured-content`。
- **强制要求**: 生成任何测试代码前，**必须**按 Section 6 依赖清单**依次读取**所有依赖文件；禁止猜测字段名、函数签名、路由路径。

**4 步执行顺序（不可跳过）**：
1. 读取 Model/Schema（homepage_search）；
2. 读取 CRUD/Service/API 代码（homepage_search、api.py）；
3. 读取 conftest.py 及现有测试文件（test_crud_homepage_search、test_service_homepage_search、test_api_homepage_search）；
4. 再生成测试代码，且仅**追加**新测试函数，不修改已有测试与 conftest 已有内容。

---

## 2. 核心测试哲学（混合策略）

| 测试层级           | 风格            | 核心工具                         | 目标                                                   |
|--------------------|-----------------|----------------------------------|--------------------------------------------------------|
| CRUD 层            | 实用派          | 真实 DB                          | 验证 get_featured_content_list_paginated 分页与总数   |
| Service 层         | 学院派          | AsyncMock + Mock CRUD            | 隔离 get_featured_content_list_admin_paginated，验证返回与权限 |
| API / Endpoint 层  | 实用派（端到端）| async_client + db_session       | 验证 GET /api/v1/admin/featured-content 状态码、分页结构、权限 |

---

## 3. 核心实现规范（继承测试母版）

- **函数式测试**：禁止类式测试，所有测试函数直接定义在模块级别。
- **async for 解包**：`async for db in db_session`、`async for client in async_client`。
- **Service 层 Mock**：`db` 使用 `AsyncMock()`；`crud.get_featured_content_list_paginated` 使用 `patch(..., new_callable=AsyncMock)`；调用链上被调用的 CRUD 须 Mock。
- **事务**：测试函数内默认不 `commit`；CRUD 测试若需验证分页结果与总数，使用增量方式（记录基线后创建数据再断言）。
- **API 用户身份**：管理员接口使用 `admin_user_token`，权限不足用例使用 `regular_user_token`；无 Token 断言 401。
- **分页响应**：断言 `data.total`、`data.page`、`data.size`、`data.items` 存在且类型正确；items 为列表且元素含 FeaturedContentItem 字段（id、title、is_active 等）。

---

## 4. 测试用例规划（仅增量）

### 4.1 CRUD 层增量（get_featured_content_list_paginated）

| 测试函数名 | 场景 | 预期 |
|------------|------|------|
| `test_get_featured_content_list_paginated_returns_page_and_total` | 库中有 0 条或若干条，调用 page=1, size=10 | 返回 (list, total)，len(list) <= 10，total >= 0 |
| `test_get_featured_content_list_paginated_respects_page_size` | 创建至少 2 条，page=1, size=1 | len(items)==1, total>=2 |
| `test_get_featured_content_list_paginated_orders_by_sort_order` | 创建 2 条（sort_order 不同），page=1, size=10 | 结果按 sort_order 升序 |

### 4.2 Service 层增量（get_featured_content_list_admin_paginated）

| 测试函数名 | 场景 | 预期 |
|------------|------|------|
| `test_get_featured_content_list_admin_paginated_success` | Mock crud.get_featured_content_list_paginated 返回 ([item], 1)，role=ADMIN | 200，data.total==1, data.page, data.size, data.items 长度 1 |
| `test_get_featured_content_list_admin_paginated_permission_denied` | role=REGULAR | 抛出 PermissionDeniedException |

**Mock 要点**：`get_featured_content_list_admin_paginated` 内先 `_check_admin_permission(role)`，再调 `crud.get_featured_content_list_paginated(db, page, size)`；须 Mock `crud.get_featured_content_list_paginated`，返回 `(list_of_featured_content_objects, total)`。

### 4.3 API 层增量（GET /api/v1/admin/featured-content）

| 测试函数名 | 场景 | 预期 |
|------------|------|------|
| `test_get_admin_featured_content_paginated_success` | 带 admin_user_token，GET /api/v1/admin/featured-content?page=1&size=10 | 200，code==200，data 含 total/page/size/items |
| `test_get_admin_featured_content_paginated_permission_denied` | 带 regular_user_token | 403，code==3002 |
| `test_get_admin_featured_content_paginated_unauthorized` | 无 Authorization | 401 |

---

## 5. Mock 与测试数据策略

- **CRUD**：使用现有 `create_test_featured_content_in_db` 或 `create_test_featured_content_data`；创建时设 `sort_order=0` 便于排序断言；增量验证：先查 total/列表，再创建 1 条，再查断言 total+1 或新 id 在 items 中。
- **Service**：`mock_db = AsyncMock()`；patch `app.services.homepage_search_service.crud.get_featured_content_list_paginated` 返回 `([mock_featured_content], 1)`；mock_featured_content 需可被 `FeaturedContentItem.model_validate` 使用（真实 Model 实例或具备 id/title/is_active 等属性的 Mock）。
- **API**：使用 `async_client`、`admin_user_token`、`regular_user_token`（来自 conftest）；路径为 **/api/v1/admin/featured-content**（非 /api/v1/featured-content/admin）。

---

## 6. 依赖文件清单（生成前必须读取）

- `backend/live_core_service/app/models/homepage_search.py`
- `backend/live_core_service/app/schemas/homepage_search.py`
- `backend/live_core_service/app/crud/homepage_search.py`
- `backend/live_core_service/app/services/homepage_search_service.py`
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`
- `backend/live_core_service/app/api/v1/api.py`
- `backend/live_core_service/app/core/deps.py`
- `backend/live_core_service/tests/conftest.py`
- `backend/live_core_service/tests/unit/test_crud_homepage_search.py`
- `backend/live_core_service/tests/unit/test_service_homepage_search.py`
- `backend/live_core_service/tests/integration/test_api_homepage_search.py`

---

## 7. 任务列表（仅追加以下测试函数）

**CRUD 层**（追加到 `tests/unit/test_crud_homepage_search.py`）：

1. `test_get_featured_content_list_paginated_returns_page_and_total` — 调用 `get_featured_content_list_paginated(db, page=1, size=10)`，断言返回元组 (list, int)，len(list) <= 10。
2. `test_get_featured_content_list_paginated_respects_page_size` — 使用 `create_test_featured_content_in_db` 创建至少 2 条（sort_order=0），调用 page=1, size=1，断言 len(items)==1, total>=2。
3. `test_get_featured_content_list_paginated_orders_by_sort_order` — 创建 2 条 sort_order=10 与 sort_order=0，调用 page=1, size=10，断言 items[0].sort_order <= items[1].sort_order。

**Service 层**（追加到 `tests/unit/test_service_homepage_search.py`）：

4. `test_get_featured_content_list_admin_paginated_success` — Mock `crud.get_featured_content_list_paginated` 返回 ([mock_content], 1)，role=ADMIN，断言 result["code"]==200，result["data"]["total"]==1，result["data"]["items"] 长度为 1。
5. `test_get_featured_content_list_admin_paginated_permission_denied` — role=REGULAR，断言 pytest.raises(PermissionDeniedException)。

**API 层**（追加到 `tests/integration/test_api_homepage_search.py`）：

6. `test_get_admin_featured_content_paginated_success` — GET /api/v1/admin/featured-content?page=1&size=10，headers admin_user_token，断言 200、data.total、data.page、data.size、data.items 为 list。
7. `test_get_admin_featured_content_paginated_permission_denied` — GET 同路径，headers regular_user_token，断言 403、body code 3002。
8. `test_get_admin_featured_content_paginated_unauthorized` — GET 同路径，无 Authorization，断言 401。

---

## 8. 质量标准与自检清单

- [ ] 仅追加新测试函数，未修改、删除已有测试及 conftest 已有内容。
- [ ] CRUD 测试使用 `async for db in db_session`，使用现有辅助函数创建数据，分页断言不依赖「第 0 条一定是刚创建的」（可断言 total 或 id 集合）。
- [ ] Service 测试：`get_featured_content_list_paginated` 已 Mock，返回 (list, total)；方法签名与源码一致（db, page, size）。
- [ ] API 测试：路径为 **/api/v1/admin/featured-content**；使用 async for client in async_client；管理员用例带 admin_user_token。
- [ ] 与现有 test_crud_homepage_search、test_service_homepage_search、test_api_homepage_search 风格一致（函数式、命名、Arrange-Act-Assert）。
- [ ] 角色枚举从 conftest 或设计文档读取（ADMIN、REGULAR），不臆造。

---

**文档结束。合并模式下，执行者应在同一流程内根据 Section 6 读取依赖并按 Section 7 逐项生成并追加测试代码。**
