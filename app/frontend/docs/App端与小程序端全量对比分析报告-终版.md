# App 端与小程序端全量对比分析报告（终版 v2.2）

> **文档版本**：v2.2
> **创建日期**：2026-08-09（v2.2 更新 2026-08-12）
> **覆盖范围**：App 端（`main` 分支 + 工作区 WIP）vs 小程序端（`wechat` 分支 c1a52cf）——页面/API 契约/基建层/认证/规范全量对比
> **分析来源**：① 用户实测报告（18 项契约冲突）；② 10 子代理多维深挖 + 对抗性验证报告（v1.1）；③ 本版对两报告全部关键声明的**源码逐一复核**（含 2 处修正）；④ v2.1 工作区现状再校准 + 功能级实施梳理；⑤ **v2.2 焦点图域实施闭环记录**（见「十三」章）
> **相关文档**：`小程序端管理功能接入App端实现方案设计文档.md`（执行批次）、`小程序端与App端管理端页面对比报告.md`（管理端模块细节附录）、`焦点图管理实施规划文档.md`（焦点图域分阶段实施主文档，v1.6 终版）、`焦点图实施测试数据登记表.md`（F1 测试数据台账）。本报告 v1.0/v1.1（已由本版取代）
> **结论先行**：两端同栈同后端**无结构性冲突**；但存在 **18 项 API 契约冲突**（后端同步后 App 端将大面积报错，最高优先）与 **5 项未完成功能暴露在线**（Mock 生产开启/我的直播占位/LiveView 聊天 Mock/下载占位/邮箱绑定死链）。行动路线：契约对齐 → P0 修正 → 管理页三模块 → 用户侧功能补齐 → 工程卫生。v2.1 校准：**留言已接真实 API、搜索已双源**，互动真实化进度过半。**v2.2：焦点图域（首页展示+管理页）已按《焦点图管理实施规划文档》分 5 阶段全部实施闭环，生产 Mock 已关闭。**

---

## 零、文档体系与使用指南（v2.1 新增）

> 目前项目里关于"小程序端 vs App 端实现"共有 **3 份对比文档** + 1 份执行计划，本表说明各自区别与职责，避免重复劳动与版本误读。

### 0.1 三份对比文档的区别

| 文档 | 版本 | 范围 | 定位 | 状态 |
|------|:----:|------|------|:----:|
| `docs/小程序端与App端管理端页面对比报告.md` | v1.0 | **仅管理端** 13 模块逐模块对比（守卫/分页/弹窗/筛选/API/状态管理），含 App→小程序回灌清单 11 项、App 独有能力 11 项、App 缺失模块 3 个 | **模块级细节附录** | ✅ 有效 |
| `docs/App端与小程序端页面实现对比分析报告.md` | v1.0→v1.1 | 全量：管理端 13 模块 + 用户侧 10 域 + 基建层 10 项 + 规范符合度 + 冲突 C1–C18 + H5 桌面管理端专项（11A）+ 优势清单 | 全量对比**初版全景**（含 10 子代理验证） | ⛔ 已被本终版取代 |
| `docs/App端与小程序端全量对比分析报告-终版.md`（**本文件**） | v2.0→v2.1 | 全量 + **合并用户实测报告**（18 项契约冲突）+ 12 项**源码复核**（修正 1 处用户错误）+ 冲突扩至 **31 项** + P0/P1/P2 行动路线 + 风险表 R1–R9 + 验收标准 | **单一事实源 / 行动主文档** | ✅ 唯一权威 |

**区别要点**：
1. **文档①只讲管理端**（13 模块逐项），粒度最细、最适合"对齐某一个管理页面"时查；
2. **文档②是第一版全量对比**（v1.1），覆盖面最广但**无用户实测数据、无逐项源码复核**，结论部分被本版修正（如 featured 目标类型）；
3. **文档③（本文件）是文档②的超集 + 用户实测合并 + 复核修正**，冲突从 18 项扩到 31 项，并给出可直接执行的行列路线——**只以本文件为准**。

### 0.2 后续如何使用

| 场景 | 用哪份 |
|------|--------|
| 日常开发/联调，查契约冲突、行动路线、风险 | **本终版**（第七章冲突清单、第八章行动路线） |
| 实施某个管理端页面（如内容安全、品牌成员） | 本终版路线 + **文档①对应模块行**（守卫/分页/弹窗/筛选逐项对齐） |
| 按批次排期执行 | `docs/小程序端管理功能接入App端实现方案设计文档.md`（P0–P3 批次） |
| 回溯 v1.1 时代结论（H5 桌面端 11A、规范符合度原始评估） | 文档②（仅查证用，不作为依据） |

> **约定**：后续对比类更新**只维护本终版**（追加 v2.x 章节），不再新开对比文档；文档①保持管理端细节附录身份不动；文档②在头部已标注"已被终版取代"。

---

## 一、分析范围与方法（v2.0）

| 端 | 分支 | 仓库 | 页面体系 | 规模 |
|----|------|------|---------|------|
| App 端 | `main`（含工作区 WIP） | `app-wechat-frontend-1` | `src/pages/app/`（App 原生） + `src/pages/h5/`（H5 桌面管理） | ~85 页，13 store，22 API 文件 |
| 小程序端 | `wechat`（`c1a52cf`，与 GitHub 同步） | 同仓库同分支 | `src/pages/` 平铺单树 | ~45 页（含 1 分包），16 store，26 API 文件 |

**v2.0 复核结论（对两份来源报告的修正）**：

