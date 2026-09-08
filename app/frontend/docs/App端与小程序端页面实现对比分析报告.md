# App 端与小程序端页面实现对比分析报告

> ⛔ **本报告（v1.0/v1.1）已被 `docs/App端与小程序端全量对比分析报告-终版.md`（v2.1）取代**。终版合并了用户实测报告与源码复核（修正本版 featured 目标类型等结论、冲突扩至 31 项）。本文件仅保留作演进记录/回溯查证用，**不作为实施依据**。
>
> **文档版本**：v1.0
> **创建日期**：2026-08-09
> **覆盖范围**：App 端（`main` 分支 + 工作区未提交 WIP）与微信小程序端（`wechat` 分支，仓库 `app-wechat-frontend-1`）全量页面/基建层对比
> **相关文档**：`小程序端管理功能接入App端实现方案设计文档.md`（v1.0，2026-08-06）、`小程序端与App端管理端页面对比报告.md`
> **结论先行**：两端代码无法直接合并（基建层 8 处冲突），但小程序端在「功能完成度」「微信生态规范」上领先，App 端在「工程化」「管理端能力」上领先；建议按本报告第八~十二章行动项推进

---

## 一、分析范围与方法

### 1.1 分析对象

| 端 | 分支 | 仓库 | 页面体系 | 规模 |
|----|------|------|---------|------|
| App 端 | `main`（含工作区未提交的 WIP 管理页） | `app-wechat-frontend-1` | `src/pages/app/`（App 原生） + `src/pages/h5/`（H5 桌面管理双树） | ~85 页，13 个 store，22 个 API 文件 |
| 小程序端 | `wechat` | 同仓库同分支 | `src/pages/` 平铺单树 | ~45 页（含 1 分包），16 个 store，26 个 API 文件 |

### 1.2 关键前提（本次核实到的事实）

1. **后端已完成融合**（`app_wechat_backend` 仓库 `7e2c914`：「App后端融合完整实施 — 管理端API、内容安全、用户管理、专家科室、系统优化」），后续同步改动不大。
2. **后端角色为统一大写枚举**：`REGULAR / MODERATOR / ADMIN / SUPERADMIN`（`backend/live_core_service/app/models/live_features.py:21-24`、`app/core/deps.py:54` 强制 `role.upper()`）。
3. **App 端上一轮方案已落地大半**：`useAdminGuard`（P0）、标签/品牌/留言/Tab 管理页、live-manage admin 模式编辑/删除/清空留言均已实现（多为未提交 WIP）。
4. 小程序端 12 个管理模块、22 个文件已全部完成。
5. **App 仓库内存在第二套 H5 桌面管理端**（`src/pages/h5/*` 15 个注册页 + `layouts/AdminLayout.vue` + element-plus）：RoomList/RoomCreate/RoomManage/Topic*/Venue/Department*/ExpertCreate。**其中 `RoomCreate` 支持「直播」类型创建**（`el-radio label="live"`）——「App 不能开直播」只对移动端 `live-manage/create.vue` 成立（仅预告/回放），H5 桌面端早已具备。这是三套管理实现并存的源头（移动 uni admin + H5 element-plus admin + 待借鉴的 MP 页）。
6. **App 登录页不读取 `?redirect=`**：`useAdminGuard` 传参、`login.vue` 无 `onLoad` 解析 → 管理员深链登录落在首页而非目标管理页（守卫链条断在最后一环）。
7. **App 内部 HTTP 动词不自洽**：`api/room.ts:54` 用 PUT（注释「uni.request 不支持 PATCH」为陈旧误导，`request.ts` 实际已导出 patch），`store/room.ts:198` 用 PATCH——同一端点仓库内两个动词。
8. **App 有 2 个通知页**：`pages/app/notifications/index`（已注册）与 `pages/app/tabbar/my/notifications/index`（**未注册孤儿页**，两页实现不同）。

---

## 二、总体结论（TL;DR）

| 维度 | 结论 |
|------|------|
| 管理端能力 | App 9 入口 vs 小程序 12 模块。App 缺：内容安全、品牌成员、品牌商品（后端接口已上线，属纯前端工作量） |
| 管理端工程质量 | **App 领先**：统一 `useAdminGuard` + 入口 `v-if="isAdmin"` 双重守卫；小程序 6 个管理页无守卫可直开 |
| 用户侧功能 | **小程序领先**：留言板（App 是演示数据）、原生分享+埋点、3D 焦点图、画质切换、会话下载、双源搜索历史、通知详情页等 20+ 项缺失 |
| 工程规范 | 小程序：微信规范贴合（子包/原生分享/无障碍/logger/11 个单测）；App：工程化强（组件化/骨架屏/路由守卫/权限指令），但 console.log 遍地、样式三套体系 |
| **合并风险** | **高**：基建层 8 处直接冲突（详见第八章），必须先统一再合代码 |
| 是否符合主流规范 | 两端均部分符合；App 缺「分享卡片/无障碍/深色模式」等 App 端主流能力，小程序缺「管理页守卫/组件化」 |

