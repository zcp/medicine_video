# homepage_search 模块增量开发 - 测试代码生成提示词（焦点图列表搜索与图片上传）

**模块名称**: homepage_search  
**测试模式**: incremental（增量测试生成模式）  
**增量主题**: 焦点图列表搜索（q/search_type）与图片上传  
**设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`  
**增量设计文档**: `docs/03_系统设计/首页与搜索模块增量开发设计文档-焦点图列表搜索与图片上传.md`

---

## 1. 角色定义与测试模式（执行者）

你是一名资深的 Python 测试架构师，精通 pytest、pytest-asyncio、httpx，并遵循「混合测试策略」。

**测试模式**：**增量测试生成模式**  
**说明**：为 homepage_search 模块**新增**测试代码，在已有测试基础上增量生成。**严禁修改**已存在的测试函数；**不修改** conftest.py 已有内容（仅允许在无冲突时新增 Fixture）。

**强制要求（生成测试代码前必须按顺序执行）**：

1. **第一步**：使用 `read_file` 读取 Section 6 所列**所有** Model、Schema 文件，提取字段与验证规则。  
2. **第二步**：读取 Section 6 所列 CRUD、Service、API 文件，提取**函数/方法/端点签名**（禁止凭记忆推断）。  
3. **第三步**：读取 `tests/conftest.py` 及现有模块测试文件，确认 Fixture 名称（如 `admin_user_token`、`regular_user_token`）、角色枚举（如 REGULAR、ADMIN）、`async for` 用法。  
4. **第四步**：按 Section 7 任务列表**仅追加**新测试函数，不修改、不删除已有测试。

---

## 2. 核心测试哲学（混合策略）

| 测试目标层级 | 强制测试风格 | 核心工具 | 验证目标 |
|-------------|-------------|----------|----------|
| **API / Endpoint 层** | 实用派 (Pragmatic) | httpx.AsyncClient + db_session | 完整链路：HTTP 状态码、JSON 响应、必要时数据库状态（新会话查询） |
| **Service 层** | 学院派 (Academic) | Mock CRUD / FileHandler | 权限、编排、异常抛出 |
| **CRUD 层** | 实用派 (Pragmatic) | db_session（真实 DB） | 查询条件、排序、count/list 一致性 |

---

## 3. 核心实现规范（必须继承）

- **3.1 测试环境**：conftest 优先不修改；新增 Fixture 前做冲突检查；必要时在测试文件内定义局部 Fixture。  
- **3.2 结构**：Arrange-Act-Assert，注释分节。  
- **3.3 异步**：`db_session`、`async_client` 必须 `async for x in fixture:` 解包。  
- **3.4 事务**：默认不 `commit`；仅唯一性/级联等例外场景可 commit。  
- **3.5 数据**：唯一字段用 Faker/uuid；外键必须先创建父对象；**禁止**用随机 UUID 作外键。  
- **3.6 函数式测试**：禁止类式测试（`class TestXXX:`）。  
- **3.7 Mock**：Service 层 `db = AsyncMock()`；CRUD 用 `new_callable=AsyncMock`；**禁止**用 MagicMock 模拟 Model，使用真实 Model 类构造 Mock 数据。  
- **3.8 动态读取**：字段名、函数签名、路由、角色名均从 Section 6 文件读取，禁止猜测。  
- **3.9 角色与权限**：角色名从 conftest 或主设计文档提取（如 REGULAR、ADMIN、SUPERADMIN）；权限顺序：参数 400 → 资源 404 → 权限 403。  
- **3.10 增量数据库验证**：记录测试前基线（count/ids），断言仅验证增量（如 count+1、新 ID 在结果中）。  
- **3.11 排序敏感**：分页查询中需断言「新建记录出现在结果中」时，创建数据显式设 `sort_order=0`。  
- **3.12 测试工具**：使用 `unittest.mock.ANY`，不用 `pytest.any`。

---

## 4. 测试用例规划（仅增量部分）

### 4.1 CRUD 增量

- **修改函数**：`get_featured_content_list_paginated(db, page, size, q, search_type)`  
- **用例方向**：q 为空时不加条件；search_type=id 且 q 为合法 UUID 时按 id 精确；否则 q 非空时 title/subtitle 模糊；排序 sort_order ASC, created_at DESC；count 与 list 共用同一 where 条件。

### 4.2 Service 增量

- **修改方法**：`get_featured_content_list_admin_paginated(..., q, search_type)` — 透传 CRUD。  
- **新增方法**：`upload_featured_content_image(db, content_id, file, current_user_id, role)` — 权限、存在性、FileHandler、更新 image_url、返回含 data 的 dict。

### 4.3 API 增量

- **修改端点**：`GET /api/v1/admin/featured-content` — 新增 Query `q`、`search_type`；search_type=id 且 q 非空时校验 UUID，非法返回 400（4001）。  
- **新增端点**：`POST /api/v1/admin/featured-content/{content_id}/image` — multipart 上传；成功 200、data 含焦点图信息及 image_url；403/404/400/500 与设计一致。

---

## 5. Mock 与测试数据策略

- **CRUD**：真实 DB，使用 `create_test_featured_content_in_db` 等辅助函数，`sort_order=0` 保证分页可见。  
- **Service**：Mock `crud` 与 `FileHandler`；`db = AsyncMock()`；返回值与 Service 实际返回结构一致（从源码读取）。  
- **API**：真实 DB + 真实 HTTP；使用 conftest 的 `admin_user_token`、`regular_user_token`；上传接口使用 `httpx` 的 multipart 构造（如 `files={"image": ("x.jpg", content, "image/jpeg")}`）。

---

## 6. 依赖文件清单（必须全部读取后再生成）

生成任何测试代码前，**必须**用 `read_file` 读取以下文件：

**核心代码**  
- `backend/live_core_service/app/models/homepage_search.py`  
- `backend/live_core_service/app/schemas/homepage_search.py`  
- `backend/live_core_service/app/crud/homepage_search.py`  
- `backend/live_core_service/app/services/homepage_search_service.py`  
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`  
- `backend/live_core_service/app/core/file_handler.py`（焦点图图片方法）  
- `backend/live_core_service/app/api/v1/api.py`（路由注册）  
- `backend/live_core_service/app/core/deps.py`（get_current_user）  
- `backend/live_core_service/app/core/response.py`（error_response）  
- `backend/live_core_service/app/exceptions.py`（NotFoundException 等）

