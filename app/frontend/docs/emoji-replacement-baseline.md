# Emoji 替换基线文档（阶段 0 产出）

> 日期：2026-08-05
> 状态：阶段 0（准备与基线）完成
> 范围：用户可见 emoji 处理项目（App 端 + 共享组件；H5 页不在实施范围）

## 1. 目标与产出

| 产出 | 状态 |
|---|---|
| 用户可见 emoji 现状冻结清单（48 处） | ✅ 本文档 §2 |
| 图标库盘点（iconfont / uni-icons 覆盖对照） | ✅ 本文档 §3 |
| 测试基线 | ✅ 本文档 §4 |
| Lint 基线 | ✅ 本文档 §4 |
| 构建基线（h5 / mp-weixin） | ✅ 本文档 §4 |
| uni-icons 工具链验证（组件级） | ✅ 本文档 §5（vitest 3/3 通过） |
| 视觉基线（页面截图） | ⏳ 人工步骤：§6 清单（CLI 无法自动化） |
| 既有问题清单 | ✅ 本文档 §7 |

## 2. 用户可见 emoji 现状清单（48 行 / 24 文件）

### A. 通知类
| 文件:行 | Emoji | 含义 | 建议替换 |
|---|---|---|---|
| `src/pages/app/notifications/index.vue:37` | 🔔 | 空状态 | uni-icons notification（阶段2） |
| `src/pages/app/notifications/index.vue:258-262` | ⚙️📺💬🔔 | 通知类型 iconMap | iconfont setting/video/message + uni-icons notification（阶段1+2） |
| `src/pages/app/tabbar/my/notifications/index.vue:26` | 🔔 | 空状态 | uni-icons notification（阶段2） |
| `src/pages/app/tabbar/my/notifications/index.vue:111-113` | 💬👍👤 | Tab 图标 | iconfont message/like-filled/my（阶段1） |
| `src/pages/app/tabbar/my/notifications/index.vue:259-263` | 📢🔔💬 | 列表 iconMap | uni-icons notification + iconfont message（阶段2） |
| `src/pages/app/tabbar/my/subscriptions/index.vue:27` | 🔔 | 空状态 | uni-icons notification（阶段2） |
| `src/pages/app/tabbar/my/watch-history/index.vue:5` | 📺 | 空状态 | iconfont video（阶段1） |

### B. 直播管理
| 文件:行 | Emoji | 含义 | 建议替换 |
|---|---|---|---|
| `live-manage/detail.vue:55` | 🔒🌍 | 私密/公开徽标 | 阶段3决策（uni-icons 无 globe，需新增或文字化） |
| `live-manage/detail.vue:120` | 🌐 | 官网链接 | uni-icons link 或删除（阶段2/1） |
| `live-manage/detail.vue:163` | 📅 | 场次时间 | uni-icons calendar（阶段2） |
| `live-manage/detail.vue:164` | 🎥 | video_id | iconfont video（阶段1） |
| `live-manage/detail.vue:166` | 🎬 | 查看回放 | iconfont play（阶段1） |
| `live-manage/edit.vue:106` | 🗑 | 删除图标 | iconfont delete（阶段1） |
| `live-manage/edit.vue:176` | 🔒🔓 | 私密开关 | 阶段3决策 |
| `live-manage/edit.vue:271` | 💡 | 提示 | 删除（阶段1） |
| `live-manage/create.vue:270` | 📂 | 分类图标兜底（后端 cat.icon） | uni-icons folder-add（阶段2，注意数据耦合） |
| `live-manage/create.vue:314` | 💡 | 提示 | 删除（阶段1） |
| `live-manage/list.vue:99` | 🔒 | 私密标签 | 阶段3决策 |
| `app/live/LiveView.vue:229` | 💡 | 演示模式提示 | 删除（阶段1） |

