# 直播SaaS平台前端设计文档

---

## 1. 角色定位说明

**作者角色：资深前端工程师**

- 具备大型直播平台（如哔哩哔哩、抖音）前端架构与实现经验。
- 精通 uni-app、Vue3、TypeScript、H5、小程序等多端开发。
- 熟悉高并发、低延迟直播场景下的前端性能优化与用户体验设计。
- 具备团队协作、规范制定、前后端协同与持续集成能力。

---

## 2. 文档目的与项目背景

### 2.1 文档目的
本设计文档旨在为“直播SaaS平台”前端项目（@/frontend_live）提供系统性、标准化的设计与开发指导，确保团队协作高效、代码质量可控、功能实现与后端接口高度一致。本项目目标是实现一套可在PC浏览器、Android App、iOS App和微信小程序等多端部署的直播平台前端，满足多端用户的直播观看、推流、互动等需求。
### 2.2 项目背景
- 平台采用前后端分离架构，后端接口详见《直播核心功能设计文档.md》。
- 前端基于 uni-app 实现，需支持H5、Android、iOS、微信小程序等多端适配。
- 参考主流直播平台（如哔哩哔哩、抖音）的交互与体验，，但所有功能和页面以现有后端接口为准，确保前后端高度一致、无冗余开发。

---

## 3. 前端开发规范

### 3.1 代码规范
- 统一风格：全项目采用 ESLint + Prettier 自动格式化，统一2空格缩进，结尾无分号，单引号为主。
- TypeScript 优先：新开发页面和组件必须使用 TypeScript，类型声明完整，接口数据类型与后端保持同步。
- 组件化开发：每个页面/业务功能拆分为小型、可复用的组件，单文件组件（.vue）结构清晰（<template> <script lang=\"ts\"> <style scoped>）。
- 禁止魔法数字/硬编码：所有常量、枚举、配置项集中管理（如 src/common/constants.ts）。
- 注释规范：关键业务逻辑、接口调用、复杂计算必须有中英文注释，函数/组件需有JSDoc风格注释。
- Git 提交规范：采用 Conventional Commits 规范，便于自动化CI/CD和版本管理。

### 3.2 命名规范
- 变量/函数：`camelCase`（如：liveRoomList）
- 组件/页面：`PascalCase`（如：LiveRoomList.vue）
- 文件/目录：`kebab-case`（如：live-room-list.vue）
- 常量：`UPPER_SNAKE_CASE`（如：MAX_ROOM_COUNT）
- API接口：`api/xxx.js`，服务：`services/xxx.js`
- 状态管理：store/xxx.ts，模块名与业务一致

### 3.3 项目结构规范
- **[最高标准]** 全局项目结构必须严格遵循以下规范，确保清晰、一致、可维护。所有新文件的创建都必须在此结构下进行。
```plaintext
frontend_live/
├── src/
│   ├── App.vue                        # 应用入口主组件
│   ├── main.ts                        # 应用入口JS
│   ├── pages.json                     # uni-app页面路由配置
│   ├── manifest.json                  # uni-app应用配置
│   ├── env.d.ts                       # 全局TypeScript环境声明
│   ├── uni.scss                       # 全局样式变量
│   ├── api/                           # 后端接口封装
│   ├── common/                        # 全局样式、mixin、常量
│   ├── components/                    # 通用/业务组件
│   ├── pages/                         # 页面级组件（按业务模块分子目录）
│   ├── store/                         # 全局状态管理
│   ├── static/                        # 静态资源（图片、icon等）
│   ├── types/                         # 全局TypeScript类型定义
│   ├── utils/                         # 工具函数
│   └── logs/                          # 新增的日志管理模块
│       ├── logger.ts                  # 日志记录和管理的实现
│       ├── logTypes.ts                # 日志类型定义
│       └── logConfig.ts               # 日志配置文件
│
├── tests/                         # 单元/集成/端到端测试
├── uni_modules/                   # uni-app插件
├── package.json                   # 项目依赖与脚本
├── vite.config.ts                 # Vite 构建配置
├── tsconfig.json                  # TypeScript 编译器配置
├── jest.config.js                 # 单元测试配置
├── .prettierrc                    # 代码格式化配置
├── .eslintrc.js                   # 代码规范配置
├── index.html                     # H5入口
├── README.md                      # 项目说明文档
└── ...                            # 其他根目录配置文件
```

**为确保任务明确、无歧义，完整且详细的前端项目结构框架：**

### A. 项目基础结构与配置文件（Project Skeleton & Config Files）
- **根目录文件与目录 (Root Files & Dirs):**
  - `package.json`: 项目依赖与脚本
  - `tsconfig.json`: TypeScript 编译器配置
  - `vite.config.ts`: Vite 构建配置
  - `.eslintrc.js`: ESLint 代码规范配置
  - `.prettierrc`: Prettier 代码格式化配置
  - `jest.config.js`: Jest 测试框架配置
  - `.gitignore`: Git 忽略文件配置
  - `README.md`: 项目说明文档
  - `tests/`: 测试用例目录
  - `uni_modules/`: uni-app 插件目录
