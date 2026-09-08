# 17 管理端直播间内容运营 MVP 模块设计文档（Admin Room Content Ops MVP）

**版本**: V1.3  
**日期**: 2026-08-08  
**状态**: ✅ 后端已落地；前端对接见《17-18-管理端与私密测播-前端对接文档》  
**基于**: 《后端设计文档模板》；《15-全站已实现功能全景地图…》；《16-D1》；《FRONTEND_IMPLEMENTATION_GUIDE》；《18-私密测播不公开通道-增量设计文档》；现网 `RoomService._check_write_permission`  
**原则**: **最简单 / 最友好 / 最快落地**——当前无法开播验收，**不做**强制结束/暂停等播控；P0 只解决「管理员找到任意直播间并改内容」。

> **与《18》的关系**：主播「测试连接 / 不公开测播」产品与 C 端 `is_private` 语义以《18》为准。本文只钉 **Admin 列表与改内容**；不扩展测播运营专页。  
> **前端仓库**: `D:\Programming\Live-Saas-Wechat` — 管理端页 `src/pages/admin/room/AdminRoomList.vue` / `AdminRoomEditDialog.vue`（列表 API 已接；文案需改为「不公开」）。

---

## ⚡ 最小落地方案（P0 只做这些）

> **现网已具备**：Admin/SUPERADMIN 对任意房间的标题/简介/封面/删房/Tab/科室/品牌/公众号/留言等写权限。  
> **P0 缺口**：运营缺少「一眼看到全站房间 + 房主」的友好列表（现 `GET /rooms` 列表字段过瘦，且非专用 Admin 入口）。
| P0 | 动作 | 说明 |
|----|------|------|
| 1 | Admin 全站房间列表 | **新增** `GET /api/v1/admin/rooms`（标题搜索 / 按房主筛 / 含 `owner_user_id` 等运营字段） |
| 2 | 改房间内容 | **全部复用**既有接口（见 §3.2 复用清单）；权限已是 Admin\|owner |
| 3 | 鉴权 | 列表用 `verify_admin_role`；写接口走现网 JWT + Service 上帝写权限 |
| 4 | 文档 + 自测 | 用 Admin Token 改**他人**房间内容的验收清单 |

| 明确不做（P0） | 原因 | 后置 |
|----------------|------|------|
| 强制结束直播 / 暂停 / 踢流 | 当前无法开播，测不了；且依赖 SRS | **附录 A（P1）**，开播链路通后再做 |
| 下架回放 / 取消预告专用包 | 同属播控；非「改内容」主诉求 | 附录 A |
| 新表 / 新状态枚举 | 无必要 | — |
| 封禁自动关播 | 《16-D1》钉死不做 | SOP |
| 重做一套「Admin 专用写接口」 | 现网写接口 Admin 已可调 | — |

> **阅读约定**：正文 = P0（列表增强 + 内容复用）。播控只在附录。验收只认文首 ⚡ 表。

### 相对前版的变更

| 从 | 到 |
|------|------|
| V1.0：场次播控 MVP | V1.1：砍掉播控 P0；改为房间内容运营；`GET /admin/rooms` |
| V1.1：称「私密」、未钉 C 端语义 | **V1.2**：`is_private` 对齐《18》「不公开」；文首互链；§1.4 管理端口径 |

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档专注于**管理端对他人直播间内容的运营能力（Admin Room Content Ops）**：

**包含能力（P0）**:
- **全站房间列表（Admin Room List）**: 管理员按标题/房主找到任意直播间（**含**不公开 / 测播间）
- **内容编辑（Content Edit）**: 标题、简介、封面、`is_private`（不公开）、Tab、科室、品牌、公众号、留言清理、删房等——**复用现网**
- **权限口径钉死**: Admin = 上帝写；无需冒充房主
**模块范围**:
- **0** 张新表
- **1** 个新 API（Admin 房间列表）
- **N** 个复用 API（清单见 §3.2）
- 自测清单（重点：改**他人**房）

### 2. 本文档的核心特点