> **v1.1 增补（2026-08-09，10 子代理交叉验证后）**：本报告经多维度深挖与对抗性校验，补入 4 个此前遗漏的关键事实——① App 仓库内还有 **H5 桌面管理端**（15 页 element-plus，`RoomCreate` 支持直播创建）；② App 登录页 **`?redirect=` 断链**（守卫传参但 login 不读）；③ App 内部 **PUT/PATCH 不自洽**（`api/room.ts` PUT vs `store/room.ts` PATCH）；④ 存在 **未注册孤儿通知页**。冲突清单扩展至 C18。

---

## 三、页面覆盖度对比

### 3.1 管理端（13 模块对照）

| 模块 | 小程序文件 | App 文件 | 状态 |
|------|-----------|---------|------|
| 用户管理 | `admin/user/UserList.vue` + `UserEditDialog.vue` | `admin/users/index.vue` | ✅ 双向 |
| 专家管理 | `admin/expert/ExpertAdminList.vue` | `admin/expert-list/index.vue` | ✅ 双向 |
| 专家分类/科室 | `admin/category/CategoryList.vue` + `CategoryFormDialog.vue` | `admin/departments/index.vue` | ⚠️ **口径不一**（/admin/categories vs /admin/expert-departments） |
| 轮播图管理 | `admin/featuredContent/FeaturedContentList.vue` + `FormDialog` | `admin/featured/index.vue` | ✅ 双向（App 多「有效期/排序」） |
| 推送通知 | ❌ 无 | `admin/notification-push/index.vue` | App 独有 |
| 标签管理 | `admin/tag/TagList.vue` + `TagFormDialog.vue` | `admin/tags/index.vue` | ✅ 双向 |
| 品牌管理 | `admin/brand/BrandAdminList.vue` | `admin/brands/index.vue` | ✅ 双向 |
| 品牌成员 | `admin/brand/BrandMemberManager.vue` | ❌ 无 | **App 缺失** |
| 品牌商品 | `admin/brandProduct/BrandProductList.vue` | ❌ 无 | **App 缺失** |
| 留言管理 | `admin/roomMessage/RoomMessageList.vue` | `admin/messages/index.vue` | ✅ 双向 |
| 内容安全 | `admin/contentSafety/` 规则+表单+日志 3 文件 | ❌ 无 | **App 缺失** |
| 房间 Tab 管理 | `admin/roomTab/RoomTabManager*.vue` 3 文件 | `admin/room-tabs/index.vue`（带 roomId） | ✅ 双向 |
| 全站房间运营 | `admin/room/AdminRoomList.vue` + `AdminRoomEditDialog.vue` | `live-manage/list.vue` `mode=admin` | ✅ 双向（App 交互更丰富） |

### 3.2 用户侧核心页

| 页面 | 小程序 | App | 评价 |
|------|--------|-----|------|
| 首页 | 859 行 + 7 组件（3D 轮播/精选专家/状态筛选/双列瀑布流/快捷菜单） | 342 行 + 5 组件（预告混排轮播/权威专家条/模块 Tab/登录引导） | 各有千秋，App 信息密度更聚焦 |
| 我的 | `profile/Profile.vue`（11 管理入口+专业品牌区） | `tabbar/my/index.vue`（9 管理入口） | App 缺品牌工作台/我的专家入口 |
| 我的直播 | `my-live/MyLive.vue`（真实列表+本地缓存合并） | **tab 是死胡同**（中转页跳首页）；真列表在 `live-manage/list.vue`（4 模式） | **App 路径不通畅** |
| 直播间 | `live/LiveView.vue` 3705 行单文件（留言板/画质/下载/原生分享/气泡菜单） | `live/LiveView.vue` 2560 行（组件化/倒计时/流量提醒/资料下载） | 功能互补，App 留言是演示数据 |
| 搜索 | 分包单页（双源历史/联想/3 Tab 数量） | 两页拆分（拼音搜索/推荐兜底） | App 无联想/无服务端历史 |
| 品牌/专家 | 名称 Tab+历史+热搜 / 字母索引+我的专家 | 拼音搜索 / 科室 Tab | App 无「我的专家/品牌工作台」 |
| 登录注册 | 分页式（一键登录含 mock token） | 三合一 Tab + 云函数登录 + 回调页 | **App 明显更强** |
| 通知 | 单列表 + 详情页 | 分类 Tab + 未读计数 + 全部已读（无详情页） | 互补 |

---

## 四、各自优势清单

### 4.1 App 端优势

