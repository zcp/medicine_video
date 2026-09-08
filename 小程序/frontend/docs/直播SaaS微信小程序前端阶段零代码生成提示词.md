# 直播SaaS微信小程序前端阶段零：项目地基与设计规范代码生成提示词 (V1 - 微信小程序版)

---

## 1. 角色定义（Role Definition）
你是一名资深微信小程序前端架构师，精通uni-app、Vue3、TypeScript和微信小程序开发及多端适配，擅长从零开始搭建可维护、可扩展、规范化的微信小程序项目骨架。你的任务是为医学直播SaaS平台微信小程序端建立坚实、一致且标准化的开发基础，并**实现**一个功能完整的日志管理模块。

---

## 2. 任务目标（Task Objective）
本次任务为"直播SaaS平台微信小程序前端项目"的**阶段零**，核心目标是**搭建项目的完整骨架，实现微信小程序UI设计规范代码化，并创建功能完备的日志管理系统**。所有生成的文件和代码都必须是生产级别的、功能完整的，而不仅仅是静态的骨架。

**为确保任务明确、无歧义，本次需具体生成以下所有文件和目录：**

### 2.1 项目根目录文件
- `package.json`
- `vite.config.ts`
- `tsconfig.json`
- `.eslintrc.cjs`
- `.prettierrc`
- `jest.config.js`
- `.gitignore`
- `README.md`

### 2.2 核心源码文件 (`src/`)
- `App.vue`
- `main.ts`
- `pages.json`
- `manifest.json`
- `env.d.ts`
- `common/uni.scss` (微信小程序设计令牌)

### 2.3 日志管理模块 (`src/logs/`)
- `logTypes.ts`
- `logConfig.ts`
- `logger.ts`

### 2.4 空目录结构
- `src/api/`
- `src/components/`
- `src/pages/`
- `src/static/`
- `src/store/`
- `src/types/`
- `src/utils/`
- `tests/`

---

## 3. 核心上下文信息（Core Context Information）

### 3.1 唯一事实来源
- **设计文档**: 《直播SaaS平台移动端前端设计文档(微信小程序).md》是所有代码生成工作的唯一且最高的设计依据。
- **设计令牌**: `uni.scss` 文件中的所有CSS变量必须严格依据设计文档中的移动端UI规范进行转换。
- **日志系统**: 日志系统的实现必须遵循移动端特性和微信小程序环境约束。

### 3.2 微信小程序技术栈
- **核心框架**: uni-app（Vue3 + Composition API + TypeScript）
- **状态管理**: Pinia
- **UI组件库**: uView Plus（按需引入，适配微信小程序）
- **构建工具**: Vite
- **多端适配**: 微信小程序、H5、Android、iOS

### 3.3 移动端设计特性
- **底部Tab导航**: 五个主Tab（首页、品牌、我的直播、专家、我的）
- **Feed流布局**: 双列瀑布流（可切换单列），无限滚动加载
- **小窗播放**: 直播观看时支持小窗模式
- **流量提醒**: 使用流量网络观看直播时自动提醒
- **昼夜模式**: 支持跟随系统、手动切换、定时切换
- **科室星标固定**: 用户可将常看的科室固定到首页筛选器前排

---

## 4. 全局强制性约束与最高准则

### 4.1 最高准则
- **功能完整性**: 生成的所有代码（尤其是配置文件和日志模块）必须是功能完整的，可直接运行。
- **零偏差原则**: 严格遵循移动端设计文档，不允许任何形式的"优化"或"变通"。
- **微信小程序适配**: 所有API调用必须使用uni-app的微信小程序兼容API。
- **移动端优先**: 优先考虑移动端体验，触摸交互、手势操作、小屏适配。

### 4.2 命名规范（强制执行）
- **变量/函数**: `camelCase`（如：`liveRoomList`、`handleTabChange`）
- **组件/页面**: `PascalCase`（如：`Home.vue`、`LiveView.vue`、`RoomCard.vue`）
- **API文件**: 小写（如：`room.ts`、`session.ts`、`user.ts`）
- **类型定义**: `PascalCase`（如：`Room`、`Session`、`User`）
- **常量**: `UPPER_SNAKE_CASE`（如：`MAX_ROOM_COUNT`、`API_BASE_URL`）
- **Store模块**: 小写（如：`store/room.ts`、`store/user.ts`）

