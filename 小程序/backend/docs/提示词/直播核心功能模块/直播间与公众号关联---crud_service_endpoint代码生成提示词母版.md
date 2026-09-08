# 直播间与公众号关联 --- CRUD/Service/Endpoint 代码生成提示词母版（模块特定）

**版本**: V1.0  
**基于设计文档**: docs/03_系统设计/直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md  
**模块名**: liveroom_official_accounts  
**功能模块名称**: 直播间与公众号关联  
**项目路径**: live_core_service

---

## 1. 角色与目标

你是一名精通学院派架构（Clean Architecture）的资深 Python 后端架构师。本母版用于生成**直播间与公众号关联**模块的 CRUD 层、Service 层与 API 层代码生成提示词；生成代码时必须严格遵循设计文档与下文交付物及规范。

---

## 2. 核心上下文与依赖

- **设计文档**: `docs/03_系统设计/直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md`（API 列表、实现流程、权限与异常规范均以该文档为准）
- **模型代码**: `backend/live_core_service/app/models/liveroom_official_accounts.py`
- **Schema 代码**: `backend/live_core_service/app/schemas/liveroom_official_accounts.py`

**架构规范**（必须完整传递到具体提示词文档）:
- 全项目通用：安全异步异常处理（try 前提取变量）、内部 ID 不对外暴露、API Schema 与 CRUD Schema 区分、Enum 声明、环境变量配置、RESTful 原则、日志与错误脱敏
- 异常处理：CRUD 层 try/except IntegrityError/finally；Service/API 层使用 API 端点实现强制模板
- CRUD 层：N+1 防治（selectinload/joinedload）、分页两次查询、SQL 级权限过滤、事务在 CRUD 内、数据库初始化脚本更新
- Service 层：业务编排、批量验证、权限模式（大写角色比较）、角色检查强制
- API 层：端点实现强制模板（完整复制）、JSONResponse/error_response、路由定义与 URL 拼接、响应格式化

---

## 3. Model 字段摘要（来源：app/models/liveroom_official_accounts.py）

**OfficialAccount**
- 主键: id (UUID, default=uuid.uuid4)
- 业务字段: name (String(100), unique, NOT NULL), slug (String(120)), app_id (String(255)), description (String(500)), is_active (Boolean, default=True)
- 时间戳: created_at, updated_at (TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
- 索引: idx_official_accounts_name, idx_official_accounts_is_active

**LiveRoomOfficialAccount**
- 复合主键: room_id (FK live_rooms.id ON DELETE CASCADE), account_id (FK official_accounts.id ON DELETE CASCADE)
- created_at (TIMESTAMP(timezone=True), server_default=func.now())
- 索引: idx_live_room_official_accounts_room_id, idx_live_room_official_accounts_account_id

---

## 4. Schema 摘要（来源：app/schemas/liveroom_official_accounts.py）

- **公众号**: OfficialAccountBase, OfficialAccountCreate, OfficialAccountUpdate, OfficialAccountItem；OfficialAccountAdminListResponse（data: PaginatedData[OfficialAccountItem]）
- **关联**: LiveRoomOfficialAccountsSetRequest（account_ids, mode replace/append）, LiveRoomOfficialAccountsSetResponse, LiveRoomOfficialAccountsListResponse（data: List[OfficialAccountItem]）
- **按公众号查房间**: RoomBriefItem（id, title, slug）, OfficialAccountRoomsListResponse（data: PaginatedData[RoomBriefItem]）
- PaginatedData 复用 content_management

---

## 5. API 与 Service 对应关系（设计文档 §4）

| API 端点 | 认证 | Service 方法 | 说明 |
|----------|------|--------------|------|
| GET /api/v1/admin/official_accounts | Admin | get_official_accounts_admin(db, user_id, role, page, size, q, search_type, include_inactive) | 分页列表，q/search_type/include_inactive |
| GET /api/v1/admin/official_accounts/{account_id} | Admin | get_official_account_by_id(db, user_id, role, account_id) | 单条详情 |
| POST /api/v1/admin/official_accounts | Admin | create_official_account(db, body, user_id, role) | 创建 |
| PATCH /api/v1/admin/official_accounts/{account_id} | Admin | update_official_account(db, account_id, body, user_id, role) | 部分更新 |
| DELETE /api/v1/admin/official_accounts/{account_id} | Admin | soft_delete_official_account(db, account_id, user_id, role) | 软删除 |
| GET /api/v1/rooms/{room_id}/official_accounts | Optional | get_official_accounts_by_room_id(db, room_id) | 按房间查公众号列表 |
| POST /api/v1/admin/rooms/{room_id}/official_accounts | Admin | set_room_official_accounts(db, user_id, role, room_id, body) | 批量设置 replace/append |
| DELETE /api/v1/admin/rooms/{room_id}/official_accounts/{account_id} | Admin | delete_room_official_account(db, user_id, role, room_id, account_id) | 删除单条关联 |
| GET /api/v1/official_accounts/{account_id}/rooms | Admin | get_rooms_by_account_id(db, user_id, role, account_id, page, size) | 按公众号分页查房间 |

权限守卫：Service 内 _check_admin_permission(role)；ADMIN/SUPERADMIN 大写比较。

---

## 6. 交付物（供生成具体提示词文档使用）

### 6.1 CRUD 层代码

- **公众号**: get_paginated_official_accounts（分页、q/search_type/include_inactive、WHERE is_active 与搜索条件）；get_official_account_by_id；create_official_account（事务内 commit，IntegrityError → rollback + DatabaseIntegrityException）；update_official_account；soft_delete_official_account（update is_active=false）
- **关联表**: get_official_accounts_by_room_id（联表 live_room_official_accounts + official_accounts，room_id + is_active=true）；set_room_official_accounts（replace：删该 room 后批量插入，append：仅插入；事务）；delete_room_official_account（删除 (room_id, account_id)，不存在则 raise）；get_rooms_by_account_id_paginated（联表 live_room_official_accounts + live_rooms，account_id，分页 total + items）

### 6.2 Service 层代码

- 上表所列 9 个 Service 方法；每个管理端接口先 _check_admin_permission(role)；按设计文档 §4 实现流程调用 CRUD 并处理 NotFoundException/DatabaseIntegrityException 等；禁止 db.commit/rollback。

### 6.3 API 层代码

- 9 个端点与上表一致；Strict Auth（get_current_user）用于写操作与 Admin 读操作；Optional Auth（get_current_user_optional）用于 GET /api/v1/rooms/{room_id}/official_accounts；每个端点 try 前提取 user_id、role、路径参数等用于 except 日志；except 块先 logger.warning 再 JSONResponse；使用 success_response/error_response 与设计文档错误码（2001/2002/3002/4001/1002 等）。

---

## 7. 规范完整性检查表（子步骤 4.1.1）

- [x] 全项目通用安全与一致性规范（7 项）
- [x] 异常处理规范（CRUD + API 端点模板）
- [x] CRUD 层实现规范（N+1、分页、SQL 权限、事务、init 脚本）
- [x] Service 层实现规范（业务编排、批量验证、权限模式、角色检查）
- [x] API 层实现规范（端点模板、导入、路由、URL 拼接、响应格式化）

生成 CRUD 层与 Service/API 层具体提示词文档时，须将上述规范完整包含或明确引用本母版及设计文档。
