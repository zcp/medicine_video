# App 前端接入后端管理功能实施设计文档

**版本**: 1.2  
**创建日期**: 2026-07-30  
**更新日期**: 2026-07-30  
**覆盖范围**: 后端融合 V4.2 → App 端（`src/pages/app/`）  
**状态**: 第一批修复已完成 · 阶段 1 路由配置已完成

---

## 一、后端当前状态简述

后端融合（`wechat-v1` → `main`）已完成 **54/58 项模块决策**，4 项条件触发（品牌电商暂不实施）。

**已上线且较稳定的管理接口**：

| 模块 | 端点 | 状态 |
|------|------|:----:|
| 用户管理 | `GET/PATCH /api/v1/admin/users` | ✅ 已上线，含 `can_stream`/`role`/`status` 修改 + session revocation |
| 管理端房间 | `GET /api/v1/admin/rooms` | ✅ 已上线，含 `q`/`owner_user_id`/`is_private` 参数 |
| 管理统计 | `GET /api/v1/admin/stats/daily`、`/admin/sessions/today` | ✅ 已上线 |
| 留言管理 | `GET /admin/messages`、`POST batch-delete`、`DELETE room` | ✅ 已上线，含限流和缓存 |
| 内容安全 | 规则 CRUD + 日志查询 | ⚠️ 基础能力已验证（block/allow），但 schema 和 DDL 存在字段不一致 |
| 专家/科室 | `/admin/experts`、`/admin/expert-departments` | ✅ 已上线 |
| 通知管理 | `/admin/notifications` | ✅ 已上线 |
| 精选内容 | `/admin/featured-content` | ✅ 已上线 |
| 专家自认领 | `GET/PATCH /experts/me` | ✅ 已上线 |
| 品牌电商 | `/admin/brands/*` | ⏸ 条件触发，暂不实施 |

**后端仍需修复的问题**（影响前端接入决策）：

| 问题 | 影响模块 | 说明 |
|------|---------|------|
| content_safety schema/model 字段不一致 | 内容安全 | `schemas.py` 定义了 `enabled`/`binding_level`/`rule_category`/`regulation_ref`/`remark`，但 `models.py` 无对应列。CRUD 用 `getattr` 兜底 |
| content_safety DDL 不完整 | 内容安全 | `V4.2_content_safety_fields.sql` 只补了部分日志列，全量列依赖手工 ALTER |
| can_stream migration 重复 | 用户管理 | live_core 和 users 下各有一份，应只保留 users 服务 |
| env/compose 配置未验证 | 全部 | `INTERNAL_SERVICE_TOKEN`、`USER_SERVICE_URL`、`LIVE_CORE_SERVICE_URL`、共享 `REDIS_URL` 需确认已置入部署配置 |
| 缺少回归测试 | 全部 | admin rooms q、用户吊销、留言限流、内容安全、缓存失效等无自动化覆盖 |

---

## 二、前端当前状态

### 2.1 已对接的管理页面（4 个）

| 页面 | 路径 | API 覆盖 | 状态 |
|------|------|---------|:----:|
| 科室管理 | `pages/app/admin/departments/index` | `department.ts`（9 函数） | ✅ 完整 |
| 专家管理 | `pages/app/admin/expert-list/index` | `expert.ts`（15 函数） | ✅ 完整 |
| 轮播图管理 | `pages/app/admin/featured/index` | `featured.ts`（6 函数） | ✅ 完整 |
| 通知推送 | `pages/app/admin/notification-push/index` | `notification.ts`（8 函数） | ✅ 已修复路径 + 指定用户逻辑 |

### 2.2 已有 API 封装但无独立管理页的模块

| 模块 | API 文件 | 是否完整 | 说明 |
|------|---------|:-------:|------|
| 品牌管理 | `brand.ts`（9 函数） | ✅ | 导航入口存在，页面在 `tabbar/brand` |
| 分类管理 | `category.ts`（7 函数） | ✅ | 由科室页面调用 |
| 标签管理 | `tag.ts`（8 函数） | ✅ | 无独立页面需求 |
| 专题管理 | `topic.ts`（15 函数） | ✅ | H5 端有页面 |
| Tab 管理 | `tab.ts`（4 函数） | ✅ | 由房间管理页面调用 |
| 房间-分类关联 | `roomCategories.ts`（3 函数） | ✅ | 由房间编辑页面调用 |

### 2.3 完全缺失的管理能力

