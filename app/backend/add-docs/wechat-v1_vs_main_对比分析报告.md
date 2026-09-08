# wechat-v1 与 main 管理能力融合分析报告

**生成日期**: 2026-07-29  
**对比分支**: `origin/wechat-v1` vs `main`  
**目标**: 梳理小程序端后端实现与 App 端本地实现的管理功能差异，形成可执行的融合策略。

---

## 一、核心结论

本次融合不建议采用“整体合并 `wechat-v1`”的方式。

推荐策略是：**以 App 端当前 main 实现为主干，选择性吸收 wechat-v1 的管理、运营、安全、合规能力**。

原因如下：

1. App 端本地实现已经围绕 App 场景做过权限、专家分类、直播间筛选、管理数据面板、接口裁剪等优化，不能被小程序端实现直接覆盖。
2. `wechat-v1` 的优势主要集中在管理后台、内容安全、注销清理、用户运营、留言管理、品牌电商等平台级能力，这些能力值得迁入。
3. 两个分支在权限模型、分类模型、路由风格上存在架构取舍差异，直接合并会引入重复接口、迁移冲突和权限语义漂移。

最终融合原则：

> App 端保留当前架构和已优化业务模型；wechat-v1 提供管理、合规、运营、安全能力；冲突处以 App 端产品需求为准，以 wechat-v1 文档和实现作为迁移参考。

---

## 二、融合决策总表

| 模块 | 决策 | 原因 |
|---|---|---|
| 权限体系 | 保留 App 主干，吸收 wechat-v1 增强点 | App 的 `permissions.py` 更集中；wechat-v1 的 session revocation、`can_stream`、`verify_admin_role` 值得迁入 |
| 管理端房间 | 修改后融合 | 需要 `/admin/rooms` 兼容入口，但底层应复用 App 端现有房间查询能力 |
| 管理端用户 | 融合并补注册 | 本地存在部分 users 管理路由但未注册；wechat-v1 的封禁、撤权、开播门禁更完整 |
| 内容安全 | 分阶段融合 | 属于合规底座，必须迁入；但接入点多，不能一次性粗暴改完 |
| 留言管理 | 融合 | 管理端留言、批量删除、清空房间、WebSocket、限流、缓存都是运营必需能力 |
| 账户注销清理 | 修改后融合 | wechat-v1 设计完整，但跨服务编排要适配 App 当前服务边界 |
| 专家模块 | 保留 App 分类模型，融合专家自认领和链式权限 | App 的专家科室体系更成熟；`/experts/me` 和房主绑定专家权限值得迁入 |
| 分类/科室 | 保留 App 方案为主，选择性吸收层级能力 | 不应直接覆盖 App 的 `ExpertDepartment`、映射、合并、同义词等设计 |
| 品牌电商 | 独立里程碑融合 | 能力完整但工作量大，建议独立排期，不塞进 P0 |
| 路由架构 | 暂不大规模重构 | 风格统一不是管理接入前置条件，早做会扩大冲突面 |
| 小程序特定登录 | 暂不融合 | 微信小程序授权等能力不是 App 端当前必需 |

---

## 三、关键差异与取舍

### 3.1 权限与鉴权体系

#### wechat-v1 的实现

- 删除了集中式 `permissions.py`。
- 倾向在 Service 内部实现 `_check_write_permission`、`_check_admin_role` 等细粒度权限。
- 新增 `verify_admin_role` 管理员依赖。
- 新增 Redis 会话吊销机制：封禁、撤权后旧 token 立即失效。
- 新增 `can_stream` 开播门禁，控制用户是否允许创建直播间。

#### App main 的实现

- 保留 `backend/live_core_service/app/core/permissions.py`，集中处理 Owner/Admin 权限。
- 资源权限更偏 App 使用场景，尤其是直播间 owner、管理员、可见性等公共校验。
- 当前本地存在一个风险：部分 users 管理路由存在但没有注册。

#### 融合建议

**保留**：

- 保留 App 端 `permissions.py`，作为通用权限工具。
- 保留 App 端 Owner/Admin 资源权限语义。

**融合**：

- 融入 `verify_admin_role`，用于纯管理端接口。
- 融入 session revocation，确保封禁、撤权、注销后旧会话即时失效。
- 融入 `can_stream` 字段、schema、JWT claim 和建房校验。

**修改后融合**：

- 专家、品牌、场次绑定这类链式资源权限，可以吸收 wechat-v1 的 Service 内联校验方式。
- 通用房间权限仍走 App 的公共权限函数，避免重复实现。

**不建议**：

- 不要删除 App 端 `permissions.py`。
- 不要把所有权限都改成 Service 内联，这会让 App 端已形成的权限边界分散。

---

### 3.2 管理端房间能力

#### wechat-v1 的实现

- 新增 `GET /admin/rooms`。
- 管理员可以查看全站直播间，包括私密房间。
- 支持标题搜索、房主筛选、分页。
- 写操作复用现有房间接口。

#### App main 的实现

- 没有独立 `/admin/rooms`。
- 但 App 端对通用 `GET /rooms` 已做更多筛选和排序优化，包括状态、日期、开始时间等。

#### 融合建议

**融合**：

- 新增 `/admin/rooms` 管理端入口。