### C. 管理后台
| 文件:行 | Emoji | 含义 | 建议替换 |
|---|---|---|---|
| `admin/departments/index.vue:40` | 🔍 | 搜索框 | iconfont search（阶段1） |
| `admin/departments/index.vue:73` | ⚠️ | 空状态 | iconfont error（阶段1） |
| `admin/departments/index.vue:81` | 📂 | 空状态 | uni-icons folder-add（阶段2） |
| `admin/departments/index.vue:92` | ▶▼ | 展开箭头 | iconfont arrow-right/down（阶段1） |
| `admin/expert-list/index.vue:28` | 🔍 | 搜索框 | iconfont search（阶段1） |
| `admin/expert-list/index.vue:73` | ⚠️ | 空状态 | iconfont error（阶段1） |
| `admin/expert-list/index.vue:80` | 👤 | 空状态 | iconfont my（阶段1） |
| `admin/featured/index.vue:45` | ⚠️ | 空状态 | iconfont error（阶段1） |
| `admin/featured/index.vue:52` | 🖼 | 空状态 | uni-icons images（阶段2） |
| `admin/users/index.vue:36` | 🔍 | 搜索框 | iconfont search（阶段1） |
| `admin/users/index.vue:81` | ⚠️ | 空状态 | iconfont error（阶段1） |

### D. 通用组件（影响面最大）
| 文件:行 | Emoji | 含义 | 建议替换 |
|---|---|---|---|
| `components/app/CreateLiveDrawer.vue:295` | 📂 | 分类兜底 | uni-icons folder-add（阶段2） |
| `components/app/VideoPlayerApp.vue:55` | 👁️ | 观看人数（cover-view 内） | 阶段3决策（cover-view 不能渲染字体图标） |
| `components/ChatTab.vue:58` | 💬 | 输入框 placeholder | 删除（阶段1） |
| `components/ChatTab-emoji-enhanced.vue` | 全文件 | 表情面板（~200 emoji） | 删除死文件（阶段1，已确认无引用） |
| `components/common/EmptyState.vue:4` | 📭 | 空状态 | 阶段3决策（uni-icons 无 inbox，可用 mail-open 近似） |
| `components/common/ScrollablePickerSheet.vue:22` | 📭 | 空状态 | 同 EmptyState |
| `components/common/ErrorBanner.vue:52-53` | ⚠ℹ✕✓ | 文本符号（非彩色 emoji） | 保留（渲染为单色文本，无跨端问题） |
| `components/shared/ModalDialog.vue:7` | 📺 | 弹窗图标 | iconfont video（阶段1） |
| `components/shared/UserInfoHeader.vue:18` | 👤 | 头像占位 | iconfont my（阶段1） |
| `components/shared/UserInfoHeader.vue:38` | 🔐 | 登录占位 | 阶段3决策（当前 App 端未使用） |

### E. 其他
| 文件:行 | Emoji | 含义 | 建议替换 |
|---|---|---|---|
| `app/auth/login.vue:32` | 📱 | 一键登录装饰 | 删除（阶段1） |
| `app/debug/auth-status.vue` | 🔧✅❌🔄🧪🗑️📋 | 调试页 | **不动**（仅开发者可见） |
| `h5/live/LiveView.vue:200-201` | 🙂⭐ | 表情按钮 | **不在实施范围**（H5 页） |

## 3. 图标库盘点

### 3.1 现有 iconfont（`src/static/fonts/iconfont.css`，80 个类名，可直接复用）
`icon-add, icon-arrow-*, icon-brand, icon-cha, icon-close, icon-delete, icon-download, icon-edit, icon-error, icon-expert, icon-eye, icon-eye-off, icon-eye-slash, icon-heart, icon-history, icon-home, icon-like-filled, icon-like-outline, icon-live, icon-live1, icon-message, icon-more, icon-my, icon-next-room, icon-pause, icon-play, icon-plus, icon-privacy, icon-remove, icon-search, icon-setting, icon-settings, icon-share, icon-shoucang1, icon-star-filled, icon-star-outline, icon-sub-outline, icon-thumbs-up-solid, icon-time, icon-user-check, icon-video, icon-view, icon-yincang, icon-yinsi-copy, icon-md-star-outline 等`

