# 管理端用户管理 / 账号能力模型与权限修订设计文档（V2）

**版本**: V2.2  
**日期**: 2026-08-07  
**状态**: ✅ 已落地；V2.2 产品裁剪：仅保留专家与品牌主体  
**基于**: 《14-管理端用户管理-后端设计文档.md》(V1.0)、《10-用户认证与管理-后端设计文档.md》(V1.2)、《用户模块设计文档.md》(V4.0)  
**关联**: 专家模块（`live_core_service`）、品牌模块（`live_core_service`）

---

## ⚠️ V2.2 产品裁剪（2026-08-07，以本节为准）

| 能力 | 决策 | 说明 |
|------|------|------|
| 专家页（公开详情/列表/关注） | **保留** | Admin CRUD 维护档案 |
| Admin 维护专家档案（含可选 `experts.user_id` 绑定） | **保留** | 运营侧绑定，**无** C 端自编辑 |
| **专家认领** `/experts/me*` 自编辑/自管头像 | **❌ 不做 / 已下线** | 永久裁剪 |
| 品牌主体（品牌 CRUD、挂房/挂专题） | **保留** | |
| **品牌成员** `brand_members` / `/brands/me` | **❌ 不做 / 已下线** | 表 DROP |
| **品牌货架商品** `brand_products` / `/admin/brand-products` | **❌ 不做 / 已下线** | 表 DROP；非电商货架 |

下文凡写「P1 专家认领」「P2 品牌成员/货架商品」处，以本节为废止声明；实现以代码为准。

---

## ⚠️ V2.1 产品修订（2026-07-30，以本节为准）

| 项 | V2.0 原语义 | V2.1 现行 |
|----|-------------|-----------|
| 默认 | `can_stream=false`（需运营授予） | `can_stream=true`（人人默认可播） |
| Admin 操作 | 「授予 / 撤销开播权」 | 「禁止开播 / 恢复开播」（紧急开关，日常以封禁为主） |
| `can_stream=false` | 未开通 | 被禁止开播 |
| 建房拒绝文案 | 未开通开播资格 | 开播功能已被禁用 |
| JWT 缺字段 | 视为 false | 视为 true |
| 存量 | 需批量授出 | 迁移一次性 `UPDATE … SET true`；已登录用户 refresh 一次即可 |

**不变**：字段与 Admin PATCH API 保留；`true→false` 仍吊销会话；封禁 / 角色主链路不动。

---

## ⚠️ 文档定位与命名说明

### 为何不叫「纯增量」？

V1（《14-管理端用户管理》）已描述并落地 **列表 + PATCH role/status**。本次不只是加几个字段，而是：

| 变更性质 | 内容 |
|----------|------|
| 【修订】 | 身份/能力模型：开播权与平台角色分离 |
| 【修订】 | ADMIN / SUPERADMIN 职责边界（做实差异或避免空转） |
| 【废弃/降级】 | 管理端日常暴露 `MODERATOR`、随意设 `PENDING_REVIEW` 等 |
| 【新增】 | `can_stream`、会话吊销联动、运营检索、专家认领、品牌成员与货架商品 |

因此采用 **「V2 修订设计」** 命名，而非模板意义上的「只新增不改基线」。

### 推荐文件名（可讨论）

| 候选名 | 含义 | 建议 |
|--------|------|------|
| `14-…-V2-账号能力模型与权限修订设计文档.md` | 强调修订 V1 身份模型 + 权限 | ✅ **采用（本文档）** |
| `14-…-V2-增量设计文档.md` | 易被理解成「V1 全保留仅叠加」 | ❌ 易误导 |
| `15-平台账号能力与业务主体设计文档.md` | 跳出「仅管理端」，覆盖专家/品牌 | 若后续拆文档可用；本轮仍挂 14 系列便于追溯 |

**阅读约定**:

- 与 V1 **冲突时，以本文档为准**
- V1 中仍有效部分：网关前缀 `/api/users/admin/`、统一响应结构、分页约定、会员产品/订阅 Admin API（本 V2 不改会员体系）

---

## 📌 核心定位说明

### 1. 本文档解决什么问题

医学直播 SaaS + 微信小程序场景下，运营与用户需要：

1. **默认可开播，必要时禁止** → `can_stream` 与角色正交；禁止开播**不能**因此变成改角色；日常停人用封禁  
2. **专家** = 简介页主体 + 可选绑登录账号 → 绑定后可自管资料；未绑定仅运营改  
3. **品牌商**可登录上架可售商品 → 品牌成员关系 + 商品 CRUD；**平台 Admin 也能管已上架商品**  
4. **ADMIN / SUPERADMIN** 若无实质差异则空转 → 做实「干活 vs 管钥匙」，或明确收敛策略  
5. **封禁 / 禁止开播立刻生效** → 复用会话吊销，避免 Token 窗口期仍可直播互动  

### 2. 能力分层总览（必读）

```text
┌─────────────────────────────────────────────────────────────┐
│  users.role（平台运维身份，尽量少）                            │
│    REGULAR | ADMIN | SUPERADMIN                               │
│    （MODERATOR：库内保留，管理端日常隐藏，本 V2 不启用）         │
├─────────────────────────────────────────────────────────────┤
│  users.can_stream（能力开关，与 role 正交；V2.1 默认 true）   │
│    true  = 可开播（普通用户默认；仍是 REGULAR，无后台运维权）   │
│    false = 被禁止开播（运营紧急开关，不封号）                   │
├─────────────────────────────────────────────────────────────┤
│  experts（业务主体：专家简介页）                               │
│    experts.user_id 可选绑定 → 登录后可认领/自编辑              │
├─────────────────────────────────────────────────────────────┤
│  brands + brand_members + brand_products（业务主体：品牌货架）  │
│    成员可自助上架；Admin 可管理全部已上架商品                     │
└─────────────────────────────────────────────────────────────┘
```

