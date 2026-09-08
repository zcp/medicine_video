# 直播SaaS平台微信小程序前端代码生成提示词（总体）

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和微信小程序开发及多端适配。你具备大型直播SaaS平台前端架构与实现经验，能够根据详细设计文档和后端API规范，编写高质量、规范、可维护的微信小程序前端代码。

---

## 2. 任务目标（Task Objective）
本次任务是为“直播SaaS平台”微信小程序项目生成一个完整、可运行的前端应用骨架。

**为确保任务明确、无歧义，本次需具体生成以下完整且详细的前端项目结构框架：**

### A. 项目基础结构与配置文件（Project Skeleton & Config Files）
- **根目录文件与目录 (Root Files & Dirs):**
  - `package.json`, `tsconfig.json`, `vite.config.ts`, `.eslintrc.js`, `.prettierrc`, `jest.config.js`, `.gitignore`, `README.md`, `tests/`, `uni_modules/`
- **核心源码目录 (Core Source Directory):**
  - `src/`: **唯一**的核心源码目录，包含以下所有内容：
    - `App.vue`, `main.ts`, `pages.json`, `manifest.json`, `env.d.ts`
    - `api/`, `common/`, `components/`, `pages/`, `static/`, `store/`, `types/`, `utils/`, `logs/`

### B. 初始化核心业务文件（Initial Core Business Files）
- **接口与状态管理 (`src/api/` & `src/store/`):**
  - `src/api/auth.ts`: 认证相关接口 (登录、注册、验证码、图形验证码、刷新Token)
  - `src/api/room.ts`: 房间相关接口 (房间详情、场次列表、关注/取消关注房间、预约/取消预约场次)
  - `src/api/expert.ts`: 专家相关接口 (专家列表、专家详情、关注/取消关注专家、专家直播列表)
  - `src/api/department.ts`: 科室相关接口 (科室列表、科室内容列表)
  - `src/api/banner.ts`: 焦点图相关接口 (获取焦点图列表)
  - `src/api/settings.ts`: 设置相关接口 (获取/更新用户设置、修改密码、绑定手机/邮箱、发送绑定验证码、清理用户缓存、获取关于信息)
  - `src/api/user.ts`: 用户相关接口 (获取用户个人资料、更新用户个人资料、获取我的关注列表、获取观看历史、退出登录)
  - `src/api/tags.ts`: 标签相关接口 (获取标签列表、创建标签、更新标签、删除标签) **【新增】**
  - `src/api/brands.ts`: 品牌相关接口 (获取品牌列表、品牌详情及关联专题、品牌CRUD、品牌专题关联管理) **【新增】**
  - `src/api/favorites.ts`: 用户收藏接口 (收藏列表、添加收藏、取消收藏、收藏状态检查) **【新增】**
  - `src/api/history.ts`: 观看历史接口 (观看历史、添加记录、更新进度、删除历史、清空历史) **【新增】**
  - `src/api/notifications.ts`: 通知接口 (通知列表、标记已读、未读数量、删除通知) **【新增】**
  - `src/api/subscriptions.ts`: 订阅提醒接口 (订阅列表、订阅房间、订阅场次、取消订阅、订阅状态检查) **【新增】**
  - `src/store/index.ts`: Pinia 入口文件
  - `src/store/auth.ts`: 认证状态管理 (用户Token、刷新Token)
  - `src/store/user.ts`: 用户状态管理 (用户信息、登录状态)
  - `src/store/room.ts`: 房间状态管理 (当前房间详情、场次列表)
  - `src/store/session.ts`: 场次状态管理 (Feed流列表、分页信息)
  - `src/store/settings.ts`: 用户设置状态管理 (深色模式、字体大小、流量提醒、固定科室)
  - `src/store/ui.ts`: UI状态管理 (首页视图模式)
  - `src/store/tags.ts`: 标签状态管理 (标签列表、选中标签、搜索筛选) **【新增】**
  - `src/store/brands.ts`: 品牌状态管理 (品牌列表、品牌详情、专题关联) **【新增】**
  - `src/store/favorites.ts`: 用户收藏状态管理 (收藏列表、收藏状态、分页数据) **【新增】**
  - `src/store/notifications.ts`: 通知状态管理 (通知列表、未读数量、通知类型筛选) **【新增】**
