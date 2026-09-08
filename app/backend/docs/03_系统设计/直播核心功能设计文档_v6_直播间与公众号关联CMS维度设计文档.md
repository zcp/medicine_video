# 直播间与公众号关联（CSM 维度）设计文档

**版本**: V1.0  
**日期**: 2026-02  
**状态**: 设计完成，可直接开发  
**基于**: 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版-含搜索与科室图片》（主文档 B）

**说明**：本文档为全新子模块设计文档 A，有机继承主文档 B 的全部规范（权限设计、日志规范、异常处理、安全规范、学院派分层等）。增量扩展，不修改 B 的现有表与 API。

**版本与变更历史**：

| 日期     | 版本  | 变更说明 |
|----------|-------|----------|
| 2026-02  | V1.0  | 初稿：直播间与公众号关联（CSM 维度） |

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档是主文档 B 的**增量子模块**，专注于**直播间-公众号关联（CSM 维度）**的完整设计，包括：

**包含模块**:
- **Official_Accounts（公众号）**: 公众号主表，用于 CSM 场景下的租户/客户维度
- **Live_Room_Official_Accounts（直播间-公众号关联）**: 直播间与公众号的多对多关联关系

**模块范围**:
- 2 张数据表（official_accounts、live_room_official_accounts）
- 若干 API 接口：公众号 CRUD（管理端）、按直播间查关联公众号、直播间绑定/解绑公众号、**CSM 核心**按公众号查直播间列表（分页）

**与主文档 B 的关系**:
- 仅依赖 v6 主文档中的 `live_rooms` 表；不修改 `live_rooms` 及 B 中任何现有表与 API
- 数据模型与 API 风格严格参考 B 中的 **Live_Room_Categories**、**Categories** 设计

### 2. 业务目标

- 为 **CSM（客户成功/运营）** 场景提供按「公众号」维度的直播间可见范围管理
- **数据隔离**：每个公众号仅能查看/管理与其关联的直播间列表（通过 `GET /api/v1/official_accounts/{account_id}/rooms` 实现）

### 3. 核心关系

- **直播间与公众号为多对多**：一个直播间可挂载到多个公众号，一个公众号可关联多个直播间
- 通过中间表 `live_room_official_accounts` 维护 (room_id, account_id)，外键 ON DELETE CASCADE

---

## 📚 依赖文档清单

1. **《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版-含搜索与科室图片》**（主文档 B）  
   - 规范来源：文档规范说明（统一响应、认证、JWT、业务状态码、**权限设计规范**）、设计要点与约定（数据库规范、API 规范、软删除、**安全与配置规范**）、错误处理与事务管理  
   - 设计参考：Live_Room_Categories 的 DDL、Schema、API 与执行流程；Categories 的主表与 CRUD 风格

2. **《直播核心功能设计文档_v6_增加权限设计版.md》**  
   - 权限系统设计

3. **《用户模块设计文档authing版+权限设计版.md》**  
   - JWT 认证规范、user_id 字段

4. **《配置与安全优化方案-实施指南.md》**（若 B 引用）  
   - 日志脱敏、配置验证

---

## 🔄 增量开发说明

- **不修改主文档 B**：不修改 B 中任何表、API、Section
- **增量扩展**：仅新增 2 张表（official_accounts、live_room_official_accounts）及相关 API
- **有机整合**：通过外键关联 `live_rooms.id` 与主文档无缝集成；公众号为系统级资源，权限与 B 一致（Admin 写、Optional/Strict 读按接口区分）

---

## 📋 文档规范说明

本文档**继承**主文档 B 的「文档规范说明」全部内容，以下仅作索引与模块化补充。

### 1. 统一响应结构

与主文档 B 一致：所有 API 返回 `{ "code", "message", "data", "timestamp" }`。

### 2. 统一分页格式

与主文档 B 一致：分页接口 `data` 含 `total`、`page`、`size`、`items`。

### 3. 统一认证规范

- **Strict Auth**：写操作（公众号 CRUD、直播间绑定/解绑公众号），`Depends(get_current_user)`，无 Token 或无效返回 401
- **Optional Auth**：读操作（如按直播间查关联公众号列表），`Depends(get_current_user_optional)`，与 B 一致
- **Admin Auth**：管理端接口需 JWT + `ADMIN` 或 `SUPERADMIN`；**CSM 核心接口** `GET /api/v1/official_accounts/{account_id}/rooms` 需 JWT，鉴权规则见 4. API 设计（仅 ADMIN 可调或按业务扩展「当前用户与公众号绑定」校验，本版采用仅 ADMIN 可调）