**明确禁止**:

- ❌ 用 `role=MODERATOR/BROADCASTER/EXPERT/BRAND` 表达开播、专家、品牌商  
- ❌ 给主播/专家/品牌成员升 `ADMIN` 才能干活  
- ❌ 认为改 `users` 表就等于改了专家页/品牌货架（各写各表）

### 3. 分 Phase 交付（最小可落地）

| Phase | 目标 | 服务 | 优先级 |
|-------|------|------|--------|
| **P0** | `can_stream` + 创建直播间校验 + JWT 声明 + Admin 禁止/恢复开播 | users + live_core | 必须先做（V2.1：默认 true） |
| **P0** | 封禁/禁止开播/降权 → 会话吊销；live_core 认 Redis | users + live_core | 必须先做 |
| **P0** | Admin 护栏：禁改自己；日常 status 白名单；检索手机号/昵称 | users | 必须先做 |
| **P0** | ADMIN/SUPERADMIN 职责做实（改 role 仅超管） | users | 必须先做 |
| **P1** | 专家认领：`GET/PATCH /experts/me`、头像可选同步 users | live_core (+ users 可选) | 体验闭环 |
| **P2** | 品牌成员 + 品牌商品 CRUD；Admin 管全部商品 | live_core | 电商货架 |

---

## 📚 依赖与影响范围

| 序号 | 文档/模块 | 关系 |
|------|-----------|------|
| 1 | 《14-管理端用户管理-后端设计文档》V1 | **被修订基线** |
| 2 | 《10-用户认证与管理》+ 会话吊销（`user_sessions_revoked`） | JWT / 吊销复用 |
| 3 | live_core 房间创建、推流相关 | 开播门禁 |
| 4 | live_core 专家模块 | P1 认领与自编辑 |
| 5 | live_core 品牌模块（现有 `brands`） | P2 扩展成员与商品 |

**网关约定（不变）**:

- 用户/Admin 用户：`/api/users/...` → `user_service`
- 专家/品牌/直播：`/api/core/...` → `live_core_service`

---

## 📋 需求与内容清单（本次讨论汇总）

> 以下为完整清单，开发/评审按此勾选。标注 【V1 已有】【修订】【新增】。

### A. 账号与平台角色

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| A1 | 平台角色仅服务「能否进运维后台」 | 【修订】 | 日常产品语言：普通人 / 管理员；库内可保留 SUPERADMIN |
| A2 | `MODERATOR` 管理端隐藏、不赋予新权 | 【修订】 | 房管未来用「房间成员关系」，不用全局 role |
| A3 | `SUPERADMIN` 与 `ADMIN` 做实差异 | 【修订】 | 仅超管可改 `role`、任命/解除管理员；ADMIN 不可碰 SUPERADMIN（V1 已有） |
| A4 | 禁止管理员 PATCH 自己 | 【新增】 | 防自封/自降权锁死后台 |
| A5 | 日常 status 仅 `NORMAL`↔`BANNED` | 【修订】 | `PENDING_REVIEW`/`REJECTED`/`DELETED` 不作为运营主按钮 |

### B. 开播能力（非身份）

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| B1 | `users.can_stream` 默认 `true`（V2.1） | 【修订】 | 默认可开播；false=禁止开播 |
| B2 | 可开播用户 = `REGULAR` + `can_stream=true`（默认即是） | 【修订】 | 无运维能力 |
| B3 | Admin 可禁止/恢复开播 | 【修订】 | PATCH，与改管理员分离；日常以封禁为主 |
| B4 | 创建直播间校验 `can_stream`（false 拒绝） | 【新增】 | ADMIN/SUPERADMIN 可旁路自测（可配置） |
| B5 | 已有房间：禁止开播后仍可管理/结束旧房，不可新建 | 【新增】 | 友好过渡 |
| B6 | JWT 含 `can_stream`；缺省视为 true（V2.1） | 【修订】 | 与默认可播一致 |

### C. 安全与即时生效

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| C1 | 封禁时吊销会话 | 【新增】 | 复用 `_revoke_user_sessions` |
| C2 | 禁止开播（`can_stream→false`）、降权时吊销会话 | 【修订】 | 避免旧 JWT 仍可建房 |
| C3 | live_core 校验 `user_sessions_revoked:{user_id}` | 【新增】 | 与 users 共用 Redis Key |
| C4 | 不在用户管理里自动关房/轮换 stream_key | 【明确不做】 | 运营 SOP 或后续独立工具 |

### D. 管理端检索与联调

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| D1 | 列表筛 `phone_number`（精确）、`nickname`（模糊） | 【新增】 | 对齐微信/手机号运营 |
| D2 | 列表返回 `can_stream` | 【新增】 | |
| D3 | 前端路径/枚举对齐 | 【修订】 | `/api/users/admin/users`；`NORMAL`/`BANNED`；`REGULAR` 非 `USER`/`active` |