- ✅ 不造第二套写接口
- ✅ 与现网 `_check_write_permission`（ADMIN/SUPERADMIN 放行）同向
- ✅ 前端：一个房间列表页 + 点进详情调既有编辑 API 即可
- ✅ 开播未通也不阻塞本包验收

### 3. 业务价值说明

- 运营可改任意主播直播间展示内容（标题/封面/Tab/挂靠等）
- 先解决「找得到、改得了」，播控等能开播后再补

### 1.4 与《18》对齐：`is_private` / 不公开 / 测播（V1.2）

> 产品与 C 端细则见《18-私密测播不公开通道-增量设计文档》。此处只写 **Admin / 客服口径**。

| 维度 | 口径 |
|------|------|
| 字段 | `is_private=true` = **不公开**（unlisted），不是「私聊」 |
| C 端发现 | 不进 homepage「直播 / 预告 / 回放」等广场列表（《18》P0） |
| C 端持链观看 | **有 roomId 即可看**，MVP **无观看密码**（《18》；相对旧「仅房主/Admin」） |
| Admin 列表 | **仍包含**不公开房；可用 `is_private` 筛选；测播间常见标题含「连接测试」 |
| Admin 读写 | 不变：上帝视角可读可改；不负责「测试连接」主路径（主播小程序能力） |
| 客服话术 | 「广场看不到，但拿到分享链接的人可以进小程序观看」 |

前端管理端筛选项文案建议：`不公开`（可副标注 `is_private`），避免只写「私密」造成与《18》误解。

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《后端设计文档模板》 | 📋 **结构模板** | 章节、响应、错误码 |
| 2 | 《15-全站已实现功能全景地图…》 | 📖 **现状** | 房间/Tab/分类/品牌等已实现面 |
| 3 | 《FRONTEND_IMPLEMENTATION_GUIDE》 | 📖 **写接口路径** | `/admin/rooms/...` 子资源 |
| 4 | 《06-直播间Tab管理》《01-科室》《07-留言》等 | 📖 **子模块** | 复用写接口语义 |
| 5 | 《16-D1》 | 📋 **约束** | 封禁≠关播；Admin 可管孤儿房 |
| 6 | 《07》Admin 前缀范例 | 📖 **鉴权** | `verify_admin_role` → `3003` |
| 7 | 《18-私密测播不公开通道…》 | 📖 **C 端语义** | `is_private` 不公开；homepage 过滤；测播双通道 |

**⚠️ 重要说明**:
- 服务：`live_core_service`；内部 `/api/v1/...`，网关常为 `/api/core/...`
- 房间 `user_id` = 房主 `public_id`
- JWT `role` 大写：`ADMIN` / `SUPERADMIN`
- 本包**不依赖**场次 `live` 状态即可验收
- Admin API **不**因《18》减少不公开房的可见性；C 端发现过滤见《18》

---

## 📖 文档规范说明

### 统一响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": { },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

### 统一分页格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "items": [ ]
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

### 统一认证规范

- **新列表接口**: `Depends(verify_admin_role)`（仅 ADMIN/SUPERADMIN）
- **复用写接口**: 现网 `get_current_user` + Service `_check_write_permission`（Admin 或 owner）
- **公开读**: 房间详情/公开列表保持不变

### JWT Token格式说明

```json
{
  "user_id": "uuid-string",
  "username": "superadmin",
  "role": "SUPERADMIN",
  "can_stream": true,
  "exp": 1717756800
}
```

### 业务状态码（本包触及）

| 状态码 | 说明 | 场景 |
|--------|------|------|
| `200` | 成功 | 列表 / 复用写成功 |
| `1002` | 数据库错误 | DB 异常 |
| `2001` | 资源不存在 | room 不存在 |
| `2004` / `2005` | 业务/内容安全 | 标题简介等触碰审核（沿用现网） |
| `3001` | 未授权 | Token 无效 |
| `3003` | 非管理员 | **仅**新列表接口 `verify_admin_role`（与留言 Admin 对齐） |
| `3002` | 权限不足 | 复用写接口上非 Admin 且非 owner（现网） |
| `4001` | 参数校验失败 | Query 非法 |