**修改后融合**：

- 不直接复制 wechat-v1 的查询实现。
- 建议做一个薄封装 facade：API 形态对齐 wechat-v1，底层调用 App 现有房间查询逻辑。
- 管理员查询时放开私密房间可见性限制。

**原因**：

- 管理后台需要稳定的 `/admin/rooms` 入口。
- App 端已有查询能力更贴近当前业务，不应丢弃。

---

### 3.3 管理端用户与开播门禁

#### wechat-v1 的实现

- 用户管理支持封禁、解封、撤销开播权限、恢复开播权限。
- `can_stream` 进入用户模型、schema、JWT。
- 建房时校验 `can_stream`。
- 管理操作后可吊销用户已有会话。

#### App main 的问题

- 本地 users 服务中存在管理路由文件，但部分 router 未注册。
- `can_stream` 和建房门禁缺失。
- session revocation 缺失。

#### 融合建议

**P0 必须融合**：

- 注册 users 管理路由：`admin_users_router`、`admin_products_router`、`admin_subscriptions_router`。
- 恢复 `can_stream` 字段、迁移、schema、JWT claim。
- 在创建直播间时增加 `can_stream` 校验。
- 管理员封禁、撤权后触发 session revocation。

**原因**：

- 这是管理后台最基础的用户运营能力。
- 没有会话吊销时，封禁和撤权不会立即生效，安全语义不完整。

---

### 3.4 内容安全与审核

#### wechat-v1 的实现

- 新增完整 `content_safety/` 模块。
- 包含规则、日志、缓存、规则引擎、医学词库、外部政治文本检测客户端。
- 管理端提供规则管理和审核日志查询。
- 业务写路径接入 `check_content_safety()` 或 `check_scene_fields()`。

#### App main 的实现

- 当前没有统一内容安全能力。

#### 融合建议

**必须融合，但分阶段落地**。

第一阶段：

- 迁入 `content_safety/` 模块。
- 新增 `content_safety_rules`、`content_safety_logs` 迁移。
- 注册管理端规则和日志接口。
- 接入留言、房间标题、房间描述这三个最高风险写路径。

第二阶段：

- 接入 room tab、搜索词、专家展示字段、品牌商品字段。
- 接入 warn 级别日志和后台审核视图。
- 补齐医学词库 seed 和外部检测配置。

**原因**：

- 内容安全属于合规底座。
- 但该模块接入面大，建议先建规则引擎和核心写路径，再逐步扩展，降低一次融合风险。

---

### 3.5 留言管理

#### wechat-v1 的实现

- 管理端留言列表。
- 单条删除、批量删除、清空房间留言。
- WebSocket 消息推送。
- Redis 缓存留言列表。
- 发送频率限制。
- 留言内容安全检查。
- 注销用户昵称占位。

#### App main 的实现

- 留言管理能力不完整，缺少管理端全局治理闭环。

#### 融合建议

**融合**：

- 管理端留言列表、删除、批量删除、清空房间留言。
- WebSocket。
- 发送频率限制。
- 发送留言前内容安全检查。
- Redis 缓存可以随留言列表优化一起迁入。

**修改后融合**：

- 注销用户昵称占位依赖 `deactivated_users` 标记，应在账户注销清理能力完成后接入。

**原因**：

- 留言是高频内容生产入口，必须同时具备运营管理、性能优化和内容审核。

---

### 3.6 账户注销与跨模块清理

#### wechat-v1 的实现

- 新增 `DeactivateCleanupService`。
- 新增 `internal_users.py` 内部清理接口。
- 新增 Redis `deactivated_users` 标记。
- 注销后清理订阅、观看历史、收藏、专家认领、品牌成员等数据。
- 读路径展示“账号已注销”。

#### App main 的实现

- 没有完整注销清理闭环。

#### 融合建议

**修改后融合**：

- 迁入注销清理策略，但不要假设 App 端服务边界与 wechat-v1 完全一致。
- 如果 App 当前是单服务或服务拆分不同，`internal_users.py` 要改为适配当前部署结构的内部接口。
- 先做写路径清理和 Redis 标记，再做读路径占位展示。

**建议顺序**：

1. 建立内部鉴权配置：`INTERNAL_SERVICE_TOKEN`。
2. 迁入 `deactivated_users.py`。
3. 迁入 `DeactivateCleanupService`。
4. 接入 users 注销流程。
5. 接入留言、专家、品牌等读路径占位。

**原因**：

- 注销清理是隐私合规能力。
- 但跨服务调用最容易因部署差异出错，需要按 App 当前架构改造。

---

### 3.7 专家与分类/科室体系

#### wechat-v1 的实现

- Category 支持 `parent_id` 层级树。
- 房间可挂分类。
- 专家不再挂全局 `category_id`，主要用 `department` 字段展示和筛选。
- 新增 `/experts/me` 专家自认领。
- 场次专家绑定支持 Admin 或房主链式权限。

#### App main 的实现

- 已经有更完整的专家科室和分类优化：
  - `ExpertDepartment`
  - 分类映射
  - 未映射处理
  - 审核、合并、同义词
  - App 端专家分类接口优化
- `Expert.category_id` 仍然存在。

#### 融合建议

