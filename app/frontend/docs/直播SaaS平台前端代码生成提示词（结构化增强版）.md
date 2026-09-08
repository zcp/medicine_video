# 直播SaaS平台前端代码生成提示词（结构化增强版）

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和多端适配，具备大型SaaS/直播平台前端架构与实现经验，能够根据详细设计文档和上下文，编写高质量、规范、可维护的前端代码。

---

## 2. 任务目标（Task Objective）
本次任务为全新搭建直播SaaS平台前端项目。目标是根据《直播SaaS平台前端设计文档.md》生成一个完整、可运行的前端应用骨架。

**为确保任务明确、无歧义，本次需具体生成以下完整且详细的前端项目结构框架：**

### A. 项目基础结构与配置文件（Project Skeleton & Config Files）
- **根目录文件与目录 (Root Files & Dirs):**
  - `package.json`, `tsconfig.json`, `vite.config.ts`, `.eslintrc.js`, `.prettierrc`, `jest.config.js`, `.gitignore`, `README.md`, `tests/`, `uni_modules/`
- **核心源码目录 (Core Source Directory):**
  - `src/`: **唯一**的核心源码目录，包含以下所有内容：
    - `App.vue`, `main.ts`, `pages.json`, `manifest.json`, `env.d.ts`
    - `api/`, `common/`, `components/`, `pages/`, `static/`, `store/`, `types/`, `utils/`

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
  - `src/pages/session/SessionList.vue`: 场次列表页
  - `src/pages/live/LiveView.vue`: 直播观看页
  - `src/pages/common/NotFound.vue`: 404页面
- **核心通用组件 (`src/components/`):**
  - `src/components/RoomCard.vue`: 房间卡片组件
  - `src/components/ModalDialog.vue`: 通用弹窗组件
  - `src/components/AppButton.vue`: 通用按钮组件

所有生成内容需严格对齐设计文档和后端接口规范，满足多端适配、无障碍、安全、性能等要求。

---

## 3. 核心上下文信息（Core Context Information）

### 3.1 推荐项目结构（与设计文档对齐，需标注生成状态）
- 目录结构严格遵循《直播SaaS平台前端设计文档.md》第 3.3 节和第 5.1 节。请根据实际生成情况为每项标注“已生成”或“需生成”：
  - `src/pages/`                # 页面（如直播间、房间列表、分会场等）（需生成）
  - `src/components/`           # 通用/业务组件（需生成）
  - `src/store/`                # 状态管理（需生成）
  - `src/api/`                  # 接口封装（需生成）
  - `src/utils/`                # 工具函数（需生成）
  - `src/static/`               # 静态资源（需生成）
  - `src/common/`               # 公共样式、mixin（需生成）
  - `src/types/`                # TypeScript类型定义 (需生成)
  - `uni_modules/`          # uni-app插件（需生成）
  - `tests/`                # 测试用例（需生成）
  - `package.json`          # 项目依赖（需生成）
  - `tsconfig.json`         # TypeScript 配置（需生成）
  - `src/manifest.json`         # uni-app 应用配置（需生成）
  - `src/pages.json`            # uni-app 页面配置（需生成）
  - `src/common/uni.scss`       # uni-app 全局样式（需生成）
  - `src/App.vue`               # Vue 应用入口文件（需生成）
  - `src/main.ts`               # Vue 初始化脚本（需生成）
  - `README.md`             # 项目说明（需生成）

### 3.2 依赖与初始化要求
- 需自动生成并配置：uni-app项目初始化、package.json、tsconfig.json、eslint/prettier配置。
- 需自动在 `src/` 目录下生成并配置：`pages.json`、`manifest.json`。
- 需自动在 `src/common/` 目录下生成 `uni.scss`。
- 需自动安装并配置：Vue3、TypeScript、Pinia、uView/NutUI/Vant、jest等依赖。
- 需自动生成全局样式、常量、接口请求封装、状态管理入口等基础文件。

---

## 4. 全局强制性约束与最高准则 (Global Mandatory Constraints & Ultimate Principle)
- **最高准则**: 本次任务的**唯一且最高准则**是：所有生成内容必须与《直播SaaS平台前端设计文档.md》和后端接口规范**100%完全一致**。任何细节的偏离、遗漏或自由发挥都是**绝对禁止**的。
- **零偏差原则**: 你必须像一个代码编译器一样，精确地将设计文档翻译成代码。不允许任何形式的“优化”或“变通”，除非设计文档明确授权。
- **命名与结构**: 所有目录、文件、组件、变量、函数、CSS类名的命名，都必须严格采用设计文档中指定的命名方案。项目结构必须完全复刻 `3.1 推荐项目结构`。
- **冲突解决**: 如果在生成过程中发现任何疑似冲突或模糊不清之处，必须以《直播SaaS平台前端设计文档.md》为唯一判断依据。

---

## 5. 分步生成与交叉验证流程 (Step-by-Step Generation & Cross-Validation Flow)
**[流程指令]** 你必须严格按照以下步骤顺序生成代码，完成一步后，进行该步骤的交叉验证，然后再进入下一步。禁止跳过、合并或打乱顺序。

