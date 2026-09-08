# 直播SaaS平台移动端前端设计文档 (V1.3)

---

## 1. 角色定位说明

**作者角色：资深移动端前端工程师**

- 具备大型直播平台（如Bilibili、抖音）移动端前端架构与实现经验
- 精通 uni-app、Vue3、TypeScript、移动端H5、小程序等跨端开发技术
- 熟悉高并发、低延迟直播场景下的移动端性能优化与用户体验设计
- 擅长移动端交互设计、手势识别、响应式布局、无障碍支持
- 具备医学SaaS平台业务理解能力，关注专业性与易用性平衡

---

## 2. 文档目的与项目背景

### 2.1 文档目的

本设计文档旨在为"医学直播SaaS平台"移动端项目（App/小程序）提供系统性、标准化的设计与开发指导，确保团队协作高效、代码质量可控、功能实现与后端接口高度一致，同时满足移动端用户的独特使用习惯和场景需求。

### 2.2 项目背景

- **技术架构**：前后端分离，后端接口详见《后端新增api接口和模块设计文档-v2.md》
- **前端技术栈**：基于 uni-app 框架，支持H5、Android App、iOS App、微信小程序等多端部署
- **设计参考**：借鉴Bilibili、抖音等主流视频平台的移动端UI/UX范式，结合医学直播专业场景需求
- **核心目标**：打造专业、高效且符合移动用户习惯的医学直播应用

### 2.3 设计原则

1. **移动优先 (Mobile First)**：所有设计从移动端场景出发，考虑触屏操作、单手使用、弱网环境
2. **专业与易用并重**：保留医学直播的专业性（专家认证、病例讨论、问答），同时简化操作流程
3. **性能优化**：关注首屏加载时间、流畅度、流量消耗、电量管理
4. **渐进增强**：核心功能优先保证，高级功能按需加载
5. **无障碍支持**：符合WCAG 2.1标准，支持屏幕阅读器、键盘操作

---

## 3. 移动端前端开发规范

### 3.1 代码规范

#### 3.1.1 基础规范
- **统一风格**：全项目采用 ESLint + Prettier 自动格式化，统一2空格缩进，单引号，无分号
- **TypeScript 强制**：所有新开发页面和组件必须使用 TypeScript，类型声明完整
- **组件化开发**：每个页面/业务功能拆分为小型、可复用的组件
- **禁止魔法数字**：所有常量、枚举、配置项集中管理（如 `src/common/constants.ts`）
- **注释规范**：关键业务逻辑、接口调用、复杂计算必须有中文注释，函数/组件需有JSDoc风格注释

#### 3.1.2 移动端特有规范
- **触摸优化**：
  - 所有可点击元素最小尺寸 ≥ 44x44px（iOS规范）或 48x48dp（Android规范）
  - 重要操作按钮间距 ≥ 8px，避免误触
- **手势支持**：
  - 支持滑动返回（iOS）、长按、双击等手势
  - 避免与系统手势冲突（如iOS底部上滑手势）
- **性能优化**：
  - 列表使用虚拟滚动（超过50项）
  - 图片懒加载，使用 `lazy-load="true"`
  - 避免大量DOM操作，使用 `v-show` 代替频繁的 `v-if`
- **尺寸单位**：
  - 统一使用 `rpx`（responsive pixel），uni-app会自动转换为各平台单位
  - 1rpx = 屏幕宽度/750

### 3.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `liveRoomList`, `handleCategoryChange` |
| 组件/页面文件 | PascalCase | `CategoryTabs.vue`, `RoomCard.vue` |
| 文件/目录 | kebab-case | `live-room-list/`, `category-tabs.vue` |
| 常量 | UPPER_SNAKE_CASE | `MAX_ROOM_COUNT`, `API_TIMEOUT` |
| CSS类名 | kebab-case | `.room-card`, `.category-tab-active` |
| API接口文件 | 小写 | `api/homepage.ts`, `api/category.ts` |
| 状态管理 | 小写 | `store/modules/homepage.ts` |
| TypeScript类型/接口 | PascalCase | `RoomItem`, `CategoryResponse` |

### 3.3 项目结构规范

```plaintext
live_app_mobile/                      # uni-app移动端项目根目录
├── src/
│   ├── App.vue                       # 应用入口主组件
│   ├── main.ts                       # 应用入口JS
│   ├── pages.json                    # uni-app页面路由配置
│   ├── manifest.json                 # uni-app应用配置
│   ├── env.d.ts                      # 全局TypeScript环境声明
│   ├── uni.scss                      # 全局样式变量（颜色、字体、间距）
│   │
│   ├── pages/                        # 页面级组件
│   │   ├── tabbar/                   # 底部Tab页面
│   │   │   ├── home/                 # 首页
│   │   │   ├── brand/                # 品牌专区
│   │   │   ├── my-live/              # 我的直播（主播后台）
│   │   │   ├── expert/               # 专家专题
│   │   │   └── my/                   # 我的页面
│   │   ├── room/                     # 直播间相关
│   │   │   ├── detail.vue            # 直播间详情页
│   │   │   └── fullscreen.vue        # 全屏播放器
│   │   ├── category/                 # 分类相关
│   │   │   ├── all.vue               # 全部科室列表
│   │   │   └── manage.vue            # 管理星标科室
│   │   ├── search/                   # 搜索相关
│   │   ├── message/                  # 消息中心
│   │   ├── auth/                     # 登录注册
│   │   └── common/                   # 通用页面
│   │       ├── 404.vue               # 404页面
│   │       ├── error.vue             # 错误页面
│   │       └── webview.vue           # 内嵌网页
│   │
│   ├── components/                   # 组件目录
│   │   ├── common/                   # 通用UI组件
│   │   │   ├── TopBar.vue            # 顶部栏
│   │   │   ├── TabBar.vue            # 底部导航栏
│   │   │   ├── Loading.vue           # 加载动画
│   │   │   └── Empty.vue             # 空状态
│   │   └── business/                 # 业务组件
│   │       ├── RoomCard.vue          # 直播卡片
│   │       ├── CategoryTabs.vue      # 分类筛选器
│   │       ├── CarouselBanner.vue    # 焦点图轮播
│   │       ├── BrandCard.vue         # 品牌卡片
│   │       ├── ExpertCard.vue        # 专家卡片
│   │       ├── CommentItem.vue       # 评论项
│   │       └── VideoPlayer.vue       # 视频播放器
│   │
│   ├── api/                          # 后端接口封装
│   │   ├── config.ts                 # API配置（BASE_URL、TIMEOUT等）
│   │   ├── request.ts                # 统一请求封装（基于uni.request）
│   │   ├── mock.ts                   # Mock数据层
│   │   ├── homepage.ts               # 首页API
│   │   ├── category.ts               # 分类API
│   │   ├── room.ts                   # 房间API
│   │   ├── session.ts                # 场次API
│   │   ├── brand.ts                  # 品牌API
│   │   ├── expert.ts                 # 专家API
│   │   ├── user.ts                   # 用户API
│   │   ├── favorite.ts               # 收藏API
│   │   ├── subscription.ts           # 订阅API
│   │   ├── message.ts                # 消息API
│   │   ├── search.ts                 # 搜索API
│   │   └── index.ts                  # API统一导出
│   │
│   ├── store/                        # 全局状态管理（Pinia）
│   │   ├── index.ts                  # Pinia实例初始化
│   │   └── modules/                  # Store模块
│   │       ├── app.ts                # 全局应用状态
│   │       ├── user.ts               # 用户状态
│   │       ├── homepage.ts           # 首页状态
│   │       ├── category.ts           # 分类状态
│   │       ├── room.ts               # 房间状态
│   │       ├── brand.ts              # 品牌状态
│   │       ├── expert.ts             # 专家状态
│   │       └── message.ts            # 消息状态
│   │
│   ├── types/                        # 全局TypeScript类型定义
│   │   ├── models.ts                 # 核心数据模型
│   │   ├── api.ts                    # API响应类型
│   │   ├── enums.ts                  # 枚举类型
│   │   └── components.ts             # 组件Props类型
│   │
│   ├── utils/                        # 工具函数
│   │   ├── time.ts                   # 时间格式化
│   │   ├── storage.ts                # 本地存储封装
│   │   ├── validate.ts               # 表单校验
│   │   ├── security.ts               # 安全相关（脱敏、加密）
│   │   ├── network.ts                # 网络检测
│   │   ├── logger.ts                 # 日志工具
│   │   ├── permission.ts             # 权限管理
│   │   └── index.ts                  # 工具函数统一导出
│   │
│   ├── common/                       # 全局公共资源
│   │   ├── constants.ts              # 常量定义
│   │   ├── enums.ts                  # 枚举定义
│   │   └── theme.scss                # 主题样式变量
│   │
│   ├── static/                       # 静态资源
│   │   ├── images/                   # 图片资源
│   │   ├── icons/                    # 图标资源
│   │   └── fonts/                    # 字体资源
│   │
│   └── logs/                         # 日志管理模块
│       ├── logger.ts                 # 日志记录实现
│       ├── logTypes.ts               # 日志类型定义
│       └── logConfig.ts              # 日志配置
│
├── tests/                            # 测试用例
├── uni_modules/                      # uni-app插件
├── package.json                      # 项目依赖与脚本
├── vite.config.ts                    # Vite 构建配置
├── tsconfig.json                     # TypeScript 编译器配置
├── .eslintrc.js                      # ESLint 代码规范配置
├── .prettierrc                       # Prettier 代码格式化配置
├── index.html                        # H5入口（uni-app H5编译使用）
└── README.md                         # 项目说明文档
```

### 3.4 Git 提交规范

采用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构（不是新功能也不是Bug修复）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例**：
```
feat(homepage): 添加首页双列瀑布流布局

- 实现双列/单列视图切换功能
- 支持长按Tab触发视图菜单
- 用户偏好保存到LocalStorage

Closes #123
```

---

### 3.5 前端日志管理与设置规范

本节定义移动端前端日志管理的完整规范，确保日志记录、脱敏、上报、监控等各环节符合医学数据安全要求，同时兼顾移动端特有的存储、流量、电量等约束。

---

#### 3.5.1 设计原则

1. **安全第一**：所有日志记录必须经过脱敏处理，禁止上报任何敏感用户信息（手机号、身份证、密码、Token、患者信息、病历内容等）。
2. **移动优先**：考虑移动端存储限制、流量消耗、电量管理等特殊约束。
3. **性能优化**：日志记录与上报必须采用异步方式，避免影响用户体验。
4. **统一标准**：与PC端日志规范保持一致，便于后端统一处理和分析。
5. **可追溯性**：所有关键操作、异常、性能问题必须有完整日志记录。

---

#### 3.5.2 日志级别定义

采用标准日志级别体系，所有日志记录必须明确指定级别：

| 日志级别 | 用途 | 示例场景 |
|---------|------|---------|
| **DEBUG** | 调试信息，仅开发环境 | 变量值、函数调用、数据流转 |
| **INFO** | 一般信息，记录关键流程 | 用户登录、页面加载、API调用成功 |
| **WARN** | 警告信息，非致命错误 | 接口慢查询、降级处理、兼容性警告 |
| **ERROR** | 错误信息，需要关注 | 接口失败、业务逻辑异常、资源加载失败 |
| **FATAL** | 严重错误，影响核心功能 | 应用崩溃、数据丢失、安全异常 |

**级别控制**：
- 开发环境（dev）：记录所有级别（DEBUG及以上）
- 测试环境（test）：记录INFO及以上
- 生产环境（prod）：记录WARN及以上
- 特殊调试：可通过远程配置临时开启DEBUG日志

---

#### 3.5.3 日志记录内容规范

**必需字段**（所有日志必须包含）：
- **timestamp**：时间戳，ISO 8601格式（如：2025-11-07T10:30:45.123Z）
- **level**：日志级别（DEBUG/INFO/WARN/ERROR/FATAL）
- **module**：模块名称（如：HomePage、RoomDetail、APIService）
- **message**：日志描述信息
- **platform**：平台标识（h5/android/ios/mp-weixin）
- **appVersion**：应用版本号

**可选字段**：
- **details**：详细信息（对象/数组，已脱敏）
- **userId**：用户ID（已hash处理，禁止明文）
- **sessionId**：会话ID（用于追踪用户行为链路）
- **deviceInfo**：设备信息（型号、系统版本、屏幕尺寸、网络类型）

**禁止记录的信息**：
- ❌ 用户手机号、身份证号、邮箱原文
- ❌ 密码、Token、推流密钥等敏感凭证
- ❌ 患者姓名、病历号、诊断信息等医疗隐私
- ❌ 完整的API请求/响应体（可记录摘要或关键字段，需脱敏）
- ❌ 用户输入的原始内容（如聊天记录、评论内容，需脱敏后记录）

**推荐记录的信息**：
- ✅ 用户操作行为（点击、滑动、搜索关键词等，需限制长度）
- ✅ 页面加载性能（首屏时间、白屏时间、API耗时）
- ✅ 异常堆栈信息（已脱敏的错误栈）
- ✅ 网络状态变化（在线/离线、网络类型切换）
- ✅ 资源加载失败（图片、视频URL可保留域名，移除敏感路径）

---

#### 3.5.4 日志脱敏规范

所有上报的日志必须经过脱敏处理，具体规范参见本文档第4.5节《日志脱敏》。

**脱敏处理要点**：
- **敏感字段识别**：通过字段名关键词自动识别（phone、idCard、password、token、patientName等）
- **脱敏规则**：
  - 手机号：保留前3后4位（如：138****5678）
  - 身份证：保留前3后4位（如：420***********1234）
  - 邮箱：保留前2位@后全部（如：ab***@example.com）
  - Token/密码：完全隐藏（显示***）
- **递归处理**：对嵌套对象、数组进行递归脱敏
- **正则匹配**：对字符串内容进行敏感信息模式匹配并脱敏

**工具封装位置**：`src/logs/logUtils.ts`，复用`@/utils/security`中的maskPhone、maskIdCard、maskEmail等工具函数

---

#### 3.5.5 日志系统实现要点

**A. 日志工具封装**（位于 `src/logs/logger.ts`）

核心功能要求：
- **日志记录**：提供debug、info、warn、error、fatal五个级别的记录方法
- **自动脱敏**：所有日志在记录时自动调用脱敏函数，确保敏感信息安全
- **队列管理**：内存中维护日志队列，达到批量上报阈值（默认20条）或定时（60秒）触发上报
- **网络感知**：监听网络状态变化，WiFi环境下立即上报积压日志，移动网络按策略降级
- **级别过滤**：根据环境（dev/test/prod）自动过滤低级别日志，生产环境仅记录WARN及以上
- **用户追踪**：自动记录用户ID（hash处理）、sessionId、设备信息、网络类型等上下文
- **全局捕获**：通过`uni.onError`和`uni.onUnhandledRejection`捕获全局异常和Promise异常
- **生命周期管理**：提供destroy方法，页面卸载时清理定时器并上报剩余日志

**B. 日志脱敏工具**（位于 `src/logs/logUtils.ts`）

实现要点：
- **敏感字段识别**：通过关键词匹配自动识别敏感字段（phone、password、token、idCard、email、patientName等）
- **递归脱敏**：支持对象、数组、字符串的递归脱敏处理
- **正则检测**：对字符串内容进行正则匹配，自动脱敏手机号、身份证号、邮箱等敏感信息
- **灵活脱敏策略**：根据字段类型选择不同脱敏方式（手机号保留前3后4位、密码/Token完全隐藏等）
- **复用安全模块**：调用`@/utils/security`中的maskPhone、maskIdCard、maskEmail等工具函数

**C. 日志配置**（位于 `src/logs/logConfig.ts`）

按环境区分配置：
- **开发环境**：DEBUG级别，控制台输出，不上报服务器，批量10条，30秒间隔
- **测试环境**：INFO级别，控制台输出，上报服务器，批量15条，45秒间隔
- **生产环境**：WARN级别，关闭控制台，上报服务器，批量20条，60秒间隔，仅WiFi上报

可选的远程动态配置：
- 支持通过后端接口动态调整日志级别、上报地址、采样率等参数
- 支持白名单用户强制开启DEBUG级别（用于生产环境问题排查）

---

#### 3.5.5 日志上报机制

**A. 统一上报接口**（位于 `src/api/log.ts`）

- **批量上报API**：`POST /api/v1/logs/batch`，携带应用版本号、平台标识，超时10秒
- **紧急上报API**：`POST /api/v1/logs/urgent`，用于FATAL级别单条上报，超时5秒
- **请求格式**：统一使用`src/api/request.ts`封装，自动注入Token、处理异常、记录请求耗时

**B. 上报策略**

| 触发条件 | 上报方式 | 说明 |
|---------|---------|------|
| 达到批量数量（20条） | 立即上报 | 避免队列过长 |
| 定时触发（60秒） | 批量上报 | 定期清空队列 |
| FATAL级别 | 立即上报 | 紧急错误优先处理 |
| 应用切到后台 | 批量上报 | 防止数据丢失 |
| 网络切换到WiFi | 批量上报 | 流量优化 |
| 应用卸载/关闭 | 批量上报 | 最后一次机会 |