**缺失（emoji 替换需要但 iconfont 没有）**：🔔铃铛、🔒🔓锁、🌍🌐地球、📂文件夹、📭收件箱、📢喇叭、💡灯泡、🖼图片、📅日历、✅❌对错、🔐、📱手机、🧪、📋

### 3.2 uni-icons（`@dcloudio/uni-ui@1.5.12`，161 个 type，自带 uniicons.ttf 字体）
覆盖关键项：`notification`(🔔) `locked`(🔒) `folder-add`(📂) `mail-open`(📭近似) `calendar`(📅) `videocam`(📺🎥🎬) `gear`/`settings`(⚙️) `person`(👤) `trash`(🗑) `search`(🔍) `eye`(👁️) `images`(🖼) `sound`(📢) `chatbubble`(💬) `phone`(📱) `list`(📋) `refresh`(🔄) `weixin`(微信图标) `checkmarkempty`/`checkbox`(✅近似) `close`/`clear`(❌) `link`(🌐近似)

**uni-icons 也没有的**：💡灯泡、🌍globe（有 `link`、`map` 可近似）、👍点赞（有 `hand-up`，但 iconfont 已有 icon-like-filled）、🔓unlocked、📭收件箱（mail-open 近似）

### 3.3 缺失项处理结论（供阶段 3 决策）
- 🔒🔓：新增 iconfont 图标（需重新生成字体，外部依赖）或文字化
- 💡：直接删除（提示性文字，无图标必要）
- 📭：mail-open 近似（uni-icons）或新增 iconfont
- 🌍：link/map 近似（uni-icons）或文字化

## 4. 基线数据（阶段 0 实测）

| 项目 | 结果 | 说明 |
|---|---|---|
| `pnpm test:run` | **17 文件：1 通过 / 16 失败**；53 用例：43 通过 / 10 失败 | 失败均为既有陈旧测试：引用已删除的旧路径（`src/components/AppButton.vue`、`src/pages/room/RoomDetail.vue` 等）或断言与 store 新行为不匹配；**与本任务无关** |
| `npx eslint src` | **158 问题：29 errors / 129 warnings** | 全部为既有问题（未使用变量、逃逸字符、解析错误等）；注意 `live-manage/detail.vue:424`、`list.vue:339` 有 Parsing error（当前处于无法解析状态） |
| `pnpm build:h5` | ✅ 通过 | 当前主要构建目标 |
| `pnpm build:mp-weixin` | ❌ **失败（既有）** | `src/pages/h5/room/RoomList.vue:62` 使用 Element Plus `v-loading` 指令，非 H5 平台未注册该指令 → vite:vue 报 unknown directive。已通过对照实验（移除阶段0改动后复现相同错误）确认与本任务无关 |

## 5. uni-icons 工具链验证记录

| 项 | 结果 |
|---|---|
| easycom 配置 | ✅ `src/pages.json:375-381` 已含 `"^uni-(.*)": "@dcloudio/uni-ui/lib/uni-$1/uni-$1.vue"` |
| 组件与字体存在 | ✅ `node_modules/@dcloudio/uni-ui/lib/uni-icons/`（uni-icons.vue + uniicons.ttf 自带字体） |
| 组件级渲染测试 | ✅ 新增 `tests/uni-icons.spec.ts`，3/3 通过：类名 `uniui-{type}`、style 注入、19 个计划使用的 type 均有字符、未知 type 不抛错 |
| 测试环境适配 | ✅ `vitest.setup.ts` 新增 weex mock（uni-icons 的 APP-NVUE 条件编译块在测试环境未被剥离时引用 weex） |
| mp-weixin 全量构建验证 | ⚠️ **被既有 v-loading 问题阻塞**（见 §4），无法完成；组件级验证 + easycom 确认已足以支撑阶段 2 引入，真机渲染留待阶段 2 验收 |

## 6. 视觉基线（人工截图清单）