- **全局类型定义 (`src/types/`):**
  - `src/types/auth.ts`: 认证相关类型定义
  - `src/types/room.ts`: 房间相关类型定义
  - `src/types/expert.ts`: 专家相关类型定义
  - `src/types/department.ts`: 科室相关类型定义
  - `src/types/banner.ts`: 焦点图相关类型定义
  - `src/types/settings.ts`: 设置相关类型定义
  - `src/types/user.ts`: 用户相关类型定义
  - `src/types/tags.ts`: 标签相关类型定义 **【新增】**
  - `src/types/brands.ts`: 品牌相关类型定义 **【新增】**
  - `src/types/favorites.ts`: 用户收藏类型定义 **【新增】**
  - `src/types/history.ts`: 观看历史类型定义 **【新增】**
  - `src/types/notifications.ts`: 通知类型定义 **【新增】**
  - `src/types/subscriptions.ts`: 订阅提醒类型定义 **【新增】**
- **全局工具 (`src/utils/`):**
  - `src/utils/request.ts`: 基于`uni.request`的统一请求封装
  - `src/utils/time.ts`: 时间格式化工具
  - `src/utils/common.ts`: 通用工具函数 (数字格式化等)
  - `src/utils/validator.ts`: 表单校验工具
- **核心业务页面 (`src/pages/`):**
  - `src/pages/auth/Login.vue`: 登录页面
  - `src/pages/auth/Register.vue`: 注册页面
  - `src/pages/auth/ForgotPassword.vue`: 忘记密码页面
  - `src/pages/home/Home.vue`: 首页
  - `src/pages/room/RoomList.vue`: 房间列表页 (我的直播 - 我的房间)
  - `src/pages/room/RoomDetail.vue`: 房间详情页
  - `src/pages/live/LiveView.vue`: 直播观看页
  - `src/pages/department/DepartmentList.vue`: 科室列表页
  - `src/pages/expert/ExpertList.vue`: 专家列表页
  - `src/pages/expert/ExpertDetail.vue`: 专家详情页
  - `src/pages/my-live/MyLive.vue`: 我的直播页面
  - `src/pages/my-live/CreateSession.vue`: 创建直播场次页面
  - `src/pages/my-live/EditSession.vue`: 编辑直播场次页面
  - `src/pages/my-live/Statistics.vue`: 数据统计页面
  - `src/pages/my-live/Revenue.vue`: 收益中心页面
  - `src/pages/my-live/HostApply.vue`: 主播申请页面
  - `src/pages/profile/Profile.vue`: 我的页面
  - `src/pages/profile/ProfileEdit.vue`: 个人资料编辑页面
  - `src/pages/profile/FollowingList.vue`: 我的关注列表页面
  - `src/pages/profile/FollowerList.vue`: 我的粉丝列表页面
  - `src/pages/profile/ViewHistory.vue`: 观看历史页面
  - `src/pages/profile/CollectionList.vue`: 我的收藏页面
  - `src/pages/profile/OrderList.vue`: 我的订单页面
  - `src/pages/profile/CouponList.vue`: 我的优惠页面
  - `src/pages/settings/Settings.vue`: 设置页面
  - `src/pages/settings/ChangePassword.vue`: 修改密码页面
  - `src/pages/settings/BindPhone.vue`: 绑定手机页面
  - `src/pages/settings/BindEmail.vue`: 绑定邮箱页面
  - `src/pages/settings/ThirdPartyAccounts.vue`: 第三方账号管理页面
  - `src/pages/settings/Blacklist.vue`: 黑名单页面
  - `src/pages/feedback/Feedback.vue`: 帮助与反馈页面
  - `src/pages/about/About.vue`: 关于我们页面
  - `src/pages/about/PrivacyPolicy.vue`: 隐私政策页面
  - `src/pages/webview/Webview.vue`: 通用Webview页面
  - `src/pages/common/NotFound.vue`: 404页面
