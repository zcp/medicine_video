# 管理端用户管理 · 账号能力模型与权限修订 — 前端设计文档（V2）

**项目**: Live-Saas-Wechat  
**模块编号**: 14  
**版本**: 2.2.0  
**创建日期**: 2026-07-14  
**状态**: **V2.2 产品裁剪已对齐后端**：仅保留专家公开页/关注/Admin 专家档案、品牌主体；专家认领与品牌成员/货架前端已下线  
**文档类型**: 设计类（业务方案 / 技术方案）  
**技术栈**: uni-app + Vue 3 + TypeScript + Pinia

> **⚠️ V2.2 产品裁剪（2026-08-07，以《权威 V2》V2.2 为准）**  
> | 项 | 前端处理 |  
> |----|----------|  
> | 专家认领 `/experts/me*` | **已下线**：`MyExpert` 仅提示；API 标记废弃且不再请求 |  
> | 品牌成员 / 货架商品 | **已下线**（Admin 入口此前已下；勿再恢复） |  
> | 专家公开页 / 关注 / Admin 专家 CRUD | **保留** |  
> | 品牌主体公开页 / Admin 品牌 CRUD | **保留** |  

> **⚠️ V2.1 产品修订（2026-07-30，开播开关语义仍有效）**

| 项 | V2.0 原语义 | V2.1 现行 |
|----|-------------|-----------|
| 默认 | `can_stream=false`（需运营授予） | `can_stream=true`（人人默认可播） |
| Admin 操作 | 「授予 / 撤销开播权」 | 「禁止开播 / 恢复开播」（紧急开关；日常以封禁为主） |
| `can_stream=false` | 未开通 | 被禁止开播 |
| 列表 tag | 可开播 / 未开通开播 | 可开播 / 已禁止开播 |
| 用户侧拦截文案 | 未开通开播资格，请联系运营 | 开播功能已被禁用 |
| JWT / `normalizeCanStream` 缺字段 | 视为 false | 视为 **true**（与后端一致） |
| 恢复开播（`true`） | Toast 请对方重登 | 仍 Toast 请对方 refresh/重登（不吊销） |

> **权威源（契约，零偏差）**：  
> 《[14-管理端用户管理-V2-账号能力模型与权限修订设计文档](./14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md)》  
> 下文简称 **《权威 V2》**。与本文冲突时，以《权威 V2》接口/校验/错误码为准；本文只落前端行为。

> **仓库后端同步副本**（非第二套设计）：  
> 《[Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0](./Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0.md)》  
> 与《权威 V2》冲突时仍以权威源为准。

> **前端基线**：  
> 《[Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0](./Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0.md)》  
> 与 V2 冲突时以**本文档**为准。V1 仍有效：users 网关前缀、`public_id` 路径参数、`size` 分页、列表页骨架。

---

## ⚠️ 文档定位与命名说明

### 为何不叫「纯增量」？

与《权威 V2》一致：V1 已有列表 + PATCH `role`/`status`。本次不是只加字段，而是修订身份/能力模型。

| 变更性质 | 前端影响 |
|----------|----------|
| 【修订】 | 开播与平台角色分离：独立 `can_stream` 开关；V2.1 默认 true，开关语义为禁止/恢复 |
| 【修订】 | ADMIN / SUPERADMIN：仅超管可见/可提交 `role`；ADMIN 无角色 picker |
| 【废弃/降级】 | 日常 UI **隐藏** `MODERATOR`；日常 status 主按钮仅 `NORMAL`↔`BANNED` |
| 【新增】 | 列表筛 `phone_number`/`nickname`/`can_stream`；JWT/`auth` 门禁；恢复开播提示 refresh/重登 |
| 【新增】 | P1 专家认领页、P2 品牌工作台（成员侧商品 CRUD）；Admin 商品/成员治理页 **前端已下线** |
| 【修订·V2.1】 | 默认可播；Admin 开播开关降为紧急操作；用户侧仅 `false` 时拦截 |

### 文件命名（对齐《通用规范-文件创建规范-v1.0》）

| 文件 | 含义 |
|------|------|
| `14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md` | ✅ **权威源（契约）** |
| `Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0.md` | 后端 V2 仓库同步副本 |
| `Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md` | ✅ **本文档** |
| `Live-Saas-Wechat-14-管理端用户管理-后端设计文档-v1.1.md` | V1 后端骨架 |
| `Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0.md` | V1 前端基线 |

**阅读约定**:

- 与 V1 **冲突时，以本文档 +《权威 V2》为准**
- 《权威 V2》§13 路由表：**后端** P0–P2 均已落地；**前端**进度见本文「行动清单」与「状态」字段，二者不得混写

---

## 📌 核心定位说明

### 1. 本文档解决什么问题（对齐《权威 V2》§核心定位）

医学直播 SaaS + 微信小程序场景下，前端需支持：

1. **默认可开播，必要时禁止** → 管理端「禁止开播 / 恢复开播」；小程序仅 `can_stream===false` 拦截新建；**不能**用「设为管理员」代替；日常停人用封禁  
2. **专家** = 简介页主体 + 可选绑登录账号 → P1「我的专家页」认领/自编辑（非 `role=EXPERT`）  
3. **品牌商**可登录上架可售商品 → P2「品牌工作台」（成员侧）；平台 Admin 商品/成员治理页 **前端已下线**（后端 API 契约仍见《权威 V2》） 
4. **ADMIN / SUPERADMIN** 做实 → UI：仅超管改 role；ADMIN 禁编自己/SUPERADMIN  
5. **封禁 / 禁止开播即时生效** → 前端按 3001/401 统一登出或跳登录；恢复开播须提示对方 refresh/重登（见 §五）

