# liveroom_official_accounts 测试代码生成提示词

**测试模式**: 增量测试生成模式  
**说明**: 为直播间与公众号关联模块**新增**测试代码，在已有测试基础上增量生成。**严禁修改**已存在的其他测试文件。可修改 `conftest.py` 仅限**增加**新内容。

---

## Section 6. 依赖文件清单（必须用 read_file 读取）

- `backend/live_core_service/app/models/liveroom_official_accounts.py`（OfficialAccount, LiveRoomOfficialAccount）
- `backend/live_core_service/app/schemas/liveroom_official_accounts.py`
- `backend/live_core_service/app/crud/liveroom_official_accounts.py`
- `backend/live_core_service/app/services/liveroom_official_accounts_service.py`
- `backend/live_core_service/app/api/v1/endpoints/liveroom_official_accounts.py`
- `backend/live_core_service/app/exceptions.py`（PermissionDeniedException, NotFoundException, InvalidParameterException）
- `backend/live_core_service/app/core/exceptions.py`（DatabaseIntegrityException）
- `backend/live_core_service/app/core/response.py`（success_response, error_response）
- `backend/live_core_service/tests/conftest.py`（db_session, async_client, admin_user_token, admin_user_id, admin_user_role）

---

## Section 7. 具体任务列表

### CRUD 层（tests/unit/test_crud_liveroom_official_accounts.py）

- test_get_paginated_official_accounts：分页列表，include_inactive=False 时仅 is_active=True；管理员可 include_inactive=True
- test_get_official_account_by_id：存在返回对象，不存在返回 None
- test_create_official_account_success：创建后 db.refresh 或再次查询验证字段（name, slug, is_active 等）
- test_create_official_account_duplicate_name：同名创建触发 DatabaseIntegrityException
- test_update_official_account_success：部分更新后再次查询验证
- test_soft_delete_official_account：软删除后再次查询 is_active=False
- test_get_official_accounts_by_room_id：先创建 room、account、关联记录，再查询列表
- test_set_room_official_accounts_replace：replace 模式先删后插，验证最终关联列表
- test_set_room_official_accounts_append：append 模式仅追加，不重复插入
- test_delete_room_official_account：删除后查询返回空或数量减一
- test_get_rooms_by_account_id_paginated：分页 total + items，验证 Room 字段（id, title）

### Service 层（tests/unit/test_service_liveroom_official_accounts.py）

- 使用 AsyncMock 作为 db；Mock CRUD 返回值
- test_get_official_accounts_admin_permission_denied：role=REGULAR 时 raise PermissionDeniedException
- test_get_official_account_by_id_not_found：CRUD 返回 None 时 raise NotFoundException
- test_create_official_account_success：Mock create_official_account 返回 OfficialAccount，验证返回 OfficialAccountItem
- test_soft_delete_official_account_not_found：CRUD 返回 False 时 raise NotFoundException
- test_get_official_accounts_by_room_id_room_not_found：room 不存在时 raise NotFoundException
- test_set_room_official_accounts_permission_denied：非 Admin raise PermissionDeniedException
- test_get_rooms_by_account_id_permission_denied：非 Admin raise PermissionDeniedException

### API 层（tests/integration/test_api_liveroom_official_accounts.py）

- test_get_official_accounts_admin_unauthorized：无 Token 请求 GET /api/v1/admin/official_accounts 返回 401 或 403
- test_get_official_accounts_admin_with_admin_token：带 admin_user_token 返回 200，data 含 total/page/size/items
- test_create_official_account_success：POST /api/v1/admin/official_accounts，Body OfficialAccountCreate，返回 201，data 含 name/id/is_active
- test_create_official_account_permission_denied：regular_user_token 请求 POST 返回 403，code 3002
- test_get_official_account_by_id_not_found：GET /api/v1/admin/official_accounts/{uuid4()} 不存在返回 404，code 2001
- test_get_rooms_official_accounts_optional_auth：GET /api/v1/rooms/{room_id}/official_accounts 可用 Optional Auth，有 room 时返回 200 data 为列表
- test_get_rooms_official_accounts_room_not_found：不存在的 room_id 返回 404
- test_set_room_official_accounts_admin：POST /api/v1/admin/rooms/{room_id}/official_accounts，Body account_ids + mode，Admin Token 返回 200
- test_get_official_accounts_rooms_paginated：GET /api/v1/official_accounts/{account_id}/rooms?page=1&size=10，Admin Token 返回 200，data 含 total/items

---

**API 基础 URL**：客户端请求时使用路径如 `/api/v1/admin/official_accounts`（conftest 中 app 已 include_router prefix="/api/v1"）。

**Fixture**：使用 conftest 中已有的 `db_session`、`async_client`、`admin_user_token`、`admin_user_id`、`admin_user_role`、`regular_user_token`、`regular_user_id`、`regular_user_role`。
