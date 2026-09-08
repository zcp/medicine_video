# 直播间与公众号关联 - Pydantic 模型代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-02  
**基于设计文档**: 《直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档》V1.0  
**目标文件**: `backend/live_core_service/app/schemas/liveroom_official_accounts.py`

---

## 1. 角色定义 (Role Definition)

你是一名精通 Pydantic v2 与 FastAPI 的资深后端工程师。你的任务是根据设计文档生成**直播间与公众号关联**模块的 Pydantic Schema 代码，用于 API 请求校验与响应序列化，与同模块 SQLAlchemy 模型及设计文档中的 Schema 定义**完全一致**。

**核心要求**：
- 使用 **Pydantic v2** 语法：`model_config = ConfigDict(from_attributes=True)`，`Field`、`field_validator` 等
- **初始开发模式**：新建独立文件 `liveroom_official_accounts.py`，不修改现有 Schema 文件
- 与设计文档 §3 的 Official_Accounts、Live_Room_Official_Accounts、按公众号查房间分页响应结构一致
- 若项目已有 `PaginatedData`（如 content_management），可复用并从中导入；否则在本文件定义泛型 `PaginatedData[T]`

---

## 2. 任务目标 (Task Objective)

- **生成文件**: `backend/live_core_service/app/schemas/liveroom_official_accounts.py`
- **生成 Schema 清单**:
  - **公众号**: OfficialAccountBase, OfficialAccountCreate, OfficialAccountUpdate, OfficialAccountItem
  - **分页**: PaginatedData（若未在它处定义则在本文件定义 Generic[T]）
  - **管理端列表响应**: OfficialAccountAdminListResponse（data 为 PaginatedData[OfficialAccountItem]）
  - **直播间-公众号关联**: LiveRoomOfficialAccountsSetRequest, LiveRoomOfficialAccountsSetResponse, LiveRoomOfficialAccountsListResponse
  - **按公众号查房间（CSM）**: RoomBriefItem（直播间简要字段：id、name、slug 等，与 v6 主文档一致）；分页响应使用 PaginatedData[RoomBriefItem]，统一 code/message/data/timestamp 的包装可由 API 层处理，Schema 层提供 data 结构即可
- **用途**: 供管理端公众号 CRUD、按直播间查/设公众号、按公众号分页查直播间等接口使用

---

## 3. 核心上下文信息 (Core Context Information)

### 3.1 项目文件结构 (Project File Structure)

```
live_core_service/app/schemas/
  __init__.py                    # 需在末尾追加本模块导出，最小改动
  content_management.py          # 参考 Tag/Category/PaginatedData 等风格，不修改
  liveroom_official_accounts.py  # 【新建】本模块
```

### 3.2 现有代码参考 (Existing Code Reference)

参考 `app/schemas/content_management.py`：
- Pydantic v2：`model_config = ConfigDict(from_attributes=True)`；`Field(..., min_length=1, max_length=80)` 等
- 名称校验：`@field_validator('name')` 中 strip 并禁止 `[<>\'";]`
- Base / Create / Update / Item 命名与字段分工（Create 含 is_active 等可选默认；Update 全可选）
- 列表响应：`List[TagItem]`、分页用 `PaginatedData`（若存在）
- 设计文档中已给出 OfficialAccountBase/Create/Update/Item、PaginatedData、OfficialAccountAdminListResponse、LiveRoomOfficialAccountsSetRequest/SetResponse/ListResponse 的代码片段，须与设计文档一致并补全必要 import 与 RoomBriefItem

### 3.3 设计文档 Schema 提取（须与设计文档 §3 一致）

#### 3.3.1 Official_Accounts Schemas

- **OfficialAccountBase**: name(必填, 1–100), slug(可选, 120), app_id(可选, 255), description(可选, 500)；name 校验 strip 且禁止 `[<>\'";]`
- **OfficialAccountCreate**: 继承 Base，增加 is_active: Optional[bool] = True
- **OfficialAccountUpdate**: 部分更新，各字段 Optional；name/slug/app_id/description/is_active
- **OfficialAccountItem**: 继承 Base，含 id(UUID)、is_active、created_at、updated_at；`model_config = ConfigDict(from_attributes=True)`
- **PaginatedData**: Generic[T]，total, page, size, items: List[T]
- **OfficialAccountAdminListResponse**: code=200, message="success", data: PaginatedData[OfficialAccountItem], timestamp

#### 3.3.2 Live_Room_Official_Accounts Schemas