| # | 优势 | 依据（文件:行） |
|---|------|----------------|
| A1 | 统一管理端守卫：入口 `v-if="isAdmin"` + 页面级 `useAdminGuard`（未登录带回跳、非管理员 toast 返回） | `tabbar/my/index.vue:85`、`composables/useAdminGuard.ts:24-50` |
| A2 | 全局路由守卫 + `v-permission` 权限指令（按角色层级隐藏元素） | `utils/routeGuard.ts`、`directives/permission.ts`、`config/permission.config.ts` |
| A3 | 页面组件化：LiveView 拆 4 Tab 组件、首页拆 5 组件、骨架屏、三态完备 | `pages/app/live/LiveView.vue`、`home/components/*` |
| A4 | 管理页交互超小程序：批量封禁、批量删留言、标签启停开关、状态 Tab、未映射专家、焦点图有效期、房间 admin 模式内联编辑（含封面上传）/清空留言/Tab 管理/删除 | `admin/users/index.vue`、`admin/messages/index.vue`、`live-manage/list.vue:116-132` |
| A5 | 首页信息利用率高：预告混排轮播 +「立即预约」CTA + 登录引导（横幅+弹窗） | `home/components/FeaturedCarousel.vue`、`LoginGuideBanner.vue` |
| A6 | 登录 UX：三合一 Tab 登录、云函数登录、认证回调页、验证码重试上限、密码强度 | `pages/app/auth/login.vue`、`shared/auth/callback.vue` |
| A7 | 播放器工程化：`VideoPlayerApp` 封装（分段事件/错误兜底）、开播倒计时、流量提醒、资料下载 | `components/app/VideoPlayerApp.vue` |
| A8 | 头像闭环：预览 + 画布裁剪（AvatarPreview / avatar-crop） | `components/shared/AvatarPreview.vue` |
| A9 | 图片链路正确：`ProxyImage` 下载缓存 7 天（App 平台外链图必需）、`resolveMediaUrl` 本地路径透传 | `components/common/ProxyImage.vue`、`utils/imageProxy.ts` |
| A10 | 空态带行动引导（「看预告/看回放」「去发现」）、「已经到底了」贴底计算 | `home/components/RoomCardGrid.vue` |
| A11 | 拼音搜索（pinyin-pro）、搜索结果推荐兜底 | `utils/pinyin.ts`、`search/results.vue` |
| A12 | 关注/订阅页 Tab+搜索、通知分类 Tab+全部已读+未读数 | `tabbar/my/follows/index.vue` 等 |
| A13 | 房间数据聚合接口用法正确（`/brands/{id}/rooms` 等公开端点，非 admin 端点） | `api/brand.ts` |

### 4.2 小程序端优势

| # | 优势 | 依据 |
|---|------|------|
| W1 | **留言板完整链路**：分页/上拉更早/长按删自己的留言/500 字限制/未登录引导/昵称归一化（注销作者快照 D3 契约） | `pages/live/LiveView.vue`、`utils/roomMessageNormalize.ts`、`components/MessageItem.vue` |
| W2 | **原生分享**：`onShareAppMessage/onShareTimeline` + `uni.showShareMenu` + 分享埋点 `trackShare→shareSession` | `pages/live/LiveView.vue` |
| W3 | **3D 焦点轮播**：中间放大/两侧 0.85+变暗、触摸暂停 8 秒恢复、点侧卡先切中、单张关闭循环 | `components/home/Banner3D.vue` |
| W4 | 焦点图跳转覆盖 expert/brand/topic 全类型（App 只有 session/room/external） | `pages/home/Home.vue` `handleBannerClick` |
| W5 | 直播画质切换、会话下载 | `pages/live/LiveView.vue` |
| W6 | 首页双列/单列视图切换（QuickMenu 悬浮菜单）、消息铃铛+未读红点直达通知 | `components/home/QuickMenu.vue`、`TopBar.vue` |
| W7 | 精选专家大模块（带实时直播状态 + 列表内关注） | `components/home/FeaturedExperts.vue` |
| W8 | 内容安全、品牌成员、品牌商品 3 个管理模块（后端已上线） | `pages/admin/contentSafety/*` 等 |
| W9 | 搜索双源历史（本地+服务端，带时间元数据、单条删除）、页内联想、3 Tab 数量角标、标签搜索页 | `subpackages/search/index.vue`、`api/search.ts` |
| W10 | 观看历史状态筛选 + 观看进度显示；通知详情页（相关对象跳转） | `profile/ViewHistory.vue`、`NotificationDetail.vue` |
| W11 | 专家字母索引（拼音锚点盲跳）、品牌工作台、我的专家 | `components/expert/LetterIndex.vue`、`brand/BrandWorkbench.vue`、`expert/MyExpert.vue` |
| W12 | 微信生态规范：分包+预载（2MB 包体）、原生自定义 tabBar、无障碍 aria-label 广泛、`logger` 结构化日志、11+ vitest 单测 | `pages.json` subPackages、`logs/logger.ts`、`test/` |
| W13 | 请求层企业级封装：响应归一化（裸数组也能包装）、业务码映射（2005/2004 人话）、acceptCodes 空态白名单、双网关路由（core/users）、参数清洗、404 诊断日志 | `utils/request.ts` |
| W14 | 我的直播本地缓存合并（myLiveCache）、列表内删除房间 | `utils/myLiveCache.ts` |
| W15 | 邮箱绑定独立页、手机/邮箱注册选择页 | `pages/settings/BindEmail.vue`、`auth/RegisterChoice.vue` |