### E. 专家（业务主体，非 role）

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| E1 | 专家 ≠ `users.role` | 【明确】 | `experts` 表是简介页真相源 |
| E2 | `experts.user_id` 绑定登录账号 | 【代码已有】 | 一对一可选（非 Doc14 V1 范围，属 live_core 专家表） |
| E3 | 登录后 `GET /experts/me` 判定「我是哪个专家」 | 【新增】 | |
| E4 | 绑定用户可 `PATCH /experts/me`、上传自己的专家头像 | 【新增】 | 未绑定仅 Admin |
| E5 | 保存专家头像可选同步 `users.avatar_url` | 【新增】 | 友好选项，默认建议同步或提供勾选 |
| E6 | 专家列表/详情读 `experts` 同行 | 【明确】 | 改专家页即更新列表，不必另刷身份表 |
| E7 | 绑专家 ≠ 自动 `can_stream` | 【明确】 | 开播另授 |

### F. 品牌商与可售商品（业务主体，非 role）

| # | 条目 | 类型 | 说明 |
|---|------|------|------|
| F1 | 现有 `brands` 仍是品牌主体 | 【代码已有】 | Logo/专题/挂房等展示（非 Doc14 V1 范围） |
| F2 | 新增 `brand_members`（品牌↔用户） | 【新增】 | 成员仍是 REGULAR |
| F3 | 新增 `brand_products`（品牌货架可售商品） | 【新增】 | 上架≠导 SQL；走 API+表单 |
| F4 | 品牌成员可对自己品牌商品 CRUD | 【新增】 | 前端「品牌工作台」 |
| F5 | **平台 Admin 可管理任意已上架商品** | 【新增】 | 审核/下架/编辑 |
| F6 | 品牌成员 ≠ ADMIN | 【明确】 | 权限看 membership，不看 role |

### G. 明确不在本 V2 范围

| # | 条目 | 说明 |
|---|------|------|
| G1 | 批量导出用户、完整审计表 | 可后续；现有日志保留 |
| G2 | 封禁自动切断推流/关房 | 跨服务风险大 |
| G3 | 房间级房管（MODERATOR 真正启用） | 另开「房间成员」设计 |
| G4 | 支付进件、分账、完整商城交易 | P2 仅货架 CRUD，交易另立项 |
| G5 | 多租户 `tenant_id` | 当前单租户 |

---

## 🔍 问题与决策记录

### 问题 1：人人均可开播（P0）

**现象**: `create_new_room` 不校验开播资格，任意登录用户可建房。  
**决策**: 【采用】`can_stream` 布尔能力开关，**不**新增角色枚举。

### 问题 2：封禁/撤权不即时（P0）

**现象**: Admin PATCH `BANNED` 不吊销会话；live_core 只验 JWT。  
**决策**: 【采用】写 `user_sessions_revoked` + live_core 读同一 Key；不引入全量用户表跨库查询。

### 问题 3：ADMIN / SUPERADMIN 空转（P0）

**现象**: 业务 API 二者等同，仅「碰超管」有差。  
**决策**: 【采用】做实差异：`ADMIN` 可封禁、授开播权、管内容；**仅 `SUPERADMIN` 可修改 `role`（任命/解除管理员）**。不在本阶段删除枚举，以免破坏已有账号数据。

### 问题 4：专家登录如何认领（P1）

**现象**: 有 `user_id` 字段，无「我的专家页」自助 API。  
**决策**: 【采用】`/experts/me` 认领与编辑；未绑定仅 Admin；头像可选同步用户表。

### 问题 5：品牌商上架可售商品（P2）

**现象**: 仅有展示型 `brands`，无成员与货架商品；运营误以为要导库。  
**决策**: 【采用】`brand_members` + `brand_products` + 成员端 API + Admin 全局商品管理；**禁止** `role=BRAND`。

---

## 1. 数据库设计

### 1.1 【新增字段】`users.can_stream`

```sql
-- user_service / users（V2.1）
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS can_stream BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE users ALTER COLUMN can_stream SET DEFAULT TRUE;
UPDATE users SET can_stream = TRUE WHERE can_stream = FALSE;

COMMENT ON COLUMN users.can_stream IS '默认 true 可开播；false 表示被禁止开播；与 role 正交';

DROP INDEX IF EXISTS idx_users_can_stream;
CREATE INDEX IF NOT EXISTS idx_users_can_stream ON users(can_stream)
  WHERE can_stream = FALSE;
```

### 1.2 【修订语义】角色与状态（不改枚举值，改管理策略）

| 字段 | V2 策略 |
|------|---------|
| `role` | 管理端日常：`REGULAR` / `ADMIN`；`SUPERADMIN` 仅超管可见可设；`MODERATOR` 隐藏 |
| `status` | 运营主路径：`NORMAL` / `BANNED`；其它状态非主按钮 |

### 1.3 【新增表】专家认领无新表（复用 `experts`）

P1 仅增加接口与权限，DDL 不变。可选：绑定唯一约束 V1 已有 `user_id UNIQUE`。

### 1.4 【新增表】`brand_members`（P2）

```sql
CREATE TABLE brand_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id        UUID NOT NULL REFERENCES brands(id),
    user_id         UUID NOT NULL,  -- users.public_id，应用层校验
    member_role     VARCHAR(32) NOT NULL DEFAULT 'EDITOR',
    -- EDITOR: 可编辑品牌资料与商品；OWNER: 可管理成员（可选，首版可只用 EDITOR）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brand_id, user_id)
);

CREATE INDEX idx_brand_members_user_id ON brand_members(user_id);
CREATE INDEX idx_brand_members_brand_id ON brand_members(brand_id);
```

### 1.5 【新增表】`brand_products`（P2）

