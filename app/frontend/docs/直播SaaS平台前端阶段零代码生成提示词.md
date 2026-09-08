# 生成直播前端阶段零：地基与设计规范的代码生成提示词 (V3 - 架构完整版)

---

## 1. 角色定义（Role Definition）
你是一名资深前端架构师，精通uni-app、Vue3、TypeScript和Vite，擅长从零开始搭建可维护、可扩展、规范化的企业级前端项目骨架。你的任务是为后续的开发工作奠定一个坚实、一致且标准化的基础，并**实现**一个功能完整的日志管理模块。

---

## 2. 任务目标（Task Objective）
本次任务为"直播SaaS平台前端项目"的**阶段零**，核心目标是**搭建项目的完整骨架，实现UI设计规范代码化，并创建功能完备的日志管理系统**。所有生成的文件和代码都必须是生产级别的、功能完整的，而不仅仅是静态的骨架。

**为确保任务明确、无歧义，本次需具体生成以下所有文件和目录：**

1.  **项目根目录文件**:
    -   `package.json`
    -   `vite.config.ts`
    -   `tsconfig.json`
    -   `.eslintrc.cjs` (使用 `.cjs` 扩展以支持 CommonJS)
    -   `.prettierrc`
    -   `jest.config.js`
    -   `.gitignore`
    -   `README.md`

2.  **核心源码文件 (`src/`)**:
    -   `App.vue`
    -   `main.ts`
    -   `pages.json`
    -   `manifest.json`
    -   `env.d.ts`
    -   `common/uni.scss` (设计令牌)

3.  **日志管理模块 (`src/logs/`)**:
    -   `logTypes.ts`
    -   `logConfig.ts`
    -   `logger.ts`

4.  **空目录结构**:
    -   `src/api/`
    -   `src/components/`
    -   `src/pages/`
    -   `src/static/`
    -   `src/store/`
    -   `src/types/`
    -   `src/utils/`
    -   `tests/`

---

## 3. 核心上下文信息（Core Context Information）
-   **唯一事实来源**: 《直播SaaS平台前端设计文档.md》是所有代码生成工作的唯一且最高的设计依据。
-   **设计令牌**: `uni.scss` 文件中的所有CSS变量必须严格依据《直播SaaS平台前端设计文档.md》**第7.3.7节**进行转换。
-   **日志系统**: 日志系统的实现必须遵循下文中的动态逻辑和功能要求。

---

## 4. 全局强制性约束与最高准则
-   **功能完整性**: 生成的所有代码（尤其是配置文件和日志模块）必须是功能完整的，可直接运行。
-   **零偏差原则**: 严格遵循设计文档，不允许任何形式的“优化”或“变通”。
-   **命名与结构**: 严格遵循《直播SaaS平台前端设计文档.md》**第 3.2 节**中的命名规范。
-   **依赖导入**: 所有模块必须正确地从其他模块导入所需的类型或函数。

---

## 5. 分步生成指令 (Step-by-Step Module Generation)

### 步骤1：项目配置文件生成

#### `package.json`
- **目标**: **创建**一个包含所有必要依赖项和脚本的 `package.json` 文件。
- **要求**:
  - **包含** `dependencies`: `vue`, `pinia`。
  - **包含** `devDependencies`: `@dcloudio/types`, `@types/node`, `typescript`, `vite`, `eslint`, `prettier`, `vue-tsc`, `@uni-helper/vite-plugin-uni-pages`, `@uni-helper/vite-plugin-uni-layouts` 等常用工具。
  - **定义** `scripts`: `dev:h5`, `dev:mp-weixin`, `build:h5`, `build:mp-weixin`, `lint`, `format`。

#### `vite.config.ts`
- **目标**: **配置** Vite 以支持 uni-app 和 TypeScript。
- **要求**:
  - **导入**并**使用** `uni` 插件。
  - **配置** `@` 路径别名，使其指向 `src` 目录。

#### `tsconfig.json`
- **目标**: **配置** TypeScript 编译器选项。
- **要求**:
  - **设置** `target` 为 `ESNext`，`module` 为 `ESNext`。
  - **包含** `@dcloudio/types` 在 `types` 数组中，以提供 `uni` 对象的类型定义。
  - **配置** `paths` 以匹配 Vite 的路径别名。

---

### 步骤2：核心应用文件生成 (`src/`)

#### `main.ts`
- **目标**: **实现** Vue 应用的入口文件。
- **要求**:
  - **创建** Vue 应用实例。
  - **创建**并**使用** Pinia 实例。
  - **挂载** 应用。