### 2. 能力分层总览（前端必读，与《权威 V2》V2.1 一致）

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
│    成员可自助上架；Admin 可管理全部已上架商品（后端；前端治理页已下线）│
└─────────────────────────────────────────────────────────────┘
```

**前端明确禁止**:

- ❌ 用角色选项 / 文案「设为专家」「设为品牌商」「设为主播」表达开播、专家、品牌身份  
- ❌ 给主播/专家/品牌成员升 `ADMIN` 才能干活  
- ❌ 请求路径 `/api/core/admin/users`（走错网关 404）  
- ❌ Query 使用 `page_size`（后端只认 `size`）  
- ❌ 日常角色 picker 暴露 `MODERATOR`；日常 status 主按钮暴露 `PENDING_REVIEW`/`REJECTED`/`DELETED`  
- ❌ JWT 缺 `can_stream` 时仍按 false（V2.1 必须按 **true**）  
- ❌ 文案继续写「开通开播资格 / 未开通开播 / 请联系运营开通」（改为禁止/恢复语义）

### 3. 分 Phase 交付（与《权威 V2》一致）

| Phase | 目标 | 后端状态（《权威 V2》§13） | 前端状态 |
|-------|------|---------------------------|----------|
| **P0** | `can_stream` + 创建直播间门禁 + JWT + Admin 禁止/恢复 + 护栏 + 检索 | ✅ 已落地（V2.1 默认 true） | ✅ 已落地；**文案/缺省须对齐 V2.1** |
| **P1** | 专家认领 `GET/PATCH /experts/me`、头像同步 | ✅ 已落地 | ✅ 已落地可联调 |
| **P2** | 品牌成员 + 品牌商品 CRUD；Admin 管全部商品（后端） | ✅ 已落地 | ✅ 成员工作台已落地；**Admin 治理页前端已下线** |

---

## 📋 目录

1. [说明与定位](#文档定位与命名说明)  
2. [依赖与网关](#一依赖与网关约定)  
3. [需求清单（A–G 前端映射）](#二需求与内容清单前端映射)  
4. [权限矩阵（UI）](#三身份与权限矩阵前端ui)  
5. [JWT 与 auth store](#四jwt-与-auth-store约定)  
6. [会话吊销对前端的影响](#五会话吊销前端体验)  
7. [API 与类型（P0/P1/P2）](#六api-与类型零偏差)  
8. [页面与文件清单](#七页面与文件清单)  
9. [核心流程](#八核心流程)  
10. [错误码处理](#九错误码处理)  
11. [列表 / 编辑 / 返回规范](#十列表--编辑--返回规范对齐)  
12. [运营文案与 SOP](#十一运营文案与-sop对齐后端--10)  
13. [行动清单](#十二行动清单)  
14. [测试要点（对齐后端 T 编号）](#十三测试要点对齐后端--11)  
15. [检查清单](#十四检查清单)  
16. [更新日志](#十五更新日志)  

---

## 一、依赖与网关约定

| 序号 | 文档/模块 | 关系 |
|------|-----------|------|
| 1 | 《权威 V2》 | **主对齐（契约权威源）** |
| 2 | 《14-管理端用户管理-后端设计文档-v1.1》 | 网关骨架、统一响应、分页、会员 Admin（本 V2 不改会员 UI） |
| 3 | 《14-管理端用户管理-前端设计文档-v1.0》 | 前端基线 |
| 4 | 《10-用户认证与管理-前端设计文档-v1.7》 | JWT、request、auth store |
| 5 | 《通用数据列表展示规范》《前端分页实现规范》 | 列表 |
| 6 | 《编辑页面数据与校验规范》 | 编辑部分更新 |
| 7 | 《页面返回机制设计文档》《前端安全编程规范》 | 返回/鉴权 |
| 8 | 《通用规范-文件创建规范-v1.0》 | 命名/结构 |

**网关约定（与《权威 V2》一致，不变）**:

| Domain | 网关前缀 | 微服务 |
|--------|----------|--------|
| 用户 / Admin 用户 | `/api/users/...` | `user_service` |
| 专家 / 品牌 / 直播 | `/api/core/...` | `live_core_service`（rewrite 服务内 `/api/v1/`） |

```
✅ GET/PATCH  http://localhost:8080/api/users/admin/users[...]
✅ POST       http://localhost:8080/api/core/rooms
✅ GET/PATCH  http://localhost:8080/api/core/experts/me
✅ *          http://localhost:8080/api/core/brands/...
✅ *          http://localhost:8080/api/core/admin/brand-products...
❌ GET        /api/core/admin/users          → 404
❌ GET        /api/v1/admin/users（作前端主路径）→ 勿混用风格；对外统一网关前缀
```

P1/P2 专家亦有 `/api/v1/experts` 直连等价；**前端对外统一写 `/api/core/...`，勿混用两套风格**（《权威 V2》§5.3）。

---

## 二、需求与内容清单（前端映射）

> 完整业务清单以《权威 V2》「需求与内容清单 A–G」为准。下表只写前端落点。标注与后端一致：【V1 已有】【修订】【新增】【明确不做】。

### A. 账号与平台角色

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| A1 | 平台角色仅服务「能否进运维后台」 | 【修订】 | 产品文案：普通人 / 管理员；库内可有 SUPERADMIN |
| A2 | `MODERATOR` 管理端隐藏 | 【修订】 | `getDailyRoleFilterOptions` / `getEditableRoleOptions` **不含** MODERATOR |
| A3 | 仅超管可改 `role` | 【修订】 | `canChangeUserRole`；ADMIN 无角色 picker；改 role 二次确认 |
| A4 | 禁止管理员 PATCH 自己 | 【新增】 | `canEditAdminUser`：目标 `public_id ===` 操作者 → 隐藏编辑 |
| A5 | 日常 status 仅 `NORMAL`↔`BANNED` | 【修订】 | `getDailyStatusOptions()`；超管也不把 PENDING/DELETED 作主按钮 |

### B. 开播能力（非身份）

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| B1 | `can_stream` 默认 true（V2.1） | 【修订】 | `normalizeCanStream`：`null/undefined` → **true**；显式 false 保留 |
| B2 | 默认可播用户 = REGULAR + can_stream（默认即是） | 【修订】 | 开播开关与角色分离；开关标签「禁止/恢复开播」 |
| B3 | Admin 可禁止/恢复开播 | 【修订】 | 编辑弹窗独立开关（次要紧急操作）；PATCH 仅变更字段 |
| B4 | 创建房间校验 can_stream | 【新增】 | `authStore.canCreateRoom`；仅 false 时 CreateLive / Profile 拦截 |
| B5 | 禁止开播后仍可管旧房 | 【修订】 | **仅新建**拦截；编辑已有房间放行 |
| B6 | JWT 含 can_stream；缺省 true（V2.1） | 【修订】 | 解析 JWT / `/me` 同步；缺字段按 true |

### C. 安全与即时生效

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| C1–C3 | 封禁/禁止开播/降权 → 会话吊销 | 【修订】 | 目标用户持旧 token → 3001/401 → 统一跳登录；见 §五 |
| C4 | 不在用户管理里自动关房 | 【明确不做】 | Admin UI **不提供**「封禁并关房」；见运营 SOP |

### D. 管理端检索与联调

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| D1 | 筛 `phone_number`（精确）、`nickname`（模糊） | 【新增】 | UserList 筛选栏 |
| D2 | 列表返回 `can_stream` | 【修订】 | tag「可开播 / 已禁止开播」；筛选项「已禁止开播」 |
| D3 | 路径/枚举对齐 | 【修订】 | `/api/users/admin/users`；`NORMAL`/`BANNED`；`REGULAR` 非 `USER`/`active` |

### E. 专家（业务主体，非 role）

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| E1–E2 | 专家 ≠ role；`user_id` 绑定 | 【明确】 | 禁止角色按钮「设为专家」 |
| E3–E5 | `/experts/me` + 头像 sync | 【新增】 | P1：`MyExpert` 页；`sync_user_avatar`；失败可方案 B 再 PATCH `/users/me` |
| E6 | 列表读 experts | 【明确】 | 改专家页即更新列表展示，不必刷 users |
| E7 | 绑专家 ≠ 自动改 can_stream | 【明确】 | 开播默认已开；禁止开播仍走 Admin 开关 |

### F. 品牌商与可售商品（非 role）

| # | 条目 | 类型 | 前端落点 |
|---|------|------|----------|
| F1–F3 | brands / members / products | 【新增】 | P2：成员工作台；Admin 治理页前端已下线 |
| F4 | 成员对本品牌商品 CRUD | 【新增】 | `BrandWorkbench` |
| F5 | 平台 Admin 管任意已上架商品 | 【新增】 | 后端 `/admin/brand-products*`；**前端 Admin 治理页已下线** |
| F6 | 品牌成员 ≠ ADMIN | 【明确】 | 入口靠 membership/API，不靠 role |

### G. 明确不在本 V2 范围

| # | 条目 | 前端 |
|---|------|------|
| G1 | 批量导出、完整审计表 | 不做 |
| G2 | 封禁自动切断推流/关房 | 不做；SOP 人工结束房间 |
| G3 | 房间级房管（MODERATOR 真正启用） | 不做 |
| G4 | 支付进件、分账、完整商城交易 | P2 仅货架 CRUD |
| G5 | 多租户 `tenant_id` | 不做 |
| — | 会员产品/订阅 Admin UI | 本 V2 **不改**（仍属 V1 后续，见 V1 前端 §七） |

---

## 三、身份与权限矩阵（前端 UI）

对齐《权威 V2》§2.1 / §2.2。

### 3.1 平台角色 → UI

| 能力 | REGULAR | ADMIN | SUPERADMIN | 前端实现要点 |
|------|:-------:|:-----:|:----------:|--------------|
| 登录 / 看播 / 留言 / 收藏 | ✅ | ✅ | ✅ | 既有 |
| 创建新直播间 | 仅 `can_stream` | ✅ 旁路* | ✅* | `canCreateRoom`；旁路与后端 `ADMIN_STREAM_BYPASS` 默认 true 一致 |
| 进入用户/内容/品牌后台 | ❌ | ✅ | ✅ | `isAdmin` 校验页 |
| 封禁、禁止/恢复开播 | ❌ | ✅ | ✅ | 编辑弹窗 status + can_stream（开播为次要紧急操作） |
| **修改他人 role** | ❌ | ❌ | ✅ | 仅超管展示角色 picker |
| 修改 SUPERADMIN 账号 | ❌ | ❌ | ✅ | ADMIN 隐藏编辑按钮 |
| 管理任意 brand_products | ❌ | ✅ | ✅ | 后端能力保留；**前端 Admin 商品页已下线** |
| 编辑自己的 Admin 账号 | — | ❌ | ❌ | 禁止改自己 |

\*与后端一致：若运营将 `ADMIN_STREAM_BYPASS=false`，管理员也需 `can_stream=true`；前端旁路逻辑须可配置或随后端环境对齐（默认旁路 true）。

### 3.2 能力与业务主体（与 role 正交）

| 主体 | 判定 | 前端入口 |
|------|------|----------|
| 默认可播用户 | `can_stream===true`（默认） | 新建直播 |
| 房间所有者 | 自己的旧房 | 编辑/结束旧房（**不**因禁止开播剥夺，B5） |
| 专家本人 | `GET /experts/me` 返回专家对象（已绑定） | Profile「我的专家页」**登录可见**；未绑定（`data=null`）进页后走**页内空态**，勿 Toast |
| 品牌成员 | `GET /brands/me` 非空 | Profile「品牌工作台」**登录可见**；空列表进页后走**页内空态**，勿 Toast |
| 平台运营 | `role ∈ {ADMIN,SUPERADMIN}` | 用户管理等（**不含**已下线的品牌成员/商品治理页） |

---

## 四、JWT 与 auth store 约定

对齐《权威 V2》§3。

### 4.1 Access Token Payload（前端解析）

```json
{
  "user_id": "uuid-string",
  "username": "optional",
  "nickname": "optional",
  "role": "REGULAR",
  "can_stream": true,
  "type": "access",
  "iat": 1717750000,
  "exp": 1717753600
}
```

| 字段 | 前端规则 |
|------|----------|
| `can_stream` | 显式 `false` → 禁止开播；缺省 / 旧 Token 缺字段 → **true**（V2.1，与后端一致）；`=== true` 为可播 |
| `role` | 同 V1；兼容大小写；管理端 UI 用大写枚举 |

所有登录路径（密码、手机、一键登录、refresh）签发后，前端必须把 `can_stream` 写入 `authStore.userInfo`。  
`refresh` 后须用新 access 重解析；`/users/me` 若返回 `can_stream` 亦同步。  
`normalizeCanStream(null|undefined)` → `true`；仅显式 `false` 为禁止。

### 4.2 Store Getter（P0 已落地）

| Getter | 语义 |
|--------|------|
| `canStream` | `normalizeCanStream(userInfo.can_stream)`（缺省 true） |
| `canCreateRoom` | ADMIN/SUPERADMIN → true（旁路）；否则 `canStream` |
| `isAdmin` | ADMIN \| SUPERADMIN |
| `isSuperAdmin` | 仅 SUPERADMIN（改 role UI） |

文件：`src/types/auth.ts`、`src/store/auth.ts`、`src/types/adminUser.ts`（`normalizeCanStream`）。

---

## 五、会话吊销（前端体验）

对齐《权威 V2》§4。前端不写 Redis，但必须理解时效。

| 场景 | 后端行为 | 前端行为 |
|------|----------|----------|
| 封禁 / 禁止开播（`can_stream→false`）/ 降权 | 写 `user_sessions_revoked` | 目标用户下次请求 → **3001/401** → 统一跳登录 |
| 恢复开播（`can_stream→true`，默认不吊销） | DB 已 true，旧 JWT 仍可能为 false | Admin Toast：**「请对方退出并重新登录（或刷新登录）后再开播」**；对方建房在 refresh 前仍可能 403 |
| 仅改 nickname | 不吊销 | 无特殊提示 |

恢复开播成功文案须保留（与《权威 V2》§4.3 一致），不可省略。

---

## 六、API 与类型（零偏差）

> 路径、方法、Query、Body 字段名与《权威 V2》§5 / §6 / §13 **逐字对齐**。

### 6.1 Phase P0 — Admin Users（users 网关）

#### 6.1.1 用户列表

| 项 | 值 |
|----|-----|
| 方法 | `GET` |
| 网关 | `/api/users/admin/users` |
| 前端函数 | `getAdminUsers` |
| Auth | JWT + ADMIN/SUPERADMIN |

| Query | 类型 | 说明 | V2 |
|-------|------|------|-----|
| page, size | int | 同 V1；**禁止** `page_size` | |
| username | str | 模糊 | V1 |
| email | str | 精确 | V1 |
| phone_number | str | 精确 | 【新增】 |
| nickname | str | 模糊 | 【新增】 |
| role | enum | REGULAR/ADMIN/SUPERADMIN（筛选项隐藏 MODERATOR） | |
| status | enum | 日常筛 NORMAL/BANNED | |
| can_stream | bool | 可选 | 【新增】 |

**响应 item**：V1 `UserResponse` + `can_stream: bool`（缺省按 **true** 归一化，V2.1）。

#### 6.1.2 更新用户

| 项 | 值 |
|----|-----|
| 方法 | `PATCH` |
| 网关 | `/api/users/admin/users/{user_uuid}` |
| 路径参数 | `public_id`（非内部 `id`） |
| 前端函数 | `adminUpdateUser` |

**Body（部分更新，只提交变更字段）**:

```json
{
  "role": "REGULAR",
  "status": "BANNED",
  "can_stream": true
}
```

| 规则（后端校验） | 前端预检 / UI |
|------------------|---------------|
| 目标 public_id == 操作者 → 403 | 隐藏编辑按钮 |
| ADMIN 修改 `role` → 403 | 不展示角色 picker，不提交 role |
| ADMIN 目标为 SUPERADMIN → 403 | 隐藏编辑 |
| ADMIN `status` ∉ {NORMAL,BANNED} → 422/403 | 日常仅两选项 |
| SUPERADMIN 写 PENDING/DELETED | UI **仍隐藏**（非运营主路径） |
| 含 `role` 变更 | 二次确认后提交 |
| `can_stream: true`（恢复开播）成功 | Toast 提示对方 refresh/重登 |
| `can_stream: false`（禁止开播）成功 | 无需额外 Toast（对方下次请求会 401） |

> V1「ADMIN 可改他人 role」**废止**，UI 必须按上表。

#### 6.1.3 创建房间门禁

| 项 | 值 |
|----|-----|
| 方法 | `POST` |
| 网关 | `/api/core/rooms` |
| 门禁（后端） | ADMIN/SUPERADMIN 旁路 **或** `can_stream==true`；否则 403 / `code=3002` message「开播功能已被禁用」 |
| 前端 | 提交前 `canCreateRoom` 拦截；后端仍为权威 |

**已有房间写操作**：不因 `can_stream=false` 剥夺（B5）。

### 6.2 Phase P1 — 专家认领（core 网关）

| 方法 | 网关路径 | Auth | 说明 | 前端函数 |
|------|----------|------|------|----------|
| GET | `/api/core/experts/me` | JWT | 返回绑定专家；**未绑定 → 200 + `data: null`（空态，非错误）** | `getMyExpert` |
| PATCH | `/api/core/experts/me` | JWT | 仅绑定用户改简介字段；未绑定 → 404/`2004` | `updateMyExpert` |
| POST | `/api/core/experts/me/avatar` | JWT | Query `sync_user_avatar=true` 可选；未绑定 → 404 | `uploadMyExpertAvatar` |

**Admin 绑定**：复用 Admin 专家编辑写 `user_id`（非 Doc14 用户列表职责）；解绑后原用户立刻失去 `/experts/me` **写**权限。

**未绑定（产品语义）**：

- `GET /experts/me`：**允许访问**，200 空态；据此隐藏「我的专家页」，**不得**当故障 Toast / 错误页
- `PATCH` / 上传头像：未绑定仍按 **404** 处理（无权写）

**头像同步**（《权威 V2》§5.3）:

| 方案 | 做法 | 前端 |
|------|------|------|
| A | live_core 调 users 内部接口（推荐，后端已落地） | 传 `sync_user_avatar=true` 即可 |
| B | 前端再调 `PATCH /api/users/me`（若 A 失败兜底） | 可选 |
| C | 同库直写 | ❌ 禁止 |

自编辑简介/头像须走与现网一致的**内容安全**错误处理（对齐《10-内容安全-前端》）。

### 6.3 Phase P2 — 品牌成员与商品（core 网关）

对外统一 `/api/core/`（对应服务内 `/api/v1/`）。

#### 6.3.1 成员管理（Admin API · 前端页已下线）

> **前端**：`BrandMemberManager` 与 Profile「品牌成员管理」入口 **已下线**；本表仅对照后端契约（见《权威 V2》）。前端不再封装 Admin 添加/移除成员 API。

| 方法 | 网关路径 | 说明 |
|------|----------|------|
| POST | `/api/core/admin/brands/{brand_id}/members` | `{ user_id, member_role }` |
| GET | `/api/core/admin/brands/{brand_id}/members` | 成员列表 |
| DELETE | `/api/core/admin/brands/{brand_id}/members/{user_id}` | 移除 |

#### 6.3.2 品牌工作台（成员，REGULAR 即可）

| 方法 | 网关路径 | 说明 |
|------|----------|------|
| GET | `/api/core/brands/me` | 我可管理的品牌列表 |
| GET | `/api/core/brands/{brand_id}/products` | 成员见草稿；非成员仅 ON_SALE |
| POST | `/api/core/brands/{brand_id}/products` | 创建草稿 |
| PATCH | `/api/core/brands/{brand_id}/products/{product_id}` | 编辑 |
| POST | `/api/core/brands/{brand_id}/products/{product_id}/publish` | → ON_SALE |
| POST | `/api/core/brands/{brand_id}/products/{product_id}/off` | → OFF_SALE |

权限：membership；403/`3002` 非成员。前端落点：`BrandWorkbench`。

#### 6.3.3 平台 Admin 管全部商品（API · 前端页已下线）

> **前端**：`BrandProductList` 与 Profile「品牌商品治理」入口 **已下线**；本表仅对照后端契约。前端不再封装跨品牌商品 Admin API。

| 方法 | 网关路径 | 说明 |
|------|----------|------|
| GET | `/api/core/admin/brand-products` | 跨品牌分页；筛 brand_id/status/name |
| PATCH | `/api/core/admin/brand-products/{product_id}` | 强制下架/改资料 |
| DELETE | `/api/core/admin/brand-products/{product_id}` | 软删 |

成员侧上架走工作台 API + 表单；**禁止**以 SQL 导入作为常规上架路径。

### 6.4 TypeScript Schema（对齐《权威 V2》§6）

文件：`src/types/adminUser.ts`（P0 已落地）。

```typescript
// 对齐后端 UserUpdate / UserFilterParams / UserResponse.can_stream

