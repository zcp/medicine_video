# LivePlayer 播放模块与自定义基座打包验证——讲解与操作文档

> **文档类型**: 概念讲解 + 操作指南
> **创建日期**: 2026-09-05
> **适用范围**: App 端（uni-app，仓库 `D:\saas_app-main`）external 直播流播放组件启用 `<live-player>` 的全过程
> **关联文档**:
> - [外部直播流创建与手动开播_现状分析与实施方案.md](./外部直播流创建与手动开播_现状分析与实施方案.md)（方案源头：风险二/风险六/待决策点 3/V1.4/V1.9）
> - `src/manifest.json`（App 模块配置）
> - `src/pages/app/live/LiveView.vue`（播放组件使用处）
> - `src/components/app/VideoPlayerApp.vue`（当前实际播放组件）
> - git 提交 `150a664`（live-player 历史实现）、`99045ca`（当前 HEAD）
> **状态**: 🟡 代码侧已就绪、打包验证未完成——本文档为该遗留待办的执行手册

---

## 目录

1. [背景：为什么要做这件事](#一背景为什么要做这件事)
2. [核心概念讲解](#二核心概念讲解)
3. [现状盘点（以仓库为准）](#三现状盘点以仓库为准)
4. [前置条件与要求](#四前置条件与要求)
5. [操作流程（分阶段）](#五操作流程分阶段)
6. [验证通过后：启用 live-player 的代码改动](#六验证通过后启用-live-player-的代码改动)
7. [操作难点与踩坑清单](#七操作难点与踩坑清单)
8. [参考与依据](#八参考与依据)

---

## 一、背景：为什么要做这件事

### 1.1 问题链路（三连问）

**Q1：当前播放组件是什么？**

App 端播放直播/回放统一使用 uni `<video>` 组件（封装于 `VideoPlayerApp.vue`），靠 ShadowParser 解析 m3u8 切片做观看上报。

**Q2：为什么不兼容 App 端播放 m3u8？**

uni `<video>` 在 **Android 端对 HLS 变体支持差**（方案文档 §6.2，风险等级 🔴 高）：

- H.265 编码播不了
- fMP4、LL-HLS（低延迟分片）播不了
- AES-128 加密流播不了
- 非标准码率的流可能播不了
- 微信小程序 Android 端对 m3u8 支持也一般

**Q3：推荐组件是什么？为什么它兼容？需要什么打包配置？**

推荐 **`<live-player>`**（uni-app 原生直播组件）：

- 流媒体专用内核，直播 HLS 兼容性/稳定性优于普通 `<video>`（方案文档 §6.2 处理项①、§12 待决策点 3）；
- 同为原生组件，不受 CORS 限制；
- 但它是独立原生模块（LivePlayer），**标准基座不含/无法稳定渲染** → 必须在 manifest 勾选模块 + **制作自定义基座**后验证，验证通过才能启用（方案文档 §6.6 风险六）。

### 1.2 演进时间线（截至本文档）

| 时间 | 事件 | 出处 |
|---|---|---|
| 2026-08-11 | 方案定稿：external 直播流用 `<live-player>`（live）+ `<video>`（回放） | 方案文档 §5.6/§12 决策点 3 |
| 2026-08-11 | manifest.json 加入 LivePlayer 模块；LiveView.vue 实现 live-player 分支 | 提交 `150a664`；方案 §9.5.1 |
| 2026-08-12 | **真机/模拟器测试：标准基座下 live-player 渲染不稳定（insertBefore 崩溃）→ 降级回 video**，LiveView 统一 VideoPlayerApp | 方案文档 V1.9 |
| 2026-08-12 | 修订记录明确：**"后续自定义基座验证后再启用 live-player"** → 成为遗留待办 | 方案文档 V1.9 ④ |
| 至今 | 待办未执行：**带 LivePlayer 模块的自定义基座打包 + 真机验证 + 启用开关** | 本文档主题 |

> 注意：V1.9 崩溃发生在"标准基座 + 模拟器"环境。**不能**据此判定 live-player 不可用——标准基座可能根本没编入 LivePlayer 原生模块，模拟器解码环境也与真机差异大。自定义基座 + 真机验证才是正确验收路径。

---

## 二、核心概念讲解

### 2.1 播放组件选型谱系（本项目语境）

| 组件 | 内核 | Android m3u8 兼容 | 模块/打包要求 | 本项目定位 |
|---|---|---|---|---|
| uni `<video>` | 系统播放器 | 差（H.265/fMP4/LL-HLS/AES 均可能不可播） | 无额外要求 | **当前兜底方案**（回放 + 直播均用它） |
| `<live-player>` | 流媒体专用内核 | 好（标准 HLS 直播流稳） | 需 manifest 勾选 LivePlayer 模块 + 自定义基座/云打包 | **目标方案**（external live 用） |
| 原生 ijkplayer 插件 | ijkplayer（FFmpeg 系） | 最好 | 原生插件 + 自定义基座 | v1.1 评估项（仍不行才上） |

启用后分工：`external + live` → `<live-player>`；回放/其他 → `<video>`（VideoPlayerApp）。

### 2.2 基座（Base）是什么

基座是 DCloud 生态里的**调试用原生 App 壳**：HBuilderX"运行到手机"时，页面代码被编译成资源装进一个预打包的原生壳里运行，这个壳就是基座。

| 类型 | 说明 | 含 LivePlayer 吗 |
|---|---|---|
| **标准基座** | HBuilderX 内置通用壳，只含常用模块 | ❌ 不含/渲染不稳定（V1.9 崩溃即此环境） |
| **自定义基座** | 按你 manifest 勾选的模块 + 原生插件，云打包生成的专属调试壳 | ✅ 勾选后编入 |
| **正式发布包** | 发行 → 原生 App-云打包 产物（release 版） | ✅ 勾选后编入 |

### 2.3 CLI 工程与 HBuilderX 的分工（关键认知）

本项目是 **CLI 工程**（package.json scripts 用 `uni build -p app-android`）：

- `npm run build:app-android` 只产出**编译后的页面资源 + manifest 配置**，**不含原生引擎与原生模块**，产出物不是可安装 APK；
- 可安装 APK 只有两条路：
  1. **HBuilderX 云打包**（DCloud 服务器把原生引擎 + manifest 勾选的模块 + 资源合成 APK）——本项目采用；
  2. 离线打包 SDK（本地 Android Studio 集成原生工程，成本高，不采用）。

结论：**自定义基座的制作必须在 HBuilderX 中完成**，用云打包方式。

### 2.4 LivePlayer 模块在打包链路中的角色

```
manifest.json(app-plus.modules.LivePlayer)  ← 代码侧开关（已加）
        ↓
HBuilderX 读取 manifest → 云打包/制作自定义基座时把该原生模块编入 APK
        ↓
安装到真机 → 页面里 <live-player> 才有原生实现 → 正常渲染播放
```

改 manifest（加/删模块、换包名）后必须**重新制作基座**，不会增量生效。

---

## 三、现状盘点（以仓库为准）

| 事项 | 状态 | 位置/证据 |
|---|---|---|
| manifest 加 LivePlayer 模块 | ✅ 已完成 | `D:\saas_app-main\src\manifest.json:25` `modules.LivePlayer`（提交 `150a664` 加入） |
| Android 包名/ABI 配置 | ✅ 已有 | `manifest.json` distribute.android：包名 `com.livesaas.app`、`abiFilters: [armeabi-v7a, arm64-v8a]`、minSdk 21、targetSdk 33 |
| live-player 使用代码 | ⚠️ 曾实现、当前被移除 | 历史实现见提交 `150a664` 的 LiveView.vue；当前 HEAD 仅存注释说明 |
| 当前实际播放组件 | `<video>`（VideoPlayerApp） | `D:\saas_app-main\src\pages\app\live\LiveView.vue:96`（注释 L93-95 说明降级原因） |
| 明文流量配置 | ⚠️ 生产 https 无碍；本地 http 联调白名单未放行 | `src/hybrid/html/network_security_config.xml`（base-config 禁明文，域名白名单为注释状态） |
| 环境变量 | 开发 `http://10.105.136.235:8080`（局域网 IP 频繁变动）；生产 `https://mp.dayilive.com` | `.env.development.local` / `.env.production` |
| 播放代理端点 | ✅ 已上线 | 后端 `GET /api/core/proxy/m3u8/{session_id}`；前端 `getProxyM3u8Url` 返回完整 URL |
| **自定义基座制作 + 真机验证** | ❌ **未做（本文档待执行项）** | 方案文档 V1.9 遗留 |
| **验证后启用 live-player** | ❌ 未做 | 同上 |

---

## 四、前置条件与要求

### 4.1 硬性要求清单

| 维度 | 要求 | 说明 |
|---|---|---|
| 工具 | HBuilderX（对应 alpha 版本） | 项目用 `@dcloudio/uni-app-plus@3.0.0-alpha-4070620250731001`（2025-07-31 alpha），HBuilderX 版本需与编译器匹配，否则导入/打包报编译器不兼容 |
| 账号 | DCloud 账号并登录 | 云打包必需；排队制，免费有次数限制 |
| Android 设备 | **arm64 真机**（USB 调试可用） | abiFilters 无 x86 → x86 模拟器装不上；**模拟器结果不可信，以真机为准** |
| iOS（如需验证） | Apple 开发者证书 p12 + 开发描述文件（含设备 UDID） | 个人付费账号才能长期真机调试（免费账号 7 天过期）；无证书只能打 iOS 模拟器基座 |
| Android 证书 | 调试：公共测试证书即可；正式发布：必须自有 keystore | 测试证书包与正式证书包互不覆盖，不能增量升级 |
| 测试数据 | 1 条 external+live 场次（真实 m3u8 走代理）+ 1 条回放场次 | 代理端点已可用；样本可参考方案文档 §2.4 |

### 4.2 证书要求详解

**Android（keystore）**：

- 制作自定义基座（调试）：HBuilderX 云打包界面选"公共测试证书"即可，无需自备；
- 正式发布：必须自备 keystore（`keytool -genkeypair` 生成，记录 alias/密码），云打包时填写；包名 `com.livesaas.app` 与签名强绑定，换证书 = 老用户无法覆盖升级。

**iOS**：

- 真机自定义基座需 Apple 开发者签名（p12 + 开发描述文件）；
- 描述文件必须包含测试真机的 UDID；
- 模拟器基座免证书，但验证不了真机 HLS 解码差异。

### 4.3 环境与网络要求

- 生产环境播放/代理地址为 `https://mp.dayilive.com`，无明文流量问题；
- 本地开发联调时 `VITE_BASE_API_URL=http://10.105.136.235:8080`（明文 http）：
  - Android 9+ 默认禁明文（`network_security_config.xml` 当前 base-config 禁明文、白名单被注释），若播放器被拦需先取消注释白名单域名或改用 https；
  - iOS ATS 对明文 http 拦截更严；
  - 注意开发机 IP 频繁变动（历史记录多次更换），真机联调前先 `ipconfig` 核对。

---

## 五、操作流程（分阶段）

### 阶段 0：前置检查（约 0.5 天）

```text
1. HBuilderX 已安装且版本与 alpha-4070620250731001 编译器兼容
2. DCloud 账号已登录，云打包服务可连通
3. Android arm64 真机已连接（adb devices 可见）；如验 iOS：证书 + 描述文件就绪
4. 确认 manifest.json 可视化界面中 LivePlayer(直播播放) 模块已勾选（与代码 modules.LivePlayer 一致）
5. 确认后端代理端点可访问、external+live 与回放测试场次各 1 条可用
6. 前端 lint/vitest 基线记录（当前应 0 error / 存量失败与基线一致）
```

**Gate**：☑ 版本匹配 ☑ 模块已勾选 ☑ 真机就绪 ☑ 测试场次就绪

### 阶段 1：制作自定义基座

```text
1. HBuilderX → 文件 → 导入 → 从本地目录导入，选择 D:\saas_app-main
   （CLI 工程根，含 src/manifest.json，HBuilderX 识别为 uni-app vue3 工程）
2. 打开 src/manifest.json 可视化界面 → App 模块配置 → 确认 LivePlayer 已勾选
   （防止历史可视化编辑把模块冲掉；代码与界面两侧保持一致）
3. 菜单：运行 → 运行到手机或模拟器 → 制作自定义调试基座
4. 弹窗选择 Android → 证书选「公共测试证书」（调试够用）→ 提交云打包
5. 等待云打包（排队 + 编译，几分钟至几十分钟）
6. 下载自定义基座 APK → 安装到真机（基座图标可辨识）
7. iOS（如需）：重复 3-6，选 iOS，需上传 p12 + 开发描述文件
```

**关键**：基座制作必须包含 LivePlayer 模块；制作完成后不要改 manifest（改了要重打）。

### 阶段 2：自定义基座真机验证（核心验收）

```text
1. 手机连接 → 菜单：运行 → 运行到手机或模拟器 → 选择设备
2. ⚠️ 基座选择下拉：务必选「自定义基座」（不是标准基座！选错复现崩溃且验证无效）
3. 页面资源自动编译推送进基座，启动 App
```

**验收用例矩阵**：

| # | 用例 | 预期 | 通过标准 |
|---|---|---|---|
| 1 | external+live 场次进播放页 | live-player 正常渲染，不再 insertBefore 崩溃 | 渲染稳定、出画出声 |
| 2 | 直播 HLS 持续播放 | 画面/声音正常，无频繁卡死 | 连续播放 ≥ 5 分钟 |
| 3 | 切后台/回前台 | 播放恢复不断流 | 无崩溃 |
| 4 | 退页销毁（反复进出播放页 5+ 次） | 无内存崩溃 | 稳定退出 |
| 5 | 播放失败场景（断网/错误地址） | `@error` 事件触发，走 handlePlaybackError 上报 | 有文案提示 + 上报 |
| 6 | external 回放场次 | 仍走 VideoPlayerApp（video）回归正常 | 断点续播/观看上报不回归 |
| 7 | Android 低端机复测 1-6 | 兼容稳定 | 不闪退 |
| 8 | iOS 真机（有条件时） | 同 1-7 | 不闪退 |

**Gate（通过则进入阶段 3；不通过见下方降级预案）**：
☑ live-player 在自定义基座下渲染稳定 ☑ 直播可播 ☑ video 回放零回归 ☑ 错误上报可用

### 阶段 3：验证通过后——启用 live-player

1. 按 [第六章](#六验证通过后启用-live-player-的代码改动) 修改 `LiveView.vue`（恢复 live-player 分支 + 事件适配）；
2. `npm run lint` + `npm run test:run` 回归（与基线一致）；
3. git 提交（参考风格：feat: 启用 live-player 播放 external 直播流）。

### 阶段 4：正式发布

```text
1. 生成自有 Android keystore（keytool），记录 alias/密码
2. HBuilderX → 发行 → 原生 App-云打包 → 选择正式证书（Android）/ 证书+描述文件（iOS）
3. 出正式包 → 真机矩阵回归（iOS/Android 主流机型）
4. 观察线上「播放失败上报」数据，确认 live 播放质量
5. 小程序端（另一条线）：mp-weixin appid wxfa6bac37fec625a8 需确认「直播」类目资质，
   与 App 基座验证相互独立，不要混淆
```

### 降级预案（Gate 不通过）

live-player 在自定义基座下仍崩溃或 Android 兼容仍差：

```text
1. 维持 <video> 现状（当前 HEAD 行为，功能可用，仅兼容性风险）
2. 记录验证证据（机型/日志/复现步骤）到本文档修订记录
3. v1.1 再评估原生 ijkplayer 插件（HBuilderX 原生插件 + 自定义基座，成本另计）
   —— 这是方案文档预留的正式退路，不是死胡同
```

---

## 六、验证通过后：启用 live-player 的代码改动

### 6.1 恢复方案（以提交 150a664 的历史实现为底稿）

历史实现（150a664）要点：

```html
<!-- V15：external 直播流用 live-player（流媒体专用内核），回放/其他用 VideoPlayerApp -->
<live-player
  v-else-if="isExternalLive"
  ref="playerRef"
  :src="playerSourceUrl"
  mode="live"
  :autoplay="true"
  :muted="false"
  @error="handlePlaybackError"
/>
```

```ts
// V15：external 直播中场次使用 live-player（流媒体专用内核，直接 HLS 兼容性优于 video）
const isExternalLive = computed(
  () => sessionInfo.value?.source_type === 'external' && sessionInfo.value?.status === 'live'
);
```

### 6.2 必须做的适配清单（防回归）

| # | 适配点 | 说明 |
|---|---|---|
| 1 | **事件体系不同** | live-player 无 `@play/@pause/@segmentchange`，事件为 `@statechange` 等；现有 handlePlay/断点续播逻辑仅适用于 video 分支，需按组件分流或确认 live 分支不触发 |
| 2 | **无 seek** | live-player 不支持 seek，断点续播（initialProgress）对 live 分支必须跳过，避免调用报错 |
| 3 | **观看上报失效** | VideoPlayerApp 的 ShadowParser 靠解析 video 的 m3u8 切片请求做观看上报，live-player 不走 webview → 观看统计口径需产品确认或换事件（statechange/播放时长） |
| 4 | **原生组件层级** | live-player 是原生组件，悬浮控件（若有）可能被盖，需 cover-view 处理；验证时重点看播放器区域的浮层 |
| 5 | **事件/方法类型** | ref 指向的组件实例方法（seek 等）只在 video 分支存在，TS/运行时都要防 |
| 6 | **autoplay 策略** | iOS 自动播放/静音策略与 video 不同，按真机验证结果决定 muted 初值 |

> 建议封装为一个 `<LivePlayerApp>` 组件（与 VideoPlayerApp 同目录 `components/app/`），对外暴露统一的 props/事件接口，LiveView 只按 `isExternalLive` 切换组件，减少页面内分支复杂度。

---

## 七、操作难点与踩坑清单

1. **基座选错（最高频坑）**：做完自定义基座后运行仍选标准基座 → 1:1 复现 insertBefore 崩溃 → 误判"live-player 不行"。基座选择在运行弹窗有独立选项。
2. **标准基座不包含 LivePlayer 原生实现**：V1.9 崩溃大概率源于此，不是代码问题；只有自定义基座能给出有效验证结论。
3. **模拟器验证失真**：abiFilters 无 x86（x86 模拟器装不上）；arm64 模拟器 GPU/解码器与真机差异大；当初崩溃正是在模拟器环境 → **以真机结果为准**。
4. **云打包排队与次数**：DCloud 免费账号有限额，高峰排队久；报错信息不直观，需看打包日志。
5. **Android 证书体系**：调试用公共测试证书 → 正式必须自有 keystore；测试/正式证书包互不覆盖 → 提前决定正式证书，别等上架才发现。
6. **iOS 证书门槛**：p12 + 含 UDID 的开发描述文件；免费账号 7 天过期；无证书只能 iOS 模拟器（验证价值有限）。
7. **alpha 编译器风险**：项目编译器为 2025-07-31 alpha；若自定义基座下仍崩，先尝试切同代 release 编译器再打基座（排除编译器缺陷）。
8. **明文 http 限制**：本地联调为 http 局域网 IP；Android `network_security_config.xml` 白名单当前全注释；iOS ATS 更严 → 本地验证前先放行或改用 https；生产 https 无碍。
9. **模块变更不增量生效**：改 manifest 必须重新制作基座；"改完直接跑"得到旧行为 → 验证结论全错。
10. **启用后的统计口径变化**（难点最易漏）：live-player 无 segmentchange，观看上报链路失效，需先与产品确认口径再启用以免上线后数据断崖。
11. **测试场次依赖**：验证需要 external+live 场次 + 后端代理可用；若后端未部署最新镜像，代理端点 404 会被误判为播放组件问题。
12. **与小程序线混淆**：小程序 live-player 需要微信「直播」类目资质，是独立验证线，别把 App 基座结论套到小程序。

---

## 八、参考与依据

### 8.1 方案文档关键位置

| 内容 | 出处 |
|---|---|
| Android m3u8 兼容性风险（🔴 高） | 外部直播流创建与手动开播_现状分析与实施方案.md §6.2 |
| live-player 打包配置风险（🟢 低） | 同上 §6.6 |
| 直播流播放组件待决策点 | 同上 §12 决策点 3 |
| 标准基座降级记录 | 同上 V1.9（修订记录） |
| 播放器分工方案（live-player 直播 + video 回放） | 同上 §5.6/§11 |
| ijkplayer v1.1 评估项 | 同上 §6.2 处理项④ / §13 |

### 8.2 前端仓库关键位置（D:\saas_app-main）

| 文件 | 说明 |
|---|---|
| `src/manifest.json` | `app-plus.modules.LivePlayer` 已勾选（L25）；Android 包名/ABI/权限配置 |
| `src/pages/app/live/LiveView.vue` | 播放组件使用处；当前仅 VideoPlayerApp（L96）+ 降级注释（L93-95） |
| `src/components/app/VideoPlayerApp.vue` | 当前播放组件（uni video + ShadowParser） |
| `src/api/session.ts` | `getProxyM3u8Url`（代理地址，须完整 URL） |
| `src/hybrid/html/network_security_config.xml` | Android 明文流量策略（白名单当前注释状态） |
| `.env.development.local` / `.env.production` | 开发 http 局域网 IP / 生产 https |
| git 提交 `150a664` | live-player 历史实现（启用时底稿） |

### 8.3 验证环境速查

- uni-app 编译器：`3.0.0-alpha-4070620250731001`（@dcloudio/uni-app-plus）
- Android：包名 `com.livesaas.app`，abiFilters `armeabi-v7a/arm64-v8a`，minSdk 21，targetSdk 33
- 后端代理端点：`GET /api/core/proxy/m3u8/{session_id}`（session 关联，防 SSRF，两级重写）
- 播放源规则（LiveView.setupPlayerSource）：external → 一律代理地址；push live → live_url 优先；回放 → playback_url

---

## 修订记录

| 版本 | 日期 | 说明 |
|---|---|---|
| V1.0 | 2026-09-05 | 初稿。整理自方案文档与前端仓库现状核对：背景/概念/现状/前置要求/操作流程/代码改动建议/难点清单 |
