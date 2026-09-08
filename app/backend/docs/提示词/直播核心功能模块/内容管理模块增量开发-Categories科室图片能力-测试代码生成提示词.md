# 内容管理模块增量开发 - 测试代码生成提示词（Categories 科室图片能力）

**基于**：主设计文档《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》、增量设计文档《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力.md》  
**既有测试提示词**：《内容管理模块增量开发_测试代码生成提示词.md》（直播间与分类多对多）  
**Service/API 增量提示词**：《内容管理模块增量开发-Categories科室图片能力-Service层和API层代码生成提示词.md》  
**运行模式**：合并模式（先生成本提示词，再按 Section 6/7 生成并追加增量测试代码）

---

## 1. 角色定义与测试模式（执行者）

你是一名资深 Python 测试架构师，使用 `pytest`、`pytest-asyncio`、`httpx`、`pytest-mock`，遵循「混合测试策略」。

### 增量测试模式

- **测试模式**：**增量测试生成模式**（仅新增 Categories 科室图片上传/删除相关测试，不修改既有 Tags/Categories/Session_Tags/Live_Room_Categories 测试）。
- **模块范围**：本次仅覆盖 **科室图片能力**：Service（upload_category_icon、delete_category_icon）、API（POST /api/v1/content/categories/{category_id}/icon、DELETE /api/v1/content/categories/{category_id}/icon）。CRUD 无新增函数，仅通过既有 update_category 更新 icon，不单独为 CRUD 增测。
- **严禁**修改已存在的测试函数与 conftest 已有内容；**只追加**新测试函数。conftest 仅允许**添加**新 Fixture/变量/导入，且须做冲突检查。
- **增量数据库验证**：上传后通过新会话查询 category.icon 或 refresh 验证；删除后验证 icon 为 null。

你必须**先读取** Section 6 所列依赖文件的完整内容，再按 Section 7 逐项生成并**追加**到已有测试文件中。

**生成前强制 4 步**：1）读取 Model；2）读取 Schema；3）读取 CRUD/Service/API/FileHandler；4）再生成测试代码。禁止猜测字段名、函数签名、路由。

---

## 2. 核心测试哲学（继承测试母版）

| 测试目标层级 | 强制测试风格 | 核心工具 | 验证目标 |
|-------------|-------------|----------|----------|
| API 层 | 实用派 | httpx.AsyncClient + db_session | HTTP 状态码、响应 JSON（含 icon 或 message）、真实 DB 状态 |
| Service 层 | 学院派 | mocker（Mock FileHandler + CRUD） | 权限检查、调用链（get_category_by_id → delete_old → save → update_category）、异常抛出 |

---

## 3. 核心实现规范（继承既有测试提示词与测试母版）

- **3.1** 测试环境：conftest 已有 `db_session`、`async_client`；增量模式仅允许添加新 Fixture，禁止修改/删除已有内容。
- **3.2** 所有用例遵循 Arrange-Act-Assert，并用注释分段。
- **3.3** 使用 `async for db in db_session:`、`async for client in async_client:` 解包。
- **3.4** **函数式测试**：本次追加的测试一律为**模块级函数**（不放在 class 内）。
- **3.5** 外键/依赖：先创建 Category，再调用上传/删除；禁止用随机 UUID 作为 category_id 除非测试「分类不存在」。
- **3.6** 唯一字段：Category.name 使用 `uuid4().hex[:8]` 等保证唯一。
- **3.7** Service 层：`db` 使用 `AsyncMock()`；Mock `app.crud.content_management.get_category_by_id`、`update_category` 及 `app.core.file_handler.FileHandler.save_category_icon`、`delete_old_category_icon`；调用链上的 CRUD/FileHandler 均须 Mock。
- **3.8** 上传请求：API 测试使用 `files={"file": ("test.jpg", BytesIO(image_bytes), "image/jpeg")}`（与现有 expert avatar / brand logo 一致）；小图片可用 `b'\xff\xd8\xff\xe0' + b'0' * 100` 等模拟 JPEG。
- **3.9** 角色枚举：REGULAR、ADMIN、SUPERADMIN（大写）；权限 403 code 3003，不存在 404 code 2001，非法文件 400 code 4001。
- **3.10** 默认不 commit；API 测试中创建 Category 后需 commit 以便接口能读到数据（或使用 db_session 的 rollback 策略与测试顺序一致）。

