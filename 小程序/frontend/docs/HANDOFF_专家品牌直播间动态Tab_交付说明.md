# 专家 / 品牌 / 直播间动态功能性Tab —— 交付说明（给接手AI/开发者）

> 目的：把「专家模块」「品牌模块」「直播间页面里专家/品牌介绍的动态功能性Tab」这一整条业务链路，按“后端设计文档 + 当前仓库实现”完整交付给下一位开发者（或其 AI）。
>
> 适用范围：微信小程序（uni-app + Vue3 + TS + Pinia）。
>
> 关键词：
> - 专家关联：`live_session_experts`（场次-专家多对多）
> - 品牌关联：`brand_rooms`（直播间-品牌多对多）
> - 功能性Tab：房间详情 `tabs`（观众端） + 管理端 `/admin/rooms/{room}/tabs` 回退 + 前端动态注入 `intro` / `expert_intro` / `brand_intro`

---

## 1. 设计文档（必须优先以此为准）

1) 专家模块设计（场次专家关联的来源）
- `docs/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md`

2) 品牌模块设计（品牌-直播间关联 / 房间品牌Tab数据结构）
- `docs/直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md`

> 接手人任何“为什么这样做”的疑问，先回到以上两份文档定位对应章节（尤其是接口与关联表部分）。

---

## 2. 数据模型与关系（用来理解为什么页面这样写）

### 2.1 直播间/场次/专家
- `live_rooms`（直播间）
- `live_sessions`（场次）
- `experts`（专家）
- `live_session_experts`（**场次-专家关联表**，多对多）

结论：
- “某个直播间有没有专家介绍 Tab”不是看 `sessionDetail.featured_expert`（可能为空），而是看 `live_session_experts` 里这个 `session_id` 是否有关联专家。
- 前端正确做法：调用公开接口 `GET /api/v1/experts/sessions/{session_id}/experts` 获取专家列表。

### 2.2 直播间/品牌
- `brands`（品牌）
- `brand_topics`（品牌-专题关联）
- `brand_rooms`（**品牌-直播间关联表**，多对多）

结论：
- “某个直播间有没有品牌介绍 Tab”取决于 `brand_rooms`（room 维度绑定品牌），以及可选增强的 `brand_topics`（topic 维度赞助品牌）。
- 前端正确做法：调用公开接口 `GET /api/v1/rooms/{room_id}/brands`（可选 `include_topic_brands/topic_id`）。

### 2.3 功能性Tab来源
- 观众端：房间详情 `GET /api/v1/rooms/{room_id}` 的 `tabs` 字段（如果后端返回）
- 管理端回退：`GET /api/v1/admin/rooms/{room_id}/tabs`（需要登录/管理员）
- 前端动态注入：`intro` / `expert_intro` / `brand_intro`（仅当有对应内容或关联数据时插入）

---

## 3. 关键文件索引（交付清单）

> 下面这些文件是“专家+品牌+直播间动态Tab”这条链路的最小闭环集合。接手人请从这里入手。

### 3.1 直播间观看页（动态Tab注入核心）
- `src/pages/live/LiveView.vue`

这里负责：
- 解析路由参数（可能只有 `roomId`，需要先找 `sessionId`）
- 拉场次详情（session detail）
- 拉场次专家列表（公开接口）
- 拉直播间品牌列表（公开接口）
- 拉功能性 tabs（房间详情 tabs 或 admin tabs 回退）
- 根据“是否有关联专家/品牌”动态注入 `expert_intro` / `brand_intro`

### 3.2 专家模块
- `src/pages/expert/ExpertList.vue`（专家列表入口）
- `src/pages/expert/ExpertDetail.vue`（专家详情 + 关联场次列表 + 跳转观看）
- `src/api/expert.ts`（专家相关 API；包含场次专家列表接口）
- `src/store/expert.ts`（专家页状态与后端字段映射）