**C. 流量优化（移动端特有）**

根据网络类型智能调整上报策略：
- **WiFi/以太网**：正常上报所有级别日志
- **4G/5G网络**：仅上报ERROR和FATAL级别，其他日志暂存等待WiFi
- **2G/3G网络**：仅上报FATAL级别，避免消耗过多流量
- **无网络**：将日志暂存到本地存储（uni.setStorageSync），网络恢复后自动上报
- **上报失败重试**：失败后最多重试1次，保留最近50条日志防止丢失

---

#### 3.5.6 移动端特有考虑

**A. 存储限制与管理**

| 平台 | 存储限制 | 应对策略 |
|-----|---------|---------|
| 微信小程序 | 10MB总存储 | 最多保留200条日志，超出则覆盖最旧的 |
| H5 | 5-10MB（浏览器限制） | 使用IndexedDB存储，定期清理过期日志 |
| Android App | 相对较大 | 可保留500条日志，定期清理7天前的日志 |
| iOS App | 相对较大 | 可保留500条日志，定期清理7天前的日志 |

**存储管理策略**：
- 定期清理过期日志（默认保留7天）
- 超出存储限制时，移除最旧的日志（FIFO队列）
- 支持手动清理接口，用户可在设置中清空日志

**B. 电量优化**

**低电量模式（电量<20%且未充电）**：
- 降低日志记录级别为ERROR（仅记录错误）
- 延长上报间隔为120秒（正常60秒）
- 关闭详细设备信息收集

**正常模式（电量≥20%或正在充电）**：
- 恢复正常日志记录级别（WARN及以上）
- 恢复正常上报间隔（60秒）

**C. 崩溃日志捕获**

**App端（Android/iOS）**：
- 监听应用崩溃事件，记录崩溃信息（错误栈、设备信息、操作路径）
- 立即保存到本地存储，下次启动时上报
- 使用条件编译 `#ifdef APP-PLUS` 避免其他平台报错

**小程序端（微信/支付宝）**：
- 监听小程序错误事件 `wx.onError` / `my.onError`
- 记录错误信息、页面路径、用户操作
- 小程序隐藏时立即上报未上报的日志

**H5端**：
- 监听 `window.onerror` 全局异常
- 监听 `unhandledrejection` Promise异常
- 记录错误栈、浏览器信息、URL参数

**D. 小程序特殊处理**

**生命周期日志**：
- `onAppShow`：记录小程序显示（场景值、来源页面）
- `onAppHide`：记录小程序隐藏，立即上报未上报的日志
- `onError`：记录小程序错误

**包大小限制**：
- 注意小程序主包2MB限制，日志工具需精简
- 使用分包策略，将日志模块放入子包
- 生产环境关闭控制台输出，减少代码体积

---

#### 3.5.7 日志监控与告警

**实时监控指标**：

| 监控指标 | 告警阈值 | 处理策略 |
|---------|---------|---------|
| ERROR日志频率 | > 100次/分钟 | 立即通知开发团队 |
| 页面加载时间 | > 5秒 | 性能优化告警 |
| API失败率 | > 10% | 后端服务告警 |
| 崩溃率 | > 0.1% | 紧急修复，版本回滚 |
| 白屏率 | > 1% | 前端优化告警 |
| 内存占用 | > 200MB | 性能优化，内存泄漏排查 |

**告警通知渠道**：
- 开发团队：钉钉/企业微信群机器人
- 运维团队：短信/电话通知（紧急告警）
- 管理后台：实时大盘展示、历史告警记录

**监控大盘（建议）**：
- 使用ELK Stack（Elasticsearch + Logstash + Kibana）搭建日志监控大盘
- 或使用Grafana + Loki 搭建轻量级日志监控
- 实时展示关键指标：PV/UV、错误率、崩溃率、性能指标
- 按平台、版本、地区等维度聚合分析
- 支持自定义告警规则和通知渠道

---

#### 3.5.8 日志配置与环境管理

**不同环境的日志配置**（参考PC端规范）：

| 配置项 | 开发环境（dev） | 测试环境（test） | 生产环境（prod） |
|-------|---------------|----------------|----------------|
| 日志级别 | DEBUG | INFO | WARN |
| 控制台输出 | 开启 | 开启 | 关闭 |
| 服务器上报 | 关闭 | 开启 | 开启 |
| 批量数量 | 10条 | 15条 | 20条 |
| 上报间隔 | 30秒 | 45秒 | 60秒 |
| 本地存储量 | 100条 | 150条 | 200条 |
| WiFi优先 | 关闭 | 关闭 | 开启 |

**远程动态配置（可选）**：
- 支持后端下发日志配置，无需发版即可调整
- 白名单用户：指定用户强制开启DEBUG日志
- 采样率：按百分比采样上报（如1%用户上报详细日志，节省成本）
- 上报开关：支持全局关闭日志上报（紧急情况）

**配置文件位置**：`src/logs/logConfig.ts`

---

#### 3.5.9 最佳实践与注意事项

**✅ 推荐做法**

1. **日志分级明确**：INFO记录关键流程，ERROR记录异常，DEBUG仅开发环境
2. **异步上报**：所有日志上报必须异步，避免阻塞主线程
3. **批量处理**：批量上报日志，减少网络请求次数
4. **流量优化**：移动网络环境下降级处理，WiFi环境正常上报
5. **定期清理**：定期清理本地存储的过期日志
6. **监控告警**：设置合理的告警阈值，及时发现问题

**❌ 禁止操作**

1. 禁止记录敏感信息原文（手机号、密码、Token等）
2. 禁止在循环中频繁记录日志（影响性能）
3. 禁止在生产环境开启DEBUG级别（日志量过大）
4. 禁止将日志暴露给用户（安全风险）
5. 禁止无限制存储日志（占用存储空间）

**⚠️ 特殊场景**

- **弱网环境**：降低日志记录频率，仅记录关键操作
- **低电量模式**：仅记录ERROR及以上级别
- **小程序审核**：关闭敏感日志，避免审核不通过
- **隐私合规**：用户可关闭日志上报功能（设置中提供开关）

---

#### 3.5.10 与第4.5节日志脱敏的关系

本节（3.5）定义了移动端日志管理的**完整体系架构**，包括日志级别、记录规范、上报机制、监控告警、移动端特有考虑等宏观规范。

第4.5节《日志脱敏》是本节的**实现细节补充**，专注于脱敏函数的具体实现和代码示例，提供可直接使用的脱敏工具。

**两者的关系**：
- **3.5节**：日志管理的"宏观规范"（做什么、为什么、怎么做）
- **4.5节**：日志脱敏的"微观实现"（具体代码、函数示例、实现细节）

**开发指导**：
1. 先阅读3.5节，理解日志管理的整体架构和规范要求
2. 再参考4.5节，实现具体的日志记录和脱敏工具
3. 综合两节内容，确保日志系统的安全性、性能和完整性

**文件组织**：
- `src/logs/logger.ts`：日志管理核心类（按3.5节规范实现）
- `src/logs/logUtils.ts`：日志脱敏工具（按4.5节示例实现）
- `src/logs/logConfig.ts`：日志配置管理（按3.5.8节配置）
- `src/logs/logTypes.ts`：日志类型定义（TypeScript接口）

---

### 3.6 前端设计概述

#### 3.6.1 框架选型

**核心技术栈**：

- **基础框架**：uni-app (Vue 3 + Composition API + TypeScript)
- **状态管理**：Pinia（Vue官方推荐，替代Vuex）
- **UI组件库**：
  - uView Plus（uni-app专用，跨端兼容性好）
  - NutUI（京东出品，组件丰富）
  - Vant（有赞出品，移动端优先）
  - 按需引入，避免包体积过大
- **视频播放**：
  - uni-app自带 `<video>` 组件（优先，兼容小程序）
  - H5端可选 video.js（功能更强大）
- **网络请求**：基于 `uni.request` 二次封装
  - 自动注入Token
  - 统一异常处理
  - 请求/响应拦截器
  - 适配FastAPI后端RESTful风格
- **路由管理**：uni-app内置路由系统
- **多端适配**：一套代码，H5/Android/iOS/微信小程序多端发布
- **开发工具**：
  - HBuilderX（uni-app官方IDE）
  - VS Code + uni-app插件
  - 微信开发者工具（小程序调试）

#### 3.6.2 核心设计原则

**1. 移动优先 (Mobile First)**
- 所有设计从移动端场景出发
- 考虑触屏操作、单手使用、弱网环境
- 关注流量消耗和电池续航

**2. 组件化与模块化**
- 页面拆分为小型、可复用的组件
- 业务逻辑与UI展示分离
- 统一的组件命名和使用规范

**3. 性能优先**
- 首屏加载时间 < 3秒
- 列表滚动流畅度 ≥ 60fps
- 图片懒加载、虚拟滚动
- 防抖节流优化

**4. 渐进增强**
- 核心功能优先保证
- 高级功能按需加载
- 降级方案覆盖弱网/低端设备

**5. 接口解耦**
- 前端不依赖后端具体实现
- 通过Mock数据支持独立开发
- API版本管理和兼容性处理

#### 3.6.3 项目架构图

```
移动端应用架构
├─ 表现层 (Presentation Layer)
│  ├─ 页面组件 (Pages)
│  ├─ 业务组件 (Business Components)
│  └─ 通用组件 (Common Components)
│
├─ 业务逻辑层 (Business Logic Layer)
│  ├─ 状态管理 (Pinia Stores)
│  ├─ 业务工具 (Utils)
│  └─ 数据转换 (Transformers)
│
├─ 数据访问层 (Data Access Layer)
│  ├─ API封装 (API Services)
│  ├─ 请求拦截器 (Interceptors)
│  └─ Mock数据 (Mock Services)
│
└─ 基础设施层 (Infrastructure Layer)
   ├─ 路由管理 (Router)
   ├─ 权限控制 (Auth)
   ├─ 日志系统 (Logger)
   └─ 工具函数 (Helpers)
```

#### 3.6.4 开发流程规范

**1. 需求分析阶段**
- 理解产品需求文档
- 确认后端API接口定义
- 评估技术可行性和工作量

**2. 设计阶段**
- 页面原型设计（Figma/墨刀）
- 组件拆分与复用规划
- 状态管理方案设计
- API调用流程设计

**3. 开发阶段**
- 创建页面和组件结构
- 实现业务逻辑
- 封装API接口
- 编写单元测试

**4. 联调阶段**
- 与后端联调接口
- 处理跨域和认证问题
- 异常场景测试

**5. 测试阶段**
- 功能测试
- 兼容性测试（多端、多设备）
- 性能测试
- 用户体验测试

**6. 发布阶段**
- 代码审查
- 打包优化
- 多端发布
- 线上监控

#### 3.6.5 多端适配策略

**H5端**：
- 支持PWA，添加到桌面
- 离线提示和缓存策略
- 响应式布局适配PC/Pad

**Android/iOS App**：
- 适配全面屏、刘海屏、折叠屏
- 支持原生分享、推送通知
- 相机、相册等原生能力调用

**微信小程序**：
- 遵循微信设计规范
- 注意包大小限制（主包2MB）
- API兼容性处理

**性能基准**：

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| 首屏加载 | < 3秒 | Performance API |
| 白屏时间 | < 1秒 | 自定义埋点 |
| FPS | ≥ 60 | uni.createSelectorQuery |
| 接口响应 | < 2秒 | 请求拦截器计时 |
| 内存占用 | < 200MB | 开发者工具监控 |

---

## 4. 移动端安全规范（医学数据场景）

### 4.1 XSS防护（跨站脚本攻击）

- **禁止使用 `v-html`**：直接渲染用户输入或API返回内容
- **必须使用 Vue 插值**：`{{ }}` 自动转义HTML标签
- **敏感场景**：评论、聊天、用户昵称、直播标题等必须进行HTML转义
- **URL校验**：外部链接跳转前校验URL合法性，防止跳转到恶意站点

### 4.2 敏感信息脱敏

医学直播平台涉及大量敏感信息，前端必须严格脱敏：

| 信息类型 | 脱敏规则 | 示例 |
|---------|---------|------|
| 手机号 | 保留前3后4位 | `138****5678` |
| 身份证 | 保留前3后4位 | `420***********1234` |
| 邮箱 | 保留前2位@后全部 | `ab***@example.com` |
| 患者姓名 | 仅显示姓+脱敏 | `张**` |
| 病历号 | 仅显示部分 | `MR****1234` |
| 医生姓名 | 根据隐私策略决定（通常可显示全名+职称） | `张三 主任医师` |

**实现位置**：`src/utils/security.ts` 中封装脱敏函数

**示例代码**：
```typescript
/**
 * 手机号脱敏
 * @param phone - 手机号
 * @returns 脱敏后的手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}
```

### 4.3 Token安全存储

- **禁止明文存储**：Token不得存储在 `localStorage` 或 `sessionStorage`（明文）
- **推荐方式**：
  - 使用 `uni.setStorageSync` 加密存储（小程序端）
  - 使用原生KeyChain/KeyStore（App端）
  - Token仅存于内存，页面刷新后重新登录（H5端）
- **Token过期处理**：
  - 检测到401错误时，清除Token并跳转登录页
  - 支持Token自动刷新机制（refresh_token）

### 4.4 API请求安全

#### 4.4.1 强制HTTPS
- 所有API请求必须使用 `https://` 协议
- 配置文件 `src/api/config.ts` 中强制校验：
  ```typescript
  export const API_CONFIG = {
    BASE_URL: import.meta.env.VITE_API_BASE_URL, // 必须以https://开头
    TIMEOUT: 30000,
    USE_MOCK: import.meta.env.MODE === 'development'
  }
  
  // 启动时校验
  if (!API_CONFIG.BASE_URL.startsWith('https://')) {
    throw new Error('API_BASE_URL必须使用HTTPS协议')
  }
  ```

#### 4.4.2 Token自动注入
在 `src/api/request.ts` 的请求拦截器中自动注入Token：

```typescript
function requestInterceptor(config: RequestConfig) {
  const token = getToken()
  if (token) {
    config.header = config.header || {}
    config.header.Authorization = `Bearer ${token}`
  }
  return config
}
```

#### 4.4.3 接口鉴权
前端需校验API返回的权限状态码：

| 状态码 | 含义 | 前端处理 |
|-------|------|---------|
| 401 | 未登录/Token过期 | 清除Token，跳转登录页 |
| 403 | 无权限 | Toast提示"您没有访问权限"，返回上一页 |
| 404 | 资源不存在 | Toast提示"内容不存在"，显示空状态 |
| 429 | 请求频率限制 | Toast提示"操作过于频繁"，禁用按钮3秒 |
| 500+ | 服务器错误 | Toast提示"服务异常，请稍后重试"，显示重试按钮 |

### 4.5 日志脱敏

#### 4.5.1 禁止上报敏感信息
- 禁止上报：用户手机号、身份证、密码、Token、患者信息、病历内容
- 必须脱敏：用户ID（使用hash）、操作记录（移除敏感参数）

#### 4.5.2 日志脱敏实现
在 `src/logs/logger.ts` 中集成脱敏逻辑：

```typescript
import { maskPhone, maskIdCard } from '@/utils/security'

const SENSITIVE_KEYS = ['phone', 'idCard', 'password', 'token', 'patientName']

function desensitizeLog(data: any): any {
  if (typeof data !== 'object' || data === null) return data
  
  const desensitized = { ...data }
  for (const key of SENSITIVE_KEYS) {
    if (desensitized[key]) {
      if (key === 'phone') desensitized[key] = maskPhone(desensitized[key])
      else if (key === 'idCard') desensitized[key] = maskIdCard(desensitized[key])
      else desensitized[key] = '***'
    }
  }
  return desensitized
}
```

### 4.6 移动端特有安全考虑

#### 4.6.1 截屏保护（可选）
对于敏感页面（如患者病历），可启用截屏保护：

```typescript
// #ifdef APP-PLUS
if (isSensitivePage) {
  plus.navigator.setFullscreen(true) // 防截屏
}
// #endif
```

#### 4.6.2 生物识别认证（可选）
支持指纹/面容ID登录：

```typescript
uni.checkIsSupportSoterAuthentication({
  success(res) {
    if (res.supportMode.includes('fingerPrint')) {
      // 支持指纹识别
      uni.startSoterAuthentication({
        requestAuthModes: ['fingerPrint'],
        challenge: 'nonce',
        authContent: '验证指纹'
      })
    }
  }
})
```

#### 4.6.3 App签名校验
防止App被篡改或重新打包：

```typescript
// #ifdef APP-PLUS
const appSignature = plus.runtime.getProperty(plus.runtime.appid, (info) => {
  const signature = info.signature
  // 校验签名是否匹配
  if (signature !== EXPECTED_SIGNATURE) {
    uni.showModal({
      title: '安全警告',
      content: 'App签名异常，可能存在安全风险',
      showCancel: false
    })
  }
})
// #endif
```