```sql
CREATE TYPE brand_product_status AS ENUM (
    'DRAFT', 'ON_SALE', 'OFF_SALE', 'DELETED'
);

CREATE TABLE brand_products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id        UUID NOT NULL REFERENCES brands(id),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    cover_url       VARCHAR(512),
    price           NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency        VARCHAR(8) NOT NULL DEFAULT 'CNY',
    external_url    VARCHAR(512),  -- 首版可外链购买；站内支付另立项
    status          brand_product_status NOT NULL DEFAULT 'DRAFT',
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_by      UUID,          -- 创建者 public_id
    updated_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_brand_products_brand_id ON brand_products(brand_id);
CREATE INDEX idx_brand_products_status ON brand_products(status);
```

> 注：首版「可售」以 **货架展示 + 外链/后续支付** 为主，避免本 V2 绑定完整支付中台。

---

## 2. 身份与权限矩阵（V2）

### 2.1 平台角色

| 能力 | REGULAR | ADMIN | SUPERADMIN |
|------|:-------:|:-----:|:----------:|
| 登录 / 看播 / 留言 / 收藏 | ✅ | ✅ | ✅ |
| 创建新直播间 | 仅 `can_stream` | ✅ 旁路或同样看开关* | ✅* |
| 进入用户/内容/品牌后台 | ❌ | ✅ | ✅ |
| 封禁用户、授/撤开播权 | ❌ | ✅ | ✅ |
| **修改他人 `role`（任命管理员）** | ❌ | ❌ | ✅ |
| 修改 SUPERADMIN 账号 | ❌ | ❌ | ✅ |
| 管理任意 brand_products | ❌ | ✅ | ✅ |

\*旁路：便于运营自测；若合规要求更严，可配置 `ADMIN_STREAM_BYPASS=false`，管理员也需 `can_stream=true`。

### 2.2 能力与业务主体（与 role 正交）

| 主体 | 判定方式 | 典型能力 |
|------|----------|----------|
| 授权主播 | `can_stream=true` | **新建**直播间（开播门禁） |
| 房间所有者 | `live_rooms.user_id = me` | 管理/结束**自己已有**房间（与 `can_stream` 正交，见 B5）；**场次关联专家、直播间绑定品牌**（见 §5.5） |
| 专家本人 | `experts.user_id = me` | 改自己的专家简介/头像 |
| 品牌成员 | `brand_members` 存在 | 上架/编辑本品牌商品 |
| 平台运营 | `role ∈ {ADMIN,SUPERADMIN}` | 管全站用户与全部商品；创建专家/品牌；绑 `experts.user_id`；管 `brand_members` |

---

## 3. JWT 约定（【修改】）

### 3.1 Access Token Payload

```json
{
  "user_id": "uuid-string",
  "username": "optional",
  "nickname": "optional",
  "role": "REGULAR",
  "can_stream": false,
  "type": "access",
  "iat": 1717750000,
  "exp": 1717753600
}
```

| 字段 | 规则 |
|------|------|
| `can_stream` | 登录/刷新时从 DB 写入；**缺省或旧 Token 缺字段 → 按 false** |
| `role` | 同 V1 |

所有登录路径（密码、手机、一键登录、refresh）签发时均带上 `can_stream`。

---

## 4. 会话吊销约定（【新增】安全）

### 4.0 与现状的重要差异（开发必读）

当前代码中 `_revoke_user_sessions` **主要拦截 refresh**：`auth_service.refresh` 会比对 `iat` 与吊销时间；  
`user_service` 的 `get_current_user` **不查**该 Key（只验 JWT + 单 token 黑名单 + DB `status=NORMAL`）。

因此仅「调用现有吊销」**不足以**立刻废掉仍在有效期内的 access token。本 V2 要求：

| 服务 | 对 access 的补强（【新增】） |
|------|------------------------------|
| `live_core` | 强制鉴权路径读取 `user_sessions_revoked`（否则开播/留言窗口期仍在） |
| `user_service`（建议同步做） | `get_current_user` 同样比对吊销时间，与 live_core 行为一致 |

> 「复用」= **复用同一 Redis Key 写法与语义**；access 路径的校验是 **新增强制项**，不是现状已有能力。

### 4.1 触发条件

Admin 或系统在以下变更成功提交后，必须写入吊销 Key：

| 变更 | 是否吊销 |
|------|----------|
| `status` → `BANNED` / `DELETED` | ✅ |
| `can_stream` → `false` | ✅（否则旧 JWT 仍带 `can_stream:true`，仅靠声明无法即时收回） |
| `role` 降级（如 ADMIN→REGULAR） | ✅ |
| `can_stream` → `true` / 解封 `NORMAL` | ⚠️ **授予旁路见 §4.3** |
| 仅改 nickname 等资料 | ❌ |

Key（与现实现一致）:

```text
user_sessions_revoked:{public_id} = ISO时间戳, TTL ≈ refresh 有效期
```

### 4.2 live_core / user_service 行为

在强制鉴权路径中：

1. 验 JWT 签名与过期  
2. 查 Redis `user_sessions_revoked:{user_id}`；若 token `iat` 早于吊销时间 → **401**  
3. 业务门禁再读 JWT 内 `can_stream` / `role`（或缺省 false）  

> 要求：两服务 **共用同一 Redis 实例/DB**。live_core 现多用于 Celery broker，**需增加**面向鉴权的 Redis 客户端读该 Key（非仅 Celery）。

### 4.3 授予开播权的生效时机（逻辑对称）

| 操作 | 即时性 |
|------|--------|
| 撤权 / 封禁 + 吊销 | access 在校验吊销后立刻失败 |
| 授 `can_stream=true` 且不吊销 | DB 已 true，但旧 access 仍可能无字段/为 false → **建房仍 403 直至 refresh 或重新登录** |