### 4.3 微信小程序安全规范
- **XSS防护**: 所有用户输入、接口返回内容渲染前必须进行转义，严禁直接插入HTML。
- **敏感信息脱敏**: 涉及患者、医生等敏感数据（如手机号、身份证、病例号等）前端展示时需做脱敏处理。
- **HTTPS强制**: 所有API请求必须通过HTTPS协议。
- **Token安全存储**: Token存储于uni.setStorageSync，小程序端自动加密。
- **小程序隐私合规**: 遵守微信小程序隐私规范，获取用户信息、位置、相机等权限前需明确告知。

---

## 5. 分步生成指令 (Step-by-Step Module Generation)

### 步骤1：微信小程序项目配置文件生成

#### `package.json`
- **目标**: **创建**一个包含微信小程序所有必要依赖项和脚本的 `package.json` 文件。
- **要求**:
  - **包含** `dependencies`: `vue`, `pinia`, `@dcloudio/uni-app`, `@dcloudio/uni-mp-weixin`。
  - **包含** `devDependencies`: `@dcloudio/types`, `@types/node`, `typescript`, `vite`, `eslint`, `prettier`, `vue-tsc` 等微信小程序开发工具。
  - **定义** `scripts`: `dev:mp-weixin`, `build:mp-weixin`, `dev:h5`, `build:h5`, `lint`, `format`。

#### `vite.config.ts`
- **目标**: **配置** Vite 以支持 uni-app 微信小程序构建。
- **要求**:
  - **导入**并**使用** `uni` 插件，配置微信小程序构建选项。
  - **配置** `@` 路径别名，使其指向 `src` 目录。
  - **配置** 微信小程序特有的构建优化。

#### `manifest.json`
- **目标**: **配置**微信小程序的应用清单。
- **要求**:
  - **设置** 小程序基本信息（名称、版本、描述）。
  - **配置** 权限申请（网络、位置、相机等）。
  - **配置** 微信小程序特有设置（分包、导航栏等）。

---

### 步骤2：微信小程序核心应用文件生成 (`src/`)

#### `main.ts`
- **目标**: **实现** Vue 应用的入口文件，适配微信小程序环境。
- **要求**:
  - **创建** Vue 应用实例。
  - **创建**并**使用** Pinia 实例。
  - **配置**微信小程序专用初始化逻辑。

#### `pages.json`
- **目标**: **配置**微信小程序页面路由和底部TabBar。
- **要求**:
  - **定义**底部TabBar，包含5个Tab（首页、品牌、我的直播、专家、我的）。
  - **配置** `globalStyle`，设置适合移动端的导航栏和背景色。
  - **使用** `uni.scss` 中定义的CSS变量。

#### `App.vue`
- **目标**: **实现**应用根组件，初始化微信小程序全局功能。
- **要求**:
  - **初始化** Pinia Store。
  - **配置**全局样式和主题。
  - **实现**微信小程序生命周期钩子（onLaunch、onShow等）。

#### `common/uni.scss`
- **目标**: **实现**移动端设计令牌的CSS变量。
- **要求**:
  - 严格依据《直播SaaS平台移动端前端设计文档(微信小程序).md》。
  - **定义**移动端适配的颜色、字体、间距、圆角等设计规范CSS变量。
  - **支持**昼夜模式切换。
  - **适配**不同屏幕尺寸的响应式设计。

---

### 步骤3：移动端日志管理模块生成 (`src/logs/`)