---

## 5. 移动端异常处理规范

### 5.1 网络异常

#### 5.1.1 网络检测
在 `src/utils/network.ts` 中实现网络检测：

```typescript
/**
 * 检测网络连接状态
 * @returns 网络类型
 */
export async function checkNetwork(): Promise<{
  isConnected: boolean
  networkType: string
  isCellular: boolean
}> {
  return new Promise((resolve) => {
    uni.getNetworkType({
      success: (res) => {
        const networkType = res.networkType
        resolve({
          isConnected: networkType !== 'none',
          networkType,
          isCellular: ['2g', '3g', '4g', '5g'].includes(networkType)
        })
      },
      fail: () => {
        resolve({ isConnected: false, networkType: 'unknown', isCellular: false })
      }
    })
  })
}
```

#### 5.1.2 网络异常处理
在 `src/api/request.ts` 中统一处理：

```typescript
try {
  const response = await uni.request({ url, method, data })
  return response.data
} catch (error: any) {
  if (error.errMsg?.includes('timeout')) {
    uni.showToast({ title: '请求超时，请检查网络', icon: 'none' })
  } else if (error.errMsg?.includes('fail')) {
    const { isConnected } = await checkNetwork()
    if (!isConnected) {
      uni.showModal({
        title: '网络连接失败',
        content: '请检查网络设置后重试',
        confirmText: '重试',
        success: (res) => {
          if (res.confirm) {
            // 重试逻辑
          }
        }
      })
    }
  }
  throw error
}
```

### 5.2 业务异常

根据后端返回的错误码显示不同提示：

```typescript
function handleBusinessError(code: number, message: string) {
  const errorMap: Record<number, string> = {
    400: '请求参数错误',
    401: '请先登录',
    403: '您没有访问权限',
    404: '内容不存在',
    429: '操作过于频繁，请稍后重试',
    500: '服务异常，请稍后重试',
    503: '服务维护中'
  }
  
  const errorMsg = errorMap[code] || message || '操作失败'
  
  uni.showToast({
    title: errorMsg,
    icon: code === 401 ? 'none' : 'error',
    duration: 2000
  })
  
  // 特殊处理
  if (code === 401) {
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/auth/login' })
    }, 1500)
  }
}
```

### 5.3 全局异常捕获

在 `src/App.vue` 中注册全局错误处理：

```vue
<script setup lang="ts">
import { onErrorCaptured } from 'vue'
import { logger } from '@/logs/logger'

// 捕获Vue组件错误
onErrorCaptured((err, instance, info) => {
  console.error('[全局错误]', err, info)
  
  // 上报到日志系统
  logger.error('Vue组件异常', {
    error: err.message,
    stack: err.stack,
    componentName: instance?.$options?.name,
    errorInfo: info
  })
  
  // 显示友好提示
  uni.showToast({
    title: '页面加载异常',
    icon: 'none'
  })
  
  // 阻止错误继续传播
  return false
})

// 捕获Promise异常
uni.onUnhandledRejection((event) => {
  console.error('[Promise异常]', event.reason)
  logger.error('Promise异常', {
    reason: event.reason
  })
})

// 监听页面错误
uni.onError((error) => {
  console.error('[页面错误]', error)
  logger.error('页面错误', { error })
})
</script>
```

### 5.4 用户操作异常

#### 5.4.1 表单校验失败
```typescript
// 字段下方即时显示红色错误提示
const errors = ref<Record<string, string>>({})

function validateForm() {
  errors.value = {}
  
  if (!form.title) {
    errors.value.title = '请输入直播标题'
  }
  
  if (!form.startTime) {
    errors.value.startTime = '请选择开始时间'
  }
  
  return Object.keys(errors.value).length === 0
}
```

#### 5.4.2 操作频繁
使用防抖/节流：

```typescript
import { debounce } from 'lodash-es'

//搜索防抖（300ms）
const handleSearch = debounce((keyword: string) => {
  // 执行搜索
}, 300)

// 提交节流（1000ms）
const handleSubmit = throttle(async () => {
  // 执行提交
}, 1000)
```

#### 5.4.3 权限不足
```typescript
if (!hasPermission) {
  uni.showModal({
    title: '权限不足',
    content: '您没有创建直播的权限，请先完成主播认证',
    confirmText: '去认证',
    success: (res) => {
      if (res.confirm) {
        uni.navigateTo({ url: '/pages/auth/verify' })
      }
    }
  })
  return
}
```

### 5.5 资源加载异常

#### 5.5.1 图片加载失败
```vue
<image
  :src="coverUrl"
  mode="aspectFill"
  @error="handleImageError"
/>

<script setup lang="ts">
function handleImageError(e: any) {
  console.error('[图片加载失败]', e)
  // 使用默认占位图
  coverUrl.value = '/static/images/default-cover.png'
}
</script>
```

#### 5.5.2 视频加载失败
```vue
<video
  :src="videoUrl"
  @error="handleVideoError"
/>

<script setup lang="ts">
function handleVideoError(e: any) {
  console.error('[视频加载失败]', e)
  uni.showModal({
    title: '播放失败',
    content: '视频加载失败，请检查网络后重试',
    confirmText: '重试',
    success: (res) => {
      if (res.confirm) {
        // 重新加载视频
        reloadVideo()
      }
    }
  })
}
</script>
```

---

## 6. 移动端性能优化规范

### 6.1 首屏加载优化

#### 6.1.1 关键资源优先加载
- **路由懒加载**：非首屏页面使用懒加载
  ```typescript
  // pages.json中配置按需加载
  {
    "pages": [
      {
        "path": "pages/tabbar/home/index",
        "style": { "enablePullDownRefresh": true }
      }
    ],
    "subPackages": [
      {
        "root": "pages/room",
        "pages": ["detail", "fullscreen"]
      }
    ]
  }
  ```

#### 6.1.2 图片优化
- **WebP格式**：支持WebP的平台优先使用（体积减少30-50%）
- **图片压缩**：封面图压缩至100KB以内
- **响应式图片**：根据屏幕尺寸加载不同分辨率
  ```typescript
  const screenWidth = uni.getSystemInfoSync().screenWidth
  const imageSize = screenWidth > 750 ? '@2x' : '@1x'
  const imageUrl = `${baseUrl}/cover${imageSize}.jpg`
  ```

#### 6.1.3 骨架屏
首屏加载时显示骨架屏，提升感知性能：

```vue
<template>
  <view v-if="isLoading" class="skeleton">
    <view class="skeleton-header" />
    <view class="skeleton-item" v-for="i in 5" :key="i" />
  </view>
  <view v-else class="content">
    <!-- 实际内容 -->
  </view>
</template>
```

### 6.2 列表性能优化

#### 6.2.1 虚拟滚动
对于超过50项的长列表，使用虚拟滚动：

```vue
<recycle-list :data="list" :item-height="200">
  <template #default="{ item }">
    <RoomCard :room="item" />
  </template>
</recycle-list>
```

#### 6.2.2 分页加载
```typescript
// 距离底部100px时触发
<scroll-view
  scroll-y
  :lower-threshold="100"
  @scrolltolower="loadMore"
>
  <!-- 内容 -->
</scroll-view>

async function loadMore() {
  if (isLoading.value || !hasMore.value) return
  
  isLoading.value = true
  const nextPage = currentPage.value + 1
  const response = await getRooms({ page: nextPage, page_size: 20 })
  
  roomList.value.push(...response.items)
  currentPage.value = nextPage
  hasMore.value = response.has_more
  isLoading.value = false
}
```

#### 6.2.3 防抖节流
```typescript
// 搜索防抖（300ms）
const handleSearch = debounce((keyword: string) => {
  searchRooms(keyword)
}, 300)

// 滚动节流（100ms）
const handleScroll = throttle((e: any) => {
  scrollTop.value = e.scrollTop
}, 100)
```

### 6.3 内存管理

#### 6.3.1 组件销毁时清理
```vue
<script setup lang="ts">
import { onUnmounted } from 'vue'

let timer: NodeJS.Timeout | null = null

onMounted(() => {
  timer = setInterval(() => {
    // 定时任务
  }, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>
```

#### 6.3.2 避免内存泄漏
```typescript
// 移除事件监听
onUnmounted(() => {
  uni.$off('themeChanged', handleThemeChange)
})

// 取消未完成的请求
const abortController = new AbortController()
onUnmounted(() => {
  abortController.abort()
})
```

### 6.4 流量优化

#### 6.4.1 流量检测与提醒
参考本文档第7.3节"直播间页面"中的"M1.3 智能流量提醒"

#### 6.4.2 自适应清晰度
```typescript
const { isCellular } = await checkNetwork()

if (isCellular && !userSettings.noCellularPrompt) {
  // 显示流量提醒
  // 推荐切换到720p或480p
}
```

---

## 7. 数据库设计（核心表结构）

本节简要介绍移动端相关的数据库设计，帮助前端理解接口数据结构和字段含义。完整的数据库设计请参考《后端新增api接口和模块设计文档-v2.md》。

### 7.1 设计原则

- **UUID主键**：所有表主键均为UUID，在应用层通过 `uuid.uuid4()` 生成，保证全局唯一性
- **时区兼容**：所有时间戳字段均为TIMESTAMPTZ，统一使用UTC时间
- **数据完整性**：通过外键约束、唯一约束、枚举类型保证数据准确性
- **软删除策略**：基础数据表（tags, categories, brands, experts）采用软删除（`is_active=false`）
- **关联表策略**：用户相关关联表（favorites, subscriptions）采用软删除，纯关联表（session_tags）采用硬删除

### 7.2 移动端核心表结构

移动端前端主要使用以下数据表：

#### 7.2.1 用户相关表

**user_favorites（用户收藏表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，收藏记录ID |
| user_id | UUID | 用户ID（关联users.public_id） |
| room_id | UUID | 房间ID（关联live_rooms.id） |
| created_at | TIMESTAMPTZ | 创建时间 |
| is_active | BOOLEAN | 是否有效（软删除标记） |

- **用途**：用户收藏直播间功能
- **前端页面**：我的收藏、直播间详情页
- **API接口**：`/api/v1/users/me/favorites`

**user_subscriptions（用户订阅表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，订阅记录ID |
| user_id | UUID | 用户ID（关联users.public_id） |
| target_type | ENUM | 订阅类型（expert/room/brand） |
| target_id | UUID | 订阅目标ID |
| created_at | TIMESTAMPTZ | 创建时间 |
| is_active | BOOLEAN | 是否有效（软删除标记） |

- **用途**：用户关注专家/房间/品牌功能
- **前端页面**：我的关注、专家详情页、品牌详情页
- **API接口**：`/api/v1/users/me/subscriptions`

**watch_history（观看历史表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，历史记录ID |
| user_id | UUID | 用户ID（关联users.public_id） |
| session_id | UUID | 场次ID（关联live_sessions.id） |
| watch_duration | INT | 观看时长（秒） |
| last_position | INT | 最后观看位置（秒） |
| created_at | TIMESTAMPTZ | 首次观看时间 |
| updated_at | TIMESTAMPTZ | 最后观看时间 |

- **用途**：记录用户观看历史，支持续播功能
- **前端页面**：观看历史、直播间（续播提示）
- **API接口**：`/api/v1/users/me/watch-history`

#### 7.2.2 内容分类与标签表

**categories（全局分类表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，分类ID |
| name | VARCHAR(100) | 分类名称（唯一） |
| slug | VARCHAR(120) | URL友好标识符 |
| icon | VARCHAR(255) | 分类图标 |
| description | TEXT | 分类描述 |
| sort_order | INT | 排序权重（数字越小越靠前） |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

- **用途**：科室分类（如：肝胆胰外科、胃肠外科）
- **前端页面**：首页分类筛选器、分类管理页
- **API接口**：`/api/v1/categories`
- **特殊功能**：支持用户星标固定（存储在user_preferences）

**tags（内容标签表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，标签ID |
| name | VARCHAR(80) | 标签名称（唯一） |
| slug | VARCHAR(100) | URL友好标识符 |
| description | TEXT | 标签描述 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

- **用途**：内容标签（如：#微创手术 #病例讨论）
- **前端页面**：直播间详情页、搜索页、标签聚合页
- **API接口**：`/api/v1/tags`
- **关联表**：session_tags（场次-标签多对多关联）

**session_tags（场次-标签关联表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| session_id | UUID | 场次ID（主键1） |
| tag_id | UUID | 标签ID（主键2） |
| created_at | TIMESTAMPTZ | 创建时间 |

- **用途**：关联直播场次与标签
- **删除策略**：级联删除（ON DELETE CASCADE）

#### 7.2.3 品牌与专家表

**brands（品牌表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，品牌ID |
| name | VARCHAR(150) | 品牌名称（唯一） |
| slug | VARCHAR(150) | URL友好标识符 |
| logo_url | VARCHAR(512) | 品牌Logo URL |
| description | TEXT | 品牌描述 |
| website_url | VARCHAR(255) | 品牌官网 |
| sort_order | INT | 排序权重 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

- **用途**：合作品牌/企业信息
- **前端页面**：品牌专区、品牌详情页
- **API接口**：`/api/v1/brands`、`/api/v1/brands/{id}/content`

**experts（专家信息表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，专家ID |
| user_id | UUID | 关联用户ID（可为空，外部专家） |
| name | VARCHAR(120) | 专家姓名 |
| title | VARCHAR(120) | 职称（如：主任医师、教授） |
| hospital | VARCHAR(200) | 所在医院 |
| department | VARCHAR(120) | 所在科室 |
| expertise_areas | TEXT | 擅长领域（逗号分隔） |
| bio | TEXT | 个人简介 |
| avatar_url | VARCHAR(512) | 头像URL |
| is_featured | BOOLEAN | 是否为推荐专家 |
| sort_order | INT | 排序权重 |
| contact_info | JSONB | 联系方式（JSON格式） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

- **用途**：专家信息管理
- **前端页面**：专家专题页、专家详情页、我的关注
- **API接口**：`/api/v1/featured-experts`、`/api/v1/professors/{id}/content`

#### 7.2.4 首页精选内容表

**featured_content（首页精选表）**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，精选内容ID |
| title | VARCHAR(200) | 标题 |
| image_url | VARCHAR(512) | 图片URL（3D焦点图） |
| target_type | ENUM | 跳转类型（session/topic/external） |
| target_id | UUID | 目标资源ID（可为空） |
| target_url | VARCHAR(512) | 外部链接（可为空） |
| cta_text | VARCHAR(50) | 行动召唤文字（如：立即观看） |
| sort_order | INT | 排序权重 |
| is_active | BOOLEAN | 是否启用 |
| start_date | TIMESTAMPTZ | 生效开始时间（可为空） |
| end_date | TIMESTAMPTZ | 生效结束时间（可为空） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

- **用途**：首页3D焦点图轮播内容
- **前端页面**：首页
- **API接口**：`/api/v1/featured-content`
- **特殊说明**：
  - `target_type='session'` 时，`target_id` 指向 `live_sessions.id`
  - `target_type='topic'` 时，`target_id` 指向 `topics.id`
  - `target_type='external'` 时，使用 `target_url` 外部链接

#### 7.2.5 直播核心表（移动端关注字段）

**live_rooms（直播房间表）**

| 字段名 | 类型 | 移动端用途 |
|-------|------|-----------|
| id | UUID | 房间唯一标识 |
| title | VARCHAR | 房间标题（显示在卡片上） |
| cover_url | VARCHAR | 封面图（16:9比例） |
| category_id | UUID | 所属科室分类（用于筛选） |
| description | TEXT | 房间描述 |
| is_private | BOOLEAN | 是否私密（影响列表显示） |

**live_sessions（直播场次表）**

| 字段名 | 类型 | 移动端用途 |
|-------|------|-----------|
| id | UUID | 场次唯一标识 |
| room_id | UUID | 所属房间 |
| status | ENUM | 场次状态（live/scheduled/replay） |
| start_time | TIMESTAMPTZ | 开始时间（预告显示） |
| end_time | TIMESTAMPTZ | 结束时间 |
| featured_expert_id | UUID | 主讲专家ID（显示专家信息） |
| summary | TEXT | 场次摘要（列表预览） |

**session_statistics（场次统计表）**

| 字段名 | 类型 | 移动端用途 |
|-------|------|-----------|
| session_id | UUID | 关联场次ID |
| current_viewer_count | INT | 实时观众数（直播中显示） |
| peak_viewer_count | INT | 峰值观众数 |
| total_viewer_count | BIGINT | 总观众数 |
| play_count | BIGINT | 回放播放次数 |

### 7.3 主要表关系图