**测试相关**  
- `backend/live_core_service/tests/conftest.py`  
- `backend/live_core_service/tests/unit/test_crud_homepage_search.py`  
- `backend/live_core_service/tests/unit/test_service_homepage_search.py`  
- `backend/live_core_service/tests/integration/test_api_homepage_search.py`

---

## 7. 具体任务列表（仅追加以下新测试函数）

### CRUD 层（追加到 `tests/unit/test_crud_homepage_search.py`）

| 序号 | 测试函数名 | 说明 |
|-----|-----------|------|
| 1 | `test_get_featured_content_list_paginated_with_q_empty` | q 为空时返回全部，total 与 items 一致 |
| 2 | `test_get_featured_content_list_paginated_with_search_type_id` | search_type=id、q 为合法 UUID 时仅返回该条 |
| 3 | `test_get_featured_content_list_paginated_with_search_type_name` | q 非空、非 id 时按 title/subtitle 模糊匹配 |
| 4 | `test_get_featured_content_list_paginated_sort_order` | 排序为 sort_order ASC、created_at DESC |

### Service 层（追加到 `tests/unit/test_service_homepage_search.py`）

| 序号 | 测试函数名 | 说明 |
|-----|-----------|------|
| 5 | `test_get_featured_content_list_admin_paginated_passes_q_and_search_type` | 调用 CRUD 时传入 q、search_type |
| 6 | `test_upload_featured_content_image_success` | Mock FileHandler 与 CRUD，断言 200 及 data 含 image_url |
| 7 | `test_upload_featured_content_image_permission_denied` | 非 ADMIN/SUPERADMIN 抛出 PermissionDeniedException |
| 8 | `test_upload_featured_content_image_not_found` | content_id 不存在时抛出 NotFoundException |

### API 层（追加到 `tests/integration/test_api_homepage_search.py`）

| 序号 | 测试函数名 | 说明 |
|-----|-----------|------|
| 9 | `test_get_admin_featured_content_paginated_with_q_empty` | 带 q 空或不传，返回分页正常 |
| 10 | `test_get_admin_featured_content_paginated_with_search_type_id_valid` | q=有效 UUID、search_type=id，返回对应条 |
| 11 | `test_get_admin_featured_content_paginated_with_search_type_id_invalid_returns_400` | search_type=id、q 非 UUID，返回 400、code 4001 |
| 12 | `test_get_admin_featured_content_paginated_with_search_type_name` | q 有值、search_type 非 id，标题/副标题模糊 |
| 13 | `test_upload_featured_content_image_api_success` | Admin Token + 合法 content_id + 合法图片，200，data 含 image_url，DB 中 image_url 已更新 |
| 14 | `test_upload_featured_content_image_api_permission_denied` | 普通用户 Token，403、3002 |
| 15 | `test_upload_featured_content_image_api_not_found` | 不存在的 content_id，404、2001 |
| 16 | `test_upload_featured_content_image_api_bad_file_returns_400` | 非法类型或缺失文件，400、4001 |

---

## 8. 质量标准与生成后验证检查清单

- [ ] 已按 4 步顺序读取 Section 6 全部依赖再生成。  
- [ ] 混合策略：API 实用派、Service 学院派、CRUD 实用派已区分。  
- [ ] 使用 `async for` 解包 db_session / async_client。  
- [ ] 函数式测试，无类式测试。  
- [ ] Service 层 db 为 AsyncMock；未用 MagicMock 模拟 Model。  
- [ ] 默认不 commit；外键先建父对象；唯一字段用 Faker/uuid。  
- [ ] 仅追加 Section 7 所列新函数，未修改/删除已有测试与 conftest 已有内容。  
- [ ] 增量验证用基线+增量方式，未依赖绝对总数。  
- [ ] 角色名来自 conftest/设计文档（REGULAR、ADMIN），未臆造。  
- [ ] search_type=id 且 q 非法时断言 400/4001。  
- [ ] Service 层方法签名与调用从源码读取一致。  
- [ ] 上传成功用例中断言响应与数据库 image_url 更新。

---

**文档结束。执行者须先完成 Section 6 读取，再按 Section 7 逐项追加测试函数。**