### 3.3 品牌模块
- `src/pages/brand/BrandZone.vue`（品牌入口页；“按品牌名称做tab”，点击tab直达详情）
- `src/pages/brand/BrandDetail.vue`（品牌详情 + 关联专题 + 关联直播间列表 + 跳转观看）
- `src/api/brands.ts`（品牌 API；包含品牌关联直播间 Admin 接口）
- `src/types/brands.ts`（品牌类型契约；含 brand_rooms 的 BrandRoomItem）

### 3.4 通用工具（高频依赖）
- `src/utils/url.ts`
  - `resolveMediaUrl()`：把后端 `/media/...` 相对路径拼成可访问 URL，并对小程序 http/https 做兼容。
- `src/utils/contractCheck.ts`
  - `diffObjectKeys()`：开发期字段契约 diff（**只 warn，不阻断**），用于尽早发现后端字段变更。
- `src/api/room.ts`
  - `getRoomById()`
  - `getRoomBrandsTab()`（直播间品牌Tab公开接口）
- `src/api/tabs.ts`
  - `getTabs()`（admin room tabs）

---

## 4. 直播间页面：动态功能性Tab注入规则（最重要）

### 4.1 路由参数与加载顺序
`LiveView.vue` 支持两种进入方式：
- 方式 A：`/pages/live/LiveView?id=<sessionId>`（直接给场次ID）
- 方式 B：`/pages/live/LiveView?roomId=<roomId>`（只有直播间ID，需要先解析出最新 sessionId）

加载链路（关键顺序）：
1) `loadSessionDetail()`
2) `loadSessionExperts()`  ✅（从 `live_session_experts` 来，决定是否显示“专家介绍”Tab）
3) `loadExpertInfo()`      ✅（拿主专家详情用于展示头像/职称/bio）
4) 并行：`loadStats()` + `loadRoomBrands()`
5) `loadRoomFunctionalTabs()` ✅（注入 intro / expert_intro / brand_intro 发生在这里）

> 注意：如果把 `loadRoomFunctionalTabs()` 放在 `loadSessionExperts()` 之前，会导致专家Tab不稳定出现。

### 4.2 专家 Tab 的判定来源
- 真实来源：`GET /api/v1/experts/sessions/{session_id}/experts`
- 前端变量：
  - `sessionExperts`（列表）
  - `primaryExpert` / `primaryExpertId`（按 sort_order 取最小的作为主专家）
- 注入条件：`primaryExpertId` 存在则注入 `tab_key = expert_intro`

兼容性：
- 后端有时可能返回数组，有时返回分页对象 `{ items: [...] }`（或嵌套 `data.items`）。
- `loadSessionExperts()` 已做兼容解析：数组 / raw.items / raw.data.items。

### 4.3 品牌 Tab 的判定来源
- 真实来源：`GET /api/v1/rooms/{room_id}/brands`
- 可选增强：`include_topic_brands=true` 时必须带 `topic_id`，否则后端 400。
- 前端策略：只有能解析到 `topic_id` 时才传 `include_topic_brands + topic_id`，否则不传该参数。

数据结构：
- 默认：`data` 为数组 `RoomBrandItem[]`
- 增强：`data` 为 `{ room_brands: [...], topic_brands: [...] }`
- 前端 `normalizeRoomBrandsTabData()` 会把两类合并并去重。

### 4.4 功能性 tabs 的来源与回退
`loadRoomFunctionalTabs()` 的有效 tabs 来源：
1) 优先：房间详情 `room.tabs`（观众端字段）
2) 回退：`GET /api/v1/admin/rooms/{room_id}/tabs`（需要登录，且可能返回 `{items,total}`）

前端额外注入的默认功能性 tab：
- `intro`：由 `room.description` / `room.summary` 归一化后生成
- `expert_intro`：由 `GET /api/v1/experts/sessions/{session_id}/experts` 是否存在数据决定
- `brand_intro`：由 `GET /api/v1/rooms/{room_id}/brands` 是否存在数据决定