**保留**：

- 保留 App 端专家分类/科室体系。
- 暂时保留 `Expert.category_id`，除非产品确认专家不再需要权威分类筛选。

**融合**：

- 融合 `/experts/me` 专家自认领。
- 融合场次专家绑定的 Admin/房主链式权限。

**选择性融合**：

- `categories.parent_id` 可以评估迁入，用于二级科室树。
- `live_rooms.category_id` 或房间主分类可以评估迁入，用于管理端和 C 端房间分类。

**不建议**：

- 不要直接套用 wechat-v1 移除 `Expert.category_id` 的迁移。
- 不要覆盖 App 端现有专家分类迁移和 seed。

**原因**：

- App 端在专家分类上已经走得更深，wechat-v1 的方案更偏简化。
- 专家分类一旦迁移错，会影响筛选、导入、后台管理和前端展示。

---

### 3.8 品牌与电商

#### wechat-v1 的实现

- 新增 `BrandMember`。
- 新增 `BrandProduct`。
- 新增品牌工作台 `GET /brands/me`。
- 新增管理端全局商品管理。
- 商品支持状态管理和软删语义。

#### App main 的实现

- 当前缺少对应平台电商能力。

#### 融合建议

**建议融合，但作为独立里程碑**。

需要融合：

- 品牌成员模型与 API。
- 品牌商品模型与 CRUD。
- 管理端商品列表、审核、上下架。
- 品牌软删和商品状态语义。

不建议放进 P0：

- 品牌电商涉及模型、权限、管理端、前端工作台、商品状态和潜在支付链路，工作量大。
- 与用户封禁、内容安全、房间管理这类底座能力混在一起，会拖慢基础管理能力上线。

---

### 3.9 路由架构

#### wechat-v1 的实现

- 倾向每个模块统一 `router`。
- prefix 在 `api.py` 集中管理。
- 路由结构更简洁。

#### App main 的实现

- 倾向按角色和场景拆分 router，例如 public/admin/owner 等。
- 权限边界更清楚，但注册层更复杂。

#### 融合建议

**暂不做大规模路由重构**。

短期只做：

- 注册缺失路由。
- 新增必要管理端入口。
- 避免双重 prefix。

中长期再做：

- 统一 router 命名规范。
- 整理 prefix 策略。
- 删除重复路由和废弃入口。

**原因**：

- 路由风格统一不是管理功能接入的前置条件。
- 大规模重构容易引入回归，也会和正在融合的功能发生冲突。

---

## 四、需要保留、融合、修改、删除的清单

### 4.1 需要保留

| 项目 | 原因 |
|---|---|
| `backend/live_core_service/app/core/permissions.py` | App 端已有集中权限工具，适合通用 Owner/Admin 校验 |
| App 端房间列表筛选和排序 | 已贴近 App 当前消费场景 |
| App 端专家科室/分类体系 | 比 wechat-v1 更完整，支持审核、映射、合并、同义词、未映射处理 |
| App 端 AdminStats 设计 | 管理数据面板对 App 管理后台有价值 |
| App 端已裁剪的真实消费接口 | 避免恢复小程序端不需要的冗余 API |

### 4.2 需要直接融合

| 项目 | 原因 |
|---|---|
| `verify_admin_role` | 管理端接口统一鉴权 |
| session revocation | 封禁、撤权、注销后旧 token 即时失效 |
| `can_stream` | 管理员可控制用户是否有开播能力 |
| 管理端用户路由注册 | 本地已有实现但入口缺失 |
| 内容安全规则和日志基础模块 | 合规底座 |
| 管理端留言治理 | 运营后台必需 |
| Redis 缓存工具 | 支撑留言缓存、注销标记、会话吊销 |
| 专家自认领 `/experts/me` | 补齐专家用户闭环 |

### 4.3 需要修改后融合

| 项目 | 修改方式 |
|---|---|
| `/admin/rooms` | API 对齐 wechat-v1，底层复用 App 房间查询 |
| 内容安全业务接入 | 分批接入留言、房间、Tab、搜索、专家、品牌字段 |
| 注销清理 | 按 App 当前服务边界调整内部编排 |
| 专家链式权限 | 融入 wechat-v1 思路，但保留 App 权限工具 |
| 分类层级化 | 只迁入 `parent_id` 等兼容增强，不覆盖 App 专家科室设计 |
| 品牌电商 | 独立里程碑迁入，避免拖慢 P0 |

### 4.4 暂不融合或不建议融合

| 项目 | 原因 |
|---|---|
| 删除 `permissions.py` | 会破坏 App 当前权限主干 |
| 移除 `Expert.category_id` | App 端产品需求未确认，风险高 |
| 微信小程序特定登录 | App 端当前不是必需 |
| 大规模 router 风格重构 | 非 P0，容易扩大冲突 |
| 直接套用 wechat-v1 分类迁移和 seed | 可能覆盖 App 端后续专家分类设计 |

### 4.5 需要删除或清理

这里的“删除”不是指删除 App 端能力，而是融合完成后清理重复和错误实现。