export type AdminUserRole = 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN'
export type AdminEntityStatus =
  | 'NORMAL' | 'BANNED' | 'DELETED' | 'PENDING_REVIEW' | 'REJECTED'

export interface AdminUserResponse {
  // ... V1 字段 ...
  can_stream: boolean  // 缺省归一化为 true（V2.1）
}

export interface AdminUserUpdatePayload {
  role?: AdminUserRole          // 仅 SUPERADMIN 实际可写
  status?: AdminEntityStatus    // ADMIN 限 NORMAL|BANNED
  can_stream?: boolean
  nickname?: string             // 可选；管理端建议少用
}

export interface AdminUserListQuery {
  page?: number
  size?: number
  username?: string
  email?: string
  phone_number?: string
  nickname?: string
  role?: AdminUserRole
  status?: AdminEntityStatus
  can_stream?: boolean
}
```

**Helpers（P0）**:

| 函数 | 对齐 |
|------|------|
| `normalizeCanStream` | 缺省 **true**（V2.1）；仅显式 `false` → false |
| `canChangeUserRole` | 仅 SUPERADMIN |
| `canEditAdminUser` | 禁自己；ADMIN 禁编 SUPERADMIN |
| `getEditableRoleOptions` | 超管：REGULAR/ADMIN/SUPERADMIN；ADMIN：`[]` |
| `getDailyStatusOptions` | NORMAL/BANNED |
| `getDailyRoleFilterOptions` | 无 MODERATOR |

P1/P2 类型另建：`src/types/expertMe.ts`、`src/types/brandCommerce.ts`（命名遵循文件创建规范）。

### 6.5 最终路由表（前端对照《权威 V2》§13）

| Domain | 网关路径 | Method | 后端 | 前端 |
|--------|----------|--------|------|------|
| admin-users | `/api/users/admin/users` | GET | ✅ | ✅ `getAdminUsers` |
| admin-users | `/api/users/admin/users/{uuid}` | PATCH | ✅ | ✅ `adminUpdateUser` |
| rooms | `/api/core/rooms` | POST | ✅ 门禁 | ✅ CreateLive 门禁 |
| experts-me | `/api/core/experts/me` | GET/PATCH | ✅ | ✅ `getMyExpert` / `updateMyExpert` |
| experts-me | `/api/core/experts/me/avatar` | POST | ✅ | ✅ `uploadMyExpertAvatar` |
| brand-members | `/api/core/admin/brands/{id}/members` | POST/GET/DELETE | ✅ | **前端已下线**（无封装/无页） |
| brand-desk | `/api/core/brands/me` | GET | ✅ | ✅ `getMyBrands` |
| brand-products | `/api/core/brands/{id}/products`… | GET/POST/PATCH/publish/off | ✅ | ✅（`BrandWorkbench`） |
| admin-products | `/api/core/admin/brand-products`… | GET/PATCH/DELETE | ✅ | **前端已下线**（无封装/无页） |

内部路径 `/api/users/internal/users/{uuid}/avatar` **仅服务间**，前端禁止调用。

---

## 七、页面与文件清单

### 7.1 目录结构

```
src/
├── api/
│   ├── user.ts                 # P0：getAdminUsers / adminUpdateUser
│   ├── expert.ts               # P1：experts/me* ✅
│   └── brands.ts               # P2：brands/me、products（成员侧）✅；Admin brand-products 封装已下线
├── types/
│   ├── adminUser.ts            # P0 ✅
│   ├── auth.ts                 # can_stream ✅
│   ├── expertMe.ts             # P1 ✅
│   └── brandCommerce.ts        # P2 ✅
├── store/
│   └── auth.ts                 # canStream / canCreateRoom / isSuperAdmin ✅
├── pages/
│   ├── admin/user/
│   │   ├── UserList.vue        # ✅
│   │   └── UserEditDialog.vue  # ✅
│   ├── profile/
│   │   └── Profile.vue         # ✅ 创建直播 + P1/P2 入口（无品牌成员/商品治理菜单）
│   ├── live/CreateLive.vue     # ✅ B5 新建门禁
│   ├── expert/MyExpert.vue     # P1 ✅
│   └── brand/BrandWorkbench.vue# P2 ✅ 成员工作台
├── pages.json                  # 注册页 ✅（Admin BrandProductList / BrandMemberManager 已移除）
└── test/
    └── adminUser.test.ts       # P0 helpers ✅