### 4. JWT 与用户身份提取

与主文档 B 一致：使用 **user_id**（非 sub）、**role**（REGULAR/ADMIN/SUPERADMIN）；在 API 层提取后传入 Service 层。

### 5. 业务状态码

与主文档 B 一致：200 成功；2001 资源不存在；2002 资源已存在；2003 操作被禁止；3002 权限不足；4001 参数校验失败；1002 系统错误。

### 6. 权限设计规范（继承 B 文档规范说明 §6）

- **API 层**：仅负责 Authentication；使用 `Depends(get_current_user)` / `Depends(get_current_user_optional)`，提取 `user_id`、`role` 传 Service
- **Service 层**：全权负责 Authorization；实现 `_check_admin_permission` 等权限守卫；抛 `PermissionDeniedException`、`NotFoundException` 等自定义异常；**禁止** `db.commit()` / `db.rollback()`
- **CRUD 层**：在 **SQL 层面**应用权限过滤（如公众号列表根据 `is_active` 与角色）；禁止内存过滤；写操作在 CRUD 内处理事务（try/except IntegrityError、rollback、logger.error、raise DatabaseIntegrityException 等）
- **双轨鉴权**：写操作用 Strict Auth；读操作按接口使用 Optional Auth 或 Strict（见 4. API 设计）
- **学院派异常流**：CRUD 层捕获 DB 异常并抛自定义异常 → Service 层不捕获 CRUD 异常、仅抛业务异常 → API 层 try/except 转为 JSONResponse（403/3002、404/2001、400/4001、500/1xxx）

### 7. 安全与配置规范（继承 B 设计要点与约定 §4）

- 安全异步异常处理：在 **try 之前**提取所有用于 except 块日志的变量（如 user_id、account_id、room_id）；**禁止**在 except 块中访问可能已失效的 db 会话或 ORM 对象属性
- 日志脱敏、异常处理中不向用户暴露敏感信息；与 B 完全一致

### 8. 日志规范（继承 B 及母版 2.8，须在文档 A 中显式可查）

- **INFO**：关键业务动作（创建、更新、删除公众号；设置/删除直播间-公众号关联；成功查询）。示例：`logger.info(f"创建公众号成功: {account_id}")`、`logger.info(f"用户 {user_id} 设置房间 {room_id} 公众号关联")`。
- **WARNING**：在 **API 层的 `except` 块中**记录非法请求、权限拒绝、资源不存在、参数异常。每个 `except` 块内**先** `logger.warning(...)` **再** `return JSONResponse(...)`。示例：`logger.warning(f"资源未找到: room_id={room_id}")`、`logger.warning(f"权限不足: user_id={user_id}, account_id={account_id}")`。
- **ERROR**：在 **CRUD 层的 `except` 块中**记录数据库异常，且必须 **`exc_info=True`**。示例：`logger.error("创建失败 (完整性错误): ...", exc_info=True)`。禁止在 except 中访问可能已失效的 db 或 ORM 对象做日志。

---

## 🎯 设计要点与约定

- **数据库规范**：与 B 一致。主键 UUID 应用层生成（uuid.uuid4()）；时间字段 TIMESTAMPTZ；created_at/updated_at；外键命名 fk_<表名>_<字段名>；索引命名 idx_<表名>_<字段名>
- **API 规范**：路径与 B 一致；公共 `/api/v1/...`，管理 `/api/v1/admin/...`；资源名词复数；子资源 REST 风格
- **软删除**：公众号表使用 **is_active** 软删除（与 B 的 tags/categories 一致）；关联表 **live_room_official_accounts** 硬删除（与 session_tags、live_room_categories 一致），ON DELETE CASCADE

---

## 2. 数据库 Schema 设计（DDL）

### 2.0 前置准备

与主文档 B 一致：触发器函数 `trigger_set_timestamp()` 已存在则复用；若本模块单独部署则需创建。时间戳字段由触发器更新 `updated_at`。

### 2.1 official_accounts（公众号主表）