---

## 4. 测试用例规划（仅增量：科室图片）

### 4.1 Service 增量

- **upload_category_icon**：Admin 成功时 Mock get_category_by_id 返回 category（可带 icon）、FileHandler.save_category_icon 返回 URL、update_category 返回 updated；断言返回 CategoryItem 且 icon 为 URL。分类不存在时 get_category_by_id 返回 None，断言 NotFoundException。非 Admin 断言 PermissionDeniedException。
- **delete_category_icon**：Admin 成功时 Mock get_category_by_id 返回 category（icon 非空）、delete_old_category_icon 不抛、update_category 返回；断言返回 dict 含 "message"。分类不存在断言 NotFoundException。非 Admin 断言 PermissionDeniedException。无 icon 时也 200（幂等），Mock icon 为空即可。

### 4.2 API 增量

- **POST /api/v1/content/categories/{category_id}/icon**  
  - 成功：创建 Category，commit；用 admin token 上传小 JPEG（BytesIO）；断言 200，响应含 icon 且以 /media/ 开头；可选：新会话查 category 的 icon 已更新。  
  - 分类不存在：用不存在的 category_id 上传；断言 404，code 2001。  
  - 非 Admin：用 regular token；断言 403，code 3003。  
  - 非法类型：上传 .txt 或 content_type 非 image；断言 400（file_handler 抛 HTTPException）。
- **DELETE /api/v1/content/categories/{category_id}/icon**  
  - 成功：创建 Category（icon 可为空或 /media/xxx），commit；用 admin token DELETE；断言 200；可选：新会话查 icon 为 null。  
  - 分类不存在：DELETE 不存在的 category_id；断言 404，code 2001。  
  - 非 Admin：用 regular token DELETE；断言 403，code 3003。  
  - 无图片（幂等）：Category 无 icon，DELETE 仍返回 200。

---

## 5. Mock 策略与测试数据策略

- **Service**：Mock `app.crud.content_management.get_category_by_id`、`update_category`；Mock `app.core.file_handler.FileHandler.delete_old_category_icon`（同步）、`FileHandler.save_category_icon`（async）。upload 时若测「已有 icon 先删再存」，则 get_category_by_id 返回的 category 带 icon 且以 /media/ 开头。
- **API**：真实 DB + AsyncClient；上传用 BytesIO 小 JPEG；删除无需 body。响应格式以实际为准：若端点返回 response_model=CategoryItem 则响应体直接为 CategoryItem（含 id、name、icon 等）；若为统一包装则 data 内为 CategoryItem。

---

## 6. 依赖文件清单（必须读取后再生成）

生成测试代码前，**必须**用 `read_file` 读取以下文件。

**核心代码**：
- `backend/live_core_service/app/models/content_management.py` — Category 及 icon 字段
- `backend/live_core_service/app/schemas/content_management.py` — CategoryItem、CategoryUpdate
- `backend/live_core_service/app/crud/content_management.py` — get_category_by_id、update_category 签名
- `backend/live_core_service/app/services/content_management_service.py` — upload_category_icon、delete_category_icon 方法签名与调用链（get_category_by_id → FileHandler → update_category）
- `backend/live_core_service/app/api/v1/endpoints/content_management.py` — POST/DELETE /categories/{category_id}/icon 路径与参数（file: File(...)）
- `backend/live_core_service/app/core/file_handler.py` — save_category_icon、delete_old_category_icon 签名
- `backend/live_core_service/app/api/v1/api.py` — content 路由 prefix

**测试与依赖**：
- `backend/live_core_service/tests/conftest.py` — db_session、async_client、admin_user_token、regular_user_token
- `backend/live_core_service/tests/unit/test_service_content_management.py` — Mock 写法与 patch 路径、service fixture
- `backend/live_core_service/tests/integration/test_api_content_management.py` — 请求头、路径、断言风格
- `backend/live_core_service/tests/integration/test_api_expert_avatar.py` — 上传 files= 与 BytesIO 用法参考
- `backend/live_core_service/app/core/deps.py` — get_current_user

---

## 7. 具体测试任务列表（仅增量：科室图片）

以下测试**追加**到已有文件，不修改已有用例。**一律使用模块级函数**。