---

## 五、可采纳的小程序设计清单（App 端行动项，按优先级）

### P0 级（直接影响主流程完整性）

| # | 采纳项 | 参考实现 | App 落地方式 | 工作量 |
|---|--------|---------|-------------|:------:|
| 1 | **直播间留言板接真实 API**（当前 ChatTab 为演示数据，`live/mock-data.ts` 可见） | `LiveView.vue` 留言板 + `utils/roomMessageNormalize.ts` + `components/MessageItem.vue` | 复用后端 `/messages` 公开接口（App `api/message.ts` 已有封装），替换 ChatTab 演示数据；迁移昵称归一化到 `utils/` | 1d |
| 2 | **原生分享补齐**：`onShareAppMessage/onShareTimeline` + 分享计数埋点 | `LiveView.vue` 分享段 | App 端可保留 `uni.share` 通道，补齐页面级分享钩子；与后端 `shareSession` 接口对接 | 0.5d |
| 3 | **焦点图 3D + expert/brand 跳转**（并行项未完成） | `components/home/Banner3D.vue` | 移植 `getCardClass` 缩放/变暗/层级，保留 `swiperKey` Android 兼容与 upcoming 混排；`handleCampaignClick` 补 expert/brand 分支，`admin/featured/index.vue` 补目标类型 | 0.5d |

### P1 级（补齐 3 个缺失管理模块，后端已就绪）

| # | 采纳项 | 参考实现 | 前置 |
|---|--------|---------|------|
| 4 | **内容安全管理页**（规则+日志双 Tab） | `contentSafety/` 3 文件 + `utils/contentSafetyDisplay.ts`（文案映射） | 与后端确认字段契约（frontend-admin-connect-plan 已标记 schema/model 不一致风险） |
| 5 | **品牌成员管理页** | `BrandMemberManager.vue` | 产品确认 App 开放品牌管理 |
| 6 | **品牌商品管理页** | `BrandProductList.vue` | 同上 |

### P2 级（用户侧体验增强）

| # | 采纳项 | 参考实现 | 说明 |
|---|--------|---------|------|
| 7 | 首页双列/单列视图切换 | `QuickMenu.vue` | App 首页已有 RoomCardGrid 双列，补悬浮菜单即可 |
| 8 | 搜索服务端历史 + 页内联想 | `subpackages/search/index.vue`、`api/search.ts` | App 历史仅本地存储 |
| 9 | 观看历史状态筛选 + 进度显示 | `ViewHistory.vue` | App 版为纯列表 |
| 10 | 通知详情页 | `NotificationDetail.vue` | 与 App 分类 Tab 体系兼容 |
| 11 | 字母索引（专家长列表盲跳） | `LetterIndex.vue` | App 已用科室 Tab，可选 |
| 12 | 精选专家大模块（直播状态+关注） | `FeaturedExperts.vue` | App 的 AuthorityStrip 为轻量横滑条，可升级 |
| 13 | 邮箱绑定页 / 我的专家 / 品牌工作台 | `BindEmail.vue`、`MyExpert.vue`、`BrandWorkbench.vue` | 与产品确认优先级 |

---

## 六、可采纳的 App 设计清单（反向：小程序可回流项）

| # | 采纳项 | 依据 | 说明 |
|---|--------|------|------|
| 1 | **管理页统一守卫** | `useAdminGuard.ts` | 小程序 6 个管理页（分类/轮播/标签/内容安全系列）无守卫可直开，属安全缺陷 |
| 2 | 管理端交互增强 | App admin 页 | 批量封禁/批量删留言/启停开关/状态 Tab/焦点图有效期 |
| 3 | 直播管理 4 模式单页 | `live-manage/list.vue` | 我的/今日场次/正在直播/全站房间统一路由 |
| 4 | 登录三合一 + 云函数登录 + 回调页 | `pages/app/auth/login.vue` | 小程序一键登录含 mock token，需接真实通道 |
| 5 | 通知分类 Tab + 未读计数 + 全部已读 | App notifications 页 | 小程序为单列表 |
| 6 | ProxyImage 缓存方案 | `components/common/ProxyImage.vue` | 小程序端微信自身有缓存，可仅作参考 |
| 7 | 骨架屏 / 空态行动引导 | App 首页/列表 | 体验规范项 |