已做的兼容点：
- admin tabs 返回 `{ items: [] }`（空数组）是合法情况，不应报“not an array”错误。
- admin tabs 返回结构不是数组时，会尝试从多种字段抽取（items/tabs/data/list/results/records/rows），并支持深层嵌套。

---

## 5. 专家页面：如何“选择专家 → 看关联直播 → 跳转观看”

### 5.1 专家列表页
文件：`src/pages/expert/ExpertList.vue`
- 点击卡片跳转：`/pages/expert/ExpertDetail?id=<expertId>`

### 5.2 专家详情页
文件：`src/pages/expert/ExpertDetail.vue`
- 数据加载：
  - `expertStore.fetchExpertById(id)` 拉专家详情
  - `expertStore.fetchExpertSessions(id)` 拉专家关联场次列表
- 展示分组：
  - 正在直播（status=live）
  - 即将开始（status=scheduled）
  - 历史直播（status=ended）
- 跳转观看：点击任一场次 → `/pages/live/LiveView?id=<sessionId>`

### 5.3 专家相关 API
文件：`src/api/expert.ts`
- `getExpertDetail(expertId)`：`GET /api/v1/experts/{expertId}`（公开）
- `getExpertSessions(expertId, params)`：`GET /api/v1/experts/{expertId}/sessions`（公开，分页）
- `getSessionExperts(sessionId)`：`GET /api/v1/experts/sessions/{sessionId}/experts`（公开）

> 提醒：直播间页的“专家介绍 Tab”判定**只看** `getSessionExperts` 的返回是否为空，不要再回退到老的 mock 或 sessionDetail 内字段。

---

## 6. 品牌页面：如何“按品牌名tab → 进详情 → 看介绍/专题/关联直播间 → 跳转观看”

### 6.1 品牌入口页（按品牌名称做tab）
文件：`src/pages/brand/BrandZone.vue`
- tabs = `['全部', ...所有品牌 name]`（去重，并按 sort_order + 名称排序）
- 行为：
  - 点击“全部”：保留网格浏览
  - 点击某个品牌名称 tab：直接跳 `BrandDetail`（通过 `name -> id` 映射）

> 如果后端将来允许重名品牌，`name -> id` 会有歧义；当前策略是“取 sort_order 更小的 id”。

### 6.2 品牌详情页
文件：`src/pages/brand/BrandDetail.vue`
- 主数据：`getBrandContent(brandId)` → `brand_info + associated_topics`
- 品牌介绍卡（不编造，只基于现有字段）
  - 入驻时间：`created_at`
  - 入驻时长：由 `created_at` 计算天数
  - 关联专题数：`associated_topics.length`
  - 关联直播间数：`brandRooms.length`（如果无权限会为 0）
- 关联直播间列表（可跳转观看）：
  - 调用 `getAdminBrandRooms(brandId)`（**管理员接口**）
  - 点击直播间 → `/pages/live/LiveView?roomId=<roomId>`

### 6.3 品牌相关 API
文件：`src/api/brands.ts`
- `getBrandList()`：`GET /api/v1/brands`（公开）
- `getBrandContent(brandId)`：`GET /api/v1/brands/{brandId}/content`（公开）
- `getAdminBrandRooms(brandId)`：`GET /api/v1/admin/brands/{brandId}/rooms`（Admin分页）

> 重要限制：品牌“关联直播间列表”目前走 admin 接口。
> - 若产品要求普通用户也能看到品牌关联直播间，需要后端提供公开端点（或 Optional Auth 的公开端点）。
> - 当前前端已做降级：401/403 不报错、不阻断，只提示“登录后可查看更多关联直播间”。

---

## 7. 常见联调问题与快速定位

### 7.1 为什么有些直播间有专家介绍，有些没有？
判定依据：`loadSessionExperts` 的 `count`。
- `count > 0`：后端已建立 `live_session_experts` 关联 → 应出现“专家介绍”tab。
- `count = 0`：该场次没有关联专家 → **按需求不显示**（不是前端 bug）。