> 新列表统一 `3003`；复用写接口错误码**不改**，保持现网行为。

---

## 📋 V1.1 行动清单（Action Checklist）

| # | 行动项 | 涉及文件/模块 | 复杂度 | 参考章节 |
|---|--------|-------------|--------|---------|
| 1 | Schema：`AdminRoomQueryParams`、`AdminRoomListItem` | `schemas/` | ⭐ | §2 |
| 2 | CRUD/Service：Admin 全站房间分页（含不公开）、标题 ILIKE、按 `owner_user_id` 筛 | `crud/room.py` + `services/` | ⭐ | §3.1 |
| 3 | API：`GET /admin/rooms` + `verify_admin_role` | `endpoints/admin_rooms.py` | ⭐ | §3.1 |
| 4 | 路由挂载 `prefix="/admin"` | `api/v1/api.py` | ⭐ | — |
| 5 | 网关确认 `/api/core/admin/rooms` | 网关 | ⭐ | §11 |
| 6 | 集成测试：Admin 列表含他人房；REGULAR 403；写他人房标题成功 | `tests/` | ⭐⭐ | §10 |
| 7 | （无代码）整理前端对接：列表 → 详情 → 复用写 API | 前端/联调 | ⭐ | §3.2 / §11 |

**关键决策**:
- ✅ P0 **只新增列表**；不新增 `PATCH /admin/rooms/{id}`（避免双写路径）
- ✅ 改内容一律打现网 `/rooms/{id}`、`/admin/rooms/{id}/tabs|categories|brands|...`
- ✅ 播控（force-end 等）整包后置附录 A
- ✅ 列表必须返回 `owner_user_id`，否则运营无法定位主播

---

## 🎯 设计要点与约定

### 1.1 数据库

- **无 DDL**
- 沿用 `live_rooms`；列表可按需使用既有 `user_id` / `title` / `created_at` 索引

### 1.2 API

- 新：`GET /api/v1/admin/rooms`
- 写：全部复用，见 §3.2

### 1.3 与现网 `GET /rooms` 的关系

| | `GET /rooms` | `GET /admin/rooms`（本包） |
|--|--------------|---------------------------|
| 权限 | Optional Auth；Admin 可见不公开房 | **仅** Admin |
| 列表字段 | id/title/cover/parent/created_at | **加** owner、description、is_private（不公开）、updated_at 等 |
| 用途 | C 端/通用 | 运营后台 |

不废弃 `GET /rooms`；Admin 后台优先走新入口，避免把运营字段塞进公开列表。

### 1.4 安全分层

```python
# 新列表
Depends(verify_admin_role)  # 非 Admin → 403 code=3003

# 复用写（现网已有）
RoomService._check_write_permission:
    if role in ('ADMIN', 'SUPERADMIN'): return
    if room.user_id == user_id: return
    raise PermissionDeniedException  # → 常映射 3002
```

---

## 1. 数据库 Schema（DDL）

**本包无变更。**

---

## 2. Pydantic Schemas 定义