```
用户相关表关系：
users (public_id) ──┬─→ user_favorites (user_id)
                    ├─→ user_subscriptions (user_id)
                    └─→ watch_history (user_id)

内容关系：
categories (id) ──→ live_rooms (category_id)
tags (id) ──→ session_tags (tag_id)
live_sessions (id) ──→ session_tags (session_id)

专家关系：
users (public_id) ──→ experts (user_id) [可为空]
experts (id) ──→ live_sessions (featured_expert_id)

订阅关系：
user_subscriptions:
  - target_type='expert' → experts (id)
  - target_type='room' → live_rooms (id)
  - target_type='brand' → brands (id)

首页精选：
featured_content:
  - target_type='session' → live_sessions (id)
  - target_type='topic' → topics (id)
  - target_type='external' → target_url
```

### 7.4 前端数据模型定义

移动端前端需要在 `src/types/` 目录定义对应的TypeScript类型：

```typescript
// src/types/models.ts

// 用户收藏
export interface UserFavorite {
  id: string
  userId: string
  roomId: string
  createdAt: string
  isActive: boolean
}

// 用户订阅
export interface UserSubscription {
  id: string
  userId: string
  targetType: 'expert' | 'room' | 'brand'
  targetId: string
  createdAt: string
  isActive: boolean
}

// 观看历史
export interface WatchHistory {
  id: string
  userId: string
  sessionId: string
  watchDuration: number
  lastPosition: number
  createdAt: string
  updatedAt: string
}

// 分类
export interface Category {
  id: string
  name: string
  slug: string
  icon: string
  description: string
  sortOrder: number
  isActive: boolean
}

// 标签
export interface Tag {
  id: string
  name: string
  slug: string
  description: string
  isActive: boolean
}

// 品牌
export interface Brand {
  id: string
  name: string
  slug: string
  logoUrl: string
  description: string
  websiteUrl: string
  sortOrder: number
  isActive: boolean
}

// 专家
export interface Expert {
  id: string
  userId?: string
  name: string
  title: string
  hospital: string
  department: string
  expertiseAreas: string
  bio: string
  avatarUrl: string
  isFeatured: boolean
  sortOrder: number
  contactInfo?: Record<string, any>
}

// 首页精选
export interface FeaturedContent {
  id: string
  title: string
  imageUrl: string
  targetType: 'session' | 'topic' | 'external'
  targetId?: string
  targetUrl?: string
  ctaText: string
  sortOrder: number
}
```

### 7.5 数据表使用场景映射

| 数据表 | 前端页面 | 主要功能 |
|--------|---------|---------|
| user_favorites | 我的收藏、直播间详情 | 收藏/取消收藏直播间 |
| user_subscriptions | 我的关注、专家/品牌详情 | 关注/取消关注专家/品牌 |
| watch_history | 观看历史、直播间 | 记录观看进度、续播提示 |
| categories | 首页、分类管理 | 科室分类筛选、星标固定 |
| tags | 直播间详情、搜索 | 标签显示、标签筛选 |
| brands | 品牌专区、品牌详情 | 品牌列表、品牌详情展示 |
| experts | 专家专题、专家详情 | 专家列表、专家主讲场次 |
| featured_content | 首页 | 3D焦点图轮播 |
| live_rooms | 首页Feed、直播间 | 房间信息展示 |
| live_sessions | 直播间、播放器 | 场次信息、播放控制 |
| session_statistics | 直播间 | 观众数、播放次数展示 |

---

## 8. 全局UI/UX设计规范

### 8.1 设计令牌（Design Tokens）

**[最高约束]** 所有样式变量必须定义在 `src/uni.scss` 中，禁止硬编码。

#### 8.1.1 颜色系统

```scss
// 主题色
$color-primary: #509cec;            // 主题蓝色
$color-primary-hover: #215588;      // 主题色悬停
$color-primary-light-1: #e9f2fc;    // 主题色浅色

// 功能色
$color-success: #28a745;            // 成功色（绿色）
$color-danger: #dc3545;             // 危险色（红色）
$color-warning: #ffc107;            // 警告色（黄色）
$color-info: #6c757d;               // 信息色（灰色）

// 文本色
$color-text-primary: #121111;       // 主文本色（深黑）
$color-text-secondary: #6c757d;     // 次文本色（灰色）
$color-text-placeholder: #adb5bd;   // 占位符色（浅灰）
$color-text-on-primary: #ffffff;    // 反色文本（白色）

// 背景色
$color-background: #f8f9fa;         // 页面背景（浅灰）
$color-background-light: #ffffff;   // 卡片背景（白色）

// 边框色
$color-border: #e9ecef;             // 默认边框色
```

#### 8.1.2 字体系统

```scss
// 字体族
$font-family-sans-serif: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

// 字号（移动端优化）
$font-size-small: 22rpx;   // 10px（说明文字）
$font-size-base: 26rpx;    // 12px（正文）
$font-size-medium: 30rpx;  // 14px（标题）
$font-size-large: 36rpx;   // 16px（大标题）
$font-size-xlarge: 40rpx;  // 18px（特大标题）

// 行高
$line-height-base: 1.5;
$line-height-tight: 1.25;
```

#### 8.1.3 间距系统

```scss
// 间距（8px基准）
$spacing-xs: 8rpx;    // 4px
$spacing-small: 16rpx;   // 8px
$spacing-medium: 24rpx;  // 12px
$spacing-large: 32rpx;   // 16px
$spacing-xlarge: 48rpx;  // 24px
$spacing-xxlarge: 64rpx; // 32px
```

#### 8.1.4 圆角系统

```scss
$radius-small: 8rpx;   // 4px（小圆角）
$radius-base: 12rpx;   // 6px（默认圆角）
$radius-large: 16rpx;  // 8px（大圆角）
$radius-circle: 50%;   // 圆形
```

#### 8.1.5 阴影系统

```scss
$shadow-small: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
$shadow-base: 0 8rpx 16rpx rgba(0, 0, 0, 0.08);
$shadow-large: 0 16rpx 32rpx rgba(0, 0, 0, 0.12);
```

### 8.2 触摸交互规范

#### 8.2.1 点击反馈
所有可点击元素必须有视觉反馈：

```scss
.clickable {
  transition: opacity 0.2s ease;
  
  &:active {
    opacity: 0.7;
  }
}
```

#### 8.2.2 长按反馈
长按操作需要震动反馈：

```typescript
const handleLongPress = () => {
  uni.vibrateShort({ type: 'light' }) // 轻微震动
  // 执行长按逻辑
}
```

#### 8.2.3 滑动手势
```typescript
let startX = 0
let startY = 0

function handleTouchStart(e: TouchEvent) {
  startX = e.touches[0].clientX
  startY = e.touches[0].clientY
}

function handleTouchEnd(e: TouchEvent) {
  const endX = e.changedTouches[0].clientX
  const endY = e.changedTouches[0].clientY
  
  const deltaX = endX - startX
  const deltaY = endY - startY
  
  // 判断滑动方向
  if (Math.abs(deltaX) > Math.abs(deltaY)) {
    if (deltaX > 50) {
      // 右滑
      handleSwipeRight()
    } else if (deltaX < -50) {
      // 左滑
      handleSwipeLeft()
    }
  }
}
```

### 8.3 Loading状态设计

#### 8.3.1 全局Loading
```typescript
// 显示全局Loading
uni.showLoading({ title: '加载中...', mask: true })

// 隐藏全局Loading
uni.hideLoading()
```

#### 8.3.2 局部Loading
```vue
<template>
  <view class="content">
    <view v-if="isLoading" class="loading">
      <uni-load-more status="loading" />
    </view>
    <view v-else>
      <!-- 内容 -->
    </view>
  </view>
</template>
```

#### 8.3.3 骨架屏
```scss
.skeleton {
  .skeleton-item {
    background: linear-gradient(
      90deg,
      #f0f0f0 25%,
      #e0e0e0 50%,
      #f0f0f0 75%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
  }
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 8.4 Toast提示规范

```typescript
// 成功提示（绿色勾号）
uni.showToast({
  title: '操作成功',
  icon: 'success',
  duration: 1500
})

// 失败提示（红色叉号）
uni.showToast({
  title: '操作失败',
  icon: 'error',
  duration: 2000
})

// 纯文字提示（无图标）
uni.showToast({
  title: '操作过于频繁',
  icon: 'none',
  duration: 2000
})
```

---

### 8.5 底部主导航栏设计（Bottom Tab Bar）

#### 8.5.1 设计理念

这是App/小程序的**一级导航**，取代PC端的顶部导航栏，采用移动端标准的底部Tab栏布局，符合用户拇指操作习惯。

#### 8.5.2 Tab结构

| 位置 | Tab名称 | 图标 | 功能定位 | 对应页面路径 |
|------|---------|------|----------|-------------|
| ① | 首页 | 🏠 | 内容发现Feed，默认选中 | `/pages/tabbar/home/index` |
| ② | 品牌 | 🏢 | 合作品牌专区 | `/pages/tabbar/brand/index` |
| ③ | 我的直播 | 🎥 | 主播后台快捷入口（SaaS核心） | `/pages/tabbar/my-live/index` |
| ④ | 专家 | 👨‍⚕️ | 专家列表与聚合页 | `/pages/tabbar/expert/index` |
| ⑤ | 我的 | 👤 | 个人中心 | `/pages/tabbar/my/index` |

**设计理念**:
- **左侧（①②）**：内容消费层（浏览直播、探索品牌）
- **中间（③）**：内容生产层（主播核心工作台，C位强调）
- **右侧（④⑤）**：工具/个人层（专家查找、个人中心）

#### 8.5.3 交互规范

**A. 标准点击**
- **行为**：切换到对应Tab页面
- **反馈**：
  - 图标颜色变为主题色（#509cec）
  - 图标轻微放大（scale: 1.1）
  - 震动反馈（可选）

**B. 长按交互（创新）**
- **触发对象**：首页Tab
- **触发时长**：500-600ms
- **功能**：弹出快捷设置菜单（视图模式切换、刷新推荐等）
- **反馈**：
  - 震动反馈（`uni.vibrateShort()`）
  - Tab图标轻微缩放动画

#### 8.5.4 实现代码

在 `src/pages.json` 中配置：

```json
{
  "tabBar": {
    "color": "#666666",
    "selectedColor": "#509cec",
    "backgroundColor": "#ffffff",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/tabbar/home/index",
        "text": "首页",
        "iconPath": "static/tabbar/home.png",
        "selectedIconPath": "static/tabbar/home-active.png"
      },
      {
        "pagePath": "pages/tabbar/brand/index",
        "text": "品牌",
        "iconPath": "static/tabbar/brand.png",
        "selectedIconPath": "static/tabbar/brand-active.png"
      },
      {
        "pagePath": "pages/tabbar/my-live/index",
        "text": "我的直播",
        "iconPath": "static/tabbar/my-live.png",
        "selectedIconPath": "static/tabbar/my-live-active.png"
      },
      {
        "pagePath": "pages/tabbar/expert/index",
        "text": "专家",
        "iconPath": "static/tabbar/expert.png",
        "selectedIconPath": "static/tabbar/expert-active.png"
      },
      {
        "pagePath": "pages/tabbar/my/index",
        "text": "我的",
        "iconPath": "static/tabbar/my.png",
        "selectedIconPath": "static/tabbar/my-active.png"
      }
    ]
  }
}
```

---

### 8.6 核心页面设计规范

**[最高约束]** 所有页面开发必须严格遵循以下原则：

1. **所有页面必须符合本文档第3-7章的规范**（代码规范、安全规范、性能优化等）
2. **所有样式变量必须引用 `uni.scss` 中的设计令牌**，禁止硬编码
3. **所有API调用必须使用 `src/api/request.ts` 的统一封装**，包含完整错误处理
4. **所有用户偏好必须同时保存到LocalStorage和服务器**（已登录用户）
5. **所有交互必须有Loading状态、成功/失败反馈、异常处理**

**说明**：本小节详细描述了移动端各核心页面的完整设计规范，包括布局结构、交互逻辑、技术实现等。开发时请严格按照本小节要求实现各页面功能。

> **提示**: 由于移动端页面设计内容详尽，完整的页面设计规范已整理在独立文档《直播saas平台网站前端效果设计---移动端版(v1.3）.md》中。本小节包含各页面的核心设计要点和技术实现指南，开发时需结合两份文档进行实施。

#### 8.6.1 页面概览与导航结构

移动端采用**底部Tab导航**作为主导航，取代PC端的顶部导航栏，符合移动用户拇指操作习惯。

**Tab导航结构**:

| 位置 | Tab名称 | 图标 | 功能定位 | 页面路径 |
|------|---------|------|----------|-------------|
| ① | 首页 | 🏠 | 内容发现Feed，默认选中 | `/pages/tabbar/home/index` |
| ② | 品牌 | 🏢 | 合作品牌专区 | `/pages/tabbar/brand/index` |
| ③ | 我的直播 | 🎥 | 主播后台快捷入口（SaaS核心） | `/pages/tabbar/my-live/index` |
| ④ | 专家 | 👨‍⚕️ | 专家列表与聚合页 | `/pages/tabbar/expert/index` |
| ⑤ | 我的 | 👤 | 个人中心 | `/pages/tabbar/my/index` |

**设计理念**:
- **左侧（①②）**：内容消费层（浏览直播、探索品牌）
- **中间（③）**：内容生产层（主播核心工作台，C位强调）
- **右侧（④⑤）**：工具/个人层（专家查找、个人中心）

#### 8.6.2 详细页面交互流程（完整版）

本节详细描述移动端各核心页面的交互流程、状态管理、异常处理等，确保开发时有明确的实施标准。

---

##### 8.6.2.1 首页（Home Feed）

**页面路径**: `/pages/tabbar/home/index`

**一、页面结构**
```
顶部搜索栏（固定）
└─ 搜索图标 + 搜索框 + 消息图标

分类筛选器（吸顶）
└─ 推荐 | ⭐科室1 | ⭐科室2 | ... | 全部 ≡

我的关注区域（可折叠）
└─ 标题栏 + 横向滚动关注列表

3D焦点图轮播
└─ 3-5张焦点图卡片，支持左右滑动

内容Feed流（双列/单列可切换）
└─ 直播卡片列表，支持下拉刷新、上拉加载更多
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad() {
  // 1. 显示骨架屏
  showSkeleton()
  
  // 2. 并行加载数据
  try {
    const [categories, featuredContent, followedExperts, rooms] = await Promise.all([
      getCategories(),           // 获取分类列表
      getFeaturedContent(),      // 获取焦点图数据
      getFollowedExperts(),      // 获取关注的专家
      getHomepageRooms({ page: 1, page_size: 20 })  // 获取直播列表
    ])
    
    // 3. 渲染数据
    renderPage(categories, featuredContent, followedExperts, rooms)
    
    // 4. 恢复用户偏好
    restoreUserPreferences()  // 视图模式、固定科室等
    
    // 5. 隐藏骨架屏
    hideSkeleton()
  } catch (error) {
    handleLoadError(error)
  }
}
```

**2. 搜索交互**
- 点击搜索框 → 跳转到搜索页 `/pages/search/index`
- 点击消息图标 → 跳转到消息中心 `/pages/message/index`

**3. 分类筛选交互**
- **点击分类Tab**: 切换当前分类，重新加载对应直播列表
- **长按Tab**: 震动反馈，弹出快捷菜单（视图切换、刷新推荐）
- **点击"全部 ≡"**: 跳转到分类管理页 `/pages/category/manage`
- **星标固定**: 在分类管理页设置，自动同步到首页Tab栏

**4. 我的关注区域**
- **展示逻辑**: 仅已登录且有关注的用户显示
- **横向滚动**: 关注的专家/品牌头像，点击跳转到详情页
- **折叠/展开**: 点击标题栏右侧箭头图标

**5. 3D焦点图轮播**
- **自动轮播**: 4秒间隔，无限循环
- **手动滑动**: 支持左右滑动切换
- **点击跳转**: 
  - `target_type='session'` → 跳转直播间 `/pages/room/detail?sessionId={target_id}`
  - `target_type='topic'` → 跳转专题页
  - `target_type='external'` → 打开外部链接（WebView）

**6. 视图模式切换**
- **触发方式**: 长按"推荐"Tab，弹出菜单选择
- **视图模式**: 双列瀑布流（默认）、单列大图
- **保存偏好**: 同时保存到LocalStorage和服务器

**7. Feed流加载**
- **下拉刷新**: 重置page为1，重新加载最新数据
- **上拉加载**: page+1，追加到列表末尾
- **无更多数据**: 显示"已经到底啦~"提示

**8. 直播卡片点击**
- 点击卡片 → 跳转到直播间详情页 `/pages/room/detail?roomId={room_id}`

**三、状态管理**
```typescript
// src/store/modules/homepage.ts
export const useHomepageStore = defineStore('homepage', {
  state: () => ({
    currentCategory: 'recommend',        // 当前选中分类
    viewMode: 'double',                  // 视图模式
    roomList: [],                        // 直播列表
    currentPage: 1,                      // 当前页码
    hasMore: true,                       // 是否有更多
    isLoading: false,                    // 加载状态
    followedExperts: [],                 // 关注的专家
    pinnedCategories: [],                // 固定的分类
  }),
  
  actions: {
    async loadRooms(categoryId: string, page: number) { ... },
    toggleViewMode() { ... },
    async refreshFeed() { ... },
  }
})
```

**四、异常处理**

| 异常场景 | 处理方式 |
|---------|---------|
| 网络断开 | Toast提示"网络连接失败"，显示重试按钮 |
| 接口超时 | Toast提示"请求超时"，自动重试1次 |
| 数据为空 | 显示空状态插画 + "暂无直播，去发现专家" |
| 加载失败 | 显示错误提示 + 重试按钮 |

---

##### 8.6.2.2 品牌专区（Brand Zone）

**页面路径**: `/pages/tabbar/brand/index`

**一、页面结构**
```
搜索栏（固定）
└─ 搜索品牌