### 7.2 为什么品牌接口会 400？
当请求 `include_topic_brands=true` 时后端要求必须传 `topic_id`。
- 前端策略：只在 `resolveTopicId()` 能拿到 topic_id 的情况下才传该增强参数。

### 7.3 为什么 scheduled 场次 /play-url 会 404？
设计上 scheduled 状态可能没有播放地址。
- 前端已做：非 `live/ended` 状态跳过 `/play-url` 兜底请求，避免噪音。

### 7.4 /media 资源 500 或图片不显示
- 后端返回 `/media/...`：前端必须用 `resolveMediaUrl()` 拼接 origin。
- 资源 500 属后端资源问题，前端只能降级（占位图/错误提示）。

---

## 8. 二次开发指南（接手人最可能会改哪里）

### 8.1 新增一个“动态Tab类型”怎么做？
以 LiveView 为例：
1) 定义一个新的 `TAB_KEY` 常量
2) 在 `loadRoomFunctionalTabs()` 里追加注入逻辑（基于“某个关联数据是否存在”）
3) 在模板渲染区增加 `v-else-if="currentTabKey === NEW_TAB_KEY"` 的内容渲染
4) 补齐样式与跳转

### 8.2 后端字段变更怎么快速发现？
- 品牌详情页已接入 `diffObjectKeys()`：只要后端返回字段与白名单不一致，会打印 warn 日志。
- 建议新增/修改接口时，也复制同样的“契约 diff（warn-only）”机制，避免上线后页面空白。

### 8.3 如果要让“品牌详情页”对普通用户展示关联直播间
需要后端提供公开接口（示例仅说明方向）：
- `GET /api/v1/brands/{brand_id}/rooms`（Optional Auth 或 public）
- 返回结构建议对齐 admin 的分页结构

前端改动点：
- `src/api/brands.ts` 新增 public API
- `BrandDetail.vue` 优先用 public；失败再回退 admin（或干脆只用 public）

---

## 9. 最小验收清单（交付给接手人/AI的自测用例）

1) 直播间页（给 roomId 进入）
- 进入一个 scheduled 房间：能通过 roomId 找到最新 sessionId
- 日志出现 `✅ [loadSessionExperts] loaded`
- 若 count>0：出现“专家介绍”tab
- 若品牌 count>0：出现“品牌介绍”tab

2) 专家页
- 专家列表点进详情
- 能看到 live/scheduled/ended 分组
- 点任意场次跳转 LiveView（以 sessionId 进入）

3) 品牌页
- BrandZone 顶部品牌名 tab 点击直接进 BrandDetail
- BrandDetail 展示：品牌介绍卡 + 关联专题
- 若使用 admin 账号：能看到关联直播间列表；点击跳转 LiveView（以 roomId 进入）

---

## 10. 交付备注（环境/工具）

- Mock 当前关闭：启动日志会显示 `VITE_USE_MOCK: false`。
- `npm run lint` 目前可能因 eslint config 依赖缺失而失败（属于环境依赖问题，不作为本链路验收阻断）。
- 推荐验收方式：以真机/开发者工具日志为准，重点看 `loadSessionExperts/loadRoomBrands/loadRoomFunctionalTabs` 相关日志。

---

## 11. 接手人快速入口（建议阅读顺序）

1) `src/pages/live/LiveView.vue`（理解动态tab注入规则与加载顺序）
2) `src/api/expert.ts`（确认专家关联接口）
3) `src/api/room.ts`（确认 brands tab 接口）
4) `src/pages/expert/ExpertDetail.vue`（确认专家→直播跳转）
5) `src/pages/brand/BrandDetail.vue`（确认品牌→直播跳转与权限降级）
6) 两份设计文档（遇到争议/疑问时回查）

---

> 文档维护建议：后续每次新增/调整接口或页面规则，请在本文件末尾追加一条“变更记录”，以便持续交付。
