# 内容管理模块增量开发 - 测试代码生成提示词（Categories 与 Tags 列表搜索能力补齐）

**基于**：主设计文档《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》、增量设计文档《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories与Tags列表搜索能力补齐.md》  
**既有测试提示词**：《内容管理模块增量开发_测试代码生成提示词.md》（直播间与分类多对多）  
**CRUD/Service 增量提示词**：《内容管理模块增量开发-Categories与Tags列表搜索能力补齐-CRUD层代码生成提示词.md》、《内容管理模块增量开发-Categories与Tags列表搜索能力补齐-Service层和API层代码生成提示词.md》  
**运行模式**：合并模式（先生成本提示词，再按 Section 6/7 生成并追加增量测试代码）

---

## 1. 角色定义与测试模式（执行者）

你是一名资深 Python 测试架构师，使用 `pytest`、`pytest-asyncio`、`httpx`、`pytest-mock`，遵循「混合测试策略」。

### 增量测试模式

- **测试模式**：**增量测试生成模式**（仅新增 Categories 与 Tags 列表搜索相关测试，不修改既有 Tags/Categories/Session_Tags/Live_Room_Categories 测试）。
- **模块范围**：本次仅覆盖 **列表搜索能力补齐**：CRUD（`get_categories_paginated`、`get_tags` 的 `q`/`search_type` 行为）、Service（`get_categories_paginated`、`get_tags_list` 传参）、API（GET /api/v1/content/categories/admin、GET /api/v1/content/tags 的 Query `q`、`search_type` 及 UUID 校验 400）。
- **严禁**修改已存在的测试函数与 conftest 已有内容；**只追加**新测试函数。conftest 仅允许**添加**新 Fixture/变量/导入，且须做冲突检查。
- **增量数据库验证**：记录测试前基线（count/ids），只验证增量变化。

你必须**先读取** Section 6 所列依赖文件的完整内容，再按 Section 7 逐项生成并**追加**到已有测试文件中。

**生成前强制 4 步**：1）读取 Model；2）读取 Schema；3）读取 CRUD/Service/API；4）再生成测试代码。禁止猜测字段名、函数签名、路由。

---

## 2. 核心测试哲学（继承测试母版）

| 测试目标层级 | 强制测试风格 | 核心工具 | 验证目标 |
|-------------|-------------|----------|----------|
| API 层 | 实用派 | httpx.AsyncClient + db_session + async_session_factory | HTTP 状态码、JSON（code/message/data）、真实 DB 状态（用新会话查询） |
| Service 层 | 学院派 | mocker（Mock CRUD/I/O） | 权限检查、数据编排、异常抛出、参数下传 |
| CRUD 层 | 实用派 | db_session（真实 DB） | 通过 refresh 或再次查询证明条件（q/search_type）生效 |

---

## 3. 核心实现规范（继承既有测试提示词与测试母版）

- **3.1** 测试环境：conftest 已有 `db_session`、`async_client`、`async_session_factory`；增量模式仅允许添加新 Fixture，禁止修改/删除已有内容。
- **3.2** 所有用例遵循 Arrange-Act-Assert，并用注释分段。
- **3.3** 使用 `async for db in db_session:`、`async for client in async_client:` 解包，禁止直接使用 fixture 参数。
- **3.4** **函数式测试**：禁止类式测试（`class TestXXX:`），**本次追加的测试一律为模块级函数**（与母版一致；若现有文件含类，新测试追加在文件末尾为独立函数）。
- **3.5** 外键：禁止用 `uuid.uuid4()` 作为外键；先创建父对象再用其 id。
- **3.6** 唯一字段使用 Faker 或 `uuid.uuid4().hex[:8]`，禁止硬编码（如 Tag.name、Category.name）。
- **3.7** 增量验证：创建前记录 count/ids，创建后断言增量；列表断言新 id 或过滤结果符合 q/search_type。
- **3.8** Service 层：`db` 使用 `AsyncMock()`；CRUD 使用 `mocker.patch(..., new_callable=AsyncMock)`；Mock 路径为 `app.crud.content_management.xxx`。
- **3.9** 默认不 `commit`；仅唯一性/级联/外键测试可 commit。
- **3.10** 角色枚举：从 conftest 或设计文档读取，使用 **REGULAR**、**ADMIN**、**SUPERADMIN**（大写），禁止臆造 USER、GUEST。
- **3.11** 权限检查顺序：参数验证 400 → 资源存在/可见 404 → 权限 403；测试断言顺序与之一致。
- **3.12** 测试工具：使用 `from unittest.mock import AsyncMock, Mock, patch, ANY`，禁止使用 `pytest.any`。