精选品牌区域
└─ 横向滚动卡片列表

全部品牌列表
├─ 领域筛选器（横向滚动）
├─ A-Z字母索引（右侧）
└─ 品牌列表（按首字母分组）
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad() {
  showLoading()
  
  try {
    const [featuredBrands, allBrands] = await Promise.all([
      getFeaturedBrands(),   // 获取精选品牌（sort_order排序）
      getAllBrands()         // 获取全部品牌（按拼音首字母排序）
    ])
    
    // 按首字母分组
    const groupedBrands = groupByInitial(allBrands)
    
    renderPage(featuredBrands, groupedBrands)
    hideLoading()
  } catch (error) {
    handleLoadError(error)
  }
}
```

**2. 搜索交互**
- 点击搜索框 → 跳转到搜索页，默认搜索类型为"品牌"

**3. 精选品牌交互**
- **横向滚动**: 展示5-10个精选品牌
- **点击卡片**: 跳转到品牌详情页 `/pages/brand/detail?brandId={brand_id}`

**4. 领域筛选器**
- **横向滚动**: 全部 | 医疗器械 | 制药 | 医学影像 | ...
- **点击筛选**: 过滤显示对应领域的品牌

**5. A-Z字母索引**
- **右侧固定**: 显示A-Z字母列表
- **点击字母**: 快速定位到对应分组
- **震动反馈**: 点击时轻微震动

**6. 品牌列表**
- **分组展示**: 按首字母分组（A、B、C...）
- **点击品牌**: 跳转到品牌详情页

**三、品牌详情页交互**

**页面路径**: `/pages/brand/detail?brandId={id}`

```
品牌封面图（顶部大图）
└─ 品牌Logo + 名称

Tabs区域（吸顶）
└─ 简介 | 直播 | 资料

Tab内容区
├─ 简介: 品牌介绍、官网链接、联系方式
├─ 直播: 品牌相关的直播列表
└─ 资料: 品牌相关的文档、视频资料
```

**交互要点**:
- 关注/取消关注按钮（右上角）
- 点击官网链接 → 打开WebView
- 点击直播卡片 → 跳转到直播间

---

##### 8.6.2.3 我的直播（My Live - 主播后台）

**页面路径**: `/pages/tabbar/my-live/index`

**一、页面结构**
```
快捷操作区（2x2网格）
├─ 创建直播
├─ 查看数据
├─ 推流设置
└─ 直播管理

当前直播状态卡片（如有直播中）
└─ 直播标题 | 观众数 | 操作按钮

历史直播列表
└─ 场次卡片列表（按时间倒序）
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad() {
  // 1. 检查权限
  if (!hasStreamerPermission()) {
    showPermissionDenied()
    return
  }
  
  showLoading()
  
  try {
    // 2. 加载主播房间和场次
    const [myRooms, liveSessions, historySessions] = await Promise.all([
      getMyRooms(),              // 获取我的房间列表
      getLiveSessions(),          // 获取正在直播的场次
      getHistorySessions({ page: 1, page_size: 20 })  // 获取历史场次
    ])
    
    renderPage(myRooms, liveSessions, historySessions)
    hideLoading()
  } catch (error) {
    handleLoadError(error)
  }
}
```

**2. 快捷操作交互**

**创建直播**
- 点击 → 跳转到创建直播页 `/pages/live/create`
- 填写表单：标题、分类、开始时间、描述、封面图
- 提交后创建房间和场次

**查看数据**
- 点击 → 跳转到数据统计页 `/pages/live/statistics`
- 展示：总观看数、峰值观众、点赞数、分享数等

**推流设置**
- 点击 → 跳转到推流设置页 `/pages/live/stream-settings`
- 展示：推流地址、推流密钥、二维码、复制按钮
- 提供推流教程链接

**直播管理**
- 点击 → 跳转到房间管理页 `/pages/live/room-manage`
- 支持编辑房间信息、删除房间、创建分会场

**3. 当前直播状态卡片**

**显示条件**: 有 status 为 'live' 的场次

**卡片内容**:
```
[封面图] 直播标题
        分类 | 观众数: 1,250
        [结束直播] [查看详情]
```

**交互**:
- 点击"结束直播" → 二次确认弹窗 → 调用结束接口
- 点击"查看详情" → 跳转到直播间页面

**4. 历史直播列表**

**场次卡片内容**:
```
[封面图] 标题
        日期 | 观看数: 5,680 | 时长: 1h 30m
        [查看回放] [查看数据]
```

**交互**:
- 点击"查看回放" → 跳转到直播间（回放模式）
- 点击"查看数据" → 跳转到场次数据详情页
- 点击卡片 → 跳转到场次编辑页

**三、权限校验**

```typescript
function checkStreamerPermission() {
  const user = getCurrentUser()
  
  if (!user) {
    uni.showModal({
      title: '请先登录',
      content: '使用主播功能需要先登录账号',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/auth/login' })
        }
      }
    })
    return false
  }
  
  if (!user.hasStreamerRole) {
    uni.showModal({
      title: '权限不足',
      content: '您还不是主播，需要先完成主播认证',
      confirmText: '去认证',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/auth/verify' })
        }
      }
    })
    return false
  }
  
  return true
}
```

---

##### 8.6.2.4 专家专题（Expert Zone）

**页面路径**: `/pages/tabbar/expert/index`

**一、页面结构**
```
搜索栏（固定）
└─ 搜索专家

推荐专家区域
└─ 横向滚动专家卡片

全部专家列表
├─ 领域筛选器（横向滚动）
├─ A-Z字母索引（右侧）
└─ 专家列表（按首字母分组）
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad() {
  showLoading()
  
  try {
    const [featuredExperts, allExperts] = await Promise.all([
      getFeaturedExperts(),   // 获取推荐专家（is_featured=true）
      getAllExperts()         // 获取全部专家
    ])
    
    // 按姓氏首字母分组
    const groupedExperts = groupByInitial(allExperts)
    
    renderPage(featuredExperts, groupedExperts)
    hideLoading()
  } catch (error) {
    handleLoadError(error)
  }
}
```

**2. 推荐专家交互**
- **横向滚动**: 展示5-10位推荐专家
- **专家卡片**: 头像 + 姓名 + 职称 + 医院
- **点击卡片**: 跳转到专家详情页 `/pages/expert/detail?expertId={expert_id}`

**3. 领域筛选器**
- **横向滚动**: 全部 | 外科 | 内科 | 影像科 | ...
- **点击筛选**: 过滤显示对应领域的专家

**4. A-Z字母索引**
- **右侧固定**: 显示A-Z字母列表
- **点击字母**: 快速定位到对应分组
- **震动反馈**: 点击时轻微震动

**三、专家详情页交互**

**页面路径**: `/pages/expert/detail?expertId={id}`

```
专家信息卡片（顶部）
├─ 头像 + 姓名 + 职称
├─ 医院 + 科室
├─ 擅长领域
└─ [关注] [私信]

Tabs区域（吸顶）
└─ 主讲场次 | 个人简介

Tab内容区
├─ 主讲场次: 专家主讲的直播列表
└─ 个人简介: 详细介绍、学术成就
```

**交互要点**:
- 关注/取消关注按钮
- 私信按钮（未实现时置灰）
- 点击直播卡片 → 跳转到直播间

---

##### 8.6.2.5 直播间页面（Room Detail）

**页面路径**: `/pages/room/detail?roomId={id}` 或 `?sessionId={id}`

**一、页面结构**
```
智能视频播放器（顶部，支持小窗）
└─ 16:9 播放器 + 控制栏

直播信息区（可展开/收起）
├─ 标题 + 分类标签
├─ 主播信息（头像 + 姓名 + 职称）
├─ 观众数/播放数 + 开始时间
└─ [收藏] [分享] [更多]

Tabs区域（吸顶）
└─ 详情 | 聊天 | 问答 | 推荐

Tab内容区
├─ 详情: 直播介绍、标签、资料附件
├─ 聊天: 实时聊天消息流
├─ 问答: 问题列表 + 提问入口
└─ 推荐: 推荐直播列表
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad(options: { roomId?: string; sessionId?: string }) {
  showLoading()
  
  try {
    let roomData, sessionData
    
    if (options.sessionId) {
      // 通过场次ID加载
      sessionData = await getSessionDetail(options.sessionId)
      roomData = await getRoomDetail(sessionData.room_id)
    } else {
      // 通过房间ID加载
      roomData = await getRoomDetail(options.roomId)
      // 获取最新的live场次
      const sessions = await getRoomSessions(options.roomId)
      sessionData = sessions.find(s => s.status === 'live') || sessions[0]
    }
    
    // 检查流量提醒
    await checkCellularWarning()
    
    renderPage(roomData, sessionData)
    initPlayer(sessionData)
    
    hideLoading()
  } catch (error) {
    handleLoadError(error)
  }
}
```

**2. 智能播放器交互**

**播放控制**:
- status='live': 显示"直播中"标识，播放实时流
- status='replay': 显示播放进度条，支持拖拽
- status='scheduled': 显示倒计时，不可播放

**小窗模式（PIP）**:
- **触发条件**: 页面向下滚动超过播放器高度的80%
- **小窗位置**: 右下角固定，尺寸200x112px
- **交互**: 
  - 点击小窗 → 恢复全屏
  - 点击关闭按钮 → 暂停播放，隐藏小窗
  - 拖拽小窗 → 调整位置（仅App端）

**全屏播放**:
- 点击全屏按钮 → 跳转到全屏播放器页面 `/pages/room/fullscreen`
- 横屏自动进入全屏模式

**流量提醒**:
```typescript
async function checkCellularWarning() {
  const { networkType, isCellular } = await checkNetwork()
  
  if (isCellular && !getStorageSync('no_cellular_prompt')) {
    uni.showModal({
      title: '⚠️ 流量提醒',
      content: `您当前使用的是${networkType.toUpperCase()}网络，观看直播可能消耗较多流量（约500MB/小时）\n\n是否继续观看？`,
      confirmText: '继续观看',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          // 询问是否不再提醒
          setTimeout(() => askNoMorePrompt(), 1000)
        } else {
          uni.navigateBack()
        }
      }
    })
  }
}
```

**3. 直播信息区交互**

**展开/收起**:
- **默认状态**: 展示2行标题 + 主播信息（精简）
- **点击展开**: 显示完整信息（描述、标签、统计数据）
- **动画效果**: 高度渐变 + 箭头图标旋转

**操作按钮**:
- **收藏**: 点击切换收藏状态，同步到服务器
- **分享**: 打开分享面板（微信、朋友圈、复制链接）
- **更多**: 打开操作菜单（举报、不感兴趣、清晰度切换）

**4. Sticky Tabs交互**

**吸顶逻辑**:
```typescript
onPageScroll((e) => {
  const scrollTop = e.scrollTop
  const stickyThreshold = 500  // 播放器+信息区总高度
  
  if (scrollTop > stickyThreshold && !isTabsSticky.value) {
    isTabsSticky.value = true
    // 添加吸顶样式和阴影
  } else if (scrollTop <= stickyThreshold && isTabsSticky.value) {
    isTabsSticky.value = false
    // 移除吸顶样式
  }
})
```

**Tab切换**:
- 点击Tab → 切换内容，底部下划线滑动动画
- Tab栏滚动到可见位置

**5. Tab内容区交互**

**详情Tab**:
- 直播介绍（富文本）
- 标签列表（可点击）
- 资料附件（PDF、图片、视频）
- 相关推荐

**聊天Tab**:
- 实时消息流（WebSocket）
- 滚动到最新消息
- 发送消息输入框（底部）
- 禁言状态提示

**问答Tab**:
- 问题列表（按热度排序）
- 提问按钮（固定底部）
- 专家回答高亮显示
- 点赞/评论功能

**推荐Tab**:
- 相似直播推荐
- 同分类直播
- 同专家其他直播

**三、异常处理**

| 异常场景 | 处理方式 |
|---------|---------|
| 视频加载失败 | 显示错误提示 + 重试按钮 |
| 网络中断 | Toast提示"网络连接失败"，自动重连 |
| 房间不存在 | 跳转到404页面 |
| 场次已结束 | 显示"直播已结束"，引导查看回放 |

---

##### 8.6.2.6 全屏播放器（Fullscreen Player）

**页面路径**: `/pages/room/fullscreen?sessionId={id}`

**一、页面结构**
```
全屏视频播放器（横屏）
└─ 16:9 播放器 + 控制栏

SaaS功能浮窗（可拖拽）
├─ 聊天浮窗（右下角）
└─ 问答浮窗（右中）
```

**二、交互流程**

**1. 页面初始化**
```typescript
async function onPageLoad(options: { sessionId: string }) {
  // 1. 锁定横屏
  uni.setScreenOrientation('landscape')
  
  // 2. 隐藏状态栏
  // #ifdef APP-PLUS
  plus.navigator.setFullscreen(true)
  // #endif
  
  // 3. 加载场次数据
  const sessionData = await getSessionDetail(options.sessionId)
  
  // 4. 初始化播放器
  initPlayer(sessionData)
  
  // 5. 初始化WebSocket（聊天/问答）
  initWebSocket(sessionData.room_id)
}
```

**2. 播放器控制**
- 单击屏幕 → 显示/隐藏控制栏
- 双击屏幕 → 播放/暂停
- 左右滑动 → 快进/快退（仅回放）
- 上下滑动（左侧） → 调节亮度
- 上下滑动（右侧） → 调节音量

**3. SaaS功能浮窗**

**聊天浮窗**:
- **位置**: 右下角，半透明背景
- **尺寸**: 300x200px
- **内容**: 最新3条聊天消息滚动显示
- **交互**: 
  - 点击浮窗 → 展开全屏聊天面板
  - 拖拽浮窗 → 调整位置

**问答浮窗**:
- **位置**: 右中，半透明背景
- **尺寸**: 300x150px
- **内容**: 最新提问和专家回答
- **交互**: 
  - 点击浮窗 → 展开全屏问答面板
  - 拖拽浮窗 → 调整位置

**4. 退出全屏**
- 点击返回按钮 → 竖屏模式 → 返回直播间页面
- 横屏切换为竖屏 → 自动退出全屏

**三、生命周期管理**
```typescript
onUnload(() => {
  // 1. 恢复竖屏
  uni.setScreenOrientation('portrait')
  
  // 2. 显示状态栏
  // #ifdef APP-PLUS
  plus.navigator.setFullscreen(false)
  // #endif
  
  // 3. 关闭WebSocket
  closeWebSocket()
  
  // 4. 停止播放器
  stopPlayer()
})
```

---

##### 8.6.2.7 我的页面（My Profile）

**页面路径**: `/pages/tabbar/my/index`

**一、页面结构**
```
用户信息卡片（顶部）
├─ 头像 + 昵称 + [编辑]
└─ 登录/注册按钮（未登录时）

功能菜单列表
├─ 我的收藏
├─ 观看历史
├─ 我的关注
├─ 消息通知
├─ 昼夜模式
├─ 清晰度设置
├─ 流量提醒
├─ 清除缓存
├─ 关于我们
└─ 退出登录

底部信息
└─ 版本号 + 隐私政策 + 用户协议
```

**二、交互流程**

**1. 用户信息卡片**

**未登录状态**:
```
[默认头像] 
  点击登录/注册
```
- 点击卡片 → 跳转到登录页 `/pages/auth/login`

**已登录状态**:
```
[用户头像] 昵称
           手机号（脱敏）
           [编辑资料]