以下页面含用户可见 emoji，请在各端（H5 dev / 微信开发者工具 / App 模拟器）截图存档作为阶段 1-3 的对照：
1. `pages/app/notifications/index`（含空状态与列表图标）
2. `pages/app/tabbar/my/notifications`
3. `pages/app/tabbar/my/subscriptions`（空状态）
4. `pages/app/tabbar/my/watch-history`（空状态）
5. `pages/app/live-manage/detail` / `edit` / `create` / `list`
6. `pages/app/live/LiveView`（演示模式提示 + 聊天输入框）
7. `pages/app/admin/departments` / `expert-list` / `featured` / `users`
8. `pages/app/auth/login`（一键登录）
9. 通用组件：CreateLiveDrawer（分类选择）、VideoPlayerApp（观看人数角标）、专家/品牌详情页空状态、ModalDialog

## 7. 阶段 0 新发现（既有问题，供后续阶段注意）

1. **`icon-wechat` / `icon-apple` 未定义**：`src/pages/app/tabbar/my/account-security/index.vue:53,63` 使用了这两个类，但 `iconfont.css` 无对应定义 → 微信/苹果第三方登录图标当前渲染为空。可后续用 uni-icons `weixin` 替换（阶段 3 可选补充项，不在本任务必做范围）。
2. **mp-weixin 构建被 h5 页面阻断**：`src/pages/h5/room/RoomList.vue:62` 的 `v-loading`。按 AGENTS.md，h5 页面不在实施范围；阶段 2-4 的"构建验证"需改用 `build:h5` + 微信开发者工具导入验证，或先局部修复该指令（需用户决策）。
3. **测试套件陈旧**：16/17 测试文件失败源于旧路径引用，任何新增测试建议独立于全量 run 执行（如 `npx vitest run tests/uni-icons.spec.ts`）。

## 7.1 阶段 1 完成记录（2026-08-05）

**已替换（iconfont，11 文件 20 处）**：
| 文件 | 替换 |
|---|---|
| `admin/departments` :40/:73/:92 | 🔍→icon-search、⚠️→icon-error、▶▼→icon-arrow-right/down（条件类） |
| `admin/expert-list` :28/:73/:80 | 🔍→icon-search、⚠️→icon-error、👤→icon-my |
| `admin/featured` :45 | ⚠️→icon-error |
| `admin/users` :36/:81 | 🔍→icon-search、⚠️→icon-error |
| `live-manage/edit` :106 | 🗑→icon-delete |
| `live-manage/detail` :164/:166 | 🎥→icon-video、🎬→icon-play（嵌套 text） |
| `app/notifications` :258-262 + :65 | iconMap ⚙️📺💬→icon-setting/video/message 类名，模板 icon-text 加 iconfont 类；default 🔔→icon-video 降级 |
| `tabbar/my/notifications` :111-113 + :14 | Tab 图标 💬👍👤→icon-message/like-filled/my，模板 category-emoji 加 iconfont 类 |
| `tabbar/my/watch-history` :5 | 📺→icon-video（view 内嵌 text） |
| `shared/ModalDialog` :7 | 📺→icon-video |
| `shared/UserInfoHeader` :18 | 👤→icon-my |

**已删除（装饰性，4 文件 5 处）**：
- `login.vue:32` 📱、`live/LiveView.vue:229` 💡、`ChatTab.vue:58` 💬 placeholder、`live-manage/edit.vue:271` + `create.vue:314` 💡 tip-icon 元素（tip-box 为 flex+gap，删除后布局正常）

**已删除死文件**：`src/components/ChatTab-emoji-enhanced.vue`（git rm，无残留引用）

**验证结果**：`build:h5` ✅ 通过；`tests/uni-icons.spec.ts` 3/3 ✅；用户可见 emoji 48→26 行，剩余均为阶段 2/3 计划项或"不动"项（debug 页、H5 页、ErrorBanner 文本符号）

**阶段 1 遗留说明**：`notifications/index.vue` 未知类型 default 图标降级为 icon-video（原计划阶段 2 统一换 uni-icons notification，经评估保持 icon-video 降级——未知类型极少触发，且列表图标与全站 iconfont 风格统一更一致，避免同一图标容器混用两套字体；该决策已记录）

## 7.2 阶段 2 完成记录（2026-08-05）