---

## 七、规范符合度评估（主流 App / 小程序规范）

### 7.1 App 端对主流 App 规范（iOS HIG / Material / 移动端通用）

| 规范项 | 状态 | 说明 |
|--------|:----:|------|
| 触控目标 ≥44pt | ⚠️ | 管理页 action-chip（padding 12rpx 24rpx）偏小；`my` 页菜单 min-height 88rpx 达标 |
| 安全区适配 | ✅ | `env(safe-area-inset-bottom)` + tabbar 112rpx 计算（`home/index.vue:363`） |
| 加载/空/错三态 | ✅ | 骨架屏 + 空态引导 + toast；缺公共 ErrorBanner（各页 `loadError` 自管） |
| 下拉刷新 + 上拉分页 | ✅ | scroll-view refresher + scrolltolower，双通道兜底 |
| 分享体系 | ❌ | **无 onShareAppMessage/onShareTimeline、无分享埋点**（主流 App 标配） |
| 深色模式 | ❌ | App 无；小程序 `theme.scss` 已有亮暗主题体系 |
| 无障碍（role/aria） | ⚠️ | 仅 LiveView action-row；小程序端广泛使用 |
| 登录引导 | ✅ | 横幅+弹窗+快捷入口（未登录快捷点击仅 toast，可再优化为引导跳登录） |
| 图片缓存/跨域 | ✅ | ProxyImage 本地缓存 7 天（平台必须） |
| 调试日志治理 | ❌ | `auth.ts`/`request.ts`/`constants/api.ts` 大量 console.log（含 emoji），生产环境应收敛为 logger |

### 7.2 小程序端对微信小程序规范

| 规范项 | 状态 | 说明 |
|--------|:----:|------|
| 包体 ≤2MB | ✅ | 搜索分包 + preloadRule |
| 原生分享/朋友圈 | ✅ | onShareAppMessage/onShareTimeline |
| 自定义 tabBar 原生实现 | ✅ | `custom-tab-bar/` wxml 目录 |
| 无障碍 | ✅ | 广泛 role/aria-label |
| 页面可维护性 | ❌ | LiveView 单文件 3705 行、CreateLive 2212 行，严重超规范 |
| 管理端安全 | ❌ | 6 个管理页无守卫，非管理员可直开 |
| 结构化日志/单测 | ✅ | logger + 11+ vitest |

### 7.3 两端共同缺失

| 缺失项 | 说明 |
|--------|------|
| 弹幕模块 | 两端直播页均无 |
| 数据埋点体系 | App `utils/analytics.ts` 与小程序 `trackShare` 未成体系，无统一埋点规范 |
| 统一的错误上报 | 无 Sentry 类聚合 |
| 深色模式 | App 缺失（小程序已有 theme.scss） |
| UI 规范文档 | 两端 token 体系各自为政（见第八章） |

---

## 八、实现冲突清单（合并前必须解决）⭐

> 两端共用同一后端，以下冲突是「合并代码」与「契约对齐」的直接障碍。