- **核心源码目录 (Core Source Directory):**
  - `src/`: **唯一**的核心源码目录，包含以下所有内容：
    - `App.vue`: 应用入口组件
    - `main.ts`: Vue 初始化脚本
    - `pages.json`: 页面路由与窗口表现配置
    - `manifest.json`: 应用配置
    - `env.d.ts`: 全局 TypeScript 环境声明
    - `api/`: 后端接口封装目录
    - `common/`: 全局样式与公共资源目录
    - `components/`: 通用组件目录
    - `pages/`: 页面级组件目录
    - `static/`: 静态资源目录
    - `store/`: 全局状态管理 (Pinia) 目录
    - `types/`: 全局 TypeScript 类型定义目录
    - `utils/`: 工具函数目录
    - `logs/`: 新增的日志管理模块
      - `logger.ts`: 日志记录和管理的实现
      - `logTypes.ts`: 日志类型定义
      - `logConfig.ts`: 日志配置文件

### B. 初始化核心业务文件（Initial Core Business Files）
- **接口与状态管理 (`src/api/` & `src/store/`):**
  - `src/api/room.ts`: 房间相关接口
  - `src/api/session.ts`: 场次相关接口
  - `src/store/index.ts`: Pinia 入口文件
  - `src/store/room.ts`: 房间状态管理
  - `src/store/session.ts`: 场次状态管理
- **全局类型定义 (`src/types/`):**
  - `src/types/room.ts`: 房间相关的类型定义
  - `src/types/session.ts`: 场次相关的类型定义
- **全局工具 (`src/utils/`):**
  - `src/utils/request.ts`: 基于`uni.request`的统一请求封装
- **核心业务页面 (`src/pages/`):**
  - `src/pages/room/RoomList.vue`: 房间列表页
  - `src/pages/room/RoomDetail.vue`: 房间详情页
  - `src/pages/live/LiveView.vue`: 直播观看页
  - `src/pages/common/NotFound.vue`: 404页面
- **核心通用组件 (`src/components/`):**
  - `src/components/RoomCard.vue`: 房间卡片组件
  - `src/components/ModalDialog.vue`: 通用弹窗组件
  - `src/components/AppButton.vue`: 通用按钮组件

### 3.4 测试规范
- 单元测试：Jest + @vue/test-utils，覆盖率>80%
- 端到端测试：H5端推荐Cypress，小程序端用uni-app官方测试工具
- 重要业务流程、核心组件必须有测试用例
- 测试用例与业务代码同目录或tests/下分模块存放
- 所有接口mock数据需与后端接口文档保持同步

### 3.5 前端安全规范（医学数据场景）
- **XSS防护**：所有用户输入、接口返回内容渲染前必须进行转义，严禁直接插入HTML。推荐使用Vue/uni-app自带的插值语法（{{}}）自动防护。
- **敏感信息脱敏**：涉及患者、医生等敏感数据（如手机号、身份证、病例号等）前端展示时需做脱敏处理（如只显示部分位数）。
- **HTTPS强制**：所有前端页面和API请求必须通过HTTPS协议，禁止明文HTTP。
- **Token安全存储**：Token等敏感凭证仅存于内存或HttpOnly Cookie，禁止localStorage/sessionStorage明文存储。
- **接口安全**：所有API请求需带上后端分配的Token，前端需校验接口返回的权限和状态码，异常时及时提示并跳转。
- **防止CSRF**：如涉及表单/操作类接口，需配合后端CSRF防护机制。
- **前端日志脱敏**：前端日志、埋点、监控上报时，禁止上传任何敏感用户信息。
- **第三方依赖安全**：定期升级依赖库，避免引入有安全漏洞的包。

---

## 4. 前端异常处理规范

- 网络异常：统一封装request拦截器，自动处理超时、断网、接口异常，弹出友好提示
- 业务异常：后端返回非200业务码时，前端根据code/message展示对应错误（如：房间不存在、禁止操作等）
- 全局异常捕获：App.vue中注册全局错误处理，收集上报异常日志
- 用户操作异常：如表单校验失败、非法输入，前端本地校验并提示
- 兜底降级：部分功能异常时，页面可降级为只读、简化模式，保证核心直播观看/推流不受影响

## 前端日志管理与设置

- **前端日志脱敏**：前端日志、埋点、监控上报时，禁止上传任何敏感用户信息。所有日志记录必须经过脱敏处理，确保不泄露用户的个人信息。具体措施包括：
  - 对敏感信息（如手机号、身份证号、邮箱等）进行遮蔽或替换。
  - 使用正则表达式或专门的脱敏库来自动处理敏感数据。

- **日志记录规范**：
  - **日志内容**:
    - 所有日志应包含以下信息：
      - **时间戳**: 记录事件发生的时间，格式应统一（如 ISO 8601）。
      - **日志级别**: 使用标准日志级别（如 INFO、WARN、ERROR、DEBUG）来标识日志的重要性。
      - **模块名称**: 记录日志的模块或组件名称，便于后续追踪。
      - **具体的错误信息**: 包含详细的错误描述和上下文信息，帮助开发者快速定位问题。
  - **存储位置**:
    - 日志应存储在安全的位置，确保只有授权人员可以访问。
    - 可以使用集中式日志管理工具（如 ELK Stack、Graylog、Splunk 等）来存储和分析日志。
  - **定期审查和清理**:
    - 定期审查日志内容，确保不存储过期或不必要的日志信息。
    - 设置日志保留策略，自动删除超过保留期限的日志。