- **核心通用组件 (`src/components/`):**
  - `src/components/common/AppButton.vue`: 通用按钮组件
  - `src/components/common/ModalDialog.vue`: 通用弹窗组件
  - `src/components/common/LoadingIndicator.vue`: 全局Loading指示器
  - `src/components/common/ErrorBanner.vue`: 全局错误提示条
  - `src/components/common/LiveCard.vue`: 直播卡片组件 (用于Feed流、直播列表等)
  - `src/components/common/ExpertCard.vue`: 专家卡片组件 (用于专家列表、科室内容列表)
  - `src/components/common/ArticleCard.vue`: 文章卡片组件 (用于科室内容列表)
  - `src/components/auth/LoginForm.vue`: 登录表单组件
  - `src/components/auth/ThirdPartyLogin.vue`: 第三方登录组件
  - `src/components/home/TopBar.vue`: 首页顶部栏组件
  - `src/components/home/CategoryTabs.vue`: 首页分类筛选器组件
  - `src/components/home/FollowingUpdates.vue`: 首页我的关注动态组件
  - `src/components/home/Banner3D.vue`: 首页3D焦点图轮播组件
  - `src/components/home/FeedList.vue`: 首页Feed流列表组件
  - `src/components/home/QuickMenu.vue`: 首页快捷菜单组件
  - `src/components/room/RoomHeader.vue`: 房间详情头部组件
  - `src/components/room/SessionTabs.vue`: 房间详情直播场次Tab组件
  - `src/components/room/ExpertMiniCard.vue`: 房间详情专家简介卡片组件
  - `src/components/department/DepartmentCategoryNav.vue`: 科室分类导航组件
  - `src/components/department/DepartmentContentList.vue`: 科室内容列表组件
  - `src/components/expert/SearchBar.vue`: 专家列表搜索栏组件
  - `src/components/expert/SpecialtyFilter.vue`: 专家列表专业领域筛选器组件
  - `src/components/expert/ExpertList.vue`: 专家列表组件
  - `src/components/my-live/QuickActions.vue`: 我的直播快捷操作区组件
  - `src/components/my-live/LiveStatusCard.vue`: 我的直播状态卡片组件
  - `src/components/my-live/SessionHistory.vue`: 我的直播历史列表组件
  - `src/components/my-live/HostApplyGuide.vue`: 我的直播主播申请引导组件
  - `src/components/profile/UserCard.vue`: 我的页面用户卡片组件
  - `src/components/profile/QuickAccess.vue`: 我的页面快捷入口组件
  - `src/components/profile/FunctionList.vue`: 我的页面功能列表组件
  - `src/components/profile/LogoutButton.vue`: 退出登录按钮组件
  - `src/components/settings/GeneralSettings.vue`: 设置页面通用设置组组件
  - `src/components/settings/AccountSecurity.vue`: 设置页面账号与安全组组件
  - `src/components/settings/PrivacySettings.vue`: 设置页面隐私管理组组件
  - `src/components/settings/InfoAndActions.vue`: 设置页面通用信息与操作组组件

所有生成内容需严格对齐《直播SaaS平台前端设计文档.md》、各模块设计文档和后端接口规范，满足多端适配、无障碍、安全、性能等要求。

---

## 3. 核心上下文信息（Core Context Information）

### 3.1 推荐项目结构（与设计文档对齐，需标注生成状态）
- 目录结构严格遵循《直播SaaS平台前端设计文档.md》第 3.3 节和第 5.1 节。请根据实际生成情况为每项标注“已生成”或“需生成”：
  - `src/pages/` # 页面（如直播间、房间列表、分会场等）
  - `src/components/` # 通用/业务组件
  - `src/store/` # 状态管理
  - `src/api/` # 接口封装
  - `src/utils/` # 工具函数
  - `src/static/` # 静态资源
  - `src/common/` # 公共样式、mixin
  - `src/types/` # TypeScript类型定义
  - `uni_modules/` # uni-app插件
  - `tests/` # 测试用例
  - `package.json` # 项目依赖
  - `tsconfig.json` # TypeScript 配置
  - `src/manifest.json` # uni-app 应用配置
  - `src/pages.json` # uni-app 页面配置
  - `src/common/uni.scss` # uni-app 全局样式
  - `src/App.vue` # Vue 应用入口文件
  - `src/main.ts` # Vue 初始化脚本
  - `README.md` # 项目说明
  - `src/logs/` # 日志管理模块