| 模块 | API 文件 | 管理页面 | `pages.json` 注册 | 导航入口 |
|------|:-------:|:-------:|:----------------:|:-------:|
| 用户管理 | ❌ | ❌ | ❌ | ❌ |
| 全站房间管理 | ✅ `getAdminRooms` 已新增 | ❌ | ❌ | ❌ |
| 管理留言 | ❌ | ❌ | ❌ | ❌ |
| 内容安全 | ❌ | ❌ | ❌ | ❌ |
| 管理首页 Dashboard | ❌ | 空目录 | ❌ | ❌ |
| 专家自认领 | ❌ | ❌ | ❌ | ❌ |

### 2.4 已有代码但需要修复的问题

| 问题 | 文件 | 状态 | 严重程度 |
|------|------|:----:|:-------:|
| 通知 API 路径含 `/api/v1` 双前缀 | `src/api/notification.ts` | ✅ **第一批已修复** | 🔴 之前是 404 |
| `User` 接口缺 `can_stream` | `src/store/auth.ts` | ✅ **第一批已修复** | 🟡 后端已检查此字段 |
| `UserInfo` 接口缺 `can_stream` | `src/types/auth.ts` | ✅ **第一批已修复** | 🟡 同上 |
| `Room` 接口缺 `owner_user_id` | `src/types/room.ts` | ✅ **第一批已修复** | 🟡 无法接收 admin room 响应 |
| 创建房间 catch 未识别 403 | `src/pages/app/live-manage/create.vue` | ✅ **第一批已修复** | 🟡 toast 信息不准确 |
| 通知页"指定用户"是空壳 | `src/pages/app/admin/notification-push/index.vue` | ✅ **第一批已修复** | 🟡 选了也无效 |
| 管理导航只有 4 个入口 | `src/pages/app/tabbar/my/index.vue` | ❌ 待第二批补齐 | 🟡 新增页面后需同步补 |
| `pages.json` 只注册了 4 个 admin 页 | `src/pages.json` | ❌ 待第二批补齐 | 🟡 新增页面需同步注册 |
| `cover_url` 手动拼接未用 `resolveMediaUrl` | `src/store/room.ts` + `live-manage/list.vue` | 🟢 技术债 | 🟢 代码重复，非阻塞 |

---

## 三、实施策略

### 3.1 批次划分原则

按 **后端接口稳定度 × 前端依赖复杂度** 分为三批：

| 批次 | 性质 | 依赖 | 可并行 |
|:----:|------|------|:-----:|
| **第一批** | 纯前端修复，不依赖后端 | 无 | ✅ |
| **第二批** | 后端接口稳定，前端新建功能 | 后端接口已上线 | ✅ |
| **第三批** | 等后端修复后再做 | 后端内容安全/品牌电商修复完成 | ⏸ |

### 3.2 详细实施计划

---

#### 第一批：纯前端修复（约 1.5h，不依赖后端）

**目标**：修复已有功能的可见性阻塞，铺平后续开发路径。

**工作项 1.1 — 通知 API 路径修复**

| 文件 | `src/api/notification.ts` |
|------|--------------------------|
| 当前状态 | 8 个函数路径全部以 `/api/v1/` 开头。`request.ts` 拼接 `BASE_URL` 后产生双路径，导致 404 |
| 改动 | 8 处 `/api/v1/users/me/notifications/...` → `/users/me/notifications/...`，`/api/v1/admin/notifications` → `/admin/notifications` |
| 涉及行 | 26, 36, 47, 56, 67, 78, 87, 96 |
| 风险 | 无。`BASE_URL` 已含 `/api/v1`，去重后路径与后端一致 |

**工作项 1.2 — `can_stream` 类型补充**

| 文件 | 改动 | 行 |
|------|------|:--:|
| `src/store/auth.ts` | `User` 接口加 `can_stream?: boolean` | 75 |
| `src/types/auth.ts` | `UserInfo` 接口加 `can_stream?: boolean` | 96 |
| `src/store/auth.ts` | `parseUserFromToken()` 中从 JWT payload 解析 `can_stream` | 35-47 |

**工作项 1.3 — `Room` 类型补 `owner_user_id`**

| 文件 | 改动 | 行 |
|------|------|:--:|
| `src/types/room.ts` | `Room` 接口加 `owner_user_id?: string` | 25 |

**工作项 1.4 — 新建 `getAdminRooms` API**

| 文件 | 改动 |
|------|------|
| `src/api/room.ts` | 新增 `getAdminRooms(params)` → `GET /admin/rooms`，支持 `page`/`size`/`q`/`owner_user_id`/`is_private` 参数 |

**工作项 1.5 — 创建房间补 403 提示**