```
- 点击头像 → 预览头像大图
- 点击"编辑资料" → 跳转到个人资料编辑页

**2. 功能菜单交互**

**我的收藏**:
- 点击 → 跳转到收藏列表页 `/pages/my/favorites`
- 显示收藏的直播间数量

**观看历史**:
- 点击 → 跳转到观看历史页 `/pages/my/history`
- 支持续播功能

**我的关注**:
- 点击 → 跳转到关注列表页 `/pages/my/following`
- 分类显示：关注的专家 | 关注的品牌 | 关注的房间

**消息通知**:
- 点击 → 跳转到消息中心 `/pages/message/index`
- 显示未读消息数量（红点）

**昼夜模式**:
- 点击 → 弹出模式选择器
- 选项：跟随系统 | 浅色模式 | 深色模式 | 定时切换
- **定时切换**: 可设置深色开始时间和浅色开始时间

**清晰度设置**:
- 点击 → 弹出清晰度选择器
- 选项：自动（默认） | 流畅 | 标清 | 高清 | 超清
- 自动模式根据网络类型智能切换

**流量提醒**:
- 点击 → 切换开关
- 开启后，使用移动网络观看直播时会弹出提醒

**清除缓存**:
- 点击 → 显示缓存大小
- 确认清除 → 清空临时文件、图片缓存
- Toast提示"已清理 XX MB 缓存"

**关于我们**:
- 点击 → 跳转到关于页面 `/pages/my/about`
- 显示：应用介绍、版本号、开发团队、开源协议

**退出登录**:
- 点击 → 二次确认弹窗
- 确认后清除Token，返回未登录状态

**3. 昼夜模式详细交互**

```typescript
// 模式选择器
function showThemePicker() {
  uni.showActionSheet({
    itemList: [
      '跟随系统',
      '浅色模式',
      '深色模式',
      '定时切换'
    ],
    success: (res) => {
      const modes = ['auto', 'light', 'dark', 'scheduled']
      const selectedMode = modes[res.tapIndex]
      
      if (selectedMode === 'scheduled') {
        // 显示时间选择器
        showScheduledTimePicker()
      } else {
        applyThemeMode(selectedMode)
      }
    }
  })
}

// 定时切换时间选择
function showScheduledTimePicker() {
  // 1. 选择深色模式开始时间
  uni.showModal({
    title: '定时切换',
    content: '请设置深色模式和浅色模式的切换时间',
    confirmText: '设置',
    success: (res) => {
      if (res.confirm) {
        // 显示时间选择器
        uni.showTimePicker({
          title: '深色模式开始时间',
          success: (darkTime) => {
            uni.showTimePicker({
              title: '浅色模式开始时间',
              success: (lightTime) => {
                saveScheduledTheme(darkTime, lightTime)
              }
            })
          }
        })
      }
    }
  })
}
```

**三、权限控制**

| 功能 | 未登录 | 已登录 |
|------|--------|--------|
| 我的收藏 | 跳转登录页 | 正常访问 |
| 观看历史 | 跳转登录页 | 正常访问 |
| 我的关注 | 跳转登录页 | 正常访问 |
| 消息通知 | 跳转登录页 | 正常访问 |
| 昼夜模式 | 正常使用 | 正常使用 |
| 清晰度设置 | 正常使用 | 正常使用 |
| 流量提醒 | 正常使用 | 正常使用 |
| 清除缓存 | 正常使用 | 正常使用 |
| 关于我们 | 正常访问 | 正常访问 |

---

#### 8.6.3 通用组件库设计规范

本节定义移动端通用组件的设计标准和代码示例，确保组件复用性和一致性。

##### 8.6.3.1 设计原则

1. **高复用性**: 组件满足多场景使用
2. **触摸优先**: 所有可点击元素 ≥ 44x44px
3. **多端适配**: 自动适配iOS、Android、小程序
4. **无障碍支持**: 支持屏幕阅读器、键盘操作
5. **性能优化**: 避免不必要的渲染和DOM操作

##### 8.6.3.2 核心组件设计

**1. 直播卡片（RoomCard）**

```vue
<template>
  <view 
    class="room-card" 
    :class="{ 'single-mode': isSingleMode }"
    @tap="handleCardClick"
  >
    <!-- 封面图 -->
    <view class="card-cover">
      <image 
        :src="room.cover_url" 
        mode="aspectFill"
        lazy-load
        @error="handleImageError"
      />
      
      <!-- 直播状态标签 -->
      <view class="status-badge" :class="room.live_status">
        <text v-if="room.live_status === 'live'">直播中</text>
        <text v-else-if="room.live_status === 'scheduled'">预告</text>
        <text v-else>回放</text>
      </view>
      
      <!-- 观众数/播放数 -->
      <view class="stat-badge">
        <uni-icons type="eye" size="12" color="#fff" />
        <text>{{ formatNumber(room.status_data.viewer_count || room.status_data.play_count) }}</text>
      </view>
    </view>
    
    <!-- 内容区 -->
    <view class="card-content">
      <text class="title">{{ room.title }}</text>
      
      <!-- 主播信息 -->
      <view class="host-info">
        <image class="avatar" :src="room.host.avatar_url" />
        <text class="name">{{ room.host.name }}</text>
        <text class="title-badge">{{ room.host.title }}</text>
      </view>
      
      <!-- 时间/热度 -->
      <view class="meta-info">
        <text v-if="room.live_status === 'scheduled'">
          {{ formatTime(room.status_data.start_time) }}
        </text>
        <text v-else>
          {{ formatHeat(room.heat) }} 热度
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  room: RoomItem
  isSingleMode?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['click'])

function handleCardClick() {
  emit('click', props.room)
}

function handleImageError() {
  // 使用默认封面
  props.room.cover_url = '/static/images/default-cover.png'
}

function formatNumber(num: number) {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  return num.toString()
}

function formatHeat(heat: number) {
  return formatNumber(heat)
}
</script>

<style scoped lang="scss">
.room-card {
  background: var(--color-background-light);
  border-radius: $radius-large;
  overflow: hidden;
  margin-bottom: $spacing-medium;
  transition: transform 0.2s ease;
  
  &:active {
    transform: scale(0.98);
  }
  
  .card-cover {
    position: relative;
    width: 100%;
    height: 200rpx;
    
    image {
      width: 100%;
      height: 100%;
    }
    
    .status-badge {
      position: absolute;
      top: $spacing-small;
      left: $spacing-small;
      padding: 4rpx 12rpx;
      border-radius: $radius-small;
      font-size: $font-size-small;
      color: #fff;
      
      &.live {
        background: $color-danger;
      }
      
      &.scheduled {
        background: $color-primary;
      }
      
      &.replay {
        background: $color-info;
      }
    }
    
    .stat-badge {
      position: absolute;
      bottom: $spacing-small;
      right: $spacing-small;
      display: flex;
      align-items: center;
      gap: 4rpx;
      padding: 4rpx 12rpx;
      background: rgba(0, 0, 0, 0.6);
      border-radius: $radius-small;
      color: #fff;
      font-size: $font-size-small;
    }
  }
  
  .card-content {
    padding: $spacing-medium;
    
    .title {
      font-size: $font-size-medium;
      color: var(--color-text-primary);
      font-weight: 600;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: $spacing-small;
    }
    
    .host-info {
      display: flex;
      align-items: center;
      gap: $spacing-small;
      margin-bottom: $spacing-small;
      
      .avatar {
        width: 40rpx;
        height: 40rpx;
        border-radius: 50%;
      }
      
      .name {
        font-size: $font-size-base;
        color: var(--color-text-secondary);
      }
      
      .title-badge {
        font-size: $font-size-small;
        color: $color-primary;
      }
    }
    
    .meta-info {
      font-size: $font-size-small;
      color: var(--color-text-secondary);
    }
  }
  
  // 单列模式样式
  &.single-mode {
    display: flex;
    
    .card-cover {
      width: 280rpx;
      flex-shrink: 0;
    }
    
    .card-content {
      flex: 1;
    }
  }
}
</style>
```

**2. 分类筛选器（CategoryTabs）**

```vue
<template>
  <scroll-view 
    scroll-x 
    class="category-tabs"
    :class="{ sticky: isSticky }"
    :scroll-left="scrollLeft"
  >
    <view 
      v-for="tab in tabs" 
      :key="tab.id"
      class="tab-item"
      :class="{ active: currentTab === tab.id }"
      @tap="handleTabClick(tab)"
      @longpress="handleTabLongPress(tab)"
    >
      <text>{{ tab.name }}</text>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Tab {
  id: string
  name: string
  type: 'default' | 'pinned' | 'all'
  isPinned?: boolean
}

interface Props {
  tabs: Tab[]
  currentTab: string
  isSticky?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['change', 'longpress'])

const scrollLeft = ref(0)

function handleTabClick(tab: Tab) {
  if (tab.id === 'all') {
    // 跳转到分类管理页
    uni.navigateTo({ url: '/pages/category/manage' })
  } else {
    emit('change', tab.id)
  }
}

function handleTabLongPress(tab: Tab) {
  if (tab.type === 'default') {
    // 震动反馈
    uni.vibrateShort({ type: 'light' })
    // 触发长按菜单
    emit('longpress', tab)
  }
}

// 监听当前Tab变化，自动滚动到可见位置
watch(() => props.currentTab, (newVal) => {
  // 计算scrollLeft，使当前Tab居中
  const index = props.tabs.findIndex(t => t.id === newVal)
  scrollLeft.value = Math.max(0, index * 120 - 300)
})
</script>

<style scoped lang="scss">
.category-tabs {
  display: flex;
  white-space: nowrap;
  background: var(--color-background-light);
  padding: $spacing-medium 0;
  border-bottom: 1rpx solid var(--color-border);
  transition: all 0.3s ease;
  
  &.sticky {
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  }
  
  .tab-item {
    display: inline-block;
    padding: $spacing-small $spacing-large;
    margin: 0 $spacing-small;
    font-size: $font-size-medium;
    color: var(--color-text-secondary);
    border-radius: $radius-base;
    transition: all 0.3s ease;
    
    &.active {
      color: $color-primary;
      background: $color-primary-light-1;
      font-weight: 600;
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
}
</style>
```

**3. 空状态组件（Empty）**

```vue
<template>
  <view class="empty-state">
    <image class="empty-image" :src="imageUrl" mode="aspectFit" />
    <text class="empty-text">{{ text }}</text>
    <button v-if="showButton" class="empty-button" @tap="handleButtonClick">
      {{ buttonText }}
    </button>
  </view>
</template>

<script setup lang="ts">
interface Props {
  type?: 'no-data' | 'no-network' | 'error' | 'no-result'
  text?: string
  buttonText?: string
  showButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'no-data',
  showButton: false
})

const emit = defineEmits(['buttonClick'])

const imageMap = {
  'no-data': '/static/images/empty-data.png',
  'no-network': '/static/images/empty-network.png',
  'error': '/static/images/empty-error.png',
  'no-result': '/static/images/empty-search.png'
}

const textMap = {
  'no-data': '暂无数据',
  'no-network': '网络连接失败',
  'error': '加载失败',
  'no-result': '暂无搜索结果'
}

const imageUrl = computed(() => imageMap[props.type])
const displayText = computed(() => props.text || textMap[props.type])

function handleButtonClick() {
  emit('buttonClick')
}
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xxlarge;
  min-height: 400rpx;
  
  .empty-image {
    width: 200rpx;
    height: 200rpx;
    margin-bottom: $spacing-large;
    opacity: 0.6;
  }
  
  .empty-text {
    font-size: $font-size-medium;
    color: var(--color-text-secondary);
    margin-bottom: $spacing-large;
  }
  
  .empty-button {
    padding: $spacing-medium $spacing-xlarge;
    background: $color-primary;
    color: #fff;
    border-radius: $radius-base;
    font-size: $font-size-medium;
  }
}
</style>
```

**4. 加载组件（Loading）**

```vue
<template>
  <view class="loading-container" :class="{ fullscreen }">
    <view class="loading-spinner">
      <view v-for="i in 3" :key="i" class="dot" :style="{ animationDelay: `${i * 0.15}s` }" />
    </view>
    <text v-if="text" class="loading-text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  fullscreen?: boolean
  text?: string
}

withDefaults(defineProps<Props>(), {
  fullscreen: false,
  text: '加载中...'
})
</script>

<style scoped lang="scss">
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xlarge;
  
  &.fullscreen {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 9999;
  }
  
  .loading-spinner {
    display: flex;
    gap: $spacing-small;
    margin-bottom: $spacing-medium;
    
    .dot {
      width: 12rpx;
      height: 12rpx;
      background: $color-primary;
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out;
    }
  }
  
  .loading-text {
    font-size: $font-size-base;
    color: var(--color-text-secondary);
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
```

---

#### 8.6.4 关键技术实现要点

本小节提炼各页面的核心技术实现要点，供开发参考。

**A. 首页核心技术点**

**A. 分类筛选器星标固定功能**

```typescript
// src/utils/category.ts
interface UserCategoryPreferences {
  pinnedDepartments: string[];  // 固定的科室ID数组
  lastUpdated: number;
}

export function getCategoryTabs() {
  const pinnedDepts = getUserPinnedDepartments();
  const allDepts = getAllDepartments();
  const defaultHotDepts = getDefaultHotDepartments();
  
  const tabs = [{ id: 'recommend', name: '推荐', type: 'default' }];
  
  // 添加用户固定的科室（带星标）
  pinnedDepts.forEach(deptId => {
    const dept = allDepts.find(d => d.id === deptId);
    if (dept) {
      tabs.push({ 
        id: dept.id, 
        name: `⭐${dept.name}`, 
        type: 'pinned',
        isPinned: true 
      });
    }
  });
  
  // 填充剩余位置
  const remainingDepts = defaultHotDepts.filter(d => !pinnedDepts.includes(d.id));
  tabs.push(...remainingDepts.slice(0, 8 - tabs.length - 1));
  
  // 添加"全部"入口
  tabs.push({ id: 'all', name: '全部 ≡', type: 'all' });
  
  return tabs;
}
```

**B. 双列/单列视图切换**

```typescript
// src/store/modules/homepage.ts
export const useHomepageStore = defineStore('homepage', {
  state: () => ({
    viewMode: 'double' as 'double' | 'single',
  }),
  
  actions: {
    toggleViewMode() {
      this.viewMode = this.viewMode === 'double' ? 'single' : 'double';
      // 保存到LocalStorage
      uni.setStorageSync('homepage_view_mode', this.viewMode);
      // 同步到服务器（已登录用户）
      if (isLoggedIn()) {
        syncPreferenceToServer('homepage_view_mode', this.viewMode);
      }
    }
  }
});
```

**C. 3D焦点图轮播**

```vue
<template>
  <swiper 
    :current="currentIndex"
    @change="handleSwiperChange"
    :circular="true"
    :autoplay="true"
    :interval="4000"
    class="carousel-3d"
  >
    <swiper-item v-for="(banner, index) in banners" :key="banner.id">
      <view 
        :class="['banner-card', getCardClass(index)]"
        @tap="handleCardClick(banner, index)"
      >
        <image :src="banner.imageUrl" mode="aspectFill" />
      </view>
    </swiper-item>
  </swiper>
</template>

<style scoped lang="scss">
.banner-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &.center {
    transform: scale(1) translateX(0);
    opacity: 1;
    z-index: 10;
  }
  
  &.left, &.right {
    transform: scale(0.85) translateX(-70%);
    opacity: 0.6;
    filter: brightness(0.8);
    z-index: 5;
  }
  
  &.right {
    transform: scale(0.85) translateX(70%);
  }
}
</style>
```

**B. 直播间核心技术点**

**A. 小窗播放器（Picture-in-Picture）**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isPIPMode = ref(false)

onPageScroll((e) => {
  const scrollTop = e.scrollTop
  const playerHeight = 300
  
  if (scrollTop > playerHeight * 0.8) {
    isPIPMode.value = true
  } else {
    isPIPMode.value = false
  }
})
</script>

<template>
  <view :class="['player-container', { 'pip-mode': isPIPMode }]">
    <video
      :src="videoUrl"
      :controls="true"
      :autoplay="true"
    />
  </view>
</template>

<style scoped lang="scss">
.player-container {
  width: 100%;
  height: 300px;
  position: relative;
  transition: all 0.3s ease;
  
  &.pip-mode {
    position: fixed;
    right: 16px;
    bottom: 16px;
    width: 200px;
    height: 112px;
    z-index: 999;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }
}
</style>
```

**B. 智能流量提醒**

```typescript
// src/utils/network.ts
export async function checkCellularWarning() {
  const res = await uni.getNetworkType()
  const networkType = res.networkType
  const isCellular = ['2g', '3g', '4g', '5g'].includes(networkType)
  
  if (isCellular) {
    const noCellularPrompt = uni.getStorageSync('no_cellular_prompt')
    
    if (!noCellularPrompt) {
      uni.showModal({
        title: '⚠️ 流量提醒',
        content: `您当前使用的是${networkType.toUpperCase()}网络，观看直播可能消耗较多流量（约500MB/小时）\n\n是否继续观看？`,
        confirmText: '继续观看',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            // 询问是否不再提醒
            setTimeout(() => {
              uni.showModal({
                title: '💡 提示',
                content: '下次使用流量时是否不再提醒？',
                confirmText: '不再提醒',
                cancelText: '仍需提醒',
                success: (res2) => {
                  if (res2.confirm) {
                    uni.setStorageSync('no_cellular_prompt', true)
                  }
                }
              })
            }, 1000)
          }
        }
      })
    }
  }
}
```

**C. Sticky Tabs滚动交互**