**产品要求（写入实现与运营话术）**：

- Admin 授开播后提示：「请用户退出并重新登录（或下拉刷新 Token）后再开播」  
- 或可选：授予后也吊销会话，强制重新登录以立刻带上新 JWT（更安全一致，略损体验）

---

## 5. API 设计

### 5.1 Phase P0 — user_service Admin Users（【修改】/【新增】）

#### 5.1.1 用户列表

**网关**: `GET /api/users/admin/users`

| Query | 类型 | 说明 |
|-------|------|------|
| page, size | int | 同 V1 |
| username | str | 模糊，同 V1 |
| email | str | 精确，同 V1 |
| phone_number | str | 【新增】精确 |
| nickname | str | 【新增】模糊 ILIKE |
| role | enum | 同 V1 |
| status | enum | 同 V1 |
| can_stream | bool | 【新增】可选筛选 |

**响应 item**: 在 V1 `UserResponse` 上增加 `can_stream: bool`。

#### 5.1.2 更新用户

**网关**: `PATCH /api/users/admin/users/{user_uuid}`

**Body（部分更新）**:

```json
{
  "role": "REGULAR",
  "status": "BANNED",
  "can_stream": true
}
```

**V2 校验规则**:

| 规则 | 结果 |
|------|------|
| 目标 `public_id ==` 操作者 | 403，禁止改自己 |
| 操作者为 ADMIN，修改 `role` 字段 | 403（仅超管可改角色） |
| 操作者为 ADMIN，目标为 SUPERADMIN | 403（同 V1） |
| 操作者为 ADMIN，`status` ∉ {NORMAL, BANNED} | 422 或 403 |
| 操作者为 SUPERADMIN 写 `PENDING_*` / `DELETED` | 允许但非运营主路径；UI 仍隐藏 |
| `status`/`can_stream`/`role` 触发 §4.1 | 写入吊销 Key 后返回 |

> V1 中「ADMIN 可改他人 role」**废止**，以本表为准。

---

### 5.2 Phase P0 — live_core 开播门禁（【修改】）

**创建房间**（现有 `POST` 房间接口）Service 层增加：

```text
if role in (ADMIN, SUPERADMIN) and ADMIN_STREAM_BYPASS:
    allow
elif can_stream == true:
    allow
else:
    403, code=3002, message="未开通开播资格"
```

**已有房间写操作**（改标题、结束、封面等）：仍按「owner 或管理员」；**不**因 `can_stream=false` 剥夺对旧房的管理（B5）。

---

### 5.3 Phase P1 — 专家认领（live_core）

| 方法 | 服务内路径 | 网关（示例） | Auth | 说明 |
|------|------------|--------------|------|------|
| GET | `/api/v1/experts/me` | `/api/core/experts/me` | JWT | 返回绑定专家；**未绑定 → 200 + `data: null`（空态，非错误）** |
| PATCH | `/api/v1/experts/me` | `/api/core/experts/me` | JWT | 仅绑定用户可改；未绑定 → 404 |
| POST | `/api/v1/experts/me/avatar` | `/api/core/experts/me/avatar` | JWT | 上传专家头像；未绑定 → 404 |
| Query | `sync_user_avatar=true` | 同上 | | 【友好】见下方跨服务同步约定 |

**Admin 绑定**:

- 复用/明确 `PATCH /admin/experts/{id}` 可写 `user_id`（`ExpertUpdate` 已有该字段）
- 解绑后原用户立刻失去 `/experts/me` 写权限

**未绑定专家（产品语义）**:

- `GET /experts/me`：**允许访问**，返回 200 空态（与 `GET /brands/me` → 空列表一致）；前端据此隐藏「我的专家页」，**不得**当故障 Toast / 错误页
- `PATCH` / 上传头像：未绑定仍 **404**（无权写）
- 专家页内容仅由 Admin 维护（外请专家、尚未绑登录账号）

**头像同步 `users.avatar_url`（跨服务，须写清）**:

`experts` 在 `live_core`，`users` 在 `user_service`，**不能**假设同库直写。实现择一：

| 方案 | 做法 | 建议 |
|------|------|------|
| A | live_core 调 users 内部/已有接口（如服务间 `PATCH` 资料，需服务令牌） | ✅ 推荐 |
| B | 前端拿到新 avatar URL 后再调 `PATCH /api/users/me` | 可用，依赖前端两次请求 |
| C | 同数据库直 UPDATE users | ❌ 违反服务边界，禁止 |

自编辑简介/头像须走与现网一致的**内容安全**校验（对齐用户昵称/头像场景）。

**网关路径说明**: Nginx 同时存在 `/api/core/`→`/api/v1/` 与 `^~ /api/v1/experts`。对外文档统一写 **`/api/core/experts/me`**（与 core 前缀约定一致）；直连 `/api/v1/experts/me` 等价，前端勿混用两套风格。

---

### 5.4 Phase P2 — 品牌成员与商品

#### 5.4.1 成员管理（Admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/admin/brands/{brand_id}/members` | 添加成员 `{ user_id, member_role }` |
| GET | `/api/v1/admin/brands/{brand_id}/members` | 成员列表 |
| DELETE | `/api/v1/admin/brands/{brand_id}/members/{user_id}` | 移除成员 |