| 项目 | 原因 |
|---|---|
| 重复的管理端房间查询实现 | 保留一个底层查询，避免 `/rooms` 和 `/admin/rooms` 行为分叉 |
| 重复的权限校验代码 | 通用场景抽回 `permissions.py`，业务链式权限保留在 Service |
| 废弃或未注册的 router 引用 | 避免文档有接口、运行时无接口 |
| 过期测试 | 如果断言旧权限或旧分类模型，需要更新或移除 |
| 无消费方的小程序端专属 API | 避免 App 后端暴露无维护承诺的接口 |

---

## 五、优先级与实施路线

### P0：先补管理和安全底座

目标：让管理后台具备最基本、可用且安全的用户和房间治理能力。

1. 修复 `admin_stats.py` 的 `Expert` 未导入问题。
2. 注册 users 服务中缺失的管理路由。
3. 融合 `can_stream` 和建房门禁。
4. 融合 session revocation。
5. 新增 `/admin/rooms` 兼容入口。
6. 融合 `verify_admin_role`。

验收标准：

- 管理员可以查看全站直播间。
- 管理员可以封禁用户、撤销开播权限。
- 被封禁或撤权用户的旧 token 失效。
- 无开播权限用户无法创建直播间。
- 管理端统计接口不再 500。

### P1：补内容治理和留言运营

目标：让平台能管内容、管留言、留审计。

1. 迁入 `content_safety/` 基础模块。
2. 新增规则表和日志表迁移。
3. 注册内容安全管理端 API。
4. 接入留言、房间标题、房间描述写入检查。
5. 融合管理端留言列表、删除、批量删除、清空房间。
6. 接入留言 WebSocket、限流和缓存。

验收标准：

- 管理员可配置规则。
- 命中 block 的内容无法写入。
- 命中 warn 的内容可写入但有日志。
- 管理员可治理留言。
- 留言高频发送被限制。

### P2：补隐私合规和专家闭环

目标：处理用户注销、专家认领和跨模块残留数据。

1. 融合 `deactivated_users.py`。
2. 融合注销清理服务。
3. 按 App 服务边界改造内部清理接口。
4. 接入 users 注销流程。
5. 融合 `/experts/me`。
6. 接入留言、专家、品牌等读路径的注销占位。

验收标准：

- 用户注销后跨模块数据按策略清理。
- 留言等历史内容不泄露已注销用户身份。
- 专家可以完成自认领和资料维护。

### P3：品牌电商和分类增强

目标：补齐平台变现和更丰富的信息组织能力。

1. 融合品牌成员。
2. 融合品牌商品。
3. 融合管理端商品治理。
4. 评估 `categories.parent_id`。
5. 评估 `live_rooms.category_id` 或房间主分类。
6. 清理路由风格和 prefix 规范。

验收标准：

- 品牌方有工作台。
- 管理员可管理商品。
- 商品上下架和软删语义明确。
- 分类体系与 App 专家科室体系不冲突。

---

## 六、代码层风险点

### 6.1 已发现的本地问题

| 问题 | 影响 | 建议 |
|---|---|---|
| `admin_stats.py` 使用 `Expert` 但未导入 | `/admin/sessions/today` 可能 500 | P0 修复 |
| users 管理路由存在但未注册 | 管理端接口无法访问 | P0 注册 |
| 缺少 `can_stream` | 无法管控开播能力 | P0 融合 |
| 缺少 session revocation | 封禁/撤权不能即时生效 | P0 融合 |
| 缺少内容安全 | 留言、房间、搜索等文本写入无合规防线 | P1 融合 |

### 6.2 合并冲突高风险区域

| 区域 | 风险 |
|---|---|
| migrations | 两边都有分类、专家、内容相关迁移，不能按文件覆盖 |
| models `__init__.py` | 模型移动和导出变化可能导致 import 断裂 |
| `api.py` 路由注册 | 容易出现重复 prefix、漏注册、重复注册 |
| 专家模型 | `category_id` 去留存在设计冲突 |
| 权限依赖 | App 和 wechat-v1 的权限抽象方式不同 |

---

## 七、建议的 PR 拆分

### PR 1：管理基础能力

- 修 `admin_stats.py`。
- 注册 users 管理路由。
- 融合 `verify_admin_role`。
- 融合 `can_stream`。
- 融合 session revocation。
- 增加 `/admin/rooms`。

### PR 2：内容安全基础

- 迁入 `content_safety/`。
- 增加迁移和 seed。
- 注册管理 API。
- 接入留言和房间文本检查。
- 添加内容安全单测。

### PR 3：留言治理

- 管理端留言列表。
- 单删、批删、清空。
- WebSocket。
- 限流。
- Redis 缓存。

### PR 4：注销清理

- `deactivated_users.py`。
- `DeactivateCleanupService`。
- 内部清理接口。
- users 注销流程接入。
- 读路径占位。

### PR 5：专家闭环

- `/experts/me`。
- 专家自认领。
- 专家资料自维护。
- 场次专家绑定链式权限。

### PR 6：品牌电商

- `BrandMember`。
- `BrandProduct`。
- 品牌工作台。
- 管理端商品治理。
- 商品状态和软删。

### PR 7：分类与路由整理

- 评估并迁入 `categories.parent_id`。
- 评估并迁入房间主分类。
- 清理重复路由。
- 统一 prefix 规范。

---

## 八、配置与环境对齐