| # | 复核项 | 结果 |
|:-:|--------|------|
| 1 | 用户报告 18 项契约冲突 | ✅ **全部属实**，其中 #2（`/sessions/sessions/{id}` 双段路径）、#8（上传字段 `image` vs `file`）有 MP 注释自证对齐最新 OpenAPI |
| 2 | `VITE_USE_MOCK=true` 生产开启 | ✅ 属实（`.env.production:27`，注释自相矛盾） |
| 3 | 我的直播 Tab 纯占位 | ✅ 属实（51 行，onShow 跳首页） |
| 4 | MP LiveView 4145 行 / CreateLive 2509 行 | ✅ 属实 |
| 5 | App `ngrok-skip-browser-warning` 遗留 header | ✅ 属实（`request.ts:122`） |
| 6 | `goToUserService` appId 占位字符串 | ✅ 属实（`auth.ts:619`） |
| 7 | App 请求层不校验业务 code / MP 有 acceptCodes | ✅ 属实（App `request.ts` 无 code 校验；MP `request.ts:643`） |
| 8 | App token 提前刷新 vs MP 仅 401 跳登录 | ✅ 属实（`store/auth.ts:215`） |
| 9 | MP 角色类型 `user/admin/expert` + toLowerCase | ✅ 属实（`types/auth.ts:8`、`store/auth.ts:147-148`）；后端大写枚举 → App 大写类型对，MP 容错写法兼容 |
| 10 | ❌ **用户报告错误**：称 App featured 表单目标类型与 MP 一致（含 expert/brand） | **App 表单仅 `[null,room,topic,external]`**（`featured/index.vue:250`），MP 为 5 类含 expert/brand（`FormDialog.vue:259`）；且 App 运行时能跳 session 而表单不能建——管理 UI 与运行时不自洽 |
| 11 | 用户报告称"无结构性冲突" | 部分成立（同栈同后端），但契约层 18 处冲突即结构性风险，见第七章 |
| 12 | 用户报告称"App 管理端比小程序少 3 模块" | ✅ 属实（品牌成员/品牌商品/内容安全） |

---

## 二、总体结论（TL;DR）

| 维度 | 小程序端 | App 端 | 判读 |
|------|---------|--------|------|
| 用户端页面 | 31 个（LiveView 4145 行/页） | 30 个（LiveView 2834 行/页） | 功能面基本对齐，交互侧重点不同 |
| 管理端页面 | 13 模块 / 22 文件 | 9 模块 / 9 页 | **App 缺 3 模块**（品牌成员/商品/内容安全） |
| 后端 API 契约 | **与最新后端 OpenAPI 对齐**（注释自证） | **大量旧契约** | ⚠️ **18 处冲突**，后端同步后 App 端会挂 |
| 请求层成熟度 | 高（业务码校验/acceptCodes/404 诊断/自动网关） | 中（**不校验业务 code**、GET 自动重试） | **小程序更强** |
| Token 刷新 | ❌ 仅 401 跳登录 | ✅ 过期前 5 分钟自动刷新 | **App 更强** |
| 认证能力 | 全（邮箱登录/绑定/注销+图形码/OTP ticket） | 部分（无邮箱登录/绑定、无注销） | **小程序更强** |
| 图片链路 | resolveMediaUrl + 兜底函数族 | ProxyImage 外链缓存 + Android file:// 转换 | 各有所长，App 适配 APP 平台更强 |
| 工程基建 | 巨型页面/类型脱节/重复代码 | 统一 ModalDialog/useSwiperTabs/useAdminGuard | **App 更强** |
| 暗黑模式 | ⚠️ 状态机有（theme.scss dark 块），palette 不全 | ❌ 无 | 两端均不完整 |
| 触控热区 | 管理页多处 24–32px < 44px | 多数达标 | **App 更符合规范** |

**核心结论**：两端没有结构性冲突（同一套 uni-app 技术栈、同一后端），差异集中在 ① **18 处 API 契约冲突**（后端同步后 App 端必须先行修正）② 小程序认证与用户侧能力比 App 全 ③ App 管理端比小程序少 3 模块 ④ 首页焦点图视觉不一致 ⑤ **App 存在 5 项未完成功能直接暴露在线上**。

---

## 三、页面实现区别（用户端全量矩阵）