| 文件 | 行 | 当前行为 | 改后行为 |
|------|:--:|---------|---------|
| `src/pages/app/live-manage/create.vue` | 1302-1308 | 展示 `error.message`（即 "Forbidden"） | 识别 `roomResult.message` 中包含"开播资格"关键字时展示"您暂无开播权限，请联系管理员" |

**工作项 1.6 — 通知页"指定用户"逻辑修复**

| 文件 | 行 | 当前行为 | 改后行为 |
|------|:--:|---------|---------|
| `src/pages/app/admin/notification-push/index.vue` | 156-166 | for 循环体为空，最终调 `createNotification` 不传 `user_ids` | 调 `batchCreateNotifications({ user_ids: ids, ...form })`；若无 `batchCreateNotifications` 支撑则隐藏"指定用户"UI |

---

#### 第二批：对接后端稳定接口（约 5-6h，后端接口已就绪）

**目标**：补全缺失的核心管理功能。

**工作项 2.1 — 用户管理**

| 维度 | 内容 |
|------|------|
| 新建 API 文件 | `src/api/adminUsers.ts` |
| 接口 | `getAdminUsers(params)` → `GET /admin/users`，`updateAdminUser(uuid, data)` → `PATCH /admin/users/{uuid}` |
| 参数 | `page`/`size`/`username`/`email`/`role`/`status`/`can_stream` |
| 新建类型 | `src/types/adminUser.ts` — `AdminUser`（`public_id`, `username`, `nickname`, `email`, `role`, `status`, `can_stream`, `avatar_url`, `created_at`, `last_login_at`） |
| 新建页面 | `src/pages/app/admin/users/index.vue` — 列表+搜索+分页+状态筛选+角色筛选，单行操作（封禁/解封、修改角色、切换 `can_stream`） |
| 注册路由 | `src/pages.json` 补 `pages/app/admin/users/index` |
| 导航入口 | `src/pages/app/tabbar/my/index.vue:850-856` `adminRoutes` 补 `users: "/pages/app/admin/users/index"` |
| 权限守卫 | 菜单项用 `v-if="authStore.isAdmin"`（已有此模式） |
| 风险 | 低。后端接口已稳定，前端页面逻辑与现有的专家/科室管理页模式相同 |

**工作项 2.2 — 管理端留言 API**

| 维度 | 内容 |
|------|------|
| 扩展文件 | `src/api/message.ts` |
| 新增函数 | `getAdminMessages(params)` → `GET /admin/messages`（支持 `room_id`/`user_id`/`keyword`/`start_time`/`end_time`/`page`/`page_size`） |
| | `batchDeleteAdminMessages(messageIds)` → `POST /admin/messages/batch-delete` |
| | `clearRoomMessages(roomId)` → `DELETE /admin/rooms/{roomId}/messages` |
| 类型补充 | `src/types/message.ts` — 补 `AdminMessageItem`（含 `user_name`/`user_avatar`），`AdminMessageQueryParams` |
| 风险 | 低。CRUD 操作，无状态变更 |

**工作项 2.3 — 管理首页 Dashboard**

| 维度 | 内容 |
|------|------|
| 新建页面 | `src/pages/app/admin/dashboard/index.vue`（当前目录存在但为空） |
| 数据源 | 已有的 `getAdminDailyStats()`（`src/api/admin.ts:19`）、`getAdminSessionsToday()`（`:23`） |
| 展示内容 | 今日场次数、当前直播数、今日场次列表（房间标题/状态/时间/专家名） |
| 注册路由 | `src/pages.json` 补 `pages/app/admin/dashboard/index` |
| 导航入口 | `src/pages/app/tabbar/my/index.vue` 管理功能区加"管理首页"入口 |
| 风险 | 低。数据源已在前端管理摘要卡片中使用 |

**工作项 2.4 — 专家自认领 API**

| 维度 | 内容 |
|------|------|
| 扩展文件 | `src/api/expert.ts` |
| 新增函数 | `getMyExpertProfile()` → `GET /experts/me`，`updateMyExpertProfile(data)` → `PATCH /experts/me`（支持 `name`/`title`/`hospital`/`department_name`/`expertise_areas`/`bio`） |
| 风险 | 低。只读+自更新，不涉及管理权限 |

**工作项 2.5 — `pages.json` 补充 + 导航入口统一**

| 改动 | 说明 |
|------|------|
| `src/pages.json:341-363` | 新增 dashboard、users、messages 等 admin 页面路由 |
| `src/pages/app/tabbar/my/index.vue:850-856` | `adminRoutes` 补充所有新增页面的映射 |

---

#### 第三批：等后端修复后再做（暂缓）