需要新增或确认以下配置：

```python
REDIS_URL: str = ""
INTERNAL_SERVICE_TOKEN: str = ""
ADMIN_STREAM_BYPASS: bool = False
CONTENT_SAFETY_ENABLED: bool = True
CONTENT_SAFETY_WARN_ONLY: bool = False
POLITICAL_TEXT_API_URL: str = ""
POLITICAL_TEXT_API_KEY: str = ""
```

配置建议：

- `REDIS_URL` 是 session revocation、留言缓存、注销用户标记的共同依赖。
- `INTERNAL_SERVICE_TOKEN` 用于内部注销清理接口鉴权。
- `ADMIN_STREAM_BYPASS` 默认建议为 `False`，避免管理员绕过开播门禁造成权限语义混乱。
- 内容安全可以支持环境级开关，但生产环境默认应开启。

---

## 九、测试策略

建议按风险补测试，而不是简单复制所有 wechat-v1 测试。

必须补：

- 管理员封禁后旧 token 失效。
- 撤销 `can_stream` 后无法建房。
- 管理员可访问 `/admin/rooms`，普通用户不可访问。
- 内容安全 block 拦截写入。
- 内容安全 warn 写入并记日志。
- 管理端留言批量删除和清空房间。
- 注销清理后读路径展示占位。

选择性补：

- 品牌商品状态流转。
- 专家自认领。
- 分类层级树。
- Redis 缓存命中和失效。

需要更新或删除：

- 与旧权限模型强绑定的测试。
- 与旧分类模型强绑定的测试。
- 已无消费方的小程序端专属测试。

---

## 十、最终建议

本次融合应该先解决“管理后台能不能安全管起来”的问题，再解决“平台能力是否完整”的问题。

推荐落地顺序：

1. **P0 管理基础**：用户管理、开播门禁、会话吊销、管理端房间、统计 bug。
2. **P1 内容治理**：内容安全、留言管理、审核日志。
3. **P2 隐私和专家闭环**：注销清理、专家自认领、读路径占位。
4. **P3 商业化和结构整理**：品牌电商、分类增强、路由规范化。

不建议一开始就做大规模路由重构、分类模型替换或品牌电商全量迁移。那些都是有价值的能力，但不应该压在管理基础能力上线之前。

---

## 附：参考文档

| 文档 | 用途 |
|---|---|
| `add-docs/17-管理端管播MVP-后端设计文档.md` | 管理端房间运营 |
| `add-docs/14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md` | 用户管理、`can_stream`、权限修订 |
| `add-docs/12-全局内容安全与审核-后端设计文档.md` | 内容安全规则与审核 |
| `add-docs/13-医学合规文本违禁词库.md` | 医学违禁词库 |
| `add-docs/07-直播间留言-V4-用户展示读时同步增量设计文档.md` | 留言展示、注销占位 |
| `add-docs/16-D-跨模块落地分包索引.md` | 注销清理和跨模块分包 |
| `app修改记录/权限体系优化设计文档_实施版.md` | App 端权限主干 |
| `app修改记录/直播间管理接口优化设计文档.md` | App 端房间接口优化 |
| `app修改记录/专家分类管理_App端接口优化设计文档.md` | App 端专家分类设计 |
| `app修改记录/管理端后台数据面板_AdminStats设计文档.md` | App 端管理数据面板 |

---

## 十一、修订方案交叉审查与补充分析

> 本章对上述融合方案第二章至第十章进行事实核查与补充。以下内容基于对两个分支的完整代码 diff、add-docs 全部设计文档、以及 App 端本地 `app修改记录/` 的交叉比对得出。

### 11.1 对方案整体方向的确认

方案核心判断"以 App 端当前 main 实现为主干，选择性吸收 wechat-v1"完全正确。理由在之前的对比分析中已有充分论证，此处补充三个代码层面的事实支撑：

1. **App 端专家科室体系确实更成熟**：`ExpertDepartment` 表（含 `synonyms` JSONB、`is_verified`、`source` 追踪、`category_id` 映射）+ `Expert.department_id` FK +向前兼容 property，这套受控词表设计明显优于 wechat-v1 仅靠 `department` 文本字段 +简单注释的方案。

2. **App 端 Category 已具备层级能力**：`categories.parent_id` 列和 `children`/`parent` relationship 已经在 ORM 层定义完成（见 `models/content_management.py:72-78`）。但 App 端使用 `ondelete="RESTRICT"`（防止误删），而 wechat-v1 使用 `SET NULL`（删父级时子级变一级）。这是一个需要明确的选择。

3. **`admin_stats_router` 已正确注册**：在 `api.py:132-137`，路由注册和对 `/admin` prefix 的挂载均已完成。该端点的主要问题是 `admin_stats.py:108,118` 使用了 `Expert` 类但 import 行（第 23 行）只导入了 `LiveSessionExpert` 和 `SessionExpertRole`，缺少 `Expert`。这是一个 import 遗漏 bug，而非路由未注册问题。

### 11.2 对二章各条目的逐项核查