| 功能域 | 小程序实现 | App 实现 | 核心差异 |
|--------|-----------|---------|---------|
| 首页 | `home/Home.vue`(956) + **Banner3D 3D 卡片**（scale 1/0.85 + 变暗 + z-index 分层 + 触摸暂停 8s 恢复） | `tabbar/home/index.vue`(379) + FeaturedCarousel（露边卡片式，无 3D 缩放；**预告混排 + CTA + swiperKey Android 兼容**） | 视觉：3D 景深 vs 平面露边；能力：App 多预告混排/CTA/安全跳转，MP 多 3D 效果 |
| 直播播放 | `live/LiveView.vue`(4145) **全真实 API**（真实留言板/聊天，留言有删除） | `live/LiveView.vue`(2834) **聊天/问答/资料为本地 Mock**（LIVEVIEW_API_MODE 开关） | ⚠️ **App 互动功能未接真实后端**；App 多断点续播/流量提醒/动态 Tab 兜底 |
| 创建直播 | `live/CreateLive.vue`(2509)，createRoomSession→extractSessionId→updateSession 两步流；**直播/预告/回放三分支** | `live-manage/create.vue`，**仅预告/回放**（直播分支只在 H5 `RoomCreate` 存在） | ⚠️ **App 移动端不能开直播** |
| 我的直播 | `my-live/MyLive.vue`(392) 真实列表+编辑/删除 | `tabbar/my-live/index.vue`(51) **纯占位页**（onShow 跳首页） | ⚠️ **App 端缺失，用户无法进入直播管理** |
| 我的 | `profile/Profile.vue`(586) | `tabbar/my/index.vue`(1506) | App 多：5 宫格统计、管理员入口、认证诊断页；MP 结构更简洁 |
| 认证 | **6 页**：OneTapLogin/Login(密码+图形码)/PhoneLogin(ticket 验证码)/RegisterChoice/Register(双模式)/ForgotPassword；**邮箱登录+绑定邮箱+注销账号（图形码确认）** | **3 页**：login(三模式合一)/register/forget-password；无邮箱登录/绑定、无注销 | **MP 认证体系明显更全**；App 多 429 限流锁定/隐私协议/错误码映射 |
| 专家 | ExpertList(330，**字母索引**) + ExpertDetail(385) + **MyExpert 专家认领**(446) | tabbar/expert + detail(523)；**无认领** | **App 缺专家认领入口**（`/experts/me` 未封装） |
| 品牌 | BrandZone(604) + BrandDetail(427) + **BrandWorkbench 商品工作台**(592) | tabbar/brand + brand/detail(437) | **MP 多工作台**（商品 CRUD/上下架）与品牌成员 |
| 搜索 | `user/search/SearchByTag.vue`(636)：**按标签 AND/OR 搜索**；全局搜索有**双源历史/联想/结果芯片/3 Tab 角标** | search/index(287) + results(813)：关键词建议+三 Tab 结果 | 产品定位不同：标签检索 vs 关键词检索；App 无联想/无服务端历史 |
| 通知 | Notifications(345)+NotificationDetail(386，**详情页 404 回退**) | notifications/index(565，**30s 轮询+全部已读+点击跳 LiveView**；另有未注册孤儿页) | 各有所长 |
| 观看历史 | ViewHistory(447)：预告/直播/回放三 Tab + 进度 | watch-history：dayjs 分组+左滑删除 | 交互维度不同 |
| 设置/账号安全 | 5 页含注销（708 行 AccountSecurity） | 4 页含隐私政策；**邮箱绑定死链**（"开发中"） | MP 多注销流程 |
| 直播管理（我的） | 无独立（并入 admin RoomList） | `live-manage/` 四件套（list/create/edit/detail） | **App 独有** |
| 通知推送管理 | ❌ 无 | admin/notification-push | **App 独有** |

管理端 13 模块详细对比（守卫/分页/弹窗/批量操作等）见 `docs/小程序端与App端管理端页面对比报告.md`，不重复。

---

## 四、各自优势

### 4.1 小程序端优势

1. **请求层最成熟**（`utils/request.ts` 811 行）：`cleanQueryParams` 防 undefined 序列化、**业务码 `code!==200` 统一校验**、`acceptCodes` 业务空态（未绑定专家 2004）、404 连通性诊断、双网关**自动路由**、内容安全错误码人话化（2004/2005）
2. **认证体系完整**：邮箱登录/绑定邮箱/注销账号（图形验证码三重确认）/`useOtpTicket` 组合式函数三处复用/图形验证码覆盖全部敏感操作
3. **用户侧能力更全**：专家认领（`/experts/me`）、品牌商品+成员+工作台、我的直播间（`/users/me/rooms`）、房间/场次统计、场次开始/结束、留言单删、分类图标上传、通知详情 404 回退、媒体下载服务、批量导入
4. **归一化工具层**：`userNormalize`（user_id/uuid/public_id 统一映射）、`roomMessageNormalize`、`resolveAvatarUrl/ResolveCoverUrl/resolveBrandLogoUrl` 兜底函数族 + broken 标记防死循环
5. **Banner3D 3D 轮播**：景深效果成熟（触摸暂停/8 秒恢复/侧卡点击切中）
6. **性能优化**：分包 + 首页 preloadRule 预下载
7. 播放器条件编译（MP-WEIXIN live-player vs video）

### 4.2 App 端优势

1. **Token 自动刷新**（`request.ts:134-167` 过期前 5 分钟提前刷新，防死循环）——MP 只有 401 跳登录
2. **图片链路针对 APP 平台深度适配**：ProxyImage 外链下载缓存 7 天、`imageProxy.ts` 的 Android `file://` 路径转换（plus.io.convertLocalFileSystemURL）、IPv4 保持 http、APP 硬编码兜底域名
3. **统一工程基建**：`useAdminGuard`（9 管理页全接入 vs MP 4 页裸奔）、`useSwiperTabs` 双向联动、共享 `ModalDialog`、`usePageLayout`（rpx2px 等）
4. **状态管理模式成熟**：Set + loaded 防重复 + RequestLock 防并发、PollingManager 30s 轮询、收藏/关注的乐观更新与错误码宽容（4001/4002/500 均视为成功）
5. **管理端能力反超**：通知推送管理、用户批量封禁/批量关开播、角色快速切换 popup、未映射专家双通道、留言时间筛选+批量删除、焦点图有效期、标签/品牌启停开关
6. **交互现代化**：上拉加载+下拉刷新（MP 全用分页器）、骨架屏、swiperKey 机制规避 Android swiper 重建 bug
7. **安全细节**：`isUrlSafe` 防 XSS 跳转黑名单、429 限流 60s 锁定、隐私协议强制勾选、422 错误 detail 提取

---

## 五、可采纳清单（App 端 ← 小程序端，按价值排序）

