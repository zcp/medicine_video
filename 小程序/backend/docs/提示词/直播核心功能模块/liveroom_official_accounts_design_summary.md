# 直播间与公众号关联 - 设计文档摘要

**来源**: docs/03_系统设计/直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md  
**模块名**: liveroom_official_accounts

---

## 1. 字段定义（DDL）

### official_accounts
- id UUID PK（应用层 uuid.uuid4()）
- name VARCHAR(100) NOT NULL UNIQUE
- slug VARCHAR(120), app_id VARCHAR(255), description VARCHAR(500)
- is_active BOOLEAN NOT NULL DEFAULT true
- created_at, updated_at TIMESTAMPTZ

### live_room_official_accounts
- room_id UUID NOT NULL, FK live_rooms(id) ON DELETE CASCADE, PK
- account_id UUID NOT NULL, FK official_accounts(id) ON DELETE CASCADE, PK
- created_at TIMESTAMPTZ

---

## 2. API 端点（设计文档 §4）

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/v1/admin/official_accounts | Admin | 分页列表，q/search_type/include_inactive |
| GET | /api/v1/admin/official_accounts/{account_id} | Admin | 单条详情 |
| POST | /api/v1/admin/official_accounts | Admin | 创建 |
| PATCH | /api/v1/admin/official_accounts/{account_id} | Admin | 部分更新 |
| DELETE | /api/v1/admin/official_accounts/{account_id} | Admin | 软删除 |
| GET | /api/v1/rooms/{room_id}/official_accounts | Optional | 按房间查公众号列表 |
| POST | /api/v1/admin/rooms/{room_id}/official_accounts | Admin | 批量设置 replace/append |
| DELETE | /api/v1/admin/rooms/{room_id}/official_accounts/{account_id} | Admin | 删除单条关联 |
| GET | /api/v1/official_accounts/{account_id}/rooms | Admin | 按公众号分页查房间 |

---

## 3. 权限与业务码

- Admin: role in ('ADMIN','SUPERADMIN')；非 Admin 写操作 → 403 code 3002
- 200 成功；2001 资源不存在；2002 名称重复；3002 权限不足；4001 参数校验；1002 系统错误

---

## 4. CRUD 函数（实际代码）

- get_paginated_official_accounts(db, page, size, q, search_type, include_inactive) -> (total, List[OfficialAccount])
- get_official_account_by_id(db, account_id) -> Optional[OfficialAccount]
- create_official_account(db, obj_in: OfficialAccountCreate) -> OfficialAccount
- update_official_account(db, account_id, obj_in: OfficialAccountUpdate) -> Optional[OfficialAccount]
- soft_delete_official_account(db, account_id) -> bool
- get_official_accounts_by_room_id(db, room_id) -> List[OfficialAccount]
- set_room_official_accounts(db, room_id, account_ids, mode) -> None
- delete_room_official_account(db, room_id, account_id) -> bool
- get_rooms_by_account_id_paginated(db, account_id, page, size) -> (total, List[LiveRoom])

---

## 5. Model 字段（OfficialAccount）

- id, name, slug, app_id, description, is_active, created_at, updated_at