#### 权限体系（方案 §2 行 31，§3.1）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "保留 App 主干" | ✅ 正确 | `permissions.py` 仍在使用，被 `admin_stats.py` 等端点引用 |
| "吸收 wechat-v1 session revocation" | ✅ 正确 | wechat-v1 的 `session_revoke.py`（Redis 吊销）+ `deps.py` 中的 `ensure_session_not_revoked()` 调用，是封禁即时生效的关键 |
| "吸收 `can_stream`" | ✅ 正确 | wechat-v1 的 `RoomService.create_new_room()` 中已有完整的开播门禁 + `ADMIN_STREAM_BYPASS` 可配置旁路逻辑 |
| "吸收 `verify_admin_role`" | ✅ 正确 | wechat-v1 在 `deps.py` 实现，返回 403/3003，比 App 端当前各处内联 `check_admin_permission` 更统一 |

**建议补入的细节**：`verify_admin_role` 依赖注入应该作为管理端**新端点**的统一鉴权方式。App 端现有的 `check_admin_permission(role)` 调用可以逐步替换，但不强制（避免扩大改动面）。二者可以共存——`verify_admin_role` 用于新端点，`check_admin_permission` 继续在已有端点工作。

#### 管理端房间（方案 §3.2）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "不直接复制 wechat-v1 的查询实现" | ✅ 正确 | App 端 `crud/room.py` 已有 `list_with_search()`，支持多维度筛选和排序 |
| "做薄封装 facade" | ✅ 正确 | 核心是在 `list_with_search()` 调用时传入 `role='ADMIN'` 来放开私密房可见性 |
| "管理员查询时放开私密房间可见性" | ✅ 正确 | 与 wechat-v1 `list_admin_rooms()` 的设计一致 |

**建议补入的细节**：
- 现有的 `list_with_search()` 已有 `role` 参数和 `role in ['ADMIN', 'SUPERADMIN']` 分支（`crud/room.py:299-300`），管理员本身就能看到私密房。新 `/admin/rooms` 入口只需在调用时传入 `role='ADMIN'` 即可。
- 需要新增的字段是 `owner_user_id` 筛选（`crud/room.py` 的 `list_admin_rooms` 中有 `owner_user_id` 参数），以及返回 `owner_user_id`, `is_private`, `updated_at` 等运营字段（App 端当前 `LiveRoomResponse` 缺少这些字段）。
- wechat-v1 和 App 端在 `list_with_search` 中都增加了 `owner_only` 参数（wechat-v1: `owner_only`, App: 同样的实现），二者一致，无需额外处理。

#### 管理端用户与开播门禁（方案 §3.3）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "本地 users 服务存在管理路由文件但部分未注册" | 需要确认 | 当前仓库可能只有 `live_core_service`。如果 users 管理路由在另一个仓库或服务中，需先确认服务边界 |
| "恢复 `can_stream`" | ✅ 正确 | wechat-v1 的 users 模型、JWT claim、建房门禁均已实现，可直接参考 |
| "建房时校验 `can_stream`" | ✅ 正确 | wechat-v1 `RoomService.create_new_room()` 第 140-148 行有完整校验 |

**需要澄清的问题**：这条依赖于 App 端是否有独立的 `user_service`。从当前仓库看，只有 `live_core_service`。如果 App 端是单服务架构（认证 + 直播都在一个服务中），则：
- `can_stream` 字段需要加在当前服务的 users 等价表中
- `session_revoke.py` 需要适配当前的 Redis 配置
- wechat-v1 的 `internal_users.py` 跨服务调用逻辑需要改为服务内调用

#### 内容安全与审核（方案 §3.4）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "分两阶段落地" | ✅ 正确 | `content_safety/` 模块包含 14 个文件，涉及 engine/models/schemas/crud/service/cache/seed/migrate/medical_lexicon/political_text，一次性迁移风险过高 |
| "先接入留言、房间标题、房间描述三个最高风险写路径" | ✅ 正确 | 这三个场景在 wechat-v1 中接入最成熟（`live_features_service.py` 的 `MessageService`、`RoomService.create_new_room/update_room`） |
| "第二阶段接入 room tab、搜索词、专家展示字段" | ✅ 正确 | wechat-v1 的 `TabService` 中 `check_scene_fields(scene="room_tab")` 的接入是完整参考 |

**建议补入的细节**：
- 第一阶段还应包括 `content_safety_rules` 和 `content_safety_logs` 表的 DDL，以及 seed 数据（至少 29 条 live_core 基础规则）
- `medical_lexicon_data.py`（270 行，32 种违禁词分类）和 `political_text/client.py`（50 行，第三方 API 占位）可以第二阶段再迁入
- 需要确定 `content_safety/service.py` 中的 `check_content_safety()` 和 `check_scene_fields()` 函数的调用约定——wechat-v1 设计为**在 Service 层写库前调用**，而非 API 层调用，这需要在 App 端保持一致

#### 留言管理（方案 §3.5）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "管理端留言治理" | ✅ 可以融合 | wechat-v1 的 `admin_message_router` + `MessageService.admin_list_messages/batch_delete/clear_room_messages` 是完整实现 |
| "WebSocket" | ✅ 可以融合 | wechat-v1 的 `message_ws_router` + `message_push.py` 可以直接迁入 |
| "注销用户昵称占位" | ✅ 正确，后置 | 确实依赖 D2 标记，不应在 P1 强行做 |

