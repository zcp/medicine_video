# live_features 测试代码生成提示词

**生成日期**: 2026-06-05  
**测试模式**: 增量测试生成模式  
**模块名**: live_features  
**设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_regular在tab和留言上的权限扩充设计.md`

---

## 测试模式说明

- **测试模式**：增量测试生成模式
- **说明**：为 live_features 模块**新增**测试代码，在已有测试基础上增量生成
- **已有测试文件**：
  - `tests/unit/test_crud_live_features.py`
  - `tests/unit/test_service_live_features.py`
  - `tests/integration/test_api_live_features.py`
- **新增测试文件**：
  - `tests/integration/test_api_live_features_public.py`（公开端点，零覆盖）
- **追加测试**（增量到已有文件）：
  - `tests/integration/test_api_live_features.py`（图片上传 6 场景）
  - `tests/unit/test_crud_live_features.py`（remove_tab SimpleNamespace）
  - `tests/unit/test_service_live_features.py`（创建者权限）

---

## 核心测试哲学（混合策略）

| 测试目标层级 | 强制测试风格 | 核心工具 |
|:---|:---|:---|
| API / Endpoint 层 | 实用派 (Pragmatic) | `httpx.AsyncClient` + `db_session` + `async_session_factory` |
| Service 层 | 学院派 (Academic) | `mocker` (Mock CRUD/I/O) |
| CRUD 层 | 实用派 (Pragmatic) | `db_session` (真实数据库) |

---

## 依赖文件清单

### 目标代码文件
- `app/models/live_features.py` — LiveRoomTab, LiveRoomTabContentType, LiveRoomMessageUserRole
- `app/models/live_core.py` — LiveRoom (is_private 字段)
- `app/schemas/live_features.py` — LiveRoomTabCreate, LiveRoomTabUpdate, LiveRoomTabResponse
- `app/crud/live_features.py` — create_tab, get_tab, get_all_by_room_id, get_active_by_room_id, update_tab, remove_tab
- `app/services/live_features_service.py` — TabService (_check_tab_management_permission, list_tabs_for_admin, create_tab, update_tab, delete_tab, get_active_tabs_for_room)
- `app/api/v1/endpoints/live_features.py` — admin_tab_router, public_tab_router (6 个 Tab 端点)
- `app/core/deps.py` — get_current_user, get_current_user_optional
- `app/core/file_handler.py` — FileHandler.save_tab_image_file

### 现有 Fixture (conftest.py)
- `regular_user_id` → UUID
- `another_user_id` → UUID
- `regular_user_token` → JWT (role=REGULAR)
- `admin_user_token` → JWT (role=ADMIN)
- `another_user_token` → JWT
- `invalid_token` → 无效 JWT
- `public_room` → is_private=False 的房间
- `private_room` → is_private=True 的房间
- `db_session` → 异步 DB 会话
- `async_client` → httpx.AsyncClient
- `async_session_factory` → 独立会话工厂

---

## 具体测试任务列表

### A. 新建文件：`tests/integration/test_api_live_features_public.py`

**公开端点**: `GET /api/v1/rooms/{room_id}/tabs`（`list_room_tabs_public`）

1. `test_public_list_tabs_anonymous_public_room` — 匿名用户访问公开房间 → 200，返回激活 Tab
2. `test_public_list_tabs_anonymous_private_room` — 匿名用户访问私有房间 → 404
3. `test_public_list_tabs_regular_other_public_room` — 登录用户访问别人公开房间 → 200
4. `test_public_list_tabs_regular_other_private_room` — 登录用户访问别人私有房间 → 404
5. `test_public_list_tabs_owner_private_room` — 创建者访问自己私有房间 → 200
6. `test_public_list_tabs_admin_private_room` — Admin 访问任意私有房间 → 200
7. `test_public_list_tabs_only_active` — 验证只返回 is_active=True 的 Tab
8. `test_public_list_tabs_sort_order` — 验证按 sort_order 升序排列

### B. 追加到：`tests/integration/test_api_live_features.py`

**图片上传端点**: `POST /api/v1/admin/rooms/{room_id}/tabs/image`

9. `test_upload_image_admin_success` — Admin 上传合法图片 → 200
10. `test_upload_image_owner_success` — 创建者上传合法图片 → 200（P1-1 修复验证）
11. `test_upload_image_non_owner_denied` — 非创建者上传 → 403
12. `test_upload_image_invalid_format` — 非图片文件 → 400
13. `test_upload_image_unauthorized` — 无 Token → 401
14. `test_upload_image_room_not_found` — 房间不存在 → 404

### C. 追加到：`tests/unit/test_crud_live_features.py`

15. `test_remove_tab_returns_simple_namespace` — 验证 remove_tab 返回 SimpleNamespace（P0 修复）

### D. 追加到：`tests/unit/test_service_live_features.py`

16. `test_upload_image_owner_permission` — 验证创建者通过 _check_tab_management_permission
17. `test_upload_image_non_owner_denied` — 验证非创建者被拒绝

---

## 核心实现规范摘要

- ✅ API 测试使用 `async for client in async_client:` + `async for db in db_session:`
- ✅ 遵循 Arrange-Act-Assert 结构
- ✅ 唯一字段使用 UUID 后缀
- ✅ 禁止在测试中 commit（除非必要）
- ✅ 增量模式：不修改已有测试函数
- ✅ 复用 conftest.py 现有 Fixture