#### 5.4.2 品牌工作台（成员，REGULAR 即可）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/brands/me` | 我可管理的品牌列表 |
| GET | `/api/v1/brands/{brand_id}/products` | 本品牌商品（成员或公开策略另定） |
| POST | `/api/v1/brands/{brand_id}/products` | 上架/创建草稿 |
| PATCH | `/api/v1/brands/{brand_id}/products/{product_id}` | 编辑 |
| POST | `/api/v1/brands/{brand_id}/products/{product_id}/publish` | 上架 ON_SALE |
| POST | `/api/v1/brands/{brand_id}/products/{product_id}/off` | 下架 |

权限：`EXISTS brand_members(brand_id, current_user)`。

#### 5.4.3 平台 Admin 管全部已上架商品（需求明确项）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/brand-products` | 跨品牌分页；筛 brand_id/status/name |
| PATCH | `/api/v1/admin/brand-products/{product_id}` | 强制下架/改资料 |
| DELETE | `/api/v1/admin/brand-products/{product_id}` | 软删 |

**前端**: 品牌商用工作台表单提交；Admin 用商品治理页。均走 API，**禁止**以 SQL 导入作为常规上架路径（批量导入可作为 Admin 可选工具，非必须）。

---

### 5.5 【修订】开播关联写权限 — 房主可关联（支持专家/品牌联动）

> **背景**: V2 将开播权下沉为 `can_stream` 后，REGULAR 主播可建房建场次，但场次↔专家、直播间↔品牌仍仅 Admin，导致开播闭环断裂。  
> **决策**: 放宽「关联」写权限；**不**开放创建专家/品牌、绑 `user_id`、加成员。  
> **明确不做**: 限制「只能绑自己的专家 / 只能绑 brand_members 内品牌」——否则无法做多专家联席、合作品牌挂房。

| 方法 | 网关路径 | 权限（修订后） | 可绑范围 |
|------|----------|----------------|----------|
| POST | `/api/core/experts/sessions/{session_id}/experts` | `ADMIN`/`SUPERADMIN` **或** 该场次所属房间的 owner | 任意 `is_active=true` 的专家 |
| POST | `/api/core/admin/rooms/{room_id}/brands` | `ADMIN`/`SUPERADMIN` **或** 该房间 owner | 任意 `is_active=true` 的品牌 |

**判定伪代码**:

```text
if role in (ADMIN, SUPERADMIN):
    allow
elif current_user_id == room.user_id:   # 场次关联时先查 session.room_id → room
    allow
else:
    403 / 3002
```

**仍仅 Admin**:

- 创建/编辑/上下架专家与品牌实体
- `PATCH` 专家 `user_id`（认领绑定）
- `brand_members` 增删
- 跨房、非 owner 的关联写操作

**产品语义**: 运营维护专家库与品牌库；授 `can_stream` 后，主播在**自己的房间**内可自由做专家联动与品牌联动，无需升为 Admin。

---

## 6. Schemas 摘要（P0）

```python
class UserUpdate(BaseModel):
    """管理端 PATCH — V2"""
    role: Optional[UserRole] = None          # 仅 SUPERADMIN 实际可写
    status: Optional[EntityStatus] = None    # ADMIN 限 NORMAL|BANNED
    can_stream: Optional[bool] = None
    nickname: Optional[str] = None           # 可选；管理端建议少用

class UserFilterParams(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None       # 新增
    nickname: Optional[str] = None           # 新增
    role: Optional[UserRole] = None
    status: Optional[EntityStatus] = None
    can_stream: Optional[bool] = None        # 新增

class UserResponse(UserBase):
    # ... V1 字段 ...
    can_stream: bool = False
```

---

## 7. 执行流程

### 7.1 授予开播权

```
1. SUPERADMIN/ADMIN PATCH { can_stream: true }
2. 校验：非改自己；目标存在
3. 更新 users.can_stream
4. 返回 UserResponse；提示用户重新登录或刷新 Token（见 §4.3）
5. 用户 login/refresh 后 JWT.can_stream=true（refresh 已从 DB 重载 role，须同步重载 can_stream）
6. 用户 POST 创建房间 → live_core 放行
```

> 实现注意：现有 `refresh_user_token` 已从 DB 读 `role` 再签发；增加 `can_stream` 时必须一并写入新 access，否则刷新后仍无开播声明。

### 7.2 撤销开播权 / 封禁

```
1. PATCH { can_stream: false } 或 { status: BANNED }
2. 更新 DB
3. _revoke_user_sessions(public_id)
4. 用户持旧 access → live_core 查吊销 → 401
5. 不可新建房间；旧房仍可被 owner 管理（仅撤开播时）/ 封禁后随 401 无法再调写接口
```

### 7.3 专家改头像并同步（P1）

```
1. 用户 JWT → GET /experts/me：已绑定继续；data=null（未绑定）则前端隐藏入口，勿报错
2. POST /experts/me/avatar?sync_user_avatar=true（未绑定 → 404）
3. 更新 experts.avatar_url
4. 若 sync：更新 users.avatar_url（同服务调用或 users 内部接口）
5. GET /experts 列表读 experts 行 → 头像已新
```

### 7.4 品牌商上架商品（P2）

```
1. Admin 将用户加入 brand_members
2. 用户 GET /brands/me → 选品牌
3. POST /brands/{id}/products → DRAFT → publish → ON_SALE
4. C 端按品牌展示货架
5. 平台 Admin 可在 /admin/brand-products 强制 OFF_SALE
```

---

## 8. 错误码