- **日志上报机制**：
  - **统一的日志上报接口**:
    - 设计一个统一的日志上报接口，确保所有日志信息能够集中管理。
    - 接口应支持批量上报，以减少网络请求次数。
  - **异步上报**:
    - 采用异步方式上报日志，避免影响用户体验。可以使用 `fetch` API 进行异步请求。
  - **记录上报状态**:
    - 记录上报成功与失败的状态，确保日志的完整性。
    - 对于上报失败的日志，考虑重试机制，确保重要日志能够最终被记录。

- **日志监控与告警**:
  - **实时监控**: 
    - 使用日志管理工具的实时监控功能，及时发现异常情况（如高频错误、用户异常行为等）。
  - **告警机制**:
    - 设置告警规则，当日志中出现特定的错误或异常时，自动通知相关人员（如开发团队、运维团队）。

- **日志分析与优化**:
  - **定期分析**:
    - 定期对日志进行分析，识别常见问题和用户行为模式，帮助优化产品和用户体验。
  - **反馈机制**:
    - 将日志分析结果反馈给开发团队，作为产品迭代和优化的依据。

---

## 5. 前端设计概述

### 5.1 项目结构
```

以下为建议生成的前端项目目录结构，具体到主要文件和文件夹，已与现有frontend_live目录融合，并完全对齐前端设计文档：

```plaintext
frontend_live/
├── src/
│   ├── App.vue                        # 应用入口主组件
│   ├── main.ts                        # 应用入口JS
│   ├── pages.json                     # uni-app页面路由配置
│   ├── manifest.json                  # uni-app应用配置
│   ├── env.d.ts                       # 全局TypeScript环境声明
│   ├── uni.scss                       # 全局样式变量
│   ├── api/                           # 后端接口封装
│   ├── common/                        # 全局样式、mixin、常量
│   ├── components/                    # 通用/业务组件
│   ├── pages/                         # 页面级组件（按业务模块分子目录）
│   ├── store/                         # 全局状态管理
│   ├── static/                        # 静态资源（图片、icon等）
│   ├── types/                         # 全局TypeScript类型定义
│   ├── utils/                         # 工具函数
│   └── logs/                          # 新增的日志管理模块
│       ├── logger.ts                  # 日志记录和管理的实现
│       ├── logTypes.ts                # 日志类型定义
│       └── logConfig.ts               # 日志配置文件
│
├── tests/                         # 单元/集成/端到端测试
├── uni_modules/                   # uni-app插件
├── package.json                   # 项目依赖与脚本
├── vite.config.ts                 # Vite 构建配置
├── tsconfig.json                  # TypeScript 编译器配置
├── jest.config.js                 # 单元测试配置
├── .prettierrc                    # 代码格式化配置
├── .eslintrc.js                   # 代码规范配置
├── index.html                     # H5入口
├── README.md                      # 项目说明文档
└── ...                            # 其他根目录配置文件
```


### 5.2 框架选型
- uni-app（Vue3 + Composition API）
- 状态管理：Pinia（推荐）
- UI库：uView Plus、NutUI、Vant等（按需引入）
- 视频播放：uni-app自带video组件（优先，兼容小程序）、H5端可选video.js
- 网络请求：基于uni.request二次封装，适配FastAPI后端RESTful接口风格，支持token自动注入、统一异常处理
- 路由：uni-app内置路由
- 多端适配：H5、Android、iOS、微信小程序一套代码多端发布
- 接口Mock：开发阶段可用Mock服务，接口结构严格参照FastAPI后端文档

### 5.3 核心设计原则
- 组件化、模块化、可复用
- 响应式布局，适配多端
- 关注直播流畅性与低延迟体验
- 关注弱网、异常场景下的用户体验
- 代码与接口解耦，便于后端变更适配

---

## 6. 数据库设计（核心表结构）

本节简要介绍直播核心模块的数据库设计，帮助前端理解接口数据结构和字段含义。

### 6.1 设计原则
- **双表模型**：将直播房间（live_rooms）与直播场次（live_sessions）分离，结构清晰、易扩展。
- **UUID主键**：所有表主键均为UUID，保证全局唯一性。
- **时区兼容**：所有时间戳字段均为TIMESTAMPTZ，统一使用UTC。
- **数据完整性**：通过FOREIGN KEY、UNIQUE、ENUM等约束保证数据准确。

### 6.2 核心表结构

#### 6.2.1 live_rooms（直播房间表）
| 字段名           | 类型      | 说明                       |
|------------------|-----------|----------------------------|
| id               | UUID      | 主键，房间唯一标识         |
| user_id          | UUID      | 房间所有者用户ID（可为空） |
| parent_room_id   | UUID      | 父房间ID（分会场用）       |
| title            | VARCHAR   | 房间标题                   |
| description      | TEXT      | 房间描述                   |
| cover_url        | VARCHAR   | 封面图片URL                |
| stream_key       | VARCHAR   | 推流密钥，唯一              |
| is_private       | BOOLEAN   | 是否私密                   |
| record_by_default| BOOLEAN   | 是否默认录制               |
| category_id      | UUID      | 分类ID（可为空）           |
| created_at       | TIMESTAMPTZ | 创建时间                 |
| updated_at       | TIMESTAMPTZ | 更新时间                 |

- **关系**：自引用parent_room_id实现主会场-分会场结构；与live_sessions为一对多关系。

#### 6.2.2 live_sessions（直播场次表）
| 字段名           | 类型      | 说明                       |
|------------------|-----------|----------------------------|
| id               | UUID      | 主键，场次唯一标识         |
| room_id          | UUID      | 所属房间ID，外键           |
| status           | ENUM      | 会话状态（scheduled/live等）|
| start_time       | TIMESTAMPTZ | 开始时间                 |
| end_time         | TIMESTAMPTZ | 结束时间（可为空）        |
| video_id         | UUID      | 关联媒资ID（可为空）       |
| created_at       | TIMESTAMPTZ | 创建时间                 |
| updated_at       | TIMESTAMPTZ | 更新时间                 |

- **关系**：与live_rooms为多对一关系；与session_statistics为一对一关系。

#### 6.2.3 session_statistics（场次统计表）
| 字段名           | 类型      | 说明                       |
|------------------|-----------|----------------------------|
| id               | UUID      | 主键，统计唯一标识         |
| session_id       | UUID      | 关联场次ID，唯一外键       |
| peak_viewer_count| INT       | 峰值观众数                 |
| total_viewer_count| BIGINT   | 总观众数                   |
| total_like_count | BIGINT    | 总点赞数                   |
| total_share_count| BIGINT    | 总分享数                   |
| created_at       | TIMESTAMPTZ | 创建时间                 |
| updated_at       | TIMESTAMPTZ | 更新时间                 |

- **关系**：与live_sessions为一对一关系。

### 6.3 主要表关系图
- 一个主会场可有多个分会场（parent_room_id自引用）
- 一个房间可有多个直播场次
- 每个直播场次有唯一的统计数据

---

## 7. 交互与UI/UX设计

### 7.1 页面原型与流程图

- **页面结构总览**  
  - 首页（房间列表页）：展示所有主会场，支持筛选、搜索、分页、卡片式布局。
  - 房间详情页：展示房间信息、分会场导航、场次列表入口，支持编辑、删除、创建分会场。
  - 分会场详情页：与房间详情一致，突出主/分会场层级关系。
  - 场次列表页：展示所有场次，支持按时间、状态筛选。
  - 场次详情页：展示直播流信息、统计数据、回放入口。
  - 直播观看页：视频播放、实时数据展示。
  - 推流信息页：展示推流码、复制、二维码、推流教程。
  - 全局异常页：404、维护、网络异常等。

- **页面跳转流程**  
  - 首页 → 房间详情 → 分会场/场次列表 → 场次详情/直播观看  
  - 房间详情/分会场详情 → 编辑/删除/创建场次  
  - 直播观看页 → 返回房间详情/首页


### 7.2 详细页面交互流程

#### 7.2.1 房间列表页（RoomList.vue）
1. 展示所有主会场（房间），支持增删改查（CRUD）。
2. 点击房间卡片或“查看详情”按钮，跳转到房间详情页（RoomDetail.vue）。
3. 支持创建新房间（主会场），弹窗表单校验。
4. 支持编辑、删除房间，操作前弹出二次确认。
5. 删除房间前会校验是否存在场次，若有场次需先清空场次。

#### 7.2.2 房间详情页（RoomDetail.vue）
1. 展示房间详细信息。
2. 展示该房间下所有直播场次（列表），支持场次的增删改查。
3. 仅当场次 status 为 live 时，操作区显示“播放”按钮，可跳转到 LiveView.vue 进行播放，其他状态不可播放。
4. 支持分会场（子房间）的增删改查，分会场列表仅主会场显示。
5. 点击分会场可跳转到对应子房间详情页（RoomDetail.vue，参数为子房间ID）。
6. 支持创建分会场，弹窗表单校验。

#### 7.2.3 直播观看页（LiveView.vue）
1. 仅支持播放 status 为 live 的场次。
2. 非 live 状态场次不可播放，前端不显示播放入口。
3. 展示视频播放区、房间简介、推荐直播间等。
4. 支持返回房间详情页、直播列表页。

#### 7.2.4 场次详情页
1. 展示场次基本信息、直播流信息、统计数据。
2. 支持编辑、删除场次，操作前二次确认。
3. 支持回放入口（如有视频ID）。
4. 网络异常时，统一弹窗提示。

#### 7.2.5 直播观看页
1. 进入页面，自动加载视频流，显示Loading动画。
2. 视频加载成功后，展示直播流和实时数据区。
3. 支持实时观众数展示。
4. 网络异常时，自动重连并提示用户。
5. 支持返回房间详情/首页。

#### 7.2.6 推流信息页
1. 展示推流码、二维码，支持一键复制。
2. 提供推流教程入口，支持新手用户快速上手。
3. 推流状态实时刷新，异常时高亮提示。

#### 7.2.7 全局异常页
1. 捕获404、维护、网络异常等，展示友好提示。
2. 提供返回首页、重试等操作。

### 7.3 交互细节与设计规范

#### 7.3.1 加载与空态
- 骨架屏：数据加载时显示骨架屏，避免白屏。
- Loading动画：接口请求、视频加载、操作处理中统一使用全局Loading组件，风格统一为“点跳动”——即几个小点依次闪烁或跳动，提升等待时的动感体验。
- 空数据提示：如“暂无直播间”、“暂无分会场”、“暂无场次”，并提供引导操作（如“去创建”按钮）。

#### 7.3.2 错误与异常处理
- 接口异常：统一弹窗/Toast提示，支持重试。
- 视频加载失败：展示“加载失败”提示，提供刷新/重试按钮。
- 表单校验：输入错误时，字段下方即时红色提示，表单提交失败时聚焦首个错误项。
- 权限不足/操作受限：弹窗提示原因，按钮置灰并显示原因。

#### 7.3.3 组件与操作反馈
- 按钮：点击后进入Loading/禁用状态，防止重复提交。
- 重要操作：如删除、退出直播，需二次确认弹窗。
- 操作结果：成功/失败均有Toast或弹窗反馈，重要操作后自动跳转或刷新页面。
- 复制推流码：点击复制按钮后，Toast提示“复制成功”。

#### 7.3.4 动画与过渡
- 页面切换：淡入淡出或滑动过渡，提升流畅感。
- 弹窗/抽屉：出现/消失有缩放或滑动动画。

#### 7.3.5 响应式与多端适配

多端适配是直播SaaS平台前端开发的核心要求，需在设计、开发、测试全流程中严格执行。以下为统一规范：

**一、设计原则**
1. 一致性优先：不同端核心功能、交互流程、视觉风格保持一致。
2. 适配性优先：根据终端特性灵活调整布局和控件，保证“看得清、点得准、用得顺”。
3. 渐进增强：优先保证主流设备体验，特殊端可适度增强或降级。
4. 一套代码多端运行：优先通过CSS媒体查询、flex/grid布局、uni-app平台能力实现，减少端上分支代码。

**二、常见多端场景与适配规范**
| 端类型     | 主要特性                         | 适配规范                                                         |
|------------|----------------------------------|------------------------------------------------------------------|
| PC/H5      | 大屏、鼠标、键盘、窗口可缩放     | 多列布局、侧边栏、悬停高亮、快捷键、内容居中、最大宽度限制       |
| 移动端App  | 竖屏、触摸、全面屏、刘海屏       | 单列布局、底部Tab、按钮大尺寸、手势滑动、适配安全区              |
| 小程序     | 竖屏、触摸、平台控件/风格限制    | 遵循平台设计规范、控件尺寸/字体/间距标准、API兼容性              |
| 平板       | 横竖屏切换、较大触摸区域         | 两列/多列布局、适配横屏、控件间距适中                            |

**三、断点适配规范**
- 断点定义（团队统一）：
  - ≥1200px：大屏（PC/桌面端）
  - 768px~1199px：平板
  - ≤767px：手机/小程序
- 布局方式：全局采用flex或grid弹性布局，卡片、列表、表单等组件宽度随断点自适应调整。
- 样式管理：所有断点样式集中在common/responsive.scss或全局样式文件统一管理，禁止在单组件内随意写媒体查询。
- 字体与控件尺寸：PC端字体14-16px，移动端13-15px，小程序端按平台规范。按钮、输入框等控件高度PC端32-40px，移动端44-48px。
- 间距与触控区域：移动端所有可点击区域≥44x44px，PC端适当缩小间距。

**四、平台特性适配**
- PC端：鼠标悬停高亮、快捷键、侧边栏/顶部导航、内容居中、最大宽度≤1440px。
- 移动端：底部Tab导航、按钮大尺寸、手势滑动返回、适配全面屏/刘海屏（safe-area）。
- 小程序端：控件、字体、间距严格遵循平台设计规范，注意API兼容性。
- 平板端：支持横竖屏切换，横屏多列，竖屏单列或两列。

**五、开发与协作规范**
1. 原型设计需提供PC、移动端、小程序三种主流尺寸适配稿。
2. 响应式样式、断点变量、控件尺寸等统一抽离为全局样式/变量，禁止重复定义。
3. 通用组件需自适应多端，禁止写死宽高。
4. 每次开发/上线前，必须在PC、主流手机、微信小程序等多端真机测试。
5. 断点、控件尺寸、适配规范等需在团队文档中明确，所有成员遵循。

**六、代码示例**
```scss
// common/responsive.scss
$breakpoint-pc: 1200px;
$breakpoint-tablet: 768px;
$breakpoint-mobile: 767px;