| # | 冲突 | App 端 | 小程序端 | 后端事实/建议 |
|---|------|--------|---------|--------------|
| C1 | **role 枚举大小写** | `auth.ts:106-108` 精确匹配 `'ADMIN'\|'SUPERADMIN'`；类型 `'REGULAR'\|'MODERATOR'\|'ADMIN'\|'SUPERADMIN'` | `store/auth.ts` `toLowerCase() === 'admin'`；类型 `'user'\|'admin'\|'expert'` | 后端 `deps.py:54` 强制 `.upper()` → **两端运行时均能工作**；但类型定义与大小写习惯不一致，合并时统一为 App 的大写枚举 + wechat 的 toLowerCase 容错写法 |
| C2 | **用户 ID 字段** | `uuid` 主键，fetchUserProfile 手动映射 `user_id` | `user_id` 主键 | 后端返回 `user_id`；App 类型层混乱，建议统一 `user_id` 别名 |
| C3 | **分页参数** | 一律 `page/size` | `tags.ts` 发 `page_size`；categories 内部 `page_size→size`；BrandProductList 双发 | 与后端确认参数名契约，建议统一 `page/size`（App 现状），小程序封装层已做映射，风险低 |
| C4 | **请求层响应语义** | 裸透传 `res.data`，后端返回裸数组会解析失败 | `normalizeApiResponse` 兜底包装（裸数组→{code,data}） | 合并时保留 App 的泛型结构，但移植 wechat 的归一化容错，避免「同一接口两端解析代码不同」 |
| C5 | **token 存储 key** | `jwt_token` | `access_token` / `user_info` | 分支独立编译不冲突；若未来同仓同构建需统一常量 |
| C6 | **401 跳转** | `navigateTo /pages/app/auth/login`（H5 整页跳外部 LOGIN_URL） | `reLaunch /pages/auth/OneTapLogin?redirect=` | 两套登录页路径，合并时按平台条件编译 |
| C7 | **CSS 变量同名不同值** | `--color-success:#52c41a`、`--color-text-secondary:#6C757D`，另有 `--home-*`/`--expert-*` 三体系并存，`--color-primary` 重复定义 | `--color-success:#67C23A`、`--color-text-secondary:#909399` 单体系 | **合并后同 key 异值会让视觉漂移**；以 App 的 `--home-*` 或统一 token 为准 |
| C8 | **组件 API 分歧** | `ModalDialog` 仅 4 props（无 content/showClose/maskClosable/插槽，遮罩点击空实现） | `ModalDialog` 全能力（content/showClose/showCancel/maskClosable/插槽） | 统一以能力全者为基线；`LoadingIndicator` 默认色 `#007AFF` 硬编码需 token 化 |
| C9 | **API 文件命名** | `favorite/subscription/notification`（单数）、`message.ts`、`featured.ts`、`tab.ts`、`watchHistory.ts` | `favorites/subscriptions/notifications`（复数）、`roomMessage.ts`、`featuredContent.ts`、`room-tabs.ts`、`history.ts` | 命名不冲突（各自独立），但合并/互相参考时易混，建议统一复数 |
| C10 | **请求封装签名** | `get(url, params, {auth})` 纯函数 | `request.get(url, config)` 类实例 | 4 层映射已按此改写，合并时以 App 签名为准 |
| C11 | **分类双体系** | `/admin/expert-departments`（departments 页） | `/admin/categories`（CategoryList 页） | **待定项**：与后端确认两套表/接口的关系，避免重复建设 |
| C12 | **上传字段名** | `file`（featured.ts:69-90 手拼 header） | `image` | 以 App 契约为准，逐个核对 |
| C13 | **留言/房间 Tab 契约** | 读 `extra.user_avatar/user_display_name`；Tab key `intro/experts/brands/chat` | 读 `user.{nickname,avatar_url}` 快照 + D3 注销占位；Tab key `intro/expert_intro/brand_intro/message`（自动注入） | **高**：同一后端 `room_messages`/`/rooms/{id}` 喂两端，换渲染器不换归一化即错名/错 Tab |
| C14 | **房间更新动词（App 内部）** | `api/room.ts:54` **PUT**（注释「uni.request 不支持 PATCH」陈旧误导）vs `store/room.ts:198` **PATCH** | 统一 PATCH | **高**：同仓库两个动词打同一端点；严格 REST 后端拒一个。`request.ts` 已导出 patch |
| C15 | **首页信息流排序/分页** | `sort='heat:desc'` + page 15+85 | `sort='created_at:desc'` + page 10 + 客户端过滤 | **高**：同一 `GET /homepage/rooms` 两端排序/覆盖不同 |
| C16 | **焦点图数据形态 + 目标词汇** | 假定裸数组；管理表单 `[null,room,topic,external]`，运行时却跳 `session` | 归一 `array\|{items}`；目标 5 类含 expert/brand | **高**：同后端一边空一边满；App 管理端 UI 与运行时不自洽 |
| C17 | **验证码字段名 / one-tap 协议** | 只读 `image_base64`；`OneTapLoginRequest` 无 `agreed_to_terms` | 优先 `captcha_image` 回退 base64；必发 `agreed_to_terms` | **中**：后端字段调整/合规校验会只挂一端 |
| C18 | **账号注销/改密载荷 + 通知枚举** | `deleteUserAccount()` 无验证码；passwordless 缺 current_password；通知枚举 `system/subscription/interaction` | `deleteMyAccount({captcha_id,captcha_solution})`；必带 current_password；通知枚举 `live_start/live_end/follow/...` | **高**：验证码强制后 App 注销必挂；同一通知两端 Tab 归类不同 |

---

## 九、后端事实核对与现状判断

| 项 | 事实 | 影响 |
|----|------|------|
| 后端角色大写 | `deps.py:54` `.upper()`、`permissions.py` 全大写判断 | App 的 isAdmin 精确匹配正确；wechat toLowerCase 恰好兼容 → 无运行时 bug，但统一建议见 C1 |
| 管理端 API 已融合 | 用户/房间/留言/内容安全/专家科室/通知/精选内容（`7e2c914`） | App 的 tags/brands/messages/room-tabs 页面「零后端成本」落地成功印证 |
| 内容安全 DDL | frontend-admin-connect-plan 记录 schema/model 不一致、DDL 不完整 | P2 开工前必须与后端确认字段契约（风险 R3） |
| admin 操作他人房间 | `updateRoom`/`deleteRoom` 非 admin 专用端点 | App `live-manage/list.vue` admin 模式已实测可编辑/删除 → R2 已解除，但建议后端补 admin 专用鉴权复核 |