| # | 采纳项 | 小程序出处 | App 落地 | 优先级 |
|---|--------|-----------|---------|:---:|
| 1 | **业务码校验**：2xx 后检查 `code!==200` 再 resolve（App 当前直接 resolve，后端报业务错误时前端静默成功） | request.ts:642-648 | utils/request.ts | 🔴 高 |
| 2 | `cleanQueryParams` 参数清洗（防 `"undefined"` 序列化） | request.ts:46-58 | utils/request.ts | 🔴 高 |
| 3 | `acceptCodes` 业务空态机制（如专家未绑定 2004 优雅降级） | request.ts:207-211 | utils/request.ts | 🔴 高 |
| 4 | 认证补齐：`loginByEmail` + 绑定邮箱 + **注销账号**（图形码确认） | auth.ts:59 / user.ts:132 / AccountSecurity.vue:348 | auth 域 | 🟡 中 |
| 5 | `useOtpTicket` 组合式函数（发码→verify→ticket 消费） | composables/useOtpTicket.ts | composables | 🟡 中 |
| 6 | 专家认领「我的专家」页 + `/experts/me` API | MyExpert.vue(446) | 新页面 | 🟡 中 |
| 7 | 首页焦点图 **3D 卡片效果**（getCardClass 缩放/变暗/层级 + 触摸暂停 8s 恢复）——注意保留 swiperKey 兼容 | Banner3D.vue:170-276 | FeaturedCarousel.vue | 🟡 中 |
| 8 | 内容安全管理页（规则分组编辑/日志+昵称补全） | ContentSafety 三件套 | admin/content-safety | 🟡 中（P2） |
| 9 | 品牌成员/品牌商品/品牌工作台（**需先产品确认**） | BrandMemberManager/BrandProductList/BrandWorkbench | 新页面 | 🟢 低（P3） |
| 10 | 房间统计、场次统计/开始/结束、`/rooms/{id}/is-favorited`、留言单删 API 封装 | room.ts:108-160 / session.ts:42-67 | api 层 | 🟢 低 |
| 11 | `getMyRooms` 我的直播间（当前 App 端 client-side 过滤，后端现已支持） | room.ts:144-158 | api/room.ts | 🟢 低 |
| 12 | 通知详情页（404 回退 + 类型标签 + 自动已读） | NotificationDetail.vue | notifications 域 | 🟢 低 |
| 13 | 404 连通性诊断（可在 debug 页复用，不建议生产默认开启） | request.ts:379-467 | 诊断工具 | 🟢 低 |
| 14 | 专家列表字母索引（A-Z 分组定位，配合现有 pinyin 排序） | ExpertList.vue | tabbar/expert | 🟢 低 |
| 15 | 留言板真实化：分页/乐观追加/长按删除复制/`我`标识/D3 注销占位 | LiveView.vue + MessageItem.vue + roomMessageNormalize.ts | ChatTab.vue | 🔴 高 |
| 16 | `?redirect=` 登录深链修复（守卫传参但 login 不读） | useAuthRedirect.ts:28-51 | login.vue | 🔴 高 |
| 17 | 内容安全文案映射（2004/2005 人话化） | utils/contentSafety.ts:46-117 | utils | 🟡 中 |
| 18 | 直播三分支创建（移动端）——先做 H5 边界决策 | CreateLive.vue:96-124 | live-manage/create.vue | 🟡 中 |
| 19 | RBAC 收紧：仅 SUPERADMIN 改角色 + 禁改 SUPERADMIN | types/adminUser.ts:159-161 | users/index.vue | 🟢 低 |
| 20 | 服务端同步用户偏好（置顶分类/视图模式） | store/preferences.ts | store | 🟢 低 |
| 21 | TargetSelector（按名选 featured 目标，免 UUID 手输） | components/TargetSelector.vue | featured/index.vue | 🟡 中 |
| 22 | 专家↔账号绑定 + 用户能力聚合 | ExpertAdminList + userCapabilityLookup | admin | 🟡 中 |

### 5.1 可回灌清单（小程序端 ← App 端）

| # | 采纳项 | 出处 | 说明 |
|---|--------|------|------|
| 1 | 管理页统一守卫 | `useAdminGuard.ts` | MP 4 个管理页无守卫可直开 |
| 2 | 通知推送管理 | admin/notification-push | MP 完全缺失 |
| 3 | 用户批量封禁/关开播 + 角色快速切换 | users/index.vue | MP 仅单条 |
| 4 | 未映射专家双通道 | expert-list | MP 仅已映射 |
| 5 | 留言时间筛选 + 批量删除 | messages/index.vue | MP 仅房间维度 |
| 6 | 焦点图有效期 | featured L190 | MP 仅 sort/is_active |
| 7 | 标签/品牌启停开关 | tags/brands toggleActive | MP 仅增删改 |
| 8 | 上拉加载 + 下拉刷新 | App 各列表 | MP 全用分页器 |
| 9 | Token 自动刷新 | request.ts:134-167 | MP 仅 401 跳登录 |
| 10 | ProxyImage 图片代理 | components/common/ProxyImage.vue | MP 微信自有缓存，可参考 |

---

## 六、主流规范符合度评估

### 6.1 小程序端