#### `src/logs/logTypes.ts`
- **目标**: **定义**微信小程序环境下所有日志相关的类型、接口和枚举。
- **强制性要求**:
  1. **定义** `LogLevel` 枚举 (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`)。
  2. **创建** `LogEntry` 接口，包含 `level`, `message`, `timestamp`, `module`, `data`, `error`, `platform` 字段。
  3. **定义** `MiniProgramConfig`, `LogFilter`, `LogStorageOptions`, `LogReportOptions`, `LoggerConfig` 等微信小程序特有配置接口。

#### `src/logs/logConfig.ts`
- **目标**: **配置**微信小程序日志系统的行为和安全策略。
- **强制性要求**:
  1. **实现**一个函数 `createLoggerConfig`，该函数能**感知**当前环境 (`development` 或 `production`) 和平台 (`mp-weixin` 或 `h5`)。
  2. **根据环境和平台**返回不同的配置对象，微信小程序生产环境**使用** `INFO` 级别并**开启**上报。
  3. **实现**一个 `sensitiveFields` 数组，**定义**医学场景特有的脱敏规则。
  4. **配置**微信小程序特有的存储限制和网络请求限制。

#### `src/logs/logger.ts`
- **目标**: **实现**完整的微信小程序日志记录、处理和上报功能。
- **微信小程序特有要求**:
  1. **使用** `uni.getStorageSync` 和 `uni.setStorageSync` 进行本地存储。
  2. **使用** `uni.request` 进行日志上报。
  3. **监听**微信小程序生命周期事件（onShow、onHide、onError）。
  4. **实现**网络状态检测（`uni.getNetworkType`），离线时缓存日志。
  5. **数据流**:
      - **输入**: `log` 方法接收原始日志数据。
      - **处理**: **调用** `sanitizeData` 方法对 `data` 参数进行深度递归脱敏。
      - **存储**: **将**处理后的 `LogEntry` 对象存储到微信小程序本地存储。
      - **上报**: 根据网络状态和配置进行批量上报。
  6. **错误处理**:
      - 所有对 `uni.storage` 的读写操作都必须被 `try...catch` 包裹。
      - `uni.request` 失败时实现指数退避重试策略。
  7. **微信小程序集成**:
      - **实现** `initialize` 方法，在小程序启动时被调用。
      - **使用** `uni.onError` 和 `uni.onUnhandledRejection` 进行全局错误捕获。

---

## 6. 微信小程序特有配置要求

### 6.1 manifest.json 配置要求
```json
{
  "name": "live-streaming-wechat",
  "appid": "",
  "description": "医学直播SaaS平台微信小程序",
  "versionName": "1.0.0",
  "versionCode": "100",
  "transformPx": false,
  "mp-weixin": {
    "appid": "",
    "setting": {
      "urlCheck": false,
      "es6": true,
      "enhance": true,
      "postcss": true,
      "preloadBackgroundData": false,
      "minified": true,
      "newFeature": false,
      "coverView": true,
      "nodeModules": false,
      "autoAudits": false,
      "showShadowRootLocation": true,
      "scopeDataCheck": false,
      "uglifyFileName": false,
      "checkInvalidKey": true,
      "checkSiteMap": true,
      "uploadWithSourceMap": true,
      "compileHotReLoad": false,
      "lazyloadPlaceholderEnable": false,
      "useMultiFrameRuntime": true,
      "useApiHook": true,
      "useApiHostProcess": true,
      "babelSetting": {
        "ignore": [],
        "disablePlugins": [],
        "outputPath": ""
      },
      "enableEngineNative": false,
      "useIsolateContext": true,
      "userConfirmedPrivacyRules": false,
      "userConfirmedBundleSwitch": false,
      "packNpmManually": false,
      "packNpmRelationList": [],
      "minifyWXSS": true,
      "disableUseStrict": false,
      "minifyWXML": true
    },
    "usingComponents": true,
    "permission": {
      "scope.userInfo": {
        "desc": "用于完善用户资料"
      }
    },
    "requiredPrivateInfos": ["getLocation"],
    "lazyCodeLoading": "requiredComponents"
  }
}
```

### 6.2 pages.json TabBar配置要求
```json
{
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#509CEC",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/home/Home",
        "text": "首页",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png"
      },
      {
        "pagePath": "pages/brand/BrandZone",
        "text": "品牌",
        "iconPath": "static/tab-brand.png",
        "selectedIconPath": "static/tab-brand-active.png"
      },
      {
        "pagePath": "pages/my-live/MyLive",
        "text": "我的直播",
        "iconPath": "static/tab-live.png",
        "selectedIconPath": "static/tab-live-active.png"
      },
      {
        "pagePath": "pages/expert/ExpertList",
        "text": "专家",
        "iconPath": "static/tab-expert.png",
        "selectedIconPath": "static/tab-expert-active.png"
      },
      {
        "pagePath": "pages/profile/Profile",
        "text": "我的",
        "iconPath": "static/tab-profile.png",
        "selectedIconPath": "static/tab-profile-active.png"
      }
    ]
  }
}
```

### 6.3 微信小程序专用uni.scss变量要求
必须包含以下移动端特有变量：
- **触摸反馈**: `--touch-feedback-duration`, `--touch-feedback-opacity`
- **安全区域**: `--safe-area-top`, `--safe-area-bottom`
- **TabBar高度**: `--tabbar-height: 50px`
- **导航栏高度**: `--navbar-height: 44px`
- **状态栏高度**: `--status-bar-height: var(--status-bar-height)`

---

## 7. 移动端性能优化要求

### 7.1 微信小程序包大小优化
- **分包加载**: 合理使用分包，主包控制在2MB以内
- **图片压缩**: 所有图片必须压缩，使用适当格式
- **代码分割**: 按需加载组件和页面

### 7.2 渲染性能优化
- **虚拟列表**: 长列表使用虚拟滚动
- **懒加载**: 图片和组件懒加载
- **防抖节流**: 搜索和滚动事件防抖处理

### 7.3 网络优化
- **请求合并**: 合并相关接口请求
- **缓存策略**: 实现合理的缓存机制
- **预加载**: 关键数据预加载

---

## 8. 移动端异常处理规范

### 8.1 网络异常处理
- **断网检测**: 使用 `uni.getNetworkType()` 检测网络状态
- **超时处理**: 微信小程序请求超时设置为10秒
- **弱网优化**: 检测到2G/3G网络时，自动降低视频清晰度

### 8.2 小程序特有异常
- **授权异常**: 用户拒绝授权的处理流程
- **版本兼容**: 低版本微信的兼容处理
- **平台限制**: 小程序平台限制的降级方案

---

## 9. 最终交付与质量保证协议

### 9.1 输出格式要求
- 每个文件一个完整、可直接运行的代码块，并标注清晰的文件路径。
- 禁止在代码之外添加任何解释、道歉或不必要的寒暄。
- 所有代码必须适配微信小程序环境。

### 9.2 自我修正要求
在每一步生成后，你必须在内部进行自查：
- 是否符合微信小程序开发规范？
- 是否正确使用了uni-app API？
- 是否考虑了移动端用户体验？
- 如果发现与设计文档或本提示词有任何偏差，必须**立即撤销并重新生成**。

### 9.3 最终一致性断言
在完成所有文件生成后，输出：
```
[微信小程序阶段零断言 - WECHAT MINIPROGRAM PHASE 0 ASSERTION]
Project skeleton and foundation setup is complete for WeChat MiniProgram.
- Configuration Files Completeness: 100%
- WeChat MiniProgram Adaptation: 100%
- Directory Structure Consistency: 100%
- Mobile UI Design Tokens: 100%
- Logger Implementation (Mobile): 100%
- Dynamic Logic Implementation: 100%
- Zero Business Logic Principle: Adhered
- Mobile-First Principle: Adhered
```

---

## 10. 特别注意事项

### 10.1 微信小程序开发约束
- 使用 `uni.request` 而非 `axios`
- 使用 `uni.setStorageSync` 而非 `localStorage`
- 使用 `uni.navigateTo` 而非 `router.push`
- 使用 `uni.showToast` 而非 `alert`
- 遵循微信小程序域名白名单限制

### 10.2 移动端交互特性
- 支持触摸手势操作
- 适配不同屏幕尺寸
- 考虑横竖屏切换
- 优化触摸反馈效果

### 10.3 医学直播场景特殊要求
- 医学数据敏感性处理
- 专业术语显示优化
- 科室分类适配移动端
- 直播观看移动端优化

---

**[开始生成指令]**
请严格按照本文档要求，从步骤1开始，逐步生成微信小程序阶段零的所有代码文件。每完成一个步骤，进行自我验证后再继续下一步。所有代码必须适配微信小程序环境并符合移动端设计规范。