---

## 十、需要优化的部分（两端）

### 10.1 App 端（按优先级）

| # | 优化项 | 现状 | 目标 |
|---|--------|------|------|
| 1 | **留言/聊天接真实数据** | ChatTab 演示数据（`live/mock-data.ts`） | 对接 `/messages` 公开接口 + 归一化 |
| 2 | **「我的直播」tab 死胡同** | `tabbar/my-live/index.vue` 中转跳首页 | 改为真实列表（可复用 live-manage/manage 模式）或明示入口 |
| 3 | **分享链路** | 无页面级分享钩子/埋点 | 补 onShareAppMessage/onShareTimeline（App 端）+ 埋点 |
| 4 | **样式体系收敛** | `--color-*` + `--home-*` + `--expert-*` 三体系、`--color-primary` 重复定义、`styles/variables.scss` 未被注入 | 统一 token 单一来源；注入或删除 variables.scss |
| 5 | **调试日志治理** | auth store/request/constants/api 大量 console.log | 收敛为 logger 分级 |
| 6 | **硬编码清理** | `https://mp.dayilive.com`（url.ts）、`124.220.235.226`（vite proxy）、`#007AFF`（LoadingIndicator） | 全部 token/环境变量化 |
| 7 | **单测补齐** | 仅 1 个 `phone.test.ts` | 移植小程序 11+ 用例（contentSafetyDisplay/留言归一化/url 兜底等） |
| 8 | **请求层容错** | 裸响应透传 | 移植 `normalizeApiResponse` + `cleanQueryParams` + 业务码映射（2005/2004） |
| 9 | 无障碍 | 仅 LiveView | 公共交互元素补 role/aria-label |
| 10 | 深色模式 | 无 | 参考小程序 theme.scss |
| 11 | 未登录快捷点击 | 仅 toast | 引导跳登录（带 redirect） |

### 10.2 小程序端（可回流建议）

| # | 优化项 | 现状 |
|---|--------|------|
| 1 | 管理页守卫 | 6 页无守卫，照搬 App `useAdminGuard` |
| 2 | LiveView 拆分 | 3705 行单文件 → 按 App 4 Tab 组件模式拆分 |
| 3 | 一键登录 mock | 含 mock token `'mock:+8613800138000'`，需接真实通道 |
| 4 | 管理端交互增强 | 批量操作/状态 Tab/启停开关按 App 对齐 |

---

## 十一、需要融入的新功能（建议清单）

| # | 新功能 | 优先级 | 建议 |
|---|--------|:------:|------|
| 1 | 内容安全管理（App 端） | 高 | 小程序实现已就绪，后端已上线，纯移植 |
| 2 | 品牌成员/商品管理（App 端） | 中 | 产品确认后移植 |
| 3 | 弹幕模块（两端） | 低 | 直播产品标配，可后置 |
| 4 | 统一埋点/数据看板（两端） | 中 | App `analytics.ts` 已有雏形 |
| 5 | 深色模式（App 端） | 低 | 小程序 theme.scss 可回流 |
| 6 | 直播画质切换/下载（App 端） | 中 | 小程序已实现（LiveView） |
| 7 | 观看进度续播（App 端） | 中 | 小程序 watch-history 已有进度字段，App 播放器可对接续播 |
| 8 | 服务端搜索历史同步（App 端） | 低 | 小程序双源方案已实现 |
| 9 | 全站 Tab 治理入口（App 端） | 低 | room-tabs 页已有 roomId 版，补全站入口需产品确认 |
| 10 | 分类双体系统一 | 待定 | 与后端确认 categories vs expert-departments 后再动 |

---

## 十一A、H5 桌面管理端（重大发现，v1.1 新增）

### 11A.1 现状

`src/pages/h5/*` 是 App 仓库内**第二套管理端**（与移动端 `pages/app/admin/` 并行），基于 element-plus 桌面组件 + `layouts/AdminLayout.vue`：

| 模块 | 页面 | 说明 |
|------|------|------|
| 房间管理 | `RoomList`/`RoomCreate`/`RoomManage`/`RoomBasicSettings`/`MultiVenueManage`/`LiveView` | **`RoomCreate` 支持「直播」类型创建**（`el-radio label="live"`，RoomCreate.vue:32） |
| 专题管理 | `TopicList`/`TopicCreate`/`TopicDisplay`/`TopicManage` | App 移动端无专题前台页面，H5 已有完整专题 |
| 科室管理 | `DepartmentManage`/`DepartmentMerge`/`UnmappedExperts` | 与移动端 `admin/departments` 功能重叠 |
| 专家创建 | `ExpertCreate` | 移动端无 |
| 场地 | `VenueDisplayPage` | — |