.room-list {
  display: grid;
  grid-gap: 16px;
  @media (min-width: $breakpoint-pc) {
    grid-template-columns: repeat(4, 1fr);
  }
  @media (min-width: $breakpoint-tablet) and (max-width: $breakpoint-pc - 1) {
    grid-template-columns: repeat(2, 1fr);
  }
  @media (max-width: $breakpoint-mobile) {
    grid-template-columns: 1fr;
  }
}
```

#### 7.3.6 无障碍与可访问性
- 色彩对比：主色与背景对比度≥4.5:1，适合弱视用户。
- 键盘操作：所有可交互元素支持Tab键切换、Enter激活。
- ARIA标签：为重要组件（如弹窗、表单）添加aria-*属性，提升可访问性。

### 7.3.7 设计令牌与视觉规范（医疗级强制标准）

**[最高约束]** 本节定义的视觉设计令牌、全局样式变量、表单输入规范等，必须与 src/common/uni.scss 保持完全一致。

#### 一、全局令牌 (Global Tokens)

- 主色（Primary）：--color-primary: #509cec
- 主色悬浮：--color-primary-hover: #215588
- 主色浅色：--color-primary-light-1: #e9f2fc
- 成功色：--color-success: #28a745
- 危险色：--color-danger: #dc3545
- 警告色：--color-warning: #ffc107
- 信息色：--color-info: #6C757D
- 主文本色：--color-text-primary: #121111
- 次文本色：--color-text-secondary: #6C757D
- 占位符色：--color-text-placeholder: #adb5bd
- 反色文本：--color-text-on-primary: #ffffff
- 背景色：--color-background: #F8F9FA
- 浅背景色：--color-background-light: #FFF
- 边框色：--color-border: #E9ECEF

#### 二、字体与排版 (Typography)
- 字体族：--font-family-sans-serif: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
- 字号：
  - --font-size-small: 10px
  - --font-size-base: 12px
  - --font-size-medium: 14px
  - --font-size-large: 18px
- 间距：
  - --spacing-small: 4px
  - --spacing-medium: 6px
  - --spacing-large: 10px
  - --spacing-xlarge: 20px
- 圆角：
  - --radius-base: 6px
  - --radius-large: 8px
  - --radius-circle: 50%
- 阴影：
  - --shadow-base: 0 4px 6px rgba(0, 0, 0, 0.05)
  - --shadow-large: 0 10px 15px rgba(0, 0, 0, 0.07)

#### 三、表单输入与交互反馈
- 输入框、textarea、uni-input、uni-textarea 等所有表单控件必须使用统一的全局样式：
  - 边框色：var(--color-border)
  - 圆角：var(--radius-base)
  - 字体：var(--font-family-sans-serif)
  - 字号：var(--font-size-medium)
  - 背景色：var(--color-background-light)
  - 过渡动画：var(--transition-base)
- 悬停/聚焦高亮：border-color: var(--color-primary)，box-shadow: 0 2px 6px rgba(0,0,0,0.12)
- 错误状态：border-color: var(--color-danger)，背景色：rgba(220,53,69,0.02)
- 禁用状态：背景色 var(--color-background)，文本色 var(--color-text-secondary)，opacity: 0.6
- 占位符色：var(--color-text-placeholder)
- textarea、uni-textarea 默认最小高度 60px，最大高度 80px，禁用 resize，隐藏滚动条
- 响应式：移动端输入框 padding 增大，font-size: 16px

#### 四、响应式与断点
- 响应式断点、表单输入、间距等样式全部以 uni.scss 为唯一标准，禁止在组件内重复定义媒体查询。

#### 五、命名与引用
- 所有样式变量、设计令牌必须通过 var(--xxx) 方式引用，禁止硬编码。
- 组件、页面、表单等样式必须直接引用 uni.scss 中的变量。

#### 六、与设计文档不符处修正说明
- 颜色、字体、间距、圆角、阴影、表单输入、响应式等所有规范以 src/common/uni.scss 为准，发现文档与样式不符处，已全部修正。

#### 7.3.8 无障碍与可访问性
*此部分内容已整合并强化到 7.3.7 节的强制性规范中。*

### 7.4 多端适配与协作建议

- H5端：支持PWA，添加到桌面，离线提示。
- App端：适配全面屏、刘海屏，支持原生分享、推送。
- 小程序端：兼容微信、支付宝等平台，注意API差异。
- 多端一致性：所有交互、动画、提示需在各端真实设备测试，保证体验一致。
- 原型/设计稿：建议团队使用Figma/墨刀等工具，所有页面、组件需有高保真原型。
- 交互文档：每个页面/组件需有交互说明，包含状态、异常、动画、适配等。
- 设计评审：前端、设计、产品定期评审交互稿，确保实现一致。
- 多端验收：上线前在PC、主流手机、微信小程序等多端验收交互体验。

### 7.5 典型交互流程图与说明

> 建议在团队协作平台补充Figma/墨刀等原型链接，或用Mermaid/ASCII图补充页面跳转流程，便于前后端、设计、测试协作。

- 首页（房间列表）→ 房间详情 → 分会场详情/场次列表 → 场次详情/直播观看
- 房间详情/分会场详情 → 编辑/删除/创建场次
- 直播观看页 → 返回房间详情/首页
- 推流信息页 → 复制推流码/查看教程
- 全局异常页 → 返回首页/重试

---


### 7.6 通用组件库设计规范

#### 一、设计原则
1. 高复用：所有通用组件（按钮、表单、弹窗、卡片等）应满足多场景复用，避免重复造轮子。
2. 风格统一：严格遵循视觉规范（色彩、圆角、阴影、字体、间距等），保证全平台一致体验。
3. 可配置性强：支持常用属性（如类型、尺寸、禁用、加载、图标、插槽等），满足业务灵活扩展。
4. 无障碍：支持键盘操作、aria标签、焦点样式，提升可访问性。
5. 多端适配：组件样式、尺寸、交互在PC、移动、小程序等端自适应。

#### 二、核心组件设计规范与代码示例

##### 1. 按钮（Button）
- 规范：
  - 支持主按钮、次按钮、危险按钮、禁用、加载、图标等状态。
  - 尺寸：大（48px）、中（40px）、小（32px）。
  - 圆角、主色、禁用色、加载动画等风格统一。
  - 支持slot自定义内容。
- 代码示例：
```vue
<template>
  <button
    :class="['btn', type, size, { disabled, loading }]"
    :disabled="disabled || loading"
    @click="handleClick"
    :aria-label="ariaLabel"
  >
    <span v-if="loading" class="btn-loading">···</span>
    <slot />
  </button>