### 3.2 依赖与初始化要求
- 需自动生成并配置：uni-app项目初始化、package.json、tsconfig.json、eslint/prettier配置。
- 需自动在 `src/` 目录下生成并配置：`pages.json`、`manifest.json`。
- 需自动在 `src/common/` 目录下生成 `uni.scss`。
- 需自动安装并配置：Vue3、TypeScript、Pinia、uView/NutUI/Vant、jest等依赖。
- 需自动生成全局样式、常量、接口请求封装、状态管理入口等基础文件。

---

## 4. 全局强制性约束与最高准则 (Global Mandatory Constraints & Ultimate Principle)
- **最高准则**: 本次任务的**唯一且最高准则**是：所有生成内容必须与《直播SaaS平台前端设计文档.md》、`直播SaaS平台移动端前端设计文档(微信小程序).md` 和**《后端新增api接口和模块设计文档-v2.md》**规范**100%完全一致**。任何细节的偏离、遗漏或自由发挥都是**绝对禁止**的。
- **新增API模块要求**: 必须完整实现Tags标签管理、Brands品牌管理、用户收藏(Favorites)、观看历史(History)、通知系统(Notifications)、订阅提醒(Subscriptions)等6个新增模块的完整功能，包括对应的API封装、类型定义、状态管理和UI组件。
- **零偏差原则**: 你必须像一个代码编译器一样，精确地将设计文档翻译成代码。不允许任何形式的“优化”或“变通”，除非设计文档明确授权。
- **命名与结构**: 所有目录、文件、组件、变量、函数、CSS类名的命名，都必须严格采用设计文档中指定的命名方案。
- **冲突解决**: 如果在生成过程中发现任何疑似冲突或模糊不清之处，必须以《直播SaaS平台前端设计文档.md》和 `直播SaaS平台移动端前端设计文档(微信小程序).md` 为唯一判断依据。

---

## 5. 分步生成与交叉验证流程 (Step-by-Step Generation & Cross-Validation Flow)
**[流程指令]** 你必须严格按照以下步骤顺序生成代码，完成一步后，进行该步骤的交叉验证，然后再进入下一步。禁止跳过、合并或打乱顺序。

### 步骤1：API 层生成（api/）
- **[约束]** 本步骤所有产出必须严格遵循《直播SaaS平台前端设计文档.md》、`直播SaaS平台移动端前端设计文档(微信小程序).md` 和**《后端新增api接口和模块设计文档-v2.md》**中定义的API规范。
- **目标**：生成所有后端接口的 TypeScript 封装文件（包括原有模块：auth.ts, room.ts, session.ts, expert.ts, department.ts, banner.ts, settings.ts, user.ts 和**新增模块：tags.ts, brands.ts, favorites.ts, history.ts, notifications.ts, subscriptions.ts**）及统一请求封装（request.ts）。
- **要求**：函数签名、参数（名称、类型、顺序）、返回类型、接口路径、请求方法、Token自动注入逻辑等，必须与后端接口定义一一对应，分毫不差。新增API模块必须与v2.md文档中的接口定义100%一致。
- **验证点**：
  - [ ] 是否所有接口都被实现？
  - [ ] 每个接口的请求/响应数据结构是否与后端Schema完全匹配？
  - [ ] 错误处理逻辑是否按文档实现？