```vue
<template>
  <scroll-view 
    scroll-y 
    :scroll-top="scrollTop"
    @scroll="handleScroll"
    class="live-room-container"
  >
    <!-- 播放器区域 -->
    <view class="player-section" :style="{ height: playerHeight + 'px' }">
      <VideoPlayer :class="{ 'pip-mode': isPIPMode }" />
    </view>
    
    <!-- 直播信息区 -->
    <view class="info-section">
      <!-- 标题、主播信息等 -->
    </view>
    
    <!-- Tabs区域（吸顶） -->
    <view class="tabs-section" :class="{ 'sticky': isTabsSticky }">
      <view 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-item', { active: currentTab === tab.id }]"
        @tap="handleTabClick(tab.id)"
      >
        {{ tab.name }}
      </view>
    </view>
    
    <!-- Tab内容区 -->
    <view class="tab-content">
      <component :is="currentTabComponent" />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const scrollTop = ref(0)
const isTabsSticky = ref(false)
const isPIPMode = ref(false)

function handleScroll(e: any) {
  scrollTop.value = e.detail.scrollTop
  
  // 判断是否进入吸顶模式
  const stickyThreshold = 500 // 播放器+信息区总高度
  isTabsSticky.value = scrollTop.value > stickyThreshold
  
  // 判断是否进入小窗模式
  const pipThreshold = 240
  isPIPMode.value = scrollTop.value > pipThreshold
}
</script>

<style scoped lang="scss">
.tabs-section {
  display: flex;
  background-color: $color-background-light;
  border-bottom: 1rpx solid $color-border;
  
  &.sticky {
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1);
  }
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: $spacing-medium 0;
    color: $color-text-secondary;
    
    &.active {
      color: $color-primary;
      font-weight: bold;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60rpx;
        height: 4rpx;
        background-color: $color-primary;
        border-radius: 2rpx;
      }
    }
  }
}
</style>
```

**C. 昼夜模式核心技术点**

**A. 主题系统初始化**

```typescript
// src/utils/theme.ts
export type ThemeMode = 'auto' | 'light' | 'dark' | 'scheduled'

interface ThemeSettings {
  mode: ThemeMode
  scheduledDarkTime?: string
  scheduledLightTime?: string
  lastUpdated: number
}

let currentTheme: 'light' | 'dark' = 'light'

export function initTheme() {
  const settings: ThemeSettings = uni.getStorageSync('theme_settings') || {
    mode: 'auto',
    scheduledDarkTime: '21:00',
    scheduledLightTime: '07:00',
    lastUpdated: Date.now()
  }
  
  switch (settings.mode) {
    case 'auto':
      applySystemTheme()
      break
    case 'light':
      applyTheme('light')
      break
    case 'dark':
      applyTheme('dark')
      break
    case 'scheduled':
      applyScheduledTheme(settings.scheduledDarkTime!, settings.scheduledLightTime!)
      break
  }
  
  // 监听系统主题变化
  uni.onThemeChange((res) => {
    if (settings.mode === 'auto') {
      applyTheme(res.theme)
    }
  })
  
  // 启动定时检查（用于定时切换模式）
  if (settings.mode === 'scheduled') {
    setInterval(() => {
      applyScheduledTheme(settings.scheduledDarkTime!, settings.scheduledLightTime!)
    }, 60000) // 每分钟检查一次
  }
}

export function applyTheme(theme: 'light' | 'dark') {
  const rootElement = document.documentElement
  rootElement.classList.remove('light-theme', 'dark-theme')
  rootElement.classList.add(`${theme}-theme`)
  
  // 更新状态栏颜色（原生App）
  // #ifdef APP-PLUS
  plus.navigator.setStatusBarStyle(theme === 'dark' ? 'light' : 'dark')
  // #endif
  
  currentTheme = theme
  uni.$emit('themeChanged', theme)
}

function applySystemTheme() {
  uni.getSystemInfo({
    success: (res) => {
      applyTheme(res.theme || 'light')
    }
  })
}

function applyScheduledTheme(darkTime: string, lightTime: string) {
  const now = new Date()
  const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  
  let shouldBeDark = false
  
  if (darkTime < lightTime) {
    // 跨天情况
    shouldBeDark = currentTime >= darkTime || currentTime < lightTime
  } else {
    // 同一天
    shouldBeDark = currentTime >= darkTime && currentTime < lightTime
  }
  
  const targetTheme = shouldBeDark ? 'dark' : 'light'
  
  if (currentTheme !== targetTheme) {
    applyTheme(targetTheme)
  }
}
```

**B. 主题样式变量**

```scss
// src/common/theme.scss

/* 浅色模式颜色变量 */
.light-theme {
  --bg-page: #F5F5F5;
  --bg-content: #FFFFFF;
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #999999;
  --border-color: #E5E5E5;
  --color-primary: #509CEC;
  --shadow-color: rgba(0, 0, 0, 0.1);
}

/* 深色模式颜色变量 */
.dark-theme {
  --bg-page: #0E0E0E;
  --bg-content: #1F1F1F;
  --text-primary: #E5E5E5;
  --text-secondary: #999999;
  --text-tertiary: #666666;
  --border-color: #2F2F2F;
  --color-primary: #509CEC;
  --shadow-color: rgba(255, 255, 255, 0.05);
}

/* 全局主题过渡 */
* {
  transition: background-color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 应用主题变量到元素 */
page {
  background-color: var(--bg-page);
  color: var(--text-primary);
}

.card {
  background-color: var(--bg-content);
  border: 1rpx solid var(--border-color);
  box-shadow: 0 2rpx 8rpx var(--shadow-color);
}
```

#### 8.6.4 页面技术要点总结表

| 页面名称 | 路径 | 核心技术点 | API接口 | 状态管理 |
|---------|------|-----------|---------|---------|
| 首页Feed流 | `/pages/tabbar/home/index` | • 双列瀑布流<br>• 视图切换<br>• 无限滚动<br>• 3D焦点图<br>• 我的关注<br>• 星标固定 | `/api/v1/homepage/rooms`<br>`/api/v1/categories`<br>`/api/v1/featured-content` | `useHomepageStore` |
| 分类管理 | `/pages/category/manage` | • 拖拽排序<br>• 星标切换<br>• 数量限制 | `/api/v1/categories`<br>`/api/v1/users/me/preferences` | `useCategoryStore` |
| 品牌专区 | `/pages/tabbar/brand/index` | • 字母索引<br>• 领域筛选<br>• 横向滚动 | `/api/v1/brands`<br>`/api/v1/brands/{id}/content` | `useBrandStore` |
| 我的直播 | `/pages/tabbar/my-live/index` | • 快捷操作<br>• 数据统计<br>• 权限校验 | `/api/v1/rooms`（主播房间）<br>`/api/v1/sessions`（场次管理） | `useRoomStore` |
| 专家专题 | `/pages/tabbar/expert/index` | • A-Z索引<br>• 专家列表<br>• 个人聚合页 | `/api/v1/featured-experts`<br>`/api/v1/professors/{id}/content` | `useExpertStore` |
| 直播间 | `/pages/room/detail` | • 小窗播放<br>• Sticky Tabs<br>• 流量提醒<br>• 渐进式展开 | `/api/v1/rooms/{id}`<br>`/api/v1/sessions/{id}` | `useRoomStore`<br>`usePlayerStore` |
| 全屏播放器 | `/pages/room/fullscreen` | • 横屏全屏<br>• SaaS浮窗 | 无独立API | `usePlayerStore` |
| 我的页面 | `/pages/tabbar/my/index` | • 昼夜模式<br>• 定时切换<br>• 用户管理 | `/api/v1/users/me`<br>`/api/v1/users/me/preferences` | `useUserStore`<br>`useThemeStore` |

#### 8.6.5 开发注意事项

**性能优化要点**

1. **列表虚拟滚动**：
   - 首页Feed流超过50项时启用虚拟滚动
   - 使用 `recycle-list` 或第三方虚拟滚动组件

2. **图片懒加载**：
   - 所有卡片封面图使用 `lazy-load="true"`
   - 预加载下一屏的图片

3. **防抖节流**：
   - 搜索输入防抖300ms
   - 滚动事件节流100ms
   - 提交操作节流1000ms

4. **状态缓存**：
   - 已加载的列表数据缓存到Pinia
   - 切换Tab时保持滚动位置
   - 返回页面时恢复之前的状态

**用户体验要点**

1. **加载状态**：
   - 首屏使用骨架屏（Skeleton Screen）
   - 列表加载使用Loading动画
   - 操作反馈使用Toast提示

2. **空状态设计**：
   - 无数据时显示友好的空状态插画
   - 提供引导操作（如"去发现专家"）

3. **错误处理**：
   - 网络错误显示重试按钮
   - 业务错误显示具体提示信息
   - 权限错误引导用户授权或登录

4. **无障碍支持**：
   - 重要元素添加 `aria-label`
   - 支持屏幕阅读器
   - 按钮尺寸 ≥ 44x44px

**测试要点**

1. **功能测试**：
   - 所有交互操作正常响应
   - 数据正确展示和更新
   - 页面跳转和返回正常

2. **兼容性测试**：
   - iOS 13+、Android 8+
   - 微信小程序基础库 2.10.0+
   - 不同屏幕尺寸适配

3. **性能测试**：
   - 首屏加载时间 < 3秒
   - 列表滚动流畅度 ≥ 60fps
   - 内存使用合理，无泄漏

---

## 9. 前后端接口与页面功能映射

### 9.1 API设计规范

#### 9.1.1 统一响应结构

所有API接口的响应都遵循以下统一结构：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... } | null,
  "timestamp": "2025-10-23T10:00:00Z"
}
```

#### 9.1.2 分页响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "items": [ ... ]
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

#### 9.1.3 认证规范

- **公开接口**: 无需JWT Token
- **用户接口**: 需要JWT Token（`Authorization: Bearer <token>`）
- **Admin接口**: 需要JWT Token + `ADMIN` 或 `SUPERADMIN` 角色

#### 9.1.4 业务状态码体系

| 业务状态码 | 含义 | 前端处理 |
|:---------|:-----|:---------|
| `200` | 成功 | 正常处理数据 |
| `2001` | 资源不存在 | Toast提示"内容不存在"，显示空状态或返回 |
| `2002` | 资源已存在 | Toast提示"xxx已存在" |
| `2003` | 操作被禁止 | Toast提示禁止原因 |
| `2004` | 业务逻辑错误 | Toast提示错误信息 |
| `3001` | 未认证 | 清除Token，跳转登录页 |
| `3002` | 权限不足 | Toast提示"您没有访问权限"，返回上一页 |
| `4001` | 参数校验失败 | Toast提示参数错误信息 |
| `1002` | 数据库错误 | Toast提示"服务异常，请稍后重试" |
| `5001` | 服务器内部错误 | Toast提示"服务异常，请稍后重试"，显示重试按钮 |

### 9.2 核心API清单

| 功能模块 | API端点 | HTTP方法 | 前端页面 | 说明 |
|---------|---------|---------|---------|------|
| **首页** | `/api/v1/homepage/rooms` | GET | 首页Feed | 获取首页房间列表（分页） |
| | `/api/v1/categories` | GET | 首页、分类管理 | 获取科室分类列表 |
| | `/api/v1/featured-content` | GET | 首页 | 获取焦点图数据（3D轮播） |
| **用户收藏** | `/api/v1/users/me/favorites` | GET | 我的收藏 | 获取用户收藏列表 |
| | `/api/v1/users/me/favorites` | POST | 直播间详情 | 添加收藏 |
| | `/api/v1/users/me/favorites/{favorite_id}` | DELETE | 我的收藏 | 取消收藏 |
| **用户订阅** | `/api/v1/users/me/subscriptions` | GET | 我的订阅 | 获取订阅列表 |
| | `/api/v1/users/me/subscriptions` | POST | 直播间详情 | 添加订阅 |
| | `/api/v1/users/me/subscriptions/{subscription_id}` | DELETE | 我的订阅 | 取消订阅 |
| **通知** | `/api/v1/users/me/notifications` | GET | 消息中心 | 获取通知列表（分页） |
| | `/api/v1/users/me/notifications/{notification_id}/read` | POST | 消息中心 | 标记通知为已读 |
| **观看历史** | `/api/v1/users/me/watch-history` | GET | 观看历史 | 获取观看历史（分页） |
| | `/api/v1/users/me/watch-history` | POST | 直播间 | 记录观看历史 |
| **房间** | `/api/v1/rooms/{room_id}` | GET | 直播间详情 | 获取房间详情 |
| | `/api/v1/rooms/{room_id}/sessions` | GET | 直播间 | 获取房间下所有场次 |
| **场次** | `/api/v1/sessions/{session_id}` | GET | 直播间 | 获取场次详情及统计 |
| **品牌** | `/api/v1/brands` | GET | 品牌专区 | 获取品牌列表 |
| | `/api/v1/brands/{brand_id}/content` | GET | 品牌详情 | 获取品牌详情及关联专题 |
| **专家** | `/api/v1/featured-experts` | GET | 专家专题 | 获取推荐专家列表 |
| | `/api/v1/professors/{expert_id}/content` | GET | 专家详情 | 获取专家详情及主讲场次 |
| **搜索** | `/api/v1/search` | GET | 搜索页 | 全局搜索（支持多类型） |
| **标签** | `/api/v1/tags` | GET | 首页、搜索 | 获取标签列表 |

### 9.3 关键API详细说明

#### 9.3.1 首页房间列表API

**请求**: `GET /api/v1/homepage/rooms`

**查询参数**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10, 最大100): 每页数量
- `sort` (string, 可选, 默认`heat:desc`): 排序规则（`heat:desc`, `start_time:asc`, `created_at:desc`）
- `category_id` (UUID, 可选): 按分类筛选

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "room_uuid_1",
        "title": "肝胆胰外科手术直播演示",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "summary": "演示最新的微创技术...",
        "live_status": "live",
        "host": {
          "expert_id": "expert_uuid_doc_B",
          "user_id": null,
          "name": "李四 教授",
          "title": "主任医师",
          "hospital": "XX 医院"
        },
        "status_data": {
          "viewer_count": 1250,
          "start_time": null,
          "duration_seconds": null,
          "play_count": null
        },
        "heat": 8500
      }
    ]
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**字段说明**:
- `live_status`: 直播状态枚举 (`live` | `scheduled` | `replay`)
- `host`: 主讲人信息，优先级：featured_expert > 房主专家 > 房主用户
- `status_data`: 根据 `live_status` 动态填充（`live`填充`viewer_count`，`scheduled`填充`start_time`，`replay`填充`duration_seconds`和`play_count`）
- `heat`: 热度值，用于排序（计算公式：`current_viewer_count * 10 + peak_viewer_count * 5 + play_count`）

#### 9.3.2 专家详情API

**请求**: `GET /api/v1/professors/{expert_id}/content`

**查询参数**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "expert_info": {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "name": "房树强",
      "title": "主任医师、教授",
      "hospital": "北京大学人民医院",
      "department": "肝胆外科",
      "expertise_areas": "肝胆胰脾外科,微创手术",
      "bio": "从事肝胆外科临床工作30余年...",
      "avatar_url": "/media/experts/fangshuqiang.jpg"
    },
    "sessions": {
      "total": 15,
      "page": 1,
      "size": 10,
      "items": [...]
    }
  },
  "timestamp": "2025-10-23T13:05:00Z"
}
```

#### 9.3.3 品牌详情API

**请求**: `GET /api/v1/brands/{brand_id}/content`

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_info": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "迈瑞医疗",
      "logo_url": "/media/brands/mindray-logo.png",
      "description": "医疗器械行业领军企业",
      "website_url": "https://www.mindray.com"
    },
    "associated_topics": [...]
  },
  "timestamp": "2025-10-23T12:05:00Z"
}
```

#### 9.3.4 焦点图API

**请求**: `GET /api/v1/featured-content`

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "featured_uuid_1",
      "title": "全国骨科学术研讨会",
      "image_url": "/media/featured/banner1.jpg",
      "target_type": "session",
      "target_id": "session_uuid_123",
      "target_url": null,
      "cta_text": "立即观看",
      "sort_order": 0
    }
  ],
  "timestamp": "2025-10-23T14:00:00Z"
}
```

**字段说明**:
- `target_type`: 跳转类型枚举 (`session` | `topic` | `external`)
- `target_id`: 当 `target_type` 为 `session` 或 `topic` 时的资源ID
- `target_url`: 当 `target_type` 为 `external` 时的外部链接

### 9.4 页面功能与接口交互流程（全量映射）

本节详细描述移动端各页面如何调用后端API，确保前后端联调顺畅。

---

#### 9.4.1 首页模块交互流程

**1. 页面初始化加载**