#### `pages.json`
- **目标**: **配置**页面的路由和全局样式。
- **要求**:
  - **定义**一个空的 `pages` 数组（后续阶段填充）。
  - **配置** `globalStyle`，设置默认的背景色、导航栏颜色等，**必须**使用 `uni.scss` 中定义的CSS变量。

#### `common/uni.scss`
- **目标**: **实现**设计令牌的CSS变量。
- **要求**:
  - 严格依据《直播SaaS平台前端设计文档.md》**第7.3.7节**。
  - **定义**颜色、字体、间距、圆角等所有设计规范的CSS变量。

---

### 步骤3：日志管理模块生成 (`src/logs/`)

*这部分将保持原有的详细动态逻辑要求，确保生成一个功能完备的日志系统。*

#### `src/logs/logTypes.ts`
- **目标**: **定义**所有日志相关的类型、接口和枚举。
- **强制性要求**:
  1. **定义** `LogLevel` 枚举 (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`)。
  2. **创建** `LogEntry` 接口，包含 `level`, `message`, `timestamp`, `module`, `data`, `error` 字段。
  3. **定义** `SensitiveConfig`, `LogFilter`, `LogStorageOptions`, `LogReportOptions`, `LoggerConfig` 等所有配置相关的接口。

#### `src/logs/logConfig.ts`
- **目标**: **配置**日志系统的行为和安全策略。
- **强制性要求**:
  1. **实现**一个函数 `createLoggerConfig`，该函数能**感知**当前环境 (`development` 或 `production`)。
  2. **根据环境**返回不同的配置对象，例如开发环境**开启** `DEBUG` 级别日志并**关闭**上报，生产环境**使用** `INFO` 级别并**开启**上报。
  3. **实现**一个 `sensitiveFields` 数组，**定义**多种脱敏规则（例如 `password` 完全隐藏, `phone` 保留首尾）。

#### `src/logs/logger.ts`
- **目标**: **实现**完整的日志记录、处理和上报功能。
- **数据流与错误处理要求**:
  1.  **实现** `log` 方法作为核心入口。此方法必须**接收**日志级别、模块、消息和可选数据。
  2.  **数据流**:
      -   **输入**: `log` 方法接收原始日志数据。
      -   **处理**: **调用** `sanitizeData` 方法对 `data` 参数进行深度递归脱敏。
      -   **存储**: **将**处理后的 `LogEntry` 对象 `push` 到内存中的 `logQueue` 数组，并**调用** `saveLogsToStorage` 将整个队列**写入** `uni.storage`。
      -   **输出**: 如果是开发环境，**调用** `printToConsole` 将日志**输出**到控制台。
  3.  **状态变化逻辑**:
      -   **存储裁剪**: 在**保存**到本地存储前，**检查** `logQueue` 的长度是否超过 `config.storage.maxEntries`。如果超过，**必须截断**数组，只保留最新的日志。
      -   **批量上报**: 当 `logQueue` 长度达到 `config.reporting.batchSize`，或定时器触发时，**必须**触发 `reportLogs` 方法。
  4.  **错误处理**:
      -   所有对 `uni.storage` 的读写操作都必须被 `try...catch` 包裹。如果 `uni.getStorageSync` 失败（例如数据损坏），**必须**在 `catch` 块中**清空** `logQueue` 并**移除**损坏的 storage item。
      -   `reportLogs` 中的 `uni.request` 必须处理 `fail` 回调。如果上报失败，**不能**清除已上报的日志，以便下次重试。
  5.  **连接应用**:
      -   **实现** `initialize` 方法，在 `Logger` 实例化时被调用。
      -   `initialize` 方法中**必须调用** `setupErrorCapture`。
      -   `setupErrorCapture` **必须使用** `uni.onError` 和 `uni.onUnhandledRejection` 来**自动捕获**全局的JS错误和未处理的Promise拒绝，并**调用** `logger.error` 方法进行记录。

---

## 6. 最终交付与质量保证协议
-   **输出格式**:
    -   每个文件一个完整、可直接运行的代码块，并标注清晰的文件路径。
    -   禁止在代码之外添加任何解释、道歉或不必要的寒暄。
-   **自我修正**: 在每一步生成后，你必须在内部进行自查。如果发现与设计文档或本提示词有任何偏差，必须**立即撤销并重新生成**。
-   **最终一致性断言**: 在完成所有文件生成后，输出：
  ```
  [PHASE 0 ASSERTION]
  Project skeleton and foundation setup is complete.
  - Configuration Files Completeness: 100%
  - Directory Structure Consistency: 100%
    - Logger Implementation: 100%
    - Dynamic Logic Implementation: 100%
  - Zero Business Logic Principle: Adhered
  ```