### A. Service 层（追加到 `tests/unit/test_service_content_management.py`）

- **upload_category_icon**  
  - `test_upload_category_icon_as_admin_success`：Mock get_category_by_id 返回 Category（icon 可为 None），Mock FileHandler.save_category_icon 返回 "/media/categories/xxx/icon_1.jpg"，Mock update_category 返回该 Category；调用 upload_category_icon；断言返回 CategoryItem，icon 为上述 URL；assert save_category_icon 被调用。  
  - `test_upload_category_icon_category_not_found`：Mock get_category_by_id 返回 None；断言 raise NotFoundException。  
  - `test_upload_category_icon_permission_denied`：role 为 REGULAR；断言 raise PermissionDeniedException。
- **delete_category_icon**  
  - `test_delete_category_icon_as_admin_success`：Mock get_category_by_id 返回 Category(icon="/media/xxx")，Mock delete_old_category_icon，Mock update_category；调用 delete_category_icon；断言返回 dict 含 "message"；assert delete_old_category_icon 被调用。  
  - `test_delete_category_icon_category_not_found`：Mock get_category_by_id 返回 None；断言 raise NotFoundException。  
  - `test_delete_category_icon_permission_denied`：role 为 REGULAR；断言 raise PermissionDeniedException。  
  - `test_delete_category_icon_no_icon_idempotent`：Mock get_category_by_id 返回 Category(icon=None)；调用 delete_category_icon；断言仍返回成功（幂等）。

### B. API 层（追加到 `tests/integration/test_api_content_management.py`）

- **POST /api/v1/content/categories/{category_id}/icon**  
  - `test_api_upload_category_icon_success`：创建 Category，commit；用 admin token POST，files={"file": ("test.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0'*100), "image/jpeg")}；断言 200；响应为 CategoryItem 时断言 response.json()["icon"].startswith("/media/")（若为包装则 data.icon）。  
  - `test_api_upload_category_icon_category_not_found`：用 admin token 对 uuid4() 上传；断言 404，code 2001。  
  - `test_api_upload_category_icon_permission_denied`：用 regular_user_token 上传；断言 403，code 3003。  
  - `test_api_upload_category_icon_invalid_file_type`：上传非图片（如 .txt 或 content_type 非 image）；断言 400。  
- **DELETE /api/v1/content/categories/{category_id}/icon**  
  - `test_api_delete_category_icon_success`：创建 Category（可先上传 icon 或初始 icon 为空），commit；用 admin token DELETE；断言 200。  
  - `test_api_delete_category_icon_category_not_found`：DELETE 不存在的 category_id；断言 404，code 2001。  
  - `test_api_delete_category_icon_permission_denied`：用 regular_user_token DELETE；断言 403，code 3003。  
  - `test_api_delete_category_icon_no_icon_idempotent`：创建 Category(icon=None)，commit；DELETE；断言 200（幂等）。

---

## 8. 质量标准与生成后验证检查清单

**交付物**：  
- 在 `tests/unit/test_service_content_management.py` 末尾**追加**科室图片 Service 测试函数。  
- 在 `tests/integration/test_api_content_management.py` 末尾**追加**科室图片 API 测试函数。

**指令**：  
1. 先读取 Section 6 全部依赖文件再生成。  
2. 仅追加新函数，不修改、不删除已有测试与 conftest。  
3. 新测试遵循 Section 2–5（async for、函数式、Arrange-Act-Assert、Mock 规范）。  
4. API 上传使用 files= 与 BytesIO 小 JPEG；角色与业务码与设计一致。

**生成后自检**：  
- [ ] 所有新增测试均使用 `async for` 解包 db_session/async_client。  
- [ ] 未使用类式测试；未修改已有测试或 conftest。  
- [ ] Service Mock 覆盖 get_category_by_id、update_category、FileHandler.save_category_icon、delete_old_category_icon（按调用链）。  
- [ ] API 路径为 `/api/v1/content/categories/{category_id}/icon`，与 api prefix /content 一致。  
- [ ] 权限 403/404/400 断言与设计一致（2001、3003、4001）。

**文档结束。合并模式下，执行者应在同一流程内根据 Section 6 读取依赖并按 Section 7 逐项生成并追加测试代码。**