- **LiveRoomOfficialAccountsSetRequest**: account_ids: List[uuid.UUID], min_length=1, max_length=50；mode: Literal["replace","append"]="replace"；account_ids 需去重校验（自定义 validator）
- **LiveRoomOfficialAccountsSetResponse**: code, message, data: dict（含 room_id, mode, accounts: List[OfficialAccountItem]）, timestamp
- **LiveRoomOfficialAccountsListResponse**: code, message, data: List[OfficialAccountItem], timestamp

#### 3.3.3 按公众号查直播间列表（CSM）

- **RoomBriefItem**: 直播间简要信息，与 v6 主文档一致，至少包含 id(UUID)、name、slug（可选其他简要字段如 status 等，按主文档或现有 live_core 的直播间简要结构）
- 分页响应：`PaginatedData[RoomBriefItem]`；若 API 层需要完整响应体 Schema，可增加例如 `OfficialAccountRoomsListResponse`：code, message, data: PaginatedData[RoomBriefItem], timestamp

### 3.4 技术栈

- Python 3.9+
- Pydantic v2
- typing: Optional, List, Literal, TypeVar, Generic；uuid, datetime

### 3.5 与 SQLAlchemy 模型的对应

- 本模块模型文件：`app/models/liveroom_official_accounts.py`（OfficialAccount, LiveRoomOfficialAccount）
- OfficialAccountItem 等需能从 ORM 实例序列化（from_attributes=True）
- 唯一性（如 name）在业务/CRUD 层保证，Schema 不负责唯一性校验

---

## 4. 代码生成具体要求 (Specific Code Generation Requirements)

### 4.1 导入与泛型

- 从 pydantic 导入：BaseModel, Field, ConfigDict, field_validator
- typing：Optional, List, Literal, TypeVar, Generic
- 标准库：uuid, datetime, re（用于 name 校验）
- 若 PaginatedData 已在 content_management 定义：`from app.schemas.content_management import PaginatedData`，避免重复定义；否则在本文件定义 `T = TypeVar('T')` 与 `class PaginatedData(BaseModel, Generic[T]): ...`

### 4.2 字段与校验

- 字符串长度：严格按设计文档 max_length（name 100, slug 120, app_id 255, description 500）
- OfficialAccountUpdate 所有字段 Optional
- LiveRoomOfficialAccountsSetRequest：account_ids 唯一性用 `@field_validator` 检查 `len(v) != len(set(v))` 时 raise ValueError

### 4.3 安全与规范

- 不在 Field description 或文档字符串中写真实敏感信息
- 列表长度限制：account_ids max_length=50；PaginatedData 的 items 由分页 size 控制即可

### 4.4 增量开发（初始模式）

- **仅新建** `app/schemas/liveroom_official_accounts.py`
- **仅修改** `app/schemas/__init__.py`：在**文件末尾**追加本模块导出（OfficialAccountBase, OfficialAccountCreate, OfficialAccountUpdate, OfficialAccountItem, PaginatedData（若本文件定义）, OfficialAccountAdminListResponse, LiveRoomOfficialAccountsSetRequest, LiveRoomOfficialAccountsSetResponse, LiveRoomOfficialAccountsListResponse, RoomBriefItem, 以及按需的 OfficialAccountRoomsListResponse 等），格式与现有导入一致
- 若 PaginatedData 从 content_management 导入，则 __init__.py 不必再导出 PaginatedData（除非希望在本模块命名空间也暴露）

---

## 5. 完整性检查清单 (Completeness Checklist)

- [ ] OfficialAccountBase/Create/Update/Item 与设计文档 §3.1 一致；name 校验 strip 与特殊字符
- [ ] PaginatedData 已存在则复用，否则本文件定义 Generic
- [ ] OfficialAccountAdminListResponse 含 PaginatedData[OfficialAccountItem]
- [ ] LiveRoomOfficialAccountsSetRequest：account_ids 唯一性校验；mode replace/append
- [ ] LiveRoomOfficialAccountsSetResponse、LiveRoomOfficialAccountsListResponse 与设计文档一致
- [ ] RoomBriefItem 定义（id, name, slug 等）；按公众号查房间分页使用 PaginatedData[RoomBriefItem]
- [ ] 所有 Response 类含 code, message, data, timestamp（与设计文档一致）
- [ ] __init__.py 仅末尾追加导入，无重复、无格式破坏

---

## 6. 最终交付 (Final Deliverable)

1. 生成完整可运行的 `app/schemas/liveroom_official_accounts.py`，可直接放入项目。
2. 在 `app/schemas/__init__.py` 末尾追加本模块需对外使用的 Schema 导入列表。
3. 说明：生成的 Schema 与 `app/models/liveroom_official_accounts.py` 配合使用；先完成数据库模型再生成本 Schema。

**使用顺序**：在《直播间与公众号关联---数据库模型代码生成提示词》生成的模型代码合入后，再使用本文档生成 Pydantic Schema。