**已替换（uni-icons，8 文件 10 处）**：
| 文件 | 替换 |
|---|---|
| `app/notifications` :37 | 🔔 空状态 → `<uni-icons type="notification" size="60" color="#c0c4cc" />` |
| `tabbar/my/notifications` :26 | 🔔 空状态 → 同上 |
| `tabbar/my/subscriptions` :27 | 🔔 空状态 → 同上 |
| `tabbar/my/notifications` :53-54 + :257-264 | 列表头像图标 📢🔔💬 → `sound`/`notification`/`chatbubble`（uni-icons size=22 color=#fff，替换原 emoji + filter 变白方案） |
| `live-manage/detail` :120 | 🌐 → `link` |
| `live-manage/detail` :163 | 📅 → `calendar` |
| `admin/featured` :52 | 🖼 → `images` |
| `admin/departments` :81 | 📂 → `folder-add` |
| `live-manage/create` :270 | 📂 兜底 → `v-if="cat.icon"` 显示后端值，`v-else` 显示 folder-add 图标 |
| `components/app/CreateLiveDrawer` :295 | 📂 兜底 → 同上 |

**工具链修复（必要）**：`vite.config.ts` 移除 `uni({ vueOptions: { exclude: [/@dcloudio\/uni-ui/] } })` —— 该 exclude 使 uni 插件跳过 uni-icons.vue 的 Vue 转换导致 H5 构建失败（`Expression expected`）。移除后：H5 构建 ✅；vitest 走独立 `vitest.config.ts`（vue() 插件）不受影响 ✅；项目此前从未实际使用 uni-ui 组件，此配置从未被构建验证过。

**验证结果**：`build:h5` ✅（产物含 `uniicons-*.ttf` 字体 + `uni-icons.*.js` 独立 chunk）；`tests/uni-icons.spec.ts` 3/3 ✅；全量测试 10 failed 与基线一致无恶化（46 passed 含新增 3）；用户可见 emoji 26→**17 行**，剩余全部为阶段 3 计划项（🔒🌍×3、📭×2、👁️、🔐）或"不动"项（debug 页、H5 页 console.log）

## 7.3 阶段 3-A 完成记录（2026-08-05）：👁️ 观看人数角标整体去除

**决策**：用户确认该角标（播放器右上角悬浮，`show-viewer-count` 写死 false，**从未实际显示**）直接去除。

**删除内容**：
- `src/components/app/VideoPlayerApp.vue`（5 处）：模板角标块（含注释）、props `showViewerCount`/`viewerCount`（定义+默认值）、`formatViewerCount` 函数、`.viewer-count-overlay`/`.viewer-text` 样式
- `src/pages/app/live/LiveView.vue`（10 处）：模板 2 个 props 传入、import `getRealtimeViewers`、import `ENV_CONFIG`（仅被删函数使用）、import 移除 `mockViewerCount`、`viewerCount` ref、`viewerCountTimer` 声明、`startViewerCountTimer()`/`clearViewerCountTimer()` 调用、loadSessionData 两处（真实/Mock 分支）`await loadViewerCount()`、三个函数块、`LIVEVIEW_API_MODE.useMockData.viewerCount` 配置行

**发现并补充**：`loadViewerCount` 实际有 **4 个调用点**（onMounted 定时器、loadSessionData 真实分支、loadSessionData Mock 分支 :958、setInterval），分析阶段只识别 3 个，实施中通过 grep 复查发现并补充删除。

**保留（死代码，无害）**：`api/playback.ts` 的 `getRealtimeViewers`、`mock-data.ts` 的 `mockViewerCount`（导出不触发 lint）；`store/player.ts` 的 `viewerCount`（独立统计 store，与 UI 无关）。

**验证结果**：`build:h5` ✅；`tests/uni-icons.spec.ts` 3/3 ✅；全量测试 10 failed 与基线一致；grep 复核 `loadViewerCount`/`viewerCountTimer`/`formatViewerCount`/`showViewerCount` **0 残留**，`viewerCount` 仅剩 store/player.ts 独立项；emoji 17→**16 行**（👁️ 消失）。