```python
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AdminRoomQueryParams(BaseModel):
    q: Optional[str] = Field(None, max_length=100, description="标题模糊搜索")
    owner_user_id: Optional[UUID] = Field(None, description="房主 public_id")
    is_private: Optional[bool] = Field(None, description="按不公开筛选；省略=全部（含测播间）")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class AdminRoomListItem(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    owner_user_id: UUID
    is_private: bool
    parent_room_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

> P0 **不**返回 `stream_key`（防运营台误泄露推流密钥；需要时走房主侧既有通道）。

---

## 3. API 接口设计

### 3.1 新增：全站房间列表（ADMIN）

**Endpoint**: `GET /api/v1/admin/rooms`  
**网关**: `GET /api/core/admin/rooms`

**描述**: 管理员分页查看全站直播间（含不公开 / 测播间），支持标题与房主过滤。

**认证**: `verify_admin_role`

**Query**:
- `q`：标题 `ILIKE`
- `owner_user_id`：精确匹配 `live_rooms.user_id`
- `is_private`：可选
- `page` / `size`

**成功响应** (`200`):

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 1,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": "11111111-2222-3333-4444-555555555555",
        "title": "骨科讲座",
        "description": "简介……",
        "cover_url": "http://localhost:8000/media/rooms/.../cover.jpg",
        "owner_user_id": "0e30b4ad-ee9e-4042-829b-812d734f1401",
        "is_private": false,
        "parent_room_id": null,
        "created_at": "2026-07-20T10:00:00Z",
        "updated_at": "2026-07-24T08:00:00Z"
      }
    ]
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

**失败**: `401/3001`；`403/3003`；`422/4001`

**执行流程**:

1. 接收 Query  
2. JWT + `verify_admin_role`  
3. 校验分页 / UUID  
4. 查询 `live_rooms`（**不过滤** `is_private`，除非 Query 指定）  
5. 可选 `title ILIKE`、`user_id = owner_user_id`  
6. `ORDER BY updated_at DESC, id DESC` 分页  
7. 拼接封面绝对 URL（与现 `GET /rooms` 同策略）  
8. 返回分页  

---

### 3.2 复用：修改直播间内容（无新接口）

> 以下路径为 **live_core 内部** `/api/v1/...`；经网关时多为 `/api/core/...`。  
> **权限**: Admin 已可操作**他人**房间（现网）。开发本包时以自测清单回归，发现缺口再单开补丁，不在本包预造双路径。

#### 3.2.1 房间本体

| 操作 | 方法路径 | 说明 |
|------|----------|------|
| 详情 | `GET /rooms/{room_id}` | Admin 可读不公开房 |
| 改标题/简介/`is_private` 等 | `PATCH /rooms/{room_id}` | body: `LiveRoomUpdate` |
| 上传封面 | `POST /rooms/{room_id}/cover` | multipart |
| 删除直播间 | `DELETE /rooms/{room_id}` | 级联见 D4；二次确认 |

#### 3.2.2 Tab / 科室 / 品牌 / 公众号 / 留言

| 操作 | 方法路径 | 权限口径（现网） |
|------|----------|------------------|
| Tab 列表/创建/改/删/图 | `/admin/rooms/{id}/tabs*`、`/admin/tabs/{tab_id}` 等 | Admin；部分另有 owner 镜像路径 |
| 设/删科室 | `POST/DELETE /admin/rooms/{id}/categories...` | 仅 Admin（见权限对照表） |
| 绑品牌 | `POST /admin/rooms/{id}/brands` | Admin（或现网规定的 owner） |
| 公众号关联 | `POST/DELETE /admin/rooms/{id}/official-accounts...` | Admin |
| 清空留言 | `DELETE /admin/rooms/{id}/messages` | Admin |
| 留言管理 | `GET/POST /admin/messages*` | Admin |

> 具体字段以各子模块设计文档 / `FRONTEND_IMPLEMENTATION_GUIDE` 为准；本包不重复定义 Schema。

#### 3.2.3 建议的前端操作流（友好、最快）

```
1. Admin 登录（superadmin）
2. GET /admin/rooms?q=关键字  → 选中房间
3. GET /rooms/{id}            → 详情回填
4. PATCH /rooms/{id}          → 改标题/简介
5. POST /rooms/{id}/cover     → 换封面
6. 按需调 Tab/科室/品牌/清留言
```

---

## 4. 执行流程详细说明

### 4.1 改他人房间标题（验收主路径）

```
1. 普通用户 A 已有房间 R（owner=A）
2. Admin 登录
3. GET /admin/rooms?owner_user_id=A → 见到 R
4. PATCH /rooms/{R} { "title": "运营修正标题" }
5. Service._check_write_permission：role=ADMIN → 放行
6. 内容安全校验（room_title）通过后写库
7. GET /rooms/{R} 标题已变
```

### 4.2 非 Admin 越权（回归）

```
用户 B（非 owner、非 Admin）PATCH /rooms/{R}
→ 403 / 3002
```

---

## 5. 错误处理与事务

- 新列表：只读；错误见 § 业务状态码  
- 复用写：沿用各接口既有事务与内容安全异常映射，本包不改  

---

## 6. 性能

- 强制分页；`q` 用 `ILIKE`  
- P0 不做缓存  
- 列表不 JOIN 场次状态（开播未通，避免无用复杂度）  

---

## 7. 测试建议

### 7.1 单元

- Admin 列表不过滤不公开房（与 C 端 homepage 相反，见《18》）  
- `owner_user_id` / `q` 过滤正确  
- 非 Admin 依赖抛 3003  

### 7.2 集成（核心）

- Admin PATCH **他人**房间标题成功  
- Admin 上传**他人**封面成功  
- REGULAR 调 `GET /admin/rooms` → 403  

### 7.3 不测（P0）

- force-end、暂停、真实推流关播  

---

## 8. 错误码对照表

| 错误码 | 说明 |
|--------|------|
| `200` | 成功 |
| `1002` | 数据库错误 |
| `2001` | 房间不存在（复用写） |
| `3001` | 未授权 |
| `3002` | 复用写：非 Admin 且非 owner |
| `3003` | 新列表：非管理员 |
| `4001` | 参数校验失败 |

---

## 9. 部署与监控

### 9.1 检查清单

- [ ] 无 DB 迁移  
- [ ] `/admin/rooms` 已挂载且网关可达  
- [ ] 超管测试账号可用（《测试账号信息.md》）  
- [ ] 用 Admin Token 对他人房走通 PATCH 标题  

### 9.2 监控

- `GET /admin/rooms` 延迟  
- Admin 写他人房的审计日志（可选 INFO：`admin=.. room=.. action=patch`）——P0 不强制改现网 PATCH，有则加、无则后置  

---

## ✅ 自测清单（Self-Test Checklist）

### 10.1 新列表

| # | 测试项 | 预期 | 结果 |
|---|--------|------|------|
| 1 | 无 Token → `GET /admin/rooms` | 401 / 3001 | `[x]` 网关冒烟 2026-07-24 |
| 2 | REGULAR → 同接口 | 403 / 3003 | `[x]` testemail → 403 |
| 3 | ADMIN 无筛选 | 含他人房 + 不公开房 | `[x]` superadmin total=9 |
| 4 | `q=标题` | 模糊命中 | `[ ]` 集成测试已写，待容器内 pytest |
| 5 | `owner_user_id=` | 仅该主播房间 | `[ ]` 集成测试已写 |
| 6 | items 含 `owner_user_id`、`updated_at` | 字段齐全 | `[x]` |
| 7 | **不**返回 `stream_key` | 响应无该字段 | `[x]` |

### 10.2 改内容（他人房间，核心）

| # | 测试项 | 预期 | 结果 |
|---|--------|------|------|
| 8 | Admin `PATCH` 他人房 `title` | 200，标题更新 | `[x]` 冒烟后已还原标题 |
| 9 | Admin `PATCH` 他人房 `description` | 200 | `[ ]` |
| 10 | Admin `POST` 他人房 cover | 200，封面变 | `[ ]` |
| 11 | Admin 改他人房 Tab（创建/改） | 200 | `[ ]` |
| 12 | Admin 设他人房科室 | 200 | `[ ]` |
| 13 | Admin 清空他人房留言 | 200 | `[ ]` |
| 14 | 非 owner 的 REGULAR `PATCH` 他人房 | 403 / 3002 | `[ ]` 集成测试已写 |
| 15 | 敏感词标题 | 现网内容安全拦截（2004/2005） | `[ ]` |

### 10.3 明确跳过（开播未通）

| # | 项 | 说明 |
|---|----|------|
| — | force-end / 暂停 / 踢流 | 附录 A，本阶段不测 |
| — | 真实推流开播关播 | 依赖开播链路 |

---

## 11. 前端对接速查

> **完整清单**：[`17-18-管理端与私密测播-前端对接文档.md`](./17-18-管理端与私密测播-前端对接文档.md)  
> **实现指南**：[`FRONTEND_IMPLEMENTATION_GUIDE.md`](./FRONTEND_IMPLEMENTATION_GUIDE.md) §十七

| 步骤 | 调用 |
|------|------|
| 列表 | `GET /api/core/admin/rooms?q=&owner_user_id=&is_private=&page=&size=` |
| 详情 | `GET /api/core/rooms/{id}` |
| 改文案 | `PATCH /api/core/rooms/{id}`（含 `is_private`） |
| 换封面 | `POST /api/core/rooms/{id}/cover` |
| Tab/科室/品牌/留言 | 既有 `/api/core/admin/rooms/{id}/...` |
| 删房 | `DELETE /api/core/rooms/{id}`（慎用） |

**UI 文案**：筛选项 / 标签统一「不公开」（勿只写「私密」）。列表**不**展示 `stream_key`。

| 小程序文件 | 状态 |
|------------|------|
| `src/config/api.ts` → `ADMIN.ROOMS` | ✅ 已接 |
| `AdminRoomList.vue` | ✅ 列表已接；✅ 文案「不公开」 |
| `AdminRoomEditDialog.vue` | ✅ 改内容已接；✅ 提示对齐 unlisted |

账号：`superadmin` / 见《测试账号信息.md》。

---

## 12. 文档自测记录（撰稿口径）

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | P0 对齐用户诉求「改内容、暂不测关播」 | ✅ |
| 2 | 仅 1 个新 API，写全复用 | ✅ |
| 3 | 与 V1.0 播控方案切割清晰（附录 A） | ✅ |
| 4 | 列表补 `owner_user_id` 解决「找不到房」 | ✅ |
| 5 | 不泄露 `stream_key` | ✅ |
| 6 | 错误码：新列表 3003 / 复用写保持 3002 | ✅ |
| 7 | 不依赖开播即可验收 | ✅ |
| 8 | 与《16-D1》封禁不关播不冲突 | ✅ |

---

## 附录 A（P1，开播通后再做）— 播控

> 原 V1.0 内容整体后置，**非本阶段范围**。

| 能力 | 建议接口 | 备注 |
|------|----------|------|
| 全站场次三态列表 | `GET /admin/sessions?bucket=` | scheduled/live/replay |
| 强制结束 | `POST /admin/sessions/{id}/force-end` | `live→finished`；可选 SRS kick |
| 下架回放 | `POST /admin/sessions/{id}/hide-replay` | 清空 `playback_url` |
| 取消预告 | 复用 `DELETE /sessions/{id}` | 禁止删 live |
| 暂停/恢复 | 未定 | 需产品+SRS |

开播链路就绪后，可另开 `17-P1` 增量文档，从本附录升级为正文。

---

## 附录 B — API 速查

| 类型 | 路径 | 方法 | 权限 | 说明 |
|------|------|------|------|------|
| **新增** | `/api/v1/admin/rooms` | GET | ADMIN | 全站房间列表 |
| 复用 | `/api/v1/rooms/{id}` | GET/PATCH/DELETE | Admin\|owner（读可见性另规） | 详情/改/删 |
| 复用 | `/api/v1/rooms/{id}/cover` | POST | Admin\|owner | 封面 |
| 复用 | `/api/v1/admin/rooms/{id}/...` | * | 见子模块 | Tab/科室/品牌/公众号/留言 |

网关将 `/api/v1` 换为 `/api/core`（以现网网关为准）。

---

## 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-24 | 首版：场次播控 MVP（force-end 等） |
| V1.1 | 2026-07-24 | **转向内容运营**：播控后置；P0=Admin 房间列表+复用改内容 |
| V1.2 | 2026-08-08 | 对齐《18》：`is_private`=不公开；Admin 仍可见测播间；§1.4 口径；文首互链；不改 Admin API 形态 |
| V1.3 | 2026-08-08 | 后端已落地；§11 同步小程序现网文件与「不公开」文案；互链《17-18 前端对接文档》 |