| 维度 | 评价 | 问题 |
|------|:----:|------|
| 页面结构 | ⚠️ | **LiveView 4145 行 / CreateLive 2509 行**巨型页面，严重违背单文件可维护性规范 |
| 类型契约 | ❌ | **Room/Expert/UserInfo 仍为旧 camelCase 模型**（coverImage/expertId/user_id/phone），与后端 snake_case JSON 脱节，页面取值大量 undefined，靠防御式解析兜底（normalizeSessionExpertItems 兼容近 10 种字段形态）——这是跨端数据对不上的根因 |
| 分页交互 | ⚠️ | 全站传统分页器（上一页/下一页），落后于主流上拉加载；BrandProductList 甚至双发 size+page_size |
| 守卫 | ⚠️ | 4 个管理页无守卫可直开（CategoryList/FeaturedContentList/TagList/ContentSafety*） |
| 代码卫生 | ⚠️ | Home.vue 大量 `console.log('🔍 API响应')`、LiveView console.warn 残留；CollectionList 与 SubscriptionList 结构几乎一致未复用 |
| 请求层/认证/空态三态 | ✅ | 完成度最高，符合主流规范 |
| 安全 | ✅ | 图形验证码全链路、注销二次确认 |
| 触控热区 | ⚠️ | 管理页多处 24–32px 低于 44px |

### 6.2 App 端

| 维度 | 评价 | 问题 |
|------|:----:|------|
| 工程基建 | ✅ | 守卫/弹窗/Tab/布局全部 composable + 共享组件，符合现代 uni-app 规范 |
| 页面结构 | ✅ | 首页组件化（5 子组件），LiveView 2834 行虽大但有 API 模式开关与注释分段 |
| 完成度 | ❌ | **「我的直播」Tab 纯占位**、LiveView 聊天/问答/资料 Mock、downloadContent 占位 toast、邮箱绑定死链——未完成功能直接暴露在线上 |
| 日志/隐私 | ⚠️ | request.ts 每请求打印 token 预览 + 完整响应头，**生产构建未分级**；`ngrok-skip-browser-warning` 遗留 header（request.ts:122）；生产环境 HTTP 仅警告不拦截 |
| 安全 | ⚠️ | `goToUserService` 小程序 appId 为占位字符串硬编码（auth.ts:619） |
| 样式 | ⚠️ | LiveView 旧样式（#333/#666/#999 硬编码）与 token 体系双轨并存；`shared/AppButton` 硬编码 `#409eff`（Element 蓝）与 teal `--color-primary` 冲突 |
| 冗余 | ⚠️ | 收藏/关注在 initializeAuth 与 loginWithTokens 中重复加载；AGENTS.md 提到的 `utils/navigation.ts` 实际不存在；**2 个通知页（其一未注册孤儿）** |
| 认证 | ⚠️ | 相比 MP 缺邮箱登录/注销；但 429 锁定/隐私协议/错误码映射更合规 |
| 暗黑模式 | ❌ | 无任何暗黑 palette（MP 至少 theme.scss 有 dark 块） |

### 6.3 两端共同缺失

弹幕模块（两端直播页均无，医疗直播重要功能）、统一埋点体系、统一错误上报、深色模式 palette、UI token 单一来源。

---

## 七、实现冲突清单（18 项，已源码验证）⭐ 最关键的发现

> **关键判断**：冲突 **#2/#8 的注释直接写明"后端 OpenAPI 实为 X，走文档路径会 404"**——说明小程序端是与后端同学最近联调对齐的版本，后端"优化"后契约大概率以小程序端为准。App 端这些调用在后端同步后必然报错。建议：与后端同学开一次契约对齐会，以小程序端为基准逐项确认最终路径/方法/字段，App 端修正（预计纯 api 层改动，0.5d）。

| # | 业务 | App 端 | 小程序端 | 谁对（依据） |
|:--:|------|--------|---------|:---:|
| 1 | 更新房间 | **PUT** /rooms/{id}（room.ts:54，注释"uni.request 不支持 PATCH 用 PUT"；**App 内部 store/room.ts:198 却用 PATCH**） | **PATCH** /rooms/{id}（room.ts:71） | 需后端确认；**App 先内部统一** |
| 2 | 场次详情/更新/删除 | /sessions/{id}（session.ts:19-49） | **/sessions/sessions/{id}**（config/api.ts:128-136，注释：后端 OpenAPI 实为此路径） | **小程序**（注释自证对齐最新 OpenAPI） |
| 3 | 绑定手机 | POST /me/bind-phone（auth.ts:185） | POST /me/phone（user.ts:91） | 需后端确认 |
| 4 | 注销账号 | DELETE /me 无 body | DELETE /me 带 body（含 captcha） | 需后端确认 |
| 5 | 场次标签 | /sessions/{id}/tags（sessionTags.ts） | 三套并存：/content/sessions/{id}/tags 与 /admin/sessions/{id}/tags（**MP 内部自相矛盾**） | 需统一 |
| 6 | 按标签搜索 | GET /sessions/search（page/size） | GET /content/tags/search/sessions（page/page_size） | 需后端确认 |
| 7 | 取消订阅 | DELETE /users/me/subscriptions?target_type=&target_id=（query 参数化） | DELETE /users/me/subscriptions/{roomId}（路径化） | 需后端确认 |
| 8 | 焦点图上传字段 | multipart 字段 `file`（featured.ts:69） | 字段 `image`（featuredContent.ts:108，注释"后端期望字段名为 image"） | **小程序** |
| 9 | 更新分类 | **PUT** /admin/categories/{id} | **PATCH** /admin/categories/{id} | 需后端确认 |
| 10 | 品牌房间列表 | GET /brands/{id}/rooms（公开） | GET **/admin**/brands/{id}/rooms（需管理员） | **App**（公开语义更合理） |
| 11 | 记录观看 | POST /users/me/watch-history | POST /sessions/{id}/watch | 需后端确认 |
| 12 | 分类内容 | GET /categories/{id}/content | GET /content/categories/{id}/content | 需后端确认 |
| 13 | 管理端分类分页 | page/size | page_size→size + include_inactive + q | 需后端确认 |
| 14 | 焦点图返回形状 | 裸数组 FeaturedContent[] | { items: [...] } | 需后端确认 |
| 15 | **双分类体系** | categories + expert_departments 双轨 | 单轨 categories 即科室 | **待确认，暂不动作** |
| 16 | UserInfo 类型 | uuid/phone_number/role=REGULAR\|ADMIN\|SUPERADMIN | user_id/phone/role=user\|admin\|expert | 小程序与 JWT payload 一致 |
| 17 | Room/Expert 类型 | snake_case 镜像后端 | camelCase 旧模型（脱节） | **App 类型对，但 MP 有 normalize 层** |
| 18 | 网关路由 | 手动 authUrl/usersUrl | 自动 shouldUseUsersGateway 前缀匹配 | 需与后端确认 users 网关路由规则 |