| 工作项 | 依赖的后端修复 | 前端可做的准备 |
|--------|--------------|--------------|
| 内容安全规则/日志管理页 | content_safety schema/model/DDL 对齐 | 可先建 `src/api/contentSafety.ts` 骨架文件，等字段确认后再补实际字段类型 |
| 内容安全拦截错误展示 | 同上一一且需联调确认错误码格式 | 可先确定前端展示规则（block→红色提示+原因，warn→黄色提示） |
| 品牌电商 | PR6 条件触发 | 隐藏当前品牌管理入口 |
| 注销读路径占位 | migration 清理 + `deactivated_users` 标记稳定 | 可在留言/专家列表组件中添加"账号已注销"条件渲染逻辑，具体数据字段等联调确认 |
| WebSocket 管理 | nginx 配置 + 上线前 | 标记为上线前任务 |

---

## 四、前后端接口对照总表

以下表格列出了所有管理相关端点的前端对接状态，按"无需改动/需修复/需新建/暂缓"分类。

### 4.1 无需改动（已对接）

| 后端端点 | 前端 API | 前端管理页 |
|---------|---------|-----------|
| `GET/POST /admin/expert-departments` | `department.ts` | `departments/index` |
| `PATCH/DELETE /admin/expert-departments/{id}` | `department.ts` | `departments/index` |
| `GET /admin/expert-departments/unmapped` | `department.ts` | `departments/index` |
| `POST /admin/expert-departments/merge` | `department.ts` | `departments/index` |
| `POST /admin/expert-departments/batch-verify` | `department.ts` | `departments/index` |
| `GET/POST /admin/experts` | `expert.ts` | `expert-list/index` |
| `PATCH/DELETE /admin/experts/{id}` | `expert.ts` | `expert-list/index` |
| `POST /admin/experts/batch-import` | `expert.ts` | `expert-list/index` |
| `GET/POST /admin/featured-content` | `featured.ts` | `featured/index` |
| `PATCH/DELETE /admin/featured-content/{id}` | `featured.ts` | `featured/index` |
| `GET/POST /admin/categories` | `category.ts` | 由科室页调用 |
| `PUT/DELETE /admin/categories/{id}` | `category.ts` | 由科室页调用 |
| `GET /admin/stats/daily` | `admin.ts` | 管理摘要卡片 |
| `GET /admin/sessions/today` | `admin.ts` | 管理摘要卡片 |
| `GET/POST /admin/brands` | `brand.ts` | `tabbar/brand` |
| `GET/POST /admin/rooms/{id}/categories` | `roomCategories.ts` | 由房间编辑调用 |
| `GET/POST /admin/rooms/{id}/tabs` | `tab.ts` | 由房间管理调用 |
| `PATCH/DELETE /admin/tabs/{id}` | `tab.ts` | 由房间管理调用 |
| `POST /admin/brands/{id}/topics` | `brandTopics.ts` | 由品牌页调用 |

### 4.2 已修复（第一批完成）

| 后端端点 | 前端文件 | 修复内容 |
|---------|---------|---------|
| `/admin/notifications`、`/users/me/notifications` 系列 | `notification.ts` | 8 处路径去掉 `/api/v1` 前缀 ✅ |
| 无（纯前端） | `store/auth.ts` | `User` 接口 + `parseUserFromToken` + `fetchUserProfile` 补 `can_stream` ✅ |
| 无（纯前端） | `types/auth.ts` | `UserInfo` 接口补 `can_stream` ✅ |
| 无（纯前端） | `live-manage/create.vue` | catch 识别 403 Forbidden 后展示"暂无开播权限" ✅ |
| 无（纯前端） | `notification-push/index.vue` | 指定用户模式调 `batchCreateNotifications` + 补 import ✅ |
| 无（纯前端） | `types/room.ts` | 补 `owner_user_id` 可选字段 ✅ |
| 无（纯前端） | `api/room.ts` | 新增 `getAdminRooms` 函数 ✅ |

### 4.3 需新建（后端已就绪）

| 后端端点 | 建议 API 文件 | 建议新页面 | 工作项编号 |
|---------|--------------|-----------|:--------:|
| `GET/PATCH /admin/users` | `adminUsers.ts` | `admin/users/index` | 2.1 |
| `GET /admin/rooms` | `room.ts`（扩展） | 嵌入 `live-manage/list` | 1.4 |
| `GET /admin/messages` | `message.ts`（扩展） | 可选 | 2.2 |
| `POST /admin/messages/batch-delete` | `message.ts`（扩展） | — | 2.2 |
| `DELETE /admin/rooms/{id}/messages` | `message.ts`（扩展） | — | 2.2 |
| `GET /admin/stats/daily` | `admin.ts`（已有） | `admin/dashboard/index` | 2.3 |
| `GET/PATCH /experts/me` | `expert.ts`（扩展） | 可选 | 2.4 |