---

## 4. 测试用例规划（仅增量：列表搜索）

### 4.1 CRUD 增量

- **get_categories_paginated(db, page, size, is_active, current_user_id, role, q, search_type)**  
  - 无 q：行为与现有一致（分页、is_active）。  
  - q=合法 UUID + search_type=id：返回至多一条，id 匹配；total 与 items 一致。  
  - q=关键词 + search_type=keyword 或未传：对 name 模糊，分页与 total 一致。  
  - 同一套 WHERE 用于 count 与分页列表。
- **get_tags(db, is_active, current_user_id, role, q, search_type)**  
  - 无 q：行为与现有一致。  
  - q=合法 UUID + search_type=id：返回至多一条。  
  - q=关键词：对 name 模糊。

### 4.2 Service 增量

- **get_categories_paginated**：传 q、search_type 给 CRUD；Mock CRUD 时断言被调用参数含 q、search_type。
- **get_tags_list**：传 q、search_type 给 CRUD；同上。

### 4.3 API 增量

- **GET /api/v1/content/categories/admin**  
  - 无 q：与现有一致（200，分页）。  
  - q=合法 UUID + search_type=id：200，data.items 至多一条且 id 匹配。  
  - q=关键词：200，data.items 为 name 模糊结果。  
  - q=非法字符串 + search_type=id：400，code 4001。
- **GET /api/v1/content/tags**  
  - 无 q：与现有一致。  
  - q=合法 UUID + search_type=id：200，data 至多一条。  
  - q=关键词：200，data 为 name 模糊结果。  
  - q=非法 UUID + search_type=id：400，code 4001。

---

## 5. Mock 策略与测试数据策略

- **CRUD**：真实 db_session，创建 Tag/Category 时 name 用唯一后缀；验证时用真实 CRUD 调用。
- **Service**：Mock `app.crud.content_management.get_categories_paginated`、`get_tags`；断言调用时带 `q=`、`search_type=`。
- **API**：真实 DB + AsyncClient；创建数据后带 Query `q`、`search_type` 请求；断言 status_code、code、data 结构及条数/内容。
- **UUID 校验**：API 层测试传 `search_type=id` 且 `q=not-a-uuid` 时断言 400、code 4001。

---

## 6. 依赖文件清单（必须读取后再生成）

生成测试代码前，**必须**用 `read_file` 读取以下文件完整内容。

**核心代码**：
- `backend/live_core_service/app/models/content_management.py` — Category、Tag 字段
- `backend/live_core_service/app/schemas/content_management.py` — CategoryAdminListResponse、TagListResponse、CategoryItem、TagItem
- `backend/live_core_service/app/crud/content_management.py` — get_categories_paginated、get_tags 签名及 q/search_type 逻辑，CATEGORY_LIST_SEARCH_FIELDS、TAGS_LIST_SEARCH_FIELDS
- `backend/live_core_service/app/services/content_management_service.py` — get_categories_paginated、get_tags_list 签名及下传 q/search_type
- `backend/live_core_service/app/api/v1/endpoints/content_management.py` — get_categories_admin、get_tags 的 Query 参数与 UUID 校验
- `backend/live_core_service/app/api/v1/api.py` — content 路由 prefix

**测试与依赖**：
- `backend/live_core_service/tests/conftest.py` — db_session、async_client、admin_user_token、regular_user_token 等
- `backend/live_core_service/tests/unit/test_crud_content_management.py` — 现有风格与辅助函数（create_test_session、create_test_room 等）
- `backend/live_core_service/tests/unit/test_service_content_management.py` — Mock 写法与 patch 路径
- `backend/live_core_service/tests/integration/test_api_content_management.py` — 请求头、路径、断言风格
- `backend/live_core_service/app/core/deps.py` — get_current_user、get_current_user_optional

---

## 7. 具体测试任务列表（仅增量：Categories 与 Tags 列表搜索）

以下测试**追加**到已有文件，不修改已有用例。**一律使用模块级函数**（不放在 class 内）。

### A. CRUD 层（追加到 `tests/unit/test_crud_content_management.py`）

- **get_categories_paginated（q/search_type）**  
  - `test_get_categories_paginated_with_q_keyword_returns_name_match`：创建 2 个 Category（name 含不同关键词），调用 get_categories_paginated(..., q="某关键词", search_type="keyword")，断言返回的 items 仅含 name 匹配的项，total 与 items 一致。  
  - `test_get_categories_paginated_with_q_id_returns_single`：创建 1 个 Category，调用 get_categories_paginated(..., q=str(category.id), search_type="id")，断言 len(items)==1 且 items[0].id==category.id，total==1。  
  - `test_get_categories_paginated_without_q_unchanged`：行为与无 q 时一致（分页、is_active 过滤）。