**补充（v2.0 核实追加，用户报告未含）**：

| # | 冲突 | App 端 | 小程序端 | 影响 |
|:--:|------|--------|---------|------|
| 19 | **留言/房间 Tab 契约** | 读 `extra.user_avatar/user_display_name`；Tab key `intro/experts/brands/chat` | 读 `user.{nickname,avatar_url}` 快照 + D3 注销占位；Tab key `intro/expert_intro/brand_intro/message`（自动注入） | **高**：同一后端喂两端，换渲染器不换归一化即错名/错 Tab |
| 20 | **首页信息流排序/分页** | `sort='heat:desc'` + page 15+85 | `sort='created_at:desc'` + page 10 + 客户端过滤 | **高**：同一 `/homepage/rooms` 两端排序/覆盖不同 |
| 21 | **焦点图目标词汇（App 内部不自洽）** | 表单仅 `[null,room,topic,external]`（featured/index.vue:250），运行时却跳 `session` | 表单 5 类含 expert/brand | **高**：App 管理 UI 造不出自己运行时能跳的 banner |
| 22 | **验证码字段名 / one-tap 协议** | 只读 `image_base64`；`OneTapLoginRequest` 无 `agreed_to_terms` | 优先 `captcha_image` 回退 base64；必发 `agreed_to_terms` | **中**：后端字段调整/合规校验会只挂一端 |
| 23 | **AppButton 品牌色 + token 三命名空间** | `#409eff` 蓝按钮 + `--color-/--home-/$color-` 三套 | 单 `--color-*` teal | **中**：蓝按钮混在 teal 里 |
| 24 | **isAdmin 大小写** | 仅大写 `ADMIN/SUPERADMIN` | toLowerCase 接受小写 | **中**：小写 role 隐藏 App 管理菜单 |
| 25 | **账号注销/改密载荷** | `deleteUserAccount()` 无验证码；passwordless 缺 current_password | `deleteMyAccount({captcha_id,captcha_solution})`；必带 current_password | **高**：验证码强制后 App 注销必挂 |
| 26 | **通知枚举语义** | `system/subscription/interaction` | `live_start/live_end/follow/...` | **高**：同一通知两端 Tab 归类不同 |
| 27 | **会话状态语义** | `finished/ended/archived/ready→回放` | + `replay/playback`→回放，未来 start_time→预告 | **中**：两端状态分类不一致 |
| 28 | **观看历史载荷** | `{sessionId, progress, extra:{...}}` | `{session_id, progress, session_type, watched_at}` | **中**：跨端续播断裂 |
| 29 | **房间字段** | 只写 `description`(500) | 写 `summary`(2000) 派生 | **中**：同内容不同字段 |
| 30 | **认证 token 存储键** | `jwt_token/refresh_token` | `STORAGE_KEYS.ACCESS_TOKEN` | **低**（共享登录桥则高） |
| 31 | **超时默认值** | 5s（request.ts:58） | 10s | **中**：慢接口 App 先超时 |

---

## 八、需要优化的部分（App 端行动路线，按优先级）

### P0（后端同步前必做，否则联调爆炸）

| # | 行动 | 说明 | 工作量 |
|:-:|------|------|:-----:|
| 1 | **契约对齐会** | 与后端同学过 18+13 项冲突（第七、八章），以小程序端为基准逐项确认最终路径/方法/字段，输出契约表 | 0.5d |
| 2 | **App 端 API 层修正** | 按契约表修正 31 项冲突涉及的 api 层（含 PUT→PATCH、`/sessions/sessions/` 双段路径、绑定手机、订阅取消、观看历史等） | 0.5d |
| 3 | **请求层补业务码校验 + 参数清洗** | 移植 MP `acceptCodes` + `cleanQueryParams` + code!==200 校验（消除静默成功与 undefined 序列化 bug） | 0.5d |
| 4 | **关闭生产 Mock** | `.env.production:27` `VITE_USE_MOCK=true` → false（注释自相矛盾，必须修） | 5min |
| 5 | **确认双分类体系口径** | `categories` vs `expert-departments`，消除重复建设 | 0.5d |

### P1（功能完整性）