```

> ~~`admin/brandProduct/`~~、~~`admin/brand/BrandMemberManager`~~：**前端已下线**，勿再注册或引用。

### 7.2 管理端用户页 UI（对齐《权威 V2》§10.1）

| 区域 | 内容 |
|------|------|
| 筛选 | username、email、phone_number、nickname、role、status、can_stream |
| 列表列 | 头像、昵称/用户名、手机、角色 tag、状态 tag、**开播 tag**、时间、编辑 |
| 编辑弹窗 | **禁止开播 / 恢复开播** \| **禁用/恢复账号** \| **设为管理员**（仅超管，二次确认）；开播为次要紧急操作 |
| 禁止文案 | 「设为专家」「设为品牌商」——改为跳转业务页绑定/加入成员（P1/P2） |

### 7.3 小程序入口（对齐《权威 V2》§10.2）

| 条件 | 入口 |
|------|------|
| `can_stream===false` 且非管理员 | 「创建直播」灰显 + Toast「开播功能已被禁用」 |
| 默认可播（true） | 「创建直播」正常可用，勿灰显 |
| 已登录（P1） | 个人中心「我的专家页」**始终展示**；页内 `GET /experts/me`：有对象则编辑，`data=null` → 页内空态（勿 Toast） |
| 已登录（P2） | 个人中心「品牌工作台」**始终展示**；页内 `GET /brands/me` 空列表 → 页内空态（勿 Toast） |

---

## 八、核心流程

对齐《权威 V2》§7。

### 8.1 列表

```
UserList.onShow
  → isAdmin？否：返回/提示
  → getAdminUsers({ page, size, username?, email?, phone_number?, nickname?, role?, status?, can_stream? })
  → items.map(normalizeAdminUserResponse)
  → 渲染角色/状态/开播 tag
  → 空态 / 错误态 / 分页（筛选取消 → page=1）