```typescript
// /pages/tabbar/home/index.vue
async function onPageLoad() {
  try {
    // 并行加载多个接口
    const [categories, featured, followed, rooms] = await Promise.all([
      getCategories(),                    // GET /api/v1/categories
      getFeaturedContent(),               // GET /api/v1/featured-content
      getFollowedExperts(),               // GET /api/v1/users/me/subscriptions?target_type=expert
      getHomepageRooms({ page: 1 })      // GET /api/v1/homepage/rooms?page=1&size=20
    ])
    
    renderPage(categories, featured, followed, rooms)
  } catch (error) {
    handleError(error)
  }
}
```

**2. 分类切换**

```typescript
async function handleCategoryChange(categoryId: string) {
  isLoading.value = true
  
  try {
    const rooms = await getHomepageRooms({
      page: 1,
      size: 20,
      category_id: categoryId  // 按分类筛选
    })
    
    roomList.value = rooms.items
    currentPage.value = 1
    hasMore.value = rooms.total > rooms.items.length
  } catch (error) {
    handleError(error)
  } finally {
    isLoading.value = false
  }
}
```

**3. 下拉刷新**

```typescript
async function onPullDownRefresh() {
  try {
    const rooms = await getHomepageRooms({
      page: 1,
      size: 20,
      category_id: currentCategory.value
    })
    
    roomList.value = rooms.items
    currentPage.value = 1
    hasMore.value = rooms.total > rooms.items.length
    
    uni.stopPullDownRefresh()
  } catch (error) {
    uni.stopPullDownRefresh()
    handleError(error)
  }
}
```

**4. 上拉加载更多**

```typescript
async function onReachBottom() {
  if (isLoading.value || !hasMore.value) return
  
  isLoading.value = true
  const nextPage = currentPage.value + 1
  
  try {
    const rooms = await getHomepageRooms({
      page: nextPage,
      size: 20,
      category_id: currentCategory.value
    })
    
    roomList.value.push(...rooms.items)
    currentPage.value = nextPage
    hasMore.value = rooms.total > (nextPage * 20)
  } catch (error) {
    handleError(error)
  } finally {
    isLoading.value = false
  }
}
```

---

#### 9.4.2 品牌专区模块交互流程

**1. 页面初始化**

```typescript
// /pages/tabbar/brand/index.vue
async function onPageLoad() {
  try {
    const [featured, all] = await Promise.all([
      getFeaturedBrands(),    // GET /api/v1/brands?is_featured=true
      getAllBrands()          // GET /api/v1/brands?sort=name_asc
    ])
    
    featuredBrands.value = featured
    allBrands.value = groupByInitial(all)
  } catch (error) {
    handleError(error)
  }
}
```

**2. 品牌详情页加载**

```typescript
// /pages/brand/detail.vue
async function loadBrandDetail(brandId: string) {
  try {
    const brand = await getBrandContent(brandId)  // GET /api/v1/brands/{brand_id}/content
    
    brandInfo.value = brand.brand_info
    topics.value = brand.associated_topics
  } catch (error) {
    if (error.code === 2001) {
      // 品牌不存在，跳转404
      uni.redirectTo({ url: '/pages/common/404' })
    } else {
      handleError(error)
    }
  }
}
```

**3. 关注/取消关注品牌**

```typescript
async function handleFollowBrand(brandId: string) {
  if (!isLoggedIn()) {
    uni.navigateTo({ url: '/pages/auth/login' })
    return
  }
  
  try {
    if (isFollowed.value) {
      // 取消关注
      await deleteSubscription(subscriptionId.value)  // DELETE /api/v1/users/me/subscriptions/{id}
      isFollowed.value = false
      uni.showToast({ title: '已取消关注', icon: 'success' })
    } else {
      // 添加关注
      const result = await createSubscription({
        target_type: 'brand',
        target_id: brandId
      })  // POST /api/v1/users/me/subscriptions
      
      subscriptionId.value = result.id
      isFollowed.value = true
      uni.showToast({ title: '关注成功', icon: 'success' })
    }
  } catch (error) {
    handleError(error)
  }
}
```

---

#### 9.4.3 专家专题模块交互流程

**1. 页面初始化**

```typescript
// /pages/tabbar/expert/index.vue
async function onPageLoad() {
  try {
    const [featured, all] = await Promise.all([
      getFeaturedExperts(),   // GET /api/v1/featured-experts
      getAllExperts()         // GET /api/v1/experts?sort=name_asc
    ])
    
    featuredExperts.value = featured
    allExperts.value = groupByInitial(all)
  } catch (error) {
    handleError(error)
  }
}
```

**2. 专家详情页加载**

```typescript
// /pages/expert/detail.vue
async function loadExpertDetail(expertId: string) {
  try {
    const expert = await getExpertContent(expertId)  // GET /api/v1/professors/{expert_id}/content
    
    expertInfo.value = expert.expert_info
    sessions.value = expert.sessions.items
    totalSessions.value = expert.sessions.total
  } catch (error) {
    if (error.code === 2001) {
      uni.redirectTo({ url: '/pages/common/404' })
    } else {
      handleError(error)
    }
  }
}
```

---

#### 9.4.4 直播间模块交互流程

**1. 直播间初始化**

```typescript
// /pages/room/detail.vue
async function onPageLoad(options: { roomId?: string; sessionId?: string }) {
  try {
    let roomData, sessionData
    
    if (options.sessionId) {
      // 通过场次ID加载
      sessionData = await getSessionDetail(options.sessionId)  // GET /api/v1/sessions/{session_id}
      roomData = await getRoomDetail(sessionData.room_id)      // GET /api/v1/rooms/{room_id}
    } else {
      // 通过房间ID加载
      roomData = await getRoomDetail(options.roomId)
      const sessions = await getRoomSessions(options.roomId)   // GET /api/v1/rooms/{room_id}/sessions
      sessionData = sessions.find(s => s.status === 'live') || sessions[0]
    }
    
    // 记录观看历史
    if (isLoggedIn() && sessionData.status === 'live') {
      recordWatchHistory(sessionData.id)  // POST /api/v1/users/me/watch-history
    }
    
    renderPage(roomData, sessionData)
  } catch (error) {
    handleError(error)
  }
}
```

**2. 收藏/取消收藏**

```typescript
async function handleFavorite(roomId: string) {
  if (!isLoggedIn()) {
    uni.navigateTo({ url: '/pages/auth/login' })
    return
  }
  
  try {
    if (isFavorited.value) {
      await deleteFavorite(favoriteId.value)  // DELETE /api/v1/users/me/favorites/{favorite_id}
      isFavorited.value = false
      uni.showToast({ title: '已取消收藏', icon: 'success' })
    } else {
      const result = await createFavorite({ room_id: roomId })  // POST /api/v1/users/me/favorites
      favoriteId.value = result.id
      isFavorited.value = true
      uni.showToast({ title: '收藏成功', icon: 'success' })
    }
  } catch (error) {
    handleError(error)
  }
}
```

**3. 更新观看进度**

```typescript
let watchTimer: number | null = null

function startWatchTracking(sessionId: string) {
  // 每30秒更新一次观看进度
  watchTimer = setInterval(async () => {
    try {
      await updateWatchHistory({
        session_id: sessionId,
        watch_duration: getCurrentWatchDuration(),
        last_position: getCurrentPlayPosition()
      })  // POST /api/v1/users/me/watch-history
    } catch (error) {
      console.error('更新观看进度失败', error)
    }
  }, 30000)
}

onUnmounted(() => {
  if (watchTimer) {
    clearInterval(watchTimer)
  }
})
```

---

#### 9.4.5 我的页面模块交互流程

**1. 用户信息加载**

```typescript
// /pages/tabbar/my/index.vue
async function loadUserInfo() {
  if (!isLoggedIn()) return
  
  try {
    const user = await getUserProfile()  // GET /api/v1/users/me
    userInfo.value = user
  } catch (error) {
    if (error.code === 3001) {
      // Token过期，清除并跳转登录
      uni.removeStorageSync('token')
      isLoggedIn.value = false
    } else {
      handleError(error)
    }
  }
}
```

**2. 我的收藏加载**

```typescript
// /pages/my/favorites.vue
async function loadFavorites() {
  try {
    const result = await getFavorites({
      page: currentPage.value,
      size: 20
    })  // GET /api/v1/users/me/favorites?page=1&size=20
    
    if (currentPage.value === 1) {
      favoriteList.value = result.items
    } else {
      favoriteList.value.push(...result.items)
    }
    
    hasMore.value = result.total > (currentPage.value * 20)
  } catch (error) {
    handleError(error)
  }
}
```

**3. 观看历史加载**

```typescript
// /pages/my/history.vue
async function loadWatchHistory() {
  try {
    const result = await getWatchHistory({
      page: currentPage.value,
      size: 20
    })  // GET /api/v1/users/me/watch-history?page=1&size=20
    
    historyList.value = currentPage.value === 1 
      ? result.items 
      : [...historyList.value, ...result.items]
    
    hasMore.value = result.total > (currentPage.value * 20)
  } catch (error) {
    handleError(error)
  }
}
```

**4. 用户偏好设置同步**

```typescript
// 保存用户偏好到服务器
async function savePreference(key: string, value: any) {
  if (!isLoggedIn()) return
  
  try {
    await updateUserPreferences({
      [key]: value
    })  // PATCH /api/v1/users/me/preferences
  } catch (error) {
    console.error('保存偏好失败', error)
  }
}

// 示例：保存昼夜模式偏好
async function saveThemeMode(mode: string) {
  uni.setStorageSync('theme_mode', mode)
  await savePreference('theme_mode', mode)
}
```

---

#### 9.4.6 消息中心模块交互流程

**1. 消息列表加载**

```typescript
// /pages/message/index.vue
async function loadNotifications() {
  try {
    const result = await getNotifications({
      page: currentPage.value,
      size: 20,
      is_read: filterType.value === 'unread' ? false : undefined
    })  // GET /api/v1/users/me/notifications?page=1&size=20
    
    notificationList.value = currentPage.value === 1
      ? result.items
      : [...notificationList.value, ...result.items]
    
    unreadCount.value = result.unread_count
    hasMore.value = result.total > (currentPage.value * 20)
  } catch (error) {
    handleError(error)
  }
}
```

**2. 标记消息已读**

```typescript
async function markAsRead(notificationId: string) {
  try {
    await markNotificationRead(notificationId)  // POST /api/v1/users/me/notifications/{id}/read
    
    // 更新本地状态
    const notification = notificationList.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  } catch (error) {
    console.error('标记已读失败', error)
  }
}
```

---

### 9.5 API调用规范

#### 9.5.1 统一封装
所有API调用必须通过 `src/api/` 目录下的封装函数，禁止直接调用 `uni.request`：

```typescript
// ❌ 错误示例（禁止）
uni.request({
  url: 'https://api.example.com/rooms',
  success: (res) => { ... }
})

// ✅ 正确示例（必须）
import { getHomepageRooms } from '@/api/homepage'

const response = await getHomepageRooms({
  page: 1,
  page_size: 20
})
```

#### 9.5.2 完整错误处理
```typescript
try {
  const response = await getHomepageRooms({ page: 1, page_size: 20 })
  roomList.value = response.items
} catch (error: any) {
  console.error('[加载失败]', error)
  
  if (error.statusCode === 401 || error.code === 3001) {
    // 清除Token，跳转登录
    uni.removeStorageSync('token')
    uni.navigateTo({ url: '/pages/auth/login' })
  } else if (error.code === 2001) {
    // 资源不存在
    uni.showToast({ title: '内容不存在', icon: 'none' })
  } else if (error.statusCode >= 500 || error.code >= 5000) {
    // 服务器错误，显示重试
    uni.showModal({
      title: '加载失败',
      content: '服务异常，请稍后重试',
      confirmText: '重试',
      success: (res) => {
        if (res.confirm) {
          // 重试逻辑
          loadData()
        }
      }
    })
  } else {
    // 其他错误，显示错误信息
    uni.showToast({
      title: error.message || '操作失败',
      icon: 'none'
    })
  }
}
```

#### 9.5.3 请求头规范

```typescript
// src/api/request.ts 中的请求拦截器
function requestInterceptor(config: RequestConfig) {
  // 自动注入Token
  const token = uni.getStorageSync('token')
  if (token) {
    config.header = config.header || {}
    config.header.Authorization = `Bearer ${token}`
  }
  
  // 自动注入Content-Type
  if (config.method === 'POST' || config.method === 'PATCH') {
    config.header['Content-Type'] = 'application/json'
  }
  
  // 自动注入平台标识
  config.header['X-Platform'] = getPlatform()  // h5/android/ios/mp-weixin
  config.header['X-App-Version'] = getAppVersion()
  
  return config
}

function getPlatform() {
  // #ifdef H5
  return 'h5'
  // #endif
  
  // #ifdef APP-PLUS
  return uni.getSystemInfoSync().platform  // android/ios
  // #endif
  
  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif
  
  return 'unknown'
}
```

---

## 10. 测试规范

### 10.1 单元测试

- **测试框架**：Jest + @vue/test-utils
- **覆盖率要求**：核心业务逻辑 ≥ 80%
- **测试位置**：与业务代码同目录或 `tests/` 下分模块存放

### 10.2 端到端测试

- **H5端**：Cypress
- **小程序端**：uni-app官方测试工具
- **App端**：Appium

### 10.3 兼容性测试

必须在以下平台真机测试：

| 平台 | 测试设备 | 测试要点 |
|------|---------|---------|
| iOS App | iPhone 12+, iOS 14+ | 刘海屏适配、手势冲突、权限申请 |
| Android App | 主流品牌（华为、小米、OPPO） | 系统差异、权限管理、返回键处理 |
| 微信小程序 | 微信开发者工具 + 真机 | API兼容性、包大小、审核规范 |
| H5 | Chrome、Safari、微信内置浏览器 | 响应式布局、浏览器兼容性 |

---

## 11. 开发实施计划

### 11.1 阶段划分

#### 阶段1：项目初始化（1周）
- uni-app项目搭建、目录结构规划
- 基础依赖安装（Vue3、Pinia、TypeScript、Vant/uView等）
- ESLint/Prettier/TS配置
- Git仓库初始化、分支策略

#### 阶段2：基础功能开发（3周）
- 底部Tab导航栏
- 首页Feed流（双列瀑布流、视图切换）
- 分类筛选器（吸顶、星标固定）
- 3D焦点图轮播
- 直播卡片组件
- API接口封装、状态管理实现

#### 阶段3：核心业务页面（4周）
- 品牌专区页面
- 专家专题页面
- 我的直播（主播后台）
- 直播间详情页（小窗播放、Sticky Tabs）
- 全屏播放器
- 搜索功能

#### 阶段4：用户体系与设置（2周）
- 登录注册
- 我的页面
- 昼夜模式设置
- 用户偏好管理
- 消息中心（预留）

#### 阶段5：测试与优化（2周）
- 单元测试、集成测试
- 多端真机测试
- 性能优化（首屏、流量、内存）
- Bug修复、代码重构

#### 阶段6：上线准备（1周）
- 多端打包发布
- 应用商店上架准备
- 小程序审核提交
- 上线监控与日志

### 11.2 里程碑

- **M1（Week 4）**：项目结构与首页完成，可演示基础Feed流
- **M2（Week 8）**：核心页面开发完成，可完成完整浏览流程
- **M3（Week 10）**：用户体系完成，支持登录和个性化设置
- **M4（Week 12）**：测试通过，体验优化，准备上线
- **M5（Week 13）**：正式发布上线

---

## 12. 附录

### 12.1 参考资料

- [uni-app 官方文档](https://uniapp.dcloud.io/)
- [Vue3 官方文档](https://cn.vuejs.org/)
- [Pinia 官方文档](https://pinia.vuejs.org/zh/)
- [TypeScript 官方文档](https://www.typescriptlang.org/zh/)
- [Bilibili 移动端设计参考](https://www.bilibili.com/)
- [iOS 人机界面指南](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design 设计规范](https://material.io/design)

### 12.2 设计规范文档

- 《直播SaaS平台前端设计文档.md》（PC端）
- 《后端新增api接口和模块设计文档-v2.md》
- 《直播saas平台网站前端效果设计---移动端版(v1.3）.md》（原产品设计文档）

### 12.3 更新日志

#### V1.3（本版本 - 2025-11-05）
- 🔥 **规范化改写**：参考PC端设计文档格式，补充完整的开发规范
- ✨ **新增章节**：角色定位、文档目的、代码规范、安全规范、异常处理、性能优化、测试规范
- 📝 **结构优化**：使文档更加专业化、结构化、可执行
- 🔧 **技术细节**：补充大量技术实现代码示例和最佳实践

#### V1.3（原版本 - 产品设计）
- ✨ 3D焦点图轮播
- ✨ 我的关注区域
- ✨ 昼夜模式设置
- 🔧 私信功能预留

#### V1.2
- 品牌专区独立Tab
- 科室分类星标固定功能
- 双列瀑布流布局
- 视图模式切换

#### V1.0
- 完整的移动端UI/UX设计
- 参考Bilibili设计范式
- 医学直播专业化功能

---

**文档编写：** AI Assistant
**最后更新：** 2025-11-05
**文档版本：** V1.3 (规范化版)