## 7.4 阶段 3-B 完成记录（2026-08-05）：🔒/🔓/🌍 私密状态组

**决策**：1A——🔒→uni-icons `locked`；🔓/🌍→文字化（公开态无图标）。

**替换内容（3 文件 3 处）**：
| 文件 | 位置 | 改动 |
|---|---|---|
| `live-manage/detail.vue` | :55 | `<uni-icons v-if="currentRoom.is_private" type="locked" size="13" class="status-icon" />`（status-icon 的 margin-right 保留在组件上）；公开态仅文字"公开房间" |
| `live-manage/edit.vue` | :176 | switch-row 内 `switch-label` 前插 `<uni-icons v-if="formData.is_private" type="locked" size="16" />`（flex+gap 自动间距）；文字去 emoji |
| `live-manage/list.vue` | :97 | 胶囊内嵌 `<uni-icons type="locked" size="10" /> 私密`（对齐 $font-xs≈10px） |

**验证结果**：`build:h5` ✅；`tests/uni-icons.spec.ts` 3/3 ✅；全量测试 10 failed 与基线一致；emoji 16→**13 行**（剩余：debug 7 + H5 console 3 + 📭×2 + 🔐×1，📭 属操作 C 待做，🔐 按决策不动）。

## 7.5 阶段 3-C 完成记录（2026-08-05）：📭 空状态

**决策**：2A——uni-icons `mail-open`（打开信封，语义接近"空收件箱"），与阶段 2 🔔 空状态同风格（size 60 ≈ 120rpx、color #c0c4cc）。

**替换内容（2 文件 2 处）**：
- `common/EmptyState.vue:4` → `<view v-else class="empty-icon-placeholder"><uni-icons type="mail-open" size="60" color="#c0c4cc" /></view>`（影响 5 处调用：brand/detail ×2、expert/detail ×2、tabbar/expert ×1，均无 icon prop 走此分支）
- `common/ScrollablePickerSheet.vue:22` → `<text class="empty-icon"><uni-icons type="mail-open" size="60" color="#c0c4cc" /></text>`（影响 CreateLiveDrawer、live-manage/create 选择器）

**验证结果**：`build:h5` ✅；`tests/uni-icons.spec.ts` 3/3 ✅；全量测试 10 failed 与基线一致；emoji 13→**11 行**，剩余全部为批准保留项（debug 页 7 + H5 console 日志 3 + UserInfoHeader 🔐 1）。

## 8. 阶段划分回顾（供阶段间审查）

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 准备与基线 | ✅ 完成 |
| 1 | iconfont 替换 + 删除装饰 + 删死文件（48→26 行） | ✅ 完成 |
| 2 | uni-icons 替换（26→17 行） | ✅ 完成 |
| 3-A | 👁️ 观看人数角标整体去除（17→16 行） | ✅ 完成 |
| 3-B | 🔒/🔓/🌍 私密状态组（16→13 行） | ✅ 完成 |
| 3-C | 📭 空状态（13→11 行） | ✅ 完成 |
| 4 | 全量回归与收尾 | ✅ 完成（本文档 §7.6） |

**阶段 3 总结**：决策 1A + 2A + 3（去除）+ 4（不动）全部落地；用户可见 emoji 从 48 处降至 **11 行**（全部为批准保留项：debug 调试页、H5 页内联 console 日志、UserInfoHeader 🔐）。

## 7.6 阶段 4 完成记录（2026-08-05）：全量回归与收尾

**收尾清理（审查报告隐患 2/3，4 文件 6 处）**：
- `api/playback.ts`：删除 `getRealtimeViewers` 函数 + `RealtimeViewers` import + 文件头注释更新
- `types/playback.ts`：删除 `RealtimeViewers` interface（PlaybackStats/StreamUrl 等保留）
- `live/mock-data.ts`：删除 `mockViewerCount`
- `tabbar/my/notifications/index.vue`：删除死样式 `.avatar-icon`（外层 + 3 处嵌套 filter，背景渐变保留——仍被 getAvatarClass 使用）