```

### 8.2 编辑（禁止 / 恢复开播）

```
1. 禁编自己 / ADMIN 禁编 SUPERADMIN
2. 预填 initialRole / initialStatus / initialCanStream
3. 仅变更字段组成 PATCH Body
4. 含 role → 二次确认（仅超管能走到）
5. adminUpdateUser(public_id, payload)
6. 若 payload.can_stream === true → Toast「请对方退出并重新登录（或刷新登录）后再开播」
7. 关闭弹窗 → 刷新列表
```

### 8.3 禁止开播 / 封禁（用户侧）

```
Admin PATCH can_stream=false 或 status=BANNED
  → 后端吊销会话
  → 目标用户后续请求 3001/401
  → request 统一清会话并跳登录
  → 不可新建房间；旧房管理仍可能短暂可用直至 401（封禁后写接口随 401 失败）
```

### 8.4 新建直播门禁（B4 + B5）

```
canCreateRoom = can_stream（缺省 true） || isAdmin（旁路）
新建：can_stream===false 时 Toast「开播功能已被禁用」并阻断（后端 3002 同文案）
编辑旧房：不因 can_stream=false 阻断
```

### 8.5 专家改头像并同步（P1）

```
1. GET /api/core/experts/me
   → 200 + 专家对象：继续编辑
   → 200 + data=null：空态/隐藏入口（勿当错误 Toast）