### 步骤1：API 层生成（api/）
- **[约束]** 本步骤所有产出必须严格遵循《直播SaaS平台前端设计文档.md》中定义的API规范。
- **目标**：生成所有后端接口的 TypeScript 封装文件（如 room.ts、session.ts、statistics.ts）及统一请求封装（request.ts）。
- **要求**：函数签名、参数（名称、类型、顺序）、返回类型、接口路径、请求方法、Token自动注入逻辑等，必须与后端接口定义一一对应，分毫不差。
- **验证点**：
  - [ ] 是否所有接口都被实现？
  - [ ] 每个接口的请求/响应数据结构是否与后端Schema完全匹配？
  - [ ] 错误处理逻辑是否按文档实现？

### 步骤2：状态管理层生成（store/）
- **[约束]** 本步骤所有产出必须严格对齐后端数据模型和前端设计文档中的状态管理章节。
- **目标**：生成Pinia状态管理文件（如 room.ts、session.ts、user.ts、index.ts）。
- **要求**：Store的State结构、字段名、类型、初始值，必须与后端数据模型（Schema）和设计文档的定义完全一致。Actions必须准确调用API层方法。
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
- **目标**：生成高复用、风格统一、无状态或轻状态的通用组件（如RoomCard、SessionCard、ModalDialog、Pagination等）。
- **要求**：组件的`props`（名称、类型、默认值）、`emits`（事件名、载荷）、`slots`，必须与设计文档完全一致。包含完整的样式、交互反馈、注释和类型声明。必须实现ARIA等无障碍规范。
- **验证点**：
  - [ ] 组件API（props/emits/slots）是否与设计文档一致？
  - [ ] 组件的各种状态（如hover, disabled）下的样式是否符合设计？
  - [ ] 无障碍属性是否按规范添加？

### 步骤5：页面级组件生成（pages/）
- **[约束]** 本步骤所有产出必须严格聚合已有模块，精确实现页面设计。
- **目标**：按业务模块生成所有页面（如home、room、session、live、push、error等）。
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
**[指令]** 以下为具体模块的生成指令，所有指令都必须在 **第4节全局约束** 和 **第5节流程约束** 的框架下执行。

### 6.1 房间详情页（`src/pages/room/detail.vue`）
- **[约束]** 严格遵循设计文档中关于“房间详情页”的全部描述。
- **数据流**: 页面加载时，从路由参数获取`room_id`，立即调用`src/store/room.ts`中的Action（如`fetchRoomDetail`）获取数据。
- **UI渲染**: 使用`v-if`或类似指令处理加载和错误状态。成功时，将数据显示在对应的组件中。必须使用骨架屏（`Skeleton Component`）作为加载状态的占位。
- **交互逻辑**:
  - 点击“编辑”按钮，弹出一个`ModalDialog`组件，并加载该房间的现有数据。
  - 点击“删除”按钮，弹出一个`ModalDialog`组件进行二次确认。
  - 当房间处于“直播中”状态（`status === 'LIVING'`）时，“编辑”和“删除”按钮必须被禁用（`disabled`）。
- **异常处理**: 当API调用失败时，必须在页面顶部显示一个错误提示条（`ErrorBanner`），并提供重试按钮。若返回404，则立即跳转到全局404页面。

### 6.2 房间卡片组件（`src/components/RoomCard.vue`）
- **[约束]** 严格遵循设计文档中关于“房间卡片”的全部描述。
- **Props**: 必须接收一个名为`room`的Prop，其TypeScript类型必须与`src/store/room.ts`中定义的房间对象类型一致。
- **交互**:
  - 整个卡片区域可点击，点击后触发`emit`一个`navigate`事件，并将`room.id`作为参数。
  - 鼠标`hover`时，卡片需有明显的视觉反馈（如阴影加深），具体样式遵循UI规范。
- **样式**: 卡片圆角、阴影、内部布局、字体、颜色等所有视觉元素，必须与UI设计稿完全一致。

### 6.3 房间API接口封装（`src/api/room.ts`）
- **[约束]** 严格对齐后端关于“房间”的API定义。
- **方法**: 必须包含`getRoomList`, `getRoomDetail`, `createRoom`, `updateRoom`, `deleteRoom`等方法。
- **实现**: 每个方法的函数签名（参数名称、类型）和返回值的类型（Promise中的泛型）必须与后端的Swagger或API文档精确匹配。

### 6.4 房间状态管理（`src/store/room.ts`）
- **[约束]** 严格对齐后端关于“房间”的数据模型。
- **State**: 必须包含`rooms: Room[]`、`currentRoom: Room | null`、`status: 'idle' | 'loading' | 'succeeded' | 'failed'`、`error: string | null`等状态。`Room`类型定义必须与后端模型一致。
- **Actions**:
  - `fetchRooms`: 调用`api/room.ts`的`getRoomList`，并处理加载、成功、失败三种状态。
  - `fetchRoomDetail`: 调用`api/room.ts`的`getRoomDetail`，更新`currentRoom`。
- **Getters**: 提供如`getRoomById`等派生状态。

---

## 7. 最终交付与质量保证协议 (Final Delivery & Quality Assurance Protocol)
- **输出格式**:
  - 你必须为每个需要生成的文件，单独输出一个完整、可直接运行的代码块。
  - 每个代码块前必须用Markdown语法标注清晰的文件路径，例如：`// frontend_live/src/pages/room/detail.vue`。
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