```sql
CREATE TABLE official_accounts (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120),
    app_id VARCHAR(255),
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_official_accounts_name UNIQUE (name)
);

CREATE INDEX idx_official_accounts_name ON official_accounts(name);
CREATE INDEX idx_official_accounts_is_active ON official_accounts(is_active);
CREATE TRIGGER set_timestamp_official_accounts
    BEFORE UPDATE ON official_accounts
    FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

COMMENT ON TABLE official_accounts IS '公众号主表（CSM 维度）';
COMMENT ON COLUMN official_accounts.id IS '主键 UUID，应用层 uuid.uuid4() 生成';
COMMENT ON COLUMN official_accounts.name IS '公众号名称，全局唯一';
COMMENT ON COLUMN official_accounts.slug IS 'URL 友好标识';
COMMENT ON COLUMN official_accounts.app_id IS '预留：外部系统标识（如微信 app_id）';
COMMENT ON COLUMN official_accounts.is_active IS '是否启用；false 表示软删除';
```

### 2.2 live_room_official_accounts（直播间-公众号关联表）

```sql
CREATE TABLE live_room_official_accounts (
    room_id UUID NOT NULL,
    account_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (room_id, account_id),

    CONSTRAINT fk_live_room_official_accounts_room_id
        FOREIGN KEY (room_id) REFERENCES live_rooms(id) ON DELETE CASCADE,
    CONSTRAINT fk_live_room_official_accounts_account_id
        FOREIGN KEY (account_id) REFERENCES official_accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_live_room_official_accounts_room_id ON live_room_official_accounts(room_id);
CREATE INDEX idx_live_room_official_accounts_account_id ON live_room_official_accounts(account_id);

COMMENT ON TABLE live_room_official_accounts IS '直播间与公众号的多对多关联表（CSM 维度）';
COMMENT ON COLUMN live_room_official_accounts.room_id IS '直播间 ID，关联 live_rooms 表';
COMMENT ON COLUMN live_room_official_accounts.account_id IS '公众号 ID，关联 official_accounts 表';
```

---

## 3. Pydantic Schemas 定义

### 3.1 Official_Accounts Schemas

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, TypeVar, Generic
import uuid
import datetime
import re

T = TypeVar('T')

class OfficialAccountBase(BaseModel):
    """公众号基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="公众号名称")
    slug: Optional[str] = Field(None, max_length=120)
    app_id: Optional[str] = Field(None, max_length=255, description="预留：外部 app_id")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('公众号名称不能包含特殊字符')
        return v

class OfficialAccountCreate(OfficialAccountBase):
    """创建公众号请求 Schema"""
    is_active: Optional[bool] = Field(True, description="是否启用")

class OfficialAccountUpdate(BaseModel):
    """更新公众号请求 Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    app_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class OfficialAccountItem(OfficialAccountBase):
    """公众号响应 Schema"""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