### 4.4 暂缓（等后端修复）

| 后端端点 | 原因 | 预计前端工作 |
|---------|------|------------|
| `GET/POST /admin/content-safety/rules` | schema/DEL 未对齐 | 规则管理页 + 类型定义 |
| `PATCH /admin/content-safety/rules/{id}` | 同上 | — |
| `GET /admin/content-safety/logs` | DDL 缺少日志列 | 审计日志查询页 |
| `/admin/brand-members`、`/admin/brand-products` | PR6 条件触发 | 品牌工作台 + 商品管理页 |

---

## 五、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|---------|
| content_safety 字段变更导致前端联调返工 | 高 | 内容安全页面需重做 | 第三批执行，等后端 schema/model/DDL 完全对齐后再做 |
| `can_stream` JWT claim 命名变更 | 低 | store 解析字段名需改 | 首批即加上，联调时验证 payload 字段名 |
| 共享 Redis 未连通导致 session revocation 不生效 | 中 | 用户管理"封禁后立即失效"不工作 | 前端不受影响（后端返回 401 即可），但需后端确认 Redis 配置 |
| `INTERNAL_SERVICE_TOKEN` 未配置导致跨服务清理失败 | 中 | 用户注销清理不完整 | 前端展示不变，后端 best-effort 降级，影响范围在日志层面 |
| 新页面权限暴露给非管理员 | 低 | 普通用户看到管理入口 | `v-if="authStore.isAdmin"` 统一守卫，路由级权限由后端保障 |
| 通知 API 路径修复后 part 兼容性问题 | 低 | 其他用到 notification API 的地方路径也跟着变 | `request.ts` 的 URL 拼接对所有 API 一致，改路径后全部统一 |

---

## 六、实施顺序建议

```text
Week 1 (Day 1) — 第一批：修复 + 准备 ✅ 已完成
├── 1.1 notification.ts 路径修复（10min）✅
├── 1.2 can_stream 类型 + 解析（30min）✅
├── 1.3 Room 补 owner_user_id（5min）✅
├── 1.4 getAdminRooms API（15min）✅
├── 1.5 create.vue 403 提示（15min）✅
├── 1.6 通知页"指定用户"（30min）✅
└── 2.5 pages.json + 导航入口统一（⏸ 随第二批做）

Week 1 (Day 2-3) — 第二批：用户管理 + Dashboard
├── 2.1 用户管理全量（3h）
├── 2.3 Dashboard 页面（1.5h）
└── 2.5 导航入口更新（随 2.1 做）

Week 2 (Day 1-2) — 第二批：留言管理 + 专家自认领
├── 2.2 留言管理 API（30min）
├── 2.4 专家自认领 API（20min）
└── 集成联调验证

Week 2+（等后端通知）— 第三批
├── 内容安全（待后端 schema 确认）
├── 品牌电商（待 PR6 决定）
├── 注销占位（待 migration 清理）
└── WebSocket（待 nginx 配置）
```

第一批与第二批**无先后依赖**，可拆给两人并行：一人做 1.1-1.6（纯修复），另一人做 2.1+2.3（用户管理 + Dashboard）。

---

## 七、验收标准

### 第一批验收 ✅ 已完成

- [x] `GET /users/me/notifications` 返回 200（通知列表恢复）
- [x] `POST /admin/notifications` 返回 200（通知推送恢复）
- [x] `authStore.user.can_stream` 存在且值与后端 JWT 一致
- [x] `createRoom` 返回 403 时展示"暂无开播权限"提示
- [x] `getAdminRooms()` 返回房间列表含 `owner_user_id`
- [x] 通知页"指定用户"可正常发送定向通知

### 第二批验收

- [ ] `GET /admin/users` 返回分页用户列表
- [ ] `PATCH /admin/users/{uuid}` 可修改 `can_stream`/`role`/`status`
- [ ] 用户管理页可完成"搜索→选中→封禁"全流程
- [ ] Dashboard 展示今日场次数和当前直播数
- [ ] `GET /admin/messages` 返回分页留言列表
- [ ] `POST /admin/messages/batch-delete` 删除成功
- [ ] `DELETE /admin/rooms/{id}/messages` 清空成功
- [ ] `GET /experts/me` 返回当前用户绑定的专家资料
- [ ] `PATCH /experts/me` 可更新专家资料
- [ ] 所有新增页面的路由在 `pages.json` 注册且导航入口可用