2. POST /api/core/experts/me/avatar?sync_user_avatar=true（未绑定写路径 → 404）
3. 成功：展示新头像；可选刷新 /users/me
4. 内容安全 2004/2005：统一人话 Toast
```

### 8.6 品牌商上架商品（P2）

```
1. 用户已在 brand_members（由后端 Admin members API 维护；小程序无成员管理页）
2. 用户 GET /api/core/brands/me → 选品牌
3. POST products → DRAFT → publish → ON_SALE（BrandWorkbench）
4. 平台 Admin 强制下架：后端仍有 /admin/brand-products；前端治理页已下线
```

---

## 九、错误码处理

对齐《权威 V2》§8。

| code | HTTP | 场景 | 前端处理 |
|------|------|------|----------|
| 200 | 200 | 成功（含 `GET /experts/me` 未绑定：`data=null`；`GET /brands/me` 无成员：空列表） | 正常 / 空态隐藏入口，**勿当错误** |
| 2004 | 404 | 用户/专家/商品不存在；`PATCH/POST /experts/me*` 未绑定（写路径） | 人话：「用户不存在」「暂无绑定的专家页」「商品不存在」 |
| 3001 | 401 | Token 无效或会话已吊销 | `request.ts` 统一跳登录 |
| 3002 | 403 | 非管理员；开播功能已被禁用；非品牌成员；ADMIN 改 role；改自己 | Toast 展示后端 message 或「开播功能已被禁用」 |
| 4001 | 422 | 参数非法（如 ADMIN 设 PENDING_REVIEW） | 展示 message |
| 1002 | 500 | 数据库错误 | 「服务异常，请稍后重试」 |

---

## 十、列表 / 编辑 / 返回规范对齐

| 规范 | 要求 |
|------|------|
| 列表 | 信息聚合、tag 可见、筛选变更 page=1、`:key="public_id"` |
| 编辑 | 保存 initial*、仅提交变更、改 role 二次确认、恢复开播 Toast |
| 返回 | 无权限 navigateBack / switchTab Profile；未登录带 redirect |
| 分页 | 使用 `size`，默认建议 20 |

---

## 十一、运营文案与 SOP（对齐《权威 V2》§10）

### 11.1 文案

- 开播：**「禁止开播」 / 「恢复开播」**（非「设为主播角色」；亦勿写「开通开播资格」）  
- 角色：**「设为管理员」 / 「取消管理员」**（仅超管）  
- 状态：**「禁用」 / 「恢复」**（NORMAL↔BANNED）  
- 列表 tag：**「可开播」 / 「已禁止开播」**  
- 用户侧拦截：**「开播功能已被禁用」**  
- ❌ 「设为专家」「设为品牌商」

### 11.2 运营 SOP（封主播）— 前端不自动化，可在帮助/备注展示

1. 禁用账号，或仅「禁止开播」（后端自动吊销会话）  
2. 如仍在播：到直播管理结束房间 / 必要时轮换密钥（独立操作）  
3. 如有专家页：下架专家 `is_active=false`  
4. 如有品牌商品：Admin 强制下架（后端 API；**前端治理页已下线**）

---

## 十二、行动清单

| # | Phase | 任务 | 文件 | 状态 |
|---|-------|------|------|------|
| A1 | P0 | 类型 `can_stream` + Query + Helpers | `types/adminUser.ts` | ✅ |
| A2 | P0 | API 列表/PATCH | `api/user.ts` | ✅ |
| A3 | P0 | 列表筛选手机/昵称/开播 + tag「可开播/已禁止开播」 | `UserList.vue` | ✅ 已落地；**文案对齐 V2.1** |
| A4 | P0 | 编辑：禁止/恢复开播、禁自己、仅超管 role | `UserEditDialog.vue` | ✅ 已落地；**文案对齐 V2.1** |
| A5 | P0 | JWT / store；`normalizeCanStream` 缺省 true | `auth.ts` / `store/auth.ts` / `adminUser.ts` | ✅ 已落地；**缺省须改 true** |
| A6 | P0 | CreateLive / Profile：仅 false 拦截，文案「开播功能已被禁用」 | `CreateLive.vue` `Profile.vue` | ✅ 已落地；**文案对齐 V2.1** |
| A7 | P0 | Helpers 单测 | `test/adminUser.test.ts` | ✅ |
| A8 | P0 | V1 文档顶部指向 V2 | V1 前端文档 | ✅ |
| B1 | P1 | `experts/me*` API 封装 | `api/expert.ts` | ✅ |
| B2 | P1 | `MyExpert.vue` + 内容安全 | `pages/expert/MyExpert.vue` | ✅ |
| B3 | P1 | Profile 入口「我的专家页」 | `Profile.vue` | ✅ |
| C1 | P2 | brands/me + products API（成员侧） | `api/brands.ts` | ✅ |
| C2 | P2 | `BrandWorkbench.vue` | 工作台页 | ✅ |
| C3 | P2 | Admin `brand-products` 治理页 | admin 页 | **已下线** |
| C4 | P2 | Admin 品牌成员管理入口 | `BrandMemberManager` | **已下线** |
| C5 | P2 | Profile「品牌工作台」入口 | `Profile.vue` | ✅ |

---

## 十三、测试要点（对齐《权威 V2》§11 编号）

> 编号与后端 **T1–T13** 一致，便于联调对表。前端另标执行面：代码门禁 / 单测 / 联调。

### P0

| # | 用例 | 预期 | 前端验证 |
|---|------|------|----------|
| T1 | REGULAR + can_stream=false 创建房间 | 403「开播功能已被禁用」 | [x] CreateLive/Profile 拦截；联调确认后端 3002 文案 |
| T2 | REGULAR + can_stream=true（默认）创建房间 | 200 | [ ] 联调（新注册/refresh 后默认可播） |
| T3 | Admin 禁止后再恢复 can_stream，refresh 后建房 | 200 | [ ] 联调 + Toast refresh/重登话术 |
| T4 | ADMIN PATCH 改他人 role | 403 | [x] UI 无 picker；单测 `canChangeUserRole` |
| T5 | SUPERADMIN 任命 ADMIN | 200 | [ ] 联调 |
| T6 | ADMIN PATCH 自己 status=BANNED | 403 | [x] 禁编自己；单测 |
| T7 | 封禁后旧 access 调 live_core | 401 | [ ] 联调（前端跳登录） |
| T8 | 禁止开播后旧 access 建房 | 401 | [ ] 联调 |
| T8b | 恢复开播后不 refresh、旧 access 仍 false | 403 | [ ] 联调（与 Toast 话术一致） |
| T9 | 列表 `phone_number`/`nickname`/`can_stream` | 筛选正确（含「已禁止开播」） | [ ] 联调 |

### P1 / P2（前后端均已可联调）

| # | 用例 | 预期 | 前端验证 |
|---|------|------|----------|
| T10 | 未绑定 GET /experts/me | **200，`data=null`**（非错误） | [ ] MyExpert **页内空态**；入口仍可见；**勿 Toast / 非错误页** |
| T10b | 未绑定 PATCH /experts/me | 404 | [ ] 写路径失败提示；不与 GET 空态混淆 |
| T10c | 无品牌成员 GET /brands/me | 200，`items=[]` | [ ] BrandWorkbench **页内空态**；入口仍可见；勿 Toast |
| T11 | 绑定后改头像+sync | experts 与 users 头像一致 | [ ] 联调 sync_user_avatar |
| T12 | 非成员 POST 商品 | 403 | [ ] BrandWorkbench / 联调 |
| T13 | 成员上架后 Admin 强制下架 | status=OFF_SALE | [ ] 后端 API 联调；**前端商品治理页已下线** |

### Helpers 单测（前端补充，不替代后端 T）

| 项 | 状态 |
|----|------|
| normalizeCanStream / canEditAdminUser / canChangeUserRole / 日常枚举选项 | ✅ 11 passed |

---

## 十四、检查清单

- [x] 文件名含项目名 `Live-Saas-Wechat` 与版本 `-v2.0`（内容版本 **2.1.0**，对齐权威 V2.1）  
- [x] 能力分层 / A–G 映射 / 权限矩阵 / JWT / 吊销体验与《权威 V2》**V2.1** 一致（默认可播 + 禁止开播）  
- [x] P0/P1/P2 API 路径与《权威 V2》§5、§13 零偏差（含 method）  
- [x] 错误码表与后端 §8 对齐  
- [x] 测试编号与后端 §11（T1–T13）对齐  
- [x] 明确：**后端** P0–P2 已落地；**前端** P0–P2 已落地可联调  
- [x] `GET /experts/me` 未绑定 = 200/`null` 空态（勿当错误）；写路径 404；T10b/T10c 已列  
- [x] 禁止项：错误网关、错误文案、用 role 表达开播/专家/品牌  
- [x] P0 单测通过  
- [x] P1/P2：`MyExpert` / `BrandWorkbench` 已注册；Profile 工作台入口已接通  
- [x] Admin `BrandProductList` / `BrandMemberManager` 与相关 Profile 菜单、Admin API 前端封装 **已下线**（2026-08-01）  

---

## 十五、更新日志

| 版本 | 日期 | 状态 | 变更摘要 |
|------|------|------|----------|
| 2.0 | 2026-07-14 | 设计完成 | 首版提纲；P0 落地说明 |
| 2.0.1 | 2026-07-14 | 设计完成 | 命名口径统一后重建；交叉引用对齐 |
| 2.0.2 | 2026-07-14 | 设计完成 | **严格零偏差对齐《权威 V2》**：补 A–G、权限矩阵、JWT/吊销、P0–P2 全量路由与 Schema、§7 流程、§8 错误码、§10 文案 SOP、T1–T13 对表；澄清后端已落地 vs 前端 P1/P2 待开发 |
| 2.0.3 | 2026-07-14 | 设计完成 | **前端 P1/P2 落地**：MyExpert、BrandWorkbench、Admin 商品治理/成员管理、Profile 操作入口；行动清单 B1–C5 勾选 |
| 2.0.4 | 2026-07-14 | 设计完成 | **对齐权威源 V2.0.4**：主对齐改为《14-…-V2-…》；`GET /experts/me` 未绑定改为 200/`null` 空态；补 T10b/T10c；清扫「前端待做/待建」过时表述 |
| 2.1.0 | 2026-07-30 | 设计完成 | **对齐权威 V2.1**：默认可播；Admin「禁止/恢复开播」；JWT/`normalizeCanStream` 缺省 true；文案「开播功能已被禁用」；列表 tag「已禁止开播」 |
| 2.1.1 | 2026-08-01 | 设计完成 | **下线** Admin「品牌商品管理 / 品牌成员管理」前端入口与 API 封装；文件树/行动清单 C3–C4/路由表标已下线；保留 `BrandWorkbench` 与后端 members/admin-products 契约对照 |

---

## 附录 A：与《权威 V2》章节对照

| 《权威 V2》 | 本文 |
|------------|------|
| 文档定位 / 能力分层 / Phase | 文首定位 + §二 Phase |
| 需求 A–G | §二 前端映射 |
| §2 权限矩阵 | §三 |
| §3 JWT | §四 |
| §4 会话吊销 | §五 |
| §5 API / §13 路由表 | §六 |
| §6 Schemas | §六.4 |
| §7 执行流程 | §八 |
| §8 错误码 | §九 |
| §10 前端/运营体验 | §七.2–7.3、§十一 |
| §11 测试 | §十三 |
| §9 V1 修订对照 | 见 V1 前端顶部修订说明 + 本文禁止项 |
| §1 / §12 DB/部署 | 后端职责；前端仅消费契约，不写 DDL |

## 附录 B：前端设计文档系列命名口径（本仓库）

| 模块 | 文件名 |
|------|--------|
| 14 权威 V2 | `14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md` |
| 14 | `Live-Saas-Wechat-14-管理端用户管理-前端设计文档-v1.0.md` |
| 14 V2 前端 | `Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md`（本文） |

其余模块命名见仓库 `docs/` 现网文件；新建须含项目名 + 版本号。

---

**文档结束**