class PaginatedData(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    items: List[T]

class OfficialAccountAdminListResponse(BaseModel):
    """公众号管理端列表响应（分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[OfficialAccountItem]
    timestamp: datetime.datetime
```

### 3.2 Live_Room_Official_Accounts Schemas

```python
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
import uuid
import datetime

class LiveRoomOfficialAccountsSetRequest(BaseModel):
    """直播间公众号批量设置请求 Schema"""
    account_ids: List[uuid.UUID] = Field(..., min_length=0, max_length=50, description="公众号 ID 列表，可为空表示清空关联")
    mode: Literal["replace", "append"] = Field("replace", description="replace=覆盖，append=追加")

    @field_validator("account_ids")
    @classmethod
    def account_ids_unique(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
        if len(v) != len(set(v)):
            raise ValueError("account_ids 不能重复")
        return v

class LiveRoomOfficialAccountsSetResponse(BaseModel):
    """直播间公众号设置响应 Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # room_id, mode, accounts: List[OfficialAccountItem]
    timestamp: datetime.datetime

class LiveRoomOfficialAccountsListResponse(BaseModel):
    """直播间关联公众号列表响应 Schema"""
    code: int = 200
    message: str = "success"
    data: List[OfficialAccountItem]
    timestamp: datetime.datetime
```

### 3.3 按公众号查直播间列表（CSM）响应

- 复用或定义 **RoomBriefItem**（id、name、slug 等直播间简要字段，与 v6 主文档一致）；分页响应为 `PaginatedData[RoomBriefItem]`，统一 `code`、`message`、`data`、`timestamp`。

---

## 4. API 接口设计

### 4.1 公众号管理端 CRUD

#### 4.1.1 获取公众号列表（管理端，分页）

**Endpoint**: `GET /api/v1/admin/official_accounts`

**描述**: 管理员分页获取公众号列表，支持 q、search_type、include_inactive（与 B 的 Categories 管理端列表一致）。

**认证**: JWT + ADMIN/SUPERADMIN。

**Query**: page（默认 1）、size（默认 10，上限 100）；q（可选）；search_type（可选，id | keyword）；include_inactive（可选，默认 false）。**本列表字符串搜索字段**：`["name"]`。

**成功响应**: 200，data 为 PaginatedData[OfficialAccountItem]。

**失败响应**: 400（q 非 UUID 且 search_type=id 时 code 4001）；403 code 3002。

**实现流程（学院派）**:
1. (API 层) 接收请求，Depends(get_current_user)、get_db；提前提取 user_id、role 用于 except 日志。
2. (API 层) 启动 try/except。
3. (API 层) 若 search_type=id 且 q 非空，校验 q 为合法 UUID，非法则 return JSONResponse(400, error_response(4001, "无效的ID格式"))。
4. (API 层) 调用 service.get_official_accounts_admin(db, user_id, role, page, size, q, search_type, include_inactive)。
5. (Service 层) _check_admin_permission(role)；调用 CRUD 获取 total 与 items（CRUD 层 WHERE 含 is_active 条件与 q/search_type 条件）。
6. (API 层) try 内 return success_response(data=...)。except PermissionDeniedException：先 `logger.warning(f"权限不足: user_id={user_id}")`，再 `return JSONResponse(403, error_response(3002, ...))`。except Exception：先 `logger.warning` 或按需记录，再 `return JSONResponse(500, error_response(1002, ...))`。

#### 4.1.2 获取公众号详情（管理端）

**Endpoint**: `GET /api/v1/admin/official_accounts/{account_id}`

**描述**: 管理员获取单个公众号详情（用于编辑页回显等）。

**认证**: JWT + ADMIN/SUPERADMIN。

**路径参数**: account_id (UUID)。

**成功响应**: 200，data 为 OfficialAccountItem。

**失败响应**: 2001 资源不存在；403 3002。

**实现流程**:
1. (API 层) Depends(get_current_user)、get_db；**try 前**提取 user_id、role、account_id 用于 except 日志。
2. (API 层) 启动 try/except。
3. (API 层) try 内调用 service.get_official_account_by_id(db, user_id, role, account_id)。
4. (Service 层) _check_admin_permission(role)；调用 CRUD 按 account_id 查询；不存在则 raise NotFoundException。
5. (API 层) except PermissionDeniedException：先 `logger.warning(f"权限不足: user_id={user_id}")`，再 return JSONResponse(403, 3002)。except NotFoundException：先 `logger.warning(f"公众号不存在: account_id={account_id}")`，再 return JSONResponse(404, 2001)。

#### 4.1.3 创建公众号

**Endpoint**: `POST /api/v1/admin/official_accounts`

**描述**: 管理员创建公众号。

**认证**: JWT + ADMIN/SUPERADMIN。

**请求体**: OfficialAccountCreate（name、slug、app_id、description、is_active）。

**成功响应**: 201，data 为 OfficialAccountItem。

**失败响应**: 2002 名称重复；4001 参数校验；403 3002。

**实现流程**: (API) 注入 db、current_user；**try 前**提取 user_id、role。try 内调用 service.create_official_account(db, body, user_id, role)；Service _check_admin_permission；CRUD create（事务内 commit，IntegrityError -> rollback + raise DatabaseIntegrityException）。except PermissionDeniedException：先 logger.warning，再 403/3002。except DatabaseIntegrityException：先 logger.warning，再 400/2002。except Exception：先 logger.warning，再 500/1002。

#### 4.1.4 更新公众号

**Endpoint**: `PATCH /api/v1/admin/official_accounts/{account_id}`

**描述**: 管理员部分更新公众号。

**认证**: JWT + ADMIN/SUPERADMIN。

**路径参数**: account_id (UUID)。

**请求体**: OfficialAccountUpdate（各字段可选）。

**成功响应**: 200，data 为 OfficialAccountItem。

**失败响应**: 2001 资源不存在；2002 名称重复；403 3002。

**实现流程**: (API) try 前提取 user_id、role、account_id。try 内调用 service.update_official_account(...)。Service 校验存在、_check_admin_permission、唯一性后调用 CRUD update。except PermissionDeniedException：先 logger.warning，再 403/3002。except NotFoundException：先 logger.warning，再 404/2001。except DatabaseIntegrityException：先 logger.warning，再 400/2002。

#### 4.1.5 删除公众号（软删除）

**Endpoint**: `DELETE /api/v1/admin/official_accounts/{account_id}`

**描述**: 管理员软删除公众号（设置 is_active=false）。

**认证**: JWT + ADMIN/SUPERADMIN。

**成功响应**: 200；data 可含 status: "soft_deleted"。

**失败响应**: 2001 资源不存在；403 3002。

**实现流程**: (API) try 前提取 user_id、role、account_id。try 内调用 service.soft_delete_official_account(...)。Service 层查存在、_check_admin_permission；CRUD 层 update is_active=false。except PermissionDeniedException：先 logger.warning，再 403/3002。except NotFoundException：先 logger.warning，再 404/2001。

### 4.2 按直播间查关联公众号

#### 4.2.1 获取直播间关联公众号列表（公开）

**Endpoint**: `GET /api/v1/rooms/{room_id}/official_accounts`

**描述**: 获取某直播间关联的已启用公众号列表。

**认证**: Optional Auth（与 B 的 GET /rooms/{room_id}/categories 一致）。

**路径参数**: room_id (UUID)。

**成功响应**: 200，data 为 List[OfficialAccountItem]；无关联时返回空数组。

**失败响应**: 2001 房间不存在。

**实现流程**:
1. (API 层) 注入 get_current_user_optional、get_db；**try 前**提取 room_id（及可选 user_id、role）用于 except 日志。
2. (API 层) 启动 try/except。
3. (API 层) try 内调用 service.get_official_accounts_by_room_id(db, room_id, ...)。Service/CRUD 先校验 room_id 对应 live_rooms 存在，不存在则 Service raise NotFoundException；再联表 live_room_official_accounts + official_accounts，条件 room_id、official_accounts.is_active=true，排序后返回。
4. (API 层) except NotFoundException：先 `logger.warning(f"房间不存在: room_id={room_id}")`，再 `return JSONResponse(404, error_response(2001, ...))`。

### 4.3 直播间绑定/解绑公众号

#### 4.3.1 批量设置直播间公众号（管理员）

**Endpoint**: `POST /api/v1/admin/rooms/{room_id}/official_accounts`

**描述**: 批量设置某直播间的公众号（replace/append）。

**认证**: JWT + ADMIN/SUPERADMIN。

**路径参数**: room_id (UUID)。

**请求体**: LiveRoomOfficialAccountsSetRequest（account_ids、mode）。

**成功响应**: 200，LiveRoomOfficialAccountsSetResponse。

**失败响应**: 2001 房间不存在；4001 account_id 无效或未启用；403 3002。

**实现流程**: (API) **try 前**提取 user_id、role、room_id。try 内调用 service.set_room_official_accounts(db, user_id, role, room_id, body)。(Service) _check_admin_permission；校验房间存在；**仅当 account_ids 非空时**校验 account_ids 均在 official_accounts 且 is_active=true；replace：删该 room 的 live_room_official_accounts 后批量插入；append：仅插入，冲突忽略。(CRUD) 事务内执行，异常 rollback + raise。except PermissionDeniedException：先 logger.warning，再 403/3002。except NotFoundException：先 logger.warning，再 404/2001。except 参数/业务校验异常：先 logger.warning，再 400/4001。

#### 4.3.2 删除直播间单个公众号关联（管理员）

**Endpoint**: `DELETE /api/v1/admin/rooms/{room_id}/official_accounts/{account_id}`

**描述**: 删除某直播间的单个公众号关联。

**认证**: JWT + ADMIN/SUPERADMIN。

**路径参数**: room_id (UUID)、account_id (UUID)。

**成功响应**: 200。

**失败响应**: 2001 关联不存在；403 3002。

**实现流程**: (API) **try 前**提取 user_id、role、room_id、account_id。try 内调用 service.delete_room_official_account(db, user_id, role, room_id, account_id)。Service _check_admin_permission；CRUD 删除 (room_id, account_id)；不存在则 raise NotFoundException。except PermissionDeniedException：先 logger.warning，再 403/3002。except NotFoundException：先 `logger.warning(f"关联不存在: room_id={room_id}, account_id={account_id}")`，再 404/2001。

### 4.4 CSM 核心：按公众号查直播间列表

**Endpoint**: `GET /api/v1/official_accounts/{account_id}/rooms`

**描述**: 分页获取与该公众号关联的直播间列表，用于「该公众号仅看自己的直播间」。

**认证**: JWT + ADMIN/SUPERADMIN（本版仅管理员可调；后续可扩展为「当前用户与该公众号绑定」校验）。

**路径参数**: account_id (UUID)。

**Query**: page（默认 1）、size（默认 10，上限 100）。

**成功响应**: 200，data 为 PaginatedData[RoomBriefItem]（或与 v6 主文档一致的直播间简要结构）。

**失败响应**: 2001 公众号不存在；403 3002。

**实现流程**:
1. (API 层) Depends(get_current_user)、get_db；提前提取 user_id、role、account_id。
2. (API 层) try 内调用 service.get_rooms_by_account_id(db, user_id, role, account_id, page, size)。
3. (Service 层) _check_admin_permission(role)；校验 account_id 对应公众号存在且 is_active=true（否则 2001）；调用 CRUD：联表 live_room_official_accounts + live_rooms，WHERE account_id=，分页返回。
4. (CRUD 层) 总数查询 + offset/limit 列表查询，WHERE 条件一致；不做内存过滤。
5. (API 层) except PermissionDeniedException：先 `logger.warning(f"权限不足: user_id={user_id}")`，再 return JSONResponse(403, 3002)。except NotFoundException：先 `logger.warning(f"公众号不存在或已禁用: account_id={account_id}")`，再 return JSONResponse(404, 2001)。

---

## 5. 执行流程详细说明

### 5.1 公众号 CRUD 执行流程

- **创建**：API 接收 → JWT 验证 → 权限检查 → Pydantic 校验 → UUID 生成 → 唯一性检查 → CRUD 创建（事务 commit）→ 异常时 rollback + logger.error + raise → API 映射异常 → 返回响应。
- **更新**：API → JWT → 权限 → 查询公众号 → 解析更新字段 → 唯一性检查 → CRUD update → 触发器更新 updated_at → 返回。
- **删除（软）**：API → JWT → 权限 → 查询公众号 → CRUD update is_active=false → 返回。

### 5.2 直播间-公众号关联执行流程

- **获取直播间关联公众号列表**：API → 校验 room 存在 → CRUD 联表查询（room_id + official_accounts.is_active=true）→ 排序序列化 → 返回。
- **批量设置**：API → JWT → 权限 → 校验房间存在 → **仅当 account_ids 非空时**校验 account_ids 有效且启用 → CRUD 根据 mode replace/append（事务）→ 返回当前列表。
- **删除单条关联**：API → JWT → 权限 → CRUD 删除 (room_id, account_id) → 不存在则 2001 → 返回。

### 5.3 按公众号查直播间列表（CSM）

- API → JWT → 权限 → Service 校验公众号存在且启用 → CRUD 联表 live_room_official_accounts + live_rooms，WHERE account_id=，分页（total + items）→ 返回。

---

## 6. 错误处理与事务管理

- **与主文档 B 完全一致**：业务异常使用业务状态码（2xxx、3xxx、4xxx）；系统异常 1002；数据库 IntegrityError → 2002；外键冲突 → 2003。
- **事务**：单表/多表均在 CRUD 层 try/except 内 commit/rollback；Service 层不控制事务。
- **API 层**：try 内调用 Service。各 except 块内**先** `logger.warning(...)`（或 ERROR 由 CRUD 层记录）**再** return JSONResponse：except PermissionDeniedException -> 403/3002；except NotFoundException -> 404/2001；except DatabaseIntegrityException -> 400/4001 或 2002；except DatabaseOperationException -> 500/1002；except Exception -> 500/1002。

---

## 7. 性能优化建议

- 索引：official_accounts(name, is_active)；live_room_official_accounts(room_id, account_id) 已建索引。
- 按公众号查直播间时使用分页，避免一次拉取过多；可考虑 Redis 缓存公众号列表（与 B 缓存策略一致）。

---

## 8. 测试建议

- **单元测试**：公众号 CRUD；live_room_official_accounts 的 replace/append、删除；get_rooms_by_account_id 分页与过滤。
- **集成测试**：GET/POST/DELETE 房间-公众号关联；GET 公众号下列直播间；权限未授权返回 403/3002；房间或公众号不存在返回 2001。
- **级联**：房间删除或公众号删除时，live_room_official_accounts 对应行 CASCADE 删除。

---

## 9. 错误码对照表

与主文档 B 逐项一致，下表为本模块所用子集：

| 错误码 | 说明           | 使用场景                     |
|--------|----------------|------------------------------|
| 200    | 成功           | 所有成功响应                 |
| 1002   | 系统错误       | 未预期系统异常               |
| 2001   | 资源不存在     | 公众号/房间/关联不存在       |
| 2002   | 资源已存在     | 公众号名称重复               |
| 2003   | 操作被禁止     | 业务规则禁止                 |
| 2004   | 资源已被修改   | 并发修改冲突（与 B 一致，本模块未用乐观锁时可不返回） |
| 3002   | 权限不足       | 非管理员访问管理接口         |
| 4001   | 参数校验失败   | 请求体/Query 校验失败、非法 UUID |
| 4011   | JWT Token 无效 | Token 过期或格式错误（由认证中间件返回，与 B 一致） |

---

## 10. 部署与监控建议

- 数据库迁移：创建 official_accounts、live_room_official_accounts 及索引、外键、触发器。
- 路由挂载：/api/v1/admin/official_accounts、/api/v1/admin/official_accounts/{account_id}（GET 详情）、/api/v1/rooms/{room_id}/official_accounts、/api/v1/admin/rooms/{room_id}/official_accounts、/api/v1/official_accounts/{account_id}/rooms。
- JWT 与权限配置与主文档 B 一致。

---

## 规范继承检查表

| 序号 | 规范类别         | 主文档 B 依据                    | 文档 A 继承情况 | 文档 A 正文位置 |
|------|------------------|----------------------------------|------------------|-----------------|
| 1    | 权限设计         | B 文档规范说明 §6                | ☑ 已继承         | 文档规范说明 §6、4. API |
| 2    | 日志规范         | B 设计要点与约定 §4.3、本文档 §8  | ☑ 已继承         | 本文档「8. 日志规范」 |
| 3    | 异常处理规范     | B §6 错误处理与事务管理、母版 2.9 | ☑ 已继承         | §6 错误处理与事务管理 |
| 4    | 编程规范         | B + 母版 2.6 学院派               | ☑ 已继承         | §5 执行流程、4. API 实现流程 |
| 5    | 安全规范         | B 设计要点与约定 §4              | ☑ 已继承         | 文档规范说明 §7 |
| 6    | 数据库规范       | B 设计要点与约定 §1、§2 DDL       | ☑ 已继承         | 设计要点与约定、2. DDL |
| 7    | 事务规范         | B §6.2、母版 2.6 CRUD 层          | ☑ 已继承         | §6 |
| 8    | API 规范         | B 文档规范说明 §1、§4 API         | ☑ 已继承         | 文档规范说明 §1、4. API |
| 9    | 软删除策略       | B 设计要点与约定 §3              | ☑ 已继承         | 设计要点与约定 |
| 10   | 用户身份提取     | B 文档规范说明 §4、§6.5           | ☑ 已继承         | 文档规范说明 §4 |
| 11   | CRUD/Service 分层| 母版 2.6                          | ☑ 已继承         | §5、4. API 实现流程 |
| 12   | 列表分页规范     | B + 母版 2.13                     | ☑ 已继承         | 4.1.1、4.4 |
| 13   | 列表筛选与搜索   | 母版 2.13.1（公众号列表支持 q/search_type） | ☑ 已继承 | 4.1.1 本列表字符串搜索字段 |
| 14   | 其他（主文档特有）| B 安全异步异常处理、日志脱敏      | ☑ 已继承         | §7、§8 |