| # | 行动 | 说明 | 工作量 |
|:-:|------|------|:-----:|
| 6 | 我的直播 Tab 接入真实 `live-manage` 列表 | 51 行占位页 → 复用 list.vue（`manage` 模式） | 0.5d |
| 7 | LiveView 聊天/问答/资料从 Mock 切真实 API | 移植 MP 留言板流程 + 归一化 + 长按治理 + 2004/2005 映射 | 1-1.5d |
| 8 | `?redirect=` 登录深链修复 | login.vue 补 onLoad 读 query + finishAuth 智能导航 | 0.25d |
| 9 | 认证补齐：邮箱登录、绑定邮箱、注销账号 | 移植 MP 三套件 + `useOtpTicket` | 1d |
| 10 | 焦点图 3D 对齐 + expert/brand 跳转 | 移植 Banner3D `getCardClass`（保留 swiperKey）；表单补 expert/brand/session 目标类型 | 0.5d |
| 11 | 管理端三模块接入 | 品牌成员/品牌商品（P3 待产品确认）、内容安全（P2，先确认字段契约 R3） | 1.5-2d |
| 12 | 专家认领「我的专家」页 | `/experts/me` API + 新页面 | 0.5d |
| 13 | 通知详情页 + 孤儿页清理 | 补 NotificationDetail；删除/合并 `tabbar/my/notifications/index` | 0.5d |

### P2（工程卫生）

| # | 行动 | 说明 |
|:-:|------|------|
| 14 | 日志分级 | dev 才打印，token 预览移除；删 `ngrok-skip-browser-warning` header |
| 15 | Mock 开关收敛 | `VITE_USE_MOCK` 全局统一控制，LiveView 的 `LIVEVIEW_API_MODE` 随契约对齐移除 |
| 16 | 品牌色统一 | `shared/AppButton` `#409eff` → `var(--color-primary)`；token 三命名空间收敛为单一来源 |
| 17 | 孤儿/冗余清理 | `utils/navigation.ts` 不存在（AGENTS.md 过期）、收藏/关注重复加载、空行格式化 |
| 18 | `room-tabs` 入口补全 | `my/index.vue` adminRoutes 加 room-tabs |
| 19 | 触控热区补齐 | AuthorityStrip 关注星 28px、AppButton 小按钮 → ≥44px |

---

## 九、风险与应对

| # | 风险 | 概率 | 影响 | 应对 |
|:-:|------|:----:|:----:|------|
| R1 | **契约冲突未对齐就接后端**（31 项） | 高 | 高 | P0-1/2 强制；契约表产出后逐项修 |
| R2 | **生产 Mock 假象**：`VITE_USE_MOCK=true` + LiveView 聊天 Mock → "看着正常其实没接后端" | 高 | 高 | P0-4 立即关；联调前全链路真实验证 |
| R3 | **内容安全后端字段仍不一致**（schema/DDL） | 高 | 高 | 开工前先对齐字段契约，预留联调窗口 |
| R4 | **"照抄 MP"覆盖 App 工程优势**（分层/范式/守卫） | 中 | 高 | 坚持"功能借鉴 MP、范式保持 App"；新建页按 App admin 范式 |
| R5 | **三套管理端并存失控**（移动 uni admin + H5 element-plus + MP 参考） | 中 | 中 | H5/移动/MP 边界文档化；能力收敛单一归属 |
| R6 | **焦点图 3D 破坏 Android swiperKey 兼容** | 低 | 中 | 保留 swiperKey；真机回归 |
| R7 | **App 内部 PUT/PATCH 不一致** → 严格 REST 后端拒一个 | 中 | 中 | P0-2 内部统一 PATCH（删误导注释） |
| R8 | **P3 品牌模块产品决策未定** | 中 | 中 | 接口已就绪，先做不做需产品确认 |
| R9 | **MP 类型 camelCase 脱节**（#17）若合并共享代码 | 中 | 中 | 以 App snake_case 为准 + MP normalize 层 |

---

## 十、行动路线图

```
阶段 0（0.5d）  契约对齐：与后端同学过 18+13 项冲突，输出最终契约表（以小程序端为基准）
阶段 1（1d）    P0 修正：App api 层按契约修正 + 业务码校验 + 参数清洗 + 关生产 Mock
阶段 2（2-3d）  P1 功能：我的直播接入 + LiveView 真实化 + 认证补齐 + 焦点图 3D + ?redirect=
阶段 3（1.5-2d）管理端三模块：品牌成员/商品（产品确认后）+ 内容安全（字段确认后）
阶段 4（1d）    P2 卫生：日志分级、Mock 收敛、品牌色、孤儿清理、入口补全
并行（0.5d）    专家认领 + 通知详情 + 留言真实化
```

**验收标准**：契约表 31 项逐项确认并修正；生产 Mock 关闭后全链路真实验证；新页面过 `pnpm lint` + `pnpm test:run`；Android 真机回归（swiperKey/ProxyImage）；两端页面功能矩阵对齐。

---

## 十一、工作区现状校准与功能级实施梳理（v2.1 新增）

### 11.1 现状校准（对 v2.0 及之前过时结论的修正）

| # | 原结论（v2.0 前） | 现状（v2.1 源码核实） | 影响 |
|:-:|-------------------|---------------------|------|
| 1 | LiveView 留言为本地 Mock（ChatTab 未接 API） | **ChatTab.vue 已接真实 API**（`getRoomMessages`/`sendRoomMessage`、5s 轮询、分页、XSS 清洗） | 互动真实化已完成**留言部分**；剩余问答/资料仍 Mock（`LIVEVIEW_API_MODE`，LiveView.vue:846-874） |
| 2 | App 搜索无服务端历史 | **搜索已双源**（`store/search.ts:64-76` 本地记录 + `getServerSearchHistory` 服务端历史合并） | 采纳清单 #2/#21 相关表述作废 |
| 3 | `admin/dashboard` 为管理首页 | **空目录残留**（无任何文件，页面树内无注册） | 新增 P2 清理项 + 排查入口死链 |
| 4 | 焦点图表单目标类型与运行时一致 | 表单仅 `[null,room,topic,external]`（featured/index.vue:250），运行时却能跳 session | 维持冲突 #21（UI 与运行时不自洽） |
| 5 | 搜索无联想/无服务端历史 | 联想仍无；服务端历史已有 | 联想缺失维持原结论 |