| code | HTTP | 场景 |
|------|------|------|
| 200 | 200 | 成功（含 `GET /experts/me` 未绑定：`data=null`；`GET /brands/me` 无成员：空列表） |
| 2004 | 404 | 用户/专家/商品不存在；`PATCH/POST /experts/me*` 未绑定（写路径） |
| 3001 | 401 | Token 无效或会话已吊销 |
| 3002 | 403 | 非管理员；未开播资格；非品牌成员；ADMIN 改 role；改自己 |
| 4001 | 422 | 参数非法（如 ADMIN 设 status=PENDING_REVIEW） |
| 1002 | 500 | 数据库错误 |

---

## 9. 对 V1（《14》原文）条款修订对照

| V1 内容 | V2 处理 |
|---------|---------|
| ADMIN 可修改用户 role | 【废止】仅 SUPERADMIN |
| 筛选项仅 username/email/role/status | 【扩展】phone/nickname/can_stream |
| 后续建议优先 verified 筛选、sort | 【降级】P0 让位于开播权与吊销 |
| 角色含 MODERATOR 日常可设 | 【降级】隐藏，不赋予新权 |
| 「已实现可联调」描述 | 【保留】列表+PATCH 骨架；语义与护栏以 V2 为准 |
| 会员产品/订阅 Admin | 【不变】 |

建议在 V1 文档顶部增加指向：

> **修订说明**: 身份模型、开播权、Admin 职责、会话吊销等以《14-…-V2-账号能力模型与权限修订设计文档》为准。

---

## 10. 前端 / 运营体验要点

### 10.1 管理端用户页

- 操作分离：**禁止开播 / 恢复开播** | **禁用/恢复账号** | **设为管理员**（仅超管可见，二次确认）  
- 文案：开播开关为次要紧急操作；日常停人用「禁用账号」  
- 文案禁止：「设为专家」「设为品牌商」——改为「绑定专家页」「加入品牌成员」跳转业务页  
- 枚举：`REGULAR` / `NORMAL` / `BANNED`；路径：`/api/users/admin/users`

### 10.2 小程序

- 默认可创建直播；仅当 `can_stream===false` 时灰显「创建直播」并提示「开播功能已被禁用」  
- 已绑定专家：个人中心入口「我的专家页」；`GET /experts/me` 为 `null` 时**勿当错误**，隐藏入口即可  
- 品牌成员：「品牌工作台」入口；`GET /brands/me` 空列表同理隐藏，勿 Toast

### 10.3 运营 SOP（封主播）

1. 禁用账号，或仅「禁止开播」（自动吊销会话）  
2. 如仍在播：到直播管理结束房间 / 必要时轮换密钥（独立操作）  
3. 如有专家页：下架专家 `is_active=false`  
4. 如有品牌商品：Admin 强制下架

---

## 11. 测试要点

### P0

| # | 用例 | 预期 |
|---|------|------|
| T1 | REGULAR + can_stream=false 创建房间 | 403「开播功能已被禁用」 |
| T2 | REGULAR + can_stream=true（默认）创建房间 | 200 |
| T3 | Admin 禁止后再恢复 can_stream，refresh 后建房 | 200 |
| T4 | ADMIN PATCH 改他人 role | 403 |
| T5 | SUPERADMIN 任命 ADMIN | 200 |
| T6 | ADMIN PATCH 自己 status=BANNED | 403 |
| T7 | 封禁后旧 access 调 live_core（已接吊销校验） | 401 |
| T8 | 禁止开播后旧 access 建房（已接吊销校验） | 401（不应再落到业务 403） |
| T8b | 恢复开播后不 refresh、旧 access 仍为 false | 403（JWT 仍为 false） |
| T9 | 列表 `phone_number`/`nickname`/`can_stream` | 筛选正确 |

### P1 / P2

| # | 用例 | 预期 |
|---|------|------|
| T10 | 未绑定 GET /experts/me | **200，`data=null`**（非错误） |
| T10b | 未绑定 PATCH /experts/me | 404 |
| T10c | 无品牌成员 GET /brands/me | 200，`items=[]` |
| T11 | 绑定后改头像+sync | experts 与 users 头像一致 |
| T12 | 非成员 POST 商品 | 403 |
| T13 | 成员上架后 Admin 强制下架 | status=OFF_SALE |

---

## 12. 部署注意

1. 跑 `users.can_stream` 迁移（V2.1：默认 true + 存量回填为 true）  
2. JWT 缺 `can_stream` → 视为 **true**；存量用户若旧 access 显式 `false`，**refresh 一次**即可（不做全站踢下线）  
3. 确认双服务 Redis 连通、live_core 鉴权可读吊销 Key 后再开启强制校验  
4. Nginx：P1/P2 走 `/api/core/`（rewrite 到服务内 `/api/v1/`）；专家亦有 `/api/v1/experts` 直连，对外统一一种即可  
5. 环境变量建议：`ADMIN_STREAM_BYPASS=true`（默认，运营自测旁路）

**跨库警告**: `users` 与 `live_rooms` 分属不同服务库时，下方历史 SQL **不能**直接在 users 库联表 live_rooms。

**V2.1 存量**：迁移已 `UPDATE users SET can_stream = TRUE WHERE can_stream = FALSE`，无需再按「曾建房用户」逐批授出。

<details><summary>历史参考：V2.0 按建房用户授出（已废弃）</summary>

```sql
-- 已废弃：V2.1 改为全量默认可播
UPDATE users u
SET can_stream = TRUE
WHERE EXISTS (
  SELECT 1 FROM live_rooms r WHERE r.user_id = u.public_id
);
```

</details>

---

## 13. 最终路由表（本 V2 相关）