**全量回归结果**：
| 项 | 结果 |
|---|---|
| `npx eslint src` | 156 problems（29 errors/127 warnings）——与基线一致，无新增 |
| `pnpm test:run` | 10 failed / 46 passed——与阶段 0 基线完全一致 |
| `pnpm build:h5` | ✅ 通过 |
| `pnpm build:mp-weixin` | ❌ 既有失败（`h5/room/RoomList.vue:62` v-loading），与阶段 0 基线一致，非本次引入 |
| emoji 终检 | **11 行**，全部为批准保留项（debug 页 7 + H5 console 3 + 🔐 1） |
| 残留 grep | getRealtimeViewers/mockViewerCount/RealtimeViewers **0 残留**；avatar-icon 剩余 4 处为其他组件合法同名类 |
| pages.json | 未触碰（用户 M 状态保留） |

**最终状态**：本次任务共改动 25 个文件（22 M + 2 新增 + 1 删除死文件），与用户未提交改动同文件共存（无冲突，提交时需按 §7.1-7.6 清单分离）。

## 7.7 漏网项修复记录（2026-08-05）：全项目 SFC 精确扫描

**背景**：用 `@vue/compiler-sfc` 精确解析发现此前扫描（仅查 template 字面量 + 简单块检测）遗漏的 5 处——script 中 computed/函数返回 emoji 字符串渲染到模板、以及嵌套 `<template v-if>` 导致的模板检测盲区。

**修复内容（3 文件 5 处）**：
| 位置 | 原状 | 修复 |
|---|---|---|
| `live/LiveView.vue:108` | ⚠️ 流量提醒弹窗图标 | → `iconfont icon-error` |
| `live/LiveView.vue:406-425` | `statusText`/`statusClass` 死代码（🔴⏰📺，均 unused） | 整体删除 |
| `live-manage/list.vue:336-338` | emptyIcon 📺🏠📋 | → iconfont 类名 `icon-video`/`icon-home`/`icon-time`，模板加 iconfont 类 |
| `admin/users:351-352` | streamBadgeText ✅❌ | → 纯文字"开通/未开通"（绿/灰胶囊已传达状态） |
| `admin/users:376-378` | emptyIcon 🔒📡👥 | → iconfont 类名 `icon-privacy`/`icon-video`/`icon-my` |

**验证结果**：SFC 精确扫描 template 13 行（全部批准保留/范围外）+ script 3 行（ErrorBanner 文本符号 ×2 + login console 参数 ×1）；`build:h5` ✅；uni-icons 3/3 ✅；全量测试与基线一致；lint 156→**154**（-2 unused）；statusText 残留 10 处均为 H5 页独立变量，streamBadgeText 为正常定义+调用。

**最终用户可见 emoji 状态**：**13 行全部为批准保留项**（UserInfoHeader 🔐 ×1 + debug 页 ×7 + H5 页 console ×3 + H5 页 🙂⭐ ×2）；ErrorBanner/uni.scss 为单色文本符号（⚠ℹ，非彩色 emoji）；login:477 为 console 参数。

## 8. 阶段划分回顾（供阶段间审查）

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 准备与基线 | ✅ 完成（本文档） |
| 1 | iconfont 替换 + 删除装饰 + 删死文件 | 待实施（约 22 处 / 11 文件） |
| 2 | uni-icons 替换（🔔📢🌍📂🖼📅 等） | 待实施（约 10 处 / 6 文件） |
| 3 | 决策项（🔒🔓📭cover-view 👁️ 后端 cat.icon） | 待决策 |
| 4 | 全量回归与收尾 | 待实施 |

## 9. 阶段 2 前置条件（本阶段审查结论）

1. uni-icons 组件验证通过（§5），easycom 可用 → 阶段 2 可直接引入
2. 真机/模拟器渲染抽查需在阶段 2 实施时进行（mp-weixin 构建验证受既有问题限制）
3. 若需 mp-weixin 构建验收，需先与用户确认是否处理 h5 RoomList.vue 的 v-loading（超出本任务范围）