**合计 15 个注册页面**（`pages.json:12-158`），依赖 `element-plus`、`@element-plus/icons-vue`、`artplayer`（H5 播放）。

### 11A.2 对之前结论的三处修正

1. **「App 无法创建直播」仅对移动端成立**——H5 `RoomCreate` 早已支持直播类型。决策需区分：移动端补直播创建（借鉴 MP `CreateLive`）or 直播创建收口到 H5 桌面端。
2. **专题（Topic）功能 App 移动端完全空白**，但 H5 已有——属于「移动端待接入」而非「全新功能」。
3. **三套管理实现并存**（移动 uni admin + H5 element-plus admin + 待借鉴 MP 页）——「管理功能」边界需明确，否则同一能力三处维护。

### 11A.3 建议

- 明确边界：**桌面运营 = H5（element-plus）；移动运营 = uni admin；MP = 功能参考源**。
- 直播创建/专题等能力决策时先查 H5 是否已有，避免重复建设。
- 三套并存的长期收敛方案（统一到某一套 or 保持分层）需产品/架构决策。

---

## 十二、协作与合并建议

1. **基建先行**：先完成第八章 C1/C3/C4/C7 四项契约统一（role 枚举写法、分页参数、响应归一化、CSS token），再谈功能合并——这四项目前是「合并即炸」项。**v1.1 增补：C13–C18 属高/中优先，其中 C14（PUT/PATCH）是 App 仓库内部 bug 应立刻修**。
2. **分支策略**：维持 `main`（App+H5）与 `wechat` 双分支，功能单向回流（小程序→App 为主，App→小程序为辅）；不建议近期直接合并分支，建议按模块 cherry-pick 代码 + 4 层映射改写（请求签名/图片/样式/守卫）。
3. **文档同步**：每个模块按既有 14 章实施文档模板落地；本次报告第八、九章冲突清单同步给后端同学确认契约。
4. **测试左移**：App 端把 wechat `test/` 下可移植用例（contentSafetyDisplay、roomMessage.contract、brand-soft-delete、adminUser）迁入 vitest。
5. **验收基线**：所有新页面过 `pnpm lint` + `pnpm test:run`；App 端 Android 真机回归（swiperKey/ProxyImage 不受影响）。
6. **v1.1 增补（高优先修复项）**：① `login.vue` 补 `onLoad` 读 `?redirect=`（守卫链条收尾）；② `api/room.ts` PUT→PATCH（删误导注释）；③ 删除/合并未注册孤儿通知页 `pages/app/tabbar/my/notifications/index`；④ `room-tabs` 补进 `my/index.vue` adminRoutes（当前只能从 live-manage 进）；⑤ H5 桌面端边界决策（§11A）。

---

## 十三、验收标准（本报告落地项）

- [ ] 直播间留言板接真实 API（替换演示数据），昵称归一化迁移
- [ ] 分享卡片/埋点补齐（App 端）
- [ ] 焦点图 3D + expert/brand 跳转完成，Android 真机回归通过
- [ ] 内容安全管理页上线（与后端字段契约确认后）
- [ ] 品牌成员/品牌商品管理页上线（产品确认后）
- [ ] role 枚举/分页参数/响应归一化/CSS token 四项契约统一
- [ ] **v1.1 增补**：`login.vue` 读 `?redirect=` 深链修复；`api/room.ts` PUT→PATCH；孤儿通知页清理；`room-tabs` 入管理菜单；H5 桌面端边界决策
- [ ] 「我的直播」tab 死胡同修复
- [ ] 样式三体系收敛为单一 token 源
- [ ] 单测从 1 个提升至 ≥10 个（移植小程序用例）
- [ ] console.log 调试输出收敛为 logger
- [ ] 管理端对比报告（`小程序端与App端管理端页面对比报告.md`）中的 11 项采纳清单逐项确认

---

## 十四、变更记录

| 版本 | 日期 | 变更内容 |
|:----:|:----:|---------|
| v1.0 | 2026-08-09 | 初版：基于两端源码逐文件核实（main 工作区含 WIP + wechat 分支），完成管理端 13 模块、用户侧 10 域、基建层 10 项对比；输出冲突清单 12 项、采纳清单 20 项、优化项 15 项、新功能 10 项 |
| v1.1 | 2026-08-09 | 增补（10 子代理多维度深挖 + 对抗性验证后）：① 新增 §1.2 事实 5-8 与 §11A H5 桌面管理端（含直播创建）；② 冲突清单扩至 C18（C13 留言/Tab 契约、C14 PUT/PATCH 内部冲突、C15 排序口径、C16 焦点图形态、C17 验证码/one-tap、C18 注销/通知枚举）；③ 协作建议补 5 项高优先修复（?redirect= 断链、PUT/PATCH、孤儿页、room-tabs 入口、H5 边界） |