</template>
<script setup lang="ts">
defineProps<{
  type?: 'primary' | 'secondary' | 'danger'
  size?: 'large' | 'medium' | 'small'
  loading?: boolean
  disabled?: boolean
  ariaLabel?: string
}>()
const emit = defineEmits(['click'])
function handleClick(e) {
  if (!props.disabled && !props.loading) emit('click', e)
}
</script>
<style scoped>
.btn { border-radius: 6px; font-size: 16px; padding: 0 20px; height: 40px; }
.btn.primary { background: var(--color-primary); color: #fff; }
.btn.secondary { background: #f0f2f5; color: var(--color-primary); }
.btn.danger { background: var(--color-danger); color: #fff; }
.btn.disabled { opacity: 0.5; cursor: not-allowed; }
.btn.loading { margin-right: 8px; animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>
```

##### 2. 表单（Form & Input）
- 规范：
  - 支持表单校验、错误提示、禁用、只读、清除、密码、数字、日期等类型。
  - 输入框高度40-48px，圆角6px，边框主色/警告色。
  - 错误提示红色，辅助信息灰色。
  - 支持label、placeholder、前后缀图标slot。
- 代码示例：
```vue
<template>
  <div class="form-item">
    <label v-if="label">{{ label }}</label>
    <input
      :type="type"
      :placeholder="placeholder"
      :value="modelValue"
      :disabled="disabled"
      :readonly="readonly"
      @input="$emit('update:modelValue', $event.target.value)"
      :aria-label="label"
    />
    <span v-if="error" class="form-error">{{ error }}</span>
    <span v-if="hint" class="form-hint">{{ hint }}</span>
  </div>
</template>
<script setup lang="ts">
defineProps<{
  label?: string
  type?: string
  placeholder?: string
  modelValue: string
  error?: string
  hint?: string
  disabled?: boolean
  readonly?: boolean
}>()
defineEmits(['update:modelValue'])
</script>
<style scoped>
.form-item { margin-bottom: 16px; }
input { height: 40px; border-radius: 6px; border: 1px solid var(--color-border); padding: 0 12px; }
input:focus { border-color: var(--color-primary); }
.form-error { color: var(--color-danger); font-size: 12px; }
.form-hint { color: #8c8c8c; font-size: 12px; }
</style>
```

##### 3. 弹窗（Modal/Dialog）
- 规范：
  - 居中弹出，圆角8px，遮罩可关闭，ESC关闭，支持标题、内容、操作按钮slot。
  - 支持主操作/取消/自定义按钮，按钮风格与主色一致。
  - 支持键盘无障碍操作。
- 代码示例：
```vue
<template>
  <div v-if="visible" class="modal-mask" @click.self="close">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-title">{{ title }}</div>
      <div class="modal-content"><slot /></div>
      <div class="modal-actions">
        <button @click="close">取消</button>
        <button class="primary" @click="confirm">确定</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ visible: boolean; title?: string }>()
const emit = defineEmits(['close', 'confirm'])
function close() { emit('close') }
function confirm() { emit('confirm') }
</script>
<style scoped>
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 8px; min-width: 320px; padding: 24px; }
.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.modal-actions { text-align: right; margin-top: 24px; }
button.primary { background: var(--color-primary); color: #fff; }
</style>
```

##### 4. 卡片（Card）
- 规范：
  - 圆角6px，阴影柔和，背景白色，内容区分明。
  - 支持标题、内容、操作区slot，支持可点击/可拖拽/可选中等状态。
  - 卡片间距16-24px，适配多端。
- 代码示例：
```vue
<template>
  <div class="card" :class="{ clickable }" @click="handleClick">
    <div v-if="title" class="card-title">{{ title }}</div>
    <div class="card-content"><slot /></div>
    <div v-if="$slots.actions" class="card-actions"><slot name="actions" /></div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ title?: string; clickable?: boolean }>()
const emit = defineEmits(['click'])
function handleClick(e) { if (props.clickable) emit('click', e) }
</script>
<style scoped>
.card { background: #fff; border-radius: 6px; box-shadow: 0 2px 8px rgba(24,144,255,0.06); padding: 20px; margin-bottom: 16px; }
.card-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.card.clickable { cursor: pointer; transition: box-shadow .2s; }
.card.clickable:hover { box-shadow: 0 4px 16px rgba(24,144,255,0.12); }
.card-actions { margin-top: 16px; text-align: right; }
</style>
```

#### 三、组件库协作与维护建议
- 文档化：每个组件需有详细文档（属性、事件、插槽、用例、设计稿链接）。
- 单元测试：核心交互、边界条件需有单元测试。
- 多端验收：每次组件变更需在PC、移动、小程序等多端真机测试。
- 版本管理：组件库单独版本管理，变更需评审和回归测试。
- 设计同步：与Figma/墨刀等设计原型保持同步，定期评审。 

 ----

## 8. 前后端接口与页面功能映射（全量规范版）

本节全面梳理前端所有页面与后端API接口的对应关系，确保与《直播核心功能设计文档.md》中API设计完全一致，便于团队协作、接口联调和后续维护。

### 8.1 页面与接口映射总览表（分模块）

#### 8.1.1 直播房间（主会场/分会场）相关
| 页面/功能                | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 房间列表页（RoomList.vue） | GET      | /api/v1/rooms                               | 分页获取所有房间，可筛选主会场 |
| 房间详情页（RoomDetail.vue） | GET      | /api/v1/rooms/{room_id}                     | 获取指定房间详情 |
| 房间创建/编辑/删除      | POST/PATCH/DELETE | /api/v1/rooms/{room_id}                  | 创建/更新/删除主会场/分会场 |
| 分会场列表              | GET      | /api/v1/rooms/{room_id}/sub-venues          | 获取主会场下所有分会场 |
| 分会场详情              | GET      | /api/v1/rooms/{sub_venue_id}                | 获取分会场详情（与房间详情一致） |
| 分会场编辑/删除         | PATCH/DELETE | /api/v1/rooms/{sub_venue_id}              | 编辑/删除分会场 |

#### 8.1.2 直播场次相关
| 页面/功能                | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 场次列表（已集成在房间详情页） | GET      | /api/v1/rooms/{room_id}/sessions            | 获取房间下所有场次 |
| 场次详情页（SessionDetail.vue） | GET      | /api/v1/sessions/{session_id}               | 获取单场直播详情及统计 |
| 场次创建/编辑/删除      | POST/PATCH/DELETE | /api/v1/sessions/{session_id}            | 创建/更新/删除场次 |

#### 8.1.3 直播观看与推流
| 页面/功能                | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 直播观看页（LiveView.vue） | GET      | /api/v1/sessions/{session_id}               | 仅 status 为 live 时可播放 |
| 推流信息页              | GET      | /api/v1/rooms/{room_id}                     | 获取 stream_key 等推流信息 |

#### 8.1.4 统计与分析
| 页面/功能                | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 场次统计数据            | GET      | /api/v1/sessions/{session_id}               | 响应中包含statistics字段 |
| 分会场列表页            | GET      | /api/v1/rooms/{room_id}/sub-venues          | items中含live_status、current_session_id |

#### 8.1.5 全局与异常
| 页面/功能                | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 全局异常/404/维护页     | -        | -                                            | 统一异常展示，无接口 |

#### 8.1.6 内部API（仅后端调用，前端无需实现页面）
| 功能                    | HTTP方法 | API端点                                      | 说明 |
|-------------------------|----------|----------------------------------------------|------|
| 推流鉴权与激活          | POST     | /internal/srs/on_publish                    | SRS推流回调 |
| 断流处理                | POST     | /internal/srs/on_unpublish                  | SRS断流回调 |

---

> 说明：本阶段所有API请求均使用后端提供的测试Token，用户登录/注册/中心等页面暂不开发，待用户模块开发完成后再补充相关内容。

---


### 8.2 页面功能与接口交互流程（全量覆盖）

#### 8.2.1 房间与分会场模块
- 房间列表页（RoomList.vue）：加载时请求 GET /api/v1/rooms，分页、筛选主会场，渲染房间卡片，支持房间的增删改查。
- 房间详情页（RoomDetail.vue）：请求 GET /api/v1/rooms/{room_id}，展示房间信息、分会场导航、场次列表。场次列表支持增删改查，分会场支持增删改查。
- 分会场详情/编辑/删除：同房间详情/编辑/删除，接口参数为分会场ID。

#### 8.2.2 场次模块
- 场次列表已集成在房间详情页，无独立 SessionList.vue 页面。
- 仅 status 为 live 的场次可在操作区显示“播放”按钮，跳转到 LiveView.vue。
- 其他状态场次不可播放，前端不显示播放入口。

#### 8.2.3 直播观看与推流
- 直播观看页（LiveView.vue）：仅支持播放 status 为 live 的场次，其他状态不可播放。
- 推流信息页：请求 GET /api/v1/rooms/{room_id}，获取 stream_key，展示推流码。

#### 8.2.4 统计与分析
- 场次详情页：响应中statistics字段展示实时/历史数据。
- 分会场列表页：items中展示live_status、current_session_id。


#### 8.2.5 全局与异常
- 全局异常/404/维护页：捕获全局异常，跳转或弹窗提示，无需接口。

#### 8.2.6 内部API（后端专用）
- 推流鉴权与激活：SRS推流时POST /internal/srs/on_publish，前端无需页面。
- 断流处理：SRS断流时POST /internal/srs/on_unpublish，前端无需页面。

---

> 本章节为前后端联调、页面开发和接口对接的权威参考，后续如有API变更请同步更新。

---

## 9. 开发实施计划

### 9.1 阶段划分
1. **项目初始化**
   - uni-app项目搭建、目录结构规划、基础依赖安装
   - ESLint/Prettier/TS配置、CI/CD集成
2. **基础功能开发**
   - 房间列表、详情、分会场、场次管理页面开发
   - API接口封装、状态管理实现
3. **直播观看与推流功能**
   - 视频播放、推流、互动功能开发
   - 弱网/异常处理、性能优化
4. **测试与优化**
   - 单元/集成/端到端测试，覆盖率达标
   - 体验优化、Bug修复、代码重构
5. **上线与运维**
   - 多端适配、打包发布、上线监控

### 9.2 里程碑
- M1：项目结构与基础页面完成
- M2：直播观看/推流功能开发完成
- M3：分会场/场次管理、互动功能完善
- M4：测试通过，体验优化，准备上线

---

## 10. 参考资料
- [uni-app 官方文档](https://uniapp.dcloud.io/)
- [哔哩哔哩直播](https://live.bilibili.com/)
- [抖音直播](https://live.douyin.com/)
- [直播核心功能设计文档.md]