### 步骤2：状态管理层生成（store/）
- **[约束]** 本步骤所有产出必须严格对齐后端数据模型和前端设计文档中的状态管理章节。
- **目标**：生成Pinia状态管理文件（包括原有Store：auth.ts, user.ts, room.ts, session.ts, settings.ts, ui.ts, index.ts 和**新增Store：tags.ts, brands.ts, favorites.ts, notifications.ts**）。
- **要求**：Store的State结构、字段名、类型、初始值，必须与后端数据模型（Schema）和设计文档的定义完全一致。Actions必须准确调用API层方法，新增Store必须完整支持对应功能模块的业务逻辑。
- **验证点**：
  - [ ] State的数据结构是否与后端模型完全一致？
  - [ ] Actions是否正确调用了步骤1中生成的API？
  - [ ] Getters的计算逻辑是否符合设计？

### 步骤3：通用工具与全局样式生成（utils/、common/）
- **[约束]** 本步骤所有产出必须严格实现设计文档中的通用规范。
- **目标**：生成时间格式化、表单校验、安全工具、全局常量、响应式断点、全局SCSS变量和混合等。
- **要求**：所有工具函数、常量值、颜色值、字体大小、间距、响应式断点值，必须与设计规范中的定义完全一致。
- **验证点**：
  - [ ] 全局样式变量（颜色、字体、间距）是否与UI规范一致？
  - [ ] 工具函数的输入输出是否符合设计？

### 步骤4：通用组件生成（components/）
- **[约束]** 本步骤所有产出必须严格复刻设计文档中的组件设计。
- **目标**：生成高复用、风格统一、无状态或轻状态的通用组件（如 AppButton, ModalDialog, LiveCard, ExpertCard, ArticleCard, LoginForm, ThirdPartyLogin 等）。
- **要求**：组件的`props`（名称、类型、默认值）、`emits`（事件名、载荷）、`slots`，必须与设计文档完全一致。包含完整的样式、交互反馈、注释和类型声明。必须实现ARIA等无障碍规范。
- **验证点**：
  - [ ] 组件API（props/emits/slots）是否与设计文档一致？
  - [ ] 组件的各种状态（如hover, disabled）下的样式是否符合设计？
  - [ ] 无障碍属性是否按规范添加？

### 步骤5：页面级组件生成（pages/）
- **[约束]** 本步骤所有产出必须严格聚合已有模块，精确实现页面设计。
- **目标**：按业务模块生成所有页面（如 auth, home, room, live, department, expert, my-live, profile, settings, feedback, about, webview, common 等）。
- **要求**：严格按照设计文档组织页面结构，调用Store中的Actions获取和提交数据，使用通用组件搭建UI。页面的交互流程、路由跳转、参数传递、骨架屏、Loading、错误提示等，必须完整实现设计文档的每一个细节。
- **验证点**：
  - [ ] 页面布局、组件使用、数据流转是否与设计文档一致？
  - [ ] 是否处理了所有在文档中定义的交互场景？
  - [ ] 加载、成功、失败、空状态的UI/UX是否都已实现？

### 步骤6：测试用例生成（tests/）
- **[约束]** 本步骤所有产出必须为已生成的代码提供充分的质量保证。
- **目标**：生成单元、集成测试用例，覆盖核心的API、Store、组件和页面逻辑。
- **要求**：测试用例必须覆盖设计文档中定义的核心业务流程、边界条件和异常场景。Mock数据必须与后端接口的真实结构保持一致。
- **验证点**
  - [ ] 核心组件和函数的测试覆盖率是否达标？
  - [ ] 是否覆盖了设计文档中描述的异常处理流程？

---

## 6. 核心模块生成指令（示例）

### 6.1 登录模块（`docs/登录_模块设计文档.md`）
- **页面**: `src/pages/auth/Login.vue`, `src/pages/auth/Register.vue`, `src/pages/auth/ForgotPassword.vue`
- **组件**: `src/components/auth/LoginForm.vue`, `src/components/auth/ThirdPartyLogin.vue`
- **API**: `src/api/auth.ts`
- **Store**: `src/store/auth.ts`
- **主要功能**: 手机号+验证码登录、账号密码登录、微信一键登录、用户注册、忘记密码、图形验证码。
- **微信小程序特性**: 微信一键登录使用 `uni.login` 和 `uni.getUserProfile`。