> **路由结论（2026-07-14）**：P0–P2 均已落地。P0 仅改既有路径行为；P1/P2 为新增路径。网关：`/api/users/*`→users，`/api/core/*`→live_core（rewrite `/api/v1/`）。

### ✅ P0 已实现（改行为，不改路径）

| Domain | 网关路径 | Method | 实现状态 | 变更摘要 |
|--------|----------|--------|----------|----------|
| admin-users | `/api/users/admin/users` | GET | ✅ 已落地 | 增筛 `phone_number` / `nickname` / `can_stream`；响应含 `can_stream` |
| admin-users | `/api/users/admin/users/{uuid}` | PATCH | ✅ 已落地 | `can_stream`；禁改自己；仅超管改 `role`；ADMIN status∈{NORMAL,BANNED}；封禁/撤开播/降权 → 吊销 |
| rooms | `/api/core/rooms`（服务内 `POST /api/v1/rooms`） | POST | ✅ 已落地 | 开播门禁：`can_stream` 或缺省 false → 403/3002；`ADMIN_STREAM_BYPASS` 旁路 |

**P0 横切能力**：JWT 写入 `can_stream`；users/live_core 鉴权读 `user_sessions_revoked:{user_id}`。

### ✅ P1 已实现（新增）

| Domain | 网关路径 | Method | 实现状态 | Notes |
|--------|----------|--------|----------|-------|
| experts-me | `/api/core/experts/me` | GET/PATCH | ❌ V2.2 裁剪 | 代码已删除 |
| experts-me | `/api/core/experts/me/avatar` | POST | ❌ V2.2 裁剪 | 代码已删除 |
| internal-avatar | `/api/users/internal/users/{uuid}/avatar` | PATCH | ✅ 已落地 | Header `X-Internal-Token`；服务间写 `avatar_url` |

### ✅ P2 已实现（新增）

| Domain | 网关路径 | Method | 实现状态 | Notes |
|--------|----------|--------|----------|-------|
| brand-members | `/api/core/admin/brands/{id}/members` | POST/GET | ❌ V2.2 裁剪 | 代码已删除 |
| brand-members | `/api/core/admin/brands/{id}/members/{user_id}` | DELETE | ❌ V2.2 裁剪 | 代码已删除 |
| brand-desk | `/api/core/brands/me` | GET | ❌ V2.2 裁剪 | 代码已删除 |
| brand-products | `/api/core/brands/{id}/products` | GET/POST | ❌ V2.2 裁剪 | 代码已删除 |
| brand-products | `/api/core/brands/{id}/products/{pid}` | PATCH | ❌ V2.2 裁剪 | 代码已删除 |
| brand-products | `/api/core/brands/{id}/products/{pid}/publish` | POST | ❌ V2.2 裁剪 | 代码已删除 |
| brand-products | `/api/core/brands/{id}/products/{pid}/off` | POST | ❌ V2.2 裁剪 | 代码已删除 |
| admin-products | `/api/core/admin/brand-products` | GET | ❌ V2.2 裁剪 | 代码已删除 |
| admin-products | `/api/core/admin/brand-products/{pid}` | PATCH/DELETE | ❌ V2.2 裁剪 | 代码已删除 |

### ✅ P2.1 开播关联权限修订（改行为，不改路径）

| Domain | 网关路径 | Method | 实现状态 | 变更摘要 |
|--------|----------|--------|----------|----------|
| session-experts | `/api/core/experts/sessions/{id}/experts` | POST | ✅ 修订 | Admin **或** 场次所属房间 owner；可绑任意启用专家（支持联动） |
| room-brands | `/api/core/admin/rooms/{id}/brands` | POST | ✅ 修订 | Admin **或** 房间 owner；可绑任意启用品牌（支持联动） |

**上线配置**：`INTERNAL_SERVICE_TOKEN`（users+live_core 一致）、`USER_SERVICE_URL`（live_core）；users 跑 `migrate_can_stream`。`migrate_brand_commerce` 仅用于 **DROP** 已废弃的 `brand_members`/`brand_products`，不再建表。

---

## 📝 修订历史

| 版本 | 日期 | 内容 |
|------|------|------|
| V2.0 | 2026-07-14 | 首版：账号能力模型、开播权、Admin 职责、吊销、专家认领、品牌货架 |
| V2.0.1 | 2026-07-14 | 自测修订：澄清吊销仅 refresh 的现状与 access 补强；授权力延迟；能力矩阵拆分房间 owner；跨服务头像同步；C 端商品 GET；标注修正 |
| V2.0.2 | 2026-07-14 | 路由表：P0 标为已落地；明确无新路径、建房网关为 `/api/core/rooms`；补 JWT/吊销横切说明 |
| V2.0.3 | 2026-07-14 | P1/P2 落地：路由表全标已实现；补内部头像同步路径与上线配置 |
| V2.0.4 | 2026-07-14 | 语义修订：`GET /experts/me` 未绑定改为 200 空态（与品牌工作台一致）；写路径仍 404 |
| V2.0.5 | 2026-07-16 | §5.5：场次专家 / 房间品牌关联放宽为 Admin 或房间 owner；不限制只能绑本人/本成员，以支持专家与品牌联动 |
| V2.1 | 2026-07-30 | 开播策略：默认人人可播；`can_stream=false`=禁止开播；JWT 缺省 true；建房文案「开播功能已被禁用」；Admin 开关降为紧急操作 |
| V2.2 | 2026-08-07 | **产品裁剪**：废弃专家认领、品牌成员、品牌货架商品；仅保留专家页/Admin 专家档案、品牌主体 |

---

**文档结束**
