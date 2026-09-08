# 前端读一致性缺口分拣（问题清单）

**项目**: Live-Saas-Wechat  
**版本**: 1.1  
**日期**: 2026-07-30  
**状态**: 第 1 批真问题已落地代码（G2/G1/F4/F7/F8/N1/N2）；第 2/3 批仍待确认  
**当前状态（problem 总表）**: 部分修复（第 1 批已修；其余待确认/可接受）  
**依据**: 《18-前端页面消费与读一致性清单》V1.2（§0.1 G*、§7 F*）；`src/pages.json` + 抽样源码  
**关联**: `docs/18-前端页面消费与读一致性清单.md`；`docs/problem/README.md`

---

## 一、说明

### 1.1 文档功能

把《18》已晾出的 **G1–G5 / F1–F8** 收成可排期的问题清单：先判定「是不是问题」，再给修法方向与批次；并记录本轮补查的 **N\*** 新发现。

### 1.2 适用范围

- 前端页面展示与读一致性、写后同步、入口死链、Store 残留  
- **不**重开《16》生命周期决策；规则冲突仍以《16》为准  
- **不**替代各模块前端详设 / OpenAPI 逐键 diff

### 1.3 三类判定口径

| 类型 | 含义 | 动作 |
|------|------|------|
| **真问题** | 用户可踩坑，或同实体多页口径明显错 | 排期修 |
| **待确认** | 依赖后端字段/公开 API，或产品取舍 | 先对齐再动 |
| **可接受** | 成本高收益低；文档已定为非阻断 | 暂不修 |

### 1.4 声明

- 本清单是《18》的**执行侧分拣**，不把 F*/N* 升格为《16》新规则  
- 与 `docs/problem` 历史缺陷（封面、watch API、专家绑定等）并行；重复项只交叉引用，不另开母缺陷

---

## 二、总览看板

| 批次 | 包含 | 建议 |
|------|------|------|
| **第 1 批**（前端可独立、风险低） | G2、G1、F4、F7、F8、**N1**、**N2** | 优先开工 |
| **第 2 批**（读一致性 / 可能动 API 参数） | F1、F5 | 先确认契约再改 |
| **第 3 批**（依赖后端/产品） | F3、F2、F6、G4、G3 | 联调/产品拍板后修 |
| **暂缓** | G5 | 明确可接受 |

```text
建议顺序：G2 → G1 → F4 → F7 → F8 → N1/N2 →（确认后）F1/F5 →（联调后）F3/F2/F6/G4/G3
不要一上来改 G5；封面兜底 / normalize 不视为本清单缺陷。
```

---

## 三、真问题（要修）

| ID | 现象 | 证据（路径 / 符号） | 为何算问题 | 修法方向 | 状态 |
|----|------|---------------------|------------|----------|------|
| **G2** | 登出/注销 `clearAuth` 只清认证，不清收藏/历史/订阅等行为 Store | `src/store/auth.ts` `clearAuth` | 换号可能短暂露旧私货 | logout/deactivate 统一 reset 行为 Store | **已修复**（`resetUserBehaviorStores`） |
| **G1** | `RoomDetail` 占位；通知关联房仍跳该页 | `pages/room/RoomDetail.vue`；`NotificationDetail.vue` `related` → `RoomDetail` | 用户进「开发中」死页 | 进房入口改 `LiveView`；或占位页 redirect | **已修复**（占位 redirect + 通知改 LiveView） |
| **F4** | 专家场次映射写死 `roomId: undefined` → 收藏钮不显示 | `src/store/expert.ts` `fetchExpertSessions`；类型 `ExpertSessionBriefItem` 亦无 `room_id` | 功能残缺 | 类型+映射补 `room_id`（若响应有）；无则与后端补字段 | **已修复**（映射多别名；若后端仍无字段则钮仍隐） |
| **F7** | SearchByTag 跳未注册路由 | `SearchByTag.vue` → `/pages/user/session/detail` | 点结果失败 | 改跳 `LiveView`（带 session/room） | **已修复** |
| **F8** | 搜索品牌 Tab 未滤 `is_active`，BrandZone 会滤 | `subpackages/search/index` vs `BrandZone` | 同实体两口径 | 搜索侧与 Zone 同滤 | **已修复** |
| **F1** | 首页状态 Tab 对已拉列表客户端再筛 | `Home.vue` `statusFilter` + `displayRooms`；`getHomepageRooms` **无 status 入参** | 分页与 Tab 脱节 | 后端支持按状态筛则传参；否则改交互/文案 | 待确认契约后改（见 §五） |
| **N1** | `FollowedExperts` 无 `onShow`，仅 `onLoad`+下拉 | `FollowedExperts.vue` 仅 `onLoad`/`onPullDownRefresh` | 他页关注变更回本页可能旧 | 补 `onShow` refresh（可节流） | **已修复** |
| **N2** | `Notifications` 无 `onShow` 刷新 | `Notifications.vue` 仅 `onLoad` | 未读/新通知可能旧 | 补 `onShow` 或接入 Store 统一刷 | **已修复** |

> **F1** 在总览进第 2 批：前端封装当前不支持状态参数，贸然「传参」不够，需先确认 homepage API。

---

## 四、待确认（先别当单纯前端 bug）