### 6.2 房间详情模块（`docs/房间详情_模块设计文档.md`）
- **页面**: `src/pages/room/RoomDetail.vue`
- **组件**: `src/components/room/RoomHeader.vue`, `src/components/room/SessionTabs.vue`, `src/components/room/ExpertMiniCard.vue`
- **API**: `src/api/room.ts`, `src/api/expert.ts`
- **Store**: `src/store/room.ts`
- **主要功能**: 房间信息展示、主播信息、关注房间、分享、直播场次列表（预告/历史）、预约/取消预约。
- **微信小程序特性**: `uni.showShareMenu` 实现分享。

### 6.3 科室模块（`docs/科室_模块设计文档.md`）
- **页面**: `src/pages/department/DepartmentList.vue`
- **组件**: `src/components/department/DepartmentCategoryNav.vue`, `src/components/department/DepartmentContentList.vue`, `src/components/common/LiveCard.vue`, `src/components/common/ExpertCard.vue`, `src/components/common/ArticleCard.vue`
- **API**: `src/api/department.ts`
- **Store**: 无特定，可能与 `src/store/session.ts` 共享数据。
- **主要功能**: 科室分类导航、科室内容列表（直播、专家、文章混合）、内容筛选、无限滚动加载。
- **微信小程序特性**: `scroll-view` 实现横向滚动导航。

### 6.4 设置模块（`docs/设置_模块设计文档.md`）
- **页面**: `src/pages/settings/Settings.vue`, `src/pages/settings/ChangePassword.vue`, `src/pages/settings/BindPhone.vue`, `src/pages/settings/BindEmail.vue`, `src/pages/settings/ThirdPartyAccounts.vue`, `src/pages/settings/Blacklist.vue`, `src/pages/feedback/Feedback.vue`, `src/pages/about/About.vue`, `src/pages/about/PrivacyPolicy.vue`
- **组件**: `src/components/settings/GeneralSettings.vue`, `src/components/settings/AccountSecurity.vue`, `src/components/settings/PrivacySettings.vue`, `src/components/settings/InfoAndActions.vue`, `src/components/profile/LogoutButton.vue`
- **API**: `src/api/settings.ts`, `src/api/auth.ts`, `src/api/user.ts`
- **Store**: `src/store/settings.ts`
- **主要功能**: 日/夜间模式、字体大小、流量提醒、修改密码、绑定手机/邮箱、第三方账号管理、授权管理、黑名单设置、清理缓存、版本信息、用户协议/隐私政策、帮助与反馈、联系客服、退出登录。
- **微信小程序特性**: `uni.openSetting` 调用原生授权设置，`uni.clearStorageSync` 清理本地存储，`uni.makePhoneCall` 联系客服。

### 6.5 首页模块（`docs/首页_模块设计文档.md`）
- **页面**: `src/pages/home/Home.vue`
- **组件**: `src/components/home/TopBar.vue`, `src/components/home/CategoryTabs.vue`, `src/components/home/FollowingUpdates.vue`, `src/components/home/Banner3D.vue`, `src/components/home/FeedList.vue`, `src/components/home/QuickMenu.vue`, `src/components/RoomCard.vue`
- **API**: `src/api/category.ts`, `src/api/user.ts`, `src/api/banner.ts`, `src/api/session.ts`
- **Store**: `src/store/settings.ts`, `src/store/ui.ts`, `src/store/session.ts`, `src/store/user.ts`
- **主要功能**: 顶部搜索栏、消息中心入口、分类筛选器（支持星标固定）、我的关注动态、3D焦点图轮播、直播/回放Feed流（双列/单列切换）、快捷菜单（长按Tab唤起）。
- **微信小程序特性**: 底部Tab长按事件（通过全局事件总线模拟）、`scroll-view`、`swiper` 组件。