**建议补入的细节**：
- `redis_cache.py`（126 行）是留言缓存、限流和注销标记的共同依赖，应该在 P1 留言治理阶段一起迁入
- 留言发送频率限制（5 秒/条）是 `check_message_rate_limit()` 函数，依赖 Redis，随 `redis_cache.py` 一起迁入

#### 账户注销与跨模块清理（方案 §3.6）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "不要假设 App 端服务边界与 wechat-v1 完全一致" | ✅ 关键提醒 | 这是最大的不确定性 |
| "先做写路径清理和 Redis 标记，再做读路径占位" | ✅ 正确 | 与 wechat-v1 的 D2→D3 依赖顺序一致 |

**建议补入的细节**：
- 如果 App 端是单服务架构，`internal_users.py` 的跨服务编排可以简化为同进程调用，但接口可以保留为 HTTP（方便未来拆分服务）
- `DeactivateCleanupService` 中的清理策略（有 `is_active` 就软藏、无软删字段就物理删）是 wechat-v1 经过多次讨论后确定的口径，不应轻易改变
- 需要注意的是 wechat-v1 的清理策略**明令禁止**在注销事务中硬删房间或留言，这个约束需要在 App 端同样生效

#### 专家与分类/科室体系（方案 §3.7）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "保留 App 端专家科室/分类体系" | ✅ 关键决定 | App 端的 `ExpertDepartment` 受控词表是比 wechat-v1 更成熟的设计 |
| "暂时保留 `Expert.category_id`" | ✅ 务实 | App 端 `Expert.category_id` 是 `NOT NULL` 且有 FK 约束，贸然删除风险极高 |
| "不要直接套用 wechat-v1 移除 `Expert.category_id` 的迁移" | ✅ 关键警告 | wechat-v1 移除了 `category_id` 及其索引和关系，App 端不能效仿 |
| "选择性融合 `categories.parent_id`" | 需要修正 | App 端 **已经**有 `parent_id`（`models/content_management.py:73`），只是 `ondelete` 策略（RESTRICT）与 wechat-v1（SET NULL）不同 |

**需要修正的判断**：方案中说 "选择性融合 `categories.parent_id`"——实际上 App 端 Category 的层级能力已经在模型层就绪，只是 `ondelete="RESTRICT"` 的语义与 wechat-v1 的 `SET NULL` 不同。这不是"从 wechat-v1 选择性迁入"的问题，而是两个分支对同一能力做了不同实现方式的选择。需要决定的是**使用 RESTRICT 还是 SET NULL**（而非是否需要 parent_id）。

**建议**：保持 App 端的 `RESTRICT` 语义。RESTRICT 在删除父分类时拒绝操作并提示先迁移子分类，比静默 SET NULL 更安全——针对医学分类场景，静默把"胆胰外科"从"普通外科"下级变成一级分类，可能导致前端树形展示异常。

#### 品牌与电商（方案 §3.8）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "作为独立里程碑" | ✅ 务实 | 品牌电商涉及 2 个新模型（BrandMember, BrandProduct）+ 400 行 BrandCommerceService + 12 个新 API + 迁移 |
| "不建议放进 P0" | ✅ 正确 | 不会拖慢管理基础能力上线 |

**建议补入的细节**：
- P2 或 P3 实施时，需要注意 `BrandMember` 和 `BrandProduct` 的迁移脚本（wechat-v1 有 `migrations/migrate_brand_commerce.py`，60 行）
- `BrandCommerceService` 依赖 `user_profile_client.py`（跨服务用户资料查询），如果 App 端是单服务架构，可以简化为直接查本地 users 表

#### 路由架构（方案 §3.9）

| 方案表述 | 核查结果 | 补充 |
|---|---|---|
| "暂不做大规模路由重构" | ✅ 务实 | 路由重构扩大冲突面，且非功能交付 |
| "短期只做注册缺失路由、避免双重 prefix" | ✅ 正确 | 这是最低摩擦的方式 |

**代码核查发现**：App 端 `api.py` 已经注册了 32 个 `include_router` 调用，wechat-v1 注册了约 25 个（合并后变少）。两个分支之间的 router 命名差异（`room_router` vs `router`）在融合时不改也不会出错——FastAPI 不关心 router 对象的 Python 变量名，只关心注册时的 `prefix` 和 `tags`。

### 11.3 方案中需要修正或强化的五处

#### 修正 1：`admin_stats.py` 的 bug 性质

方案中说"修复 `admin_stats.py` 的 `Expert` 未导入问题"。经代码确认，修复方式是在第 23 行补充 `Expert` 的 import：

```python
# 当前（第 23 行）：
from app.models.experts import LiveSessionExpert, SessionExpertRole

# 修复后：
from app.models.experts import Expert, LiveSessionExpert, SessionExpertRole
```

这个修复只需一行改动，可以在 PR 1 中顺手完成。

#### 修正 2：分类层级能力已是 App 端现有能力

方案 §3.7 说"选择性融合 `categories.parent_id`"，但实际 App 端已有。应改为：