- **get_tags（q/search_type）**  
  - `test_get_tags_with_q_keyword_returns_name_match`：创建 2 个 Tag，调用 get_tags(..., q="某关键词", search_type="keyword")，断言返回列表仅含 name 匹配的。  
  - `test_get_tags_with_q_id_returns_single`：创建 1 个 Tag，调用 get_tags(..., q=str(tag.id), search_type="id")，断言 len==1 且 id 匹配。  
  - `test_get_tags_without_q_unchanged`：无 q 时行为与现有一致。

### B. Service 层（追加到 `tests/unit/test_service_content_management.py`）

- **get_categories_paginated**  
  - `test_get_categories_paginated_passes_q_and_search_type_to_crud`：Mock get_categories_paginated，调用 service.get_categories_paginated(..., q="x", search_type="id")，assert mock 被调用时含 q="x", search_type="id"。
- **get_tags_list**  
  - `test_get_tags_list_passes_q_and_search_type_to_crud`：Mock get_tags，调用 service.get_tags_list(..., q="y", search_type="keyword")，assert mock 被调用时含 q="y", search_type="keyword"。

### C. API 层（追加到 `tests/integration/test_api_content_management.py`）

- **GET /api/v1/content/categories/admin**  
  - `test_api_categories_admin_q_invalid_uuid_returns_400`：带 admin token，GET `/api/v1/content/categories/admin?q=not-a-uuid&search_type=id`，断言 status_code==400，body code==4001。  
  - `test_api_categories_admin_q_valid_uuid_returns_match`：创建 1 个 Category，GET `?q={category.id}&search_type=id`，断言 200，data.items 长度为 1 且 id 匹配。  
  - `test_api_categories_admin_q_keyword_filters_by_name`：创建 2 个 Category（name 一个含 "肝胆"，一个含 "骨科"），GET `?q=肝胆&search_type=keyword`（或未传 search_type），断言 200，data.items 仅含 name 含 "肝胆" 的。
- **GET /api/v1/content/tags**  
  - `test_api_tags_q_invalid_uuid_returns_400`：GET `/api/v1/content/tags?q=invalid&search_type=id`，断言 400，code 4001。  
  - `test_api_tags_q_valid_uuid_returns_match`：创建 1 个 Tag，GET `?q={tag.id}&search_type=id`，断言 200，data 长度为 1 且 id 匹配。  
  - `test_api_tags_q_keyword_filters_by_name`：创建 2 个 Tag（name 不同），GET `?q=某词`，断言 200，data 仅含 name 匹配的。

---

## 8. 质量标准与生成后验证检查清单

**交付物**：  
- 在 `tests/unit/test_crud_content_management.py` 末尾**追加**列表搜索相关 CRUD 测试函数。  
- 在 `tests/unit/test_service_content_management.py` 末尾**追加**列表搜索相关 Service 测试函数。  
- 在 `tests/integration/test_api_content_management.py` 末尾**追加**列表搜索相关 API 测试函数。

**指令**：  
1. 先读取 Section 6 全部依赖文件再生成。  
2. 仅追加新函数，不修改、不删除已有测试与 conftest 已有内容。  
3. 新测试遵循 Section 2–5（async for、函数式、Arrange-Act-Assert、增量验证、Mock 规范）。  
4. 角色名使用 REGULAR/ADMIN/SUPERADMIN；API 路径为 `/api/v1/content/categories/admin`、`/api/v1/content/tags`。

**生成后自检**：  
- [ ] 4 步执行顺序已执行（读 Model → Schema → CRUD/Service/API → 生成）。  
- [ ] 所有新增测试均使用 `async for` 解包 db_session/async_client。  
- [ ] 未使用类式测试；未修改已有测试或 conftest 已有项。  
- [ ] CRUD/API 中涉及数量或列表的用例使用增量验证或明确过滤预期。  
- [ ] Service Mock 断言调用参数含 q、search_type。  
- [ ] API 层 400 用例（非法 UUID + search_type=id）已覆盖，断言 code 4001。  
- [ ] 与现有测试风格一致（命名 test_xxx_yyy、Arrange-Act-Assert 注释）。

**文档结束。合并模式下，执行者应在同一流程内根据 Section 6 读取依赖并按 Section 7 逐项生成并追加测试代码。**