### 11.2 功能级实施梳理（"实施后 App 端长什么样"总览）

**现有页面调整（10 处）**：

| # | 位置 | 调整 | 优先级 |
|:-:|------|------|:---:|
| 1 | `utils/request.ts` | 补业务码 `code!==200` 校验 + `cleanQueryParams` + `acceptCodes` | P0 |
| 2 | `src/api/` | 按契约表修正 31 项冲突（PUT→PATCH、`/sessions/sessions/`、绑定手机、订阅取消、观看历史等） | P0 |
| 3 | `.env.production` | `VITE_USE_MOCK=true` → false | P0 |
| 4 | `tabbar/my-live/index.vue` | 51 行占位页 → 复用 live-manage `list.vue`（manage 模式） | P1 |
| 5 | `live/LiveView.vue` | 问答/资料从 Mock 切真实 API（留言已完成） | P1 |
| 6 | `auth/login.vue` | 补 `?redirect=` 深链读取与智能导航 | P1 |
| 7 | 认证域 | 邮箱登录/绑定邮箱/注销账号 + `useOtpTicket` | P1 |
| 8 | `admin/featured` | 目标类型补 expert/brand/session + 3D 卡片（保留 swiperKey） | P1 |
| 9 | `tabbar/my/index.vue` adminRoutes | 补 room-tabs 菜单入口 | P2 |
| 10 | 通知域 | 孤儿页清理 + 详情页补齐 | P1 |

**新增页面（7 个）**：

| # | 页面 | 优先级 |
|:-:|------|:---:|
| 1 | 管理端·内容安全（规则/日志/昵称补全，先对齐字段契约 R3） | P2 |
| 2 | 管理端·品牌成员 | P3（待产品确认） |
| 3 | 管理端·品牌商品 | P3（待产品确认） |
| 4 | 专家认领「我的专家」页（`/experts/me`） | P1 |
| 5 | 通知详情页（404 回退 + 自动已读） | P1 |
| 6 | 移动端开直播分支（先做 H5 边界决策） | P1 |
| 7 | 品牌工作台（商品 CRUD/上下架） | P3（待产品确认） |

**明确不采纳（防"照抄 MP"覆盖 App 工程优势，见 R4）**：

| 不采纳项 | 原因 |
|----------|------|
| MP 全站分页器（上一页/下一页） | App 上拉加载更主流，已采纳清单不包含 |
| MP camelCase 旧类型模型 | 与后端 snake_case 脱节是 MP 自身缺陷，App 类型对（冲突 #17） |
| MP 自定义 tabBar | App 保持原生，避免平台差异 |
| MP 巨型单文件模式（LiveView 4145 行） | 违背规范，不模仿 |
| 弹幕/深色模式 | 两端均缺，MP 无现成可抄 |

**工作量汇总**：P0 ≈1.5d（含契约对齐会 0.5d）+ P1 ≈4-5d + P2 ≈1d + P3 待产品确认。

---

## 十二、变更记录

| 版本 | 日期 | 变更内容 |
|:----:|:----:|---------|
| v1.0 | 2026-08-09 | 初版：管理端 13 模块、用户侧 10 域、基建层 10 项对比；冲突清单 12 项 |
| v1.1 | 2026-08-09 | 10 子代理交叉验证：补 H5 桌面管理端、?redirect= 断链、PUT/PATCH 内部冲突、孤儿通知页；冲突扩至 C18 |
| v2.0 | 2026-08-09 | **合并用户实测报告**（18 项契约冲突 + VITE_USE_MOCK 生产开启 + 我的直播占位 + MP 页面规模等），全部关键声明**源码逐一复核**；修正 1 处用户报告错误（featured 目标类型）；冲突清单扩至 31 项；行动路线重排为 P0/P1/P2 + 风险表 |
| v2.1 | 2026-08-09 | **工作区现状再校准**：ChatTab 留言已接真实 API、搜索已双源、admin/dashboard 空目录（修正 3 处过时结论）；新增「零」章文档体系与使用指南（三文档区别与职责）；新增功能级实施梳理（现有页面调整 10 处/新增页面 7 个/不采纳清单/工作量汇总） |
| v2.2 | 2026-08-12 | **焦点图域实施闭环**：新增「十三」章（5 阶段落地清单、6 项契约实锤、遗留跟踪 5 项）；生产 Mock 已关闭（R2 消除）；修正/实锤：公开接口裸数组（#14 App 本就正确）、上传字段 image（#8）、target_type 无 expert、公开 /brands/{id} 缺失（新发现） |
| v2.3 | 2026-08-12 | **焦点图需求调整**：跳转目标类型精简为 `[null, room, brand, external]`（移除 session/topic——一房一场次模型下 room 与 session 语义一致，运行时经 LiveView roomId 解析场次；App 无专题落地页故移除 topic）；关联交互改为弹出式列表（半屏弹层默认加载 20 条 + 搜索过滤 + 点行关联，无需手输 ID）；「十三」章同步更新 |