### 6.6 我的模块（`docs/我的_模块设计文档.md`）
- **页面**: `src/pages/profile/Profile.vue`, `src/pages/profile/ProfileEdit.vue`, `src/pages/profile/FollowingList.vue`, `src/pages/profile/FollowerList.vue`, `src/pages/profile/ViewHistory.vue`, `src/pages/profile/CollectionList.vue`, `src/pages/profile/OrderList.vue`, `src/pages/profile/CouponList.vue`
- **组件**: `src/components/profile/UserCard.vue`, `src/components/profile/QuickAccess.vue`, `src/components/profile/FunctionList.vue`, `src/components/profile/LogoutButton.vue`
- **API**: `src/api/user.ts`, `src/api/auth.ts`
- **Store**: `src/store/user.ts`
- **主要功能**: 用户信息展示（头像、昵称、ID、关注/粉丝数）、登录/未登录状态切换、快捷功能入口（观看历史、我的收藏、我的订单、我的优惠）、功能列表（设置、帮助与反馈、关于我们、隐私政策）、主播认证入口、退出登录。
- **微信小程序特性**: `uni.navigateTo` 进行页面跳转。

### 6.7 我的直播模块（`docs/我的直播_模块设计文档.md`）
- **页面**: `src/pages/my-live/MyLive.vue`, `src/pages/my-live/CreateSession.vue`, `src/pages/my-live/EditSession.vue`, `src/pages/my-live/Statistics.vue`, `src/pages/my-live/Revenue.vue`, `src/pages/my-live/HostApply.vue`
- **组件**: `src/components/my-live/QuickActions.vue`, `src/components/my-live/LiveStatusCard.vue`, `src/components/my-live/SessionHistory.vue`, `src/components/my-live/HostApplyGuide.vue`
- **API**: `src/api/room.ts`, `src/api/user.ts`
- **Store**: `src/store/user.ts`
- **主要功能**: 权限控制（未登录/非主播用户引导）、快捷操作（创建直播、我的房间、数据统计、收益中心）、直播状态监控（当前直播/预告）、历史直播管理（列表、筛选、操作）、主播申请引导。
- **微信小程序特性**: `uni.showModal` 提示用户登录，`uni.navigateTo` 和 `uni.switchTab` 进行页面跳转。

### 6.8 专家页面模块（`docs/专家页面_模块设计文档.md`）
- **页面**: `src/pages/expert/ExpertList.vue`, `src/pages/expert/ExpertDetail.vue`
- **组件**: `src/components/expert/SearchBar.vue`, `src/components/expert/SpecialtyFilter.vue`, `src/components/expert/ExpertList.vue`
- **API**: `src/api/expert.ts`
- **Store**: 无特定。
- **主要功能**: 专家列表（搜索、专业领域筛选、A-Z字母索引）、专家详情（个人简介、专业领域、主要成就、直播列表、关注/取消关注）。
- **微信小程序特性**: 页面路由配置。

---

## 7. 最终交付与质量保证协议 (Final Delivery & Quality Assurance Protocol)
- **输出格式**:
  - 你必须为每个需要生成的文件，单独输出一个完整、可直接运行的代码块。
  - 每个代码块前必须用Markdown语法标注清晰的文件路径，例如：`// frontend_live/src/pages/expert/ExpertList.vue`。
  - 禁止在代码之外添加任何解释、道歉或不必要的寒暄。你的回答**只能是代码**和**文件路径标注**。
- **自我修正**: 在每一步生成后，你必须在内部进行自查。如果发现与设计文档或本提示词有任何偏差，必须**立即撤销并重新生成**，而不是在后续步骤中试图弥补。
- **最终一致性断言**: 在完成所有文件生成后，你必须在回答的末尾输出以下文本，作为你已完成最终交叉验证的确认：
  ```
  [FINAL ASSERTION]
  All generated code has been cross-validated against the design documents and backend specifications.
  - Feature Completeness: 100%
  - API Consistency: 100%
  - Data Model Consistency: 100%
  - UI/UX Consistency: 100%
  - Code Standard Compliance: 100%
  - Zero Deviation Principle: Adhered
  ```