| ID | 现象 | 要先确认什么 | 确认后动作 | 状态 |
|----|------|--------------|------------|------|
| **F2** | BrandDetail 关联房走 `getAdminBrandRooms` | 是否有**公开**关联房契约？problem 总表曾记「Admin 链路已止血」 | 有公开 API→换读；无→网关/权限写清或后端补公开接口 | 待确认 |
| **F3** | 专家列表/详情 stats 硬编码 0 | 后端是否返回粉丝/场次/观看 | 有→映射；无→隐藏统计区 | 待确认 |
| **F5** | 观看历史 Tab 客户端二次过滤 | 后端是否已按 session 类型分页过滤 | 对齐参数或保留本地 Tab 并标明 | 待确认 |
| **F6** | OneTapLogin `mockToken` 硬编码 | 现网是否已接运营商 SDK | 接真 SDK / 去 mock | 待确认（阶段性） |
| **G4** | 专家/搜索软删主要信后端 | 后端是否保证不回软删实体 | 保证→可只信后端；不保证→与科室/品牌统一客户端滤 | 待确认 |
| **G3** | 注销成功无「旧房仍可能公开」说明 | 产品要不要 D1 说明文案 | 要→文案/FAQ；不要→关闭本条 | 待确认（非逻辑阻断） |
| **F1**（契约侧） | homepage 客户端类型无 live 状态筛选项 | Core `homepage/rooms` 是否支持 status/live_status 过滤 | 支持→改请求；不支持→产品接受「当前批筛选」或后端加参 | 待确认 |

---

## 五、可接受（明确暂不修）

| ID | 现象 | 为何可接受 | 状态 |
|----|------|------------|------|
| **G5** | Admin 删房/软删后，已打开 C 端不即时失效 | 《18》定为依赖下次 `onShow`/下拉；不做跨端推送 | 可接受 |

**本清单不当作缺陷的常见模式**（避免误修）：

- 媒体 URL `resolveCoverUrl` / 默认封面头像兜底  
- 收藏/订阅列表字段不全时 `getRoomById` 补拉  
- 留言 `normalizeRoomMessage*` 消费 D3 占位（属正确守约）

---

## 六、本轮补查：新发现与「未再扩大」范围

### 6.1 新发现（N*）

| ID | 严重度 | 简述 | 证据 |
|----|--------|------|------|
| **N1** | 真问题 | 关注列表缺 `onShow` 刷新 | `FollowedExperts.vue` |
| **N2** | 真问题 | 通知列表缺 `onShow` 刷新 | `Notifications.vue` |

### 6.2 对已知项的核验（仍成立）

| ID | 核验结论 |
|----|----------|
| G2 | ✅ `clearAuth` 仅清 token/userInfo/permissions，未见 reset 行为 Store |
| G1 | ✅ 占位页仍在；`NotificationDetail` 仍指向 `RoomDetail` |
| F4 | ✅ `roomId: undefined` 硬编码；类型亦无 `room_id` |
| F7 | ✅ 仍跳 `/pages/user/session/detail` |
| F1 | ✅ 客户端 filter；且 `getHomepageRooms` 参数无 status |
| F6 | ✅ `mock:+8613800138000` 仍在 |
| G5 | ✅ 维持可接受 |

### 6.3 本轮抽查范围与边界

已抽查：`auth.clearAuth`、全仓 `RoomDetail` 导航、`expert` sessions 映射、`getHomepageRooms` 签名、`FollowedExperts`/`Notifications` 生命周期、`SearchByTag` 跳转、`OneTapLogin` mock。

**未再发现额外高优先死链**（除已列 G1/F7）。未做：Admin Dialog 字段级、真机回归、OpenAPI 逐键、全 Store 订阅图。

---

## 七、与《18》/历史 problem 的交叉

| 来源 | 关系 |
|------|------|
| 《18》§0.1 G* | 编排/同步缺口；本清单给分拣与批次 |
| 《18》§7 F* | 展示×填充缺口；本清单给是否真问题 |
| `problem/README` 封面/专家绑定/watch API 等 | **并行历史缺陷**；不并入本分拣母单，修复时各自关闭 |
| BrandDetail Admin 关联房 | problem 记「已止血」；本清单 **F2** 仍为契约待确认（止血≠公开契约完备） |

---

## 八、检查清单（关闭本清单前）

- [x] 第 1 批真问题有对应代码改动（G2/G1/F4/F7/F8/N1/N2，2026-07-30）  
- [ ] F1/F3/F2/F5/F6/G4/G3 均有「确认结论」再改代码  
- [ ] G5 保持可接受或产品改口后重开  
- [ ] 《18》§0.1 / §7.7 状态与本清单同步（修完勾选）  
- [ ] `docs/problem/README.md` 总表状态已更新  

### 8.1 第 1 批落地摘要（代码）

| ID | 改动要点 |
|----|----------|
| G2 | `clearAuth` → `resetUserBehaviorStores()`；favorites/subscriptions/watchHistory `resetForLogout`；notifications `clearNotificationsData` |
| G1 | `RoomDetail` `redirectTo` LiveView；`NotificationDetail` room/session 直达 LiveView |
| F4 | `ExpertSessionBriefItem` 增 `room_id`；store 映射多别名，不再写死 `undefined` |
| F7 | SearchByTag → `/pages/live/LiveView?sessionId=` |
| F8 | 搜索品牌 Tab `is_active !== false` 过滤 |
| N1/N2 | FollowedExperts / Notifications 补 `onShow` 刷新 |

---

## 更新日志

| 版本 | 日期 | 状态 | 变更摘要 |
|------|------|------|----------|
| 1.0 | 2026-07-30 | 待评审 | 初版：G*/F* 三类分拣 + 批次；补查 N1/N2；交叉《18》与 problem 总表 |
| 1.1 | 2026-07-30 | 部分修复 | 第 1 批真问题代码落地并勾选；F1 仍属第 2 批待确认 |
