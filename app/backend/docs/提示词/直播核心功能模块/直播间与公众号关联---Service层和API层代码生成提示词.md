# 直播间与公众号关联 --- Service 层和 API 层代码生成提示词

**版本**: V1.0  
**基于**: 直播间与公众号关联---crud_service_endpoint代码生成提示词母版.md、设计文档 §4/§6  
**目标文件**:  
- `backend/live_core_service/app/services/liveroom_official_accounts_service.py`  
- `backend/live_core_service/app/api/v1/endpoints/liveroom_official_accounts.py`

---

## 1. 角色与任务

你是精通学院派分层与 FastAPI 的后端架构师。请根据设计文档与已有 CRUD/Schema，生成**直播间与公众号关联**模块的 Service 层与 API 层代码。Service 层负责权限与业务编排，禁止 `db.commit()`/`db.rollback()`；API 层仅做参数注入、调用 Service、捕获异常并返回 JSONResponse。

**必须**先使用 `read_file()` 读取：
- `app/schemas/liveroom_official_accounts.py`（响应结构、请求 Schema）
- 设计文档 §4（每个端点的认证、成功/失败响应、实现流程）

---

## 2. API 端点实现强制模板（每个端点必须遵循）

```python
# 在 try 之前提取所有用于 except 日志的变量（禁止在 except 内访问可能失效的 db 或 ORM 属性）
user_id = current_user.get("user_id")  # 或从 token 解析
role = current_user.get("role")
account_id = account_id  # 路径参数
# ...

try:
    result = service.xxx(db, user_id, role, ...)
    return JSONResponse(status_code=200, content=success_response(data=result))
except PermissionDeniedException as e:
    logger.warning(f"权限不足: user_id={user_id}, ...")
    return JSONResponse(status_code=403, content=error_response(3002, str(e)))
except NotFoundException as e:
    logger.warning(f"资源未找到: account_id={account_id}, ...")
    return JSONResponse(status_code=404, content=error_response(2001, str(e)))
except DatabaseIntegrityException as e:
    logger.warning(f"数据完整性错误: ...")
    return JSONResponse(status_code=400, content=error_response(2002, str(e)))
except Exception as e:
    logger.warning(f"未预期错误: ...")
    return JSONResponse(status_code=500, content=error_response(1002, str(e)))
```

---

## 3. 权限与 URL 规范

- **权限**：Service 内 `_check_admin_permission(role)`：若 role 非 ADMIN/SUPERADMIN（大写），raise PermissionDeniedException；所有管理端接口均需此检查。
- **URL 拼接**：使用设计文档中的完整路径，避免重复前缀；路由注册时前缀为 `/api/v1`，admin 子路径为 `/admin/...`。
- **响应格式化**：统一 `success_response(data=...)`、`error_response(code, message)`；分页 data 含 total、page、size、items；与设计文档 §4 一致。

---

## 4. Service 方法清单（与 API 一一对应）

| Service 方法 | 说明 | 调用 CRUD |
|--------------|------|-----------|
| get_official_accounts_admin(db, user_id, role, page, size, q, search_type, include_inactive) | _check_admin_permission；get_paginated_official_accounts | 返回 PaginatedData[OfficialAccountItem] |
| get_official_account_by_id(db, user_id, role, account_id) | _check_admin_permission；get_official_account_by_id；无则 raise NotFoundException | OfficialAccountItem |
| create_official_account(db, body, user_id, role) | _check_admin_permission；create_official_account；IntegrityError → DatabaseIntegrityException | OfficialAccountItem |
| update_official_account(db, account_id, body, user_id, role) | _check_admin_permission；get + update；无则 NotFoundException | OfficialAccountItem |
| soft_delete_official_account(db, account_id, user_id, role) | _check_admin_permission；soft_delete_official_account；无则 NotFoundException | 可返回 status |
| get_official_accounts_by_room_id(db, room_id) | 校验 room 存在（可选，或 CRUD 返回空）；get_official_accounts_by_room_id | List[OfficialAccountItem] |
| set_room_official_accounts(db, user_id, role, room_id, body) | _check_admin_permission；校验房间存在、account_ids 有效且 is_active；set_room_official_accounts | SetResponse data |
| delete_room_official_account(db, user_id, role, room_id, account_id) | _check_admin_permission；delete_room_official_account；0 行 raise NotFoundException | 200 |
| get_rooms_by_account_id(db, user_id, role, account_id, page, size) | _check_admin_permission；校验公众号存在且 is_active；get_rooms_by_account_id_paginated | PaginatedData[RoomBriefItem] |

---

## 5. API 端点清单（与设计文档 §4 完全一致）

| 方法 | 路径 | 认证 | 请求体/Query |
|------|------|------|---------------|
| GET | /api/v1/admin/official_accounts | Strict + Admin | page, size, q, search_type, include_inactive |
| GET | /api/v1/admin/official_accounts/{account_id} | Strict + Admin | - |
| POST | /api/v1/admin/official_accounts | Strict + Admin | OfficialAccountCreate |
| PATCH | /api/v1/admin/official_accounts/{account_id} | Strict + Admin | OfficialAccountUpdate |
| DELETE | /api/v1/admin/official_accounts/{account_id} | Strict + Admin | - |
| GET | /api/v1/rooms/{room_id}/official_accounts | Optional | - |
| POST | /api/v1/admin/rooms/{room_id}/official_accounts | Strict + Admin | LiveRoomOfficialAccountsSetRequest |
| DELETE | /api/v1/admin/rooms/{room_id}/official_accounts/{account_id} | Strict + Admin | - |
| GET | /api/v1/official_accounts/{account_id}/rooms | Strict + Admin | page, size |

---

## 6. 批量验证与异常

- set_room_official_accounts：在 Service 内校验每个 account_id 在 official_accounts 中存在且 is_active=true；否则 400/4001；校验 room 存在否则 404/2001。
- 所有 Admin 接口：先 _check_admin_permission，再业务逻辑；禁止在 API 层做权限判断（仅 Depends(get_current_user) 注入用户）。

---

## 7. 路由注册

- 在 `app/api/v1/api.py` 中挂载本模块路由，例如：  
  `include_router(liveroom_official_accounts.router, prefix="/admin/official_accounts", tags=["直播间与公众号关联-管理端"])`  
  以及 rooms 下子路径、official_accounts/{account_id}/rooms；具体前缀与设计文档 §4、§10 一致，避免重复 /api/v1。

---

## 8. 最终交付

- 生成 `app/services/liveroom_official_accounts_service.py`（上述 9 个方法 + _check_admin_permission）。
- 生成 `app/api/v1/endpoints/liveroom_official_accounts.py`（9 个端点，每个遵循 §2 模板）。
- 更新 `app/api/v1/api.py` 注册路由。
- 确保 success_response/error_response 与项目现有工具函数一致；logger 使用项目约定模块名。