> **对齐分类删除策略**：两个分支在 `categories.parent_id` 的 `ondelete` 策略上存在差异。App 端使用 `RESTRICT`（安全优先），wechat-v1 使用 `SET NULL`（便利优先）。建议沿用 App 端的 `RESTRICT`，在删除父分类时拒绝操作并提示先迁移子分类——这对于医学分类场景更安全。

#### 修正 3：需要明确单服务 vs 多服务的架构假设

方案的多个决策（注销清理的 `internal_users.py`、品牌电商的 `user_profile_client.py`、会话吊销的 Redis 共享）都依赖于"App 端是否有独立的 `user_service`"。建议在方案开头显式声明当前架构假设：

> **前提**：当前 App 端仓库为单服务架构，认证和直播核心在同一进程中。融合时对 wechat-v1 的"跨服务调用"部分做服务内适配（保留接口形态，但调用方式从 HTTP 改为本地调用或保留 HTTP 以备未来拆分）。

#### 修正 4：P2 留言治理应该拆分为两个子阶段

当前方案 P1 的留言治理目标涵盖了管理端留言、WebSocket、限流、缓存、内容安全接入等多项能力，实际上这些能力的依赖链较长：

```
redis_cache.py → check_message_rate_limit（限流）
              → get_cached_messages / set_cached_messages（缓存）
              → invalidate_message_cache（缓存失效）
content_safety/ → check_scene_fields(scene="message")（内容安全检查）
```

建议将 P1 留言治理拆分为：
- **P1A**（可与 P0 并行）：管理端留言列表、删除、批量删除、清空房间 —— 纯 CRUD，不依赖 Redis 和 content_safety
- **P1B**（依赖 P0 和 content_safety 基础）：WebSocket、限流、缓存、内容安全检查

#### 修正 5：P3 分类增强中 room 主分类的结论需要明确

方案 §3.7 最后一句说"`live_rooms.category_id` 或房间主分类可以评估迁入"。经代码对比：
- wechat-v1 在 `live_rooms` 表有 `category_id` 列
- App 端在 `live_rooms` 表中**没有**这个列

这是一个功能决策：房间是否需要直属一个主分类，还是仅通过 `live_room_categories` 关联表来表达分类关系。wechat-v1 选择了前者（简单直接），App 端选择了后者（多对多灵活）。这不是"迁入"问题，而是产品设计选择——建议由产品需求驱动，而非技术对齐驱动。

### 11.4 补充：融合清单中遗漏的两个 wechat-v1 能力

在交叉比对中发现两个 wechat-v1 有价值但在方案中未提及的能力：

#### 遗漏 1：`user_profile_client.py`（跨服务用户画像查询）

wechat-v1 的 `user_profile_client.py`（64 行）提供了一个批量查询用户资料（昵称、头像）的客户端，被留言展示（`resolve_message_user_display`）、品牌成员列表（`_to_member_items`）等读路径使用。如果 App 端是单服务架构，可以直接查本地表；如果有多服务规划，应该保留这个 client 的接口形态。

建议：在 P1 留言治理中纳入，或者在 P3 品牌电商中纳入（与 `BrandCommerceService` 绑定）。

#### 遗漏 2：wechat-v1 的 `config.py` 新增字段

wechat-v1 在 `config.py` 中新增了约 7 个配置项（`REDIS_URL`、`INTERNAL_SERVICE_TOKEN`、`ADMIN_STREAM_BYPASS`、内容安全相关等），但方案 §8 只列出了其中的 6 个。还需确认是否需要：

- `IMAGE_MODERATION_PROVIDER` — 图片审核提供商（占位/wechat/aliyun/tencent），如果内容安全第二阶段接入图片审核就需要
- `CONTENT_SAFETY_CACHE_TTL` — 规则缓存 TTL（默认 60s），内容安全模块依赖

### 11.5 交叉审查结论

修订后的融合方案在**整体方向和核心决策上准确到位**：
- "以 App 为主干、选择性吸收 wechat-v1"的总策略正确
- 保留权限主干、保留专家科室体系、不删除 `permissions.py` 等关键判断全部成立
- P0→P1→P2→P3 的分阶段路线清晰可行

需要调整的五处已在上文 §11.3 逐一列出，均属细节修正，不影响整体框架。

---

## 附：参考文档

| 文档 | 用途 |
|---|---|
| `add-docs/17-管理端管播MVP-后端设计文档.md` | 管理端房间运营 |
| `add-docs/14-管理端用户管理-V2-账号能力模型与权限修订设计文档.md` | 用户管理、`can_stream`、权限修订 |
| `add-docs/12-全局内容安全与审核-后端设计文档.md` | 内容安全规则与审核 |
| `add-docs/13-医学合规文本违禁词库.md` | 医学违禁词库 |
| `add-docs/07-直播间留言-V4-用户展示读时同步增量设计文档.md` | 留言展示、注销占位 |
| `add-docs/16-D-跨模块落地分包索引.md` | 注销清理和跨模块分包 |
| `app修改记录/权限体系优化设计文档_实施版.md` | App 端权限主干 |
| `app修改记录/直播间管理接口优化设计文档.md` | App 端房间接口优化 |
| `app修改记录/专家分类管理_App端接口优化设计文档.md` | App 端专家分类设计 |
| `app修改记录/管理端后台数据面板_AdminStats设计文档.md` | App 端管理数据面板 |
